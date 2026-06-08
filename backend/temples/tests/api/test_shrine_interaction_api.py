

import pytest
from rest_framework.test import APIClient

from temples.models import Shrine, ShrineInteractionLog


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="interaction-user",
        email="interaction@example.com",
        password="password-test",
    )


@pytest.fixture
def shrine():
    return Shrine.objects.create(
        name_jp="行動ログ神社",
        address="東京都千代田区",
    )


@pytest.mark.django_db
def test_create_shrine_interaction_log(api_client, user, shrine):
    api_client.force_authenticate(user=user)

    response = api_client.post(
        "/api/shrine-interactions/",
        {
            "shrine_id": shrine.id,
            "action_type": "detail_view",
            "source": "shrine_detail",
            "metadata": {"screen": "detail"},
        },
        format="json",
    )

    assert response.status_code == 201

    log = ShrineInteractionLog.objects.get()

    assert log.user_id == user.id
    assert log.shrine_id == shrine.id
    assert log.action_type == "detail_view"
    assert log.source == "shrine_detail"
    assert log.metadata == {"screen": "detail"}


@pytest.mark.django_db
def test_create_shrine_interaction_requires_authentication(api_client, shrine):
    response = api_client.post(
        "/api/shrine-interactions/",
        {
            "shrine_id": shrine.id,
            "action_type": "detail_view",
        },
        format="json",
    )

    assert response.status_code in (401, 403)
