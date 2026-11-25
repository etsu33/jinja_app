"""Local disposable database checks for `scripts/g7_dedicated_preflight_runner.py`（readiness §15）.

Runs only against the pytest-django test database on localhost（the CI service container or a local throwaway
cluster）. It never creates a role and never grants or revokes anything. The values are meaningless for Production:
the test checks that every §14.7 statement is accepted by PostgreSQL one at a time and that its result fits the
runner's contract, and that a real libpq session is stopped by the live-settings check and by PF-1.
"""

from __future__ import annotations

import importlib.util
import sys
import time
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


def _open_loopback_raw():
    """A new autocommit libpq connection to the local test database over 127.0.0.1 only."""
    import psycopg  # noqa: PLC0415 - test-only driver; the runner itself imports none

    return psycopg.connect(**_local_params(), autocommit=True)


def _is_loopback_raw(raw) -> bool:
    import psycopg  # noqa: PLC0415

    return type(raw) is psycopg.Connection and not raw.closed and raw.info.hostaddr == "127.0.0.1"


class LocalConnection:
    """Autocommit libpq session to the local test database. `live_settings()` reads the real conninfo.

    It wraps a handle the connector already allocated and recorded（ownership contract step 1）, and refuses
    anything that is not an open psycopg connection whose actual transport address is 127.0.0.1.
    """

    def __init__(self, raw, live_override=None):
        if not _is_loopback_raw(raw):
            raise RuntimeError("local_disposable_only")
        self.raw = raw
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
        self.allocated: list = []  # every handle this connector opened（for assertions only）
        self.backend_pids: list[int] = (
            []
        )  # server-side identity of those handles（for assertions only）
        self._unadopted: list = []

    def connect(self, params):
        raw = _open_loopback_raw()
        self.allocated.append(raw)
        self._unadopted.append(raw)  # recorded before anything else can fail
        self.backend_pids.append(raw.info.backend_pid)
        self.conn = LocalConnection(raw, self.live_override)
        return self.conn

    def release_unadopted(self):
        """Close only handles this connector opened. Never touches the object `connect()` returned."""
        pending, self._unadopted = self._unadopted, []
        for raw in pending:
            if not raw.closed:
                raw.close()


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
    conn = LocalConnection(_open_loopback_raw())
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


def test_sr1_instance_connect_override_on_local_connector_is_rejected(ca_file):
    """SR-1 R2 for the local-disposable kind: the override is never called and no session is opened."""
    connector = LocalConnector()
    called = []
    connector.connect = lambda params: called.append(params)
    report = pf.run_preflight(_config(ca_file), connector)
    assert (report.stopped_at, report.stop_reason) == ("CONNECT", "connector_not_authorized")
    assert called == [] and connector.conn is None


def test_sr1_local_connector_cannot_return_a_fake_connection(ca_file, monkeypatch):
    """SR-1 R1: the local-disposable kind accepts only `LocalConnection`, and never uses anything else."""

    class Other:
        def __init__(self):
            self.calls = []

        def live_settings(self):
            self.calls.append("live_settings")

        def execute(self, sql):
            self.calls.append("execute")

        def rollback(self):
            self.calls.append("rollback")

        def close(self):
            self.calls.append("close")

    other = Other()
    monkeypatch.setattr(
        sys.modules[__name__], "LocalConnection", lambda raw, live_override=None: other
    )
    report = pf.run_preflight(_config(ca_file), LocalConnector())
    assert (report.stopped_at, report.stop_reason) == ("CONNECT", "connection_not_trusted")
    assert other.calls == []


# --------------------------------------------------------------------------- #
# Ownership contract on a real local session（server-side verification via pg_stat_activity）
# --------------------------------------------------------------------------- #


