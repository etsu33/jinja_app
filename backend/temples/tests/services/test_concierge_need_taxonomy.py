from __future__ import annotations

import pytest

from temples.domain.need_tags import extract_need_tags
from temples.services.concierge_chat import build_chat_recommendations
from temples.tests.fixtures.concierge_core_candidates import CONCIERGE_CORE_CANDIDATES


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("query", "expected_tag"),
    [
        ("受験に向けて学業成就を祈願したい", "study"),
        ("資格試験に受かりたい", "study"),
        ("転職を成功させたい", "career"),
        ("仕事で良い流れをつかみたい", "career"),
        ("最近流れが悪い。厄を落としたい", "protection"),
        ("最近流れが悪い。厄を落としたい", "mental"),
    ],
)
def test_need_taxonomy_separates_study_and_career(query, expected_tag, monkeypatch):

    recs = build_chat_recommendations(
        query=query,
        language="ja",
        candidates=CONCIERGE_CORE_CANDIDATES,
        birthdate=None,
        flow="A",
    )

    assert expected_tag in recs["_need"]["tags"]


@pytest.mark.django_db
def test_need_taxonomy_detects_protection_cleansing_context(monkeypatch):
    recs = build_chat_recommendations(
        query="最近流れが悪い。厄を落としたい",
        language="ja",
        candidates=CONCIERGE_CORE_CANDIDATES,
        birthdate=None,
        flow="A",
    )

    tags = recs["_need"]["tags"]

    assert "protection" in tags
    assert "mental" in tags
    assert recs["recommendations"][0]["reason_source"] != "reason:original"


@pytest.mark.parametrize(
    ("query", "expected_tag", "expected_hit"),
    [
        ("年収を上げたい", "money", "年収"),
        ("もっと稼ぎたい", "money", "もっと稼ぎたい"),
        ("収益を伸ばしたい", "money", "収益"),
        ("副業したい", "career", "副業"),
        ("好きな仕事をしたい", "career", "好きな仕事"),
        ("仕事を辞めたい", "career", "仕事を辞めたい"),
        ("会社を作りたい", "career", "会社を作りたい"),
        ("気持ちを切り替えたい", "mental", "気持ちを切り替えたい"),
        ("前向きになれる参拝がしたい", "courage", "前向きになれる"),
        ("自由に働きたい", "courage", "自由に働きたい"),
        ("会社に縛られたくない", "courage", "会社に縛られたくない"),
    ],
)
def test_need_taxonomy_detects_money_career_and_courage_keyword_boundaries(
    query,
    expected_tag,
    expected_hit,
):
    extracted = extract_need_tags(query)

    assert expected_tag in extracted.tags
    assert expected_hit in extracted.hits[expected_tag]


def test_recovery_without_health_context_resolves_to_rest_only():
    extracted = extract_need_tags("無理せず回復できる場所に行きたい")

    assert "rest" in extracted.tags
    assert "health" not in extracted.tags


def test_tired_recovery_resolves_to_rest_without_health():
    extracted = extract_need_tags("疲れを回復したい")

    assert "rest" in extracted.tags
    assert "health" not in extracted.tags


def test_illness_recovery_keeps_health():
    extracted = extract_need_tags("病気から回復したい")

    assert "health" in extracted.tags


def test_physical_condition_recovery_keeps_health():
    extracted = extract_need_tags("体調を回復したい")

    assert "health" in extracted.tags


def test_discomfort_cure_keeps_health():
    extracted = extract_need_tags("不調を治す")

    assert "health" in extracted.tags


@pytest.mark.parametrize(
    ("query", "expected_tag", "unexpected_tags"),
    [
        ("静かな場所でゆっくり休みたい", "rest", ["protection", "career"]),
        ("不安が強くて気持ちを整えたい", "mental", ["career", "money"]),
        ("落ち込んでいて、少し心を整えたい", "mental", ["career", "money"]),
        ("眠れないので穏やかに過ごしたい", "rest", ["career", "money"]),
    ],
)
def test_need_taxonomy_separates_rest_and_mental_boundaries(
    query,
    expected_tag,
    unexpected_tags,
):
    extracted = extract_need_tags(query)

    assert expected_tag in extracted.tags
    for unexpected_tag in unexpected_tags:
        assert unexpected_tag not in extracted.tags


@pytest.mark.parametrize(
    ("query", "expected_tag", "unexpected_tags"),
    [
        ("転職するかどうか考えたい", "career", ["money"]),
        ("キャリアの方向性を見直したい", "career", ["money"]),
        ("一歩踏み出す勇気がほしい", "courage", ["career", "money"]),
        ("新しい行動を始めたい", "courage", ["money"]),
    ],
)
def test_need_taxonomy_separates_courage_and_career_boundaries(
    query,
    expected_tag,
    unexpected_tags,
):
    extracted = extract_need_tags(query)

    assert expected_tag in extracted.tags
    for unexpected_tag in unexpected_tags:
        assert unexpected_tag not in extracted.tags


@pytest.mark.parametrize(
    ("query", "expected_tag", "unexpected_tags"),
    [
        ("恋愛で良い出会いがほしい", "love", ["career", "money"]),
        ("復縁について気持ちを整理したい", "love", ["career", "money"]),
        ("職場の人間関係を整えたい", "relationship", ["love", "money"]),
        ("友達との関係を見直したい", "relationship", ["love", "money"]),
    ],
)
def test_need_taxonomy_separates_love_and_relationship_boundaries(
    query,
    expected_tag,
    unexpected_tags,
):
    extracted = extract_need_tags(query)

    assert expected_tag in extracted.tags
    for unexpected_tag in unexpected_tags:
        assert unexpected_tag not in extracted.tags


@pytest.mark.parametrize(
    ("query", "expected_tag", "unexpected_tags"),
    [
        ("収入を増やしたい", "money", ["love"]),
        ("売上を伸ばしたい", "money", ["love"]),
        ("仕事の方向性を考えたい", "career", ["money", "love"]),
        ("副業の始め方を考えたい", "career", ["love"]),
    ],
)
def test_need_taxonomy_separates_money_and_career_boundaries(
    query,
    expected_tag,
    unexpected_tags,
):
    extracted = extract_need_tags(query)

    assert expected_tag in extracted.tags
    for unexpected_tag in unexpected_tags:
        assert unexpected_tag not in extracted.tags
