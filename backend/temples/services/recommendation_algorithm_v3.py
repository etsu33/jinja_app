

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from temples.services.recommendation_score_components import (
    calculate_recommendation_score_components,
)


@dataclass(frozen=True)
class RecommendationAlgorithmV3Result:
    mode: str = "shadow"
    shadow_mode: bool = True
    ranking_applied: bool = False
    score_v3: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "shadow_mode": self.shadow_mode,
            "ranking_applied": self.ranking_applied,
            "score_v3": self.score_v3,
        }


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def build_score_v3_debug(
    recommendation_input_profile: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build debug.score_v3 payload for shadow observation.

    This function must not sort, filter, mutate, or otherwise change
    recommendation ranking. It only computes observation payload.
    """

    profile = _as_dict(recommendation_input_profile)
    components = calculate_recommendation_score_components(profile)

    return {
        "mode": "shadow",
        "ranking_applied": False,
        "components": components,
        "observation": {
            "top1_changed": False,
            "delta": 0.0,
            "reason": [],
        },
    }


def run_recommendation_algorithm_v3_shadow(
    recommendation_input_profile: dict[str, Any] | None,
) -> dict[str, Any]:
    """Run Recommendation Algorithm v3 in shadow mode only.

    The return value is safe to attach to debug payloads. It must not be
    used as the source of active ranking until a later activation decision.
    """

    score_v3 = build_score_v3_debug(recommendation_input_profile)

    return RecommendationAlgorithmV3Result(
        mode="shadow",
        shadow_mode=True,
        ranking_applied=False,
        score_v3=score_v3,
    ).as_dict()


__all__ = [
    "RecommendationAlgorithmV3Result",
    "build_score_v3_debug",
    "run_recommendation_algorithm_v3_shadow",
]
