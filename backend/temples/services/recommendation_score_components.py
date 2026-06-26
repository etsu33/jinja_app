

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SCORE_KEYS = (
    "state_match_score",
    "meaning_match_score",
    "shrine_profile_score",
    "behavior_score",
    "history_score",
)


@dataclass(frozen=True)
class RecommendationScoreComponents:
    state_match_score: float = 0.0
    meaning_match_score: float = 0.0
    shrine_profile_score: float = 0.0
    behavior_score: float = 0.0
    history_score: float = 0.0

    @property
    def final_score(self) -> float:
        return _clamp_score(
            self.state_match_score
            + self.meaning_match_score
            + self.shrine_profile_score
            + self.behavior_score
            + self.history_score,
            max_value=5.0,
        )

    def as_dict(self) -> dict[str, float]:
        return {
            "state_match_score": self.state_match_score,
            "meaning_match_score": self.meaning_match_score,
            "shrine_profile_score": self.shrine_profile_score,
            "behavior_score": self.behavior_score,
            "history_score": self.history_score,
            "final_score": self.final_score,
        }


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _clamp_score(value: Any, *, max_value: float = 1.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number < 0.0:
        return 0.0
    if number > max_value:
        return max_value
    return round(number, 4)


def calculate_state_match_score(profile: dict[str, Any] | None) -> float:
    """Score current-state fit for shadow observation only."""

    data = _as_dict(profile)
    interpretation_profile = _as_dict(data.get("interpretation_profile"))
    state_profile = _as_dict(interpretation_profile.get("state_profile"))
    candidate_profile = _as_dict(data.get("candidate_profile"))

    primary_state = state_profile.get("primary_state")
    state_confidence = _clamp_score(state_profile.get("confidence"))
    candidate_history_theme = candidate_profile.get("history_theme")

    if not primary_state:
        return 0.0

    score = 0.35
    if state_confidence:
        score += state_confidence * 0.35
    if candidate_history_theme:
        score += 0.3
    return _clamp_score(score)


def calculate_meaning_match_score(profile: dict[str, Any] | None) -> float:
    """Score Meaning Translation fit for shadow observation only."""

    data = _as_dict(profile)
    translation_result = _as_dict(data.get("translation_result"))

    score = 0.0
    if translation_result.get("history_theme"):
        score += 0.35
    if translation_result.get("action_context"):
        score += 0.35
    if translation_result.get("reflection_question_seed"):
        score += 0.3
    return _clamp_score(score)


def calculate_shrine_profile_score(profile: dict[str, Any] | None) -> float:
    """Score candidate profile completeness for shadow observation only."""

    data = _as_dict(profile)
    candidate_profile = _as_dict(data.get("candidate_profile"))

    score = 0.0
    if candidate_profile.get("shrine_id") or candidate_profile.get("id"):
        score += 0.2
    if candidate_profile.get("name") or candidate_profile.get("name_jp"):
        score += 0.2
    if candidate_profile.get("history_theme"):
        score += 0.2
    if candidate_profile.get("goriyaku") or _as_list(candidate_profile.get("goriyaku_tags")):
        score += 0.2
    if _as_list(candidate_profile.get("visit_style_tags")) or candidate_profile.get("place_id"):
        score += 0.2
    return _clamp_score(score)


def calculate_behavior_score(profile: dict[str, Any] | None) -> float:
    """Score behavior signals for shadow observation only."""

    data = _as_dict(profile)
    candidate_profile = _as_dict(data.get("candidate_profile"))
    behavior_signals = _as_dict(candidate_profile.get("behavior_signals"))

    score = 0.0
    if behavior_signals.get("detail_view") or behavior_signals.get("detail_view_count"):
        score += 0.2
    if behavior_signals.get("save") or behavior_signals.get("save_count"):
        score += 0.25
    if behavior_signals.get("route_open") or behavior_signals.get("route_open_count"):
        score += 0.25
    if behavior_signals.get("visit_done") or behavior_signals.get("visit_done_count"):
        score += 0.2
    if behavior_signals.get("reflection_saved") or behavior_signals.get("reflection_saved_count"):
        score += 0.1
    return _clamp_score(score)


def calculate_history_score(profile: dict[str, Any] | None) -> float:
    """Score history-theme connection for shadow observation only."""

    data = _as_dict(profile)
    translation_result = _as_dict(data.get("translation_result"))
    candidate_profile = _as_dict(data.get("candidate_profile"))

    translated_theme = translation_result.get("history_theme")
    candidate_theme = candidate_profile.get("history_theme")

    if not translated_theme or not candidate_theme:
        return 0.0
    if translated_theme == candidate_theme:
        return 1.0
    return 0.35


def calculate_recommendation_score_components(
    profile: dict[str, Any] | None,
) -> dict[str, float]:
    """Calculate Score v3 components without changing recommendation ranking."""

    components = RecommendationScoreComponents(
        state_match_score=calculate_state_match_score(profile),
        meaning_match_score=calculate_meaning_match_score(profile),
        shrine_profile_score=calculate_shrine_profile_score(profile),
        behavior_score=calculate_behavior_score(profile),
        history_score=calculate_history_score(profile),
    )
    return components.as_dict()


__all__ = [
    "RecommendationScoreComponents",
    "calculate_state_match_score",
    "calculate_meaning_match_score",
    "calculate_shrine_profile_score",
    "calculate_behavior_score",
    "calculate_history_score",
    "calculate_recommendation_score_components",
]
