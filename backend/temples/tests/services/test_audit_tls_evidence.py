"""TLS self-observation for `evidence_coverage_audit`（IN_TRANSACTION_SELF_OBSERVATION）.

Offline: synthetic driver objects and the local disposable test database only. No Production connection.
The evidence is an observation; nothing here evaluates or passes G-6 / G-7.
"""

from __future__ import annotations

import json
import uuid
from io import StringIO
from types import SimpleNamespace
from unittest import mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection

from temples.management.commands import evidence_coverage_audit as command_module
from temples.services import audit_tls_evidence as tls

SECRET_PASSWORD = "SYNTHETIC-NOT-A-SECRET-91c2"
SECRET_HOST = "db.example.invalid"
SECRET_USER = "synthetic_user.tenantref"
SECRET_ROOTCERT = "/synthetic/certs/provider-root.pem"
SECRETS = (SECRET_PASSWORD, SECRET_HOST, SECRET_USER, SECRET_ROOTCERT, "4242")


def _opt(keyword: str, value: str | None):
    return SimpleNamespace(
        keyword=keyword.encode(), val=value.encode() if value is not None else None
    )


def _pgconn(*, sslmode="verify-full", rootcert=SECRET_ROOTCERT, ssl_in_use=True, info_raises=False):
    options = [
        _opt("host", SECRET_HOST),
        _opt("user", SECRET_USER),
        _opt("password", SECRET_PASSWORD),
        _opt("sslmode", sslmode),
        _opt("sslrootcert", rootcert),
    ]

    class _PG:
        backend_pid = 4242

        @property
        def info(self):
            if info_raises:
                raise RuntimeError(f"conninfo failed for {SECRET_HOST} password={SECRET_PASSWORD}")
            return options

    pg = _PG()
    pg.ssl_in_use = ssl_in_use
    return pg


class _Cursor:
    def __init__(self, rows=None, error=None):
        self.rows = rows if rows is not None else [(True,)]
        self.error = error
        self.sql = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.sql.append(sql)
        if self.error is not None:
            raise self.error

    def fetchall(self):
        return self.rows


class _Conn:
    alias = "default"

    def __init__(self, pgconn=None, *, rows=None, error=None, raw_missing=False):
        self.connection = None if raw_missing else SimpleNamespace(pgconn=pgconn)
        self._cursor = _Cursor(rows=rows, error=error)

    def cursor(self):
        return self._cursor


@pytest.fixture(autouse=True)
def _no_real_savepoint(monkeypatch):
    """The collector wraps the pg_stat_ssl query in a savepoint; synthetic connections have none."""

    class _Atomic:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(tls.transaction, "atomic", _Atomic)


def _collect(conn):
    evidence, handle = tls.collect_tls_evidence(conn)
    return evidence, handle


# --------------------------------------------------------------------------- #
# effective sslmode / sslrootcert (from the live conninfo, never settings)
# --------------------------------------------------------------------------- #


def test_verify_full_observed_from_live_conninfo():
    evidence, _ = _collect(_Conn(_pgconn(sslmode="verify-full")))
    assert evidence["effective_sslmode"] == "verify-full"
    assert evidence["verify_full_observed"] == "true"
    assert evidence["sslrootcert_configured"] == "yes"


@pytest.mark.parametrize("mode", ["prefer", "require", "verify-ca", "disable"])
def test_weaker_effective_mode_is_not_verify_full(mode):
    evidence, _ = _collect(_Conn(_pgconn(sslmode=mode)))
    assert evidence["effective_sslmode"] == mode
    assert evidence["verify_full_observed"] == "false"


@pytest.mark.parametrize("bad", [None, "verify_full", "VERIFY-FULL", ""])
def test_unparseable_or_missing_effective_mode_is_unknown(bad):
    evidence, _ = _collect(_Conn(_pgconn(sslmode=bad)))
    assert evidence["effective_sslmode"] == "unknown"
    assert evidence["verify_full_observed"] == "unknown"


