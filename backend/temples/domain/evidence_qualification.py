# backend/temples/domain/evidence_qualification.py
"""Evidence Foundation PR-F1: EvidenceQualification shared contract.

「Evidenceとして採用可能か」の判定結果を、単なるboolではなく将来拡張可能な
明示的contractとして扱う。ここで定義する5次元・判定ロジックは、Mother Ship
承認済みのShared Evidence Foundation Contract v1をそのまま実装したもので、
新しい判定基準を追加してはいない。

重要（Mother Ship確定事項）:
    semantic value exists != Qualified Evidence
    Qualified Evidence != Relationship Origin ALLOW

この契約はEvidenceが「qualifiedかどうか」だけを判定する。Relationship Origin
としての採否・Recommendationへの接続は、本モジュールの責務外（PR-F1では未接続）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

# EvidenceQualification契約そのもののバージョン。taxonomy versionや
# assignmentのschema versionとは別物 -- 「qualified/not qualifiedの
# 判定基準自体がいつ変わったか」を追跡するための、この契約固有のバージョン。
EVIDENCE_QUALIFICATION_CONTRACT_VERSION = 1

SUPPORTED_EVIDENCE_QUALIFICATION_CONTRACT_VERSIONS = frozenset(
    {EVIDENCE_QUALIFICATION_CONTRACT_VERSION}
)

# Shared Evidence Foundation Contract v1の5次元。
# Mother Ship指定のcamelCase (identifiable / taxonomyStable /
# provenanceSatisfied / semanticAssignmentTraceable / transportTraceable)
# を、既存repositoryのPython側命名規約（snake_case、例: history_theme）に
# 合わせてそのまま1:1で変換したのみで、意味・数・順序は変更していない。
_QUALIFICATION_DIMENSIONS: Tuple[str, ...] = (
    "identifiable",
    "taxonomy_stable",
    "provenance_satisfied",
    "semantic_assignment_traceable",
    "transport_traceable",
)


@dataclass(frozen=True)
class EvidenceQualificationInput:
    """5次元の入力値。真偽値以外が渡された場合はinvalid inputとして扱う
    （F1-2のinvalid input境界）。"""

    identifiable: Any
    taxonomy_stable: Any
    provenance_satisfied: Any
    semantic_assignment_traceable: Any
    transport_traceable: Any

    def as_dimension_dict(self) -> Dict[str, Any]:
        return {
            "identifiable": self.identifiable,
            "taxonomy_stable": self.taxonomy_stable,
            "provenance_satisfied": self.provenance_satisfied,
            "semantic_assignment_traceable": self.semantic_assignment_traceable,
            "transport_traceable": self.transport_traceable,
        }


@dataclass(frozen=True)
class EvidenceQualificationResult:
    """判定結果contract。qualified/not qualifiedをboolだけで返さず、
    decision reasonとqualification versionを常に伴わせる。"""

    qualified: bool
    reason: str
    qualification_version: int
    unmet_dimensions: Tuple[str, ...]


def evaluate_evidence_qualification(
    qualification_input: EvidenceQualificationInput,
    *,
    qualification_version: int = EVIDENCE_QUALIFICATION_CONTRACT_VERSION,
) -> EvidenceQualificationResult:
    """5次元すべてがTrueの場合のみqualified=Trueを返す、pure deterministic
    判定。同じ入力に対して常に同じ結果を返す -- LLM/random/現在時刻/DB状態/
    外部APIへの依存は一切持たない。

    3つの境界:
      - unsupported input: qualification_versionが未対応版の場合、
        5次元の中身を見ずに一律reject（将来この契約自体が改版された場合の
        後方互換境界）。
      - invalid input: 5次元のいずれかがbool型でない場合、reject
        （型不正はqualifiedかどうかの判定以前の問題として扱う）。
      - valid input: 5次元すべてがbool型の場合のみ、値そのものを判定する。
    """
    if qualification_version not in SUPPORTED_EVIDENCE_QUALIFICATION_CONTRACT_VERSIONS:
        return EvidenceQualificationResult(
            qualified=False,
            reason=(
                f"unsupported_qualification_version: {qualification_version!r} is not "
                f"a supported EvidenceQualification contract version"
            ),
            qualification_version=qualification_version,
            unmet_dimensions=tuple(_QUALIFICATION_DIMENSIONS),
        )

    dimension_values = qualification_input.as_dimension_dict()

    invalid_type_dimensions = tuple(
        name
        for name in _QUALIFICATION_DIMENSIONS
        if not isinstance(dimension_values[name], bool)
    )
    if invalid_type_dimensions:
        return EvidenceQualificationResult(
            qualified=False,
            reason=(
                "invalid_input: the following dimensions are not bool: "
                + ", ".join(invalid_type_dimensions)
            ),
            qualification_version=qualification_version,
            unmet_dimensions=invalid_type_dimensions,
        )

    unmet_dimensions = tuple(
        name for name in _QUALIFICATION_DIMENSIONS if dimension_values[name] is not True
    )

    if unmet_dimensions:
        return EvidenceQualificationResult(
            qualified=False,
            reason="not_qualified: unmet dimensions: " + ", ".join(unmet_dimensions),
            qualification_version=qualification_version,
            unmet_dimensions=unmet_dimensions,
        )

    return EvidenceQualificationResult(
        qualified=True,
        reason="qualified: all required dimensions satisfied",
        qualification_version=qualification_version,
        unmet_dimensions=(),
    )


__all__ = [
    "EVIDENCE_QUALIFICATION_CONTRACT_VERSION",
    "SUPPORTED_EVIDENCE_QUALIFICATION_CONTRACT_VERSIONS",
    "EvidenceQualificationInput",
    "EvidenceQualificationResult",
    "evaluate_evidence_qualification",
]
