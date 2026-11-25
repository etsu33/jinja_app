"""PR-2 PostgreSQL enforcement, schema state, locks, and failure recovery."""

import importlib
from typing import Any, cast

import pytest
from django.db import IntegrityError, OperationalError, ProgrammingError, connection, transaction
from django.db.migrations.loader import MigrationLoader
from temples.constraints_highlights import CompositeForeignKey
from temples.models import (
    Shrine,
    ShrineHighlight,
    ShrineHighlightHistory,
    ShrineHistory,
    ShrineKnowledgeSource,
)

pytestmark = pytest.mark.django_db
MODULES = [
    "temples.migrations.0125_highlights_same_shrine_integrity",
    "temples.migrations_nogis.0024_highlights_same_shrine_integrity",
]
NAMES = {
    "hl_id_shrine_unique",
    "history_id_shrine_unique",
    "hl_history_highlight_shrine_fk",
    "hl_history_history_shrine_fk",
}


@pytest.fixture
def rows():
    shrines = [Shrine.objects.create(name_jp=f"整合性試験{i}") for i in range(2)]
    highlights = [
        ShrineHighlight.objects.create(
            shrine=s, stable_key=f"integrity-{i}", category="architecture"
        )
        for i, s in enumerate(shrines)
    ]
    histories = [
        ShrineHistory.objects.create(
            shrine=s, history_type="historical_event", title="試験", content="試験専用"
        )
        for s in shrines
    ]
    return shrines, highlights, histories


def link(rows):
    shrines, highlights, histories = rows
    return ShrineHighlightHistory.objects.create(
        shrine=shrines[0], highlight=highlights[0], history=histories[0]
    )


