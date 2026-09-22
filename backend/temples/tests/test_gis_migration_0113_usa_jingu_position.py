"""Regression tests for temples.0113_adopt_usa_jingu_position.

The migration is fail-closed and intentionally excludes the Production
location column because its physical type is legacy text while the historical
Django model declares a GIS field.
"""

import importlib
import os

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

if os.getenv("USE_GIS") != "1":
    pytest.skip("GIS disabled by env", allow_module_level=True)

_mod = importlib.import_module("temples.migrations.0113_adopt_usa_jingu_position")
PreconditionViolation = _mod.PreconditionViolation

PRE_0113 = [("temples", "0112_adopt_atsuta_jingu_position")]
AT_0113 = [("temples", "0113_adopt_usa_jingu_position")]

SHRINE_ID = 8
NAME = "宇佐神宮"
ADDRESS = "大分県宇佐市南宇佐2859"
OLD_LAT, OLD_LNG = 33.531, 131.379
NEW_LAT, NEW_LNG = 33.52344557, 131.37716659

# 宇佐神宮 is pk=8; 熱田神宮 is pk=7 (the temples.0112 target, already at its
# adopted coordinate at PRE_0113) and must never be touched by 0113.
OTHER_SHRINE_ID = 7
OTHER_NAME = "熱田神宮"
OTHER_ADDRESS = "愛知県名古屋市熱田区神宮1-1-1"
OTHER_LAT, OTHER_LNG = 35.12737043, 136.90868002


def _executor():
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    return executor


def _migrate(executor, target):
    executor.migrate(target)
    executor.loader.build_graph()


def _truncate_shrine_tables():
    with connection.cursor() as cur:
        cur.execute("TRUNCATE temples_shrine CASCADE")


def _temples_head(executor):
    return list(executor.loader.graph.leaf_nodes("temples"))


def _restore_head(executor):
    _truncate_shrine_tables()
    _migrate(executor, _temples_head(executor))


@pytest.fixture
def pre_0113():
    executor = _executor()
    _truncate_shrine_tables()
    _migrate(executor, PRE_0113)
    try:
        yield executor
    finally:
        _restore_head(executor)


def _historical_shrine_model(executor):
    state = executor.loader.project_state(PRE_0113[0])
    return state.apps.get_model("temples", "Shrine")


def _seed_target(Shrine, *, lat=OLD_LAT, lng=OLD_LNG, name=NAME, address=ADDRESS):
    return Shrine.objects.create(
        id=SHRINE_ID,
        name_jp=name,
        address=address,
        latitude=lat,
        longitude=lng,
        kind="shrine",
    )


def _seed_other(Shrine):
    return Shrine.objects.create(
        id=OTHER_SHRINE_ID,
        name_jp=OTHER_NAME,
        address=OTHER_ADDRESS,
        latitude=OTHER_LAT,
        longitude=OTHER_LNG,
        kind="shrine",
    )


def _raw_row(shrine_id):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT id, name_jp, address, latitude, longitude, location::text, updated_at "
            "FROM temples_shrine WHERE id = %s",
            [shrine_id],
        )
        row = cur.fetchone()
        if row is None:
            return None
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row, strict=True))


def _delete_target():
    with connection.cursor() as cur:
        cur.execute("DELETE FROM temples_shrine WHERE id = %s", [SHRINE_ID])


def _migration_recorded():
    with connection.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM django_migrations "
            "WHERE app = 'temples' AND name = '0113_adopt_usa_jingu_position'"
        )
        return cur.fetchone() is not None


def _force_text_location(value="legacy-location-value"):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT indexname FROM pg_indexes "
            "WHERE tablename = 'temples_shrine' "
            "AND indexdef ILIKE '%% USING gist (location)%%'"
        )
        indexes = [row[0] for row in cur.fetchall()]
        for name in indexes:
            cur.execute(f'DROP INDEX "{name}"')
        cur.execute('ALTER TABLE temples_shrine ALTER COLUMN "location" TYPE text USING NULL')
        cur.execute(
            'UPDATE temples_shrine SET "location" = %s WHERE id = %s',
            [value, SHRINE_ID],
        )
    return indexes


def _restore_geometry_location(indexes):
    with connection.cursor() as cur:
        cur.execute(
            'ALTER TABLE temples_shrine ALTER COLUMN "location" '
            "TYPE geometry(Point,4326) USING NULL"
        )
        for name in indexes:
            cur.execute(f'CREATE INDEX "{name}" ON temples_shrine USING gist (location)')


@pytest.mark.django_db(transaction=True)
def test_forward_updates_exact_audited_target(pre_0113):
    executor = pre_0113
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)

    _migrate(executor, AT_0113)

    row = _raw_row(SHRINE_ID)
    assert row["latitude"] == NEW_LAT
    assert row["longitude"] == NEW_LNG
    assert row["name_jp"] == NAME
    assert row["address"] == ADDRESS
    assert _migration_recorded()


