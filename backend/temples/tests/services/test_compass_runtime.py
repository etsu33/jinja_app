from __future__ import annotations

from datetime import date
from unittest.mock import patch

from temples.services.compass_runtime import NoCommonDirectionResult, build_compass_direction_runtime
from temples.services.direction_reference import DIRECTION_REFERENCE_NOTE

BIRTHDATE = "1984-05-15"


def test_valid_birthdate_and_target_date_returns_direction_runtime():
    result = build_compass_direction_runtime(birthdate=BIRTHDATE, target_date="2026-09-15")

    assert result == {
        "targetDate": "2026-09-15",
        "targetYear": 2026,
        "solarMonthIndex": 8,
        "referenceDirections": ["北西"],
        "calculationMethod": "annual_monthly_kyusei_v1",
        "note": DIRECTION_REFERENCE_NOTE,
    }


def test_missing_target_date_defaults_to_today():
    with patch(
        "temples.services.compass_runtime.timezone.localdate",
        return_value=date(2026, 9, 15),
    ):
        result = build_compass_direction_runtime(birthdate=BIRTHDATE, target_date=None)

    assert result is not None
    assert result["targetDate"] == "2026-09-15"


def test_empty_string_target_date_defaults_to_today_same_as_none():
    with patch(
        "temples.services.compass_runtime.timezone.localdate",
        return_value=date(2026, 9, 15),
    ):
        result = build_compass_direction_runtime(birthdate=BIRTHDATE, target_date="   ")

    assert result is not None
    assert result["targetDate"] == "2026-09-15"


def test_invalid_but_present_target_date_is_omitted_not_defaulted_to_today():
    """Fail-safe contract: an invalid target_date must not silently become
    'today' -- it must omit the direction context entirely."""
    with patch(
        "temples.services.compass_runtime.timezone.localdate",
        return_value=date(2026, 9, 15),
    ) as mock_today:
        result = build_compass_direction_runtime(birthdate=BIRTHDATE, target_date="not-a-date")

    assert result is None
    mock_today.assert_not_called()


def test_missing_birthdate_returns_none():
    result = build_compass_direction_runtime(birthdate=None, target_date="2026-09-15")
    assert result is None


def test_invalid_birthdate_returns_none():
    result = build_compass_direction_runtime(birthdate="not-a-birthdate", target_date="2026-09-15")
    assert result is None


def test_no_lucky_directions_for_period_returns_no_common_direction_marker():
    """Runtime Contract Section 8 Group B: birthdate/target_date were both
    valid and the calculation completed -- only the annual/monthly
    intersection is empty. This is NOT the same None used for Group A
    (invalid/unavailable runtime, see test_missing_birthdate_returns_none
    and test_invalid_birthdate_returns_none below)."""
    with patch(
        "temples.services.compass_runtime.planned_visit_lucky_directions",
        return_value={
            "luckyDirection": None,
            "luckyDirections": [],
            "targetYear": 2026,
            "targetMonth": 9,
            "solarMonthIndex": 8,
            "visitDate": "2026-09-15",
            "calculationMethod": "annual_monthly_kyusei_v1",
            "excludedDirections": [],
            "source": "calculated",
        },
    ):
        result = build_compass_direction_runtime(birthdate=BIRTHDATE, target_date="2026-09-15")

    assert isinstance(result, NoCommonDirectionResult)
    assert result is not None


def test_no_common_direction_reproducible_against_real_kyusei():
    """Same case as above, but against the real (unmocked)
    planned_visit_lucky_directions() -- synthetic birthdate, not a real
    user's. Confirmed empty for this birthdate/date pair independently in
    docs/audit/compass-direction-filter-unavailable-root-cause.md."""
    result = build_compass_direction_runtime(birthdate="1975-06-15", target_date="2026-08-20")
    assert isinstance(result, NoCommonDirectionResult)


def test_does_not_expose_internal_only_fields():
    result = build_compass_direction_runtime(birthdate=BIRTHDATE, target_date="2026-09-15")

    assert result is not None
    assert "excludedDirections" not in result
    assert "luckyDirection" not in result
    assert set(result.keys()) == {
        "targetDate",
        "targetYear",
        "solarMonthIndex",
        "referenceDirections",
        "calculationMethod",
        "note",
    }
