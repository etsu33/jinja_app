"""Compass Runtime Authority assembler.

Builds the CompassDirectionRuntime payload (see
docs/product/compass-mvp-runtime-contract.md Section 5) from birthdate +
target_date. This is the piece Section 3's flow diagram in
docs/product/compass-product-contract.md labels "direction runtime signal"
-- it answers only "what direction, for what month", never "which shrine".
Candidate filtering (compass_direction_filter.py) and Recommendation
integration (compass_recommendation_orchestrator.py) both take this
module's output as an input; neither is touched here.

Implements the Monthly Fallback precedence
(docs/product/compass-product-contract.md Section 2.2,
docs/product/compass-mvp-runtime-contract.md Section 5-1,
docs/product/compass-product-direction-decision.md #2508 Final Direction
Logic: Option C):

    1. annual ∩ monthly non-empty  -> COMMON DIRECTION       (annual_monthly_kyusei_v1)
    2. else monthly-only non-empty -> MONTHLY FALLBACK        (monthly_kyusei_v1)
    3. else                        -> NoCommonDirectionResult (narrowed)

Reuses kyusei.py's planned_visit_lucky_directions() (for step 1) and
monthly_lucky_directions() (for step 2, #2506) as the sole calculation
sources (Signal Reuse, compass-product-contract.md Section 1: kyusei.py is a
"product-context-free pure calculation module" Compass may reuse) and
direction_reference.py's DIRECTION_REFERENCE_NOTE for the safe user-facing
note text, per Runtime Contract Section 5's requirement that the note be
"of the same kind as the existing DIRECTION_REFERENCE_NOTE". kyusei.py
itself is not modified -- the fallback precedence policy lives only here
(Compass Layer B), never in kyusei.py's shared calculation layer -- see
NoCommonDirectionResult below.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from django.utils import timezone

from temples.domain.kyusei import (
    monthly_lucky_directions,
    parse_birthdate,
    planned_visit_lucky_directions,
)
from temples.services.direction_reference import DIRECTION_REFERENCE_NOTE


@dataclass(frozen=True)
class NoCommonDirectionResult:
    """Marks a VALID no-direction outcome (narrowed, #2508).

    Runtime Contract Section 8 Group B (docs/product/compass-mvp-runtime-contract.md):
    birthdate and target_date were both valid, and the annual/monthly kyusei
    calculation itself completed successfully -- the annual/monthly
    intersection is empty AND the monthly-only lucky directions
    (monthly_lucky_directions()) are also empty. This is a legitimate
    result, not a fail-safe.

    Deliberately distinct from plain `None`, which remains reserved for
    Group A (invalid/unavailable runtime -- missing or unparseable
    birthdate/target_date, or the calculation itself not completing).
    Carries no fields: there is no direction data to pass along (annual and
    monthly were each computed, they simply share nothing, and monthly alone
    has nothing either), so callers only need to know *that* this happened,
    not any additional payload.
    """


def build_compass_direction_runtime(
    *,
    birthdate: Optional[str],
    target_date: Optional[str],
) -> Optional[dict[str, Any]] | NoCommonDirectionResult:
    """Resolve the minimal CompassDirectionRuntime payload.

    Returns one of three distinct shapes:
      - a CompassDirectionRuntime dict (Section 5) when a reference direction
        exists -- either COMMON (calculationMethod="annual_monthly_kyusei_v1")
        or MONTHLY FALLBACK (calculationMethod="monthly_kyusei_v1", Section 2.2)
      - NoCommonDirectionResult() when birthdate/target_date were valid and the
        calculation completed, but both annual ∩ monthly and monthly-only are
        empty (Group B, narrowed by #2508)
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
    if result.get("luckyDirections"):
        return {
            "targetDate": result["visitDate"],
            "targetYear": result["targetYear"],
            "solarMonthIndex": result["solarMonthIndex"],
            "referenceDirections": result["luckyDirections"],
            "calculationMethod": result["calculationMethod"],
            "note": DIRECTION_REFERENCE_NOTE,
        }

    # Common direction unavailable (empty intersection) -- attempt Monthly
    # Fallback (Section 2.2) before concluding no_common_direction. Never
    # overrides a valid common direction: this branch is only reached when
    # the block above already found luckyDirections empty.
    monthly = monthly_lucky_directions(birthdate, resolved_target_date)
    if monthly and monthly.get("luckyDirections"):
        return {
            "targetDate": monthly["visitDate"],
            "targetYear": monthly["targetYear"],
            "solarMonthIndex": monthly["solarMonthIndex"],
            "referenceDirections": monthly["luckyDirections"],
            "calculationMethod": monthly["calculationMethod"],
            "note": DIRECTION_REFERENCE_NOTE,
        }

    return NoCommonDirectionResult()


__all__ = ["build_compass_direction_runtime", "NoCommonDirectionResult"]
