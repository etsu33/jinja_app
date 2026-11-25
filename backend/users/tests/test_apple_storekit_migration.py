from datetime import timedelta

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from users.models import PremiumPassPurchase, PremiumSubscription


@pytest.mark.django_db(transaction=True)
def test_schema_rollback_is_blocked_before_apple_subscriptions_can_be_lost(django_user_model):
    user = django_user_model.objects.create_user(username="apple-subscriber")
    apple = PremiumSubscription.objects.create(
        user=user,
        source="apple",
        product_id="com.morietsu.kamimusubi.premium.monthly",
        original_transaction_id="100",
        status="active",
        environment="Production",
    )

    try:
        with pytest.raises(RuntimeError, match="discard verified Apple billing state"):
            MigrationExecutor(connection).migrate([("users", "0011_separate_premium_entitlements")])

        assert PremiumSubscription.objects.filter(pk=apple.pk).exists()
        assert ("users", "0014_apple_storekit_receipt") in MigrationExecutor(
            connection
        ).loader.applied_migrations
    finally:
        MigrationExecutor(connection).migrate([("users", "0015_apple_billing_environments")])


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "environments", [("Sandbox",), ("Production",), (), ("Sandbox", "Production")]
)
def test_backfill_requires_an_unambiguous_verified_apple_pass_receipt(
    django_user_model, environments
):
    old = ("users", "0014_apple_storekit_receipt")
    new = ("users", "0015_apple_billing_environments")
    apps = MigrationExecutor(connection).migrate([old]).apps
    user = django_user_model.objects.create_user(username="apple-pass-owner")
    rows = apps.get_model("users", "PremiumPassPurchase").objects
    end = timezone.now() + timedelta(days=7)
    apple = rows.create(
        user_id=user.pk,
        source="apple",
        external_id="100",
        days=7,
        period_end_after=end,
        effective_period_end=end,
    )
    stripe = rows.create(
        user_id=user.pk,
        source="stripe",
        external_id="100",
        days=1,
        period_end_after=end,
    )
    receipts = apps.get_model("users", "AppleStoreKitReceipt").objects
    for environment in environments:
        receipts.create(environment=environment, kind="pass", external_id="100")

    try:
        if len(environments) == 1:
            MigrationExecutor(connection).migrate([new])
            migrated = PremiumPassPurchase.objects.get(pk=apple.pk)
            assert migrated.environment == environments[0]
            assert migrated.effective_period_end == end
            assert PremiumPassPurchase.objects.get(pk=stripe.pk).environment == ""
        else:
            with pytest.raises(RuntimeError, match="unique verified environment"):
                MigrationExecutor(connection).migrate([new])
            assert new not in MigrationExecutor(connection).loader.applied_migrations
            assert rows.get(pk=apple.pk).effective_period_end == end
    finally:
        rows.filter(pk__in=[apple.pk, stripe.pk]).delete()
        MigrationExecutor(connection).migrate([new])
