"""Contract of the `postgis` marker gate (temples/tests/_postgis_marker.py + conftest)."""

import pytest
from django.db import connection

from temples.tests._postgis_marker import (
    EXTENSION_MISSING_REASON,
    SKIP_REASON,
    postgis_backend_configured,
    postgis_extension_installed,
    postgis_skip_reason,
)

POSTGIS = {"ENGINE": "django.contrib.gis.db.backends.postgis", "NAME": "test_db"}
PLAIN_POSTGRES = {"ENGINE": "django.db.backends.postgresql", "NAME": "test_db"}


class _Probe:
    def __init__(self, result=True, error=None):
        self.calls = 0
        self.result = result
        self.error = error

    def __call__(self):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.result


class _FakeCursor:
    def __init__(self, row=None, error=None):
        self.row = row
        self.error = error
        self.sql = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql):
        self.sql = sql
        if self.error is not None:
            raise self.error

    def fetchone(self):
        return self.row


class _FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


def test_backend_detection_reads_only_the_engine():
    assert postgis_backend_configured(POSTGIS) is True
    assert postgis_backend_configured(PLAIN_POSTGRES) is False
    assert postgis_backend_configured({}) is False


def test_gis_disabled_skips_without_touching_the_database():
    probe = _Probe()

    assert postgis_skip_reason(PLAIN_POSTGRES, probe) == SKIP_REASON
    assert probe.calls == 0


def test_postgis_backend_with_extension_runs():
    probe = _Probe(result=True)

    assert postgis_skip_reason(POSTGIS, probe) is None
    assert probe.calls == 1


def test_postgis_backend_without_extension_skips_with_its_own_reason():
    assert postgis_skip_reason(POSTGIS, _Probe(result=False)) == EXTENSION_MISSING_REASON


def test_unexpected_probe_failure_propagates_instead_of_skipping():
    with pytest.raises(RuntimeError, match="probe exploded"):
        postgis_skip_reason(POSTGIS, _Probe(error=RuntimeError("probe exploded")))


def test_force_override_runs_without_probing():
    probe = _Probe(result=False)

    assert postgis_skip_reason(PLAIN_POSTGRES, probe, force=True) is None
    assert probe.calls == 0


def test_extension_probe_queries_pg_extension():
    present = _FakeCursor(row=(1,))
    assert postgis_extension_installed(_FakeConnection(present)) is True
    assert "pg_extension" in present.sql and "'postgis'" in present.sql

    assert postgis_extension_installed(_FakeConnection(_FakeCursor(row=None))) is False


def test_extension_probe_does_not_swallow_database_errors():
    broken = _FakeConnection(_FakeCursor(error=RuntimeError("connection reset")))

    with pytest.raises(RuntimeError, match="connection reset"):
        postgis_extension_installed(broken)


@pytest.mark.postgis
def test_marked_test_runs_after_the_test_database_is_set_up(db):
    """Runs only when the gate decided PostGIS is available: by then the probe has
    already seen the test database, not the configured development database."""
    assert connection.settings_dict["NAME"].startswith("test_")
    assert postgis_backend_configured(connection.settings_dict)
    assert postgis_extension_installed(connection)
