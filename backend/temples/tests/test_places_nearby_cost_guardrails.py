# backend/temples/tests/test_places_nearby_cost_guardrails.py
"""
Google Places Cost Guardrails の回帰テスト。

観点:
- New API を呼ぶ条件（PLACES_API_NEW / shrine_mode）
- New → Legacy fallback を一時障害だけに限定していること
- Legacy を canonical 1 call に整理したこと（upstream 回数）
- shrine_mode 判定（default / keyword / type-only）
- server-side kill switch
- New FieldMask に高 SKU field が含まれないこと
- Nearby response contract
"""
from unittest.mock import patch

import pytest
import requests
import responses
from django.core.cache import cache
from rest_framework.test import APIClient

from temples.services import google_places as GP


LEGACY_NEARBY = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
NEW_SEARCH_TEXT = "https://places.googleapis.com/v1/places:searchText"

NEARBY_URL = "/api/places/nearby/"


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def _dummy_api_key(monkeypatch):
    """upstream を実際に叩かせずに client を組み立てられるようにする。"""
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "DUMMY_KEY")
    monkeypatch.setattr(GP, "API_KEY", "DUMMY_KEY", raising=False)
    monkeypatch.setattr(GP, "_client_singleton", None, raising=False)
    yield
    GP._client_singleton = None


@pytest.fixture(autouse=True)
def _places_api_new_off(monkeypatch):
    monkeypatch.delenv("PLACES_API_NEW", raising=False)


def _legacy_calls():
    return [c for c in responses.calls if c.request.url.startswith(LEGACY_NEARBY)]


def _new_calls():
    return [c for c in responses.calls if c.request.url.startswith(NEW_SEARCH_TEXT)]


def _legacy_body(status="OK"):
    return {
        "status": status,
        "results": [
            {
                "place_id": "PID-1",
                "name": "テスト神社",
                "formatted_address": "東京都テスト区1-1",
                "geometry": {"location": {"lat": 35.0, "lng": 139.0}},
                "types": ["shinto_shrine", "point_of_interest"],
                "rating": 4.2,
                "user_ratings_total": 12,
            }
        ]
        if status == "OK"
        else [],
    }


def _new_body():
    return {
        "places": [
            {
                "id": "PID-NEW-1",
                "displayName": {"text": "テスト神社"},
                "formattedAddress": "東京都テスト区1-1",
                "location": {"latitude": 35.0, "longitude": 139.0},
                "types": ["shinto_shrine", "point_of_interest"],
            }
        ]
    }


# ---------------------------------------------------------------
# New API を呼ぶ条件
# ---------------------------------------------------------------
@pytest.mark.django_db
@responses.activate
def test_places_api_new_unset_does_not_call_new_api():
    responses.add(responses.GET, LEGACY_NEARBY, json=_legacy_body(), status=200)

    r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0})

    assert r.status_code == 200, r.content
    assert len(_new_calls()) == 0
    assert len(_legacy_calls()) == 1


@pytest.mark.django_db
@responses.activate
def test_new_success_does_not_call_legacy(monkeypatch):
    monkeypatch.setenv("PLACES_API_NEW", "1")
    responses.add(responses.POST, NEW_SEARCH_TEXT, json=_new_body(), status=200)
    responses.add(responses.GET, LEGACY_NEARBY, json=_legacy_body(), status=200)

    r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0})

    assert r.status_code == 200, r.content
    assert len(_new_calls()) == 1
    assert len(_legacy_calls()) == 0


# ---------------------------------------------------------------
# New → Legacy fallback は一時障害のみ
# ---------------------------------------------------------------
@pytest.mark.django_db
@responses.activate
@pytest.mark.parametrize("upstream_status", [500, 502, 503])
def test_new_transient_error_falls_back_to_legacy_once(monkeypatch, upstream_status):
    monkeypatch.setenv("PLACES_API_NEW", "1")
    responses.add(responses.POST, NEW_SEARCH_TEXT, json={}, status=upstream_status)
    responses.add(responses.GET, LEGACY_NEARBY, json=_legacy_body(), status=200)

    r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0})

    assert r.status_code == 200, r.content
    assert len(_new_calls()) == 1
    assert len(_legacy_calls()) == 1


@pytest.mark.django_db
@responses.activate
def test_new_429_does_not_fall_back_to_legacy(monkeypatch):
    """
    429 は Google Cloud quota / rate limit がコスト上限として効いている合図。
    legacy へ fallback すると別 SKU で通信を継続し quota による停止を
    迂回してしまうため、fail closed（controlled failure）にする。
    """
    monkeypatch.setenv("PLACES_API_NEW", "1")
    responses.add(responses.POST, NEW_SEARCH_TEXT, json={}, status=429)
    responses.add(responses.GET, LEGACY_NEARBY, json=_legacy_body(), status=200)

    r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0})

    assert len(_new_calls()) == 1
    assert len(_legacy_calls()) == 0
    # controlled failure: 500 ではなく 502、かつ JSON の detail を返す
    assert r.status_code == 502, r.content
    assert "detail" in r.json()


