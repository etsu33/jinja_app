"""legacy model 退役 migration の契約テスト。

対象:
    temples/migrations/0108_remove_legacy_temples_models.py         （主系 lineage）
    temples/migrations_nogis/0013_remove_legacy_temples_models.py   （NoGIS lineage）

両 lineage で同じ 4 model / 4 table を退役させることを構造として固定し、
database 側の挙動（fresh / drift / partial drift）は pytest が実際に使う
NoGIS lineage の migration を `Migration.apply()` で動かして検証する。

なぜ主系 migration を executor で動かさないか:
    pytest 実行時の設定だけでは NoGIS lineage に自動切替されないため、
    NoGIS graph が必要な箇所ではテスト内部で
    `MIGRATION_MODULES["temples"] = "temples.migrations_nogis"` を明示して読み込む。
    主系 lineage をこのプロセスで読み込むと
    `0045_add_location_state_only` が GDAL を要求して CI で落ちる。
    主系側の `makemigrations --check` / leaf / final ProjectState は
    PR の Migration QA 手順で確認する。
"""

import importlib

import pytest
from django.apps import apps as global_apps
from django.contrib.auth import get_user_model
from django.db import connection, migrations
from django.db.migrations.exceptions import IrreversibleError
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState
from django.test import override_settings
from django.test.utils import CaptureQueriesContext

from temples.models import Shrine

MAIN_MIGRATION = "temples.migrations.0108_remove_legacy_temples_models"
NOGIS_MIGRATION = "temples.migrations_nogis.0013_remove_legacy_temples_models"

NOGIS_PARENT = "0012_weekly_presentation_snapshot_foundation"
NOGIS_TARGET = "0013_remove_legacy_temples_models"

EXPECTED_TABLES = (
    "temples_like",
    "temples_concierge_recommendation_click_log",
    "temples_conciergehistory",
    "temples_rankinglog",
)
EXPECTED_MODELS = (
    "Like",
    "ConciergeRecommendationClickLog",
    "ConciergeHistory",
    "RankingLog",
)

User = get_user_model()


def _table_names():
    return set(connection.introspection.table_names())


def _nogis_parent_state():
    """NoGIS lineage の 0012 時点の ProjectState（= 4 model がまだ在る状態）。"""
    with override_settings(
        MIGRATION_MODULES={"temples": "temples.migrations_nogis"}
    ):
        loader = MigrationLoader(connection, ignore_no_migrations=True)
    return loader, loader.project_state(("temples", NOGIS_PARENT))


def _recreate_legacy_tables(state, table_subset):
    """historical model から legacy table を作り直す（DDL は手書きしない）。"""
    with connection.schema_editor() as schema_editor:
        for model_name in EXPECTED_MODELS:
            model = state.apps.get_model("temples", model_name)
            if model._meta.db_table in table_subset:
                schema_editor.create_model(model)


def _apply_nogis_migration(loader, before_state):
    migration = loader.disk_migrations[("temples", NOGIS_TARGET)]
    with connection.schema_editor() as schema_editor:
        return migration.apply(before_state.clone(), schema_editor)


# --- 構造（両 lineage が同じ契約であること） ---------------------------------


@pytest.mark.parametrize(
    "module_path, expected_dependency",
    [
        (MAIN_MIGRATION, ("temples", "0107_restore_places_seed_schema")),
        (NOGIS_MIGRATION, ("temples", NOGIS_PARENT)),
    ],
)
def test_migration_shape_is_identical_across_lineages(module_path, expected_dependency):
    module = importlib.import_module(module_path)
    migration = module.Migration

    assert migration.dependencies == [expected_dependency]
    assert module.LEGACY_TABLES == EXPECTED_TABLES
    assert module.LEGACY_MODELS == EXPECTED_MODELS

    guard, split = migration.operations
    assert isinstance(guard, migrations.RunPython)
    assert isinstance(split, migrations.SeparateDatabaseAndState)

    # database 側: DROP TABLE IF EXISTS のみ。CASCADE も no-op reverse も使わない。
    dropped = []
    for operation in split.database_operations:
        assert isinstance(operation, migrations.RunSQL)
        assert operation.reverse_sql is None, "reverse_sql=NOOP は禁止"
        assert "CASCADE" not in operation.sql.upper()
        assert operation.sql.startswith("DROP TABLE IF EXISTS ")
        dropped.append(operation.sql)
    assert len(dropped) == len(EXPECTED_TABLES)
    for table in EXPECTED_TABLES:
        assert any(f'"{table}"' in sql for sql in dropped)

    # state 側: DeleteModel × 4 のみ
    assert [type(op).__name__ for op in split.state_operations] == ["DeleteModel"] * 4
    assert [op.name for op in split.state_operations] == list(EXPECTED_MODELS)


@pytest.mark.parametrize(
    "module_path, migration_name",
    [
        (MAIN_MIGRATION, "0108_remove_legacy_temples_models"),
        (NOGIS_MIGRATION, NOGIS_TARGET),
    ],
)
def test_migration_is_explicitly_irreversible(module_path, migration_name):
    """reverse は IrreversibleError で停止する（state だけ戻る drift を作らない）。"""
    module = importlib.import_module(module_path)
    migration = module.Migration(migration_name, "temples")

    guard = migration.operations[0]
    assert guard.reversible is False

    with connection.schema_editor() as schema_editor:
        with pytest.raises(IrreversibleError):
            migration.unapply(ProjectState(), schema_editor)


