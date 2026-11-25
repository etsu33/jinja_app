"""`temples/migrations/0107_restore_places_seed_schema.py` の契約テスト。

この migration は「Production の physical schema から欠落した table だけを復旧する」
database-only repair である。ここでは repair 関数を直接呼び、
Production 相当の drift を local test DB 上で再現して挙動を固定する。

なぜ migration chain 経由で検証しないか:
    pytest 実行時は settings が `MIGRATION_MODULES["temples"] = "temples.migrations_nogis"`
    へ切り替わるため（`TEMPLES_USE_NOGIS_MIGRATIONS`）、test DB は主系 lineage ではなく
    NoGIS lineage で構築される。主系 lineage をこのプロセスで読み込むと
    `0045_add_location_state_only` が GDAL を要求して CI で落ちる。
    そのため repair 関数単体と migration の宣言内容を検証する。
    主系 lineage 側の `showmigrations` / `migrate --plan` / `makemigrations --check` は
    PR の Migration QA 手順で確認する。
"""

import importlib

import pytest
from django.apps import apps as global_apps
from django.db import connection, migrations

from temples.models_places_seeds import PlacesSeed, PlacesSeedState

MIGRATION_MODULE = "temples.migrations.0107_restore_places_seed_schema"

SEED_TABLE = PlacesSeed._meta.db_table
STATE_TABLE = PlacesSeedState._meta.db_table


@pytest.fixture
def migration_module():
    return importlib.import_module(MIGRATION_MODULE)


def _table_names():
    return set(connection.introspection.table_names())


def _column_names(table_name):
    with connection.cursor() as cursor:
        return {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }


def _drop_table(table_name):
    with connection.cursor() as cursor:
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')


def _run_repair(migration_module):
    # historical app registry の代わりに現行 registry を渡す。
    # PlacesSeed / PlacesSeedState は 0075 が唯一の定義元で以降変更が無く、
    # `makemigrations --check` も差分なしのため、両者は一致する。
    with connection.schema_editor() as schema_editor:
        migration_module.restore_missing_tables(global_apps, schema_editor)


def _make_seed(seed_key="sentinel-seed"):
    return PlacesSeed.objects.create(
        seed_key=seed_key,
        pref_code="13",
        pref="東京都",
        label="capital",
        name="sentinel",
        lat=35.0,
        lng=139.0,
    )


# --- migration の宣言内容（state を動かさないことの保証） -----------------------


def test_migration_is_database_only_repair(migration_module):
    """ProjectState を変更しない。operation は RunPython 1 本だけ。"""
    migration = migration_module.Migration

    assert migration.dependencies == [("temples", "0106_weekly_presentation_snapshot_foundation")]
    assert len(migration.operations) == 1

    operation = migration.operations[0]
    assert isinstance(operation, migrations.RunPython)
    # state_operations を持つ SeparateDatabaseAndState でも CreateModel でもない
    assert not isinstance(operation, migrations.SeparateDatabaseAndState)
    assert operation.reverse_code is migration_module.noop_reverse


def test_reverse_does_not_drop_tables(migration_module):
    """reverse は NO-OP。physical table を消してはいけない。"""
    before = _table_names()

    with connection.schema_editor() as schema_editor:
        migration_module.noop_reverse(global_apps, schema_editor)

    assert SEED_TABLE in before and STATE_TABLE in before
    assert {SEED_TABLE, STATE_TABLE} <= _table_names()


# --- Case A: 両 table 存在（fresh DB 相当） ------------------------------------


@pytest.mark.django_db
def test_healthy_schema_is_noop_and_preserves_data(migration_module):
    """両 table が揃っている環境では no-op。既存 data を壊さない。"""
    seed = _make_seed()
    PlacesSeedState.objects.create(seed=seed)

    columns_before = (_column_names(SEED_TABLE), _column_names(STATE_TABLE))

    _run_repair(migration_module)

    assert {SEED_TABLE, STATE_TABLE} <= _table_names()
    assert (_column_names(SEED_TABLE), _column_names(STATE_TABLE)) == columns_before
    assert PlacesSeed.objects.filter(seed_key=seed.seed_key).exists()
    assert PlacesSeedState.objects.filter(seed_id=seed.seed_key).exists()


