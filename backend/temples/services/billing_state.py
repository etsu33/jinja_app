# backend/temples/services/billing_state.py
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from django.utils import timezone as dj_timezone
from users.models import UserProfile
from users.services.billing import is_subscription_active
from users.services.premium_pass import get_pass_period_end
from users.services.premium_subscription import get_subscription_entitlement

PROVIDER_CHOICES = ("stub", "stripe", "revenuecat", "unknown")


@dataclass(frozen=True)
class BillingStatus:
    plan: str  # "free" | "premium"
    is_active: bool
    provider: str  # "stub" | "stripe" | "revenuecat" | "unknown"
    current_period_end: Optional[datetime]
    trial_ends_at: Optional[datetime]
    cancel_at_period_end: bool


def provider() -> str:
    p = (os.getenv("BILLING_PROVIDER", "stub") or "stub").strip().lower()
    return p if p in PROVIDER_CHOICES else "unknown"


def _billing_stub_env() -> tuple[str, str]:
    plan = (os.environ.get("BILLING_STUB_PLAN") or "free").strip().lower()
    active = (os.environ.get("BILLING_STUB_ACTIVE") or "0").strip().lower()
    return plan, active


def get_billing_status(*, user=None, now: Optional[datetime] = None) -> BillingStatus:
    """Return the public billing status from the account's entitlement sources."""
    return _resolve_billing_status(user, now or dj_timezone.now())


def _resolve_billing_status(user, now: datetime, *, staff_access: bool = False) -> BillingStatus:
    prov = provider()
    authenticated = getattr(user, "is_authenticated", False)
    user_id = getattr(user, "pk", None) if authenticated else None
    profile = UserProfile.objects.filter(user_id=user_id).first() if user_id is not None else None

    if profile and profile.account_entitlement_disabled:
        return BillingStatus("free", False, prov, None, None, False)
    if staff_access and authenticated and getattr(user, "is_staff", False):
        return BillingStatus("premium", True, prov, None, None, False)
    if prov == "stub" or not authenticated:
        return _status_from_stub_env(now_=now, prov=prov)

    has_subscription_rows, subscription_end = (
        get_subscription_entitlement(user_id=user_id, now=now)
        if user_id is not None
        else (False, None)
    )
    subscription_active = subscription_end is not None
    if not has_subscription_rows and profile:
        subscription_end = profile.current_period_end
        subscription_active = is_subscription_active(
            status=profile.subscription_status,
            current_period_end=subscription_end,
            now=now,
        )

    pass_end = get_pass_period_end(user_id=user_id) if user_id is not None else None
    pass_active = pass_end is not None and pass_end > now
    legacy_end = profile.legacy_premium_until if profile else None
    legacy_active = legacy_end is not None and legacy_end > now

    active = subscription_active or pass_active or legacy_active
    active_ends = (
        end
        for enabled, end in (
            (subscription_active, subscription_end),
            (pass_active, pass_end),
            (legacy_active, legacy_end),
        )
        if enabled and end is not None
    )
    effective_end = max(active_ends, default=None)
    # Preserve the response for an undated legacy subscription during the fallback.
    if subscription_active and subscription_end is None:
        effective_end = None
    return BillingStatus(
        plan="premium" if active else "free",
        is_active=active,
        provider=prov,
        current_period_end=effective_end,
        trial_ends_at=None,
        cancel_at_period_end=bool(profile and profile.cancel_at_period_end),
    )


def _status_from_stub_env(*, now_: datetime, prov: str) -> BillingStatus:
    """
    stub 課金状態の解決。

    用途:
    - Billing 未導入環境
    - テスト環境
    - premium/free の切り替えを env で擬似再現したい場面

    注意:
    - ここでは表示文言や API レスポンス形は扱わない
    - chat / plan のレスポンス責務とは分離する
    """
    plan_env, active_env = _billing_stub_env()
    active = active_env in {"1", "true", "yes", "y", "on"}
    plan = "premium" if plan_env == "premium" else "free"

    if plan == "premium" and os.getenv("BILLING_STUB_ACTIVE") is None:
        active = True

    cpe = (now_ + timedelta(days=30)) if active else None

    prov_out = prov
    if plan == "premium" and prov_out == "stub":
        prov_out = "stripe"

    cancel_at_period_end = (os.getenv("BILLING_STUB_CANCEL_AT_PERIOD_END", "0") or "0").strip().lower() in {
        "1", "true", "yes", "y", "on",
    }

    return BillingStatus(
        plan=plan,
        is_active=bool(active),
        provider=prov_out,
        current_period_end=cpe,
        trial_ends_at=None,
        cancel_at_period_end=bool(cancel_at_period_end),
    )



def is_premium_for_request(request) -> bool:
    user = getattr(request, "user", None)
    return is_premium_for_user(user)


def is_premium_for_user(user) -> bool:
    """
    課金状態の利用側向けヘルパー。
    chat API の無料回数分岐はこの関数を正本として判定する。
    """

    st = _resolve_billing_status(user, dj_timezone.now(), staff_access=True)
    return st.plan == "premium" and st.is_active


def recommend_limit_for_user(user) -> int:
    return 6 if is_premium_for_user(user) else 3
