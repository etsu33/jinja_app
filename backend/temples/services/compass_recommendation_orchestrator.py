"""Compass Recommendation Orchestrator.

Connects the Compass-authorized direction candidate space (Phase 3,
temples.services.compass_direction_filter.filter_candidates_by_direction) to
the existing Recommendation domain (build_chat_candidates +
build_chat_recommendations) without changing Concierge behavior, Ranking
weights, or Recommendation Reason authority. See
docs/product/compass-product-contract.md Section 6 and
docs/product/compass-mvp-runtime-contract.md Section 6.

Boundary this module deliberately keeps:

- It does NOT compute direction runtime signals (kyusei / direction_reference
  math). That is Compass Runtime Authority's job and is expected to already
  be resolved by the caller into `direction_context` (the
  CompassDirectionRuntime shape from compass-mvp-runtime-contract.md
  Section 5) before calling this module.
- It does NOT route through ConciergeChatView or touch its compat-mode
  heuristics (compass-mvp-runtime-contract.md Section 6, "ConciergeChatView
  を実装都合で流用しない").
- `direction_context` / `purpose` / `origin` are kept as separate parameters,
  never merged into one object -- this mirrors
  CompassRecommendationHandoffContext (same contract, Section 6) at the code
  level, not just in documentation.
- `birthdate` is intentionally NOT a parameter here. Direction-calc
  (kyusei.honmei_star et al.) already consumed it upstream to produce
  `direction_context`; CompassRecommendationHandoffContext has no birthdate
  field, so it does not travel further into Recommendation Integration.

Compass Geographic Distance Boundary: `filter_candidates_by_direction` is
bearing-only and has no distance cap of its own (by design -- distance is
this module's responsibility, not Direction Filter's). This module applies
`_apply_compass_distance_stage` (15km -> 30km -> 60km, expanding only when a
narrower ring is too thin to compare) between Direction Filter and
Recommendation Ranking, so a candidate merely sharing the right compass
sector at, say, 90km no longer reaches Recommendation. This is Compass-only:
it does not touch Concierge, Ranking's own distance decay, or Direction
Filter's bearing math.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from temples.domain.need_tags import NEED_TAGS
from temples.services.compass_direction_filter import filter_candidates_by_direction
from temples.services.compass_runtime import NoCommonDirectionResult
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_candidates import build_chat_candidates_with_eligibility
from temples.services.consultation_interpreter import interpret_consultation
from temples.services.direction_reference import _coordinate

# Fail-safe / result states (Section 11, plus compass-mvp-runtime-contract.md
# Section 8 Group A/B). Kept as distinct string constants -- never collapse
# two of these into a shared generic "empty" outcome; that is exactly what
# Section 8 forbids for origin/target_date fail-safes, and the same
# principle applies here.
STATE_INVALID_PURPOSE = "invalid_purpose"
STATE_DIRECTION_FILTER_UNAVAILABLE = "direction_filter_unavailable"
STATE_NO_COMMON_DIRECTION = "no_common_direction"
# Shared Recommendation Eligibility gate（concierge_chat_candidates）が候補を
# 全て除外した状態。「方位で落ちた」でも「Recommendationが0件を返した」でもなく、
# 「共有Eligibility契約を満たすShrineが1件も無かった」という別事実であり、
# 正常なproduct resultである（technical errorではない）。他のzero状態へ
# 統合しない。
STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES = "recommendation_eligibility_zero_candidates"
STATE_DIRECTION_ZERO_CANDIDATES = "direction_zero_candidates"
STATE_EVIDENCE_ZERO_CANDIDATES = "evidence_zero_candidates"
STATE_RECOMMENDATION_SUCCESS = "recommendation_success"

# Initial DB candidate pool size before geographic narrowing. Direction
# filtering typically keeps only 1-2 of 8 sectors, so Compass requests a
# wider pre-filter pool than Concierge's default (DEFAULT_LIMIT=20) to avoid
# collapsing to direction_zero_candidates purely from an undersized pool.
# This is a Compass-side call argument, not a change to
# build_chat_candidates() itself or its default for other callers.
DEFAULT_CANDIDATE_POOL_LIMIT = 60

# Compass Geographic Distance Boundary (Compass-only; does not touch
# Recommendation Ranking's existing distance decay, Concierge, or
# filter_candidates_by_direction's bearing-only responsibility). Direction
# Filter alone has no distance cap -- any candidate whose bearing falls in
# an authorized sector passes regardless of distance (docs/audit/
# shrine-dataset-integrity.md Section 14 confirmed this reaches ~99km in
# practice). This stage narrows that to a realistic visiting distance,
# expanding outward only when the narrower ring is too thin to compare.
DISTANCE_STAGE_1_KM = 15
DISTANCE_STAGE_2_KM = 30
DISTANCE_STAGE_3_KM = 60

# Not a minimum candidate count for Recommendation to proceed (1-4 survive
# happily at Stage 3, see _apply_compass_distance_stage docstring) -- this is
# only the "is this narrower ring thick enough to compare candidates in"
# threshold that decides whether to expand to the next stage.
DISTANCE_STAGE_EXPANSION_THRESHOLD = 5


@dataclass(frozen=True)
class CompassRecommendationResult:
    """Result of Compass Recommendation Integration for one request.

    `recommendations` are the untouched recommendation dicts returned by
    build_chat_recommendations() -- this module does not reshape, flatten,
    or relabel their fields (Section 10: direction/purpose/recommendation/
    shrine-fact evidence must remain separately identifiable for a future
    Phase 5 Presentation Authority, not flattened here).

    `direction_context` is passed back unmodified purely so a caller has
    both halves of "why this direction" / "why this shrine" together
    without this module merging them into recommendation entries.
    """

    state: str
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    purpose: Optional[str] = None
    direction_context: Optional[Mapping[str, Any]] = None
    # Compass Geographic Distance Boundary metadata (None for every fail-safe
    # state that never reaches the distance stage -- invalid_purpose,
    # direction_filter_unavailable, no_common_direction -- see
    # _apply_compass_distance_stage and get_compass_recommendations).
    distance_stage_km: Optional[int] = None
    direction_candidate_count: Optional[int] = None
    distance_candidate_count: Optional[int] = None
    # Shared Recommendation Eligibility gateの内訳（共有層が返す値をそのまま
    # 保持するだけで、Compassはeligibilityを自分で判定しない）。候補生成へ
    # 到達しないfail-safe state（invalid_purpose / no_common_direction /
    # direction_filter_unavailable）ではNone。
    source_candidate_count: Optional[int] = None
    eligible_candidate_count: Optional[int] = None


def _apply_compass_distance_stage(
    candidates: Sequence[Mapping[str, Any]],
) -> tuple[list[Mapping[str, Any]], int]:
    """Compass-only Geographic Distance Boundary, applied after Direction
    Filter and before Recommendation Ranking.

    Pure, deterministic, order-preserving: returns a subset of `candidates`
    in their original order, never re-ranked, re-scored, or reshaped -- the
    same isolation contract filter_candidates_by_direction already follows.

    Tries 15km, then 30km, then 60km, in that order. `5` is not a minimum
    candidate count for Recommendation to proceed -- it only decides whether
    the current (narrower) ring has enough candidates to compare, or whether
    to expand to the next one. Stage 3 (60km) is terminal: 1-4 candidates
    there is a normal success, and 0 there means genuinely no candidate
    exists within any realistic visiting distance in this direction -- never
    backfilled from beyond 60km.

    A candidate with a missing/invalid `distance_m` is excluded from every
    stage (never eligible at any distance), but never raises -- one bad
    candidate must not break the whole batch (same isolation pattern as
    filter_candidates_by_direction).

    Returns (eligible_candidates, distance_stage_km) -- the second value is
    always the last stage actually reached (15, 30, or 60), even when that
    stage's result is empty, so callers can tell "Stage 3 tried and failed"
    apart from "never reached the distance stage at all" (None).
    """

    def _within(limit_m: int) -> list[Mapping[str, Any]]:
        eligible: list[Mapping[str, Any]] = []
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                continue
            distance = candidate.get("distance_m")
            if not isinstance(distance, (int, float)) or isinstance(distance, bool):
                continue
            if distance <= limit_m:
                eligible.append(candidate)
        return eligible

    stage_1 = _within(DISTANCE_STAGE_1_KM * 1000)
    if len(stage_1) >= DISTANCE_STAGE_EXPANSION_THRESHOLD:
        return stage_1, DISTANCE_STAGE_1_KM

    stage_2 = _within(DISTANCE_STAGE_2_KM * 1000)
    if len(stage_2) >= DISTANCE_STAGE_EXPANSION_THRESHOLD:
        return stage_2, DISTANCE_STAGE_2_KM

    stage_3 = _within(DISTANCE_STAGE_3_KM * 1000)
    return stage_3, DISTANCE_STAGE_3_KM


def get_compass_recommendations(
    *,
    purpose: str,
    origin: Optional[Mapping[str, Any]],
    direction_context: Optional[Mapping[str, Any]] | NoCommonDirectionResult,
    language: str = "ja",
    candidate_pool_limit: int = DEFAULT_CANDIDATE_POOL_LIMIT,
) -> CompassRecommendationResult:
    """Resolve Compass candidates through the existing Recommendation domain.

    Never falls back to "all shrines" or silently treats an unavailable
    direction filter as a confirmed-empty one -- see
    compass_direction_filter.filter_candidates_by_direction's own
    None-vs-[] contract, which this function preserves rather than collapses.

    `direction_context` being a NoCommonDirectionResult (Group B -- valid
    input, empty annual/monthly intersection) is likewise never collapsed
    into the generic STATE_DIRECTION_FILTER_UNAVAILABLE (Group A -- invalid
    or unavailable runtime); see compass-mvp-runtime-contract.md Section 8.
    """
    purpose_slug = str(purpose or "").strip()
    if purpose_slug not in NEED_TAGS:
        return CompassRecommendationResult(
            state=STATE_INVALID_PURPOSE,
            purpose=purpose_slug or None,
            direction_context=direction_context if isinstance(direction_context, Mapping) else None,
        )

    if isinstance(direction_context, NoCommonDirectionResult):
        return CompassRecommendationResult(
            state=STATE_NO_COMMON_DIRECTION,
            purpose=purpose_slug,
            direction_context=None,
        )

    if not isinstance(direction_context, Mapping):
        return CompassRecommendationResult(
            state=STATE_DIRECTION_FILTER_UNAVAILABLE,
            purpose=purpose_slug,
            direction_context=None,
        )

    reference_directions = direction_context.get("referenceDirections")

    origin_lat = _coordinate(origin, "lat", "latitude") if isinstance(origin, Mapping) else None
    origin_lng = _coordinate(origin, "lng", "longitude") if isinstance(origin, Mapping) else None

    interpretation_profile = interpret_consultation(
        query="",
        need_tags=[purpose_slug],
        selected_goriyaku_tag_ids=[],
    )

    candidate_build = build_chat_candidates_with_eligibility(
        lat=origin_lat,
        lng=origin_lng,
        limit=candidate_pool_limit,
        interpretation_profile=interpretation_profile,
    )
    candidate_pool = candidate_build.candidates

    filtered_candidates = filter_candidates_by_direction(
        candidate_pool,
        origin=origin,
        reference_directions=reference_directions,
    )

    # Group A（入力/runtimeがそもそも成立していない）はGroup Bの
    # product resultより先に判定する。filter_candidates_by_direction()の
    # None契約はorigin / reference_directionsだけで決まり、候補件数には
    # 依存しないため、この順序でも「候補が0件だからunavailableになる」ことは
    # 起きない（compass-mvp-runtime-contract.md Section 8のGroup A/B分離）。
    if filtered_candidates is None:
        return CompassRecommendationResult(
            state=STATE_DIRECTION_FILTER_UNAVAILABLE,
            purpose=purpose_slug,
            direction_context=direction_context,
            source_candidate_count=candidate_build.source_count,
            eligible_candidate_count=candidate_build.eligible_count,
        )

    if candidate_build.source_count > 0 and candidate_build.eligible_count == 0:
        # 候補sourceは存在したのに、Shared Recommendation Eligibility契約を
        # 満たすShrineが1件も残らなかった場合だけこのstateを返す。
        # Direction Filterが候補を落としたのではなく、そもそもDirection Filterへ
        # 渡せるeligibleな候補が存在しない、という別事実である。
        # direction_zero_candidates（eligibleな候補はあったが方位で全滅）とは
        # 区別し、ineligibleなShrineをここで復活させることもしない。
        #
        # source_count == 0（候補sourceそのものが0件）はeligibility failureでは
        # ないため、ここでは扱わない。既存のzero-candidate flow
        # （空poolがDirection Filterを通り direction_zero_candidates へ落ちる）
        # にそのまま任せる -- 新しいstateは追加しない。
        return CompassRecommendationResult(
            state=STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES,
            purpose=purpose_slug,
            direction_context=direction_context,
            direction_candidate_count=None,
            distance_candidate_count=None,
            distance_stage_km=None,
            source_candidate_count=candidate_build.source_count,
            eligible_candidate_count=candidate_build.eligible_count,
        )

    if not filtered_candidates:
        return CompassRecommendationResult(
            state=STATE_DIRECTION_ZERO_CANDIDATES,
            purpose=purpose_slug,
            direction_context=direction_context,
            direction_candidate_count=0,
            distance_candidate_count=0,
            distance_stage_km=None,
            source_candidate_count=candidate_build.source_count,
            eligible_candidate_count=candidate_build.eligible_count,
        )

    direction_candidate_count = len(filtered_candidates)
    distance_filtered_candidates, distance_stage_km = _apply_compass_distance_stage(filtered_candidates)
    distance_candidate_count = len(distance_filtered_candidates)

    if not distance_filtered_candidates:
        # Direction Filter found candidates, but none within even the widest
        # (60km) ring -- distinct from the direction_candidate_count=0 case
        # above via metadata, not a new result_state (Required Behavior:
        # "この2状態を新しいresult_stateへ分割しない").
        return CompassRecommendationResult(
            state=STATE_DIRECTION_ZERO_CANDIDATES,
            purpose=purpose_slug,
            direction_context=direction_context,
            direction_candidate_count=direction_candidate_count,
            distance_candidate_count=0,
            distance_stage_km=distance_stage_km,
            source_candidate_count=candidate_build.source_count,
            eligible_candidate_count=candidate_build.eligible_count,
        )

    bias = (
        {"lat": origin_lat, "lng": origin_lng, "radius": None, "radius_m": None}
        if origin_lat is not None and origin_lng is not None
        else None
    )

    recs = build_chat_recommendations(
        query="",
        language=language,
        candidates=list(distance_filtered_candidates),
        bias=bias,
        need_tags=[purpose_slug],
        public_mode="need",
        flow="A",
        interpretation_profile=interpretation_profile,
    )

    recommendations = [r for r in (recs.get("recommendations") or []) if isinstance(r, dict)]

    if not recommendations:
        # Not reachable under the traced Evidence Gate / pool-fill behavior
        # today (see module docstring in compass_recommendation_orchestrator
        # tests) -- kept as an explicit branch so a future change to
        # build_chat_recommendations that *does* start dropping candidates
        # surfaces as this distinct state rather than silently looking like
        # direction_zero_candidates.
        return CompassRecommendationResult(
            state=STATE_EVIDENCE_ZERO_CANDIDATES,
            purpose=purpose_slug,
            direction_context=direction_context,
            direction_candidate_count=direction_candidate_count,
            distance_candidate_count=distance_candidate_count,
            distance_stage_km=distance_stage_km,
            source_candidate_count=candidate_build.source_count,
            eligible_candidate_count=candidate_build.eligible_count,
        )

    return CompassRecommendationResult(
        state=STATE_RECOMMENDATION_SUCCESS,
        recommendations=recommendations,
        purpose=purpose_slug,
        direction_context=direction_context,
        direction_candidate_count=direction_candidate_count,
        distance_candidate_count=distance_candidate_count,
        distance_stage_km=distance_stage_km,
        source_candidate_count=candidate_build.source_count,
        eligible_candidate_count=candidate_build.eligible_count,
    )


__all__ = [
    "STATE_INVALID_PURPOSE",
    "STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES",
    "STATE_DIRECTION_FILTER_UNAVAILABLE",
    "STATE_NO_COMMON_DIRECTION",
    "STATE_DIRECTION_ZERO_CANDIDATES",
    "STATE_EVIDENCE_ZERO_CANDIDATES",
    "STATE_RECOMMENDATION_SUCCESS",
    "DISTANCE_STAGE_1_KM",
    "DISTANCE_STAGE_2_KM",
    "DISTANCE_STAGE_3_KM",
    "DISTANCE_STAGE_EXPANSION_THRESHOLD",
    "CompassRecommendationResult",
    "get_compass_recommendations",
]
