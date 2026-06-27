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
def test_chat_response_preserves_action_suggestion_v4_preview_contract(client, monkeypatch):
    _stub_candidates(monkeypatch)
    _stub_recommendations(
        monkeypatch,
        [
            {
                "name": "神社A",
                "reason": "ok-a",
                "reason_source": "reason:test",
                "_score_total": 10.0,
                "action_suggestion_v4_preview": {
                    "primary_action": {
                        "label": "まず詳細を見て、行く理由を確認する",
                        "description": "候補神社の詳細を見て判断材料を増やします。",
                        "action_type": "detail_open",
                        "confidence": 0.82,
                    },
                    "secondary_action": {
                        "label": "候補として保存して、あとで見返す",
                        "description": "後から相談内容と一緒に見返せます。",
                        "action_type": "save",
                        "confidence": 0.74,
                    },
                    "reflection_prompt": {
                        "question": "この神社に行くとしたら、何を整理する時間にしたいですか？",
                        "prompt_type": "before_visit",
                        "source_seed": "fallback",
                    },
                    "action_source": {
                        "source": "fallback",
                        "reason": "入力が不足しているため、詳細確認と保存を安全な初期提案にした",
                    },
                    "preview": True,
                    "version": "v4",
                    "source_keys": ["meaning_translation"],
                },
            },
            {
                "name": "神社B",
                "reason": "ok-b",
                "reason_source": "reason:test",
                "_score_total": 9.0,
                "action_suggestion_v4_preview": {
                    "primary_action": {
                        "label": "行く前に、今日の問いを一つだけ決める",
                        "description": "問いを一つに絞ります。",
                        "action_type": "reflect",
                        "confidence": 0.78,
                    },
                    "secondary_action": {
                        "label": "候補として保存して、あとで見返す",
                        "description": "後から相談内容と一緒に見返せます。",
                        "action_type": "save",
                        "confidence": 0.74,
                    },
                    "reflection_prompt": {
                        "question": "今日持っていく問いは何ですか？",
                        "prompt_type": "before_visit",
                        "source_seed": "今日持っていく問いは何ですか？",
                    },
                    "action_source": {
                        "source": "action_context",
                        "reason": "意味変換層の行動文脈をもとに提案した",
                    },
                    "preview": True,
                    "version": "v4",
                    "source_keys": ["meaning_translation"],
                },
            },
        ],
    )

    r = client.post(
        URL,
        data=json.dumps({"query": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert r.status_code == 200

    recommendations = r.json()["data"]["recommendations"]
    assert [rec["name"] for rec in recommendations] == ["神社A", "神社B"]
    assert [rec["_score_total"] for rec in recommendations] == [10.0, 9.0]

    preview = recommendations[0]["action_suggestion_v4_preview"]
    assert set(preview.keys()) == {
        "primary_action",
        "secondary_action",
        "reflection_prompt",
        "action_source",
        "preview",
        "version",
        "source_keys",
    }
    assert preview["preview"] is True
    assert preview["version"] == "v4"
    assert preview["primary_action"]["action_type"] == "detail_open"
    assert preview["secondary_action"]["action_type"] == "save"
    assert preview["reflection_prompt"]["prompt_type"] == "before_visit"
    assert preview["action_source"]["source"] == "fallback"


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
                "interpretation_profile": {
                    "raw_query": "近場で参拝したい",
                    "state_profile": {},
                    "need_profile": {},
                    "direction_profile": {},
                    "emotion_profile": {},
                    "action_intent": {},
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
                "score_v3": {
                    "mode": "shadow",
                    "shadow_mode": True,
                    "ranking_applied": False,
                    "score_v3": {
                        "mode": "shadow",
                        "ranking_applied": False,
                        "components": {
                            "state_match_score": 0.0,
                            "meaning_match_score": 0.0,
                            "shrine_profile_score": 0.0,
                            "behavior_score": 0.0,
                            "history_score": 0.0,
                            "final_score": 0.0,
                        },
                        "observation": {
                            "top1_changed": False,
                            "delta": 0.0,
                            "reason": [],
                        },
                    },
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
        "interpretation_profile",
        "visit_style_observation",
        "ranking_breakdown_observation",
        "score_v3",
        "trim_observation",
    }

    interpretation_profile = debug["interpretation_profile"]
    assert set(interpretation_profile.keys()) == {
        "raw_query",
        "state_profile",
        "need_profile",
        "direction_profile",
        "emotion_profile",
        "action_intent",
    }
    assert interpretation_profile["raw_query"] == "近場で参拝したい"
    assert isinstance(interpretation_profile["state_profile"], dict)
    assert isinstance(interpretation_profile["need_profile"], dict)
    assert isinstance(interpretation_profile["direction_profile"], dict)
    assert isinstance(interpretation_profile["emotion_profile"], dict)
    assert isinstance(interpretation_profile["action_intent"], dict)

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

    score_v3 = debug["score_v3"]
    assert set(score_v3.keys()) == {
        "mode",
        "shadow_mode",
        "ranking_applied",
        "score_v3",
    }
    assert score_v3["mode"] == "shadow"
    assert score_v3["shadow_mode"] is True
    assert score_v3["ranking_applied"] is False

    score_v3_payload = score_v3["score_v3"]
    assert set(score_v3_payload.keys()) == {
        "mode",
        "ranking_applied",
        "components",
        "observation",
    }
    assert score_v3_payload["mode"] == "shadow"
    assert score_v3_payload["ranking_applied"] is False
    assert set(score_v3_payload["components"].keys()) == {
        "state_match_score",
        "meaning_match_score",
        "shrine_profile_score",
        "behavior_score",
        "history_score",
        "final_score",
    }
    assert score_v3_payload["observation"] == {
        "top1_changed": False,
        "delta": 0.0,
        "reason": [],
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
