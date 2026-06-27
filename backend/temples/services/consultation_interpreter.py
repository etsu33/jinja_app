from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


NEED_KEYWORDS: dict[str, tuple[str, ...]] = {
    "mental": ("不安", "悩み", "迷い", "焦り", "落ち着", "整え", "考えすぎ"),
    "rest": ("疲れ", "休み", "癒", "静か", "一人", "ひとり", "休息"),
    "career": ("仕事", "転職", "独立", "キャリア", "挑戦", "働き方"),
    "money": ("お金", "金運", "収入", "商売", "売上", "生活費"),
    "love": ("恋愛", "縁", "人間関係", "結婚", "出会い", "仲直り"),
    "study": ("勉強", "資格", "試験", "学び", "スキル", "合格"),
    "courage": ("前に進", "決断", "勇気", "勝負", "変えたい", "始めたい"),
}

STATE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "tired": ("疲れ", "しんど", "休み", "癒"),
    "anxious": ("不安", "怖", "心配", "焦り"),
    "uncertain": ("迷", "わから", "決められ", "悩"),
    "stuck": ("停滞", "動け", "進ま", "詰ま"),
    "ready_to_change": ("変えたい", "切り替え", "やり直", "始めたい"),
}

DIRECTION_BY_STATE: dict[str, tuple[str, tuple[str, ...]]] = {
    "tired": ("rest", ("静寂", "復興")),
    "anxious": ("stabilize", ("守り", "静寂")),
    "uncertain": ("review", ("静寂", "再出発")),
    "stuck": ("reset", ("再出発", "静寂")),
    "ready_to_change": ("challenge", ("再出発", "勝負")),
}

ACTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "visit": ("行きたい", "参拝", "神社", "場所", "向かう"),
    "reflect": ("考えたい", "整理", "見つめ", "振り返"),
    "save": ("残したい", "保存", "記録"),
}

DECISION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "career_decision": ("転職", "独立", "仕事", "働き方", "キャリア"),
    "relationship_decision": ("恋愛", "結婚", "人間関係", "仲直り", "関係"),
    "money_decision": ("お金", "金運", "収入", "生活費", "商売", "売上"),
    "rest_or_action": ("休む", "動く", "始めたい", "前に進", "切り替え"),
}

CONSTRAINT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "time": ("時間がない", "忙しい", "余裕がない"),
    "money": ("お金が不安", "生活費", "収入", "金銭"),
    "energy": ("疲れ", "しんど", "体力", "休みたい"),
    "relationship": ("人間関係", "家族", "職場", "相手"),
}

OUTCOME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "decide": ("決めたい", "決断", "選びたい"),
    "calm": ("落ち着", "安心", "整え"),
    "move_forward": ("前に進", "背中", "始めたい"),
    "clarify": ("整理", "見直", "考えたい"),
}


@dataclass(frozen=True)
class InterpretationProfile:
    raw_query: str
    state_profile: dict[str, Any] = field(default_factory=dict)
    need_profile: dict[str, Any] = field(default_factory=dict)
    direction_profile: dict[str, Any] = field(default_factory=dict)
    emotion_profile: dict[str, Any] = field(default_factory=dict)
    action_intent: dict[str, Any] = field(default_factory=dict)
    decision_context: dict[str, Any] = field(default_factory=dict)
    constraint_profile: dict[str, Any] = field(default_factory=dict)
    outcome_hint: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "raw_query": self.raw_query,
            "state_profile": self.state_profile,
            "need_profile": self.need_profile,
            "direction_profile": self.direction_profile,
            "emotion_profile": self.emotion_profile,
            "action_intent": self.action_intent,
            "decision_context": self.decision_context,
            "constraint_profile": self.constraint_profile,
            "outcome_hint": self.outcome_hint,
        }


def _collect_hits(query: str, keyword_map: dict[str, tuple[str, ...]]) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for key, keywords in keyword_map.items():
        matched = [keyword for keyword in keywords if keyword in query]
        if matched:
            hits[key] = matched
    return hits


def _confidence_from_hits(total_hits: int) -> float:
    if total_hits <= 0:
        return 0.0
    return min(0.95, 0.45 + total_hits * 0.12)


def build_state_profile(query: str) -> dict[str, Any]:
    hits = _collect_hits(query, STATE_KEYWORDS)
    states = list(hits.keys())
    total_hits = sum(len(values) for values in hits.values())

    return {
        "primary_state": states[0] if states else None,
        "secondary_states": states[1:],
        "state_hits": hits,
        "confidence": _confidence_from_hits(total_hits),
    }


