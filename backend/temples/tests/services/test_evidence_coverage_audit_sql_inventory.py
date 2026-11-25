# -*- coding: utf-8 -*-
"""Evidence Coverage Audit が実際に読む relation と、権限 inventory（audited_tables()）の一致検証。

docs/audit/sph21-evidence-audit-select-role-matrix-2026-11-01.md（#3401）の
`ORM_TABLE_ACCESS_VERIFIED=UNKNOWN` を、ローカル / テスト DB での実測で埋めるための test。

方法（文字列一致に頼らない）:

1. 監査の実行中に発行された SQL と params を `connection.execute_wrapper` で記録する。
2. SELECT ごとに、同じ params で `EXPLAIN (VERBOSE, FORMAT JSON)` を PostgreSQL に解釈させ、
   plan tree の `Relation Name` / `Schema` を集める（subquery / JOIN / M2M 中間テーブルを含む）。
   planner が不要な JOIN を除去しうるため、これは観測値の報告用である。
3. 判定の正本: SELECT 権限を audited_tables() だけに持つ使い捨てロールで全 branch を再実行する。
   PostgreSQL は plan で除去される relation を含め、参照された全 relation の権限を検査するので、
   inventory 外の relation を 1 つでも読めば permission denied で失敗する。
   1 table を外した negative control で、この検出が実際に効くことも確認する。

接続先がローカル / テスト用 PostgreSQL であることを確認できなければ、何も実行せずに fail する（fail closed）。
SQL 本文・行の内容は出力しない。
"""

from __future__ import annotations

import ipaddress
import uuid
from contextlib import contextmanager
from typing import Any, Iterator

import pytest
from django.db import DatabaseError, connection, transaction

from temples.management.commands.evidence_coverage_audit import (
    _verify_select_only_role,
    audited_tables,
)
from temples.services.evidence_coverage_audit import build_evidence_coverage_report
from temples.tests.services.test_evidence_coverage_audit import (
    _deity,
    _history,
    _install_registry,
    _shrine,
    _source_fact,
    _tag,
)

ORIGIN = "repository-seed-local"
_LOCAL_HOSTS = {"", "localhost", "127.0.0.1", "::1"}
_REMOTE_MARKERS = ("supabase", "pooler", "render.com", "amazonaws", "neon.tech")


