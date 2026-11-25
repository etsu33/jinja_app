# backend/users/services/premium_pass.py
"""買い切りの旅行パス（1日・7日・14日）で Premium の期限を延ばす・戻す。

- 期限を延ばす処理はこのファイルの grant_premium_pass に1か所でまとめる。
  Stripe の Webhook と Apple の購入登録から呼ぶ。
- 新しい期限は「今と、Pass期限の遅い方」に日数を足した日時（1日 = 24時間）。
- 同じ支払いは1回分しか数えない。Apple の購入IDは環境ごとに管理する。
- 返金では購入時の記録を保持し、有効期限だけを調整する。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone
from users.models import PremiumPassPurchase, UserProfile
from users.services.billing import BillingOwnershipConflict

log = logging.getLogger(__name__)


def get_pass_period_end(*, user_id) -> Optional[datetime]:
    return _period_end(PremiumPassPurchase.objects.filter(user_id=user_id))


def _period_end(purchases):
    return purchases.filter(status=PremiumPassPurchase.STATUS_COMPLETED).aggregate(
        end=Max("effective_period_end")
    )["end"]


def _pass_stack(user_id, environment):
    purchases = PremiumPassPurchase.objects.filter(user_id=user_id)
    if environment == "Sandbox":
        return purchases.filter(environment="Sandbox")
    # Sandbox can grant Premium to a reviewer without altering paid Pass time.
    return purchases.exclude(environment="Sandbox")


def _pass_identity(source, external_id, environment):
    if source == PremiumPassPurchase.SOURCE_APPLE:
        if environment not in ("Production", "Sandbox"):
            raise ValueError("Apple Pass purchases require a verified environment")
    elif environment:
        raise ValueError("Only Apple Pass purchases have a StoreKit environment")
    return PremiumPassPurchase.objects.filter(
        source=source, external_id=external_id, environment=environment
    )


@dataclass(frozen=True)
class PassDefinition:
    pass_type: str
    days: int


# パスの種類 → 日数。値段（Stripe の Price）は temples.services.billing_checkout が環境変数から引く。
PASS_DEFINITIONS: dict[str, PassDefinition] = {
    "1d": PassDefinition(pass_type="1d", days=1),
    "7d": PassDefinition(pass_type="7d", days=7),
    "14d": PassDefinition(pass_type="14d", days=14),
}


def get_pass_definition(pass_type: object) -> Optional[PassDefinition]:
    if not isinstance(pass_type, str):
        return None
    return PASS_DEFINITIONS.get(pass_type.strip())


@dataclass(frozen=True)
class GrantResult:
    """applied: 今回の呼び出しで期限を延ばしたか（同じ支払いの2回目以降は False）。"""

    applied: bool
    period_end: Optional[datetime]


def grant_premium_pass(
    *,
    user,
    days: int,
    source: str,
    external_id: str,
    pass_type: str = "",
    amount: Optional[int] = None,
    currency: str = "",
    payment_intent_id: str = "",
    environment: str = "",
    now: Optional[datetime] = None,
) -> GrantResult:
    """パスの購入を記録し、Premium の期限を延ばす。

    同じ支払いの記録がすでにあれば、何もせずに今の期限を返す。
    """
    if not isinstance(days, int) or days <= 0:
        raise ValueError("days must be a positive integer")
    source = (source or "").strip()
    external_id = (external_id or "").strip()
    if not source or not external_id:
        raise ValueError("source and external_id are required")

    now_ = now or timezone.now()

    with transaction.atomic():
        UserProfile.objects.select_for_update().get_or_create(user=user)
        before = _period_end(_pass_stack(user.pk, environment))
        payment = _pass_identity(source, external_id, environment)
        if _already_granted(payment, user=user, source=source):
            return GrantResult(applied=False, period_end=before)

        base = before if before is not None and before > now_ else now_
        after = base + timedelta(days=days)

        try:
            with transaction.atomic():
                PremiumPassPurchase.objects.create(
                    user=user,
                    source=source,
                    external_id=external_id,
                    environment=environment,
                    payment_intent_id=(payment_intent_id or "").strip(),
                    pass_type=(pass_type or "").strip(),
                    days=days,
                    amount=amount,
                    currency=(currency or "").strip().lower(),
                    period_end_before=before,
                    period_end_after=after,
                    effective_period_end=after,
                )
        except IntegrityError:
            if not _already_granted(payment, user=user, source=source):
                raise
            return GrantResult(applied=False, period_end=before)

    log.info("[premium-pass] granted source=%s days=%s", source, days)
    return GrantResult(applied=True, period_end=after)


def _already_granted(payment, *, user, source):
    owner_id = payment.values_list("user_id", flat=True).first()
    if owner_id is not None and source == PremiumPassPurchase.SOURCE_APPLE and owner_id != user.pk:
        raise BillingOwnershipConflict
    return owner_id is not None


@dataclass(frozen=True)
class RefundResult:
    """applied: 今回の呼び出しで期限を戻したか。"""

    applied: bool
    period_end: Optional[datetime]


def revoke_premium_pass_for_refund(
    *,
    source: str,
    payment_intent_id: str,
    now: Optional[datetime] = None,
) -> RefundResult:
    """Apply a full refund once, reducing the remaining Pass deadline."""
    payment_intent_id = (payment_intent_id or "").strip()
    if not payment_intent_id:
        return RefundResult(applied=False, period_end=None)

    return _revoke_pass(
        PremiumPassPurchase.objects.filter(source=source, payment_intent_id=payment_intent_id),
        now_=now or timezone.now(),
    )


def revoke_premium_pass(
    *, source: str, external_id: str, environment: str = "", now: Optional[datetime] = None
) -> RefundResult:
    """Apply a provider revocation by its original purchase identifier."""
    if not source or not external_id:
        return RefundResult(applied=False, period_end=None)
    return _revoke_pass(
        _pass_identity(source, external_id, environment),
        now_=now or timezone.now(),
        preserve_separate_stacks=True,
    )


def _revoke_pass(
    payment, *, now_: datetime, preserve_separate_stacks: bool = False
) -> RefundResult:
    with transaction.atomic():
        user_id = payment.values_list("user_id", flat=True).first()
        if user_id is None:
            return RefundResult(applied=False, period_end=None)

        # Both grants and refunds acquire the profile lock before changing purchases.
        UserProfile.objects.select_for_update().get_or_create(user_id=user_id)
        purchase = payment.filter(user_id=user_id).first()
        if purchase is None or purchase.status != PremiumPassPurchase.STATUS_COMPLETED:
            return RefundResult(applied=False, period_end=None)

        stack = _pass_stack(user_id, purchase.environment)
        current = _period_end(stack)
        purchase.status = PremiumPassPurchase.STATUS_REFUNDED
        purchase.refunded_at = now_
        purchase.effective_period_end = None
        purchase.save(update_fields=["status", "refunded_at", "effective_period_end"])

        cutoff = None
        if current is not None and (
            not preserve_separate_stacks or _in_latest_stack(purchase, stack)
        ):
            cutoff = max(now_, current - timedelta(days=purchase.days))
            # A later purchase can include days from the refunded purchase.
            stack.filter(
                status=PremiumPassPurchase.STATUS_COMPLETED,
                effective_period_end__gt=cutoff,
            ).update(effective_period_end=cutoff)
        end = _period_end(stack)
        if end is not None and end <= now_:
            end = now_

    log.info("[premium-pass] refunded source=%s days=%s", purchase.source, purchase.days)
    return RefundResult(applied=True, period_end=end or cutoff)


def _in_latest_stack(purchase, stack):
    """A new stack after a lapse does not include days from an earlier purchase."""
    later = stack.filter(pk__gt=purchase.pk)
    for before, after, days in later.values_list("period_end_before", "period_end_after", "days"):
        if before is None or after - timedelta(days=days) > before:
            return False
    return True
