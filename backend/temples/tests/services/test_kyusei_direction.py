from datetime import date

from temples.domain.kyusei import annual_lucky_directions


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