def test_conninfo_failure_is_unknown_and_not_leaked():
    evidence, _ = _collect(_Conn(_pgconn(info_raises=True)))
    assert evidence["effective_sslmode"] == "unknown"
    assert evidence["sslrootcert_configured"] == "unknown"
    assert not any(secret in json.dumps(evidence) for secret in SECRETS)


def test_rootcert_absent_is_no():
    evidence, _ = _collect(_Conn(_pgconn(rootcert=None)))
    assert evidence["sslrootcert_configured"] == "no"


def test_settings_are_never_consulted():
    """A connection whose Django settings say verify-full but whose live conninfo says 'prefer'
    is reported as 'prefer' (the collector reads the live connection only)."""
    conn = _Conn(_pgconn(sslmode="prefer"))
    conn.settings_dict = {"OPTIONS": {"sslmode": "verify-full", "sslrootcert": SECRET_ROOTCERT}}
    evidence, _ = _collect(conn)
    assert evidence["effective_sslmode"] == "prefer"
    assert evidence["verify_full_observed"] == "false"


# --------------------------------------------------------------------------- #
# client ssl_in_use / server pg_stat_ssl / consistency
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("value, expected", [(True, "true"), (False, "false"), (None, "unknown")])
def test_client_ssl_in_use(value, expected):
    evidence, _ = _collect(_Conn(_pgconn(ssl_in_use=value)))
    assert evidence["client_ssl_in_use"] == expected


@pytest.mark.parametrize(
    "rows, error, expected",
    [
        ([(True,)], None, "true"),
        ([(False,)], None, "false"),
        ([(None,)], None, "unknown"),
        ([], None, "unknown"),
        ([(True,), (True,)], None, "unknown"),
        (None, RuntimeError(f"permission denied host={SECRET_HOST}"), "unknown"),
    ],
)
def test_server_pg_stat_ssl(rows, error, expected):
    conn = _Conn(_pgconn(), rows=rows, error=error)
    evidence, _ = _collect(conn)
    assert evidence["server_pg_stat_ssl"] == expected
    assert evidence["server_scope"] == "backend_session"
    assert not any(secret in json.dumps(evidence) for secret in SECRETS)


def test_pooler_ambiguity_is_explicit():
    """Agreement is 'consistent', never 'verified'; a pooler cannot be detected."""
    evidence, _ = _collect(_Conn(_pgconn(ssl_in_use=True), rows=[(True,)]))
    assert evidence["client_server_consistency"] == "consistent"
    assert evidence["pooler_detection"] == "unknown"
    assert evidence["certificate_verified"] == evidence["hostname_verified"] == "unknown"
    assert evidence["gate_evaluation"] == "not_evaluated"


@pytest.mark.parametrize("client, server", [(True, [(False,)]), (False, [(True,)])])
def test_client_server_contradiction(client, server):
    evidence, _ = _collect(_Conn(_pgconn(ssl_in_use=client), rows=server))
    assert evidence["client_server_consistency"] == "contradictory"
    assert "client_server_contradiction" in tls.production_tls_problems(evidence)


# --------------------------------------------------------------------------- #
# missing metadata / connection replacement
# --------------------------------------------------------------------------- #


def test_missing_driver_connection_is_unknown_everywhere():
    evidence, handle = _collect(_Conn(raw_missing=True))
    assert handle is None
    for key in (
        "effective_sslmode",
        "client_ssl_in_use",
        "server_pg_stat_ssl",
        "connection_correlation",
    ):
        assert evidence[key] == "unknown", key


def test_missing_pgconn_is_unknown():
    conn = _Conn(None)
    evidence, _ = _collect(conn)
    assert evidence["effective_sslmode"] == "unknown"
    assert evidence["client_ssl_in_use"] == "unknown"


def test_same_connection_is_confirmed():
    conn = _Conn(_pgconn())
    evidence, handle = _collect(conn)
    assert (
        tls.confirm_same_connection(conn, handle, evidence)["connection_correlation"]
        == "same_connection"
    )


def test_replaced_connection_is_mismatch_and_blocks_production():
    conn = _Conn(_pgconn())
    evidence, handle = _collect(conn)
    conn.connection = SimpleNamespace(pgconn=_pgconn())  # Django reopened / replaced the connection
    confirmed = tls.confirm_same_connection(conn, handle, evidence)
    assert confirmed["connection_correlation"] == "mismatch"
    assert "connection_not_correlated" in tls.production_tls_problems(confirmed)


