"""期限を延ばす・戻す関数（users.services.premium_pass）の契約。"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from users.models import PremiumPassPurchase, UserProfile
from users.services.billing import is_subscription_active
from users.services.premium_pass import (
    PASS_DEFINITIONS,
    get_pass_definition,
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
    assert profile.current_period_end == now + timedelta(hours=24)
    assert profile.subscription_status == "active"
    assert is_subscription_active(
        status=profile.subscription_status, current_period_end=profile.current_period_end, now=now
    )


@pytest.mark.django_db
def test_grant_adds_to_a_future_period_and_records_before_after():
    user = _user()
    now = timezone.now()
    future = now + timedelta(days=3)
    UserProfile.objects.update_or_create(user=user, defaults={"current_period_end": future})

    grant_premium_pass(user=user, days=7, source="stripe", external_id="cs_1", pass_type="7d", now=now)

    purchase = PremiumPassPurchase.objects.get(user=user)
    assert purchase.period_end_before == future
    assert purchase.period_end_after == future + timedelta(days=7)


@pytest.mark.django_db
def test_grant_is_idempotent_per_source_and_external_id():
    user = _user()
    now = timezone.now()
    first = grant_premium_pass(user=user, days=7, source="stripe", external_id="cs_1", now=now)

    again = grant_premium_pass(user=user, days=7, source="stripe", external_id="cs_1", now=now)
    other_source = grant_premium_pass(user=user, days=1, source="apple", external_id="cs_1", now=now)

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
def test_refund_without_period_end_does_not_leave_premium_active():
    user = _user()
    now = timezone.now()
    grant_premium_pass(user=user, days=1, source="stripe", external_id="cs_1", payment_intent_id="pi_1", now=now)
    UserProfile.objects.filter(user=user).update(current_period_end=None)

    result = revoke_premium_pass_for_refund(source="stripe", payment_intent_id="pi_1", now=now)

    assert result.applied is True
    profile = UserProfile.objects.get(user=user)
    assert not is_subscription_active(
        status=profile.subscription_status, current_period_end=profile.current_period_end, now=now
    )


@pytest.mark.django_db
def test_refund_clamps_to_now():
    user = _user()
    now = timezone.now()
    grant_premium_pass(user=user, days=1, source="stripe", external_id="cs_1", payment_intent_id="pi_1", now=now)

    result = revoke_premium_pass_for_refund(source="stripe", payment_intent_id="pi_1", now=now + timedelta(hours=1))

    assert result.period_end == now + timedelta(hours=1)
