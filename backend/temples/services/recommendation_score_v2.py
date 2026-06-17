

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ScoreV2Input:
    """Input contract for Recommendation Score v2.

    This calculator intentionally receives already-resolved signals from
    concierge_chat_ranking.py. It must not fetch DB records or re-run matching.
    """

    score_total_ranked: float
    score_total_ranked_base: float
    score_need_rank_weighted: float
    score_need: int
    score_visit_style: int
    score_element: int
    score_distance: float
    score_popular: float
    astro_bonus: float
    direction_bonus: float
    direction_reason: Optional[str]
    behavior_signal: float
    behavior_contribution: float
    capped_behavior_contribution: float
    behavior_ratio: float
    visit_signal: float
    reflection_signal: float
    need_weight: float
    element_weight: float
    distance_weight: float
    popular_weight: float
    visit_style_weight: float
    matched_need_tags: List[str] = field(default_factory=list)
    matched_by_tag: List[str] = field(default_factory=list)
    matched_by_text: List[str] = field(default_factory=list)
    matched_by_gid: List[str] = field(default_factory=list)
    matched_visit_style_tags: List[str] = field(default_factory=list)
    matched_user_selected_goriyaku_tag_ids: List[int] = field(default_factory=list)
    context_profile: Dict[str, Any] = field(default_factory=dict)
    shrine_meaning_profile: Dict[str, Any] = field(default_factory=dict)
    behavior_profile: Dict[str, Any] = field(default_factory=dict)
    behavior_breakdown: Dict[str, Any] = field(default_factory=dict)
    reflection_hint: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ScoreV2Result:
    """Output contract for Recommendation Score v2."""

    total: float
    components: Dict[str, Any]
    signals: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "version": 1,
            "ranking_applied": True,
            "total": float(self.total),
            "components": self.components,
            "signals": self.signals,
        }


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def calculate_recommendation_score_v2(input_data: ScoreV2Input) -> ScoreV2Result:
    """Build the score_v2 payload from already-computed ranking signals.

    This is a first extraction step. The ranking math stays compatible with the
    existing _attach_breakdown behavior, while the public score_v2 payload is
    centralized here.
    """

    components: Dict[str, Any] = {
        "user_state_match": float(input_data.score_need_rank_weighted * input_data.need_weight),
        "shrine_meaning_match": float(input_data.score_need * input_data.need_weight),
        "context_match": float(input_data.score_visit_style * input_data.visit_style_weight),
        "element_match": float(input_data.score_element * input_data.element_weight),
        "distance_score": float(input_data.score_distance * input_data.distance_weight),
        "popularity_score": float(input_data.score_popular * input_data.popular_weight),
        "astro_bonus": float(input_data.astro_bonus),
        "behavior_signal": float(input_data.behavior_signal),
        "behavior_contribution": float(input_data.behavior_contribution),
        "capped_behavior_contribution": float(input_data.capped_behavior_contribution),
        "behavior_ratio": float(input_data.behavior_ratio),
        "visit_signal": float(input_data.visit_signal),
        "reflection_signal": float(input_data.reflection_signal),
        "direction_bonus": float(input_data.direction_bonus),
        "direction_reason": input_data.direction_reason,
    }

    signals: Dict[str, Any] = {
        "matched_need_tags": list(input_data.matched_need_tags),
        "matched_by_tag": list(input_data.matched_by_tag),
        "matched_by_text": list(input_data.matched_by_text),
        "matched_by_gid": list(input_data.matched_by_gid),
        "matched_visit_style_tags": list(input_data.matched_visit_style_tags),
        "context_profile": dict(input_data.context_profile),
        "matched_user_selected_goriyaku_tag_ids": list(input_data.matched_user_selected_goriyaku_tag_ids),
        "shrine_meaning_profile": dict(input_data.shrine_meaning_profile),
        "behavior_profile": dict(input_data.behavior_profile),
        "behavior_breakdown": dict(input_data.behavior_breakdown),
        "reflection_hint": dict(input_data.reflection_hint or {}),
    }

    return ScoreV2Result(
        total=_safe_float(input_data.score_total_ranked),
        components=components,
        signals=signals,
    )
