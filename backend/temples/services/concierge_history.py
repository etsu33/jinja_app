from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, Any

from django.db import transaction
from django.utils import timezone

from temples.models import (
    ActionEvent,
    ConciergeHistory,
    ConciergeMessage,
    ConciergeThread,
    Favorite,
    ShrineInteractionLog,
    ShrineReflection,
    Visit,
)

from temples.services.reflection_state_change import build_reflection_state_change


HistoryActionState = str


def classify_history_action(*, user, history: ConciergeHistory) -> HistoryActionState:
    shrine_id = getattr(history, "shrine_id", None)
    return classify_shrine_action_state(user=user, shrine_id=shrine_id)


def classify_shrine_action_state(*, user, shrine_id: int | None) -> HistoryActionState:
    if user is None or not getattr(user, "is_authenticated", False):
        return "none"

    if shrine_id is None:
        return "none"

    has_reflection = ShrineReflection.objects.filter(
        user=user,
        shrine_id=shrine_id,
    ).exists()
    if has_reflection:
        return "reflected"

    has_visit = Visit.objects.filter(
        user=user,
        shrine_id=shrine_id,
        status="added",
    ).exists()
    if has_visit:
        return "visited"

    has_favorite = Favorite.objects.filter(
        user=user,
        shrine_id=shrine_id,
    ).exists()
    if has_favorite:
        return "saved"

    has_route_open = ShrineInteractionLog.objects.filter(
        user=user,
        shrine_id=shrine_id,
        action_type=ShrineInteractionLog.ActionType.ROUTE_OPEN,
    ).exists()
    if has_route_open:
        return "route_opened"

    has_detail_view = ShrineInteractionLog.objects.filter(
        user=user,
        shrine_id=shrine_id,
        action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
    ).exists()
    if has_detail_view:
        return "detail_viewed"

    return "none"


def calculate_shrine_behavior_signal(*, user, shrine_id: int | None) -> float:
    if user is None or not getattr(user, "is_authenticated", False):
        return 0.0

    if shrine_id is None:
        return 0.0

    score = 0.0

    if ShrineInteractionLog.objects.filter(
        user=user,
        shrine_id=shrine_id,
        action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
    ).exists():
        score += 0.5

    if ShrineInteractionLog.objects.filter(
        user=user,
        shrine_id=shrine_id,
        action_type=ShrineInteractionLog.ActionType.ROUTE_OPEN,
    ).exists():
        score += 1.0

    if Favorite.objects.filter(user=user, shrine_id=shrine_id).exists():
        score += 2.0

    if Visit.objects.filter(user=user, shrine_id=shrine_id, status="added").exists():
        score += 4.0

    if ShrineReflection.objects.filter(user=user, shrine_id=shrine_id).exists():
        score += 5.0

    return min(score, 10.0)


def _recency_multiplier(latest_at) -> float:
    if latest_at is None:
        return 0.0

    now = timezone.now()
    age = now - latest_at

    if age <= timedelta(days=30):
        return 1.0
    if age <= timedelta(days=90):
        return 0.5
    return 0.2


# New breakdown helper for v2
def calculate_shrine_behavior_signal_breakdown(*, user, shrine_id: int | None) -> dict[str, float]:
    if user is None or not getattr(user, "is_authenticated", False):
        return {
            "detail_view_signal": 0.0,
            "route_open_signal": 0.0,
            "save_signal": 0.0,
            "visit_signal": 0.0,
            "reflection_signal": 0.0,
            "action_completed_signal": 0.0,
            "total": 0.0,
        }

    if shrine_id is None:
        return {
            "detail_view_signal": 0.0,
            "route_open_signal": 0.0,
            "save_signal": 0.0,
            "visit_signal": 0.0,
            "reflection_signal": 0.0,
            "action_completed_signal": 0.0,
            "total": 0.0,
        }

    detail_view_qs = ShrineInteractionLog.objects.filter(
        user=user,
        shrine_id=shrine_id,
        action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
    )
    detail_view_latest = (
        detail_view_qs.order_by("-created_at")
        .values_list("created_at", flat=True)
        .first()
    )
    detail_view_signal = detail_view_qs.count() * 0.2 * _recency_multiplier(detail_view_latest)

    route_open_qs = ShrineInteractionLog.objects.filter(
        user=user,
        shrine_id=shrine_id,
        action_type=ShrineInteractionLog.ActionType.ROUTE_OPEN,
    )
    route_open_latest = (
        route_open_qs.order_by("-created_at")
        .values_list("created_at", flat=True)
        .first()
    )
    route_open_signal = route_open_qs.count() * 0.6 * _recency_multiplier(route_open_latest)

    favorite_latest = (
        Favorite.objects.filter(user=user, shrine_id=shrine_id)
        .order_by("-created_at")
        .values_list("created_at", flat=True)
        .first()
    )
    save_signal = 0.0
    if favorite_latest is not None:
        save_signal = 1.5 * _recency_multiplier(favorite_latest)

    visit_latest = (
        Visit.objects.filter(user=user, shrine_id=shrine_id, status="added")
        .order_by("-visited_at")
        .values_list("visited_at", flat=True)
        .first()
    )
    visit_signal = 0.0
    if visit_latest is not None:
        visit_signal = 3.0 * _recency_multiplier(visit_latest)

    reflection_latest = (
        ShrineReflection.objects.filter(user=user, shrine_id=shrine_id)
        .order_by("-created_at")
        .values_list("created_at", flat=True)
        .first()
    )
    reflection_signal = 0.0
    if reflection_latest is not None:
        reflection_signal = 4.0 * _recency_multiplier(reflection_latest)

    action_completed_latest = (
        ActionEvent.objects.filter(
            user=user,
            shrine_id=shrine_id,
            action_type=ActionEvent.ActionType.ACTION_COMPLETED,
        )
        .order_by("-created_at")
        .values_list("created_at", flat=True)
        .first()
    )
    action_completed_signal = 0.0
    if action_completed_latest is not None:
        action_completed_signal = 2.0 * _recency_multiplier(action_completed_latest)

    total = min(
        detail_view_signal
        + route_open_signal
        + save_signal
        + visit_signal
        + reflection_signal
        + action_completed_signal,
        10.0,
    )

    return {
        "detail_view_signal": float(detail_view_signal),
        "route_open_signal": float(route_open_signal),
        "save_signal": float(save_signal),
        "visit_signal": float(visit_signal),
        "reflection_signal": float(reflection_signal),
        "action_completed_signal": float(action_completed_signal),
        "total": float(total),
    }


