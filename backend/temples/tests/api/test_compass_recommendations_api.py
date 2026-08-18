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
