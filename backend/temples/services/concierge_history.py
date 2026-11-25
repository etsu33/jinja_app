from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional, Any

from django.db import transaction
from django.db.models import Count, Max
from django.utils import timezone

from temples.models import (
    ActionEvent,
    ConciergeMessage,
    ConciergeThread,
    Favorite,
    ShrineInteractionLog,
    ShrineReflection,
    Visit,
)

from temples.services.reflection_state_change import build_reflection_state_change


HistoryActionState = str


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


def calculate_reflection_profile_breakdown(
    *,
    behavior_breakdown: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Reflection Profile v1: reflection_signal のみを対象にする。
    behavior_breakdown から抽出するため DB 再クエリなし。
    reflection 内容の意味解析はこの PR では行わない。
    """
    bd = behavior_breakdown or {}
    reflection = float(bd.get("reflection_signal") or 0.0)
    return {
        "score": reflection,
        "reflection_signal": reflection,
        "status": "reflected" if reflection > 0 else "not_reflected",
        "reason": "reflection_saved_only",
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

    reflection = _latest_reflection(user=user, shrine_id=shrine_id)
    if reflection is None:
        return None

    return _reflection_hint_payload(reflection)


def _latest_reflection(*, user, shrine_id: int | None) -> ShrineReflection | None:
    """build_recent_reflection_hint が使う「最新の reflection」の query（created_at 降順の先頭）。

    同じ created_at の行が複数あるときの順序は定義していない（DB の返す順）。一括取得側（B-1）も同時刻の
    ときはこの関数に委ね、新しい選択規則を持ち込まない。
    """
    qs = ShrineReflection.objects.filter(user=user).select_related("shrine")
    if shrine_id is not None:
        qs = qs.filter(shrine_id=shrine_id)
    return qs.order_by("-created_at").first()


def _reflection_hint_payload(reflection: ShrineReflection) -> dict[str, Any]:
    """build_recent_reflection_hint の応答形（DB は読まない。shrine は select_related 済みであること）。"""
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


# ---------------------------------------------------------------------------
# B-1: recommendation 用の履歴一括取得
# docs/audit/concierge-latency-result-failure-root-cause-2026-10-27.md §7 B-1
#
# 上の per-shrine 関数（classify_shrine_action_state / calculate_shrine_behavior_signal_breakdown /
# build_recent_reflection_hint）は 1 候補あたり最大 14 クエリを逐次に発行する。Concierge の推薦では候補 20 件に
# 対して同じ値を、request ごと・table ごとに 1 クエリでまとめて読む。
#
# 同値性（tests/test_concierge_history_batch.py で per-shrine 関数と突き合わせる）:
# - filter は同一（user / shrine_id / action_type / Visit.status="added"）
# - 「最新」は ORDER BY ... DESC LIMIT 1 の代わりに MAX()。対象の日時列はすべて NOT NULL なので値は一致する
# - 件数は COUNT()。存在判定は件数 > 0 / 最新日時の有無から導く
# - recency は同じ _recency_multiplier を、同じ最新日時に対して適用する
# - action state の優先順位は reflection > visit(added) > favorite > route_open > detail_view
# - reflection hint の行: per-shrine 版は created_at 降順の先頭で、同時刻の行どうしの順は定義していない。
#   一括版は最新時刻の行が 1 件ならそれを使い、同時刻の行が複数ある shrine だけ per-shrine 版と同じ query
#   （_latest_reflection）で選び直す。新しい選択規則は持ち込まない（同時刻の shrine ごとに 1 クエリ増える）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ShrineHistoryFacts:
    """1 user × 1 shrine の履歴の要約（推薦の behavior signal / action state / reflection hint の入力）。"""

    detail_view_count: int = 0
    detail_view_latest: Optional[datetime] = None
    route_open_count: int = 0
    route_open_latest: Optional[datetime] = None
    favorite_latest: Optional[datetime] = None
    visit_added_latest: Optional[datetime] = None
    action_completed_latest: Optional[datetime] = None
    latest_reflection: Optional[ShrineReflection] = None

    @property
    def reflection_latest(self) -> Optional[datetime]:
        return self.latest_reflection.created_at if self.latest_reflection is not None else None


EMPTY_SHRINE_HISTORY_FACTS = ShrineHistoryFacts()


def load_shrine_history_facts(*, user, shrine_ids: Iterable[int | None]) -> dict[int, ShrineHistoryFacts] | None:
    """`shrine_ids` の履歴を table ごとに 1 クエリで読む（5 クエリ。最新 reflection が同時刻で複数ある shrine
    ごとに +1。候補数には依存しない）。

    未認証なら None を返す（呼び出し側は従来の per-shrine 経路 = DB を読まない anonymous 経路を使う）。
    履歴の無い shrine は結果に含めない（EMPTY_SHRINE_HISTORY_FACTS として扱う）。
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return None

    ids = sorted({int(i) for i in shrine_ids if isinstance(i, int) and not isinstance(i, bool)})
    if not ids:
        return {}

    values: dict[int, dict[str, Any]] = {}

    def slot(shrine_id: int) -> dict[str, Any]:
        return values.setdefault(shrine_id, {})

    interaction_rows = (
        ShrineInteractionLog.objects.filter(
            user=user,
            shrine_id__in=ids,
            action_type__in=[
                ShrineInteractionLog.ActionType.DETAIL_VIEW,
                ShrineInteractionLog.ActionType.ROUTE_OPEN,
            ],
        )
        .order_by()
        .values("shrine_id", "action_type")
        .annotate(n=Count("id"), latest=Max("created_at"))
    )
    for row in interaction_rows:
        prefix = "detail_view" if row["action_type"] == ShrineInteractionLog.ActionType.DETAIL_VIEW else "route_open"
        slot(row["shrine_id"]).update({f"{prefix}_count": int(row["n"]), f"{prefix}_latest": row["latest"]})

    for model, extra_filter, column, key in (
        (Favorite, {}, "created_at", "favorite_latest"),
        (Visit, {"status": "added"}, "visited_at", "visit_added_latest"),
        (ActionEvent, {"action_type": ActionEvent.ActionType.ACTION_COMPLETED}, "created_at", "action_completed_latest"),
    ):
        rows = (
            model.objects.filter(user=user, shrine_id__in=ids, **extra_filter)
            .order_by()
            .values("shrine_id")
            .annotate(latest=Max(column))
        )
        for row in rows:
            slot(row["shrine_id"])[key] = row["latest"]

    # 各 shrine の最新 reflection（hint の内容と reflection signal の日時）。
    reflections = (
        ShrineReflection.objects.filter(user=user, shrine_id__in=ids)
        .select_related("shrine")
        .order_by("shrine_id", "-created_at")
    )
    tied_shrine_ids: set[int] = set()
    for reflection in reflections:
        bucket = slot(reflection.shrine_id)
        latest = bucket.get("latest_reflection")
        if latest is None:
            bucket["latest_reflection"] = reflection
        elif reflection.created_at == latest.created_at:
            tied_shrine_ids.add(reflection.shrine_id)
    # 最新時刻の行が複数ある shrine は、per-shrine 版と同じ query で選ぶ（同時刻の順序規則を新設しない）。
    for shrine_id in sorted(tied_shrine_ids):
        values[shrine_id]["latest_reflection"] = _latest_reflection(user=user, shrine_id=shrine_id)

    return {shrine_id: ShrineHistoryFacts(**fields) for shrine_id, fields in values.items()}


def behavior_signal_breakdown_from_facts(facts: ShrineHistoryFacts) -> dict[str, float]:
    """calculate_shrine_behavior_signal_breakdown と同じ計算を、一括取得した値から行う。"""
    detail_view_signal = facts.detail_view_count * 0.2 * _recency_multiplier(facts.detail_view_latest)
    route_open_signal = facts.route_open_count * 0.6 * _recency_multiplier(facts.route_open_latest)

    save_signal = 0.0
    if facts.favorite_latest is not None:
        save_signal = 1.5 * _recency_multiplier(facts.favorite_latest)

    visit_signal = 0.0
    if facts.visit_added_latest is not None:
        visit_signal = 3.0 * _recency_multiplier(facts.visit_added_latest)

    reflection_signal = 0.0
    if facts.reflection_latest is not None:
        reflection_signal = 4.0 * _recency_multiplier(facts.reflection_latest)

    action_completed_signal = 0.0
    if facts.action_completed_latest is not None:
        action_completed_signal = 2.0 * _recency_multiplier(facts.action_completed_latest)

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


def action_state_from_facts(facts: ShrineHistoryFacts) -> HistoryActionState:
    """classify_shrine_action_state と同じ優先順位。"""
    if facts.latest_reflection is not None:
        return "reflected"
    if facts.visit_added_latest is not None:
        return "visited"
    if facts.favorite_latest is not None:
        return "saved"
    if facts.route_open_count > 0:
        return "route_opened"
    if facts.detail_view_count > 0:
        return "detail_viewed"
    return "none"


def reflection_hint_from_facts(facts: ShrineHistoryFacts) -> dict[str, Any] | None:
    """build_recent_reflection_hint(shrine_id=...) と同じ応答形。"""
    if facts.latest_reflection is None:
        return None
    return _reflection_hint_payload(facts.latest_reflection)


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
            # user を持つ thread は、anonymous_id が一致していても匿名経路からは触れない
            # （ConciergeThreadDetailView の読み取り条件と同じ。docs/audit/fu2-p7-concierge-thread-ownership-2026-10-27.md F3）。
            thread = ConciergeThread.objects.select_for_update().get(
                id=thread_id,
                user__isnull=True,
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
