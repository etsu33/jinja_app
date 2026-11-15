import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from users.models import PremiumSubscription


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

    with pytest.raises(RuntimeError, match="discard verified Apple billing state"):
        MigrationExecutor(connection).migrate([("users", "0011_separate_premium_entitlements")])

    assert PremiumSubscription.objects.filter(pk=apple.pk).exists()
    assert ("users", "0014_apple_storekit_receipt") in MigrationExecutor(
        connection
    ).loader.applied_migrations
