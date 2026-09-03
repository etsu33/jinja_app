# backend/temples/tests/test_gis_migration_0091_shrine_reason_facts.py
"""Regression tests for temples.0091_fill_missing_local_shrine_reason_facts.

Production has a schema drift: the historical model state this migration's
RunPython runs against declares `Shrine.location` as a PostGIS `PointField`,
but the actual production column is a legacy `text` column. A bare
`Shrine.objects.filter(...).first()` selects every column (including
`location`), so Django's GeometryField converter tries to parse the text
value as WKB and raises `GEOSException` before any row is touched
(confirmed against a restored production dump; see
docs/audit/temples-0091-production-remediation.md).

Separately, two of the migration's target shrine names each have an
accidental duplicate row in production (the original catalog row plus a
later row created by the map "resolve"/Google Places flow, which always has
a `place_ref_id`). `Shrine.Meta.ordering = ["-updated_at"]` means a bare
`.first()` deterministically picks the *duplicate* row, not the catalog row
this migration is meant to enrich.

These tests only run under GIS (module-level skip below): under
`USE_GIS=0` the `temples` app uses `temples.migrations_nogis`, a squashed
migration set that does not contain this migration as a separate step, and
`location` there is a genuine `TextField` with no drift to reproduce.
"""

import os

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

if os.getenv("USE_GIS") != "1":
    pytest.skip("GIS disabled by env", allow_module_level=True)

PRE_0091 = [("temples", "0090_add_rest_healing_tag_to_silent_shrines")]
AT_0091 = [("temples", "0091_fill_missing_local_shrine_reason_facts")]