def build_need_profile(
    query: str,
    *,
    need_tags: list[str] | None = None,
    selected_goriyaku_tag_ids: list[int] | None = None,
) -> dict[str, Any]:
    hits = _collect_hits(query, NEED_KEYWORDS)
    extracted_need_tags = list(hits.keys())
    merged_need_tags = list(dict.fromkeys([*(need_tags or []), *extracted_need_tags]))

    return {
        "need_tags": merged_need_tags,
        "need_hits": hits,
        "primary_need_tag": merged_need_tags[0] if merged_need_tags else None,
        "selected_goriyaku_tag_ids": selected_goriyaku_tag_ids or [],
    }


def build_direction_profile(state_profile: dict[str, Any]) -> dict[str, Any]:
    primary_state = state_profile.get("primary_state")
    direction, themes = DIRECTION_BY_STATE.get(primary_state, (None, ()))

    return {
        "direction": direction,
        "themes": list(themes),
        "source_state": primary_state,
    }


def build_emotion_profile(query: str, state_profile: dict[str, Any]) -> dict[str, Any]:
    state_hits = state_profile.get("state_hits") or {}
    signals = sorted({signal for values in state_hits.values() for signal in values})
    confidence = float(state_profile.get("confidence") or 0.0)

    if confidence >= 0.75:
        intensity = "high"
    elif confidence >= 0.45:
        intensity = "medium"
    elif signals:
        intensity = "low"
    else:
        intensity = "unknown"

    tone = state_profile.get("primary_state") or "unknown"

    return {
        "tone": tone,
        "intensity": intensity,
        "signals": signals,
    }


def build_action_intent(query: str) -> dict[str, Any]:
    hits = _collect_hits(query, ACTION_KEYWORDS)
    intents = list(hits.keys())

    return {
        "intent": intents[0] if intents else None,
        "strength": "soft" if intents else "unknown",
        "candidates": intents,
        "intent_hits": hits,
    }


def build_decision_context(query: str) -> dict[str, Any]:
    hits = _collect_hits(query, DECISION_KEYWORDS)
    contexts = list(hits.keys())

    return {
        "primary_decision": contexts[0] if contexts else None,
        "decision_candidates": contexts,
        "decision_hits": hits,
    }


def build_constraint_profile(query: str) -> dict[str, Any]:
    hits = _collect_hits(query, CONSTRAINT_KEYWORDS)
    constraints = list(hits.keys())

    return {
        "primary_constraint": constraints[0] if constraints else None,
        "constraints": constraints,
        "constraint_hits": hits,
    }


def build_outcome_hint(query: str) -> dict[str, Any]:
    hits = _collect_hits(query, OUTCOME_KEYWORDS)
    outcomes = list(hits.keys())

    return {
        "primary_outcome": outcomes[0] if outcomes else None,
        "outcome_candidates": outcomes,
        "outcome_hits": hits,
    }


def interpret_consultation(
    query: str | None,
    *,
    need_tags: list[str] | None = None,
    selected_goriyaku_tag_ids: list[int] | None = None,
) -> dict[str, Any]:
    """Build a shadow-safe interpretation profile for a concierge query.

    This service intentionally does not change recommendation ranking.
    It prepares structured input for debug payloads, Meaning Translation Layer,
    and future Score v3 shadow observation.
    """

    raw_query = (query or "").strip()
    state_profile = build_state_profile(raw_query)
    need_profile = build_need_profile(
        raw_query,
        need_tags=need_tags,
        selected_goriyaku_tag_ids=selected_goriyaku_tag_ids,
    )
    direction_profile = build_direction_profile(state_profile)
    emotion_profile = build_emotion_profile(raw_query, state_profile)
    action_intent = build_action_intent(raw_query)
    decision_context = build_decision_context(raw_query)
    constraint_profile = build_constraint_profile(raw_query)
    outcome_hint = build_outcome_hint(raw_query)

    return InterpretationProfile(
        raw_query=raw_query,
        state_profile=state_profile,
        need_profile=need_profile,
        direction_profile=direction_profile,
        emotion_profile=emotion_profile,
        action_intent=action_intent,
        decision_context=decision_context,
        constraint_profile=constraint_profile,
        outcome_hint=outcome_hint,
    ).as_dict()
