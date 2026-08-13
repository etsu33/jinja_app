# -*- coding: utf-8 -*-
"""
Recommendation Instance Identity Contract
(docs/audit/recommendation-instance-identity-propagation.md, Option C).

Backend must reuse the existing per-request `rid` as `recommendation_instance_id` on
every recommendation item -- no new ID generator, no derivation from content.
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
def test_recommendation_instance_id_equals_request_rid(client, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(
        monkeypatch,
        [
            {"name": "神社A", "shrine_id": 1, "reason": "ok"},
            {"name": "神社B", "shrine_id": 2, "reason": "ok"},
        ],
    )

    r = client.post(
        URL,
        data=json.dumps({"query": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert r.status_code == 200

    body = r.json()
    rid = body["_debug"]["rid"]
    assert rid

    recs = body["data"]["recommendations"]
    assert len(recs) == 2
    for rec in recs:
        assert rec["recommendation_instance_id"] == rid


@pytest.mark.django_db
def test_recommendation_instance_id_propagates_to_recommendations_v2(client, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(
        monkeypatch,
        {
            "recommendations": [{"name": "神社A", "shrine_id": 1, "reason": "ok"}],
            "recommendations_v2": [{"name": "神社A", "shrine_id": 1, "reason": "ok"}],
        },
    )

    r = client.post(
        URL,
        data=json.dumps({"query": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert r.status_code == 200

    body = r.json()
    rid = body["_debug"]["rid"]
    assert body["data"]["recommendations"][0]["recommendation_instance_id"] == rid
    assert body["data"]["recommendations_v2"][0]["recommendation_instance_id"] == rid


@pytest.mark.django_db
def test_recommendation_instance_id_differs_across_requests_with_identical_content(client, monkeypatch):
    """
    Same stubbed recommendation content across two independent requests must still
    get two different recommendation_instance_id values -- proving the id tracks the
    request/generation (rid), not the recommendation content (no derivation/hash of
    the payload, no reuse of a previous id).
    """
    _stub_candidates(monkeypatch)
    _stub_recommendations(monkeypatch, [{"name": "神社A", "shrine_id": 1, "reason": "ok"}])

    r1 = client.post(
        URL,
        data=json.dumps({"query": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    r2 = client.post(
        URL,
        data=json.dumps({"query": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )

    id1 = r1.json()["data"]["recommendations"][0]["recommendation_instance_id"]
    id2 = r2.json()["data"]["recommendations"][0]["recommendation_instance_id"]
    assert id1 != id2


@pytest.mark.django_db
def test_recommendation_instance_id_absent_when_no_recommendations(client, monkeypatch):
    """Quota-reached early return: recs={"recommendations": []} has nothing to embed."""
    _stub_candidates(monkeypatch)
    _stub_recommendations(monkeypatch, [])

    r = client.post(
        URL,
        data=json.dumps({"query": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert r.status_code == 200
    assert r.json()["data"]["recommendations"] == []
