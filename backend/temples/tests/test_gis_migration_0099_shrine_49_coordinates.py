# backend/temples/tests/test_gis_migration_0099_shrine_49_coordinates.py
"""Regression tests for temples.0099_fix_shrine_49_coordinates (P8-C).

`docs/audit/p8-identity-coordinate-remediation.md` §10, §16 (Design A).

Mirrors the established coordinate-fix pattern of
`test_gis_migration_0094_shrine_70_coordinates.py`: the migration is exercised
through `MigrationExecutor` against the true historical `Shrine` model (no
custom `save()`), and `location` is deliberately forced to a raw `text` value
in one test to reproduce production's legacy-column drift and prove the
`.only()` guard avoids `GEOSException`.

0099 is **fail-closed** (`P8_C_PRESTATE_POLICY = FAIL_CLOSED`): when the pk-49
row exists it must match the exact approved PRE state for the direction being
run, else `PreconditionViolation` is raised before any write and the
migration is not recorded as applied. The *only* clean no-op is a genuinely
absent subject (no pk-49 row at all) -- exactly symmetric in forward and
reverse.

These tests only run under GIS (module-level skip below): under `USE_GIS=0`
the `temples` app uses `temples.migrations_nogis`, a squashed set that does
not contain 0099 as a separate step -- same as 0091 / 0094.
"""

import importlib
import os

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

if os.getenv("USE_GIS") != "1":
    pytest.skip("GIS disabled by env", allow_module_level=True)

_mod = importlib.import_module("temples.migrations.0099_fix_shrine_49_coordinates")
PreconditionViolation = _mod.PreconditionViolation

PRE_0099 = [("temples", "0098_remove_stray_test_source_id1")]
AT_0099 = [("temples", "0099_fix_shrine_49_coordinates")]
HEAD = AT_0099

SHRINE_ID = 49
NAME = "富岡八幡宮"
ADDRESS = "東京都江東区富岡1-20-3"
OLD_LAT, OLD_LNG = 35.6733, 139.7967
NEW_LAT, NEW_LNG = 35.6717809, 139.799519

# a query point ~by the shrine, for the narrow distance-helper regression
NEAR_LAT, NEAR_LNG = 35.6718, 139.7996


def _executor() -> MigrationExecutor:
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    return executor


def _migrate(executor: MigrationExecutor, target):
    executor.migrate(target)
    executor.loader.build_graph()


def _truncate_shrine_tables():
    """Empty every Shrine-derived table so that any forward roll through the
    fail-closed data migrations 0095-0098 (which raise once their audited
    subject row exists but does not match) is a guaranteed clean no-op.

    `test_gis_migration_0094` only ever moves between 0093<->0094 and never
    needs this; this file is the first coordinate-fix test whose fixture may
    cross the 0095-0098 band on a `--reuse-db` session where an earlier
    executor-style test left `temples` below HEAD.
    """
    with connection.cursor() as cur:
        cur.execute("TRUNCATE temples_shrine CASCADE")


@pytest.fixture
def pre_0099():
    """Reverse temples to 0098 (0099 unapplied) and restore to HEAD after.

    Shrine tables are truncated on both sides so the 0095-0098 fail-closed
    guards are clean no-ops regardless of suite ordering. Raise-path tests
    also delete the pk-49 row they seed before returning, so this teardown's
    `_migrate(executor, HEAD)` hits 0099's absent-subject no-op.
    """
    executor = _executor()
    _truncate_shrine_tables()
    _migrate(executor, PRE_0099)
    try:
        yield executor
    finally:
        _truncate_shrine_tables()
        _migrate(executor, HEAD)


def _historical_shrine_model(executor: MigrationExecutor):
    state = executor.loader.project_state(PRE_0099[0])
    return state.apps.get_model("temples", "Shrine")


def _raw_shrine_row(shrine_id):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT id, name_jp, address, latitude, longitude, updated_at "
            "FROM temples_shrine WHERE id = %s",
            [shrine_id],
        )
        row = cur.fetchone()
        if row is None:
            return None
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row, strict=True))


