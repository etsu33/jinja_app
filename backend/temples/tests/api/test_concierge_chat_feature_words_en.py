# -*- coding: utf-8 -*-
"""/api/concierge/chat/ の travel モードの特徴語（feature_words_en）の契約テスト。

- mode=travel のときだけ応答に feature_words_en を載せ、記録（ConciergeRecommendationLog）に残す
- 言語とモードは独立。英語の辞書を使うのは language=en のときだけ。日本語は dictionary="none"
- mode=travel でなければ、language=en でも何も足さない（今までの応答の形は変えない）
- 並べ替えは英語の辞書を使ったとき（mode=travel・language=en）だけ。語の一覧を
  build_chat_recommendations に渡す（並べ替え自体は test_build_chat_recommendations_travel.py）
"""

import json
from io import StringIO

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


@pytest.fixture
def capture_pipeline(monkeypatch):
    calls = []
    monkeypatch.setattr("temples.api_views_concierge.build_chat_candidates", lambda **kwargs: [])

    def fake(**kwargs):
        calls.append(kwargs)
        return {"recommendations": [dict(r) for r in RECS]}

    monkeypatch.setattr("temples.api_views_concierge.build_chat_recommendations", fake)
    return calls


@pytest.mark.django_db
def test_travel_mode_in_english_passes_words_for_reranking(client, capture_pipeline):
    _post(client, {"query": "Somewhere quiet with old trees", "mode": "travel", "language": "en"})
    assert capture_pipeline[-1]["travel_request_feature_ids"] == ["S_FOREST", "F_QUIET"]


@pytest.mark.django_db
def test_travel_mode_in_english_without_words_still_reranks_by_place_value(client, capture_pipeline):
    _post(client, {"query": "I want to rest", "mode": "travel", "language": "en"})
    assert capture_pipeline[-1]["travel_request_feature_ids"] == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "extra",
    [{}, {"language": "en"}, {"mode": "need"}, {"mode": "travel"}, {"mode": "travel", "language": "ja"}],
)
def test_no_reranking_without_english_travel(client, capture_pipeline, extra):
    _post(client, {"query": "quiet forest", **extra})
    assert capture_pipeline[-1]["travel_request_feature_ids"] is None


@pytest.mark.django_db
def test_travel_ranking_observation_is_returned_and_logged(client, monkeypatch):
    monkeypatch.setattr("temples.api_views_concierge.build_chat_candidates", lambda **kwargs: [])
    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        lambda **kwargs: {
            "recommendations": [dict(r) for r in RECS],
            "_travel_ranking": {"pool_size": 2, "covered_in_pool": 0},
        },
    )
    r = _post(client, {"query": "quiet forest", "mode": "travel", "language": "en"})
    body = r.json()
    assert body["feature_words_en"]["travel_ranking"]["pool_size"] == 2
    assert "_travel_ranking" not in body["data"]
    assert _latest_log().result_state["feature_words_en"]["travel_ranking"]["covered_in_pool"] == 0


@pytest.mark.django_db
def test_travel_mode_records_overlap_with_recommended_shrines(client, monkeypatch):
    from temples.models import Shrine

    from django.core.management import call_command

    akasaka = Shrine.objects.create(
        name_jp="赤坂氷川神社", kind="shrine", address="東京都港区赤坂6-10-12"
    )
    call_command("import_feature_words_en", stdout=StringIO(), stderr=StringIO())
    monkeypatch.setattr("temples.api_views_concierge.build_chat_candidates", lambda **kwargs: [])
    monkeypatch.setattr(
        "temples.api_views_concierge.build_chat_recommendations",
        lambda **kwargs: {
            "recommendations": [{"name": "赤坂氷川神社", "reason": "ok", "shrine_id": akasaka.pk}]
        },
    )

    r = _post(
        client, {"query": "Somewhere quiet with old trees", "mode": "travel", "language": "en"}
    )
    assert r.status_code == 200

    shrine_matches = r.json()["feature_words_en"]["shrine_matches"]
    assert shrine_matches["matches"][0]["covered"] is True
    assert shrine_matches["matches"][0]["overlap_ids"] == ["S_FOREST", "F_QUIET"]

    logged = _latest_log().result_state["feature_words_en"]["shrine_matches"]
    assert logged["matches"][0]["overlap_count"] == 2
