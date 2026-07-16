from __future__ import annotations

from temples.services.meaning_translation import translate_meaning


def test_translate_meaning_returns_stable_schema_from_interpretation_profile():
    result = translate_meaning(
        {
            "need_profile": {
                "need_tags": ["career"],
                "primary_need_tag": "career",
            },
            "direction_profile": {
                "direction": "reset",
                "themes": ["再出発"],
            },
            "action_intent": {
                "intent": "visit",
                "candidates": ["visit"],
            },
        }
    )

    assert set(result.keys()) == {
        "history_theme",
        "history_theme_secondary",
        "shrine_context_need",
        "action_context",
        "reflection_question_seed",
        "source",
    }
    assert result["history_theme"] == "再出発"
    assert result["history_theme_secondary"] is None
    assert result["shrine_context_need"] == "仕事や進路の流れを見直したい"
    assert result["action_context"] == "実際に足を運び、今の状態を確認する"
    assert result["reflection_question_seed"] == "次に小さく動かすなら、何から始めますか？"
    assert result["source"] == {
        "history_theme": "direction_profile.direction",
        "history_theme_secondary": "fallback.none",
        "shrine_context_need": "need_profile.primary_need_tag",
        "action_context": "action_intent.intent",
        "reflection_question_seed": "history_theme",
    }


def test_translate_meaning_resolves_secondary_history_theme_from_direction_profile_themes():
    """direction_profile.themes（DIRECTION_BY_STATE由来）の2番目の値を副次候補として拾う。

    例: "疲れている"(tired) は state_profile.primary_state 経由で
    themes=["静寂", "復興"] を持つが、主値の解決はHISTORY_THEME_BY_DIRECTIONのみを見るため、
    "復興"はこれまでどこにも現れなかった（history-theme-contract-audit.mdのP0）。
    """
    result = translate_meaning(
        {
            "need_profile": {},
            "direction_profile": {
                "direction": "rest",
                "themes": ["静寂", "復興"],
            },
            "action_intent": {},
        }
    )

    assert result["history_theme"] == "静寂"
    assert result["history_theme_secondary"] == "復興"
    assert result["source"]["history_theme_secondary"] == "direction_profile.themes"


def test_translate_meaning_secondary_history_theme_is_none_when_themes_has_one_item():
    result = translate_meaning(
        {
            "need_profile": {},
            "direction_profile": {
                "direction": "reset",
                "themes": ["再出発"],
            },
            "action_intent": {},
        }
    )

    assert result["history_theme_secondary"] is None
    assert result["source"]["history_theme_secondary"] == "fallback.none"


def test_translate_meaning_falls_back_to_need_when_direction_is_missing():
    result = translate_meaning(
        {
            "need_profile": {
                "need_tags": ["study"],
                "primary_need_tag": "study",
            },
            "direction_profile": {},
            "action_intent": {},
        }
    )

    assert result["history_theme"] == "学び"
    assert result["shrine_context_need"] == "学びや積み重ねを続けたい"
    assert result["action_context"] is None
    assert result["reflection_question_seed"] == "今後も積み重ねたい学びや行動は何ですか？"
    assert result["source"]["history_theme"] == "need_profile.primary_need_tag"


def test_translate_meaning_falls_back_to_decision_context_for_history_theme():
    result = translate_meaning(
        {
            "need_profile": {},
            "direction_profile": {},
            "action_intent": {},
            "decision_context": {
                "primary_decision": "relationship_decision",
                "decision_candidates": ["relationship_decision"],
            },
        }
    )

    assert result["history_theme"] == "縁"
    assert result["reflection_question_seed"] == "今、大切にしたい関係や距離感は何ですか？"
    assert result["source"]["history_theme"] == "decision_context.primary_decision"


def test_translate_meaning_falls_back_to_constraint_profile_for_shrine_context_need():
    result = translate_meaning(
        {
            "need_profile": {},
            "direction_profile": {},
            "action_intent": {},
            "constraint_profile": {
                "primary_constraint": "money",
                "constraints": ["money"],
            },
        }
    )

    assert result["shrine_context_need"] == "生活や収入への不安を整え、足元を見直したい"
    assert result["source"]["shrine_context_need"] == "constraint_profile.primary_constraint"


def test_translate_meaning_falls_back_to_outcome_hint_for_action_context():
    result = translate_meaning(
        {
            "need_profile": {},
            "direction_profile": {},
            "action_intent": {},
            "outcome_hint": {
                "primary_outcome": "decide",
                "outcome_candidates": ["decide"],
            },
        }
    )

    assert result["action_context"] == "選択肢を一つに絞り、次の判断材料を持ち帰る"
    assert result["source"]["action_context"] == "outcome_hint.primary_outcome"


def test_translate_meaning_keeps_existing_priority_over_v4_fallback_fields():
    result = translate_meaning(
        {
            "need_profile": {
                "need_tags": ["career"],
                "primary_need_tag": "career",
            },
            "direction_profile": {
                "direction": "challenge",
            },
            "action_intent": {
                "intent": "reflect",
                "candidates": ["reflect"],
            },
            "decision_context": {
                "primary_decision": "relationship_decision",
                "decision_candidates": ["relationship_decision"],
            },
            "constraint_profile": {
                "primary_constraint": "money",
                "constraints": ["money"],
            },
            "outcome_hint": {
                "primary_outcome": "decide",
                "outcome_candidates": ["decide"],
            },
        }
    )

    assert result["history_theme"] == "勝負"
    assert result["shrine_context_need"] == "仕事や進路の流れを見直したい"
    assert result["action_context"] == "問いを一つに絞り、今の状態を整理する"
    assert result["source"]["history_theme"] == "direction_profile.direction"
    assert result["source"]["shrine_context_need"] == "need_profile.primary_need_tag"
    assert result["source"]["action_context"] == "action_intent.intent"


def test_translate_meaning_handles_empty_profile_safely():
    result = translate_meaning(None)

    assert result == {
        "history_theme": None,
        "history_theme_secondary": None,
        "shrine_context_need": None,
        "action_context": None,
        "reflection_question_seed": None,
        "source": {
            "history_theme": "fallback.none",
            "history_theme_secondary": "fallback.none",
            "shrine_context_need": "fallback.none",
            "action_context": "fallback.none",
            "reflection_question_seed": "fallback.none",
        },
    }
