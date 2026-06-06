import pytest
from django.contrib.auth.models import AnonymousUser

from temples.models import Favorite, Shrine, ShrineInteractionLog, ShrineReflection, Visit

from temples.services.concierge_history import (
    calculate_shrine_behavior_signal,
    calculate_shrine_behavior_signal_v2,
    classify_shrine_action_state,
)

@pytest.fixture
def shrine():
    return Shrine.objects.create(name_jp="分類テスト神社", address="東京都千代田区")


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="action-state-user",
        email="action-state@example.com",
        password="password-test",
    )


def test_classify_shrine_action_state_returns_none_for_anonymous_user(shrine):
    assert classify_shrine_action_state(user=AnonymousUser(), shrine_id=shrine.id) == "none"


@pytest.mark.django_db
def test_classify_shrine_action_state_returns_none_without_shrine_id(user):
    assert classify_shrine_action_state(user=user, shrine_id=None) == "none"


@pytest.mark.django_db
def test_classify_shrine_action_state_returns_none_without_action(user, shrine):
    assert classify_shrine_action_state(user=user, shrine_id=shrine.id) == "none"


@pytest.mark.django_db
def test_classify_shrine_action_state_returns_saved_when_favorite_exists(user, shrine):
    Favorite.objects.create(user=user, shrine=shrine)

    assert classify_shrine_action_state(user=user, shrine_id=shrine.id) == "saved"


@pytest.mark.django_db
def test_classify_shrine_action_state_returns_visited_when_visit_exists(user, shrine):
    Visit.objects.create(user=user, shrine=shrine, status="added")

    assert classify_shrine_action_state(user=user, shrine_id=shrine.id) == "visited"


@pytest.mark.django_db
def test_classify_shrine_action_state_returns_reflected_when_reflection_exists(user, shrine):
    ShrineReflection.objects.create(
        user=user,
        shrine=shrine,
        history_theme="勝負",
        prompt="参拝して、今どんな変化がありましたか？",
        answer="前に進む整理ができた。",
    )

    assert classify_shrine_action_state(user=user, shrine_id=shrine.id) == "reflected"


@pytest.mark.django_db
def test_classify_shrine_action_state_prioritizes_reflected_over_visit_and_favorite(user, shrine):
    Favorite.objects.create(user=user, shrine=shrine)
    Visit.objects.create(user=user, shrine=shrine, status="added")
    ShrineReflection.objects.create(
        user=user,
        shrine=shrine,
        history_theme="再出発",
        prompt="参拝して、今どんな変化がありましたか？",
        answer="一区切りついた。",
    )

    assert classify_shrine_action_state(user=user, shrine_id=shrine.id) == "reflected"



@pytest.mark.django_db
def test_shrine_interaction_log_can_store_detail_view(user, shrine):
    log = ShrineInteractionLog.objects.create(
        user=user,
        shrine=shrine,
        action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
        source="shrine_detail",
        metadata={"from": "test"},
    )

    assert log.action_type == "detail_view"
    assert log.source == "shrine_detail"
    assert log.metadata == {"from": "test"}
    assert log.thread is None


@pytest.mark.django_db
def test_classify_shrine_action_state_returns_detail_viewed_when_detail_view_exists(user, shrine):
    ShrineInteractionLog.objects.create(
        user=user,
        shrine=shrine,
        action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
        source="shrine_detail",
    )

    assert classify_shrine_action_state(user=user, shrine_id=shrine.id) == "detail_viewed"


@pytest.mark.django_db
def test_classify_shrine_action_state_returns_route_opened_when_route_open_exists(user, shrine):
    ShrineInteractionLog.objects.create(
        user=user,
        shrine=shrine,
        action_type=ShrineInteractionLog.ActionType.ROUTE_OPEN,
        source="shrine_detail",
    )

    assert classify_shrine_action_state(user=user, shrine_id=shrine.id) == "route_opened"


@pytest.mark.django_db
def test_calculate_shrine_behavior_signal_adds_detail_view_weight(user, shrine):
    ShrineInteractionLog.objects.create(
        user=user,
        shrine=shrine,
        action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
        source="shrine_detail",
    )

    assert calculate_shrine_behavior_signal(user=user, shrine_id=shrine.id) == 0.5



@pytest.mark.django_db
def test_calculate_shrine_behavior_signal_adds_route_open_weight(user, shrine):
    ShrineInteractionLog.objects.create(
        user=user,
        shrine=shrine,
        action_type=ShrineInteractionLog.ActionType.ROUTE_OPEN,
        source="shrine_detail",
    )

    assert calculate_shrine_behavior_signal(user=user, shrine_id=shrine.id) == 1.0


# --- v2 tests ---


@pytest.mark.django_db
def test_calculate_shrine_behavior_signal_v2_counts_detail_view_and_route_open(user, shrine):
    ShrineInteractionLog.objects.create(
        user=user,
        shrine=shrine,
        action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
        source="shrine_detail",
    )
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

    assert calculate_shrine_behavior_signal_v2(user=user, shrine_id=shrine.id) == 1.0


@pytest.mark.django_db
def test_calculate_shrine_behavior_signal_v2_adds_save_visit_and_reflection(user, shrine):
    Favorite.objects.create(user=user, shrine=shrine)
    Visit.objects.create(user=user, shrine=shrine, status="added")
    ShrineReflection.objects.create(
        user=user,
        shrine=shrine,
        history_theme="再出発",
        prompt="参拝して、今どんな変化がありましたか？",
        answer="整理できました。",
    )

    assert calculate_shrine_behavior_signal_v2(user=user, shrine_id=shrine.id) == 8.5


@pytest.mark.django_db
def test_calculate_shrine_behavior_signal_v2_caps_score_at_10(user, shrine):
    for _ in range(80):
        ShrineInteractionLog.objects.create(
            user=user,
            shrine=shrine,
            action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
            source="shrine_detail",
        )

    assert calculate_shrine_behavior_signal_v2(user=user, shrine_id=shrine.id) == 10.0
