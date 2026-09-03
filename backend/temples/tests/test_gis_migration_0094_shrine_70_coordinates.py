# backend/temples/tests/test_gis_migration_0094_shrine_70_coordinates.py
"""Regression tests for temples.0094_fix_shrine_70_coordinates.

Mirrors the established pattern from
test_gis_migration_0091_shrine_reason_facts.py: production's
`temples_shrine.location` column is a legacy `text` column, while the
historical model state any migration runs against declares it as a
PostGIS `PointField` (docs/audit/temples-0091-production-remediation.md).
A bare `Shrine.objects.filter(...)` (no `.only()`) selects every column
including `location`, and Django's GeometryField converter raises
GEOSException trying to parse the raw text value as WKB before any row is
touched. 0094 avoids this by using `.only()` to exclude `location`
entirely from both the SELECT and the write (docs/audit/
shrine-70-coordinate-correction.md).

These tests only run under GIS (module-level skip below): under
`USE_GIS=0` the `temples` app uses `temples.migrations_nogis`, a squashed
migration set that does not contain 0094 as a separate step.
"""

import os

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

if os.getenv("USE_GIS") != "1":
    pytest.skip("GIS disabled by env", allow_module_level=True)

PRE_0094 = [("temples", "0093_shrine_knowledge_model_foundation")]
AT_0094 = [("temples", "0094_fix_shrine_70_coordinates")]

SHRINE_ID = 70
NAME = "多摩川浅間神社"
ADDRESS = "東京都大田区田園調布1-55-12"
OLD_LAT, OLD_LNG = 35.5898, 139.6688
NEW_LAT, NEW_LNG = 35.5875263, 139.6687549


def _executor() -> MigrationExecutor:
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    return executor


def _migrate(executor: MigrationExecutor, target):
    executor.migrate(target)
    executor.loader.build_graph()


def _temples_head(executor: MigrationExecutor):
    """The actual latest `temples` migration in this lineage, resolved at call
    time from the migration graph."""
    return list(executor.loader.graph.leaf_nodes("temples"))


def _truncate_shrine_tables():
    """Empty every Shrine-derived table so the forward roll back to HEAD is a
    guaranteed clean no-op through the fail-closed data migrations (0095+),
    which raise once their audited subject row exists but does not match.
    Mirrors `test_gis_migration_0099`'s teardown."""
    with connection.cursor() as cur:
        cur.execute("TRUNCATE temples_shrine CASCADE")


def _restore_head(executor: MigrationExecutor):
    """Roll `temples` forward to the real latest migration after a test.

    Previously this restored to a hardcoded `HEAD` pinned at the migration
    under test (0094), which left every later migration unapplied for the
    remainder of the pytest session -- including 0102's
    `HistoryThemeAssignment` table. `pytest-randomly` shuffles module order,
    so on any seed that placed this file before an unrelated test needing
    that schema, the unrelated test failed against a stale database.
    """
    _truncate_shrine_tables()
    _migrate(executor, _temples_head(executor))


@pytest.fixture
def pre_0094():
    """Reverse temples to 0093 (0094 unapplied) and restore afterwards."""
    executor = _executor()
    _migrate(executor, PRE_0094)
    try:
        yield executor
    finally:
        _restore_head(executor)


def _historical_shrine_model(executor: MigrationExecutor):
    state = executor.loader.project_state(PRE_0094[0])
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


def _create_shrine_with_text_location(Shrine, pk, name_jp, address, lat, lng):
    """Create a shrine row and force its `location` column to a
    non-WKB-parseable raw text value, reproducing the confirmed
    production drift (`temples-0091-production-remediation.md` Section
    2) without needing a real production dump."""
    shrine = Shrine.objects.create(
        id=pk, name_jp=name_jp, address=address, latitude=lat, longitude=lng, kind="shrine"
    )
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


@pytest.mark.django_db(transaction=True)
def test_a_geos_exception_avoided_under_text_location_drift(pre_0094):
    """0094 must not raise GEOSException when `location` is physically
    `text` (the confirmed production drift condition)."""
    executor = pre_0094
    Shrine = _historical_shrine_model(executor)
    _shrine, gist_index_names = _create_shrine_with_text_location(
        Shrine, SHRINE_ID, NAME, ADDRESS, OLD_LAT, OLD_LNG
    )

    try:
        _migrate(executor, AT_0094)
    finally:
        _restore_location_geometry_column(gist_index_names)

    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == NEW_LAT
    assert row["longitude"] == NEW_LNG


@pytest.mark.django_db(transaction=True)
def test_b_forward_corrects_only_the_target_shrine(pre_0094):
    """Forward migration updates only shrine_id=70's lat/lng, and does not
    touch an unrelated shrine's coordinates."""
    executor = pre_0094
    Shrine = _historical_shrine_model(executor)

    Shrine.objects.create(id=SHRINE_ID, name_jp=NAME, address=ADDRESS, latitude=OLD_LAT, longitude=OLD_LNG, kind="shrine")
    other = Shrine.objects.create(
        id=999070, name_jp="別の神社", address="どこか別の住所", latitude=1.0, longitude=2.0, kind="shrine"
    )

    _migrate(executor, AT_0094)

    target_row = _raw_shrine_row(SHRINE_ID)
    assert target_row["latitude"] == NEW_LAT
    assert target_row["longitude"] == NEW_LNG
    assert target_row["name_jp"] == NAME
    assert target_row["address"] == ADDRESS

    other.refresh_from_db()
    assert other.latitude == 1.0
    assert other.longitude == 2.0


@pytest.mark.django_db(transaction=True)
def test_c_mismatched_name_or_address_is_left_untouched(pre_0094):
    """If id=70 exists but its name/address no longer match what this
    correction was written against, the migration must not touch it."""
    executor = pre_0094
    Shrine = _historical_shrine_model(executor)

    Shrine.objects.create(
        id=SHRINE_ID, name_jp="別のIDになった神社", address="想定外の住所", latitude=OLD_LAT, longitude=OLD_LNG, kind="shrine"
    )

    _migrate(executor, AT_0094)

    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == OLD_LAT
    assert row["longitude"] == OLD_LNG


@pytest.mark.django_db(transaction=True)
def test_d_fresh_db_with_no_shrine_70_is_a_noop(pre_0094):
    """No shrine_id=70 row at all: migration applies cleanly, no exception."""
    executor = pre_0094
    assert _raw_shrine_row(SHRINE_ID) is None

    _migrate(executor, AT_0094)

    assert _raw_shrine_row(SHRINE_ID) is None


@pytest.mark.django_db(transaction=True)
def test_e_reverse_migration_restores_old_coordinates(pre_0094):
    """Reversing 0094 restores the previous (wrong, but recorded)
    coordinates -- documented rollback path, not auto-applied."""
    executor = pre_0094
    Shrine = _historical_shrine_model(executor)

    Shrine.objects.create(id=SHRINE_ID, name_jp=NAME, address=ADDRESS, latitude=OLD_LAT, longitude=OLD_LNG, kind="shrine")

    _migrate(executor, AT_0094)
    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == NEW_LAT
    assert row["longitude"] == NEW_LNG

    _migrate(executor, PRE_0094)

    row = _raw_shrine_row(SHRINE_ID)
    assert row["latitude"] == OLD_LAT
    assert row["longitude"] == OLD_LNG
