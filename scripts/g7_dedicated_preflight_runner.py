#!/usr/bin/env python3
"""Dedicated preflight runner for the audit role (OFFLINE IMPLEMENTATION ONLY).

Readiness doc: `docs/audit/evidence-coverage-production-readiness-2026-11-01.md` §13, §14 (OP-6, §14.5 – §14.9)
and §15 (this implementation).

Status
------
- **Offline only.** This module contains no database driver, no socket code and no Production connector.
  `run_preflight()` only accepts connectors whose kind is an offline test double or a local disposable database,
  and the command-line entry point prints fixed STOP tokens without reading any environment or file.
- Implementing this runner does **not** authorize AG-3 (connection) or AG-4 (read-only preflight). Every report it
  produces carries `AG3=NOT_AUTHORIZED`, `AG4=NOT_AUTHORIZED`, `PRODUCTION_CONNECTION=STOP`, `G6=UNMET`,
  `G7=UNMET`, even when every PF step is PASS on a test double.

Contract (§14.5, §14.6 `SEQUENTIAL_FAIL_CLOSED`)
-----------------------------------------------
1. PF-0 (G7-A1..A6 result of `scripts/g7_gate1_identity_check.py`) and PF-0b (explicit CA: `sslmode=verify-full`,
   explicit `sslrootcert` file path, not `system`, not implicit, SHA-256 equal to §8.1.1) are evaluated **before**
   any connection is opened.
2. After connecting, the live connection settings are checked (effective `sslmode`, live `sslrootcert` equal to the
   configured value, client `ssl_in_use`, login user = the audit role), still before any SQL.
3. `BEGIN READ ONLY`, then PF-1 … PF-15 one statement at a time from a fixed registry (the §14.7 statements,
   verbatim). Each result is evaluated before the next statement is submitted. Only PASS continues.
4. PF-16 is gated offline on an *accepted independent inventory* (§14.6.1). The acceptance contract is UNRESOLVED,
   so the default policy never accepts one: PF-16 is UNKNOWN, G7-B1 UNMET, and no count SQL is submitted.
5. PF-17 (owner confirmation) is an offline input: explicit and dated, otherwise UNKNOWN.
6. On FAIL, UNKNOWN, a malformed result or any exception: nothing further is submitted, the transaction is rolled
   back when one was opened, the connection is closed, and only fixed tokens are returned.

There is no API that takes SQL. Every submitted statement must be one of the registry objects below and also pass
`validate_statement()` (single statement; SELECT / SHOW, or one of three fixed control statements; no `SET ROLE`,
DML, DDL, GRANT / REVOKE or side-effecting functions).

Redaction (§14.8)
-----------------
Only fixed tokens, booleans, counts, the approved role name and the ten approved table names leave this module.
Never connection strings, passwords, hosts, project references, certificate paths, live user names, exception text,
relation / schema / function names found by PF-5, PF-6, PF-10 or PF-11, or PF-16 row counts. Nothing is logged.
"""

from __future__ import annotations

import hashlib
import hmac
import importlib.util
import inspect
import os
import re
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

PASS, FAIL, UNKNOWN = "PASS", "FAIL", "UNKNOWN"
STATUSES = (PASS, FAIL, UNKNOWN)

AUDIT_ROLE = "kamimusubi_audit_ro"
# `audited_tables()` on the §13 baseline. Must be regenerated on the approved SHA before any approved use (§14.7);
# a test compares this constant with `audited_tables()` on every run.
APPROVED_TABLES = (
    "temples_goriyakutag",
    "temples_shrine",
    "temples_shrine_goriyaku_tags",
    "temples_shrinedeity",
    "temples_shrinedeity_sources",
    "temples_shrinehistory",
    "temples_shrinehistory_sources",
    "temples_shrineknowledgesource",
    "temples_shrinesourcefact",
    "temples_shrinesourcefact_sources",
)
# §8.1.1 File SHA-256 of the provider CA (owner-reported). Comparing bytes is not authenticity evidence.
ACCEPTED_CA_SHA256 = "700723581420dd1ac98fd7e9ac529f0ef210eadcaf87fc868a3ad7d114c2f3b7"
SYSTEM_ROOTCERT = "system"
REQUIRED_SSLMODE = "verify-full"

# Connector kinds this runner will call. There is deliberately no Production kind: adding one needs a separate,
# independently reviewed PR and AG-3 / AG-4 approval (§14.2).
CONNECTOR_KIND_ATTR = "PREFLIGHT_CONNECTOR_KIND"
ACCEPTED_CONNECTOR_KINDS = frozenset({"offline_test_double", "local_disposable"})
# Offline test implementations must originate from these exact checked-in test files.
# This is defence in depth, not a substitute for OS-level network isolation.
TRUSTED_OFFLINE_CONNECTORS = {
    "offline_test_double": (
        Path(__file__).resolve().parent.parent
        / "backend/tests/test_g7_dedicated_preflight_runner.py",
        "FakeConnector",
    ),
    "local_disposable": (
        Path(__file__).resolve().parent.parent
        / "backend/tests/test_g7_dedicated_preflight_runner_db.py",
        "LocalConnector",
    ),
}
INVENTORY_POLICY_KIND_ATTR = "PREFLIGHT_INVENTORY_POLICY_KIND"
ACCEPTED_INVENTORY_POLICY_KINDS = frozenset({"offline_test_double"})

FINAL_STATE = (
    ("runner_mode", "offline_only"),
    ("ag3_connection_approval", "NOT_AUTHORIZED"),
    ("ag4_preflight_approval", "NOT_AUTHORIZED"),
    ("role_creation_execution", "NOT_AUTHORIZED"),
    ("grant_execution", "NOT_AUTHORIZED"),
    ("production_connection", "STOP"),
    ("g6", "UNMET"),
    ("g7", "UNMET"),
)

