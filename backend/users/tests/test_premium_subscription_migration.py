from datetime import timedelta

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from temples.services.billing_state import get_billing_status
from users.models import PremiumSubscription

SCHEMA = ("users", "0012_premium_subscription")
BACKFILL = ("users", "0013_backfill_stripe_premium_subscriptions")

pytestmark = pytest.mark.django_db(transaction=True)


def migrate(target):
    return MigrationExecutor(connection).migrate([target]).apps


@pytest.fixture
def before_backfill():
    apps = migrate(SCHEMA)
    profiles = apps.get_model("users", "UserProfile").objects
    try:
        yield apps
    finally:
        # Remove any deliberately invalid legacy rows before restoring the latest schema.
        profiles.all().delete()
        migrate(("users", "0015_apple_billing_environments"))


def create_profile(apps, username, **fields):
    user = apps.get_model("auth", "User").objects.create(username=username)
    return apps.get_model("users", "UserProfile").objects.create(user=user, **fields)


def profile_status(user, now):
    status = get_billing_status(user=user, now=now)
    return (status.plan, status.is_active, status.current_period_end)


@pytest.mark.parametrize(
    "old_status, days, normalized, cancel",
    [
        ("active", 5, "active", False),
        ("trialing", 5, "active", False),
        ("active", 5, "active", True),
        ("active", -5, "active", False),
        ("canceled", 5, "revoked", False),
        ("past_due", -5, "billing_retry", False),
    ],
)
def test_backfill_matches_the_fallback_resolver(
    before_backfill, django_user_model, monkeypatch, old_status, days, normalized, cancel
):
    monkeypatch.setenv("BILLING_PROVIDER", "stripe")
    now = timezone.now()
    end = now + timedelta(days=days)
    profile = create_profile(
        before_backfill,
        "subscriber",
        stripe_subscription_id="sub_existing",
        stripe_price_id="price_monthly",
        subscription_status=old_status,
        current_period_end=end,
        cancel_at_period_end=cancel,
    )
    user = django_user_model.objects.get(pk=profile.user_id)
    before = profile_status(user, now)

    migrate(BACKFILL)

    after = profile_status(user, now)
    assert after == before
    row = PremiumSubscription.objects.get(user=user)
    assert row.source == "stripe"
    assert row.external_subscription_id == "sub_existing"
    assert row.product_id == "price_monthly"
    assert row.status == normalized
    assert row.current_period_end == end
    assert row.auto_renew_enabled is not cancel
    assert row.current_period_start is None
    assert row.last_event_at is None
    assert row.environment == "unknown"


def test_backfill_keeps_free_and_other_entitlements_unchanged(before_backfill):
    apps = before_backfill
    now = timezone.now()
    end = now + timedelta(days=8)
    free = create_profile(apps, "free")
    profile = create_profile(
        apps,
        "hybrid",
        stripe_subscription_id="sub_hybrid",
        stripe_price_id="price_monthly",
        subscription_status="active",
        current_period_end=end,
        legacy_premium_until=end,
        account_entitlement_disabled=True,
    )
    subscriptions = apps.get_model("users", "PremiumSubscription").objects
    apple = subscriptions.create(
        user_id=profile.user_id,
        source="apple",
        original_transaction_id="apple_original",
        product_id="apple.monthly",
        status="grace",
        current_period_end=end,
        environment="sandbox",
        auto_renew_enabled=True,
    )
    existing_apple = subscriptions.values().get(pk=apple.pk)
    purchases = apps.get_model("users", "PremiumPassPurchase").objects
    purchase = purchases.create(
        user_id=profile.user_id,
        days=7,
        source="stripe",
        external_id="pass",
        period_end_before=now,
        period_end_after=end,
        effective_period_end=end - timedelta(days=1),
    )
    existing_purchase = purchases.values().get(pk=purchase.pk)
    profiles = apps.get_model("users", "UserProfile").objects
    existing_profile = profiles.values().get(pk=profile.pk)

    migrate(BACKFILL)

    assert not subscriptions.filter(user_id=free.user_id).exists()
    assert subscriptions.filter(user_id=profile.user_id, source="stripe").count() == 1
    assert subscriptions.values().get(pk=apple.pk) == existing_apple
    assert purchases.values().get(pk=purchase.pk) == existing_purchase
    assert profiles.values().get(pk=profile.pk) == existing_profile


