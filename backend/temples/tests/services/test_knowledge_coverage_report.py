# -*- coding: utf-8 -*-
import pytest
from django.utils import timezone

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.knowledge_coverage_report import build_knowledge_coverage_report


def _shrine(name: str) -> Shrine:
    return Shrine.objects.create(name_jp=name, address="東京都千代田区", popular_score=0.0)


def _source(verification_status: str = "source_confirmed", source_type: str = "shrine_official") -> ShrineKnowledgeSource:
    kwargs = dict(source_type=source_type, title="出典", verification_status=verification_status)
    if verification_status in ("source_confirmed", "reviewed"):
        kwargs["verified_at"] = timezone.now()
    return ShrineKnowledgeSource.objects.create(**kwargs)


@pytest.mark.django_db
def test_empty_knowledge_db_reports_zero_coverage():
    _shrine("神社A")
    _shrine("神社B")

    report = build_knowledge_coverage_report()

    assert report["audit_target_shrines"] == 2
    assert report["knowledge_coverage"] == {"count": 0, "percentage": 0.0}
    assert report["zero_knowledge"] == {"count": 2, "percentage": 100.0}
    assert report["verified_source_count"] == 0


@pytest.mark.django_db
def test_one_knowledge_shrine_is_counted():
    shrine = _shrine("知識あり神社")
    _shrine("知識なし神社")
    source = _source()

    deity = ShrineDeity.objects.create(
        shrine=shrine, display_name="祭神A", sort_order=0,
        verification_status="source_confirmed", verified_at=timezone.now(),
    )
    deity.sources.add(source)

    report = build_knowledge_coverage_report()

    assert report["audit_target_shrines"] == 2
    assert report["knowledge_coverage"] == {"count": 1, "percentage": 50.0}
    assert report["zero_knowledge"] == {"count": 1, "percentage": 50.0}
    assert report["deity_coverage"]["count"] == 1
    assert report["source_coverage"]["count"] == 1


@pytest.mark.django_db
def test_fact_ready_deity_and_history_are_counted_via_evidence_gate():
    shrine = _shrine("Fact-ready神社")
    source = _source("source_confirmed")

    deity = ShrineDeity.objects.create(
        shrine=shrine, display_name="祭神A", sort_order=0,
        verification_status="source_confirmed", verified_at=timezone.now(),
    )
    deity.sources.add(source)

    history = ShrineHistory.objects.create(
        shrine=shrine, history_type="tradition", title="由緒A", content="内容A",
        period_text="", sort_order=0,
        verification_status="source_confirmed", verified_at=timezone.now(),
    )
    history.sources.add(source)

    report = build_knowledge_coverage_report()
    fact_ready = report["fact_ready_coverage"]

    assert fact_ready["fact_ready_deity_shrines"]["count"] == 1
    assert fact_ready["fact_ready_history_shrines"]["count"] == 1
    assert fact_ready["fact_ready_any_shrines"]["count"] == 1


@pytest.mark.django_db
def test_unusable_fact_is_excluded_from_fact_ready_but_counted_in_raw_coverage():
    """draft状態のFactは Evidence Gate で usable=False。
    raw coverage（knowledge_coverage/deity_coverage）には含まれるが、
    fact_ready_coverageには含まれないことを確認する。
    """
    shrine = _shrine("Draft神社")
    source = _source("source_confirmed")

    deity = ShrineDeity.objects.create(
        shrine=shrine, display_name="下書き祭神", sort_order=0,
        verification_status="draft",
    )
    deity.sources.add(source)

    report = build_knowledge_coverage_report()

    assert report["knowledge_coverage"]["count"] == 1
    assert report["deity_coverage"]["count"] == 1
    assert report["fact_ready_coverage"]["fact_ready_deity_shrines"]["count"] == 0
    assert report["verification_status_distribution"].get("draft") == 1


