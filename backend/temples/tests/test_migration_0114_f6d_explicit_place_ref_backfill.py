# backend/temples/tests/test_migration_0114_f6d_explicit_place_ref_backfill.py
"""Behavioral tests for temples.0114_f6d_explicit_place_ref_backfill (F-6D).

`docs/audit/place-id-shadow-identity-hardening.md` §18.

`F6D_PRESTATE_POLICY = FAIL_CLOSED`: forward runs only when the COMPLETE audited
PRE state for all three mappings is present, and raises `PreconditionViolation`
otherwise (aborting the whole `RunPython` transaction). The only clean no-op is a
genuinely absent subject, proven symmetric with reverse.

Forward/reverse callables are exercised directly against the real models via a
tiny `apps` + `schema_editor` shim, matching the 0095-0100 / 0109-0113
migration-test pattern. That pattern is GIS/nogis-independent, which matters
here: the test database is built from `temples.migrations_nogis` (13 condensed
migrations), so a real `MigrationExecutor` run of `temples.0114` is not
reachable from the test lineage at all. The callable contract is therefore the
testable surface, exactly as it is for 0100.
"""

import importlib
from datetime import datetime, timezone

import pytest
from django.db import connection

from temples.models import PlaceRef, Shrine, ShrineInteractionLog

_mod = importlib.import_module("temples.migrations.0114_f6d_explicit_place_ref_backfill")
forward = _mod.backfill_forward
reverse = _mod.backfill_reverse
PreconditionViolation = _mod.PreconditionViolation
PAIRS = _mod.PAIRS

PID22 = "ChIJl-MEepfxGGAR1Eo44p__GaE"
PID21 = "ChIJX19mq8nxGGARsA2kP4gX90M"
PID49 = "ChIJK11I4BGJGGAR5mZswigcu58"

EVENT_A_TS = datetime(2026, 6, 11, 7, 18, 5, 580624, tzinfo=timezone.utc)
EVENT_B_TS = datetime(2026, 6, 11, 8, 0, 22, 85501, tzinfo=timezone.utc)

CORRECTED_49 = (35.6717809, 139.799519)

S21 = dict(
    name_jp="長太稲荷神社",
    address="日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０",
    latitude=35.660614,
    longitude=139.6017688,
)
S22 = dict(
    name_jp="給田六所神社",
    address="日本、〒157-0064 東京都世田谷区給田１丁目３−７",
    latitude=35.662443,
    longitude=139.5920237,
)
S49 = dict(
    name_jp="富岡八幡宮",
    address="東京都江東区富岡1-20-3",
    latitude=CORRECTED_49[0],
    longitude=CORRECTED_49[1],
)

EXPECTED = {22: PID22, 21: PID21, 49: PID49}


class _Apps:
    _models = {
        "Shrine": Shrine,
        "PlaceRef": PlaceRef,
        "ShrineInteractionLog": ShrineInteractionLog,
    }

    def get_model(self, app_label, model_name):
        assert app_label == "temples"
        return self._models[model_name]


class _SchemaEditor:
    connection = connection


APPS = _Apps()
SE = _SchemaEditor()


# --------------------------------------------------------------------------- #
# builders
# --------------------------------------------------------------------------- #
def _operator(django_user_model):
    u, _ = django_user_model.objects.get_or_create(
        id=1, defaults=dict(username="f6d-operator", email="op@example.test")
    )
    return u


def _place_refs(*, skip=()):
    for pid, name in ((PID22, "給田六所神社"), (PID21, "長太稲荷神社"), (PID49, "富岡八幡宮")):
        if pid in skip:
            continue
        PlaceRef.objects.get_or_create(place_id=pid, defaults=dict(name=name))


def _primary(pk, spec, **overrides):
    data = dict(kind="shrine", **spec)
    data.update(overrides)
    return Shrine.objects.create(id=pk, **data)


def _event(user, shrine_id, ts):
    return ShrineInteractionLog.objects.create(
        user=user,
        shrine_id=shrine_id,
        action_type="detail_view",
        source="map",
        metadata={"ctx": "map", "event": "shrine_detail_view"},
        created_at=ts,
    )


@pytest.fixture
def full_pre(db, django_user_model):
    """The complete audited F-6D PRE state (pre-F6D orphan state)."""
    op = _operator(django_user_model)
    _place_refs()
    p22 = _primary(22, S22, goriyaku="地域の氏神として…")
    p21 = _primary(21, S21, goriyaku="地域に根ざした稲荷社として…")
    p49 = _primary(49, S49, goriyaku="勝運・商売繁盛")
    _event(op, 22, EVENT_A_TS)
    _event(op, 21, EVENT_B_TS)
    return {"op": op, 22: p22, 21: p21, 49: p49}


