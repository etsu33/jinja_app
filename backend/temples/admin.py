# backend/temples/admin.py
from __future__ import annotations

from django.apps import apps
from django.contrib import admin, messages
from django import forms
from django.db import models
from django.utils.html import format_html
from django.urls import reverse

from .models import Goshuin, GoshuinImage, Shrine, ShrineSubmission
from temples.services.shrine_submission import (
    ShrineSubmissionDuplicateError,
    ShrineSubmissionInvalidStateError,
    approve_shrine_submission,
    normalize_shrine_address,
    normalize_shrine_name,
    reject_shrine_submission,
)

from temples.management.commands.seed_history_theme import HISTORY_THEME_SEED


@admin.register(Goshuin)
class GoshuinAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "shrine", "title", "is_public", "created_at")
    list_filter = ("is_public", "created_at")
    search_fields = ("title", "user__username", "shrine__name_jp")


@admin.register(GoshuinImage)
class GoshuinImageAdmin(admin.ModelAdmin):
    list_display = ("id", "goshuin", "order")
    list_filter = ("order",)


@admin.register(ShrineSubmission)
class ShrineSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "name",
        "address",
        "user",
        "goriyaku_tags_summary",
        "review_status_summary",
        "created_at",
        "reviewed_by",
        "reviewed_at",
    )
    list_filter = ("status", "created_at", "reviewed_at")
    search_fields = ("name", "address", "user__username", "user__email")
    ordering = ("-created_at",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "reviewed_at",
        "reviewed_by",
        "review_status_summary",
        "approved_shrine_admin_link",
        "shrine_create_preview",
    )
    formfield_overrides = {
        models.TextField: {
            "widget": forms.Textarea(attrs={"rows": 6, "cols": 80}),
        },
    }
    fieldsets = (
        (
            "投稿内容",
            {
                "fields": (
                    "status",
                    "name",
                    "address",
                    ("lat", "lng"),
                    "goriyaku_tags",
                    "note",
                )
            },
        ),
        (
            "審査情報",
            {
                "fields": (
                    "review_comment",
                    "review_status_summary",
                    "approved_shrine_admin_link",
                    "shrine_create_preview",
                    "reviewed_by",
                    "reviewed_at",
                )
            },
        ),
        (
            "メタ情報",
            {
                "fields": (
                    "user",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    actions = ["mark_approved", "mark_rejected"]

    @admin.display(description="ご利益タグ")
    def goriyaku_tags_summary(self, obj):
        tags = obj.goriyaku_tags
        if not tags:
            return "-"

        if isinstance(tags, list):
            normalized = [str(tag) for tag in tags if str(tag).strip()]
            if not normalized:
                return "-"
            visible = normalized[:5]
            suffix = f" 他{len(normalized) - 5}件" if len(normalized) > 5 else ""
            return f"{', '.join(visible)}{suffix}"

        return str(tags)

    @admin.display(description="承認時の Shrine 反映プレビュー")
    def shrine_create_preview(self, obj):
        return format_html(
            "神社名: {}<br>住所: {}<br>緯度: {}<br>経度: {}<br>所有者: {}<br>ご利益タグ: Shrine本体へは自動反映しません",
            normalize_shrine_name(obj.name),
            normalize_shrine_address(obj.address),
            obj.lat if obj.lat is not None else "-",
            obj.lng if obj.lng is not None else "-",
            obj.user,
        )

    @admin.display(description="審査状態")
    def review_status_summary(self, obj):
        if obj.status == ShrineSubmission.Status.APPROVED:
            return format_html(
                "<strong>承認済み</strong><br>確認者: {}<br>確認日時: {}",
                obj.reviewed_by or "-",
                obj.reviewed_at or "-",
            )
        if obj.status == ShrineSubmission.Status.REJECTED:
            return format_html(
                "<strong>却下済み</strong><br>確認者: {}<br>確認日時: {}",
                obj.reviewed_by or "-",
                obj.reviewed_at or "-",
            )
        return "審査待ち"

    @admin.display(description="作成済み Shrine")
    def approved_shrine_admin_link(self, obj):
        if obj.status != ShrineSubmission.Status.APPROVED:
            return "未承認"

        shrine = Shrine.objects.filter(
            name_jp=normalize_shrine_name(obj.name),
            address=normalize_shrine_address(obj.address),
        ).first()

        if shrine is None:
            return "未作成または特定できません"

        url = reverse("admin:temples_shrine_change", args=[shrine.id])
        return format_html('<a href="{}">{} (id={})</a>', url, shrine.name_jp, shrine.id)

    @admin.action(description="Mark as approved")
    def mark_approved(self, request, queryset):
        success_count = 0
        fail_count = 0
        created_shrines = []

        for submission in queryset:
            try:
                shrine = approve_shrine_submission(
                    submission_id=submission.id,
                    reviewer=request.user,
                )
                created_shrines.append(f"id={shrine.id}: {shrine.name_jp}")
                success_count += 1
            except (ShrineSubmissionDuplicateError, ShrineSubmissionInvalidStateError) as exc:
                fail_count += 1
                self.message_user(
                    request,
                    f"id={submission.id} の承認に失敗: {exc}",
                    level=messages.WARNING,
                )

        if success_count:
            shrine_summary = " / ".join(created_shrines[:5])
            suffix = f" 他{len(created_shrines) - 5}件" if len(created_shrines) > 5 else ""
            detail = f" 作成: {shrine_summary}{suffix}" if shrine_summary else ""
            self.message_user(
                request,
                f"{success_count}件を承認し、Shrine へ反映しました。{detail}",
                level=messages.SUCCESS,
            )

        if fail_count:
            self.message_user(
                request,
                f"{fail_count}件は承認できませんでした。",
                level=messages.WARNING,
            )

    @admin.action(description="Mark as rejected")
    def mark_rejected(self, request, queryset):
        success_count = 0
        fail_count = 0

        for submission in queryset:
            try:
                reject_shrine_submission(
                    submission_id=submission.id,
                    reviewer=request.user,
                )
                success_count += 1
            except Exception as exc:
                fail_count += 1
                self.message_user(
                    request,
                    f"id={submission.id} の却下に失敗: {exc}",
                    level=messages.WARNING,
                )

        if success_count:
            self.message_user(
                request,
                f"{success_count}件を rejected に更新しました。",
                level=messages.SUCCESS,
            )

        if fail_count:
            self.message_user(
                request,
                f"{fail_count}件は却下できませんでした。",
                level=messages.WARNING,
            )


def _maybe_register(model_name: str, admin_cls: type[admin.ModelAdmin]) -> None:
    """
    temples に model_name があれば Admin へ登録。
    無ければ静かにスキップ。既登録なら安全にスキップ。
    """
    try:
        Model = apps.get_model("temples", model_name, require_ready=False)
    except LookupError:
        return
    if Model is None:
        return
    try:
        admin.site.register(Model, admin_cls)
    except admin.sites.AlreadyRegistered:
        pass


class DeityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "kana")
    search_fields = ("name", "kana", "aliases")


class GoriyakuTagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category")
    search_fields = ("name", "category")


class ShrineAdmin(admin.ModelAdmin):
    """神社モデルの管理画面（GISウィジェットなしの暫定版）"""

    list_display = (
        "name_jp",
        "address",
        "history_theme",
        "popular_score",
        "views_30d",
        "favorites_30d",
        "updated_at",
    )
    search_fields = ("name_jp", "name_romaji", "address")
    list_filter = ("kind", "element", "kyusei", "history_theme")
    ordering = ("-popular_score", "-updated_at")
    readonly_fields = ("last_popular_calc_at",)
    filter_horizontal = ("goriyaku_tags",)
    actions = ["seed_history_theme"]

    @admin.action(description="history_theme 初期値を投入する")
    def seed_history_theme(self, request, queryset):
        updated = 0
        skipped = 0
        missing: list[int] = []

        for shrine_id, history_theme in HISTORY_THEME_SEED.items():
            shrine = Shrine.objects.filter(id=shrine_id).only("id", "name_jp", "history_theme").first()
            if shrine is None:
                missing.append(shrine_id)
                continue

            current = shrine.history_theme or ""
            if current == history_theme:
                skipped += 1
                continue

            shrine.history_theme = history_theme
            shrine.save(update_fields=["history_theme"])
            updated += 1

        if missing:
            self.message_user(
                request,
                f"history_theme 初期投入: 存在しない Shrine id があります: {missing}",
                level=messages.WARNING,
            )

        self.message_user(
            request,
            f"history_theme 初期投入完了: 更新 {updated}件 / 既存一致 {skipped}件 / 定義 {len(HISTORY_THEME_SEED)}件",
            level=messages.SUCCESS,
        )


# ---- 動的登録（存在する時だけ）----
_maybe_register("Deity", DeityAdmin)
_maybe_register("GoriyakuTag", GoriyakuTagAdmin)
_maybe_register("Shrine", ShrineAdmin)
