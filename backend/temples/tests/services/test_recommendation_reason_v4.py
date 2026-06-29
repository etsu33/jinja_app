from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RecommendationReasonV4:
    reason_text: str
    fact: dict[str, Any] = field(default_factory=dict)
    interpretation: dict[str, Any] = field(default_factory=dict)
    action: dict[str, Any] = field(default_factory=dict)
    source: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "reason_text": self.reason_text,
            "fact": self.fact,
            "interpretation": self.interpretation,
            "action": self.action,
            "source": self.source,
        }


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    return item.strip()
        if isinstance(value, tuple):
            for item in value:
                if isinstance(item, str) and item.strip():
                    return item.strip()
    return None


NEED_COPY: dict[str, str] = {
    "mental": "気持ちを落ち着け、今の状態を整理したい",
    "rest": "疲れを整え、静かに回復したい",
    "career": "仕事や働き方を見直したい",
    "money": "生活や収入の土台を整えたい",
    "love": "人との縁や関係性を見直したい",
    "relationship": "人間関係を見直したい",
    "marriage": "良縁や結婚について考えたい",
    "communication": "伝え方や対話を整えたい",
    "study": "学びや積み重ねを続けたい",
    "health": "体調や健康面を気にかけたい",
    "protection": "不安な流れを落ち着けたい",
    "courage": "次に進むための一歩を決めたい",
    "focus": "集中や継続の流れを作りたい",
    "family": "家族に関する願いを整えたい",
    "travel_safe": "移動や旅の安全を考えたい",
}

DECISION_COPY: dict[str, str] = {
    "career_decision": "仕事や働き方について判断したい",
    "relationship_decision": "人との関係について見直したい",
    "money_decision": "お金や生活の判断を整えたい",
    "rest_or_action": "休むか動くかを見極めたい",
}

CONSTRAINT_COPY: dict[str, str] = {
    "time": "時間の余裕が少ない",
    "money": "お金や収入への不安がある",
    "energy": "体力や気力が落ちている",
    "relationship": "人間関係の制約がある",
}

OUTCOME_COPY: dict[str, str] = {
    "decide": "判断材料を持ち帰りたい",
    "calm": "気持ちを落ち着けたい",
    "move_forward": "小さく前に進みたい",
    "clarify": "考えを整理したい",
}

ACTION_INTENT_COPY: dict[str, str] = {
    "visit": "実際に足を運んで確認したい",
    "reflect": "問いを一つに絞って整理したい",
    "save": "今回の相談を残して振り返りたい",
}

STATE_COPY: dict[str, str] = {
    "tired": "疲れや休みたい気持ち",
    "anxious": "不安や心配",
    "uncertain": "判断に迷う様子",
    "stuck": "流れが止まっている感覚",
    "ready_to_change": "今の流れを切り替えたい気持ち",
}

DIRECTION_COPY: dict[str, str] = {
    "rest": "静かに回復する方向",
    "stabilize": "不安を落ち着ける方向",
    "review": "いまの状態を見直す方向",
    "reset": "流れを切り替える方向",
    "challenge": "次の行動を決める方向",
}


def _copy_for_key(mapping: dict[str, str], key: str | None) -> str | None:
    if not key:
        return None
    return mapping.get(key, key)


def _tone_suffix(interpretation_profile: dict[str, Any]) -> str:
    emotion_profile = _as_dict(interpretation_profile.get("emotion_profile"))
    intensity = _first_string(emotion_profile.get("intensity"))

    if intensity == "high":
        return "文脈が強めに含まれています"
    if intensity in {"medium", "low"}:
        return "文脈があります"
    return "文脈として受け取れます"


