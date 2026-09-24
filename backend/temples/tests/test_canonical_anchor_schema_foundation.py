"""Canonical Shrine Anchor Schema Foundation の契約テスト。

正本: docs/core/split-anchor-architecture.md（PHASE_1）

対象:
    temples/models_canonical_anchor.py
    temples/domain/canonical_anchor.py
    temples/migrations/0115_canonical_anchor_schema_foundation.py        （主系 lineage）
    temples/migrations_nogis/0014_canonical_anchor_schema_foundation.py  （NoGIS lineage）

DB制約は「model save（full_clean）で ValidationError」と
「validation を経由しない bulk_create で IntegrityError」の両経路で確認する。
主系 migration はこのprocessで graph として読み込まない
（`0045_add_location_state_only` が GDAL を要求するため。
test_migration_0108_remove_legacy_temples_models.py と同じ理由）。
主系 lineage の `makemigrations --check` / migrate / rollback は PR の Migration QA で確認する。
"""

from __future__ import annotations

import importlib
import io
import itertools
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, connection, migrations, transaction
from django.db.migrations.loader import MigrationLoader
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from temples.domain.canonical_anchor import (
    CanonicalMeanError,
    compute_unweighted_component_mean,
)
from temples.models import (
    PlaceRef,
    Shrine,
    ShrineCanonicalAnchor,
    ShrineCanonicalAnchorComponent,
    ShrineCanonicalAnchorEvidence,
)

MAIN_MIGRATION = "temples.migrations.0115_canonical_anchor_schema_foundation"
NOGIS_MIGRATION = "temples.migrations_nogis.0014_canonical_anchor_schema_foundation"
NOGIS_PARENT = "0013_remove_legacy_temples_models"
NOGIS_TARGET = "0014_canonical_anchor_schema_foundation"

MODELS_CHILD_FIRST = (
    ShrineCanonicalAnchorEvidence,
    ShrineCanonicalAnchorComponent,
    ShrineCanonicalAnchor,
)


# --- helpers ------------------------------------------------------------------

_shrine_seq = itertools.count(1)


def _shrine(**kwargs):
    n = next(_shrine_seq)
    kwargs.setdefault("name_jp", f"Canonical試験神社{n}")
    kwargs.setdefault("address", f"試験県試験市{n}")
    kwargs.setdefault("latitude", 35.0 + n / 1000)
    kwargs.setdefault("longitude", 135.0 + n / 1000)
    return Shrine.objects.create(**kwargs)


def _confirmed_direct_kwargs(shrine, **overrides):
    kwargs = dict(
        shrine=shrine,
        status="CONFIRMED",
        subject="本殿",
        subject_type="SINGLE_PRINCIPAL_UNIT",
        point_method="DIRECT_POINT",
        latitude=35.5,
        longitude=135.5,
        verified_at=timezone.now(),
    )
    kwargs.update(overrides)
    return kwargs


def _hold_kwargs(shrine, **overrides):
    kwargs = dict(shrine=shrine, status="HOLD_POSITION_REVIEW")
    kwargs.update(overrides)
    return kwargs


def _assert_rejected_both_paths(model, **kwargs):
    """model save は ValidationError、validationを経由しない insert は IntegrityError。"""
    count_before = model.objects.count()
    with pytest.raises(ValidationError):
        model.objects.create(**kwargs)
    assert model.objects.count() == count_before
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            model.objects.bulk_create([model(**kwargs)])


def _multi_mean_anchor(shrine, **overrides):
    """component追加前の MULTI + MEAN Anchor（HOLD、座標なし）。"""
    kwargs = dict(
        shrine=shrine,
        status="HOLD_POSITION_REVIEW",
        subject="正殿群",
        subject_type="MULTI_PRINCIPAL_UNIT",
        point_method="UNWEIGHTED_COMPONENT_MEAN",
        component_set_status="COMPLETE",
    )
    kwargs.update(overrides)
    return ShrineCanonicalAnchor.objects.create(**kwargs)


def _component(anchor, name, classification="INCLUDED", lat=None, lng=None, sort_order=0):
    return ShrineCanonicalAnchorComponent.objects.create(
        anchor=anchor,
        source_attested_name=name,
        classification=classification,
        latitude=lat,
        longitude=lng,
        sort_order=sort_order,
    )


