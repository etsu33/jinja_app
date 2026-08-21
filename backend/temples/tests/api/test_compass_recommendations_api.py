from __future__ import annotations

import json

import pytest

from temples.models import Shrine

URL = "/api/compass/recommendations/"
ORIGIN = {"lat": 35.0, "lng": 135.0}
BIRTHDATE = "1984-05-15"
TARGET_DATE = "2026-09-15"


@pytest.fixture
def shrine_factory(db):
    def _factory(*, name: str, latitude: float, longitude: float, goriyaku: str = "") -> Shrine:
        shrine = Shrine(
            name_jp=name,
            address="東京都千代田区",
            latitude=latitude,
            longitude=longitude,
            goriyaku=goriyaku,
        )
        Shrine.objects.bulk_create([shrine])
        return Shrine.objects.get(pk=shrine.pk)

    return _factory


@pytest.mark.django_db
def test_valid_request_returns_recommendation_success(client, shrine_factory):
    # 2026-09-15 + 1984-05-15 birthdate resolves to 北西 (see test_kyusei_direction.py)
    shrine_factory(name="北西の神社", latitude=35.5, longitude=134.5, goriyaku="仕事運")

    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "birthdate": BIRTHDATE,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "recommendation_success"
    assert body["purpose"] == "career"
    assert body["direction_context"]["referenceDirections"] == ["北西"]
    names = [rec["name"] for rec in body["recommendations"]]
    assert "北西の神社" in names
    assert len(body["recommendation_instance_id"]) == 8
    assert all(
        rec["recommendation_instance_id"] == body["recommendation_instance_id"]
        for rec in body["recommendations"]
    )


@pytest.mark.django_db
def test_separate_compass_results_get_separate_recommendation_instances(client, shrine_factory):
    shrine_factory(name="北西の神社", latitude=35.5, longitude=134.5, goriyaku="仕事運")
    payload = json.dumps(
        {
            "purpose": "career",
            "origin": ORIGIN,
            "birthdate": BIRTHDATE,
            "target_date": TARGET_DATE,
        }
    )

    first = client.post(URL, data=payload, content_type="application/json").json()
    second = client.post(URL, data=payload, content_type="application/json").json()

    assert first["recommendation_instance_id"] != second["recommendation_instance_id"]


@pytest.mark.django_db
def test_invalid_purpose_returns_400(client):
    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "not_a_real_tag",
                "origin": ORIGIN,
                "birthdate": BIRTHDATE,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 400
    assert r.json()["state"] == "invalid_purpose"


@pytest.mark.django_db
def test_missing_birthdate_returns_direction_filter_unavailable(client):
    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "direction_filter_unavailable"
    assert body["direction_context"] is None
    assert body["recommendations"] == []


@pytest.mark.django_db
def test_no_common_direction_returns_dedicated_state_not_unavailable(client):
    # Synthetic birthdate (not a real user's). For target_date 2026-11-15
    # this honmei star's annual/monthly lucky directions share nothing
    # (empty intersection) AND monthly-only guidance is also empty -- the
    # narrowed no_common_direction residual case under Monthly Fallback
    # (Product Contract Section 2.2-4, #2508 Option C), distinct from
    # test_monthly_fallback_returns_recommendation_flow_state below where
    # the intersection is empty but monthly-only guidance is not.
    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "birthdate": "1976-06-15",
                "target_date": "2026-11-15",
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "no_common_direction"
    assert body["state"] != "direction_filter_unavailable"
    assert body["direction_context"] is None
    assert body["recommendations"] == []


@pytest.mark.django_db
def test_monthly_fallback_returns_recommendation_flow_state(client, shrine_factory):
    """Product Contract Section 2.2 / Runtime Contract Section 5-1 (#2508
    Option C): synthetic birthdate (not a real user's) where, for
    target_date 2026-08-20, the annual/monthly intersection is empty but
    monthly-only guidance (["南東"]) is available. This must reach the
    normal recommendation flow -- not no_common_direction, not
    direction_filter_unavailable -- with calculationMethod="monthly_kyusei_v1"
    (never "annual_monthly_kyusei_v1", which would misrepresent this as
    annual/monthly agreement)."""
    shrine_factory(name="南東の神社", latitude=34.5, longitude=136.0, goriyaku="仕事運")

    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "birthdate": "1975-06-15",
                "target_date": "2026-08-20",
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "recommendation_success"
    assert body["state"] != "no_common_direction"
    assert body["direction_context"]["referenceDirections"] == ["南東"]
    assert body["direction_context"]["calculationMethod"] == "monthly_kyusei_v1"
    names = [rec["name"] for rec in body["recommendations"]]
    assert "南東の神社" in names


@pytest.mark.django_db
def test_missing_origin_returns_direction_filter_unavailable(client):
    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "birthdate": BIRTHDATE,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    assert r.json()["state"] == "direction_filter_unavailable"


@pytest.mark.django_db
def test_no_shrines_in_sector_returns_direction_zero_candidates(client, shrine_factory):
    # South of origin -- outside the 北西 (northwest) authorized sector.
    shrine_factory(name="南の神社", latitude=34.0, longitude=135.0)

    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "birthdate": BIRTHDATE,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    assert r.status_code == 200
    body = r.json()
    assert body["state"] == "direction_zero_candidates"
    assert body["recommendations"] == []


@pytest.mark.django_db
def test_missing_purpose_returns_400(client):
    r = client.post(
        URL,
        data=json.dumps({"origin": ORIGIN, "birthdate": BIRTHDATE, "target_date": TARGET_DATE}),
        content_type="application/json",
    )

    assert r.status_code == 400
    assert r.json()["state"] == "invalid_purpose"


@pytest.mark.django_db
def test_response_never_leaks_internal_direction_fields(client, shrine_factory):
    shrine_factory(name="北西の神社", latitude=35.5, longitude=134.5, goriyaku="仕事運")

    r = client.post(
        URL,
        data=json.dumps(
            {
                "purpose": "career",
                "origin": ORIGIN,
                "birthdate": BIRTHDATE,
                "target_date": TARGET_DATE,
            }
        ),
        content_type="application/json",
    )

    direction_context = r.json()["direction_context"]
    assert "excludedDirections" not in direction_context
    assert "luckyDirection" not in direction_context