_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_-]+$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_g7_fields() -> tuple[str, ...]:
    spec = importlib.util.spec_from_file_location(
        "_g7_gate1_identity_check_for_preflight",
        Path(__file__).resolve().parent / "g7_gate1_identity_check.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return tuple(module.FIELDS)


G7_GATE1_FIELDS = _load_g7_fields()


class ProductionConnectionDisabled(Exception):
    """Raised when anything tries to reach a Production connector through this module."""


# --------------------------------------------------------------------------- #
# Statement guard (defence in depth; the registry is the primary control)
# --------------------------------------------------------------------------- #

CONTROL_STATEMENTS = frozenset({"BEGIN READ ONLY", "ROLLBACK", "SET LOCAL row_security = off"})
_STRING_LITERAL = re.compile(r"'(?:[^']|'')*'")
_FORBIDDEN_WORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|UPSERT|ALTER|CREATE|DROP|TRUNCATE|GRANT|REVOKE|COPY|CALL|DO|EXECUTE|PREPARE|"
    r"DEALLOCATE|LOCK|VACUUM|ANALYZE|REFRESH|REINDEX|CLUSTER|COMMENT|IMPORT|LISTEN|NOTIFY|UNLISTEN|DISCARD|LOAD|"
    r"CHECKPOINT|SET|RESET|ROLE|AUTHORIZATION|INTO|BEGIN|COMMIT|ROLLBACK|SAVEPOINT|RELEASE|START|ABORT)\b",
    re.IGNORECASE,
)
_FORBIDDEN_FUNCTIONS = re.compile(
    r"\b(set_config|pg_terminate_backend|pg_cancel_backend|pg_reload_conf|pg_rotate_logfile|pg_promote|"
    r"lo_import|lo_export|lo_unlink|lo_create|lo_from_bytea|pg_read_file|pg_read_binary_file|pg_ls_dir|pg_stat_file|"
    r"dblink\w*|nextval|setval|pg_advisory\w*|pg_try_advisory\w*|pg_switch_wal|pg_create\w*|pg_drop\w*|"
    r"pg_logical\w*|pg_replication\w*|txid_current|pg_current_xact_id|pg_notify|query_to_xml\w*|"
    r"table_to_xml\w*|cursor_to_xml\w*|database_to_xml\w*|schema_to_xml\w*)\s*\(",
    re.IGNORECASE,
)
_FOR_LOCKING = re.compile(r"\bFOR\s+(NO\s+KEY\s+|KEY\s+)?(UPDATE|SHARE)\b", re.IGNORECASE)


def validate_statement(sql: Any) -> tuple[bool, str]:
    """(ok, reason token). Accepts one read-only statement or one of the fixed control statements only."""
    if not isinstance(sql, str) or not sql or sql != sql.strip():
        return False, "statement_not_a_clean_string"
    if sql in CONTROL_STATEMENTS:
        return True, "ok"
    without_literals = _STRING_LITERAL.sub("''", sql)
    if without_literals.count("'") % 2:
        return False, "statement_unbalanced_literal"
    if ";" in without_literals:
        return False, "statement_batch_rejected"
    if "--" in without_literals or "/*" in without_literals or "*/" in without_literals:
        return False, "statement_comment_rejected"
    if "$" in without_literals or '"' in without_literals or "\\" in without_literals:
        return False, "statement_quoting_rejected"
    first = without_literals.split(None, 1)[0].upper()
    if first not in ("SELECT", "SHOW"):
        return False, "statement_verb_rejected"
    if _FORBIDDEN_WORDS.search(without_literals) or _FOR_LOCKING.search(without_literals):
        return False, "statement_forbidden_keyword"
    if _FORBIDDEN_FUNCTIONS.search(without_literals):
        return False, "statement_forbidden_function"
    return True, "ok"


# --------------------------------------------------------------------------- #
# Result contracts
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class QueryResult:
    """What a connector returns for one statement: column names and rows."""

    columns: tuple
    rows: tuple


@dataclass(frozen=True)
class Outcome:
    status: str
    reason: str
    shared: tuple = ()  # ((key, bool | int | token), ...) — redacted values only


class _Malformed(Exception):
    pass


def _is_bool(value: Any) -> bool:
    return type(value) is bool


def _is_count(value: Any) -> bool:
    return type(value) is int and value >= 0


def _rows(result: Any, columns: tuple[str, ...]) -> tuple:
    if not isinstance(result, QueryResult):
        raise _Malformed
    if tuple(result.columns) != columns:
        raise _Malformed
    rows = tuple(result.rows)
    for row in rows:
        if not isinstance(row, tuple) or len(row) != len(columns):
            raise _Malformed
    return rows


def _single(result: Any, columns: tuple[str, ...]) -> tuple | None:
    """The only row, or None when there is no row. More than one row is malformed."""
    rows = _rows(result, columns)
    if not rows:
        return None
    if len(rows) != 1:
        raise _Malformed
    return rows[0]


def _bools(row: tuple) -> bool:
    """True when all values are booleans; False when a value is NULL; malformed otherwise."""
    for value in row:
        if value is None:
            return False
        if not _is_bool(value):
            raise _Malformed
    return True


def _counts(row: tuple) -> None:
    for value in row:
        if not _is_count(value):
            raise _Malformed


def _eval_pf1(result):
    cols = ("role_is_audit_role", "login_role_is_session_role", "txn_read_only")
    row = _single(result, cols)
    if row is None:
        return Outcome(UNKNOWN, "no_row")
    role_ok, session_ok, read_only = row
    if role_ok is None or session_ok is None or read_only is None:
        return Outcome(UNKNOWN, "null_value")
    if not _is_bool(role_ok) or not _is_bool(session_ok) or not isinstance(read_only, str):
        raise _Malformed
    shared = (
        ("role_is_audit_role", role_ok),
        ("login_role_is_session_role", session_ok),
        ("txn_read_only_on", read_only == "on"),
    )
    if read_only not in ("on", "off"):
        raise _Malformed
    if role_ok and session_ok and read_only == "on":
        return Outcome(PASS, "ok", shared)
    return Outcome(FAIL, "session_identity_mismatch", shared)


def _eval_pf2(result):
    cols = (
        "rolsuper",
        "rolcreatedb",
        "rolcreaterole",
        "rolreplication",
        "rolbypassrls",
        "rolinherit",
        "rolcanlogin",
        "connlimit_is_1",
        "valid_until_future",
    )
    row = _single(result, cols)
    if row is None:
        return Outcome(UNKNOWN, "no_row")
    if not _bools(row):
        return Outcome(UNKNOWN, "null_value")
    shared = tuple(zip(cols, row, strict=True))
    values = dict(shared)
    must_be_false = cols[:6]
    must_be_true = cols[6:]
    if all(values[c] is False for c in must_be_false) and all(
        values[c] is True for c in must_be_true
    ):
        return Outcome(PASS, "ok", shared)
    return Outcome(FAIL, "role_attributes_mismatch", shared)


