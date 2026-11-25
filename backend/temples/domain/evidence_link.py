"""Evidence Foundation PR-F4のDB非依存predicate。

このモジュールはsnapshotだけを評価し、DB・現在時刻・外部APIへ依存しない。
ORMからsnapshotを組み立てる責務は ``temples.services.evidence_foundation`` に置く。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Tuple

HISTORY_THEME_ASSIGNMENT = "HistoryThemeAssignment"
GORIYAKU_ASSIGNMENT = "ShrineGoriyakuAssignment"
SHRINE_HISTORY = "ShrineHistory"
SHRINE_DEITY = "ShrineDeity"

SUPPORTED_ASSIGNMENT_MODELS = frozenset({HISTORY_THEME_ASSIGNMENT, GORIYAKU_ASSIGNMENT})
SUPPORTED_FACT_MODELS = frozenset({SHRINE_HISTORY, SHRINE_DEITY})
SUPPORTED_EVIDENCE_LINK_PAIRS = frozenset(
    (assignment_model, fact_model)
    for assignment_model in SUPPORTED_ASSIGNMENT_MODELS
    for fact_model in SUPPORTED_FACT_MODELS
)


@dataclass(frozen=True)
class EvidenceLinkSnapshot:
    """Predicate入力。relation解決とDB取得の結果を値として固定したもの。"""

    link_id: object | None
    assignment_selector_count: int
    assignment_model: str | None
    assignment_id: object | None
    assignment_shrine_id: object | None
    assignment_resolved: bool
    fact_selector_count: int
    fact_model: str | None
    fact_id: object | None
    fact_shrine_id: object | None
    fact_resolved: bool
    rationale: object


def evidence_link_structural_issues(snapshot: EvidenceLinkSnapshot) -> Tuple[str, ...]:
    """Evidence Link structural validityの違反理由を安定した順序で返す。"""

    issues = []
    if snapshot.link_id is None:
        issues.append("missing_link_identity")
    if snapshot.assignment_selector_count != 1:
        issues.append("assignment_not_exactly_one")
    if snapshot.fact_selector_count != 1:
        issues.append("fact_not_exactly_one")
    if (snapshot.assignment_model, snapshot.fact_model) not in SUPPORTED_EVIDENCE_LINK_PAIRS:
        issues.append("unsupported_model_pair")
    if not snapshot.assignment_resolved or snapshot.assignment_id is None:
        issues.append("assignment_unresolved")
    if not snapshot.fact_resolved or snapshot.fact_id is None:
        issues.append("fact_unresolved")
    if (
        snapshot.assignment_shrine_id is None
        or snapshot.fact_shrine_id is None
        or snapshot.assignment_shrine_id != snapshot.fact_shrine_id
    ):
        issues.append("cross_shrine_or_unresolved_shrine")
    if not isinstance(snapshot.rationale, str):
        issues.append("rationale_not_string")
    elif not snapshot.rationale.strip():
        issues.append("rationale_blank")
    return tuple(issues)


def is_evidence_link_structurally_valid(snapshot: EvidenceLinkSnapshot) -> bool:
    """C-1 allowlistを含むF4 structural validity predicate。"""

    return not evidence_link_structural_issues(snapshot)


@dataclass(frozen=True)
class FactSourceQualitySnapshot:
    verification_status: object
    source_verification_statuses: Tuple[object, ...]


class FactSourceQualityStatus(str, Enum):
    PASS = "PASS"
    BLOCK = "BLOCK"
    NOT_APPLICABLE = "NOT_APPLICABLE"


def is_fact_source_quality_satisfied(
    snapshot: FactSourceQualitySnapshot,
) -> bool:
    """Fact ready AND ready Sourceが最低1件、だけを判定する共通predicate。"""

    # Local importでmodels -> domainのimport cycleを避けつつ、ready値は既存正本だけを使う。
    from temples.models import KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES

    ready = frozenset(KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES)
    return snapshot.verification_status in ready and any(
        status in ready for status in snapshot.source_verification_statuses
    )


def evaluate_linked_facts_quality(
    snapshots: Iterable[FactSourceQualitySnapshot],
) -> FactSourceQualityStatus:
    """linked Fact全件を評価する。0件はPASSではなくNOT_APPLICABLE。"""

    materialized = tuple(snapshots)
    if not materialized:
        return FactSourceQualityStatus.NOT_APPLICABLE
    if all(is_fact_source_quality_satisfied(snapshot) for snapshot in materialized):
        return FactSourceQualityStatus.PASS
    return FactSourceQualityStatus.BLOCK


def semantic_assignment_traceable(
    *,
    assignment_model: str,
    assignment_id: object | None,
    links: Iterable[EvidenceLinkSnapshot],
) -> bool:
    """exact Assignment × Fact edge上の永続rationaleを全Linkで確認する。"""

    materialized = tuple(links)
    if assignment_model not in SUPPORTED_ASSIGNMENT_MODELS or assignment_id is None:
        return False
    if not materialized:
        return False

    for link in materialized:
        if link.link_id is None:
            return False
        if link.assignment_selector_count != 1 or link.fact_selector_count != 1:
            return False
        if link.assignment_model != assignment_model or link.assignment_id != assignment_id:
            return False
        if link.fact_model not in SUPPORTED_FACT_MODELS or link.fact_id is None:
            return False
        if not isinstance(link.rationale, str) or not link.rationale.strip():
            return False
    return True


__all__ = [
    "HISTORY_THEME_ASSIGNMENT",
    "GORIYAKU_ASSIGNMENT",
    "SHRINE_HISTORY",
    "SHRINE_DEITY",
    "SUPPORTED_ASSIGNMENT_MODELS",
    "SUPPORTED_FACT_MODELS",
    "SUPPORTED_EVIDENCE_LINK_PAIRS",
    "EvidenceLinkSnapshot",
    "FactSourceQualitySnapshot",
    "FactSourceQualityStatus",
    "evidence_link_structural_issues",
    "is_evidence_link_structurally_valid",
    "is_fact_source_quality_satisfied",
    "evaluate_linked_facts_quality",
    "semantic_assignment_traceable",
]
