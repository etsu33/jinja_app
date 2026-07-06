

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.db.models import QuerySet

from temples.models import Favorite, ShrineInteractionLog, ShrineReflection, Visit


@dataclass(frozen=True)
class BehaviorFunnelMetrics:
    detail_view_count: int
    route_open_count: int
    save_count: int
    visit_count: int
    reflection_count: int
    save_to_visit_cvr: float
    visit_to_reflection_cvr: float


def _apply_common_filters(
    qs: QuerySet,
    *,
    user: Any = None,
    shrine_id: int | None = None,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    date_field: str = "created_at",
) -> QuerySet:
    if user is not None:
        qs = qs.filter(user=user)

    if shrine_id is not None:
        qs = qs.filter(shrine_id=shrine_id)

    if from_dt is not None:
        qs = qs.filter(**{f"{date_field}__gte": from_dt})

    if to_dt is not None:
        qs = qs.filter(**{f"{date_field}__lt": to_dt})

    return qs


def _safe_cvr(*, numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def get_behavior_funnel_metrics(
    *,
    user: Any = None,
    shrine_id: int | None = None,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> BehaviorFunnelMetrics:
    """Return behavior funnel metrics for shrine recommendation actions.

    The service intentionally reads persisted backend records rather than frontend
    analytics events, so the metrics can be reused by tests, admin dashboards,
    observation logs, and future APIs without re-implementing funnel math.
    """

    interaction_qs = _apply_common_filters(
        ShrineInteractionLog.objects.all(),
        user=user,
        shrine_id=shrine_id,
        from_dt=from_dt,
        to_dt=to_dt,
        date_field="created_at",
    )

    detail_view_count = interaction_qs.filter(
        action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
    ).count()

    route_open_count = interaction_qs.filter(
        action_type=ShrineInteractionLog.ActionType.ROUTE_OPEN,
    ).count()

    save_count = _apply_common_filters(
        Favorite.objects.filter(shrine__isnull=False),
        user=user,
        shrine_id=shrine_id,
        from_dt=from_dt,
        to_dt=to_dt,
        date_field="created_at",
    ).count()

    visit_count = _apply_common_filters(
        Visit.objects.filter(status="added"),
        user=user,
        shrine_id=shrine_id,
        from_dt=from_dt,
        to_dt=to_dt,
        date_field="visited_at",
    ).count()

    reflection_count = _apply_common_filters(
        ShrineReflection.objects.all(),
        user=user,
        shrine_id=shrine_id,
        from_dt=from_dt,
        to_dt=to_dt,
        date_field="created_at",
    ).count()

    return BehaviorFunnelMetrics(
        detail_view_count=detail_view_count,
        route_open_count=route_open_count,
        save_count=save_count,
        visit_count=visit_count,
        reflection_count=reflection_count,
        save_to_visit_cvr=_safe_cvr(numerator=visit_count, denominator=save_count),
        visit_to_reflection_cvr=_safe_cvr(numerator=reflection_count, denominator=visit_count),
    )


def build_score_v3_funnel_correlation_summary(
    funnel: dict[str, Any],
    score_v3_summary: dict[str, Any],
) -> dict[str, Any]:
    """score_v3_ab_observation の集計と behavior_funnel 指標を突合するサマリを返す。

    DB 再クエリなし。既存 dict を受け取って合成するのみ。

    funnel は BehaviorFunnelMetrics.__dict__ または同等の dict を想定。
    rate は detail_view_count を分母として計算する。
    detail_view_count が 0 の場合はすべて 0.0。

    score_v3_summary は summarize_score_v3_ab_observations() の返り値を想定。
    """
    dv = int(funnel.get("detail_view_count") or 0)

    def _rate(count: Any) -> float:
        if dv <= 0:
            return 0.0
        return round(int(count or 0) / dv, 6)

    funnel_summary = {
        "detail_view_count": int(funnel.get("detail_view_count") or 0),
        "route_open_count": int(funnel.get("route_open_count") or 0),
        "save_count": int(funnel.get("save_count") or 0),
        "visit_count": int(funnel.get("visit_count") or 0),
        "reflection_count": int(funnel.get("reflection_count") or 0),
        "route_open_rate": _rate(funnel.get("route_open_count")),
        "save_rate": _rate(funnel.get("save_count")),
        "visit_done_rate": _rate(funnel.get("visit_count")),
        "reflection_saved_rate": _rate(funnel.get("reflection_count")),
    }

    score_v3_slice = {
        "top1_changed_rate_avg": float(score_v3_summary.get("top1_changed_rate_avg") or 0.0),
        "activation_candidate_rate": float(score_v3_summary.get("activation_candidate_rate") or 0.0),
        "avg_delta": float(score_v3_summary.get("avg_delta") or 0.0),
        "max_abs_delta_max": float(score_v3_summary.get("max_abs_delta_max") or 0.0),
    }

    return {
        "score_v3": score_v3_slice,
        "funnel": funnel_summary,
        "analysis_hint": "compare_score_v3_delta_with_behavior_funnel",
    }