def _count_eq_zero(column: str, positive_status: str, reason: str):
    def evaluate(result):
        row = _single(result, (column,))
        if row is None:
            return Outcome(UNKNOWN, "no_row")
        _counts(row)
        shared = ((column, row[0]),)
        if row[0] == 0:
            return Outcome(PASS, "ok", shared)
        return Outcome(positive_status, reason, shared)

    return evaluate


def _eval_pf4a(result):
    cols = ("db_connect", "db_create", "db_temp_effective")
    row = _single(result, cols)
    if row is None:
        return Outcome(UNKNOWN, "no_row")
    if not _bools(row):
        return Outcome(UNKNOWN, "null_value")
    connect, create, temp = row
    shared = tuple(zip(cols, row, strict=True))
    if connect is True and create is False:
        # db_temp_effective may be true only through PUBLIC; PF-4b decides (explicit grants must be 0).
        return Outcome(PASS, "ok", shared)
    return Outcome(FAIL, "database_privileges_mismatch", shared)


def _eval_pf5a(result):
    cols = ("public_usage", "public_create")
    row = _single(result, cols)
    if row is None:
        return Outcome(UNKNOWN, "no_row")
    if not _bools(row):
        return Outcome(UNKNOWN, "null_value")
    shared = tuple(zip(cols, row, strict=True))
    if row == (True, False):
        return Outcome(PASS, "ok", shared)
    return Outcome(FAIL, "schema_privileges_mismatch", shared)


def _eval_pf6(result):
    cols = ("audited_readable", "other_readable")
    row = _single(result, cols)
    if row is None:
        return Outcome(UNKNOWN, "no_row")
    _counts(row)
    audited, other = row
    if audited > len(APPROVED_TABLES):
        raise _Malformed
    shared = tuple(zip(cols, row, strict=True))
    if audited < len(APPROVED_TABLES):
        return Outcome(FAIL, "audited_tables_not_readable", shared)
    if other > 0:
        return Outcome(UNKNOWN, "unexplained_readable_relations", shared)
    return Outcome(PASS, "ok", shared)


def _eval_pf9(result):
    cols = ("owned_relations", "owned_schemas", "owned_functions")
    row = _single(result, cols)
    if row is None:
        return Outcome(UNKNOWN, "no_row")
    _counts(row)
    shared = tuple(zip(cols, row, strict=True))
    if row == (0, 0, 0):
        return Outcome(PASS, "ok", shared)
    return Outcome(FAIL, "role_owns_objects", shared)


def _eval_pf11(result):
    cols = ("default_acl_to_public", "default_acl_to_role")
    row = _single(result, cols)
    if row is None:
        return Outcome(UNKNOWN, "no_row")
    _counts(row)
    to_public, to_role = row
    shared = tuple(zip(cols, row, strict=True))
    if to_role > 0:
        return Outcome(FAIL, "default_acl_to_role", shared)
    if to_public > 0:
        return Outcome(UNKNOWN, "unexplained_default_acl_to_public", shared)
    return Outcome(PASS, "ok", shared)


def _eval_pf12(result):
    cols = ("name", "present", "can_select", "rls_enabled", "rls_forced")
    rows = _rows(result, cols)
    if not rows:
        return Outcome(UNKNOWN, "no_row")
    # ORDER BY follows the database collation, which may differ from Python ordering.
    # Require exactly the approved names once each, independent of row order.
    names = tuple(row[0] for row in rows)
    if (
        len(rows) != len(APPROVED_TABLES)
        or len(set(names)) != len(APPROVED_TABLES)
        or set(names) != set(APPROVED_TABLES)
    ):
        raise _Malformed
    rows_by_name = {row[0]: row for row in rows}
    missing = rls = null = False
    shared = []
    for name, present, can_select, rls_enabled, rls_forced in (rows_by_name[t] for t in APPROVED_TABLES):
        for value in (present, can_select):
            if not _is_bool(value):
                raise _Malformed
        for value in (rls_enabled, rls_forced):
            if value is not None and not _is_bool(value):
                raise _Malformed
        shared.append((f"{name}.present", present))
        shared.append((f"{name}.can_select", can_select))
        if not present or not can_select:
            missing = True
            continue
        if rls_enabled is None or rls_forced is None:
            null = True
            continue
        shared.append((f"{name}.rls_enabled", rls_enabled))
        shared.append((f"{name}.rls_forced", rls_forced))
        if rls_enabled or rls_forced:
            rls = True
    if missing:
        return Outcome(FAIL, "audited_table_missing_or_not_selectable", tuple(shared))
    if rls:
        return Outcome(FAIL, "rls_enabled_stop", tuple(shared))
    if null:
        return Outcome(UNKNOWN, "null_value", tuple(shared))
    return Outcome(PASS, "ok", tuple(shared))


def _eval_pf13(result):
    cols = ("legacy_present", "legacy_readable")
    row = _single(result, cols)
    if row is None:
        return Outcome(UNKNOWN, "no_row")
    if not _bools(row):
        return Outcome(UNKNOWN, "null_value")
    shared = tuple(zip(cols, row, strict=True))
    if row[1] is False:
        return Outcome(PASS, "ok", shared)
    return Outcome(FAIL, "legacy_relation_readable", shared)


def _eval_pf14a(result):
    cols = (
        "pg_roles",
        "pg_class",
        "pg_type",
        "pg_stat_ssl",
        "fn_has_table_privilege",
        "fn_to_regclass",
        "fn_unnest",
        "fn_pg_backend_pid",
    )
    row = _single(result, cols)
    if row is None:
        return Outcome(UNKNOWN, "no_row")
    if not _bools(row):
        return Outcome(UNKNOWN, "null_value")
    shared = tuple(zip(cols, row, strict=True))
    if all(row):
        return Outcome(PASS, "ok", shared)
    return Outcome(FAIL, "catalog_visibility_missing", shared)


def _eval_pf14b(result):
    cols = ("own_pg_stat_ssl_rows", "own_ssl")
    row = _single(result, cols)
    if row is None:
        raise _Malformed  # an aggregate always returns one row
    rows_seen, own_ssl = row
    if not _is_count(rows_seen):
        raise _Malformed
    if rows_seen == 0:
        if own_ssl is not None:
            raise _Malformed
        return Outcome(UNKNOWN, "own_pg_stat_ssl_row_absent", (("own_pg_stat_ssl_rows", 0),))
    if rows_seen != 1 or not _is_bool(own_ssl):
        return Outcome(UNKNOWN, "own_pg_stat_ssl_ambiguous", (("own_pg_stat_ssl_rows", rows_seen),))
    shared = (("own_pg_stat_ssl_rows", 1), ("own_ssl", own_ssl))
    if own_ssl:
        return Outcome(PASS, "ok", shared)
    return Outcome(FAIL, "own_ssl_false", shared)


