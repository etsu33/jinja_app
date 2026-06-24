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
