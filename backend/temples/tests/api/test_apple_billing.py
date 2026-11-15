from datetime import timedelta
from unittest.mock import Mock

import pytest
from appstoreserverlibrary.models.AutoRenewStatus import AutoRenewStatus
from appstoreserverlibrary.models.Data import Data
from appstoreserverlibrary.models.Environment import Environment
from appstoreserverlibrary.models.JWSRenewalInfoDecodedPayload import JWSRenewalInfoDecodedPayload
from appstoreserverlibrary.models.JWSTransactionDecodedPayload import JWSTransactionDecodedPayload
from appstoreserverlibrary.models.NotificationTypeV2 import NotificationTypeV2
from appstoreserverlibrary.models.ResponseBodyV2DecodedPayload import ResponseBodyV2DecodedPayload
from appstoreserverlibrary.models.Status import Status
from appstoreserverlibrary.signed_data_verifier import (
    SignedDataVerifier,
    VerificationException,
    VerificationStatus,
)
from django.utils import timezone
from rest_framework.test import APIClient
from temples.services.billing_state import get_billing_status
from users.models import AppleStoreKitReceipt, PremiumPassPurchase, PremiumSubscription, UserProfile
from users.services import apple_storekit
from users.services.apple_storekit import AppleStoreKitInvalid, resolve_apple_product
from users.services.premium_pass import get_pass_period_end, grant_premium_pass

PURCHASE = "/api/billings/apple/transactions/"
WEBHOOK = "/api/webhooks/apple/app-store/"
BUNDLE = "com.morietsu.kamimusubi"
MONTHLY = f"{BUNDLE}.premium.monthly"
ENVIRONMENT = Environment.SANDBOX

pytestmark = pytest.mark.django_db


def ms(value):
    return int(value.timestamp() * 1000)


@pytest.fixture
def now():
    return timezone.now().replace(microsecond=0)


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="apple-purchaser")


@pytest.fixture
def sdk(monkeypatch, settings):
    settings.APPLE_STOREKIT_ENVIRONMENT = ENVIRONMENT.value
    monkeypatch.setenv("BILLING_PROVIDER", "stripe")
    sdk = Mock(spec=SignedDataVerifier)
    monkeypatch.setattr(apple_storekit, "_configured_verifier", lambda environment: sdk)
    return sdk


def apple_transaction(
    now, *, product=MONTHLY, transaction_id="100", original_id="100", **overrides
):
    fields = {
        "bundleId": BUNDLE,
        "environment": ENVIRONMENT,
        "productId": product,
        "transactionId": transaction_id,
        "originalTransactionId": original_id,
        "purchaseDate": ms(now),
        "expiresDate": ms(now + timedelta(days=30)),
        "signedDate": ms(now),
    }
    fields.update(overrides)
    return JWSTransactionDecodedPayload(**fields)


def notification(sdk, *, time, status=None, kind=NotificationTypeV2.DID_RENEW, **overrides):
    fields = {
        "bundleId": BUNDLE,
        "environment": ENVIRONMENT,
        "signedTransactionInfo": "inner-jws",
        "rawStatus": status,
    }
    fields.update(overrides)
    sdk.verify_and_decode_notification.return_value = ResponseBodyV2DecodedPayload(
        rawNotificationType=kind,
        signedDate=ms(time),
        data=Data(**fields),
    )
    return APIClient().post(WEBHOOK, {"signedPayload": "outer-jws"}, format="json")


def claim(user, **fields):
    client = APIClient()
    client.force_authenticate(user)
    return client.post(PURCHASE, {"signed_transaction": "purchase-jws", **fields}, format="json")


@pytest.mark.parametrize(
    "suffix, pass_type, days", [("1day", "1d", 1), ("7day", "7d", 7), ("14day", "14d", 14)]
)
def test_catalog_and_apple_pass_grant_only_once(sdk, user, now, suffix, pass_type, days):
    product = f"{BUNDLE}.pass.{suffix}"
    definition = resolve_apple_product(product)
    assert definition.kind == "pass"
    assert (definition.travel_pass.pass_type, definition.travel_pass.days) == (pass_type, days)
    sdk.verify_and_decode_signed_transaction.return_value = apple_transaction(now, product=product)

    assert claim(user).data["plan"] == "premium"
    first = PremiumPassPurchase.objects.get(source="apple")
    assert claim(user).status_code == 200
    assert PremiumPassPurchase.objects.count() == 1
    assert (first.pass_type, first.days, first.period_end_after) == (
        pass_type,
        days,
        now + timedelta(days=days),
    )


