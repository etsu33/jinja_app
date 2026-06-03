

import pytest
from django.contrib.auth.models import AnonymousUser

from temples.models import Favorite, Shrine, ShrineReflection, Visit
from temples.services.concierge_history import classify_shrine_action_state


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