def _build_fact(candidate_profile: dict[str, Any], meaning_translation: dict[str, Any]) -> dict[str, Any]:
    history_theme = _first_string(candidate_profile.get("history_theme"), meaning_translation.get("history_theme"))
    goriyaku = _first_string(candidate_profile.get("goriyaku"), candidate_profile.get("goriyaku_tags"))
    name = _first_string(candidate_profile.get("name"))

    label = _first_string(history_theme, goriyaku, name, "候補神社") or "候補神社"
    evidence: list[str] = []

    if history_theme:
        evidence.append(f"history_theme:{history_theme}")
    if goriyaku:
        evidence.append(f"goriyaku:{goriyaku}")
    if name:
        evidence.append(f"name:{name}")

    return {
        "label": label,
        "evidence": evidence,
    }


def _build_interpretation(
    interpretation_profile: dict[str, Any],
    meaning_translation: dict[str, Any],
) -> dict[str, Any]:
    state_profile = _as_dict(interpretation_profile.get("state_profile"))
    need_profile = _as_dict(interpretation_profile.get("need_profile"))
    direction_profile = _as_dict(interpretation_profile.get("direction_profile"))
    decision_context = _as_dict(interpretation_profile.get("decision_context"))
    constraint_profile = _as_dict(interpretation_profile.get("constraint_profile"))
    outcome_hint = _as_dict(interpretation_profile.get("outcome_hint"))

    theme = _first_string(
        meaning_translation.get("history_theme"),
        direction_profile.get("themes"),
        need_profile.get("primary_need_tag"),
        decision_context.get("primary_decision"),
        constraint_profile.get("primary_constraint"),
        outcome_hint.get("primary_outcome"),
    ) or "相談文脈"

    shrine_context_need = _first_string(meaning_translation.get("shrine_context_need"))
    primary_need = _copy_for_key(
        NEED_COPY,
        _first_string(need_profile.get("primary_need_tag"), need_profile.get("need_tags")),
    )
    primary_decision = _copy_for_key(
        DECISION_COPY,
        _first_string(decision_context.get("primary_decision"), decision_context.get("decision_candidates")),
    )
    primary_constraint = _copy_for_key(
        CONSTRAINT_COPY,
        _first_string(constraint_profile.get("primary_constraint"), constraint_profile.get("constraints")),
    )
    primary_outcome = _copy_for_key(
        OUTCOME_COPY,
        _first_string(outcome_hint.get("primary_outcome"), outcome_hint.get("outcome_candidates")),
    )
    primary_state = _copy_for_key(STATE_COPY, _first_string(state_profile.get("primary_state")))
    direction = _copy_for_key(DIRECTION_COPY, _first_string(direction_profile.get("direction")))
    suffix = _tone_suffix(interpretation_profile)

    parts: list[str] = []
    if shrine_context_need:
        parts.append(shrine_context_need)
    elif primary_need:
        parts.append(f"{primary_need}相談として受け取れます")

    detail_parts: list[str] = []
    if primary_state:
        detail_parts.append(primary_state)
    if primary_decision:
        detail_parts.append(primary_decision)
    if primary_constraint:
        detail_parts.append(primary_constraint)
    if primary_outcome:
        detail_parts.append(primary_outcome)
    if direction:
        detail_parts.append(direction)

    if detail_parts:
        parts.append(f"{detail_parts[0]}を中心に、{suffix}")

    if not parts:
        parts.append("相談内容と神社側の文脈を照合する候補です")

    text = "。".join(parts[:2]) + "。"

    return {
        "theme": theme,
        "text": text,
    }