def _eval_pf15a(result):
    row = _single(result, ("default_transaction_read_only",))
    if row is None:
        return Outcome(UNKNOWN, "no_row")
    if not isinstance(row[0], str):
        raise _Malformed
    shared = (("default_transaction_read_only_on", row[0] == "on"),)
    if row[0] == "on":
        return Outcome(PASS, "ok", shared)
    if row[0] == "off":
        return Outcome(FAIL, "default_transaction_read_only_off", shared)
    raise _Malformed


def _eval_bool_true(column: str, reason: str):
    def evaluate(result):
        row = _single(result, (column,))
        if row is None:
            return Outcome(UNKNOWN, "no_row")
        if row[0] is None:
            return Outcome(UNKNOWN, "null_value")
        if not _is_bool(row[0]):
            raise _Malformed
        shared = ((column, row[0]),)
        return Outcome(PASS, "ok", shared) if row[0] else Outcome(FAIL, reason, shared)

    return evaluate


def _eval_control(result):
    # BEGIN READ ONLY / SET LOCAL: a successful submission with no result set.
    if not isinstance(result, QueryResult) or tuple(result.columns) or tuple(result.rows):
        raise _Malformed
    return Outcome(PASS, "ok")


def _eval_not_standalone(result):  # noqa: ARG001
    # PF-16 count rows are compared inside `_run_pf16` only; any other use fails closed.
    raise _Malformed


def _eval_row_security(result):
    row = _single(result, ("row_security",))
    if row is None or not isinstance(row[0], str):
        raise _Malformed
    if row[0] == "off":
        return Outcome(PASS, "ok", (("row_security_off", True),))
    return Outcome(FAIL, "row_security_not_off", (("row_security_off", False),))


# --------------------------------------------------------------------------- #
# Registry: the §14.7 statements, verbatim, in order. Nothing else is ever submitted.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Statement:
    step: str  # PF id the statement belongs to
    sub: str  # sub-step id (one statement each)
    sql: str
    evaluate: Callable[[Any], Outcome] = field(compare=False, repr=False)


_TABLE_ARRAY = "ARRAY[" + ", ".join(f"'{t}'" for t in APPROVED_TABLES) + "]"

BEGIN_STATEMENT = Statement("TXN", "begin", "BEGIN READ ONLY", _eval_control)

