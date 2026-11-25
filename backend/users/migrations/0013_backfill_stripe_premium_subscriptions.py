from django.db import migrations
from django.utils import timezone

STRIPE_STATUSES = {
    "active": "active",
    "trialing": "active",
    "grace": "grace",
    "past_due": "billing_retry",
    "unpaid": "billing_retry",
    "billing_retry": "billing_retry",
    "": "expired",
    "inactive": "expired",
    "incomplete": "expired",
    "incomplete_expired": "expired",
    "expired": "expired",
    "canceled": "revoked",
    "revoked": "revoked",
}


def normalized_status(profile, now):
    old_status = profile.subscription_status.strip()
    status = STRIPE_STATUSES.get(old_status)
    if status is None:
        raise RuntimeError("Stripe profile status has no unambiguous subscription mapping.")

    end = profile.current_period_end
    future_end = end is not None and end > now
    legacy_active = old_status != "canceled" and (
        future_end if end is not None else old_status in ("active", "trialing")
    )
    normalized_active = status in ("active", "grace") and future_end
    if legacy_active != normalized_active:
        raise RuntimeError(
            "Stripe profile status and deadline cannot be backfilled with entitlement parity."
        )
    return status


def backfill_stripe_subscriptions(apps, schema_editor):
    alias = schema_editor.connection.alias
    profiles = apps.get_model("users", "UserProfile").objects.using(alias)
    subscriptions = apps.get_model("users", "PremiumSubscription").objects.using(alias)
    candidates = profiles.exclude(
        stripe_subscription_id="", stripe_price_id="", cancel_at_period_end=False
    )
    seen_ids = set()
    now = timezone.now()

    for profile in candidates.order_by("pk").iterator():
        subscription_id = profile.stripe_subscription_id
        price_id = profile.stripe_price_id
        if subscription_id != subscription_id.strip() or price_id != price_id.strip():
            raise RuntimeError("Stripe profile has malformed subscription identifiers.")
        if price_id and not subscription_id:
            raise RuntimeError("Stripe profile has a price ID without a subscription ID.")
        if subscription_id and not price_id:
            raise RuntimeError("Stripe profile has a subscription ID without a price ID.")
        if not subscription_id:
            raise RuntimeError(
                "Stripe profile has a cancellation scheduled without subscription identity."
            )
        if subscription_id in seen_ids:
            raise RuntimeError("A Stripe subscription ID is assigned to multiple profiles.")
        seen_ids.add(subscription_id)

        identity = {"source": "stripe", "external_subscription_id": subscription_id}
        subscription = subscriptions.filter(**identity).first()
        if subscription is None:
            subscription, _ = subscriptions.get_or_create(
                **identity,
                defaults={
                    "user_id": profile.user_id,
                    "product_id": price_id,
                    "status": normalized_status(profile, now),
                    "current_period_end": profile.current_period_end,
                    "auto_renew_enabled": not profile.cancel_at_period_end,
                },
            )
        if subscription.user_id != profile.user_id or subscription.product_id != price_id:
            raise RuntimeError(
                "Existing Stripe subscription conflicts with profile ownership or product."
            )


class Migration(migrations.Migration):
    dependencies = [("users", "0012_premium_subscription")]

    operations = [
        # Reapplying the backfill is safe and leaves independently recorded rows intact.
        migrations.RunPython(backfill_stripe_subscriptions, migrations.RunPython.noop),
    ]
