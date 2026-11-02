"""RLS fail-closed detection and explicit CA propagation for `evidence_coverage_audit`.

Mother Ship decisions (2026-11-02): RLS_POLICY = FAIL_CLOSED_WITH_VISIBILITY_AUDIT,
CA_PROPAGATION_POLICY = EXPLICIT_SSLROOTCERT_FAIL_CLOSED.

Offline: synthetic driver objects and the local disposable test database only. No Production connection.
Nothing here evaluates or passes G-6 / G-7.
"""

from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from io import StringIO
from types import SimpleNamespace
from unittest import mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError, connection

from temples.management.commands import evidence_coverage_audit as command_module
from temples.services import audit_rls_visibility as rls
from temples.services import audit_tls_evidence as tls

SECRET_PASSWORD = "SYNTHETIC-NOT-A-SECRET-5d1e"
SECRET_HOST = "db.example.invalid"
SECRET_USER = "synthetic_user.tenantref"
SECRET_ROOTCERT = "/synthetic/secret-dir/provider-root.pem"
SECRETS = (SECRET_PASSWORD, SECRET_HOST, SECRET_USER, SECRET_ROOTCERT, "secret-dir")


# --------------------------------------------------------------------------- #
# explicit CA propagation: pre-connection gate (configured values only)
# --------------------------------------------------------------------------- #


def test_preconnect_accepts_verify_full_with_explicit_rootcert():
    assert (
        tls.preconnect_ca_problems({"sslmode": "verify-full", "sslrootcert": SECRET_ROOTCERT}) == []
    )


@pytest.mark.parametrize(
    "options, problem",
    [
        ({"sslmode": "verify-full"}, "sslrootcert_not_explicit"),
        ({"sslmode": "verify-full", "sslrootcert": ""}, "sslrootcert_not_explicit"),
        ({"sslmode": "verify-full", "sslrootcert": "   "}, "sslrootcert_not_explicit"),
        ({"sslmode": "verify-full", "sslrootcert": "system"}, "sslrootcert_system_not_accepted"),
        ({"sslmode": "verify-full", "sslrootcert": "SYSTEM"}, "sslrootcert_system_not_accepted"),
        (
            {"sslmode": "require", "sslrootcert": SECRET_ROOTCERT},
            "configured_sslmode_not_verify_full",
        ),
        (
            {"sslmode": "verify-ca", "sslrootcert": SECRET_ROOTCERT},
            "configured_sslmode_not_verify_full",
        ),
        ({}, "configured_sslmode_not_verify_full"),
        (None, "sslrootcert_not_explicit"),
    ],
)
def test_preconnect_missing_or_weak_ca_fails_closed(options, problem):
    problems = tls.preconnect_ca_problems(options)
    assert problem in problems
    assert not any(secret in " ".join(problems) for secret in SECRETS)


# --------------------------------------------------------------------------- #
# explicit CA propagation: live conninfo must show the explicitly configured file
# --------------------------------------------------------------------------- #


def _conn(
    *, configured=SECRET_ROOTCERT, live=SECRET_ROOTCERT, info_raises=False, raw_missing=False
):
    class _PG:
        @property
        def info(self):
            if info_raises:
                raise RuntimeError(f"conninfo failed for {SECRET_HOST} password={SECRET_PASSWORD}")
            return [
                SimpleNamespace(keyword=b"host", val=SECRET_HOST.encode()),
                SimpleNamespace(keyword=b"password", val=SECRET_PASSWORD.encode()),
                SimpleNamespace(keyword=b"sslrootcert", val=live.encode() if live else None),
            ]

    options = {"sslmode": "verify-full"}
    if configured is not None:
        options["sslrootcert"] = configured
    raw = None if raw_missing else SimpleNamespace(pgconn=_PG())
    return SimpleNamespace(connection=raw, settings_dict={"OPTIONS": options})


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({}, "explicit_match"),
        ({"live": "/synthetic/other/ca.pem"}, "mismatch"),
        ({"live": "system"}, "system"),
        ({"configured": None}, "implicit"),  # e.g. PGSSLROOTCERT, not explicit propagation
        ({"configured": None, "live": None}, "not_configured"),
        ({"live": None}, "not_configured"),
        ({"info_raises": True}, "unknown"),
        ({"raw_missing": True}, "unknown"),
    ],
)
def test_live_ca_propagation(kwargs, expected):
    result = tls.observe_ca_propagation(_conn(**kwargs))
    assert result == expected
    assert not any(secret in result for secret in SECRETS)
    assert tls.production_ca_problems(result) == (
        [] if expected == "explicit_match" else ["ca_not_explicitly_propagated"]
    )


