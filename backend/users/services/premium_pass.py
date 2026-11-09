# backend/users/services/premium_pass.py
"""買い切りの旅行パス（1日・7日・14日）で Premium の期限を延ばす・戻す。

- 期限を延ばす処理はこのファイルの grant_premium_pass に1か所でまとめる。
  Stripe の Webhook から呼ぶ。あとで Apple のアプリ内課金の通知からも同じ関数を呼ぶ。
- 新しい期限は「今と、今の期限の遅い方」に日数を足した日時（1日 = 24時間）。
- 同じ支払い（source + external_id）は1回分しか数えない。
- Premium の判定（users.services.billing.is_subscription_active：期限が未来なら Premium）は変えない。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from django.db import IntegrityError, transaction
from django.utils import timezone
from users.models import PremiumPassPurchase, UserProfile

log = logging.getLogger(__name__)

ACTIVE_STATUS = "active"


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
    now: Optional[datetime] = None,
) -> GrantResult:
    """パスの購入を記録し、Premium の期限を延ばす。

    同じ source + external_id の記録がすでにあれば、何もせずに今の期限を返す。
    """
    if not isinstance(days, int) or days <= 0:
        raise ValueError("days must be a positive integer")
    source = (source or "").strip()
    external_id = (external_id or "").strip()
    if not source or not external_id:
        raise ValueError("source and external_id are required")

    now_ = now or timezone.now()

    with transaction.atomic():
        profile, _ = UserProfile.objects.select_for_update().get_or_create(user=user)

        existing = PremiumPassPurchase.objects.filter(source=source, external_id=external_id).first()
        if existing is not None:
            return GrantResult(applied=False, period_end=profile.current_period_end)

        before = profile.current_period_end
        base = before if before is not None and before > now_ else now_
        after = base + timedelta(days=days)

        try:
            with transaction.atomic():
                PremiumPassPurchase.objects.create(
                    user=user,
                    source=source,
                    external_id=external_id,
                    payment_intent_id=(payment_intent_id or "").strip(),
                    pass_type=(pass_type or "").strip(),
                    days=days,
                    amount=amount,
                    currency=(currency or "").strip().lower(),
                    period_end_before=before,
                    period_end_after=after,
                )
        except IntegrityError:
            # ほかの処理が同じ支払いを先に記録した（同時に届いた通知）。延ばさない。
            return GrantResult(applied=False, period_end=profile.current_period_end)

        profile.current_period_end = after
        profile.subscription_status = ACTIVE_STATUS
        profile.cancel_at_period_end = False
        profile.save(
            update_fields=["current_period_end", "subscription_status", "cancel_at_period_end", "updated_at"]
        )

    log.info(
        "[premium-pass] granted source=%s external_id=%s days=%s period_end=%s",
        source,
        external_id,
        days,
        after.isoformat(),
    )
    return GrantResult(applied=True, period_end=after)


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
    """全額返金されたパスの日数を、期限から引く。

    - 記録が無い・すでに返金済みなら何もしない。
    - 引いた結果が今より前になったら、今で終わり（期限＝今）にする。
    """
    payment_intent_id = (payment_intent_id or "").strip()
    if not payment_intent_id:
        return RefundResult(applied=False, period_end=None)

    now_ = now or timezone.now()

    with transaction.atomic():
        purchase = (
            PremiumPassPurchase.objects.select_for_update()
            .filter(source=source, payment_intent_id=payment_intent_id)
            .first()
        )
        if purchase is None or purchase.status == PremiumPassPurchase.STATUS_REFUNDED:
            return RefundResult(applied=False, period_end=None)

        profile, _ = UserProfile.objects.select_for_update().get_or_create(user=purchase.user)
        current = profile.current_period_end
        new_end: Optional[datetime] = None
        if current is not None:
            new_end = current - timedelta(days=purchase.days)
            if new_end < now_:
                new_end = now_

        purchase.status = PremiumPassPurchase.STATUS_REFUNDED
        purchase.refunded_at = now_
        purchase.save(update_fields=["status", "refunded_at"])

        profile.current_period_end = new_end
        update_fields = ["current_period_end", "updated_at"]
        if new_end is None:
            # 期限が無いまま status が active だと、判定（is_subscription_active）が Premium のままになる。
            profile.subscription_status = "inactive"
            update_fields.append("subscription_status")
        profile.save(update_fields=update_fields)

    log.info(
        "[premium-pass] refunded source=%s payment_intent=%s days=%s period_end=%s",
        source,
        payment_intent_id,
        purchase.days,
        new_end.isoformat() if new_end else None,
    )
    return RefundResult(applied=True, period_end=new_end)
