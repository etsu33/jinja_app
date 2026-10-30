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

Only for `@pytest.mark.django_db(transaction=True)` tests: a test transaction
would pin the connection to the shared database.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from django.db import connection
from django.db.migrations.executor import MigrationExecutor


@contextmanager
def isolated_migration_database(target) -> Iterator[MigrationExecutor]:
    shared_name = connection.settings_dict["NAME"]
    isolated_name = f"{shared_name}_mig_{uuid.uuid4().hex[:12]}"

    connection.close()
    # `_nodb_cursor()` is the maintenance-database cursor Django's own test
    # database creation uses for CREATE / DROP DATABASE.
    with connection._nodb_cursor() as cur:
        cur.execute(f'CREATE DATABASE "{isolated_name}"')
    connection.settings_dict["NAME"] = isolated_name
    try:
        with connection.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        executor = MigrationExecutor(connection)
        executor.migrate(target)
        executor.loader.build_graph()
        yield executor
    finally:
        connection.close()
        connection.settings_dict["NAME"] = shared_name
        with connection._nodb_cursor() as cur:
            cur.execute(f'DROP DATABASE IF EXISTS "{isolated_name}" WITH (FORCE)')
