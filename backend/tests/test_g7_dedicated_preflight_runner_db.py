"""Local disposable database checks for `scripts/g7_dedicated_preflight_runner.py`（readiness §15）.

Runs only against the pytest-django test database on localhost（the CI service container or a local throwaway
cluster）. It never creates a role and never grants or revokes anything. The values are meaningless for Production:
the test checks that every §14.7 statement is accepted by PostgreSQL one at a time and that its result fits the
runner's contract, and that a real libpq session is stopped by the live-settings check and by PF-1.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from django.db import connection

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "g7_dedicated_preflight_runner.py"
_spec = importlib.util.spec_from_file_location("g7_dedicated_preflight_runner_db", SCRIPT)
pf = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = pf
_spec.loader.exec_module(pf)

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
pytestmark = pytest.mark.django_db


def _local_params() -> dict:
    settings = connection.settings_dict
    host = settings.get("HOST") or "localhost"
    if host not in LOCAL_HOSTS or connection.vendor != "postgresql":
        raise RuntimeError("local_disposable_only")
    # Force the actual libpq transport to loopback; never trust a hostname alias.
    return {
        "host": "127.0.0.1",
        "hostaddr": "127.0.0.1",
        "port": settings.get("PORT") or 5432,
        "user": settings.get("USER"),
        "password": settings.get("PASSWORD") or None,
        "dbname": settings["NAME"],
    }


class LocalConnection:
    """Autocommit libpq session to the local test database. `live_settings()` reads the real conninfo."""

    def __init__(self, live_override=None):
        import psycopg  # noqa: PLC0415 - test-only driver; the runner itself imports none

        self.raw = psycopg.connect(**_local_params(), autocommit=True)
        self._live_override = live_override
        self.executed: list[str] = []

    def live_settings(self):
        if self._live_override is not None:
            return self._live_override
        info = {
            o.keyword.decode(): (o.val.decode() if o.val is not None else None)
            for o in self.raw.pgconn.info
        }
        return {
            "sslmode": info.get("sslmode"),
            "sslrootcert": info.get("sslrootcert"),
            "ssl_in_use": bool(self.raw.pgconn.ssl_in_use),
            "user": info.get("user"),
        }

    def execute(self, sql):
        self.executed.append(sql)
        with self.raw.cursor() as cursor:
            cursor.execute(sql)
            if cursor.description is None:
                return pf.QueryResult((), ())
            return pf.QueryResult(
                tuple(c.name for c in cursor.description),
                tuple(tuple(r) for r in cursor.fetchall()),
            )

    def rollback(self):
        self.raw.execute("ROLLBACK")

    def close(self):
        self.raw.close()


class LocalConnector:
    PREFLIGHT_CONNECTOR_KIND = "local_disposable"

    def __init__(self, live_override=None):
        self.live_override = live_override
        self.conn = None

    def connect(self, params):
        self.conn = LocalConnection(self.live_override)
        return self.conn


@pytest.fixture
def ca_file(tmp_path):
    path = tmp_path / "local-synthetic-ca.crt"
    path.write_bytes(
        b"-----BEGIN CERTIFICATE-----\nTE9DQUwtU1lOVEhFVElD\n-----END CERTIFICATE-----\n"
    )
    return path


def _config(ca_file):
    import hashlib  # noqa: PLC0415

    return pf.PreflightConfig(
        sslmode="verify-full",
        sslrootcert=str(ca_file),
        g7_gate1_result={f: "PASS" for f in pf.G7_GATE1_FIELDS},
        expected_ca_sha256=hashlib.sha256(ca_file.read_bytes()).hexdigest(),
        environ={},
    )


def test_disposable_connector_rejects_remote_config(monkeypatch):
    settings = connection.settings_dict
    monkeypatch.setitem(settings, "HOST", "remote.example.invalid")
    with pytest.raises(RuntimeError, match="local_disposable_only"):
        _local_params()


def test_disposable_connector_forces_loopback():
    params = _local_params()
    assert params["host"] == params["hostaddr"] == "127.0.0.1"


def test_every_registry_statement_runs_alone_and_fits_its_contract():
    conn = LocalConnection()
    try:
        for stmt in (*pf.PF_STATEMENTS, pf.PF16_SHOW_ROW_SECURITY):
            conn.execute("BEGIN READ ONLY")
            try:
                if stmt is pf.PF16_SHOW_ROW_SECURITY:
                    assert conn.execute(pf.PF16_ROW_SECURITY_OFF.sql) == pf.QueryResult((), ())
                outcome = pf._evaluate(stmt, conn.execute(stmt.sql))
            finally:
                conn.rollback()
            assert outcome.status in pf.STATUSES, stmt.sub
            assert outcome.reason not in ("malformed_result", "evaluation_error"), stmt.sub
        conn.execute("BEGIN READ ONLY")
        try:
            conn.execute(pf.PF16_ROW_SECURITY_OFF.sql)
            for table, stmt in zip(pf.APPROVED_TABLES, pf.PF16_COUNT_STATEMENTS, strict=True):
                result = conn.execute(stmt.sql)
                assert result.columns == ("t", "count")
                assert (
                    len(result.rows) == 1
                    and result.rows[0][0] == table
                    and type(result.rows[0][1]) is int
                )
        finally:
            conn.rollback()
    finally:
        conn.close()


def test_approved_tables_equal_audited_tables():
    from temples.management.commands.evidence_coverage_audit import audited_tables  # noqa: PLC0415

    assert tuple(audited_tables()) == pf.APPROVED_TABLES


def test_real_libpq_session_without_verify_full_stops_before_sql(ca_file):
    connector = LocalConnector()
    report = pf.run_preflight(_config(ca_file), connector)
    assert report.stopped_at == "LIVE"
    assert report.stop_reason in ("live_sslmode_not_verify_full", "live_sslrootcert_not_configured")
    assert connector.conn.executed == []
    assert connector.conn.raw.closed and report.close == "done"


def test_real_session_stops_at_pf1_and_rolls_back(ca_file):
    live = {
        "sslmode": "verify-full",
        "sslrootcert": str(ca_file),
        "ssl_in_use": True,
        "user": pf.AUDIT_ROLE,
    }
    connector = LocalConnector(live_override=live)
    report = pf.run_preflight(_config(ca_file), connector)
    # The local test role is not kamimusubi_audit_ro, so PF-1 is a FAIL and nothing else is submitted.
    assert (report.stopped_at, report.stop_reason) == ("PF-1", "session_identity_mismatch")
    assert connector.conn.executed == ["BEGIN READ ONLY", pf.PF_STATEMENTS[0].sql]
    assert report.rollback == "done" and report.close == "done"
    assert connector.conn.raw.closed
    shared = dict(report.steps[-1].shared)
    assert shared["role_is_audit_role"] is False and shared["txn_read_only_on"] is True
