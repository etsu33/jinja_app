from __future__ import annotations

from temples.services.recommendation_reason_v4 import (
    build_recommendation_reason_quality_audit,
    build_recommendation_reason_v4,
)

def test_build_recommendation_reason_v4_returns_stable_schema():
    result = build_recommendation_reason_v4(
        interpretation_profile={
            "state_profile": {
                "primary_state": "uncertain",
            },
            "need_profile": {
                "primary_need_tag": "career",
                "need_tags": ["career"],
            },
            "direction_profile": {
                "direction": "review",
                "themes": ["静寂", "再出発"],
            },
            "emotion_profile": {
                "intensity": "medium",
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
        "used_fact",
        "used_interpretation",
        "used_action",
        "quality",
        "source",
    }
    assert isinstance(result["reason_text"], str)
    assert isinstance(result["fact"], dict)
    assert isinstance(result["interpretation"], dict)
    assert isinstance(result["action"], dict)
    assert isinstance(result["used_fact"], dict)
    assert isinstance(result["used_interpretation"], dict)
    assert isinstance(result["used_action"], dict)
    assert isinstance(result["quality"], dict)
    assert set(result["fact"].keys()) == {"label", "name", "deity", "shrine_history", "place_context", "history_theme", "goriyaku", "visit_style_tags", "evidence"}
    assert set(result["interpretation"].keys()) == {"theme", "text"}
    assert set(result["action"].keys()) == {"text", "source"}
    assert set(result["used_fact"].keys()) == {"deity", "shrine_history", "place_context", "goriyaku", "history_theme", "evidence"}
    assert set(result["used_interpretation"].keys()) == {"consultation_axis", "need_profile", "state_profile", "historical_interpretation", "theme"}
    assert set(result["used_action"].keys()) == {"action_context", "reflection_question_seed", "action_intent", "source"}
    assert set(result["quality"].keys()) == {"shrine_data_rate", "consultation_reflection_rate", "fallback_reason_rate", "evidence_rate", "action_grounding_rate", "is_ai_inference_only", "fallback_source"}
    assert set(result["source"].keys()) == {"fact", "interpretation", "action"}


def test_build_recommendation_reason_v4_builds_fact_layer_from_candidate_and_meaning():
    result = build_recommendation_reason_v4(
        meaning_translation={"history_theme": "再出発"},
        candidate_profile={
            "name": "神社A",
            "deity": "武神",
            "shrine_history": "古くから勝負の祈願で知られる",
            "place_context": "静かな丘の上",
            "history_theme": "再出発",
            "goriyaku": "仕事運",
            "visit_style_tags": ["quiet", "nature"],
        },
    )

    assert result["fact"] == {
        "label": "武神",
        "name": "神社A",
        "deity": "武神",
        "shrine_history": "古くから勝負の祈願で知られる",
        "place_context": "静かな丘の上",
        "history_theme": "再出発",
        "goriyaku": "仕事運",
        "visit_style_tags": ["quiet", "nature"],
        "evidence": [
            "deity:武神",
            "shrine_history:古くから勝負の祈願で知られる",
            "place_context:静かな丘の上",
            "history_theme:再出発",
            "goriyaku:仕事運",
            "visit_style_tags:quiet,nature",
            "name:神社A",
        ],
    }
    assert result["source"]["fact"] == "candidate_profile|meaning_translation"
    assert result["used_fact"] == {
        "deity": "武神",
        "shrine_history": "古くから勝負の祈願で知られる",
        "place_context": "静かな丘の上",
        "goriyaku": "仕事運",
        "history_theme": "再出発",
        "evidence": [
            "deity:武神",
            "shrine_history:古くから勝負の祈願で知られる",
            "place_context:静かな丘の上",
            "history_theme:再出発",
            "goriyaku:仕事運",
            "visit_style_tags:quiet,nature",
            "name:神社A",
        ],
    }


def test_build_recommendation_reason_v4_includes_shrine_name_in_reason_text():
    result = build_recommendation_reason_v4(
        interpretation_profile={
            "need_profile": {
                "primary_need_tag": "career",
                "need_tags": ["career"],
            },
        },
        meaning_translation={"history_theme": "再出発"},
        candidate_profile={
            "name": "神社A",
            "history_theme": "再出発",
            "goriyaku": "仕事運",
        },
    )

    assert "神社Aには、仕事運に関する情報があります。" in result["reason_text"]


def test_build_recommendation_reason_v4_keeps_goriyaku_and_visit_style_in_fact():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "神社D",
            "goriyaku": "縁結び",
            "visit_style_tags": ["quiet", "less_crowded"],
        },
    )

    assert result["fact"]["goriyaku"] == "縁結び"
    assert result["fact"]["visit_style_tags"] == ["quiet", "less_crowded"]
    assert "goriyaku:縁結び" in result["fact"]["evidence"]
    assert "visit_style_tags:quiet,less_crowded" in result["fact"]["evidence"]


