"""Throwaway PostgreSQL databases for historical `temples` migration tests.

`temples.0108_remove_legacy_temples_models` is intentionally irreversible
(its leading `RunPython(..., reverse_code=None)` makes `unapply()` raise
`IrreversibleError` before touching database or state). The shared pytest
database is migrated to HEAD, so a test that needs a pre-0108 schema
(0091 / 0094 / 0099) cannot reach it by reversing that database.

Instead, `isolated_migration_database(target)` creates a separate database,
applies migrations *forward* from zero to `target` only, points the default
connection at it for the duration of the test, and drops it afterwards.
0108 is never applied there, so nothing has to be reversed through it, and
the shared test database is never moved off HEAD.

Cleanup contract:
- once the temporary database exists, its cleanup is always attempted;
- the shared database name is restored even if closing the connection fails;
- only a name of the form `<shared>_mig_<hex>` is ever dropped, never the
  shared test database;
- if the test (or migrating) raised, that exception propagates unchanged and
  cleanup failures are attached to it as notes; otherwise cleanup failures
  raise `IsolatedMigrationDatabaseCleanupError`.

Only for `@pytest.mark.django_db(transaction=True)` tests: a test transaction
would pin the connection to the shared database.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from django.db import connection
from django.db.migrations.executor import MigrationExecutor

ISOLATED_NAME_MARKER = "_mig_"


class IsolatedMigrationDatabaseCleanupError(RuntimeError):
    """Cleanup of a temporary migration database failed after a passing test."""

    def __init__(self, isolated_name: str, errors: list[BaseException]):
        self.isolated_name = isolated_name
        self.errors = errors
        summary = "; ".join(f"{type(err).__name__}: {err}" for err in errors)
        super().__init__(f"cleanup of temporary database {isolated_name!r} failed: {summary}")


def _drop_isolated_database(shared_name: str, isolated_name: str) -> None:
    if isolated_name == shared_name or not isolated_name.startswith(
        f"{shared_name}{ISOLATED_NAME_MARKER}"
    ):
        raise RuntimeError(
            f"refusing to drop {isolated_name!r}: not a temporary migration database"
        )
    # `_nodb_cursor()` is the maintenance-database cursor Django's own test
    # database creation uses for CREATE / DROP DATABASE.
    with connection._nodb_cursor() as cur:
        cur.execute(f'DROP DATABASE IF EXISTS "{isolated_name}" WITH (FORCE)')


def _cleanup(shared_name: str, isolated_name: str, created: bool) -> list[BaseException]:
    errors: list[BaseException] = []
    try:
        connection.close()
    except Exception as exc:  # noqa: BLE001 - collected and reported by the caller
        errors.append(exc)
    finally:
        connection.settings_dict["NAME"] = shared_name
    if created:
        try:
            _drop_isolated_database(shared_name, isolated_name)
        except Exception as exc:  # noqa: BLE001 - collected and reported by the caller
            errors.append(exc)
    return errors


@contextmanager
def isolated_migration_database(target) -> Iterator[MigrationExecutor]:
    shared_name = connection.settings_dict["NAME"]
    isolated_name = f"{shared_name}{ISOLATED_NAME_MARKER}{uuid.uuid4().hex[:12]}"
    created = False

    connection.close()
    try:
        with connection._nodb_cursor() as cur:
            cur.execute(f'CREATE DATABASE "{isolated_name}"')
            created = True
        connection.settings_dict["NAME"] = isolated_name
        with connection.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        executor = MigrationExecutor(connection)
        executor.migrate(target)
        executor.loader.build_graph()
        yield executor
    except BaseException as exc:
        for err in _cleanup(shared_name, isolated_name, created):
            exc.add_note(
                f"isolated migration database cleanup also failed: {type(err).__name__}: {err}"
            )
        raise
    else:
        errors = _cleanup(shared_name, isolated_name, created)
        if errors:
            raise IsolatedMigrationDatabaseCleanupError(isolated_name, errors) from errors[0]
