from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from temples.models import Shrine, ShrineSubmission


pytestmark = pytest.mark.django_db


def _create_user(username: str = "submission_user"):
    User = get_user_model()
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="testpass123",
    )


def test_create_shrine_submission_authenticated():
    user = _create_user()

    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "name": "投稿テスト神社",
        "address": "東京都投稿区1-2-3",
        "lat": 35.6812,
        "lng": 139.7671,
        "goriyaku_tags": ["開運", "厄除け"],
        "note": "投稿APIの動作確認",
    }

    resp = client.post("/api/shrine-submissions/", payload, format="json")

    assert resp.status_code == 201
    body = resp.json()

    assert body["name"] == "投稿テスト神社"
    assert body["address"] == "東京都投稿区1-2-3"
    assert body["status"] == "pending"
    assert body["goriyaku_tags"] == ["開運", "厄除け"]
    assert body["note"] == "投稿APIの動作確認"

    sub = ShrineSubmission.objects.get(id=body["id"])
    assert sub.user_id == user.id
    assert sub.status == ShrineSubmission.Status.PENDING

    # 投稿時点では shrine 本体は作られない
    assert not Shrine.objects.filter(name_jp="投稿テスト神社", address="東京都投稿区1-2-3").exists()


def test_create_shrine_submission_requires_auth():
    client = APIClient()

    payload = {
        "name": "未ログイン投稿神社",
        "address": "東京都未ログイン区1-1-1",
        "lat": 35.6812,
        "lng": 139.7671,
        "goriyaku_tags": ["開運"],
        "note": "未ログイン投稿",
    }

    resp = client.post("/api/shrine-submissions/", payload, format="json")

    assert resp.status_code in (401, 403)
    assert ShrineSubmission.objects.filter(name="未ログイン投稿神社").count() == 0


def test_create_shrine_submission_rejects_duplicate_existing_shrine():
    user = _create_user(username="dup_user")

    Shrine.objects.create(
        name_jp="既存重複神社",
        address="東京都重複区9-9-9",
        latitude=35.7000,
        longitude=139.7000,
        owner=user,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "name": "既存重複神社",
        "address": "東京都重複区9-9-9",
        "lat": 35.7000,
        "lng": 139.7000,
        "goriyaku_tags": ["厄除け"],
        "note": "duplicate test",
    }

    resp = client.post("/api/shrine-submissions/", payload, format="json")

    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "duplicate_candidate"
    assert body["message"] == "この神社はすでに登録されている可能性があります。"
    assert len(body["candidates"]) >= 1
    assert body["candidates"][0]["id"] == Shrine.objects.get(name_jp="既存重複神社", address="東京都重複区9-9-9").id
    assert body["candidates"][0]["name"] == "既存重複神社"
    assert body["candidates"][0]["address"] == "東京都重複区9-9-9"
    assert ShrineSubmission.objects.filter(name="既存重複神社", address="東京都重複区9-9-9").count() == 0


def test_create_shrine_submission_allows_duplicate_pending_submission():
    user = _create_user(username="pending_dup_user")

    ShrineSubmission.objects.create(
        user=user,
        name="審査中重複神社",
        address="東京都審査中区8-8-8",
        lat=35.6800,
        lng=139.7600,
        goriyaku_tags=["開運"],
        note="existing pending",
        status=ShrineSubmission.Status.PENDING,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "name": "審査中重複神社",
        "address": "東京都審査中区8-8-8",
        "lat": 35.6800,
        "lng": 139.7600,
        "goriyaku_tags": ["開運"],
        "note": "new pending dup",
    }

    resp = client.post("/api/shrine-submissions/", payload, format="json")

    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "審査中重複神社"
    assert body["address"] == "東京都審査中区8-8-8"
    assert body["status"] == "pending"
    assert ShrineSubmission.objects.filter(name="審査中重複神社", address="東京都審査中区8-8-8").count() == 2


def test_create_shrine_submission_rejects_multiple_duplicate_candidates():
    user = _create_user(username="multi_dup_user")

    # 同じ名前で異なる住所の Shrine を2件作成
    shrine1 = Shrine.objects.create(
        name_jp="複数候補神社",
        address="東京都複数1区1-1-1",
        latitude=35.7000,
        longitude=139.7000,
        owner=user,
    )
    shrine2 = Shrine.objects.create(
        name_jp="複数候補神社",
        address="東京都複数2区2-2-2",
        latitude=35.7100,
        longitude=139.7100,
        owner=user,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "name": "複数候補神社",
        "address": "東京都新規区3-3-3",  # 異なる住所で投稿
        "lat": 35.7200,
        "lng": 139.7200,
        "goriyaku_tags": ["開運"],
        "note": "multiple duplicate test",
    }

    resp = client.post("/api/shrine-submissions/", payload, format="json")

    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "duplicate_candidate"
    assert body["message"] == "この神社はすでに登録されている可能性があります。"
    assert len(body["candidates"]) >= 2  # 少なくとも2件の候補
    # candidates に shrine1 と shrine2 が含まれていることを確認
    candidate_ids = {c["id"] for c in body["candidates"]}
    assert shrine1.id in candidate_ids
    assert shrine2.id in candidate_ids
    for candidate in body["candidates"]:
        assert "id" in candidate
        assert "name" in candidate
        assert "address" in candidate
        assert candidate["name"] == "複数候補神社"
    # ShrineSubmission は作成されていない
    assert ShrineSubmission.objects.filter(name="複数候補神社").count() == 0


def test_create_shrine_submission_allows_ambiguous_match_as_pending():
    user = _create_user(username="ambiguous_user")

    Shrine.objects.create(
        name_jp="神田神社（神田明神）",
        address="東京都千代田区外神田2-16-2",
        latitude=35.7023,
        longitude=139.7745,
        owner=user,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    payload = {
        "name": "神田",
        "address": "東京都渋谷区1-2-3",
        "lat": 35.6595,
        "lng": 139.7005,
        "goriyaku_tags": ["開運"],
        "note": "ambiguous match should be allowed",
    }

    resp = client.post("/api/shrine-submissions/", payload, format="json")

    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "神田"
    assert body["address"] == "東京都渋谷区1-2-3"
    assert body["status"] == "pending"

    assert ShrineSubmission.objects.filter(name="神田", address="東京都渋谷区1-2-3").count() == 1