def test_build_recommendation_reason_v4_reflects_goriyaku_and_visit_style_in_fact_text():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "神社E",
            "history_theme": "再出発",
            "goriyaku": "仕事運",
            "visit_style_tags": ["quiet", "nature"],
        },
    )

    assert "神社Eには、仕事運に関する情報があります。静かに参拝しやすい、自然を感じながら過ごしやすいも確認材料になります。" in result["reason_text"]


def test_build_recommendation_reason_v4_prioritizes_shrine_specific_fact_fields():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "神社F",
            "history_theme": "勝負",
            "goriyaku": "仕事運",
            "deity": "武神",
            "shrine_history": "古くから武運の祈願で知られる",
            "place_context": "駅から少し離れた静かな境内",
        },
    )

    assert result["fact"]["label"] == "武神"
    assert result["fact"]["deity"] == "武神"
    assert result["fact"]["shrine_history"] == "古くから武運の祈願で知られる"
    assert result["fact"]["place_context"] == "駅から少し離れた静かな境内"
    assert "deity:武神" in result["fact"]["evidence"]
    assert "shrine_history:古くから武運の祈願で知られる" in result["fact"]["evidence"]
    assert "place_context:駅から少し離れた静かな境内" in result["fact"]["evidence"]


def test_build_recommendation_reason_v4_builds_interpretation_layer_from_profiles():
    result = build_recommendation_reason_v4(
        interpretation_profile={
            "state_profile": {
                "primary_state": "uncertain",
            },
            "need_profile": {
                "primary_need_tag": "career",
                "need_tags": ["career"],
            },
            "direction_profile": {
                "direction": "review",
                "themes": ["静寂", "再出発"],
            },
            "emotion_profile": {
                "intensity": "medium",
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
        "text": "仕事や進路の流れを見直したい。判断に迷う様子を中心に、要素があります。",
    }
    assert result["source"]["interpretation"] == "interpretation_profile|meaning_translation"
    assert result["used_interpretation"] == {
        "consultation_axis": None,
        "need_profile": {
            "primary_need_tag": "career",
            "need_tags": ["career"],
        },
        "state_profile": {
            "primary_state": "uncertain",
            "secondary_states": [],
        },
        "historical_interpretation": None,
        "theme": "再出発",
    }


def test_build_recommendation_reason_v4_prioritizes_consultation_axis_in_interpretation():
    result = build_recommendation_reason_v4(
        interpretation_profile={
            "consultation_axis": "career_decision",
            "need_profile": {"primary_need_tag": "mental"},
            "state_profile": {"primary_state": "uncertain"},
        },
        meaning_translation={"history_theme": "再出発"},
    )

    assert result["interpretation"]["theme"] == "career_decision"
    assert "仕事や働き方の判断を中心にした相談として受け取れます" in result["interpretation"]["text"]
    assert "気持ちを落ち着け、今の状態を整理したい相談として受け取れます" not in result["interpretation"]["text"]

    assert result["used_interpretation"]["consultation_axis"] == "career_decision"
    assert result["used_interpretation"]["need_profile"] == {
        "primary_need_tag": "mental",
        "need_tags": [],
    }
    assert result["used_interpretation"]["state_profile"] == {
        "primary_state": "uncertain",
        "secondary_states": [],
    }



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
        "text": "参拝後は「次に小さく動かすなら、何から始めますか？」を一つだけ振り返ると、次の行動に残しやすくなります。",
        "source": "meaning_translation.reflection_question_seed",
    }
    assert result["source"]["action"] == "meaning_translation.reflection_question_seed"
    assert result["used_action"] == {
        "action_context": "問いを一つに絞り、今の状態を整理する",
        "reflection_question_seed": "次に小さく動かすなら、何から始めますか？",
        "action_intent": "reflect",
        "source": "meaning_translation.reflection_question_seed",
    }


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

    # translation_result.history_theme is Derived Meaning, not a raw Shrine Fact.
    assert result["fact"]["label"] == "縁結び"
    assert result["fact"]["history_theme"] is None
    assert result["interpretation"]["theme"] == "縁"
    assert result["action"]["text"] == "参拝前に、気持ちを落ち着け、今の状態を静かに見直すことを一つだけ決めておくと、行動につなげやすくなります。"


def test_build_recommendation_reason_quality_audit_calculates_rates_from_used_payload():
    reason = {
        "used_fact": {
            "deity": "武神",
            "shrine_history": "古くから武運の祈願で知られる",
            "place_context": "静かな境内",
            "goriyaku": "仕事運",
            "history_theme": None,
            "evidence": [
                "deity:武神",
                "shrine_history:古くから武運の祈願で知られる",
                "place_context:静かな境内",
            ],
        },
        "used_interpretation": {
            "consultation_axis": "career_decision",
            "need_profile": {"primary_need_tag": "career", "need_tags": ["career"]},
            "state_profile": {"primary_state": "uncertain", "secondary_states": []},
            "historical_interpretation": "古くから武運の祈願で知られるを、今回の相談を受け取る補助材料として参照しています。",
        },
        "used_action": {
            "action_context": "問いを一つに絞る",
            "reflection_question_seed": None,
            "action_intent": "reflect",
            "source": "meaning_translation.action_context",
        },
    }

    # QUALITY_FACT_KEYS = (deity, shrine_history, goriyaku, history_theme) の4キーのみが
    # Fact根拠として数えられる。history_theme は None のため 3/4 = 0.75。
    # evidence も同じ4キーでフィルタするため、place_context の evidence エントリは
    # 分子から除外され、deity + shrine_history の 2/4 = 0.5 になる。
    assert build_recommendation_reason_quality_audit(reason) == {
        "shrine_data_rate": 0.75,
        "consultation_reflection_rate": 1.0,
        "fallback_reason_rate": 0.0,
        "evidence_rate": 0.5,
        "action_grounding_rate": 0.6667,
        "is_ai_inference_only": False,
        "fallback_source": None,
    }


def test_build_recommendation_reason_quality_audit_detects_fallback_and_ai_inference_only():
    reason = {
        "used_fact": {
            "deity": None,
            "shrine_history": None,
            "place_context": None,
            "goriyaku": None,
            "history_theme": None,
            "evidence": [],
        },
        "used_interpretation": {
            "consultation_axis": None,
            "need_profile": {"primary_need_tag": None, "need_tags": []},
            "state_profile": {"primary_state": None, "secondary_states": []},
            "historical_interpretation": None,
        },
        "used_action": {
            "action_context": None,
            "reflection_question_seed": None,
            "action_intent": None,
            "source": "fallback",
        },
    }

    assert build_recommendation_reason_quality_audit(reason) == {
        "shrine_data_rate": 0.0,
        "consultation_reflection_rate": 0.0,
        "fallback_reason_rate": 1.0,
        "evidence_rate": 0.0,
        "action_grounding_rate": 0.0,
        "is_ai_inference_only": True,
        "fallback_source": "fallback",
    }

    
def test_build_recommendation_reason_v4_handles_missing_inputs_safely():
    result = build_recommendation_reason_v4()

    assert result == {
        "reason_text": "神社固有情報が十分でないため、確認できる情報をもとに候補として整理しています。相談内容から、今扱いたいテーマを読み取っています。参拝前に、次に確認したいことを一つだけ決めておきます。",
        "fact": {
            "label": "候補神社",
            "name": None,
            "deity": None,
            "shrine_history": None,
            "place_context": None,
            "history_theme": None,
            "goriyaku": None,
            "visit_style_tags": [],
            "evidence": [],
        },
        "interpretation": {
            "theme": "相談文脈",
            "text": "相談内容から、今扱いたいテーマを読み取っています。",
        },
        "action": {
            "text": "参拝前に、次に確認したいことを一つだけ決めておきます。",
            "source": "fallback",
        },
        "used_fact": {
            "deity": None,
            "shrine_history": None,
            "place_context": None,
            "goriyaku": None,
            "history_theme": None,
            "evidence": [],
        },
        "used_interpretation": {
            "consultation_axis": None,
            "need_profile": {
                "primary_need_tag": None,
                "need_tags": [],
            },
            "state_profile": {
                "primary_state": None,
                "secondary_states": [],
            },
            "historical_interpretation": None,
            "theme": "相談文脈",
        },
        "used_action": {
            "action_context": None,
            "reflection_question_seed": None,
            "action_intent": None,
            "source": "fallback",
        },
        "quality": {
            "shrine_data_rate": 0.0,
            "consultation_reflection_rate": 0.0,
            "fallback_reason_rate": 1.0,
            "evidence_rate": 0.0,
            "action_grounding_rate": 0.0,
            "is_ai_inference_only": True,
            "fallback_source": "fallback",
        },
        "source": {
            "fact": "candidate_profile|meaning_translation",
            "interpretation": "interpretation_profile|meaning_translation",
            "action": "fallback",
        },
    }


def test_build_recommendation_reason_v4_keeps_historical_interpretation_as_auxiliary_context():
    result = build_recommendation_reason_v4(
        interpretation_profile={
            "consultation_axis": "career_decision",
        },
        candidate_profile={
            "name": "神社G",
            "shrine_history": "古くから道を開く祈願で知られる",
        },
    )

    assert result["used_interpretation"]["historical_interpretation"] == "古くから道を開く祈願で知られるを、今回の相談を受け取る補助材料として参照しています。"
    assert "古くから道を開く祈願で知られるを、今回の相談を受け取る補助材料として参照しています。" not in result["action"]["text"]


def test_build_recommendation_reason_v4_does_not_expose_internal_keys_in_reason_text():
    result = build_recommendation_reason_v4(
        interpretation_profile={
            "need_profile": {
                "primary_need_tag": "career",
                "need_tags": ["career"],
            },
            "decision_context": {
                "primary_decision": "career_decision",
            },
            "constraint_profile": {
                "primary_constraint": "money",
            },
            "outcome_hint": {
                "primary_outcome": "decide",
            },
        },
        candidate_profile={
            "history_theme": "再出発",
            "goriyaku": "仕事運",
        },
    )

    assert "career" not in result["reason_text"]
    assert "career_decision" not in result["reason_text"]
    assert "money" not in result["reason_text"]
    assert "decide" not in result["reason_text"]
    assert "相談テーマ:" not in result["reason_text"]
    assert "判断文脈:" not in result["reason_text"]


def test_build_recommendation_reason_v4_uses_state_direction_and_emotion_profiles():
    result = build_recommendation_reason_v4(
        interpretation_profile={
            "state_profile": {
                "primary_state": "anxious",
            },
            "need_profile": {
                "primary_need_tag": "mental",
            },
            "direction_profile": {
                "direction": "stabilize",
                "themes": ["守り", "静寂"],
            },
            "emotion_profile": {
                "intensity": "high",
            },
        },
        meaning_translation={
            "history_theme": "守り",
        },
        candidate_profile={
            "name": "神社C",
            "history_theme": "守り",
        },
    )

    assert result["interpretation"] == {
        "theme": "守り",
        "text": "気持ちを落ち着け、今の状態を整理したい相談として受け取れます。不安や心配を中心に、要素が強めに出ています。",
    }
    assert "あなたは" not in result["reason_text"]


# --- Fact種別別コピー修正: place_context誤用防止・種別別文型のテスト ---


def test_build_recommendation_reason_v4_place_context_only_does_not_state_address_as_feature():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "place_context": "東京都渋谷区代々木神園町1-1",
        },
    )

    assert "東京都渋谷区代々木神園町1-1" not in result["reason_text"]
    assert "の特徴があります" not in result["reason_text"]
    assert (
        "神社固有情報が十分でないため、確認できる情報をもとに候補として整理しています。"
        in result["reason_text"]
    )