@pytest.mark.django_db(transaction=True)
def test_forward_does_not_read_or_write_legacy_text_location(pre_0113):
    executor = pre_0113
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)
    indexes = _force_text_location("keep-this-text")

    try:
        _migrate(executor, AT_0113)
        row = _raw_row(SHRINE_ID)
        assert row["latitude"] == NEW_LAT
        assert row["longitude"] == NEW_LNG
        assert row["location"] == "keep-this-text"
    finally:
        _restore_geometry_location(indexes)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("name", "address"),
    [
        ("別の神社", ADDRESS),
        (NAME, "大分県宇佐市別住所1"),
    ],
)
def test_forward_wrong_identity_fails_closed(pre_0113, name, address):
    executor = pre_0113
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine, name=name, address=address)
    before = _raw_row(SHRINE_ID)

    with pytest.raises(PreconditionViolation):
        _migrate(executor, AT_0113)

    assert _raw_row(SHRINE_ID) == before
    assert not _migration_recorded()
    _delete_target()


@pytest.mark.django_db(transaction=True)
def test_forward_unexpected_coordinate_fails_closed(pre_0113):
    executor = pre_0113
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine, lat=33.9999, lng=131.9999)
    before = _raw_row(SHRINE_ID)

    with pytest.raises(PreconditionViolation):
        _migrate(executor, AT_0113)

    assert _raw_row(SHRINE_ID) == before
    assert not _migration_recorded()
    _delete_target()


@pytest.mark.django_db(transaction=True)
def test_forward_already_corrected_fails_closed(pre_0113):
    executor = pre_0113
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine, lat=NEW_LAT, lng=NEW_LNG)

    with pytest.raises(PreconditionViolation):
        _migrate(executor, AT_0113)

    row = _raw_row(SHRINE_ID)
    assert row["latitude"] == NEW_LAT
    assert row["longitude"] == NEW_LNG
    assert not _migration_recorded()
    _delete_target()


@pytest.mark.django_db(transaction=True)
def test_absent_target_is_symmetric_noop(pre_0113):
    executor = pre_0113
    assert _raw_row(SHRINE_ID) is None

    _migrate(executor, AT_0113)
    assert _raw_row(SHRINE_ID) is None

    _migrate(executor, PRE_0113)
    assert _raw_row(SHRINE_ID) is None


@pytest.mark.django_db(transaction=True)
def test_reverse_restores_exact_old_coordinate(pre_0113):
    executor = pre_0113
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)

    _migrate(executor, AT_0113)
    _migrate(executor, PRE_0113)

    row = _raw_row(SHRINE_ID)
    assert row["latitude"] == OLD_LAT
    assert row["longitude"] == OLD_LNG
    assert row["name_jp"] == NAME
    assert row["address"] == ADDRESS


@pytest.mark.django_db(transaction=True)
def test_forward_reverse_forward_is_deterministic(pre_0113):
    executor = pre_0113
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)

    _migrate(executor, AT_0113)
    first = _raw_row(SHRINE_ID)
    assert first["latitude"] == NEW_LAT
    assert first["longitude"] == NEW_LNG

    _migrate(executor, PRE_0113)
    reverted = _raw_row(SHRINE_ID)
    assert reverted["latitude"] == OLD_LAT
    assert reverted["longitude"] == OLD_LNG

    _migrate(executor, AT_0113)
    second = _raw_row(SHRINE_ID)
    assert second["latitude"] == NEW_LAT
    assert second["longitude"] == NEW_LNG
    assert second["name_jp"] == first["name_jp"]
    assert second["address"] == first["address"]
    assert second["location"] == first["location"]


@pytest.mark.django_db(transaction=True)
def test_reverse_unexpected_coordinate_fails_closed(pre_0113):
    executor = pre_0113
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)

    _migrate(executor, AT_0113)
    with connection.cursor() as cur:
        cur.execute(
            "UPDATE temples_shrine SET latitude = %s, longitude = %s WHERE id = %s",
            [33.8888, 131.8888, SHRINE_ID],
        )
    before = _raw_row(SHRINE_ID)

    with pytest.raises(PreconditionViolation):
        _migrate(executor, PRE_0113)

    assert _raw_row(SHRINE_ID) == before
    assert _migration_recorded()


@pytest.mark.django_db(transaction=True)
def test_unrelated_shrine_is_untouched(pre_0113):
    executor = pre_0113
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)
    _seed_other(Shrine)
    other_before = _raw_row(OTHER_SHRINE_ID)

    _migrate(executor, AT_0113)
    assert _raw_row(OTHER_SHRINE_ID) == other_before

    _migrate(executor, PRE_0113)
    assert _raw_row(OTHER_SHRINE_ID) == other_before


def test_migration_dependency_and_shape():
    assert _mod.Migration.dependencies == [
        ("temples", "0112_adopt_atsuta_jingu_position")
    ]
    assert len(_mod.Migration.operations) == 1
    assert _mod.Migration.operations[0].__class__.__name__ == "RunPython"


def test_migration_constants_match_the_audited_contract():
    assert _mod.SHRINE_ID == SHRINE_ID
    assert _mod.EXPECTED_NAME == NAME
    assert _mod.EXPECTED_ADDRESS == ADDRESS
    assert _mod.OLD_LATITUDE == OLD_LAT
    assert _mod.OLD_LONGITUDE == OLD_LNG
    assert _mod.NEW_LATITUDE == NEW_LAT
    assert _mod.NEW_LONGITUDE == NEW_LNG
    assert "location" not in _mod.LOOKUP_FIELDS
