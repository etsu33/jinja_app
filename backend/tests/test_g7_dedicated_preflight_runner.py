"""Offline tests for `scripts/g7_dedicated_preflight_runner.py`（readiness §14.5 – §14.9, §15）.

Deterministic fake connections only. No database, DNS or network: socket creation and name resolution fail for
every test in this module. Synthetic values only（`.invalid` hosts, fake passwords, references and paths）.
The local-disposable-database checks live in `test_g7_dedicated_preflight_runner_db.py`.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import re
import socket
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "g7_dedicated_preflight_runner.py"
DOC = REPO / "docs" / "audit" / "evidence-coverage-production-readiness-2026-11-01.md"
_spec = importlib.util.spec_from_file_location("g7_dedicated_preflight_runner", SCRIPT)
pf = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = pf  # dataclasses resolve annotations through sys.modules
_spec.loader.exec_module(pf)

PASSWORD = "SYNTH-pw-9d3f:/?#"
HOST = "pooler-synthetic.example.invalid"
PROJECT = "synthprojref0001"
DRIVER_TEXT = (
    f'connection to server at "{HOST}" failed: password authentication failed for {PASSWORD}'
)
CA_PEM = (
    b"-----BEGIN CERTIFICATE-----\nU1lOVEhFVElDLU5PVC1BLVJFQUwtQ0E=\n-----END CERTIFICATE-----\n"
)
SENSITIVE_RELATION = "secret_private_relation_xyz"


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)


@pytest.fixture
def ca_file(tmp_path):
    path = tmp_path / "synthetic-ca-dir" / "synthetic-ca.crt"
    path.parent.mkdir()
    path.write_bytes(CA_PEM)
    path.chmod(0o600)
    return path


def _config(ca_file, **overrides):
    values = dict(
        sslmode="verify-full",
        sslrootcert=str(ca_file),
        g7_gate1_result={f: "PASS" for f in pf.G7_GATE1_FIELDS},
        expected_ca_sha256=hashlib.sha256(CA_PEM).hexdigest(),
        pf16_inventory=None,
        pf17_owner_confirmation=None,
        environ={},
    )
    values.update(overrides)
    return pf.PreflightConfig(**values)


Q = pf.QueryResult


def _pass_results():
    """sub-step id -> QueryResult that PASSes, in registry order."""
    tables = pf.APPROVED_TABLES
    return {
        "PF-1": Q(
            ("role_is_audit_role", "login_role_is_session_role", "txn_read_only"),
            ((True, True, "on"),),
        ),
        "PF-2": Q(
            (
                "rolsuper",
                "rolcreatedb",
                "rolcreaterole",
                "rolreplication",
                "rolbypassrls",
                "rolinherit",
                "rolcanlogin",
                "connlimit_is_1",
                "valid_until_future",
            ),
            ((False, False, False, False, False, False, True, True, True),),
        ),
        "PF-3": Q(("member_of_count",), ((0,),)),
        "PF-4a": Q(("db_connect", "db_create", "db_temp_effective"), ((True, False, True),)),
        "PF-4b": Q(("explicit_db_create_or_temp_for_role",), ((0,),)),
        "PF-5a": Q(("public_usage", "public_create"), ((True, False),)),
        "PF-5b": Q(("other_schemas_with_usage",), ((0,),)),
        "PF-5c": Q(("schemas_with_create",), ((0,),)),
        "PF-6": Q(("audited_readable", "other_readable"), ((10, 0),)),
        "PF-7": Q(("write_class_relations",), ((0,),)),
        "PF-8": Q(("usable_sequences",), ((0,),)),
        "PF-9": Q(("owned_relations", "owned_schemas", "owned_functions"), ((0, 0, 0),)),
        "PF-10": Q(("executable_security_definer",), ((0,),)),
        "PF-11": Q(("default_acl_to_public", "default_acl_to_role"), ((0, 0),)),
        "PF-12": Q(
            ("name", "present", "can_select", "rls_enabled", "rls_forced"),
            tuple((t, True, True, False, False) for t in tables),
        ),
        "PF-13": Q(("legacy_present", "legacy_readable"), ((True, False),)),
        "PF-14a": Q(
            (
                "pg_roles",
                "pg_class",
                "pg_type",
                "pg_stat_ssl",
                "fn_has_table_privilege",
                "fn_to_regclass",
                "fn_unnest",
                "fn_pg_backend_pid",
            ),
            ((True,) * 8,),
        ),
        "PF-14b": Q(("own_pg_stat_ssl_rows", "own_ssl"), ((1, True),)),
        "PF-15a": Q(("default_transaction_read_only",), (("on",),)),
        "PF-15b": Q(("statement_timeout_set",), ((True,),)),
    }


INVENTORY = {t: i * 7 for i, t in enumerate(pf.APPROVED_TABLES)}


class FakeConnection:
    def __init__(self, live, results, raise_on=None, rollback_raises=False, close_raises=False):
        self._live = live
        self._results = results
        self._raise_on = raise_on
        self._rollback_raises = rollback_raises
        self._close_raises = close_raises
        self.executed: list[str] = []
        self.rolled_back = 0
        self.closed = 0

    def live_settings(self):
        if isinstance(self._live, Exception):
            raise self._live
        return self._live

    def execute(self, sql):
        self.executed.append(sql)
        stmt = next(s for s in pf.REGISTRY if s.sql == sql)
        if self._raise_on == stmt.sub:
            raise RuntimeError(DRIVER_TEXT)
        if stmt.sub in self._results:
            return self._results[stmt.sub]
        if stmt.step == "PF-16" and stmt.sub.startswith("PF-16.temples_"):
            table = stmt.sub.split(".", 1)[1]
            return Q(("t", "count"), ((table, INVENTORY[table]),))
        if stmt.sub == "PF-16.show_row_security":
            return Q(("row_security",), (("off",),))
        return Q((), ())  # BEGIN READ ONLY, SET LOCAL

    def rollback(self):
        self.rolled_back += 1
        if self._rollback_raises:
            raise RuntimeError(DRIVER_TEXT)

    def close(self):
        self.closed += 1
        if self._close_raises:
            raise RuntimeError(DRIVER_TEXT)


class FakeConnector:
    PREFLIGHT_CONNECTOR_KIND = "offline_test_double"

    def __init__(self, conn=None, connect_raises=False):
        self.conn = conn
        self.connect_raises = connect_raises
        self.params = []

    def connect(self, params):
        self.params.append(params)
        if self.connect_raises:
            raise RuntimeError(DRIVER_TEXT)
        return self.conn


class AcceptingInventoryPolicy:
    PREFLIGHT_INVENTORY_POLICY_KIND = "offline_test_double"

    def accept(self, inventory):
        return True


def _live(ca_file, **overrides):
    values = {
        "sslmode": "verify-full",
        "sslrootcert": str(ca_file),
        "ssl_in_use": True,
        "user": f"kamimusubi_audit_ro.{PROJECT}",
    }
    values.update(overrides)
    return values


def _run(ca_file, results=None, live=None, config=None, policy=None, **conn_kwargs):
    conn = FakeConnection(
        live if live is not None else _live(ca_file), results or _pass_results(), **conn_kwargs
    )
    connector = FakeConnector(conn)
    report = pf.run_preflight(config or _config(ca_file), connector, policy)
    return report, conn, connector


def _submitted_subs(conn):
    return [next(s for s in pf.REGISTRY if s.sql == sql).sub for sql in conn.executed]


def _assert_redacted(text, ca_file):
    for secret in (
        PASSWORD,
        HOST,
        PROJECT,
        str(ca_file),
        ca_file.name,
        "synthetic-ca-dir",
        DRIVER_TEXT,
        "password authentication",
        SENSITIVE_RELATION,
    ):
        assert secret not in text
    for line in text.splitlines():
        assert re.fullmatch(r"[A-Za-z0-9_.\-]+=[A-Za-z0-9_\-]+", line), line


# --------------------------------------------------------------------------- #
# Ordering and PASS progression
# --------------------------------------------------------------------------- #


def test_full_pass_progression_in_section_14_order(ca_file):
    config = _config(
        ca_file,
        pf16_inventory=INVENTORY,
        pf17_owner_confirmation=pf.OwnerConfirmation(True, date(2026, 11, 2)),
    )
    report, conn, _ = _run(ca_file, config=config, policy=AcceptingInventoryPolicy())
    assert report.stopped_at is None
    assert [s.step for s in report.steps] == list(pf.STEP_ORDER)
    assert all(s.status == "PASS" for s in report.steps)
    assert report.all_pass
    expected = (
        ["begin"]
        + [s.sub for s in pf.PF_STATEMENTS]
        + [
            "PF-16.row_security",
            "PF-16.show_row_security",
            *[f"PF-16.{t}" for t in pf.APPROVED_TABLES],
        ]
    )
    assert _submitted_subs(conn) == expected
    assert conn.rolled_back == 1 and conn.closed == 1
    text = report.render()
    assert "preflight_overall=ALL_PASS_OFFLINE" in text
    # Even an all-PASS offline run never satisfies G-6 / G-7 or authorizes AG-3 / AG-4.
    for line in (
        "g6=UNMET",
        "g7=UNMET",
        "preflight_g7_b1=UNMET",
        "preflight_g7_b2=UNMET",
        "production_connection=STOP",
        "ag3_connection_approval=NOT_AUTHORIZED",
        "ag4_preflight_approval=NOT_AUTHORIZED",
        "role_creation_execution=NOT_AUTHORIZED",
        "grant_execution=NOT_AUTHORIZED",
    ):
        assert line in text.splitlines()
    _assert_redacted(text, ca_file)
    # PF-16 shares match yes/no only, never counts.
    assert "preflight_PF-16.temples_shrine.match=true" in text
    assert "=14" not in text and "=63" not in text


def test_step_order_matches_section_14_6():
    assert pf.STEP_ORDER == ("PF-0", "PF-0b", *[f"PF-{i}" for i in range(1, 18)])


def test_pf_sql_is_verbatim_from_section_14_7():
    text = DOC.read_text(encoding="utf-8")
    block = text.split("### 14.7", 1)[1].split("```sql", 1)[1].split("```", 1)[0]
    doc_statements = [
        line.rstrip(";") for line in block.splitlines() if line and not line.startswith("--")
    ]
    runner = [s.sql for s in pf.PF_STATEMENTS]
    assert doc_statements[0] == "BEGIN READ ONLY" and doc_statements[-1] == "ROLLBACK"
    assert doc_statements[1:-1] == runner


# --------------------------------------------------------------------------- #
# Immediate STOP: no further SQL, rollback and disconnect
# --------------------------------------------------------------------------- #

FAILING = {
    "PF-1": (
        Q(
            ("role_is_audit_role", "login_role_is_session_role", "txn_read_only"),
            ((False, True, "on"),),
        ),
        "FAIL",
    ),
    "PF-3": (Q(("member_of_count",), ((1,),)), "FAIL"),
    "PF-4b": (Q(("explicit_db_create_or_temp_for_role",), ((1,),)), "FAIL"),
    "PF-5b": (Q(("other_schemas_with_usage",), ((2,),)), "UNKNOWN"),
    "PF-6": (Q(("audited_readable", "other_readable"), ((10, 1),)), "UNKNOWN"),
    "PF-7": (Q(("write_class_relations",), ((3,),)), "FAIL"),
    "PF-10": (Q(("executable_security_definer",), ((1,),)), "UNKNOWN"),
    "PF-11": (Q(("default_acl_to_public", "default_acl_to_role"), ((1, 0),)), "UNKNOWN"),
    "PF-14b": (Q(("own_pg_stat_ssl_rows", "own_ssl"), ((0, None),)), "UNKNOWN"),
    "PF-15a": (Q(("default_transaction_read_only",), (("off",),)), "FAIL"),
}


@pytest.mark.parametrize("sub", sorted(FAILING))
def test_stop_after_first_fail_or_unknown(ca_file, sub):
    result, status = FAILING[sub]
    results = _pass_results()
    results[sub] = result
    report, conn, _ = _run(ca_file, results=results)
    step = next(s.step for s in pf.PF_STATEMENTS if s.sub == sub)
    assert report.stopped_at == step
    assert report.steps[-1].step == step and report.steps[-1].status == status
    submitted = _submitted_subs(conn)
    assert submitted[-1] == sub  # nothing after the failed evaluation
    assert submitted.count(sub) == 1  # no retry
    assert conn.rolled_back == 1 and conn.closed == 1
    assert report.rollback == "done" and report.close == "done"
    assert not report.all_pass
    assert "preflight_overall=STOP" in report.render()


def test_rls_enabled_is_a_stop(ca_file):
    results = _pass_results()
    rows = [(t, True, True, t == "temples_shrine", False) for t in pf.APPROVED_TABLES]
    results["PF-12"] = Q(results["PF-12"].columns, tuple(rows))
    report, conn, _ = _run(ca_file, results=results)
    assert (report.stopped_at, report.stop_reason) == ("PF-12", "rls_enabled_stop")
    assert _submitted_subs(conn)[-1] == "PF-12"


def test_execution_exception_stops_with_fixed_token(ca_file):
    report, conn, _ = _run(ca_file, raise_on="PF-8")
    assert (report.stopped_at, report.stop_reason) == ("PF-8", "execution_error")
    assert _submitted_subs(conn)[-1] == "PF-8"
    assert conn.rolled_back == 1 and conn.closed == 1
    _assert_redacted(report.render(), ca_file)


def test_rollback_error_still_closes(ca_file):
    results = _pass_results()
    results["PF-3"] = FAILING["PF-3"][0]
    report, conn, _ = _run(ca_file, results=results, rollback_raises=True)
    assert report.rollback == "error" and conn.closed == 1 and report.close == "done"
    _assert_redacted(report.render(), ca_file)


def test_begin_failure_rolls_back_and_runs_no_pf_sql(ca_file):
    report, conn, _ = _run(ca_file, raise_on="begin")
    assert report.stopped_at == "TXN"
    assert conn.executed == ["BEGIN READ ONLY"]
    assert conn.rolled_back == 1 and conn.closed == 1


# --------------------------------------------------------------------------- #
# Malformed or unexpected results
# --------------------------------------------------------------------------- #

MALFORMED = [
    ("PF-1", Q(("role_is_audit_role",), ((True,),))),  # wrong columns
    (
        "PF-1",
        Q(
            ("role_is_audit_role", "login_role_is_session_role", "txn_read_only"),
            ((1, True, "on"),),
        ),
    ),
    (
        "PF-1",
        Q(
            ("role_is_audit_role", "login_role_is_session_role", "txn_read_only"),
            ((True, True, "maybe"),),
        ),
    ),
    ("PF-2", Q(_pass_results()["PF-2"].columns, ((False,) * 6 + (True, True, "t"),))),
    ("PF-3", Q(("member_of_count",), ((0,), (0,)))),  # two rows
    ("PF-3", Q(("member_of_count",), ((-1,),))),
    ("PF-3", Q(("member_of_count",), (("0",),))),
    ("PF-6", Q(("audited_readable", "other_readable"), ((11, 0),))),
    (
        "PF-12",
        Q(
            ("name", "present", "can_select", "rls_enabled", "rls_forced"),
            tuple((t, True, True, False, False) for t in reversed(pf.APPROVED_TABLES)),
        ),
    ),
    (
        "PF-12",
        Q(
            ("name", "present", "can_select", "rls_enabled", "rls_forced"),
            ((SENSITIVE_RELATION, True, True, False, False),),
        ),
    ),
    ("PF-14b", Q(("own_pg_stat_ssl_rows", "own_ssl"), ())),
    ("PF-15a", Q(("default_transaction_read_only",), ((True,),))),
    ("PF-4a", "not a query result"),
]


@pytest.mark.parametrize("sub,result", MALFORMED)
def test_malformed_results_are_unknown_and_stop(ca_file, sub, result):
    results = _pass_results()
    results[sub] = result
    report, conn, _ = _run(ca_file, results=results)
    assert report.steps[-1].status == "UNKNOWN"
    assert report.stop_reason == "malformed_result"
    assert _submitted_subs(conn)[-1] == sub
    assert conn.rolled_back == 1 and conn.closed == 1
    _assert_redacted(report.render(), ca_file)


@pytest.mark.parametrize("sub", ["PF-1", "PF-2", "PF-3", "PF-13", "PF-15b"])
def test_no_row_is_unknown(ca_file, sub):
    results = _pass_results()
    results[sub] = Q(results[sub].columns, ())
    report, conn, _ = _run(ca_file, results=results)
    assert report.steps[-1].status == "UNKNOWN" and report.stop_reason == "no_row"
    assert _submitted_subs(conn)[-1] == sub


def test_null_value_is_unknown(ca_file):
    results = _pass_results()
    results["PF-14a"] = Q(results["PF-14a"].columns, ((True,) * 7 + (None,),))
    report, _, _ = _run(ca_file, results=results)
    assert (report.stopped_at, report.steps[-1].status) == ("PF-14", "UNKNOWN")


# --------------------------------------------------------------------------- #
# PF-0 / PF-0b offline prerequisites and the explicit CA
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "g7,status",
    [
        (None, "UNKNOWN"),
        ({}, "UNKNOWN"),
        ({**{f: "PASS" for f in pf.G7_GATE1_FIELDS}, "a1_project": "FAIL"}, "FAIL"),
        ({**{f: "PASS" for f in pf.G7_GATE1_FIELDS}, "a2_tenant": "UNKNOWN"}, "UNKNOWN"),
        ({**{f: "PASS" for f in pf.G7_GATE1_FIELDS}, "a2_tenant": "yes"}, "UNKNOWN"),
    ],
)
def test_pf0_stops_before_connecting(ca_file, g7, status):
    report, conn, connector = _run(ca_file, config=_config(ca_file, g7_gate1_result=g7))
    assert (report.stopped_at, report.steps[-1].status) == ("PF-0", status)
    assert connector.params == [] and conn.executed == [] and conn.closed == 0


def _pf0b(ca_file, **overrides):
    report, conn, connector = _run(ca_file, config=_config(ca_file, **overrides))
    assert report.stopped_at == "PF-0b"
    assert connector.params == [] and conn.executed == []
    _assert_redacted(report.render(), ca_file)
    return report


@pytest.mark.parametrize(
    "overrides,reason",
    [
        ({"sslmode": "require"}, "configured_sslmode_not_verify_full"),
        ({"sslmode": "verify-ca"}, "configured_sslmode_not_verify_full"),
        ({"sslmode": None}, "configured_sslmode_not_verify_full"),
        ({"sslrootcert": None}, "sslrootcert_not_explicit"),
        ({"sslrootcert": ""}, "sslrootcert_not_explicit"),
        ({"sslrootcert": "system"}, "sslrootcert_system_not_accepted"),
        ({"sslrootcert": "SYSTEM"}, "sslrootcert_system_not_accepted"),
        ({"sslrootcert": "relative/ca.crt"}, "sslrootcert_not_absolute_path"),
        ({"sslrootcert": "/nonexistent/synthetic/ca.crt"}, "ca_file_invalid"),
        ({"expected_ca_sha256": "0" * 64}, "ca_sha256_mismatch"),
    ],
)
def test_pf0b_rejects_missing_system_invalid_or_mismatched_ca(ca_file, overrides, reason):
    report = _pf0b(ca_file, **overrides)
    assert report.stop_reason == reason
    assert report.steps[-1].status == "FAIL"


def test_pf0b_rejects_implicit_ca_from_environment(ca_file):
    report = _pf0b(ca_file, sslrootcert=None, environ={"PGSSLROOTCERT": str(ca_file)})
    assert report.stop_reason == "sslrootcert_implicit"


@pytest.mark.parametrize("environ", [{"PGSSLROOTCERT": "/other/ca.crt"}, {"PGSSLMODE": "prefer"}])
def test_pf0b_rejects_conflicting_tls_environment(ca_file, environ):
    assert _pf0b(ca_file, environ=environ).stop_reason == "tls_environment_conflict"


def test_pf0b_rejects_directory_and_non_pem(ca_file, tmp_path):
    assert _pf0b(ca_file, sslrootcert=str(tmp_path)).stop_reason == "ca_file_invalid"
    junk = tmp_path / "junk.crt"
    junk.write_bytes(b"not a certificate")
    assert _pf0b(ca_file, sslrootcert=str(junk)).stop_reason == "ca_file_invalid"


def test_pf0b_rejects_ca_inside_repository(ca_file):
    assert _pf0b(ca_file, sslrootcert=str(SCRIPT)).stop_reason == "ca_file_inside_repository"


def test_pf0b_invalid_expected_digest_is_unknown(ca_file):
    report = _pf0b(ca_file, expected_ca_sha256="not-a-digest")
    assert report.steps[-1].status == "UNKNOWN"


def test_default_expected_digest_is_section_8_1_1():
    assert pf.ACCEPTED_CA_SHA256 in DOC.read_text(encoding="utf-8")


def test_connector_receives_only_validated_tls_params(ca_file):
    _, _, connector = _run(ca_file)
    assert connector.params == [pf.ConnectParams(sslmode="verify-full", sslrootcert=str(ca_file))]


# --------------------------------------------------------------------------- #
# Live connection settings and login role
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "overrides,status,reason",
    [
        ({"sslmode": "require"}, "FAIL", "live_sslmode_not_verify_full"),
        ({"sslrootcert": None}, "FAIL", "live_sslrootcert_not_configured"),
        ({"sslrootcert": "system"}, "FAIL", "live_sslrootcert_system"),
        ({"sslrootcert": "/other/synthetic/ca.crt"}, "FAIL", "live_sslrootcert_mismatch"),
        ({"ssl_in_use": False}, "FAIL", "live_ssl_not_in_use"),
        ({"ssl_in_use": None}, "UNKNOWN", "live_settings_unavailable"),
        ({"user": "postgres"}, "FAIL", "login_role_mismatch"),
        ({"user": f"postgres.{PROJECT}"}, "FAIL", "login_role_mismatch"),
        ({"user": "kamimusubi_audit_ro_x"}, "FAIL", "login_role_mismatch"),
        ({"user": "kamimusubi_audit_ro."}, "FAIL", "login_role_mismatch"),
        ({"user": "kamimusubi_audit_ro.a.b"}, "FAIL", "login_role_mismatch"),
    ],
)
def test_live_settings_mismatch_stops_before_any_sql(ca_file, overrides, status, reason):
    report, conn, _ = _run(ca_file, live=_live(ca_file, **overrides))
    assert (report.stopped_at, report.stop_reason) == ("LIVE", reason)
    assert conn.executed == []
    assert (
        conn.rolled_back == 0 and conn.closed == 1
    )  # no transaction to roll back; always disconnect
    _assert_redacted(report.render(), ca_file)
    assert status in ("FAIL", "UNKNOWN")


@pytest.mark.parametrize("live", [{}, {"sslmode": "verify-full"}, RuntimeError(DRIVER_TEXT), "x"])
def test_live_settings_unavailable_stops(ca_file, live):
    report, conn, _ = _run(ca_file, live=live)
    assert (report.stopped_at, report.stop_reason) == ("LIVE", "live_settings_unavailable")
    assert conn.executed == [] and conn.closed == 1
    _assert_redacted(report.render(), ca_file)


def test_plain_login_role_without_pooler_suffix_is_accepted(ca_file):
    report, _, _ = _run(ca_file, live=_live(ca_file, user="kamimusubi_audit_ro"))
    assert report.stopped_at == "PF-16"  # reached the inventory gate


# --------------------------------------------------------------------------- #
# PF-16 independent inventory
# --------------------------------------------------------------------------- #


def test_missing_inventory_stops_before_count_sql(ca_file):
    report, conn, _ = _run(ca_file)
    assert (report.stopped_at, report.stop_reason) == ("PF-16", "independent_inventory_missing")
    assert report.steps[-1].status == "UNKNOWN"
    assert not any(s.startswith("PF-16") for s in _submitted_subs(conn))
    assert not any("count(*) FROM public." in sql for sql in conn.executed)
    assert "row_security" not in " ".join(conn.executed)
    assert "preflight_g7_b1=UNMET" in report.render()
    assert conn.rolled_back == 1 and conn.closed == 1


def test_default_policy_never_accepts_an_inventory(ca_file):
    report, conn, _ = _run(ca_file, config=_config(ca_file, pf16_inventory=INVENTORY))
    assert report.stop_reason == "independent_inventory_contract_unresolved"
    assert not any(s.startswith("PF-16") for s in _submitted_subs(conn))


@pytest.mark.parametrize(
    "inventory",
    [
        {},
        {t: 1 for t in pf.APPROVED_TABLES[:-1]},
        {**INVENTORY, "temples_shrine": -1},
        {**INVENTORY, "temples_shrine": "5"},
        [1, 2],
    ],
)
def test_malformed_inventory_stops_before_count_sql(ca_file, inventory):
    report, conn, _ = _run(
        ca_file,
        config=_config(ca_file, pf16_inventory=inventory),
        policy=AcceptingInventoryPolicy(),
    )
    assert report.stop_reason == "independent_inventory_malformed"
    assert not any(s.startswith("PF-16") for s in _submitted_subs(conn))


def test_policy_without_accepted_kind_is_unresolved(ca_file):
    class Spoof:
        def accept(self, inventory):
            return True

    report, conn, _ = _run(
        ca_file, config=_config(ca_file, pf16_inventory=INVENTORY), policy=Spoof()
    )
    assert report.stop_reason == "independent_inventory_contract_unresolved"
    assert not any(s.startswith("PF-16") for s in _submitted_subs(conn))


def test_count_mismatch_stops_at_that_table(ca_file):
    inventory = {**INVENTORY, "temples_shrinedeity": INVENTORY["temples_shrinedeity"] + 1}
    report, conn, _ = _run(
        ca_file,
        config=_config(ca_file, pf16_inventory=inventory),
        policy=AcceptingInventoryPolicy(),
    )
    assert (report.stopped_at, report.stop_reason) == ("PF-16", "count_mismatch")
    assert _submitted_subs(conn)[-1] == "PF-16.temples_shrinedeity"
    text = report.render()
    assert "preflight_PF-16.temples_shrinedeity.match=false" in text
    assert str(INVENTORY["temples_shrinedeity"]) not in [
        line.split("=")[1] for line in text.splitlines() if "PF-16" in line
    ]


def test_row_security_not_off_stops_before_counts(ca_file):
    results = _pass_results()
    results["PF-16.show_row_security"] = Q(("row_security",), (("on",),))
    report, conn, _ = _run(
        ca_file,
        results=results,
        config=_config(ca_file, pf16_inventory=INVENTORY),
        policy=AcceptingInventoryPolicy(),
    )
    assert report.stop_reason == "row_security_not_off"
    assert _submitted_subs(conn)[-1] == "PF-16.show_row_security"


def test_pf16_count_error_is_unknown(ca_file):
    report, conn, _ = _run(
        ca_file,
        raise_on="PF-16.temples_shrine",
        config=_config(ca_file, pf16_inventory=INVENTORY),
        policy=AcceptingInventoryPolicy(),
    )
    assert (report.stopped_at, report.stop_reason) == ("PF-16", "execution_error")
    assert _submitted_subs(conn)[-1] == "PF-16.temples_shrine"


# --------------------------------------------------------------------------- #
# PF-17
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "confirmation",
    [
        None,
        pf.OwnerConfirmation(False, date(2026, 11, 2)),
        pf.OwnerConfirmation(True, None),
        pf.OwnerConfirmation(True, date.today() + timedelta(days=1)),
        "yes",
    ],
)
def test_pf17_requires_explicit_dated_confirmation(ca_file, confirmation):
    config = _config(ca_file, pf16_inventory=INVENTORY, pf17_owner_confirmation=confirmation)
    report, conn, _ = _run(ca_file, config=config, policy=AcceptingInventoryPolicy())
    assert (report.stopped_at, report.steps[-1].status) == ("PF-17", "UNKNOWN")
    assert conn.rolled_back == 1 and conn.closed == 1


# --------------------------------------------------------------------------- #
# Statement guard: no batch, arbitrary SQL, SET ROLE, mutation or privilege change
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1; SELECT 2",
        "SELECT 1;",
        "BEGIN READ ONLY; SELECT 1",
        "SET ROLE postgres",
        "set role postgres",
        "SET SESSION AUTHORIZATION postgres",
        "RESET ROLE",
        "SELECT 1 FROM pg_roles WHERE rolname = 'x' AND (SELECT set_config('role', 'postgres', true)) IS NOT NULL",
        "INSERT INTO temples_shrine VALUES (1)",
        "UPDATE temples_shrine SET name_jp = 'x'",
        "DELETE FROM temples_shrine",
        "WITH d AS (DELETE FROM temples_shrine RETURNING 1) SELECT * FROM d",
        "SELECT * INTO t2 FROM temples_shrine",
        "SELECT * FROM temples_shrine FOR UPDATE",
        "SELECT * FROM temples_shrine FOR KEY SHARE",
        "CREATE ROLE x",
        "GRANT SELECT ON temples_shrine TO x",
        "REVOKE SELECT ON temples_shrine FROM x",
        "ALTER ROLE kamimusubi_audit_ro SUPERUSER",
        "DROP TABLE temples_shrine",
        "TRUNCATE temples_shrine",
        "COPY temples_shrine TO STDOUT",
        "SELECT pg_terminate_backend(1)",
        "SELECT nextval('s')",
        "SELECT 1 -- comment",
        "SELECT 1 /* c */",
        "SELECT $$x$$",
        'SELECT "x"',
        "SELECT 'unterminated",
        "DO $$BEGIN END$$",
        "EXPLAIN ANALYZE SELECT 1",
        "COMMIT",
        "",
        " SELECT 1",
        None,
    ],
)
def test_guard_rejects_unsafe_statements(sql):
    ok, reason = pf.validate_statement(sql)
    assert ok is False and reason != "ok"


def test_guard_accepts_every_registry_statement():
    for stmt in pf.REGISTRY:
        assert pf.validate_statement(stmt.sql) == (True, "ok"), stmt.sub


def test_registry_has_no_set_role_or_mutation():
    for stmt in pf.REGISTRY:
        upper = stmt.sql.upper()
        assert "SET ROLE" not in upper and "SESSION AUTHORIZATION" not in upper
        assert ";" not in stmt.sql
    controls = [s.sql for s in pf.REGISTRY if not s.sql.startswith(("SELECT", "SHOW"))]
    assert controls == ["BEGIN READ ONLY", "SET LOCAL row_security = off"]


def test_session_refuses_statements_outside_the_registry(ca_file):
    report = pf.PreflightReport()
    conn = FakeConnection(_live(ca_file), _pass_results())
    session = pf._GuardedSession(conn, report)
    lookalike = pf.Statement("PF-1", "PF-1", pf.PF_STATEMENTS[0].sql, pf.PF_STATEMENTS[0].evaluate)
    for stmt in (lookalike, pf.Statement("PF-1", "PF-1", "SELECT 1", pf.PF_STATEMENTS[0].evaluate)):
        with pytest.raises(pf._Stop) as exc:
            session.submit(stmt)
        assert exc.value.reason == "statement_not_in_registry"
    assert conn.executed == []


def test_public_api_takes_no_sql():
    import inspect

    params = set(inspect.signature(pf.run_preflight).parameters)
    assert params == {"config", "connector", "inventory_policy"}
    assert not any("sql" in f for f in pf.PreflightConfig.__dataclass_fields__)


# --------------------------------------------------------------------------- #
# Production and remote connections remain inaccessible
# --------------------------------------------------------------------------- #


def test_default_connector_is_the_disabled_production_path(ca_file):
    report = pf.run_preflight(_config(ca_file))
    assert (report.stopped_at, report.stop_reason) == ("CONNECT", "production_connection_disabled")
    assert report.statements_submitted == 0 and not report.connected


@pytest.mark.parametrize("kind", [None, "production", "remote", "psycopg", ""])
def test_connector_without_accepted_kind_is_never_called(ca_file, kind):
    conn = FakeConnection(_live(ca_file), _pass_results())
    connector = FakeConnector(conn)
    if kind is None:
        connector.PREFLIGHT_CONNECTOR_KIND = None
    else:
        connector.PREFLIGHT_CONNECTOR_KIND = kind
    report = pf.run_preflight(_config(ca_file), connector)
    assert (report.stopped_at, report.stop_reason) == ("CONNECT", "connector_not_authorized")
    assert connector.params == [] and conn.executed == []


def test_spoofed_kind_from_untrusted_connector_never_connects(ca_file):
    class RemoteConnector:
        PREFLIGHT_CONNECTOR_KIND = "offline_test_double"

        def __init__(self):
            self.called = False

        def connect(self, params):
            self.called = True
            raise AssertionError("must never call untrusted connector")

    connector = RemoteConnector()
    report = pf.run_preflight(_config(ca_file), connector)
    assert (report.stopped_at, report.stop_reason) == ("CONNECT", "connector_not_authorized")
    assert not connector.called


def test_spoofed_subclass_is_rejected(ca_file):
    class RemoteSubclass(FakeConnector):
        pass

    connector = RemoteSubclass()
    report = pf.run_preflight(_config(ca_file), connector)
    assert report.stop_reason == "connector_not_authorized"
    assert connector.params == []


def test_accepted_connector_kinds_have_no_production_kind():
    assert pf.ACCEPTED_CONNECTOR_KINDS == frozenset({"offline_test_double", "local_disposable"})
    assert pf.ACCEPTED_INVENTORY_POLICY_KINDS == frozenset({"offline_test_double"})


@pytest.mark.parametrize("cleanup_failure", ["rollback_raises", "close_raises"])
def test_cleanup_failure_turns_all_pass_into_stop(ca_file, cleanup_failure):
    config = _config(
        ca_file,
        pf16_inventory=INVENTORY,
        pf17_owner_confirmation=pf.OwnerConfirmation(True, date(2026, 11, 2)),
    )
    report, conn, _ = _run(ca_file, config=config, policy=AcceptingInventoryPolicy(), **{cleanup_failure: True})
    assert all(step.status == "PASS" for step in report.steps)
    assert report.stopped_at == "CLEANUP"
    assert report.stop_reason == "session_cleanup_failed"
    assert not report.all_pass
    assert "preflight_overall=STOP" in report.render()
    assert conn.rolled_back == 1 and conn.closed == 1
    _assert_redacted(report.render(), ca_file)


def test_connection_failure_is_redacted(ca_file):
    connector = FakeConnector(connect_raises=True)
    report = pf.run_preflight(_config(ca_file), connector)
    assert (report.stopped_at, report.stop_reason) == ("CONNECT", "connection_failed")
    _assert_redacted(report.render(), ca_file)


def test_module_imports_no_driver_socket_or_django():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    forbidden = {
        "socket",
        "ssl",
        "psycopg",
        "psycopg2",
        "asyncpg",
        "django",
        "subprocess",
        "urllib",
        "http",
        "requests",
        "logging",
    }
    assert not imported & forbidden
    assert "print(" not in SCRIPT.read_text(encoding="utf-8")


def test_cli_entry_point_is_disabled(tmp_path):
    env = {
        "PATH": "/usr/bin:/bin",
        "DATABASE_URL": f"postgresql://kamimusubi_audit_ro.{PROJECT}:{PASSWORD}@{HOST}:5432/db",
    }
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--target", str(tmp_path)],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert proc.returncode == 2
    assert proc.stderr == ""
    lines = proc.stdout.splitlines()
    assert "preflight_stop_reason=production_entry_point_disabled" in lines
    for line in (
        "production_connection=STOP",
        "g6=UNMET",
        "g7=UNMET",
        "ag3_connection_approval=NOT_AUTHORIZED",
        "ag4_preflight_approval=NOT_AUTHORIZED",
    ):
        assert line in lines
    for secret in (PASSWORD, HOST, PROJECT):
        assert secret not in proc.stdout


def test_migration_safety_bridge_is_unchanged_and_still_not_for_preflight():
    """§14.5: the shared bridge keeps exporting no PGSSLROOTCERT and must not be used for this preflight."""
    sys.path.insert(0, str(REPO / "scripts" / "migration_safety"))
    try:
        import guard  # noqa: PLC0415
    finally:
        sys.path.pop(0)
    out = guard.pg_env_exports(
        f"postgresql://u:p@{HOST}:5432/db?sslmode=verify-full&sslrootcert=/x/ca.crt"
    )
    assert "PGSSLMODE" in out and "PGSSLROOTCERT" not in out
