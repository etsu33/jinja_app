"""Knowledge Coverage集計（read-only）。

Knowledge Pilot（`docs/audit/shrine-knowledge-pilot-5-result.md`）、
Rollout Batch 1/2（`docs/audit/shrine-knowledge-rollout-batch-1.md`、
`shrine-knowledge-rollout-batch-2.md`）で繰り返し手動実行してきたCoverage
集計クエリを、`knowledge_coverage_report` management commandから呼び出す
唯一の計算ロジックとしてまとめる。

このモジュールは以下を再実装しない。

- Fact usable判定（`temples.services.evidence_gate.decide_fact_usability`へ委譲）
- QA fixture Shrineの除外条件
  （`temples.services.shrine_qa_fixture_exclusion.exclude_qa_fixture_shrines`へ委譲）
- Knowledge Fact取得の候補条件
  （`temples.services.shrine_knowledge_selector`へ委譲）

DBへの書き込みは一切行わない。`docs/core/recommendation-readiness.md`の
Governance Coverage契約・`docs/knowledge/shrine-knowledge-contract.md`の
Evidence Gate契約を再定義せず、既存契約の集計結果を表示するのみ。
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from django.db.models import Count, Q, QuerySet

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services import evidence_gate
from temples.services.shrine_knowledge_selector import (
    fetch_fact_ready_knowledge_deities,
    fetch_fact_ready_knowledge_histories,
)
from temples.services.shrine_qa_fixture_exclusion import exclude_qa_fixture_shrines


def _audit_target_shrine_ids() -> list[int]:
    return list(exclude_qa_fixture_shrines(Shrine.objects.all()).values_list("id", flat=True))


def _per_shrine_fact_counts(queryset: QuerySet, shrine_ids: list[int]) -> dict[int, int]:
    """shrine_id毎のFact件数を1クエリで取得する（shrine数に比例したN+1を発生させない）。"""
    counted = dict(
        queryset.values("shrine_id").annotate(n=Count("id")).values_list("shrine_id", "n")
    )
    return {sid: counted.get(sid, 0) for sid in shrine_ids}


def _count_distribution(counts_by_shrine: dict[int, int]) -> dict[str, int]:
    histogram = Counter(counts_by_shrine.values())
    return {str(k): v for k, v in sorted(histogram.items())}


def _source_counts_by_shrine(shrine_ids: list[int]) -> dict[int, int]:
    """shrine毎の（deity/history経由の）distinct Source件数を2クエリで取得する。"""
    pairs: set[tuple[int, int]] = set()
    for shrine_id, source_id in ShrineDeity.objects.filter(
        shrine_id__in=shrine_ids, sources__isnull=False
    ).values_list("shrine_id", "sources__id"):
        pairs.add((shrine_id, source_id))
    for shrine_id, source_id in ShrineHistory.objects.filter(
        shrine_id__in=shrine_ids, sources__isnull=False
    ).values_list("shrine_id", "sources__id"):
        pairs.add((shrine_id, source_id))

    counts = Counter(shrine_id for shrine_id, _ in pairs)
    return {sid: counts.get(sid, 0) for sid in shrine_ids}


def _shrines_with_source(shrine_ids: list[int]) -> set[int]:
    return {sid for sid, count in _source_counts_by_shrine(shrine_ids).items() if count > 0}


def _audit_scoped_sources_queryset(shrine_ids: list[int]) -> QuerySet:
    return ShrineKnowledgeSource.objects.filter(
        Q(deities__shrine_id__in=shrine_ids) | Q(histories__shrine_id__in=shrine_ids)
    ).distinct()


def build_knowledge_coverage_report() -> dict[str, Any]:
    """Knowledge Coverageのread-only集計結果をdictで返す。

    件数（count）に加え、audit_target_shrinesに対する割合（percentage、
    小数点1桁）も併記する。現在のDB実測値をhardcodeせず、呼び出し時点の
    DB状態から毎回計算する。
    """

    total_db_shrines = Shrine.objects.count()
    audit_target_ids = _audit_target_shrine_ids()
    audit_target_shrines = len(audit_target_ids)
    excluded_test_shrines = total_db_shrines - audit_target_shrines

    deity_counts = _per_shrine_fact_counts(
        ShrineDeity.objects.filter(shrine_id__in=audit_target_ids), audit_target_ids
    )
    history_counts = _per_shrine_fact_counts(
        ShrineHistory.objects.filter(shrine_id__in=audit_target_ids), audit_target_ids
    )
    source_counts = _source_counts_by_shrine(audit_target_ids)

    deity_shrine_ids = {sid for sid, n in deity_counts.items() if n > 0}
    history_shrine_ids = {sid for sid, n in history_counts.items() if n > 0}
    source_shrine_ids = {sid for sid, n in source_counts.items() if n > 0}
    any_knowledge_ids = deity_shrine_ids | history_shrine_ids
    both_deity_history_ids = deity_shrine_ids & history_shrine_ids

    fact_ready_deities = fetch_fact_ready_knowledge_deities(audit_target_ids)
    fact_ready_histories = fetch_fact_ready_knowledge_histories(audit_target_ids)
    fact_ready_deity_ids = {sid for sid, facts in fact_ready_deities.items() if facts}
    fact_ready_history_ids = {sid for sid, facts in fact_ready_histories.items() if facts}
    fact_ready_any_ids = fact_ready_deity_ids | fact_ready_history_ids

    audit_sources_qs = _audit_scoped_sources_queryset(audit_target_ids)
    verified_source_count = audit_sources_qs.filter(
        verification_status__in=evidence_gate.FACT_READY_VERIFICATION_STATUSES
    ).count()
    total_source_count = audit_sources_qs.count()

    verification_status_counter = Counter(
        ShrineDeity.objects.filter(shrine_id__in=audit_target_ids).values_list(
            "verification_status", flat=True
        )
    ) + Counter(
        ShrineHistory.objects.filter(shrine_id__in=audit_target_ids).values_list(
            "verification_status", flat=True
        )
    )
    confidence_counter = Counter(
        ShrineDeity.objects.filter(shrine_id__in=audit_target_ids).values_list(
            "confidence", flat=True
        )
    ) + Counter(
        ShrineHistory.objects.filter(shrine_id__in=audit_target_ids).values_list(
            "confidence", flat=True
        )
    )
    source_type_counter = Counter(audit_sources_qs.values_list("source_type", flat=True))

    def pct(count: int) -> float:
        if audit_target_shrines == 0:
            return 0.0
        return round(count * 100 / audit_target_shrines, 1)

    return {
        "total_db_shrines": total_db_shrines,
        "audit_target_shrines": audit_target_shrines,
        "excluded_test_shrines": excluded_test_shrines,
        "knowledge_coverage": {
            "count": len(any_knowledge_ids),
            "percentage": pct(len(any_knowledge_ids)),
        },
        "zero_knowledge": {
            "count": audit_target_shrines - len(any_knowledge_ids),
            "percentage": pct(audit_target_shrines - len(any_knowledge_ids)),
        },
        "deity_coverage": {
            "count": len(deity_shrine_ids),
            "percentage": pct(len(deity_shrine_ids)),
        },
        "history_coverage": {
            "count": len(history_shrine_ids),
            "percentage": pct(len(history_shrine_ids)),
        },
        "source_coverage": {
            "count": len(source_shrine_ids),
            "percentage": pct(len(source_shrine_ids)),
        },
        "both_deity_and_history_coverage": {
            "count": len(both_deity_history_ids),
            "percentage": pct(len(both_deity_history_ids)),
        },
        "fact_ready_coverage": {
            "fact_ready_deity_shrines": {
                "count": len(fact_ready_deity_ids),
                "percentage": pct(len(fact_ready_deity_ids)),
            },
            "fact_ready_history_shrines": {
                "count": len(fact_ready_history_ids),
                "percentage": pct(len(fact_ready_history_ids)),
            },
            "fact_ready_any_shrines": {
                "count": len(fact_ready_any_ids),
                "percentage": pct(len(fact_ready_any_ids)),
            },
        },
        "verified_source_count": verified_source_count,
        "total_source_count": total_source_count,
        "deity_count_distribution": _count_distribution(deity_counts),
        "history_count_distribution": _count_distribution(history_counts),
        "source_count_distribution": _count_distribution(source_counts),
        "verification_status_distribution": dict(sorted(verification_status_counter.items())),
        "confidence_distribution": dict(sorted(confidence_counter.items())),
        "source_type_distribution": dict(sorted(source_type_counter.items())),
    }


__all__ = ["build_knowledge_coverage_report"]
