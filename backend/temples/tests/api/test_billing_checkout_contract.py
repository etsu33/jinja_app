import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_billing_checkout_requires_auth(client: APIClient):
    res = client.post(
        "/api/billings/checkout/",
        {
            "success_url": "http://localhost:3000/billing/success",
            "cancel_url": "http://localhost:3000/billing/cancel",
        },
        format="json",
    )

    assert res.status_code == 401


@pytest.mark.django_db
def test_billing_checkout_stub_returns_safe_session(monkeypatch):
    monkeypatch.setenv("BILLING_PROVIDER", "stub")
    user = get_user_model().objects.create_user(username="billing-user", password="pass1234")
    client = APIClient()
    client.force_authenticate(user=user)

    res = client.post(
        "/api/billings/checkout/",
        {
            "success_url": "http://localhost:3000/billing/success",
            "cancel_url": "http://localhost:3000/billing/cancel",
        },
        format="json",
    )

    assert res.status_code == 200
    data = res.json()
    assert set(data.keys()) == {"session_id", "checkout_url"}
    assert data["session_id"].startswith("stub_checkout_")
    assert data["checkout_url"].startswith("http://localhost:3000/billing/success")
    assert "checkout_session_id=" in data["checkout_url"]
