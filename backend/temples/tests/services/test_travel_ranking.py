# -*- coding: utf-8 -*-
"""travel モードの並べ替え（temples/services/travel_ranking.py）。

決めたこと（2026-11-13）
- ① 特徴語を持たない神社も外さない。点数0で、持つ神社の後ろに元の順で並べる
- ② 相談の語のうち神社が持っていた語の割合。F_QUIET もほかの語と同じ。季節の語は数えない
- ③ Craft と Story の語の種類の数（PLACE_VALUE_CAP 種類で 1.0）
- 理由：一致した語の英語ラベル。一致が無ければ神社が持つ語を3つまで
"""

import pytest

from temples.models import Shrine, ShrineFeatureWordEn
from temples.services.travel_ranking import (
    PLACE_VALUE_CAP,
    TRAVEL_MATCH_WEIGHT,
    TRAVEL_PLACE_WEIGHT,
    build_reason_en,
    match_score,
    place_value,
    rerank_for_travel,
)


def _shrine(name, word_ids):
    shrine = Shrine.objects.create(name_jp=name, kind="shrine", address=f"東京都テスト区{name}")
    for word_id in word_ids:
        ShrineFeatureWordEn.objects.create(
            shrine=shrine,
            word_id=word_id,
            vocabulary_version="2026-11-12",
            evidence_quote=f"{name}の根拠",
            source_url="https://example.com/",
            source_type="神社公式",
            checked_on="2026-11-13",
        )
    return shrine


def test_weights_follow_the_instruction_hypothesis():
    assert TRAVEL_MATCH_WEIGHT == 0.59
    assert TRAVEL_PLACE_WEIGHT == 0.41
    assert PLACE_VALUE_CAP == 10


def test_match_score_is_share_of_request_words_the_shrine_has():
    score, overlap = match_score(["S_FOREST", "F_QUIET"], ["S_FOREST", "ST_ANCIENT"])
    assert score == 0.5
    assert overlap == ["S_FOREST"]


def test_quiet_counts_like_any_other_word():
    score, overlap = match_score(["F_QUIET"], ["F_QUIET"])
    assert score == 1.0
    assert overlap == ["F_QUIET"]


def test_seasonal_words_are_not_counted():
    # 見頃の時期のデータが無いので、季節の語は分母にも分子にも入れない
    score, overlap = match_score(["S_FLOWERS", "S_FOREST"], ["S_FLOWERS", "S_FOREST"])
    assert score == 1.0
    assert overlap == ["S_FOREST"]
    assert match_score(["S_AUTUMN"], ["S_AUTUMN"]) == (0.0, [])


def test_no_request_words_means_zero_match():
    assert match_score([], ["S_FOREST"]) == (0.0, [])


def test_place_value_counts_distinct_craft_and_story_words_only():
    value, count = place_value(["C_NATIONAL_TREASURE", "ST_ANCIENT", "S_FOREST", "F_FESTIVAL"])
    assert count == 2
    assert value == 2 / PLACE_VALUE_CAP


def test_place_value_is_capped():
    many = [
        "C_NATIONAL_TREASURE", "C_WORLD_HERITAGE", "C_HERITAGE", "C_ORIGINAL_BUILDINGS",
        "C_CARVINGS", "C_VERMILION", "ST_SHOGUN", "ST_SAMURAI", "ST_MYTH", "ST_ANIMAL",
        "ST_ANCIENT", "ST_IMPERIAL",
    ]
    value, count = place_value(many)
    assert count == 12
    assert value == 1.0


def test_reason_lists_matched_labels():
    reason = build_reason_en(["S_FOREST", "F_FESTIVAL"], ["S_FOREST", "F_FESTIVAL", "ST_MYTH"])
    assert reason["type"] == "matches"
    assert reason["text"] == "Matches your interests: sacred forest, festival"


def test_reason_without_match_shows_up_to_three_known_features():
    reason = build_reason_en([], ["S_FOREST", "C_VERMILION", "ST_MYTH", "F_FESTIVAL"])
    assert reason["type"] == "known_for"
    assert reason["labels"] == ["sacred forest", "vermilion lacquer", "myths and legends"]
    assert reason["text"] == "Known for: sacred forest, vermilion lacquer, myths and legends"


def test_reason_is_none_for_shrine_without_features():
    assert build_reason_en([], []) is None


@pytest.mark.django_db
def test_rerank_puts_better_match_first_and_keeps_uncovered_at_the_end():
    plain = Shrine.objects.create(name_jp="特徴なし", kind="shrine", address="東京都テスト区0")
    forest = _shrine("森の社", ["S_FOREST", "F_QUIET"])
    history = _shrine("歴史の社", ["ST_ANCIENT", "ST_SAMURAI", "C_HERITAGE"])
    recs = [
        {"name": "特徴なし", "shrine_id": plain.pk},
        {"name": "歴史の社", "shrine_id": history.pk},
        {"name": "森の社", "shrine_id": forest.pk},
    ]

    ordered, observation = rerank_for_travel(recs, ["S_FOREST", "F_QUIET"])

    assert [r["name"] for r in ordered] == ["森の社", "歴史の社", "特徴なし"]
    assert ordered[0]["travel_score"]["match"] == 1.0
    assert ordered[0]["travel_reason_en"]["type"] == "matches"
    assert ordered[1]["travel_reason_en"]["type"] == "known_for"
    assert ordered[2]["travel_score"] is None
    assert ordered[2]["travel_reason_en"] is None
    assert observation["covered_in_pool"] == 2
    assert observation["pool_size"] == 3


@pytest.mark.django_db
def test_place_value_decides_when_nothing_matches():
    small = _shrine("小さい社", ["ST_MYTH"])
    big = _shrine("大きい社", ["ST_MYTH", "ST_ANCIENT", "C_NATIONAL_TREASURE"])
    recs = [{"name": "小さい社", "shrine_id": small.pk}, {"name": "大きい社", "shrine_id": big.pk}]

    ordered, _ = rerank_for_travel(recs, [])

    assert [r["name"] for r in ordered] == ["大きい社", "小さい社"]
    expected = round(TRAVEL_PLACE_WEIGHT * 3 / PLACE_VALUE_CAP, 6)
    assert ordered[0]["travel_score"]["total"] == expected


@pytest.mark.django_db
def test_ties_and_uncovered_keep_the_original_need_order():
    a = _shrine("社A", ["ST_MYTH"])
    b = _shrine("社B", ["ST_MYTH"])
    p1 = Shrine.objects.create(name_jp="特徴なし1", kind="shrine", address="東京都テスト区1")
    p2 = Shrine.objects.create(name_jp="特徴なし2", kind="shrine", address="東京都テスト区2")
    recs = [
        {"name": "特徴なし1", "shrine_id": p1.pk},
        {"name": "社B", "shrine_id": b.pk},
        {"name": "特徴なし2", "shrine_id": p2.pk},
        {"name": "社A", "shrine_id": a.pk},
    ]

    ordered, _ = rerank_for_travel(recs, [])

    assert [r["name"] for r in ordered] == ["社B", "社A", "特徴なし1", "特徴なし2"]


@pytest.mark.django_db
def test_rerank_reads_features_with_one_query(django_assert_num_queries):
    a = _shrine("社A", ["ST_MYTH"])
    b = _shrine("社B", ["S_FOREST"])
    recs = [{"name": "社A", "shrine_id": a.pk}, {"name": "社B", "shrine_id": b.pk}]
    with django_assert_num_queries(1):
        rerank_for_travel(recs, ["S_FOREST"])
