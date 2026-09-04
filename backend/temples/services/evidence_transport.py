"""Evidence Foundation PR-F5 normalization / Transport Integrity / final qualification。

責務境界:

* ``temples.domain.evidence_transport`` -- normalized transport immutable types、
  canonical serializer、pure Transport Integrity predicate（DB非依存）。
* ``temples.services.evidence_foundation`` -- F4 materialization / evaluation
  のみ。Evaluatorをimportしない（F4境界）。
* 本module -- single authoritative snapshot orchestration、そのsnapshotからの
  F4 evaluation、normalized_evidence生成、Transport Integrity評価、
  F5NormalizationResult、final 5 dimension assembly、official
  ``evaluate_evidence_qualification()`` 呼び出し。

このmoduleはDBへ書き込まない。欠損補完・推論・repair・legacy fallbackは行わず、
不足や不整合はBUILD BLOCKまたはtransport issueとしてそのまま表面化させる。
Recommendation / Ranking / Concierge / Compassへは接続しない。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Tuple

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from temples.domain.evidence_link import (
    GORIYAKU_ASSIGNMENT,
    HISTORY_THEME_ASSIGNMENT,
    SHRINE_DEITY,
    SHRINE_HISTORY,
)
from temples.domain.evidence_qualification import (
    EvidenceQualificationInput,
    EvidenceQualificationResult,
    evaluate_evidence_qualification,
)
from temples.domain.evidence_transport import (
    NormalizedAssignmentRefV1,
    NormalizedAssignmentV1,
    NormalizedEvidenceLinkV1,
    NormalizedEvidenceV1,
    NormalizedFactV1,
    NormalizedProvenanceV1,
    NormalizedShrineDeityPayloadV1,
    NormalizedShrineHistoryPayloadV1,
    NormalizedSourceV1,
    NormalizedTaxonomyV1,
    TransportIntegrityIssue,
    TransportSerializationError,
    canonical_date,
    canonical_datetime,
    serialize_normalized_evidence,
    verify_transport_integrity,
)
from temples.domain.goriyaku_taxonomy_v1 import GORIYAKU_TAXONOMY_NAMESPACE
from temples.domain.history_theme_taxonomy_v1 import HISTORY_THEME_TAXONOMY_NAMESPACE
from temples.services.evidence_foundation import (
    F4QualificationPreparation,
    evaluate_f4_from_snapshot,
    materialize_evidence_snapshot,
)

INVALID_TRANSPORT_DATETIME = "invalid_transport_datetime"
REQUIRED_DIMENSION_PROVIDER_INVALID = "required_dimension_provider_invalid"
REQUIRED_PROVIDER_UNAVAILABLE = "required_provider_unavailable"

_TAXONOMY_NAMESPACE_BY_ASSIGNMENT_MODEL = {
    HISTORY_THEME_ASSIGNMENT: HISTORY_THEME_TAXONOMY_NAMESPACE,
    GORIYAKU_ASSIGNMENT: GORIYAKU_TAXONOMY_NAMESPACE,
}


class TransportProviderError(ValueError):
    """normalized transportに必要なprimitiveが提供されなかった場合に送出する。

    値を補完せずfail-closedし、呼び出し側がBUILD BLOCKへ変換する。
    """


@dataclass(frozen=True)
class F5NormalizationResult:
    f4_preparation: F4QualificationPreparation
    normalized_evidence: NormalizedEvidenceV1 | None
    transport_traceable: bool | None
    transport_issues: Tuple[TransportIntegrityIssue, ...]
    build_blocked: bool
    block_reasons: Tuple[str, ...]


class FinalQualificationStatus(str, Enum):
    BLOCKED = "BLOCKED"
    EVALUATED = "EVALUATED"


@dataclass(frozen=True)
class EvidenceQualificationOutcome:
    """BLOCKEDとNOT QUALIFIEDを取り違えないためのimmutable orchestration result。

    ``qualified`` を第二の正本fieldとして持たない。正本は
    ``qualification_result.qualified`` のみ。
    """

    status: FinalQualificationStatus
    build_blocked: bool
    block_reasons: Tuple[str, ...]
    qualification_input: EvidenceQualificationInput | None
    qualification_result: EvidenceQualificationResult | None


def _require_str(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise TransportProviderError(f"{REQUIRED_DIMENSION_PROVIDER_INVALID}: {path}")
    return value


def _require_ident(value: Any, path: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TransportProviderError(f"{REQUIRED_DIMENSION_PROVIDER_INVALID}: {path}")
    return value


def _normalized_source(source: object) -> NormalizedSourceV1:
    return NormalizedSourceV1(
        id=_require_ident(source.pk, "source.id"),
        source_type=_require_str(source.source_type, "source.sourceType"),
        title=_require_str(source.title, "source.title"),
        publisher=_require_str(source.publisher, "source.publisher"),
        url=_require_str(source.url, "source.url"),
        bibliography=_require_str(source.bibliography, "source.bibliography"),
        accessed_at=canonical_date(source.accessed_at),
        verified_at=canonical_datetime(source.verified_at),
        verification_status=_require_str(
            source.verification_status, "source.verificationStatus"
        ),
        confidence=_require_str(source.confidence, "source.confidence"),
        language=_require_str(source.language, "source.language"),
    )


def _normalized_history_payload(fact: object) -> NormalizedShrineHistoryPayloadV1:
    return NormalizedShrineHistoryPayloadV1(
        history_type=_require_str(fact.history_type, "fact.payload.historyType"),
        title=_require_str(fact.title, "fact.payload.title"),
        content=_require_str(fact.content, "fact.payload.content"),
        period_text=_require_str(fact.period_text, "fact.payload.periodText"),
        event_date=canonical_date(fact.event_date),
    )


def _normalized_deity_payload(fact: object) -> NormalizedShrineDeityPayloadV1:
    return NormalizedShrineDeityPayloadV1(
        display_name=_require_str(fact.display_name, "fact.payload.displayName"),
        canonical_name=_require_str(fact.canonical_name, "fact.payload.canonicalName"),
        role=_require_str(fact.role, "fact.payload.role"),
    )


def _resolved_fact(link: object) -> Tuple[str, object]:
    """EvidenceLinkのFact selectorをtyped identityへ解決する。

    F4 structural prerequisiteを通過したLinkだけがここへ到達する。selectorが
    1つに定まらない場合は補正せずfail-closedする。
    """

    if link.shrine_history_id is not None and link.shrine_deity_id is None:
        return SHRINE_HISTORY, link.shrine_history
    if link.shrine_deity_id is not None and link.shrine_history_id is None:
        return SHRINE_DEITY, link.shrine_deity
    raise TransportProviderError(f"{REQUIRED_DIMENSION_PROVIDER_INVALID}: link.fact")


def _normalized_fact(fact_model: str, fact: object) -> NormalizedFactV1:
    if fact is None:
        raise TransportProviderError(f"{REQUIRED_DIMENSION_PROVIDER_INVALID}: link.fact")
    payload = (
        _normalized_history_payload(fact)
        if fact_model == SHRINE_HISTORY
        else _normalized_deity_payload(fact)
    )
    # sourcesはmaterialization時にpk ASCでprefetch済みのcomplete set。
    # verification_status等でfilterせず、draft Sourceも削除しない。
    sources = tuple(_normalized_source(source) for source in fact.sources.all())
    return NormalizedFactV1(
        type=fact_model,
        id=_require_ident(fact.pk, "fact.id"),
        shrine_id=_require_ident(fact.shrine_id, "fact.shrineId"),
        verification_status=_require_str(fact.verification_status, "fact.verificationStatus"),
        confidence=_require_str(fact.confidence, "fact.confidence"),
        verified_at=canonical_datetime(fact.verified_at),
        payload=payload,
        sources=sources,
    )


def _normalized_assignment(assignment_model: str, assignment: object) -> NormalizedAssignmentV1:
    namespace = _TAXONOMY_NAMESPACE_BY_ASSIGNMENT_MODEL.get(assignment_model)
    if namespace is None:
        raise TransportProviderError(
            f"{REQUIRED_DIMENSION_PROVIDER_INVALID}: assignment.taxonomy.namespace"
        )
    return NormalizedAssignmentV1(
        type=assignment_model,
        id=_require_ident(assignment.pk, "assignment.id"),
        shrine_id=_require_ident(assignment.shrine_id, "assignment.shrineId"),
        canonical_key=_require_str(assignment.canonical_key, "assignment.canonicalKey"),
        taxonomy=NormalizedTaxonomyV1(
            namespace=namespace,
            taxonomy_version=_require_str(
                assignment.taxonomy_version, "assignment.taxonomy.taxonomyVersion"
            ),
        ),
        lifecycle=_require_str(assignment.lifecycle, "assignment.lifecycle"),
        provenance=NormalizedProvenanceV1(
            producer=_require_str(assignment.producer, "assignment.provenance.producer"),
            mechanism=_require_str(assignment.mechanism, "assignment.provenance.mechanism"),
            assigned_at=canonical_datetime(assignment.assigned_at),
        ),
    )


def build_normalized_evidence(snapshot) -> NormalizedEvidenceV1:
    """authoritative snapshotからnormalized_evidence v1を組み立てる。

    DBを再取得せず、書き込みも行わない。EvidenceLinkはsnapshotが保持する
    complete set（pk ASC）をそのまま運ぶ。
    """

    assignment_model = snapshot.assignment_model
    assignment = _normalized_assignment(assignment_model, snapshot.assignment)
    assignment_ref = NormalizedAssignmentRefV1(type=assignment.type, id=assignment.id)
    links = []
    for link in snapshot.links:
        fact_model, fact = _resolved_fact(link)
        links.append(
            NormalizedEvidenceLinkV1(
                id=_require_ident(link.pk, "link.id"),
                assignment_ref=assignment_ref,
                rationale=_require_str(link.rationale, "link.rationale"),
                fact=_normalized_fact(fact_model, fact),
            )
        )
    return NormalizedEvidenceV1(assignment=assignment, evidence_links=tuple(links))


def _blocked_normalization(
    f4_preparation: F4QualificationPreparation, block_reasons: Tuple[str, ...]
) -> F5NormalizationResult:
    return F5NormalizationResult(
        f4_preparation=f4_preparation,
        normalized_evidence=None,
        transport_traceable=None,
        transport_issues=(),
        build_blocked=True,
        block_reasons=block_reasons,
    )


def normalize_evidence_transport(assignment: object) -> F5NormalizationResult:
    """1 invocation = 1 authoritative snapshotで、F4準備とF5 transportを揃える。"""

    snapshot = materialize_evidence_snapshot(assignment)
    f4_preparation = evaluate_f4_from_snapshot(snapshot)
    if f4_preparation.build_blocked:
        # F4 block reasonはrename・隠蔽・qualified=Falseへの変換をせずそのまま運ぶ。
        return _blocked_normalization(f4_preparation, f4_preparation.block_reasons)

    try:
        normalized = build_normalized_evidence(snapshot)
    except TransportSerializationError:
        return _blocked_normalization(
            f4_preparation, f4_preparation.block_reasons + (INVALID_TRANSPORT_DATETIME,)
        )
    except TransportProviderError:
        return _blocked_normalization(
            f4_preparation,
            f4_preparation.block_reasons + (REQUIRED_DIMENSION_PROVIDER_INVALID,),
        )
    except (DatabaseError, ObjectDoesNotExist):
        return _blocked_normalization(
            f4_preparation, f4_preparation.block_reasons + (REQUIRED_PROVIDER_UNAVAILABLE,)
        )

    integrity = verify_transport_integrity(
        authoritative=normalized,
        candidate=serialize_normalized_evidence(normalized),
    )
    return F5NormalizationResult(
        f4_preparation=f4_preparation,
        normalized_evidence=normalized,
        transport_traceable=integrity.transport_traceable,
        transport_issues=integrity.issues,
        build_blocked=False,
        block_reasons=(),
    )


def build_final_qualification(
    normalization: F5NormalizationResult,
) -> EvidenceQualificationOutcome:
    """F5NormalizationResultだけを入力とするfinal qualification orchestration。

    DBを再取得せず、dimensionを再計算しない。BUILD BLOCK時はEvaluatorを
    呼ばない（BLOCKED != NOT QUALIFIED）。
    """

    if normalization.build_blocked:
        return EvidenceQualificationOutcome(
            status=FinalQualificationStatus.BLOCKED,
            build_blocked=True,
            block_reasons=normalization.block_reasons,
            qualification_input=None,
            qualification_result=None,
        )

    dimensions = normalization.f4_preparation.dimensions
    qualification_input = EvidenceQualificationInput(
        identifiable=dimensions.identifiable,
        taxonomy_stable=dimensions.taxonomy_stable,
        provenance_satisfied=dimensions.provenance_satisfied,
        semantic_assignment_traceable=dimensions.semantic_assignment_traceable,
        transport_traceable=normalization.transport_traceable,
    )
    qualification_result = evaluate_evidence_qualification(qualification_input)
    return EvidenceQualificationOutcome(
        status=FinalQualificationStatus.EVALUATED,
        build_blocked=False,
        block_reasons=(),
        qualification_input=qualification_input,
        qualification_result=qualification_result,
    )


def qualify_evidence(assignment: object) -> EvidenceQualificationOutcome:
    """official F5 path。Assignment 1件をnormalizeし、5次元を1:1でassemblyする。"""

    return build_final_qualification(normalize_evidence_transport(assignment))


__all__ = [
    "INVALID_TRANSPORT_DATETIME",
    "REQUIRED_DIMENSION_PROVIDER_INVALID",
    "REQUIRED_PROVIDER_UNAVAILABLE",
    "EvidenceQualificationOutcome",
    "F5NormalizationResult",
    "FinalQualificationStatus",
    "TransportProviderError",
    "build_final_qualification",
    "build_normalized_evidence",
    "normalize_evidence_transport",
    "qualify_evidence",
]
