

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ACTIVATION_TOP1_CHANGED_RATE_MAX = 0.35
ACTIVATION_AVG_DELTA_MAX = 0.25
ACTIVATION_MAX_ABS_DELTA_MAX = 0.75


@dataclass(frozen=True)
class ScoreV3ShadowObservationPayload:
    session_count: int = 0
    top1_changed_count: int = 0
    top1_changed_rate: float = 0.0
    avg_delta: float = 0.0
    max_abs_delta: float = 0.0
    activation_candidate: bool = False
    component_summary: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_count": self.session_count,
            "top1_changed_count": self.top1_changed_count,
            "top1_changed_rate": self.top1_changed_rate,
            "avg_delta": self.avg_delta,
            "max_abs_delta": self.max_abs_delta,
            "activation_candidate": self.activation_candidate,
            "component_summary": self.component_summary,
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


def _is_top1_changed(value: Any) -> bool:
    return value is True


def _component_summary_from_observations(
    observations: list[dict[str, Any]],
) -> dict[str, float]:
    component_keys = (
        "state_match_score",
        "meaning_match_score",
        "shrine_profile_score",
        "behavior_score",
        "history_score",
        "final_score",
    )
    if not observations:
        return {key: 0.0 for key in component_keys}

    totals = {key: 0.0 for key in component_keys}
    count = 0

    for observation in observations:
        component_summary = _as_dict(observation.get("component_summary"))
        if not component_summary:
            continue
        count += 1
        for key in component_keys:
            totals[key] += _to_float(component_summary.get(key))

    if count == 0:
        return {key: 0.0 for key in component_keys}

    return {
        key: round(totals[key] / count, 4)
        for key in component_keys
    }


def build_score_v3_shadow_observation_payload(
    observations: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Build aggregate Score v3 shadow observation payload.

    This is an observation-only payload builder. It does not save to DB,
    does not mutate input observations, and does not change ranking.
    DB persistence is intentionally left for a later PR.
    """

    items = [item for item in _as_list(observations) if isinstance(item, dict)]
    session_count = len(items)
    top1_changed_count = sum(
        1 for item in items if _is_top1_changed(item.get("top1_changed"))
    )
    top1_changed_rate = round(
        top1_changed_count / session_count,
        4,
    ) if session_count else 0.0

    deltas = [_to_float(item.get("delta")) for item in items]
    avg_delta = round(sum(deltas) / session_count, 4) if session_count else 0.0
    max_abs_delta = round(max((abs(delta) for delta in deltas), default=0.0), 4)

    activation_candidate = bool(
        session_count > 0
        and top1_changed_rate <= ACTIVATION_TOP1_CHANGED_RATE_MAX
        and abs(avg_delta) <= ACTIVATION_AVG_DELTA_MAX
        and max_abs_delta <= ACTIVATION_MAX_ABS_DELTA_MAX
    )

    return ScoreV3ShadowObservationPayload(
        session_count=session_count,
        top1_changed_count=top1_changed_count,
        top1_changed_rate=top1_changed_rate,
        avg_delta=avg_delta,
        max_abs_delta=max_abs_delta,
        activation_candidate=activation_candidate,
        component_summary=_component_summary_from_observations(items),
    ).as_dict()


__all__ = [
    "ACTIVATION_TOP1_CHANGED_RATE_MAX",
    "ACTIVATION_AVG_DELTA_MAX",
    "ACTIVATION_MAX_ABS_DELTA_MAX",
    "ScoreV3ShadowObservationPayload",
    "build_score_v3_shadow_observation_payload",
]
