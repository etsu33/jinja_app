from __future__ import annotations

import pytest

from temples.services.concierge_chat import build_chat_recommendations


def _shrine(id_: int, **overrides):
    candidate = {
        "id": id_,
        "shrine_id": id_,
        "name": f"神社{id_}",
        "address": "テスト所在地",
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
    return build_chat_recommendations(**params)["recommendations"][0]


@pytest.fixture(autouse=True)
def deterministic(settings):
    settings.CONCIERGE_USE_LLM = False


@pytest.mark.django_db
def test_ranked_history_theme_action_keeps_catalog_grounding():
    rec = _run(
        _shrine(1, astro_tags=["relationship"], history_theme="縁"),
        query="関係を修復したい",
        need_tags=["relationship"],
        consultation_axis="relationship_repair",
    )

    selected = rec["_explanation_payload"]["action_suggestions"][0]
    preview = rec["action_suggestion_v4_preview"]
    assert selected["grounding_class"] == "consultation_grounded"
    assert selected["grounding_source"] == "ranked_history_theme"
    assert preview["primary_action"]["description"] == selected["description"]
    assert preview["action_source"] == {
        "source": "action_context",
        "reason": "ランキングに寄与したhistory_theme「縁」の行動カタログから提案した",
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case,candidate,params",
    [
        ("themeなし", _shrine(2, astro_tags=["career"]), {"need_tags": ["career"]}),
        ("fallback Recommendation", _shrine(3), {}),
        (
            "Knowledge Explanation-only",
            _shrine(4, knowledge_deities=[{"display_name": "天照大神", "confidence": "high"}]),
            {"query": "天照大神にお参りしたい"},
        ),
        ("Context-only", _shrine(5, distance_m=50), {"bias": {"lat": 35.0, "lng": 139.0}}),
        (
            "Personalization-only",
            _shrine(6, astro_elements=["火", "水", "木", "金", "土"]),
            {"birthdate": "1990-01-01", "public_mode": "compat"},
        ),
    ],
)
def test_ungrounded_scenarios_keep_generic_safe_action_with_fallback_provenance(
    case, candidate, params
):
    rec = _run(candidate, **params)

    selected = rec["_explanation_payload"]["action_suggestions"][0]
    preview = rec["action_suggestion_v4_preview"]
    assert selected["grounding_class"] == "generic_safe", case
    assert selected["grounding_source"] == "fallback", case
    assert preview["primary_action"]["action_type"] == "detail_open", case
    assert preview["action_source"] == {
        "source": "fallback",
        "reason": "入力が不足しているため、詳細確認と保存を安全な初期提案にした",
    }, case


@pytest.mark.django_db
def test_culture_translation_action_keeps_consultation_provenance():
    rec = _run(
        _shrine(
            7,
            astro_tags=["career"],
            culture_translation={"present": True},
            meaning_payload={
                "source": {
                    "translationResult": {
                        "history_theme": "再出発",
                        "action_context": "今の仕事を一つ整理する",
                    }
                }
            },
        ),
        query="仕事を見直したい",
        need_tags=["career"],
    )

    selected = rec["_explanation_payload"]["action_suggestions"][0]
    preview = rec["action_suggestion_v4_preview"]
    assert selected["grounding_class"] == "generic_safe"
    assert selected["grounding_source"] == "fallback"
    assert "今の仕事を一つ整理する" in preview["primary_action"]["description"]
    assert preview["action_source"] == {
        "source": "action_context",
        "reason": "culture_translationの行動文脈を相談に基づく説明素材として提案した",
    }
    assert preview["source_keys"] == ["recommendation_reason_v4", "culture_translation"]
