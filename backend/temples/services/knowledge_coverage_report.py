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

母集団選択（POPULATION SELECTION）と集計（COVERAGE CALCULATION）を分離する
（`docs/audit/knowledge-coverage-canonical-scope-fix.md` = P9）。この関数は
「どのShrineがcanonicalな実在神社identityか」を決めない。呼び出し側が
`shrine_ids` を明示指定すればそのスコープで、指定しなければ従来どおり
QA fixture除外後の全DB行（＝canonical unique-real-shrine setではない）で
集計する。QA fixture除外（`shrine_qa_fixture_exclusion`）は QA/テスト命名規約
のみを責務とし、非-shrine artifactや重複shadow identityの解決には使わない。
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from django.db.models import Count, Q, QuerySet

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services import evidence_gate
from temples.services.shrine_knowledge_selector import (
    fetch_fact_ready_knowledge_deities,
    fetch_fact_ready_knowledge_histories,
)
from temples.services.shrine_qa_fixture_exclusion import exclude_qa_fixture_shrines


def _qa_filtered_shrine_ids() -> list[int]:
    """既定スコープ: QA/テストfixtureを命名規約で除外した現DB行の id。

    これは「canonicalな実在神社identityの集合」ではない。非-shrine artifact
    （PR #2614: id 105 広島市）や、確定済み重複shadow row（101/103/104）は
    ここでは除外されない — その解決は identity監査（PR #2612–#2614）の責務で、
    QA fixture除外ヘルパーの責務ではない。
    """
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


def _resolve_scope(
    shrine_ids: Iterable[int] | QuerySet | None,
) -> tuple[str, list[int]]:
    """母集団選択をここに一本化する（集計ロジックとは分離）。

    - ``None``      → 既定スコープ（QA fixture除外後の全DB行）。「canonical
      unique-real-shrine set」ではない点に注意。
    - iterable/QuerySet → 明示スコープ。**空**（``[]`` / 空QuerySet）は
      「0社を監査する」を意味し、``None`` とは決して同一視しない。

    重複idは順序を保って除去する（決定的）。存在しないidはそのまま残す
    （呼び出し側の scope 定義誤りを隠さないため。``scope.resolved_in_db``
    で乖離が見える）。
    """
    if shrine_ids is None:
        return "qa_filtered_db", _qa_filtered_shrine_ids()
    if isinstance(shrine_ids, QuerySet):
        ids = list(shrine_ids.values_list("id", flat=True))
    else:
        ids = [int(x) for x in shrine_ids]
    # dedupe, order-preserving, deterministic
    return "explicit", list(dict.fromkeys(ids))


def build_knowledge_coverage_report(
    shrine_ids: Iterable[int] | QuerySet | None = None,
) -> dict[str, Any]:
    """Knowledge Coverageのread-only集計結果をdictで返す。

    母集団選択と集計の分離（P9,
    `docs/audit/knowledge-coverage-canonical-scope-fix.md`）:

    - ``shrine_ids=None``（既定）: 従来どおり QA fixture除外後の全DB行を対象。
      後方互換のため既定挙動は変えない。ただしこの母数は
      **canonical unique-real-shrine denominator ではない**
      （PR #2614: Production では 107、canonical は 103）。
    - ``shrine_ids`` に iterable / QuerySet を渡す: そのスコープちょうどで集計。
      **空スコープ（``[]`` / 空QuerySet）は「0社を監査」= 有効なゼロレポート**
      であり、``None``（既定スコープ）へはフォールバックしない。

    件数(count)に加え、対象スコープ件数に対する割合(percentage、小数1桁)も
    併記する。DB実測値をhardcodeせず、呼び出し時点のDB状態から毎回計算する。
    ``scope`` キーに母数の意味論（mode / count / total_db_shrines /
    outside_scope_count / resolved_in_db / note）を明示する。
    """

    total_db_shrines = Shrine.objects.count()
    scope_mode, audit_target_ids = _resolve_scope(shrine_ids)
    audit_target_shrines = len(audit_target_ids)
    excluded_test_shrines = total_db_shrines - audit_target_shrines
    resolved_in_db = (
        Shrine.objects.filter(id__in=audit_target_ids).count() if audit_target_ids else 0
    )
    if scope_mode == "qa_filtered_db":
        scope_note = (
            "qa_filtered_db: QA/テストfixture命名規約で除外した現DB行数。"
            "非-shrine artifact（PR #2614: id 105）や確定済み重複shadow row"
            "（101/103/104）は解決しないため、canonical unique-real-shrine "
            "denominator（PR #2614 = 103）ではない。canonicalスコープで測るには"
            "呼び出し側が shrine_ids を明示指定する。"
        )
    else:
        scope_note = (
            "explicit: 呼び出し側が明示指定した audit scope ちょうどで集計。"
            "空スコープは0社監査を意味する（既定スコープにフォールバックしない）。"
        )
    scope = {
        "mode": scope_mode,
        "count": audit_target_shrines,
        "total_db_shrines": total_db_shrines,
        "outside_scope_count": excluded_test_shrines,
        "resolved_in_db": resolved_in_db,
        "note": scope_note,
    }

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
        # 後方互換キー。値は「対象スコープ件数」。scope.mode が qa_filtered_db の
        # ときは canonical unique-real-shrine denominator **ではない**
        # （scope メタデータ参照）。
        "audit_target_shrines": audit_target_shrines,
        "excluded_test_shrines": excluded_test_shrines,
        "scope": scope,
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
