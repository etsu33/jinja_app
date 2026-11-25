from dataclasses import dataclass
from datetime import datetime

from django.db import transaction
from django.db.models import Count, Max, Q
from users.models import PremiumSubscription
from users.services.billing import BillingOwnershipConflict


def get_subscription_entitlement(*, user_id, now: datetime) -> tuple[bool, datetime | None]:
    """Return whether provider rows exist and their latest eligible deadline."""
    subscriptions = PremiumSubscription.objects.filter(user_id=user_id).aggregate(
        row_count=Count("pk"),
        active_end=Max(
            "current_period_end",
            filter=Q(
                status__in=(PremiumSubscription.Status.ACTIVE, PremiumSubscription.Status.GRACE),
                current_period_end__gt=now,
            ),
        ),
    )
    return subscriptions["row_count"] > 0, subscriptions["active_end"]


@dataclass(frozen=True)
class SubscriptionUpdate:
    source: str
    identity: str
    product_id: str
    environment: str
    status: str
    period_start: datetime
    period_end: datetime
    event_at: datetime
    auto_renew_enabled: bool | None = None


@transaction.atomic
def apply_subscription_update(update: SubscriptionUpdate, *, user=None, authoritative: bool = True):
    """Apply verified provider state. Only an authenticated claim may establish ownership."""
    identity_field = {
        PremiumSubscription.Source.APPLE: "original_transaction_id",
        PremiumSubscription.Source.STRIPE: "external_subscription_id",
    }[update.source]
    rows = PremiumSubscription.objects.select_for_update()
    identity = {"source": update.source, identity_field: update.identity}
    if update.source == PremiumSubscription.Source.APPLE:
        identity["environment"] = update.environment
    values = {
        "product_id": update.product_id,
        "environment": update.environment,
        "status": update.status,
        "current_period_start": update.period_start,
        "current_period_end": update.period_end,
        "last_event_at": update.event_at,
    }
    if update.auto_renew_enabled is not None:
        values["auto_renew_enabled"] = update.auto_renew_enabled

    if user is None:
        subscription = rows.filter(**identity).first()
        if subscription is None:
            return None
    else:
        subscription, created = rows.get_or_create(**identity, defaults={"user": user, **values})
        if created:
            return subscription
        if subscription.user_id != user.pk:
            raise BillingOwnershipConflict

    if (
        subscription.environment != update.environment
        or subscription.product_id != update.product_id
    ):
        raise BillingOwnershipConflict
    if _is_stale_subscription_update(subscription, update, authoritative=authoritative):
        return subscription

    for field, value in values.items():
        setattr(subscription, field, value)
    subscription.save(update_fields=[*values, "updated_at"])
    return subscription


def _is_stale_subscription_update(subscription, update, *, authoritative):
    start = subscription.current_period_start
    if start is not None and (
        update.period_start < start or (update.period_start == start and not authoritative)
    ):
        return True
    if subscription.last_event_at is None or update.event_at > subscription.last_event_at:
        return False
    # Equal signing times cannot restore access after a revocation.
    return not (
        update.event_at == subscription.last_event_at
        and update.status == PremiumSubscription.Status.REVOKED
        and subscription.status != PremiumSubscription.Status.REVOKED
    )
