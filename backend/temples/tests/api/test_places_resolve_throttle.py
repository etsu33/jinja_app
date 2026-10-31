"""POST /api/places/resolve/ dedicated throttle (`places-resolve`, default 10/min).

- POST only: GET keeps the global limits only.
- Reuses the default WS-04 throttle classes, so anonymous identity is `remote:<REMOTE_ADDR>` here
  (no trusted edge, no BFF attestation in tests). Every client sets its own REMOTE_ADDR.
- Throttles run before the handler: a rejected request makes no Google call and no DB write.
- Each test gets its own LocMem cache location.
"""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from shrine_project.throttle_config import (
    DISABLE_THROTTLE_EXEMPT_SCOPES,
    DISABLE_THROTTLE_RELAXED_RATE,
    relax_rates_for_disable_throttle,
)
from temples.api.views.places_resolve import PLACES_RESOLVE_THROTTLE_SCOPE
from temples.models import PlaceRef, Shrine, ShrineCandidate
from temples.services import google_places
from temples.services import places as places_service

pytestmark = pytest.mark.django_db

RESOLVE_URL = "/api/places/resolve/"
BACKEND_DIR = Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def isolated_throttle_cache(settings):
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": f"places-resolve-throttle-{uuid.uuid4().hex}",
        }
    }
    rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    rates[PLACES_RESOLVE_THROTTLE_SCOPE] = "10/min"
    rates["anon"] = "1000/min"
    rates["user"] = "1000/min"
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def google_details(monkeypatch):
    """Counts Place Details calls; returns a valid, collision-free place for any place_id."""
    calls: list[str] = []

    def fake_details(*, place_id, **_kwargs):
        calls.append(place_id)
        index = len(calls)
        return {
            "status": "OK",
            "result": {
                "place_id": place_id,
                "name": f"スロットル検証の場所{index}",
                "formatted_address": f"北海道どこか{index}-1",
                # far apart and far from any test Shrine, so no collision
                "geometry": {"location": {"lat": 40.0 + index, "lng": 140.0 + index * 0.5}},
            },
        }

    monkeypatch.setattr(google_places, "details", fake_details)
    return calls


def _client(ip: str = "198.51.100.10") -> APIClient:
    return APIClient(REMOTE_ADDR=ip)


def _post(client: APIClient, place_id: str):
    return client.post(RESOLVE_URL, {"place_id": place_id}, format="json")


def _counts() -> tuple[int, int, int]:
    return PlaceRef.objects.count(), ShrineCandidate.objects.count(), Shrine.objects.count()


def test_scope_default_is_ten_per_minute():
    from shrine_project import settings as project_settings

    assert project_settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["places-resolve"] == "10/min"
    assert PLACES_RESOLVE_THROTTLE_SCOPE == "places-resolve"


def test_ten_posts_pass_and_the_eleventh_is_rejected_without_side_effects(google_details):
    client = _client()

    for i in range(10):
        res = _post(client, f"PID_THROTTLE_{i:02d}")
        assert res.status_code == 200, (i, res.content)
        assert res.json()["registered"] is False

    assert len(google_details) == 10
    before = _counts()

    res = _post(client, "PID_THROTTLE_REJECTED")

    assert res.status_code == 429
    assert len(google_details) == 10  # no Google call for the rejected request
    assert _counts() == before  # no PlaceRef / ShrineCandidate / Shrine write
    assert not PlaceRef.objects.filter(pk="PID_THROTTLE_REJECTED").exists()
    assert not ShrineCandidate.objects.filter(place_id="PID_THROTTLE_REJECTED").exists()


def test_buckets_are_per_client_identity(google_details):
    first, second = _client("198.51.100.20"), _client("198.51.100.21")
    for i in range(10):
        assert _post(first, f"PID_A_{i}").status_code == 200

    assert _post(first, "PID_A_X").status_code == 429
    assert _post(second, "PID_B_0").status_code == 200


def test_registered_and_unregistered_resolution_are_unchanged():
    pr = PlaceRef.objects.create(
        place_id="PID_THR_REG", name="登録済み", address="沖縄県1-1", latitude=26.2, longitude=127.7
    )
    shrine = Shrine.objects.create(
        name_jp="登録済み", address="沖縄県1-1", latitude=26.2, longitude=127.7, place_ref=pr
    )
    PlaceRef.objects.create(
        place_id="PID_THR_UNREG", name="未登録", address="北海道1-1", latitude=43.0, longitude=141.0
    )
    client = _client()
    shrines_before = Shrine.objects.count()

    reg = _post(client, "PID_THR_REG")
    unreg = _post(client, "PID_THR_UNREG")

    assert reg.status_code == 200
    assert set(reg.json()) == {"id", "shrine_id", "place_id", "candidate_id"}
    assert reg.json()["shrine_id"] == shrine.id
    assert unreg.status_code == 200
    assert unreg.json()["registered"] is False and unreg.json()["shrine_id"] is None
    assert Shrine.objects.count() == shrines_before


