from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, Any

from django.db import transaction
from django.utils import timezone

from temples.models import (
    ConciergeHistory,
    ConciergeMessage,
    ConciergeThread,
    Favorite,
    ShrineInteractionLog,
    ShrineReflection,
    Visit,
)


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


def calculate_shrine_behavior_signal_v2(*, user, shrine_id: int | None) -> float:
    if user is None or not getattr(user, "is_authenticated", False):
        return 0.0

    if shrine_id is None:
        return 0.0

    score = 0.0

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
    score += detail_view_qs.count() * 0.2 * _recency_multiplier(detail_view_latest)

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
    score += route_open_qs.count() * 0.6 * _recency_multiplier(route_open_latest)

    favorite_latest = (
        Favorite.objects.filter(user=user, shrine_id=shrine_id)
        .order_by("-created_at")
        .values_list("created_at", flat=True)
        .first()
    )
    if favorite_latest is not None:
        score += 1.5 * _recency_multiplier(favorite_latest)

    visit_latest = (
        Visit.objects.filter(user=user, shrine_id=shrine_id, status="added")
        .order_by("-visited_at")
        .values_list("visited_at", flat=True)
        .first()
    )
    if visit_latest is not None:
        score += 3.0 * _recency_multiplier(visit_latest)

    reflection_latest = (
        ShrineReflection.objects.filter(user=user, shrine_id=shrine_id)
        .order_by("-created_at")
        .values_list("created_at", flat=True)
        .first()
    )
    if reflection_latest is not None:
        score += 4.0 * _recency_multiplier(reflection_latest)

    return min(score, 10.0)


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
    query: str,
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
