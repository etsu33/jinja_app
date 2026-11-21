"""Foundation editing only; this admin does not publish via a runtime gate."""

from django.contrib import admin
from temples.models import (
    ShrineHighlight,
    ShrineHighlightHistory,
    ShrineHighlightSource,
    ShrineHighlightTranslation,
)


@admin.register(ShrineHighlight)
class ShrineHighlightAdmin(admin.ModelAdmin):
    list_display = ("stable_key", "shrine", "category", "publication_status", "verification_status")
    list_filter = ("publication_status", "verification_status")
    search_fields = ("stable_key", "shrine__name_jp", "category")

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.publication_status != ShrineHighlight.PublicationStatus.DRAFT:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(ShrineHighlightTranslation)
class ShrineHighlightTranslationAdmin(admin.ModelAdmin):
    list_display = ("highlight", "language_code", "name", "review_status")
    list_filter = ("language_code", "review_status")


@admin.register(ShrineHighlightSource)
class ShrineHighlightSourceAdmin(admin.ModelAdmin):
    list_display = ("highlight", "source")


@admin.register(ShrineHighlightHistory)
class ShrineHighlightHistoryAdmin(admin.ModelAdmin):
    list_display = ("highlight", "history", "shrine")
