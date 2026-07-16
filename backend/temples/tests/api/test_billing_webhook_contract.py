import hashlib
import hmac
import json
import time

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from users.models import UserProfile

WEBHOOK_URL = "/api/billings/webhook/"


def _enable_stripe_billing(settings, monkeypatch):
    monkeypatch.setenv("BILLING_PROVIDER", "stripe")
    settings.BILLING_PROVIDER = "stripe"


def _payload(event_type: str, obj: dict) -> bytes:
    return json.dumps(
        {
            "id": f"evt_{event_type.replace('.', '_')}",
            "object": "event",
            "type": event_type,
            "data": {"object": obj},
        },
        separators=(",", ":"),
    ).encode()


def _signature(payload: bytes, secret: str) -> str:
    ts = str(int(time.time()))
    digest = hmac.new(secret.encode(), ts.encode() + b"." + payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={digest}"


def _post_signed(client: APIClient, payload: bytes, secret: str):
    return client.post(
        WEBHOOK_URL,
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=_signature(payload, secret),
    )


@pytest.mark.django_db
def test_billing_webhook_fails_safely_when_secret_missing(settings):
    settings.STRIPE_WEBHOOK_SECRET = ""

    res = APIClient().post(
        WEBHOOK_URL,
        data=_payload("checkout.session.completed", {"customer": "cus_missing"}),
        content_type="application/json",
    )

    assert res.status_code == 503


@pytest.mark.django_db
def test_billing_webhook_rejects_invalid_signature(settings):
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
    payload = _payload("checkout.session.completed", {"customer": "cus_bad"})

    res = APIClient().post(
        WEBHOOK_URL,
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=1,v1=bad",
    )

    assert res.status_code == 400


@pytest.mark.django_db
def test_checkout_completed_updates_profile_and_billing_status(settings, monkeypatch):
    _enable_stripe_billing(settings, monkeypatch)
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
    user = get_user_model().objects.create_user(username="billing-webhook-user")
    client = APIClient()
    payload = _payload(
        "checkout.session.completed",
        {
            "id": "cs_test_123",
            "customer": "cus_123",
            "subscription": "sub_123",
            "metadata": {"user_id": str(user.pk)},
        },
    )

    res = _post_signed(client, payload, settings.STRIPE_WEBHOOK_SECRET)

    assert res.status_code == 200
    profile = UserProfile.objects.get(user=user)
    assert profile.stripe_customer_id == "cus_123"
    assert profile.stripe_subscription_id == "sub_123"
    assert profile.subscription_status == "active"

    client.force_authenticate(user=user)
    status_res = client.get("/api/billings/status/")
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["provider"] == "stripe"
    assert data["plan"] == "premium"
    assert data["is_active"] is True


@pytest.mark.django_db
def test_subscription_updated_and_deleted_drive_billing_state(settings, monkeypatch):
    _enable_stripe_billing(settings, monkeypatch)
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
    period_end = int(time.time()) + 3600
    user = get_user_model().objects.create_user(username="billing-subscription-user")
    UserProfile.objects.update_or_create(user=user, defaults={"stripe_customer_id": "cus_sub"})
    client = APIClient()

    updated = _payload(
        "customer.subscription.updated",
        {
            "id": "sub_456",
            "customer": "cus_sub",
            "status": "active",
            "current_period_end": period_end,
            "items": {"data": [{"price": {"id": "price_premium"}}]},
        },
    )
    updated_res = _post_signed(client, updated, settings.STRIPE_WEBHOOK_SECRET)

    assert updated_res.status_code == 200
    profile = UserProfile.objects.get(user=user)
    assert profile.stripe_subscription_id == "sub_456"
    assert profile.stripe_price_id == "price_premium"
    assert profile.subscription_status == "active"
    assert int(profile.current_period_end.timestamp()) == period_end

    deleted = _payload(
        "customer.subscription.deleted",
        {
            "id": "sub_456",
            "customer": "cus_sub",
            "status": "canceled",
            "current_period_end": period_end,
        },
    )
    deleted_res = _post_signed(client, deleted, settings.STRIPE_WEBHOOK_SECRET)

    assert deleted_res.status_code == 200
    profile.refresh_from_db()
    assert profile.subscription_status == "canceled"
    assert profile.current_period_end is None

    client.force_authenticate(user=user)
    status_res = client.get("/api/billings/status/")
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["plan"] == "free"
    assert data["is_active"] is False
