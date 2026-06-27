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


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


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
    need_profile = _as_dict(interpretation_profile.get("need_profile"))
    decision_context = _as_dict(interpretation_profile.get("decision_context"))
    constraint_profile = _as_dict(interpretation_profile.get("constraint_profile"))
    outcome_hint = _as_dict(interpretation_profile.get("outcome_hint"))

    theme = _first_string(
        meaning_translation.get("history_theme"),
        need_profile.get("primary_need_tag"),
        decision_context.get("primary_decision"),
        constraint_profile.get("primary_constraint"),
        outcome_hint.get("primary_outcome"),
    ) or "相談文脈"

    shrine_context_need = _first_string(meaning_translation.get("shrine_context_need"))
    primary_need = _first_string(need_profile.get("primary_need_tag"), need_profile.get("need_tags"))
    primary_decision = _first_string(decision_context.get("primary_decision"), decision_context.get("decision_candidates"))
    primary_constraint = _first_string(constraint_profile.get("primary_constraint"), constraint_profile.get("constraints"))
    primary_outcome = _first_string(outcome_hint.get("primary_outcome"), outcome_hint.get("outcome_candidates"))

    parts: list[str] = []
    if shrine_context_need:
        parts.append(shrine_context_need)
    if primary_need:
        parts.append(f"相談テーマ:{primary_need}")
    if primary_decision:
        parts.append(f"判断文脈:{primary_decision}")
    if primary_constraint:
        parts.append(f"制約:{primary_constraint}")
    if primary_outcome:
        parts.append(f"着地点:{primary_outcome}")

    text = " / ".join(parts) if parts else "相談内容と神社側の文脈を照合する候補です。"

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

    if action_context and reflection_question_seed:
        text = f"{action_context}。振り返りでは「{reflection_question_seed}」を確認します。"
        source = "meaning_translation.action_context+reflection_question_seed"
    elif action_context:
        text = action_context
        source = "meaning_translation.action_context"
    elif reflection_question_seed:
        text = f"振り返りでは「{reflection_question_seed}」を確認します。"
        source = "meaning_translation.reflection_question_seed"
    elif intent:
        text = f"次に取る行動として、{intent}を小さく確認します。"
        source = "interpretation_profile.action_intent"
    elif outcome:
        text = f"望む着地点として、{outcome}に向けた小さな確認を行います。"
        source = "interpretation_profile.outcome_hint"
    else:
        text = "次に確認したいことを一つだけ決めます。"
        source = "fallback"

    return {
        "text": text,
        "source": source,
    }


def _build_reason_text(fact: dict[str, Any], interpretation: dict[str, Any], action: dict[str, Any]) -> str:
    fact_label = _first_string(fact.get("label")) or "この候補"
    interpretation_text = _first_string(interpretation.get("text")) or "相談内容と神社側の文脈を照合しています。"
    action_text = _first_string(action.get("text")) or "次に確認したいことを一つだけ決めます。"

    return f"{fact_label}は、{interpretation_text} {action_text}"


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
