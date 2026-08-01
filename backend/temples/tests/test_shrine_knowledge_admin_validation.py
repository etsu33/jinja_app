from __future__ import annotations

import re

import pytest
from django.urls import reverse

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource

pytestmark = pytest.mark.django_db


def _login_superuser(client, django_user_model, username="qa_admin"):
    user = django_user_model.objects.create_superuser(
        username=username, password="pass12345", email=f"{username}@example.com"
    )
    client.force_login(user)
    return user


def _split_datetime_now(client, url):
    """Admin Add画面が初期表示するcreated_atのSplitDateTimeField値を取得する。"""
    resp = client.get(url)
    html = resp.content.decode()
    date_ = re.search(r'name="created_at_0"[^>]*value="([^"]*)"', html).group(1)
    time_ = re.search(r'name="created_at_1"[^>]*value="([^"]*)"', html).group(1)
    return date_, time_


def _errorlist_texts(content: str) -> list[str]:
    return [
        re.sub(r"<[^>]+>", "", block).strip()
        for block in re.findall(r'<ul class="errorlist"[^>]*>(.*?)</ul>', content, re.S)
    ]


# --- ShrineKnowledgeSource: 独立Admin(Add/Change)経由の回帰テスト ---


def test_admin_add_source_confirmed_without_verified_at_is_rejected(client, django_user_model):
    _login_superuser(client, django_user_model)
    url = reverse("admin:temples_shrineknowledgesource_add")
    created_at_0, created_at_1 = _split_datetime_now(client, url)

    resp = client.post(
        url,
        {
            "source_type": "shrine_official",
            "title": "Admin経由出典",
            "publisher": "",
            "url": "",
            "bibliography": "",
            "accessed_at": "",
            "verified_at": "",
            "verification_status": "source_confirmed",
            "confidence": "",
            "language": "",
            "note": "",
            "created_at_0": created_at_0,
            "created_at_1": created_at_1,
            "_save": "Save",
        },
    )

    assert resp.status_code == 200  # フォーム再描画(保存失敗)
    assert ShrineKnowledgeSource.objects.count() == 0
    errors = _errorlist_texts(resp.content.decode())
    assert any("verified_at" in "".join(errors) or "verification_status" in e for e in errors)
    # 入力値がフォームに保持されていること(Error後に入力値を保持)
    assert "Admin経由出典" in resp.content.decode()


def test_admin_change_draft_to_source_confirmed_without_verified_at_is_rejected(
    client, django_user_model
):
    _login_superuser(client, django_user_model, username="qa_admin_change")
    source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official", title="既存draft出典", verification_status="draft"
    )
    url = reverse("admin:temples_shrineknowledgesource_change", args=[source.id])
    created_at_0, created_at_1 = _split_datetime_now(client, url)

    resp = client.post(
        url,
        {
            "source_type": "shrine_official",
            "title": "既存draft出典",
            "publisher": "",
            "url": "",
            "bibliography": "",
            "accessed_at": "",
            "verified_at": "",
            "verification_status": "source_confirmed",
            "confidence": "",
            "language": "",
            "note": "",
            "created_at_0": created_at_0,
            "created_at_1": created_at_1,
            "_save": "Save",
        },
    )

    assert resp.status_code == 200
    source.refresh_from_db()
    assert source.verification_status == "draft"
    assert source.verified_at is None


def test_admin_add_source_draft_without_verified_at_is_allowed(client, django_user_model):
    _login_superuser(client, django_user_model, username="qa_admin_draft_ok")
    url = reverse("admin:temples_shrineknowledgesource_add")
    created_at_0, created_at_1 = _split_datetime_now(client, url)

    resp = client.post(
        url,
        {
            "source_type": "shrine_official",
            "title": "Admin経由draft出典",
            "publisher": "",
            "url": "",
            "bibliography": "",
            "accessed_at": "",
            "verified_at": "",
            "verification_status": "draft",
            "confidence": "",
            "language": "",
            "note": "",
            "created_at_0": created_at_0,
            "created_at_1": created_at_1,
            "_save": "Save",
        },
    )

    assert resp.status_code == 302  # 保存成功(Adminのredirect)
    assert ShrineKnowledgeSource.objects.filter(title="Admin経由draft出典").exists()


# --- ShrineDeity: 独立Admin(Add)経由の回帰テスト ---


def _shrine():
    return Shrine.objects.create(
        name_jp="Admin監査神社",
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )


def test_admin_add_deity_source_confirmed_without_verified_at_is_rejected(
    client, django_user_model
):
    _login_superuser(client, django_user_model, username="qa_admin_deity")
    shrine = _shrine()
    url = reverse("admin:temples_shrinedeity_add")
    created_at_0, created_at_1 = _split_datetime_now(client, url)

    resp = client.post(
        url,
        {
            "shrine": str(shrine.id),
            "display_name": "テスト祭神",
            "canonical_name": "",
            "role": "primary",
            "sort_order": "0",
            "verification_status": "source_confirmed",
            "confidence": "",
            "verified_at": "",
            "note": "",
            "sources": [],
            "created_at_0": created_at_0,
            "created_at_1": created_at_1,
            "_save": "Save",
        },
    )

    assert resp.status_code == 200
    assert ShrineDeity.objects.filter(shrine=shrine).count() == 0
    errors = "".join(_errorlist_texts(resp.content.decode()))
    assert "verified_at" in errors or "verification_status" in errors


# --- ShrineHistory: 独立Admin(Add)経由の回帰テスト ---


def test_admin_add_history_reviewed_without_verified_at_is_rejected(client, django_user_model):
    _login_superuser(client, django_user_model, username="qa_admin_history")
    shrine = _shrine()
    url = reverse("admin:temples_shrinehistory_add")
    created_at_0, created_at_1 = _split_datetime_now(client, url)

    resp = client.post(
        url,
        {
            "shrine": str(shrine.id),
            "history_type": "official_origin",
            "title": "テスト由緒",
            "content": "内容",
            "period_text": "",
            "event_date": "",
            "sort_order": "0",
            "verification_status": "reviewed",
            "confidence": "",
            "verified_at": "",
            "note": "",
            "sources": [],
            "created_at_0": created_at_0,
            "created_at_1": created_at_1,
            "_save": "Save",
        },
    )

    assert resp.status_code == 200
    assert ShrineHistory.objects.filter(shrine=shrine).count() == 0
    errors = "".join(_errorlist_texts(resp.content.decode()))
    assert "verified_at" in errors or "verification_status" in errors
