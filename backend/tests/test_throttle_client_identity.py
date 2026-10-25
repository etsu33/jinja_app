"""WS-04: throttle client identity（shrine_project/throttling.py）の回帰テスト。

docs/audit/ws04-throttle-client-identity-design-2026-10-25.md §5 / §11.4。DB 不要。
"""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path

import pytest
from django.conf import settings
from django.core.cache import cache
from rest_framework import throttling as drf_throttling
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView
from shrine_project import throttling as km

SECRET = "s" * 48
CLIENT_A = "203.0.113.10"
CLIENT_B = "198.51.100.20"
VERCEL_EGRESS = "192.0.2.50"
RENDER_PROXY = "10.20.30.40"
PATH = "/api/concierge/chat/"

factory = APIRequestFactory()


@pytest.fixture(autouse=True)
def _isolate(settings):
    settings.THROTTLE_TRUSTED_EDGE = ""
    settings.THROTTLE_CLIENT_IDENTITY_SECRET = ""
    km._warned.clear()
    cache.clear()
    yield
    km._warned.clear()
    cache.clear()


@pytest.fixture
def trusted_edge(settings):
    settings.THROTTLE_TRUSTED_EDGE = km.TRUSTED_EDGE_RENDER_CLOUDFLARE


@pytest.fixture
def bff_secret(settings):
    settings.THROTTLE_CLIENT_IDENTITY_SECRET = SECRET


def attestation(ip, *, method="POST", path=PATH, ts=None, secret=SECRET):
    ts = str(int(time.time()) if ts is None else ts)
    sig = km.sign_client_identity(secret.encode(), ts, method, path, ip)
    return {"HTTP_X_KM_CLIENT_IP": ip, "HTTP_X_KM_CLIENT_TS": ts, "HTTP_X_KM_CLIENT_SIG": sig}


def make_request(method="POST", path=PATH, *, remote=RENDER_PROXY, **meta):
    req = getattr(factory, method.lower())(path, REMOTE_ADDR=remote, **meta)
    return req


def ident(req):
    return km.AnonRateThrottle().get_ident(req)


def test_signature_matches_the_bff_signing_vector():
    """apps/web/src/lib/server/__tests__/clientIdentity.test.ts と同じベクタ。"""
    secret = b"test-secret-0123456789abcdef-0123456789"
    assert (
        km.sign_client_identity(secret, "1700000000", "post", "/api/concierge/chat/", CLIENT_A)
        == "39ca396bfa3550aa1d1a17da0df2b6dd866f339d7e47c5db9aade26fbca84857"
    )


# --- strict IP validation -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value, expected",
    [
        (CLIENT_A, CLIENT_A),
        ("2001:db8::1", "2001:db8::1"),
        ("2001:0DB8:0000::0001", "2001:db8::1"),
        ("::ffff:203.0.113.10", CLIENT_A),
    ],
)
def test_parse_client_ip_accepts_single_addresses(value, expected):
    assert km.parse_client_ip(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        " 203.0.113.10",
        "203.0.113.10 ",
        "203.0.113.10, 10.0.0.1",
        "203.0.113.10:443",
        "[2001:db8::1]",
        "fe80::1%eth0",
        "203.0.113.256",
        "example.com",
        "1" * 46,
        12345,
    ],
)
def test_parse_client_ip_rejects_malformed_values(value):
    assert km.parse_client_ip(value) is None


# --- X-Forwarded-For ------------------------------------------------------------------------------


def test_before_drf_default_identity_splits_buckets_on_forged_xff():
    """変更前の挙動（DRF 既定）: XFF の値ごとに別 bucket になっていた。"""
    a = make_request(HTTP_X_FORWARDED_FOR=f"forged-1, {CLIENT_A}")
    b = make_request(HTTP_X_FORWARDED_FOR=f"forged-2, {CLIENT_A}")
    assert drf_throttling.AnonRateThrottle().get_ident(a) != drf_throttling.AnonRateThrottle().get_ident(b)


@pytest.mark.parametrize("edge", ["", km.TRUSTED_EDGE_RENDER_CLOUDFLARE])
def test_forged_xff_values_do_not_create_buckets(settings, edge):
    settings.THROTTLE_TRUSTED_EDGE = edge
    idents = {
        ident(make_request(HTTP_CF_CONNECTING_IP=CLIENT_A, HTTP_X_FORWARDED_FOR=f"{i}.0.0.1, {CLIENT_A}, 10.0.0.1"))
        for i in range(1, 6)
    }
    assert len(idents) == 1
    (only,) = idents
    assert "0.0.1" not in only