def _delete_shrine(shrine_id):
    with connection.cursor() as cur:
        cur.execute("DELETE FROM temples_shrine WHERE id = %s", [shrine_id])


def _migration_recorded(name_prefix):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM django_migrations WHERE app = 'temples' AND name LIKE %s",
            [name_prefix + "%"],
        )
        return cur.fetchone() is not None


def _seed_target(Shrine, *, lat=OLD_LAT, lng=OLD_LNG, name=NAME, address=ADDRESS):
    return Shrine.objects.create(
        id=SHRINE_ID, name_jp=name, address=address, latitude=lat, longitude=lng, kind="shrine"
    )


def _create_with_text_location(Shrine, *, lat=OLD_LAT, lng=OLD_LNG):
    """Seed pk 49 and force `location` to raw non-WKB `text`, reproducing the
    confirmed production legacy-column drift (as 0094's test does)."""
    shrine = _seed_target(Shrine, lat=lat, lng=lng)
    with connection.cursor() as cur:
        cur.execute(
            "SELECT indexname FROM pg_indexes "
            "WHERE tablename = 'temples_shrine' AND indexdef ILIKE '%% USING gist (location)%%'"
        )
        gist_index_names = [row[0] for row in cur.fetchall()]
        for index_name in gist_index_names:
            cur.execute(f'DROP INDEX "{index_name}";')
        cur.execute('ALTER TABLE temples_shrine ALTER COLUMN "location" TYPE text USING NULL;')
        cur.execute(
            'UPDATE temples_shrine SET "location" = %s WHERE id = %s;',
            ["not-a-valid-wkb-value", shrine.id],
        )
    return shrine, gist_index_names


def _restore_location_geometry_column(gist_index_names):
    with connection.cursor() as cur:
        cur.execute(
            'ALTER TABLE temples_shrine ALTER COLUMN "location" TYPE geometry(Point,4326) '
            "USING NULL;"
        )
        for index_name in gist_index_names:
            cur.execute(f'CREATE INDEX "{index_name}" ON temples_shrine USING gist (location);')


# --------------------------------------------------------------------------- #
# 1 / 15 -- exact OLD PRE -> forward sets exact NEW; dependency is 0098
# --------------------------------------------------------------------------- #
@pytest.mark.django_db(transaction=True)
def test_a_exact_old_pre_forward_sets_new(pre_0099):
    executor = pre_0099
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)

    _migrate(executor, AT_0099)

    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == NEW_LAT
    assert row["longitude"] == NEW_LNG
    assert row["name_jp"] == NAME
    assert row["address"] == ADDRESS
    assert _migration_recorded("0099_fix_shrine_49_coordinates")


def test_o_dependency_is_latest_approved_temples_migration():
    assert _mod.Migration.dependencies == [("temples", "0098_remove_stray_test_source_id1")]
    ops = _mod.Migration.operations
    assert len(ops) == 1 and ops[0].__class__.__name__ == "RunPython"


# --------------------------------------------------------------------------- #
# 2 -- already-corrected PRE -> forward raises; row unchanged; not recorded
# --------------------------------------------------------------------------- #
@pytest.mark.django_db(transaction=True)
def test_b_already_corrected_forward_raises(pre_0099):
    executor = pre_0099
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine, lat=NEW_LAT, lng=NEW_LNG)

    with pytest.raises(PreconditionViolation):
        _migrate(executor, AT_0099)

    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == NEW_LAT and row["longitude"] == NEW_LNG  # untouched
    assert not _migration_recorded("0099_fix_shrine_49_coordinates")
    _delete_shrine(SHRINE_ID)  # let fixture teardown hit the absent-subject no-op


# --------------------------------------------------------------------------- #
# 3 -- wrong name -> forward raises; unchanged
# --------------------------------------------------------------------------- #
@pytest.mark.django_db(transaction=True)
def test_c_wrong_name_forward_raises(pre_0099):
    executor = pre_0099
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine, name="別名になった神社")

    with pytest.raises(PreconditionViolation):
        _migrate(executor, AT_0099)

    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == OLD_LAT and row["longitude"] == OLD_LNG
    assert row["name_jp"] == "別名になった神社"
    assert not _migration_recorded("0099_fix_shrine_49_coordinates")
    _delete_shrine(SHRINE_ID)