NAME_A = "長太稲荷神社"
NAME_B = "給田六所神社"
HISTORY_THEME = "守り"
GORIYAKU_A = "地域に根ざした稲荷社として、商売繁盛や五穀豊穣、日々の暮らしの安定を願う神社。"
GORIYAKU_B = "地域の氏神として、暮らしや家内安全、日々の無事を見守る神社。"
TAGS_A = ["商売繁盛", "五穀豊穣", "地域安泰"]
TAGS_B = ["地域安泰", "家内安全"]


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

    Previously this restored to a hardcoded `HEAD` pinned at 0093, which left
    every later migration unapplied for the remainder of the pytest session --
    including 0102's `HistoryThemeAssignment` table. `pytest-randomly` shuffles
    module order, so on any seed that placed this file before an unrelated test
    needing that schema, the unrelated test failed against a stale database.
    """
    _truncate_shrine_tables()
    _migrate(executor, _temples_head(executor))


@pytest.fixture
def pre_0091():
    """Reverse temples to 0090 (0091 unapplied) and restore the full chain afterwards."""
    executor = _executor()
    _migrate(executor, PRE_0091)
    try:
        yield executor
    finally:
        _restore_head(executor)


def _historical_models(executor: MigrationExecutor):
    state = executor.loader.project_state(PRE_0091[0])
    Shrine = state.apps.get_model("temples", "Shrine")
    GoriyakuTag = state.apps.get_model("temples", "GoriyakuTag")
    PlaceRef = state.apps.get_model("temples", "PlaceRef")
    return Shrine, GoriyakuTag, PlaceRef


def _create_duplicate_shrine(Shrine, PlaceRef, name_jp, place_id, **extra):
    """Create a shrine row with a resolved `place_ref`, matching how the
    real map "resolve" flow creates duplicate rows in production (see
    docs/audit/temples-0091-production-remediation.md, Phase 3)."""
    place_ref = PlaceRef.objects.create(place_id=place_id, name=name_jp)
    return Shrine.objects.create(name_jp=name_jp, kind="shrine", place_ref_id=place_ref.pk, **extra)


def _raw_shrine_row(name_jp):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT id, history_theme, goriyaku, updated_at FROM temples_shrine "
            "WHERE name_jp = %s ORDER BY id",
            [name_jp],
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row, strict=True)) for row in cur.fetchall()]


def _raw_tag_names_for_shrine(shrine_id):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT t.name FROM temples_shrine_goriyaku_tags gt "
            "JOIN temples_goriyakutag t ON t.id = gt.goriyakutag_id "
            "WHERE gt.shrine_id = %s ORDER BY t.name",
            [shrine_id],
        )
        return [row[0] for row in cur.fetchall()]


@pytest.mark.django_db(transaction=True)
def test_a_geos_exception_avoided_under_text_location_drift(pre_0091):
    """Test A: 0091 must not raise GEOSException when the physical `location`
    column is `text` (the confirmed production drift condition), even though
    the historical model declares it as a PostGIS PointField."""
    executor = pre_0091
    Shrine, _GoriyakuTag, _PlaceRef = _historical_models(executor)
    shrine = Shrine.objects.create(name_jp=NAME_A, kind="shrine", place_ref_id=None)

    with connection.cursor() as cur:
        # The GiST index on `location` has no default operator class for
        # `text`, so it must be dropped before the type change (and rebuilt
        # after) to simulate the drift without an unrelated index error.
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

    try:
        _migrate(executor, AT_0091)
    finally:
        with connection.cursor() as cur:
            cur.execute(
                'ALTER TABLE temples_shrine ALTER COLUMN "location" TYPE geometry(Point,4326) '
                "USING NULL;"
            )
            for index_name in gist_index_names:
                cur.execute(f'CREATE INDEX "{index_name}" ON temples_shrine USING gist (location);')

    rows = _raw_shrine_row(NAME_A)
    assert len(rows) == 1
    assert rows[0]["history_theme"] == HISTORY_THEME
    assert rows[0]["goriyaku"] == GORIYAKU_A


@pytest.mark.django_db(transaction=True)
def test_b_only_canonical_duplicate_is_updated(pre_0091):
    """Test B: when a name has a duplicate (original catalog row + later
    place-resolved row), only the canonical (no place_ref_id) row is updated."""
    executor = pre_0091
    Shrine, _GoriyakuTag, PlaceRef = _historical_models(executor)

    canonical = Shrine.objects.create(name_jp=NAME_A, kind="shrine", place_ref_id=None)
    duplicate = _create_duplicate_shrine(Shrine, PlaceRef, NAME_A, "ChIJdummyplaceref0001")
    # Duplicate is the more recently touched row, matching the real production
    # pattern (resolve-created rows are newer) and proving `.first()`'s
    # implicit `-updated_at` ordering is not what selects the target.
    Shrine.objects.filter(pk=duplicate.pk).update(name_jp=NAME_A)

    _migrate(executor, AT_0091)

    canonical.refresh_from_db()
    duplicate.refresh_from_db()

    assert canonical.history_theme == HISTORY_THEME
    assert canonical.goriyaku == GORIYAKU_A
    assert duplicate.history_theme == ""
    assert duplicate.goriyaku in ("", None)


@pytest.mark.django_db(transaction=True)
def test_c_non_target_duplicate_left_completely_unchanged(pre_0091):
    """Test C: the untouched duplicate keeps its original field values and
    gets no goriyaku_tags relations, even though a tag matching its name
    exists and would apply if it were (incorrectly) selected."""
    executor = pre_0091
    Shrine, GoriyakuTag, PlaceRef = _historical_models(executor)

    for name in TAGS_A:
        GoriyakuTag.objects.get_or_create(name=name)

    canonical = Shrine.objects.create(name_jp=NAME_A, kind="shrine", place_ref_id=None)
    duplicate = _create_duplicate_shrine(
        Shrine,
        PlaceRef,
        NAME_A,
        "ChIJdummyplaceref0002",
        history_theme="",
        goriyaku="",
    )

    _migrate(executor, AT_0091)

    duplicate.refresh_from_db()
    assert duplicate.history_theme == ""
    assert duplicate.goriyaku in ("", None)
    assert _raw_tag_names_for_shrine(duplicate.id) == []

    canonical.refresh_from_db()
    assert canonical.history_theme == HISTORY_THEME
    assert sorted(_raw_tag_names_for_shrine(canonical.id)) == sorted(TAGS_A)


@pytest.mark.django_db(transaction=True)
def test_d_missing_tag_is_silently_skipped_without_blocking_field_updates(pre_0091):
    """Test D: when a requested tag ("地域安泰", matching production) does not
    exist in GoriyakuTag, the migration must not error, must still set
    history_theme/goriyaku, and must attach only the tags that do exist."""
    executor = pre_0091
    Shrine, GoriyakuTag, _PlaceRef = _historical_models(executor)

    # "地域安泰" intentionally not created, matching production's confirmed gap.
    GoriyakuTag.objects.get_or_create(name="商売繁盛")
    GoriyakuTag.objects.get_or_create(name="五穀豊穣")
    GoriyakuTag.objects.get_or_create(name="家内安全")
    assert not GoriyakuTag.objects.filter(name="地域安泰").exists()

    shrine_a = Shrine.objects.create(name_jp=NAME_A, kind="shrine", place_ref_id=None)
    shrine_b = Shrine.objects.create(name_jp=NAME_B, kind="shrine", place_ref_id=None)

    _migrate(executor, AT_0091)

    shrine_a.refresh_from_db()
    shrine_b.refresh_from_db()

    assert shrine_a.history_theme == HISTORY_THEME
    assert shrine_a.goriyaku == GORIYAKU_A
    assert sorted(_raw_tag_names_for_shrine(shrine_a.id)) == ["五穀豊穣", "商売繁盛"]

    assert shrine_b.history_theme == HISTORY_THEME
    assert shrine_b.goriyaku == GORIYAKU_B
    assert _raw_tag_names_for_shrine(shrine_b.id) == ["家内安全"]


@pytest.mark.django_db(transaction=True)
def test_e_reverse_migration_undoes_only_the_canonical_row(pre_0091):
    """Test E: reversing 0091 clears history_theme/goriyaku and removes the
    tag relations it added, again touching only the canonical row (not any
    duplicate), and without raising GEOSException."""
    executor = pre_0091
    Shrine, GoriyakuTag, PlaceRef = _historical_models(executor)

    for name in TAGS_A:
        GoriyakuTag.objects.get_or_create(name=name)

    canonical = Shrine.objects.create(name_jp=NAME_A, kind="shrine", place_ref_id=None)
    duplicate = _create_duplicate_shrine(Shrine, PlaceRef, NAME_A, "ChIJdummyplaceref0003")

    _migrate(executor, AT_0091)
    canonical.refresh_from_db()
    assert canonical.history_theme == HISTORY_THEME
    assert sorted(_raw_tag_names_for_shrine(canonical.id)) == sorted(TAGS_A)

    _migrate(executor, PRE_0091)

    canonical.refresh_from_db()
    duplicate.refresh_from_db()
    assert canonical.history_theme == ""
    assert canonical.goriyaku in ("", None)
    assert _raw_tag_names_for_shrine(canonical.id) == []
    assert duplicate.history_theme == ""


@pytest.mark.django_db(transaction=True)
def test_f_fresh_db_migration_chain_0090_to_0091_succeeds():
    """Test F: on a fresh migration graph with no pre-existing shrine data
    (nothing named 長太稲荷神社/給田六所神社 exists), 0090 -> 0091 applies and
    reverses cleanly with exit-equivalent success (no exception raised)."""
    executor = _executor()
    try:
        _migrate(executor, PRE_0091)
        _migrate(executor, AT_0091)
        assert _raw_shrine_row(NAME_A) == []
        assert _raw_shrine_row(NAME_B) == []
    finally:
        _restore_head(executor)
