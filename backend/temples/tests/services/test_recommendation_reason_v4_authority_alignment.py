"""Reason v4 consumes the existing Primary Authority without resolving it again."""

from __future__ import annotations

import pytest

from temples.services.concierge_chat import build_chat_recommendations


def _shrine(id_: int, name: str, **overrides):
    candidate = {
        "id": id_,
        "shrine_id": id_,
        "name": name,
        "address": f"テスト所在地{id_}",
        "lat": 35.0,
        "lng": 139.0,
        "distance_m": 1000,
        "goriyaku": "",
        "description": "",
        "goriyaku_tag_ids": [],
        "astro_tags": [],
        "astro_elements": [],
        "astro_priority": 0,
        "visit_style_tags": [],
        "history_theme": "",
        "popular_score": 0.5,
        "knowledge_deities": [],
        "knowledge_histories": [],
    }
    candidate.update(overrides)
    return candidate


def _run(candidate, **overrides):
    params = {
        "query": "",
        "language": "ja",
        "candidates": [candidate],
        "public_mode": "need",
        "flow": "A",
    }
    params.update(overrides)
    rec = build_chat_recommendations(**params)["recommendations"][0]
    return rec, rec["recommendation_reason_v4_detail"]


@pytest.fixture(autouse=True)
def deterministic(settings):
    settings.CONCIERGE_USE_LLM = False


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case,candidate,params,expected_primary,expected_fact,expected_text",
    [
        (
            "need_tag Primary",
            _shrine(1, "仕事神社", astro_tags=["career"]),
            {"query": "仕事を見直したい", "need_tags": ["career"]},
            "need_tag",
            None,
            "登録情報があります",
        ),
        (
            "history_theme Primary",
            _shrine(2, "縁神社", astro_tags=["relationship"], history_theme="縁"),
            {
                "query": "関係を修復したい",
                "need_tags": ["relationship"],
                "consultation_axis": "relationship_repair",
            },
            "history_theme",
            "縁",
            "縁という文脈",
        ),
        (
            "goriyaku Primary",
            _shrine(3, "恋愛神社", goriyaku="縁結び・恋愛成就"),
            {"query": "恋愛の縁を結びたい", "need_tags": ["love"]},
            "text_hint",
            "縁結び・恋愛成就",
            "縁結び・恋愛成就に関する情報",
        ),
    ],
)
def test_primary_authority_keeps_grounded_reason_strength(
    case, candidate, params, expected_primary, expected_fact, expected_text
):
    rec, detail = _run(candidate, **params)

    assert rec["_primary_reason_source"] == expected_primary, case
    if expected_primary == "history_theme":
        assert detail["fact"]["history_theme"] == expected_fact
    if expected_primary == "text_hint":
        assert detail["fact"]["goriyaku"] == expected_fact
    if expected_primary == "need_tag":
        assert detail["fact"]["goriyaku"] is None
    assert expected_text in detail["reason_text"]
    assert "明確な意味的一致が確認できない" not in detail["interpretation"]["text"]
    assert rec["recommendation_reason_quality"]["fallback_source"] in {None, "fallback"}


@pytest.mark.django_db
def test_explicit_constraint_is_not_described_as_ranking_meaning_match():
    rec, detail = _run(
        _shrine(4, "指定神社", goriyaku_tag_ids=[501]),
        query="条件に合う神社",
        goriyaku_tag_ids=[501],
    )

    assert rec["_primary_reason_source"] == "user_selected_tag"
    assert "指定された条件を満たす候補" in detail["interpretation"]["text"]
    assert "順位への意味的一致を示すものではありません" in detail["reason_text"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case,candidate,params,expected_primary",
    [
        (
            "Personalization-only",
            _shrine(5, "五行神社", astro_elements=["火", "水", "木", "金", "土"]),
            {"birthdate": "1990-01-01", "public_mode": "compat"},
            "element",
        ),
        ("Secondary-only", _shrine(6, "人気神社", popular_score=10.0), {}, "fallback"),
        (
            "Context-only",
            _shrine(7, "近隣神社", distance_m=50),
            {"bias": {"lat": 35.0, "lng": 139.0}},
            "fallback",
        ),
        ("fallback", _shrine(10, "情報なし神社"), {}, "fallback"),
    ],
)
def test_non_semantic_authority_does_not_claim_a_match(
    case, candidate, params, expected_primary
):
    rec, detail = _run(candidate, **params)

    assert rec["_primary_reason_source"] == expected_primary, case
    assert detail["fact"]["goriyaku"] is None
    assert "明確な意味的一致が確認できない" in detail["interpretation"]["text"]
    assert "相談条件との一致" not in detail["reason_text"]
    assert "あなたの相談に合う" not in detail["reason_text"]
    assert rec["recommendation_reason_quality"]["fallback_source"] == "fallback"


@pytest.mark.django_db
def test_knowledge_fact_is_explicitly_separate_from_ranking_attribution():
    rec, detail = _run(
        _shrine(
            8,
            "知識神社",
            knowledge_deities=[{"display_name": "天照大神", "confidence": "high"}],
            knowledge_histories=[
                {
                    "history_type": "founding",
                    "content": "古くから地域を見守る由緒があります。",
                    "confidence": "high",
                }
            ],
        ),
        query="天照大神にお参りしたい",
    )

    assert rec["_primary_reason_source"] == "fallback"
    assert detail["fact"]["deity"] == "天照大神"
    assert "今回の順位根拠ではありません" in detail["reason_text"]
    assert "明確な意味的一致が確認できない" in detail["interpretation"]["text"]
    assert rec["recommendation_reason_quality"]["fallback_source"] == "fallback"


@pytest.mark.django_db
def test_culture_translation_stays_derived_meaning_not_shrine_fact():
    rec, detail = _run(
        _shrine(
            9,
            "翻訳神社",
            astro_tags=["career"],
            culture_translation={"present": True},
            meaning_payload={
                "source": {
                    "translationResult": {
                        "history_theme": "再出発",
                        "shrine_context_need": "仕事の流れを見直す",
                        "action_context": "今の仕事を一つ整理する",
                    }
                }
            },
        ),
        query="仕事を見直したい",
        need_tags=["career"],
    )

    assert rec["_primary_reason_source"] == "need_tag"
    assert detail["fact"]["history_theme"] is None
    assert detail["fact"]["goriyaku"] is None
    assert detail["interpretation"]["theme"] == "再出発"
    assert detail["action"]["source"] == "meaning_translation.action_context"
    assert "再出発という文脈で整理" not in detail["reason_text"]
    assert rec["recommendation_reason_quality"]["fallback_source"] is None
