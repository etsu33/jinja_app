"""Account Deletion service の契約。

実 Stripe / R2 / Production DB へは接続しない。Stripe は mock する。
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from temples.models import (
    ActionEvent,
    ConciergeMessage,
    ConciergeRecommendationLog,
    ConciergeThread,
    ConciergeUsage,
    Favorite,
    FeatureUsage,
    Goshuin,
    GoshuinImage,
    Shrine,
    ShrineInteractionLog,
    ShrineReflection,
    ShrineSubmission,
    Visit,
    WeeklyPresentationSnapshot,
)
from tests.factories import UserFactory
from users.models import UserProfile
from users.services.account_deletion import (
    AccountDataDeletionFailed,
    BillingCleanupFailed,
    BillingCustomerCleanupFailed,
    BillingStateSyncFailed,
    delete_user_account,
)

pytestmark = pytest.mark.django_db


def _shrine(name="テスト神社"):
    return Shrine.objects.create(
        name_jp=name, address="東京都千代田区1-1", latitude=35.6812, longitude=139.7671
    )


def _profile(user, **fields):
    profile = UserProfile.objects.get(user=user)
    if fields:
        UserProfile.objects.filter(pk=profile.pk).update(**fields)
        profile.refresh_from_db()
    return profile


def _stripe_mock(*, subscription=None, customer_of=None):
    mock = MagicMock()
    mock.Subscription.retrieve.return_value = subscription if subscription is not None else {
        "id": "sub_x",
        "customer": customer_of or "cus_x",
        "status": "active",
    }
    return mock


def _patch_stripe(mock):
    """service が使う import 経路（関数内 import stripe）を差し替える。"""
    return patch.dict("sys.modules", {"stripe": mock})


# ---------------------------------------------------------------- Free User


def test_free_user_without_stripe_ids_is_deleted_without_calling_stripe(settings):
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = UserFactory()
    stripe = MagicMock()

    with _patch_stripe(stripe):
        result = delete_user_account(user=user)

    assert result.account_deleted is True
    assert result.billing_cleanup_performed is False
    stripe.Subscription.retrieve.assert_not_called()
    stripe.Subscription.cancel.assert_not_called()
    stripe.Customer.delete.assert_not_called()
    assert not UserProfile.objects.filter(user_id=user.pk).exists()


def test_personal_cascade_data_is_deleted(settings):
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = UserFactory()
    shrine = _shrine()
    thread = ConciergeThread.objects.create(user=user)
    ConciergeMessage.objects.create(thread=thread, role="user", content="x")
    Favorite.objects.create(user=user, shrine=shrine)
    Visit.objects.create(user=user, shrine=shrine)
    ShrineReflection.objects.create(user=user, shrine=shrine)
    ActionEvent.objects.create(user=user, action_type="view")
    ShrineInteractionLog.objects.create(
        user=user, shrine=shrine, action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW
    )
    goshuin = Goshuin.objects.create(user=user, shrine=shrine)
    GoshuinImage.objects.create(goshuin=goshuin)
    ConciergeUsage.objects.create(user=user, date=timezone.now().date())
    FeatureUsage.objects.create(
        scope=FeatureUsage.Scope.USER, user=user, feature=FeatureUsage.Feature.CONCIERGE
    )
    WeeklyPresentationSnapshot.objects.create(
        user=user,
        week_start=timezone.now().date(),
        purpose="work",
        direction_fingerprint="f" * 64,
        presentation_version="v1",
    )
    ShrineSubmission.objects.create(user=user, name="申請神社", address="東京都1-1")

    delete_user_account(user=user)

    assert ConciergeThread.objects.count() == 0
    assert ConciergeMessage.objects.count() == 0
    assert Favorite.objects.count() == 0
    assert Visit.objects.count() == 0
    assert ShrineReflection.objects.count() == 0
    assert ActionEvent.objects.count() == 0
    assert ShrineInteractionLog.objects.count() == 0
    assert Goshuin.objects.count() == 0
    assert GoshuinImage.objects.count() == 0
    assert ConciergeUsage.objects.count() == 0
    assert FeatureUsage.objects.count() == 0
    assert WeeklyPresentationSnapshot.objects.count() == 0
    assert ShrineSubmission.objects.count() == 0


# ------------------------------------------------------- RecommendationLog


def test_recommendation_logs_owned_by_the_user_are_deleted(settings):
    user = UserFactory()
    ConciergeRecommendationLog.objects.create(user=user, query="mine")

    result = delete_user_account(user=user)

    assert ConciergeRecommendationLog.objects.count() == 0
    assert result.recommendation_logs_deleted == 1


def test_anonymous_logs_attached_to_the_users_thread_are_deleted(settings):
    user = UserFactory()
    thread = ConciergeThread.objects.create(user=user)
    ConciergeRecommendationLog.objects.create(user=None, thread=thread, query="anon-on-my-thread")

    result = delete_user_account(user=user)

    assert ConciergeRecommendationLog.objects.count() == 0
    assert result.recommendation_logs_deleted == 1


def test_logs_owned_by_another_user_are_kept(settings):
    user = UserFactory()
    other = UserFactory()
    other_log = ConciergeRecommendationLog.objects.create(user=other, query="theirs")
    other_thread_log = ConciergeRecommendationLog.objects.create(
        user=None, thread=ConciergeThread.objects.create(user=other), query="their-anon"
    )

    delete_user_account(user=user)

    assert ConciergeRecommendationLog.objects.filter(pk=other_log.pk).exists()
    assert ConciergeRecommendationLog.objects.filter(pk=other_thread_log.pk).exists()


def test_no_orphan_recommendation_log_remains_after_deletion(settings):
    """user=NULL かつ thread=NULL の孤児が残らないこと。"""
    user = UserFactory()
    thread = ConciergeThread.objects.create(user=user)
    ConciergeRecommendationLog.objects.create(user=user, thread=thread, query="a")
    ConciergeRecommendationLog.objects.create(user=None, thread=thread, query="b")

    delete_user_account(user=user)

    assert (
        ConciergeRecommendationLog.objects.filter(user__isnull=True, thread__isnull=True).count()
        == 0
    )


# -------------------------------------------------------------- Shared data


def test_shared_master_data_survives_and_owner_becomes_null(settings):
    user = UserFactory()
    other = UserFactory()
    shrine = _shrine()
    Shrine.objects.filter(pk=shrine.pk).update(owner=user)
    other_submission = ShrineSubmission.objects.create(
        user=other, name="他ユーザー申請", address="東京都2-2", reviewed_by=user
    )

    delete_user_account(user=user)

    shrine.refresh_from_db()
    assert Shrine.objects.filter(pk=shrine.pk).exists()
    assert shrine.owner_id is None

    other_submission.refresh_from_db()
    assert ShrineSubmission.objects.filter(pk=other_submission.pk).exists()
    assert other_submission.reviewed_by_id is None
    assert other_submission.user_id == other.pk


# ------------------------------------------------------------------ Tokens


def test_outstanding_tokens_are_blacklisted_and_survive_user_deletion(settings):
    user = UserFactory()
    RefreshToken.for_user(user)
    token = OutstandingToken.objects.get(user=user)

    result = delete_user_account(user=user)

    assert result.tokens_blacklisted == 1
    # 失効の証跡は User 削除後も残る（OutstandingToken.user は SET_NULL）
    token.refresh_from_db()
    assert token.user_id is None
    assert BlacklistedToken.objects.filter(token=token).exists()


def test_blacklisting_is_safe_when_already_blacklisted(settings):
    user = UserFactory()
    refresh = RefreshToken.for_user(user)
    refresh.blacklist()

    result = delete_user_account(user=user)

    assert result.tokens_blacklisted == 0
    assert BlacklistedToken.objects.count() == 1


def test_other_users_tokens_are_untouched(settings):
    user = UserFactory()
    other = UserFactory()
    RefreshToken.for_user(user)
    RefreshToken.for_user(other)

    delete_user_account(user=user)

    other_token = OutstandingToken.objects.get(user=other)
    assert not BlacklistedToken.objects.filter(token=other_token).exists()
    assert other_token.user_id == other.pk


def test_refresh_token_cannot_be_reused_after_deletion(settings):
    """blacklist 済み jti は検証を通らない。"""
    from rest_framework_simplejwt.exceptions import TokenError

    user = UserFactory()
    refresh = RefreshToken.for_user(user)
    raw = str(refresh)

    delete_user_account(user=user)

    with pytest.raises(TokenError):
        RefreshToken(raw).check_blacklist()


# ------------------------------------------------------------------ Stripe


def _stripe_error(code=None):
    """Stripe の例外形だけを再現する（SDK の内部実装には依存しない）。"""
    exc = Exception("stripe failure: cus_SECRET sub_SECRET sk_live_SECRET")
    exc.code = code
    return exc


def _premium_user(sub="sub_1", cus="cus_1"):
    user = UserFactory()
    _profile(
        user,
        stripe_subscription_id=sub,
        stripe_customer_id=cus,
        subscription_status="active",
        current_period_end=timezone.now() + timedelta(days=20),
        cancel_at_period_end=False,
    )
    return user


def test_subscription_is_cancelled_immediately_and_customer_deleted(settings):
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = _premium_user()
    stripe = _stripe_mock()

    with _patch_stripe(stripe):
        result = delete_user_account(user=user)

    stripe.Subscription.cancel.assert_called_once_with("sub_1")
    stripe.Customer.delete.assert_called_once_with("cus_1")
    assert result.billing_cleanup_performed is True
    assert result.account_deleted is True


def test_cancel_does_not_use_period_end_or_proration_or_refund(settings):
    """将来請求の停止を優先する。日割り返金・proration は行わない。"""
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = _premium_user()
    stripe = _stripe_mock()

    with _patch_stripe(stripe):
        delete_user_account(user=user)

    # cancel_at_period_end / proration 系の引数を渡していない
    _, kwargs = stripe.Subscription.cancel.call_args
    assert kwargs == {}
    stripe.Subscription.modify.assert_not_called()
    stripe.Refund.create.assert_not_called()
    stripe.InvoiceItem.create.assert_not_called()


def test_subscription_only_profile_discovers_customer_from_stripe(settings):
    """customer_id が無くても、ID を推測せず Stripe から取得する。"""
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = UserFactory()
    _profile(user, stripe_subscription_id="sub_2", stripe_customer_id="")
    stripe = _stripe_mock(subscription={"id": "sub_2", "customer": "cus_found", "status": "active"})

    with _patch_stripe(stripe):
        delete_user_account(user=user)

    stripe.Customer.delete.assert_called_once_with("cus_found")


def test_already_canceled_subscription_is_idempotent(settings):
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = _premium_user()
    stripe = _stripe_mock(subscription={"id": "sub_1", "customer": "cus_1", "status": "canceled"})

    with _patch_stripe(stripe):
        result = delete_user_account(user=user)

    stripe.Subscription.cancel.assert_not_called()
    assert result.account_deleted is True


def test_already_deleted_stripe_resources_are_idempotent(settings):
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = _premium_user()
    stripe = MagicMock()
    stripe.Subscription.retrieve.side_effect = _stripe_error(code="resource_missing")
    stripe.Customer.delete.side_effect = _stripe_error(code="resource_missing")

    with _patch_stripe(stripe):
        result = delete_user_account(user=user)

    assert result.account_deleted is True


def test_unexpected_stripe_error_fails_closed(settings):
    """network / auth / timeout は success 扱いしない。DB を一切触らない。"""
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = _premium_user()
    RefreshToken.for_user(user)
    log = ConciergeRecommendationLog.objects.create(user=user, query="mine")
    stripe = MagicMock()
    stripe.Subscription.retrieve.side_effect = _stripe_error(code=None)

    with _patch_stripe(stripe):
        with pytest.raises(BillingCleanupFailed):
            delete_user_account(user=user)

    assert type(user).objects.filter(pk=user.pk).exists()
    assert ConciergeRecommendationLog.objects.filter(pk=log.pk).exists()
    assert BlacklistedToken.objects.count() == 0
    assert UserProfile.objects.filter(user=user).exists()


def test_missing_stripe_secret_fails_closed_for_a_stripe_linked_user(settings):
    """請求停止を確認する手段が無いなら進まない。"""
    settings.STRIPE_SECRET_KEY = ""
    user = _premium_user()

    with pytest.raises(BillingCleanupFailed):
        delete_user_account(user=user)

    assert type(user).objects.filter(pk=user.pk).exists()


def test_stripe_failure_log_contains_no_ids_or_secrets(settings, caplog):
    import logging

    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = _premium_user()
    stripe = MagicMock()
    stripe.Subscription.retrieve.side_effect = _stripe_error(code=None)

    with _patch_stripe(stripe):
        with caplog.at_level(logging.ERROR, logger="users.services.account_deletion"):
            with pytest.raises(BillingCleanupFailed):
                delete_user_account(user=user)

    message = caplog.records[0].getMessage()
    for secret in ("cus_", "sub_", "sk_live", "sk_test", user.email):
        assert secret not in message
    assert "stripe subscription cancel failed" in message


# ------------------------------------------------------- partial failure


def test_db_failure_after_stripe_cleanup_keeps_the_account_but_not_premium(settings):
    """外部APIとDBは同一transactionにできない。その partial failure の契約。"""
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = _premium_user()
    stripe = _stripe_mock()

    with _patch_stripe(stripe):
        with patch(
            "users.services.account_deletion._delete_recommendation_logs",
            side_effect=RuntimeError("db boom"),
        ):
            with pytest.raises(AccountDataDeletionFailed):
                delete_user_account(user=user)

    # Stripe は停止済み。Account は残る。成功として返さない。
    assert type(user).objects.filter(pk=user.pk).exists()
    stripe.Subscription.cancel.assert_called_once_with("sub_1")

    # billing mirror は Premium active へ戻らない
    profile = UserProfile.objects.get(user=user)
    assert profile.subscription_status == "canceled"
    assert profile.current_period_end is None
    assert profile.cancel_at_period_end is False


def test_db_failure_does_not_blacklist_or_delete_rows(settings):
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = _premium_user()
    RefreshToken.for_user(user)
    log = ConciergeRecommendationLog.objects.create(user=user, query="mine")
    stripe = _stripe_mock()

    with _patch_stripe(stripe):
        with patch.object(type(user), "delete", side_effect=RuntimeError("db boom")):
            with pytest.raises(AccountDataDeletionFailed):
                delete_user_account(user=user)

    # transaction rollback により blacklist も log 削除も巻き戻る
    assert BlacklistedToken.objects.count() == 0
    assert ConciergeRecommendationLog.objects.filter(pk=log.pk).exists()


# ------------------------------------------- Stripe partial failure (phase B)


def test_customer_delete_failure_keeps_the_account_but_stops_future_charges(settings):
    """Subscription cancel 成功 → Customer delete 失敗。

    将来請求は止まっている。Account は消さず、retry 可能な例外を返す。
    Account を先に消すと Stripe の customer を消す手がかりが DB から失われる。
    """
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = _premium_user()
    log = ConciergeRecommendationLog.objects.create(user=user, query="mine")
    RefreshToken.for_user(user)
    stripe = _stripe_mock()
    stripe.Customer.delete.side_effect = _stripe_error(code=None)

    with _patch_stripe(stripe):
        with pytest.raises(BillingCustomerCleanupFailed):
            delete_user_account(user=user)

    # 将来請求は停止済み
    stripe.Subscription.cancel.assert_called_once_with("sub_1")
    # Account 本体は残る
    assert type(user).objects.filter(pk=user.pk).exists()
    assert ConciergeRecommendationLog.objects.filter(pk=log.pk).exists()
    assert BlacklistedToken.objects.count() == 0


def test_customer_delete_failure_still_leaves_billing_mirror_canceled(settings):
    """課金が止まった事実は、Customer 削除の成否と無関係に確定させる。"""
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = _premium_user()
    stripe = _stripe_mock()
    stripe.Customer.delete.side_effect = _stripe_error(code=None)

    with _patch_stripe(stripe):
        with pytest.raises(BillingCustomerCleanupFailed):
            delete_user_account(user=user)

    profile = UserProfile.objects.get(user=user)
    assert profile.subscription_status == "canceled"
    assert profile.current_period_end is None
    assert profile.cancel_at_period_end is False


def test_retry_after_customer_delete_failure_is_idempotent(settings):
    """retry 時、既に canceled な Subscription へ cancel を投げ直さない。"""
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = _premium_user()

    failing = _stripe_mock()
    failing.Customer.delete.side_effect = _stripe_error(code=None)
    with _patch_stripe(failing):
        with pytest.raises(BillingCustomerCleanupFailed):
            delete_user_account(user=user)

    # retry: Stripe 側では subscription は既に canceled
    retry = _stripe_mock(
        subscription={"id": "sub_1", "customer": "cus_1", "status": "canceled"}
    )
    with _patch_stripe(retry):
        result = delete_user_account(user=user)

    retry.Subscription.cancel.assert_not_called()
    retry.Customer.delete.assert_called_once_with("cus_1")
    assert result.account_deleted is True
    assert not type(user).objects.filter(pk=user.pk).exists()


# --------------------------------------------- billing mirror update failure


def test_billing_mirror_update_failure_stops_before_user_delete(settings):
    """mirror 更新に失敗したら User.delete へ進まない。"""
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = _premium_user()
    stripe = _stripe_mock()

    with _patch_stripe(stripe):
        with patch(
            "users.services.account_deletion._mark_billing_canceled",
            side_effect=RuntimeError("db boom"),
        ):
            with pytest.raises(BillingStateSyncFailed):
                delete_user_account(user=user)

    # 将来請求は止まっているが、Account は残る
    stripe.Subscription.cancel.assert_called_once_with("sub_1")
    stripe.Customer.delete.assert_not_called()
    assert type(user).objects.filter(pk=user.pk).exists()
    assert UserProfile.objects.filter(user=user).exists()


def test_billing_mirror_update_failure_does_not_leak_the_raw_db_exception(settings):
    """raw DB exception を API 契約としてそのまま返さない。"""
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = _premium_user()
    stripe = _stripe_mock()

    with _patch_stripe(stripe):
        with patch(
            "users.services.account_deletion._mark_billing_canceled",
            side_effect=RuntimeError("connection to cus_1 failed: password=hunter2"),
        ):
            with pytest.raises(BillingStateSyncFailed) as excinfo:
                delete_user_account(user=user)

    assert excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__ is True
    assert "hunter2" not in str(excinfo.value)
    assert "cus_1" not in str(excinfo.value)


# ------------------------------------------------ raw Stripe cause 非伝播


@pytest.mark.parametrize(
    "failing_call,expected",
    [
        ("Subscription.retrieve", BillingCleanupFailed),
        ("Customer.delete", BillingCustomerCleanupFailed),
    ],
)
def test_raw_stripe_exception_is_not_propagated_as_cause(settings, failing_call, expected):
    """raw Stripe exception が traceback / error monitoring へ流れないこと。"""
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = _premium_user()
    stripe = _stripe_mock()
    target = stripe
    for part in failing_call.split("."):
        target = getattr(target, part)
    target.side_effect = _stripe_error(code=None)

    with _patch_stripe(stripe):
        with pytest.raises(expected) as excinfo:
            delete_user_account(user=user)

    # __cause__ / __context__ が切れている = raw 例外が外へ出ない
    assert excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__ is True
    message = str(excinfo.value)
    for secret in ("cus_", "sub_", "sk_live", "sk_test", user.email):
        assert secret not in message


# ------------------------------------------------- ShrineInteractionLog CASCADE


def test_shrine_interaction_logs_are_cascaded_without_touching_other_users(settings):
    """ShrineInteractionLog.user は CASCADE。Shrine 本体と他 User の log は残る。"""
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user = UserFactory()
    other = UserFactory()
    shrine = _shrine()
    mine = ShrineInteractionLog.objects.create(
        user=user, shrine=shrine, action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW
    )
    theirs = ShrineInteractionLog.objects.create(
        user=other, shrine=shrine, action_type=ShrineInteractionLog.ActionType.ROUTE_OPEN
    )

    delete_user_account(user=user)

    assert not ShrineInteractionLog.objects.filter(pk=mine.pk).exists()
    assert ShrineInteractionLog.objects.filter(pk=theirs.pk).exists()
    # 共有 master data は残る
    assert Shrine.objects.filter(pk=shrine.pk).exists()


# --------------------------------------------------- customer-only 経路


def _customer_only_user(cus="cus_only"):
    """subscription を持たず customer だけが残っている User。"""
    user = UserFactory()
    period_end = timezone.now() + timedelta(days=20)
    _profile(
        user,
        stripe_subscription_id="",
        stripe_customer_id=cus,
        subscription_status="active",
        current_period_end=period_end,
        cancel_at_period_end=False,
    )
    return user, period_end


def test_customer_only_deletes_customer_without_touching_subscription_api(settings):
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user, _ = _customer_only_user()
    stripe = MagicMock()

    with _patch_stripe(stripe):
        result = delete_user_account(user=user)

    # subscription が無い経路では Subscription API を一切触らない
    stripe.Subscription.retrieve.assert_not_called()
    stripe.Subscription.cancel.assert_not_called()
    stripe.Customer.delete.assert_called_once_with("cus_only")
    assert result.billing_cleanup_performed is True
    assert result.account_deleted is True
    assert not type(user).objects.filter(pk=user.pk).exists()


def test_customer_only_failure_leaves_the_billing_mirror_untouched(settings):
    """Customer cleanup 成功前に mirror を変更しない。

    subscription が無いこの経路では「将来請求を止めた」と言える操作が存在せず、
    Customer が残ったまま canceled と記録してはいけない。
    """
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user, period_end = _customer_only_user()
    log = ConciergeRecommendationLog.objects.create(user=user, query="mine")
    RefreshToken.for_user(user)
    stripe = MagicMock()
    stripe.Customer.delete.side_effect = _stripe_error(code=None)

    with _patch_stripe(stripe):
        with pytest.raises(BillingCleanupFailed):
            delete_user_account(user=user)

    # Account も UserProfile も残る
    assert type(user).objects.filter(pk=user.pk).exists()
    profile = UserProfile.objects.get(user=user)
    # mirror は変更前のまま
    assert profile.subscription_status == "active"
    assert profile.current_period_end is not None
    assert int(profile.current_period_end.timestamp()) == int(period_end.timestamp())
    assert profile.cancel_at_period_end is False
    # DB 側の削除も token blacklist も始まっていない
    assert ConciergeRecommendationLog.objects.filter(pk=log.pk).exists()
    assert BlacklistedToken.objects.count() == 0


def test_customer_only_failure_does_not_claim_charges_are_stopped(settings, caplog):
    """この時点では将来請求の停止を保証できないため、そう読める文言を出さない。"""
    import logging

    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user, _ = _customer_only_user()
    stripe = MagicMock()
    stripe.Customer.delete.side_effect = _stripe_error(code=None)

    with _patch_stripe(stripe):
        with caplog.at_level(logging.ERROR, logger="users.services.account_deletion"):
            with pytest.raises(BillingCleanupFailed) as excinfo:
                delete_user_account(user=user)

    message = caplog.records[0].getMessage()
    assert "future charges are already stopped" not in message
    assert "no DB rows were touched" in message
    # raw Stripe exception を外へ出さない
    assert excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__ is True
    for secret in ("cus_", "sk_live", "sk_test", user.email):
        assert secret not in str(excinfo.value)


def test_customer_only_resource_missing_is_idempotent_success(settings):
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user, _ = _customer_only_user()
    stripe = MagicMock()
    stripe.Customer.delete.side_effect = _stripe_error(code="resource_missing")

    with _patch_stripe(stripe):
        result = delete_user_account(user=user)

    assert result.account_deleted is True
    assert not type(user).objects.filter(pk=user.pk).exists()
    assert not UserProfile.objects.filter(user_id=user.pk).exists()


def test_customer_only_retry_after_failure_succeeds(settings):
    """初回失敗では無変更、retry で mirror canceled → Account 削除まで進む。"""
    settings.STRIPE_SECRET_KEY = "sk_test_dummy"
    user, period_end = _customer_only_user()
    other = UserFactory()
    _profile(other, stripe_customer_id="cus_other", subscription_status="active")
    other_log = ConciergeRecommendationLog.objects.create(user=other, query="theirs")

    failing = MagicMock()
    failing.Customer.delete.side_effect = _stripe_error(code=None)
    with _patch_stripe(failing):
        with pytest.raises(BillingCleanupFailed):
            delete_user_account(user=user)

    # 初回: Account も mirror も無変更
    assert type(user).objects.filter(pk=user.pk).exists()
    profile = UserProfile.objects.get(user=user)
    assert profile.subscription_status == "active"
    assert int(profile.current_period_end.timestamp()) == int(period_end.timestamp())

    # retry: 成功
    retry = MagicMock()
    with _patch_stripe(retry):
        result = delete_user_account(user=user)

    retry.Customer.delete.assert_called_once_with("cus_only")
    retry.Subscription.cancel.assert_not_called()
    assert result.account_deleted is True
    assert not type(user).objects.filter(pk=user.pk).exists()

    # 他 User の Stripe / DB data には触れていない
    other_profile = UserProfile.objects.get(user=other)
    assert other_profile.stripe_customer_id == "cus_other"
    assert other_profile.subscription_status == "active"
    assert ConciergeRecommendationLog.objects.filter(pk=other_log.pk).exists()
    assert "cus_other" not in [c.args[0] for c in retry.Customer.delete.call_args_list]