def _confirm_with(anchor, lat, lng):
    anchor.status = "CONFIRMED"
    anchor.latitude = lat
    anchor.longitude = lng
    anchor.verified_at = timezone.now()
    anchor.save()
    return anchor


INCLUDED_POINTS = ((35.10, 135.10), (35.20, 135.40), (35.60, 135.70))


def _anchor_with_three_included(shrine):
    anchor = _multi_mean_anchor(shrine)
    for i, (lat, lng) in enumerate(INCLUDED_POINTS):
        _component(anchor, f"正殿{i}", lat=lat, lng=lng, sort_order=i)
    return anchor


def _mean_of(points):
    return compute_unweighted_component_mean(
        [SimpleNamespace(classification="INCLUDED", latitude=a, longitude=b) for a, b in points]
    )


# --- Anchor -------------------------------------------------------------------


@pytest.mark.django_db
def test_01_one_shrine_has_at_most_one_anchor():
    shrine = _shrine()
    ShrineCanonicalAnchor.objects.create(**_hold_kwargs(shrine))
    with pytest.raises(ValidationError):
        ShrineCanonicalAnchor.objects.create(**_hold_kwargs(shrine))
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ShrineCanonicalAnchor.objects.bulk_create(
                [ShrineCanonicalAnchor(**_hold_kwargs(shrine))]
            )
    assert ShrineCanonicalAnchor.objects.filter(shrine=shrine).count() == 1


@pytest.mark.django_db
def test_02_anchor_row_absent_is_valid_not_adjudicated():
    shrine = _shrine()
    shrine.full_clean()
    assert not ShrineCanonicalAnchor.objects.filter(shrine=shrine).exists()
    with pytest.raises(ShrineCanonicalAnchor.DoesNotExist):
        _ = Shrine.objects.get(pk=shrine.pk).canonical_anchor


@pytest.mark.django_db
def test_03_hold_with_null_coordinate_is_allowed():
    anchor = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    anchor.refresh_from_db()
    assert anchor.latitude is None and anchor.longitude is None


@pytest.mark.django_db
def test_04_hold_with_coordinate_is_rejected():
    _assert_rejected_both_paths(
        ShrineCanonicalAnchor, **_hold_kwargs(_shrine(), latitude=35.0, longitude=135.0)
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "subject_type", ["SINGLE_PRINCIPAL_UNIT", "MULTI_PRINCIPAL_UNIT", "NON_BUILDING_RITUAL_CENTER"]
)
def test_05_confirmed_with_required_fields_is_allowed(subject_type):
    anchor = ShrineCanonicalAnchor.objects.create(
        **_confirmed_direct_kwargs(_shrine(), subject_type=subject_type)
    )
    anchor.refresh_from_db()
    assert anchor.status == "CONFIRMED"
    assert anchor.subject_type == subject_type


@pytest.mark.django_db
@pytest.mark.parametrize(
    "missing",
    [
        {"subject": ""},
        {"subject_type": None},
        {"point_method": None},
        {"latitude": None, "longitude": None},
        {"verified_at": None},
    ],
)
def test_06_confirmed_missing_required_field_is_rejected(missing):
    _assert_rejected_both_paths(
        ShrineCanonicalAnchor, **_confirmed_direct_kwargs(_shrine(), **missing)
    )


@pytest.mark.django_db
def test_06b_confirmed_whitespace_subject_is_rejected():
    with pytest.raises(ValidationError):
        ShrineCanonicalAnchor.objects.create(**_confirmed_direct_kwargs(_shrine(), subject="   "))


@pytest.mark.django_db
def test_07_latitude_only_is_rejected():
    _assert_rejected_both_paths(
        ShrineCanonicalAnchor, **_confirmed_direct_kwargs(_shrine(), longitude=None)
    )


@pytest.mark.django_db
def test_08_longitude_only_is_rejected():
    _assert_rejected_both_paths(
        ShrineCanonicalAnchor, **_confirmed_direct_kwargs(_shrine(), latitude=None)
    )


@pytest.mark.django_db
@pytest.mark.parametrize("lat", [-90.0001, 90.0001])
def test_09_latitude_out_of_range_is_rejected(lat):
    _assert_rejected_both_paths(
        ShrineCanonicalAnchor, **_confirmed_direct_kwargs(_shrine(), latitude=lat)
    )