def test_monthly_purchase_is_idempotent_and_cannot_move_between_users(
    sdk, user, now, django_user_model
):
    assert (resolve_apple_product(MONTHLY).kind, resolve_apple_product(MONTHLY).entitlement) == (
        "subscription",
        "premium",
    )
    with pytest.raises(AppleStoreKitInvalid):
        resolve_apple_product("unknown.apple.product")
    sdk.verify_and_decode_signed_transaction.return_value = apple_transaction(now)
    response = claim(user)

    assert response.status_code == 200
    assert response.data["plan"] == "premium"
    row = PremiumSubscription.objects.get()
    assert claim(user).status_code == 200
    assert claim(django_user_model.objects.create_user(username="other")).status_code == 409
    row.refresh_from_db()
    assert row.user_id == user.pk
    assert row.last_event_at == now
    assert row.current_period_end == now + timedelta(days=30)
    assert row.source == "apple"
    assert row.original_transaction_id == "100"
    assert row.status == "active"


def test_authentication_and_strict_signed_input(sdk, user):
    assert (
        APIClient()
        .post(PURCHASE, {"signed_transaction": "purchase-jws"}, format="json")
        .status_code
        == 401
    )
    for extra in (
        {"days": 999},
        {"user_id": user.pk},
        {"premium": True},
        {"entitlement_type": "premium"},
        {"expires_at": "2099-01-01"},
    ):
        assert claim(user, **extra).status_code == 400
    sdk.verify_and_decode_signed_transaction.assert_not_called()


@pytest.mark.parametrize(
    "overrides",
    [
        {"bundleId": "unrelated.bundle"},
        {"environment": Environment.PRODUCTION},
        {"productId": "unknown"},
    ],
)
def test_invalid_verified_transaction_fields_fail_closed(sdk, user, now, overrides):
    sdk.verify_and_decode_signed_transaction.return_value = apple_transaction(now, **overrides)

    assert claim(user).status_code == 400
    assert not PremiumSubscription.objects.exists()
    assert not PremiumPassPurchase.objects.exists()


def test_invalid_jws_is_rejected_by_real_apple_sdk(sdk, user, monkeypatch):
    verifier = SignedDataVerifier([], True, ENVIRONMENT, BUNDLE)
    monkeypatch.setattr(apple_storekit, "_configured_verifier", lambda environment: verifier)

    assert claim(user).status_code == 400
    assert APIClient().post(WEBHOOK, {"signedPayload": "garbage"}, format="json").status_code == 400
    assert not AppleStoreKitReceipt.objects.exists()


def test_production_never_accepts_sandbox_transaction(sdk, user, now, settings):
    settings.APPLE_STOREKIT_ENVIRONMENT = "Production"
    sdk.verify_and_decode_signed_transaction.return_value = apple_transaction(now)

    assert claim(user).status_code == 400
    assert not PremiumSubscription.objects.exists()


@pytest.mark.parametrize(
    "apple_status, stored_status, premium",
    [
        (Status.BILLING_RETRY, "billing_retry", False),
        (Status.EXPIRED, "expired", False),
        (Status.REVOKED, "revoked", False),
        (Status.BILLING_GRACE_PERIOD, "grace", True),
    ],
)
def test_notifications_normalize_state_verify_inner_signatures_and_prevent_rollback(
    sdk,
    user,
    now,
    apple_status,
    stored_status,
    premium,
):
    tx = apple_transaction(now)
    sdk.verify_and_decode_signed_transaction.return_value = tx
    assert claim(user).status_code == 200
    grace_end = now + timedelta(days=33)
    sdk.verify_and_decode_renewal_info.return_value = JWSRenewalInfoDecodedPayload(
        originalTransactionId="100",
        rawEnvironment=ENVIRONMENT,
        rawAutoRenewStatus=AutoRenewStatus.ON,
        gracePeriodExpiresDate=ms(grace_end),
    )
    event = {
        "time": now + timedelta(minutes=2),
        "status": apple_status,
        "signedRenewalInfo": "renewal-jws",
    }

    assert notification(sdk, **event).status_code == 200
    stored = PremiumSubscription.objects.values().get()
    assert stored["status"] == stored_status
    assert stored["auto_renew_enabled"]
    assert get_billing_status(user=user, now=now).is_active is premium
    if premium:
        assert stored["current_period_end"] == grace_end

    assert notification(sdk, **event).status_code == 200
    assert (
        notification(sdk, time=now + timedelta(minutes=1), status=Status.ACTIVE).status_code == 200
    )
    # A re-signed copy of the same purchase cannot replace authoritative notification state.
    tx.signedDate = ms(now + timedelta(minutes=3))
    assert claim(user).status_code == 200
    assert PremiumSubscription.objects.values().get() == stored
    sdk.verify_and_decode_renewal_info.assert_called_with("renewal-jws")
    assert any(
        call.args == ("inner-jws",)
        for call in sdk.verify_and_decode_signed_transaction.call_args_list
    )