@pytest.mark.django_db
def test_qa_fixture_shrines_are_excluded_from_audit_target():
    # conftest.py の `_ensure_shrine_exists`（autouse）が pk=1 の「テスト神社」を
    # 自動生成するため、絶対件数ではなくbaselineからの差分で検証する。
    baseline = build_knowledge_coverage_report()

    _shrine("実在神社")
    _shrine("承認テスト神社")
    _shrine("重複検証神社")
    _shrine("テスト神社")

    report = build_knowledge_coverage_report()

    assert report["total_db_shrines"] == baseline["total_db_shrines"] + 4
    assert report["audit_target_shrines"] == baseline["audit_target_shrines"] + 1
    assert report["excluded_test_shrines"] == baseline["excluded_test_shrines"] + 3


@pytest.mark.django_db
def test_source_type_and_confidence_distribution():
    shrine = _shrine("分布確認神社")
    source_official = _source("source_confirmed", source_type="shrine_official")
    source_cultural = _source("source_confirmed", source_type="cultural_property")

    deity = ShrineDeity.objects.create(
        shrine=shrine, display_name="祭神A", sort_order=0, confidence="high",
        verification_status="source_confirmed", verified_at=timezone.now(),
    )
    deity.sources.add(source_official)

    history = ShrineHistory.objects.create(
        shrine=shrine, history_type="historical_event", title="出来事A", content="内容A",
        period_text="", sort_order=0, confidence="medium",
        verification_status="source_confirmed", verified_at=timezone.now(),
    )
    history.sources.add(source_cultural)

    report = build_knowledge_coverage_report()

    assert report["source_type_distribution"] == {
        "cultural_property": 1,
        "shrine_official": 1,
    }
    assert report["confidence_distribution"] == {"high": 1, "medium": 1}


@pytest.mark.django_db
def test_report_does_not_write_to_database():
    _shrine("書き込みなし確認神社")

    before = list(Shrine.objects.values_list("id", "name_jp"))
    build_knowledge_coverage_report()
    after = list(Shrine.objects.values_list("id", "name_jp"))

    assert before == after
    assert ShrineDeity.objects.count() == 0
    assert ShrineHistory.objects.count() == 0
    assert ShrineKnowledgeSource.objects.count() == 0


# --------------------------------------------------------------------------
# P9: 母集団選択（POPULATION SELECTION）と集計（COVERAGE CALCULATION）の分離
# docs/audit/knowledge-coverage-canonical-scope-fix.md
# --------------------------------------------------------------------------


@pytest.mark.django_db
def test_none_scope_defaults_to_qa_filtered_db():
    baseline = build_knowledge_coverage_report()  # shrine_ids=None
    assert baseline["scope"]["mode"] == "qa_filtered_db"
    assert baseline["scope"]["count"] == baseline["audit_target_shrines"]

    _shrine("実在神社A")
    _shrine("承認テスト神社")  # QA fixture 命名 → 既定スコープからは除外される

    report = build_knowledge_coverage_report()

    assert report["scope"]["mode"] == "qa_filtered_db"
    # 「実在神社A」だけ +1、「承認テスト神社」は QA 除外
    assert report["audit_target_shrines"] == baseline["audit_target_shrines"] + 1


@pytest.mark.django_db
def test_explicit_scope_population_injection_ignores_qa_and_artifact_and_dup_rows():
    """A/B ちょうどを scope に渡すと、QA fixture / artifact風 / duplicate風の
    余剰行があっても canonical scope = 2 として集計できる
    （global な QA 除外ルールを変えずに）。"""
    a = _shrine("実在神社A")
    b = _shrine("実在神社B")
    _shrine("承認テスト神社")          # QA fixture
    _shrine("広島市")                   # 非-shrine artifact 風
    Shrine.objects.create(
        name_jp="実在神社A", address="日本、〒000-0000 東京都別区", popular_score=0.0
    )  # 同名 duplicate 風（別 pk / 別 address）

    report = build_knowledge_coverage_report(shrine_ids=[a.id, b.id])

    assert report["scope"]["mode"] == "explicit"
    assert report["scope"]["count"] == 2
    assert report["audit_target_shrines"] == 2
    assert report["scope"]["resolved_in_db"] == 2
    # DB 全行数は増えているが、スコープは供給された 2 社ちょうど
    assert report["total_db_shrines"] >= 6