def _snapshot(pks=(21, 22, 49)):
    return {
        row["id"]: row
        for row in Shrine.objects.filter(pk__in=pks).values(
            "id",
            "name_jp",
            "address",
            "latitude",
            "longitude",
            "place_ref_id",
            "goriyaku",
            "kind",
            "updated_at",
        )
    }


def _assert_linked():
    for pk, pid in EXPECTED.items():
        assert Shrine.objects.get(pk=pk).place_ref_id == pid, pk


def _assert_unlinked():
    for pk in EXPECTED:
        assert Shrine.objects.get(pk=pk).place_ref_id is None, pk


# =========================================================================== #
# 1-6  valid forward
# =========================================================================== #
def test_1_valid_forward_links_all_three_exact_pairs(full_pre):
    forward(APPS, SE)

    _assert_linked()
    assert {p["shrine_pk"]: p["place_ref_id"] for p in PAIRS} == EXPECTED


def test_2_valid_forward_changes_no_other_shrine_field(full_pre):
    before = _snapshot()

    forward(APPS, SE)

    after = _snapshot()
    for pk in (21, 22, 49):
        for field in ("name_jp", "address", "latitude", "longitude", "goriyaku", "kind"):
            assert after[pk][field] == before[pk][field], (pk, field)
        assert after[pk]["place_ref_id"] == EXPECTED[pk]


def test_3_valid_forward_preserves_updated_at(full_pre):
    before = {pk: row["updated_at"] for pk, row in _snapshot().items()}

    forward(APPS, SE)

    after = {pk: row["updated_at"] for pk, row in _snapshot().items()}
    assert after == before, "QuerySet.update() must not touch auto_now updated_at"


def test_4_valid_forward_preserves_place_ref_rows(full_pre):
    before = list(
        PlaceRef.objects.order_by("place_id").values("place_id", "name", "address", "synced_at")
    )

    forward(APPS, SE)

    assert (
        list(
            PlaceRef.objects.order_by("place_id").values(
                "place_id", "name", "address", "synced_at"
            )
        )
        == before
    )
    assert PlaceRef.objects.count() == 3


def test_5_valid_forward_preserves_audited_interaction_events(full_pre):
    before = list(
        ShrineInteractionLog.objects.order_by("created_at").values(
            "id", "user_id", "shrine_id", "action_type", "metadata", "created_at"
        )
    )

    forward(APPS, SE)

    assert (
        list(
            ShrineInteractionLog.objects.order_by("created_at").values(
                "id", "user_id", "shrine_id", "action_type", "metadata", "created_at"
            )
        )
        == before
    )


def test_6_valid_forward_keeps_shadows_absent(full_pre):
    forward(APPS, SE)

    assert not Shrine.objects.filter(pk__in=[101, 103, 104]).exists()


# =========================================================================== #
# 7-9  valid reverse / round trip
# =========================================================================== #
def test_7_valid_reverse_restores_all_three_to_null(full_pre):
    forward(APPS, SE)

    reverse(APPS, SE)

    _assert_unlinked()


def test_8_valid_reverse_preserves_place_ref_rows(full_pre):
    forward(APPS, SE)

    reverse(APPS, SE)

    assert PlaceRef.objects.count() == 3
    assert set(PlaceRef.objects.values_list("place_id", flat=True)) == {PID21, PID22, PID49}
    # orphaned again
    assert not Shrine.objects.filter(place_ref_id__in=[PID21, PID22, PID49]).exists()


def test_9_forward_then_reverse_restores_exact_pre_f6d_state(full_pre):
    before = _snapshot()
    logs_before = list(
        ShrineInteractionLog.objects.order_by("created_at").values(
            "id", "shrine_id", "created_at"
        )
    )

    forward(APPS, SE)
    reverse(APPS, SE)

    assert _snapshot() == before
    assert (
        list(
            ShrineInteractionLog.objects.order_by("created_at").values(
                "id", "shrine_id", "created_at"
            )
        )
        == logs_before
    )
    assert PlaceRef.objects.count() == 3


# =========================================================================== #
# 10-21  fail closed
# =========================================================================== #
def test_10_wrong_primary_name_fails_closed(full_pre):
    Shrine.objects.filter(pk=21).update(name_jp="別の神社")

    with pytest.raises(PreconditionViolation, match="name_jp"):
        forward(APPS, SE)

    _assert_unlinked()


def test_11_wrong_primary_address_fails_closed(full_pre):
    Shrine.objects.filter(pk=22).update(address="別の住所")

    with pytest.raises(PreconditionViolation, match="address"):
        forward(APPS, SE)

    _assert_unlinked()


def test_12_wrong_shrine_49_coordinate_fails_closed(full_pre):
    Shrine.objects.filter(pk=49).update(latitude=35.6733, longitude=139.7967)

    with pytest.raises(PreconditionViolation, match="coordinate"):
        forward(APPS, SE)

    _assert_unlinked()