# --- CF-Connecting-IP and the trusted edge boundary -----------------------------------------------


def test_cf_connecting_ip_is_ignored_without_trusted_edge_configuration():
    a = make_request(HTTP_CF_CONNECTING_IP=CLIENT_A)
    b = make_request(HTTP_CF_CONNECTING_IP=CLIENT_B)
    assert ident(a) == ident(b) == f"remote:{RENDER_PROXY}"


def test_unknown_trusted_edge_value_is_not_trusted(settings):
    settings.THROTTLE_TRUSTED_EDGE = "cloudflare"
    assert ident(make_request(HTTP_CF_CONNECTING_IP=CLIENT_A)) == f"remote:{RENDER_PROXY}"


def test_trusted_edge_uses_cf_connecting_ip(trusted_edge):
    assert ident(make_request(HTTP_CF_CONNECTING_IP=CLIENT_A)) == f"edge:{CLIENT_A}"
    assert ident(make_request(HTTP_CF_CONNECTING_IP=CLIENT_B)) == f"edge:{CLIENT_B}"


@pytest.mark.parametrize("value", [None, "", "unknown", f"{CLIENT_A}, {CLIENT_B}", f"{CLIENT_A}:80", "999.1.1.1"])
def test_missing_or_malformed_edge_identity_fails_safe(trusted_edge, value):
    meta = {} if value is None else {"HTTP_CF_CONNECTING_IP": value}
    assert ident(make_request(**meta)) == f"remote:{RENDER_PROXY}"


def test_missing_remote_addr_still_yields_a_fixed_identity():
    req = make_request()
    req.META.pop("REMOTE_ADDR", None)
    assert ident(req) == "remote:unknown"


# --- HMAC-signed BFF client identity --------------------------------------------------------------


def test_valid_attestation_is_used(bff_secret, trusted_edge):
    req = make_request(HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **attestation(CLIENT_A))
    assert ident(req) == f"bff:{CLIENT_A}"


def test_distinct_attested_web_clients_use_separate_buckets(bff_secret, trusted_edge):
    a = make_request(HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **attestation(CLIENT_A))
    b = make_request(HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **attestation(CLIENT_B))
    a2 = make_request(HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **attestation(CLIENT_A))
    assert ident(a) != ident(b)
    assert ident(a) == ident(a2)


def test_unattested_web_requests_share_the_bff_egress_bucket(bff_secret, trusted_edge):
    a = make_request(HTTP_CF_CONNECTING_IP=VERCEL_EGRESS)
    b = make_request(HTTP_CF_CONNECTING_IP=VERCEL_EGRESS)
    assert ident(a) == ident(b) == f"edge:{VERCEL_EGRESS}"


def _tampered(**changes):
    headers = attestation(CLIENT_A)
    headers.update(changes)
    return headers


def _without(name):
    return {k: v for k, v in attestation(CLIENT_A).items() if k != name}


# 時刻に依存するため、ヘッダはテスト実行時に組み立てる（収集時に作ると skew 境界がずれる）
INVALID_ATTESTATIONS = {
    "wrong-secret": lambda: attestation(CLIENT_A, secret="x" * 48),
    "ip-swapped": lambda: _tampered(HTTP_X_KM_CLIENT_IP=CLIENT_B),
    "forged-signature": lambda: _tampered(HTTP_X_KM_CLIENT_SIG="0" * 64),
    "expired": lambda: attestation(CLIENT_A, ts=int(time.time()) - km.MAX_CLOCK_SKEW_SECONDS - 5),
    "future": lambda: attestation(CLIENT_A, ts=int(time.time()) + km.MAX_CLOCK_SKEW_SECONDS + 5),
    "other-path": lambda: attestation(CLIENT_A, path="/api/compass/recommendations/"),
    "other-method": lambda: attestation(CLIENT_A, method="GET"),
    "ip-list": lambda: attestation(f"{CLIENT_A}, {CLIENT_B}"),
    "ip-malformed": lambda: attestation("not-an-ip"),
    "ts-malformed": lambda: _tampered(HTTP_X_KM_CLIENT_TS="soon"),
    "sig-upper": lambda: _tampered(
        HTTP_X_KM_CLIENT_SIG=attestation(CLIENT_A)["HTTP_X_KM_CLIENT_SIG"].upper()
    ),
    "sig-short": lambda: _tampered(HTTP_X_KM_CLIENT_SIG="zz"),
    "sig-missing": lambda: _without("HTTP_X_KM_CLIENT_SIG"),
    "ts-missing": lambda: _without("HTTP_X_KM_CLIENT_TS"),
    "ip-missing": lambda: _without("HTTP_X_KM_CLIENT_IP"),
}


