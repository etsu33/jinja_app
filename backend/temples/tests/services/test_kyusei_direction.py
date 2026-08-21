from datetime import date

from temples.domain.kyusei import (
    annual_lucky_directions,
    monthly_lucky_directions,
    planned_visit_lucky_directions,
)
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


def test_monthly_lucky_directions_matches_current_inline_semantics():
    # #2505's audit contract: monthly_lucky_directions() is annual_lucky_directions()'s
    # monthly sibling, extracted verbatim from planned_visit_lucky_directions()'s
    # former inline block. This fixture uses the same birthdate/visit_date as
    # test_planned_visit_direction_intersects_annual_and_monthly_plans() above.
    assert monthly_lucky_directions("1984-05-15", "2026-09-15") == {
        "luckyDirection": "北西",
        "luckyDirections": ["北西"],
        "targetYear": 2026,
        "solarMonthIndex": 8,
        "visitDate": "2026-09-15",
        "calculationMethod": "monthly_kyusei_v1",
        "excludedDirections": ["北", "北東", "東", "南", "南西"],
        "source": "calculated",
    }


def test_monthly_lucky_directions_uses_solar_month_boundary():
    before = monthly_lucky_directions("1984-05-15", "2026-08-07")
    after = monthly_lucky_directions("1984-05-15", "2026-08-08")
    assert before["solarMonthIndex"] == 6
    assert after["solarMonthIndex"] == 7


def test_monthly_lucky_directions_empty_case():
    result = monthly_lucky_directions("1975-06-15", "2022-11-20")
    assert result["luckyDirections"] == []
    assert result["luckyDirection"] is None


def test_monthly_lucky_directions_non_empty_case():
    result = monthly_lucky_directions("1975-06-15", "2022-02-20")
    assert result["luckyDirections"] == ["南東"]
    assert result["luckyDirection"] == "南東"


def test_monthly_lucky_directions_invalid_birthdate_returns_none():
    assert monthly_lucky_directions(None, "2026-09-15") is None
    assert monthly_lucky_directions("not-a-date", "2026-09-15") is None


def test_monthly_lucky_directions_invalid_visit_date_returns_none():
    assert monthly_lucky_directions("1984-05-15", "not-a-date") is None
    assert monthly_lucky_directions("1984-05-15", None) is None


def test_monthly_lucky_directions_all_nine_honmei_and_multi_year_intersection_equivalence():
    """Behavior-preservation proof for the kyusei.py extraction (#2505/#2506):
    for every (honmei star, solar-month bucket, year) combination in the same
    9x12x9 deterministic grid #2497/#2503/#2504 established, intersecting
    annual_lucky_directions() and monthly_lucky_directions() independently
    reproduces planned_visit_lucky_directions()'s own luckyDirections exactly
    -- i.e. the extraction introduced zero calculation drift.
    """
    birthdates_by_num = {
        1: "1981-06-15",
        2: "1980-06-15",
        3: "1979-06-15",
        4: "1978-06-15",
        5: "1977-06-15",
        6: "1976-06-15",
        7: "1975-06-15",
        8: "1983-06-15",
        9: "1982-06-15",
    }
    solar_month_buckets = {
        0: (2, 20),
        1: (3, 20),
        2: (4, 20),
        3: (5, 20),
        4: (6, 20),
        5: (7, 20),
        6: (8, 20),
        7: (9, 20),
        8: (10, 20),
        9: (11, 20),
        10: (12, 20),
        11: (1, 20),
    }
    checked = 0
    for birthdate in birthdates_by_num.values():
        for month, day in solar_month_buckets.values():
            for year in range(2022, 2031):
                visit_date = f"{year:04d}-{month:02d}-{day:02d}"
                annual = annual_lucky_directions(birthdate, today=date(year, month, day))
                monthly = monthly_lucky_directions(birthdate, visit_date)
                planned = planned_visit_lucky_directions(birthdate, visit_date)
                assert annual is not None
                assert monthly is not None
                assert planned is not None
                expected = [d for d in annual["luckyDirections"] if d in monthly["luckyDirections"]]
                assert planned["luckyDirections"] == expected
                checked += 1
    assert checked == 972


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


def test_direction_signal_failure_keeps_normal_candidate_without_direction_score(monkeypatch, caplog):
    rec = {"name": "private shrine", "reason": "normal reason", "latitude": 35.0, "longitude": 140.0}
    monkeypatch.setattr(
        "temples.services.direction_reference.build_direction_reference",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("private consultation")),
    )

    assert _score_direction_signal(rec, {"direction_profile": {}}, {"lat": 35.0, "lng": 139.0}) == (0.0, [])
    assert rec["reason"] == "normal reason"
    assert "direction_reference" not in rec
    assert "direction_score_candidate_failed" in caplog.text
    assert "private consultation" not in caplog.text
