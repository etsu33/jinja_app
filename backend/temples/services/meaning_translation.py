

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


HISTORY_THEME_BY_DIRECTION: dict[str, str] = {
    "rest": "静寂",
    "stabilize": "守り",
    "review": "静寂",
    "reset": "再出発",
    "challenge": "勝負",
}

HISTORY_THEME_BY_NEED: dict[str, str] = {
    "mental": "静寂",
    "rest": "静寂",
    "career": "再出発",
    "money": "守り",
    "love": "縁",
    "study": "学び",
    "courage": "勝負",
}

SHRINE_CONTEXT_NEED_BY_NEED: dict[str, str] = {
    "mental": "気持ちを落ち着け、今の状態を整理したい",
    "rest": "疲れを整え、静かに回復したい",
    "career": "仕事や進路の流れを見直したい",
    "money": "生活や収入の土台を整えたい",
    "love": "人との縁や関係性を見直したい",
    "study": "学びや積み重ねを続けたい",
    "courage": "次に進むための一歩を決めたい",
}

ACTION_CONTEXT_BY_INTENT: dict[str, str] = {
    "visit": "実際に足を運び、今の状態を確認する",
    "reflect": "問いを一つに絞り、今の状態を整理する",
    "save": "今回の相談を残し、あとで振り返れるようにする",
}

REFLECTION_QUESTION_BY_HISTORY_THEME: dict[str, str] = {
    "静寂": "今、いちばん静かに整理したいことは何ですか？",
    "守り": "今の生活や気持ちの中で、守りたい土台は何ですか？",
    "再出発": "次に小さく動かすなら、何から始めますか？",
    "勝負": "今、勇気を使うならどの選択に向けたいですか？",
    "縁": "今、大切にしたい関係や距離感は何ですか？",
    "学び": "今後も積み重ねたい学びや行動は何ですか？",
}


@dataclass(frozen=True)
class MeaningTranslationResult:
    history_theme: str | None = None
    shrine_context_need: str | None = None
    action_context: str | None = None
    reflection_question_seed: str | None = None
    source: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "history_theme": self.history_theme,
            "shrine_context_need": self.shrine_context_need,
            "action_context": self.action_context,
            "reflection_question_seed": self.reflection_question_seed,
            "source": self.source,
        }


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _first_string(value: Any) -> str | None:
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


def _resolve_history_theme(
    *,
    direction_profile: dict[str, Any],
    need_profile: dict[str, Any],
) -> tuple[str | None, str]:
    direction = _first_string(direction_profile.get("direction"))
    if direction and direction in HISTORY_THEME_BY_DIRECTION:
        return HISTORY_THEME_BY_DIRECTION[direction], "direction_profile.direction"

    primary_need_tag = _first_string(need_profile.get("primary_need_tag"))
    if primary_need_tag and primary_need_tag in HISTORY_THEME_BY_NEED:
        return HISTORY_THEME_BY_NEED[primary_need_tag], "need_profile.primary_need_tag"

    need_tags = need_profile.get("need_tags")
    need_tag = _first_string(need_tags)
    if need_tag and need_tag in HISTORY_THEME_BY_NEED:
        return HISTORY_THEME_BY_NEED[need_tag], "need_profile.need_tags"

    return None, "fallback.none"


def _resolve_shrine_context_need(need_profile: dict[str, Any]) -> tuple[str | None, str]:
    primary_need_tag = _first_string(need_profile.get("primary_need_tag"))
    if primary_need_tag and primary_need_tag in SHRINE_CONTEXT_NEED_BY_NEED:
        return SHRINE_CONTEXT_NEED_BY_NEED[primary_need_tag], "need_profile.primary_need_tag"

    need_tags = need_profile.get("need_tags")
    need_tag = _first_string(need_tags)
    if need_tag and need_tag in SHRINE_CONTEXT_NEED_BY_NEED:
        return SHRINE_CONTEXT_NEED_BY_NEED[need_tag], "need_profile.need_tags"

    return None, "fallback.none"


def _resolve_action_context(action_intent: dict[str, Any]) -> tuple[str | None, str]:
    intent = _first_string(action_intent.get("intent"))
    if intent and intent in ACTION_CONTEXT_BY_INTENT:
        return ACTION_CONTEXT_BY_INTENT[intent], "action_intent.intent"

    candidates = action_intent.get("candidates")
    candidate = _first_string(candidates)
    if candidate and candidate in ACTION_CONTEXT_BY_INTENT:
        return ACTION_CONTEXT_BY_INTENT[candidate], "action_intent.candidates"

    return None, "fallback.none"


def _resolve_reflection_question_seed(history_theme: str | None) -> tuple[str | None, str]:
    if history_theme and history_theme in REFLECTION_QUESTION_BY_HISTORY_THEME:
        return REFLECTION_QUESTION_BY_HISTORY_THEME[history_theme], "history_theme"
    return None, "fallback.none"


def translate_meaning(interpretation_profile: dict[str, Any] | None) -> dict[str, Any]:
    """Translate interpretation profile into meaning-layer context.

    v1 is intentionally deterministic and side-effect free.
    It does not change recommendation ranking, scoring, or generated copy.
    """

    profile = _as_dict(interpretation_profile)
    need_profile = _as_dict(profile.get("need_profile"))
    direction_profile = _as_dict(profile.get("direction_profile"))
    action_intent = _as_dict(profile.get("action_intent"))

    history_theme, history_theme_source = _resolve_history_theme(
        direction_profile=direction_profile,
        need_profile=need_profile,
    )
    shrine_context_need, shrine_context_need_source = _resolve_shrine_context_need(need_profile)
    action_context, action_context_source = _resolve_action_context(action_intent)
    reflection_question_seed, reflection_question_seed_source = _resolve_reflection_question_seed(history_theme)

    return MeaningTranslationResult(
        history_theme=history_theme,
        shrine_context_need=shrine_context_need,
        action_context=action_context,
        reflection_question_seed=reflection_question_seed,
        source={
            "history_theme": history_theme_source,
            "shrine_context_need": shrine_context_need_source,
            "action_context": action_context_source,
            "reflection_question_seed": reflection_question_seed_source,
        },
    ).as_dict()


__all__ = [
    "MeaningTranslationResult",
    "translate_meaning",
]
