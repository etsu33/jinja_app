from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    nickname = models.CharField(max_length=64, blank=True, default="")
    is_public = models.BooleanField(default=False)
    bio = models.TextField(blank=True, null=True)
    icon = models.ImageField(upload_to="icons/", blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    birth_time = models.TimeField(blank=True, null=True)
    birth_place = models.CharField(max_length=32, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    stripe_customer_id = models.CharField(max_length=255, blank=True, default="")
    stripe_subscription_id = models.CharField(max_length=255, blank=True, default="")
    stripe_price_id = models.CharField(max_length=255, blank=True, default="")

    subscription_status = models.CharField(
        max_length=32,
        blank=True,
        default="inactive",
        db_index=True,
    )
    # Subscription period end.
    current_period_end = models.DateTimeField(blank=True, null=True)
    # Stripe subscription.cancel_at_period_end のミラー。
    # 「期間終了時に解約」予約の有無だけを持ち、Premium/Free の判定には使わない
    # （判定は subscription_status + current_period_end が正）。
    cancel_at_period_end = models.BooleanField(default=False)

    legacy_premium_until = models.DateTimeField(blank=True, null=True)
    account_entitlement_disabled = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nickname or self.user.get_username()


class PremiumPassPurchase(models.Model):
    """買い切りの旅行パス（1日・7日・14日）の購入の記録。

    - 同じ支払いでは期限を1回だけ延ばす。Apple の購入IDは環境ごとに一意。
    - 期限を延ばす処理は users.services.premium_pass.grant_premium_pass に1か所でまとめる。
    - 退会のときは、ユーザーと一緒に消える（CASCADE）。
    """

    SOURCE_STRIPE = "stripe"
    SOURCE_APPLE = "apple"

    STATUS_COMPLETED = "completed"
    STATUS_REFUNDED = "refunded"
    STATUS_CHOICES = [(STATUS_COMPLETED, "completed"), (STATUS_REFUNDED, "refunded")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="premium_pass_purchases",
    )
    # 支払いの出どころ。あとで Apple のアプリ内課金（"apple"）を足す。
    source = models.CharField(max_length=16)
    # 支払いの ID。Stripe ならチェックアウトの ID（cs_...）。
    external_id = models.CharField(max_length=255)
    environment = models.CharField(max_length=32, blank=True, default="")
    # Stripe の PaymentIntent の ID（pi_...）。返金の通知との照合に使う。
    payment_intent_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    pass_type = models.CharField(max_length=8, blank=True, default="")
    days = models.PositiveIntegerField()
    amount = models.PositiveIntegerField(blank=True, null=True)
    currency = models.CharField(max_length=8, blank=True, default="")
    period_end_before = models.DateTimeField(blank=True, null=True)
    period_end_after = models.DateTimeField()
    # Refunds may reduce the usable deadline without rewriting the purchase history.
    effective_period_end = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_COMPLETED)
    refunded_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_id"],
                condition=~models.Q(source="apple"),
                name="uniq_premium_pass_non_apple_id",
            ),
            models.UniqueConstraint(
                fields=["source", "environment", "external_id"],
                condition=models.Q(source="apple"),
                name="uniq_premium_pass_apple_environment_id",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(source="apple", environment__in=("Production", "Sandbox"))
                    | (~models.Q(source="apple") & models.Q(environment=""))
                ),
                name="premium_pass_environment_matches_source",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.source}:{self.external_id} ({self.pass_type or self.days})"


class PremiumSubscription(models.Model):
    class Source(models.TextChoices):
        STRIPE = "stripe", "Stripe"
        APPLE = "apple", "Apple"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        GRACE = "grace", "Grace"
        BILLING_RETRY = "billing_retry", "Billing retry"
        EXPIRED = "expired", "Expired"
        REVOKED = "revoked", "Revoked"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="premium_subscriptions",
    )
    source = models.CharField(max_length=16, choices=Source.choices)
    product_id = models.CharField(max_length=255)
    external_subscription_id = models.CharField(max_length=255, blank=True, default="")
    original_transaction_id = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=16, choices=Status.choices)
    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    auto_renew_enabled = models.BooleanField(default=False)
    environment = models.CharField(max_length=32, default="unknown")
    last_event_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "external_subscription_id"],
                condition=models.Q(source="stripe"),
                name="uniq_premium_subscription_stripe_id",
            ),
            models.UniqueConstraint(
                fields=["source", "environment", "original_transaction_id"],
                condition=models.Q(source="apple"),
                name="uniq_premium_subscription_apple_environment_id",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(source="stripe", external_subscription_id__gt="")
                    | models.Q(source="apple", original_transaction_id__gt="")
                ),
                name="premium_subscription_has_provider_id",
            ),
        ]


class AppleStoreKitReceipt(models.Model):
    """A lock and the latest verified state received before a purchase has an owner."""

    environment = models.CharField(max_length=32)
    kind = models.CharField(max_length=16)
    external_id = models.CharField(max_length=255)
    event_at = models.DateTimeField(null=True, blank=True)
    purchased_at = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, blank=True, default="")
    auto_renew_enabled = models.BooleanField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "kind", "external_id"], name="uniq_apple_storekit_receipt"
            ),
        ]
