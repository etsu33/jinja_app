

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ActionType = Literal["detail_open", "route_open", "save", "visit", "reflect", "pause"]
PromptType = Literal["before_visit", "after_visit", "decision", "emotion", "constraint"]
ActionSourceType = Literal[
    "decision_context",
    "constraint_profile",
    "outcome_hint",
    "action_context",
    "reflection_question_seed",
    "fallback",
]

ACTION_TYPE_VALUES = {"detail_open", "route_open", "save", "visit", "reflect", "pause"}
PROMPT_TYPE_VALUES = {"before_visit", "after_visit", "decision", "emotion", "constraint"}
ACTION_SOURCE_VALUES = {
    "decision_context",
    "constraint_profile",
    "outcome_hint",
    "action_context",
    "reflection_question_seed",
    "fallback",
}


@dataclass(frozen=True)
class ActionItem:
    label: str
    description: str
    action_type: ActionType
    confidence: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "description": self.description,
            "action_type": self.action_type,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class ReflectionPrompt:
    question: str
    prompt_type: PromptType
    source_seed: str

    def as_dict(self) -> dict[str, str]:
        return {
            "question": self.question,
            "prompt_type": self.prompt_type,
            "source_seed": self.source_seed,
        }


@dataclass(frozen=True)
class ActionSource:
    source: ActionSourceType
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "source": self.source,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ActionSuggestionV4:
    primary_action: ActionItem
    secondary_action: ActionItem
    reflection_prompt: ReflectionPrompt
    action_source: ActionSource
    preview: bool = True
    version: str = "v4"
    source_keys: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "primary_action": self.primary_action.as_dict(),
            "secondary_action": self.secondary_action.as_dict(),
            "reflection_prompt": self.reflection_prompt.as_dict(),
            "action_source": self.action_source.as_dict(),
            "preview": self.preview,
            "version": self.version,
            "source_keys": list(self.source_keys),
        }


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (list, tuple)):
            for item in value:
                if isinstance(item, str) and item.strip():
                    return item.strip()
    return None


def _confidence(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 2)))


def _build_primary_action(
    *,
    action_context: str | None,
    reflection_question_seed: str | None,
    primary_constraint: str | None,
    primary_decision: str | None,
    primary_outcome: str | None,
) -> ActionItem:
    if primary_constraint:
        return ActionItem(
            label="まず詳細を見て、無理なく行けるか確認する",
            description="時間・体力・お金などの制約がある場合は、すぐ行くよりも負担を確認する段階です。",
            action_type="detail_open",
            confidence=_confidence(0.84),
        )

    if primary_decision:
        return ActionItem(
            label="詳細を見て、判断材料を一つ増やす",
            description="今すぐ結論を出すのではなく、この神社が判断したいテーマとどう接続しているかを確認します。",
            action_type="detail_open",
            confidence=_confidence(0.82),
        )

    if action_context:
        return ActionItem(
            label="行く前に、今日の問いを一つだけ決める",
            description=action_context,
            action_type="reflect",
            confidence=_confidence(0.78),
        )

    if reflection_question_seed:
        return ActionItem(
            label="参拝前に、整理したい問いを一つ決める",
            description="答えを急がず、参拝中に静かに置いておきたい問いを一つだけ決めます。",
            action_type="reflect",
            confidence=_confidence(0.76),
        )

    if primary_outcome:
        return ActionItem(
            label="望む着地点を一つだけ言葉にする",
            description="大きく動く前に、今回の相談で何を整理したいのかを短く確認します。",
            action_type="pause",
            confidence=_confidence(0.72),
        )

    return ActionItem(
        label="まず詳細を見て、行く理由を確認する",
        description="入力が少ないため、候補神社の詳細を見て判断材料を増やします。",
        action_type="detail_open",
        confidence=_confidence(0.66),
    )


def _build_secondary_action(primary_action_type: str) -> ActionItem:
    if primary_action_type == "save":
        return ActionItem(
            label="経路を確認して、行ける日を考える",
            description="候補として残したあと、無理なく行ける距離かを確認します。",
            action_type="route_open",
            confidence=_confidence(0.72),
        )

    if primary_action_type == "route_open":
        return ActionItem(
            label="候補として保存して、あとで見返す",
            description="今すぐ行けない場合でも、判断材料として残しておけます。",
            action_type="save",
            confidence=_confidence(0.74),
        )

    return ActionItem(
        label="候補として保存して、あとで見返す",
        description="今すぐ決めきれない場合でも、後から相談内容と一緒に見返せます。",
        action_type="save",
        confidence=_confidence(0.74),
    )


def _build_reflection_prompt(
    *,
    reflection_question_seed: str | None,
    primary_constraint: str | None,
    primary_decision: str | None,
    primary_outcome: str | None,
) -> ReflectionPrompt:
    if reflection_question_seed:
        return ReflectionPrompt(
            question=reflection_question_seed,
            prompt_type="before_visit",
            source_seed=reflection_question_seed,
        )

    if primary_constraint:
        return ReflectionPrompt(
            question="今の制約の中で、無理なくできる一歩はどこまでですか？",
            prompt_type="constraint",
            source_seed=primary_constraint,
        )

    if primary_decision:
        return ReflectionPrompt(
            question="この判断で、急いで決めたいことと、まだ保留してよいことは何ですか？",
            prompt_type="decision",
            source_seed=primary_decision,
        )

    if primary_outcome:
        return ReflectionPrompt(
            question="今回の相談で、最初に整理できたら十分なことは何ですか？",
            prompt_type="emotion",
            source_seed=primary_outcome,
        )

    return ReflectionPrompt(
        question="この神社に行くとしたら、何を決めるためではなく、何を整理する時間にしたいですか？",
        prompt_type="before_visit",
        source_seed="fallback",
    )