@pytest.mark.django_db
@pytest.mark.parametrize("lng", [-180.0001, 180.0001])
def test_10_longitude_out_of_range_is_rejected(lng):
    _assert_rejected_both_paths(
        ShrineCanonicalAnchor, **_confirmed_direct_kwargs(_shrine(), longitude=lng)
    )


@pytest.mark.django_db
@pytest.mark.parametrize("lat, lng", [(-90.0, -180.0), (90.0, 180.0)])
def test_10b_coordinate_range_bounds_are_inclusive(lat, lng):
    ShrineCanonicalAnchor.objects.create(
        **_confirmed_direct_kwargs(_shrine(), latitude=lat, longitude=lng)
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field, value",
    [
        ("status", "NOT_ADJUDICATED"),
        ("subject_type", "MULTI"),
        ("point_method", "WEIGHTED_MEAN"),
        ("component_set_status", "PARTIAL"),
    ],
)
def test_10c_unknown_enum_value_is_rejected(field, value):
    _assert_rejected_both_paths(
        ShrineCanonicalAnchor, **_confirmed_direct_kwargs(_shrine(), **{field: value})
    )


@pytest.mark.django_db
def test_10d_confirmed_with_incomplete_component_set_is_rejected():
    _assert_rejected_both_paths(
        ShrineCanonicalAnchor,
        **_confirmed_direct_kwargs(_shrine(), component_set_status="INCOMPLETE"),
    )


@pytest.mark.django_db
def test_10e_hold_may_record_incomplete_component_set():
    ShrineCanonicalAnchor.objects.create(
        **_hold_kwargs(
            _shrine(),
            subject_type="MULTI_PRINCIPAL_UNIT",
            point_method="UNWEIGHTED_COMPONENT_MEAN",
            component_set_status="INCOMPLETE",
        )
    )


# --- Component ----------------------------------------------------------------


@pytest.mark.django_db
def test_11_classification_accepts_exactly_three_values():
    anchor = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    for value in ("INCLUDED", "EXCLUDED", "UNCLASSIFIED"):
        _component(anchor, f"社殿-{value}", classification=value)
    assert set(ShrineCanonicalAnchorComponent._meta.get_field("classification").choices) == {
        ("INCLUDED", "INCLUDED"),
        ("EXCLUDED", "EXCLUDED"),
        ("UNCLASSIFIED", "UNCLASSIFIED"),
    }
    _assert_rejected_both_paths(
        ShrineCanonicalAnchorComponent,
        anchor=anchor,
        source_attested_name="拝殿",
        classification="MAYBE",
    )


@pytest.mark.django_db
def test_12_included_with_null_coordinate_is_allowed_in_progress():
    anchor = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    component = _component(anchor, "東本殿")
    component.refresh_from_db()
    assert component.latitude is None and component.longitude is None


@pytest.mark.django_db
def test_13_included_with_coordinate_pair_is_allowed():
    anchor = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    component = _component(anchor, "東本殿", lat=35.1, lng=135.1)
    component.refresh_from_db()
    assert (component.latitude, component.longitude) == (35.1, 135.1)


