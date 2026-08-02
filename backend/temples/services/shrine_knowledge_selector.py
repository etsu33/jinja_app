"""Recommendation専用のKnowledge読み取りselector。

docs/knowledge/shrine-knowledge-contract.md「Fact利用条件」に従い、
ShrineDeity / ShrineHistoryのうちFact利用可能なものだけをRecommendation入力向けの
最小dictへ変換する。利用可否の判定そのもの（Fact自身のverification_status +
Relation済みSourceのverification_status）はtemples.services.evidence_gateへ委譲し、
本モジュールでは判定条件をSQLへ再実装しない。

このモジュールの責務は「候補Factの取得（N+1を発生させない）」に限定し、
「Factを使えるか判断する」責務はevidence_gate.decide_fact_usability()に一本化する。
これによりRecommendationとShrine Detail（temples/api/serializers/shrine.py）が
同一のEvidence Gate判定を共有する。

DRF Serializer/ViewとRecommendation内部契約を混在させないため、
temples.api配下（Serializer/View）には一切依存しない。
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from django.db.models import Prefetch
from temples.models import ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services import evidence_gate


def _fact_ready_sources_prefetch() -> Prefetch:
    return Prefetch(
        "sources",
        queryset=ShrineKnowledgeSource.objects.filter(
            verification_status__in=evidence_gate.FACT_READY_VERIFICATION_STATUSES
        ),
    )


def fetch_fact_ready_knowledge_deities(
    shrine_ids: list[int],
) -> dict[int, list[dict[str, Any]]]:
    """対象shrine_ids分のFact-ready ShrineDeityを、shrine_id単位でまとめて取得する。

    候補（Fact自身のverification_statusがfact-ready）をshrine_ids一括で1クエリ取得し、
    Sourceをまとめてprefetchする（合計2クエリ、対象Shrine数に関わらず一定）。
    usable判定自体はevidence_gate.decide_fact_usability()で行う。
    """
    if not shrine_ids:
        return {}

    candidates = (
        ShrineDeity.objects.filter(
            shrine_id__in=shrine_ids,
            verification_status__in=evidence_gate.FACT_READY_VERIFICATION_STATUSES,
        )
        .order_by("sort_order", "id")
        .prefetch_related(_fact_ready_sources_prefetch())
    )

    result: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for deity in candidates:
        decision = evidence_gate.decide_fact_usability(
            verification_status=deity.verification_status,
            confidence=deity.confidence,
            source_verification_statuses=(s.verification_status for s in deity.sources.all()),
        )
        if not decision.usable:
            continue
        result[deity.shrine_id].append(
            {
                "display_name": deity.display_name,
                "sort_order": deity.sort_order,
                "confidence": deity.confidence,
            }
        )
    return dict(result)


def fetch_fact_ready_knowledge_histories(
    shrine_ids: list[int],
) -> dict[int, list[dict[str, Any]]]:
    """対象shrine_ids分のFact-ready ShrineHistoryを、shrine_id単位でまとめて取得する。

    候補（Fact自身のverification_statusがfact-ready）をshrine_ids一括で1クエリ取得し、
    Sourceをまとめてprefetchする（合計2クエリ、対象Shrine数に関わらず一定）。
    usable判定自体はevidence_gate.decide_fact_usability()で行う。
    """
    if not shrine_ids:
        return {}

    candidates = (
        ShrineHistory.objects.filter(
            shrine_id__in=shrine_ids,
            verification_status__in=evidence_gate.FACT_READY_VERIFICATION_STATUSES,
        )
        .order_by("sort_order", "id")
        .prefetch_related(_fact_ready_sources_prefetch())
    )

    result: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for history in candidates:
        decision = evidence_gate.decide_fact_usability(
            verification_status=history.verification_status,
            confidence=history.confidence,
            source_verification_statuses=(s.verification_status for s in history.sources.all()),
        )
        if not decision.usable:
            continue
        result[history.shrine_id].append(
            {
                "history_type": history.history_type,
                "title": history.title,
                "content": history.content,
                "period_text": history.period_text,
                "sort_order": history.sort_order,
                "confidence": history.confidence,
            }
        )
    return dict(result)


__all__ = [
    "fetch_fact_ready_knowledge_deities",
    "fetch_fact_ready_knowledge_histories",
]