# --------------------------------------------------------------------------- #
# 4 -- wrong address -> forward raises; unchanged
# --------------------------------------------------------------------------- #
@pytest.mark.django_db(transaction=True)
def test_d_wrong_address_forward_raises(pre_0099):
    executor = pre_0099
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine, address="東京都江東区どこか9-9-9")

    with pytest.raises(PreconditionViolation):
        _migrate(executor, AT_0099)

    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == OLD_LAT and row["longitude"] == OLD_LNG
    assert row["address"] == "東京都江東区どこか9-9-9"
    assert not _migration_recorded("0099_fix_shrine_49_coordinates")
    _delete_shrine(SHRINE_ID)


# --------------------------------------------------------------------------- #
# 5 -- third coordinate -> forward raises; unchanged
# --------------------------------------------------------------------------- #
@pytest.mark.django_db(transaction=True)
def test_e_third_coordinate_forward_raises(pre_0099):
    executor = pre_0099
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine, lat=35.9999, lng=139.0001)

    with pytest.raises(PreconditionViolation):
        _migrate(executor, AT_0099)

    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == 35.9999 and row["longitude"] == 139.0001
    assert not _migration_recorded("0099_fix_shrine_49_coordinates")
    _delete_shrine(SHRINE_ID)


# --------------------------------------------------------------------------- #
# 6 -- failed forward leaves the whole row byte-unchanged (atomic rollback)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db(transaction=True)
def test_f_failed_forward_leaves_db_unchanged(pre_0099):
    executor = pre_0099
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine, lat=NEW_LAT, lng=NEW_LNG)  # already-corrected -> will raise
    before = _raw_shrine_row(SHRINE_ID)

    with pytest.raises(PreconditionViolation):
        _migrate(executor, AT_0099)

    assert _raw_shrine_row(SHRINE_ID) == before
    assert not _migration_recorded("0099_fix_shrine_49_coordinates")
    _delete_shrine(SHRINE_ID)


# --------------------------------------------------------------------------- #
# 7 -- valid forward -> reverse restores exact OLD
# --------------------------------------------------------------------------- #
@pytest.mark.django_db(transaction=True)
def test_g_valid_forward_then_reverse_restores_old(pre_0099):
    executor = pre_0099
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)

    _migrate(executor, AT_0099)
    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == NEW_LAT and row["longitude"] == NEW_LNG

    _migrate(executor, PRE_0099)
    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == OLD_LAT and row["longitude"] == OLD_LNG
    assert not _migration_recorded("0099_fix_shrine_49_coordinates")


# --------------------------------------------------------------------------- #
# 8 -- valid forward -> reverse -> forward is deterministic
# --------------------------------------------------------------------------- #
@pytest.mark.django_db(transaction=True)
def test_h_forward_reverse_forward_deterministic(pre_0099):
    executor = pre_0099
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)

    _migrate(executor, AT_0099)
    _migrate(executor, PRE_0099)
    _migrate(executor, AT_0099)

    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == NEW_LAT and row["longitude"] == NEW_LNG


# --------------------------------------------------------------------------- #
# 9 -- reverse from an unexpected third coordinate raises and overwrites nothing
# --------------------------------------------------------------------------- #
@pytest.mark.django_db(transaction=True)
def test_i_reverse_from_unexpected_coordinate_raises(pre_0099):
    executor = pre_0099
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)

    _migrate(executor, AT_0099)  # now at NEW
    # someone moved it to a third value after forward
    with connection.cursor() as cur:
        cur.execute(
            "UPDATE temples_shrine SET latitude = %s, longitude = %s WHERE id = %s",
            [35.5, 139.5, SHRINE_ID],
        )

    with pytest.raises(PreconditionViolation):
        _migrate(executor, PRE_0099)

    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == 35.5 and row["longitude"] == 139.5  # NOT overwritten
    # restore so fixture teardown (forward to HEAD) succeeds
    with connection.cursor() as cur:
        cur.execute(
            "UPDATE temples_shrine SET latitude = %s, longitude = %s WHERE id = %s",
            [OLD_LAT, OLD_LNG, SHRINE_ID],
        )


