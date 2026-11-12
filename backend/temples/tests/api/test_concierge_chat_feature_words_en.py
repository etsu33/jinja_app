# -*- coding: utf-8 -*-
"""/api/concierge/chat/ の英語の特徴語（language=en）の契約テスト。

- language=en のときだけ応答に feature_words_en を載せ、記録（ConciergeRecommendationLog）に残す
- language が無い・ja のときは応答にも記録にも出さない（日本語の応答の形は変えない）
- 並び順には使わない（推薦の結果は language で変わらない）
"""

import json

import pytest

from temples.models_concierge_analytics import ConciergeRecommendationLog

URL = "/api/concierge/chat/"
RECS = [{"name": "神社A", "reason": "ok"}, {"name": "神社B", "reason": "ok"}]


@pytest.fixture
def stub_pipeline(monkeypatch):
    monkeypatch.setattr("temples.api_views_concierge.build_chat_candidates", lambda **kwargs: [])
    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        lambda **kwargs: {"recommendations": [dict(r) for r in RECS]},
    )


def _post(client, payload):
    return client.post(URL, data=json.dumps(payload), content_type="application/json")


@pytest.mark.django_db
def test_english_request_returns_and_logs_feature_words(client, stub_pipeline):
    r = _post(
        client,
        {"query": "Somewhere quiet with old trees", "language": "en", "lat": 35.0, "lng": 139.0},
    )
    assert r.status_code == 200

    body = r.json()
    assert body["feature_words_en"]["ids"] == ["S_FOREST", "F_QUIET"]
    assert body["feature_words_en"]["matched"] is True

    log_row = ConciergeRecommendationLog.objects.latest("created_at")
    assert log_row.result_state["feature_words_en"]["ids"] == ["S_FOREST", "F_QUIET"]


@pytest.mark.django_db
def test_english_request_with_no_hit_is_logged_as_a_miss(client, stub_pipeline):
    r = _post(client, {"query": "I want to rest", "language": "en", "lat": 35.0, "lng": 139.0})
    assert r.status_code == 200
    assert r.json()["feature_words_en"]["ids"] == []

    log_row = ConciergeRecommendationLog.objects.latest("created_at")
    assert log_row.result_state["feature_words_en"]["matched"] is False


@pytest.mark.django_db
@pytest.mark.parametrize("language", [None, "ja"])
def test_japanese_or_unspecified_request_has_no_feature_words(client, stub_pipeline, language):
    payload = {"query": "quiet forest", "lat": 35.0, "lng": 139.0}
    if language is not None:
        payload["language"] = language
    r = _post(client, payload)
    assert r.status_code == 200
    assert "feature_words_en" not in r.json()

    log_row = ConciergeRecommendationLog.objects.latest("created_at")
    assert "feature_words_en" not in (log_row.result_state or {})


@pytest.mark.django_db
def test_feature_words_do_not_change_recommendations(client, stub_pipeline):
    base = {"query": "quiet forest", "lat": 35.0, "lng": 139.0}
    ja = _post(client, base).json()
    en = _post(client, {**base, "language": "en"}).json()
    assert _names(en) == _names(ja)


def _names(body):
    return [r.get("name") for r in body["data"]["recommendations"]]


@pytest.mark.django_db
def test_english_request_records_overlap_with_recommended_shrines(client, monkeypatch):
    from temples.models import Shrine

    akasaka = Shrine.objects.create(
        name_jp="赤坂氷川神社", kind="shrine", address="東京都港区赤坂6-10-12"
    )
    monkeypatch.setattr("temples.api_views_concierge.build_chat_candidates", lambda **kwargs: [])
    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        lambda **kwargs: {
            "recommendations": [{"name": "赤坂氷川神社", "reason": "ok", "shrine_id": akasaka.pk}]
        },
    )

    r = _post(
        client,
        {"query": "Somewhere quiet with old trees", "language": "en", "lat": 35.0, "lng": 139.0},
    )
    assert r.status_code == 200

    shrine_matches = r.json()["feature_words_en"]["shrine_matches"]
    assert shrine_matches["matches"][0]["covered"] is True
    assert shrine_matches["matches"][0]["overlap_ids"] == ["S_FOREST", "F_QUIET"]

    log_row = ConciergeRecommendationLog.objects.latest("created_at")
    logged = log_row.result_state["feature_words_en"]["shrine_matches"]
    assert logged["matches"][0]["overlap_count"] == 2
