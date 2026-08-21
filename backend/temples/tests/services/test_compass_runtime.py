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
    """Runtime Contract Section 8 Group B (narrowed, #2508): birthdate/
    target_date were both valid and the calculation completed -- the
    annual/monthly intersection is empty AND monthly-only guidance
    (monthly_lucky_directions()) is also empty. This is NOT the same None
    used for Group A (invalid/unavailable runtime, see
    test_missing_birthdate_returns_none and test_invalid_birthdate_returns_none
    below), and it is distinct from the Monthly Fallback case (Section 2.2)
    where monthly-only guidance is available -- see
    test_monthly_fallback_used_when_intersection_empty_but_monthly_available."""
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
    ), patch(
        "temples.services.compass_runtime.monthly_lucky_directions",
        return_value={
            "luckyDirection": None,
            "luckyDirections": [],
            "targetYear": 2026,
            "solarMonthIndex": 8,
            "visitDate": "2026-09-15",
            "calculationMethod": "monthly_kyusei_v1",
            "excludedDirections": [],
            "source": "calculated",
        },
    ):
        result = build_compass_direction_runtime(birthdate=BIRTHDATE, target_date="2026-09-15")

    assert isinstance(result, NoCommonDirectionResult)
    assert result is not None


def test_no_common_direction_reproducible_against_real_kyusei():
    """Same case as above, but against the real (unmocked) kyusei
    functions -- synthetic birthdate, not a real user's. Confirmed that
    both the annual/monthly intersection AND monthly-only guidance are
    empty for this birthdate/date pair (the narrowed, #2508 residual
    no_common_direction case, distinct from a Monthly Fallback case)."""
    result = build_compass_direction_runtime(birthdate="1976-06-15", target_date="2026-11-15")
    assert isinstance(result, NoCommonDirectionResult)


def test_monthly_fallback_used_when_intersection_empty_but_monthly_available():
    """Runtime Contract Section 5-1 / Product Contract Section 2.2 (#2508
    Option C): when the annual/monthly intersection is empty but
    monthly-only guidance exists, Compass falls back to the monthly-only
    result rather than returning NoCommonDirectionResult. The result must
    carry calculationMethod="monthly_kyusei_v1", never
    "annual_monthly_kyusei_v1" -- it must not be presented as annual/monthly
    agreement (Signal-to-Explanation Rule)."""
    with patch(
        "temples.services.compass_runtime.planned_visit_lucky_directions",
        return_value={
            "luckyDirection": None,
            "luckyDirections": [],
            "targetYear": 2026,
            "targetMonth": 8,
            "solarMonthIndex": 7,
            "visitDate": "2026-08-20",
            "calculationMethod": "annual_monthly_kyusei_v1",
            "excludedDirections": [],
            "source": "calculated",
        },
    ), patch(
        "temples.services.compass_runtime.monthly_lucky_directions",
        return_value={
            "luckyDirection": "南東",
            "luckyDirections": ["南東"],
            "targetYear": 2026,
            "solarMonthIndex": 7,
            "visitDate": "2026-08-20",
            "calculationMethod": "monthly_kyusei_v1",
            "excludedDirections": ["北", "北東", "南", "南西"],
            "source": "calculated",
        },
    ):
        result = build_compass_direction_runtime(birthdate="1975-06-15", target_date="2026-08-20")

    assert result == {
        "targetDate": "2026-08-20",
        "targetYear": 2026,
        "solarMonthIndex": 7,
        "referenceDirections": ["南東"],
        "calculationMethod": "monthly_kyusei_v1",
        "note": DIRECTION_REFERENCE_NOTE,
    }


def test_monthly_fallback_reproducible_against_real_kyusei():
    """Same case as above, against the real (unmocked) kyusei functions --
    synthetic birthdate, not a real user's. Confirmed that the annual/
    monthly intersection is empty but monthly-only guidance (["南東"]) is
    available for this birthdate/date pair."""
    result = build_compass_direction_runtime(birthdate="1975-06-15", target_date="2026-08-20")

    assert result == {
        "targetDate": "2026-08-20",
        "targetYear": 2026,
        "solarMonthIndex": 7,
        "referenceDirections": ["南東"],
        "calculationMethod": "monthly_kyusei_v1",
        "note": DIRECTION_REFERENCE_NOTE,
    }


def test_common_direction_not_overridden_by_monthly_fallback():
    """Priority requirement (Product Contract Section 2.2-2 / Runtime
    Contract Section 5-1 STEP 4): a valid common direction must never be
    replaced by a monthly-only fallback. monthly_lucky_directions() must not
    even be consulted once a non-empty intersection is found."""
    with patch(
        "temples.services.compass_runtime.monthly_lucky_directions",
        side_effect=AssertionError("monthly_lucky_directions must not be called when a common direction exists"),
    ):
        result = build_compass_direction_runtime(birthdate=BIRTHDATE, target_date="2026-09-15")

    assert result is not None
    assert not isinstance(result, NoCommonDirectionResult)
    assert result["calculationMethod"] == "annual_monthly_kyusei_v1"


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
