from datetime import timedelta

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone
from temples.services.billing_state import (
    get_billing_status,
    is_premium_for_user,
    recommend_limit_for_user,
)
from users.models import PremiumSubscription, UserProfile
from users.services.premium_pass import grant_premium_pass

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(django_user_model, monkeypatch):
    monkeypatch.setenv("BILLING_PROVIDER", "stripe")
    return django_user_model.objects.create_user(username="subscription-test")


def subscription(user, *, source="stripe", identity="monthly", **fields):
    key = "external_subscription_id" if source == "stripe" else "original_transaction_id"
    return PremiumSubscription.objects.create(
        user=user,
        source=source,
        product_id="premium.monthly",
        **{key: identity},
        **fields,
    )


@pytest.mark.parametrize(
    "source, status, days, active",
    [
        ("stripe", "active", 10, True),
        ("apple", "grace", 10, True),
        ("apple", "billing_retry", 10, False),
        ("stripe", "expired", 10, False),
        ("apple", "revoked", 10, False),
        ("stripe", "active", None, False),
        ("apple", "grace", 0, False),
    ],
)
def test_only_active_and_grace_with_future_deadlines_grant_premium(
    user, source, status, days, active
):
    now = timezone.now()
    end = now + timedelta(days=days) if days is not None else None
    subscription(user, source=source, status=status, current_period_end=end)

    result = get_billing_status(user=user, now=now)

    assert result.plan == ("premium" if active else "free")
    assert result.is_active is active
    assert result.current_period_end == (end if active else None)
    assert recommend_limit_for_user(user) == (6 if active else 3)


@pytest.mark.parametrize(
    "pass_days, legacy_days, expected_days", [(None, None, 10), (14, 8, 14), (7, 12, 12)]
)
def test_maximum_deadline_across_multiple_sources(user, pass_days, legacy_days, expected_days):
    now = timezone.now()
    subscription(user, status="active", current_period_end=now + timedelta(days=3))
    subscription(user, source="apple", status="grace", current_period_end=now + timedelta(days=10))
    subscription(
        user,
        source="apple",
        identity="revoked",
        status="revoked",
        current_period_end=now + timedelta(days=60),
    )
    if pass_days:
        grant_premium_pass(user=user, source="stripe", external_id="pass", days=pass_days, now=now)
    if legacy_days:
        UserProfile.objects.filter(user=user).update(
            legacy_premium_until=now + timedelta(days=legacy_days)
        )

    result = get_billing_status(user=user, now=now)

    assert result.plan == "premium"
    assert result.current_period_end == now + timedelta(days=expected_days)


@pytest.mark.parametrize("with_app_row", [False, True])
def test_profile_deadline_is_used_only_without_provider_rows(user, with_app_row):
    now = timezone.now()
    mirror_end = now + timedelta(days=60)
    UserProfile.objects.filter(user=user).update(
        subscription_status="active", current_period_end=mirror_end
    )
    if with_app_row:
        subscription(user, source="apple", status="revoked", current_period_end=mirror_end)

    result = get_billing_status(user=user, now=now)
    assert result.is_active is not with_app_row
    assert result.current_period_end == (None if with_app_row else mirror_end)

    if with_app_row:
        active_end = now + timedelta(days=4)
        subscription(user, status="active", current_period_end=active_end)
        assert get_billing_status(user=user, now=now).current_period_end == active_end


@pytest.mark.parametrize("kind", ["pass", "legacy"])
def test_non_subscription_entitlements_still_grant_premium(user, kind):
    now = timezone.now()
    end = now + timedelta(days=1)
    subscription(user, source="apple", status="expired")
    if kind == "pass":
        grant_premium_pass(user=user, source="stripe", external_id="pass", days=1, now=now)
    else:
        UserProfile.objects.filter(user=user).update(legacy_premium_until=end)

    result = get_billing_status(user=user, now=now)
    assert result.is_active
    assert result.current_period_end == end


def test_disabled_account_wins_over_provider_rows_pass_legacy_staff_and_stub(user, monkeypatch):
    now = timezone.now()
    end = now + timedelta(days=3)
    subscription(user, source="apple", status="active", current_period_end=end)
    subscription(user, status="grace", current_period_end=end)
    grant_premium_pass(user=user, source="stripe", external_id="pass", days=1, now=now)
    UserProfile.objects.filter(user=user).update(
        legacy_premium_until=end,
        account_entitlement_disabled=True,
    )
    user.is_staff = True
    monkeypatch.setenv("BILLING_STUB_PLAN", "premium")
    monkeypatch.setenv("BILLING_STUB_ACTIVE", "1")

    for provider in ("stripe", "stub"):
        monkeypatch.setenv("BILLING_PROVIDER", provider)
        result = get_billing_status(user=user, now=now)
        assert result.plan == "free"
        assert not result.is_active
        assert result.current_period_end is None
        assert not is_premium_for_user(user)
        assert recommend_limit_for_user(user) == 3


def test_existing_staff_and_stub_behavior(user, monkeypatch):
    now = timezone.now()
    subscription(user, source="apple", status="revoked", current_period_end=now + timedelta(days=3))
    user.is_staff = True
    assert is_premium_for_user(user)
    assert not get_billing_status(user=user, now=now).is_active

    user.is_staff = False
    monkeypatch.setenv("BILLING_PROVIDER", "stub")
    monkeypatch.setenv("BILLING_STUB_PLAN", "premium")
    monkeypatch.setenv("BILLING_STUB_ACTIVE", "1")
    assert get_billing_status(user=user, now=now) == get_billing_status(now=now)
    assert is_premium_for_user(user)


@pytest.mark.parametrize("source", ["stripe", "apple"])
def test_provider_subscription_identity_is_unique_across_accounts(user, django_user_model, source):
    other = django_user_model.objects.create_user(username="other-subscriber")
    subscription(user, source=source, status="expired")

    with pytest.raises(IntegrityError), transaction.atomic():
        subscription(other, source=source, status="expired")


def test_undated_profile_subscription_can_still_use_the_temporary_fallback(user):
    now = timezone.now()
    UserProfile.objects.filter(user=user).update(subscription_status="trialing")

    result = get_billing_status(user=user, now=now)

    assert (result.plan, result.is_active, result.current_period_end) == ("premium", True, None)
