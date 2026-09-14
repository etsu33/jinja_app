# backend/users/services/account_deletion.py
"""認証済み User のアカウント削除。

この service が守る契約:

1. Stripe の将来請求停止を確認できないうちは、DB を一切壊さない。
   Stripe cleanup が失敗したら User も RecommendationLog も token も
   触らずに例外を返す（fail closed）。

2. 外部API(Stripe)と DB は同じ transaction に入れられない。
   Stripe を止めたあとで DB 削除が失敗する partial failure は
   構造上ゼロにできない。そのため:
     - Stripe 成功直後に、ローカルの billing mirror を canceled 相当へ倒す
       （別 transaction で確定させる）。DB 削除が失敗して Account が残っても
       Premium active のまま見えないようにするため。
     - DB 削除の失敗は「成功」として返さない。retry 可能な例外を返す。
     - Stripe 契約を復活させることはしない（請求再開のほうが害が大きい）。

3. Storage 上の実ファイル削除は再実装しない。
   PR #2829 で入れた post_delete receiver + transaction.on_commit に任せる。
   DB transaction が rollback すれば Storage も削除されない。

log / 戻り値に出さないもの:
    Stripe の customer ID / subscription ID / 例外メッセージ / secret /
    email / 相談本文 / 位置情報。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from django.conf import settings
from django.db import models, transaction
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from temples.models import ConciergeRecommendationLog
from users.models import UserProfile

logger = logging.getLogger(__name__)

# webhook が書く既存の status vocabulary に合わせる。新しい文字列は作らない。
# users/services/stripe_webhook.py::_apply_subscription_object の
# customer.subscription.deleted 分岐と同じ値。
CANCELED_SUBSCRIPTION_STATUS = "canceled"


class AccountDeletionError(RuntimeError):
    """アカウント削除の失敗を表す基底例外。"""


class BillingCleanupFailed(AccountDeletionError):
    """Stripe 側の停止を確認できなかった。DB は一切変更していない。"""


class AccountDataDeletionFailed(AccountDeletionError):
    """Stripe は停止済みだが DB 削除に失敗した。Account は残っている。

    「DB も Stripe も完全に rollback した」ではない。呼び出し側はこれを
    成功として扱ってはならず、retry で解消しうる状態として扱う。
    """


@dataclass(frozen=True)
class AccountDeletionResult:
    """呼び出し側が API を実装できる最小限の情報だけを持つ。

    Stripe の ID / token 文字列 / email / query本文 は含めない。
    """

    account_deleted: bool
    billing_cleanup_performed: bool
    tokens_blacklisted: int
    recommendation_logs_deleted: int


# --- Stripe -----------------------------------------------------------------


def _is_missing_resource(exc: Exception) -> bool:
    """Stripe が「そのリソースは存在しない」と明示したときだけ True。

    message 文字列の照合はしない（文言は変わりうる）。Stripe が返す
    `code == "resource_missing"` だけを根拠にする。
    network error / auth error / timeout はここに入らない = success にしない。
    """
    return getattr(exc, "code", None) == "resource_missing"


def _stripe_module():
    """既存 service（billing_checkout / billing_portal）と同じ初期化手順。"""
    secret_key = (getattr(settings, "STRIPE_SECRET_KEY", "") or "").strip()
    if not secret_key:
        # 請求停止を確認する手段が無い。ここで止める。
        raise BillingCleanupFailed("stripe secret key is not configured")

    try:
        import stripe  # type: ignore
    except Exception as exc:  # pragma: no cover - optional deployment package
        raise BillingCleanupFailed("stripe sdk is not installed") from exc

    stripe.api_key = secret_key
    return stripe


def _cancel_subscription(stripe: Any, subscription_id: str) -> Optional[str]:
    """subscription を即時 cancel し、判明した customer id を返す。

    - `cancel_at_period_end` は使わない。将来請求の停止を最優先する。
    - proration / refund の API は呼ばない。日割り返金は行わない契約。
    - 既に canceled なら cancel を投げ直さない（status を見て判断する。
      例外メッセージの文言には依存しない）。
    """
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
    except Exception as exc:
        if _is_missing_resource(exc):
            return None  # 既に存在しない = 将来請求は発生しない
        raise

    customer_id = subscription.get("customer") if hasattr(subscription, "get") else None
    if not isinstance(customer_id, str):
        customer_id = None

    status = subscription.get("status") if hasattr(subscription, "get") else None
    if status == "canceled":
        return customer_id

    try:
        stripe.Subscription.cancel(subscription_id)
    except Exception as exc:
        if not _is_missing_resource(exc):
            raise

    return customer_id


def _delete_customer(stripe: Any, customer_id: str) -> None:
    try:
        stripe.Customer.delete(customer_id)
    except Exception as exc:
        if not _is_missing_resource(exc):
            raise


def _cleanup_billing(*, profile: Optional[UserProfile]) -> bool:
    """Stripe 側の将来請求を止める。実際に外部APIを呼んだら True。

    停止を確認できない場合は必ず BillingCleanupFailed を送出する。
    """
    subscription_id = (getattr(profile, "stripe_subscription_id", "") or "").strip()
    customer_id = (getattr(profile, "stripe_customer_id", "") or "").strip()

    if not subscription_id and not customer_id:
        # Stripe と紐づいていない。外部呼び出しなしで DB 削除へ進める。
        return False

    stripe = _stripe_module()

    try:
        if subscription_id:
            # subscription_id しか無い異常系でも、ここで customer を確認できる。
            # ID を推測で組み立てることはしない。
            discovered_customer_id = _cancel_subscription(stripe, subscription_id)
            if not customer_id and discovered_customer_id:
                customer_id = discovered_customer_id

        if customer_id:
            _delete_customer(stripe, customer_id)
    except BillingCleanupFailed:
        raise
    except Exception as exc:
        # 例外本文には customer / subscription ID が載りうるので出さない。
        logger.error(
            "[account-deletion] stripe cleanup failed error_type=%s "
            "(account was NOT deleted; no DB rows were touched)",
            type(exc).__name__,
        )
        raise BillingCleanupFailed("failed to stop stripe billing") from exc

    return True


def _mark_billing_canceled(*, profile: Optional[UserProfile]) -> None:
    """ローカルの billing mirror を canceled 相当へ倒す。

    DB 削除が失敗して UserProfile が残った場合でも、Premium active のまま
    見えないようにするための保険。削除 transaction とは別に確定させる
    （同じ transaction に入れると rollback で巻き戻ってしまう）。

    値は webhook の customer.subscription.deleted 分岐と揃える。
    """
    if profile is None or profile.pk is None:
        return

    UserProfile.objects.filter(pk=profile.pk).update(
        subscription_status=CANCELED_SUBSCRIPTION_STATUS,
        current_period_end=None,
        cancel_at_period_end=False,
    )


# --- DB ---------------------------------------------------------------------


def _blacklist_outstanding_tokens(*, user) -> int:
    """対象 User の refresh token を再利用不能にする。

    OutstandingToken は削除しない。BlacklistedToken は OutstandingToken へ
    CASCADE しているため、先に消すと失効の証跡ごと消える。
    User 削除時は OutstandingToken.user が SET_NULL になるだけで row は残り、
    jti による blacklist 判定は User 削除後も成立する。

    他 User の token には触れない。
    """
    blacklisted = 0
    for token in OutstandingToken.objects.filter(user=user):
        _, created = BlacklistedToken.objects.get_or_create(token=token)
        if created:
            blacklisted += 1
    return blacklisted


def _delete_recommendation_logs(*, user) -> int:
    """User 由来の RecommendationLog を明示削除する。

    `ConciergeRecommendationLog.user` は SET_NULL、`thread` も SET_NULL なので、
    User を先に消すと user=NULL / thread=NULL の孤児 log が残る。

    対象:
        1. user == 対象 User
        2. user IS NULL かつ thread.user == 対象 User
           （匿名で始めた相談が後からこの User の Thread になったケース）

    別 User が owner の log は削除しない。
    """
    deleted, _ = ConciergeRecommendationLog.objects.filter(
        models.Q(user=user) | models.Q(user__isnull=True, thread__user=user)
    ).delete()
    return deleted


# --- public -----------------------------------------------------------------


def delete_user_account(*, user) -> AccountDeletionResult:
    """アカウント削除の単一入口。

    個別の cleanup 手順を service の外から直接呼ばないこと。
    順序（Stripe → billing mirror → token → RecommendationLog → User）自体が
    安全契約であり、部分的に呼ぶと契約が崩れる。
    """
    profile = UserProfile.objects.filter(user=user).first()

    # 1. Stripe を先に止める。ここで失敗したら DB は一切触らない。
    billing_cleanup_performed = _cleanup_billing(profile=profile)

    # 2. Stripe が止まった事実を、削除 transaction の外で確定させる。
    if billing_cleanup_performed:
        _mark_billing_canceled(profile=profile)

    # 3. DB 削除。Storage 削除は post_delete receiver が on_commit へ積む。
    try:
        with transaction.atomic():
            tokens_blacklisted = _blacklist_outstanding_tokens(user=user)
            recommendation_logs_deleted = _delete_recommendation_logs(user=user)
            # CASCADE / SET_NULL は Django の relation contract に任せる。
            # 個別モデルを手で消さない。
            user.delete()
    except Exception as exc:
        logger.error(
            "[account-deletion] account data deletion failed after billing cleanup "
            "error_type=%s (stripe billing is already stopped; the account still "
            "exists and deletion can be retried)",
            type(exc).__name__,
        )
        raise AccountDataDeletionFailed("failed to delete account data") from exc

    return AccountDeletionResult(
        account_deleted=True,
        billing_cleanup_performed=billing_cleanup_performed,
        tokens_blacklisted=tokens_blacklisted,
        recommendation_logs_deleted=recommendation_logs_deleted,
    )
