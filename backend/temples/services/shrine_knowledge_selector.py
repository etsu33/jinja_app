"""Recommendation専用のKnowledge読み取りselector。

docs/knowledge/shrine-knowledge-contract.md「Fact利用条件」に従い、
ShrineDeity / ShrineHistoryのうちFact利用可能なもの
（verification_status in KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES、かつ
 fact-readyなShrineKnowledgeSourceを1件以上持つもの）だけをRecommendation
入力向けの最小dictへ変換する。

DRF Serializer/ViewとRecommendation内部契約を混在させないため、
temples.api配下（Serializer/View）には一切依存しない。
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from temples.models import (
    KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES,
    ShrineDeity,
    ShrineHistory,
)


def fetch_fact_ready_knowledge_deities(
    shrine_ids: list[int],
) -> dict[int, list[dict[str, Any]]]:
    """対象shrine_ids分のFact-ready ShrineDeityを、shrine_id単位でまとめて取得する。

    N+1回避のため、対象Shrine数に関わらず1クエリのみ発行する。
    """
    if not shrine_ids:
        return {}

    rows = (
        ShrineDeity.objects.filter(
            shrine_id__in=shrine_ids,
            verification_status__in=KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES,
            sources__verification_status__in=KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES,
        )
        .order_by("sort_order", "id")
        .values("id", "shrine_id", "display_name", "sort_order", "confidence")
    )

    result: dict[int, list[dict[str, Any]]] = defaultdict(list)
    seen_ids: set[int] = set()
    for row in rows:
        # sources__verification_status__inのJOINにより、fact-ready Sourceを
        # 複数持つDeityは行が重複し得るため、id単位で重複排除する。
        if row["id"] in seen_ids:
            continue
        seen_ids.add(row["id"])
        result[row["shrine_id"]].append(
            {
                "display_name": row["display_name"],
                "sort_order": row["sort_order"],
                "confidence": row["confidence"],
            }
        )
    return dict(result)


def fetch_fact_ready_knowledge_histories(
    shrine_ids: list[int],
) -> dict[int, list[dict[str, Any]]]:
    """対象shrine_ids分のFact-ready ShrineHistoryを、shrine_id単位でまとめて取得する。

    N+1回避のため、対象Shrine数に関わらず1クエリのみ発行する。
    """
    if not shrine_ids:
        return {}

    rows = (
        ShrineHistory.objects.filter(
            shrine_id__in=shrine_ids,
            verification_status__in=KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES,
            sources__verification_status__in=KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES,
        )
        .order_by("sort_order", "id")
        .values(
            "id",
            "shrine_id",
            "history_type",
            "title",
            "content",
            "period_text",
            "sort_order",
            "confidence",
        )
    )

    result: dict[int, list[dict[str, Any]]] = defaultdict(list)
    seen_ids: set[int] = set()
    for row in rows:
        if row["id"] in seen_ids:
            continue
        seen_ids.add(row["id"])
        result[row["shrine_id"]].append(
            {
                "history_type": row["history_type"],
                "title": row["title"],
                "content": row["content"],
                "period_text": row["period_text"],
                "sort_order": row["sort_order"],
                "confidence": row["confidence"],
            }
        )
    return dict(result)


__all__ = [
    "fetch_fact_ready_knowledge_deities",
    "fetch_fact_ready_knowledge_histories",
]
