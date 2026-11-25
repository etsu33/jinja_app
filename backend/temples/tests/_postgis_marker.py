"""Capability check behind the `postgis` pytest marker.

The marker used to query the database from `pytest_runtest_setup`. pytest-django
blocks database access there (the test database may not even be set up yet), so
the query raised `RuntimeError: Database access not allowed`, which was swallowed
and reported as "PostGIS unavailable": every marked test was skipped, even on
the PostGIS CI job.

The check now runs from an autouse fixture (`temples/tests/conftest.py`):
- no database access when the backend is not PostGIS (GIS-disabled jobs skip as before);
- otherwise only after `django_db_setup`, inside `django_db_blocker.unblock()`;
- unexpected database errors propagate instead of turning into a skip.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

SKIP_REASON = "PostGIS is not available in this environment."
EXTENSION_MISSING_REASON = "PostGIS extension is not installed in the test database."


def postgis_backend_configured(settings_dict: Mapping[str, object]) -> bool:
    return "postgis" in str(settings_dict.get("ENGINE") or "")


def postgis_extension_installed(conn) -> bool:
    """True if the `postgis` extension exists in the connected database.

    Database errors are not caught: a failing probe is a broken environment, not a
    database without PostGIS.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'postgis'")
        return cur.fetchone() is not None


def postgis_skip_reason(
    settings_dict: Mapping[str, object],
    probe: Callable[[], bool],
    *,
    force: bool = False,
) -> str | None:
    """None when PostGIS-marked tests should run, otherwise the skip reason.

    `probe` is called only for a PostGIS backend, so GIS-disabled runs never touch
    the database here.
    """
    if force:
        return None
    if not postgis_backend_configured(settings_dict):
        return SKIP_REASON
    if not probe():
        return EXTENSION_MISSING_REASON
    return None
