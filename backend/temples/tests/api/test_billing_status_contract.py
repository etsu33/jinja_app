import re

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from temples.services.billing_state import is_premium_for_user
from users.models import UserProfile


ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")

@pytest.mark.django_db
def test_billing_status_contract_default(client: APIClient):
    res = client.get("/api/billings/status/")
    assert res.status_code == 200
    data = res.json()

    # 1) キー集合（これが“契約”）
    assert set(data.keys()) == {
        "plan",
        "is_active",
        "provider",
        "current_period_end",
        "trial_ends_at",
        "cancel_at_period_end",
    }

    # 2) 型と値域（最低限）
    assert data["plan"] in {"free", "premium"}
    assert isinstance(data["is_active"], bool)
    assert data["provider"] in {"stub", "stripe", "revenuecat", "unknown"}
    assert isinstance(data["cancel_at_period_end"], bool)

    # 3) 日付フィールド（null か ISO8601(Z)）
    if data["current_period_end"] is not None:
        assert isinstance(data["current_period_end"], str)
        assert ISO_Z_RE.match(data["current_period_end"])
    if data["trial_ends_at"] is not None:
        assert isinstance(data["trial_ends_at"], str)
        assert ISO_Z_RE.match(data["trial_ends_at"])


@pytest.mark.django_db
def test_billing_status_contract_premium_active(monkeypatch, client: APIClient):
    monkeypatch.setenv("BILLING_STUB_PLAN", "premium")
    monkeypatch.setenv("BILLING_STUB_ACTIVE", "1")
    monkeypatch.setenv("BILLING_PROVIDER", "stripe")

    res = client.get("/api/billings/status/")
    assert res.status_code == 200
    data = res.json()

    assert data["plan"] == "premium"
    assert data["is_active"] is True
    assert data["provider"] == "stripe"
    # active のときは current_period_end が入る想定（入らないならここで落ちる）
    assert data["current_period_end"] is not None



@pytest.mark.django_db
def test_billing_status_stub_provider_ignores_authenticated_user_db_state(monkeypatch, django_user_model):
    monkeypatch.setenv("BILLING_PROVIDER", "stub")
    monkeypatch.setenv("BILLING_STUB_PLAN", "free")
    monkeypatch.setenv("BILLING_STUB_ACTIVE", "0")

    user = django_user_model.objects.create_user(username="stub-user", password="password")
    UserProfile.objects.update_or_create(
        user=user,
        defaults={
            "subscription_status": "active",
            "current_period_end": timezone.now() + timezone.timedelta(days=30),
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)
    res = client.get("/api/billings/status/")

    assert res.status_code == 200
    data = res.json()
    assert data["plan"] == "free"
    assert data["is_active"] is False
    assert data["provider"] == "stub"
    assert data["current_period_end"] is None


@pytest.mark.django_db
def test_billing_status_stub_premium_without_active_env_defaults_to_active(monkeypatch, client: APIClient):
    monkeypatch.setenv("BILLING_PROVIDER", "stub")
    monkeypatch.setenv("BILLING_STUB_PLAN", "premium")
    monkeypatch.delenv("BILLING_STUB_ACTIVE", raising=False)

    res = client.get("/api/billings/status/")

    assert res.status_code == 200
    data = res.json()
    assert data["plan"] == "premium"
    assert data["is_active"] is True
    assert data["provider"] == "stripe"
    assert data["current_period_end"] is not None


@pytest.mark.django_db
def test_billing_status_stub_inactive_env_returns_free(monkeypatch, client: APIClient):
    monkeypatch.setenv("BILLING_PROVIDER", "stub")
    monkeypatch.setenv("BILLING_STUB_PLAN", "premium")
    monkeypatch.setenv("BILLING_STUB_ACTIVE", "0")

    res = client.get("/api/billings/status/")

    assert res.status_code == 200
    data = res.json()
    assert data["plan"] == "premium"
    assert data["is_active"] is False
    assert data["provider"] == "stripe"
    assert data["current_period_end"] is None


@pytest.mark.django_db
def test_is_premium_for_user_allows_staff_bypass(monkeypatch, django_user_model):
    monkeypatch.setenv("BILLING_PROVIDER", "stripe")
    monkeypatch.setenv("BILLING_STUB_PLAN", "free")
    monkeypatch.setenv("BILLING_STUB_ACTIVE", "0")

    user = django_user_model.objects.create_user(
        username="staff-bypass-user",
        password="password",
        is_staff=True,
    )

    assert is_premium_for_user(user) is True
