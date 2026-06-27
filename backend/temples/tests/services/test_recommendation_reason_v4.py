

from __future__ import annotations

from temples.services.recommendation_reason_v4 import build_recommendation_reason_v4


def test_build_recommendation_reason_v4_returns_stable_schema():
    result = build_recommendation_reason_v4(
        interpretation_profile={
            "need_profile": {
                "primary_need_tag": "career",
                "need_tags": ["career"],
            },
            "decision_context": {
                "primary_decision": "career_decision",
                "decision_candidates": ["career_decision"],
            },
            "constraint_profile": {
                "primary_constraint": "time",
                "constraints": ["time"],
            },
            "outcome_hint": {
                "primary_outcome": "decide",
                "outcome_candidates": ["decide"],
            },
            "action_intent": {
                "intent": "reflect",
                "candidates": ["reflect"],
            },
        },
        meaning_translation={
            "history_theme": "再出発",
            "shrine_context_need": "仕事や進路の流れを見直したい",
            "action_context": "問いを一つに絞り、今の状態を整理する",
            "reflection_question_seed": "次に小さく動かすなら、何から始めますか？",
        },
        candidate_profile={
            "name": "神社A",
            "history_theme": "再出発",
            "goriyaku": "仕事運",
            "goriyaku_tags": ["career"],
        },
    )

    assert set(result.keys()) == {
        "reason_text",
        "fact",
        "interpretation",
        "action",
        "source",
    }
    assert isinstance(result["reason_text"], str)
    assert isinstance(result["fact"], dict)
    assert isinstance(result["interpretation"], dict)
    assert isinstance(result["action"], dict)
    assert isinstance(result["source"], dict)
    assert set(result["fact"].keys()) == {"label", "evidence"}
    assert set(result["interpretation"].keys()) == {"theme", "text"}
    assert set(result["action"].keys()) == {"text", "source"}
    assert set(result["source"].keys()) == {"fact", "interpretation", "action"}


def test_build_recommendation_reason_v4_builds_fact_layer_from_candidate_and_meaning():
    result = build_recommendation_reason_v4(
        meaning_translation={"history_theme": "再出発"},
        candidate_profile={
            "name": "神社A",
            "history_theme": "再出発",
            "goriyaku": "仕事運",
        },
    )

    assert result["fact"] == {
        "label": "再出発",
        "evidence": [
            "history_theme:再出発",
            "goriyaku:仕事運",
            "name:神社A",
        ],
    }
    assert result["source"]["fact"] == "candidate_profile|meaning_translation"


def test_build_recommendation_reason_v4_builds_interpretation_layer_from_profiles():
    result = build_recommendation_reason_v4(
        interpretation_profile={
            "need_profile": {
                "primary_need_tag": "career",
                "need_tags": ["career"],
            },
            "decision_context": {
                "primary_decision": "career_decision",
                "decision_candidates": ["career_decision"],
            },
            "constraint_profile": {
                "primary_constraint": "money",
                "constraints": ["money"],
            },
            "outcome_hint": {
                "primary_outcome": "decide",
                "outcome_candidates": ["decide"],
            },
        },
        meaning_translation={
            "history_theme": "再出発",
            "shrine_context_need": "仕事や進路の流れを見直したい",
        },
    )

    assert result["interpretation"] == {
        "theme": "再出発",
        "text": "仕事や進路の流れを見直したい。仕事や働き方を見直したい相談として受け取れます。仕事や働き方について判断したい文脈があります。お金や収入への不安があることも考慮します。判断材料を持ち帰りたい方向に整理できます。",
    }
    assert result["source"]["interpretation"] == "interpretation_profile|meaning_translation"


def test_build_recommendation_reason_v4_builds_action_layer_from_meaning_translation():
    result = build_recommendation_reason_v4(
        interpretation_profile={
            "action_intent": {
                "intent": "reflect",
                "candidates": ["reflect"],
            },
            "outcome_hint": {
                "primary_outcome": "clarify",
                "outcome_candidates": ["clarify"],
            },
        },
        meaning_translation={
            "action_context": "問いを一つに絞り、今の状態を整理する",
            "reflection_question_seed": "次に小さく動かすなら、何から始めますか？",
        },
    )

    assert result["action"] == {
        "text": "問いを一つに絞り、今の状態を整理する。振り返りでは「次に小さく動かすなら、何から始めますか？」を確認します。",
        "source": "meaning_translation.action_context+reflection_question_seed",
    }
    assert result["source"]["action"] == "meaning_translation.action_context+reflection_question_seed"


def test_build_recommendation_reason_v4_uses_recommendation_input_profile_when_direct_inputs_are_missing():
    result = build_recommendation_reason_v4(
        recommendation_input_profile={
            "interpretation_profile": {
                "need_profile": {
                    "primary_need_tag": "love",
                    "need_tags": ["love"],
                },
                "outcome_hint": {
                    "primary_outcome": "calm",
                    "outcome_candidates": ["calm"],
                },
            },
            "translation_result": {
                "history_theme": "縁",
                "shrine_context_need": "人との縁や関係性を見直したい",
                "action_context": "気持ちを落ち着け、今の状態を静かに見直す",
            },
            "candidate_profile": {
                "name": "神社B",
                "goriyaku": "縁結び",
            },
        }
    )

    assert result["fact"]["label"] == "縁"
    assert result["interpretation"]["theme"] == "縁"
    assert result["action"]["text"] == "気持ちを落ち着け、今の状態を静かに見直す"


def test_build_recommendation_reason_v4_handles_missing_inputs_safely():
    result = build_recommendation_reason_v4()

    assert result == {
        "reason_text": "この候補は、相談内容と神社側の文脈を照合する候補です。相談内容と神社側の文脈を照合する候補です。次に確認したいことを一つだけ決めます。",
        "fact": {
            "label": "候補神社",
            "evidence": [],
        },
        "interpretation": {
            "theme": "相談文脈",
            "text": "相談内容と神社側の文脈を照合する候補です。",
        },
        "action": {
            "text": "次に確認したいことを一つだけ決めます。",
            "source": "fallback",
        },
        "source": {
            "fact": "candidate_profile|meaning_translation",
            "interpretation": "interpretation_profile|meaning_translation",
            "action": "fallback",
        },
    }
