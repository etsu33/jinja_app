

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


StateChangeDirection = Literal["improved", "unchanged", "worsened", "unknown"]


@dataclass(frozen=True)
class ReflectionStateChange:
    state_change_direction: StateChangeDirection
    state_change_summary: str
    next_need_hint: list[str]
    next_history_theme_hint: list[str]


IMPROVED_WORDS = (
    "落ち着いた",
    "軽くなった",
    "少し軽い",
    "整理できた",
    "前に進む",
    "進めそう",
    "すっきり",
    "区切り",
    "一区切り",
    "安心",
)

WORSENED_WORDS = (
    "もっと不安",
    "まだ不安",
    "苦しい",
    "つらい",
    "辛い",
    "迷っている",
    "決めきれない",
    "変わらない不安",
)

UNCHANGED_WORDS = (
    "変わらない",
    "特に変化なし",
    "まだ分からない",
    "わからない",
)

NEED_HINT_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("courage", ("動きたい", "進みたい", "前に進む", "踏み出", "挑戦", "決めたい")),
    ("mental", ("不安", "落ち着", "気持ち", "心", "しんどい", "つらい", "辛い")),
    ("career", ("仕事", "転職", "キャリア", "働き方", "方向性", "独立")),
    ("relationship", ("人間関係", "人とのつながり", "関係", "連絡", "家族", "職場")),
    ("love", ("恋愛", "縁", "出会い", "復縁", "結婚")),
    ("rest", ("疲れ", "休み", "休息", "眠れ", "静か", "回復")),
    ("protection", ("守り", "厄", "清め", "お祓い", "流れが悪い")),
)


def _text_from_reflection(reflection: Any) -> str:
    return " ".join(
        str(value or "").strip()
        for value in (
            getattr(reflection, "mood_before", ""),
            getattr(reflection, "mood_after", ""),
            getattr(reflection, "answer", ""),
        )
        if str(value or "").strip()
    )


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    return any(word in text for word in words)


def infer_state_change_direction(reflection: Any) -> StateChangeDirection:
    text = _text_from_reflection(reflection)
    mood_before = str(getattr(reflection, "mood_before", "") or "").strip()
    mood_after = str(getattr(reflection, "mood_after", "") or "").strip()

    if not text:
        return "unknown"

    if mood_before and mood_after and mood_before == mood_after:
        return "unchanged"

    if _contains_any(text, WORSENED_WORDS):
        return "worsened"

    if _contains_any(text, IMPROVED_WORDS):
        return "improved"

    if _contains_any(text, UNCHANGED_WORDS):
        return "unchanged"

    return "unknown"


def build_next_need_hint(reflection: Any) -> list[str]:
    text = _text_from_reflection(reflection)
    hints: list[str] = []

    for need_tag, keywords in NEED_HINT_KEYWORDS:
        if _contains_any(text, keywords):
            hints.append(need_tag)

    return hints[:3]


def build_next_history_theme_hint(reflection: Any) -> list[str]:
    text = _text_from_reflection(reflection)
    history_theme = str(getattr(reflection, "history_theme", "") or "").strip()
    direction = infer_state_change_direction(reflection)

    if history_theme == "静寂":
        if direction == "improved" and _contains_any(text, ("動きたい", "進みたい", "踏み出")):
            return ["勝負", "再出発"]
        if direction in ("unchanged", "worsened"):
            return ["守り", "静寂"]

    if history_theme == "守り":
        if direction == "improved":
            return ["再出発"]
        if direction in ("unchanged", "worsened"):
            return ["守り", "静寂"]

    if history_theme == "勝負":
        if _contains_any(text, ("決めきれない", "迷っている", "まだ不安")):
            return ["静寂", "守り"]
        if direction == "improved":
            return ["勝負", "再出発"]

    if history_theme == "縁":
        if _contains_any(text, ("連絡", "伝え", "会う", "つながり")):
            return ["縁", "勝負"]

    if history_theme:
        return [history_theme]

    return []


def build_state_change_summary(reflection: Any) -> str:
    direction = infer_state_change_direction(reflection)
    next_need_hint = build_next_need_hint(reflection)
    next_history_theme_hint = build_next_history_theme_hint(reflection)

    if direction == "improved":
        base = "参拝後に状態が少し整った可能性があります。"
    elif direction == "worsened":
        base = "参拝後も不安や迷いが残っている可能性があります。"
    elif direction == "unchanged":
        base = "参拝前後で大きな変化はまだ見えにくい状態です。"
    else:
        base = "参拝後の状態変化はまだ明確には判定できません。"

    if next_need_hint or next_history_theme_hint:
        return f"{base} 次回推薦では、振り返り内容を補助情報として扱います。"

    return base


def build_reflection_state_change(reflection: Any) -> ReflectionStateChange:
    return ReflectionStateChange(
        state_change_direction=infer_state_change_direction(reflection),
        state_change_summary=build_state_change_summary(reflection),
        next_need_hint=build_next_need_hint(reflection),
        next_history_theme_hint=build_next_history_theme_hint(reflection),
    )