# --------------------------------------------------------------------------- #
# fail-closed rule for production-readonly
# --------------------------------------------------------------------------- #


def test_production_problems_empty_only_when_everything_is_observed():
    evidence, _ = _collect(_Conn(_pgconn(), rows=[(True,)]))
    assert tls.production_tls_problems(evidence) == []


@pytest.mark.parametrize(
    "kwargs, rows, problem",
    [
        ({"sslmode": "require"}, [(True,)], "effective_sslmode_not_verify_full"),
        ({"sslmode": None}, [(True,)], "effective_sslmode_not_verify_full"),
        ({"rootcert": None}, [(True,)], "sslrootcert_not_configured"),
        ({"ssl_in_use": False}, [(False,)], "client_ssl_not_in_use"),
        ({}, [(False,)], "pg_stat_ssl_not_true"),
        ({}, [], "pg_stat_ssl_not_true"),
    ],
)
def test_production_problems(kwargs, rows, problem):
    evidence, _ = _collect(_Conn(_pgconn(**kwargs), rows=rows))
    assert problem in tls.production_tls_problems(evidence)


def test_evidence_contains_only_allowlisted_tokens():
    evidence, _ = _collect(_Conn(_pgconn(), rows=[(True,)]))
    rendered = json.dumps(evidence)
    assert not any(secret in rendered for secret in SECRETS)
    allowed = tls.VALID_SSLMODES | {
        "true",
        "false",
        "unknown",
        "yes",
        "no",
        "pending",
        "same_connection",
        "mismatch",
        "consistent",
        "contradictory",
        "backend_session",
        "not_evaluated",
        "in_transaction_self_observation",
    }
    assert set(evidence.values()) <= allowed


# --------------------------------------------------------------------------- #
# command integration on the local disposable test database
# --------------------------------------------------------------------------- #


@pytest.mark.django_db(transaction=True)
def test_command_collects_on_its_own_connection_inside_the_guarded_transaction(monkeypatch):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL only")
    monkeypatch.undo()  # use the real savepoint for the real database
    seen = {}
    real_collect = tls.collect_tls_evidence

    def spy(conn):
        with conn.cursor() as cursor:
            cursor.execute("SHOW transaction_read_only")
            seen["read_only"] = cursor.fetchone()[0]
        seen["raw"] = conn.connection
        return real_collect(conn)

    out = StringIO()
    with mock.patch.object(command_module, "collect_tls_evidence", side_effect=spy):
        call_command(
            "evidence_coverage_audit",
            "--data-origin",
            "repository-seed-local",
            "--format",
            "json",
            stdout=out,
        )
    report = json.loads(out.getvalue())
    evidence = report["execution"]["tls_evidence"]

    assert seen["read_only"] == "on"  # collected after the guard, in the same transaction
    assert evidence["collection"] == "in_transaction_self_observation"
    assert evidence["connection_correlation"] == "same_connection"
    assert evidence["effective_sslmode"] in tls.VALID_SSLMODES  # read from the live conninfo
    assert evidence["server_pg_stat_ssl"] in ("true", "false")
    assert evidence["gate_evaluation"] == "not_evaluated"
    assert report["execution"]["read_only_guard"] == "postgresql_transaction_read_only"
    db = connection.settings_dict
    rendered = out.getvalue()
    for value in (db.get("PASSWORD"), db.get("USER"), db.get("HOST")):
        if value and value not in ("localhost", "127.0.0.1"):
            assert value not in rendered


@pytest.mark.django_db(transaction=True)
def test_production_origin_fails_closed_without_verify_full(monkeypatch):
    """The local test DB is not verify-full: production-readonly must stop before reading data."""
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL only")
    monkeypatch.undo()
    out = StringIO()
    with (
        mock.patch.object(command_module, "_verify_select_only_role", return_value=None),
        mock.patch.object(command_module, "preconnect_ca_problems", return_value=[]),
    ):
        with mock.patch.object(command_module, "build_evidence_coverage_report") as build:
            with pytest.raises(CommandError, match="effective_sslmode_not_verify_full"):
                call_command(
                    "evidence_coverage_audit",
                    "--data-origin",
                    "production-readonly",
                    "--confirm-read-only-production",
                    stdout=out,
                )
    build.assert_not_called()
    assert out.getvalue() == ""


