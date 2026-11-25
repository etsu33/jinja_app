from django.contrib import admin

try:
    from .models import UserProfile

    @admin.register(UserProfile)
    class UserProfileAdmin(admin.ModelAdmin):
        list_display = ("user", "nickname", "is_public", "created_at")
        search_fields = ("user__username", "user__email")

except Exception:
    # UserProfile が無いプロジェクトでも落ちないようにする
    pass

try:
    from .models import PremiumPassPurchase

    @admin.register(PremiumPassPurchase)
    class PremiumPassPurchaseAdmin(admin.ModelAdmin):
        """旅行パスの購入の記録。期限の調べ・返金の確認用（作成・変更は Webhook が行う）。"""

        list_display = ("user", "source", "pass_type", "days", "status", "period_end_after", "created_at")
        list_filter = ("source", "pass_type", "status")
        search_fields = ("user__username", "user__email", "external_id", "payment_intent_id")
        readonly_fields = tuple(field.name for field in PremiumPassPurchase._meta.fields)

        def has_add_permission(self, request):
            return False

except Exception:
    pass