@pytest.mark.django_db
@responses.activate
@pytest.mark.parametrize(
    "exc", [requests.exceptions.Timeout(), requests.exceptions.ConnectionError()]
)
def test_new_network_error_falls_back_to_legacy_once(monkeypatch, exc):
    monkeypatch.setenv("PLACES_API_NEW", "1")
    responses.add(responses.POST, NEW_SEARCH_TEXT, body=exc)
    responses.add(responses.GET, LEGACY_NEARBY, json=_legacy_body(), status=200)

    r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0})

    assert r.status_code == 200, r.content
    assert len(_new_calls()) == 1
    assert len(_legacy_calls()) == 1


@pytest.mark.django_db
@responses.activate
@pytest.mark.parametrize("upstream_status", [400, 401, 403])
def test_new_deterministic_error_does_not_fall_back(monkeypatch, upstream_status):
    monkeypatch.setenv("PLACES_API_NEW", "1")
    responses.add(responses.POST, NEW_SEARCH_TEXT, json={}, status=upstream_status)
    responses.add(responses.GET, LEGACY_NEARBY, json=_legacy_body(), status=200)

    r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0})

    assert r.status_code == 502, r.content
    assert len(_new_calls()) == 1
    assert len(_legacy_calls()) == 0


@pytest.mark.django_db
@responses.activate
def test_new_missing_api_key_does_not_fall_back(monkeypatch, settings):
    monkeypatch.setenv("PLACES_API_NEW", "1")
    settings.GOOGLE_MAPS_API_KEY = ""
    settings.GOOGLE_PLACES_API_KEY = ""
    for name in (
        "GOOGLE_MAPS_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_PLACES_API_KEY",
        "MAPS_API_KEY",
        "PLACES_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    responses.add(responses.GET, LEGACY_NEARBY, json=_legacy_body(), status=200)

    r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0})

    assert r.status_code == 502, r.content
    assert len(_new_calls()) == 0
    assert len(_legacy_calls()) == 0


# ---------------------------------------------------------------
# Legacy attempts は canonical 1 call
# ---------------------------------------------------------------
@pytest.mark.django_db
@responses.activate
def test_legacy_success_calls_upstream_once():
    responses.add(responses.GET, LEGACY_NEARBY, json=_legacy_body(), status=200)

    r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0})

    assert r.status_code == 200, r.content
    assert len(_legacy_calls()) == 1


@pytest.mark.django_db
@responses.activate
def test_legacy_zero_results_calls_upstream_once():
    responses.add(
        responses.GET, LEGACY_NEARBY, json=_legacy_body(status="ZERO_RESULTS"), status=200
    )

    r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0})

    assert r.status_code == 200, r.content
    assert r.json()["results"] == []
    assert len(_legacy_calls()) == 1


@pytest.mark.django_db
@responses.activate
def test_legacy_invalid_request_calls_upstream_at_most_twice(monkeypatch):
    monkeypatch.setattr(GP.time, "sleep", lambda *_a, **_kw: None)
    responses.add(responses.GET, LEGACY_NEARBY, json={"status": "INVALID_REQUEST"}, status=200)
    responses.add(responses.GET, LEGACY_NEARBY, json={"status": "INVALID_REQUEST"}, status=200)
    responses.add(responses.GET, LEGACY_NEARBY, json=_legacy_body(), status=200)

    r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0})

    assert r.status_code == 200, r.content
    assert len(_legacy_calls()) == 2


# ---------------------------------------------------------------
# shrine_mode 判定
# ---------------------------------------------------------------
@pytest.mark.django_db
def test_default_request_keeps_shrine_mode():
    with patch("temples.services.google_places.nearby_search") as mock_call:
        mock_call.return_value = {"status": "OK", "results": []}
        r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0})

    assert r.status_code == 200, r.content
    assert mock_call.call_count == 1
    kwargs = mock_call.call_args.kwargs
    assert kwargs["keyword"] == "神社"
    assert "type_" not in kwargs


@pytest.mark.django_db
def test_type_only_request_keeps_type_and_is_not_shrine_mode(monkeypatch):
    monkeypatch.setenv("PLACES_API_NEW", "1")

    with patch("temples.services.google_places.nearby_search") as mock_call, patch(
        "temples.services.google_places.nearby_search_new"
    ) as mock_new:
        mock_call.return_value = {
            "status": "OK",
            "results": [
                {"place_id": "P1", "name": "テスト公園", "types": ["park"], "lat": 35.0, "lng": 139.0},
                {"place_id": "P2", "name": "テスト神社", "types": ["shinto_shrine"], "lat": 35.0, "lng": 139.0},
            ],
        }
        r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0, "type": "park"})

    assert r.status_code == 200, r.content
    # type だけの指定では New(shrine) 経路に入らない
    assert mock_new.call_count == 0
    # type は None にせず upstream へ渡す
    kwargs = mock_call.call_args.kwargs
    assert kwargs["type_"] == "park"
    assert "keyword" not in kwargs
    # shrine filter ではなく type filter が効く
    assert [x["place_id"] for x in r.json()["results"]] == ["P1"]


