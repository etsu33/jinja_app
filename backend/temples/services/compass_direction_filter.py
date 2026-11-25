"""Compass Direction Candidate Filter.

Answers only: "which shrines are geographically inside the Compass direction
candidate space from this origin?" It does not score, rank, or generate
recommendation reasons — that remains Recommendation Authority's
responsibility (see docs/product/compass-product-contract.md Section 6).

Reuses the existing bearing calculation and 8-direction sector labeling from
temples.services.direction_reference rather than reimplementing them, per
docs/product/compass-mvp-runtime-contract.md Section 5 ("do not duplicate
direction math").
"""

from __future__ import annotations

import logging
from typing import Any, Mapping, Optional, Sequence

from temples.services.direction_reference import (
    _DIRECTION_LABELS,
    _bearing,
    _coordinate,
    _direction_label,
)

logger = logging.getLogger(__name__)


def filter_candidates_by_direction(
    candidates: Sequence[Mapping[str, Any]],
    *,
    origin: Optional[Mapping[str, Any]],
    reference_directions: Optional[Sequence[str]],
) -> Optional[list[Mapping[str, Any]]]:
    """Retain only candidates whose bearing from origin resolves to an authorized sector.

    Returns None — not an empty list — when the filter cannot be safely
    performed (origin missing/invalid, or reference_directions missing/empty
    after validation against the existing 8-direction label set). This
    mirrors direction_reference.build_direction_reference's "grounded inputs
    only" contract: an inability to determine the candidate space is never
    represented the same way as a confirmed-empty candidate space ([]).

    Each candidate is evaluated independently; a candidate missing or having
    invalid coordinates is excluded from the result rather than raising, so
    one bad candidate never breaks the whole batch (same isolation pattern as
    direction_reference.attach_direction_references).

    Candidates are returned as the same objects passed in, in their original
    order — this function filters only, it never scores, re-ranks, or
    reshapes candidate data.
    """
    origin_lat = _coordinate(origin, "lat", "latitude") if origin else None
    origin_lng = _coordinate(origin, "lng", "longitude") if origin else None
    if origin_lat is None or origin_lng is None:
        return None

    authorized = {
        str(value).strip()
        for value in (reference_directions or [])
        if str(value).strip() in _DIRECTION_LABELS
    }
    if not authorized:
        return None

    matched: list[Mapping[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue

        shrine_lat = _coordinate(candidate, "latitude", "lat")
        shrine_lng = _coordinate(candidate, "longitude", "lng")
        if shrine_lat is None or shrine_lng is None:
            continue

        try:
            bearing = _bearing(
                from_lat=origin_lat,
                from_lng=origin_lng,
                to_lat=shrine_lat,
                to_lng=shrine_lng,
            )
            label = _direction_label(bearing)
        except Exception:
            # Candidate data is intentionally excluded from this log.
            logger.error("compass_direction_filter_candidate_failed")
            continue

        if label in authorized:
            matched.append(candidate)

    return matched