@pytest.mark.django_db
@pytest.mark.parametrize("classification", ["EXCLUDED", "UNCLASSIFIED"])
def test_14_15_non_included_with_coordinate_is_rejected(classification):
    anchor = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    _assert_rejected_both_paths(
        ShrineCanonicalAnchorComponent,
        anchor=anchor,
        source_attested_name="楼門",
        classification=classification,
        latitude=35.1,
        longitude=135.1,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("lat, lng", [(35.1, None), (None, 135.1)])
def test_16_component_single_sided_coordinate_is_rejected(lat, lng):
    anchor = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    _assert_rejected_both_paths(
        ShrineCanonicalAnchorComponent,
        anchor=anchor,
        source_attested_name="西本殿",
        classification="INCLUDED",
        latitude=lat,
        longitude=lng,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("lat, lng", [(90.5, 135.0), (35.0, -180.5)])
def test_16b_component_coordinate_out_of_range_is_rejected(lat, lng):
    anchor = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    _assert_rejected_both_paths(
        ShrineCanonicalAnchorComponent,
        anchor=anchor,
        source_attested_name="西本殿",
        classification="INCLUDED",
        latitude=lat,
        longitude=lng,
    )


@pytest.mark.django_db
def test_16c_source_attested_name_is_kept_verbatim_and_required():
    anchor = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    raw = "  第一殿（東御本殿）  "
    component = _component(anchor, raw)
    component.refresh_from_db()
    assert component.source_attested_name == raw
    _assert_rejected_both_paths(
        ShrineCanonicalAnchorComponent,
        anchor=anchor,
        source_attested_name="",
        classification="INCLUDED",
    )


# --- Mean / Cross-row ---------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("component_set_status", [None, "INCOMPLETE"])
def test_17_multi_mean_confirmed_requires_complete(component_set_status):
    shrine = _shrine()
    anchor = _anchor_with_three_included(shrine)
    anchor.component_set_status = component_set_status
    anchor.save()
    mean = _mean_of(INCLUDED_POINTS)
    with pytest.raises(ValidationError):
        _confirm_with(anchor, mean.latitude, mean.longitude)
    # DB制約単体でも拒否される（validationを経由しない経路）。
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ShrineCanonicalAnchor.objects.filter(pk=anchor.pk).update(
                status="CONFIRMED",
                latitude=mean.latitude,
                longitude=mean.longitude,
                verified_at=timezone.now(),
            )


@pytest.mark.django_db
def test_18_zero_included_components_is_rejected():
    anchor = _multi_mean_anchor(_shrine())
    _component(anchor, "楼門", classification="EXCLUDED")
    _component(anchor, "摂社", classification="UNCLASSIFIED")
    with pytest.raises(ValidationError):
        _confirm_with(anchor, 35.0, 135.0)
    # componentが1件も無い新規 CONFIRMED MEAN も拒否される。
    with pytest.raises(ValidationError):
        _multi_mean_anchor(
            _shrine(),
            status="CONFIRMED",
            latitude=35.0,
            longitude=135.0,
            verified_at=timezone.now(),
        )


@pytest.mark.django_db
def test_19_included_without_coordinate_is_rejected():
    anchor = _multi_mean_anchor(_shrine())
    _component(anchor, "東本殿", lat=35.1, lng=135.1)
    _component(anchor, "西本殿")  # 座標未確認
    with pytest.raises(ValidationError):
        _confirm_with(anchor, 35.1, 135.1)


@pytest.mark.django_db
def test_20_mean_from_all_included_is_allowed():
    anchor = _anchor_with_three_included(_shrine())
    mean = _mean_of(INCLUDED_POINTS)
    _confirm_with(anchor, mean.latitude, mean.longitude)
    anchor.refresh_from_db()
    assert anchor.status == "CONFIRMED"
    assert (anchor.latitude, anchor.longitude) == (mean.latitude, mean.longitude)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "subset",
    [INCLUDED_POINTS[:2], INCLUDED_POINTS[1:], INCLUDED_POINTS[:1]],
)
def test_21_mean_from_partial_components_is_rejected(subset):
    anchor = _anchor_with_three_included(_shrine())
    partial = _mean_of(subset)
    with pytest.raises(ValidationError):
        _confirm_with(anchor, partial.latitude, partial.longitude)


@pytest.mark.django_db
def test_22_excluded_and_unclassified_do_not_enter_mean():
    included = ((35.0, 135.0), (35.2, 135.2))
    anchor = _multi_mean_anchor(_shrine())
    _component(anchor, "東本殿", lat=included[0][0], lng=included[0][1])
    _component(anchor, "西本殿", lat=included[1][0], lng=included[1][1])
    _component(anchor, "楼門", classification="EXCLUDED")
    _component(anchor, "若宮", classification="UNCLASSIFIED")
    mean = _mean_of(included)
    _confirm_with(anchor, mean.latitude, mean.longitude)

    # helper単体: 座標付きで渡されても EXCLUDED / UNCLASSIFIED は計算に入らない。
    point = compute_unweighted_component_mean(
        [
            SimpleNamespace(classification="INCLUDED", latitude=10.0, longitude=20.0),
            SimpleNamespace(classification="INCLUDED", latitude=12.0, longitude=22.0),
            SimpleNamespace(classification="EXCLUDED", latitude=80.0, longitude=170.0),
            SimpleNamespace(classification="UNCLASSIFIED", latitude=-80.0, longitude=-170.0),
        ]
    )
    assert (point.latitude, point.longitude) == (11.0, 21.0)


def test_23_mean_is_order_independent():
    # 浮動小数の加算順で結果が変わりやすい値を使う。
    points = [(0.1, 0.7), (0.2, 1e-16), (0.3, 1.0), (1e-16, 0.1), (35.123456789, 139.987654321)]
    results = {
        (p.latitude, p.longitude)
        for p in (_mean_of(perm) for perm in itertools.permutations(points))
    }
    assert len(results) == 1


def test_23b_mean_helper_fails_closed():
    with pytest.raises(CanonicalMeanError):
        compute_unweighted_component_mean([])
    with pytest.raises(CanonicalMeanError):
        compute_unweighted_component_mean(
            [SimpleNamespace(classification="EXCLUDED", latitude=None, longitude=None)]
        )
    with pytest.raises(CanonicalMeanError):
        compute_unweighted_component_mean(
            [
                SimpleNamespace(classification="INCLUDED", latitude=1.0, longitude=1.0),
                SimpleNamespace(classification="INCLUDED", latitude=None, longitude=None),
            ]
        )


@pytest.mark.django_db
def test_23c_db_order_does_not_change_accepted_mean():
    shrine_a, shrine_b = _shrine(), _shrine()
    a = _multi_mean_anchor(shrine_a)
    b = _multi_mean_anchor(shrine_b)
    for i, (lat, lng) in enumerate(INCLUDED_POINTS):
        _component(a, f"正殿{i}", lat=lat, lng=lng, sort_order=i)
        _component(b, f"正殿{i}", lat=lat, lng=lng, sort_order=len(INCLUDED_POINTS) - i)
    mean = _mean_of(INCLUDED_POINTS)
    _confirm_with(a, mean.latitude, mean.longitude)
    _confirm_with(b, mean.latitude, mean.longitude)


@pytest.mark.django_db
def test_23d_component_changes_cannot_break_confirmed_mean():
    anchor = _anchor_with_three_included(_shrine())
    mean = _mean_of(INCLUDED_POINTS)
    _confirm_with(anchor, mean.latitude, mean.longitude)
    first = anchor.components.order_by("sort_order").first()

    # 新しい INCLUDED の追加
    with pytest.raises(ValidationError):
        _component(anchor, "追加本殿", lat=35.9, lng=135.9)
    # INCLUDED 座標の変更
    first.latitude = 35.15
    with pytest.raises(ValidationError):
        first.save()
    first.refresh_from_db()
    # INCLUDED -> EXCLUDED への再分類
    first.classification = "EXCLUDED"
    first.latitude = first.longitude = None
    with pytest.raises(ValidationError):
        first.save()
    first.refresh_from_db()
    # INCLUDED の削除
    with pytest.raises(ValidationError):
        first.delete()

    # mean に影響しない変更は許可する。
    _component(anchor, "楼門", classification="EXCLUDED", sort_order=9)
    first.classification_rationale = "公式由緒の記載による"
    first.save()
    assert anchor.components.filter(classification="INCLUDED").count() == 3


@pytest.mark.django_db
def test_23e_component_anchor_cannot_be_reassigned():
    a = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    b = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    component = _component(a, "東本殿")
    component.anchor = b
    with pytest.raises(ValidationError):
        component.save()


@pytest.mark.django_db
def test_23f_direct_point_does_not_use_component_mean():
    anchor = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    _component(anchor, "本殿", lat=35.1, lng=135.1)
    anchor.status = "CONFIRMED"
    anchor.subject = "本殿"
    anchor.subject_type = "SINGLE_PRINCIPAL_UNIT"
    anchor.point_method = "DIRECT_POINT"
    anchor.latitude, anchor.longitude = 35.2, 135.2
    anchor.verified_at = timezone.now()
    anchor.save()


# --- Evidence -----------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["SEMANTIC", "COORDINATE"])
def test_24_25_evidence_role_can_be_saved(role):
    anchor = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    evidence = ShrineCanonicalAnchorEvidence.objects.create(
        anchor=anchor,
        evidence_role=role,
        source_type="shrine_official",
        title="由緒",
        publisher="試験神社",
        url="https://example.invalid/yuisho",
        extraction_method="manual_reading",
        evidence_strength="primary",
        stated_precision="building",
    )
    evidence.refresh_from_db()
    assert evidence.evidence_role == role


@pytest.mark.django_db
def test_24b_unknown_evidence_role_is_rejected():
    anchor = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    _assert_rejected_both_paths(ShrineCanonicalAnchorEvidence, anchor=anchor, evidence_role="BOTH")


@pytest.mark.django_db
def test_26_evidence_component_is_nullable():
    anchor = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    evidence = ShrineCanonicalAnchorEvidence.objects.create(anchor=anchor, evidence_role="SEMANTIC")
    assert evidence.component_id is None


@pytest.mark.django_db
def test_27_evidence_with_same_anchor_component_is_allowed():
    anchor = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    component = _component(anchor, "東本殿")
    evidence = ShrineCanonicalAnchorEvidence.objects.create(
        anchor=anchor, component=component, evidence_role="COORDINATE"
    )
    assert list(component.evidences.all()) == [evidence]


@pytest.mark.django_db
def test_28_evidence_with_other_anchor_component_is_rejected():
    anchor_a = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    anchor_b = ShrineCanonicalAnchor.objects.create(**_hold_kwargs(_shrine()))
    foreign = _component(anchor_b, "他社の本殿")
    with pytest.raises(ValidationError):
        ShrineCanonicalAnchorEvidence.objects.create(
            anchor=anchor_a, component=foreign, evidence_role="COORDINATE"
        )
    assert not ShrineCanonicalAnchorEvidence.objects.exists()


# --- Migration Safety ---------------------------------------------------------


def _nogis_loader():
    with override_settings(MIGRATION_MODULES={"temples": "temples.migrations_nogis"}):
        return MigrationLoader(connection, ignore_no_migrations=True)


def _shrine_snapshot():
    return list(
        Shrine.objects.order_by("pk").values_list(
            "pk",
            "name_jp",
            "address",
            "latitude",
            "longitude",
            "location",
            "place_ref_id",
            "updated_at",
        )
    )


def _place_ref_snapshot():
    return list(PlaceRef.objects.order_by("place_id").values())


@pytest.mark.django_db
def test_29_to_32_applying_migration_leaves_existing_rows_untouched():
    """NoGIS 0014 を 0013 相当schemaへ実適用し、既存行が1bitも変わらないこと。"""
    place_ref = PlaceRef.objects.create(
        place_id="ChIJcanonical-anchor-test",
        name="PR",
        address="試験県",
        latitude=35.3,
        longitude=135.3,
    )
    _shrine(place_ref=place_ref)
    _shrine()
    shrines_before = _shrine_snapshot()
    place_refs_before = _place_ref_snapshot()
    created = [row for row in shrines_before if row[1].startswith("Canonical試験神社")]
    assert len(created) == 2
    assert all(row[3] is not None and row[4] is not None and row[5] is not None for row in created)
    assert any(row[6] == place_ref.place_id for row in created)

    loader = _nogis_loader()
    assert loader.graph.leaf_nodes("temples") == [("temples", NOGIS_TARGET)]
    before_state = loader.project_state(("temples", NOGIS_PARENT))
    with connection.schema_editor() as schema_editor:
        for model in MODELS_CHILD_FIRST:
            schema_editor.delete_model(model)
    assert not {m._meta.db_table for m in MODELS_CHILD_FIRST} & set(
        connection.introspection.table_names()
    )

    migration = loader.disk_migrations[("temples", NOGIS_TARGET)]
    with CaptureQueriesContext(connection) as ctx:
        with connection.schema_editor() as schema_editor:
            migration.apply(before_state.clone(), schema_editor)

    assert {m._meta.db_table for m in MODELS_CHILD_FIRST} <= set(
        connection.introspection.table_names()
    )
    # 29 / 30 / 31: Shrine件数・座標・location 不変
    assert _shrine_snapshot() == shrines_before
    # 32: PlaceRef 不変
    assert _place_ref_snapshot() == place_refs_before
    # backfill = 0
    assert ShrineCanonicalAnchor.objects.count() == 0
    assert ShrineCanonicalAnchorComponent.objects.count() == 0
    assert ShrineCanonicalAnchorEvidence.objects.count() == 0
    # 33: DMLを1文も発行しない
    dml = [
        q["sql"]
        for q in ctx.captured_queries
        if re.match(r"\s*(INSERT|UPDATE|DELETE)\b", q["sql"], re.IGNORECASE)
    ]
    assert dml == []


@pytest.mark.parametrize("module_path", [MAIN_MIGRATION, NOGIS_MIGRATION])
def test_33_migration_contains_no_data_operation(module_path):
    migration = importlib.import_module(module_path).Migration
    allowed = (migrations.CreateModel, migrations.AddConstraint, migrations.AddIndex)
    assert migration.operations
    for operation in migration.operations:
        assert isinstance(operation, allowed), type(operation).__name__
    created = [op.name for op in migration.operations if isinstance(op, migrations.CreateModel)]
    assert created == [
        "ShrineCanonicalAnchor",
        "ShrineCanonicalAnchorComponent",
        "ShrineCanonicalAnchorEvidence",
    ]
    # Shrine / PlaceRef への操作を含まない（Shrine.location にも触れない）。
    touched = {getattr(op, "model_name", None) for op in migration.operations} - {None}
    assert touched <= {
        "shrinecanonicalanchor",
        "shrinecanonicalanchorcomponent",
        "shrinecanonicalanchorevidence",
    }


def _normalized_operations(module_path):
    normalized = []
    for operation in importlib.import_module(module_path).Migration.operations:
        name, args, kwargs = operation.deconstruct()
        if "fields" in kwargs:
            kwargs = dict(kwargs)
            kwargs["fields"] = [(n, f.deconstruct()[1:]) for n, f in kwargs["fields"]]
        normalized.append((name, args, kwargs))
    return normalized


def test_34_standard_and_nogis_migrations_are_logically_identical():
    main = importlib.import_module(MAIN_MIGRATION).Migration
    nogis = importlib.import_module(NOGIS_MIGRATION).Migration
    assert main.dependencies == [("temples", "0114_f6d_explicit_place_ref_backfill")]
    assert nogis.dependencies == [("temples", NOGIS_PARENT)]
    assert _normalized_operations(MAIN_MIGRATION) == _normalized_operations(NOGIS_MIGRATION)


def test_34b_no_canonical_point_field_and_no_derived_fields():
    for model in (ShrineCanonicalAnchor, ShrineCanonicalAnchorComponent):
        names = {f.name for f in model._meta.get_fields()}
        assert "canonical_location" not in names
        assert "location" not in names
        assert "component_count" not in names
        assert "canonical_navigation_delta_m" not in names
    assert {f.name for f in ShrineCanonicalAnchor._meta.concrete_fields} == {
        "id",
        "shrine",
        "status",
        "subject",
        "subject_type",
        "point_method",
        "component_set_status",
        "latitude",
        "longitude",
        "verified_at",
        "note",
        "created_at",
        "updated_at",
    }


def test_35_makemigrations_check_passes():
    out, err = io.StringIO(), io.StringIO()
    try:
        call_command("makemigrations", "temples", "--check", "--dry-run", stdout=out, stderr=err)
    except SystemExit as exc:
        pytest.fail(
            "makemigrations --check reported pending model changes:\n"
            f"stdout={out.getvalue()}\nstderr={err.getvalue()}\nexit_code={exc.code}"
        )


# --- Public Runtime Boundary --------------------------------------------------

_BACKEND = Path(__file__).resolve().parents[2]
_ALLOWED_REFERENCES = {
    "temples/models.py",
    "temples/models_canonical_anchor.py",
    "temples/domain/canonical_anchor.py",
    "temples/migrations/0115_canonical_anchor_schema_foundation.py",
    "temples/migrations_nogis/0014_canonical_anchor_schema_foundation.py",
}


def test_36_no_runtime_consumer_reads_canonical_anchor():
    """Serializer / API / Compass / Map / distance / route 等は Canonical を読まない。"""
    pattern = re.compile(r"canonical_anchor|ShrineCanonicalAnchor|domain\.canonical_anchor")
    offenders = []
    for path in _BACKEND.rglob("*.py"):
        rel = path.relative_to(_BACKEND).as_posix()
        if "/tests/" in f"/{rel}" or rel.startswith(("tests/", ".venv/", "venv/")):
            continue
        if rel in _ALLOWED_REFERENCES:
            continue
        if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
            offenders.append(rel)
    assert offenders == []
