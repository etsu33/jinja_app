# backend/temples/domain/evidence_provenance.py
"""Evidence Foundation PR-F1: Producer / Mechanism / Provenance contracts.

producer と mechanism は責務が異なる。
    producer  : 誰 / 何が生成したか
    mechanism : どの管理された処理（controlled process）によって
                assignmentが作られたか
この2つを混ぜない。

member候補はMother Ship FINAL値をそのまま実装したものであり、
既存`ShrineKnowledgeSource.SOURCE_TYPE_CHOICES`等から再推論・簡略化
していない。格納形式（stored machine representation）のみ、本
repositoryの既存命名規約（lowercase snake_case: 例
`CONSULTATION_AXES`の"money_growth"、`SOURCE_TYPE_CHOICES`の
"shrine_official"）に合わせた -- 意味・数・責務はMother Ship FINAL値
と1:1で対応する。

Producer（Mother Ship FINAL）:
    ADMIN                 -> "admin"
    CURATOR                -> "curator"
    MIGRATION               -> "migration"
    VERIFIED_IMPORT          -> "verified_import"
    CONTROLLED_AUTOMATION     -> "controlled_automation"

Mechanism（Mother Ship FINAL v1）:
    MANUAL_REVIEW            -> "manual_review"
    SOURCE_BACKED_IMPORT       -> "source_backed_import"
    VERIFIED_MIGRATION          -> "verified_migration"
    CONTROLLED_RULE               -> "controlled_rule"

想定される組み合わせ例（Mother Ship提示）:
    MIGRATION + VERIFIED_MIGRATION
    VERIFIED_IMPORT + SOURCE_BACKED_IMPORT
    CONTROLLED_AUTOMATION + CONTROLLED_RULE

重要: これらの組み合わせは、それだけでEvidenceQualificationの
qualified=Trueを意味しない。qualificationは引き続き5次元すべてを
要求する（evidence_qualification.py）。producer/mechanismの組み合わせ
は`provenance_satisfied`という1次元への入力候補になり得るだけで、
本モジュールはqualification判定そのものには関与しない。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

EvidenceProducer = str

# Mother Ship FINAL: ADMIN / CURATOR / MIGRATION / VERIFIED_IMPORT /
# CONTROLLED_AUTOMATION の5値。格納表現のみsnake_case化。
EVIDENCE_PRODUCERS: List[EvidenceProducer] = [
    "admin",
    "curator",
    "migration",
    "verified_import",
    "controlled_automation",
]
EVIDENCE_PRODUCER_SET = set(EVIDENCE_PRODUCERS)


EvidenceMechanism = str

# Mother Ship FINAL v1: MANUAL_REVIEW / SOURCE_BACKED_IMPORT /
# VERIFIED_MIGRATION / CONTROLLED_RULE の4値。格納表現のみsnake_case化。
EVIDENCE_MECHANISMS: List[EvidenceMechanism] = [
    "manual_review",
    "source_backed_import",
    "verified_migration",
    "controlled_rule",
]
EVIDENCE_MECHANISM_SET = set(EVIDENCE_MECHANISMS)


def is_valid_evidence_producer(value: object) -> bool:
    return isinstance(value, str) and value in EVIDENCE_PRODUCER_SET


def is_valid_evidence_mechanism(value: object) -> bool:
    return isinstance(value, str) and value in EVIDENCE_MECHANISM_SET


@dataclass(frozen=True)
class EvidenceProvenance:
    """F1-8: Evidence assignmentで共通利用できるprovenance contract。

    重要: これはpure Python dataclassであり、Django modelではない
    （PR-F1ではDB model化しない。migration責務を一切持たない）。
    F2/F3で実際のDB modelを設計する際、この形（producer / mechanism /
    assigned_at）をfieldとして再利用することを想定しているが、その
    DB化自体はこのPRのscope外。

    assigned_atは呼び出し側が明示的に渡す（このcontract自身は
    datetime.now()等の現在時刻に依存しない）。qualification判定
    （evidence_qualification.py）が現在時刻に依存しないのと同じ理由で、
    provenance構築自体も暗黙の時刻取得を持たない。
    """

    producer: EvidenceProducer
    mechanism: EvidenceMechanism
    assigned_at: datetime


@dataclass(frozen=True)
class EvidenceProvenanceBuildResult:
    provenance: Optional[EvidenceProvenance]
    valid: bool
    reason: str


def build_evidence_provenance(
    *,
    producer: object,
    mechanism: object,
    assigned_at: object,
) -> EvidenceProvenanceBuildResult:
    """producer / mechanism / assigned_atを検証したうえでEvidenceProvenance
    を構築する。無効な値が渡された場合は例外を投げず、
    EvidenceProvenanceBuildResult(valid=False, ...)を返す -- 呼び出し側が
    分岐処理をtry/exceptなしで書けるようにするため（既存の
    evidence_qualification.evaluate_evidence_qualification()と同じ
    設計方針）。

    producer/mechanismの組み合わせがMother Ship提示の想定例（例:
    MIGRATION + VERIFIED_MIGRATION）と一致するかどうかは検証しない --
    v1では両者とも独立した許可済み値であればよく、組み合わせの妥当性
    チェックはこのPRのscope外（将来必要になった場合は別途Mother Ship
    決定）。
    """
    if not is_valid_evidence_producer(producer):
        return EvidenceProvenanceBuildResult(
            provenance=None,
            valid=False,
            reason=f"invalid_producer: {producer!r} is not one of {EVIDENCE_PRODUCERS}",
        )

    if not is_valid_evidence_mechanism(mechanism):
        return EvidenceProvenanceBuildResult(
            provenance=None,
            valid=False,
            reason=f"invalid_mechanism: {mechanism!r} is not one of {EVIDENCE_MECHANISMS}",
        )

    if not isinstance(assigned_at, datetime):
        return EvidenceProvenanceBuildResult(
            provenance=None,
            valid=False,
            reason=f"invalid_assigned_at: {assigned_at!r} is not a datetime",
        )

    return EvidenceProvenanceBuildResult(
        provenance=EvidenceProvenance(
            producer=producer,
            mechanism=mechanism,
            assigned_at=assigned_at,
        ),
        valid=True,
        reason="valid",
    )


__all__ = [
    "EVIDENCE_PRODUCERS",
    "EVIDENCE_PRODUCER_SET",
    "EVIDENCE_MECHANISMS",
    "EVIDENCE_MECHANISM_SET",
    "is_valid_evidence_producer",
    "is_valid_evidence_mechanism",
    "EvidenceProvenance",
    "EvidenceProvenanceBuildResult",
    "build_evidence_provenance",
]
