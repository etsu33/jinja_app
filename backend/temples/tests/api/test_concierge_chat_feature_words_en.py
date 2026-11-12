# -*- coding: utf-8 -*-
"""/api/concierge/chat/ の travel モードの特徴語（feature_words_en）の契約テスト。

- mode=travel のときだけ応答に feature_words_en を載せ、記録（ConciergeRecommendationLog）に残す
- 言語とモードは独立。英語の辞書を使うのは language=en のときだけ。日本語は dictionary="none"
- mode=travel でなければ、language=en でも何も足さない（今までの応答の形は変えない）
- 並び順には使わない（推薦の結果は mode=travel で変わらない）
"""

import json

import pytest

from temples.models_concierge_analytics import ConciergeRecommendationLog

URL = "/api/concierge/chat/"
RECS = [{"name": "神社A", "reason": "ok"}, {"name": "神社B", "reason": "ok"}]
BASE = {"lat": 35.0, "lng": 139.0}


@pytest.fixture
def stub_pipeline(monkeypatch):
    monkeypatch.setattr("temples.api_views_concierge.build_chat_candidates", lambda **kwargs: [])
    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        lambda **kwargs: {"recommendations": [dict(r) for r in RECS]},
    )


def _post(client, payload):
    return client.post(URL, data=json.dumps({**BASE, **payload}), content_type="application/json")


def _latest_log():
    return ConciergeRecommendationLog.objects.latest("created_at")


def _names(body):
    return [r.get("name") for r in body["data"]["recommendations"]]


@pytest.mark.django_db
def test_travel_mode_in_english_returns_and_logs_feature_words(client, stub_pipeline):
    r = _post(
        client, {"query": "Somewhere quiet with old trees", "mode": "travel", "language": "en"}
    )
    assert r.status_code == 200

    payload = r.json()["feature_words_en"]
    assert payload["requested_mode"] == "travel"
    assert payload["dictionary"] == "en"
    assert payload["ids"] == ["S_FOREST", "F_QUIET"]
    assert payload["matched"] is True

    logged = _latest_log().result_state["feature_words_en"]
    assert logged["requested_mode"] == "travel"
    assert logged["ids"] == ["S_FOREST", "F_QUIET"]


@pytest.mark.django_db
def test_travel_mode_miss_is_logged(client, stub_pipeline):
    r = _post(client, {"query": "I want to rest", "mode": "travel", "language": "en"})
    assert r.status_code == 200
    assert r.json()["feature_words_en"]["ids"] == []
    assert _latest_log().result_state["feature_words_en"]["matched"] is False


@pytest.mark.django_db
@pytest.mark.parametrize("language", [None, "ja"])
def test_travel_mode_in_japanese_has_no_dictionary_yet(client, stub_pipeline, language):
    payload = {"query": "quiet forest", "mode": "travel"}
    if language is not None:
        payload["language"] = language
    r = _post(client, payload)
    assert r.status_code == 200

    body_payload = r.json()["feature_words_en"]
    assert body_payload["requested_mode"] == "travel"
    assert body_payload["dictionary"] == "none"
    assert body_payload["ids"] == []
    assert _latest_log().result_state["feature_words_en"]["dictionary"] == "none"


@pytest.mark.django_db
@pytest.mark.parametrize("extra", [{}, {"language": "en"}, {"mode": "need"}, {"language": "ja"}])
def test_without_travel_mode_nothing_is_added(client, stub_pipeline, extra):
    r = _post(client, {"query": "quiet forest", **extra})
    assert r.status_code == 200
    assert "feature_words_en" not in r.json()
    assert "feature_words_en" not in (_latest_log().result_state or {})


@pytest.mark.django_db
def test_travel_mode_does_not_change_recommendations(client, stub_pipeline):
    need = _post(client, {"query": "quiet forest"}).json()
    travel = _post(client, {"query": "quiet forest", "mode": "travel", "language": "en"}).json()
    assert _names(travel) == _names(need)
