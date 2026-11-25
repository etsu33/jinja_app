"""Row-level security (RLS) fail-closed detection for `evidence_coverage_audit`.

Mother Ship decision (2026-11-02): RLS_POLICY = FAIL_CLOSED_WITH_VISIBILITY_AUDIT.
Readiness doc: `docs/audit/evidence-coverage-production-readiness-2026-11-01.md` §10–§11.

Why: for a role without BYPASSRLS, a table with RLS enabled and no matching policy returns **0 rows without an
error**. The audit would then produce a plausible but wrong report.

What this module does, inside the audit's own guarded read-only transaction:

1. `SET LOCAL row_security = off`, then `SHOW row_security` must return `off`.
   **This is not an RLS bypass.** With `row_security = off`, PostgreSQL raises an error for any query to which
   a row security policy would apply (SQLSTATE 42501, "query would be affected by row-level security policy"),
   instead of silently filtering rows. Roles that already bypass RLS (superusers, BYPASSRLS roles, table owners
   without FORCE) are not affected by this setting at all; it grants nothing.
2. A catalog-only visibility audit of `audited_tables()`: `pg_class.relrowsecurity` / `relforcerowsecurity`, and
   whether the effective role is a superuser or has BYPASSRLS. No application row is read.

Only table names (public schema object names), booleans and fixed tokens leave this module.
"""

from __future__ import annotations

from typing import Any

UNKNOWN = "unknown"

_RLS_CATALOG_SQL = (
    "SELECT t.name, c.relrowsecurity, c.relforcerowsecurity "
    "FROM unnest(%s::text[]) AS t(name) "
    "LEFT JOIN pg_class c ON c.oid = to_regclass(t.name) "
    "ORDER BY t.name"
)
_ROLE_BYPASS_SQL = "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user"

RLS_SQLSTATE = (
    "42501"  # insufficient_privilege: RLS refusal under row_security=off, or a missing grant
)
_RLS_MESSAGE_MARKER = "row-level security"


def enforce_row_security_off(conn) -> str:
    """Set `row_security = off` for the current transaction only. Returns the value SHOW reports.

    Must be called inside the guarded transaction. The caller fails closed unless the result is `off`.
    """
    with conn.cursor() as cursor:
        cursor.execute("SET LOCAL row_security = off")
        cursor.execute("SHOW row_security")
        row = cursor.fetchone()
    if not row or row[0] is None:
        return UNKNOWN
    return str(row[0]).lower()


def collect_rls_visibility(conn, tables: list[str], row_security: str) -> dict[str, Any]:
    """Catalog-only RLS visibility for `tables` on the audit connection."""
    enabled: list[str] = []
    forced: list[str] = []
    unresolved: list[str] = []
    bypass = UNKNOWN
    try:
        with conn.cursor() as cursor:
            cursor.execute(_RLS_CATALOG_SQL, [list(tables)])
            rows = cursor.fetchall()
            cursor.execute(_ROLE_BYPASS_SQL)
            role_row = cursor.fetchone()
    except Exception:  # noqa: BLE001 - unavailable catalog -> UNKNOWN (fail closed upstream)
        rows, role_row = None, None
    if rows is None or len(rows) != len(set(tables)):
        status = UNKNOWN
        unresolved = sorted(set(tables))
    else:
        for name, rls, force in rows:
            if rls is None:
                unresolved.append(name)
            elif rls:
                enabled.append(name)
                if force:
                    forced.append(name)
        if unresolved:
            status = UNKNOWN
        elif enabled:
            status = "rls_enabled"
        else:
            status = "no_rls"
    if role_row is not None and role_row[0] is not None:
        bypass = "true" if role_row[0] else "false"
    return {
        "collection": "in_transaction_catalog",
        "row_security": row_security if row_security in ("on", "off") else UNKNOWN,
        "tables_checked": len(set(tables)),
        "status": status,
        "rls_enabled_tables": enabled,
        "rls_forced_tables": forced,
        "unresolved_tables": unresolved,
        "role_bypasses_rls": bypass,
    }


def production_rls_problems(visibility: dict[str, Any]) -> list[str]:
    """Fail-closed reasons for production-readonly. Empty list means no RLS reason to stop here."""
    problems = []
    if visibility.get("row_security") != "off":
        problems.append("row_security_not_off")
    status = visibility.get("status")
    if status == "rls_enabled":
        problems.append("rls_enabled_on_audited_tables")
    elif status != "no_rls":
        problems.append("rls_state_unknown")
    if visibility.get("role_bypasses_rls") != "false":
        problems.append("role_bypass_rls_not_excluded")
    return problems


def refusal_reason(exc: BaseException) -> str | None:
    """Classify a database refusal raised during the audit reads, without exposing its text.

    Returns `row_level_security_would_apply`, `privilege_missing`, or None if this is not SQLSTATE 42501.
    """
    cause = exc.__cause__ if exc.__cause__ is not None else exc
    if getattr(cause, "sqlstate", None) != RLS_SQLSTATE:
        return None
    if _RLS_MESSAGE_MARKER in str(cause).lower():
        return "row_level_security_would_apply"
    return "privilege_missing"