def test_13_missing_primary_fails_closed(full_pre):
    Shrine.objects.filter(pk=49).delete()

    with pytest.raises(PreconditionViolation, match="partial primary set"):
        forward(APPS, SE)

    assert Shrine.objects.get(pk=21).place_ref_id is None
    assert Shrine.objects.get(pk=22).place_ref_id is None


def test_14_missing_target_place_ref_fails_closed(db, django_user_model):
    op = _operator(django_user_model)
    _place_refs(skip=(PID49,))
    _primary(22, S22)
    _primary(21, S21)
    _primary(49, S49)
    _event(op, 22, EVENT_A_TS)
    _event(op, 21, EVENT_B_TS)

    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)

    _assert_unlinked()


def test_15_target_place_ref_already_claimed_fails_closed(full_pre):
    Shrine.objects.create(id=900, kind="shrine", name_jp="横取り神社", address="どこか", place_ref_id=PID49)

    with pytest.raises(PreconditionViolation, match="already claimed"):
        forward(APPS, SE)

    _assert_unlinked()


def test_16_target_primary_already_linked_fails_closed(full_pre):
    Shrine.objects.filter(pk=22).update(place_ref_id=PID22)

    with pytest.raises(PreconditionViolation, match="already has place_ref_id"):
        forward(APPS, SE)

    assert Shrine.objects.get(pk=21).place_ref_id is None
    assert Shrine.objects.get(pk=49).place_ref_id is None


def test_17_partial_already_linked_set_fails_closed(full_pre):
    Shrine.objects.filter(pk=21).update(place_ref_id=PID21)
    Shrine.objects.filter(pk=22).update(place_ref_id=PID22)

    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)

    assert Shrine.objects.get(pk=49).place_ref_id is None


@pytest.mark.parametrize("shadow_pk", [101, 103, 104])
def test_18_shadow_present_fails_closed(full_pre, shadow_pk):
    Shrine.objects.create(id=shadow_pk, kind="shrine", name_jp="影", address="影の住所")

    with pytest.raises(PreconditionViolation, match="shadow"):
        forward(APPS, SE)

    _assert_unlinked()


def test_19_audited_event_missing_fails_closed(full_pre):
    ShrineInteractionLog.objects.filter(created_at=EVENT_A_TS).delete()

    with pytest.raises(PreconditionViolation, match="global matches"):
        forward(APPS, SE)

    _assert_unlinked()


def test_20_audited_event_duplicated_globally_fails_closed(full_pre):
    _event(full_pre["op"], 49, EVENT_A_TS)

    with pytest.raises(PreconditionViolation, match="global matches"):
        forward(APPS, SE)

    _assert_unlinked()


def test_21_audited_event_on_wrong_shrine_fails_closed(full_pre):
    ShrineInteractionLog.objects.filter(created_at=EVENT_A_TS).update(shrine_id=49)

    with pytest.raises(PreconditionViolation, match="expected its P8-A primary"):
        forward(APPS, SE)

    _assert_unlinked()


# =========================================================================== #
# 22-25  rerun / fresh lineage
# =========================================================================== #
def test_22_direct_forward_rerun_after_successful_forward_fails_closed(full_pre):
    forward(APPS, SE)

    with pytest.raises(PreconditionViolation, match="already has place_ref_id"):
        forward(APPS, SE)

    _assert_linked()  # unchanged by the refused rerun


def test_23_direct_reverse_rerun_after_successful_reverse_fails_closed(full_pre):
    forward(APPS, SE)
    reverse(APPS, SE)

    with pytest.raises(PreconditionViolation, match="post-forward shape"):
        reverse(APPS, SE)

    _assert_unlinked()


def test_24_complete_subject_absent_is_a_symmetric_no_op(db):
    """Fresh lineage = the ENTIRE audited F-6D subject is absent.

    The base test schema may carry unrelated seed rows; the no-op boundary is
    about the subject (primaries / targets / shadows / audited events), not
    about the whole table being empty.
    """
    Shrine.objects.filter(pk__in=[21, 22, 49, 101, 103, 104]).delete()
    PlaceRef.objects.filter(pk__in=[PID21, PID22, PID49]).delete()
    ShrineInteractionLog.objects.all().delete()
    unrelated_before = set(Shrine.objects.values_list("id", flat=True))

    forward(APPS, SE)
    reverse(APPS, SE)

    assert not Shrine.objects.filter(pk__in=[21, 22, 49, 101, 103, 104]).exists()
    assert not PlaceRef.objects.filter(pk__in=[PID21, PID22, PID49]).exists()
    assert set(Shrine.objects.values_list("id", flat=True)) == unrelated_before


