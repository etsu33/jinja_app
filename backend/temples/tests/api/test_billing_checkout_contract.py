"""チェックアウトの窓口の契約（買い切りの旅行パス）。"""

import logging
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


class _FakeStripeError(Exception):
    """stripe.StripeError の代わり（code / http_status / request_id を持つ）。"""

    def __init__(self, message, *, code=None, http_status=None, request_id=None, param=None):
        super().__init__(message)
        self.code = code
        self.param = param
        self.http_status = http_status
        self.request_id = request_id


class _FakeInvalidRequestError(_FakeStripeError):
    pass


class _FakeSession:
    calls: list = []
    error: Exception | None = None
    errors: list = []  # 1回ごとに先頭から投げる（空なら error を使う）

    @classmethod
    def create(cls, **params):
        cls.calls.append(params)
        if cls.errors:
            raise cls.errors.pop(0)
        if cls.error is not None:
            raise cls.error
        return {"id": "cs_fake", "url": "https://checkout.stripe.com/c/pay/cs_fake"}


@pytest.fixture
def fake_stripe(settings, monkeypatch):
    monkeypatch.setenv("BILLING_PROVIDER", "stripe")
    settings.STRIPE_SECRET_KEY = "sk_test_x"
    settings.STRIPE_PASS_PRICE_ID_1D = "price_1d"
    settings.STRIPE_PASS_PRICE_ID_7D = "price_7d"
    settings.STRIPE_PASS_PRICE_ID_14D = "price_14d"
    _FakeSession.calls = []
    _FakeSession.error = None
    _FakeSession.errors = []
    module = types.ModuleType("stripe")
    module.checkout = types.SimpleNamespace(Session=_FakeSession)
    module.StripeError = _FakeStripeError
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
    # Stripe の目印は、エンコードせずに文字どおり入っていること（Stripe が置き換える）。
    assert params["success_url"] == "http://localhost:3000/billing/success?checkout_session_id={CHECKOUT_SESSION_ID}"


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


@pytest.mark.django_db
def test_success_url_keeps_other_query_params_and_the_literal_placeholder(fake_stripe):
    _, client = _client()
    urls = {**URLS, "success_url": "http://localhost:3000/billing/success?from=shrine%2F1&a=b%20c"}

    client.post(CHECKOUT_URL, {"pass_type": "7d", **urls}, format="json")

    success_url = fake_stripe.calls[-1]["success_url"]
    assert success_url == (
        "http://localhost:3000/billing/success?from=shrine%2F1&a=b+c&checkout_session_id={CHECKOUT_SESSION_ID}"
    )
    assert "%7B" not in success_url and "%7D" not in success_url


@pytest.mark.django_db
def test_stripe_create_error_returns_checkout_unavailable_and_logs_safely(fake_stripe, caplog):
    fake_stripe.error = _FakeInvalidRequestError(
        "No such price: 'prod_SECRET_LIKE_VALUE'",
        code="resource_missing",
        http_status=400,
        request_id="req_test_123",
    )
    _, client = _client()

    with caplog.at_level(logging.ERROR):
        res = client.post(CHECKOUT_URL, {"pass_type": "7d", **URLS}, format="json")

    assert res.status_code == 503
    body = res.json()
    assert body == {"detail": "checkout is unavailable"}
    assert "prod_" not in res.content.decode()
    assert "price_7d" not in res.content.decode()

    messages = "\n".join(record.getMessage() for record in caplog.records)
    assert "checkout session create failed" in messages
    assert "error_type=_FakeInvalidRequestError" in messages
    assert "code=resource_missing" in messages
    assert "request_id=req_test_123" in messages
    # Stripe のエラーの本文（値段の ID などを含みうる）はログにも出さない。
    assert "prod_SECRET_LIKE_VALUE" not in messages


@pytest.mark.django_db
def test_stripe_checkout_recreates_a_customer_missing_in_the_current_mode(fake_stripe, caplog):
    """サンドボックスで保存した客 ID は、本番のキーでは見つからない。作り直して決済を続ける。"""
    user, client = _client()
    UserProfile.objects.update_or_create(user=user, defaults={"stripe_customer_id": "cus_from_sandbox"})
    fake_stripe.errors = [
        _FakeInvalidRequestError("No such customer: 'cus_from_sandbox'", code="resource_missing", param="customer")
    ]

    with caplog.at_level(logging.WARNING):
        res = client.post(CHECKOUT_URL, {"pass_type": "1d", **URLS}, format="json")

    assert res.status_code == 200
    first, second = fake_stripe.calls
    assert first["customer"] == "cus_from_sandbox"
    assert "customer" not in second
    assert second["customer_creation"] == "always"
    assert second["customer_email"] == user.email
    # 古い ID を消し、Webhook が新しい客 ID を保存できるようにする。
    assert UserProfile.objects.get(user=user).stripe_customer_id == ""
    messages = "\n".join(record.getMessage() for record in caplog.records)
    assert "stored customer is missing" in messages
    assert "cus_from_sandbox" not in messages


@pytest.mark.django_db
@pytest.mark.parametrize(
    "error",
    [
        _FakeInvalidRequestError("No such price", code="resource_missing", param="line_items[0][price]"),
        _FakeInvalidRequestError("bad customer", code="parameter_invalid_string", param="customer"),
        _FakeStripeError("network", code=None),
    ],
)
def test_stripe_checkout_keeps_the_customer_on_other_errors(fake_stripe, error):
    """客が居ないと Stripe が明示したとき以外は、作り直さず、保存済みの ID も消さない。"""
    user, client = _client()
    UserProfile.objects.update_or_create(user=user, defaults={"stripe_customer_id": "cus_existing"})
    fake_stripe.errors = [error]

    res = client.post(CHECKOUT_URL, {"pass_type": "1d", **URLS}, format="json")

    assert res.status_code == 503
    assert len(fake_stripe.calls) == 1
    assert UserProfile.objects.get(user=user).stripe_customer_id == "cus_existing"


@pytest.mark.django_db
def test_stripe_checkout_fails_when_the_recreated_customer_also_fails(fake_stripe):
    """作り直しても失敗したら、1回だけで止めて失敗を返す。"""
    user, client = _client()
    UserProfile.objects.update_or_create(user=user, defaults={"stripe_customer_id": "cus_from_sandbox"})
    fake_stripe.errors = [
        _FakeInvalidRequestError("No such customer", code="resource_missing", param="customer"),
        _FakeInvalidRequestError("No such price", code="resource_missing", param="line_items[0][price]"),
    ]

    res = client.post(CHECKOUT_URL, {"pass_type": "1d", **URLS}, format="json")

    assert res.status_code == 503
    assert len(fake_stripe.calls) == 2
