from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from temples.models import Shrine, ShrineReflection


pytestmark = pytest.mark.django_db


def _create_user(username: str = "reflection_user"):
    User = get_user_model()
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )


def _create_shrine(name: str = "振り返りテスト神社") -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都振り返り区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
        history_theme="静寂",
    )


def test_create_shrine_reflection_requires_auth():
    shrine = _create_shrine(name="未ログイン振り返り神社")
    client = APIClient()

    payload = {
        "history_theme": "静寂",
        "prompt": "参拝して、今どんな変化がありましたか？",
        "answer": "少し落ち着いた気がします。",
        "mood_before": "tired",
        "mood_after": "calm",
    }

    resp = client.post(f"/api/shrines/{shrine.id}/reflection/", payload, format="json")

    assert resp.status_code in (401, 403)
    assert ShrineReflection.objects.count() == 0


def test_create_shrine_reflection_authenticated():
    user = _create_user()
    shrine = _create_shrine()

    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "history_theme": "静寂",
        "prompt": "参拝して、今どんな変化がありましたか？",
        "answer": "境内を歩いたことで、考えが少し整理されました。",
        "mood_before": "anxious",
        "mood_after": "calm",
    }

    resp = client.post(f"/api/shrines/{shrine.id}/reflection/", payload, format="json")

    assert resp.status_code == 201
    body = resp.json()

    assert body["shrine"] == shrine.id
    assert body["shrine_name"] == shrine.name_jp
    assert body["history_theme"] == "静寂"
    assert body["prompt"] == "参拝して、今どんな変化がありましたか？"
    assert body["answer"] == "境内を歩いたことで、考えが少し整理されました。"
    assert body["mood_before"] == "anxious"
    assert body["mood_after"] == "calm"

    reflection = ShrineReflection.objects.get(id=body["id"])
    assert reflection.user_id == user.id
    assert reflection.shrine_id == shrine.id


def test_create_shrine_reflection_returns_404_for_unknown_shrine():
    user = _create_user(username="reflection_missing_shrine_user")

    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "history_theme": "再出発",
        "prompt": "参拝後に何を持ち帰りましたか？",
        "answer": "次にやることを一つ決めました。",
    }

    resp = client.post("/api/shrines/999999/reflection/", payload, format="json")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Shrine not found"
    assert ShrineReflection.objects.count() == 0