def test_build_recommendation_reason_v4_name_and_address_only_does_not_assert_unique_feature():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "place_context": "東京都渋谷区代々木神園町1-1",
        },
    )

    assert "東京都渋谷区代々木神園町1-1" not in result["reason_text"]
    assert "テスト神社には、東京都渋谷区代々木神園町1-1" not in result["reason_text"]


def test_build_recommendation_reason_v4_history_theme_only_is_prioritized_over_address():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "history_theme": "縁",
        },
    )

    assert "テスト神社は、縁という文脈で整理されています。" in result["reason_text"]

    result_with_address = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "history_theme": "縁",
            "place_context": "東京都渋谷区代々木神園町1-1",
        },
    )
    assert "テスト神社は、縁という文脈で整理されています。" in result_with_address["reason_text"]
    assert "東京都渋谷区代々木神園町1-1" not in result_with_address["reason_text"]


def test_build_recommendation_reason_v4_goriyaku_only_is_not_labeled_as_history_or_deity():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "goriyaku": "縁結び・厄除け",
        },
    )

    assert "テスト神社には、縁結び・厄除けに関する情報があります。" in result["reason_text"]
    assert "の特徴があります" not in result["reason_text"]
    assert "祀られています" not in result["reason_text"]
    assert "由緒" not in result["reason_text"]


