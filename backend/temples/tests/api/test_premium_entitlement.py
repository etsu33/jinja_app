from datetime import timedelta

import pytest
from django.utils import timezone

from temples.services.billing_state import get_billing_status, is_premium_for_user, recommend_limit_for_user
from users.models import UserProfile
from users.services.premium_pass import grant_premium_pass, revoke_premium_pass_for_refund


@pytest.mark.django_db
@pytest.mark.parametrize(
    "subscription, pass_state, legacy, disabled, expected",
    [
        ("inactive", None, None, False, False),
        ("active", None, None, False, True),
        ("inactive", "active", None, False, True),
        ("inactive", None, "active", False, True),
        ("active", "active", None, False, True),
        ("active", None, "active", False, True),
        ("inactive", "active", "active", False, True),
        ("expired", "active", None, False, True),
        ("active", "expired", None, False, True),
        ("canceled", None, None, False, False),
        ("canceled", "active", None, False, True),
        ("canceled", None, "active", False, True),
        ("inactive", "refunded", None, False, False),
        ("active", "refunded", None, False, True),
        ("inactive", None, "expired", False, False),
        ("active", None, None, True, False),
        ("inactive", "active", None, True, False),
        ("inactive", None, "active", True, False),
        ("active", "active", "active", True, False),
    ],
)
def test_entitlement_sources(django_user_model, monkeypatch, subscription, pass_state, legacy, disabled, expected):
    monkeypatch.setenv("BILLING_PROVIDER", "stripe")
    now = timezone.now()
    user = django_user_model.objects.create_user(username="entitlement")
    future = now + timedelta(days=1)
    past = now - timedelta(days=1)
    UserProfile.objects.update_or_create(user=user, defaults={
        "stripe_subscription_id": "sub_test" if subscription != "inactive" else "",
        "subscription_status": "active" if subscription == "expired" else subscription,
        "current_period_end": {"active": future, "expired": past, "canceled": future}.get(subscription),
        "legacy_premium_until": {"active": future, "expired": past}.get(legacy),
        "account_entitlement_disabled": disabled,
    })
    if pass_state:
        grant_premium_pass(
            user=user, days=1, source="stripe", external_id="cs_test", payment_intent_id="pi_test",
            now=past - timedelta(days=1) if pass_state == "expired" else now,
        )
    if pass_state == "refunded":
        revoke_premium_pass_for_refund(source="stripe", payment_intent_id="pi_test", now=now)

    status = get_billing_status(user=user, now=now)
    assert status.plan == ("premium" if expected else "free")
    assert status.is_active is expected
    assert is_premium_for_user(user) is expected
    assert recommend_limit_for_user(user) == (6 if expected else 3)


@pytest.mark.django_db
def test_account_stop_precedes_stub_and_staff(django_user_model, monkeypatch):
    monkeypatch.setenv("BILLING_PROVIDER", "stub")
    monkeypatch.setenv("BILLING_STUB_PLAN", "premium")
    monkeypatch.setenv("BILLING_STUB_ACTIVE", "1")
    user = django_user_model.objects.create_user(username="disabled-staff", is_staff=True)
    UserProfile.objects.update_or_create(user=user, defaults={"account_entitlement_disabled": True})

    assert not get_billing_status(user=user).is_active
    assert not is_premium_for_user(user)
