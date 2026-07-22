from datetime import date

from temples.domain.kyusei import annual_lucky_directions, planned_visit_lucky_directions
from temples.services.concierge_chat_ranking import _score_direction_signal


def test_annual_lucky_directions_matches_mobile_and_web_contract():
    assert annual_lucky_directions("1984-05-15", today=date(2026, 7, 21)) == {
        "luckyDirection": "東",
        "luckyDirections": ["東", "北西"],
        "targetYear": 2026,
        "calculationMethod": "annual_kyusei_v1",
        "excludedDirections": ["北", "北東", "南", "南西"],
        "source": "calculated",
    }


def test_annual_lucky_directions_uses_february_fourth_boundary():
    before = annual_lucky_directions("1984-05-15", today=date(2026, 2, 3))
    after = annual_lucky_directions("1984-05-15", today=date(2026, 2, 4))
    assert before["targetYear"] == 2025
    assert after["targetYear"] == 2026


def test_planned_visit_direction_intersects_annual_and_monthly_plans():
    result = planned_visit_lucky_directions("1984-05-15", "2026-09-15")
    assert result["luckyDirections"] == ["北西"]
    assert result["targetMonth"] == 9
    assert result["calculationMethod"] == "annual_monthly_kyusei_v1"


def test_direction_signal_uses_actual_bearing_from_origin_to_shrine():
    rec = {"latitude": 35.0, "longitude": 140.0}
    score, matched = _score_direction_signal(
        rec,
        {
            "direction_profile": {
                "luckyDirections": ["東", "北西"],
                "source": "calculated",
                "calculationMethod": "annual_monthly_kyusei_v1",
                "visitDate": "2026-09-15",
            }
        },
        {"lat": 35.0, "lng": 139.0},
    )
    assert score == 0.02
    assert matched == ["plannedLuckyDirection:東"]
    assert rec["direction_from_origin"] == "東"
    assert rec["direction_reference"]["matched"] is True


def test_direction_signal_requires_every_calculation_input():
    valid_profile = {
        "luckyDirections": ["東"],
        "source": "calculated",
        "calculationMethod": "annual_monthly_kyusei_v1",
        "visitDate": "2026-09-15",
    }
    rec = {"latitude": 35.0, "longitude": 140.0}
    origin = {"lat": 35.0, "lng": 139.0}

    for missing in ("source", "calculationMethod", "visitDate"):
        profile = {key: value for key, value in valid_profile.items() if key != missing}
        assert _score_direction_signal(rec.copy(), {"direction_profile": profile}, origin) == (0.0, [])
    assert _score_direction_signal({}, {"direction_profile": valid_profile}, origin) == (0.0, [])
    assert _score_direction_signal(rec.copy(), {"direction_profile": valid_profile}, None) == (0.0, [])


def test_direction_signal_does_not_score_a_non_matching_bearing():
    score, matched = _score_direction_signal(
        {"latitude": 36.0, "longitude": 139.0},
        {"direction_profile": {
            "luckyDirections": ["東"], "source": "calculated",
            "calculationMethod": "annual_monthly_kyusei_v1", "visitDate": "2026-09-15",
        }},
        {"lat": 35.0, "lng": 139.0},
    )
    assert score == 0.0
    assert matched == []