def test_build_recommendation_reason_v4_deity_uses_enshrined_copy_not_feature_copy():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "deity": "テスト祭神",
        },
    )

    assert "テスト神社では、テスト祭神が祀られています。" in result["reason_text"]
    assert "テスト祭神の特徴があります" not in result["reason_text"]


def test_build_recommendation_reason_v4_shrine_history_uses_background_copy_without_broken_grammar():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "shrine_history": "戦災で焼失した後、氏子により再建された",
        },
    )

    assert (
        "テスト神社には、戦災で焼失した後、氏子により再建されたという背景があります。"
        in result["reason_text"]
    )
    assert "の特徴があります" not in result["reason_text"]
    # 日本語として破綻する二重句点・不自然な接続がないことを確認する
    assert "。。" not in result["reason_text"]
    assert "たの特徴" not in result["reason_text"]


# --- PR-B: Knowledge Fact confidenceによるReason表現強度制御 ---


def test_reason_v4_deity_confidence_high_uses_current_compatible_wording():
    result = build_recommendation_reason_v4(
        candidate_profile={"name": "テスト神社", "deity": "テスト祭神", "deity_confidence": "high"},
    )

    assert "テスト神社では、テスト祭神が祀られています。" in result["reason_text"]
    assert result["fact"]["deity"] == "テスト祭神"


