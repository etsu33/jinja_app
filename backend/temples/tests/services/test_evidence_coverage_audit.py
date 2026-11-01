# -*- coding: utf-8 -*-
"""PR-E1 Evidence Coverage Audit（read-only）の focused tests。"""

from __future__ import annotations

import json
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from temples.domain import source_fact_mapping_registry_v1 as registry_module
from temples.domain.source_fact_mapping_registry_v1 import SourceFactMappingRecord, build_registry
from temples.models import (
    GoriyakuTag,
    Shrine,
    ShrineDeity,
    ShrineHistory,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.services.concierge_chat_candidates import build_chat_candidates_with_eligibility
from temples.services.evidence_coverage_audit import (
    EvidenceCoverageInputError,
    build_evidence_coverage_report,
    compare_reports,
    parse_axis_conflicts,
    prefecture_of,
)
from temples.tests.test_bootstrap_goriyaku_master_exact39_contract import CANONICAL_MASTER

CANONICAL_ID_BY_NAME = {name: tag_id for tag_id, name in CANONICAL_MASTER}
ORIGIN = "repository-seed-local"


def _tag(name: str) -> GoriyakuTag:
    tag, _ = GoriyakuTag.objects.get_or_create(id=CANONICAL_ID_BY_NAME[name], name=name)
    return tag


def _shrine(name: str, address: str = "東京都千代田区1-1") -> Shrine:
    return Shrine.objects.create(
        name_jp=name, kind="shrine", address=address, latitude=35.0, longitude=139.0
    )


def _source(
    *, source_type="shrine_official", url="https://example.jp/yuisho", status="source_confirmed"
):
    kwargs = dict(source_type=source_type, title="出典", url=url, verification_status=status)
    if status in ("source_confirmed", "reviewed"):
        kwargs["verified_at"] = timezone.now()
    return ShrineKnowledgeSource.objects.create(**kwargs)


def _deity(shrine, source=None, status="source_confirmed"):
    deity = ShrineDeity.objects.create(
        shrine=shrine,
        display_name="祭神A",
        verification_status=status,
        verified_at=timezone.now() if status in ("source_confirmed", "reviewed") else None,
    )
    deity.sources.add(source or _source())
    return deity


def _history(
    shrine, history_type="tradition", source=None, status="source_confirmed", title="由緒A"
):
    history = ShrineHistory.objects.create(
        shrine=shrine,
        history_type=history_type,
        title=title,
        content="本文",
        verification_status=status,
        verified_at=timezone.now() if status in ("source_confirmed", "reviewed") else None,
    )
    history.sources.add(source or _source())
    return history


def _source_fact(shrine, key, wording="学業成就", source=None):
    fact = ShrineSourceFact.objects.create(
        shrine=shrine,
        stable_key=key,
        source_attested_wording=wording,
        evidence_characterization="official_prayer_supported",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    fact.sources.add(source or _source())
    return fact


def _install_registry(monkeypatch, *pairs):
    records = tuple(
        SourceFactMappingRecord(
            source_fact_key=k, canonical_concept_name=c, mapping_classification="EXACT"
        )
        for k, c in pairs
    )
    monkeypatch.setattr(registry_module, "_default_registry", build_registry(records))


def _row(report, name):
    return next(r for r in report["shrines"] if r["name_jp"] == name)


@pytest.fixture
def mixed_db(monkeypatch):
    _tag("学業成就")
    _tag("縁結び")

    verified = _shrine("根拠充足神社")
    _deity(verified)
    _history(verified, "tradition")
    _source_fact(verified, "e1-study", "学業成就")

    partial_a = _shrine("基礎充足神社")
    _deity(partial_a)
    _history(partial_a, "official_origin")
    partial_a.goriyaku_tags.add(_tag("縁結び"))

    partial_b = _shrine("文脈のみ神社", address="新潟県新潟市1-1")
    _history(partial_b, "regional_context", source=_source(source_type="government"))

    _shrine("知識なし神社", address="新潟県長岡市1-1").goriyaku_tags.add(_tag("縁結び"))

    _install_registry(monkeypatch, ("e1-study", "学業成就"))
    return {"verified": verified, "partial_a": partial_a, "partial_b": partial_b}


@pytest.mark.django_db
def test_classes_follow_pillars(mixed_db):
    report = build_evidence_coverage_report(data_origin=ORIGIN)

    assert _row(report, "根拠充足神社")["evidence_class"] == "VERIFIED"
    assert _row(report, "根拠充足神社")["verified_needs"] == ["focus", "study"]
    assert _row(report, "基礎充足神社")["evidence_class"] == "PARTIAL_A"
    assert _row(report, "文脈のみ神社")["evidence_class"] == "PARTIAL_B"
    assert _row(report, "知識なし神社")["evidence_class"] == "INSUFFICIENT"
    assert report["summary"]["class_counts"] == {
        "VERIFIED": 1,
        "PARTIAL_A": 1,
        "PARTIAL_B": 1,
        "INSUFFICIENT": 1,
    }


@pytest.mark.django_db
def test_eligible_now_matches_shared_eligibility_and_is_not_changed(mixed_db):
    """regional_context だけの神社は現行 eligibility を満たす（観測のみで境界を変えない）。"""
    report = build_evidence_coverage_report(data_origin=ORIGIN)
    runtime_ids = {
        c["shrine_id"]
        for c in build_chat_candidates_with_eligibility(
            apply_popularity_pool_limit=False
        ).candidates
    }
    audited_eligible = {r["id"] for r in report["shrines"] if r["eligible_now"]}

    assert audited_eligible == runtime_ids
    assert _row(report, "文脈のみ神社")["eligible_now"] is True
    assert _row(report, "文脈のみ神社")["pillar_h"] is False


@pytest.mark.django_db
def test_legacy_tags_are_unattributed_and_never_counted_as_c(mixed_db):
    report = build_evidence_coverage_report(data_origin=ORIGIN)
    row = _row(report, "基礎充足神社")

    assert row["legacy_unattributed_needs"] == ["love", "marriage", "relationship"]
    assert row["c_needs"] == []
    love = report["summary"]["by_need"]["love"]
    assert love["legacy_unattributed"] == 2
    assert love["legacy_unattributed_and_eligible_now"] == 1
    assert love["c_source_backed"] == 0


@pytest.mark.django_db
def test_c_requires_attributable_source(monkeypatch):
    _tag("学業成就")
    shrine = _shrine("出典URLなし神社")
    _deity(shrine)
    _history(shrine)
    _source_fact(shrine, "e1-nourl", source=_source(url=""))
    _install_registry(monkeypatch, ("e1-nourl", "学業成就"))

    row = _row(build_evidence_coverage_report(data_origin=ORIGIN), "出典URLなし神社")

    assert row["c_needs"] == []
    assert row["evidence_class"] == "PARTIAL_A"


@pytest.mark.django_db
def test_epistemic_types_distinguish_fact_tradition_interpretation():
    shrine = _shrine("性質神社")
    _deity(shrine)
    _history(shrine, "historical_event", source=_source(source_type="government"), title="公的史料")
    _history(
        shrine, "historical_event", source=_source(source_type="shrine_official"), title="公式のみ"
    )
    _history(shrine, "regional_context", title="文脈")

    report = build_evidence_coverage_report(data_origin=ORIGIN, trace_shrine_ids=[shrine.id])
    chain = report["trace_chains"][0]
    by_label = {f["label"]: f["epistemic_type"] for f in chain["facts"]}

    assert by_label == {
        "祭神A": "tradition",
        "公的史料": "fact",
        "公式のみ": "tradition",
        "文脈": "interpretation",
    }
    assert _row(report, "性質神社")["attributable_fact_epistemic"] == {
        "fact": 1,
        "tradition": 2,
        "interpretation": 1,
    }


@pytest.mark.django_db
def test_axis_conflict_removes_only_that_need(mixed_db):
    conflicts = parse_axis_conflicts(
        [
            {
                "name_jp": "根拠充足神社",
                "address": "東京都千代田区1-1",
                "need": "study",
                "basis": "review",
            },
            {"name_jp": "存在しない神社", "address": "", "need": "love", "basis": "review"},
        ]
    )
    report = build_evidence_coverage_report(data_origin=ORIGIN, axis_conflicts=conflicts)
    row = _row(report, "根拠充足神社")

    assert row["conflicting_needs"] == ["study"]
    assert row["verified_needs"] == ["focus"]
    assert row["evidence_class"] == "VERIFIED"
    assert report["summary"]["by_need"]["study"]["conflicting"] == 1
    assert report["axis_conflict_input"]["unmatched_identity_keys"] == ["存在しない神社\t"]


def test_axis_conflict_input_is_validated():
    with pytest.raises(EvidenceCoverageInputError):
        parse_axis_conflicts([{"name_jp": "A", "need": "unknown_need", "basis": "x"}])
    with pytest.raises(EvidenceCoverageInputError):
        parse_axis_conflicts([{"name_jp": "A", "need": "love"}])


@pytest.mark.django_db
def test_pillar_conflict_when_only_disputed_history():
    shrine = _shrine("争い神社")
    _deity(shrine)
    _history(shrine, "tradition", status="disputed")

    row = _row(build_evidence_coverage_report(data_origin=ORIGIN), "争い神社")

    assert row["pillar_conflicts"] == ["H"]
    assert row["disputed_fact_count"] == 1
    assert row["evidence_class"] == "PARTIAL_B"


@pytest.mark.django_db
def test_prefecture_aggregation(mixed_db):
    by_pref = build_evidence_coverage_report(data_origin=ORIGIN)["summary"]["by_prefecture"]

    assert by_pref["東京都"]["total"] == 2
    assert by_pref["新潟県"] == {
        "total": 2,
        "eligible_now": 1,
        "base_complete": 0,
        "VERIFIED": 0,
        "PARTIAL_A": 0,
        "PARTIAL_B": 1,
        "INSUFFICIENT": 1,
    }


def test_prefecture_of_handles_google_maps_format_and_unknown():
    assert prefecture_of("日本、〒157-0076 東京都世田谷区") == "東京都"
    assert prefecture_of("不明な住所") is None


@pytest.mark.django_db
def test_trace_chain_links_fact_source_consultation_and_reason_inputs(mixed_db):
    report = build_evidence_coverage_report(data_origin=ORIGIN)
    chain = next(c for c in report["trace_chains"] if c["shrine"]["name_jp"] == "根拠充足神社")

    assert {c["shrine"]["evidence_class"] for c in report["trace_chains"]} == {
        "VERIFIED",
        "PARTIAL_A",
        "PARTIAL_B",
        "INSUFFICIENT",
    }
    assert chain["facts"][0]["sources"][0]["attributable"] is True
    assert (
        chain["consultation_evidence"]["channel_b_source_backed"][0]["source_fact_key"]
        == "e1-study"
    )
    assert chain["reason_inputs"]["knowledge_deity_names"] == ["祭神A"]
    assert chain["reason_inputs"]["channel_b_wordings"] == ["学業成就"]
    assert "content" not in json.dumps(chain["reason_inputs"])


@pytest.mark.django_db
def test_report_is_deterministic_and_read_only(mixed_db):
    counts_before = {
        m.__name__: m.objects.count()
        for m in (
            Shrine,
            ShrineDeity,
            ShrineHistory,
            ShrineKnowledgeSource,
            ShrineSourceFact,
            GoriyakuTag,
        )
    }
    with CaptureQueriesContext(connection) as ctx:
        first = build_evidence_coverage_report(data_origin=ORIGIN)
    second = build_evidence_coverage_report(data_origin=ORIGIN)

    assert json.dumps(first, sort_keys=True, ensure_ascii=False) == json.dumps(
        second, sort_keys=True, ensure_ascii=False
    )
    sql = " ".join(q["sql"].lower() for q in ctx.captured_queries)
    assert not any(w in sql for w in ("insert ", "update ", "delete "))
    assert "concierge" not in sql  # 相談文・thread・利用ログを読まない
    assert counts_before == {
        m.__name__: m.objects.count()
        for m in (
            Shrine,
            ShrineDeity,
            ShrineHistory,
            ShrineKnowledgeSource,
            ShrineSourceFact,
            GoriyakuTag,
        )
    }


@pytest.mark.django_db
def test_compare_reports_lists_discrepancies(mixed_db):
    seed_report = build_evidence_coverage_report(data_origin=ORIGIN)
    Shrine.objects.filter(name_jp="知識なし神社").delete()
    _history(Shrine.objects.get(name_jp="文脈のみ神社"), "founding")
    prod_like = build_evidence_coverage_report(data_origin="other")

    diff = compare_reports(prod_like, seed_report)

    assert diff["only_in_other"] == ["知識なし神社\t新潟県長岡市1-1"]
    assert diff["changed"] == [
        {
            "identity_key": "文脈のみ神社\t新潟県新潟市1-1",
            "differences": {"pillar_h": {"other": False, "current": True}},
        }
    ]
    assert diff["class_count_delta"]["INSUFFICIENT"] == -1


@pytest.mark.django_db
def test_command_requires_confirmation_for_production_origin(mixed_db):
    with pytest.raises(CommandError, match="confirm-read-only-production"):
        call_command("evidence_coverage_audit", "--data-origin", "production-readonly")


@pytest.mark.django_db(transaction=True)
def test_command_json_runs_in_read_only_transaction_and_compares(mixed_db, tmp_path):
    out = StringIO()
    with CaptureQueriesContext(connection) as ctx:
        call_command(
            "evidence_coverage_audit", "--data-origin", ORIGIN, "--format", "json", stdout=out
        )
    report = json.loads(out.getvalue())

    assert report["data_origin"] == ORIGIN
    assert report["summary"]["shrine_count"] == 4
    if connection.vendor == "postgresql":
        assert report["execution"] == {
            "read_only_guard": "postgresql_transaction_read_only",
            "select_only_role_verified": None,
            "target_identity_verified": False,
        }
        assert any("set transaction read only" in q["sql"].lower() for q in ctx.captured_queries)

    path = tmp_path / "seed.json"
    path.write_text(out.getvalue(), encoding="utf-8")
    text_out = StringIO()
    call_command(
        "evidence_coverage_audit",
        "--data-origin",
        "other",
        "--compare-with",
        str(path),
        stdout=text_out,
    )
    text = text_out.getvalue()
    assert "Comparison with: repository-seed-local" in text
    assert "changed: 0" in text
    assert "does NOT mean false" in text


@pytest.mark.django_db(transaction=True)
def test_read_only_guard_rejects_writes_on_postgresql():
    if connection.vendor != "postgresql":
        pytest.skip("read-only transaction guard is PostgreSQL-specific")
    from django.db import DatabaseError, transaction

    with pytest.raises(DatabaseError):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
            Shrine.objects.create(name_jp="書込不可", address="東京都")


# ---------- #3396 review amendments ----------


@pytest.mark.django_db
def test_empty_explicit_scope_is_a_valid_zero_report(mixed_db):
    """空の明示スコープは 0 社監査であり、既定スコープへフォールバックしない。"""
    report = build_evidence_coverage_report(data_origin=ORIGIN, shrine_ids=[])

    assert report["scope"] == {"mode": "explicit", "requested_count": 0, "resolved_in_db": 0}
    assert report["shrines"] == []
    assert report["trace_chains"] == []
    assert report["summary"]["shrine_count"] == 0
    assert report["summary"]["class_counts"] == {
        "VERIFIED": 0,
        "PARTIAL_A": 0,
        "PARTIAL_B": 0,
        "INSUFFICIENT": 0,
    }
    assert report["summary"]["by_prefecture"] == {}
    assert all(v["legacy_unattributed"] == 0 for v in report["summary"]["by_need"].values())


@pytest.mark.django_db
def test_multiple_sources_one_attributable_is_enough():
    shrine = _shrine("複数出典神社")
    deity = _deity(shrine, source=_source(status="draft"))
    deity.sources.add(_source(url=""))  # fact-ready だが URL なし
    deity.sources.add(_source(url="https://example.jp/official"))  # 出典追跡可能
    _history(shrine, "founding")

    report = build_evidence_coverage_report(data_origin=ORIGIN, trace_shrine_ids=[shrine.id])
    row = _row(report, "複数出典神社")
    deity_trace = next(f for f in report["trace_chains"][0]["facts"] if f["kind"] == "deity")

    assert row["pillar_d"] is True
    assert [s["attributable"] for s in deity_trace["sources"]] == [False, False, True]
    assert deity_trace["attributable"] is True


@pytest.mark.django_db
def test_missing_provenance_keeps_current_eligibility_but_not_pillars():
    """URL も書誌も無い fact-ready Source は usable（現行 eligibility）だが出典追跡不可。

    provenance 欠落は「誤り」ではない: eligible_now は変えず、柱に数えないだけ。
    """
    shrine = _shrine("出典欠落神社")
    _deity(shrine, source=_source(url=""))
    _history(shrine, "tradition", source=_source(url=""))

    row = _row(build_evidence_coverage_report(data_origin=ORIGIN), "出典欠落神社")

    assert row["eligible_now"] is True
    assert (row["pillar_d"], row["pillar_h"]) == (False, False)
    assert row["evidence_class"] == "PARTIAL_B"
    assert row["pillar_conflicts"] == []
    assert row["disputed_fact_count"] == 0


def _report_with_rows(origin, rows):
    return {
        "schema_version": "1",
        "data_origin": origin,
        "shrines": rows,
        "summary": {
            "class_counts": {c: 0 for c in ("VERIFIED", "PARTIAL_A", "PARTIAL_B", "INSUFFICIENT")}
        },
    }


def _cmp_row(key, evidence_class="PARTIAL_A"):
    return {
        "identity_key": key,
        "evidence_class": evidence_class,
        "eligible_now": True,
        "pillar_d": True,
        "pillar_h": True,
        "c_needs": [],
    }


def test_compare_reports_never_collapses_duplicate_identity_keys():
    current = _report_with_rows(
        "production-readonly",
        [
            _cmp_row("同名神社\t東京都"),
            _cmp_row("同名神社\t東京都", "PARTIAL_B"),
            _cmp_row("単独神社\t東京都"),
        ],
    )
    other = _report_with_rows(
        ORIGIN, [_cmp_row("同名神社\t東京都"), _cmp_row("単独神社\t東京都", "PARTIAL_B")]
    )

    diff = compare_reports(current, other)

    assert diff["duplicate_identity_keys"] == {"current": ["同名神社\t東京都"], "other": []}
    assert diff["only_in_current"] == []
    assert diff["only_in_other"] == []
    assert [c["identity_key"] for c in diff["changed"]] == ["単独神社\t東京都"]


def test_compare_reports_rejects_schema_mismatch():
    other = _report_with_rows(ORIGIN, [])
    other["schema_version"] = "0"
    with pytest.raises(EvidenceCoverageInputError, match="schema_version"):
        compare_reports(_report_with_rows(ORIGIN, []), other)


# ---------- #3396 review amendments (2): Source Fact checks / fail-closed guard ----------

from unittest import mock  # noqa: E402

from temples.management.commands import evidence_coverage_audit as command_module  # noqa: E402
from temples.services import evidence_coverage_audit as service_module  # noqa: E402
from temples.services.channel_b_typed_need_match import TypedNeedMatch  # noqa: E402


def _typed(key: str, need: str = "study") -> TypedNeedMatch:
    return TypedNeedMatch(
        need=need,
        canonical_concept_name="学業成就",
        signal_type="official_prayer_supported",
        source_fact_key=key,
        source_attested_wording="学業成就",
    )


@pytest.mark.django_db
def test_source_fact_c_is_attributed_only_to_its_owner(monkeypatch):
    _tag("学業成就")
    owner = _shrine("所有神社")
    other = _shrine("非所有神社", address="東京都港区1-1")
    for s in (owner, other):
        _deity(s)
        _history(s)
    _source_fact(owner, "e1-owned")
    _install_registry(monkeypatch, ("e1-owned", "学業成就"))

    report = build_evidence_coverage_report(data_origin=ORIGIN)

    assert _row(report, "所有神社")["c_needs"] == ["focus", "study"]
    assert _row(report, "非所有神社")["c_needs"] == []


@pytest.mark.django_db
def test_mismatched_source_fact_ownership_fails_closed(monkeypatch):
    """一致が別 Shrine の Source Fact を指していたら、出典追跡可能として数えない。"""
    claimant = _shrine("主張側神社")
    owner = _shrine("実所有神社", address="東京都港区1-1")
    for s in (claimant, owner):
        _deity(s)
        _history(s)
    _source_fact(owner, "e1-foreign")
    monkeypatch.setattr(
        service_module,
        "fetch_typed_need_matches",
        lambda ids: {claimant.id: (_typed("e1-foreign"),)},
    )

    report = build_evidence_coverage_report(data_origin=ORIGIN, trace_shrine_ids=[claimant.id])
    row = _row(report, "主張側神社")
    chain = next(c for c in report["trace_chains"] if c["shrine"]["id"] == claimant.id)

    assert row["c_needs"] == []
    assert row["evidence_class"] == "PARTIAL_A"
    assert chain["consultation_evidence"]["channel_b_source_backed"][0]["attributable"] is False


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["draft", "disputed", "unverified"])
def test_non_fact_ready_source_fact_is_never_c(monkeypatch, status):
    _tag("学業成就")
    shrine = _shrine("未確認SF神社")
    _deity(shrine)
    _history(shrine)
    fact = _source_fact(shrine, "e1-status")
    ShrineSourceFact.objects.filter(pk=fact.pk).update(verification_status=status)
    _install_registry(monkeypatch, ("e1-status", "学業成就"))

    # runtime gate（fetch_typed_need_matches）で落ちる。
    assert _row(build_evidence_coverage_report(data_origin=ORIGIN), "未確認SF神社")["c_needs"] == []

    # gate を迂回した一致が来ても、監査側で fact-ready を再確認して数えない（fail closed）。
    monkeypatch.setattr(
        service_module, "fetch_typed_need_matches", lambda ids: {shrine.id: (_typed("e1-status"),)}
    )
    assert _row(build_evidence_coverage_report(data_origin=ORIGIN), "未確認SF神社")["c_needs"] == []


@pytest.mark.django_db
def test_disputed_only_deity_is_insufficient_with_pillar_conflict():
    shrine = _shrine("祭神争い神社")
    _deity(shrine, status="disputed")

    row = _row(build_evidence_coverage_report(data_origin=ORIGIN), "祭神争い神社")

    assert row["eligible_now"] is False
    assert row["evidence_class"] == "INSUFFICIENT"
    assert row["pillar_conflicts"] == ["D"]


@pytest.mark.django_db
def test_command_fails_closed_inside_nested_transaction(mixed_db):
    """pytest の transaction 内（= 入れ子）では guard を張れないので、何も読まずに止まる。"""
    out = StringIO()
    with pytest.raises(CommandError, match="cannot establish a PostgreSQL read-only"):
        call_command("evidence_coverage_audit", "--data-origin", ORIGIN, stdout=out)
    assert out.getvalue() == ""


@pytest.mark.django_db
def test_allow_unguarded_local_is_explicit_and_recorded(mixed_db):
    out = StringIO()
    call_command(
        "evidence_coverage_audit",
        "--data-origin",
        ORIGIN,
        "--allow-unguarded-local",
        "--format",
        "json",
        stdout=out,
    )
    assert json.loads(out.getvalue())["execution"] == {
        "read_only_guard": "unguarded_explicitly_allowed_local",
        "select_only_role_verified": None,
        "target_identity_verified": False,
    }


@pytest.mark.django_db
def test_allow_unguarded_local_is_refused_for_production(mixed_db):
    with pytest.raises(CommandError, match="cannot be combined"):
        call_command(
            "evidence_coverage_audit",
            "--data-origin",
            "production-readonly",
            "--confirm-read-only-production",
            "--allow-unguarded-local",
        )


@pytest.mark.django_db(transaction=True)
def test_guard_aborts_when_read_only_is_not_effective(mixed_db):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL-specific guard")
    fake_cursor = mock.MagicMock()
    fake_cursor.fetchone.return_value = ("off",)
    fake_cursor.__enter__.return_value = fake_cursor
    with mock.patch.object(command_module.connection, "cursor", return_value=fake_cursor):
        with pytest.raises(CommandError, match="not effective"):
            call_command("evidence_coverage_audit", "--data-origin", ORIGIN)


@pytest.mark.django_db(transaction=True)
def test_established_guard_rejects_writes():
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL-specific guard")
    from django.db import DatabaseError, transaction

    with pytest.raises(DatabaseError):
        with transaction.atomic():
            command_module._establish_read_only_transaction()
            Shrine.objects.create(name_jp="書込拒否", address="東京都")


@pytest.mark.django_db(transaction=True)
def test_production_origin_fails_closed_for_writable_role(mixed_db):
    """confirm フラグは権限の証明ではない。書き込み可能なロール（test DB の所有者）なら止まる。"""
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL-specific guard")
    out = StringIO()
    with pytest.raises(CommandError, match="SELECT-only"):
        call_command(
            "evidence_coverage_audit",
            "--data-origin",
            "production-readonly",
            "--confirm-read-only-production",
            stdout=out,
        )
    assert out.getvalue() == ""


@pytest.mark.django_db(transaction=True)
def test_production_origin_runs_with_select_only_role(mixed_db):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL-specific guard")
    import uuid

    role = f"ecaudit_ro_{uuid.uuid4().hex[:8]}"
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT rolcreaterole OR rolsuper FROM pg_roles WHERE rolname = current_user"
        )
        if not cursor.fetchone()[0]:
            pytest.skip("test role cannot create roles")
        cursor.execute(f"CREATE ROLE {role} NOLOGIN")
        cursor.execute(f"GRANT USAGE ON SCHEMA public TO {role}")
        cursor.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {role}")
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SET ROLE {role}")
        out = StringIO()
        call_command(
            "evidence_coverage_audit",
            "--data-origin",
            "production-readonly",
            "--confirm-read-only-production",
            "--format",
            "json",
            stdout=out,
        )
        report = json.loads(out.getvalue())
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET ROLE")
            cursor.execute(f"DROP OWNED BY {role}")
            cursor.execute(f"DROP ROLE {role}")

    assert report["execution"] == {
        "read_only_guard": "postgresql_transaction_read_only",
        "select_only_role_verified": True,
        "target_identity_verified": False,
    }
    assert report["summary"]["shrine_count"] == 4
