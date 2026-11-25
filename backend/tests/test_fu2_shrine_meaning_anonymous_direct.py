"""FU-2-P2: Shrine Meaning の anonymous SSR 直行 request（docs/audit/fu2-shrine-meaning-ssr-boundary-2026-10-27.md）.

Web の SSR は auth context が無いとき、Cookie / Authorization を付けずに Django を直接呼び、ページ request の
client identity を WS-04 HMAC で署名する。この形の request について Backend 側の不変条件を固定する:

- Premium 本文とその復元経路は anonymous に返らない（block / generated / source のすべて）。
- anonymous の shaping は free user と同一（直行しても表示は BFF 経由の anonymous と変わらない）。
- 署名は throttle identity にだけ使われ（`bff:<client ip>`）、plan には影響しない。
- 署名が無い・不正なときは edge identity に fail-safe で倒れ、200 のまま。

Backend の認可・throttle・署名のコードは変更しない（テストのみ）。
"""

from __future__ import annotations

import time
from datetime import timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from shrine_project import throttling as km
from temples.models import Shrine
from temples.services.shrine_meaning_access import (
    PREMIUM_GENERATED_OPTIONAL_TEXT_FIELDS,
    PREMIUM_GENERATED_REQUIRED_TEXT_FIELDS,
    PREMIUM_SOURCE_RESTORATION_FIELDS,
)
from users.models import UserProfile

SECRET = "s" * 48
CLIENT_IP = "203.0.113.10"
EDGE_IP = "198.51.100.20"

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _isolate(settings, monkeypatch):
    settings.THROTTLE_TRUSTED_EDGE = km.TRUSTED_EDGE_RENDER_CLOUDFLARE
    settings.THROTTLE_CLIENT_IDENTITY_SECRET = SECRET
    monkeypatch.setenv("BILLING_PROVIDER", "stripe")
    monkeypatch.setenv("BILLING_STUB_PLAN", "free")
    monkeypatch.setenv("BILLING_STUB_ACTIVE", "0")
    km._warned.clear()
    km._reset_attestation_diagnostics()
    km._reset_identity_observability()
    cache.clear()
    yield
    km._warned.clear()
    km._reset_attestation_diagnostics()
    km._reset_identity_observability()
    cache.clear()


@pytest.fixture
def shrine():
    return Shrine.objects.create(
        kind="shrine",
        name_jp="例の神社",
        address="東京都世田谷区",
        latitude=35.0,
        longitude=139.0,
        goriyaku="厄除け / 縁結び",
        sajin="例の祭神",
        description="静かに心を整えやすい神社。",
        history_theme="再出発",
        element="木",
    )


def _user(django_user_model, username, *, premium=False):
    user = django_user_model.objects.create_user(username=username, password="pw-fu2-p2")
    UserProfile.objects.update_or_create(
        user=user,
        defaults={
            "subscription_status": "active" if premium else "",
            "current_period_end": timezone.now() + timedelta(days=30) if premium else None,
        },
    )
    return user


def _bearer(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {AccessToken.for_user(user)}"}


def _attestation(path, ip=CLIENT_IP):
    ts = str(int(time.time()))
    return {
        "HTTP_X_KM_CLIENT_IP": ip,
        "HTTP_X_KM_CLIENT_TS": ts,
        "HTTP_X_KM_CLIENT_SIG": km.sign_client_identity(SECRET.encode(), ts, "GET", path, ip),
    }


def _url(shrine):
    return f"/api/shrines/{shrine.pk}/meaning/"


def _anonymous_direct(shrine, **extra):
    """Web SSR の anonymous 直行と同じ形: Accept + 署名のみ。Cookie / Authorization なし。"""
    path = _url(shrine)
    client = APIClient()
    return client.get(path, HTTP_ACCEPT="application/json", HTTP_CF_CONNECTING_IP=EDGE_IP, **{**_attestation(path), **extra})


def _throttle_keys():
    keys = set()
    for raw in list(cache._cache.keys()):  # noqa: SLF001 — isolated LocMemCache in tests
        name = raw.split(":", 2)[-1]
        if name.startswith("throttle_"):
            keys.add(name)
    return keys


def _assert_no_premium_content(payload):
    assert all(block.get("access") in ("anonymous", "free") for block in payload["display"]["blocks"])
    for key in PREMIUM_GENERATED_REQUIRED_TEXT_FIELDS:
        assert payload["generated"].get(key) == ""
    for key in PREMIUM_GENERATED_OPTIONAL_TEXT_FIELDS:
        assert payload["generated"].get(key) is None
    for key in PREMIUM_SOURCE_RESTORATION_FIELDS:
        assert payload["source"].get(key) is None


def test_anonymous_direct_request_never_receives_premium_content(shrine, django_user_model):
    premium = APIClient().get(_url(shrine), HTTP_CF_CONNECTING_IP=EDGE_IP, **_bearer(_user(django_user_model, "fu2-premium", premium=True)))
    assert premium.status_code == 200
    # 前提: この shrine には premium block がある（shaping の差が観測できる）
    assert any(block["access"] == "premium" for block in premium.json()["display"]["blocks"])

    res = _anonymous_direct(shrine)
    assert res.status_code == 200
    _assert_no_premium_content(res.json())


def test_anonymous_direct_shaping_equals_free_user_shaping(shrine, django_user_model):
    free = APIClient().get(_url(shrine), HTTP_CF_CONNECTING_IP=EDGE_IP, **_bearer(_user(django_user_model, "fu2-free")))
    anonymous = _anonymous_direct(shrine)
    assert free.status_code == anonymous.status_code == 200
    assert anonymous.json() == free.json()


def test_anonymous_direct_signature_selects_client_identity_only(shrine):
    res = _anonymous_direct(shrine, HTTP_X_PLAN="premium")
    assert res.status_code == 200
    _assert_no_premium_content(res.json())
    keys = _throttle_keys()
    assert keys, "the request should have been throttled by identity"
    assert all(k.endswith(f"bff:{CLIENT_IP}") for k in keys)
    assert {"throttle_shrines_", "throttle_anon_", "throttle_user_"} == {k.split("bff:")[0] for k in keys}


@pytest.mark.parametrize(
    "extra",
    [
        {"HTTP_X_KM_CLIENT_SIG": "0" * 64},  # bad signature
        {"HTTP_X_KM_CLIENT_TS": "1"},  # expired
        {"HTTP_X_KM_CLIENT_IP": "not-an-ip"},  # malformed
    ],
)
def test_invalid_identity_fails_safe_to_edge_and_still_returns_public_payload(shrine, extra):
    res = _anonymous_direct(shrine, **extra)
    assert res.status_code == 200
    _assert_no_premium_content(res.json())
    keys = _throttle_keys()
    assert keys and all(k.endswith(f"edge:{EDGE_IP}") for k in keys)


def test_missing_identity_fails_safe_to_edge(shrine):
    res = APIClient().get(_url(shrine), HTTP_ACCEPT="application/json", HTTP_CF_CONNECTING_IP=EDGE_IP)
    assert res.status_code == 200
    _assert_no_premium_content(res.json())
    assert all(k.endswith(f"edge:{EDGE_IP}") for k in _throttle_keys())


def test_unknown_shrine_is_404_on_the_direct_path():
    path = "/api/shrines/999999/meaning/"
    res = APIClient().get(path, HTTP_CF_CONNECTING_IP=EDGE_IP, **_attestation(path))
    assert res.status_code == 404
