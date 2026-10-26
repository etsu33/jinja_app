"""WS-04 認証成功・失敗の回帰監査: ShrineMeaningView / BillingStatusView（PR #3354）。

throttle bucket は DRF の cache key（`throttle_<scope>_<ident>`）を直接見て確認する。
本番アカウント・課金データは使わない（fixture の user と UserProfile のみ）。
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
from users.models import UserProfile

SECRET = "s" * 48
CLIENT_IP = "203.0.113.10"
EDGE_IP = "198.51.100.20"
VERCEL_EGRESS = "192.0.2.50"
BILLING_URL = "/api/billings/status/"

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
    user = django_user_model.objects.create_user(username=username, password="pw-ws04-audit")
    UserProfile.objects.update_or_create(
        user=user,
        defaults={
            "subscription_status": "active" if premium else "",
            "current_period_end": timezone.now() + timedelta(days=30) if premium else None,
        },
    )
    return user


@pytest.fixture
def premium_user(django_user_model):
    return _user(django_user_model, "ws04-premium", premium=True)


@pytest.fixture
def free_user(django_user_model):
    return _user(django_user_model, "ws04-free")


def bearer(user=None, *, expired=False, raw=None):
    if raw is not None:
        return {"HTTP_AUTHORIZATION": f"Bearer {raw}"}
    token = AccessToken.for_user(user)
    if expired:
        token.set_exp(lifetime=-timedelta(minutes=5))
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def attestation(ip, path, *, method="GET", secret=SECRET):
    ts = str(int(time.time()))
    return {
        "HTTP_X_KM_CLIENT_IP": ip,
        "HTTP_X_KM_CLIENT_TS": ts,
        "HTTP_X_KM_CLIENT_SIG": km.sign_client_identity(secret.encode(), ts, method, path, ip),
    }


def meaning_url(shrine):
    return f"/api/shrines/{shrine.pk}/meaning/"


def throttle_keys():
    """LocMemCache 上の throttle bucket key（version / prefix を除いた名前）。"""
    keys = set()
    for raw in list(cache._cache.keys()):  # noqa: SLF001 — isolated LocMemCache in tests
        name = raw.split(":", 2)[-1]
        if name.startswith("throttle_"):
            keys.add(name)
    return keys


def fill_bucket(throttle_cls, scope_view_attr, ident):
    """bucket を上限まで埋める（rate は変更しない）。"""
    throttle = throttle_cls()
    if scope_view_attr:
        throttle.scope = scope_view_attr
        throttle.rate = throttle.get_rate()
        throttle.num_requests, throttle.duration = throttle.parse_rate(throttle.rate)
    now = time.time()
    cache.set(throttle.cache_format % {"scope": throttle.scope, "ident": ident}, [now] * throttle.num_requests, 60)


def has_premium_block(payload):
    return any(block.get("access") == "premium" for block in payload["display"]["blocks"])


# --- 1. valid JWT ----------------------------------------------------------------------------------


def test_valid_jwt_uses_user_id_bucket_for_meaning(shrine, free_user):
    res = APIClient().get(meaning_url(shrine), HTTP_CF_CONNECTING_IP=EDGE_IP, **bearer(free_user))
    assert res.status_code == 200
    assert throttle_keys() == {f"throttle_shrines_{free_user.pk}", f"throttle_user_{free_user.pk}"}


def test_valid_jwt_uses_user_id_bucket_for_billing(free_user):
    res = APIClient().get(BILLING_URL, HTTP_CF_CONNECTING_IP=EDGE_IP, **bearer(free_user))
    assert res.status_code == 200
    assert throttle_keys() == {f"throttle_user_{free_user.pk}"}


def test_valid_jwt_ignores_a_valid_attestation_for_bucket_selection(shrine, free_user):
    path = meaning_url(shrine)
    res = APIClient().get(path, HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **bearer(free_user), **attestation(CLIENT_IP, path))
    assert res.status_code == 200
    assert throttle_keys() == {f"throttle_shrines_{free_user.pk}", f"throttle_user_{free_user.pk}"}


# --- 2. distinct authenticated users ---------------------------------------------------------------


def test_distinct_users_have_separate_meaning_buckets(shrine, free_user, premium_user):
    fill_bucket(km.ScopedRateThrottle, "shrines", free_user.pk)
    a = APIClient().get(meaning_url(shrine), HTTP_CF_CONNECTING_IP=EDGE_IP, **bearer(free_user))
    b = APIClient().get(meaning_url(shrine), HTTP_CF_CONNECTING_IP=EDGE_IP, **bearer(premium_user))
    assert a.status_code == 429
    assert b.status_code == 200


def test_distinct_users_have_separate_billing_buckets(free_user, premium_user):
    fill_bucket(km.UserRateThrottle, None, free_user.pk)
    a = APIClient().get(BILLING_URL, HTTP_CF_CONNECTING_IP=EDGE_IP, **bearer(free_user))
    b = APIClient().get(BILLING_URL, HTTP_CF_CONNECTING_IP=EDGE_IP, **bearer(premium_user))
    assert a.status_code == 429
    assert b.status_code == 200


# --- 3. missing JWT --------------------------------------------------------------------------------


def test_missing_jwt_is_anonymous_for_meaning(shrine):
    res = APIClient().get(meaning_url(shrine), HTTP_CF_CONNECTING_IP=EDGE_IP)
    assert res.status_code == 200
    assert not has_premium_block(res.json())
    assert throttle_keys() == {
        f"throttle_shrines_edge:{EDGE_IP}",
        f"throttle_anon_edge:{EDGE_IP}",
        f"throttle_user_edge:{EDGE_IP}",
    }


def test_missing_jwt_is_anonymous_for_billing():
    res = APIClient().get(BILLING_URL, HTTP_CF_CONNECTING_IP=EDGE_IP)
    assert res.status_code == 200
    assert res.json()["plan"] == "free"
    assert throttle_keys() == {f"throttle_anon_edge:{EDGE_IP}", f"throttle_user_edge:{EDGE_IP}"}


# --- 4 / 5. invalid and expired JWT -----------------------------------------------------------------


@pytest.mark.parametrize("kind", ["invalid", "expired"])
@pytest.mark.parametrize("target", ["meaning", "billing"])
def test_bad_jwt_is_rejected_with_401_before_throttling(shrine, free_user, kind, target):
    auth = bearer(raw="not-a-jwt") if kind == "invalid" else bearer(free_user, expired=True)
    url = meaning_url(shrine) if target == "meaning" else BILLING_URL
    res = APIClient().get(url, HTTP_CF_CONNECTING_IP=EDGE_IP, **auth)
    assert res.status_code == 401
    assert res.json()["code"] == "token_not_valid"
    # DRF は認証 → 権限 → throttle の順。401 は throttle の手前で返り、bucket は消費されない（PR 前と同じ）。
    assert throttle_keys() == set()


def test_bad_jwt_is_not_downgraded_to_anonymous_even_with_valid_attestation(shrine):
    path = meaning_url(shrine)
    res = APIClient().get(path, HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **bearer(raw="x.y.z"), **attestation(CLIENT_IP, path))
    assert res.status_code == 401
    assert throttle_keys() == set()


# --- 6 / 7 / 8. anonymous identity selection -------------------------------------------------------


def test_valid_attestation_selects_bff_identity(shrine):
    path = meaning_url(shrine)
    res = APIClient().get(path, HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **attestation(CLIENT_IP, path))
    assert res.status_code == 200
    assert f"throttle_shrines_bff:{CLIENT_IP}" in throttle_keys()
    assert all(VERCEL_EGRESS not in k for k in throttle_keys())


def test_valid_attestation_selects_bff_identity_for_billing():
    res = APIClient().get(BILLING_URL, HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **attestation(CLIENT_IP, BILLING_URL))
    assert res.status_code == 200
    assert throttle_keys() == {f"throttle_anon_bff:{CLIENT_IP}", f"throttle_user_bff:{CLIENT_IP}"}


@pytest.mark.parametrize("target", ["meaning", "billing"])
def test_invalid_attestation_falls_back_to_trusted_edge(shrine, target):
    path = meaning_url(shrine) if target == "meaning" else BILLING_URL
    forged = attestation(CLIENT_IP, path, secret="x" * 48)
    res = APIClient().get(path, HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **forged)
    assert res.status_code == 200
    keys = throttle_keys()
    assert f"throttle_anon_edge:{VERCEL_EGRESS}" in keys
    assert all(CLIENT_IP not in k for k in keys)
    assert km.attestation_rejection_counts()["bad_signature"] == 1


def test_attestation_signed_for_another_path_is_rejected(shrine):
    forged = attestation(CLIENT_IP, BILLING_URL)
    res = APIClient().get(meaning_url(shrine), HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **forged)
    assert res.status_code == 200
    assert f"throttle_shrines_edge:{VERCEL_EGRESS}" in throttle_keys()


@pytest.mark.parametrize("target", ["meaning", "billing"])
def test_missing_cf_identity_fails_safe_to_remote_addr(shrine, target):
    url = meaning_url(shrine) if target == "meaning" else BILLING_URL
    res = APIClient().get(url, REMOTE_ADDR="10.20.30.40")
    assert res.status_code == 200
    keys = throttle_keys()
    assert "throttle_anon_remote:10.20.30.40" in keys
    assert all("edge:" not in k and "bff:" not in k for k in keys)


# --- 9. meaning plan authorization -----------------------------------------------------------------


def test_meaning_plan_comes_from_the_backend_user(shrine, premium_user, free_user):
    premium = APIClient().get(meaning_url(shrine), HTTP_CF_CONNECTING_IP=EDGE_IP, **bearer(premium_user))
    free = APIClient().get(meaning_url(shrine), HTTP_CF_CONNECTING_IP=EDGE_IP, **bearer(free_user))
    assert premium.status_code == free.status_code == 200
    assert has_premium_block(premium.json())
    assert not has_premium_block(free.json())


def test_valid_attestation_does_not_grant_a_plan(shrine, premium_user):
    """attestation は throttle identity だけに使われ、認証や plan には影響しない。"""
    path = meaning_url(shrine)
    res = APIClient().get(
        path,
        HTTP_CF_CONNECTING_IP=VERCEL_EGRESS,
        HTTP_X_PLAN="premium",
        **attestation(CLIENT_IP, path),
    )
    assert res.status_code == 200
    assert not has_premium_block(res.json())


# --- 10. billing isolation -------------------------------------------------------------------------


def test_billing_status_is_scoped_to_the_token_user(premium_user, free_user):
    mine = APIClient().get(BILLING_URL, HTTP_CF_CONNECTING_IP=EDGE_IP, **bearer(premium_user)).json()
    other = APIClient().get(BILLING_URL, HTTP_CF_CONNECTING_IP=EDGE_IP, **bearer(free_user)).json()
    assert mine["plan"] == "premium" and mine["current_period_end"] is not None
    assert other["plan"] == "free" and other["current_period_end"] is None
    assert other["provider"] == "stripe"


def test_billing_status_ignores_identity_headers_and_query(premium_user, free_user):
    res = APIClient().get(
        f"{BILLING_URL}?user_id={premium_user.pk}",
        HTTP_CF_CONNECTING_IP=EDGE_IP,
        HTTP_X_USER_ID=str(premium_user.pk),
        **bearer(free_user),
        **attestation(CLIENT_IP, BILLING_URL),
    )
    assert res.status_code == 200
    assert res.json()["plan"] == "free"
    assert res.json()["current_period_end"] is None


def test_anonymous_billing_never_returns_a_users_subscription(premium_user):
    res = APIClient().get(BILLING_URL, HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **attestation(CLIENT_IP, BILLING_URL))
    assert res.status_code == 200
    assert res.json()["plan"] == "free"
    assert res.json()["current_period_end"] is None


# --- logs ------------------------------------------------------------------------------------------


def test_backend_logs_never_contain_tokens_signatures_secrets_or_ips(shrine, free_user, caplog):
    import logging

    caplog.set_level(logging.DEBUG)
    valid = bearer(free_user)
    expired = bearer(free_user, expired=True)
    path = meaning_url(shrine)
    good = attestation(CLIENT_IP, path)
    bad = attestation(CLIENT_IP, BILLING_URL, secret="x" * 48)
    client = APIClient()
    client.get(path, HTTP_CF_CONNECTING_IP=EDGE_IP, **valid)
    client.get(path, HTTP_CF_CONNECTING_IP=EDGE_IP, **expired)
    client.get(path, HTTP_CF_CONNECTING_IP=EDGE_IP, **bearer(raw="not-a-jwt"))
    client.get(path, HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **good)
    client.get(BILLING_URL, HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **bad)
    client.get(BILLING_URL, **valid)

    text = "\n".join(r.getMessage() for r in caplog.records)
    assert "attestation rejected" in text  # ログ自体は取れている
    for value in (
        valid["HTTP_AUTHORIZATION"].split()[1],
        expired["HTTP_AUTHORIZATION"].split()[1],
        good["HTTP_X_KM_CLIENT_SIG"],
        bad["HTTP_X_KM_CLIENT_SIG"],
        SECRET,
        CLIENT_IP,
        EDGE_IP,
        VERCEL_EGRESS,
    ):
        assert value not in text
