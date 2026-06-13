from __future__ import annotations

from collections import defaultdict
from typing import Any

from django.db.models import Count, QuerySet

from temples.models import ActionEvent, ShrineReflection


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 4)


def _base_action_events_qs(*, user: Any | None = None, shrine_id: int | None = None) -> QuerySet[ActionEvent]:
    qs = ActionEvent.objects.all()
    if user is not None:
        qs = qs.filter(user=user)
    if shrine_id is not None:
        qs = qs.filter(shrine_id=shrine_id)
    return qs


def _base_reflections_qs(*, user: Any | None = None, shrine_id: int | None = None) -> QuerySet[ShrineReflection]:
    qs = ShrineReflection.objects.all()
    if user is not None:
        qs = qs.filter(user=user)
    if shrine_id is not None:
        qs = qs.filter(shrine_id=shrine_id)
    return qs


def build_action_completion_observation(*, user: Any | None = None, shrine_id: int | None = None) -> dict[str, Any]:
    """Build action completion observation from persisted backend data.

    action_suggestion_view is intentionally excluded because it is currently
    tracked only as a frontend analytics event and is not persisted in the DB.
    """

    action_events = _base_action_events_qs(user=user, shrine_id=shrine_id)

    action_started_count = action_events.filter(
        action_type=ActionEvent.ActionType.ACTION_STARTED,
    ).count()
    action_completed_count = action_events.filter(
        action_type=ActionEvent.ActionType.ACTION_COMPLETED,
    ).count()

    history_theme_rows = (
        action_events.values("history_theme", "action_type")
        .annotate(count=Count("id"))
        .order_by("history_theme", "action_type")
    )
    history_theme_map: dict[str, dict[str, int]] = defaultdict(
        lambda: {"action_started_count": 0, "action_completed_count": 0}
    )
    for row in history_theme_rows:
        history_theme = str(row.get("history_theme") or "")
        action_type = row.get("action_type")
        count = int(row.get("count") or 0)

        if action_type == ActionEvent.ActionType.ACTION_STARTED:
            history_theme_map[history_theme]["action_started_count"] = count
        elif action_type == ActionEvent.ActionType.ACTION_COMPLETED:
            history_theme_map[history_theme]["action_completed_count"] = count

    history_theme_completion = []
    for history_theme, counts in sorted(history_theme_map.items(), key=lambda item: item[0]):
        started = counts["action_started_count"]
        completed = counts["action_completed_count"]
        history_theme_completion.append(
            {
                "history_theme": history_theme,
                "action_started_count": started,
                "action_completed_count": completed,
                "completion_rate": _safe_rate(completed, started),
            }
        )

    completed_pairs = set(
        action_events.filter(action_type=ActionEvent.ActionType.ACTION_COMPLETED)
        .exclude(shrine_id__isnull=True)
        .values_list("user_id", "shrine_id")
    )
    reflection_pairs = set(
        _base_reflections_qs(user=user, shrine_id=shrine_id)
        .values_list("user_id", "shrine_id")
    )
    completed_with_reflection_count = len(completed_pairs & reflection_pairs)
    completed_pair_count = len(completed_pairs)

    return {
        "action_started_count": int(action_started_count),
        "action_completed_count": int(action_completed_count),
        "started_to_completed_rate": _safe_rate(action_completed_count, action_started_count),
        "history_theme_completion": history_theme_completion,
        "completed_pair_count": completed_pair_count,
        "completed_with_reflection_count": completed_with_reflection_count,
        "completed_to_reflection_rate": _safe_rate(completed_with_reflection_count, completed_pair_count),
        "view_to_started_rate": None,
        "view_to_started_rate_reason": "action_suggestion_view is not persisted in backend DB.",
    }


__all__ = ["build_action_completion_observation"]