def test_25a_partial_subject_absent_primaries_only_fails_closed(db):
    _primary(22, S22)
    _primary(21, S21)
    _primary(49, S49)

    with pytest.raises(PreconditionViolation):
        forward(APPS, SE)

    _assert_unlinked()


def test_25b_partial_subject_absent_place_refs_only_fails_closed(db):
    _place_refs()

    with pytest.raises(PreconditionViolation, match="partial primary set"):
        forward(APPS, SE)

    assert PlaceRef.objects.count() == 3


def test_25c_partial_subject_absent_reverse_fails_closed(db):
    _place_refs()

    with pytest.raises(PreconditionViolation):
        reverse(APPS, SE)


# =========================================================================== #
# 26  reverse partial-unique conflict
# =========================================================================== #
def test_26_reverse_detects_partial_unique_conflict_before_mutation(full_pre):
    forward(APPS, SE)
    # A place_ref-less twin of Shrine 21 appears while F-6D is applied. Releasing
    # 21's place_ref would move it into the partial unique index and collide.
    twin = Shrine.objects.create(id=901, kind="shrine", **S21)

    with pytest.raises(PreconditionViolation, match="partial unique"):
        reverse(APPS, SE)

    _assert_linked()  # zero mutation
    assert Shrine.objects.get(pk=twin.pk).place_ref_id is None


def test_26b_reverse_ignores_a_twin_that_already_holds_a_place_ref(full_pre):
    forward(APPS, SE)
    other = PlaceRef.objects.create(place_id="OTHER_PID", name="別")
    Shrine.objects.create(id=902, kind="shrine", place_ref_id=other.pk, **S21)

    reverse(APPS, SE)

    _assert_unlinked()


# =========================================================================== #
# 27-30  migration wiring / safety
# =========================================================================== #
def test_27_migration_dependency_points_to_the_fresh_actual_leaf():
    assert _mod.Migration.dependencies == [("temples", "0113_adopt_usa_jingu_position")]


def test_28_migration_is_atomic_and_reversible():
    m = _mod.Migration
    # Django's default is atomic=True; the migration must not opt out.
    assert getattr(m, "atomic", True) is True
    op = m.operations[0]
    assert op.reversible is True
    assert op.code is forward
    assert op.reverse_code is reverse


def test_29_unrelated_shrine_is_untouched(full_pre):
    other = Shrine.objects.create(
        id=777, kind="shrine", name_jp="無関係神社", address="北海道札幌市1-1",
        latitude=43.06, longitude=141.35, goriyaku="そのまま",
    )
    before = Shrine.objects.filter(pk=777).values().first()

    forward(APPS, SE)

    assert Shrine.objects.filter(pk=777).values().first() == before
    assert Shrine.objects.get(pk=777).place_ref_id is None
    assert other.pk == 777


def test_30_migration_never_projects_legacy_location(full_pre):
    """`location` must never appear in a SELECT the migration issues.

    Production's temples_shrine.location is a legacy text column while the model
    declares a PostGIS PointField, so projecting it raises before any row is
    read. The only permitted use is an IS NULL / equality comparison in raw SQL.
    """
    from django.test.utils import CaptureQueriesContext

    with CaptureQueriesContext(connection) as ctx:
        forward(APPS, SE)
        reverse(APPS, SE)

    selects = [q["sql"] for q in ctx.captured_queries if q["sql"].lstrip().upper().startswith("SELECT")]
    assert selects
    for sql in selects:
        head = sql.upper().split(" FROM ", 1)[0]
        assert '"LOCATION"' not in head and ".LOCATION" not in head, sql


def test_30b_static_mapping_is_exactly_three_audited_pairs():
    assert len(PAIRS) == 3
    assert {p["shrine_pk"] for p in PAIRS} == {21, 22, 49}
    assert {p["place_ref_id"] for p in PAIRS} == {PID21, PID22, PID49}


def test_30c_migration_module_imports_no_runtime_models():
    """Historical models only: the migration must not import temples.models."""
    import inspect

    src = inspect.getsource(_mod)
    assert "from temples.models" not in src
    assert "import temples.models" not in src
    assert "apps.get_model" in src


def test_30d_forward_uses_narrow_update_not_save(full_pre):
    """A model .save() would bump auto_now updated_at; assert none happens."""
    import inspect

    import ast

    src = inspect.getsource(_mod)
    assert ".update(place_ref_id=" in src

    # No `.save(...)` CALL anywhere in the module (a docstring mentioning
    # `Model.save()` must not satisfy or break this check).
    tree = ast.parse(src)
    save_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "save"
    ]
    assert save_calls == [], "migration must use QuerySet.update(), never Model.save()"

    stamp = Shrine.objects.get(pk=21).updated_at
    assert stamp is not None

    forward(APPS, SE)

    assert Shrine.objects.get(pk=21).updated_at == stamp
