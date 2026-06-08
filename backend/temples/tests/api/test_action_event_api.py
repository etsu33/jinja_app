import pytest
from rest_framework.test import APIClient

from temples.models import ActionEvent, Shrine


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="action-event-user",
        email="action-event@example.com",
        password="password-test",
    )


@pytest.fixture
def shrine():
    return Shrine.objects.create(
        name_jp="行動提案ログ神社",
        address="東京都千代田区",
    )


@pytest.mark.django_db
def test_create_action_event(api_client, user, shrine):
    api_client.force_authenticate(user=user)

    response = api_client.post(
        "/api/action-events/",
        {
            "action_type": "action_started",
            "action_suggestion_id": "challenge_choose_this_week",
            "history_theme": "勝負",
            "action_category": "prepare",
            "source": "concierge_result",
            "shrine_id": shrine.id,
            "metadata": {"screen": "result"},
        },
        format="json",
    )

    assert response.status_code == 201

    event = ActionEvent.objects.get()

    assert event.user_id == user.id
    assert event.shrine_id == shrine.id
    assert event.action_type == "action_started"
    assert event.action_suggestion_id == "challenge_choose_this_week"
    assert event.history_theme == "勝負"
    assert event.action_category == "prepare"
    assert event.source == "concierge_result"
    assert event.metadata == {"screen": "result"}


@pytest.mark.django_db
def test_create_action_event_requires_authentication(api_client):
    response = api_client.post(
        "/api/action-events/",
        {
            "action_type": "action_started",
            "action_suggestion_id": "challenge_choose_this_week",
        },
        format="json",
    )

    assert response.status_code in (401, 403)
