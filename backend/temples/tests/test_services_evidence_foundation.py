from __future__ import annotations

from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

import pytest
from django.db import DatabaseError

from temples.domain.evidence_link import FactSourceQualityStatus
from temples.models import (
    EvidenceLink,
    HistoryThemeAssignment,
    Shrine,
    ShrineDeity,
    ShrineHistory,
    ShrineKnowledgeSource,
)
from temples.services import evidence_foundation
from temples.services.evidence_foundation import prepare_f4_qualification

pytestmark = pytest.mark.django_db


def _shrine(name: str = "F4準備神社") -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )


def _assignment(shrine: Shrine, **overrides) -> HistoryThemeAssignment:
    values = dict(
        shrine=shrine,
        canonical_key="history_theme:restart",
        taxonomy_version="v1",
        lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=datetime(2026, 1, 1, tzinfo=dt_timezone.utc),
    )
    values.update(overrides)
    return HistoryThemeAssignment.objects.create(**values)


def _source(status: str = "reviewed") -> ShrineKnowledgeSource:
    return ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title=f"{status}出典",
        verification_status=status,
    )


def _history(shrine: Shrine, status: str = "reviewed") -> ShrineHistory:
    fact = ShrineHistory.objects.create(
        shrine=shrine,
        history_type="official_origin",
        title="由緒",
        content="根拠となる由緒。",
        verification_status=status,
        confidence="low",
    )
    return fact


def _deity(shrine: Shrine, status: str = "source_confirmed") -> ShrineDeity:
    return ShrineDeity.objects.create(
        shrine=shrine,
        display_name="天照大神",
        verification_status=status,
        confidence="low",
    )


def test_active_valid_links_and_all_quality_pass_prepare_four_dimensions():
    shrine = _shrine()
    assignment = _assignment(shrine)
    history = _history(shrine)
    deity = _deity(shrine)
    ready_source = _source()
    history.sources.add(ready_source)
    deity.sources.add(ready_source)
    EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_history=history,
        rationale="由緒が再出発を裏付ける。",
    )
    EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_deity=deity,
        rationale="祭神が再出発を裏付ける。",
    )

    result = prepare_f4_qualification(assignment)

    assert result.lifecycle_prerequisite is True
    assert result.structural_prerequisite is True
    assert result.fact_source_quality_prerequisite is FactSourceQualityStatus.PASS
    assert result.dimensions.identifiable is True
    assert result.dimensions.taxonomy_stable is True
    assert result.dimensions.provenance_satisfied is True
    assert result.dimensions.semantic_assignment_traceable is True
    assert result.build_blocked is False


def test_non_active_assignment_is_build_blocked_but_evidence_is_retained():
    shrine = _shrine()
    assignment = _assignment(shrine, lifecycle=HistoryThemeAssignment.Lifecycle.SUPERSEDED)
    history = _history(shrine)
    history.sources.add(_source())
    link = EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_history=history,
        rationale="履歴用の根拠。",
    )

    result = prepare_f4_qualification(assignment)

    assert result.build_blocked is True
    assert result.block_reasons == ("non_active_assignment",)
    assert EvidenceLink.objects.filter(pk=link.pk).exists()


def test_zero_links_is_not_structural_corruption_or_fake_quality_pass():
    result = prepare_f4_qualification(_assignment(_shrine()))

    assert result.structural_prerequisite is True
    assert result.fact_source_quality_prerequisite is FactSourceQualityStatus.NOT_APPLICABLE
    assert result.dimensions.semantic_assignment_traceable is False
    assert result.build_blocked is False


def test_quality_failure_blocks_whole_assignment_without_filtering_bad_fact():
    shrine = _shrine()
    assignment = _assignment(shrine)
    good = _history(shrine)
    bad = _deity(shrine, status="draft")
    good.sources.add(_source("reviewed"))
    bad.sources.add(_source("reviewed"))
    EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_history=good,
        rationale="ready Factの根拠。",
    )
    EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_deity=bad,
        rationale="draft Factもsilent filterしない。",
    )

    result = prepare_f4_qualification(assignment)

    assert result.fact_source_quality_prerequisite is FactSourceQualityStatus.BLOCK
    assert "fact_source_quality_failed" in result.block_reasons
    assert result.dimensions.semantic_assignment_traceable is True


def test_cross_shrine_corruption_is_revalidated_and_build_blocked():
    assignment_shrine = _shrine("Assignment神社")
    fact_shrine = _shrine("Fact神社")
    assignment = _assignment(assignment_shrine)
    history = _history(fact_shrine)
    history.sources.add(_source())
    with patch.object(EvidenceLink, "full_clean"):
        EvidenceLink.objects.create(
            history_theme_assignment=assignment,
            shrine_history=history,
            rationale="DBだけではsame-shrineを保証しない。",
        )

    result = prepare_f4_qualification(assignment)

    assert result.structural_prerequisite is False
    assert "cross_shrine" in result.block_reasons
    assert result.build_blocked is True


def test_duplicate_edge_guard_blocks_even_if_provider_returns_corrupt_duplicates(monkeypatch):
    shrine = _shrine()
    assignment = _assignment(shrine)
    history = _history(shrine)
    deity = _deity(shrine)
    source = _source()
    history.sources.add(source)
    deity.sources.add(source)
    EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_history=history,
        rationale="1つ目。",
    )
    EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_deity=deity,
        rationale="2つ目。",
    )
    original_snapshot = evidence_foundation._snapshot
    first_snapshot = None

    def duplicate_second(link):
        nonlocal first_snapshot
        snapshot = original_snapshot(link)
        if first_snapshot is None:
            first_snapshot = snapshot
            return snapshot
        return first_snapshot

    monkeypatch.setattr(evidence_foundation, "_snapshot", duplicate_second)

    result = prepare_f4_qualification(assignment)

    assert result.build_blocked is True
    assert "duplicate_edge" in result.block_reasons


def test_dimension_false_is_preserved_separately_from_build_block():
    assignment = _assignment(
        _shrine(),
        taxonomy_version="v999",
        producer="invalid_producer",
    )

    result = prepare_f4_qualification(assignment)

    assert result.build_blocked is False
    assert result.dimensions.identifiable is True
    assert result.dimensions.taxonomy_stable is False
    assert result.dimensions.provenance_satisfied is False
    assert result.dimensions.semantic_assignment_traceable is False


def test_unsupported_assignment_model_is_build_blocked():
    result = prepare_f4_qualification(_shrine())
    assert result.build_blocked is True
    assert result.block_reasons == ("unsupported_assignment_model",)


def test_required_provider_unavailable_is_build_blocked():
    assignment = _assignment(_shrine())
    with patch.object(
        HistoryThemeAssignment.objects,
        "filter",
        side_effect=DatabaseError("provider unavailable"),
    ):
        result = prepare_f4_qualification(assignment)

    assert result.build_blocked is True
    assert result.block_reasons == ("required_provider_unavailable",)


def test_f4_boundary_has_no_transport_or_final_qualification_evaluation():
    result = prepare_f4_qualification(_assignment(_shrine()))

    assert not hasattr(result.dimensions, "transport_traceable")
    assert not hasattr(evidence_foundation, "EvidenceQualificationInput")
    assert not hasattr(evidence_foundation, "evaluate_evidence_qualification")