@pytest.mark.django_db(transaction=True)
def test_i2_reverse_when_old_already_present_raises(pre_0099):
    """Reverse must not silently accept 'already old' -- fail-closed."""
    executor = pre_0099
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)
    _migrate(executor, AT_0099)
    with connection.cursor() as cur:
        cur.execute(
            "UPDATE temples_shrine SET latitude = %s, longitude = %s WHERE id = %s",
            [OLD_LAT, OLD_LNG, SHRINE_ID],
        )

    with pytest.raises(PreconditionViolation):
        _migrate(executor, PRE_0099)

    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == OLD_LAT and row["longitude"] == OLD_LNG  # unchanged


# --------------------------------------------------------------------------- #
# 10 -- another Shrine is untouched
# --------------------------------------------------------------------------- #
@pytest.mark.django_db(transaction=True)
def test_j_other_shrine_untouched(pre_0099):
    executor = pre_0099
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)
    other = Shrine.objects.create(
        id=999049, name_jp="別の神社", address="どこか", latitude=OLD_LAT, longitude=OLD_LNG, kind="shrine"
    )

    _migrate(executor, AT_0099)

    other.refresh_from_db()
    assert other.latitude == OLD_LAT and other.longitude == OLD_LNG
    assert other.name_jp == "別の神社"


# --------------------------------------------------------------------------- #
# 11 / 12 / 13 -- Recommendation semantic fields, goriyaku_tags, and Knowledge
#                 relations for id 49 are all unchanged by the coordinate fix.
#   Relations are seeded/asserted with the *real* models (0099 makes no schema
#   change, so the real models are valid at both 0098 and HEAD); the migration
#   itself still runs through the executor.
# --------------------------------------------------------------------------- #
@pytest.mark.django_db(transaction=True)
def test_k_semantic_fields_and_relations_unchanged(pre_0099):
    from temples.models import (
        GoriyakuTag,
        Shrine,
        ShrineDeity,
        ShrineHistory,
        ShrineKnowledgeSource,
    )

    executor = pre_0099
    shrine = Shrine.objects.create(
        id=SHRINE_ID, name_jp=NAME, address=ADDRESS,
        latitude=OLD_LAT, longitude=OLD_LNG, kind="shrine", goriyaku="勝運・商売繁盛",
    )
    t1 = GoriyakuTag.objects.create(name="商売繁盛-t")
    t2 = GoriyakuTag.objects.create(name="勝運-t")
    shrine.goriyaku_tags.set([t1, t2])
    src = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official", title="富岡八幡宮 御由緒",
        url="http://www.tomiokahachimangu.or.jp/annai/goyuisho/goyuisho.html",
        verification_status="source_confirmed", confidence="high",
    )
    d = ShrineDeity.objects.create(
        shrine=shrine, display_name="応神天皇", role="primary", sort_order=0,
        verification_status="source_confirmed", confidence="high",
    )
    d.sources.set([src])
    h = ShrineHistory.objects.create(
        shrine=shrine, history_type="founding", title="寛永4年(1627)の創建",
        content="…", sort_order=0, verification_status="source_confirmed", confidence="high",
    )
    h.sources.set([src])

    before_tag_ids = set(shrine.goriyaku_tags.values_list("id", flat=True))
    before_goriyaku = shrine.goriyaku
    before_deity_ids = set(ShrineDeity.objects.filter(shrine_id=SHRINE_ID).values_list("id", flat=True))
    before_hist_ids = set(ShrineHistory.objects.filter(shrine_id=SHRINE_ID).values_list("id", flat=True))
    before_src_ids = set(d.sources.values_list("id", flat=True)) | set(h.sources.values_list("id", flat=True))

    _migrate(executor, AT_0099)

    shrine.refresh_from_db()
    assert shrine.latitude == NEW_LAT and shrine.longitude == NEW_LNG  # only this changed
    assert shrine.goriyaku == before_goriyaku
    assert shrine.name_jp == NAME and shrine.address == ADDRESS
    assert set(shrine.goriyaku_tags.values_list("id", flat=True)) == before_tag_ids
    assert set(ShrineDeity.objects.filter(shrine_id=SHRINE_ID).values_list("id", flat=True)) == before_deity_ids
    assert set(ShrineHistory.objects.filter(shrine_id=SHRINE_ID).values_list("id", flat=True)) == before_hist_ids
    d.refresh_from_db()
    h.refresh_from_db()
    after_src_ids = set(d.sources.values_list("id", flat=True)) | set(h.sources.values_list("id", flat=True))
    assert after_src_ids == before_src_ids