@pytest.mark.parametrize(
    "ids, extra, message",
    [
        (("", "price_monthly"), {}, "price ID without a subscription ID"),
        (("sub_missing_price", ""), {}, "subscription ID without a price ID"),
        (
            ("", ""),
            {"cancel_at_period_end": True},
            "cancellation scheduled without subscription identity",
        ),
        (("sub_no_end", "price_monthly"), {"subscription_status": "active"}, "entitlement parity"),
        ((" sub_dirty", "price_monthly"), {}, "malformed subscription identifiers"),
    ],
)
def test_backfill_aborts_atomically_on_ambiguous_profile(before_backfill, ids, extra, message):
    apps = before_backfill
    create_profile(
        apps,
        "valid_first",
        stripe_subscription_id="sub_valid",
        stripe_price_id="price_monthly",
        subscription_status="trialing",
        current_period_end=timezone.now() + timedelta(days=3),
    )
    create_profile(
        apps, "ambiguous", stripe_subscription_id=ids[0], stripe_price_id=ids[1], **extra
    )

    with pytest.raises(RuntimeError, match=message):
        migrate(BACKFILL)

    assert BACKFILL not in MigrationExecutor(connection).loader.applied_migrations
    assert not PremiumSubscription.objects.exists()


def test_backfill_rejects_duplicate_profile_ownership(before_backfill):
    for username in ("first", "second"):
        create_profile(
            before_backfill,
            username,
            stripe_subscription_id="sub_shared",
            stripe_price_id="price_monthly",
        )

    with pytest.raises(RuntimeError, match="assigned to multiple profiles"):
        migrate(BACKFILL)

    assert not PremiumSubscription.objects.exists()


@pytest.mark.parametrize("conflict", ["ownership", "product"])
def test_backfill_rejects_conflicting_subscription_rows(before_backfill, conflict):
    apps = before_backfill
    profile = create_profile(
        apps, "subscriber", stripe_subscription_id="sub_existing", stripe_price_id="price_monthly"
    )
    other = create_profile(apps, "other")
    existing = apps.get_model("users", "PremiumSubscription").objects
    row = existing.create(
        user_id=other.user_id if conflict == "ownership" else profile.user_id,
        source="stripe",
        external_subscription_id="sub_existing",
        product_id="price_other" if conflict == "product" else "price_monthly",
        status="revoked",
    )
    snapshot = existing.values().get(pk=row.pk)

    with pytest.raises(RuntimeError, match="conflicts with profile ownership or product"):
        migrate(BACKFILL)

    assert existing.values().get(pk=row.pk) == snapshot


def test_matching_existing_stripe_row_remains_authoritative(before_backfill):
    apps = before_backfill
    profile = create_profile(
        apps,
        "subscriber",
        stripe_subscription_id="sub_existing",
        stripe_price_id="price_monthly",
        subscription_status="active",
        current_period_end=timezone.now() + timedelta(days=5),
    )
    existing = apps.get_model("users", "PremiumSubscription").objects
    row = existing.create(
        user_id=profile.user_id,
        source="stripe",
        external_subscription_id="sub_existing",
        product_id="price_monthly",
        status="revoked",
    )
    snapshot = existing.values().get(pk=row.pk)

    migrate(BACKFILL)
    migrate(SCHEMA)
    migrate(BACKFILL)

    assert existing.count() == 1
    assert existing.values().get(pk=row.pk) == snapshot