def calculate_light_behavior_profile_breakdown(
    *,
    behavior_breakdown: dict[str, float] | None = None,
) -> dict[str, float]:
    """
    Behavior Profile v1: detail_view / route_open / save のみを対象にする。
    visit_signal / reflection_signal は含めない。

    behavior_breakdown が渡された場合はそこから light signals を抽出する（DB再クエリなし）。
    """
    bd = behavior_breakdown or {}
    detail = float(bd.get("detail_view_signal") or 0.0)
    route = float(bd.get("route_open_signal") or 0.0)
    save = float(bd.get("save_signal") or 0.0)
    return {
        "detail_view_signal": detail,
        "route_open_signal": route,
        "save_signal": save,
        "total": detail + route + save,
    }


def calculate_action_profile_breakdown(
    *,
    behavior_breakdown: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Action Profile v1: visit_signal のみを対象にする。
    behavior_breakdown から抽出するため DB 再クエリなし。
    """
    bd = behavior_breakdown or {}
    visit = float(bd.get("visit_signal") or 0.0)
    return {
        "score": visit,
        "visit_signal": visit,
        "status": "visited" if visit > 0 else "not_visited",
        "reason": "visit_done_only",
    }


def calculate_shrine_behavior_signal_v2(*, user, shrine_id: int | None) -> float:
    breakdown = calculate_shrine_behavior_signal_breakdown(
        user=user,
        shrine_id=shrine_id,
    )
    return float(breakdown["total"])


def build_recent_reflection_hint(*, user, shrine_id: int | None = None) -> dict[str, Any] | None:
    """Return the latest reflection-derived hint for recommendation support.

    This helper exposes reflection content as a safe audit payload only.
    It does not change ranking by itself.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return None

    qs = ShrineReflection.objects.filter(user=user).select_related("shrine")
    if shrine_id is not None:
        qs = qs.filter(shrine_id=shrine_id)

    reflection = qs.order_by("-created_at").first()
    if reflection is None:
        return None

    state_change = build_reflection_state_change(reflection)

    return {
        "state_change_direction": state_change.state_change_direction,
        "state_change_summary": state_change.state_change_summary,
        "next_need_hint": state_change.next_need_hint,
        "next_history_theme_hint": state_change.next_history_theme_hint,
        "source_reflection_id": reflection.id,
        "source_shrine_id": reflection.shrine_id,
        "source_shrine_name": getattr(reflection.shrine, "name_jp", "") or "",
        "source_history_theme": reflection.history_theme,
        "created_at": reflection.created_at.isoformat() if reflection.created_at else None,
    }


@dataclass
class ChatSaveResult:
    thread: ConciergeThread
    user_message: ConciergeMessage
    assistant_message: Optional[ConciergeMessage]


def _short_title(text: str, max_len: int = 40) -> str:
    text = (text or "").strip()
    if not text:
        return "相談スレッド"
    return text[:max_len]


@transaction.atomic
def append_chat(
    *,
    user=None,
    anonymous_id: Optional[str] = None,
    query: str = "",
    reply_text: Optional[str] = None,
    thread_id: Optional[int] = None,
    recommendations: Optional[list[dict[str, Any]]] = None,
    recommendations_v2: Optional[list[dict[str, Any]]] = None,
) -> ChatSaveResult:
    now = timezone.now()

    if user is None and not anonymous_id:
        raise ValueError("user または anonymous_id のどちらかが必要です")

    if thread_id is not None:
        if user is not None:
            thread = ConciergeThread.objects.select_for_update().get(
                id=thread_id,
                user=user,
            )
        else:
            thread = ConciergeThread.objects.select_for_update().get(
                id=thread_id,
                anonymous_id=anonymous_id,
            )
    else:
        thread = ConciergeThread.objects.create(
            user=user,
            anonymous_id=anonymous_id,
            title=_short_title(query),
            last_message_at=now,
            recommendations=recommendations,
            recommendations_v2=recommendations_v2,
        )
    user_msg = ConciergeMessage.objects.create(
        thread=thread,
        role="user",
        content=query,
        created_at=now,
    )

    assistant_msg: Optional[ConciergeMessage] = None
    if reply_text:
        assistant_msg = ConciergeMessage.objects.create(
            thread=thread,
            role="assistant",
            content=reply_text,
        )

    last_at = assistant_msg.created_at if assistant_msg else user_msg.created_at

    ConciergeThread.objects.filter(pk=thread.pk).update(
        last_message_at=last_at,
        recommendations=recommendations,
        recommendations_v2=recommendations_v2,
    )

    thread.refresh_from_db()
    return ChatSaveResult(thread=thread, user_message=user_msg, assistant_message=assistant_msg)
