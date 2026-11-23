"""Local disposable database checks for the SPH-21 permission snapshot query set.

Runs only against the pytest-django test database on localhost（the CI service container or a local throwaway
cluster）. Fixture objects are created in that test database and removed afterwards; no role is created and
nothing outside the test database is touched. Production is never contacted. Review record:
docs/audit/sph21-permission-snapshot-sql-review-2026-11-23.md

What is checked:
- every query S0-S9 is accepted by the local PostgreSQL inside one REPEATABLE READ READ ONLY transaction;
- S0 stops a run that is not REPEATABLE READ READ ONLY;
- NULL ACL, explicit grant and explicit empty ACL are told apart; column, schema-default and database ACLs appear;
- grants and policies committed by another session during the transaction do not appear in S1-S9.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.db import connection

REPO = Path(__file__).resolve().parents[2]
SQL = REPO / "docs" / "audit" / "sql" / "sph21_permission_snapshot.sql"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
PREFIX = "sph21fx_"

pytestmark = pytest.mark.django_db(transaction=True)

FIXTURE_DDL = [
    f"CREATE TABLE public.{PREFIX}t_default (id int)",
    f"CREATE TABLE public.{PREFIX}t_granted (id int, a text, b text)",
    f"GRANT SELECT ON public.{PREFIX}t_granted TO PUBLIC",
    f"CREATE TABLE public.{PREFIX}t_revoked (id int)",
    f"REVOKE ALL ON public.{PREFIX}t_revoked FROM CURRENT_USER",
    f"CREATE TABLE public.{PREFIX}t_colgrant (id int, a text)",
    f"GRANT SELECT (a) ON public.{PREFIX}t_colgrant TO PUBLIC",
    f"CREATE TABLE public.{PREFIX}t_rls (id int)",
    f"ALTER TABLE public.{PREFIX}t_rls ENABLE ROW LEVEL SECURITY",
    f"CREATE POLICY {PREFIX}p_read ON public.{PREFIX}t_rls FOR SELECT USING (id > 0)",
    f"CREATE FUNCTION public.{PREFIX}f() RETURNS int LANGUAGE sql AS 'SELECT 1'",
    f"CREATE SEQUENCE public.{PREFIX}s",
    "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO PUBLIC",
]
FIXTURE_CLEANUP = [
    "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE SELECT ON TABLES FROM PUBLIC",
    f"DROP TABLE IF EXISTS public.{PREFIX}t_default, public.{PREFIX}t_granted, public.{PREFIX}t_revoked, "
    f"public.{PREFIX}t_colgrant, public.{PREFIX}t_rls, public.{PREFIX}t_late",
    f"DROP FUNCTION IF EXISTS public.{PREFIX}f()",
    f"DROP SEQUENCE IF EXISTS public.{PREFIX}s",
]


def _queries() -> dict[str, str]:
    blocks = re.split(r"(?m)^(?=-- S\d\. )", SQL.read_text(encoding="utf-8"))[1:]
    return {re.match(r"-- (S\d)\.", b).group(1): b.strip().rstrip(";") for b in blocks}


def _local_params() -> dict:
    settings = connection.settings_dict
    host = settings.get("HOST") or "localhost"
    if host not in LOCAL_HOSTS or connection.vendor != "postgresql":
        raise RuntimeError("local_disposable_only")
    return {
        "host": "127.0.0.1",
        "hostaddr": "127.0.0.1",
        "port": settings.get("PORT") or 5432,
        "user": settings.get("USER"),
        "password": settings.get("PASSWORD") or None,
        "dbname": settings["NAME"],
    }


def _connect():
    """Autocommit session, so the explicit BEGIN below sets the isolation level itself."""
    import psycopg  # noqa: PLC0415 - test-only driver

    conn = psycopg.connect(**_local_params(), autocommit=True)
    assert conn.info.hostaddr == "127.0.0.1"
    return conn


@pytest.fixture()
def fixture_objects():
    admin = _connect()
    try:
        for stmt in FIXTURE_CLEANUP + FIXTURE_DDL:
            admin.execute(stmt)
        yield admin
    finally:
        for stmt in FIXTURE_CLEANUP:
            admin.execute(stmt)
        admin.close()


def _run_all(conn, queries, ids):
    out = {}
    for qid in ids:
        cur = conn.execute(queries[qid])
        cols = [d.name for d in cur.description]
        out[qid] = [dict(zip(cols, row, strict=True)) for row in cur.fetchall()]
    return out


def _mine(rows, key="object_name"):
    return [r for r in rows if str(r.get(key) or "").startswith(PREFIX)]


def test_all_queries_run_in_one_repeatable_read_read_only_transaction(fixture_objects):
    q = _queries()
    reader = _connect()
    try:
        reader.execute("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY")
        res = _run_all(reader, q, [f"S{i}" for i in range(10)])
        reader.execute("ROLLBACK")
    finally:
        reader.close()
    assert res["S0"][0]["guard"] == "ok"
    assert res["S0"][0]["transaction_read_only"] == "on"
    for qid, rows in res.items():
        assert all(r["snapshot_query"] == qid for r in rows), qid

    s2 = {r["object_name"]: r for r in _mine(res["S2"])}
    assert s2[f"{PREFIX}t_default"]["acl_is_null"] is True
    assert s2[f"{PREFIX}t_default"]["default_acl"]  # implied ACL is spelled out
    assert (
        s2[f"{PREFIX}t_granted"]["acl_is_null"] is False
        and "=r/" in s2[f"{PREFIX}t_granted"]["raw_acl"]
    )
    assert (
        s2[f"{PREFIX}t_revoked"]["acl_is_null"] is False
        and s2[f"{PREFIX}t_revoked"]["raw_acl"] == "{}"
    )
    assert s2[f"{PREFIX}t_rls"]["rls_enabled"] is True

    s7 = _mine(res["S7"])
    assert [(r["object_name"], r["column_name"]) for r in s7] == [(f"{PREFIX}t_colgrant", "a")]

    s6 = [r for r in res["S6"] if r["table_name"] == f"{PREFIX}t_rls"]
    assert [(r["policy_name"], r["policy_roles"]) for r in s6] == [(f"{PREFIX}p_read", ["PUBLIC"])]

    assert any(
        r["target_schema"] == "public" and r["object_type"] == "r" and "=r/" in r["raw_acl"]
        for r in res["S4"]
    )
    assert len(res["S8"]) == 1 and res["S8"][0]["default_acl"]

    s9 = _mine(res["S9"])
    source = {(r["object_type"], r["object_name"]): r["acl_source"] for r in s9}
    assert source[("relation", f"{PREFIX}t_default")] == "implied_default"
    assert source[("relation", f"{PREFIX}t_granted")] == "explicit"
    assert source[("relation", f"{PREFIX}t_revoked")] == "explicit_empty"
    assert source[("column", f"{PREFIX}t_colgrant.a")] == "explicit"
    assert source[("function", f"{PREFIX}f()")] == "implied_default"
    assert ("function", f"{PREFIX}f()", "PUBLIC", "EXECUTE") in {
        (r["object_type"], r["object_name"], r["grantee"], r["privilege_type"]) for r in s9
    }


def test_s0_stops_a_run_that_is_not_repeatable_read_read_only(fixture_objects):
    import psycopg  # noqa: PLC0415

    q = _queries()
    for begin in ("BEGIN", "BEGIN ISOLATION LEVEL REPEATABLE READ", "BEGIN READ ONLY"):
        reader = _connect()
        try:
            reader.execute(begin)
            with pytest.raises(psycopg.errors.InvalidTextRepresentation, match="STOP:"):
                reader.execute(q["S0"]).fetchall()
        finally:
            reader.execute("ROLLBACK")
            reader.close()


def test_changes_committed_during_the_snapshot_do_not_appear(fixture_objects):
    q = _queries()
    ids = [f"S{i}" for i in range(1, 10)]
    reader = _connect()
    try:
        reader.execute("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY")
        before = _run_all(reader, q, ids)
        admin = fixture_objects
        admin.execute(f"GRANT SELECT ON public.{PREFIX}t_default TO PUBLIC")
        admin.execute(f"GRANT SELECT (id) ON public.{PREFIX}t_rls TO PUBLIC")
        admin.execute(
            f"CREATE POLICY {PREFIX}p_late ON public.{PREFIX}t_rls FOR SELECT USING (false)"
        )
        admin.execute(f"CREATE TABLE public.{PREFIX}t_late (id int)")
        after = _run_all(reader, q, ids)
        reader.execute("ROLLBACK")
    finally:
        reader.close()
    for qid in ids:
        assert before[qid] == after[qid], qid
