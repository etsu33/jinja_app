"""Highlights の編集画面。公開判定は表示のたびに temples.services.highlight_publication で行う。

一覧の「表示条件」列で、日本語・英語それぞれの判定結果と落ちた理由を確かめられる。
"""

from django.contrib import admin
from temples.models import (
    ShrineHighlight,
    ShrineHighlightAnswer,
    ShrineHighlightHistory,
    ShrineHighlightSource,
    ShrineHighlightTranslation,
)
from temples.services import highlight_publication


class ShrineHighlightAnswerInline(admin.TabularInline):
    """見どころの画面の中で、相談の種類ごとのアンサーを入れられるようにする。"""

    model = ShrineHighlightAnswer
    extra = 1
    fields = ("need_tag", "language_code", "answer_text", "review_status", "reviewed_at")


@admin.register(ShrineHighlight)
class ShrineHighlightAdmin(admin.ModelAdmin):
    inlines = [ShrineHighlightAnswerInline]
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


@admin.register(ShrineHighlightAnswer)
class ShrineHighlightAnswerAdmin(admin.ModelAdmin):
    """見どころへのアンサー。「表示条件」列で出せるかと落ちた理由を確かめられる。"""

    list_display = ("highlight", "need_tag", "language_code", "review_status", "display_check")
    list_filter = ("need_tag", "language_code", "review_status")
    search_fields = ("highlight__stable_key", "highlight__shrine__name_jp", "answer_text")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("highlight", "highlight__shrine")
            .prefetch_related("highlight__translations", "highlight__source_links__source")
        )

    @admin.display(description="表示条件")
    def display_check(self, obj):
        decision = highlight_publication.decide_answer_publication(obj, obj.language_code)
        return "OK" if decision.displayable else ", ".join(decision.reasons)
