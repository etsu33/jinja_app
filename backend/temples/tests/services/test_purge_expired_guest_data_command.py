"""purge_expired_guest_data command の契約。

固定すること:
    - 既定は dry-run（--execute なしでは1行も消さない）
    - --execute を明示したときだけ削除する
    - 出力に PII を載せない
"""

from __future__ import annotations

from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from temples.models import (
    ConciergeMessage,
    ConciergeRecommendationLog,
    ConciergeThread,
    FeatureUsage,
    WeeklyPresentationSnapshot,
)

SECRET_ANON_ID = "anon-super-secret-id"
SECRET_QUERY = "恋愛の悩みを相談したい"
SECRET_MESSAGE = "誰にも言えない相談本文"


def _seed_expired():
    old = timezone.now() - timedelta(days=200)

    thread = ConciergeThread.objects.create(anonymous_id=SECRET_ANON_ID)
    ConciergeMessage.objects.create(thread=thread, role="user", content=SECRET_MESSAGE)
    ConciergeThread.objects.filter(pk=thread.pk).update(created_at=old, last_message_at=old)

    ConciergeRecommendationLog.objects.create(
        thread=thread, query=SECRET_QUERY, lat=35.6762, lng=139.6503
    )

    usage = FeatureUsage.objects.create(
        scope=FeatureUsage.Scope.ANONYMOUS,
        anon_id=SECRET_ANON_ID,
        feature=FeatureUsage.Feature.CONCIERGE,
        count=3,
    )
    FeatureUsage.objects.filter(pk=usage.pk).update(updated_at=old)

    WeeklyPresentationSnapshot.objects.create(
        anonymous_id=SECRET_ANON_ID,
        week_start=timezone.now().date(),
        purpose="work",
        direction_fingerprint="f" * 64,
        weekly_theme={"key": "calm"},
        featured_shrine_ids=[],
        presentation_version="v1",
        created_at=old,
    )
    return thread


def _run(*args):
    out = StringIO()
    call_command("purge_expired_guest_data", *args, stdout=out)
    return out.getvalue()


@pytest.mark.django_db
def test_default_is_dry_run_and_changes_nothing():
    thread = _seed_expired()

    output = _run()

    assert "DRY-RUN" in output
    assert "matched=1" in output
    assert "dry-run: no rows were modified" in output
    # DB は1行も変わらない
    assert ConciergeThread.objects.filter(pk=thread.pk).exists()
    assert ConciergeMessage.objects.count() == 1
    assert ConciergeRecommendationLog.objects.count() == 1
    assert FeatureUsage.objects.count() == 1
    assert WeeklyPresentationSnapshot.objects.count() == 1


@pytest.mark.django_db
def test_execute_flag_actually_deletes():
    thread = _seed_expired()

    output = _run("--execute")

    assert "EXECUTE" in output
    assert "deleted=1" in output
    assert not ConciergeThread.objects.filter(pk=thread.pk).exists()
    assert ConciergeMessage.objects.count() == 0
    assert ConciergeRecommendationLog.objects.count() == 0
    assert FeatureUsage.objects.count() == 0
    assert WeeklyPresentationSnapshot.objects.count() == 0


@pytest.mark.django_db
def test_output_contains_counts_and_cutoff_but_no_pii():
    _seed_expired()

    output = _run("--execute")

    # 出してよいもの
    assert "cutoff=" in output
    assert "days=90" in output
    for model_name in (
        "ConciergeThread",
        "ConciergeMessage",
        "ConciergeRecommendationLog",
        "FeatureUsage",
        "WeeklyPresentationSnapshot",
    ):
        assert model_name in output

    # 出してはいけないもの
    for secret in (SECRET_ANON_ID, SECRET_QUERY, SECRET_MESSAGE, "35.6762", "139.6503"):
        assert secret not in output
    # SQL 本文も出さない
    assert "SELECT" not in output
    assert "DELETE" not in output


@pytest.mark.django_db
def test_days_option_narrows_the_window():
    """--days は既定90。Production で90以外を使う運用は想定しないが、動作は固定する。"""
    thread = ConciergeThread.objects.create(anonymous_id="anon-30d")
    ConciergeThread.objects.filter(pk=thread.pk).update(
        created_at=timezone.now() - timedelta(days=40), last_message_at=None
    )

    _run("--execute")
    assert ConciergeThread.objects.filter(pk=thread.pk).exists()

    _run("--days", "30", "--execute")
    assert not ConciergeThread.objects.filter(pk=thread.pk).exists()


@pytest.mark.django_db
def test_rerun_after_execute_reports_zero():
    _seed_expired()

    _run("--execute")
    output = _run("--execute")

    assert "total deleted=0" in output


@pytest.mark.django_db
def test_invalid_days_is_rejected():
    with pytest.raises(CommandError):
        _run("--days", "0")
