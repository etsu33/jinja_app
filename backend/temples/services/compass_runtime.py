"""Compass Runtime Authority assembler.

Builds the CompassDirectionRuntime payload (see
docs/product/compass-mvp-runtime-contract.md Section 5) from birthdate +
target_date. This is the piece Section 3's flow diagram in
docs/product/compass-product-contract.md labels "direction runtime signal"
-- it answers only "what direction, for what month", never "which shrine".
Candidate filtering (compass_direction_filter.py) and Recommendation
integration (compass_recommendation_orchestrator.py) both take this
module's output as an input; neither is touched here.

Reuses kyusei.py's planned_visit_lucky_directions() as the sole calculation
source (Signal Reuse, compass-product-contract.md Section 1: kyusei.py is a
"product-context-free pure calculation module" Compass may reuse) and
direction_reference.py's DIRECTION_REFERENCE_NOTE for the safe user-facing
note text, per Runtime Contract Section 5's requirement that the note be
"of the same kind as the existing DIRECTION_REFERENCE_NOTE". kyusei.py
itself is not modified -- see NoCommonDirectionResult below.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from django.utils import timezone

from temples.domain.kyusei import parse_birthdate, planned_visit_lucky_directions
from temples.services.direction_reference import DIRECTION_REFERENCE_NOTE


@dataclass(frozen=True)
class NoCommonDirectionResult:
    """Marks a VALID no-common-direction outcome.

    Runtime Contract Section 8 Group B (docs/product/compass-mvp-runtime-contract.md):
    birthdate and target_date were both valid, and the annual/monthly kyusei
    calculation itself completed successfully -- it is only their
    intersection (planned_visit_lucky_directions()'s own luckyDirections)
    that is empty. This is a legitimate result, not a fail-safe.

    Deliberately distinct from plain `None`, which remains reserved for
    Group A (invalid/unavailable runtime -- missing or unparseable
    birthdate/target_date, or the calculation itself not completing).
    Carries no fields: there is no direction data to pass along (annual and
    monthly were each computed, they simply share nothing), so callers only
    need to know *that* this happened, not any additional payload.
    """


def build_compass_direction_runtime(
    *,
    birthdate: Optional[str],
    target_date: Optional[str],
) -> Optional[dict[str, Any]] | NoCommonDirectionResult:
    """Resolve the minimal CompassDirectionRuntime payload.

    Returns one of three distinct shapes:
      - a CompassDirectionRuntime dict (Section 5) when a reference direction exists
      - NoCommonDirectionResult() when birthdate/target_date were valid and the
        calculation completed, but annual ∩ monthly is empty (Group B)
      - None when the runtime is genuinely invalid/unavailable (Group A)

    Fail-safe contract (Runtime Contract Section 8): a missing target_date
    defaults to today's date; an invalid-but-present target_date is NOT
    silently replaced with today -- direction context is omitted (None)
    instead, exactly like a missing/invalid birthdate. Never guesses.
    """
    raw_target_date = str(target_date or "").strip()
    if not raw_target_date:
        resolved_target_date = timezone.localdate().isoformat()
    elif parse_birthdate(raw_target_date) is None:
        return None
    else:
        resolved_target_date = raw_target_date

    result = planned_visit_lucky_directions(birthdate, resolved_target_date)
    if not result:
        return None
    if not result.get("luckyDirections"):
        return NoCommonDirectionResult()

    return {
        "targetDate": result["visitDate"],
        "targetYear": result["targetYear"],
        "solarMonthIndex": result["solarMonthIndex"],
        "referenceDirections": result["luckyDirections"],
        "calculationMethod": result["calculationMethod"],
        "note": DIRECTION_REFERENCE_NOTE,
    }


__all__ = ["build_compass_direction_runtime", "NoCommonDirectionResult"]
