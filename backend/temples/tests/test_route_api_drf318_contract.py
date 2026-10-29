"""H-9（DRF 3.17.2 → 3.18.2）: pins the POST /api/route/ contract after the upgrade.

- ListSerializer errors are index-keyed dicts（DRF 3.18 default）, not positional lists;
- non-finite floats（NaN / Infinity / -Infinity）are rejected with 400;
- valid requests keep the existing 200 response shape.
"""

import json

import pytest
from rest_framework.test import APIClient

ENDPOINTS = ["/api/route/", "/api/routes/"]
ORIGIN = {"lat": 35.68, "lng": 139.76}
DEST = {"lat": 35.67, "lng": 139.71}


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.parametrize("url", ENDPOINTS)
def test_invalid_destination_errors_are_index_keyed(api_client, url):
    payload = {
        "mode": "walking",
        "origin": ORIGIN,
        "destinations": [DEST, {"lat": "x", "lng": 139.71}, DEST, {"lat": 35.0}],
    }
    res = api_client.post(url, data=payload, format="json")

    assert res.status_code == 400
    errors = res.json()["destinations"]
    assert isinstance(errors, dict)
    assert set(errors) == {"1", "3"}  # valid items are omitted, not padded with {}
    assert set(errors["1"]) == {"lat"}
    assert set(errors["3"]) == {"lng"}


@pytest.mark.parametrize("url", ENDPOINTS)
def test_empty_destinations_error_shape_is_unchanged(api_client, url):
    res = api_client.post(
        url, data={"mode": "walking", "origin": ORIGIN, "destinations": []}, format="json"
    )

    assert res.status_code == 400
    assert set(res.json()["destinations"]) == {"non_field_errors"}


@pytest.mark.parametrize("url", ENDPOINTS)
@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
@pytest.mark.parametrize(
    "location,key",
    [("origin", "lat"), ("origin", "lng"), ("destinations", "lat"), ("destinations", "lng")],
)
def test_non_finite_coordinates_are_rejected(api_client, url, value, location, key):
    origin = dict(ORIGIN)
    dest = dict(DEST)
    (origin if location == "origin" else dest)[key] = value
    payload = {"mode": "walking", "origin": origin, "destinations": [dest]}

    res = api_client.post(url, data=payload, format="json")

    assert res.status_code == 400
    body = res.json()
    if location == "origin":
        assert key in body["origin"]
    else:
        assert key in body["destinations"]["0"]


@pytest.mark.parametrize("url", ENDPOINTS)
@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_json_literals_are_rejected(api_client, url, token):
    body = '{"mode": "walking", "origin": {"lat": %s, "lng": 139.76}, "destinations": [%s]}' % (
        token,
        json.dumps(DEST),
    )

    res = api_client.post(url, data=body, content_type="application/json")

    assert res.status_code == 400


@pytest.mark.parametrize("url", ENDPOINTS)
def test_valid_request_keeps_response_shape(api_client, url):
    payload = {
        "mode": "walking",
        "origin": ORIGIN,
        "destinations": [DEST, {"lat": 35.66, "lng": 139.70}],
    }

    res = api_client.post(url, data=payload, format="json")

    assert res.status_code == 200, res.content
    body = res.json()
    assert set(body) == {
        "mode",
        "legs",
        "distance_m_total",
        "duration_s_total",
        "provider",
        "cached",
    }
    assert body["mode"] == "walking"
    assert len(body["legs"]) == 2
    for leg in body["legs"]:
        assert set(leg) == {"from_", "to", "distance_m", "duration_s", "geometry"}
        assert all(len(pt) == 2 for pt in leg["geometry"])
    assert body["legs"][0]["to"] == DEST
    assert body["distance_m_total"] == sum(leg["distance_m"] for leg in body["legs"])
    assert body["duration_s_total"] == sum(leg["duration_s"] for leg in body["legs"])
