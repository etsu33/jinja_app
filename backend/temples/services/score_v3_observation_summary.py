

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


COMPONENT_KEYS = (
    "state_match_score",
    "meaning_match_score",
    "shrine_profile_score",
    "behavior_score",
    "history_score",
    "final_score",
)


@dataclass(frozen=True)
class ScoreV3ObservationSummary:
    top1_changed: bool = False
    delta: float = 0.0
    component_summary: dict[str, float] = field(default_factory=dict)
    reason: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "top1_changed": self.top1_changed,
            "delta": self.delta,
            "component_summary": self.component_summary,
            "reason": self.reason,
        }


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _to_float(value: Any) -> float:
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return 0.0


def _component_values(score_v3: dict[str, Any] | None) -> dict[str, float]:
    score_v3_dict = _as_dict(score_v3)
    components = _as_dict(score_v3_dict.get("components"))

    return {
        key: _to_float(components.get(key))
        for key in COMPONENT_KEYS
    }


def summarize_score_v3_components(
    score_v3_items: list[dict[str, Any]] | None,
) -> dict[str, float]:
    """Return average component values for Score v3 debug payloads."""

    items = [item for item in _as_list(score_v3_items) if isinstance(item, dict)]
    if not items:
        return {key: 0.0 for key in COMPONENT_KEYS}

    totals = {key: 0.0 for key in COMPONENT_KEYS}
    for item in items:
        values = _component_values(item)
        for key in COMPONENT_KEYS:
            totals[key] += values[key]

    return {
        key: round(totals[key] / len(items), 4)
        for key in COMPONENT_KEYS
    }


def build_score_v3_observation_summary(
    *,
    current_top_id: Any = None,
    score_v3_top_id: Any = None,
    current_top_score: Any = None,
    score_v3_top_score: Any = None,
    score_v3_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build Score v3 observation summary without changing ranking.

    This function is observation-only. It must not sort, mutate, or apply
    Score v3 ranking. API attachment is handled in a later phase.
    """

    has_current_top = current_top_id is not None
    has_score_v3_top = score_v3_top_id is not None
    top1_changed = bool(
        has_current_top
        and has_score_v3_top
        and str(current_top_id) != str(score_v3_top_id)
    )
    delta = round(_to_float(score_v3_top_score) - _to_float(current_top_score), 4)

    reason: list[str] = []
    if top1_changed:
        reason.append("top1_changed")
    if delta:
        reason.append("score_delta")
    if score_v3_items:
        reason.append("component_summary_available")

    return ScoreV3ObservationSummary(
        top1_changed=top1_changed,
        delta=delta,
        component_summary=summarize_score_v3_components(score_v3_items),
        reason=reason,
    ).as_dict()


__all__ = [
    "COMPONENT_KEYS",
    "ScoreV3ObservationSummary",
    "summarize_score_v3_components",
    "build_score_v3_observation_summary",
]
