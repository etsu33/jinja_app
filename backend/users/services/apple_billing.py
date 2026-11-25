"""Apply verified Apple purchases and notifications through existing billing services."""

import logging

from django.db import transaction
from users.models import AppleStoreKitReceipt, PremiumPassPurchase, PremiumSubscription
from users.services.apple_storekit import (
    VerifiedAppleNotification,
    VerifiedAppleTransaction,
    apple_subscription_update,
    resolve_apple_product,
)
from users.services.billing import BillingOwnershipConflict
from users.services.premium_pass import grant_premium_pass, revoke_premium_pass
from users.services.premium_subscription import SubscriptionUpdate, apply_subscription_update

log = logging.getLogger(__name__)


def _receipt(purchase):
    identity = (
        purchase.original_transaction_id
        if purchase.kind == "subscription"
        else purchase.transaction_id
    )
    receipt, _ = AppleStoreKitReceipt.objects.select_for_update().get_or_create(
        environment=purchase.environment,
        kind=purchase.kind,
        external_id=identity,
    )
    return receipt


def _pending_subscription(receipt, product_id):
    return SubscriptionUpdate(
        source=PremiumSubscription.Source.APPLE,
        identity=receipt.external_id,
        product_id=product_id,
        environment=receipt.environment,
        status=receipt.status,
        period_start=receipt.purchased_at,
        period_end=receipt.period_end,
        event_at=receipt.event_at,
        auto_renew_enabled=receipt.auto_renew_enabled,
    )


def _record_unclaimed_subscription(receipt, update):
    if receipt.event_at is not None and (
        update.event_at < receipt.event_at
        or update.period_start < receipt.purchased_at
        or (
            update.event_at == receipt.event_at
            and update.status != PremiumSubscription.Status.REVOKED
        )
    ):
        return
    receipt.event_at = update.event_at
    receipt.purchased_at = update.period_start
    receipt.period_end = update.period_end
    receipt.status = update.status
    receipt.auto_renew_enabled = update.auto_renew_enabled
    receipt.save(
        update_fields=["event_at", "purchased_at", "period_end", "status", "auto_renew_enabled"]
    )


def _revoke_apple_pass(receipt, event_at):
    if receipt.event_at is None or event_at > receipt.event_at:
        receipt.event_at = event_at
        receipt.save(update_fields=["event_at"])
    return revoke_premium_pass(
        source=PremiumPassPurchase.SOURCE_APPLE,
        external_id=receipt.external_id,
        environment=receipt.environment,
    )


@transaction.atomic
def apply_apple_purchase(purchase: VerifiedAppleTransaction, *, user):
    receipt = _receipt(purchase)
    if purchase.kind == "subscription":
        update = apple_subscription_update(purchase, event_at=purchase.signed_at)
        authoritative = update.status == PremiumSubscription.Status.REVOKED
        if receipt.event_at is not None and receipt.purchased_at >= update.period_start:
            pending = _pending_subscription(receipt, purchase.product_id)
            if not authoritative or pending.event_at > update.event_at:
                update = pending
            authoritative = True
        return apply_subscription_update(update, user=user, authoritative=authoritative)

    definition = resolve_apple_product(purchase.product_id).travel_pass
    if purchase.revoked_at is not None or receipt.event_at is not None:
        owner_id = (
            PremiumPassPurchase.objects.filter(
                source=PremiumPassPurchase.SOURCE_APPLE,
                external_id=purchase.transaction_id,
                environment=purchase.environment,
            )
            .values_list("user_id", flat=True)
            .first()
        )
        if owner_id is not None and owner_id != user.pk:
            raise BillingOwnershipConflict
        return _revoke_apple_pass(receipt, purchase.revoked_at or receipt.event_at)
    return grant_premium_pass(
        user=user,
        source=PremiumPassPurchase.SOURCE_APPLE,
        external_id=purchase.transaction_id,
        environment=purchase.environment,
        pass_type=definition.pass_type,
        days=definition.days,
        now=purchase.purchased_at,
    )


@transaction.atomic
def apply_apple_notification(notification: VerifiedAppleNotification):
    purchase = notification.transaction
    if notification.subscription is not None:
        receipt = _receipt(purchase)
        if apply_subscription_update(notification.subscription) is None:
            _record_unclaimed_subscription(receipt, notification.subscription)
            log.info("Verified Apple subscription notification has no local owner.")
    elif notification.revoked:
        receipt = _receipt(purchase)
        if not _revoke_apple_pass(receipt, notification.event_at).applied:
            log.info("Verified Apple Pass revocation had no completed local purchase.")
