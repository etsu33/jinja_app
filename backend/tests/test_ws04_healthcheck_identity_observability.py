"""WS-04 follow-up: health check の throttle 除外（P-1）、edge warning の件数化（P-2）、識別子の集計（P-3）。"""

from __future__ import annotations

import logging
import time

import pytest
from django.conf import settings
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from shrine_project import throttling as km

SECRET = "s" * 48
CLIENT_IP = "203.0.113.10"
EDGE_IP = "198.51.100.20"
VERCEL_EGRESS = "192.0.2.50"
CHECKER = "10.204.1.7"
BILLING_URL = "/api/billings/status/"
WINDOW = km.OBSERVABILITY_WINDOW_SECONDS

# DRF の既定 rate（pytest では places-nearby だけ 2/min に上書きされる。settings.py）
EXPECTED_RATES = {
    "anon": "100/min",
    "user": "100/min",
    "auth_login": "5/min",
    "concierge": "8/min",
    "deep_dive": "8/min",
    "compass": "20/min",
    "places": "30/min",
    "places-nearby": "2/min",
    "shrines": "60/min",
    "route": "20/min",
    "geocode": "30/min",
    "favorites": "30/min",
    "routes": "60/min",
    "shrines_ingest": "1/min",
    "places-resolve": "10/min",
}


@pytest.fixture(autouse=True)
def _isolate(settings):
    settings.THROTTLE_TRUSTED_EDGE = km.TRUSTED_EDGE_RENDER_CLOUDFLARE
    settings.THROTTLE_CLIENT_IDENTITY_SECRET = SECRET
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
def clock(monkeypatch):
    now = [1_800_000_000.0]
    monkeypatch.setattr(km.time, "time", lambda: now[0])
    return now


def throttle_keys():
    return {
        k.split(":", 2)[-1]
        for k in list(cache._cache.keys())  # noqa: SLF001 — isolated LocMemCache in tests
        if k.split(":", 2)[-1].startswith("throttle_")
    }


def attestation(ip, path, *, secret=SECRET, ts=None):
    ts = str(int(time.time() if ts is None else ts))
    return {
        "HTTP_X_KM_CLIENT_IP": ip,
        "HTTP_X_KM_CLIENT_TS": ts,
        "HTTP_X_KM_CLIENT_SIG": km.sign_client_identity(secret.encode(), ts, "GET", path, ip),
    }


def fill_anon_buckets(ident):
    for cls in (km.AnonRateThrottle, km.UserRateThrottle):
        t = cls()
        cache.set(t.cache_format % {"scope": t.scope, "ident": ident}, [time.time()] * t.num_requests, 60)


def summaries(caplog):
    return [r.getMessage() for r in caplog.records if "throttle identity summary" in r.getMessage()]


def edge_warnings(caplog):
    return [r.getMessage() for r in caplog.records if "event=edge_missing" in r.getMessage()]


# --- P-1: /healthz/ ---------------------------------------------------------------------------------


def test_healthz_returns_the_existing_contract_without_throttle_or_resolver(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    calls = []
    original = km.resolve_client_ident
    monkeypatch.setattr(km, "resolve_client_ident", lambda r: calls.append(1) or original(r))

    res = APIClient().get("/healthz/", REMOTE_ADDR=CHECKER)

    assert res.status_code == 200
    assert res.json() == {"ok": True, "release": getattr(settings, "RELEASE", None)}
    assert calls == []
    assert throttle_keys() == set()
    assert edge_warnings(caplog) == []
    assert sum(km.identity_observability_counts().values()) == 0


def test_healthz_stays_healthy_when_anonymous_buckets_are_full():
    fill_anon_buckets(f"remote:{CHECKER}")
    fill_anon_buckets(f"edge:{EDGE_IP}")
    assert APIClient().get("/healthz/", REMOTE_ADDR=CHECKER).status_code == 200
    assert APIClient().get("/healthz/", HTTP_CF_CONNECTING_IP=EDGE_IP).status_code == 200


def test_other_endpoints_keep_their_throttle(django_db_blocker):
    fill_anon_buckets(f"remote:{CHECKER}")
    with django_db_blocker.unblock():
        res = APIClient().get(BILLING_URL, REMOTE_ADDR=CHECKER)
    assert res.status_code == 429


@pytest.mark.django_db
def test_other_endpoints_enforce_the_original_limit():
    limit = km.AnonRateThrottle().num_requests
    client = APIClient()
    codes = [client.get(BILLING_URL, HTTP_CF_CONNECTING_IP=EDGE_IP).status_code for _ in range(limit + 1)]
    assert codes[:limit] == [200] * limit
    assert codes[limit] == 429


def test_throttle_rates_are_unchanged():
    """settings を別プロセスで読み直す（他のテストが rate の dict を書き換えても影響されない）。"""
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    backend = Path(__file__).resolve().parents[1]
    env = {
        k: v
        for k, v in os.environ.items()
        if not (k.startswith("THROTTLE_") or k in {"DISABLE_THROTTLE", "CONCIERGE_THROTTLE", "RENDER_EXTERNAL_HOSTNAME"})
    }
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(backend), env.get("PYTHONPATH", "")]))
    code = (
        "import json; from shrine_project import settings as s; "
        "print(json.dumps({'rates': s.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'], "
        "'classes': list(s.REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'])}))"
    )
    out = subprocess.run([sys.executable, "-c", code], cwd=backend, env=env, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-2000:]
    loaded = json.loads(out.stdout.strip().splitlines()[-1])
    assert loaded["rates"] == EXPECTED_RATES
    assert loaded["classes"] == [
        "shrine_project.throttling.ScopedRateThrottle",
        "shrine_project.throttling.AnonRateThrottle",
        "shrine_project.throttling.UserRateThrottle",
    ]


