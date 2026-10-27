"""Shared fixture data for the Concierge history batch-loading tests（B-1）.

docs/audit/concierge-latency-result-failure-root-cause-2026-10-27.md §7 B-1.

`build_mixed_history()` creates one user with varied history across several shrines, an unrelated user whose history
must never leak, and empty shrines. All timestamps are fixed relative to `NOW`. Callers freeze
`temples.services.concierge_history.timezone.now` to `NOW`, so the recency multipliers are deterministic.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

from temples.models import (
    ActionEvent,
    Favorite,
    Shrine,
    ShrineInteractionLog,
    ShrineReflection,
    Visit,
)

NOW = datetime(2026, 10, 27, 12, 0, 0, tzinfo=dt_timezone.utc)
DV = ShrineInteractionLog.ActionType.DETAIL_VIEW
RO = ShrineInteractionLog.ActionType.ROUTE_OPEN
DONE = ActionEvent.ActionType.ACTION_COMPLETED
STARTED = ActionEvent.ActionType.ACTION_STARTED


def ago(days: float) -> datetime:
    return NOW - timedelta(days=days)


def make_shrines(n: int, *, prefix: str = "batch") -> list[Shrine]:
    return [
        Shrine.objects.create(
            kind="shrine",
            name_jp=f"{prefix}-神社-{i}",
            address=f"東京都{prefix}{i}",
            latitude=35.0 + i * 0.001,
            longitude=139.0 + i * 0.001,
            goriyaku="厄除け / 縁結び" if i % 2 == 0 else "仕事運",
            history_theme="再出発" if i % 3 == 0 else "",
        )
        for i in range(n)
    ]


def _log(user, shrine, action, days):
    ShrineInteractionLog.objects.create(user=user, shrine=shrine, action_type=action, created_at=ago(days))


def _reflection(user, shrine, days, *, answer="感謝できた", theme="再出発", mood_before="不安", mood_after="安心"):
    return ShrineReflection.objects.create(
        user=user,
        shrine=shrine,
        answer=answer,
        history_theme=theme,
        mood_before=mood_before,
        mood_after=mood_after,
        created_at=ago(days),
    )


def build_mixed_history(user, other_user, shrines: list[Shrine]) -> None:
    """Varied history on shrines[0..6]; shrines[7:] stay empty for `user`."""
    s = shrines
    # s0: everything, several records per kind, every recency bucket
    for days in (1, 60, 200):
        _log(user, s[0], DV, days)
    _log(user, s[0], RO, 2)
    Favorite.objects.create(user=user, shrine=s[0])
    Favorite.objects.filter(user=user, shrine=s[0]).update(created_at=ago(45))  # auto_now_add: set afterwards
    Visit.objects.create(user=user, shrine=s[0], visited_at=ago(10), status="added")
    Visit.objects.create(user=user, shrine=s[0], visited_at=ago(1), status="removed")  # newer, but not "added"
    _reflection(user, s[0], 5, answer="前より落ち着いた")
    _reflection(user, s[0], 40, answer="まだ迷いがある", mood_after="不安")
    ActionEvent.objects.create(user=user, shrine=s[0], action_type=DONE, action_suggestion_id="a1", created_at=ago(100))
    ActionEvent.objects.create(user=user, shrine=s[0], action_type=STARTED, action_suggestion_id="a2", created_at=ago(1))

    # s1: favorite only（recent）
    Favorite.objects.create(user=user, shrine=s[1])
    Favorite.objects.filter(user=user, shrine=s[1]).update(created_at=ago(3))

    # s2: removed visit only → must not count as visited
    Visit.objects.create(user=user, shrine=s[2], visited_at=ago(2), status="removed")

    # s3: two route opens with the SAME timestamp + one detail view with the same timestamp
    _log(user, s[3], RO, 20)
    _log(user, s[3], RO, 20)
    _log(user, s[3], DV, 20)

    # s4: old reflection only
    _reflection(user, s[4], 120, answer="区切りをつけた")

    # s5: detail views only, two buckets
    _log(user, s[5], DV, 31)
    _log(user, s[5], DV, 91)

    # s6: several added visits; latest wins; plus a completed action
    Visit.objects.create(user=user, shrine=s[6], visited_at=ago(80), status="added")
    Visit.objects.create(user=user, shrine=s[6], visited_at=ago(15), status="added")
    ActionEvent.objects.create(user=user, shrine=s[6], action_type=DONE, action_suggestion_id="a3", created_at=ago(7))

    # another user's history on shared shrines must never be visible to `user`
    _log(other_user, s[1], RO, 1)
    _reflection(other_user, s[7], 1, answer="他人の記録")
    Visit.objects.create(user=other_user, shrine=s[8], visited_at=ago(1), status="added")
    Favorite.objects.create(user=other_user, shrine=s[9])
    ActionEvent.objects.create(user=other_user, shrine=s[7], action_type=DONE, action_suggestion_id="o1", created_at=ago(1))


def candidate_recs(shrines: list[Shrine]) -> list[dict]:
    """The dict shape the Concierge pool passes to `_attach_breakdown`（ids, names, tag lists）."""
    return [
        {
            "shrine_id": sh.pk,
            "id": sh.pk,
            "name": sh.name_jp,
            "address": sh.address,
            "goriyaku": sh.goriyaku,
            "history_theme": sh.history_theme,
            "astro_tags": [],
            "astro_elements": [],
            "popular_score": 3,
            "distance_m": 1000 + i * 250,
        }
        for i, sh in enumerate(shrines)
    ]