@pytest.mark.django_db(transaction=True)
def test_production_origin_discards_report_on_connection_mismatch(monkeypatch):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL only")
    monkeypatch.undo()
    ok = {
        "collection": "in_transaction_self_observation",
        "verify_full_observed": "true",
        "sslrootcert_configured": "yes",
        "client_ssl_in_use": "true",
        "server_pg_stat_ssl": "true",
        "client_server_consistency": "consistent",
        "connection_correlation": "pending",
        "gate_evaluation": "not_evaluated",
    }
    out = StringIO()
    clean_rls = {
        "collection": "in_transaction_catalog",
        "row_security": "off",
        "status": "no_rls",
        "role_bypasses_rls": "false",
    }
    with (
        mock.patch.object(command_module, "_verify_select_only_role", return_value=None),
        mock.patch.object(
            command_module, "collect_tls_evidence", return_value=(dict(ok), object())
        ),
        mock.patch.object(command_module, "preconnect_ca_problems", return_value=[]),
        mock.patch.object(command_module, "observe_ca_propagation", return_value="explicit_match"),
        mock.patch.object(command_module, "collect_rls_visibility", return_value=clean_rls),
    ):
        with pytest.raises(CommandError, match="did not finish on the observed connection"):
            call_command(
                "evidence_coverage_audit",
                "--data-origin",
                "production-readonly",
                "--confirm-read-only-production",
                stdout=out,
            )
    assert out.getvalue() == ""


@pytest.mark.django_db(transaction=True)
def test_read_only_guard_failure_stops_before_tls_collection(monkeypatch):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL only")
    monkeypatch.undo()
    fake_cursor = mock.MagicMock()
    fake_cursor.fetchone.return_value = ("off",)
    fake_cursor.__enter__.return_value = fake_cursor
    with (
        mock.patch.object(command_module.connection, "cursor", return_value=fake_cursor),
        mock.patch.object(command_module, "collect_tls_evidence") as collect,
    ):
        with pytest.raises(CommandError, match="not effective"):
            call_command("evidence_coverage_audit", "--data-origin", "repository-seed-local")
    collect.assert_not_called()


@pytest.mark.django_db
def test_pg_stat_ssl_query_reads_only_catalog(monkeypatch):
    """The collector adds no application-table read (catalog / statistics views only)."""
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL only")
    monkeypatch.undo()
    with connection.cursor() as cursor:
        cursor.execute("EXPLAIN (VERBOSE, FORMAT JSON) " + tls._PG_STAT_SSL_SQL)
        plan = json.dumps(cursor.fetchone()[0])
    assert "temples_" not in plan
    evidence, _ = tls.collect_tls_evidence(connection)  # as the session (login) role
    assert evidence["server_pg_stat_ssl"] in ("true", "false")


@pytest.mark.django_db
def test_pg_stat_ssl_is_unknown_when_role_differs_from_session_user(monkeypatch):
    """Observed locally: after SET ROLE to an unprivileged role, pg_stat_ssl hides the session's own
    row, so the collector reports UNKNOWN (fail closed). The audit role must be the login role."""
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL only")
    monkeypatch.undo()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT rolcreaterole OR rolsuper FROM pg_roles WHERE rolname = current_user"
        )
        if not cursor.fetchone()[0]:
            pytest.skip("NOT RUN: test database role cannot create roles")
        role = f"ec_tls_{uuid.uuid4().hex[:10]}"
        cursor.execute(f"CREATE ROLE {role} NOLOGIN")
        cursor.execute(f"SET ROLE {role}")
    try:
        evidence, _ = tls.collect_tls_evidence(connection)
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET ROLE")
    assert evidence["server_pg_stat_ssl"] == "unknown"
    assert "pg_stat_ssl_not_true" in tls.production_tls_problems(evidence)
