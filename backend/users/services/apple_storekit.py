"""Verify Apple-signed payloads and translate them into backend billing data."""

from dataclasses import dataclass
from datetime import datetime
from datetime import timezone as utc_timezone
from functools import lru_cache
from pathlib import Path

from appstoreserverlibrary.models.Environment import Environment
from appstoreserverlibrary.models.NotificationTypeV2 import NotificationTypeV2
from appstoreserverlibrary.models.Status import Status
from appstoreserverlibrary.signed_data_verifier import (
    SignedDataVerifier,
    VerificationException,
    VerificationStatus,
)
from cattrs import BaseValidationError
from django.conf import settings
from django.utils import timezone
from users.models import PremiumSubscription
from users.services.premium_pass import PASS_DEFINITIONS, PassDefinition
from users.services.premium_subscription import SubscriptionUpdate

BUNDLE_ID = "com.morietsu.kamimusubi"


class AppleStoreKitInvalid(ValueError):
    """The signed input cannot be accepted."""


class AppleStoreKitUnavailable(RuntimeError):
    """Verification is unconfigured or temporarily unavailable."""


@dataclass(frozen=True)
class AppleProduct:
    kind: str
    entitlement: str = "premium"
    travel_pass: PassDefinition | None = None


APPLE_PRODUCTS = {
    f"{BUNDLE_ID}.premium.monthly": AppleProduct("subscription"),
    f"{BUNDLE_ID}.pass.1day": AppleProduct("pass", travel_pass=PASS_DEFINITIONS["1d"]),
    f"{BUNDLE_ID}.pass.7day": AppleProduct("pass", travel_pass=PASS_DEFINITIONS["7d"]),
    f"{BUNDLE_ID}.pass.14day": AppleProduct("pass", travel_pass=PASS_DEFINITIONS["14d"]),
}

SUBSCRIPTION_STATUSES = {
    Status.ACTIVE: PremiumSubscription.Status.ACTIVE,
    Status.EXPIRED: PremiumSubscription.Status.EXPIRED,
    Status.BILLING_RETRY: PremiumSubscription.Status.BILLING_RETRY,
    Status.BILLING_GRACE_PERIOD: PremiumSubscription.Status.GRACE,
    Status.REVOKED: PremiumSubscription.Status.REVOKED,
}


@dataclass(frozen=True)
class VerifiedAppleTransaction:
    transaction_id: str
    original_transaction_id: str
    product_id: str
    kind: str
    environment: str
    purchased_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    signed_at: datetime
    upgraded: bool


@dataclass(frozen=True)
class VerifiedAppleNotification:
    transaction: VerifiedAppleTransaction
    event_at: datetime
    subscription: SubscriptionUpdate | None = None
    revoked: bool = False


def resolve_apple_product(product_id: str) -> AppleProduct:
    product = APPLE_PRODUCTS.get(product_id)
    if product is None:
        raise AppleStoreKitInvalid("Unknown Apple product.")
    return product


def _configured_environments() -> tuple[Environment, ...]:
    values = {value.strip() for value in settings.APPLE_STOREKIT_ENVIRONMENTS.split(",")}
    # The Production notification verifier checks appAppleId before environment.
    # Start with Sandbox when allowed, then fully verify Production on a signed mismatch.
    supported = (Environment.SANDBOX, Environment.PRODUCTION)
    if not values <= {environment.value for environment in supported}:
        raise AppleStoreKitUnavailable("Unsupported Apple StoreKit environment.")
    return tuple(environment for environment in supported if environment.value in values)


def _verify_in_configured_environment(method, signed):
    for environment in _configured_environments():
        verifier = _configured_verifier(environment)
        try:
            decoded = _verify(getattr(verifier, method), signed, allow_environment_mismatch=True)
        except VerificationException:
            # SDK v3.1.2 emits INVALID_ENVIRONMENT after signature and chain checks.
            continue
        return decoded, verifier, environment
    raise AppleStoreKitInvalid("Apple signed environment is not enabled.")


@lru_cache(maxsize=4)
def _verifier(
    environment: Environment, root_paths: str, configured_app_id: str
) -> SignedDataVerifier:
    try:
        roots = [Path(path.strip()).read_bytes() for path in root_paths.split(",") if path.strip()]
        app_id = int(configured_app_id) if configured_app_id else None
        if not roots or (app_id is not None and app_id <= 0):
            raise ValueError
        return SignedDataVerifier(roots, True, environment, BUNDLE_ID, app_id)
    except (OSError, ValueError):
        raise AppleStoreKitUnavailable("Apple StoreKit verification is unconfigured.") from None


def _configured_verifier(environment: Environment) -> SignedDataVerifier:
    return _verifier(
        environment, settings.APPLE_STOREKIT_ROOT_CERTIFICATES, settings.APPLE_STOREKIT_APP_ID
    )


def _verify(decode, signed, *, allow_environment_mismatch=False):
    try:
        return decode(signed)
    except VerificationException as exc:
        if allow_environment_mismatch and exc.status == VerificationStatus.INVALID_ENVIRONMENT:
            raise
        if exc.status == VerificationStatus.RETRYABLE_VERIFICATION_FAILURE:
            raise AppleStoreKitUnavailable(
                "Apple verification is temporarily unavailable."
            ) from None
        raise AppleStoreKitInvalid("Invalid Apple signature.") from None
    except (BaseValidationError, ValueError, TypeError):
        raise AppleStoreKitInvalid("Malformed Apple payload.") from None


