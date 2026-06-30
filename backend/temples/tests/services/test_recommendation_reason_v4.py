from __future__ import annotations

from temples.services.recommendation_reason_v4 import build_recommendation_reason_v4


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
        "source",
    }
    assert isinstance(result["reason_text"], str)
    assert isinstance(result["fact"], dict)
    assert isinstance(result["interpretation"], dict)
    assert isinstance(result["action"], dict)
    assert isinstance(result["source"], dict)
    assert set(result["fact"].keys()) == {"label", "name", "deity", "shrine_history", "place_context", "goriyaku", "visit_style_tags", "evidence"}
    assert set(result["interpretation"].keys()) == {"theme", "text"}
    assert set(result["action"].keys()) == {"text", "source"}
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

    assert "神社Aには、再出発の特徴があり、仕事運の要素も材料になります。" in result["reason_text"]


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

    assert "神社Eには、再出発の特徴があり、仕事運の要素、静かに参拝しやすい、自然を感じながら過ごしやすいも材料になります。" in result["reason_text"]


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
    assert result["action"]["text"] == "参拝前に、気持ちを落ち着け、今の状態を静かに見直すことを一つだけ決めておくと、行動につなげやすくなります。"


def test_build_recommendation_reason_v4_handles_missing_inputs_safely():
    result = build_recommendation_reason_v4()

    assert result == {
        "reason_text": "この候補は、相談内容と神社側の情報を照合する候補です。相談内容から、今扱いたいテーマを読み取っています。参拝前に、次に確認したいことを一つだけ決めておきます。",
        "fact": {
            "label": "候補神社",
            "name": None,
            "deity": None,
            "shrine_history": None,
            "place_context": None,
            "goriyaku": None,
            "visit_style_tags": [],
            "evidence": [],
        },
        "interpretation": {
            "theme": "相談文脈",
            "text": "相談内容から、今扱いたいテーマを読み取る候補です。",
        },
        "action": {
            "text": "参拝前に、次に確認したいことを一つだけ決めておきます。",
            "source": "fallback",
        },
        "source": {
            "fact": "candidate_profile|meaning_translation",
            "interpretation": "interpretation_profile|meaning_translation",
            "action": "fallback",
        },
    }


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
