

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
        "shrine_context_need",
        "action_context",
        "reflection_question_seed",
        "source",
    }
    assert result["history_theme"] == "再出発"
    assert result["shrine_context_need"] == "仕事や進路の流れを見直したい"
    assert result["action_context"] == "実際に足を運び、今の状態を確認する"
    assert result["reflection_question_seed"] == "次に小さく動かすなら、何から始めますか？"
    assert result["source"] == {
        "history_theme": "direction_profile.direction",
        "shrine_context_need": "need_profile.primary_need_tag",
        "action_context": "action_intent.intent",
        "reflection_question_seed": "history_theme",
    }


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


def test_translate_meaning_handles_empty_profile_safely():
    result = translate_meaning(None)

    assert result == {
        "history_theme": None,
        "shrine_context_need": None,
        "action_context": None,
        "reflection_question_seed": None,
        "source": {
            "history_theme": "fallback.none",
            "shrine_context_need": "fallback.none",
            "action_context": "fallback.none",
            "reflection_question_seed": "fallback.none",
        },
    }