def test_reason_v4_deity_confidence_medium_uses_weakened_wording():
    result = build_recommendation_reason_v4(
        candidate_profile={"name": "テスト神社", "deity": "テスト祭神", "deity_confidence": "medium"},
    )

    assert "テスト神社では、テスト祭神が祀られているとされています。" in result["reason_text"]
    # Fact値自体は加工されない(文体を混ぜ込まない)
    assert result["fact"]["deity"] == "テスト祭神"
    assert "可能性があります" not in result["reason_text"]
    assert "かもしれません" not in result["reason_text"]
    assert "おそらく" not in result["reason_text"]
    assert "。。" not in result["reason_text"]


def test_reason_v4_deity_confidence_low_suppresses_knowledge_fact_from_reason():
    result = build_recommendation_reason_v4(
        candidate_profile={"name": "テスト神社", "deity": "テスト祭神", "deity_confidence": "low"},
    )

    assert "テスト祭神" not in result["reason_text"]
    # Fact自体(fact.deity/used_fact.deity)もReason生成の出力からは無くなる
    # (Detail API・DB・Knowledge selectorには影響しない。これはReason生成内部の話)。
    assert result["fact"]["deity"] is None
    assert result["used_fact"]["deity"] is None


def test_reason_v4_deity_confidence_empty_string_uses_current_compatible_wording():
    result = build_recommendation_reason_v4(
        candidate_profile={"name": "テスト神社", "deity": "テスト祭神", "deity_confidence": ""},
    )

    assert "テスト神社では、テスト祭神が祀られています。" in result["reason_text"]
    assert result["fact"]["deity"] == "テスト祭神"