@pytest.mark.parametrize("case", sorted(INVALID_ATTESTATIONS))
def test_invalid_attestation_falls_back_to_the_peer_identity(bff_secret, trusted_edge, case):
    req = make_request(HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **INVALID_ATTESTATIONS[case]())
    assert ident(req) == f"edge:{VERCEL_EGRESS}"


def test_attestation_within_the_clock_skew_is_accepted(bff_secret, trusted_edge):
    for offset in (-km.MAX_CLOCK_SKEW_SECONDS + 5, km.MAX_CLOCK_SKEW_SECONDS - 5):
        headers = attestation(CLIENT_A, ts=int(time.time()) + offset)
        assert ident(make_request(HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **headers)) == f"bff:{CLIENT_A}"


def test_attestation_is_ignored_when_no_secret_is_configured(trusted_edge):
    req = make_request(HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **attestation(CLIENT_A))
    assert ident(req) == f"edge:{VERCEL_EGRESS}"


def test_attestation_is_ignored_when_the_secret_is_too_short(settings, trusted_edge):
    short = "k" * (km.MIN_SECRET_LENGTH - 1)
    settings.THROTTLE_CLIENT_IDENTITY_SECRET = short
    req = make_request(HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **attestation(CLIENT_A, secret=short))
    assert ident(req) == f"edge:{VERCEL_EGRESS}"


def test_spoofed_bff_headers_cannot_create_buckets(bff_secret, trusted_edge):
    """直接呼び出しで X-KM-Client-* を偽造しても、署名が通らなければ edge の値にまとまる。"""
    idents = set()
    for i in range(5):
        forged = {
            "HTTP_X_KM_CLIENT_IP": f"198.51.100.{i}",
            "HTTP_X_KM_CLIENT_TS": str(int(time.time())),
            "HTTP_X_KM_CLIENT_SIG": f"{i:064x}",
        }
        idents.add(ident(make_request(HTTP_CF_CONNECTING_IP=CLIENT_A, **forged)))
    assert idents == {f"edge:{CLIENT_A}"}


# --- authenticated identity -----------------------------------------------------------------------


class _User:
    is_authenticated = True
    pk = 4242


def _authenticated_drf_request(**meta):
    view = _ConciergeScopedView()
    req = make_request(**meta)
    force_authenticate(req, user=_User())
    return view.initialize_request(req), view


def test_authenticated_identity_is_unchanged(bff_secret, trusted_edge):
    request, view = _authenticated_drf_request(HTTP_CF_CONNECTING_IP=CLIENT_A, **attestation(CLIENT_B))
    view.throttle_scope = "concierge"
    for ours, theirs in [
        (km.ScopedRateThrottle(), drf_throttling.ScopedRateThrottle()),
        (km.UserRateThrottle(), drf_throttling.UserRateThrottle()),
    ]:
        ours.allow_request(request, view)
        theirs.allow_request(request, view)
        assert ours.key == theirs.key
        assert str(_User.pk) in ours.key
    assert km.AnonRateThrottle().get_cache_key(request, view) is None


# --- end-to-end throttling ------------------------------------------------------------------------


class _ConciergeScopedView(APIView):
    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes = [km.ScopedRateThrottle]
    throttle_scope = "concierge"

    def post(self, request):
        return Response({"ok": True})


def _concierge_limit() -> int:
    num, _ = km.ScopedRateThrottle().parse_rate(km.ScopedRateThrottle.THROTTLE_RATES["concierge"])
    return num


def _call(**meta):
    return _ConciergeScopedView.as_view()(make_request(**meta)).status_code


