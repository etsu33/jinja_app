"""Evidence Foundation PR-F4 qualification preparation orchestration。

F4は4 dimensionの準備までを行う。transport_traceable、最終
EvidenceQualificationInput、evaluate_evidence_qualification()はF4境界の外
（PR-F5 ``temples.services.evidence_transport``）にある。このmoduleは
Evaluatorをimportしない。

PR-F5では、F4とF5が同じFoundation DB stateを二重取得しないよう、このmoduleの
内部を materialization（``materialize_evidence_snapshot``）と
evaluation（``evaluate_f4_from_snapshot``）へ分離した。
``prepare_f4_qualification()`` はその2つを順に呼ぶだけであり、既存利用者から
見た公開挙動は変更していない。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.db.models import Prefetch
from temples.domain.evidence_link import (
    GORIYAKU_ASSIGNMENT,
    HISTORY_THEME_ASSIGNMENT,
    SHRINE_DEITY,
    SHRINE_HISTORY,
    EvidenceLinkSnapshot,
    FactSourceQualitySnapshot,
    FactSourceQualityStatus,
    evaluate_linked_facts_quality,
    evidence_link_structural_issues,
    semantic_assignment_traceable,
)
from temples.domain.evidence_provenance import build_evidence_provenance
from temples.domain.evidence_taxonomy import get_current_taxonomy_version
from temples.domain.goriyaku_taxonomy_v1 import (
    GORIYAKU_TAXONOMY_NAMESPACE,
    validate_goriyaku_v1_canonical_key,
)
from temples.domain.history_theme_taxonomy_v1 import (
    HISTORY_THEME_TAXONOMY_NAMESPACE,
    validate_history_theme_v1_canonical_key,
)
from temples.models import (
    EvidenceLink,
    HistoryThemeAssignment,
    ShrineGoriyakuAssignment,
    ShrineKnowledgeSource,
)


@dataclass(frozen=True)
class F4DimensionPreparation:
    identifiable: bool
    taxonomy_stable: bool
    provenance_satisfied: bool
    semantic_assignment_traceable: bool


@dataclass(frozen=True)
class F4QualificationPreparation:
    assignment_model: str | None
    assignment_id: object | None
    lifecycle_prerequisite: bool
    structural_prerequisite: bool
    fact_source_quality_prerequisite: FactSourceQualityStatus
    dimensions: F4DimensionPreparation
    build_blocked: bool
    block_reasons: Tuple[str, ...]
    structural_issues: Tuple[str, ...]


class EvidenceSnapshotStatus(str, Enum):
    """authoritative snapshotの成立状態。"""

    UNSUPPORTED_ASSIGNMENT_MODEL = "UNSUPPORTED_ASSIGNMENT_MODEL"
    NOT_PERSISTED = "NOT_PERSISTED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    MATERIALIZED = "MATERIALIZED"


@dataclass(frozen=True)
class AuthoritativeEvidenceSnapshot:
    """1回のinvocationにつき1度だけmaterializeされるFoundation DB stateの写し。

    ``assignment`` はcallerから渡されたinstanceではなく、type + persistent PKで
    再resolveしたcurrent DB rowである。``caller_assignment`` は、まだ永続化
    されていないobjectについてのみ（DB rowが存在しないため）参照する。

    このsnapshotはF4 evaluation・F5 normalization・Transport Integrity
    verificationで共有され、同一invocation内で再取得されることはない。
    """

    status: EvidenceSnapshotStatus
    assignment_model: str | None
    assignment_id: object | None
    caller_assignment: object
    assignment: object | None
    links: Tuple[EvidenceLink, ...]


def _unsupported_preparation(reason: str) -> F4QualificationPreparation:
    return F4QualificationPreparation(
        assignment_model=None,
        assignment_id=None,
        lifecycle_prerequisite=False,
        structural_prerequisite=False,
        fact_source_quality_prerequisite=FactSourceQualityStatus.NOT_APPLICABLE,
        dimensions=F4DimensionPreparation(
            identifiable=False,
            taxonomy_stable=False,
            provenance_satisfied=False,
            semantic_assignment_traceable=False,
        ),
        build_blocked=True,
        block_reasons=(reason,),
        structural_issues=(),
    )


def _assignment_contract(assignment):
    if type(assignment) is HistoryThemeAssignment:
        return (
            HISTORY_THEME_ASSIGNMENT,
            HistoryThemeAssignment.Lifecycle.ACTIVE,
            validate_history_theme_v1_canonical_key,
            HISTORY_THEME_TAXONOMY_NAMESPACE,
        )
    if type(assignment) is ShrineGoriyakuAssignment:
        return (
            GORIYAKU_ASSIGNMENT,
            ShrineGoriyakuAssignment.Lifecycle.ACTIVE,
            validate_goriyaku_v1_canonical_key,
            GORIYAKU_TAXONOMY_NAMESPACE,
        )
    return None


def _resolved_relation(link: EvidenceLink, field_name: str):
    try:
        return getattr(link, field_name)
    except ObjectDoesNotExist:
        return None


def _snapshot(link: EvidenceLink) -> EvidenceLinkSnapshot:
    assignment_fields = (
        ("history_theme_assignment", HISTORY_THEME_ASSIGNMENT),
        ("goriyaku_assignment", GORIYAKU_ASSIGNMENT),
    )
    fact_fields = (
        ("shrine_history", SHRINE_HISTORY),
        ("shrine_deity", SHRINE_DEITY),
    )
    selected_assignments = [
        (field_name, model_name)
        for field_name, model_name in assignment_fields
        if getattr(link, f"{field_name}_id") is not None
    ]
    selected_facts = [
        (field_name, model_name)
        for field_name, model_name in fact_fields
        if getattr(link, f"{field_name}_id") is not None
    ]

    assignment_field, assignment_model = (
        selected_assignments[0] if len(selected_assignments) == 1 else (None, None)
    )
    fact_field, fact_model = selected_facts[0] if len(selected_facts) == 1 else (None, None)
    assignment = _resolved_relation(link, assignment_field) if assignment_field else None
    fact = _resolved_relation(link, fact_field) if fact_field else None

    return EvidenceLinkSnapshot(
        link_id=link.pk,
        assignment_selector_count=len(selected_assignments),
        assignment_model=assignment_model,
        assignment_id=getattr(link, f"{assignment_field}_id") if assignment_field else None,
        assignment_shrine_id=getattr(assignment, "shrine_id", None),
        assignment_resolved=assignment is not None,
        fact_selector_count=len(selected_facts),
        fact_model=fact_model,
        fact_id=getattr(link, f"{fact_field}_id") if fact_field else None,
        fact_shrine_id=getattr(fact, "shrine_id", None),
        fact_resolved=fact is not None,
        rationale=link.rationale,
    )


def _fact_quality_snapshot(link: EvidenceLink) -> FactSourceQualitySnapshot | None:
    fact = None
    if link.shrine_history_id is not None and link.shrine_deity_id is None:
        fact = _resolved_relation(link, "shrine_history")
    elif link.shrine_deity_id is not None and link.shrine_history_id is None:
        fact = _resolved_relation(link, "shrine_deity")
    if fact is None:
        return None
    # sourcesはmaterialization時にpk ASCでprefetch済み。ここで再queryしない
    # （F4とF5がEvidence graphを二重取得しないための共有snapshot契約）。
    source_statuses = tuple(source.verification_status for source in fact.sources.all())
    return FactSourceQualitySnapshot(
        verification_status=fact.verification_status,
        source_verification_statuses=source_statuses,
    )


def _link_queryset(assignment):
    """EvidenceLinkのcomplete setをpk ASCで取得するqueryset。

    Fact -> Sourceはcomplete M2M setをpk ASCでprefetchする。verification_status
    等によるfilterは行わない（ready Sourceだけを運ぶことは禁止）。
    """

    source_queryset = ShrineKnowledgeSource.objects.order_by("pk")
    return (
        assignment.evidence_links.select_related(
            "history_theme_assignment",
            "goriyaku_assignment",
            "shrine_history",
            "shrine_deity",
        )
        .prefetch_related(
            Prefetch("shrine_history__sources", queryset=source_queryset),
            Prefetch("shrine_deity__sources", queryset=source_queryset),
        )
        .order_by("pk")
    )


def materialize_evidence_snapshot(assignment: object) -> AuthoritativeEvidenceSnapshot:
    """Foundation DB stateを1回だけmaterializeし、immutable snapshotを返す。

    callerから渡されたmodel instanceのfield値は正本として信用せず、
    type + persistent PKでcurrent DB rowを再resolveする。新しいtransaction
    isolation levelやDB lock policyは導入しない。
    """

    contract = _assignment_contract(assignment)
    if contract is None:
        return AuthoritativeEvidenceSnapshot(
            status=EvidenceSnapshotStatus.UNSUPPORTED_ASSIGNMENT_MODEL,
            assignment_model=None,
            assignment_id=None,
            caller_assignment=assignment,
            assignment=None,
            links=(),
        )

    assignment_model = contract[0]
    assignment_id = assignment.pk
    try:
        current = (
            type(assignment).objects.filter(pk=assignment_id).first()
            if assignment_id is not None
            else None
        )
        if current is None:
            return AuthoritativeEvidenceSnapshot(
                status=EvidenceSnapshotStatus.NOT_PERSISTED,
                assignment_model=assignment_model,
                assignment_id=assignment_id,
                caller_assignment=assignment,
                assignment=None,
                links=(),
            )
        links = tuple(_link_queryset(current))
    except (DatabaseError, ObjectDoesNotExist):
        return AuthoritativeEvidenceSnapshot(
            status=EvidenceSnapshotStatus.PROVIDER_UNAVAILABLE,
            assignment_model=assignment_model,
            assignment_id=assignment_id,
            caller_assignment=assignment,
            assignment=None,
            links=(),
        )

    return AuthoritativeEvidenceSnapshot(
        status=EvidenceSnapshotStatus.MATERIALIZED,
        assignment_model=assignment_model,
        assignment_id=assignment_id,
        caller_assignment=assignment,
        assignment=current,
        links=links,
    )


def _not_persisted_preparation(
    snapshot: AuthoritativeEvidenceSnapshot, active_lifecycle
) -> F4QualificationPreparation:
    return F4QualificationPreparation(
        assignment_model=snapshot.assignment_model,
        assignment_id=snapshot.assignment_id,
        lifecycle_prerequisite=snapshot.caller_assignment.lifecycle == active_lifecycle,
        structural_prerequisite=True,
        fact_source_quality_prerequisite=FactSourceQualityStatus.NOT_APPLICABLE,
        dimensions=F4DimensionPreparation(
            identifiable=False,
            taxonomy_stable=False,
            provenance_satisfied=False,
            semantic_assignment_traceable=False,
        ),
        build_blocked=True,
        block_reasons=("assignment_not_persisted",),
        structural_issues=(),
    )


def _provider_unavailable_preparation(
    snapshot: AuthoritativeEvidenceSnapshot,
) -> F4QualificationPreparation:
    result = _unsupported_preparation("required_provider_unavailable")
    return F4QualificationPreparation(
        assignment_model=snapshot.assignment_model,
        assignment_id=snapshot.assignment_id,
        lifecycle_prerequisite=False,
        structural_prerequisite=False,
        fact_source_quality_prerequisite=result.fact_source_quality_prerequisite,
        dimensions=result.dimensions,
        build_blocked=True,
        block_reasons=result.block_reasons,
        structural_issues=(),
    )


def evaluate_f4_from_snapshot(
    snapshot: AuthoritativeEvidenceSnapshot,
) -> F4QualificationPreparation:
    """materialize済みのauthoritative snapshotだけからF4を評価する。

    この関数はDBを再取得しない。F5 orchestrationは同じsnapshotを渡すことで、
    F4とF5がEvidence graphを別々にmaterializeしないことを保証する。
    """

    if snapshot.status is EvidenceSnapshotStatus.UNSUPPORTED_ASSIGNMENT_MODEL:
        return _unsupported_preparation("unsupported_assignment_model")

    contract = _assignment_contract(snapshot.caller_assignment)
    assignment_model, active_lifecycle, taxonomy_validator, taxonomy_namespace = contract

    if snapshot.status is EvidenceSnapshotStatus.NOT_PERSISTED:
        return _not_persisted_preparation(snapshot, active_lifecycle)
    if snapshot.status is EvidenceSnapshotStatus.PROVIDER_UNAVAILABLE:
        return _provider_unavailable_preparation(snapshot)

    assignment = snapshot.assignment
    assignment_id = snapshot.assignment_id
    links = snapshot.links
    snapshots = tuple(_snapshot(link) for link in links)
    quality_snapshots = tuple(
        item
        for item in (_fact_quality_snapshot(link) for link in links)
        if item is not None
    )

    structural_issues = tuple(
        issue for item in snapshots for issue in evidence_link_structural_issues(item)
    )
    edge_keys = tuple(
        (item.assignment_model, item.assignment_id, item.fact_model, item.fact_id)
        for item in snapshots
    )
    duplicate_edge = len(edge_keys) != len(set(edge_keys))
    structural_prerequisite = not structural_issues and not duplicate_edge
    quality = evaluate_linked_facts_quality(quality_snapshots)

    taxonomy_validation = taxonomy_validator(assignment.canonical_key)
    taxonomy_stable = (
        taxonomy_validation.valid
        and assignment.taxonomy_version == get_current_taxonomy_version(taxonomy_namespace).version
    )
    provenance_satisfied = build_evidence_provenance(
        producer=assignment.producer,
        mechanism=assignment.mechanism,
        assigned_at=assignment.assigned_at,
    ).valid
    traceable = semantic_assignment_traceable(
        assignment_model=assignment_model,
        assignment_id=assignment_id,
        links=snapshots,
    )
    lifecycle_prerequisite = assignment.lifecycle == active_lifecycle

    block_reasons = []
    if not lifecycle_prerequisite:
        block_reasons.append("non_active_assignment")
    if structural_issues:
        block_reasons.append("invalid_evidence_link_structure")
    if any(issue == "cross_shrine_or_unresolved_shrine" for issue in structural_issues):
        block_reasons.append("cross_shrine")
    if duplicate_edge:
        block_reasons.append("duplicate_edge")
    if quality is FactSourceQualityStatus.BLOCK:
        block_reasons.append("fact_source_quality_failed")

    return F4QualificationPreparation(
        assignment_model=assignment_model,
        assignment_id=assignment_id,
        lifecycle_prerequisite=lifecycle_prerequisite,
        structural_prerequisite=structural_prerequisite,
        fact_source_quality_prerequisite=quality,
        dimensions=F4DimensionPreparation(
            identifiable=True,
            taxonomy_stable=taxonomy_stable,
            provenance_satisfied=provenance_satisfied,
            semantic_assignment_traceable=traceable,
        ),
        build_blocked=bool(block_reasons),
        block_reasons=tuple(block_reasons),
        structural_issues=structural_issues,
    )


def prepare_f4_qualification(assignment: object) -> F4QualificationPreparation:
    """Supported Assignment 1件についてF4の前提と4 dimensionを準備する。"""

    return evaluate_f4_from_snapshot(materialize_evidence_snapshot(assignment))


__all__ = [
    "AuthoritativeEvidenceSnapshot",
    "EvidenceSnapshotStatus",
    "F4DimensionPreparation",
    "F4QualificationPreparation",
    "evaluate_f4_from_snapshot",
    "materialize_evidence_snapshot",
    "prepare_f4_qualification",
]
