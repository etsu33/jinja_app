# backend/tests/test_favorites_migration_0003_retire_legacy_favorite.py
"""`favorites.0003_retire_legacy_favorite` の fail-safe guard を検証する。

Case A: legacy table が空 -> migration 成功、table と migration state から消える。
Case B: legacy table に row が残っている -> migration 失敗、row も table も保持される。

実際に `MigrationExecutor` で 0002 <-> 0003 を往復させるため、各テストは終了時に
必ず最新 state（0003 適用済み）へ復旧する。
"""

import importlib

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

_mod = importlib.import_module("favorites.migrations.0003_retire_legacy_favorite")
LegacyFavoritesDataFound = _mod.LegacyFavoritesDataFound
LEGACY_DATA_MARKER = _mod.LEGACY_DATA_MARKER
LEGACY_TABLE = _mod.LEGACY_TABLE

APP = "favorites"
AT_0002 = "0002_remove_favorite_favorites_f_user_id_5e9d49_idx_and_more"
AT_0003 = "0003_retire_legacy_favorite"


def _migrate(target):
    """favorites app を `target` まで（前方/後方どちらでも）migrate する。"""
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate([(APP, target)])


def _table_exists(name):
    with connection.cursor() as cursor:
        return name in connection.introspection.table_names(cursor)


def _historical_favorite(target):
    """`target` 時点の historical `Favorite` model を返す。"""
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    state = executor.loader.project_state((APP, target))
    return state.apps.get_model(APP, "Favorite")


def _state_has_favorite(target):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    state = executor.loader.project_state((APP, target))
    try:
        state.apps.get_model(APP, "Favorite")
    except LookupError:
        return False
    return True


@pytest.fixture
def at_0002():
    """0002 state（legacy table が存在する状態）を作り、後で必ず 0003 へ戻す。"""
    _migrate(AT_0002)
    assert _table_exists(LEGACY_TABLE), "setup失敗: 0002 state で legacy table が無い"
    try:
        yield
    finally:
        # guard を通せるよう残存 row を除去してから最新 state へ復旧する。
        if _table_exists(LEGACY_TABLE):
            with connection.cursor() as cursor:
                cursor.execute(f'DELETE FROM "{LEGACY_TABLE}"')
        _migrate(AT_0003)
        assert not _table_exists(LEGACY_TABLE), "teardown失敗: legacy tableが残存"


@pytest.mark.django_db(transaction=True)
def test_case_a_empty_legacy_table_is_retired(at_0002):
    """Case A: legacy row が 0 件なら 0003 は成功し table / state から消える。"""
    Favorite = _historical_favorite(AT_0002)
    assert Favorite.objects.count() == 0

    _migrate(AT_0003)

    assert not _table_exists(LEGACY_TABLE)
    assert _state_has_favorite(AT_0002) is True
    assert _state_has_favorite(AT_0003) is False


@pytest.mark.django_db(transaction=True)
def test_case_b_non_empty_legacy_table_stops_migration(at_0002):
    """Case B: legacy row が残っていたら 0003 は失敗し、row も table も保持される。"""
    user = get_user_model().objects.create_user(username="legacy-fav-owner", password="x")
    Favorite = _historical_favorite(AT_0002)
    Favorite.objects.create(user_id=user.pk, target_type="shrine", target_id=1)
    assert Favorite.objects.count() == 1

    with pytest.raises(LegacyFavoritesDataFound) as excinfo:
        _migrate(AT_0003)

    message = str(excinfo.value)
    assert LEGACY_DATA_MARKER in message
    assert LEGACY_TABLE in message
    assert "1 row(s)" in message

    # guard 失敗時に table も row も破壊されないこと（transaction rollback）。
    assert _table_exists(LEGACY_TABLE)
    assert Favorite.objects.count() == 1
    # migration state も 0002 のまま（0003 は未適用）。
    assert _state_has_favorite(AT_0002) is True


@pytest.mark.django_db(transaction=True)
def test_guard_callable_raises_with_actionable_message(at_0002):
    """guard 単体: 例外メッセージが運用判断に必要な情報を含むこと。"""
    user = get_user_model().objects.create_user(username="legacy-fav-owner2", password="x")
    Favorite = _historical_favorite(AT_0002)
    Favorite.objects.create(user_id=user.pk, target_type="shrine", target_id=2)

    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    state = executor.loader.project_state((APP, AT_0002))

    with connection.schema_editor() as schema_editor:
        with pytest.raises(LegacyFavoritesDataFound) as excinfo:
            _mod.guard_legacy_favorites_is_empty(state.apps, schema_editor)

    message = str(excinfo.value)
    assert "does NOT delete them automatically" in message
    assert "Migration STOPPED" in message
