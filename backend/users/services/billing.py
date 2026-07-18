# backend/users/services/billing.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from django.utils import timezone

ACTIVE_STATUSES = {"active", "trialing"}


def is_subscription_active(
    *,
    status: str | None,
    current_period_end: Optional[datetime],
    now: Optional[datetime] = None,
) -> bool:
    """
    status だけに頼ると事故るので、current_period_end があるなら期限優先。
    """
    s = (status or "").strip()
    now_ = now or timezone.now()

    if current_period_end is not None:
        # 期限が未来なら有効。statusが多少ズレても救う。
        return now_ < current_period_end

    return s in ACTIVE_STATUSES
