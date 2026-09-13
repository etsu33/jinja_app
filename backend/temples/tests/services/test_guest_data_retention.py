"""匿名Owner データの保持期限（90日）の契約。

境界の扱いを固定する:
    判定は常に `effective_last_activity < cutoff` の厳密比較。
    ちょうど境界上の row は残す（「90日経過」を「90日を超えた」と読む）。

絶対条件も固定する:
    - 認証済み user を持つ row は、どれだけ古くても削除しない
    - anonymous_id が無い / 空の異常 row は推測で削除しない
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from temples.models import (
    ConciergeMessage,
    ConciergeRecommendationLog,
    ConciergeThread,
    FeatureUsage,
    WeeklyPresentationSnapshot,
)
from temples.services.guest_data_retention import (
    DEFAULT_RETENTION_DAYS,
    compute_cutoff,
    run_guest_data_retention,
)
from tests.factories import UserFactory

NOW = timezone.now()


def _ago(days: float):
    return NOW - timedelta(days=days)


def _thread(*, anonymous_id="anon-1", user=None, created_at=None, last_message_at=None):
    """last_message_at は ConciergeMessage.save() が上書きするため直接 update で入れる。"""
    thread = ConciergeThread.objects.create(
        user=user,
        anonymous_id=anonymous_id,
        created_at=created_at or NOW,
    )
    ConciergeThread.objects.filter(pk=thread.pk).update(
        created_at=created_at or NOW, last_message_at=last_message_at
    )
    thread.refresh_from_db()
    return thread


def _feature_usage(*, anon_id="anon-1", updated_at, scope=FeatureUsage.Scope.ANONYMOUS, user=None):
    usage = FeatureUsage.objects.create(
        scope=scope,
        user=user,
        anon_id=anon_id,
        feature=FeatureUsage.Feature.CONCIERGE,
        count=1,
    )
    # updated_at は auto_now。QuerySet.update() は auto_now を発火させない。
    FeatureUsage.objects.filter(pk=usage.pk).update(updated_at=updated_at)
    return usage


def _snapshot(*, created_at, anonymous_id="anon-1", user=None, week_start=None):
    return WeeklyPresentationSnapshot.objects.create(
        user=user,
        anonymous_id=anonymous_id,
        week_start=(week_start or NOW.date()),
        purpose="work",
        direction_fingerprint="f" * 64,
        weekly_theme={"key": "calm"},
        featured_shrine_ids=[],
        presentation_version="v1",
        created_at=created_at,
    )


def _purge(days=DEFAULT_RETENTION_DAYS):
    return run_guest_data_retention(days=days, execute=True, now=NOW)


# --------------------------------------------------------------------------
# cutoff 境界
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_thread_at_89_days_is_kept():
    thread = _thread(last_message_at=_ago(89))

    _purge()

    assert ConciergeThread.objects.filter(pk=thread.pk).exists()


@pytest.mark.django_db
def test_thread_exactly_at_the_90_day_boundary_is_kept():
    """境界そのものは `<` を満たさないので残る。"""
    cutoff = compute_cutoff(days=DEFAULT_RETENTION_DAYS, now=NOW)
    thread = _thread(last_message_at=cutoff)

    _purge()

    assert ConciergeThread.objects.filter(pk=thread.pk).exists()


@pytest.mark.django_db
def test_thread_older_than_90_days_is_deleted():
    thread = _thread(last_message_at=_ago(91))

    report = _purge()

    assert not ConciergeThread.objects.filter(pk=thread.pk).exists()
    assert report.counts["ConciergeThread"] == 1


@pytest.mark.django_db
def test_thread_without_last_message_at_falls_back_to_created_at():
    stale = _thread(anonymous_id="anon-stale", created_at=_ago(120), last_message_at=None)
    fresh = _thread(anonymous_id="anon-fresh", created_at=_ago(10), last_message_at=None)

    _purge()

    assert not ConciergeThread.objects.filter(pk=stale.pk).exists()
    assert ConciergeThread.objects.filter(pk=fresh.pk).exists()


@pytest.mark.django_db
def test_recent_message_keeps_an_old_thread():
    """created_at が古くても last_message_at が新しければ残る（last_message_at 優先）。"""
    thread = _thread(created_at=_ago(400), last_message_at=_ago(5))

    _purge()

    assert ConciergeThread.objects.filter(pk=thread.pk).exists()


# --------------------------------------------------------------------------
# 絶対条件
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_authenticated_thread_is_never_deleted_even_when_ancient():
    user = UserFactory()
    thread = _thread(user=user, anonymous_id=None, created_at=_ago(400), last_message_at=_ago(400))

    report = _purge()

    assert ConciergeThread.objects.filter(pk=thread.pk).exists()
    assert report.counts["ConciergeThread"] == 0


@pytest.mark.django_db
def test_authenticated_thread_with_anonymous_id_is_also_kept():
    """匿名IDが残っていても、user を持つ Thread は匿名データではない。"""
    user = UserFactory()
    thread = _thread(user=user, anonymous_id="anon-merged", last_message_at=_ago(400))

    _purge()

    assert ConciergeThread.objects.filter(pk=thread.pk).exists()


@pytest.mark.django_db
def test_thread_without_anonymous_id_is_not_guessed_at():
    """user も anonymous_id も無い異常 row は、古くても推測で削除しない。"""
    thread = ConciergeThread.objects.create(anonymous_id="placeholder", created_at=_ago(400))
    # CheckConstraint を迂回して異常 row を再現する（本来は発生しない形）。
    ConciergeThread.objects.filter(pk=thread.pk).update(anonymous_id="", created_at=_ago(400))

    _purge()

    assert ConciergeThread.objects.filter(pk=thread.pk).exists()


# --------------------------------------------------------------------------
# 関連データの削除経路
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_messages_are_deleted_with_their_thread_by_cascade():
    thread = _thread(created_at=_ago(200), last_message_at=None)
    ConciergeMessage.objects.create(thread=thread, role="user", content="x")
    ConciergeMessage.objects.create(thread=thread, role="assistant", content="y")
    # Message 作成で last_message_at が現在時刻に更新されるため、期限切れへ戻す。
    ConciergeThread.objects.filter(pk=thread.pk).update(last_message_at=_ago(200))

    report = _purge()

    assert not ConciergeThread.objects.filter(pk=thread.pk).exists()
    assert ConciergeMessage.objects.filter(thread_id=thread.pk).count() == 0
    assert report.counts["ConciergeMessage"] == 2


@pytest.mark.django_db
def test_recommendation_logs_are_deleted_explicitly_before_the_thread():
    """thread は on_delete=SET_NULL。明示削除しないと thread=NULL で残る。"""
    thread = _thread(created_at=_ago(200), last_message_at=None)
    ConciergeRecommendationLog.objects.create(thread=thread, query="secret query")

    report = _purge()

    assert ConciergeRecommendationLog.objects.count() == 0
    assert report.counts["ConciergeRecommendationLog"] == 1


@pytest.mark.django_db
def test_recommendation_logs_of_kept_threads_survive():
    fresh = _thread(anonymous_id="anon-fresh", last_message_at=_ago(1))
    ConciergeRecommendationLog.objects.create(thread=fresh, query="keep me")

    _purge()

    assert ConciergeRecommendationLog.objects.count() == 1


def test_recommendation_click_log_model_is_retired():
    """ConciergeRecommendationClickLog は migration 0108 で正式退役済み。

    「ClickLog は RecommendationLog の CASCADE で消える」という前提の回帰testは
    書けない（model も table も存在しない）。復活させる場合は、RecommendationLog
    への CASCADE を確認したうえでこのtestを本物のcascade testへ置き換えること。
    """
    from django.apps import apps

    with pytest.raises(LookupError):
        apps.get_model("temples", "ConciergeRecommendationClickLog")


# --------------------------------------------------------------------------
# FeatureUsage / WeeklyPresentationSnapshot
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_anonymous_feature_usage_is_deleted_only_when_expired():
    expired = _feature_usage(anon_id="anon-old", updated_at=_ago(120))
    fresh = _feature_usage(anon_id="anon-new", updated_at=_ago(10))

    report = _purge()

    assert not FeatureUsage.objects.filter(pk=expired.pk).exists()
    assert FeatureUsage.objects.filter(pk=fresh.pk).exists()
    assert report.counts["FeatureUsage"] == 1


@pytest.mark.django_db
def test_user_scoped_feature_usage_is_never_deleted():
    user = UserFactory()
    usage = _feature_usage(
        anon_id="", updated_at=_ago(400), scope=FeatureUsage.Scope.USER, user=user
    )

    _purge()

    assert FeatureUsage.objects.filter(pk=usage.pk).exists()


@pytest.mark.django_db
def test_anonymous_weekly_snapshot_is_deleted_only_when_expired():
    expired = _snapshot(created_at=_ago(120), anonymous_id="anon-old")
    fresh = _snapshot(created_at=_ago(10), anonymous_id="anon-new")

    report = _purge()

    assert not WeeklyPresentationSnapshot.objects.filter(pk=expired.pk).exists()
    assert WeeklyPresentationSnapshot.objects.filter(pk=fresh.pk).exists()
    assert report.counts["WeeklyPresentationSnapshot"] == 1


@pytest.mark.django_db
def test_user_owned_weekly_snapshot_is_never_deleted():
    user = UserFactory()
    snapshot = _snapshot(created_at=_ago(400), anonymous_id=None, user=user)

    _purge()

    assert WeeklyPresentationSnapshot.objects.filter(pk=snapshot.pk).exists()


# --------------------------------------------------------------------------
# dry-run / 冪等性
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_dry_run_reports_counts_without_changing_the_database():
    thread = _thread(created_at=_ago(200), last_message_at=None)
    ConciergeMessage.objects.create(thread=thread, role="user", content="x")
    ConciergeThread.objects.filter(pk=thread.pk).update(last_message_at=_ago(200))
    ConciergeRecommendationLog.objects.create(thread=thread, query="q")
    _feature_usage(anon_id="anon-old", updated_at=_ago(120))
    _snapshot(created_at=_ago(120))

    report = run_guest_data_retention(days=DEFAULT_RETENTION_DAYS, execute=False, now=NOW)

    assert report.executed is False
    assert report.counts == {
        "ConciergeThread": 1,
        "ConciergeMessage": 1,
        "ConciergeRecommendationLog": 1,
        "FeatureUsage": 1,
        "WeeklyPresentationSnapshot": 1,
    }
    # DB は1行も変わらない
    assert ConciergeThread.objects.count() == 1
    assert ConciergeMessage.objects.count() == 1
    assert ConciergeRecommendationLog.objects.count() == 1
    assert FeatureUsage.objects.count() == 1
    assert WeeklyPresentationSnapshot.objects.count() == 1


@pytest.mark.django_db
def test_second_run_deletes_nothing_and_succeeds():
    _thread(created_at=_ago(200), last_message_at=None)
    _feature_usage(anon_id="anon-old", updated_at=_ago(120))
    _snapshot(created_at=_ago(120))

    first = _purge()
    second = _purge()

    assert first.total > 0
    assert second.total == 0
    assert second.counts == {
        "ConciergeThread": 0,
        "ConciergeMessage": 0,
        "ConciergeRecommendationLog": 0,
        "FeatureUsage": 0,
        "WeeklyPresentationSnapshot": 0,
    }