# --- P-2: bounded edge warning --------------------------------------------------------------------


def _missing_edge(n=1):
    for _ in range(n):
        km.resolve_client_ident(_request())


def _request(**meta):
    from rest_framework.test import APIRequestFactory

    return APIRequestFactory().get("/api/x/", REMOTE_ADDR=meta.pop("REMOTE_ADDR", CHECKER), **meta)


def test_edge_warning_is_bounded_and_counted(caplog, clock):
    caplog.set_level(logging.WARNING, logger=km.logger.name)

    _missing_edge(1)
    assert edge_warnings(caplog) == [
        "trusted edge identity missing or malformed; using fail-safe throttle identity: "
        f"event=edge_missing count=1 window_seconds={WINDOW}"
    ]

    clock[0] += 10
    _missing_edge(49)
    assert len(edge_warnings(caplog)) == 1  # 同じ窓では出さない

    clock[0] += WINDOW  # 前回の warning から 300 秒以上
    _missing_edge(1)
    logs = edge_warnings(caplog)
    assert len(logs) == 2
    assert logs[1].endswith(f"event=edge_missing count=50 window_seconds={WINDOW}")
    assert km.identity_observability_counts()["edge_missing"] == 51


def test_repeated_missing_edge_events_remain_observable_across_windows(caplog, clock):
    caplog.set_level(logging.WARNING, logger=km.logger.name)
    for _ in range(4):
        _missing_edge(3)
        clock[0] += WINDOW
    assert len(edge_warnings(caplog)) == 4


def test_missing_edge_still_falls_back_safely(clock):
    assert km.resolve_client_ident(_request()) == f"remote:{CHECKER}"
    assert km.resolve_client_ident(_request(HTTP_CF_CONNECTING_IP="garbage")) == f"remote:{CHECKER}"


def test_edge_not_configured_is_not_an_edge_missing_event(settings, caplog):
    settings.THROTTLE_TRUSTED_EDGE = ""
    caplog.set_level(logging.WARNING, logger=km.logger.name)
    _missing_edge(3)
    assert edge_warnings(caplog) == []
    assert km.identity_observability_counts()["edge_missing"] == 0


# --- P-3: identity counters -----------------------------------------------------------------------


def test_each_path_and_outcome_is_counted(clock):
    path = "/api/x/"
    km.resolve_client_ident(_request(HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **attestation(CLIENT_IP, path, ts=clock[0])))
    km.resolve_client_ident(_request(HTTP_CF_CONNECTING_IP=EDGE_IP))
    km.resolve_client_ident(_request(HTTP_CF_CONNECTING_IP=EDGE_IP, **attestation(CLIENT_IP, path, secret="x" * 48, ts=clock[0])))
    km.resolve_client_ident(_request())
    km.resolve_client_ident(_request(HTTP_X_KM_CLIENT_IP=CLIENT_IP))

    assert km.identity_observability_counts() == {
        "edge_missing": 2,
        "bff": 1,
        "edge": 2,
        "remote": 2,
        "absent": 2,
        "valid": 1,
        "rejected": 2,
    }


def test_one_request_through_all_throttle_classes_counts_once(clock):
    req = _request(HTTP_CF_CONNECTING_IP=EDGE_IP)
    for cls in (km.AnonRateThrottle, km.UserRateThrottle, km.ScopedRateThrottle, km.AnonRateThrottle):
        cls().get_ident(req)
    counts = km.identity_observability_counts()
    assert counts["edge"] == 1
    assert counts["absent"] == 1
    assert sum(counts[k] for k in km.IDENTITY_PATHS) == 1


