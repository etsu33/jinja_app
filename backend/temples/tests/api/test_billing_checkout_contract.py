"""チェックアウトの窓口の契約（買い切りの旅行パス）。"""

import sys
import types

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from users.models import UserProfile

CHECKOUT_URL = "/api/billings/checkout/"
URLS = {
    "success_url": "http://localhost:3000/billing/success",
    "cancel_url": "http://localhost:3000/billing/cancel",
}


def _client(username="billing-user"):
    user = get_user_model().objects.create_user(username=username, password="pass1234", email=f"{username}@example.com")
    client = APIClient()
    client.force_authenticate(user=user)
    return user, client


@pytest.mark.django_db
def test_billing_checkout_requires_auth(client: APIClient):
    res = client.post(CHECKOUT_URL, {"pass_type": "7d", **URLS}, format="json")

    assert res.status_code == 401


@pytest.mark.django_db
def test_billing_checkout_stub_returns_safe_session(monkeypatch):
    monkeypatch.setenv("BILLING_PROVIDER", "stub")
    _, client = _client()

    res = client.post(CHECKOUT_URL, {"pass_type": "7d", **URLS}, format="json")

    assert res.status_code == 200
    data = res.json()
    assert set(data.keys()) == {"session_id", "checkout_url"}
    assert data["session_id"].startswith("stub_checkout_")
    assert data["checkout_url"].startswith("http://localhost:3000/billing/success")
    assert "checkout_session_id=" in data["checkout_url"]


@pytest.mark.django_db
@pytest.mark.parametrize("body", [{}, {"pass_type": "30d"}, {"pass_type": ""}])
def test_billing_checkout_requires_a_known_pass_type(monkeypatch, body):
    monkeypatch.setenv("BILLING_PROVIDER", "stub")
    _, client = _client()

    res = client.post(CHECKOUT_URL, {**body, **URLS}, format="json")

    assert res.status_code == 400


class _FakeSession:
    calls: list = []

    @classmethod
    def create(cls, **params):
        cls.calls.append(params)
        return {"id": "cs_fake", "url": "https://checkout.stripe.com/c/pay/cs_fake"}


@pytest.fixture
def fake_stripe(settings, monkeypatch):
    monkeypatch.setenv("BILLING_PROVIDER", "stripe")
    settings.STRIPE_SECRET_KEY = "sk_test_x"
    settings.STRIPE_PASS_PRICE_ID_1D = "price_1d"
    settings.STRIPE_PASS_PRICE_ID_7D = "price_7d"
    settings.STRIPE_PASS_PRICE_ID_14D = "price_14d"
    _FakeSession.calls = []
    module = types.ModuleType("stripe")
    module.checkout = types.SimpleNamespace(Session=_FakeSession)
    monkeypatch.setitem(sys.modules, "stripe", module)
    return _FakeSession


@pytest.mark.django_db
@pytest.mark.parametrize("pass_type,price", [("1d", "price_1d"), ("7d", "price_7d"), ("14d", "price_14d")])
def test_stripe_checkout_is_a_card_only_one_time_payment_for_the_chosen_pass(fake_stripe, pass_type, price):
    user, client = _client()

    res = client.post(CHECKOUT_URL, {"pass_type": pass_type, **URLS}, format="json")

    assert res.status_code == 200
    assert res.json() == {"session_id": "cs_fake", "checkout_url": "https://checkout.stripe.com/c/pay/cs_fake"}
    params = fake_stripe.calls[-1]
    assert params["mode"] == "payment"
    assert params["payment_method_types"] == ["card"]
    assert params["line_items"] == [{"price": price, "quantity": 1}]
    assert params["customer_creation"] == "always"
    assert params["customer_email"] == user.email
    assert "customer" not in params
    assert params["metadata"] == {"user_id": str(user.pk), "pass_type": pass_type}
    assert params["payment_intent_data"] == {"metadata": {"user_id": str(user.pk), "pass_type": pass_type}}
    assert params["success_url"].endswith("checkout_session_id=%7BCHECKOUT_SESSION_ID%7D")


@pytest.mark.django_db
def test_stripe_checkout_reuses_the_existing_customer(fake_stripe):
    user, client = _client()
    UserProfile.objects.update_or_create(user=user, defaults={"stripe_customer_id": "cus_existing"})

    client.post(CHECKOUT_URL, {"pass_type": "1d", **URLS}, format="json")

    params = fake_stripe.calls[-1]
    assert params["customer"] == "cus_existing"
    assert "customer_creation" not in params
    assert "customer_email" not in params


@pytest.mark.django_db
def test_stripe_checkout_without_the_price_setting_is_unavailable(fake_stripe, settings):
    settings.STRIPE_PASS_PRICE_ID_14D = ""
    _, client = _client()

    res = client.post(CHECKOUT_URL, {"pass_type": "14d", **URLS}, format="json")

    assert res.status_code == 503
    assert fake_stripe.calls == []


@pytest.mark.django_db
def test_portal_endpoint_is_removed():
    _, client = _client()

    res = client.post("/api/billings/portal/", {"return_url": "http://localhost:3000/billing"}, format="json")

    assert res.status_code == 404
