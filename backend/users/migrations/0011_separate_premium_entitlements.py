from django.db import migrations, models
from django.db.models import F, Max, Q


def separate_entitlements(apps, schema_editor):
    alias = schema_editor.connection.alias
    profiles = apps.get_model("users", "UserProfile").objects.using(alias)
    purchases = apps.get_model("users", "PremiumPassPurchase").objects.using(alias)
    pass_users = purchases.values("user_id")
    if purchases.exclude(user_id__in=profiles.values("user_id")).exists():
        raise RuntimeError("Cannot verify existing Pass deadlines without a billing profile.")

    for profile in profiles.filter(user_id__in=pass_users).iterator():
        if profile.stripe_subscription_id or profile.stripe_price_id or profile.cancel_at_period_end:
            raise RuntimeError("Cannot separate a shared deadline with both Pass and subscription evidence.")

        previous_end = None
        history = purchases.filter(user_id=profile.user_id).order_by("created_at", "pk")
        for purchase in history.iterator():
            before = purchase.period_end_before
            if previous_end is None and before is not None and before > purchase.created_at:
                raise RuntimeError("Cannot classify the initial deadline preceding a Pass purchase.")
            if previous_end is not None and before != previous_end:
                raise RuntimeError("Cannot verify the chain of existing Pass deadlines.")
            if purchase.status != "completed" or purchase.refunded_at is not None:
                raise RuntimeError("Cannot verify existing Pass deadlines with refund history.")
            previous_end = purchase.period_end_after

        if previous_end != profile.current_period_end:
            raise RuntimeError("Existing Pass deadline does not match the shared deadline.")

    without_subscription = profiles.filter(stripe_subscription_id="", stripe_price_id="")
    if without_subscription.filter(cancel_at_period_end=True).exists():
        raise RuntimeError("Cannot classify a cancellation-scheduled profile without subscription identifiers.")
    purchases.update(effective_period_end=F("period_end_after"))
    without_subscription.exclude(user_id__in=pass_users).update(legacy_premium_until=F("current_period_end"))
    without_subscription.update(current_period_end=None, subscription_status="inactive", cancel_at_period_end=False)


def restore_shared_deadlines(apps, schema_editor):
    alias = schema_editor.connection.alias
    profiles = apps.get_model("users", "UserProfile").objects.using(alias)
    purchases = apps.get_model("users", "PremiumPassPurchase").objects.using(alias)
    pass_users = purchases.filter(effective_period_end__isnull=False).values("user_id")
    if profiles.filter(account_entitlement_disabled=True).exists():
        raise RuntimeError("Rollback would discard an account entitlement stop.")

    legacy_profiles = profiles.filter(legacy_premium_until__isnull=False)
    has_subscription = (
        ~Q(stripe_subscription_id="") | ~Q(stripe_price_id="") | Q(current_period_end__isnull=False)
        | Q(subscription_status__in=("active", "trialing")) | Q(cancel_at_period_end=True)
    )
    if (
        legacy_profiles.filter(has_subscription | Q(user_id__in=pass_users)).exists()
        or profiles.filter(user_id__in=pass_users).filter(has_subscription).exists()
    ):
        raise RuntimeError("Rollback would merge independently managed Premium deadlines.")

    for profile in profiles.filter(user_id__in=pass_users).iterator():
        end = purchases.filter(user_id=profile.user_id, status="completed").aggregate(
            end=Max("effective_period_end")
        )["end"]
        profiles.filter(pk=profile.pk).update(current_period_end=end, subscription_status="active")

    legacy_profiles.update(current_period_end=F("legacy_premium_until"), subscription_status="active")


class Migration(migrations.Migration):
    dependencies = [("users", "0010_premium_pass_purchase")]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="legacy_premium_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="account_entitlement_disabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="premiumpasspurchase",
            name="effective_period_end",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(separate_entitlements, restore_shared_deadlines),
    ]
