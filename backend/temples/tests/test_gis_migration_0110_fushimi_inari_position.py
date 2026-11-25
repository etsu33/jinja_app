"""Regression tests for temples.0110_adopt_fushimi_inari_position.

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

_mod = importlib.import_module("temples.migrations.0110_adopt_fushimi_inari_position")
PreconditionViolation = _mod.PreconditionViolation

PRE_0110 = [("temples", "0109_adopt_izumo_taisha_position")]
AT_0110 = [("temples", "0110_adopt_fushimi_inari_position")]

SHRINE_ID = 2
NAME = "伏見稲荷大社"
ADDRESS = "京都府京都市伏見区深草薮之内町68"
OLD_LAT, OLD_LNG = 34.9671, 135.7727
NEW_LAT, NEW_LNG = 34.967133624329, 135.77318468005

# 伏見稲荷大社 is pk=2; 出雲大社 is pk=4 and must never be touched by 0110.
OTHER_SHRINE_ID = 4
OTHER_NAME = "出雲大社"
OTHER_ADDRESS = "島根県出雲市大社町杵築東195"
OTHER_LAT, OTHER_LNG = 35.40190463, 132.68547534


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
def pre_0110():
    executor = _executor()
    _truncate_shrine_tables()
    _migrate(executor, PRE_0110)
    try:
        yield executor
    finally:
        _restore_head(executor)


def _historical_shrine_model(executor):
    state = executor.loader.project_state(PRE_0110[0])
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
            "WHERE app = 'temples' AND name = '0110_adopt_fushimi_inari_position'"
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
def test_forward_updates_exact_audited_target(pre_0110):
    executor = pre_0110
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)

    _migrate(executor, AT_0110)

    row = _raw_row(SHRINE_ID)
    assert row["latitude"] == NEW_LAT
    assert row["longitude"] == NEW_LNG
    assert row["name_jp"] == NAME
    assert row["address"] == ADDRESS
    assert _migration_recorded()


@pytest.mark.django_db(transaction=True)
def test_forward_does_not_read_or_write_legacy_text_location(pre_0110):
    executor = pre_0110
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)
    indexes = _force_text_location("keep-this-text")

    try:
        _migrate(executor, AT_0110)
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
        (NAME, "京都府京都市伏見区別住所1"),
    ],
)
def test_forward_wrong_identity_fails_closed(pre_0110, name, address):
    executor = pre_0110
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine, name=name, address=address)
    before = _raw_row(SHRINE_ID)

    with pytest.raises(PreconditionViolation):
        _migrate(executor, AT_0110)

    assert _raw_row(SHRINE_ID) == before
    assert not _migration_recorded()
    _delete_target()


@pytest.mark.django_db(transaction=True)
def test_forward_unexpected_coordinate_fails_closed(pre_0110):
    executor = pre_0110
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine, lat=34.9999, lng=135.9999)
    before = _raw_row(SHRINE_ID)

    with pytest.raises(PreconditionViolation):
        _migrate(executor, AT_0110)

    assert _raw_row(SHRINE_ID) == before
    assert not _migration_recorded()
    _delete_target()


@pytest.mark.django_db(transaction=True)
def test_forward_already_corrected_fails_closed(pre_0110):
    executor = pre_0110
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine, lat=NEW_LAT, lng=NEW_LNG)

    with pytest.raises(PreconditionViolation):
        _migrate(executor, AT_0110)

    row = _raw_row(SHRINE_ID)
    assert row["latitude"] == NEW_LAT
    assert row["longitude"] == NEW_LNG
    assert not _migration_recorded()
    _delete_target()


@pytest.mark.django_db(transaction=True)
def test_absent_target_is_symmetric_noop(pre_0110):
    executor = pre_0110
    assert _raw_row(SHRINE_ID) is None

    _migrate(executor, AT_0110)
    assert _raw_row(SHRINE_ID) is None

    _migrate(executor, PRE_0110)
    assert _raw_row(SHRINE_ID) is None


@pytest.mark.django_db(transaction=True)
def test_reverse_restores_exact_old_coordinate(pre_0110):
    executor = pre_0110
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)

    _migrate(executor, AT_0110)
    _migrate(executor, PRE_0110)

    row = _raw_row(SHRINE_ID)
    assert row["latitude"] == OLD_LAT
    assert row["longitude"] == OLD_LNG
    assert row["name_jp"] == NAME
    assert row["address"] == ADDRESS


@pytest.mark.django_db(transaction=True)
def test_forward_reverse_forward_is_deterministic(pre_0110):
    executor = pre_0110
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)

    _migrate(executor, AT_0110)
    first = _raw_row(SHRINE_ID)
    assert first["latitude"] == NEW_LAT
    assert first["longitude"] == NEW_LNG

    _migrate(executor, PRE_0110)
    reverted = _raw_row(SHRINE_ID)
    assert reverted["latitude"] == OLD_LAT
    assert reverted["longitude"] == OLD_LNG

    _migrate(executor, AT_0110)
    second = _raw_row(SHRINE_ID)
    assert second["latitude"] == NEW_LAT
    assert second["longitude"] == NEW_LNG
    assert second["name_jp"] == first["name_jp"]
    assert second["address"] == first["address"]
    assert second["location"] == first["location"]


@pytest.mark.django_db(transaction=True)
def test_reverse_unexpected_coordinate_fails_closed(pre_0110):
    executor = pre_0110
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)

    _migrate(executor, AT_0110)
    with connection.cursor() as cur:
        cur.execute(
            "UPDATE temples_shrine SET latitude = %s, longitude = %s WHERE id = %s",
            [34.8888, 135.8888, SHRINE_ID],
        )
    before = _raw_row(SHRINE_ID)

    with pytest.raises(PreconditionViolation):
        _migrate(executor, PRE_0110)

    assert _raw_row(SHRINE_ID) == before
    assert _migration_recorded()


@pytest.mark.django_db(transaction=True)
def test_unrelated_shrine_is_untouched(pre_0110):
    executor = pre_0110
    Shrine = _historical_shrine_model(executor)
    _seed_target(Shrine)
    _seed_other(Shrine)
    other_before = _raw_row(OTHER_SHRINE_ID)

    _migrate(executor, AT_0110)
    assert _raw_row(OTHER_SHRINE_ID) == other_before

    _migrate(executor, PRE_0110)
    assert _raw_row(OTHER_SHRINE_ID) == other_before


def test_migration_dependency_and_shape():
    assert _mod.Migration.dependencies == [
        ("temples", "0109_adopt_izumo_taisha_position")
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
