"""Cleanup contract of `temples.tests._isolated_migration_db`.

Normal and fault-injected paths: the shared database name is always restored,
a created temporary database is always dropped, the shared test database is
never dropped, the original exception propagates, and cleanup failures are
observable. GIS only, like the migration tests that use the helper.
"""

import os

import pytest
from django.db import connection, connections
from django.db.migrations.executor import MigrationExecutor

from temples.tests import _isolated_migration_db as iso

if os.getenv("USE_GIS") != "1":
    pytest.skip("GIS disabled by env", allow_module_level=True)

# The earliest temples migration keeps each throwaway database cheap to build.
TARGET = [("temples", "0001_initial")]


def _existing_databases() -> set[str]:
    with connection._nodb_cursor() as cur:
        cur.execute("SELECT datname FROM pg_database")
        return {row[0] for row in cur.fetchall()}


def _temporary_databases(shared_name: str) -> set[str]:
    prefix = f"{shared_name}{iso.ISOLATED_NAME_MARKER}"
    return {name for name in _existing_databases() if name.startswith(prefix)}


@pytest.fixture
def shared_name():
    name = connection.settings_dict["NAME"]
    assert _temporary_databases(name) == set()
    yield name
    # Whatever happened, leave the shared connection usable and nothing behind.
    connections["default"].close()
    assert connection.settings_dict["NAME"] == name
    leftovers = _temporary_databases(name)
    for leftover in leftovers:
        iso._drop_isolated_database(name, leftover)
    assert leftovers == set()
    assert name in _existing_databases()


@pytest.mark.django_db(transaction=True)
def test_success_restores_the_shared_name_and_drops_the_temporary_database(shared_name):
    with iso.isolated_migration_database(TARGET) as executor:
        isolated = connection.settings_dict["NAME"]
        assert isolated.startswith(f"{shared_name}{iso.ISOLATED_NAME_MARKER}")
        assert isolated in _existing_databases()
        assert ("temples", "0001_initial") in executor.recorder.applied_migrations()

    assert connection.settings_dict["NAME"] == shared_name
    assert isolated not in _existing_databases()


@pytest.mark.django_db(transaction=True)
def test_exception_in_the_test_body_propagates_and_cleanup_still_runs(shared_name):
    with pytest.raises(ValueError, match="assertion inside the test") as excinfo:
        with iso.isolated_migration_database(TARGET):
            isolated = connection.settings_dict["NAME"]
            raise ValueError("assertion inside the test")

    assert not getattr(excinfo.value, "__notes__", [])
    assert connection.settings_dict["NAME"] == shared_name
    assert isolated not in _existing_databases()


@pytest.mark.django_db(transaction=True)
def test_exception_while_migrating_propagates_and_cleanup_still_runs(shared_name, monkeypatch):
    seen = {}

    def failing_migrate(self, targets, *args, **kwargs):
        seen["isolated"] = connection.settings_dict["NAME"]
        raise RuntimeError("migration failed")

    monkeypatch.setattr(MigrationExecutor, "migrate", failing_migrate)

    with pytest.raises(RuntimeError, match="migration failed"):
        with iso.isolated_migration_database(TARGET):
            pytest.fail("must not yield when migrating fails")

    assert seen["isolated"].startswith(f"{shared_name}{iso.ISOLATED_NAME_MARKER}")
    assert connection.settings_dict["NAME"] == shared_name
    assert seen["isolated"] not in _existing_databases()


def _fail_close_during_cleanup(monkeypatch):
    """`connection.close()` raises from the cleanup call only (the first call,
    before CREATE DATABASE, succeeds)."""
    wrapper = connections["default"]
    real_close = wrapper.close
    calls = {"n": 0}

    def close():
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("close failed")
        real_close()

    monkeypatch.setattr(wrapper, "close", close)
    return calls


@pytest.mark.django_db(transaction=True)
def test_close_failure_after_a_passing_test_is_reported_and_name_restored(shared_name, monkeypatch):
    calls = _fail_close_during_cleanup(monkeypatch)

    with pytest.raises(iso.IsolatedMigrationDatabaseCleanupError, match="close failed") as excinfo:
        with iso.isolated_migration_database(TARGET):
            isolated = connection.settings_dict["NAME"]

    assert calls["n"] == 2
    assert excinfo.value.isolated_name == isolated
    assert isinstance(excinfo.value.__cause__, RuntimeError)
    assert connection.settings_dict["NAME"] == shared_name
    # The drop is still attempted after the failed close.
    assert isolated not in _existing_databases()


@pytest.mark.django_db(transaction=True)
def test_close_failure_keeps_the_original_exception_and_adds_a_note(shared_name, monkeypatch):
    _fail_close_during_cleanup(monkeypatch)

    with pytest.raises(ValueError, match="assertion inside the test") as excinfo:
        with iso.isolated_migration_database(TARGET):
            isolated = connection.settings_dict["NAME"]
            raise ValueError("assertion inside the test")

    notes = excinfo.value.__notes__
    assert len(notes) == 1 and "close failed" in notes[0]
    assert connection.settings_dict["NAME"] == shared_name
    assert isolated not in _existing_databases()


@pytest.mark.django_db(transaction=True)
def test_drop_failure_is_reported_and_the_shared_database_survives(shared_name, monkeypatch):
    real_drop = iso._drop_isolated_database

    def failing_drop(shared, isolated):
        raise RuntimeError("drop failed")

    monkeypatch.setattr(iso, "_drop_isolated_database", failing_drop)

    with pytest.raises(iso.IsolatedMigrationDatabaseCleanupError, match="drop failed"):
        with iso.isolated_migration_database(TARGET):
            isolated = connection.settings_dict["NAME"]

    assert connection.settings_dict["NAME"] == shared_name
    assert shared_name in _existing_databases()
    # The injected failure left it behind: remove it here so the fixture's
    # no-leftover check stays strict.
    assert isolated in _existing_databases()
    real_drop(shared_name, isolated)


@pytest.mark.django_db(transaction=True)
def test_drop_guard_refuses_anything_but_a_temporary_database(shared_name):
    for name in (
        shared_name,
        f"{shared_name}_other",
        "postgres",
        f"x{iso.ISOLATED_NAME_MARKER}abc",
    ):
        with pytest.raises(RuntimeError, match="refusing to drop"):
            iso._drop_isolated_database(shared_name, name)

    assert shared_name in _existing_databases()
