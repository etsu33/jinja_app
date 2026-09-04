"""Evidence Foundation PR-F4 qualification preparation orchestration。

F4は4 dimensionの準備までを行う。transport_traceable、最終
EvidenceQualificationInput、evaluate_evidence_qualification()はF5境界の外にある。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
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
from temples.models import EvidenceLink, HistoryThemeAssignment, ShrineGoriyakuAssignment


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
    source_statuses = tuple(
        fact.sources.order_by("pk").values_list("verification_status", flat=True)
    )
    return FactSourceQualitySnapshot(
        verification_status=fact.verification_status,
        source_verification_statuses=source_statuses,
    )


def prepare_f4_qualification(assignment: object) -> F4QualificationPreparation:
    """Supported Assignment 1件についてF4の前提と4 dimensionを準備する。"""

    contract = _assignment_contract(assignment)
    if contract is None:
        return _unsupported_preparation("unsupported_assignment_model")

    assignment_model, active_lifecycle, taxonomy_validator, taxonomy_namespace = contract
    assignment_id = assignment.pk
    try:
        persisted = (
            assignment_id is not None and type(assignment).objects.filter(pk=assignment_id).exists()
        )
        if not persisted:
            return F4QualificationPreparation(
                assignment_model=assignment_model,
                assignment_id=assignment_id,
                lifecycle_prerequisite=assignment.lifecycle == active_lifecycle,
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

        links = tuple(
            assignment.evidence_links.select_related(
                "history_theme_assignment",
                "goriyaku_assignment",
                "shrine_history",
                "shrine_deity",
            ).order_by("pk")
        )
        snapshots = tuple(_snapshot(link) for link in links)
        quality_snapshots = tuple(
            snapshot
            for snapshot in (_fact_quality_snapshot(link) for link in links)
            if snapshot is not None
        )
    except (DatabaseError, ObjectDoesNotExist):
        result = _unsupported_preparation("required_provider_unavailable")
        return F4QualificationPreparation(
            assignment_model=assignment_model,
            assignment_id=assignment_id,
            lifecycle_prerequisite=False,
            structural_prerequisite=False,
            fact_source_quality_prerequisite=result.fact_source_quality_prerequisite,
            dimensions=result.dimensions,
            build_blocked=True,
            block_reasons=result.block_reasons,
            structural_issues=(),
        )

    structural_issues = tuple(
        issue for snapshot in snapshots for issue in evidence_link_structural_issues(snapshot)
    )
    edge_keys = tuple(
        (snapshot.assignment_model, snapshot.assignment_id, snapshot.fact_model, snapshot.fact_id)
        for snapshot in snapshots
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


__all__ = [
    "F4DimensionPreparation",
    "F4QualificationPreparation",
    "prepare_f4_qualification",
]