# --------------------------------------------------------------------------- #
# 14 -- the goriyaku / Need scoring evidence is coordinate-independent;
#       the distance signal legitimately reflects the corrected position
#       (that is the point of the fix -- see §16 map/recommendation notes).
# --------------------------------------------------------------------------- #
@pytest.mark.django_db(transaction=True)
def test_l_need_scoring_evidence_unchanged_distance_reflects_fix(pre_0099):
    from temples.models import GoriyakuTag, Shrine
    from temples.services.concierge_chat_candidates import _distance_m

    executor = pre_0099
    shrine = Shrine.objects.create(
        id=SHRINE_ID, name_jp=NAME, address=ADDRESS,
        latitude=OLD_LAT, longitude=OLD_LNG, kind="shrine",
    )
    t = GoriyakuTag.objects.create(name="勝運-need-t")
    shrine.goriyaku_tags.set([t])
    before_gids = set(shrine.goriyaku_tags.values_list("id", flat=True))

    dist_before = _distance_m(NEAR_LAT, NEAR_LNG, OLD_LAT, OLD_LNG)

    _migrate(executor, AT_0099)

    shrine.refresh_from_db()
    # goriyaku / Need scoring evidence: byte-identical
    assert set(shrine.goriyaku_tags.values_list("id", flat=True)) == before_gids
    # distance signal: now measured from the corrected (real) position, and
    # closer to a by-the-shrine query point -- the intended effect.
    dist_after = _distance_m(NEAR_LAT, NEAR_LNG, shrine.latitude, shrine.longitude)
    assert dist_before is not None and dist_after is not None
    assert dist_after < dist_before
    assert dist_after < 60  # within ~60 m of the real shrine grounds
    assert dist_before > 250  # the drifted seed was ~305 m off


# --------------------------------------------------------------------------- #
# Applicability boundary -- genuinely absent subject: symmetric no-op
# --------------------------------------------------------------------------- #
@pytest.mark.django_db(transaction=True)
def test_m_absent_subject_forward_and_reverse_are_symmetric_noops(pre_0099):
    executor = pre_0099
    assert _raw_shrine_row(SHRINE_ID) is None

    _migrate(executor, AT_0099)   # forward: clean no-op
    assert _raw_shrine_row(SHRINE_ID) is None
    assert _migration_recorded("0099_fix_shrine_49_coordinates")

    _migrate(executor, PRE_0099)  # reverse: clean no-op
    assert _raw_shrine_row(SHRINE_ID) is None


# --------------------------------------------------------------------------- #
# GEOSException guard -- `location` physically `text` (production drift)
# --------------------------------------------------------------------------- #
@pytest.mark.django_db(transaction=True)
def test_n_geos_exception_avoided_under_text_location_drift(pre_0099):
    executor = pre_0099
    Shrine = _historical_shrine_model(executor)
    _shrine, gist_index_names = _create_with_text_location(Shrine)

    try:
        _migrate(executor, AT_0099)
    finally:
        _restore_location_geometry_column(gist_index_names)

    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == NEW_LAT
    assert row["longitude"] == NEW_LNG