def test_reason_v4_deity_confidence_missing_key_uses_current_compatible_wording():
    """deity_confidence未指定(既存呼び出し互換)は現行のassertive表現のまま。"""
    result = build_recommendation_reason_v4(
        candidate_profile={"name": "テスト神社", "deity": "テスト祭神"},
    )

    assert "テスト神社では、テスト祭神が祀られています。" in result["reason_text"]


def test_reason_v4_shrine_history_confidence_high_uses_current_compatible_wording():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "shrine_history": "戦災で焼失した後、氏子により再建された",
            "shrine_history_confidence": "high",
        },
    )

    assert (
        "テスト神社には、戦災で焼失した後、氏子により再建されたという背景があります。"
        in result["reason_text"]
    )


def test_reason_v4_shrine_history_confidence_medium_uses_weakened_wording():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "shrine_history": "戦災で焼失した後、氏子により再建された",
            "shrine_history_confidence": "medium",
        },
    )

    assert (
        "テスト神社には、戦災で焼失した後、氏子により再建されたと伝えられています。"
        in result["reason_text"]
    )
    assert result["fact"]["shrine_history"] == "戦災で焼失した後、氏子により再建された"
    assert "。。" not in result["reason_text"]


def test_reason_v4_shrine_history_confidence_low_suppresses_knowledge_fact_from_reason():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "shrine_history": "戦災で焼失した後、氏子により再建された",
            "shrine_history_confidence": "low",
        },
    )

    assert "戦災で焼失した後" not in result["reason_text"]
    assert result["fact"]["shrine_history"] is None
    assert result["used_fact"]["shrine_history"] is None
    # deity/shrine_history両方無い場合の既存fallback文言へ落ちる
    assert "神社固有情報が十分でないため" in result["reason_text"]


def test_reason_v4_shrine_history_confidence_empty_string_uses_current_compatible_wording():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "shrine_history": "戦災で焼失した後、氏子により再建された",
            "shrine_history_confidence": "",
        },
    )

    assert (
        "テスト神社には、戦災で焼失した後、氏子により再建されたという背景があります。"
        in result["reason_text"]
    )


def test_reason_v4_low_deity_falls_through_to_high_shrine_history():
    """deityがlowでsuppressされても、shrine_historyが別confidenceなら独立してFactとして使われる。"""
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "deity": "テスト祭神",
            "deity_confidence": "low",
            "shrine_history": "戦災で焼失した後、氏子により再建された",
            "shrine_history_confidence": "high",
        },
    )

    assert "テスト祭神" not in result["reason_text"]
    assert (
        "テスト神社には、戦災で焼失した後、氏子により再建されたという背景があります。"
        in result["reason_text"]
    )


def test_reason_v4_fact_schema_unchanged_when_confidence_fields_present():
    """confidence関連fieldはfact dictへ混入しない(公開Schema不変)。"""
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "deity": "テスト祭神",
            "deity_confidence": "medium",
            "shrine_history": "背景",
            "shrine_history_confidence": "low",
        },
    )

    assert set(result["fact"].keys()) == {
        "label",
        "name",
        "deity",
        "shrine_history",
        "place_context",
        "history_theme",
        "goriyaku",
        "visit_style_tags",
        "evidence",
    }
    assert "reason_strength" not in result["fact"]
    assert "confidence" not in result["fact"]
    assert "deity_confidence" not in result["fact"]


def test_build_recommendation_reason_v4_all_facts_present_prioritizes_deity_and_excludes_place_context():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "deity": "テスト祭神",
            "shrine_history": "戦災で焼失した後、氏子により再建された",
            "place_context": "東京都渋谷区代々木神園町1-1",
            "history_theme": "縁",
            "goriyaku": "縁結び・厄除け",
            "visit_style_tags": ["quiet", "nature"],
        },
    )

    assert result["reason_text"].startswith("テスト神社では、テスト祭神が祀られています。")
    assert "縁結び・厄除けの要素" in result["reason_text"]
    assert "静かに参拝しやすい" in result["reason_text"]
    assert "自然を感じながら過ごしやすい" in result["reason_text"]
    assert "東京都渋谷区代々木神園町1-1" not in result["reason_text"]


def test_build_recommendation_reason_v4_no_facts_falls_back_without_fabricating_specificity():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
        },
    )

    assert (
        "神社固有情報が十分でないため、確認できる情報をもとに候補として整理しています。"
        in result["reason_text"]
    )
    assert result["quality"]["fallback_source"] == "fallback"