def _build_action_source(
    *,
    action_context: str | None,
    reflection_question_seed: str | None,
    primary_constraint: str | None,
    primary_decision: str | None,
    primary_outcome: str | None,
) -> ActionSource:
    if primary_constraint:
        return ActionSource(
            source="constraint_profile",
            reason="制約があるため、すぐ参拝ではなく詳細確認を優先した",
        )
    if primary_decision:
        return ActionSource(
            source="decision_context",
            reason="判断文脈があるため、決断前の材料確認を優先した",
        )
    if action_context:
        return ActionSource(
            source="action_context",
            reason="意味変換層の行動文脈をもとに提案した",
        )
    if reflection_question_seed:
        return ActionSource(
            source="reflection_question_seed",
            reason="振り返り問いの種をもとに提案した",
        )
    if primary_outcome:
        return ActionSource(
            source="outcome_hint",
            reason="望む着地点をもとに小さな整理行動へ落とした",
        )
    return ActionSource(
        source="fallback",
        reason="入力が不足しているため、詳細確認と保存を安全な初期提案にした",
    )


def build_action_suggestion(
    *,
    recommendation_input_profile: dict[str, Any] | None = None,
    interpretation_profile: dict[str, Any] | None = None,
    meaning_translation: dict[str, Any] | None = None,
    recommendation_reason_v4: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a preview-only Action Suggestion v4 payload.

    This function is deterministic and side-effect free.
    It does not change ranking, recommendation score, or existing action_suggestions output.
    """

    recommendation_input = _as_dict(recommendation_input_profile)
    interpretation = _as_dict(interpretation_profile) or _as_dict(recommendation_input.get("interpretation_profile"))
    meaning = _as_dict(meaning_translation) or _as_dict(recommendation_input.get("translation_result"))
    reason = _as_dict(recommendation_reason_v4)

    decision_context = _as_dict(interpretation.get("decision_context"))
    constraint_profile = _as_dict(interpretation.get("constraint_profile"))
    outcome_hint = _as_dict(interpretation.get("outcome_hint"))

    action_layer = _as_dict(reason.get("action"))

    primary_decision = _first_string(
        decision_context.get("primary_decision"),
        decision_context.get("decision_candidates"),
    )
    primary_constraint = _first_string(
        constraint_profile.get("primary_constraint"),
        constraint_profile.get("constraints"),
    )
    primary_outcome = _first_string(
        outcome_hint.get("primary_outcome"),
        outcome_hint.get("outcome_candidates"),
    )
    action_context = _first_string(
        meaning.get("action_context"),
        action_layer.get("text"),
    )
    reflection_question_seed = _first_string(meaning.get("reflection_question_seed"))

    primary_action = _build_primary_action(
        action_context=action_context,
        reflection_question_seed=reflection_question_seed,
        primary_constraint=primary_constraint,
        primary_decision=primary_decision,
        primary_outcome=primary_outcome,
    )
    secondary_action = _build_secondary_action(primary_action.action_type)
    reflection_prompt = _build_reflection_prompt(
        reflection_question_seed=reflection_question_seed,
        primary_constraint=primary_constraint,
        primary_decision=primary_decision,
        primary_outcome=primary_outcome,
    )
    action_source = _build_action_source(
        action_context=action_context,
        reflection_question_seed=reflection_question_seed,
        primary_constraint=primary_constraint,
        primary_decision=primary_decision,
        primary_outcome=primary_outcome,
    )

    source_keys = [
        key
        for key, value in {
            "recommendation_input_profile": recommendation_input,
            "interpretation_profile": interpretation,
            "meaning_translation": meaning,
            "recommendation_reason_v4": reason,
        }.items()
        if value
    ]

    return ActionSuggestionV4(
        primary_action=primary_action,
        secondary_action=secondary_action,
        reflection_prompt=reflection_prompt,
        action_source=action_source,
        source_keys=source_keys,
    ).as_dict()


def attach_action_suggestion_v4_preview(recs: dict[str, Any]) -> dict[str, Any]:
    """Attach Action Suggestion v4 preview to each recommendation.

    Preview payload is additive only. Existing recommendation order, score, reason,
    and `_explanation_payload.action_suggestions` are not modified.
    """

    recommendations = [
        rec for rec in _as_list(recs.get("recommendations"))
        if isinstance(rec, dict)
    ]

    for rec in recommendations:
        explanation_payload = _as_dict(rec.get("_explanation_payload"))
        history_context = _as_dict(explanation_payload.get("history_context"))
        action_suggestions = _as_list(explanation_payload.get("action_suggestions"))
        first_action_suggestion = action_suggestions[0] if action_suggestions and isinstance(action_suggestions[0], dict) else {}

        meaning_translation = {
            "history_theme": _first_string(history_context.get("label"), rec.get("history_theme")),
            "action_context": _first_string(
                first_action_suggestion.get("description"),
                rec.get("action_meaning"),
            ),
            "reflection_question_seed": _first_string(
                first_action_suggestion.get("title"),
                "この候補を見たあと、何を整理したいですか？",
            ),
        }

        rec["action_suggestion_v4_preview"] = build_action_suggestion(
            meaning_translation=meaning_translation,
        )

    return recs


__all__ = [
    "ACTION_SOURCE_VALUES",
    "ACTION_TYPE_VALUES",
    "PROMPT_TYPE_VALUES",
    "ActionItem",
    "ActionSource",
    "ActionSuggestionV4",
    "ReflectionPrompt",
    "attach_action_suggestion_v4_preview",
    "build_action_suggestion",
]