def test_forged_xff_cannot_escape_the_scope_limit(trusted_edge):
    limit = _concierge_limit()
    codes = [_call(HTTP_CF_CONNECTING_IP=CLIENT_A, HTTP_X_FORWARDED_FOR=f"10.9.{i}.1, {CLIENT_A}") for i in range(limit + 1)]
    assert codes[:limit] == [200] * limit
    assert codes[limit] == 429


def test_forged_bff_headers_cannot_escape_the_scope_limit(bff_secret, trusted_edge):
    limit = _concierge_limit()
    codes = []
    for i in range(limit + 1):
        forged = attestation(f"198.51.100.{i}", secret="x" * 48)
        codes.append(_call(HTTP_CF_CONNECTING_IP=CLIENT_A, **forged))
    assert codes[limit] == 429


def test_distinct_attested_clients_have_independent_limits(bff_secret, trusted_edge):
    limit = _concierge_limit()
    a = [_call(HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **attestation(CLIENT_A)) for _ in range(limit + 1)]
    b = _call(HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **attestation(CLIENT_B))
    assert a[limit] == 429
    assert b == 200


def test_identity_is_resolved_once_per_request(bff_secret, trusted_edge, monkeypatch):
    calls = []
    original = km.verified_bff_client_ip
    monkeypatch.setattr(km, "verified_bff_client_ip", lambda r, **kw: calls.append(1) or original(r, **kw))
    req = make_request(HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **attestation(CLIENT_A))
    for cls in (km.AnonRateThrottle, km.UserRateThrottle, km.ScopedRateThrottle):
        assert cls().get_ident(req) == f"bff:{CLIENT_A}"
    assert len(calls) == 1


# --- configuration --------------------------------------------------------------------------------


def test_default_throttle_classes_use_the_client_identity_resolver():
    assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] == (
        "shrine_project.throttling.ScopedRateThrottle",
        "shrine_project.throttling.AnonRateThrottle",
        "shrine_project.throttling.UserRateThrottle",
    )


def test_project_throttles_keep_drf_scopes():
    assert km.AnonRateThrottle.scope == drf_throttling.AnonRateThrottle.scope == "anon"
    assert km.UserRateThrottle.scope == drf_throttling.UserRateThrottle.scope == "user"
    assert km.ScopedRateThrottle.scope_attr == drf_throttling.ScopedRateThrottle.scope_attr


def test_no_view_uses_drf_identity_throttles_directly():
    backend = Path(__file__).resolve().parents[1]
    pattern = re.compile(r"^\s*from rest_framework\.throttling import .*\b(Anon|User|Scoped)RateThrottle\b", re.M)
    offenders = []
    for path in backend.rglob("*.py"):
        rel = path.relative_to(backend)
        if rel.parts[0] in {"tests", ".venv", "venv"} or "tests" in rel.parts or rel.as_posix() == "shrine_project/throttling.py":
            continue
        if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
            offenders.append(rel.as_posix())
    assert offenders == []


# --- logging --------------------------------------------------------------------------------------


def test_logs_never_contain_addresses_signatures_or_secrets(settings, caplog):
    caplog.set_level(logging.DEBUG)
    good = attestation(CLIENT_A)
    cases = [
        ("", "", {"HTTP_CF_CONNECTING_IP": CLIENT_B}),
        (km.TRUSTED_EDGE_RENDER_CLOUDFLARE, SECRET, {"HTTP_CF_CONNECTING_IP": "garbage", **good}),
        (km.TRUSTED_EDGE_RENDER_CLOUDFLARE, SECRET, {"HTTP_CF_CONNECTING_IP": CLIENT_B, **attestation(CLIENT_A, secret="x" * 48)}),
        ("cloudflare", "short-secret", {"HTTP_CF_CONNECTING_IP": CLIENT_B, **good}),
    ]
    for edge, secret, meta in cases:
        settings.THROTTLE_TRUSTED_EDGE = edge
        settings.THROTTLE_CLIENT_IDENTITY_SECRET = secret
        ident(make_request(**meta))

    text = "\n".join(r.getMessage() for r in caplog.records)
    assert caplog.records, "configuration problems should be reported without values"
    for secret_value in (CLIENT_A, CLIENT_B, RENDER_PROXY, SECRET, "short-secret", good["HTTP_X_KM_CLIENT_SIG"], "garbage"):
        assert secret_value not in text