# ---------------------------------------------------------------------------
# 接続先の確認（fail closed）
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _require_local_test_postgresql(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        settings = connection.settings_dict
        host = str(settings.get("HOST") or "").strip().lower()
        name = str(settings.get("NAME") or "")
        problems = []
        if connection.vendor != "postgresql":
            problems.append(f"vendor={connection.vendor}")
        if host not in _LOCAL_HOSTS:
            problems.append("HOST is not a loopback/socket host")
        if any(marker in host for marker in _REMOTE_MARKERS):
            problems.append("HOST looks like a managed/remote database")
        if not name.startswith("test_"):
            problems.append("database is not a test-runner database (NAME must start with test_)")
        if not problems:
            with connection.cursor() as cursor:
                cursor.execute("SELECT inet_server_addr()")
                (server_addr,) = cursor.fetchone()
            if server_addr is not None:
                addr = ipaddress.ip_address(str(server_addr).split("/")[0])
                if not (addr.is_loopback or addr.is_private):
                    problems.append("server address is not loopback/private")
    if problems:
        pytest.fail(
            "REFUSED: SQL inventory capture runs only against a local test PostgreSQL "
            f"({'; '.join(problems)})."
        )


# ---------------------------------------------------------------------------
# 捕捉と relation 抽出
# ---------------------------------------------------------------------------


@contextmanager
def _capture_statements() -> Iterator[list[tuple[str, Any]]]:
    captured: list[tuple[str, Any]] = []

    def wrapper(execute, sql, params, many, context):
        captured.append((sql, params))
        return execute(sql, params, many, context)

    with connection.execute_wrapper(wrapper):
        yield captured


def _plan_relations(node: Any, out: set[tuple[str, str]]) -> None:
    if isinstance(node, dict):
        if "Relation Name" in node:
            out.add((node.get("Schema", ""), node["Relation Name"]))
        for value in node.values():
            _plan_relations(value, out)
    elif isinstance(node, list):
        for value in node:
            _plan_relations(value, out)


def _relations_read(captured: list[tuple[str, Any]]) -> dict[str, Any]:
    """捕捉した SELECT の relation を EXPLAIN で抽出する（SQL 本文は返さない）。"""
    relations: set[tuple[str, str]] = set()
    per_query: list[frozenset[str]] = []
    select_count = 0
    other_kinds: set[str] = set()
    with connection.cursor() as cursor:
        for sql, params in captured:
            head = sql.lstrip().split(None, 1)[0].upper() if sql.strip() else ""
            if head not in ("SELECT", "WITH"):
                other_kinds.add(head)
                continue
            select_count += 1
            cursor.execute(f"EXPLAIN (VERBOSE, FORMAT JSON) {sql}", params)
            (plan,) = cursor.fetchone()
            query_relations: set[tuple[str, str]] = set()
            _plan_relations(plan, query_relations)
            relations |= query_relations
            per_query.append(frozenset(name for _, name in query_relations))
    app = {name for schema, name in relations if schema not in ("pg_catalog", "information_schema")}
    catalog = {name for schema, name in relations if schema in ("pg_catalog", "information_schema")}
    return {
        "select_count": select_count,
        "per_query_relations": per_query,
        "app_relations": app,
        "catalog_relations": catalog,
        "other_statement_kinds": other_kinds,
    }


# ---------------------------------------------------------------------------
# Branch を網羅するデータ（使い捨て test DB）
# ---------------------------------------------------------------------------


def _populate(monkeypatch, *, registry: str) -> dict[str, Any]:
    """registry: "mapped" | "unmapped_only" | "empty"。"""
    _tag("学業成就")
    _tag("縁結び")
    full = _shrine("棚卸神社")
    _deity(full)
    _history(full, "tradition")
    full.goriyaku_tags.add(_tag("縁結び"))  # legacy Channel A
    _source_fact(full, "inv-mapped")
    other = _shrine("棚卸文脈神社", address="新潟県新潟市1-1")
    _history(other, "regional_context")
    _source_fact(other, "inv-unmapped")  # registry に record が無い Source Fact
    _shrine("知識なし棚卸神社", address="東京都港区1-1")
    _shrine("テスト棚卸QA神社")  # QA fixture 除外の対象（既定スコープ）
    if registry == "mapped":
        _install_registry(monkeypatch, ("inv-mapped", "学業成就"))
    elif registry == "unmapped_only":
        _install_registry(monkeypatch, ("inv-not-in-db", "学業成就"))
    else:
        _install_registry(monkeypatch)
    return {"full": full, "other": other}


def _run_all_paths(ids: dict[str, Any]) -> None:
    build_evidence_coverage_report(data_origin=ORIGIN, trace_per_class=1)  # 既定 QA 除外スコープ
    build_evidence_coverage_report(  # 明示スコープ + trace
        data_origin=ORIGIN,
        shrine_ids=[ids["full"].id, ids["other"].id],
        trace_shrine_ids=[ids["full"].id],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

# branch ごとに「必ず読まれるはずの relation」。読まれなければ branch が未実行とみなして fail する。
_EXPECTED_BY_BRANCH = {
    "scope_and_identity": {"temples_shrine"},
    "deity_history_source_prefetch": {
        "temples_shrinedeity",
        "temples_shrinedeity_sources",
        "temples_shrinehistory",
        "temples_shrinehistory_sources",
        "temples_shrineknowledgesource",
    },
    "legacy_goriyaku_tags": {"temples_shrine_goriyaku_tags", "temples_goriyakutag"},
    "channel_b_source_facts": {"temples_shrinesourcefact", "temples_shrinesourcefact_sources"},
}


@pytest.mark.django_db
@pytest.mark.parametrize("registry", ["mapped", "unmapped_only", "empty"])
def test_observed_application_reads_are_within_audited_tables(monkeypatch, registry):
    ids = _populate(monkeypatch, registry=registry)
    with _capture_statements() as captured:
        _run_all_paths(ids)
    observed = _relations_read(captured)
    inventory = set(audited_tables())

    missing = observed["app_relations"] - inventory
    assert missing == set(), f"relations read but not in audited_tables(): {sorted(missing)}"
    assert observed["select_count"] > 0
    assert observed["other_statement_kinds"] <= {"SAVEPOINT", "RELEASE"}, observed[
        "other_statement_kinds"
    ]

    expected = set().union(*_EXPECTED_BY_BRANCH.values())
    if registry == "empty":
        # registry が空なら Channel B は DB を読まない（fetch_typed_need_matches の契約）。
        expected -= _EXPECTED_BY_BRANCH["channel_b_source_facts"]
    unexercised = expected - observed["app_relations"]
    assert unexercised == set(), f"branch not exercised: {sorted(unexercised)}"


@pytest.mark.django_db
def test_mapped_channel_b_reads_concept_tag_and_unmapped_does_not(monkeypatch):
    """mapped / unmapped の Channel B branch が実際に分岐していることの確認。

    legacy の goriyaku_tags prefetch も temples_goriyakutag を（中間テーブルと JOIN して）読むため、
    relation の和集合では区別できない。query 単位の relation 集合で、Channel B の concept 解決
    （temples_goriyakutag だけを読む query）が mapped のときだけ発行されることを確認する。
    """
    ids = _populate(monkeypatch, registry="unmapped_only")
    with _capture_statements() as unmapped:
        build_evidence_coverage_report(data_origin=ORIGIN, shrine_ids=[ids["full"].id])
    _install_registry(monkeypatch, ("inv-mapped", "学業成就"))
    with _capture_statements() as mapped:
        build_evidence_coverage_report(data_origin=ORIGIN, shrine_ids=[ids["full"].id])

    unmapped_obs = _relations_read(unmapped)
    mapped_obs = _relations_read(mapped)
    concept_lookup = frozenset({"temples_goriyakutag"})
    legacy_prefetch = frozenset({"temples_goriyakutag", "temples_shrine_goriyaku_tags"})

    assert "temples_shrinesourcefact" in unmapped_obs["app_relations"]
    assert concept_lookup not in unmapped_obs["per_query_relations"]
    assert concept_lookup in mapped_obs["per_query_relations"]
    assert legacy_prefetch in unmapped_obs["per_query_relations"]
    assert legacy_prefetch in mapped_obs["per_query_relations"]
    assert mapped_obs["select_count"] == unmapped_obs["select_count"] + 1


@pytest.mark.django_db
def test_guard_reads_only_catalog_relations(monkeypatch):
    """production-readonly の role guard が読むのは catalog だけ（application-data ではない）。"""
    _populate(monkeypatch, registry="mapped")
    with _capture_statements() as captured:
        try:
            _verify_select_only_role()
        except Exception:  # noqa: BLE001 - 結果（拒否）ではなく、読んだ relation だけを見る
            pass
    observed = _relations_read(captured)
    assert observed["app_relations"] == set()
    assert observed["catalog_relations"], "guard must read the role catalog"


def _grant_role(tables: list[str]) -> str:
    role = f"ec_inv_{uuid.uuid4().hex[:10]}"
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT rolcreaterole OR rolsuper FROM pg_roles WHERE rolname = current_user"
        )
        if not cursor.fetchone()[0]:
            pytest.skip("NOT RUN: test database role cannot create roles")
        cursor.execute(f"CREATE ROLE {role} NOLOGIN")
        cursor.execute(f"GRANT USAGE ON SCHEMA public TO {role}")
        for table in tables:
            cursor.execute(f"GRANT SELECT ON TABLE {connection.ops.quote_name(table)} TO {role}")
    return role


@contextmanager
def _as_role(role: str) -> Iterator[None]:
    with connection.cursor() as cursor:
        cursor.execute(f"SET ROLE {role}")
    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET ROLE")


@pytest.mark.django_db
@pytest.mark.parametrize("registry", ["mapped", "unmapped_only", "empty"])
def test_all_paths_succeed_with_select_only_on_audited_tables(monkeypatch, registry):
    """判定の正本: SELECT 権限が audited_tables() だけのロールで、全 branch が通ること。

    ロールは test の transaction 内で作られ、終了時の rollback で消える。
    """
    ids = _populate(monkeypatch, registry=registry)
    role = _grant_role(audited_tables())
    with _as_role(role):
        _run_all_paths(ids)


@pytest.mark.django_db
def test_negative_control_missing_table_is_detected(monkeypatch):
    """inventory から 1 table を外すと permission denied になる = 検出が実際に効いている。"""
    ids = _populate(monkeypatch, registry="mapped")
    role = _grant_role([t for t in audited_tables() if t != "temples_goriyakutag"])
    with _as_role(role):
        with pytest.raises(DatabaseError, match="permission denied"):
            with transaction.atomic():
                _run_all_paths(ids)