def _datetime(value: int) -> datetime:
    if type(value) is not int or value <= 0:
        raise AppleStoreKitInvalid("Invalid Apple timestamp.")
    seconds, milliseconds = divmod(value, 1000)
    try:
        return datetime.fromtimestamp(seconds, tz=utc_timezone.utc).replace(
            microsecond=milliseconds * 1000
        )
    except (ValueError, OverflowError, OSError):
        raise AppleStoreKitInvalid("Invalid Apple timestamp.") from None


def _normalize_transaction(decoded, environment) -> VerifiedAppleTransaction:
    if decoded.bundleId != BUNDLE_ID or decoded.environment != environment:
        raise AppleStoreKitInvalid("Apple bundle or environment does not match.")
    product = resolve_apple_product(decoded.productId)
    ids = (decoded.transactionId, decoded.originalTransactionId)
    if any(
        not value or not value.isascii() or not value.isdecimal() or len(value) > 255
        for value in ids
    ):
        raise AppleStoreKitInvalid("Invalid Apple transaction identity.")
    purchased_at = _datetime(decoded.purchaseDate)
    expires_at = _datetime(decoded.expiresDate) if decoded.expiresDate is not None else None
    if product.kind == "subscription" and (expires_at is None or expires_at <= purchased_at):
        raise AppleStoreKitInvalid("Invalid Apple subscription period.")
    return VerifiedAppleTransaction(
        transaction_id=decoded.transactionId,
        original_transaction_id=decoded.originalTransactionId,
        product_id=decoded.productId,
        kind=product.kind,
        environment=environment.value,
        purchased_at=purchased_at,
        expires_at=expires_at,
        revoked_at=_datetime(decoded.revocationDate)
        if decoded.revocationDate is not None
        else None,
        signed_at=_datetime(decoded.signedDate),
        upgraded=bool(decoded.isUpgraded),
    )


def verify_apple_transaction(signed: str) -> VerifiedAppleTransaction:
    decoded, _, environment = _verify_in_configured_environment(
        "verify_and_decode_signed_transaction", signed
    )
    return _normalize_transaction(decoded, environment)


def apple_subscription_update(
    purchase: VerifiedAppleTransaction,
    *,
    event_at: datetime,
    status: str | None = None,
    grace_end: datetime | None = None,
    auto_renew_enabled: bool | None = None,
) -> SubscriptionUpdate:
    end = purchase.expires_at
    if purchase.kind != "subscription" or end is None:
        raise AppleStoreKitInvalid("Missing Apple subscription expiry.")
    if purchase.revoked_at is not None or purchase.upgraded:
        status = PremiumSubscription.Status.REVOKED
    if status is None:
        status = (
            PremiumSubscription.Status.ACTIVE
            if end > timezone.now()
            else PremiumSubscription.Status.EXPIRED
        )
    if status == PremiumSubscription.Status.GRACE:
        if grace_end is None or grace_end < end:
            raise AppleStoreKitInvalid("Invalid Apple grace period.")
        end = grace_end
    return SubscriptionUpdate(
        source=PremiumSubscription.Source.APPLE,
        identity=purchase.original_transaction_id,
        product_id=purchase.product_id,
        environment=purchase.environment,
        status=status,
        period_start=purchase.purchased_at,
        period_end=end,
        event_at=event_at,
        auto_renew_enabled=auto_renew_enabled,
    )


def _subscription_notification(verifier, data, purchase, event_at):
    status = SUBSCRIPTION_STATUSES.get(data.status)
    if status is None and purchase.revoked_at is None:
        raise AppleStoreKitInvalid("Missing or unsupported Apple subscription status.")
    renew = None
    if data.signedRenewalInfo:
        renew = _verify(verifier.verify_and_decode_renewal_info, data.signedRenewalInfo)
        if (
            renew.originalTransactionId != purchase.original_transaction_id
            or renew.environment != purchase.environment
        ):
            raise AppleStoreKitInvalid("Apple renewal identity does not match the transaction.")
    grace_end = (
        _datetime(renew.gracePeriodExpiresDate)
        if renew is not None and renew.gracePeriodExpiresDate is not None
        else None
    )
    auto_renew = (
        bool(renew.autoRenewStatus)
        if renew is not None and renew.autoRenewStatus is not None
        else None
    )
    return apple_subscription_update(
        purchase,
        event_at=event_at,
        status=status,
        grace_end=grace_end,
        auto_renew_enabled=auto_renew,
    )


def verify_apple_notification(signed: str) -> VerifiedAppleNotification | None:
    decoded, verifier, environment = _verify_in_configured_environment(
        "verify_and_decode_notification", signed
    )
    if decoded.notificationType is None:
        raise AppleStoreKitInvalid("Unsupported Apple notification type.")
    if decoded.data is None or decoded.notificationType == NotificationTypeV2.TEST:
        # Summary and test notifications do not carry purchase state.
        return None
    data = decoded.data
    if not data.signedTransactionInfo:
        raise AppleStoreKitInvalid("Missing Apple notification transaction.")
    if data.bundleId != BUNDLE_ID or data.environment != environment:
        raise AppleStoreKitInvalid("Apple notification bundle or environment does not match.")
    transaction = _verify(verifier.verify_and_decode_signed_transaction, data.signedTransactionInfo)
    purchase = _normalize_transaction(transaction, environment)
    event_at = _datetime(decoded.signedDate)
    revoked = purchase.revoked_at is not None or decoded.notificationType in (
        NotificationTypeV2.REFUND,
        NotificationTypeV2.REVOKE,
    )
    if purchase.kind == "pass":
        return VerifiedAppleNotification(purchase, event_at, revoked=revoked)
    return VerifiedAppleNotification(
        purchase,
        event_at,
        subscription=_subscription_notification(verifier, data, purchase, event_at),
    )
