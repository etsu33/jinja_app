"""WS-13: Nearby GET endpoints use the WS-04 identity through DRF throttling.

- One shared APIView for `/api/places/nearby/`, `/api/places/nearby_search/` and `/api/places/nearby-search/`,
  with `throttle_scope = "places-nearby"` on the view class.
- The default DRF throttle classes (WS-04 ScopedRateThrottle / AnonRateThrottle / UserRateThrottle) apply.
- One request consumes one scope slot; a 429 makes zero Google calls.

Isolation: each test gets its own LocMem cache location and sets its own rates. Anonymous identities are
deterministic `remote:<REMOTE_ADDR>` unless a valid BFF attestation is attached.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest
from django.core.cache import cache
from django.urls import resolve
from rest_framework.test import APIClient

from shrine_project.throttling import sign_client_identity
from temples.api.views.search import (
    PLACES_NEARBY_THROTTLE_SCOPE,
    PlacesNearbySearchLegacyView,
    PlacesNearbySearchView,
)
from temples.services import google_places as GP

pytestmark = pytest.mark.django_db

CANONICAL = "/api/places/nearby/"
LEGACY_UNDERSCORE = "/api/places/nearby_search/"
LEGACY_HYPHEN = "/api/places/nearby-search/"
ALL_URLS = (CANONICAL, LEGACY_UNDERSCORE, LEGACY_HYPHEN)
PARAMS = {"lat": 35.0, "lng": 139.0, "radius": 1000}
ATTEST_SECRET = "n" * 48
BACKEND_DIR = Path(__file__).resolve().parents[3]

UPSTREAM_RESULT = {
    "status": "OK",
    "results": [
        {
            "place_id": "PID_NEARBY_1",
            "name": "テスト神社",
            "address": "東京都",
            "lat": 35.001,
            "lng": 139.001,
            "types": ["place_of_worship", "establishment"],
        }
    ],
}


@pytest.fixture(autouse=True)
def isolated(settings, monkeypatch):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": f"places-nearby-throttle-{uuid.uuid4().hex}",
        }
    }
    rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    rates[PLACES_NEARBY_THROTTLE_SCOPE] = "3/min"
    rates["anon"] = "1000/min"
    rates["user"] = "1000/min"
    settings.GOOGLE_PLACES_ENABLED = True
    settings.THROTTLE_TRUSTED_EDGE = ""
    settings.THROTTLE_CLIENT_IDENTITY_SECRET = ""
    monkeypatch.delenv("PLACES_API_NEW", raising=False)
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def google(monkeypatch):
    """Counts legacy Nearby calls (the only upstream used when PLACES_API_NEW is unset)."""
    calls: list[dict] = []

    def fake_nearby_search(**kwargs):
        calls.append(kwargs)
        return json.loads(json.dumps(UPSTREAM_RESULT))

    def fail_new(**_kwargs):  # pragma: no cover - must not be reached
        raise AssertionError("Places API (New) must not be called in these tests")

    monkeypatch.setattr(GP, "nearby_search", fake_nearby_search)
    monkeypatch.setattr(GP, "nearby_search_new", fail_new)
    return calls


def _client(ip: str = "198.51.100.40") -> APIClient:
    return APIClient(REMOTE_ADDR=ip)


def _attested(
    ip: str, *, path: str = CANONICAL, secret: str = ATTEST_SECRET, remote: str = "10.0.1.5"
):
    ts = str(int(time.time()))
    sig = sign_client_identity(secret.encode("utf-8"), ts, "GET", path, ip)
    return APIClient(
        REMOTE_ADDR=remote,
        HTTP_X_KM_CLIENT_IP=ip,
        HTTP_X_KM_CLIENT_TS=ts,
        HTTP_X_KM_CLIENT_SIG=sig,
    )


# --------------------------------------------------------------------------- #
# view wiring
# --------------------------------------------------------------------------- #


def test_actual_drf_view_classes_carry_the_scope():
    assert PLACES_NEARBY_THROTTLE_SCOPE == "places-nearby"
    for url, expected in (
        (CANONICAL, PlacesNearbySearchView),
        (LEGACY_UNDERSCORE, PlacesNearbySearchLegacyView),
        (LEGACY_HYPHEN, PlacesNearbySearchLegacyView),
    ):
        view_cls = resolve(url).func.cls
        assert view_cls is expected
        assert issubclass(view_cls, PlacesNearbySearchView)
        assert view_cls.throttle_scope == "places-nearby"
        # global WS-04 throttle classes, not a per-view override
        assert [
            type(t).__module__ + "." + type(t).__name__ for t in view_cls().get_throttles()
        ] == [
            "shrine_project.throttling.ScopedRateThrottle",
            "shrine_project.throttling.AnonRateThrottle",
            "shrine_project.throttling.UserRateThrottle",
        ]


def test_manual_remote_addr_throttle_is_gone():
    from temples.api.views import search

    assert not hasattr(search, "_apply_places_nearby_throttle")
    assert not hasattr(search, "_nearby_ident")


# --------------------------------------------------------------------------- #
# bucket behaviour
# --------------------------------------------------------------------------- #


def test_same_client_is_throttled_at_the_configured_limit_with_zero_google_calls_on_429(google):
    client = _client()
    for _ in range(3):
        assert client.get(CANONICAL, PARAMS).status_code == 200
    assert len(google) == 3

    res = client.get(CANONICAL, PARAMS)

    assert res.status_code == 429
    assert "Retry-After" in res
    assert len(google) == 3  # rejected request made no upstream call


@pytest.mark.parametrize("order", [ALL_URLS, tuple(reversed(ALL_URLS))])
def test_all_three_urls_share_one_bucket(order, google):
    client = _client()
    for url in order:
        assert client.get(url, PARAMS).status_code == 200, url

    for url in ALL_URLS:
        assert client.get(url, PARAMS).status_code == 429, url
    assert len(google) == 3


@pytest.mark.parametrize("url", [LEGACY_UNDERSCORE, LEGACY_HYPHEN])
def test_legacy_request_consumes_exactly_one_slot(url, google):
    """With limit 3, nested dispatch (2 slots per request) would reject the 2nd request."""
    client = _client()
    for i in range(3):
        assert client.get(url, PARAMS).status_code == 200, i
    assert client.get(url, PARAMS).status_code == 429
    assert len(google) == 3


def test_different_clients_have_independent_buckets(google):
    first, second = _client("198.51.100.41"), _client("198.51.100.42")
    for _ in range(3):
        assert first.get(CANONICAL, PARAMS).status_code == 200
    assert first.get(CANONICAL, PARAMS).status_code == 429
    assert second.get(CANONICAL, PARAMS).status_code == 200


def test_valid_ws04_attestations_get_independent_buckets_behind_one_proxy(settings, google):
    settings.THROTTLE_CLIENT_IDENTITY_SECRET = ATTEST_SECRET
    for _ in range(3):
        assert _attested("203.0.113.11").get(CANONICAL, PARAMS).status_code == 200
    assert _attested("203.0.113.11").get(CANONICAL, PARAMS).status_code == 429

    assert _attested("203.0.113.12").get(CANONICAL, PARAMS).status_code == 200
    assert (
        _attested("203.0.113.12", path=LEGACY_HYPHEN).get(LEGACY_HYPHEN, PARAMS).status_code == 200
    )


@pytest.mark.parametrize(
    "case", ["wrong_secret", "multiple_ips", "malformed_ip", "unsigned_ip", "xff"]
)
def test_forged_attestation_cannot_open_an_independent_bucket(case, settings, google):
    settings.THROTTLE_CLIENT_IDENTITY_SECRET = ATTEST_SECRET
    proxy = "10.0.1.9"
    for _ in range(3):
        assert (
            _client(proxy).get(CANONICAL, PARAMS).status_code == 200
        )  # exhaust the fallback bucket

    if case == "wrong_secret":
        forged = _attested("198.51.100.77", secret="z" * 48, remote=proxy)
    elif case == "multiple_ips":
        forged = _attested("198.51.100.77, 198.51.100.78", remote=proxy)
    elif case == "malformed_ip":
        forged = _attested("not-an-ip", remote=proxy)
    elif case == "unsigned_ip":
        forged = APIClient(REMOTE_ADDR=proxy, HTTP_X_KM_CLIENT_IP="198.51.100.77")
    else:
        forged = APIClient(REMOTE_ADDR=proxy, HTTP_X_FORWARDED_FOR="198.51.100.77")

    calls = len(google)
    assert forged.get(CANONICAL, PARAMS).status_code == 429
    assert len(google) == calls


def test_authenticated_users_get_per_user_buckets(django_user_model, google):
    alice = django_user_model.objects.create_user(username="nearby-alice", password="unused-a")
    bob = django_user_model.objects.create_user(username="nearby-bob", password="unused-b")
    a, b = _client("198.51.100.50"), _client("198.51.100.50")
    a.force_authenticate(alice)
    b.force_authenticate(bob)

    for _ in range(3):
        assert a.get(CANONICAL, PARAMS).status_code == 200
    assert a.get(CANONICAL, PARAMS).status_code == 429
    assert b.get(CANONICAL, PARAMS).status_code == 200


# --------------------------------------------------------------------------- #
# global throttles, kill switch, response compatibility
# --------------------------------------------------------------------------- #


def test_global_anon_throttle_still_applies(settings, google):
    rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    rates[PLACES_NEARBY_THROTTLE_SCOPE] = "1000/min"
    rates["anon"] = "2/min"
    client = _client("198.51.100.60")

    assert client.get(CANONICAL, PARAMS).status_code == 200
    assert client.get(LEGACY_HYPHEN, PARAMS).status_code == 200
    assert client.get(LEGACY_UNDERSCORE, PARAMS).status_code == 429
    assert len(google) == 2


def test_global_user_throttle_still_applies(settings, django_user_model, google):
    rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    rates[PLACES_NEARBY_THROTTLE_SCOPE] = "1000/min"
    rates["user"] = "2/min"
    user = django_user_model.objects.create_user(
        username="nearby-user-throttle", password="unused-c"
    )
    client = _client()
    client.force_authenticate(user)

    assert client.get(CANONICAL, PARAMS).status_code == 200
    assert client.get(CANONICAL, PARAMS).status_code == 200
    assert client.get(CANONICAL, PARAMS).status_code == 429
    assert len(google) == 2


def test_kill_switch_is_preserved_and_makes_no_google_call(settings, google):
    settings.GOOGLE_PLACES_ENABLED = False

    res = _client().get(CANONICAL, PARAMS)

    assert res.status_code == 503
    assert res.json() == {
        "detail": "places upstream is disabled",
        "status": "PLACES_DISABLED",
        "results": [],
    }
    assert google == []


def test_bad_parameters_still_return_400_without_google(google):
    assert _client().get(CANONICAL, {"lat": "x", "lng": 139}).status_code == 400
    assert google == []


def test_legacy_urls_return_the_same_successful_response(google):
    bodies = {}
    for i, url in enumerate(ALL_URLS):
        res = _client(f"198.51.100.7{i}").get(url, PARAMS)
        assert res.status_code == 200, url
        bodies[url] = res.json()

    assert bodies[CANONICAL] == bodies[LEGACY_UNDERSCORE] == bodies[LEGACY_HYPHEN]
    result = bodies[CANONICAL]["results"][0]
    assert result["place_id"] == "PID_NEARBY_1"
    assert isinstance(result["distance_m"], int)
    assert google[0] == {"location": "35.0,139.0", "radius": 1000, "keyword": "神社"}


def test_openapi_documents_only_the_canonical_path():
    res = APIClient().get("/api/schema/", {"format": "json"})
    assert res.status_code == 200
    paths = res.json()["paths"]
    assert paths[CANONICAL]["get"]["operationId"] == "api_places_nearby_retrieve"
    assert LEGACY_UNDERSCORE not in paths
    assert LEGACY_HYPHEN not in paths


# --------------------------------------------------------------------------- #
# rate configuration contract (fresh settings, outside pytest's 2/min override)
# --------------------------------------------------------------------------- #


def _fresh_rates(extra_env: dict[str, str]) -> dict:
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(
            ("THROTTLE_", "DISABLE_THROTTLE", "PYTEST_", "RENDER_EXTERNAL_HOSTNAME")
        )
    }
    env.update(
        {
            "DJANGO_SETTINGS_MODULE": "shrine_project.settings",
            "DJANGO_SECRET_KEY": env.get("DJANGO_SECRET_KEY") or "x" * 50,
            "PYTHONPATH": str(BACKEND_DIR),
            "IS_PYTEST": "0",
        }
    )
    env.update(extra_env)
    code = (
        "import json; from django.conf import settings; "
        "print(json.dumps(settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(BACKEND_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_default_rate_is_thirty_per_minute():
    assert _fresh_rates({})["places-nearby"] == "30/min"


def test_env_override_is_honoured():
    assert _fresh_rates({"THROTTLE_PLACES_NEARBY": "12/min"})["places-nearby"] == "12/min"
