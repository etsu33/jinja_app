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
