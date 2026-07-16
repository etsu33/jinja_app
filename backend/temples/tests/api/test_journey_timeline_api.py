from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from temples.models import ConciergeMessage, ConciergeThread, Shrine, Visit


pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="journey-api-user",
        email="journey-api@example.com",
        password="password-test",
    )


@pytest.fixture
def shrine():
    return Shrine.objects.create(name_jp="API旅路神社", address="東京都千代田区")


def test_journey_timeline_requires_authentication(api_client):
    response = api_client.get("/api/journeys/timeline/")

    assert response.status_code in (401, 403)


def test_journey_timeline_returns_results_wrapper_and_events(api_client, user, shrine):
    api_client.force_authenticate(user=user)
    base = timezone.now()
    thread = ConciergeThread.objects.create(
        user=user,
        recommendations_v2=[
            {
                "id": shrine.id,
                "name": shrine.name_jp,
                "history_theme": "静寂",
                "reason": "静けさを求める相談内容と一致しました。",
                "reason_facts": [{"type": "goriyaku_tag", "label": "厄除け"}],
                "action_suggestion_v4_preview": {
                    "primary_action": {"label": "詳細を見る", "description": "判断材料を増やします。"},
                    "secondary_action": {"label": "保存する", "description": "あとで見返せます。"},
                    "reflection_prompt": {"question": "何を整理したいですか？"},
                    "action_source": {"source": "fallback", "reason": "安全な初期提案にした"},
                },
            }
        ],
    )
    ConciergeMessage.objects.create(
        thread=thread,
        role=ConciergeMessage.ROLE_USER,
        content="仕事について相談しました",
        created_at=base,
    )
    ConciergeMessage.objects.create(
        thread=thread,
        role=ConciergeMessage.ROLE_ASSISTANT,
        content="提案しました",
        created_at=base + timedelta(minutes=1),
    )
    visit = Visit.objects.create(
        user=user,
        shrine=shrine,
        visited_at=base + timedelta(days=1),
        status="added",
    )
    Visit.objects.create(
        user=user,
        shrine=shrine,
        visited_at=base + timedelta(days=2),
        status="removed",
    )

    response = api_client.get("/api/journeys/timeline/")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"results"}

    results = body["results"]
    assert [item["event_type"] for item in results] == [
        "visit_completed",
        "recommendation_shown",
        "consultation_created",
    ]
    assert results[0] == {
        "id": f"visit:{visit.id}",
        "event_type": "visit_completed",
        "occurred_at": results[0]["occurred_at"],
        "title": "参拝しました",
        "description": f"{shrine.name_jp}に参拝しました。",
        "thread_id": None,
        "shrine_id": shrine.id,
        "shrine_name": shrine.name_jp,
        "metadata": {"note": ""},
    }
    assert results[1]["id"] == f"thread:{thread.id}:recommendation:{shrine.id}"
    assert results[1]["thread_id"] == thread.id
    assert results[1]["metadata"] == {
        "rank": 1,
        "history_theme": "静寂",
        "reason": "静けさを求める相談内容と一致しました。",
        "reason_facts": [{"type": "goriyaku_tag", "label": "厄除け"}],
        "matched_benefits": ["厄除け"],
        "action_suggestion": {
            "primary_action": {"label": "詳細を見る", "description": "判断材料を増やします。"},
            "secondary_action": {"label": "保存する", "description": "あとで見返せます。"},
            "reflection_prompt": {"question": "何を整理したいですか？"},
            "action_source": {"source": "fallback", "reason": "安全な初期提案にした"},
        },
    }
    assert results[2]["id"] == f"thread:{thread.id}:consultation"
    assert results[2]["shrine_id"] is None