def constraints():
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT conname, contype, convalidated, condeferrable,
            pg_get_constraintdef(oid) FROM pg_constraint WHERE conname::text = ANY(%s)""",
            [sorted(NAMES)],
        )
        return {r[0]: r[1:] for r in cursor.fetchall()}


def counts():
    return [m.objects.count() for m in [Shrine, ShrineHistory, ShrineKnowledgeSource]]


def test_database_and_state_describe_same_constraints():
    actual = constraints()
    assert set(actual) == NAMES
    loader = MigrationLoader(connection)
    state = loader.project_state()
    for model in [ShrineHighlight, ShrineHistory, ShrineHighlightHistory]:
        expected = {c.name for c in model._meta.constraints} & NAMES
        saved = {c.name for c in state.apps.get_model("temples", model.__name__)._meta.constraints}
        assert expected <= saved
    for name, (kind, validated, deferrable, definition) in actual.items():
        assert validated and not deferrable
        assert kind == ("f" if name.endswith("_fk") else "u")
        assert "shrine_id" in definition
        assert len(name.encode()) <= 63
    assert (
        "FOREIGN KEY (highlight_id, shrine_id) REFERENCES temples_shrinehighlight(id, shrine_id)"
        in actual["hl_history_highlight_shrine_fk"][3]
    )
    assert (
        "FOREIGN KEY (history_id, shrine_id) REFERENCES temples_shrinehistory(id, shrine_id)"
        in actual["hl_history_history_shrine_fk"][3]
    )
    with connection.cursor() as cursor:
        columns = connection.introspection.get_table_description(
            cursor, ShrineHighlightHistory._meta.db_table
        )
        indexes = connection.introspection.get_constraints(
            cursor, ShrineHighlightHistory._meta.db_table
        )
    assert all(
        not col.null_ok
        for col in columns
        if col.name in {"highlight_id", "history_id", "shrine_id"}
    )
    # The original UNIQUE(highlight_id, history_id) indexes highlight_id first;
    # the ordinary FK index already covers history_id for parent-key checks.
    assert any(
        v["unique"] and v["columns"] == ["highlight_id", "history_id"] for v in indexes.values()
    )
    assert any(v["index"] and v["columns"][0] == "history_id" for v in indexes.values())


def test_valid_relations_preserve_existing_rows(rows):
    shrines, highlights, histories = rows
    extra = ShrineHistory.objects.create(
        shrine=shrines[0], history_type="regional_context", title="試験2", content="試験"
    )
    before = counts()
    link(rows)
    ShrineHighlightHistory.objects.create(shrine=shrines[0], highlight=highlights[0], history=extra)
    ShrineHighlightHistory.objects.create(
        shrine=shrines[1], highlight=highlights[1], history=histories[1]
    )
    assert ShrineHighlightHistory.objects.count() == 3
    assert counts() == before


def test_mismatched_bulk_create_is_rejected(rows):
    shrines, highlights, histories = rows
    with pytest.raises(IntegrityError), transaction.atomic():
        ShrineHighlightHistory.objects.bulk_create(
            [
                ShrineHighlightHistory(
                    shrine=shrines[0], highlight=highlights[0], history=histories[1]
                )
            ]
        )
    assert ShrineHighlightHistory.objects.count() == 0


@pytest.mark.parametrize("field", ["highlight_id", "history_id", "shrine_id"])
@pytest.mark.parametrize("raw", [False, True])
def test_mismatched_update_is_rejected(rows, field, raw):
    shrines, highlights, histories = rows
    item = link(rows)
    value = {
        "highlight_id": highlights[1].pk,
        "history_id": histories[1].pk,
        "shrine_id": shrines[1].pk,
    }[field]
    with pytest.raises(IntegrityError), transaction.atomic():
        if raw:
            with connection.cursor() as cursor:
                cursor.execute(
                    f'UPDATE temples_shrinehighlighthistory SET "{field}" = %s WHERE id = %s',
                    [value, item.pk],
                )
        else:
            ShrineHighlightHistory.objects.filter(pk=item.pk).update(**{field: value})
    item.refresh_from_db()
    assert item.shrine_id == shrines[0].pk


def test_mismatched_sql_insert_is_rejected(rows):
    shrines, highlights, histories = rows
    with pytest.raises(IntegrityError), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO temples_shrinehighlighthistory (highlight_id, history_id, shrine_id) VALUES (%s, %s, %s)",
                [highlights[0].pk, histories[1].pk, shrines[0].pk],
            )


@pytest.mark.parametrize("parent", ["highlight", "history"])
def test_parent_shrine_cannot_break_existing_link(rows, parent):
    shrines, highlights, histories = rows
    link(rows)
    obj = highlights[0] if parent == "highlight" else histories[0]
    with pytest.raises(IntegrityError), transaction.atomic():
        type(obj).objects.filter(pk=obj.pk).update(shrine=shrines[1])
    obj.refresh_from_db()
    assert obj.shrine_id == shrines[0].pk


@pytest.mark.parametrize("field", ["highlight_id", "history_id", "shrine_id"])
def test_link_columns_remain_not_null(rows, field):
    item = link(rows)
    with pytest.raises(IntegrityError), transaction.atomic():
        ShrineHighlightHistory.objects.filter(pk=item.pk).update(**{field: None})


def test_duplicate_relation_rejected_and_transaction_recovers(rows):
    item = link(rows)
    with pytest.raises(IntegrityError), transaction.atomic():
        ShrineHighlightHistory.objects.bulk_create(
            [
                ShrineHighlightHistory(
                    shrine_id=item.shrine_id,
                    highlight_id=item.highlight_id,
                    history_id=item.history_id,
                )
            ]
        )
    assert ShrineHighlightHistory.objects.count() == 1


def test_migration_series_have_identical_operations():
    main, nogis = [importlib.import_module(m).Migration for m in MODULES]
    assert main.atomic and nogis.atomic
    assert main.dependencies == [("temples", "0124_highlight_translation_location_hint")]
    assert nogis.dependencies == [("temples", "0023_highlight_translation_location_hint")]
    assert [op.deconstruct() for op in main.operations] == [
        op.deconstruct() for op in nogis.operations
    ]


def migration_context():
    # 後続のMigration（見どころへのアンサーなど）が乗っても、同一神社制約のMigrationを
    # 対象にする。最新（leaf）を前提にすると、後続のMigrationを外して戻すことになる。
    # この制約は見どころ・由緒・つながりの表だけに効くので、後続の表があっても単独で往復できる。
    loader = MigrationLoader(connection)
    key = next(
        k
        for k in loader.disk_migrations
        if k[0] == "temples" and k[1].endswith("_highlights_same_shrine_integrity")
    )
    active = loader.disk_migrations[key]
    return active, loader.project_state(active.dependencies)


@pytest.mark.parametrize("module", MODULES)
@pytest.mark.django_db(transaction=True)
def test_migration_round_trip_and_locks(module, rows):
    active, before = migration_context()
    migration = importlib.import_module(module).Migration("integrity_test", "temples")
    snapshot = counts()
    link(rows)
    with connection.schema_editor() as editor:
        active.unapply(before.clone(), editor)
    assert not constraints()
    try:
        with connection.schema_editor() as editor:
            state = migration.apply(before.clone(), editor)
            with connection.cursor() as cursor:
                cursor.execute("""SELECT c.relname, l.mode FROM pg_locks l
                    JOIN pg_class c ON c.oid=l.relation
                    WHERE l.pid=pg_backend_pid() AND l.granted""")
                locks = set(cursor.fetchall())
            assert ("temples_shrinehistory", "AccessExclusiveLock") in locks
            assert ("temples_shrinehighlight", "AccessExclusiveLock") in locks
            assert ("temples_shrinehighlighthistory", "ShareRowExclusiveLock") in locks
        assert set(constraints()) == NAMES
        assert any(
            isinstance(c, CompositeForeignKey)
            for c in state.apps.get_model("temples", "ShrineHighlightHistory")._meta.constraints
        )
        with pytest.raises(ProgrammingError), connection.schema_editor() as editor:
            migration.apply(before.clone(), editor)
        assert set(constraints()) == NAMES
        with connection.schema_editor() as editor:
            migration.unapply(before.clone(), editor)
        assert not constraints()
    finally:
        if not constraints():
            with connection.schema_editor() as editor:
                active.apply(before.clone(), editor)
    assert counts() == snapshot


@pytest.mark.django_db(transaction=True)
def test_invalid_existing_link_rolls_back_all_ddl_then_can_retry(rows):
    active, before = migration_context()
    with connection.schema_editor() as editor:
        active.unapply(before.clone(), editor)
    shrines, highlights, histories = rows
    bad = ShrineHighlightHistory.objects.bulk_create(
        [ShrineHighlightHistory(shrine=shrines[0], highlight=highlights[0], history=histories[1])]
    )[0]
    try:
        with pytest.raises(IntegrityError), connection.schema_editor() as editor:
            active.apply(before.clone(), editor)
        assert not constraints()
    finally:
        ShrineHighlightHistory.objects.filter(pk=bad.pk).delete()
        with connection.schema_editor() as editor:
            active.apply(before.clone(), editor)
    assert set(constraints()) == NAMES


@pytest.mark.django_db(transaction=True)
def test_lock_timeout_rolls_back_and_retry_succeeds():
    active, before = migration_context()
    with connection.schema_editor() as editor:
        active.unapply(before.clone(), editor)
    # BaseDatabaseWrapper stubs omit the concrete backend driver attribute.
    blocker = cast(Any, connection).Database.connect(**connection.get_connection_params())
    try:
        blocker.autocommit = False
        with blocker.cursor() as cursor:
            cursor.execute("LOCK TABLE temples_shrinehistory IN ROW EXCLUSIVE MODE")
        with (
            pytest.raises(OperationalError, match="lock timeout"),
            connection.schema_editor() as editor,
        ):
            active.apply(before.clone(), editor)
        assert not constraints()
    finally:
        blocker.rollback()
        blocker.close()
        with connection.schema_editor() as editor:
            active.apply(before.clone(), editor)
    assert set(constraints()) == NAMES
