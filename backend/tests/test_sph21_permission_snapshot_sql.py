"""Static checks for the SPH-21 permission snapshot query set（docs/audit/sql/sph21_permission_snapshot.sql）.

No database. The checks pin the safety contract of the design-only SQL: catalog-only SELECT statements,
one labelled query per id S0-S9, snapshot-consistent role names, deterministic ordering, and a runner that
opens one REPEATABLE READ READ ONLY transaction and never commits. Review record:
docs/audit/sph21-permission-snapshot-sql-review-2026-11-23.md
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SQL = REPO / "docs" / "audit" / "sql" / "sph21_permission_snapshot.sql"
RUNNER = REPO / "docs" / "audit" / "sql" / "sph21_permission_snapshot_run.psql"
DOC = REPO / "docs" / "audit" / "sph21-permission-snapshot-sql-review-2026-11-23.md"

QUERY_IDS = [f"S{i}" for i in range(10)]

FORBIDDEN_WORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "TRUNCATE",
    "GRANT",
    "REVOKE",
    "ALTER",
    "CREATE",
    "DROP",
    "COPY",
    "CALL",
    "DO",
    "VACUUM",
    "ANALYZE",
    "CLUSTER",
    "REINDEX",
    "LOCK",
    "COMMENT",
    "REFRESH",
    "SET",
    "RESET",
    "BEGIN",
    "COMMIT",
    "ROLLBACK",
    "PREPARE",
    "EXECUTE",
    "LISTEN",
    "NOTIFY",
    "SECURITY",
)
FORBIDDEN_FUNCTIONS = (
    "nextval",
    "setval",
    "pg_terminate_backend",
    "pg_cancel_backend",
    "pg_reload_conf",
    "pg_read_file",
    "pg_read_binary_file",
    "pg_ls_dir",
    "lo_import",
    "lo_export",
    "dblink",
    "set_config",
    "pg_sleep",
    "pg_get_userbyid",
)


def _strip_comments(text: str) -> str:
    return "\n".join(line.split("--", 1)[0] for line in text.splitlines())


def _strip_literals(text: str) -> str:
    return re.sub(r"'(?:[^']|'')*'", "''", text)


def queries() -> dict[str, str]:
    """Split the file on `-- S<n>.` headers; each block holds exactly one statement."""
    blocks = re.split(r"(?m)^(?=-- S\d\. )", SQL.read_text(encoding="utf-8"))[1:]
    out: dict[str, str] = {}
    for block in blocks:
        qid = re.match(r"-- (S\d)\.", block).group(1)
        assert qid not in out, f"duplicate {qid}"
        out[qid] = block
    return out


def test_query_ids_are_s0_to_s9_in_order():
    assert list(queries()) == QUERY_IDS


@pytest.mark.parametrize("qid", QUERY_IDS)
def test_each_block_is_one_select_statement(qid):
    body = _strip_literals(_strip_comments(queries()[qid])).strip()
    statements = [s for s in body.split(";") if s.strip()]
    assert len(statements) == 1, f"{qid}: {len(statements)} statements"
    assert re.match(r"(?is)^\s*(SELECT|WITH)\b", statements[0]), qid


@pytest.mark.parametrize("qid", QUERY_IDS)
def test_no_write_ddl_or_session_statement(qid):
    body = _strip_literals(_strip_comments(queries()[qid])).upper()
    for word in FORBIDDEN_WORDS:
        assert not re.search(rf"\b{word}\b", body), f"{qid}: {word}"


@pytest.mark.parametrize("qid", QUERY_IDS)
def test_no_side_effect_or_syscache_role_functions(qid):
    body = _strip_literals(_strip_comments(queries()[qid])).lower()
    for fn in FORBIDDEN_FUNCTIONS:
        assert not re.search(rf"\b{fn}\s*\(", body), f"{qid}: {fn}"
    # ::regrole and pg_get_userbyid() resolve names outside the transaction snapshot（review §3.1）.
    assert "::regrole" not in body, qid


@pytest.mark.parametrize("qid", QUERY_IDS)
def test_every_result_row_is_labelled(qid):
    body = _strip_comments(queries()[qid])
    assert f"'{qid}' AS snapshot_query" in body, qid
    top_level_selects = re.findall(r"(?m)^SELECT ", body)
    labelled = re.findall(rf"(?m)^SELECT '{qid}'", body)
    wrapper = re.findall(r"(?m)^SELECT \* FROM \($", body)
    assert len(labelled) + len(wrapper) == len(top_level_selects), qid


@pytest.mark.parametrize("qid", [q for q in QUERY_IDS if q not in ("S0", "S8")])
def test_multi_row_queries_have_deterministic_order(qid):
    body = _strip_comments(queries()[qid])
    order_by = body[body.rindex("ORDER BY") :]
    assert 'COLLATE "C"' in order_by, qid


def test_s0_guards_isolation_and_read_only():
    body = _strip_comments(queries()["S0"])
    assert "current_setting('transaction_isolation') = 'repeatable read'" in body
    assert "current_setting('transaction_read_only') = 'on'" in body


def test_null_acl_columns_carry_the_implied_default():
    q = queries()
    for qid, kind in (("S2", "'r'"), ("S3", "'s'"), ("S5", "'n'"), ("S5", "'f'"), ("S8", "'d'")):
        assert f"acldefault({kind}," in q[qid], (qid, kind)
    assert "explicit_empty" in q["S9"] and "implied_default" in q["S9"]


def test_runner_uses_one_read_only_repeatable_read_transaction_and_never_commits():
    text = RUNNER.read_text(encoding="utf-8")
    code = _strip_comments(text)
    assert "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;" in code
    assert (
        code.index("BEGIN ISOLATION")
        < code.index("\\ir sph21_permission_snapshot.sql")
        < code.index("ROLLBACK;")
    )
    assert not re.search(r"\bCOMMIT\b", code.upper())
    assert "\\set ON_ERROR_STOP on" in code
    for needle in ("host=", "password", "postgresql://", "postgres://", "\\connect", "\\c "):
        assert needle not in text.lower(), needle


def test_review_document_exists_and_links_the_sql():
    text = DOC.read_text(encoding="utf-8")
    assert "docs/audit/sql/sph21_permission_snapshot.sql" in text
    assert "sph21_permission_snapshot_run.psql" in text