# --------------------------------------------------------------------------- #
# RLS: visibility audit and fail-closed rules (synthetic)
# --------------------------------------------------------------------------- #


class _Cursor:
    def __init__(self, rows=None, role_row=(False,), error=None):
        self._results = [rows, role_row]
        self._error = error
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        if self._error:
            raise self._error
        self.executed.append(sql)

    def fetchall(self):
        return self._results[0]

    def fetchone(self):
        return self._results[1]


def _visibility(rows, role_row=(False,), error=None, tables=("a", "b")):
    cursor = _Cursor(rows=rows, role_row=role_row, error=error)
    return rls.collect_rls_visibility(SimpleNamespace(cursor=lambda: cursor), list(tables), "off")


def test_no_rls_and_no_bypass_is_clean():
    v = _visibility([("a", False, False), ("b", False, False)])
    assert v["status"] == "no_rls"
    assert v["role_bypasses_rls"] == "false"
    assert rls.production_rls_problems(v) == []


def test_rls_enabled_table_is_recorded_and_blocks_production():
    v = _visibility([("a", True, True), ("b", False, False)])
    assert v["status"] == "rls_enabled"
    assert v["rls_enabled_tables"] == ["a"]
    assert v["rls_forced_tables"] == ["a"]
    assert rls.production_rls_problems(v) == ["rls_enabled_on_audited_tables"]


@pytest.mark.parametrize(
    "rows, error",
    [
        ([("a", None, None), ("b", False, False)], None),  # unresolved table
        ([("a", False, False)], None),  # row count mismatch
        (None, RuntimeError(f"catalog failed {SECRET_HOST}")),
    ],
)
def test_unknown_rls_state_blocks_production(rows, error):
    v = _visibility(rows, error=error)
    assert v["status"] == "unknown"
    assert "rls_state_unknown" in rls.production_rls_problems(v)
    assert SECRET_HOST not in json.dumps(v)


@pytest.mark.parametrize("role_row, problem", [((True,), True), (None, True), ((False,), False)])
def test_role_that_can_bypass_rls_blocks_production(role_row, problem):
    v = _visibility([("a", False, False), ("b", False, False)], role_row=role_row)
    assert ("role_bypass_rls_not_excluded" in rls.production_rls_problems(v)) is problem


def test_row_security_not_off_blocks_production():
    v = {"row_security": "on", "status": "no_rls", "role_bypasses_rls": "false"}
    assert rls.production_rls_problems(v) == ["row_security_not_off"]


@pytest.mark.parametrize(
    "sqlstate, text, expected",
    [
        (
            "42501",
            'query would be affected by row-level security policy for table "x"',
            "row_level_security_would_apply",
        ),
        ("42501", "permission denied for table x", "privilege_missing"),
        ("57014", "canceling statement due to statement timeout", None),
        (None, "anything", None),
    ],
)
def test_refusal_reason_classifies_without_text(sqlstate, text, expected):
    cause = Exception(text)
    cause.sqlstate = sqlstate
    exc = Exception("wrapped")
    exc.__cause__ = cause
    assert rls.refusal_reason(exc) == expected


# --------------------------------------------------------------------------- #
# command integration on the local disposable test database
# --------------------------------------------------------------------------- #


def _require_postgres_and_createrole():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL only")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT rolcreaterole OR rolsuper FROM pg_roles WHERE rolname = current_user"
        )
        if not cursor.fetchone()[0]:
            pytest.skip("NOT RUN: test database role cannot create roles")


