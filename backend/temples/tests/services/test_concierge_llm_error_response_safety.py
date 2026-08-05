# backend/temples/tests/services/test_concierge_llm_error_response_safety.py
#
# resolve_llm_route() used to store f"{type(e).__name__}: {e}" in llm_error,
# which flows through build_signals() -> _signals.llm.error -> the live
# /api/concierge/chat/ response body (backend/temples/api_views_concierge.py
# _build_chat_response: data = dict(recs); body["data"] = data). For
# openai's APIStatusError subclasses (AuthenticationError/BadRequestError/
# RateLimitError/generic APIStatusError), str(e) embeds OpenAI's own
# response body verbatim, which can include an API key fragment (auth
# failures) or request content (validation failures) -- verified earlier
# with dummy credentials against the real openai SDK. This guards that the
# fix (a fixed safe-category string) actually holds for every relevant
# exception class, using only synthetic sentinels, no real API calls.
from __future__ import annotations

import logging

import httpx
import pytest
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)

from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_llm_route import resolve_llm_route

API_KEY_SENTINEL = "sk-test-secret-do-not-leak"
QUERY_SENTINEL = "PRIVATE_CONSULTATION_SENTINEL"
UPSTREAM_BODY_SENTINEL = "PRIVATE_UPSTREAM_BODY_SENTINEL"

SAFE_CODES = {
    "connection_error",
    "authentication_error",
    "rate_limit",
    "bad_request",
    "provider_error",
    "unknown_error",
}


def _fake_request() -> httpx.Request:
    return httpx.Request(
        "POST",
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY_SENTINEL}"},
        json={"messages": [{"role": "user", "content": QUERY_SENTINEL}]},
    )


def _fake_response(status: int, message: str) -> httpx.Response:
    req = _fake_request()
    return httpx.Response(status, request=req, json={"error": {"message": message}})


def _make_exception(kind: str) -> Exception:
    req = _fake_request()
    if kind == "connection_error":
        return APIConnectionError(request=req)
    if kind == "timeout":
        return APITimeoutError(request=req)
    if kind == "authentication_error":
        resp = _fake_response(401, f"Incorrect API key provided: {API_KEY_SENTINEL}")
        return AuthenticationError(message=f"Error code: 401 - {resp.json()}", response=resp, body=resp.json())
    if kind == "bad_request":
        resp = _fake_response(400, f"Invalid content: '{QUERY_SENTINEL}'")
        return BadRequestError(message=f"Error code: 400 - {resp.json()}", response=resp, body=resp.json())
    if kind == "rate_limit":
        resp = _fake_response(429, UPSTREAM_BODY_SENTINEL)
        return RateLimitError(message=f"Error code: 429 - {resp.json()}", response=resp, body=resp.json())
    if kind == "provider_error":
        resp = _fake_response(500, UPSTREAM_BODY_SENTINEL)
        return APIStatusError(message=f"Error code: 500 - {resp.json()}", response=resp, body=resp.json())
    raise AssertionError(f"unknown kind {kind}")


def _assert_no_sentinel(text: str) -> None:
    assert API_KEY_SENTINEL not in text
    assert QUERY_SENTINEL not in text
    assert UPSTREAM_BODY_SENTINEL not in text


@pytest.mark.django_db
@pytest.mark.parametrize(
    "kind,expected_code",
    [
        ("connection_error", "connection_error"),
        ("timeout", "connection_error"),
        ("authentication_error", "authentication_error"),
        ("bad_request", "bad_request"),
        ("rate_limit", "rate_limit"),
        ("provider_error", "provider_error"),
    ],
)
def test_resolve_llm_route_returns_safe_code_only(monkeypatch, settings, caplog, kind, expected_code):
    settings.CONCIERGE_USE_LLM = True

    from temples.llm import orchestrator as orch_mod

    exc = _make_exception(kind)

    def _boom(*args, **kwargs):
        raise exc

    monkeypatch.setattr(orch_mod.ConciergeOrchestrator, "suggest", _boom, raising=True)

    with caplog.at_level(logging.INFO, logger="temples.services.concierge_chat_llm_route"):
        out = resolve_llm_route(
            query=QUERY_SENTINEL,
            valid_candidates=[],
            need_tags=[],
            llm_enabled=True,
        )

    assert out["llm_error"] == expected_code
    assert out["llm_error"] in SAFE_CODES

    logged = "\n".join(record.getMessage() for record in caplog.records)
    _assert_no_sentinel(logged)


@pytest.mark.django_db
def test_build_chat_recommendations_response_has_no_sentinel_on_llm_failure(monkeypatch, settings, caplog):
    settings.CONCIERGE_USE_LLM = True

    from temples.llm import orchestrator as orch_mod

    exc = _make_exception("authentication_error")

    def _boom(*args, **kwargs):
        raise exc

    monkeypatch.setattr(orch_mod.ConciergeOrchestrator, "suggest", _boom, raising=True)

    with caplog.at_level(logging.INFO):
        recs = build_chat_recommendations(
            query=QUERY_SENTINEL,
            language="ja",
            candidates=[],
            bias=None,
            birthdate=None,
            goriyaku_tag_ids=None,
            extra_condition=None,
            flow="A",
        )

    llm_signal = (recs.get("_signals") or {}).get("llm") or {}
    assert llm_signal.get("error") == "authentication_error"
    assert llm_signal.get("error") in SAFE_CODES

    import json

    # Scope note: this only checks the field this fix touches
    # (_signals.llm.error), not the full recs payload. A separate,
    # pre-existing, unconditional issue was found during this audit where
    # recs["_debug"] embeds raw consultation query text (unrelated to LLM
    # exception handling) and is copied wholesale into the live API
    # response by _build_chat_response(); that is out of scope for this
    # fix and is reported separately.
    llm_signal_serialized = json.dumps(llm_signal, ensure_ascii=False, default=str)
    _assert_no_sentinel(llm_signal_serialized)

    logged = "\n".join(record.getMessage() for record in caplog.records)
    _assert_no_sentinel(logged)
