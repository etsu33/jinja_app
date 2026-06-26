

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RecommendationInputProfile:
    interpretation_profile: dict[str, Any] = field(default_factory=dict)
    translation_result: dict[str, Any] = field(default_factory=dict)
    candidate_profile: dict[str, Any] = field(default_factory=dict)
    score_v2_fields: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "interpretation_profile": self.interpretation_profile,
            "translation_result": self.translation_result,
            "candidate_profile": self.candidate_profile,
            "score_v2_fields": self.score_v2_fields,
        }


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def build_recommendation_input_profile(
    *,
    interpretation_profile: dict[str, Any] | None = None,
    translation_result: dict[str, Any] | None = None,
    candidate_profile: dict[str, Any] | None = None,
    score_v2_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the stable Recommendation Algorithm v3 input schema.

    This profile is currently used only as a normalized input for
    Score v3 shadow observation. It MUST NOT change recommendation
    ranking or existing Score v2 behaviour.
    """

    return RecommendationInputProfile(
        interpretation_profile=_as_dict(interpretation_profile),
        translation_result=_as_dict(translation_result),
        candidate_profile=_as_dict(candidate_profile),
        score_v2_fields=_as_dict(score_v2_fields),
    ).as_dict()


__all__ = [
    "RecommendationInputProfile",
    "build_recommendation_input_profile",
]
