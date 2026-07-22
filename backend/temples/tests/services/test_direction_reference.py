import pytest

from temples.services.direction_reference import attach_direction_references, build_direction_reference


PROFILE = {
    "visitDate": "2026-08-10",
    "luckyDirections": ["東", "北西"],
    "calculationMethod": "annual_monthly_kyusei_v1",
    "source": "calculated",
}
ORIGIN = {"lat": 35.0, "lng": 139.0}
SHRINE = {"latitude": 35.0, "longitude": 140.0}


def test_build_direction_reference_returns_shared_display_contract():
    assert build_direction_reference(
        direction_profile=PROFILE,
        user_origin=ORIGIN,
        shrine=SHRINE,
    ) == {
        "visit_date": "2026-08-10",
        "actual_direction": "東",
        "reference_directions": ["東", "北西"],
        "matched": True,
        "calculation_method": "annual_monthly_kyusei_v1",
        "note": "年盤と月盤による参考情報です。日盤は使用していません。",
    }


def test_build_direction_reference_returns_mismatch_without_suppressing_grounded_result():
    result = build_direction_reference(
        direction_profile={**PROFILE, "luckyDirections": ["西"]},
        user_origin=ORIGIN,
        shrine=SHRINE,
    )
    assert result is not None
    assert result["actual_direction"] == "東"
    assert result["matched"] is False


@pytest.mark.parametrize(
    ("profile", "origin", "shrine"),
    [
        (None, ORIGIN, SHRINE),
        ({**PROFILE, "source": "client"}, ORIGIN, SHRINE),
        ({**PROFILE, "calculationMethod": "annual_kyusei_v1"}, ORIGIN, SHRINE),
        ({**PROFILE, "visitDate": ""}, ORIGIN, SHRINE),
        ({**PROFILE, "luckyDirections": []}, ORIGIN, SHRINE),
        (PROFILE, None, SHRINE),
        (PROFILE, ORIGIN, {"latitude": 35.0}),
    ],
)
def test_build_direction_reference_omits_ungrounded_results(profile, origin, shrine):
    assert build_direction_reference(
        direction_profile=profile,
        user_origin=origin,
        shrine=shrine,
    ) is None


def test_attach_direction_references_isolates_a_candidate_failure(monkeypatch, caplog):
    recommendations = [
        {"name": "broken", "latitude": 35.0, "longitude": 140.0},
        {"name": "healthy", "latitude": 35.0, "longitude": 140.0},
    ]
    original = build_direction_reference

    def injected_failure(**kwargs):
        if kwargs["shrine"]["name"] == "broken":
            raise RuntimeError("secret-coordinate-35.0")
        return original(**kwargs)

    monkeypatch.setattr("temples.services.direction_reference.build_direction_reference", injected_failure)
    attach_direction_references(recommendations, direction_profile=PROFILE, user_origin=ORIGIN)

    assert "direction_reference" not in recommendations[0]
    assert recommendations[1]["direction_reference"]["matched"] is True
    assert "direction_reference_candidate_failed" in caplog.text
    assert "secret-coordinate" not in caplog.text