@contextmanager
def _rls_enabled(table: str):
    quoted = connection.ops.quote_name(table)
    with connection.cursor() as cursor:
        cursor.execute(f"ALTER TABLE {quoted} ENABLE ROW LEVEL SECURITY")
    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute(f"ALTER TABLE {quoted} DISABLE ROW LEVEL SECURITY")


@contextmanager
def _restricted_role(tables: list[str]):
    """NOLOGIN, NOBYPASSRLS role with SELECT on `tables` only, entered with SET ROLE."""
    role = f"ec_rls_{uuid.uuid4().hex[:10]}"
    with connection.cursor() as cursor:
        cursor.execute(f"CREATE ROLE {role} NOLOGIN NOBYPASSRLS")
        cursor.execute(f"GRANT USAGE ON SCHEMA public TO {role}")
        for table in tables:
            cursor.execute(f"GRANT SELECT ON TABLE {connection.ops.quote_name(table)} TO {role}")
        cursor.execute(f"SET ROLE {role}")
    try:
        yield role
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET ROLE")
            cursor.execute(f"DROP OWNED BY {role}")
            cursor.execute(f"DROP ROLE {role}")


def _run_local_json() -> dict:
    out = StringIO()
    call_command(
        "evidence_coverage_audit",
        "--data-origin",
        "repository-seed-local",
        "--format",
        "json",
        stdout=out,
    )
    return json.loads(out.getvalue())


@pytest.mark.django_db(transaction=True)
def test_rls_enabled_audited_table_is_visible_in_the_report():
    _require_postgres_and_createrole()
    with _rls_enabled("temples_goriyakutag"):
        report = _run_local_json()  # the test DB owner bypasses RLS; the state is still recorded
    v = report["execution"]["rls_visibility"]
    assert v["row_security"] == "off"
    assert v["status"] == "rls_enabled"
    assert v["rls_enabled_tables"] == ["temples_goriyakutag"]


