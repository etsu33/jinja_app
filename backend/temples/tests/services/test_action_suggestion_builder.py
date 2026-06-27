from __future__ import annotations

from temples.services.action_suggestion_builder import (
    ACTION_SOURCE_VALUES,
    ACTION_TYPE_VALUES,
    PROMPT_TYPE_VALUES,
    attach_action_suggestion_v4_preview,
    build_action_suggestion,
)


def _assert_stable_schema(result: dict) -> None:
    assert set(result.keys()) == {
        "primary_action",
        "secondary_action",
        "reflection_prompt",
        "action_source",
        "preview",
        "version",
        "source_keys",
    }
    assert result["preview"] is True
    assert result["version"] == "v4"
    assert isinstance(result["source_keys"], list)

    assert set(result["primary_action"].keys()) == {
        "label",
        "description",
        "action_type",
        "confidence",
    }
    assert set(result["secondary_action"].keys()) == {
        "label",
        "description",
        "action_type",
        "confidence",
    }
    assert set(result["reflection_prompt"].keys()) == {
        "question",
        "prompt_type",
        "source_seed",
    }
    assert set(result["action_source"].keys()) == {
        "source",
        "reason",
    }

    assert result["primary_action"]["action_type"] in ACTION_TYPE_VALUES
    assert result["secondary_action"]["action_type"] in ACTION_TYPE_VALUES
    assert result["primary_action"]["action_type"] != result["secondary_action"]["action_type"]
    assert result["reflection_prompt"]["prompt_type"] in PROMPT_TYPE_VALUES
    assert result["action_source"]["source"] in ACTION_SOURCE_VALUES

    assert isinstance(result["primary_action"]["label"], str)
    assert isinstance(result["primary_action"]["description"], str)
    assert isinstance(result["secondary_action"]["label"], str)
    assert isinstance(result["secondary_action"]["description"], str)
    assert isinstance(result["reflection_prompt"]["question"], str)
    assert isinstance(result["reflection_prompt"]["source_seed"], str)
    assert isinstance(result["action_source"]["reason"], str)

    assert 0.0 <= result["primary_action"]["confidence"] <= 1.0
    assert 0.0 <= result["secondary_action"]["confidence"] <= 1.0


def test_build_action_suggestion_returns_stable_schema():
    result = build_action_suggestion(
        interpretation_profile={
            "decision_context": {
                "primary_decision": "career_decision",
                "decision_candidates": ["career_decision"],
            },
            "constraint_profile": {
                "primary_constraint": "time",
                "constraints": ["time"],
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

    _assert_stable_schema(result)
    assert result["action_source"]["source"] == "constraint_profile"
    assert result["primary_action"]["action_type"] == "detail_open"
    assert result["reflection_prompt"]["question"] == "次に小さく動かすなら、何から始めますか？"


def test_build_action_suggestion_uses_recommendation_input_profile_when_direct_inputs_are_missing():
    result = build_action_suggestion(
        recommendation_input_profile={
            "interpretation_profile": {
                "decision_context": {
                    "primary_decision": "relationship_decision",
                    "decision_candidates": ["relationship_decision"],
                },
            },
            "translation_result": {
                "action_context": "関係性を急いで決めず、今の距離感を見直す",
                "reflection_question_seed": "この関係で、今守りたい距離感は何ですか？",
            },
        }
    )

    _assert_stable_schema(result)
    assert result["action_source"]["source"] == "decision_context"
    assert result["primary_action"]["action_type"] == "detail_open"
    assert result["reflection_prompt"]["question"] == "この関係で、今守りたい距離感は何ですか？"
    assert result["source_keys"] == [
        "recommendation_input_profile",
        "interpretation_profile",
        "meaning_translation",
    ]


def test_build_action_suggestion_uses_recommendation_reason_action_when_meaning_translation_is_missing():
    result = build_action_suggestion(
        recommendation_reason_v4={
            "action": {
                "text": "次に取る行動として、保存してあとで見返します。",
                "source": "meaning_translation.action_context",
            }
        }
    )

    _assert_stable_schema(result)
    assert result["primary_action"]["action_type"] == "reflect"
    assert result["primary_action"]["description"] == "次に取る行動として、保存してあとで見返します。"
    assert result["action_source"]["source"] == "action_context"
    assert result["source_keys"] == ["recommendation_reason_v4"]


def test_build_action_suggestion_handles_missing_inputs_safely():
    result = build_action_suggestion()

    _assert_stable_schema(result)
    assert result["primary_action"] == {
        "label": "まず詳細を見て、行く理由を確認する",
        "description": "入力が少ないため、候補神社の詳細を見て判断材料を増やします。",
        "action_type": "detail_open",
        "confidence": 0.66,
    }
    assert result["secondary_action"]["action_type"] == "save"
    assert result["reflection_prompt"] == {
        "question": "この神社に行くとしたら、何を決めるためではなく、何を整理する時間にしたいですか？",
        "prompt_type": "before_visit",
        "source_seed": "fallback",
    }
    assert result["action_source"] == {
        "source": "fallback",
        "reason": "入力が不足しているため、詳細確認と保存を安全な初期提案にした",
    }


def test_attach_action_suggestion_v4_preview_adds_preview_without_changing_order_or_existing_suggestions():
    recs = {
        "recommendations": [
            {
                "id": 1,
                "name": "神社A",
                "_score_total": 10.0,
                "_explanation_payload": {
                    "history_context": {"label": "勝負"},
                    "action_suggestions": [
                        {
                            "id": "challenge_choose_this_week",
                            "title": "今週勝負したいことを1つ決める",
                            "description": "気合いではなく、今週動かす対象を1つに絞ります。",
                        }
                    ],
                },
            },
            {
                "id": 2,
                "name": "神社B",
                "_score_total": 9.0,
                "_explanation_payload": {
                    "history_context": {"label": "静寂"},
                    "action_suggestions": [],
                },
            },
        ]
    }

    result = attach_action_suggestion_v4_preview(recs)

    assert [rec["id"] for rec in result["recommendations"]] == [1, 2]
    assert result["recommendations"][0]["_score_total"] == 10.0
    assert result["recommendations"][0]["_explanation_payload"]["action_suggestions"][0]["id"] == "challenge_choose_this_week"
    _assert_stable_schema(result["recommendations"][0]["action_suggestion_v4_preview"])
    _assert_stable_schema(result["recommendations"][1]["action_suggestion_v4_preview"])


def test_attach_action_suggestion_v4_preview_handles_missing_recommendations_safely():
    recs = {"recommendations": None}

    assert attach_action_suggestion_v4_preview(recs) == {"recommendations": None}