# --- 品質指標修正: QUALITY_FACT_KEYS(deity/shrine_history/goriyaku/history_theme)基準のテスト ---


def test_quality_name_only_has_no_shrine_grounding():
    result = build_recommendation_reason_v4(candidate_profile={"name": "候補神社"})
    quality = result["quality"]

    assert quality["shrine_data_rate"] == 0.0
    assert quality["evidence_rate"] == 0.0
    assert quality["is_ai_inference_only"] is True


def test_quality_address_only_has_no_shrine_grounding():
    result = build_recommendation_reason_v4(
        candidate_profile={"place_context": "東京都渋谷区代々木神園町1-1"}
    )
    quality = result["quality"]

    assert quality["shrine_data_rate"] == 0.0
    assert quality["evidence_rate"] == 0.0
    assert quality["is_ai_inference_only"] is True


def test_quality_name_and_address_only_has_no_shrine_grounding():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "候補神社",
            "place_context": "東京都渋谷区代々木神園町1-1",
        }
    )
    quality = result["quality"]

    assert quality["shrine_data_rate"] == 0.0
    assert quality["evidence_rate"] == 0.0
    assert quality["is_ai_inference_only"] is True


def test_quality_history_theme_only_is_grounded():
    result = build_recommendation_reason_v4(candidate_profile={"history_theme": "縁"})
    quality = result["quality"]

    assert quality["shrine_data_rate"] == 0.25
    assert quality["evidence_rate"] == 0.25
    assert quality["is_ai_inference_only"] is False


def test_quality_goriyaku_only_is_grounded():
    result = build_recommendation_reason_v4(candidate_profile={"goriyaku": "縁結び"})
    quality = result["quality"]

    assert quality["shrine_data_rate"] == 0.25
    assert quality["evidence_rate"] == 0.25
    assert quality["is_ai_inference_only"] is False


def test_quality_deity_only_is_grounded():
    result = build_recommendation_reason_v4(candidate_profile={"deity": "テスト祭神"})
    quality = result["quality"]

    assert quality["shrine_data_rate"] == 0.25
    assert quality["is_ai_inference_only"] is False


def test_quality_shrine_history_only_is_grounded():
    result = build_recommendation_reason_v4(
        candidate_profile={"shrine_history": "戦災で焼失した後、氏子により再建された"}
    )
    quality = result["quality"]

    assert quality["shrine_data_rate"] == 0.25
    assert quality["is_ai_inference_only"] is False


def test_quality_all_facts_present_reaches_full_rate_without_exceeding_one():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "テスト神社",
            "deity": "テスト祭神",
            "shrine_history": "戦災で焼失した後、氏子により再建された",
            "place_context": "東京都渋谷区代々木神園町1-1",
            "history_theme": "縁",
            "goriyaku": "縁結び・厄除け",
            "visit_style_tags": ["quiet", "nature"],
        }
    )
    quality = result["quality"]

    assert quality["shrine_data_rate"] == 1.0
    assert quality["evidence_rate"] == 1.0
    assert quality["evidence_rate"] <= 1.0
    assert quality["is_ai_inference_only"] is False


def test_quality_visit_style_tags_alone_do_not_count_as_shrine_grounding():
    # visit_style_tagsは参拝体験の補助属性として扱い、
    # 神社固有Factの品質指標(QUALITY_FACT_KEYS)には含めない契約を固定する。
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "候補神社",
            "visit_style_tags": ["quiet", "nature"],
        }
    )
    quality = result["quality"]

    assert quality["shrine_data_rate"] == 0.0
    assert quality["evidence_rate"] == 0.0
    assert quality["is_ai_inference_only"] is True


def test_quality_does_not_miscount_invalid_or_empty_fact_values():
    result = build_recommendation_reason_v4(
        candidate_profile={
            "name": "候補神社",
            "deity": "",
            "shrine_history": None,
            "goriyaku": [],
            "history_theme": {"unexpected": "shape"},
            "place_context": 12345,
        }
    )
    quality = result["quality"]

    assert quality["shrine_data_rate"] == 0.0
    assert quality["evidence_rate"] == 0.0
    assert quality["is_ai_inference_only"] is True
