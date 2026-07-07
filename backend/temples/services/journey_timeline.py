from __future__ import annotations

from typing import Any

from django.contrib.auth.models import AnonymousUser
from django.db.models import Prefetch

from temples.models import ConciergeMessage, ConciergeThread, Shrine, ShrineReflection, Visit


JourneyEvent = dict[str, Any]


def build_journey_timeline(user) -> list[JourneyEvent]:
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return []

    events: list[JourneyEvent] = []

    threads = _user_threads(user)
    recommendation_shrines = _recommendation_shrines(threads)

    for thread in threads:
        events.extend(_thread_events(thread, recommendation_shrines))

    events.extend(_visit_events(user))
    events.extend(_reflection_events(user))

    return sorted(events, key=lambda event: event["occurred_at"], reverse=True)


def _user_threads(user):
    user_messages = ConciergeMessage.objects.filter(
        role=ConciergeMessage.ROLE_USER,
    ).order_by("created_at", "id")
    assistant_messages = ConciergeMessage.objects.filter(
        role=ConciergeMessage.ROLE_ASSISTANT,
    ).order_by("created_at", "id")

    return list(
        ConciergeThread.objects.filter(user=user)
        .prefetch_related(
            Prefetch("messages", queryset=user_messages, to_attr="_journey_user_messages"),
            Prefetch("messages", queryset=assistant_messages, to_attr="_journey_assistant_messages"),
        )
        .order_by("-last_message_at", "-id")
    )


def _thread_events(thread, recommendation_shrines: dict[int, Shrine]) -> list[JourneyEvent]:
    events: list[JourneyEvent] = []
    user_messages = list(getattr(thread, "_journey_user_messages", []))
    first_user_message = user_messages[0] if user_messages else None

    if first_user_message:
        events.append(
            {
                "id": f"thread:{thread.id}:consultation",
                "event_type": "consultation_created",
                "occurred_at": first_user_message.created_at,
                "title": "相談しました",
                "description": first_user_message.content,
                "thread_id": thread.id,
                "shrine_id": None,
                "shrine_name": None,
                "metadata": {},
            }
        )

    recommendation_time = _recommendation_occurred_at(thread)
    for index, recommendation in enumerate(_thread_recommendations(thread), start=1):
        shrine_id = _recommendation_shrine_id(recommendation)
        shrine = recommendation_shrines.get(shrine_id) if shrine_id else None
        shrine_name = _recommendation_shrine_name(recommendation, shrine)
        event_key = shrine_id or index

        events.append(
            {
                "id": f"thread:{thread.id}:recommendation:{event_key}",
                "event_type": "recommendation_shown",
                "occurred_at": recommendation_time,
                "title": "神社をご提案しました",
                "description": f"{shrine_name}をご提案しました。" if shrine_name else "神社をご提案しました。",
                "thread_id": thread.id,
                "shrine_id": shrine_id,
                "shrine_name": shrine_name,
                "metadata": {
                    "rank": index,
                    "history_theme": _string_or_empty(recommendation.get("history_theme")),
                },
            }
        )

    return events


def _thread_recommendations(thread) -> list[dict[str, Any]]:
    raw = thread.recommendations_v2 or thread.recommendations or []
    if isinstance(raw, dict):
        raw = raw.get("recommendations") or []
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _recommendation_occurred_at(thread):
    assistant_messages = list(getattr(thread, "_journey_assistant_messages", []))
    if assistant_messages:
        return assistant_messages[0].created_at
    return thread.last_message_at or thread.updated_at or thread.created_at


def _recommendation_shrines(threads) -> dict[int, Shrine]:
    shrine_ids = {
        shrine_id
        for thread in threads
        for recommendation in _thread_recommendations(thread)
        if (shrine_id := _recommendation_shrine_id(recommendation))
    }
    if not shrine_ids:
        return {}
    return Shrine.objects.in_bulk(shrine_ids)


def _recommendation_shrine_id(recommendation: dict[str, Any]) -> int | None:
    raw = (
        recommendation.get("shrine_id")
        or recommendation.get("shrineId")
        or recommendation.get("shrine")
        or recommendation.get("id")
    )
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _recommendation_shrine_name(recommendation: dict[str, Any], shrine: Shrine | None) -> str | None:
    name = recommendation.get("name") or recommendation.get("shrine_name") or recommendation.get("shrineName")
    if isinstance(name, str) and name:
        return name
    return shrine.name_jp if shrine else None


def _visit_events(user) -> list[JourneyEvent]:
    visits = (
        Visit.objects.filter(user=user)
        .exclude(status="removed")
        .select_related("shrine")
        .order_by("-visited_at", "-id")
    )
    return [
        {
            "id": f"visit:{visit.id}",
            "event_type": "visit_completed",
            "occurred_at": visit.visited_at,
            "title": "参拝しました",
            "description": f"{visit.shrine.name_jp}に参拝しました。",
            "thread_id": None,
            "shrine_id": visit.shrine_id,
            "shrine_name": visit.shrine.name_jp,
            "metadata": {"note": visit.note or ""},
        }
        for visit in visits
    ]


def _reflection_events(user) -> list[JourneyEvent]:
    reflections = (
        ShrineReflection.objects.filter(user=user)
        .select_related("shrine")
        .order_by("-created_at", "-id")
    )
    return [
        {
            "id": f"reflection:{reflection.id}",
            "event_type": "reflection_created",
            "occurred_at": reflection.created_at,
            "title": "振り返りを書きました",
            "description": reflection.answer,
            "thread_id": None,
            "shrine_id": reflection.shrine_id,
            "shrine_name": reflection.shrine.name_jp,
            "metadata": {
                "history_theme": reflection.history_theme,
                "prompt": reflection.prompt,
                "mood_before": reflection.mood_before,
                "mood_after": reflection.mood_after,
            },
        }
        for reflection in reflections
    ]


def _string_or_empty(value: Any) -> str:
    return value if isinstance(value, str) else ""
