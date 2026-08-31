# -*- coding: utf-8 -*-
"""Consultation Meaning v1 (PR-C) API contract tests.

Confirms `consultation_meaning` is a stable, top-level, always-present
field on the /api/concierge/chat/ response -- independent of `_debug`,
independent of quota/Recommendation state, never exposing raw free_text.
"""

import json

import pytest

URL = "/api/concierge/chat/"


def _stub_candidates(monkeypatch):
    monkeypatch.setattr("temples.api_views_concierge.build_chat_candidates", lambda **kwargs: [])


def _stub_recommendations(monkeypatch, payload):
    if isinstance(payload, list):
        payload = {"recommendations": payload}

    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        lambda **kwargs: payload,
    )


@pytest.mark.django_db
def test_consultation_meaning_is_present_and_shaped_correctly(client, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(monkeypatch, [{"name": "神社A", "reason": "ok"}])

    r = client.post(
        URL,
        data=json.dumps({"query": "気持ちを整理したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert r.status_code == 200

    body = r.json()
    assert "consultation_meaning" in body

    meaning = body["consultation_meaning"]
    assert set(meaning.keys()) == {
        "situation_signals",
        "desired_outcome_signals",
        "explicit_constraint_signals",
    }
    for key in meaning:
        assert isinstance(meaning[key], list)


@pytest.mark.django_db
def test_consultation_meaning_reflects_real_free_text_signals(client, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(monkeypatch, [{"name": "神社A", "reason": "ok"}])

    r = client.post(
        URL,
        data=json.dumps({"query": "気持ちを整理したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    body = r.json()

    outcome_types = {s["type"] for s in body["consultation_meaning"]["desired_outcome_signals"]}
    assert "clarify" in outcome_types


@pytest.mark.django_db
def test_consultation_meaning_empty_families_serialize_as_empty_arrays(client, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(monkeypatch, [{"name": "神社A", "reason": "ok"}])

    r = client.post(
        URL,
        data=json.dumps({"query": "今日はいい天気ですね", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    body = r.json()

    meaning = body["consultation_meaning"]
    assert meaning["situation_signals"] == []
    assert meaning["desired_outcome_signals"] == []
    assert meaning["explicit_constraint_signals"] == []


@pytest.mark.django_db
def test_consultation_meaning_does_not_expose_raw_free_text(client, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(monkeypatch, [{"name": "神社A", "reason": "ok"}])

    secret_query = "気持ちを整理したい、これはユニークな文言マーカーXYZ123"
    r = client.post(
        URL,
        data=json.dumps({"query": secret_query, "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    body = r.json()

    raw = json.dumps(body["consultation_meaning"], ensure_ascii=False)
    assert secret_query not in raw
    assert "XYZ123" not in raw


@pytest.mark.django_db
def test_consultation_meaning_present_even_when_quota_limit_reached(client, monkeypatch):
    """consultation_meaning must not depend on Recommendation/quota state --
    even the limit-reached response path includes it."""
    _stub_candidates(monkeypatch)
    _stub_recommendations(monkeypatch, [])

    def _fake_check_quota(*args, **kwargs):
        from types import SimpleNamespace

        return SimpleNamespace(allowed=False, remaining=0, limit=1, unlimited=False)

    monkeypatch.setattr("temples.api_views_concierge.check_quota", _fake_check_quota)

    r = client.post(
        URL,
        data=json.dumps({"query": "気持ちを整理したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    body = r.json()
    assert "consultation_meaning" in body
    assert isinstance(body["consultation_meaning"]["desired_outcome_signals"], list)


@pytest.mark.django_db
def test_default_response_does_not_depend_on_debug(client, monkeypatch):
    """consultation_meaning must be readable without relying on _debug --
    it lives at the top level as its own field, not nested under _debug."""
    _stub_candidates(monkeypatch)
    _stub_recommendations(monkeypatch, [{"name": "神社A", "reason": "ok"}])

    r = client.post(
        URL,
        data=json.dumps({"query": "気持ちを整理したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    body = r.json()

    assert "consultation_meaning" in body
    if "_debug" in body:
        assert "consultation_meaning" not in body["_debug"]
