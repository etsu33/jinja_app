# backend/temples/models_canonical_anchor.py
"""Canonical Shrine Anchor（神社中心座標）Schema Foundation.

正本: docs/core/split-anchor-architecture.md（PHASE_1）

    Shrine
     └── 1 : 0..1 ShrineCanonicalAnchor
                    ├── 1 : N ShrineCanonicalAnchorComponent
                    └── 1 : N ShrineCanonicalAnchorEvidence

境界（変更しないこと）:
    - `Shrine.latitude / longitude / location` は Visitor / Navigation Anchor
      （参拝ナビ座標）のまま。本moduleはそれらを読まず、書かず、コピーしない。
    - Anchor row不在 = NOT_ADJUDICATED。空rowを作らない。
    - Canonical欠損時にNavigation座標へfallbackしない。
    - `ShrineKnowledgeSource` をEvidenceとして流用しない。
    - Canonical側にPointFieldを持たない（scalar lat/lngのみ）。

保存しない派生値（意図的な非保存 -- 追加しないこと）:
    component_count               -> INCLUDED componentから導出する
    canonical_navigation_delta_m  -> 現Navigation座標と現Canonical座標から導出する

単一row内で表現できる不変条件は CheckConstraint で保証する。
cross-row条件（component集合とのmean一致、Evidenceのcomponent所属）は
save()/delete() 上の validation で fail closed にする。
QuerySet.update() / bulk_create() はこのvalidationを経由しないため使用しないこと。
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Q
from temples.domain.canonical_anchor import (
    ANCHOR_STATUS_CONFIRMED,
    ANCHOR_STATUS_HOLD_POSITION_REVIEW,
    ANCHOR_STATUSES,
    COMPONENT_CLASSIFICATIONS,
    COMPONENT_INCLUDED,
    COMPONENT_SET_STATUS_COMPLETE,
    COMPONENT_SET_STATUS_INCOMPLETE,
    COMPONENT_SET_STATUSES,
    EVIDENCE_ROLES,
    POINT_METHOD_UNWEIGHTED_COMPONENT_MEAN,
    POINT_METHODS,
    SUBJECT_TYPE_MULTI_PRINCIPAL_UNIT,
    SUBJECT_TYPES,
    CanonicalMeanError,
    compute_unweighted_component_mean,
    requires_component_mean,
)


def _choices(values):
    return [(v, v) for v in values]


def _lat_field():
    return models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
    )


def _lng_field():
    return models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
    )


_LAT_LNG_PAIR = Q(latitude__isnull=True, longitude__isnull=True) | Q(
    latitude__isnull=False, longitude__isnull=False
)
_LAT_RANGE = Q(latitude__gte=-90.0) & Q(latitude__lte=90.0)
_LNG_RANGE = Q(longitude__gte=-180.0) & Q(longitude__lte=180.0)


def _validate_component_mean(*, anchor, components) -> None:
    """CONFIRMED + MULTI_PRINCIPAL_UNIT + UNWEIGHTED_COMPONENT_MEAN の cross-row 検証。"""
    if anchor.component_set_status != COMPONENT_SET_STATUS_COMPLETE:
        raise ValidationError(
            {"component_set_status": "UNWEIGHTED_COMPONENT_MEAN の確定には COMPLETE が必要です。"}
        )
    try:
        point = compute_unweighted_component_mean(components)
    except CanonicalMeanError as exc:
        raise ValidationError(str(exc), code="canonical_mean_unavailable") from exc
    if anchor.latitude != point.latitude or anchor.longitude != point.longitude:
        raise ValidationError(
            "Anchor の latitude / longitude が INCLUDED component 全件の"
            " UNWEIGHTED_COMPONENT_MEAN と一致しません。",
            code="canonical_mean_mismatch",
        )


def _lock_anchor(anchor_id) -> None:
    """Anchor row を行lockし、Anchor / component の cross-row 検証を直列化する。"""
    if anchor_id is not None:
        list(
            ShrineCanonicalAnchor.objects.select_for_update()
            .filter(pk=anchor_id)
            .values_list("pk", flat=True)
        )


class ShrineCanonicalAnchor(models.Model):
    """神社中心座標の審査結果・semantic subject・代表点算出方法・最終確定座標。"""

    shrine = models.OneToOneField(
        "temples.Shrine",
        on_delete=models.CASCADE,
        related_name="canonical_anchor",
    )
    status = models.CharField(max_length=32, choices=_choices(ANCHOR_STATUSES))
    # 何を principal ritual unit / center として扱ったか。
    subject = models.TextField(blank=True, default="")
    subject_type = models.CharField(
        max_length=32, choices=_choices(SUBJECT_TYPES), null=True, blank=True
    )
    point_method = models.CharField(
        max_length=32, choices=_choices(POINT_METHODS), null=True, blank=True
    )
    # 単一対象・非建物対象では必須としない（split-anchor-architecture.md §6）。
    component_set_status = models.CharField(
        max_length=16, choices=_choices(COMPONENT_SET_STATUSES), null=True, blank=True
    )
    # CONFIRMED の場合だけ保持する最終座標。候補値・途中経過は書かない。
    latitude = _lat_field()
    longitude = _lng_field()
    verified_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "temples_shrine_canonical_anchor"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=ANCHOR_STATUSES),
                name="chk_canon_anchor_status",
            ),
            models.CheckConstraint(
                condition=Q(subject_type__isnull=True) | Q(subject_type__in=SUBJECT_TYPES),
                name="chk_canon_anchor_subject_type",
            ),
            models.CheckConstraint(
                condition=Q(point_method__isnull=True) | Q(point_method__in=POINT_METHODS),
                name="chk_canon_anchor_point_method",
            ),
            models.CheckConstraint(
                condition=Q(component_set_status__isnull=True)
                | Q(component_set_status__in=COMPONENT_SET_STATUSES),
                name="chk_canon_anchor_component_set_status",
            ),
            models.CheckConstraint(condition=_LAT_LNG_PAIR, name="chk_canon_anchor_lat_lng_pair"),
            models.CheckConstraint(condition=_LAT_RANGE, name="chk_canon_anchor_lat_range"),
            models.CheckConstraint(condition=_LNG_RANGE, name="chk_canon_anchor_lng_range"),
            # HOLD_POSITION_REVIEW は最終座標を持たない。
            models.CheckConstraint(
                condition=~Q(status=ANCHOR_STATUS_HOLD_POSITION_REVIEW)
                | Q(latitude__isnull=True, longitude__isnull=True),
                name="chk_canon_anchor_hold_no_coordinate",
            ),
            # CONFIRMED の最低条件（split-anchor-architecture.md §3.3 / §10.3）。
            models.CheckConstraint(
                condition=~Q(status=ANCHOR_STATUS_CONFIRMED)
                | (
                    ~Q(subject="")
                    & Q(
                        subject_type__isnull=False,
                        point_method__isnull=False,
                        latitude__isnull=False,
                        longitude__isnull=False,
                        verified_at__isnull=False,
                    )
                ),
                name="chk_canon_anchor_confirmed_required",
            ),
            # INCOMPLETE の場合 CONFIRMED にしない（split-anchor-architecture.md §6）。
            models.CheckConstraint(
                condition=~Q(
                    status=ANCHOR_STATUS_CONFIRMED,
                    component_set_status=COMPONENT_SET_STATUS_INCOMPLETE,
                ),
                name="chk_canon_anchor_confirmed_not_incomplete",
            ),
            # CONFIRMED + MULTI + MEAN -> COMPLETE（split-anchor-architecture.md §10.5）。
            models.CheckConstraint(
                condition=~Q(
                    status=ANCHOR_STATUS_CONFIRMED,
                    subject_type=SUBJECT_TYPE_MULTI_PRINCIPAL_UNIT,
                    point_method=POINT_METHOD_UNWEIGHTED_COMPONENT_MEAN,
                )
                # NULL = 'COMPLETE' は SQL上 NULL となり CHECK を素通りするため、
                # isnull=False を明示して NULL を拒否する。
                | Q(
                    component_set_status__isnull=False,
                    component_set_status=COMPONENT_SET_STATUS_COMPLETE,
                ),
                name="chk_canon_anchor_multi_mean_complete",
            ),
        ]

    def __str__(self) -> str:
        return f"ShrineCanonicalAnchor(shrine={self.shrine_id}, status={self.status})"

    def clean(self) -> None:
        super().clean()
        if self.status == ANCHOR_STATUS_CONFIRMED and not (self.subject or "").strip():
            raise ValidationError({"subject": "CONFIRMED の場合 subject は必須です。"})
        if requires_component_mean(
            status=self.status, subject_type=self.subject_type, point_method=self.point_method
        ):
            components = list(self.components.all()) if self.pk is not None else []
            _validate_component_mean(anchor=self, components=components)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.pk is not None:
                # component側の並行変更と cross-row 検証を直列化する。
                _lock_anchor(self.pk)
            self.full_clean()
            return super().save(*args, **kwargs)


class ShrineCanonicalAnchorComponent(models.Model):
    """複数主要構成物を扱う場合の監査可能な入力（A-7b Component Membership）。"""

    anchor = models.ForeignKey(
        ShrineCanonicalAnchor,
        on_delete=models.CASCADE,
        related_name="components",
    )
    # Sourceが実際に用いた構成物名。正規化名称へ置換しない。
    source_attested_name = models.TextField()
    classification = models.CharField(max_length=16, choices=_choices(COMPONENT_CLASSIFICATIONS))
    classification_rationale = models.TextField(blank=True, default="")
    # INCLUDED componentの確認済み座標。INCLUDEDは調査途中のNULLを許可する。
    latitude = _lat_field()
    longitude = _lng_field()
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "temples_shrine_canonical_anchor_component"
        ordering = ["anchor_id", "sort_order", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(classification__in=COMPONENT_CLASSIFICATIONS),
                name="chk_canon_component_classification",
            ),
            models.CheckConstraint(
                condition=~Q(source_attested_name=""),
                name="chk_canon_component_name_nonempty",
            ),
            models.CheckConstraint(
                condition=_LAT_LNG_PAIR, name="chk_canon_component_lat_lng_pair"
            ),
            models.CheckConstraint(condition=_LAT_RANGE, name="chk_canon_component_lat_range"),
            models.CheckConstraint(condition=_LNG_RANGE, name="chk_canon_component_lng_range"),
            # EXCLUDED / UNCLASSIFIED は座標を持たない。
            models.CheckConstraint(
                condition=Q(classification=COMPONENT_INCLUDED)
                | Q(latitude__isnull=True, longitude__isnull=True),
                name="chk_canon_component_coord_included_only",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.source_attested_name} ({self.classification})"

    def _persisted_anchor_id(self):
        if self.pk is None:
            return None
        return type(self).objects.filter(pk=self.pk).values_list("anchor_id", flat=True).first()

    def _validate_parent_anchor(self, *, removing: bool) -> None:
        """変更後のcomponent集合が親Anchorの確定meanを壊さないことを検証する。"""
        anchor = ShrineCanonicalAnchor.objects.get(pk=self.anchor_id)
        if not requires_component_mean(
            status=anchor.status,
            subject_type=anchor.subject_type,
            point_method=anchor.point_method,
        ):
            return
        components = [c for c in anchor.components.all() if c.pk != self.pk]
        if not removing:
            components.append(self)
        _validate_component_mean(anchor=anchor, components=components)

    def clean(self) -> None:
        super().clean()
        if not (self.source_attested_name or "").strip():
            raise ValidationError({"source_attested_name": "source_attested_name は必須です。"})
        persisted_anchor_id = self._persisted_anchor_id()
        if persisted_anchor_id is not None and persisted_anchor_id != self.anchor_id:
            # 付け替えは旧Anchorのcomponent集合とEvidence所属を同時に壊すため禁止する。
            raise ValidationError({"anchor": "既存 component の anchor は変更できません。"})

    def save(self, *args, **kwargs):
        with transaction.atomic():
            _lock_anchor(self.anchor_id)
            self.full_clean()
            self._validate_parent_anchor(removing=False)
            return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            _lock_anchor(self.anchor_id)
            self._validate_parent_anchor(removing=True)
            return super().delete(*args, **kwargs)


class ShrineCanonicalAnchorEvidence(models.Model):
    """神社中心の「意味の根拠」(SEMANTIC) と「座標値の根拠」(COORDINATE)。

    `ShrineKnowledgeSource` とは別物（split-anchor-architecture.md §8）。
    source_type / extraction_method / evidence_strength / stated_precision は
    正式taxonomy未定義のため文字列のみ（enumを発明しない）。
    """

    anchor = models.ForeignKey(
        ShrineCanonicalAnchor,
        on_delete=models.CASCADE,
        related_name="evidences",
    )
    # component固有Evidenceの場合のみ。component.anchor == anchor を必須とする。
    component = models.ForeignKey(
        ShrineCanonicalAnchorComponent,
        on_delete=models.CASCADE,
        related_name="evidences",
        null=True,
        blank=True,
    )
    evidence_role = models.CharField(max_length=16, choices=_choices(EVIDENCE_ROLES))
    source_type = models.CharField(max_length=64, blank=True, default="")
    title = models.TextField(blank=True, default="")
    publisher = models.TextField(blank=True, default="")
    url = models.CharField(max_length=2048, blank=True, default="")
    accessed_at = models.DateField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    extraction_method = models.TextField(blank=True, default="")
    evidence_strength = models.CharField(max_length=64, blank=True, default="")
    stated_precision = models.TextField(blank=True, default="")
    note = models.TextField(blank=True, default="")

    class Meta:
        db_table = "temples_shrine_canonical_anchor_evidence"
        ordering = ["anchor_id", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(evidence_role__in=EVIDENCE_ROLES),
                name="chk_canon_evidence_role",
            ),
        ]

    def __str__(self) -> str:
        return f"ShrineCanonicalAnchorEvidence(anchor={self.anchor_id}, role={self.evidence_role})"

    def clean(self) -> None:
        super().clean()
        if self.component_id is not None:
            component_anchor_id = (
                ShrineCanonicalAnchorComponent.objects.filter(pk=self.component_id)
                .values_list("anchor_id", flat=True)
                .first()
            )
            if component_anchor_id != self.anchor_id:
                raise ValidationError(
                    {"component": "component は同一 Anchor に属している必要があります。"}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
