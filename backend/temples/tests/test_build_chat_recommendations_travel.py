# -*- coding: utf-8 -*-
"""build_chat_recommendations の travel の並べ替え（travel_request_feature_ids）。

- None（travel でない・英語でない）のときは今まで通り。並びも項目も変えない
- 語の一覧を渡すと、need で並んだ候補を travel の点数で並べ替え、上位3社に英語の理由を付ける
"""

import pytest

from temples.models import Shrine, ShrineFeatureWordEn
from temples.services.concierge_chat import build_chat_recommendations


def _shrine(name, word_ids, lat):
    shrine = Shrine.objects.create(
        name_jp=name, kind="shrine", address=f"東京都テスト区{name}", latitude=lat, longitude=139.0
    )
    for word_id in word_ids:
        ShrineFeatureWordEn.objects.create(
            shrine=shrine,
            word_id=word_id,
            vocabulary_version="2026-11-12",
            evidence_quote="根拠",
            source_url="https://example.com/",
            source_type="神社公式",
            checked_on="2026-11-13",
        )
    return shrine


def _candidate(shrine, popular):
    return {
        "id": shrine.pk,
        "shrine_id": shrine.pk,
        "name": shrine.name_jp,
        "address": shrine.address,
        "distance_m": 500.0,
        "lat": shrine.latitude,
        "lng": shrine.longitude,
        "popular_score": popular,
    }


@pytest.fixture
def three_shrines(db):
    plain = _shrine("人気の社", [], 35.001)
    history = _shrine("歴史の社", ["ST_ANCIENT"], 35.002)
    forest = _shrine("森の社", ["S_FOREST", "F_QUIET"], 35.003)
    # need では人気の高い順になりやすいよう、人気の社を最も高くする
    return [_candidate(plain, 9.0), _candidate(history, 5.0), _candidate(forest, 1.0)]


def _run(candidates, travel_ids=None):
    kwargs = {"query": "quiet forest", "language": "en", "candidates": candidates}
    if travel_ids is not None:
        kwargs["travel_request_feature_ids"] = travel_ids
    return build_chat_recommendations(**kwargs)


@pytest.mark.django_db
def test_without_travel_ids_nothing_changes(monkeypatch, settings, three_shrines):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    before = _run(three_shrines)
    names = [r["name"] for r in before["recommendations"]]
    assert all("travel_reason_en" not in r for r in before["recommendations"])
    assert "_travel_ranking" not in before

    again = _run(three_shrines)
    assert [r["name"] for r in again["recommendations"]] == names


@pytest.mark.django_db
def test_travel_ids_rerank_and_attach_english_reasons(monkeypatch, settings, three_shrines):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    recs = _run(three_shrines, ["S_FOREST", "F_QUIET"])

    items = recs["recommendations"]
    assert [r["name"] for r in items] == ["森の社", "歴史の社", "人気の社"]
    assert items[0]["travel_reason_en"]["text"] == "Matches your interests: sacred forest, quiet"
    assert items[1]["travel_reason_en"]["text"] == "Known for: over 1,000 years old"
    assert items[2]["travel_reason_en"] is None
    assert recs["_travel_ranking"]["covered_in_pool"] == 2
