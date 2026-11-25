"""Compass Geographic Distance Stage（15km -> 30km -> 60km）.

Compass の距離 Product Boundary の唯一の実装。旧 Monthly orchestrator
（compass_recommendation_orchestrator）と Direction-only Core
（compass_direction_only_core）の両方がここを使う。

purpose / Recommendation / Knowledge を一切参照しない純粋関数だけを置く。
挙動は compass_recommendation_orchestrator から移設する前と同一である
（定数・判定・返り値の順序を変えていない）。
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

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
# happily at Stage 3, see apply_compass_distance_stage docstring) -- this is
# only the "is this narrower ring thick enough to compare candidates in"
# threshold that decides whether to expand to the next stage.
DISTANCE_STAGE_EXPANSION_THRESHOLD = 5


def apply_compass_distance_stage(
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


__all__ = [
    "DISTANCE_STAGE_1_KM",
    "DISTANCE_STAGE_2_KM",
    "DISTANCE_STAGE_3_KM",
    "DISTANCE_STAGE_EXPANSION_THRESHOLD",
    "apply_compass_distance_stage",
]
