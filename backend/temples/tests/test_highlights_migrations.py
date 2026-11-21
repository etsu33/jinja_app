"""Both new migration operation sets round-trip on isolated PostgreSQL tables."""

import importlib
import io

import pytest
from django.apps import apps
from django.core.management import call_command
from django.db import connection, migrations
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState

MAIN = "temples.migrations.0123_highlights_model_foundation"
NOGIS = "temples.migrations_nogis.0022_highlights_model_foundation"
MODELS = [
    "ShrineHighlight",
    "ShrineHighlightHistory",
    "ShrineHighlightSource",
    "ShrineHighlightTranslation",
]


def normalized_operations(module):
    result = []
    for operation in importlib.import_module(module).Migration.operations:
        name, args, kwargs = operation.deconstruct()
        if "fields" in kwargs:
            kwargs = dict(kwargs)
            kwargs["fields"] = [(n, f.deconstruct()[1:]) for n, f in kwargs["fields"]]
        if "field" in kwargs:
            kwargs = dict(kwargs)
            kwargs["field"] = kwargs["field"].deconstruct()[1:]
        result.append((name, args, kwargs))
    return result


def test_migration_series_match_and_only_add_new_tables_and_constraints():
    assert normalized_operations(MAIN) == normalized_operations(NOGIS)
    for module, parent in [
        (MAIN, "0122_shrine_feature_word_en"),
        (NOGIS, "0021_shrine_feature_word_en"),
    ]:
        migration = importlib.import_module(module).Migration
        assert migration.dependencies == [("temples", parent)]
        assert {
            op.name for op in migration.operations if isinstance(op, migrations.CreateModel)
        } == set(MODELS)
        assert all(
            isinstance(op, (migrations.CreateModel, migrations.AddConstraint))
            for op in migration.operations
        )


@pytest.mark.django_db
def test_model_state_and_migration_state_match():
    output = io.StringIO()
    call_command("makemigrations", "temples", check=True, dry_run=True, stdout=output)
    loader = MigrationLoader(connection)
    changes = MigrationAutodetector(loader.project_state(), ProjectState.from_apps(apps)).changes(
        graph=loader.graph
    )
    assert not changes.get("temples"), output.getvalue()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("module", [MAIN, NOGIS])
def test_new_migration_apply_reverse_reapply_preserves_existing_facts(module):
    assert connection.vendor == "postgresql", "This constraint/DDL test requires PostgreSQL"
    loader = MigrationLoader(connection)
    leaf = loader.graph.leaf_nodes("temples")[0]
    # 後続のMigration（PR-3の location_hint など）が乗っても、Highlights基盤の
    # Migrationだけを往復させる。基盤から最新までの鎖を逆順に外し、最後に戻す。
    foundation_key = next(
        ("temples", name.rsplit(".", 1)[-1])
        for name in (MAIN, NOGIS)
        if ("temples", name.rsplit(".", 1)[-1]) in loader.disk_migrations
    )
    plan = loader.graph.forwards_plan(leaf)
    chain = plan[plan.index(foundation_key) :]
    active_migration = loader.disk_migrations[foundation_key]
    before = loader.project_state(active_migration.dependencies)
    current = loader.project_state([leaf])
    states_before = [before] + [loader.project_state([node]) for node in chain[:-1]]
    migration = importlib.import_module(module).Migration("highlights_test", "temples")
    existing = ["temples_shrine", "temples_shrinehistory", "temples_shrineknowledgesource"]

    def counts():
        with connection.cursor() as cursor:
            result = []
            for table in existing:
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                result.append(cursor.fetchone()[0])
            return result

    snapshot = counts()
    # Unapply the active Highlights chain only; never reverse old migrations.
    for node, state in reversed(list(zip(chain, states_before, strict=True))):
        with connection.schema_editor() as editor:
            loader.disk_migrations[node].unapply(state.clone(), editor)
    try:
        assert not {f"temples_{name.lower()}" for name in MODELS} & set(
            connection.introspection.table_names()
        )
        with connection.schema_editor() as editor:
            after = migration.apply(before.clone(), editor)
        with connection.cursor() as cursor:
            for name in MODELS:
                table = after.apps.get_model("temples", name)._meta.db_table
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                assert cursor.fetchone()[0] == 0
                constraints = connection.introspection.get_constraints(cursor, table)
                assert any(c["foreign_key"] for c in constraints.values())
        with connection.schema_editor() as editor:
            migration.unapply(before.clone(), editor)
        with connection.schema_editor() as editor:
            migration.apply(before.clone(), editor)
        assert counts() == snapshot
        assert set(current.models) == set(after.models)
    finally:
        # Restore the active schema even if an assertion failed mid-round-trip.
        tables = set(connection.introspection.table_names())
        with connection.schema_editor() as editor:
            for name in reversed(MODELS):
                model = current.apps.get_model("temples", name)
                if model._meta.db_table in tables:
                    editor.delete_model(model)
        for node, state in zip(chain, states_before, strict=True):
            with connection.schema_editor() as editor:
                loader.disk_migrations[node].apply(state.clone(), editor)


LOCATION_HINT_MAIN = "temples.migrations.0124_highlight_translation_location_hint"
LOCATION_HINT_NOGIS = "temples.migrations_nogis.0023_highlight_translation_location_hint"


def test_location_hint_migration_series_match_and_only_add_one_field():
    assert normalized_operations(LOCATION_HINT_MAIN) == normalized_operations(LOCATION_HINT_NOGIS)
    for module, parent in [
        (LOCATION_HINT_MAIN, "0123_highlights_model_foundation"),
        (LOCATION_HINT_NOGIS, "0022_highlights_model_foundation"),
    ]:
        migration = importlib.import_module(module).Migration
        assert migration.dependencies == [("temples", parent)]
        assert [type(op) for op in migration.operations] == [migrations.AddField]
        assert migration.operations[0].name == "location_hint"
