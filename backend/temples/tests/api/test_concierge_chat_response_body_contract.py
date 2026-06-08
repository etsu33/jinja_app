# -*- coding: utf-8 -*-
import json
from types import SimpleNamespace

import pytest
from rest_framework.test import APIClient

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
def test_chat_response_includes_base_contract_fields(client, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(monkeypatch, [{"name": "神社A", "reason": "ok", "reason_source": "reason:test"}])

    r = client.post(
        URL,
        data=json.dumps({"query": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert r.status_code == 200

    body = r.json()
    for key in ("ok", "intent", "data", "_debug"):
        assert key in body


@pytest.mark.django_db
def test_chat_response_message_mode_reply_prefix_and_names(client, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(
        monkeypatch,
        [
            {"name": "神社A", "reason": "ok", "reason_source": "reason:test"},
            {"display_name": "神社B", "reason": "ok", "reason_source": "reason:test"},
        ],
    )

    r = client.post(
        URL,
        data=json.dumps({"message": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert r.status_code == 200

    reply = r.json()["reply"]
    assert isinstance(reply, str)
    assert reply.startswith("候補: ")
    assert "神社A" in reply
    assert "神社B" in reply


@pytest.mark.django_db
def test_chat_response_query_mode_reply_is_none(client, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(monkeypatch, [{"name": "神社A", "reason": "ok", "reason_source": "reason:test"}])

    r = client.post(
        URL,
        data=json.dumps({"query": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert r.status_code == 200
    assert r.json()["reply"] is None


@pytest.mark.django_db
def test_chat_response_authenticated_non_premium_includes_remaining_and_limit(user, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(monkeypatch, [{"name": "神社A", "reason": "ok", "reason_source": "reason:test"}])
    monkeypatch.setattr("temples.api_views_concierge.is_premium_for_user", lambda _u: False)

    client = APIClient()
    client.force_authenticate(user=user)

    r = client.post(
        URL,
        data=json.dumps({"query": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert r.status_code == 200

    body = r.json()
    assert body["plan"] == "free"
    assert "remaining" in body
    assert body["remaining"] == 4
    assert body["limit"] == 5
    assert body["limitReached"] is False


@pytest.mark.django_db
def test_chat_response_anonymous_includes_remaining_and_limit(client, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(
        monkeypatch,
        [{"name": "神社A", "reason": "ok", "reason_source": "reason:test"}],
    )

    r = client.post(
        URL,
        data=json.dumps({"query": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert r.status_code == 200

    body = r.json()
    assert "remaining" in body
    assert isinstance(body["remaining"], int)
    assert 0 <= body["remaining"] <= body["limit"]
    assert body["plan"] == "anonymous"
    assert body["limitReached"] is False


@pytest.mark.django_db
def test_chat_response_includes_thread_id_when_append_chat_succeeds(user, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(monkeypatch, [{"name": "神社A", "reason": "ok", "reason_source": "reason:test"}])
    monkeypatch.setattr("temples.api_views_concierge.is_premium_for_user", lambda _u: False)
    monkeypatch.setattr(
        "temples.api_views_concierge.append_chat",
        lambda **kwargs: SimpleNamespace(thread=SimpleNamespace(id=123)),
    )

    client = APIClient()
    client.force_authenticate(user=user)

    r = client.post(
        URL,
        data=json.dumps({"query": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert r.status_code == 200
    assert r.json()["thread"]["id"] == 123


@pytest.mark.django_db
def test_chat_response_anonymous_includes_thread_when_append_chat_succeeds(client, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(
        monkeypatch,
        [{"name": "神社A", "reason": "ok", "reason_source": "reason:test"}],
    )

    called = {"append_chat": 0, "observability": 0}

    def _append_chat_stub(**kwargs):
        called["append_chat"] += 1
        return SimpleNamespace(thread=SimpleNamespace(id=1))

    def _save_log_stub(**kwargs):
        called["observability"] += 1
        return None

    monkeypatch.setattr("temples.api_views_concierge.append_chat", _append_chat_stub)
    monkeypatch.setattr(
        "temples.services.concierge_observability.save_concierge_recommendation_log",
        _save_log_stub,
    )

    r = client.post(
        URL,
        data=json.dumps({"query": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert r.status_code == 200

    body = r.json()
    assert called["append_chat"] == 1
    assert called["observability"] == 1
    assert "thread" in body
    assert body["thread"]["id"] == 1
    assert body["thread_id"] == "1"
    assert body["data"]["thread_id"] == "1"


@pytest.mark.django_db
def test_chat_response_includes_debug_observation_contract_fields(client, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(
        monkeypatch,
        {
            "recommendations": [
                {"name": "神社A", "reason": "ok", "reason_source": "reason:test"}
            ],
            "_debug": {
                "candidate_pool_observation": {
                    "valid_candidate_count": 1,
                    "with_place_id": 1,
                    "missing_latlng": 0,
                    "distance_none": 0,
                    "score_top10": [],
                    "filter_context": {},
                },
                "visit_style_observation": {
                    "pool_size": 1,
                    "hit_count": 0,
                    "matched_tag_counts": {},
                    "rows": [],
                },
                "ranking_breakdown_observation": {
                    "ranked_count": 1,
                    "top10": [],
                },
                "trim_observation": {
                    "before_count": 1,
                    "after_count": 1,
                    "dropped_count": 0,
                    "before": [],
                    "after": [],
                    "dropped": [],
                },
            },
        },
    )

    r = client.post(
        URL,
        data=json.dumps({"query": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert r.status_code == 200

    debug = r.json()["data"]["_debug"]

    assert set(debug.keys()) == {
        "candidate_pool_observation",
        "visit_style_observation",
        "ranking_breakdown_observation",
        "trim_observation",
    }

    candidate_pool = debug["candidate_pool_observation"]
    assert set(candidate_pool.keys()) == {
        "valid_candidate_count",
        "with_place_id",
        "missing_latlng",
        "distance_none",
        "score_top10",
        "filter_context",
    }

    visit_style = debug["visit_style_observation"]
    assert set(visit_style.keys()) == {
        "pool_size",
        "hit_count",
        "matched_tag_counts",
        "rows",
    }

    ranking_breakdown = debug["ranking_breakdown_observation"]
    assert set(ranking_breakdown.keys()) == {
        "ranked_count",
        "top10",
    }

    trim = debug["trim_observation"]
    assert set(trim.keys()) == {
        "before_count",
        "after_count",
        "dropped_count",
        "before",
        "after",
        "dropped",
    }
