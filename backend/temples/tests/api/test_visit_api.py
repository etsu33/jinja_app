from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from temples.models import ConciergeThread, Shrine, Visit


pytestmark = pytest.mark.django_db


def _create_user(username: str = "visit_user"):
    User = get_user_model()
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )


def _create_shrine(name: str = "参拝テスト神社") -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都参拝区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
        history_theme="勝負",
    )


def test_create_visit_requires_auth():
    shrine = _create_shrine(name="未ログイン参拝神社")
    client = APIClient()

    resp = client.post(f"/api/shrines/{shrine.id}/visit/", {}, format="json")

    assert resp.status_code in (401, 403)
    assert Visit.objects.count() == 0


def test_create_visit_without_thread_id():
    user = _create_user()
    shrine = _create_shrine()

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post(f"/api/shrines/{shrine.id}/visit/", {}, format="json")

    assert resp.status_code == 201
    visit = Visit.objects.get(id=resp.json()["id"])
    assert visit.user_id == user.id
    assert visit.shrine_id == shrine.id
    assert visit.thread_id is None


def test_create_visit_with_own_thread_id_saves_thread():
    user = _create_user(username="visit_thread_owner")
    shrine = _create_shrine(name="スレッド紐付け参拝神社")
    thread = ConciergeThread.objects.create(user=user, title="相談スレッド")

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post(
        f"/api/shrines/{shrine.id}/visit/",
        {"thread_id": thread.id},
        format="json",
    )

    assert resp.status_code == 201
    visit = Visit.objects.get(id=resp.json()["id"])
    assert visit.thread_id == thread.id


def test_create_visit_with_other_users_thread_id_returns_400():
    user = _create_user(username="visit_thread_requester")
    other_user = _create_user(username="visit_thread_stranger")
    shrine = _create_shrine(name="他人スレッド参拝神社")
    other_thread = ConciergeThread.objects.create(user=other_user, title="他人の相談スレッド")

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post(
        f"/api/shrines/{shrine.id}/visit/",
        {"thread_id": other_thread.id},
        format="json",
    )

    assert resp.status_code == 400
    assert Visit.objects.count() == 0


def test_create_visit_returns_404_for_unknown_shrine():
    user = _create_user(username="visit_missing_shrine_user")

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post("/api/shrines/999999/visit/", {}, format="json")

    assert resp.status_code == 404
    assert Visit.objects.count() == 0


def test_list_visits_requires_auth():
    client = APIClient()

    resp = client.get("/api/visits/")

    assert resp.status_code in (401, 403)


def test_list_visits_returns_only_own_visits():
    user = _create_user(username="visit_list_owner")
    other_user = _create_user(username="visit_list_other")
    shrine = _create_shrine(name="一覧テスト参拝神社")

    own_visit = Visit.objects.create(user=user, shrine=shrine)
    Visit.objects.create(user=other_user, shrine=shrine)

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get("/api/visits/")

    assert resp.status_code == 200
    body = resp.json()
    results = body["results"] if isinstance(body, dict) and "results" in body else body

    assert [item["id"] for item in results] == [own_visit.id]
    assert results[0]["thread_id"] is None
