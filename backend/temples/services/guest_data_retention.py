# backend/temples/services/guest_data_retention.py
"""匿名Ownerに紐づく永続データの保持期限（Retention）。

責務:
    「どのrowが期限切れの匿名データか」の判定と、その安全な削除だけ。

このモジュールが守る境界:
    - 認証済み user を持つ row は絶対に削除しない
    - 匿名Ownerを特定できない異常 row は推測で削除しない（残して調査対象にする）
    - PII（anonymous_id / query本文 / lat / lng / message本文 / email）を
      戻り値にもログにも載せない。出すのは件数と cutoff だけ

意図的に持たないもの:
    - 定期実行のスケジュール（別Gateで決める）
    - startup時の自動実行
    - 認証済みアカウントの削除（Account deletion は別機能）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from temples.models import (
    ConciergeMessage,
    ConciergeRecommendationLog,
    ConciergeThread,
    FeatureUsage,
    WeeklyPresentationSnapshot,
)

# Production の保持期間。90日以外での運用は想定しない。
DEFAULT_RETENTION_DAYS = 90


def compute_cutoff(*, days: int = DEFAULT_RETENTION_DAYS, now: Optional[datetime] = None) -> datetime:
    """削除対象の境界時刻。

    判定は常に `< cutoff` の厳密比較とする。ちょうど境界上の row は残す。
    「90日経過」を「90日を超えた」と読むため、境界で消えないほうが安全側。
    """
    now_ = now or timezone.now()
    return now_ - timedelta(days=days)


def expired_anonymous_threads(*, cutoff: datetime) -> QuerySet[ConciergeThread]:
    """期限切れの匿名Thread。

    effective_last_activity = last_message_at があればそれ、無ければ created_at。
    `Coalesce` を使わず Q の OR で書いているのは、NULL 比較の意図を
    そのまま読める形に残すため。

    絶対条件:
        - user を持つ Thread は対象にしない（`user__isnull=True`）
        - anonymous_id が無い / 空の異常 row は対象にしない
    """
    return ConciergeThread.objects.filter(
        Q(last_message_at__isnull=False, last_message_at__lt=cutoff)
        | Q(last_message_at__isnull=True, created_at__lt=cutoff),
        user__isnull=True,
        anonymous_id__isnull=False,
    ).exclude(anonymous_id="")


def expired_anonymous_feature_usages(*, cutoff: datetime) -> QuerySet[FeatureUsage]:
    """期限切れの匿名 FeatureUsage。

    scope=anonymous かつ user を持たず、anon_id が空でない row のみ。
    scope=user の row と、scope が anonymous でも anon_id を持たない異常 row は残す。

    `chk_feature_usage_scope_target` により scope=anonymous なら user は NULL のはずだが、
    DB制約に依存せず query 自身でも認証User除外を保証する。制約が将来ゆるめられても
    Retention の安全契約が崩れないようにするため。
    """
    return FeatureUsage.objects.filter(
        scope=FeatureUsage.Scope.ANONYMOUS,
        user__isnull=True,
        updated_at__lt=cutoff,
    ).exclude(anon_id="")


def expired_anonymous_weekly_snapshots(*, cutoff: datetime) -> QuerySet[WeeklyPresentationSnapshot]:
    """期限切れの匿名 WeeklyPresentationSnapshot。

    user IS NULL かつ anonymous_id が非NULL・非空の row のみ。
    Owner XOR 制約があるため通常は両立しないが、制約に依存せず明示的に絞る。

    anonymous_id="" は「匿名Ownerを特定できない異常 row」として扱い、削除しない。
    ConciergeThread / FeatureUsage と同じ安全契約に揃える。
    """
    return WeeklyPresentationSnapshot.objects.filter(
        user__isnull=True,
        anonymous_id__isnull=False,
        created_at__lt=cutoff,
    ).exclude(anonymous_id="")


def expired_anonymous_recommendation_logs(
    *, thread_ids
) -> QuerySet[ConciergeRecommendationLog]:
    """削除対象Threadに紐づく RecommendationLog のうち、匿名Ownerのものだけ。

    Thread が匿名でも、log 自身が認証済み user を持つことがある
    （匿名で始めた相談の途中でログインした場合など）。その log は匿名データではないので
    削除しない。Thread 削除時に `thread` が SET_NULL になり、user との紐付けは残る。
    """
    return ConciergeRecommendationLog.objects.filter(
        thread_id__in=thread_ids, user__isnull=True
    )


@dataclass(frozen=True)
class GuestDataPurgeReport:
    """件数と cutoff だけを持つ。PII は載せない。"""

    cutoff: datetime
    days: int
    executed: bool
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def collect_expired_counts(*, cutoff: datetime) -> dict[str, int]:
    """削除せずに対象件数だけを数える（dry-run 用）。

    ConciergeMessage は Thread の CASCADE で消えるため、
    実削除と同じ見積りになるよう対象Threadに紐づく件数を数える。
    """
    threads = expired_anonymous_threads(cutoff=cutoff)

    return {
        "ConciergeThread": threads.count(),
        "ConciergeMessage": ConciergeMessage.objects.filter(thread__in=threads).count(),
        "ConciergeRecommendationLog": expired_anonymous_recommendation_logs(
            thread_ids=threads.values_list("id", flat=True)
        ).count(),
        "FeatureUsage": expired_anonymous_feature_usages(cutoff=cutoff).count(),
        "WeeklyPresentationSnapshot": expired_anonymous_weekly_snapshots(cutoff=cutoff).count(),
    }


@transaction.atomic
def purge_expired_guest_data(*, cutoff: datetime) -> dict[str, int]:
    """期限切れの匿名データを削除し、モデル別の削除件数を返す。

    削除順序（この順でなければならない）:
        1. ConciergeRecommendationLog（匿名Ownerのものだけ）
           `thread` は on_delete=SET_NULL なので、Thread を先に消すと
           log 側は thread=NULL で残ってしまう。明示的に先へ削除する。
           認証済み user を持つ log は削除せず、thread=NULL で残す。
        2. ConciergeThread
           ConciergeMessage は thread の CASCADE で同時に消える。
        3. FeatureUsage / WeeklyPresentationSnapshot（Thread とは独立）

    注記:
        ConciergeRecommendationClickLog は temples migration 0108 で正式退役済み
        （model / table ともに存在しない）。復活した場合は
        ConciergeRecommendationLog への CASCADE で 1. に巻き取られる。
    """
    threads = expired_anonymous_threads(cutoff=cutoff)
    # delete() 後に queryset を数え直さないよう、対象 id を先に確定させる。
    thread_ids = list(threads.values_list("id", flat=True))

    counts: dict[str, int] = {
        "ConciergeThread": 0,
        "ConciergeMessage": 0,
        "ConciergeRecommendationLog": 0,
        "FeatureUsage": 0,
        "WeeklyPresentationSnapshot": 0,
    }

    if thread_ids:
        log_deleted, _ = expired_anonymous_recommendation_logs(thread_ids=thread_ids).delete()
        counts["ConciergeRecommendationLog"] = log_deleted

        # CASCADE 分も含めた内訳が per-model dict で返る。
        _, per_model = ConciergeThread.objects.filter(id__in=thread_ids).delete()
        counts["ConciergeThread"] = per_model.get("temples.ConciergeThread", 0)
        counts["ConciergeMessage"] = per_model.get("temples.ConciergeMessage", 0)

    usage_deleted, _ = expired_anonymous_feature_usages(cutoff=cutoff).delete()
    counts["FeatureUsage"] = usage_deleted

    snapshot_deleted, _ = expired_anonymous_weekly_snapshots(cutoff=cutoff).delete()
    counts["WeeklyPresentationSnapshot"] = snapshot_deleted

    return counts


def run_guest_data_retention(
    *,
    days: int = DEFAULT_RETENTION_DAYS,
    execute: bool = False,
    now: Optional[datetime] = None,
) -> GuestDataPurgeReport:
    """dry-run / 実削除の共通入口。

    execute=False（既定）では DB を一切変更せず、対象件数だけを返す。
    """
    cutoff = compute_cutoff(days=days, now=now)

    if not execute:
        return GuestDataPurgeReport(
            cutoff=cutoff, days=days, executed=False, counts=collect_expired_counts(cutoff=cutoff)
        )

    return GuestDataPurgeReport(
        cutoff=cutoff, days=days, executed=True, counts=purge_expired_guest_data(cutoff=cutoff)
    )
