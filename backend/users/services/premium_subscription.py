from datetime import datetime

from django.db.models import Count, Max, Q
from users.models import PremiumSubscription


def get_subscription_entitlement(*, user_id, now: datetime) -> tuple[bool, datetime | None]:
    """Return whether provider rows exist and their latest eligible deadline."""
    subscriptions = PremiumSubscription.objects.filter(user_id=user_id).aggregate(
        row_count=Count("pk"),
        active_end=Max(
            "current_period_end",
            filter=Q(
                status__in=(PremiumSubscription.Status.ACTIVE, PremiumSubscription.Status.GRACE),
                current_period_end__gt=now,
            ),
        ),
    )
    return subscriptions["row_count"] > 0, subscriptions["active_end"]
