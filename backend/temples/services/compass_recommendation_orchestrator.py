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
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from temples.domain.need_tags import NEED_TAGS
from temples.services.compass_direction_filter import filter_candidates_by_direction
from temples.services.compass_runtime import NoCommonDirectionResult
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_candidates import build_chat_candidates
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

    candidate_pool = build_chat_candidates(
        lat=origin_lat,
        lng=origin_lng,
        limit=candidate_pool_limit,
        interpretation_profile=interpretation_profile,
    )

    filtered_candidates = filter_candidates_by_direction(
        candidate_pool,
        origin=origin,
        reference_directions=reference_directions,
    )

    if filtered_candidates is None:
        return CompassRecommendationResult(
            state=STATE_DIRECTION_FILTER_UNAVAILABLE,
            purpose=purpose_slug,
            direction_context=direction_context,
        )

    if not filtered_candidates:
        return CompassRecommendationResult(
            state=STATE_DIRECTION_ZERO_CANDIDATES,
            purpose=purpose_slug,
            direction_context=direction_context,
        )

    bias = (
        {"lat": origin_lat, "lng": origin_lng, "radius": None, "radius_m": None}
        if origin_lat is not None and origin_lng is not None
        else None
    )

    recs = build_chat_recommendations(
        query="",
        language=language,
        candidates=list(filtered_candidates),
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
        )

    return CompassRecommendationResult(
        state=STATE_RECOMMENDATION_SUCCESS,
        recommendations=recommendations,
        purpose=purpose_slug,
        direction_context=direction_context,
    )


__all__ = [
    "STATE_INVALID_PURPOSE",
    "STATE_DIRECTION_FILTER_UNAVAILABLE",
    "STATE_NO_COMMON_DIRECTION",
    "STATE_DIRECTION_ZERO_CANDIDATES",
    "STATE_EVIDENCE_ZERO_CANDIDATES",
    "STATE_RECOMMENDATION_SUCCESS",
    "CompassRecommendationResult",
    "get_compass_recommendations",
]