PF_STATEMENTS = (
    Statement(
        "PF-1",
        "PF-1",
        "SELECT current_user = 'kamimusubi_audit_ro' AS role_is_audit_role, current_user = session_user AS "
        "login_role_is_session_role, current_setting('transaction_read_only') AS txn_read_only",
        _eval_pf1,
    ),
    Statement(
        "PF-2",
        "PF-2",
        "SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls, rolinherit, rolcanlogin, "
        "rolconnlimit = 1 AS connlimit_is_1, (rolvaliduntil IS NOT NULL AND rolvaliduntil > now()) AS "
        "valid_until_future FROM pg_roles WHERE rolname = current_user",
        _eval_pf2,
    ),
    Statement(
        "PF-3",
        "PF-3",
        "SELECT count(*) AS member_of_count FROM pg_auth_members WHERE member = (SELECT oid FROM pg_roles WHERE "
        "rolname = current_user)",
        _count_eq_zero("member_of_count", FAIL, "role_has_memberships"),
    ),
    Statement(
        "PF-4",
        "PF-4a",
        "SELECT has_database_privilege(current_database(), 'CONNECT') AS db_connect, "
        "has_database_privilege(current_database(), 'CREATE') AS db_create, "
        "has_database_privilege(current_database(), 'TEMP') AS db_temp_effective",
        _eval_pf4a,
    ),
    Statement(
        "PF-4",
        "PF-4b",
        "SELECT count(*) AS explicit_db_create_or_temp_for_role FROM pg_database d, aclexplode(d.datacl) a WHERE "
        "d.datname = current_database() AND a.grantee = (SELECT oid FROM pg_roles WHERE rolname = current_user) "
        "AND a.privilege_type IN ('CREATE', 'TEMPORARY')",
        _count_eq_zero(
            "explicit_db_create_or_temp_for_role", FAIL, "explicit_db_create_or_temp_grant"
        ),
    ),
    Statement(
        "PF-5",
        "PF-5a",
        "SELECT has_schema_privilege('public', 'USAGE') AS public_usage, has_schema_privilege('public', 'CREATE') "
        "AS public_create",
        _eval_pf5a,
    ),
    Statement(
        "PF-5",
        "PF-5b",
        "SELECT count(*) AS other_schemas_with_usage FROM pg_namespace n WHERE n.nspname NOT IN ('pg_catalog', "
        "'information_schema', 'public') AND n.nspname NOT LIKE 'pg\\_toast%' AND n.nspname NOT LIKE "
        "'pg\\_temp\\_%' AND has_schema_privilege(n.oid, 'USAGE')",
        _count_eq_zero("other_schemas_with_usage", UNKNOWN, "unexplained_schema_usage"),
    ),
    Statement(
        "PF-5",
        "PF-5c",
        "SELECT count(*) AS schemas_with_create FROM pg_namespace n WHERE n.nspname NOT LIKE 'pg\\_temp\\_%' AND "
        "n.nspname NOT LIKE 'pg\\_toast\\_temp\\_%' AND has_schema_privilege(n.oid, 'CREATE')",
        _count_eq_zero("schemas_with_create", FAIL, "schema_create_privilege"),
    ),
    Statement(
        "PF-6",
        "PF-6",
        "SELECT count(*) FILTER (WHERE in_set) AS audited_readable, count(*) FILTER (WHERE NOT in_set) AS "
        "other_readable FROM (SELECT (n.nspname = 'public' AND c.relname = ANY ("
        + _TABLE_ARRAY
        + ")) AS in_set "
        "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname NOT IN ('pg_catalog', "
        "'information_schema') AND n.nspname NOT LIKE 'pg\\_toast%' AND c.relkind IN ('r', 'p', 'v', 'm', 'f') "
        "AND (has_table_privilege(c.oid, 'SELECT') OR has_any_column_privilege(c.oid, 'SELECT'))) s",
        _eval_pf6,
    ),
    Statement(
        "PF-7",
        "PF-7",
        "SELECT count(*) AS write_class_relations FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname NOT LIKE 'pg\\_toast%' AND "
        "c.relkind IN ('r', 'p', 'v', 'm', 'f') AND (has_table_privilege(c.oid, "
        "'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') OR has_any_column_privilege(c.oid, "
        "'INSERT,UPDATE,REFERENCES'))",
        _count_eq_zero("write_class_relations", FAIL, "write_class_privilege"),
    ),
    Statement(
        "PF-8",
        "PF-8",
        "SELECT count(*) AS usable_sequences FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE "
        "c.relkind = 'S' AND n.nspname NOT IN ('pg_catalog', 'information_schema') AND CASE WHEN c.relkind = 'S' "
        "THEN has_sequence_privilege(c.oid, 'USAGE,SELECT,UPDATE') ELSE false END",
        _count_eq_zero("usable_sequences", FAIL, "usable_sequences"),
    ),
    Statement(
        "PF-9",
        "PF-9",
        "SELECT (SELECT count(*) FROM pg_class WHERE relowner = r.oid) AS owned_relations, (SELECT count(*) FROM "
        "pg_namespace WHERE nspowner = r.oid) AS owned_schemas, (SELECT count(*) FROM pg_proc WHERE proowner = "
        "r.oid) AS owned_functions FROM pg_roles r WHERE r.rolname = current_user",
        _eval_pf9,
    ),
    Statement(
        "PF-10",
        "PF-10",
        "SELECT count(*) AS executable_security_definer FROM pg_proc p JOIN pg_namespace n ON n.oid = "
        "p.pronamespace WHERE p.prosecdef AND n.nspname NOT IN ('pg_catalog', 'information_schema') AND "
        "has_schema_privilege(n.oid, 'USAGE') AND has_function_privilege(p.oid, 'EXECUTE')",
        # "0, or each one explained and approved": this runner has no approval input, so > 0 stays UNKNOWN.
        _count_eq_zero("executable_security_definer", UNKNOWN, "unexplained_security_definer"),
    ),
    Statement(
        "PF-11",
        "PF-11",
        "SELECT count(*) FILTER (WHERE a.grantee = 0) AS default_acl_to_public, count(*) FILTER (WHERE a.grantee "
        "= (SELECT oid FROM pg_roles WHERE rolname = current_user)) AS default_acl_to_role FROM pg_default_acl d, "
        "aclexplode(d.defaclacl) a",
        _eval_pf11,
    ),
    Statement(
        "PF-12",
        "PF-12",
        "SELECT t.name, c.oid IS NOT NULL AS present, coalesce(has_table_privilege(c.oid, 'SELECT'), false) AS "
        "can_select, c.relrowsecurity AS rls_enabled, c.relforcerowsecurity AS rls_forced FROM unnest("
        + _TABLE_ARRAY
        + "::text[]) AS t(name) LEFT JOIN pg_class c ON c.oid = to_regclass('public.' || t.name) ORDER BY t.name",
        _eval_pf12,
    ),
    Statement(
        "PF-13",
        "PF-13",
        "SELECT to_regclass('public.temples_shrine_deities') IS NOT NULL AS legacy_present, "
        "coalesce(has_table_privilege(to_regclass('public.temples_shrine_deities'), 'SELECT'), false) AS "
        "legacy_readable",
        _eval_pf13,
    ),
    Statement(
        "PF-14",
        "PF-14a",
        "SELECT has_table_privilege('pg_catalog.pg_roles', 'SELECT') AS pg_roles, "
        "has_table_privilege('pg_catalog.pg_class', 'SELECT') AS pg_class, "
        "has_table_privilege('pg_catalog.pg_type', 'SELECT') AS pg_type, "
        "has_table_privilege('pg_catalog.pg_stat_ssl', 'SELECT') AS pg_stat_ssl, "
        "has_function_privilege('pg_catalog.has_table_privilege(name, text, text)', 'EXECUTE') AS "
        "fn_has_table_privilege, has_function_privilege('pg_catalog.to_regclass(text)', 'EXECUTE') AS "
        "fn_to_regclass, has_function_privilege('pg_catalog.unnest(anyarray)', 'EXECUTE') AS fn_unnest, "
        "has_function_privilege('pg_catalog.pg_backend_pid()', 'EXECUTE') AS fn_pg_backend_pid",
        _eval_pf14a,
    ),
    Statement(
        "PF-14",
        "PF-14b",
        "SELECT count(*) AS own_pg_stat_ssl_rows, bool_and(ssl) AS own_ssl FROM pg_stat_ssl WHERE pid = "
        "pg_backend_pid()",
        _eval_pf14b,
    ),
    Statement("PF-15", "PF-15a", "SHOW default_transaction_read_only", _eval_pf15a),
    Statement(
        "PF-15",
        "PF-15b",
        "SELECT current_setting('statement_timeout') <> '0' AS statement_timeout_set",
        _eval_bool_true("statement_timeout_set", "statement_timeout_not_set"),
    ),
)

PF16_ROW_SECURITY_OFF = Statement(
    "PF-16", "PF-16.row_security", "SET LOCAL row_security = off", _eval_control
)
PF16_SHOW_ROW_SECURITY = Statement(
    "PF-16", "PF-16.show_row_security", "SHOW row_security", _eval_row_security
)
# §14.7: `SELECT '<table>' AS t, count(*) FROM public.<table>` — one per audited table, compared privately.
PF16_COUNT_STATEMENTS = tuple(
    Statement(
        "PF-16",
        f"PF-16.{table}",
        f"SELECT '{table}' AS t, count(*) FROM public.{table}",
        _eval_not_standalone,
    )
    for table in APPROVED_TABLES
)

REGISTRY = (
    BEGIN_STATEMENT,
    *PF_STATEMENTS,
    PF16_ROW_SECURITY_OFF,
    PF16_SHOW_ROW_SECURITY,
    *PF16_COUNT_STATEMENTS,
)
for _stmt in REGISTRY:  # fail at import if the registry itself would be refused
    if validate_statement(_stmt.sql) != (True, "ok"):
        raise RuntimeError("preflight registry contains a statement the guard refuses")
