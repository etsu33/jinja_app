from datetime import timedelta

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from users.models import PremiumPassPurchase, UserProfile
from users.services.premium_pass import get_pass_period_end, revoke_premium_pass_for_refund

OLD = [("users", "0010_premium_pass_purchase")]
NEW = [("users", "0011_separate_premium_entitlements")]
LATEST = [("users", "0015_apple_billing_environments")]

pytestmark = pytest.mark.django_db(transaction=True)


def migrate(target):
    return MigrationExecutor(connection).migrate(target).apps


@pytest.fixture(autouse=True)
def restore_latest_schema():
    migrate(NEW)
    try:
        yield
    finally:
        migrate(LATEST)


@pytest.fixture
def old_schema(restore_latest_schema):
    try:
        yield migrate(OLD)
    finally:
        migrate(NEW)


@pytest.mark.parametrize("had_expired_baseline", [False, True])
def test_migration_preserves_deadlines_and_can_reverse(old_schema, had_expired_baseline):
    users = old_schema.get_model("auth", "User").objects
    profiles = old_schema.get_model("users", "UserProfile").objects
    purchases = old_schema.get_model("users", "PremiumPassPurchase").objects
    now = timezone.now()
    end = now + timedelta(days=1)
    final_end = end + timedelta(days=7)
    free = profiles.create(user=users.create(username="free"))
    legacy = profiles.create(user=users.create(username="legacy"), current_period_end=end)
    subscription = profiles.create(
        user=users.create(username="subscription"), current_period_end=final_end,
        stripe_subscription_id="sub_test", stripe_price_id="price_test", subscription_status="active", cancel_at_period_end=True,
    )
    pass_profile = profiles.create(
        user=users.create(username="pass"), current_period_end=final_end, subscription_status="active",
    )
    purchases.create(
        user_id=pass_profile.user_id, days=1, source="stripe", external_id="first", payment_intent_id="first",
        period_end_before=now - timedelta(days=1) if had_expired_baseline else None, period_end_after=end,
    )
    second = purchases.create(
        user_id=pass_profile.user_id, days=7, source="stripe", external_id="second",
        period_end_before=end, period_end_after=final_end,
    )

    migrate(NEW)
    assert not UserProfile.objects.filter(account_entitlement_disabled=True).exists()
    assert UserProfile.objects.get(pk=free.pk).current_period_end is None
    assert UserProfile.objects.get(pk=free.pk).legacy_premium_until is None
    assert UserProfile.objects.get(pk=legacy.pk).legacy_premium_until == end
    assert UserProfile.objects.get(pk=legacy.pk).current_period_end is None
    assert UserProfile.objects.get(pk=pass_profile.pk).current_period_end is None
    assert get_pass_period_end(user_id=pass_profile.user_id) == final_end
    sub = UserProfile.objects.get(pk=subscription.pk)
    assert sub.current_period_end == final_end
    assert sub.subscription_status == "active"
    assert sub.cancel_at_period_end

    restored = migrate(OLD).get_model("users", "UserProfile").objects
    assert restored.get(pk=legacy.pk).current_period_end == end
    assert restored.get(pk=pass_profile.pk).current_period_end == final_end
    assert restored.get(pk=subscription.pk).current_period_end == final_end

    migrate(LATEST)
    revoke_premium_pass_for_refund(source="stripe", payment_intent_id="first", now=now)
    assert get_pass_period_end(user_id=pass_profile.user_id) == final_end - timedelta(days=1)
    assert PremiumPassPurchase.objects.get(pk=second.pk).period_end_after == final_end


def test_migration_refuses_to_assign_ambiguous_initial_deadline(old_schema):
    user = old_schema.get_model("auth", "User").objects.create(username="ambiguous")
    profiles = old_schema.get_model("users", "UserProfile").objects
    purchases = old_schema.get_model("users", "PremiumPassPurchase").objects
    before = timezone.now() + timedelta(days=7)
    end = before + timedelta(days=1)
    profile = profiles.create(user_id=user.pk, current_period_end=end, subscription_status="active")
    purchase = purchases.create(
        user_id=user.pk, days=1, source="stripe", external_id="ambiguous",
        period_end_before=before, period_end_after=end,
    )
    try:
        with pytest.raises(RuntimeError, match="initial deadline"):
            migrate(NEW)
        assert NEW[0] not in MigrationExecutor(connection).loader.applied_migrations
        assert profiles.get(pk=profile.pk).current_period_end == end
    finally:
        purchase.delete()


def test_migration_refuses_legacy_classification_for_cancellation_scheduled_profile(old_schema):
    user = old_schema.get_model("auth", "User").objects.create(username="cancellation_scheduled")
    profiles = old_schema.get_model("users", "UserProfile").objects
    period_end = timezone.now() + timedelta(days=7)
    profile = profiles.create(
        user_id=user.pk,
        current_period_end=period_end,
        subscription_status="active",
        cancel_at_period_end=True,
    )
    try:
        with pytest.raises(RuntimeError, match="cancellation-scheduled"):
            migrate(NEW)

        assert NEW[0] not in MigrationExecutor(connection).loader.applied_migrations
        unchanged = profiles.get(pk=profile.pk)
        assert unchanged.stripe_subscription_id == ""
        assert unchanged.stripe_price_id == ""
        assert unchanged.current_period_end == period_end
        assert unchanged.subscription_status == "active"
        assert unchanged.cancel_at_period_end
    finally:
        profile.delete()


def test_reverse_preserves_account_stop_by_refusing_rollback(django_user_model):
    user = django_user_model.objects.create_user(username="disabled")
    UserProfile.objects.update_or_create(user=user, defaults={"account_entitlement_disabled": True})

    with pytest.raises(RuntimeError, match="discard an account entitlement stop"):
        migrate(OLD)

    assert UserProfile.objects.get(user=user).account_entitlement_disabled


def test_reverse_refuses_to_overwrite_subscription_with_legacy(django_user_model):
    user = django_user_model.objects.create_user(username="mixed")
    now = timezone.now()
    sub_end = now + timedelta(days=20)
    legacy_end = now + timedelta(days=5)
    UserProfile.objects.update_or_create(user=user, defaults={
        "stripe_subscription_id": "sub_test",
        "stripe_price_id": "price_test",
        "subscription_status": "active",
        "current_period_end": sub_end,
        "legacy_premium_until": legacy_end,
    })

    with pytest.raises(RuntimeError, match="merge independently managed"):
        migrate(OLD)

    profile = UserProfile.objects.get(user=user)
    assert profile.current_period_end == sub_end
    assert profile.legacy_premium_until == legacy_end
