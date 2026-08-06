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