def test_newer_renewal_ignores_a_later_refund_for_an_older_period(sdk, user, now):
    old = apple_transaction(now)
    sdk.verify_and_decode_signed_transaction.return_value = old
    assert claim(user).status_code == 200
    renew_at = now + timedelta(days=30)
    sdk.verify_and_decode_signed_transaction.return_value = apple_transaction(
        renew_at,
        transaction_id="101",
        original_id="100",
    )
    assert notification(sdk, time=renew_at, status=Status.ACTIVE).status_code == 200

    sdk.verify_and_decode_signed_transaction.return_value = old
    assert (
        notification(sdk, time=renew_at + timedelta(days=1), status=Status.REVOKED).status_code
        == 200
    )
    row = PremiumSubscription.objects.get()
    assert row.current_period_start == renew_at
    assert row.status == "active"


def test_unknown_subscription_is_acknowledged_without_inventing_ownership(
    sdk, now, django_user_model, user
):
    sdk.verify_and_decode_signed_transaction.return_value = apple_transaction(now)
    before = django_user_model.objects.count()

    assert (
        notification(sdk, time=now + timedelta(seconds=5), status=Status.REVOKED).status_code == 200
    )
    assert django_user_model.objects.count() == before
    assert not PremiumSubscription.objects.exists()

    assert claim(user).data["plan"] == "free"
    assert PremiumSubscription.objects.get().status == "revoked"


def test_invalid_inner_transaction_and_retryable_verification_failure(sdk, now):
    sdk.verify_and_decode_signed_transaction.side_effect = VerificationException(
        VerificationStatus.INVALID_CHAIN
    )
    assert notification(sdk, time=now, status=Status.ACTIVE).status_code == 400

    sdk.verify_and_decode_notification.side_effect = VerificationException(
        VerificationStatus.RETRYABLE_VERIFICATION_FAILURE,
    )
    assert notification(sdk, time=now, status=Status.ACTIVE).status_code == 503
    assert not AppleStoreKitReceipt.objects.exists()


def test_pass_refund_keeps_history_and_preserves_stripe_behavior(sdk, user, now):
    spec = apple_transaction(now, product=f"{BUNDLE}.pass.7day")
    sdk.verify_and_decode_signed_transaction.return_value = spec
    assert claim(user).status_code == 200
    stripe = grant_premium_pass(
        user=user, days=1, source="stripe", external_id="stripe-pass", now=now
    )
    assert stripe.period_end == now + timedelta(days=8)

    for _ in range(2):
        assert notification(sdk, time=now, kind=NotificationTypeV2.REFUND).status_code == 200
    assert claim(user).status_code == 200
    apple = PremiumPassPurchase.objects.get(source="apple")
    assert apple.status == "refunded"
    assert apple.period_end_after == now + timedelta(days=7)
    assert get_pass_period_end(user_id=user.pk) == now + timedelta(days=1)


def test_refund_before_first_pass_registration_cannot_be_replayed(sdk, user, now):
    sdk.verify_and_decode_signed_transaction.return_value = apple_transaction(
        now, product=f"{BUNDLE}.pass.14day"
    )
    assert notification(sdk, time=now, kind=NotificationTypeV2.REFUND).status_code == 200

    assert claim(user).data["plan"] == "free"
    assert not PremiumPassPurchase.objects.exists()


def test_disabled_account_wins_over_verified_purchase_and_legacy(sdk, user, now):
    UserProfile.objects.filter(user=user).update(
        account_entitlement_disabled=True,
        legacy_premium_until=now + timedelta(days=60),
    )
    sdk.verify_and_decode_signed_transaction.return_value = apple_transaction(now)

    assert claim(user).data["plan"] == "free"
    assert PremiumSubscription.objects.get().status == "active"


def test_expired_or_revoked_direct_claim_cannot_grant_premium(sdk, user, now):
    sdk.verify_and_decode_signed_transaction.return_value = apple_transaction(
        now - timedelta(days=31)
    )
    assert claim(user).data["plan"] == "free"
    assert PremiumSubscription.objects.get().status == "expired"

    sdk.verify_and_decode_signed_transaction.return_value = apple_transaction(
        now,
        transaction_id="200",
        original_id="200",
        revocationDate=ms(now),
    )
    assert claim(user).data["plan"] == "free"
    assert PremiumSubscription.objects.get(original_transaction_id="200").status == "revoked"


def test_receipt_from_earlier_pass_stack_does_not_shorten_new_pass(sdk, user, now):
    sdk.verify_and_decode_signed_transaction.return_value = apple_transaction(
        now - timedelta(days=4),
        product=f"{BUNDLE}.pass.1day",
    )
    assert claim(user).data["plan"] == "free"
    newer = grant_premium_pass(
        user=user, days=7, source="stripe", external_id="newer-pass", now=now
    )

    assert notification(sdk, time=now, kind=NotificationTypeV2.REFUND).status_code == 200
    assert PremiumPassPurchase.objects.get(source="apple").status == "refunded"
    assert get_pass_period_end(user_id=user.pk) == newer.period_end


def test_missing_signed_transaction_cannot_apply_notification(sdk, now):
    assert (
        notification(sdk, time=now, status=Status.ACTIVE, signedTransactionInfo=None).status_code
        == 400
    )
    assert not AppleStoreKitReceipt.objects.exists()