del _stmt

STEP_ORDER = ("PF-0", "PF-0b", *dict.fromkeys(s.step for s in PF_STATEMENTS), "PF-16", "PF-17")


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class OwnerConfirmation:
    """PF-17 / G7-B2: the owner's explicit, dated confirmation that the matched target is the intended one."""

    confirmed: bool
    confirmed_on: date | None


@dataclass(frozen=True)
class ConnectParams:
    """The only values handed to a connector: the validated TLS settings. No host, user or password."""

    sslmode: str
    sslrootcert: str


@dataclass(frozen=True)
class PreflightConfig:
    sslmode: str | None
    sslrootcert: str | None
    g7_gate1_result: Mapping[str, str] | None
    expected_ca_sha256: str = ACCEPTED_CA_SHA256
    pf16_inventory: Mapping[str, int] | None = None
    pf17_owner_confirmation: OwnerConfirmation | None = None
    environ: Mapping[str, str] | None = (
        None  # PG* variables to check for implicit / conflicting TLS settings
    )


def _trusted_offline_connector(connector: Any) -> bool:
    """Accept only the concrete checked-in test connector classes, never a claimed kind alone.

    Code inside this process is trusted; hard network isolation belongs to the test sandbox.
    """
    kind = getattr(connector, CONNECTOR_KIND_ATTR, None)
    if kind not in TRUSTED_OFFLINE_CONNECTORS:
        return False
    expected_path, expected_name = TRUSTED_OFFLINE_CONNECTORS[kind]
    cls = type(connector)
    if cls.__name__ != expected_name or CONNECTOR_KIND_ATTR not in cls.__dict__:
        return False
    try:
        class_path = Path(inspect.getfile(cls)).resolve(strict=True)
        method_path = Path(inspect.getfile(cls.connect)).resolve(strict=True)
        return class_path == expected_path.resolve(strict=True) and method_path == class_path
    except (OSError, TypeError, ValueError):
        return False


class UnresolvedInventoryAcceptance:
    """Default PF-16 policy. §14.6.1: the inventory source, capture time and verification are UNRESOLVED, so no
    inventory can be accepted. PF-16 is UNKNOWN, G7-B1 UNMET, and no count query is submitted."""

    PREFLIGHT_INVENTORY_POLICY_KIND = "unresolved"

    def accept(self, inventory: Mapping[str, int]) -> bool:  # noqa: ARG002
        return False


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #


@dataclass
class StepResult:
    step: str
    status: str
    reason: str
    shared: tuple = ()


@dataclass
class PreflightReport:
    steps: list = field(default_factory=list)
    stopped_at: str | None = None
    stop_reason: str | None = None
    connected: bool = False
    transaction_opened: bool = False
    rollback: str = "not_needed"
    close: str = "not_needed"
    statements_submitted: int = 0

    @property
    def all_pass(self) -> bool:
        return (
            self.stopped_at is None
            and [s.step for s in self.steps] == list(STEP_ORDER)
            and all(s.status == PASS for s in self.steps)
            and self.connected
            and self.transaction_opened
            and self.rollback == "done"
            and self.close == "done"
        )

    def render(self) -> str:
        lines = []
        for step in self.steps:
            lines.append(f"preflight_{step.step}={step.status}")
            if step.reason != "ok":
                lines.append(f"preflight_{step.step}_reason={step.reason}")
            for key, value in step.shared:
                lines.append(f"preflight_{step.step}.{key}={_token(value)}")
        lines.append(f"preflight_overall={'ALL_PASS_OFFLINE' if self.all_pass else 'STOP'}")
        if self.stopped_at:
            lines.append(f"preflight_stopped_at={self.stopped_at}")
            lines.append(f"preflight_stop_reason={self.stop_reason}")
        lines.append(f"preflight_transaction_rollback={self.rollback}")
        lines.append(f"preflight_connection_close={self.close}")
        # A PF-16 / PF-17 PASS here is never G7-B1 / G7-B2 evidence (§14.6: G-7 needs the recorded, approved run).
        lines.append("preflight_g7_b1=UNMET")
        lines.append("preflight_g7_b2=UNMET")
        lines.extend(f"{key}={value}" for key, value in FINAL_STATE)
        return "\n".join(lines)


