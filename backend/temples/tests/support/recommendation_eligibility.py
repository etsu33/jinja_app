"""Shared Recommendation Eligibility 用のtest helper。

`build_chat_candidates()` のShared Recommendation Eligibility gateは
「usable Deity Fact または usable History Fact が少なくとも1件」を要求する。
そのため、Recommendation候補として登場させたいtest ShrineにはKnowledge Factを
1件付与する必要がある。

usableの条件そのものはここで再定義せず、
`temples.services.evidence_gate.decide_fact_usability()` が要求する形
（Fact自身がfact-ready かつ fact-ready Sourceを1件以上Relation）を素直に組み立てる。
"""

from __future__ import annotations

from django.utils import timezone

from temples.models import ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services import evidence_gate

FACT_READY_STATUS = evidence_gate.FACT_READY_VERIFICATION_STATUSES[0]


def create_fact_ready_source(title: str = "適格出典") -> ShrineKnowledgeSource:
    return ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title=title,
        verification_status=FACT_READY_STATUS,
        verified_at=timezone.now(),
    )


def attach_usable_deity_fact(
    shrine,
    *,
    display_name: str = "適格祭神",
    confidence: str = "high",
    source: ShrineKnowledgeSource | None = None,
) -> ShrineDeity:
    """RecommendationのEligibilityを満たすusable Deity Factを1件付与する。"""
    deity = ShrineDeity.objects.create(
        shrine=shrine,
        display_name=display_name,
        sort_order=0,
        verification_status=FACT_READY_STATUS,
        confidence=confidence,
        verified_at=timezone.now(),
    )
    deity.sources.add(source or create_fact_ready_source())
    return deity


def attach_usable_history_fact(
    shrine,
    *,
    title: str = "適格由緒",
    content: str = "Recommendation eligibilityを満たす由緒。",
    confidence: str = "high",
    source: ShrineKnowledgeSource | None = None,
) -> ShrineHistory:
    """RecommendationのEligibilityを満たすusable History Factを1件付与する。"""
    history = ShrineHistory.objects.create(
        shrine=shrine,
        history_type="official_origin",
        title=title,
        content=content,
        sort_order=0,
        verification_status=FACT_READY_STATUS,
        confidence=confidence,
        verified_at=timezone.now(),
    )
    history.sources.add(source or create_fact_ready_source())
    return history


__all__ = [
    "FACT_READY_STATUS",
    "attach_usable_deity_fact",
    "attach_usable_history_fact",
    "create_fact_ready_source",
]