@pytest.mark.django_db(transaction=True)
def test_production_stops_before_reading_when_an_audited_table_has_rls():
    _require_postgres_and_createrole()
    passing_tls = {
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
    with (
        _rls_enabled("temples_shrine"),
        _restricted_role(command_module.audited_tables()),
        mock.patch.object(command_module, "preconnect_ca_problems", return_value=[]),
        mock.patch.object(
            command_module,
            "collect_tls_evidence",
            side_effect=lambda conn: (dict(passing_tls), conn.connection),
        ),
        mock.patch.object(command_module, "observe_ca_propagation", return_value="explicit_match"),
        mock.patch.object(command_module, "build_evidence_coverage_report") as build,
    ):
        with pytest.raises(CommandError, match="rls_enabled_on_audited_tables"):
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
def test_rls_policy_effect_raises_instead_of_returning_zero_rows():
    """row_security=off is not a bypass: a read that RLS would filter becomes an error, not 0 rows."""
    _require_postgres_and_createrole()
    from temples.models import Shrine

    Shrine.objects.create(name_jp="RLS確認神社", address="東京都")
    tables = command_module.audited_tables()
    with _rls_enabled("temples_shrine"), _restricted_role(tables):
        # control: without row_security=off the same role silently sees 0 rows
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM temples_shrine")
            assert cursor.fetchone()[0] == 0
        out = StringIO()
        with pytest.raises(CommandError, match="row_level_security_would_apply") as excinfo:
            call_command(
                "evidence_coverage_audit", "--data-origin", "repository-seed-local", stdout=out
            )
    assert out.getvalue() == ""
    message = str(excinfo.value)
    assert "temples_shrine" not in message and "policy for table" not in message
    assert excinfo.value.__cause__ is None and excinfo.value.__suppress_context__


@pytest.mark.django_db(transaction=True)
def test_missing_grant_is_reported_as_privilege_refusal():
    _require_postgres_and_createrole()
    tables = [t for t in command_module.audited_tables() if t != "temples_shrine"]
    with _restricted_role(tables):
        with pytest.raises(CommandError, match="privilege_missing"):
            call_command("evidence_coverage_audit", "--data-origin", "repository-seed-local")


@pytest.mark.django_db(transaction=True)
def test_row_security_not_off_aborts_before_reading():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL only")
    with (
        mock.patch.object(command_module, "enforce_row_security_off", return_value="on"),
        mock.patch.object(command_module, "build_evidence_coverage_report") as build,
    ):
        with pytest.raises(CommandError, match="row_security could not be set to off"):
            call_command("evidence_coverage_audit", "--data-origin", "repository-seed-local")
    build.assert_not_called()


@pytest.mark.django_db(transaction=True)
def test_rls_catalog_query_reads_only_catalog():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL only")
    with connection.cursor() as cursor:
        cursor.execute(
            "EXPLAIN (VERBOSE, FORMAT JSON) " + rls._RLS_CATALOG_SQL,
            [command_module.audited_tables()],
        )
        plan = json.dumps(cursor.fetchone()[0])
    assert '"Relation Name": "temples_' not in plan
    assert "pg_class" in plan


# --------------------------------------------------------------------------- #
# production connection path: missing CA and credential redaction
# --------------------------------------------------------------------------- #


@pytest.mark.django_db(transaction=True)
def test_production_missing_ca_stops_before_connecting():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL only")
    out = StringIO()
    with (
        mock.patch.dict(connection.settings_dict["OPTIONS"], {"sslmode": "verify-full"}),
        mock.patch.object(connection, "ensure_connection") as ensure,
        mock.patch.object(command_module, "build_evidence_coverage_report") as build,
    ):
        connection.settings_dict["OPTIONS"].pop("sslrootcert", None)
        with pytest.raises(CommandError, match="sslrootcert_not_explicit") as excinfo:
            call_command(
                "evidence_coverage_audit",
                "--data-origin",
                "production-readonly",
                "--confirm-read-only-production",
                stdout=out,
            )
    ensure.assert_not_called()
    build.assert_not_called()
    assert "before connecting" in str(excinfo.value)
    assert out.getvalue() == ""


@pytest.mark.django_db(transaction=True)
def test_production_system_rootcert_is_refused_without_leaking_the_value():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL only")
    with (
        mock.patch.dict(
            connection.settings_dict["OPTIONS"],
            {"sslmode": "require", "sslrootcert": SECRET_ROOTCERT},
        ),
        mock.patch.object(connection, "ensure_connection") as ensure,
    ):
        with pytest.raises(CommandError, match="configured_sslmode_not_verify_full") as excinfo:
            call_command(
                "evidence_coverage_audit",
                "--data-origin",
                "production-readonly",
                "--confirm-read-only-production",
            )
    ensure.assert_not_called()
    assert not any(secret in str(excinfo.value) for secret in SECRETS)


@pytest.mark.django_db(transaction=True)
def test_production_connection_failure_is_redacted():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL only")
    driver_text = (
        f'connection to server at "{SECRET_HOST}", port 6543 failed: FATAL: password authentication failed '
        f'for user "{SECRET_USER}" password={SECRET_PASSWORD} root certificate file "{SECRET_ROOTCERT}"'
    )
    out, err = StringIO(), StringIO()
    with (
        mock.patch.object(command_module, "preconnect_ca_problems", return_value=[]),
        mock.patch.object(
            connection, "ensure_connection", side_effect=OperationalError(driver_text)
        ),
        mock.patch.object(command_module, "build_evidence_coverage_report") as build,
    ):
        with pytest.raises(CommandError) as excinfo:
            call_command(
                "evidence_coverage_audit",
                "--data-origin",
                "production-readonly",
                "--confirm-read-only-production",
                stdout=out,
                stderr=err,
            )
    build.assert_not_called()
    rendered = " ".join([str(excinfo.value), out.getvalue(), err.getvalue()])
    assert not any(secret in rendered for secret in SECRETS)
    assert "could not connect" in str(excinfo.value)
    # the driver exception is not chained, so a traceback cannot print it either
    assert excinfo.value.__cause__ is None and excinfo.value.__suppress_context__