def test_collision_still_returns_409_within_the_limit():
    Shrine.objects.create(name_jp="衝突神社", address="東京都1-1", latitude=35.66, longitude=139.59)
    PlaceRef.objects.create(
        place_id="PID_THR_COLLIDE",
        name="衝突神社",
        address="東京都1-1",
        latitude=35.66,
        longitude=139.59,
    )
    before = Shrine.objects.count()

    res = _post(_client(), "PID_THR_COLLIDE")

    assert res.status_code == 409
    assert set(res.json()) == {"detail", "code"}
    assert res.json()["code"] == "shrine_collision_review_required"
    assert Shrine.objects.count() == before


def test_get_is_not_subject_to_the_dedicated_limit(monkeypatch):
    searches: list[str] = []

    def fake_text_search(params):
        searches.append(params["query"])
        return {"results": [{"place_id": "PID_GET", "name": "神社", "formatted_address": "東京都"}]}

    monkeypatch.setattr(places_service, "places_text_search", fake_text_search)
    client = _client()

    for _ in range(12):
        res = client.get(RESOLVE_URL, {"q": "神社テスト"})
        assert res.status_code == 200
        assert res.json()["results"][0]["place_id"] == "PID_GET"

    assert len(searches) == 12


def test_get_does_not_consume_the_post_bucket(google_details, monkeypatch):
    monkeypatch.setattr(places_service, "places_text_search", lambda params: {"results": []})
    client = _client()
    for _ in range(15):
        assert client.get(RESOLVE_URL, {"q": "神社テスト"}).status_code == 200

    for i in range(10):
        assert _post(client, f"PID_AFTER_GET_{i}").status_code == 200
    assert _post(client, "PID_AFTER_GET_X").status_code == 429


def test_global_anon_limit_still_applies_to_post_and_get(settings, google_details, monkeypatch):
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["anon"] = "3/min"
    monkeypatch.setattr(places_service, "places_text_search", lambda params: {"results": []})

    post_client = _client("198.51.100.30")
    for i in range(3):
        assert _post(post_client, f"PID_ANON_{i}").status_code == 200
    rejected = _post(post_client, "PID_ANON_X")
    assert rejected.status_code == 429
    assert len(google_details) == 3

    get_client = _client("198.51.100.31")
    for _ in range(3):
        assert get_client.get(RESOLVE_URL, {"q": "神社テスト"}).status_code == 200
    assert get_client.get(RESOLVE_URL, {"q": "神社テスト"}).status_code == 429


def test_rate_override_is_honoured(settings, google_details):
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][PLACES_RESOLVE_THROTTLE_SCOPE] = "2/min"
    client = _client()

    assert _post(client, "PID_OVR_0").status_code == 200
    assert _post(client, "PID_OVR_1").status_code == 200
    assert _post(client, "PID_OVR_2").status_code == 429


# --------------------------------------------------------------------------- #
# DISABLE_THROTTLE: places-resolve stays limited (like shrines_ingest)
# --------------------------------------------------------------------------- #


def test_relax_keeps_exempt_scopes_and_relaxes_the_rest():
    rates = {
        "anon": "100/min",
        "places": "30/min",
        "shrines_ingest": "1/min",
        "places-resolve": "10/min",
    }

    relax_rates_for_disable_throttle(rates)

    assert rates == {
        "anon": DISABLE_THROTTLE_RELAXED_RATE,
        "places": DISABLE_THROTTLE_RELAXED_RATE,
        "shrines_ingest": "1/min",
        "places-resolve": "10/min",
    }
    assert DISABLE_THROTTLE_EXEMPT_SCOPES == {"shrines_ingest", "places-resolve"}


def _rates_in_fresh_settings(extra_env: dict[str, str]) -> dict:
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("THROTTLE_", "DISABLE_THROTTLE", "PYTEST_"))
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
    import json

    return json.loads(out.stdout.strip().splitlines()[-1])


def test_settings_disable_throttle_keeps_places_resolve_at_ten_per_minute():
    rates = _rates_in_fresh_settings({"DISABLE_THROTTLE": "1"})

    assert rates["places-resolve"] == "10/min"
    assert rates["shrines_ingest"] == "1/min"
    assert rates["anon"] == DISABLE_THROTTLE_RELAXED_RATE


def test_settings_env_override_for_places_resolve():
    rates = _rates_in_fresh_settings({"THROTTLE_PLACES_RESOLVE": "30/min", "DISABLE_THROTTLE": "1"})

    assert rates["places-resolve"] == "30/min"