@pytest.mark.django_db
def test_one_api_request_counts_once():
    APIClient().get(BILLING_URL, HTTP_CF_CONNECTING_IP=EDGE_IP)
    counts = km.identity_observability_counts()
    assert counts["edge"] == 1 and counts["absent"] == 1
    assert sum(counts[k] for k in km.IDENTITY_PATHS) == 1


@pytest.mark.django_db
def test_authenticated_requests_are_not_counted(django_user_model):
    user = django_user_model.objects.create_user(username="ws04-obs", password="pw-ws04-obs")
    APIClient().get(BILLING_URL, HTTP_CF_CONNECTING_IP=EDGE_IP, HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    assert sum(km.identity_observability_counts().values()) == 0


def test_summary_is_emitted_once_per_window_with_window_counts(caplog, clock):
    caplog.set_level(logging.INFO, logger=km.logger.name)

    km.resolve_client_ident(_request(HTTP_CF_CONNECTING_IP=EDGE_IP))  # 窓の開始
    clock[0] += 100
    km.resolve_client_ident(_request(HTTP_CF_CONNECTING_IP=EDGE_IP))
    assert summaries(caplog) == []

    clock[0] += WINDOW
    km.resolve_client_ident(_request(HTTP_CF_CONNECTING_IP=EDGE_IP, **attestation(CLIENT_IP, "/api/x/", ts=clock[0])))
    assert summaries(caplog) == [
        f"throttle identity summary: window_seconds={WINDOW} bff=1 edge=2 remote=0 "
        "attestation_absent=2 attestation_valid=1 attestation_rejected=0"
    ]

    clock[0] += 10
    km.resolve_client_ident(_request(HTTP_CF_CONNECTING_IP=EDGE_IP))
    assert len(summaries(caplog)) == 1  # 新しい窓の途中

    clock[0] += WINDOW
    km.resolve_client_ident(_request(HTTP_CF_CONNECTING_IP=EDGE_IP))
    logs = summaries(caplog)
    assert len(logs) == 2
    assert "bff=0 edge=2 remote=0 attestation_absent=2 attestation_valid=0" in logs[1]


def test_no_events_produce_no_summary(caplog, clock):
    caplog.set_level(logging.INFO, logger=km.logger.name)
    clock[0] += WINDOW * 10
    APIClient().get("/healthz/")  # health check は数えない
    assert summaries(caplog) == []
    assert sum(km.identity_observability_counts().values()) == 0


def test_counters_are_thread_safe(clock):
    import threading

    def worker():
        for _ in range(200):
            km.resolve_client_ident(_request(HTTP_CF_CONNECTING_IP=EDGE_IP))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    counts = km.identity_observability_counts()
    assert counts["edge"] == 1600
    assert counts["absent"] == 1600


def test_identity_category_is_not_exposed_in_responses(django_db_blocker):
    with django_db_blocker.unblock():
        res = APIClient().get(BILLING_URL, HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **attestation(CLIENT_IP, BILLING_URL))
    assert res.status_code == 200
    body = res.content.decode()
    headers = " ".join(f"{k}: {v}" for k, v in res.items())
    for marker in ("bff", "edge:", "remote:", CLIENT_IP, VERCEL_EGRESS):
        assert marker not in body
        assert marker not in headers


# --- logs -----------------------------------------------------------------------------------------


def test_observability_logs_never_reveal_sensitive_values(caplog, clock, django_db_blocker, django_user_model):
    caplog.set_level(logging.DEBUG)
    with django_db_blocker.unblock():
        user = django_user_model.objects.create_user(username="ws04-obs-log", password="pw-ws04-obs")
        token = str(AccessToken.for_user(user))
        good = attestation(CLIENT_IP, BILLING_URL, ts=clock[0])
        bad = attestation(CLIENT_IP, BILLING_URL, secret="x" * 48, ts=clock[0])
        client = APIClient()
        client.get(BILLING_URL, HTTP_CF_CONNECTING_IP=VERCEL_EGRESS, **good)
        client.get(BILLING_URL, HTTP_CF_CONNECTING_IP=EDGE_IP, **bad)
        client.get(BILLING_URL, REMOTE_ADDR=CHECKER)
        client.get(BILLING_URL, HTTP_AUTHORIZATION=f"Bearer {token}")
        clock[0] += WINDOW
        client.get(BILLING_URL, REMOTE_ADDR=CHECKER, HTTP_CF_CONNECTING_IP="not-an-ip")

    text = "\n".join(r.getMessage() for r in caplog.records)
    assert "throttle identity summary" in text and "event=edge_missing" in text
    for value in (
        CLIENT_IP,
        EDGE_IP,
        VERCEL_EGRESS,
        CHECKER,
        "not-an-ip",
        token,
        good["HTTP_X_KM_CLIENT_SIG"],
        bad["HTTP_X_KM_CLIENT_SIG"],
        SECRET,
    ):
        assert value not in text
