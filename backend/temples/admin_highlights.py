"""Highlights の編集画面。公開判定は表示のたびに temples.services.highlight_publication で行う。

一覧の「表示条件」列で、日本語・英語それぞれの判定結果と落ちた理由を確かめられる。
"""

from django.contrib import admin
from temples.models import (
    ShrineHighlight,
    ShrineHighlightHistory,
    ShrineHighlightSource,
    ShrineHighlightTranslation,
)
from temples.services import highlight_publication


@admin.register(ShrineHighlight)
class ShrineHighlightAdmin(admin.ModelAdmin):
    list_display = (
        "stable_key",
        "shrine",
        "category",
        "sort_order",
        "publication_status",
        "verification_status",
        "display_check",
    )
    list_filter = ("publication_status", "verification_status")
    search_fields = ("stable_key", "shrine__name_jp", "category")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("shrine")
            .prefetch_related("translations", "source_links__source")
        )

    @admin.display(description="表示条件")
    def display_check(self, obj):
        parts = []
        for language in ("ja", "en"):
            decision = highlight_publication.decide_for_highlight(obj, language)
            parts.append(
                f"{language}: OK"
                if decision.displayable
                else f"{language}: {', '.join(decision.reasons)}"
            )
        return " / ".join(parts)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.publication_status != ShrineHighlight.PublicationStatus.DRAFT:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(ShrineHighlightTranslation)
class ShrineHighlightTranslationAdmin(admin.ModelAdmin):
    list_display = ("highlight", "language_code", "name", "location_hint", "review_status")
    list_filter = ("language_code", "review_status")


@admin.register(ShrineHighlightSource)
class ShrineHighlightSourceAdmin(admin.ModelAdmin):
    list_display = ("highlight", "source")


@admin.register(ShrineHighlightHistory)
class ShrineHighlightHistoryAdmin(admin.ModelAdmin):
    list_display = ("highlight", "history", "shrine")
