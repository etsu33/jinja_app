from datetime import timedelta

import pytest
from django.utils import timezone

from temples.models import ConciergeMessage, ConciergeThread, Goshuin, Shrine, ShrineReflection, Visit
from temples.services.journey_timeline import build_journey_timeline


pytestmark = pytest.mark.django_db


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="journey-user",
        email="journey@example.com",
        password="password-test",
    )


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user(
        username="other-journey-user",
        email="other-journey@example.com",
        password="password-test",
    )


@pytest.fixture
def shrine():
    return Shrine.objects.create(name_jp="旅路テスト神社", address="東京都千代田区")


def test_build_journey_timeline_returns_phase1_events_ordered_desc(user, shrine):
    base = timezone.now()
    thread = ConciergeThread.objects.create(
        user=user,
        title="仕事の相談",
        recommendations_v2=[
            {
                "id": shrine.id,
                "name": shrine.name_jp,
                "history_theme": "静寂",
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
        content="おすすめです",
        created_at=base + timedelta(minutes=1),
    )
    visit = Visit.objects.create(
        user=user,
        shrine=shrine,
        visited_at=base + timedelta(days=1),
        note="朝に参拝",
        status="added",
    )
    reflection = ShrineReflection.objects.create(
        user=user,
        shrine=shrine,
        history_theme="静寂",
        prompt="どうでしたか？",
        answer="気持ちが整いました。",
    )
    ShrineReflection.objects.filter(pk=reflection.pk).update(created_at=base + timedelta(days=2))
    reflection.refresh_from_db()

    events = build_journey_timeline(user)

    assert [event["event_type"] for event in events] == [
        "reflection_created",
        "visit_completed",
        "recommendation_shown",
        "consultation_created",
    ]
    assert events[0]["id"] == f"reflection:{reflection.id}"
    assert events[0]["thread_id"] is None
    assert events[0]["shrine_id"] == shrine.id
    assert events[1]["id"] == f"visit:{visit.id}"
    assert events[1]["thread_id"] is None
    assert events[1]["metadata"] == {"note": "朝に参拝"}
    assert events[2]["id"] == f"thread:{thread.id}:recommendation:{shrine.id}"
    assert events[2]["thread_id"] == thread.id
    assert events[2]["shrine_name"] == shrine.name_jp
    assert events[2]["metadata"] == {"rank": 1, "history_theme": "静寂"}
    assert events[3]["id"] == f"thread:{thread.id}:consultation"
    assert events[3]["description"] == "仕事について相談しました"


def test_build_journey_timeline_filters_by_user_and_excludes_removed_visits_and_goshuin(
    user,
    other_user,
    shrine,
):
    base = timezone.now()
    own_visit = Visit.objects.create(
        user=user,
        shrine=shrine,
        visited_at=base,
        status="added",
    )
    Visit.objects.create(
        user=user,
        shrine=shrine,
        visited_at=base + timedelta(hours=1),
        status="removed",
    )
    Visit.objects.create(
        user=other_user,
        shrine=shrine,
        visited_at=base + timedelta(hours=2),
        status="added",
    )
    Goshuin.objects.create(user=user, shrine=shrine, title="対象外の御朱印")

    events = build_journey_timeline(user)

    assert [event["id"] for event in events] == [f"visit:{own_visit.id}"]
    assert events[0]["event_type"] == "visit_completed"


def test_recommendations_field_is_used_when_recommendations_v2_is_empty(user, shrine):
    thread = ConciergeThread.objects.create(
        user=user,
        recommendations=[{"shrine_id": shrine.id, "history_theme": "再出発"}],
    )
    ConciergeMessage.objects.create(
        thread=thread,
        role=ConciergeMessage.ROLE_ASSISTANT,
        content="おすすめです",
    )

    events = build_journey_timeline(user)

    assert len(events) == 1
    assert events[0]["event_type"] == "recommendation_shown"
    assert events[0]["shrine_id"] == shrine.id
    assert events[0]["shrine_name"] == shrine.name_jp
