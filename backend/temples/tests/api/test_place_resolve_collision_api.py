"""F-6B: collision 時に両 endpoint が 409 を返すことの HTTP 回帰。

    ON_COLLISION:
      CREATE_NEW_SHRINE         = NO
      AUTO_BIND_EXISTING_SHRINE = NO
      HTTP_STATUS               = 409

候補 Shrine の id は body に載せない
（AUTO_BIND_ON_SINGLE_CANDIDATE = PROHIBITED）。

docs/audit/place-id-shadow-identity-hardening.md §14
"""
from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from temples.models import PlaceRef, Shrine

pytestmark = pytest.mark.django_db

NAME = "給田六所神社"
ADDR = "日本、〒157-0064 東京都世田谷区給田１丁目３−７"
LAT = 35.662443
LNG = 139.5920237
HISTORICAL_PLACE_ID = "ChIJl-MEepfxGGAR1Eo44p__GaE"


def _place_ref(place_id, **kwargs):
    base = {"name": NAME, "address": ADDR, "latitude": LAT, "longitude": LNG}
    base.update(kwargs)
    return PlaceRef.objects.create(place_id=place_id, **base)


def _shrine(**kwargs):
    base = {"name_jp": NAME, "address": ADDR, "latitude": LAT, "longitude": LNG}
    base.update(kwargs)
    return Shrine.objects.create(**base)


class TestPlacesResolveEndpoint:
    def test_collision_returns_409_and_creates_no_shrine(self):
        existing = _shrine()
        _place_ref("PID_API_COLLIDE")
        before = Shrine.objects.count()

        res = APIClient().post(
            "/api/places/resolve/", {"place_id": "PID_API_COLLIDE"}, format="json"
        )

        assert res.status_code == 409
        assert res.json()["code"] == "shrine_collision_review_required"
        assert Shrine.objects.count() == before
        existing.refresh_from_db()
        assert existing.place_ref_id is None

    def test_409_body_does_not_leak_candidate_shrine_ids(self):
        existing = _shrine()
        _place_ref("PID_API_NOLEAK")

        res = APIClient().post(
            "/api/places/resolve/", {"place_id": "PID_API_NOLEAK"}, format="json"
        )

        body = res.json()
        assert set(body) == {"detail", "code"}
        assert str(existing.id) not in str(body)

    def test_historical_place_id_returns_409_instead_of_recreating_a_shadow(self):
        """F-6A §2.2 が証明した shadow 再発経路が閉じていること。"""
        primary = _shrine()
        _place_ref(HISTORICAL_PLACE_ID)
        before = Shrine.objects.count()

        res = APIClient().post(
            "/api/places/resolve/", {"place_id": HISTORICAL_PLACE_ID}, format="json"
        )

        assert res.status_code == 409
        assert Shrine.objects.count() == before
        primary.refresh_from_db()
        assert primary.place_ref_id is None

    def test_no_collision_still_returns_200_with_the_unchanged_shape(self):
        _place_ref("PID_API_OK", name="新規神社", address="東京都新規区1-1")

        res = APIClient().post(
            "/api/places/resolve/", {"place_id": "PID_API_OK"}, format="json"
        )

        assert res.status_code == 200
        body = res.json()
        assert set(body) == {"id", "shrine_id", "place_id", "candidate_id"}
        assert body["shrine_id"] == body["id"]
        assert body["place_id"] == "PID_API_OK"

    def test_already_linked_still_returns_200(self):
        pr = _place_ref("PID_API_LINKED")
        existing = _shrine(place_ref=pr)

        res = APIClient().post(
            "/api/places/resolve/", {"place_id": "PID_API_LINKED"}, format="json"
        )

        assert res.status_code == 200
        assert res.json()["shrine_id"] == existing.id


class TestShrineIngestEndpoint:
    def test_collision_returns_409_and_creates_no_shrine(self):
        _shrine()
        _place_ref("PID_INGEST_COLLIDE")
        before = Shrine.objects.count()

        res = APIClient().post(
            "/api/shrines/ingest/", {"place_id": "PID_INGEST_COLLIDE"}, format="json"
        )

        assert res.status_code == 409
        assert res.json()["code"] == "shrine_collision_review_required"
        assert Shrine.objects.count() == before

    def test_no_collision_still_returns_200(self):
        _place_ref("PID_INGEST_OK", name="新規神社", address="東京都新規区1-1")

        res = APIClient().post(
            "/api/shrines/ingest/", {"place_id": "PID_INGEST_OK"}, format="json"
        )

        assert res.status_code == 200
        assert res.json()["place_id"] == "PID_INGEST_OK"
