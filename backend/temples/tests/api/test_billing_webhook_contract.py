"""Stripe Webhook の契約（買い切りの旅行パス）。

- checkout.session.completed（mode=payment、payment_status=paid）で期限を延ばす。
- 同じ支払いの通知が2回届いても、期限は1回分しか延ばさない。
- charge.refunded（全額返金）でパスの日数を期限から引く。一部返金は期限を変えない。
- 月額の自動更新（mode=subscription、customer.subscription.*）は扱わない。
"""

import hashlib
import hmac
import json
import time
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from users.models import PremiumPassPurchase, UserProfile

WEBHOOK_URL = "/api/billings/webhook/"
STATUS_URL = "/api/billings/status/"
SECRET = "whsec_test"


@pytest.fixture
def stripe_billing(settings, monkeypatch):
    monkeypatch.setenv("BILLING_PROVIDER", "stripe")
    settings.BILLING_PROVIDER = "stripe"
    settings.STRIPE_WEBHOOK_SECRET = SECRET


def _payload(event_type: str, obj: dict) -> bytes:
    return json.dumps(
        {"id": f"evt_{event_type.replace('.', '_')}", "object": "event", "type": event_type, "data": {"object": obj}},
        separators=(",", ":"),
    ).encode()


def _signature(payload: bytes, secret: str) -> str:
    ts = str(int(time.time()))
    digest = hmac.new(secret.encode(), ts.encode() + b"." + payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={digest}"


def _post(event_type: str, obj: dict):
    payload = _payload(event_type, obj)
    return APIClient().post(
        WEBHOOK_URL,
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=_signature(payload, SECRET),
    )


def _session(user, *, session_id="cs_test_1", pass_type="7d", payment_status="paid", mode="payment", **extra):
    obj = {
        "id": session_id,
        "object": "checkout.session",
        "mode": mode,
        "payment_status": payment_status,
        "customer": "cus_pass",
        "payment_intent": f"pi_{session_id}",
        "amount_total": 799,
        "currency": "usd",
        "client_reference_id": str(user.pk),
        "metadata": {"user_id": str(user.pk), "pass_type": pass_type},
    }
    obj.update(extra)
    return obj


def _status_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    res = client.get(STATUS_URL)
    assert res.status_code == 200
    return res.json()


def _user(name="pass-user"):
    return get_user_model().objects.create_user(username=name)


# --- 署名 ----------------------------------------------------------------------


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
    settings.STRIPE_WEBHOOK_SECRET = SECRET
    payload = _payload("checkout.session.completed", {"customer": "cus_bad"})

    res = APIClient().post(
        WEBHOOK_URL, data=payload, content_type="application/json", HTTP_STRIPE_SIGNATURE="t=1,v1=bad"
    )

    assert res.status_code == 400


# --- 支払い完了 -------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("pass_type,days", [("1d", 1), ("7d", 7), ("14d", 14)])
def test_paid_checkout_extends_period_from_now_and_makes_premium(stripe_billing, pass_type, days):
    user = _user()
    before = timezone.now()

    res = _post("checkout.session.completed", _session(user, pass_type=pass_type))

    assert res.status_code == 200
    profile = UserProfile.objects.get(user=user)
    assert profile.stripe_customer_id == "cus_pass"
    assert profile.subscription_status == "active"
    assert profile.cancel_at_period_end is False
    expected = before + timedelta(days=days)
    assert abs((profile.current_period_end - expected).total_seconds()) < 60

    purchase = PremiumPassPurchase.objects.get(user=user)
    assert (purchase.source, purchase.external_id, purchase.payment_intent_id) == ("stripe", "cs_test_1", "pi_cs_test_1")
    assert (purchase.pass_type, purchase.days, purchase.amount, purchase.currency) == (pass_type, days, 799, "usd")

    data = _status_for(user)
    assert data["plan"] == "premium"
    assert data["is_active"] is True
    assert data["current_period_end"] is not None
    assert data["cancel_at_period_end"] is False


@pytest.mark.django_db
def test_same_checkout_delivered_twice_extends_only_once(stripe_billing):
    user = _user()

    _post("checkout.session.completed", _session(user, pass_type="7d"))
    first_end = UserProfile.objects.get(user=user).current_period_end
    res = _post("checkout.session.completed", _session(user, pass_type="7d"))

    assert res.status_code == 200
    assert UserProfile.objects.get(user=user).current_period_end == first_end
    assert PremiumPassPurchase.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_second_pass_extends_from_the_current_period_end(stripe_billing):
    user = _user()

    _post("checkout.session.completed", _session(user, session_id="cs_a", pass_type="7d"))
    first_end = UserProfile.objects.get(user=user).current_period_end
    _post("checkout.session.completed", _session(user, session_id="cs_b", pass_type="1d"))

    assert UserProfile.objects.get(user=user).current_period_end == first_end + timedelta(days=1)


@pytest.mark.django_db
def test_pass_after_expiry_starts_from_now(stripe_billing):
    user = _user()
    UserProfile.objects.update_or_create(
        user=user, defaults={"current_period_end": timezone.now() - timedelta(days=3), "subscription_status": "active"}
    )
    before = timezone.now()

    _post("checkout.session.completed", _session(user, pass_type="1d"))

    end = UserProfile.objects.get(user=user).current_period_end
    assert abs((end - (before + timedelta(days=1))).total_seconds()) < 60


@pytest.mark.django_db
@pytest.mark.parametrize(
    "overrides",
    [
        {"payment_status": "unpaid"},
        {"mode": "subscription"},
        {"metadata": {"user_id": "0", "pass_type": "7d"}, "client_reference_id": None},
        {"pass_type": "30d"},
    ],
)
def test_checkout_without_a_paid_known_pass_does_not_extend(stripe_billing, overrides):
    user = _user()
    pass_type = overrides.pop("pass_type", "7d")
    obj = _session(user, pass_type=pass_type, **overrides)

    res = _post("checkout.session.completed", obj)

    assert res.status_code == 200
    profile = UserProfile.objects.filter(user=user).first()
    assert profile is None or profile.current_period_end is None
    assert not PremiumPassPurchase.objects.filter(user=user).exists()
    assert _status_for(user)["plan"] == "free"


@pytest.mark.django_db
def test_existing_customer_id_is_not_overwritten(stripe_billing):
    user = _user()
    UserProfile.objects.update_or_create(user=user, defaults={"stripe_customer_id": "cus_original"})

    _post("checkout.session.completed", _session(user, customer="cus_other"))

    assert UserProfile.objects.get(user=user).stripe_customer_id == "cus_original"


# --- 返金 -----------------------------------------------------------------------


def _charge(payment_intent: str, *, amount=799, amount_refunded=799, refunded=True):
    return {
        "id": "ch_1",
        "object": "charge",
        "payment_intent": payment_intent,
        "amount": amount,
        "amount_refunded": amount_refunded,
        "refunded": refunded,
    }


@pytest.mark.django_db
def test_full_refund_removes_the_pass_days(stripe_billing):
    user = _user()
    _post("checkout.session.completed", _session(user, session_id="cs_a", pass_type="7d"))
    _post("checkout.session.completed", _session(user, session_id="cs_b", pass_type="1d"))
    end_before = UserProfile.objects.get(user=user).current_period_end

    res = _post("charge.refunded", _charge("pi_cs_a"))

    assert res.status_code == 200
    assert UserProfile.objects.get(user=user).current_period_end == end_before - timedelta(days=7)
    purchase = PremiumPassPurchase.objects.get(external_id="cs_a")
    assert purchase.status == "refunded"
    assert purchase.refunded_at is not None
    assert _status_for(user)["plan"] == "premium"


@pytest.mark.django_db
def test_full_refund_of_the_only_pass_ends_premium_now(stripe_billing):
    user = _user()
    _post("checkout.session.completed", _session(user, pass_type="1d"))

    _post("charge.refunded", _charge("pi_cs_test_1"))

    assert _status_for(user)["plan"] == "free"


@pytest.mark.django_db
def test_refund_delivered_twice_is_applied_once(stripe_billing):
    user = _user()
    _post("checkout.session.completed", _session(user, session_id="cs_a", pass_type="7d"))
    _post("checkout.session.completed", _session(user, session_id="cs_b", pass_type="14d"))
    _post("charge.refunded", _charge("pi_cs_a"))
    end_after_first = UserProfile.objects.get(user=user).current_period_end

    _post("charge.refunded", _charge("pi_cs_a"))

    assert UserProfile.objects.get(user=user).current_period_end == end_after_first


@pytest.mark.django_db
def test_partial_refund_keeps_the_period(stripe_billing):
    user = _user()
    _post("checkout.session.completed", _session(user, pass_type="7d"))
    end_before = UserProfile.objects.get(user=user).current_period_end

    _post("charge.refunded", _charge("pi_cs_test_1", amount_refunded=300, refunded=False))

    assert UserProfile.objects.get(user=user).current_period_end == end_before
    assert PremiumPassPurchase.objects.get(user=user).status == "completed"


@pytest.mark.django_db
def test_refund_for_unknown_payment_does_nothing(stripe_billing):
    res = _post("charge.refunded", _charge("pi_unknown"))

    assert res.status_code == 200


# --- 月額の自動更新は扱わない ---------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "event_type", ["customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"]
)
def test_subscription_events_are_ignored(stripe_billing, event_type):
    user = _user()
    UserProfile.objects.update_or_create(user=user, defaults={"stripe_customer_id": "cus_sub"})

    res = _post(
        event_type,
        {
            "id": "sub_1",
            "customer": "cus_sub",
            "status": "active",
            "current_period_end": int(time.time()) + 3600,
            "cancel_at_period_end": True,
        },
    )

    assert res.status_code == 200
    profile = UserProfile.objects.get(user=user)
    assert profile.current_period_end is None
    assert profile.stripe_subscription_id == ""
    assert profile.cancel_at_period_end is False
    assert _status_for(user)["plan"] == "free"


# --- 退会でユーザーと一緒に消える --------------------------------------------------------


@pytest.mark.django_db
def test_purchases_are_deleted_with_the_user(stripe_billing):
    user = _user()
    _post("checkout.session.completed", _session(user))

    user.delete()

    assert not PremiumPassPurchase.objects.exists()