def _build_action(interpretation_profile: dict[str, Any], meaning_translation: dict[str, Any]) -> dict[str, Any]:
    action_intent = _as_dict(interpretation_profile.get("action_intent"))
    outcome_hint = _as_dict(interpretation_profile.get("outcome_hint"))

    action_context = _first_string(meaning_translation.get("action_context"))
    reflection_question_seed = _first_string(meaning_translation.get("reflection_question_seed"))
    intent = _first_string(action_intent.get("intent"), action_intent.get("candidates"))
    outcome = _first_string(outcome_hint.get("primary_outcome"), outcome_hint.get("outcome_candidates"))

    if reflection_question_seed:
        text = f"参拝後は「{reflection_question_seed}」を一つだけ振り返ると、次の行動に残しやすくなります。"
        source = "meaning_translation.reflection_question_seed"
    elif action_context:
        text = f"参拝前に、{action_context}ことを一つだけ決めておくと、行動につなげやすくなります。"
        source = "meaning_translation.action_context"
    elif intent:
        intent_copy = _copy_for_key(ACTION_INTENT_COPY, intent) or "次に取りたい行動"
        text = f"参拝前に、{intent_copy}ことを一つだけ決めておくと、行動につなげやすくなります。"
        source = "interpretation_profile.action_intent"
    elif outcome:
        outcome_copy = _copy_for_key(OUTCOME_COPY, outcome) or outcome
        text = f"参拝後は、{outcome_copy}方向に向けて次の小さな行動を一つだけ記録します。"
        source = "interpretation_profile.outcome_hint"
    else:
        text = "参拝前に、次に確認したいことを一つだけ決めておきます。"
        source = "fallback"

    return {
        "text": text,
        "source": source,
    }


def _build_reason_text(fact: dict[str, Any], interpretation: dict[str, Any], action: dict[str, Any]) -> str:
    fact_label = _first_string(fact.get("label")) or "候補神社"
    interpretation_text = _first_string(interpretation.get("text")) or "相談内容と神社側の文脈を照合しています。"
    action_text = _first_string(action.get("text")) or "参拝前に、次に確認したいことを一つだけ決めておきます。"

    if fact_label == "候補神社":
        fact_text = "この候補は、相談内容と神社側の文脈を照合する候補です。"
    else:
        fact_text = f"この候補には、{fact_label}というテーマが含まれています。"

    return "".join([fact_text, interpretation_text, action_text])


def build_recommendation_reason_v4(
    *,
    recommendation_input_profile: dict[str, Any] | None = None,
    interpretation_profile: dict[str, Any] | None = None,
    meaning_translation: dict[str, Any] | None = None,
    candidate_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a preview-only Recommendation Reason v4 payload.

    This function is deterministic and side-effect free.
    It does not change ranking, Score v3 weights, or existing recommendation reason output.
    """

    recommendation_input = _as_dict(recommendation_input_profile)
    interpretation = _as_dict(interpretation_profile) or _as_dict(recommendation_input.get("interpretation_profile"))
    meaning = _as_dict(meaning_translation) or _as_dict(recommendation_input.get("translation_result"))
    candidate = _as_dict(candidate_profile) or _as_dict(recommendation_input.get("candidate_profile"))

    fact = _build_fact(candidate, meaning)
    interpretation_layer = _build_interpretation(interpretation, meaning)
    action = _build_action(interpretation, meaning)

    return RecommendationReasonV4(
        reason_text=_build_reason_text(fact, interpretation_layer, action),
        fact=fact,
        interpretation=interpretation_layer,
        action=action,
        source={
            "fact": "candidate_profile|meaning_translation",
            "interpretation": "interpretation_profile|meaning_translation",
            "action": action.get("source") or "fallback",
        },
    ).as_dict()


__all__ = [
    "RecommendationReasonV4",
    "build_recommendation_reason_v4",
]
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
        "text": "仕事や進路の流れを見直したい。判断に迷う様子を中心に、文脈があります。",
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
        "reason_text": "この候補は、相談内容と神社側の文脈を照合する候補です。相談内容と神社側の文脈を照合する候補です。参拝前に、次に確認したいことを一つだけ決めておきます。",
        "fact": {
            "label": "候補神社",
            "evidence": [],
        },
        "interpretation": {
            "theme": "相談文脈",
            "text": "相談内容と神社側の文脈を照合する候補です。",
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
        "text": "気持ちを落ち着け、今の状態を整理したい相談として受け取れます。不安や心配を中心に、文脈が強めに含まれています。",
    }
    assert "あなたは" not in result["reason_text"]
