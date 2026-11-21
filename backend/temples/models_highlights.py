"""Highlights foundation. Publication/translation gates belong to later PRs.

The pre_delete receiver covers ORM instance, queryset, admin and cascade deletes.
It is intentionally not a database DELETE trigger: raw SQL bypasses it.
Cross-shrine link integrity is validated here; composite FKs belong to PR-2.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from temples.models import (
    KNOWLEDGE_CONFIDENCE_CHOICES,
    KNOWLEDGE_VERIFICATION_STATUS_CHOICES,
    _validate_not_blank,
    _validate_verified_at_consistency,
)

# Match Python whitespace validation even under a PostgreSQL C collation.
_HAS_NON_WHITESPACE = (
    "[^\t\n\v\f\r \x1c\x1d\x1e\x1f\x85\xa0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]"
)


class ShrineHighlight(models.Model):
    class Category(models.TextChoices):
        ARCHITECTURE = "architecture", "Architecture"
        CULTURAL_HERITAGE = "cultural_heritage", "Cultural heritage"
        NATURE = "nature", "Nature"
        RITUAL_FESTIVAL = "ritual_festival", "Ritual / festival"
        HISTORICAL_SITE = "historical_site", "Historical site"
        EXPERIENCE = "experience", "Experience"

    class PublicationStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    shrine = models.ForeignKey(
        "temples.Shrine", on_delete=models.CASCADE, related_name="highlights"
    )
    stable_key = models.CharField(max_length=255, unique=True, validators=[_validate_not_blank])
    # Highlights own this vocabulary; it is independent of GoriyakuTag.
    category = models.CharField(
        max_length=50, choices=Category.choices, validators=[_validate_not_blank]
    )
    sort_order = models.PositiveIntegerField(default=0)
    verification_status = models.CharField(
        max_length=32, choices=KNOWLEDGE_VERIFICATION_STATUS_CHOICES, default="draft"
    )
    confidence = models.CharField(
        max_length=8, choices=KNOWLEDGE_CONFIDENCE_CHOICES, blank=True, default=""
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    publication_status = models.CharField(
        max_length=16, choices=PublicationStatus.choices, default=PublicationStatus.DRAFT
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(stable_key__regex=_HAS_NON_WHITESPACE), name="hl_key_not_blank"
            ),
            models.CheckConstraint(
                condition=Q(category__regex=_HAS_NON_WHITESPACE), name="hl_category_not_blank"
            ),
            models.CheckConstraint(
                condition=Q(
                    category__in=[
                        "architecture",
                        "cultural_heritage",
                        "nature",
                        "ritual_festival",
                        "historical_site",
                        "experience",
                    ]
                ),
                name="hl_category_valid",
            ),
            models.CheckConstraint(
                condition=Q(
                    verification_status__in=[v for v, _ in KNOWLEDGE_VERIFICATION_STATUS_CHOICES]
                ),
                name="hl_verification_valid",
            ),
            models.CheckConstraint(
                condition=Q(confidence__in=["", *[v for v, _ in KNOWLEDGE_CONFIDENCE_CHOICES]]),
                name="hl_confidence_valid",
            ),
            models.CheckConstraint(
                condition=~Q(verification_status__in=["source_confirmed", "reviewed"])
                | Q(verified_at__isnull=False),
                name="hl_verified_at_required",
            ),
            models.CheckConstraint(
                condition=Q(publication_status__in=["draft", "published", "archived"]),
                name="hl_publication_valid",
            ),
        ]

    def __str__(self):
        return self.stable_key

    def clean(self):
        super().clean()
        _validate_verified_at_consistency(self.verification_status, self.verified_at)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


@receiver(pre_delete, sender=ShrineHighlight, dispatch_uid="highlights_protect_non_draft_delete")
def protect_non_draft_highlight(sender, instance, using, **kwargs):
    # Collector emits this signal within its delete transaction. Lock and read
    # current persisted status, not a potentially stale model/admin instance.
    status = (
        sender.objects.using(using)
        .select_for_update()
        .filter(pk=instance.pk)
        .values_list("publication_status", flat=True)
        .first()
    )
    if status is not None and status != ShrineHighlight.PublicationStatus.DRAFT:
        raise ProtectedError(
            "Published/archived Highlights must be archived, not deleted.", [instance]
        )


class ShrineHighlightTranslation(models.Model):
    class Language(models.TextChoices):
        JA = "ja", "Japanese"
        EN = "en", "English"

    class ReviewStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    highlight = models.ForeignKey(
        ShrineHighlight, on_delete=models.CASCADE, related_name="translations"
    )
    language_code = models.CharField(max_length=2, choices=Language.choices)
    name = models.CharField(max_length=255, validators=[_validate_not_blank])
    description = models.TextField(blank=True, default="")
    historical_connection = models.TextField(blank=True, default="")
    # 境内での位置の目安（例: 鳥居をくぐって右手）。言語で書き方が変わるため翻訳側に持つ。
    location_hint = models.CharField(max_length=255, blank=True, default="")
    review_status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.DRAFT
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["language_code", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["highlight", "language_code"], name="hl_translation_language_unique"
            ),
            models.CheckConstraint(
                condition=Q(language_code__in=["ja", "en"]), name="hl_language_valid"
            ),
            models.CheckConstraint(
                condition=Q(name__regex=_HAS_NON_WHITESPACE), name="hl_translation_name_not_blank"
            ),
            models.CheckConstraint(
                condition=Q(review_status__in=["draft", "approved", "rejected"]),
                name="hl_review_valid",
            ),
            models.CheckConstraint(
                condition=~Q(review_status="approved") | Q(reviewed_at__isnull=False),
                name="hl_reviewed_at_required",
            ),
        ]

    def __str__(self):
        return f"{self.highlight_id}:{self.language_code}:{self.name}"

    # 承認後に変わったら承認を取り消す項目（PR-3）。利用者に見える文章のすべて。
    REVIEWED_CONTENT_FIELDS = ("name", "description", "historical_connection", "location_hint")

    def clean(self):
        super().clean()
        if self.review_status == self.ReviewStatus.APPROVED and self.reviewed_at is None:
            raise ValidationError({"reviewed_at": "Approved translations require reviewed_at."})

    def _invalidate_approval_if_content_changed(self) -> None:
        """保存済みの状態がapprovedで、文章が変わっていたらdraftへ戻す。

        同じ保存で文章を変えて承認し直すことはできない（承認は文章を変えない保存で行う）。
        QuerySet.update / bulk_update / raw SQLはsaveを通らないため対象外。
        """
        if self.pk is None:
            return
        stored = (
            type(self)
            .objects.filter(pk=self.pk)
            .values("review_status", *self.REVIEWED_CONTENT_FIELDS)
            .first()
        )
        if stored is None or stored["review_status"] != self.ReviewStatus.APPROVED:
            return
        changed = any(
            getattr(self, field) != stored[field] for field in self.REVIEWED_CONTENT_FIELDS
        )
        if changed:
            self.review_status = self.ReviewStatus.DRAFT
            self.reviewed_at = None

    def save(self, *args, **kwargs):
        self._invalidate_approval_if_content_changed()
        self.full_clean()
        return super().save(*args, **kwargs)


class ShrineHighlightSource(models.Model):
    highlight = models.ForeignKey(
        ShrineHighlight, on_delete=models.CASCADE, related_name="source_links"
    )
    source = models.ForeignKey(
        "temples.ShrineKnowledgeSource", on_delete=models.PROTECT, related_name="highlight_links"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["highlight", "source"], name="hl_source_unique"),
        ]


class ShrineHighlightHistory(models.Model):
    highlight = models.ForeignKey(
        ShrineHighlight, on_delete=models.CASCADE, related_name="history_links"
    )
    history = models.ForeignKey(
        "temples.ShrineHistory", on_delete=models.PROTECT, related_name="highlight_links"
    )
    shrine = models.ForeignKey(
        "temples.Shrine", on_delete=models.CASCADE, related_name="highlight_history_links"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["highlight", "history"], name="hl_history_unique"),
        ]

    def clean(self):
        super().clean()
        if self.highlight_id and self.history_id and self.shrine_id:
            if (
                self.highlight.shrine_id != self.shrine_id
                or self.history.shrine_id != self.shrine_id
            ):
                raise ValidationError(
                    {"shrine": "Highlight and History must belong to this shrine."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