@pytest.mark.django_db
def test_reverse_attempt_changes_nothing():
    """unapply 試行後も physical schema は変化しない（silent drift なし）。"""
    module = importlib.import_module(NOGIS_MIGRATION)
    migration = module.Migration(NOGIS_TARGET, "temples")
    tables_before = _table_names()

    with connection.schema_editor() as schema_editor:
        with pytest.raises(IrreversibleError):
            migration.unapply(ProjectState(), schema_editor)

    assert _table_names() == tables_before


# --- database 挙動（NoGIS lineage の実 migration を動かす） --------------------


@pytest.mark.django_db
def test_fresh_schema_drops_all_four_tables():
    """4 legacy table が存在する fresh schema で適用 → 4 table が消える。"""
    loader, parent_state = _nogis_parent_state()
    _recreate_legacy_tables(parent_state, set(EXPECTED_TABLES))
    assert set(EXPECTED_TABLES) <= _table_names()

    active_before = _table_names() - set(EXPECTED_TABLES)

    after_state = _apply_nogis_migration(loader, parent_state)

    assert not (set(EXPECTED_TABLES) & _table_names())
    # active な table は無傷
    assert active_before <= _table_names()
    for model_name in EXPECTED_MODELS:
        assert ("temples", model_name.lower()) not in after_state.models


@pytest.mark.django_db
def test_production_drift_reproduction_does_not_fail():
    """4 table が既に欠落した Production 相当 schema でも失敗しない。"""
    loader, parent_state = _nogis_parent_state()
    assert not (set(EXPECTED_TABLES) & _table_names()), "test DB は 0013 適用済みで 4 table は不在"

    after_state = _apply_nogis_migration(loader, parent_state)

    assert not (set(EXPECTED_TABLES) & _table_names())
    for model_name in EXPECTED_MODELS:
        assert ("temples", model_name.lower()) not in after_state.models


@pytest.mark.django_db
def test_partial_drift_drops_only_existing_tables():
    """一部だけ存在する partial drift でも成功し、最終的に全 4 table が不在になる。"""
    loader, parent_state = _nogis_parent_state()
    present = {"temples_like", "temples_rankinglog"}
    _recreate_legacy_tables(parent_state, present)

    tables = _table_names()
    assert present <= tables
    assert not ({"temples_conciergehistory", "temples_concierge_recommendation_click_log"} & tables)

    after_state = _apply_nogis_migration(loader, parent_state)

    assert not (set(EXPECTED_TABLES) & _table_names())
    for model_name in EXPECTED_MODELS:
        assert ("temples", model_name.lower()) not in after_state.models


# --- regression: Collector が legacy relation を辿らないこと -------------------


@pytest.mark.django_db
def test_user_delete_no_longer_touches_legacy_tables():
    """User.delete が legacy table を問い合わせず成功する。"""
    user = User.objects.create_user(
        username="legacy-retire-user", email="u@example.com", password="password123"
    )
    user_id = user.id

    with CaptureQueriesContext(connection) as captured:
        user.delete()

    sql_text = " ".join(query["sql"] for query in captured.captured_queries)
    for table in (
        "temples_like",
        "temples_conciergehistory",
        "temples_concierge_recommendation_click_log",
    ):
        assert table not in sql_text, f"{table} を参照しています"

    assert not User.objects.filter(id=user_id).exists()


@pytest.mark.django_db
def test_shrine_delete_no_longer_touches_legacy_tables():
    """Shrine.delete が legacy table を問い合わせず成功する。"""
    shrine = Shrine.objects.create(name_jp="退役テスト神社", latitude=35.0, longitude=135.0)
    shrine_id = shrine.id

    with CaptureQueriesContext(connection) as captured:
        shrine.delete()

    sql_text = " ".join(query["sql"] for query in captured.captured_queries)
    for table in ("temples_like", "temples_conciergehistory", "temples_rankinglog"):
        assert table not in sql_text, f"{table} を参照しています"

    assert not Shrine.objects.filter(id=shrine_id).exists()


# --- app registry / import smoke ---------------------------------------------


@pytest.mark.parametrize("model_name", EXPECTED_MODELS)
def test_model_is_gone_from_app_registry(model_name):
    with pytest.raises(LookupError):
        global_apps.get_model("temples", model_name)


def test_import_smoke_after_removal():
    """削除済み model の import 残骸で ImportError が出ないこと。"""
    importlib.import_module("temples.models")
    importlib.import_module("temples.models_concierge_analytics")
    importlib.import_module("temples.services.concierge_history")
    importlib.import_module("temples.api.serializers.concierge")
    importlib.import_module("temples.api.urls")

    from django.urls import get_resolver

    assert get_resolver().url_patterns

    from temples.api.serializers import concierge as alias

    assert "ConciergeHistorySerializer" not in alias.__all__
    assert not hasattr(alias, "ConciergeHistorySerializer")