@pytest.mark.django_db
def test_repair_is_idempotent_on_healthy_schema(migration_module):
    """正常 schema に対して repair 相当処理を繰り返しても何も変わらない。"""
    seed = _make_seed()
    PlacesSeedState.objects.create(seed=seed)

    snapshot = (_column_names(SEED_TABLE), _column_names(STATE_TABLE))

    _run_repair(migration_module)
    _run_repair(migration_module)

    assert (_column_names(SEED_TABLE), _column_names(STATE_TABLE)) == snapshot
    assert PlacesSeed.objects.count() == 1
    assert PlacesSeedState.objects.count() == 1


# --- Case B: 両 table 欠落（Production drift の再現） ---------------------------


@pytest.mark.django_db
def test_full_drift_is_restored(migration_module):
    """Production 相当の drift（両 table 欠落）から復旧する。"""
    _drop_table(STATE_TABLE)
    _drop_table(SEED_TABLE)
    assert not ({SEED_TABLE, STATE_TABLE} & _table_names())

    _run_repair(migration_module)

    assert {SEED_TABLE, STATE_TABLE} <= _table_names()
    assert _column_names(SEED_TABLE) == {f.column for f in PlacesSeed._meta.local_fields}
    assert _column_names(STATE_TABLE) == {f.column for f in PlacesSeedState._meta.local_fields}


@pytest.mark.django_db
def test_orm_smoke_after_full_restore(migration_module):
    """復旧後に ORM の create / read / relation が通る（外部 API は呼ばない）。"""
    _drop_table(STATE_TABLE)
    _drop_table(SEED_TABLE)

    _run_repair(migration_module)

    seed = _make_seed(seed_key="JP-13-capital")
    state = PlacesSeedState.objects.create(seed=seed, last_status=PlacesSeedState.Status.NEVER)

    fetched = PlacesSeed.objects.select_related("state").get(seed_key="JP-13-capital")
    assert fetched.name == "sentinel"
    assert fetched.is_active is True
    assert fetched.state.pk == state.pk
    assert fetched.state.last_status == PlacesSeedState.Status.NEVER
    assert state.seed.seed_key == "JP-13-capital"


# --- Case C: 部分 drift --------------------------------------------------------


@pytest.mark.django_db
def test_partial_drift_restores_only_missing_table(migration_module):
    """PlacesSeed は残し PlacesSeedState だけ欠落 → state だけ作り直す。"""
    seed = _make_seed(seed_key="keep-me")
    _drop_table(STATE_TABLE)

    assert SEED_TABLE in _table_names()
    assert STATE_TABLE not in _table_names()

    _run_repair(migration_module)

    assert {SEED_TABLE, STATE_TABLE} <= _table_names()
    # PlacesSeed は recreate されていない（sentinel row が残っていることが証拠）
    assert PlacesSeed.objects.filter(seed_key="keep-me").count() == 1
    assert PlacesSeed.objects.get(seed_key="keep-me").name == seed.name
    # 復旧した state table は使える
    PlacesSeedState.objects.create(seed=seed)
    assert PlacesSeedState.objects.filter(seed_id="keep-me").exists()


# --- Case D: 想定外 schema（推測修復しない） -----------------------------------


@pytest.mark.django_db
def test_incomplete_table_is_reported_not_guessed(migration_module):
    """table 名だけ在って column が欠けている場合、推測修復せず検出可能に落ちる。"""
    with connection.cursor() as cursor:
        cursor.execute(f'ALTER TABLE "{SEED_TABLE}" DROP COLUMN "keyword";')

    with pytest.raises(RuntimeError) as excinfo:
        _run_repair(migration_module)

    message = str(excinfo.value)
    assert SEED_TABLE in message
    assert "keyword" in message
    # 推測 ALTER をしていない＝落ちた時点で column は戻っていない
    assert "keyword" not in _column_names(SEED_TABLE)