def _live_backends(pids) -> int:
    """How many of these exact server backends still exist（robust to other sessions and parallel workers）.

    Uses its own autocommit loopback session: PostgreSQL caches the `pg_stat_activity` snapshot for the rest of a
    transaction, so querying through the Django test transaction would return stale counts.
    """
    observer = _open_loopback_raw()
    try:
        row = observer.execute(
            "SELECT count(*) FROM pg_stat_activity WHERE pid = ANY(%s)", [list(pids)]
        ).fetchone()
    finally:
        observer.close()
    return row[0]


def _wait_until_gone(pids, timeout: float = 5.0) -> int:
    deadline = time.monotonic() + timeout
    count = _live_backends(pids)
    while count and time.monotonic() < deadline:
        time.sleep(0.05)
        count = _live_backends(pids)
    return count


def test_ownership_observer_sees_open_backends_and_their_exit():
    """Positive control: the server-side check is not vacuous."""
    raw = _open_loopback_raw()
    pid = raw.info.backend_pid
    assert _live_backends([pid]) == 1
    raw.close()
    assert _wait_until_gone([pid]) == 0


def test_ownership_local_handle_is_closed_when_connection_construction_fails(ca_file, monkeypatch):
    seen_before_failure = []

    def failing_construction(raw, live_override=None):
        # The handle really exists on the server before construction fails.
        seen_before_failure.append(_live_backends([raw.info.backend_pid]))
        raise RuntimeError("synthetic construction failure after allocation")

    monkeypatch.setattr(sys.modules[__name__], "LocalConnection", failing_construction)
    connector = LocalConnector()
    report = pf.run_preflight(_config(ca_file), connector)
    assert (report.stopped_at, report.stop_reason) == ("CONNECT", "connection_failed")
    assert report.connector_release == "done" and report.statements_submitted == 0
    assert seen_before_failure == [1]
    assert len(connector.allocated) == 1 and connector.allocated[0].closed
    assert _wait_until_gone(connector.backend_pids) == 0
    assert "synthetic construction failure" not in report.render()


def test_ownership_local_handle_is_closed_when_returned_connection_is_rejected(
    ca_file, monkeypatch
):
    class Rejected:
        def __init__(self, raw, live_override=None):
            self.calls = []
            self.backend_seen = _live_backends([raw.info.backend_pid])  # positive control

        def execute(self, sql):
            self.calls.append(sql)

    made = []
    monkeypatch.setattr(
        sys.modules[__name__],
        "LocalConnection",
        lambda raw, live_override=None: made.append(Rejected(raw)) or made[-1],
    )
    connector = LocalConnector()
    report = pf.run_preflight(_config(ca_file), connector)
    assert report.stop_reason == "connection_not_trusted"
    assert made[0].calls == [] and report.statements_submitted == 0
    assert made[0].backend_seen == 1
    assert report.connector_release == "done" and connector.allocated[0].closed
    assert _wait_until_gone(connector.backend_pids) == 0


def test_ownership_transfer_on_real_session_runner_closes(ca_file):
    live = {
        "sslmode": "verify-full",
        "sslrootcert": str(ca_file),
        "ssl_in_use": True,
        "user": pf.AUDIT_ROLE,
    }
    connector = LocalConnector(live_override=live)
    report = pf.run_preflight(_config(ca_file), connector)
    assert (report.stopped_at, report.stop_reason) == ("PF-1", "session_identity_mismatch")
    assert report.connector_release == "not_needed"  # ownership transferred; the runner closed it
    assert report.rollback == "done" and report.close == "done"
    assert connector.allocated[0].closed and connector._unadopted == [connector.allocated[0]]
    assert _wait_until_gone(connector.backend_pids) == 0


def test_ownership_local_connection_refuses_non_loopback_or_foreign_handles():
    with pytest.raises(RuntimeError, match="local_disposable_only"):
        LocalConnection(object())
    raw = _open_loopback_raw()
    raw.close()
    with pytest.raises(RuntimeError, match="local_disposable_only"):
        LocalConnection(raw)