@pytest.mark.django_db
def test_explicit_scope_percentages_use_supplied_scope_not_all_db_rows():
    a = _shrine("知識あり神社")
    b = _shrine("知識なし神社")
    for i in range(20):
        Shrine.objects.create(
            name_jp=f"ノイズ神社{i}", address=f"東京都ノイズ区{i}", popular_score=0.0
        )  # 大量の DB 行（スコープ外）

    source = _source()
    deity = ShrineDeity.objects.create(
        shrine=a, display_name="祭神A", sort_order=0,
        verification_status="source_confirmed", verified_at=timezone.now(),
    )
    deity.sources.add(source)

    report = build_knowledge_coverage_report(shrine_ids=[a.id, b.id])

    assert report["audit_target_shrines"] == 2
    assert report["knowledge_coverage"] == {"count": 1, "percentage": 50.0}
    assert report["zero_knowledge"] == {"count": 1, "percentage": 50.0}


@pytest.mark.django_db
def test_explicit_empty_scope_audits_zero_and_does_not_fall_back_to_all():
    _shrine("実在神社A")
    _shrine("実在神社B")

    report = build_knowledge_coverage_report(shrine_ids=[])

    assert report["scope"]["mode"] == "explicit"
    assert report["audit_target_shrines"] == 0
    assert report["scope"]["count"] == 0
    assert report["knowledge_coverage"] == {"count": 0, "percentage": 0.0}
    assert report["zero_knowledge"] == {"count": 0, "percentage": 0.0}
    assert report["verified_source_count"] == 0
    assert report["total_source_count"] == 0
    # 明示的な空スコープは None（既定スコープ）とは別物
    assert report["audit_target_shrines"] != build_knowledge_coverage_report()["audit_target_shrines"]


@pytest.mark.django_db
def test_explicit_scope_accepts_a_queryset():
    a = _shrine("実在神社A")
    b = _shrine("実在神社B")
    _shrine("承認テスト神社")

    qs = Shrine.objects.filter(id__in=[a.id, b.id])
    report = build_knowledge_coverage_report(shrine_ids=qs)

    assert report["scope"]["mode"] == "explicit"
    assert report["audit_target_shrines"] == 2


@pytest.mark.django_db
def test_scope_metadata_shape_and_semantics():
    a = _shrine("実在神社A")
    report = build_knowledge_coverage_report(shrine_ids=[a.id, a.id, 999999])

    scope = report["scope"]
    assert set(scope.keys()) == {
        "mode", "count", "total_db_shrines", "qa_fixture_excluded_count",
        "outside_scope_count", "resolved_in_db", "note",
    }
    assert scope["mode"] == "explicit"
    # 重複 id は決定的に除去される
    assert scope["count"] == 2
    # 存在しない id は隠さず可視化する（resolved_in_db で乖離が分かる）
    assert scope["resolved_in_db"] == 1
    assert isinstance(scope["note"], str) and scope["note"]


@pytest.mark.django_db
def test_p9_did_not_repurpose_qa_helper_into_canonical_identity_resolver():
    """回帰: exclude_qa_fixture_shrines は QA/テスト命名規約のみを責務とする。
    P9 は artifact / duplicate identity をここで解決しない。"""
    from temples.services.shrine_qa_fixture_exclusion import exclude_qa_fixture_shrines

    _shrine("実在神社A")
    Shrine.objects.create(name_jp="実在神社A", address="東京都別区", popular_score=0.0)  # dup 風
    _shrine("広島市")       # 非-shrine artifact 風

    remaining = set(
        exclude_qa_fixture_shrines(Shrine.objects.exclude(pk=1)).values_list("name_jp", flat=True)
    )
    # duplicate 風 / artifact 風 は QA 除外の対象ではない（除外されない）
    assert "実在神社A" in remaining
    assert "広島市" in remaining


