"""期限を延ばす・戻す関数（users.services.premium_pass）の契約。"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from users.models import PremiumPassPurchase, UserProfile
from users.services.premium_pass import (
    PASS_DEFINITIONS,
    get_pass_definition,
    get_pass_period_end,
    grant_premium_pass,
    revoke_premium_pass_for_refund,
)


def _user(name="pass-service-user"):
    return get_user_model().objects.create_user(username=name)


def test_pass_definitions_are_1_7_14_days():
    assert {key: value.days for key, value in PASS_DEFINITIONS.items()} == {"1d": 1, "7d": 7, "14d": 14}
    assert get_pass_definition("7d").days == 7
    assert get_pass_definition("30d") is None
    assert get_pass_definition(None) is None


@pytest.mark.django_db
def test_grant_from_now_when_no_period():
    user = _user()
    now = timezone.now()

    result = grant_premium_pass(user=user, days=1, source="stripe", external_id="cs_1", now=now)

    assert result.applied is True
    assert result.period_end == now + timedelta(hours=24)
    profile = UserProfile.objects.get(user=user)
    assert profile.current_period_end is None
    assert profile.subscription_status == "inactive"
    assert get_pass_period_end(user_id=user.pk) == result.period_end


@pytest.mark.django_db
def test_grant_adds_to_a_future_period_and_records_before_after():
    user = _user()
    now = timezone.now()
    future = now + timedelta(days=3)
    grant_premium_pass(
        user=user, days=3, source="apple", environment="Production", external_id="previous", now=now,
    )

    grant_premium_pass(user=user, days=7, source="stripe", external_id="cs_1", pass_type="7d", now=now)

    purchase = PremiumPassPurchase.objects.get(user=user, source="stripe")
    assert purchase.period_end_before == future
    assert purchase.period_end_after == future + timedelta(days=7)


@pytest.mark.django_db
def test_grant_is_idempotent_per_source_and_external_id():
    user = _user()
    now = timezone.now()
    first = grant_premium_pass(user=user, days=7, source="stripe", external_id="cs_1", now=now)

    again = grant_premium_pass(user=user, days=7, source="stripe", external_id="cs_1", now=now)
    other_source = grant_premium_pass(
        user=user, days=1, source="apple", environment="Production", external_id="cs_1", now=now,
    )

    assert again.applied is False
    assert again.period_end == first.period_end
    assert other_source.applied is True
    assert other_source.period_end == first.period_end + timedelta(days=1)
    assert PremiumPassPurchase.objects.filter(user=user).count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize("kwargs", [{"days": 0}, {"days": -1}, {"external_id": ""}, {"source": ""}])
def test_grant_rejects_invalid_arguments(kwargs):
    user = _user()
    params = {"user": user, "days": 1, "source": "stripe", "external_id": "cs_1", **kwargs}

    with pytest.raises(ValueError):
        grant_premium_pass(**params)


@pytest.mark.django_db
def test_refund_preserves_subscription_and_legacy_deadlines():
    user = _user()
    now = timezone.now()
    grant_premium_pass(user=user, days=1, source="stripe", external_id="cs_1", payment_intent_id="pi_1", now=now)
    subscription_end = now + timedelta(days=30)
    legacy_end = now + timedelta(days=10)
    UserProfile.objects.filter(user=user).update(
        current_period_end=subscription_end, legacy_premium_until=legacy_end,
        subscription_status="active", cancel_at_period_end=True,
    )

    result = revoke_premium_pass_for_refund(source="stripe", payment_intent_id="pi_1", now=now)

    assert result.applied is True
    profile = UserProfile.objects.get(user=user)
    assert profile.current_period_end == subscription_end
    assert profile.legacy_premium_until == legacy_end
    assert profile.subscription_status == "active"
    assert profile.cancel_at_period_end is True
    assert get_pass_period_end(user_id=user.pk) is None


@pytest.mark.django_db
def test_refund_clamps_to_now():
    user = _user()
    now = timezone.now()
    grant_premium_pass(user=user, days=1, source="stripe", external_id="cs_1", payment_intent_id="pi_1", now=now)

    result = revoke_premium_pass_for_refund(source="stripe", payment_intent_id="pi_1", now=now + timedelta(hours=1))

    assert result.period_end == now + timedelta(hours=1)


@pytest.mark.django_db
@pytest.mark.parametrize("refunded, remaining_days", [("first", 7), ("second", 1)])
def test_refund_preserves_purchase_history_and_reduces_the_stack(refunded, remaining_days):
    user = _user()
    now = timezone.now()
    first = grant_premium_pass(
        user=user, days=1, source="stripe", external_id="first", payment_intent_id="first", now=now,
    )
    second = grant_premium_pass(
        user=user, days=7, source="stripe", external_id="second", payment_intent_id="second", now=now,
    )
    expected = now + timedelta(days=remaining_days)

    result = revoke_premium_pass_for_refund(source="stripe", payment_intent_id=refunded, now=now)
    repeated = revoke_premium_pass_for_refund(source="stripe", payment_intent_id=refunded, now=now)

    assert result.applied and result.period_end == expected
    assert not repeated.applied
    assert get_pass_period_end(user_id=user.pk) == expected
    purchase = PremiumPassPurchase.objects.get(external_id="second")
    assert purchase.period_end_before == first.period_end
    assert purchase.period_end_after == second.period_end

    next_pass = grant_premium_pass(user=user, days=14, source="stripe", external_id="third", now=now)
    assert next_pass.period_end == expected + timedelta(days=14)