@pytest.mark.django_db
def test_explicit_shrine_keyword_is_shrine_mode(monkeypatch):
    monkeypatch.setenv("PLACES_API_NEW", "1")

    with patch("temples.services.google_places.nearby_search_new") as mock_new:
        mock_new.return_value = {"status": "OK", "results": []}
        r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0, "keyword": "神社"})

    assert r.status_code == 200, r.content
    assert mock_new.call_count == 1


@pytest.mark.django_db
def test_non_shrine_keyword_is_not_shrine_mode(monkeypatch):
    monkeypatch.setenv("PLACES_API_NEW", "1")

    with patch("temples.services.google_places.nearby_search") as mock_call, patch(
        "temples.services.google_places.nearby_search_new"
    ) as mock_new:
        mock_call.return_value = {"status": "OK", "results": []}
        r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0, "keyword": "寺"})

    assert r.status_code == 200, r.content
    assert mock_new.call_count == 0
    assert mock_call.call_args.kwargs["keyword"] == "寺"


# ---------------------------------------------------------------
# kill switch
# ---------------------------------------------------------------
@pytest.mark.django_db
@responses.activate
def test_kill_switch_off_makes_zero_upstream_requests(settings):
    settings.GOOGLE_PLACES_ENABLED = False

    r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0})

    assert r.status_code == 503, r.content
    assert r.json()["results"] == []
    assert len(responses.calls) == 0


@responses.activate
def test_kill_switch_off_blocks_service_layer(settings):
    settings.GOOGLE_PLACES_ENABLED = False

    with pytest.raises(GP.GooglePlacesDisabled):
        GP.GooglePlacesClient(api_key="DUMMY").nearby_search(location="35,139", radius=100)

    with pytest.raises(GP.GooglePlacesDisabled):
        GP.nearby_search_new(lat=35.0, lng=139.0, radius=100)

    with pytest.raises(GP.GooglePlacesDisabled):
        GP.textsearch(query="神社")

    assert len(responses.calls) == 0


def test_kill_switch_default_is_enabled(settings, monkeypatch):
    monkeypatch.delenv("GOOGLE_PLACES_ENABLED", raising=False)
    if hasattr(settings, "GOOGLE_PLACES_ENABLED"):
        del settings.GOOGLE_PLACES_ENABLED
    assert GP.places_upstream_enabled() is True


# ---------------------------------------------------------------
# New FieldMask
# ---------------------------------------------------------------
@responses.activate
def test_new_field_mask_excludes_high_sku_fields():
    responses.add(responses.POST, NEW_SEARCH_TEXT, json=_new_body(), status=200)

    GP.nearby_search_new(lat=35.0, lng=139.0, radius=1000)

    field_mask = responses.calls[0].request.headers["X-Goog-FieldMask"]
    fields = set(field_mask.split(","))
    assert fields == {
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.location",
        "places.types",
    }
    for banned in (
        "places.rating",
        "places.userRatingCount",
        "places.currentOpeningHours",
        "places.photos",
    ):
        assert banned not in field_mask


# ---------------------------------------------------------------
# response contract
# ---------------------------------------------------------------
CONTRACT_KEYS = {
    "place_id",
    "name",
    "address",
    "formatted_address",
    "lat",
    "lng",
    "types",
    "rating",
    "user_ratings_total",
    "photo_reference",
    "open_now",
    "icon",
    "distance_m",
}


@pytest.mark.django_db
@responses.activate
def test_legacy_nearby_response_contract_is_preserved():
    responses.add(responses.GET, LEGACY_NEARBY, json=_legacy_body(), status=200)

    r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0})

    assert r.status_code == 200, r.content
    body = r.json()
    assert body["status"] == "OK"
    item = body["results"][0]
    assert CONTRACT_KEYS.issubset(item.keys())
    assert item["place_id"] == "PID-1"
    assert item["name"] == "テスト神社"
    assert item["lat"] == 35.0
    assert item["lng"] == 139.0


@pytest.mark.django_db
@responses.activate
def test_new_nearby_response_contract_is_preserved(monkeypatch):
    monkeypatch.setenv("PLACES_API_NEW", "1")
    responses.add(responses.POST, NEW_SEARCH_TEXT, json=_new_body(), status=200)

    r = APIClient().get(NEARBY_URL, {"lat": 35.0, "lng": 139.0})

    assert r.status_code == 200, r.content
    item = r.json()["results"][0]
    assert CONTRACT_KEYS.issubset(item.keys())
    assert item["place_id"] == "PID-NEW-1"
    assert item["name"] == "テスト神社"
    assert item["address"] == "東京都テスト区1-1"
    assert item["lat"] == 35.0
    assert item["lng"] == 139.0
    # FieldMask から外した field は null で互換維持
    assert item["rating"] is None
    assert item["user_ratings_total"] is None
    assert item["photo_reference"] is None
    assert item["open_now"] is None