@pytest.mark.django_db
def test_excluded_test_shrines_stays_qa_only_while_outside_scope_count_tracks_scope():
    """excluded_test_shrines は「QA/test fixture 除外数そのもの」であり続ける。
    explicit スコープ外の artifact風 / duplicate風 行は QA fixture として数えない。

    autouse の pk=1「テスト神社」は QA 命名なので、名前だけ実在神社に更新して
    （delete は別スキーマの cascade を踏むため update で無害化）DB をちょうど
    6 行にし、QA 命名は「承認テスト神社」1 行だけにする:
      total_db_shrines = 6
      audit_target_shrines = 2
      excluded_test_shrines = 1      （QA fixture 命名の 1 行のみ）
      scope.outside_scope_count = 4  （6 - 2）
    数値は固定値ではなく、行構成から動的に導出できる関係として検証する。
    """
    Shrine.objects.filter(pk=1).update(name_jp="pk1実在神社", address="東京都pk1区")

    a = _shrine("実在神社A")
    b = _shrine("実在神社B")
    _shrine("承認テスト神社")  # QA fixture 命名（← これだけが QA 除外対象）
    _shrine("広島市")           # 非-shrine artifact 風（QA命名ではない）
    Shrine.objects.create(
        name_jp="実在神社A", address="東京都別区", popular_score=0.0
    )  # duplicate 風（QA命名ではない）

    report = build_knowledge_coverage_report(shrine_ids=[a.id, b.id])

    assert report["total_db_shrines"] == 6
    assert report["audit_target_shrines"] == 2
    # QA fixture 命名は「承認テスト神社」の 1 行のみ。
    # 広島市（artifact風）/ duplicate 実在神社A は QA fixture として数えない。
    assert report["excluded_test_shrines"] == 1
    assert report["scope"]["qa_fixture_excluded_count"] == 1
    # スコープ外行数 = total - scope.count = 6 - 2 = 4（QA除外数 1 とは別物）
    assert report["scope"]["outside_scope_count"] == report["total_db_shrines"] - report["audit_target_shrines"]
    assert report["scope"]["outside_scope_count"] == 4
    assert report["scope"]["outside_scope_count"] != report["excluded_test_shrines"]


@pytest.mark.django_db
def test_default_scope_qa_excluded_equals_outside_scope_count():
    """qa_filtered_db モードでは両者が一致する（従来挙動の維持）。"""
    _shrine("実在神社A")
    _shrine("承認テスト神社")

    report = build_knowledge_coverage_report()  # None → qa_filtered_db

    assert report["excluded_test_shrines"] == report["scope"]["outside_scope_count"]
    assert report["excluded_test_shrines"] == report["scope"]["qa_fixture_excluded_count"]


@pytest.mark.django_db
def test_explicit_scope_report_is_read_only():
    a = _shrine("実在神社A")
    b = _shrine("実在神社B")
    before = list(Shrine.objects.values_list("id", "name_jp"))
    build_knowledge_coverage_report(shrine_ids=[a.id, b.id])
    build_knowledge_coverage_report(shrine_ids=[])
    after = list(Shrine.objects.values_list("id", "name_jp"))
    assert before == after
    assert ShrineDeity.objects.count() == 0
    assert ShrineHistory.objects.count() == 0


@pytest.mark.django_db
def test_orphan_source_with_no_fact_relation_is_excluded_from_scoped_counts():
    """shrine/factのいずれにも紐付かないSourceは、audit-target-scoped集計に含めない
    （PR実装時に実DBで発見した実例: id=999002「テスト神社公式サイト」相当のケース）。
    """
    _shrine("神社A")
    _source("source_confirmed")  # どのDeity/Historyにもattachしない

    report = build_knowledge_coverage_report()

    assert report["verified_source_count"] == 0
    assert report["total_source_count"] == 0
