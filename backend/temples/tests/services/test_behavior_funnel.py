

from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from temples.models import Favorite, Shrine, ShrineInteractionLog, ShrineReflection, Visit
from temples.services.behavior_funnel import get_behavior_funnel_metrics


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="behavior-funnel-user",
        email="behavior-funnel@example.com",
        password="password-test",
    )


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user(
        username="behavior-funnel-other-user",
        email="behavior-funnel-other@example.com",
        password="password-test",
    )


@pytest.fixture
def shrine():
    return Shrine.objects.create(name_jp="行動ファネル神社", address="東京都千代田区")


@pytest.fixture
def other_shrine():
    return Shrine.objects.create(name_jp="別の行動ファネル神社", address="東京都港区")


@pytest.mark.django_db
def test_get_behavior_funnel_metrics_counts_actions_and_cvr(user, shrine):
    ShrineInteractionLog.objects.create(
        user=user,
        shrine=shrine,
        action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
        source="shrine_detail",
    )
    ShrineInteractionLog.objects.create(
        user=user,
        shrine=shrine,
        action_type=ShrineInteractionLog.ActionType.ROUTE_OPEN,
        source="shrine_detail",
    )
    Favorite.objects.create(user=user, shrine=shrine)
    Visit.objects.create(user=user, shrine=shrine, status="added")
    ShrineReflection.objects.create(
        user=user,
        shrine=shrine,
        history_theme="再出発",
        prompt="参拝して、今どんな変化がありましたか？",
        answer="一歩進めそうです。",
    )

    metrics = get_behavior_funnel_metrics()

    assert metrics.detail_view_count == 1
    assert metrics.route_open_count == 1
    assert metrics.save_count == 1
    assert metrics.visit_count == 1
    assert metrics.reflection_count == 1
    assert metrics.save_to_visit_cvr == 1.0
    assert metrics.visit_to_reflection_cvr == 1.0


@pytest.mark.django_db
def test_get_behavior_funnel_metrics_filters_by_user(user, other_user, shrine):
    ShrineInteractionLog.objects.create(
        user=user,
        shrine=shrine,
        action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
        source="shrine_detail",
    )
    ShrineInteractionLog.objects.create(
        user=other_user,
        shrine=shrine,
        action_type=ShrineInteractionLog.ActionType.ROUTE_OPEN,
        source="shrine_detail",
    )
    Favorite.objects.create(user=user, shrine=shrine)
    Visit.objects.create(user=other_user, shrine=shrine, status="added")

    metrics = get_behavior_funnel_metrics(user=user)

    assert metrics.detail_view_count == 1
    assert metrics.route_open_count == 0
    assert metrics.save_count == 1
    assert metrics.visit_count == 0
    assert metrics.reflection_count == 0
    assert metrics.save_to_visit_cvr == 0.0
    assert metrics.visit_to_reflection_cvr == 0.0


@pytest.mark.django_db
def test_get_behavior_funnel_metrics_filters_by_shrine(user, shrine, other_shrine):
    ShrineInteractionLog.objects.create(
        user=user,
        shrine=shrine,
        action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
        source="shrine_detail",
    )
    ShrineInteractionLog.objects.create(
        user=user,
        shrine=other_shrine,
        action_type=ShrineInteractionLog.ActionType.ROUTE_OPEN,
        source="shrine_detail",
    )
    Favorite.objects.create(user=user, shrine=other_shrine)
    Visit.objects.create(user=user, shrine=shrine, status="added")

    metrics = get_behavior_funnel_metrics(shrine_id=shrine.id)

    assert metrics.detail_view_count == 1
    assert metrics.route_open_count == 0
    assert metrics.save_count == 0
    assert metrics.visit_count == 1
    assert metrics.reflection_count == 0
    assert metrics.save_to_visit_cvr == 0.0
    assert metrics.visit_to_reflection_cvr == 0.0


@pytest.mark.django_db
def test_get_behavior_funnel_metrics_filters_by_period(user, shrine):
    now = timezone.now()
    old_log = ShrineInteractionLog.objects.create(
        user=user,
        shrine=shrine,
        action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
        source="shrine_detail",
    )
    ShrineInteractionLog.objects.filter(id=old_log.id).update(created_at=now - timedelta(days=10))

    ShrineInteractionLog.objects.create(
        user=user,
        shrine=shrine,
        action_type=ShrineInteractionLog.ActionType.ROUTE_OPEN,
        source="shrine_detail",
    )
    Favorite.objects.create(user=user, shrine=shrine)

    metrics = get_behavior_funnel_metrics(
        from_dt=now - timedelta(days=1),
        to_dt=now + timedelta(days=1),
    )

    assert metrics.detail_view_count == 0
    assert metrics.route_open_count == 1
    assert metrics.save_count == 1


@pytest.mark.django_db
def test_get_behavior_funnel_metrics_ignores_removed_visits(user, shrine):
    Favorite.objects.create(user=user, shrine=shrine)
    Visit.objects.create(user=user, shrine=shrine, status="removed")

    metrics = get_behavior_funnel_metrics(user=user)

    assert metrics.save_count == 1
    assert metrics.visit_count == 0
    assert metrics.save_to_visit_cvr == 0.0