def _token(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if type(value) is int:
        return str(value)
    if isinstance(value, str) and _SAFE_TOKEN.match(value):
        return value
    return "redacted"


# --------------------------------------------------------------------------- #
# Offline prerequisites
# --------------------------------------------------------------------------- #


def evaluate_pf0(result: Mapping[str, str] | None) -> Outcome:
    """PF-0: the G7-A1..A6 output of `g7_gate1_identity_check.evaluate()`; every field must be PASS."""
    if result is None:
        return Outcome(UNKNOWN, "g7_gate1_result_missing")
    if not isinstance(result, Mapping) or set(result) != set(G7_GATE1_FIELDS):
        return Outcome(UNKNOWN, "g7_gate1_result_malformed")
    values = [result[f] for f in G7_GATE1_FIELDS]
    if any(v not in STATUSES for v in values):
        return Outcome(UNKNOWN, "g7_gate1_result_malformed")
    shared = tuple((f, result[f]) for f in G7_GATE1_FIELDS)
    if all(v == PASS for v in values):
        return Outcome(PASS, "ok", shared)
    if any(v == FAIL for v in values):
        return Outcome(FAIL, "g7_gate1_not_all_pass", shared)
    return Outcome(UNKNOWN, "g7_gate1_not_all_pass", shared)


def evaluate_pf0b(config: PreflightConfig) -> Outcome:
    """PF-0b: OP-5 (explicit verify-full CA configuration) and OP-4 (CA SHA-256), before any connection."""
    environ = config.environ if config.environ is not None else os.environ
    env_mode = environ.get("PGSSLMODE")
    env_root = environ.get("PGSSLROOTCERT")
    if config.sslmode != REQUIRED_SSLMODE:
        return Outcome(FAIL, "configured_sslmode_not_verify_full", (("op5_explicit_ca", False),))
    root = config.sslrootcert
    if root is None or not isinstance(root, str) or not root.strip():
        reason = "sslrootcert_implicit" if env_root else "sslrootcert_not_explicit"
        return Outcome(FAIL, reason, (("op5_explicit_ca", False),))
    if root.strip().lower() == SYSTEM_ROOTCERT:
        return Outcome(FAIL, "sslrootcert_system_not_accepted", (("op5_explicit_ca", False),))
    if root != root.strip():
        return Outcome(FAIL, "sslrootcert_invalid", (("op5_explicit_ca", False),))
    if (env_mode is not None and env_mode != REQUIRED_SSLMODE) or (
        env_root is not None and env_root != root
    ):
        return Outcome(FAIL, "tls_environment_conflict", (("op5_explicit_ca", False),))
    path = Path(root)
    if not path.is_absolute():
        return Outcome(FAIL, "sslrootcert_not_absolute_path", (("op5_explicit_ca", False),))
    try:
        real = path.resolve(strict=True)
        if not real.is_file():
            return Outcome(FAIL, "ca_file_invalid", (("op5_explicit_ca", False),))
        if real == _REPO_ROOT or _REPO_ROOT in real.parents:
            return Outcome(FAIL, "ca_file_inside_repository", (("op5_explicit_ca", False),))
        data = real.read_bytes()
    except (OSError, RuntimeError, ValueError):
        return Outcome(FAIL, "ca_file_invalid", (("op5_explicit_ca", False),))
    if b"-----BEGIN CERTIFICATE-----" not in data or b"-----END CERTIFICATE-----" not in data:
        return Outcome(FAIL, "ca_file_invalid", (("op5_explicit_ca", False),))
    expected = config.expected_ca_sha256
    if not isinstance(expected, str) or not _HEX64.match(expected):
        return Outcome(UNKNOWN, "ca_expected_sha256_invalid", (("op5_explicit_ca", True),))
    digest = hashlib.sha256(data).hexdigest()
    if not hmac.compare_digest(digest, expected):
        return Outcome(
            FAIL, "ca_sha256_mismatch", (("op5_explicit_ca", True), ("op4_ca_sha256_match", False))
        )
    return Outcome(PASS, "ok", (("op5_explicit_ca", True), ("op4_ca_sha256_match", True)))


def evaluate_live_settings(settings: Any, configured_rootcert: str) -> Outcome:
    """§14.5: after connecting and before any SQL, the effective connection must match the validated config.

    `settings` comes from the connector's `live_settings()`: {"sslmode", "sslrootcert", "ssl_in_use", "user"}.
    Values are compared and never returned.
    """
    if not isinstance(settings, Mapping) or set(settings) != {
        "sslmode",
        "sslrootcert",
        "ssl_in_use",
        "user",
    }:
        return Outcome(UNKNOWN, "live_settings_unavailable")
    mode, root, in_use, user = (
        settings[k] for k in ("sslmode", "sslrootcert", "ssl_in_use", "user")
    )
    if not isinstance(mode, str) or not _is_bool(in_use) or not isinstance(user, str):
        return Outcome(UNKNOWN, "live_settings_unavailable")
    if root is not None and not isinstance(root, str):
        return Outcome(UNKNOWN, "live_settings_unavailable")
    if mode != REQUIRED_SSLMODE:
        return Outcome(FAIL, "live_sslmode_not_verify_full")
    if not root:
        return Outcome(FAIL, "live_sslrootcert_not_configured")
    if root.strip().lower() == SYSTEM_ROOTCERT:
        return Outcome(FAIL, "live_sslrootcert_system")
    if not hmac.compare_digest(root.encode("utf-8"), configured_rootcert.encode("utf-8")):
        return Outcome(FAIL, "live_sslrootcert_mismatch")
    if in_use is not True:
        return Outcome(FAIL, "live_ssl_not_in_use")
    role, dot, suffix = user.partition(".")
    if not hmac.compare_digest(role.encode("utf-8"), AUDIT_ROLE.encode("utf-8")):
        return Outcome(FAIL, "login_role_mismatch")
    if dot and (not suffix or not _SAFE_TOKEN.match(suffix)):
        return Outcome(FAIL, "login_role_mismatch")
    return Outcome(
        PASS,
        "ok",
        (("live_verify_full", True), ("live_explicit_ca", True), ("login_role_ok", True)),
    )


def evaluate_pf17(confirmation: OwnerConfirmation | None) -> Outcome:
    if confirmation is None:
        return Outcome(UNKNOWN, "owner_confirmation_absent")
    if not isinstance(confirmation, OwnerConfirmation):
        return Outcome(UNKNOWN, "owner_confirmation_malformed")
    if confirmation.confirmed is not True or not isinstance(confirmation.confirmed_on, date):
        return Outcome(UNKNOWN, "owner_confirmation_not_explicit_and_dated")
    if confirmation.confirmed_on > date.today():
        return Outcome(UNKNOWN, "owner_confirmation_date_in_future")
    return Outcome(
        PASS,
        "ok",
        (("owner_confirmed", True), ("confirmed_on", confirmation.confirmed_on.isoformat())),
    )


def _inventory_gate(inventory: Any, policy: Any) -> Outcome:
    """PF-16 offline gate: missing or unaccepted independent evidence is UNKNOWN before any count SQL."""
    if inventory is None:
        return Outcome(UNKNOWN, "independent_inventory_missing")
    if (
        not isinstance(inventory, Mapping)
        or set(inventory) != set(APPROVED_TABLES)
        or not all(_is_count(v) for v in inventory.values())
    ):
        return Outcome(UNKNOWN, "independent_inventory_malformed")
    if getattr(policy, INVENTORY_POLICY_KIND_ATTR, None) not in ACCEPTED_INVENTORY_POLICY_KINDS:
        return Outcome(UNKNOWN, "independent_inventory_contract_unresolved")
    try:
        accepted = policy.accept(inventory) is True
    except Exception:  # noqa: BLE001
        accepted = False
    if not accepted:
        return Outcome(UNKNOWN, "independent_inventory_not_accepted")
    return Outcome(PASS, "ok")


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #


class _Stop(Exception):
    def __init__(self, step: str, status: str, reason: str):
        super().__init__(reason)
        self.step, self.status, self.reason = step, status, reason


class _GuardedSession:
    """The only path to the connection. Accepts registry statements only, one at a time."""

    def __init__(self, conn: Any, report: PreflightReport):
        self._conn = conn
        self._report = report

    def submit(self, stmt: Statement) -> Any:
        if not any(stmt is registered for registered in REGISTRY):
            raise _Stop(
                stmt.step if isinstance(stmt, Statement) else "?",
                UNKNOWN,
                "statement_not_in_registry",
            )
        ok, reason = validate_statement(stmt.sql)
        if not ok:
            raise _Stop(stmt.step, UNKNOWN, reason)
        if stmt is BEGIN_STATEMENT:
            self._report.transaction_opened = True  # roll back even if BEGIN itself raises
        self._report.statements_submitted += 1
        try:
            return self._conn.execute(stmt.sql)
        except Exception:  # noqa: BLE001 - driver text is never kept
            raise _Stop(stmt.step, UNKNOWN, "execution_error") from None


def _evaluate(stmt: Statement, result: Any) -> Outcome:
    try:
        outcome = stmt.evaluate(result)
    except _Malformed:
        return Outcome(UNKNOWN, "malformed_result")
    except Exception:  # noqa: BLE001
        return Outcome(UNKNOWN, "evaluation_error")
    if not isinstance(outcome, Outcome) or outcome.status not in STATUSES:
        return Outcome(UNKNOWN, "evaluation_error")
    return outcome


def _record(report: PreflightReport, step: str, outcome: Outcome) -> None:
    """Merge a sub-step outcome into the step's single result row and stop on anything but PASS."""
    if report.steps and report.steps[-1].step == step:
        current = report.steps[-1]
        current.shared = current.shared + outcome.shared
        current.status, current.reason = outcome.status, outcome.reason
    else:
        report.steps.append(StepResult(step, outcome.status, outcome.reason, outcome.shared))
    if outcome.status != PASS:
        raise _Stop(step, outcome.status, outcome.reason)


def _run_pf16(
    session: _GuardedSession, report: PreflightReport, config: PreflightConfig, policy: Any
) -> None:
    gate = _inventory_gate(config.pf16_inventory, policy)
    if gate.status != PASS:
        _record(report, "PF-16", gate)  # STOP: no count SQL is submitted
    _record(
        report, "PF-16", _evaluate(PF16_ROW_SECURITY_OFF, session.submit(PF16_ROW_SECURITY_OFF))
    )
    _record(
        report, "PF-16", _evaluate(PF16_SHOW_ROW_SECURITY, session.submit(PF16_SHOW_ROW_SECURITY))
    )
    inventory = config.pf16_inventory
    for table, stmt in zip(APPROVED_TABLES, PF16_COUNT_STATEMENTS, strict=True):
        result = session.submit(stmt)
        try:
            row = _single(result, ("t", "count"))
            if row is None or row[0] != table or not _is_count(row[1]):
                raise _Malformed
        except _Malformed:
            _record(report, "PF-16", Outcome(UNKNOWN, "malformed_result"))
        matched = hmac.compare_digest(str(row[1]).encode(), str(inventory[table]).encode())
        if not matched:
            _record(report, "PF-16", Outcome(FAIL, "count_mismatch", ((f"{table}.match", False),)))
        _record(report, "PF-16", Outcome(PASS, "ok", ((f"{table}.match", True),)))


def run_preflight(
    config: PreflightConfig,
    connector: Any = None,
    inventory_policy: Any = None,
) -> PreflightReport:
    """Run PF-0 … PF-17 under SEQUENTIAL_FAIL_CLOSED. Never raises for FAIL / UNKNOWN; returns a redacted report.

    `connector` must expose `PREFLIGHT_CONNECTOR_KIND` in ACCEPTED_CONNECTOR_KINDS and `connect(ConnectParams)`,
    returning an object with `live_settings()`, `execute(sql) -> QueryResult`, `rollback()` and `close()`.
    The default (None) is the disabled Production path: STOP before connecting.
    """
    report = PreflightReport()
    policy = inventory_policy if inventory_policy is not None else UnresolvedInventoryAcceptance()
    conn = None
    try:
        _record(report, "PF-0", evaluate_pf0(config.g7_gate1_result))
        _record(report, "PF-0b", evaluate_pf0b(config))
        if connector is None:
            raise _Stop("CONNECT", UNKNOWN, "production_connection_disabled")
        if not _trusted_offline_connector(connector):
            raise _Stop("CONNECT", UNKNOWN, "connector_not_authorized")
        try:
            conn = connector.connect(
                ConnectParams(sslmode=config.sslmode, sslrootcert=config.sslrootcert)
            )
        except Exception:  # noqa: BLE001 - never echo host, user, certificate path or driver text
            raise _Stop("CONNECT", UNKNOWN, "connection_failed") from None
        if conn is None:
            raise _Stop("CONNECT", UNKNOWN, "connection_failed")
        report.connected = True
        try:
            live = conn.live_settings()
        except Exception:  # noqa: BLE001
            live = None
        outcome = evaluate_live_settings(live, config.sslrootcert)
        if outcome.status != PASS:
            raise _Stop("LIVE", outcome.status, outcome.reason)

        session = _GuardedSession(conn, report)
        begin = _evaluate(BEGIN_STATEMENT, session.submit(BEGIN_STATEMENT))
        if begin.status != PASS:
            raise _Stop("TXN", begin.status, begin.reason)
        for stmt in PF_STATEMENTS:
            result = session.submit(stmt)
            _record(report, stmt.step, _evaluate(stmt, result))
        _run_pf16(session, report, config, policy)
        _record(report, "PF-17", evaluate_pf17(config.pf17_owner_confirmation))
    except _Stop as stop:
        report.stopped_at, report.stop_reason = stop.step, stop.reason
    except Exception:  # noqa: BLE001 - unexpected internal error: fixed token only
        report.stopped_at, report.stop_reason = "INTERNAL", "internal_error"
    finally:
        _end_session(conn, report)
    return report


def _end_session(conn: Any, report: PreflightReport) -> None:
    if conn is None:
        return
    if report.transaction_opened:
        try:
            conn.rollback()
            report.rollback = "done"
        except Exception:  # noqa: BLE001
            report.rollback = "error"
    try:
        conn.close()
        report.close = "done"
    except Exception:  # noqa: BLE001
        report.close = "error"
    if report.rollback == "error" or report.close == "error":
        report.stopped_at = report.stopped_at or "CLEANUP"
        report.stop_reason = report.stop_reason or "session_cleanup_failed"


# --------------------------------------------------------------------------- #
# CLI: disabled. Reads no environment, file or argument; opens nothing.
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    lines = ["preflight_overall=STOP", "preflight_stop_reason=production_entry_point_disabled"]
    lines.extend(f"{key}={value}" for key, value in FINAL_STATE)
    sys.stdout.write("\n".join(lines) + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
