from __future__ import annotations

from dataclasses import replace

import pytest

from temples.domain.evidence_link import (
    HISTORY_THEME_ASSIGNMENT,
    SHRINE_DEITY,
    SHRINE_HISTORY,
    EvidenceLinkSnapshot,
    FactSourceQualitySnapshot,
    FactSourceQualityStatus,
    evaluate_linked_facts_quality,
    is_evidence_link_structurally_valid,
    is_fact_source_quality_satisfied,
    semantic_assignment_traceable,
)
from temples.models import KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES


def _link(**overrides) -> EvidenceLinkSnapshot:
    values = dict(
        link_id=1,
        assignment_selector_count=1,
        assignment_model=HISTORY_THEME_ASSIGNMENT,
        assignment_id=10,
        assignment_shrine_id=100,
        assignment_resolved=True,
        fact_selector_count=1,
        fact_model=SHRINE_HISTORY,
        fact_id=20,
        fact_shrine_id=100,
        fact_resolved=True,
        rationale="由緒の記述がこのthemeを直接裏付ける。",
    )
    values.update(overrides)
    return EvidenceLinkSnapshot(**values)


def test_structural_predicate_accepts_supported_persisted_same_shrine_edge():
    assert is_evidence_link_structurally_valid(_link()) is True


@pytest.mark.parametrize(
    "overrides",
    [
        {"link_id": None},
        {"assignment_selector_count": 0},
        {"assignment_selector_count": 2},
        {"fact_selector_count": 0},
        {"fact_selector_count": 2},
        {"assignment_model": "Shrine"},
        {"fact_model": "ShrineKnowledgeSource"},
        {"assignment_resolved": False},
        {"fact_resolved": False},
        {"fact_shrine_id": 101},
        {"rationale": None},
        {"rationale": " \n\t"},
    ],
)
def test_structural_predicate_fails_closed_for_each_invalid_condition(overrides):
    assert is_evidence_link_structurally_valid(_link(**overrides)) is False


@pytest.mark.parametrize(
    "fact_status,source_status",
    [(status, status) for status in KNOWLEDGE_FACT_READY_VERIFICATION_STATUSES],
)
def test_common_quality_accepts_ready_fact_with_ready_source(fact_status, source_status):
    snapshot = FactSourceQualitySnapshot(
        verification_status=fact_status,
        source_verification_statuses=("draft", source_status),
    )
    assert is_fact_source_quality_satisfied(snapshot)


@pytest.mark.parametrize(
    "fact_status,source_statuses",
    [
        ("draft", ("reviewed",)),
        ("disputed", ("reviewed",)),
        ("reviewed", ()),
        ("reviewed", ("draft",)),
    ],
)
def test_common_quality_rejects_nonready_fact_or_missing_ready_source(fact_status, source_statuses):
    assert not is_fact_source_quality_satisfied(
        FactSourceQualitySnapshot(fact_status, source_statuses)
    )


def test_linked_fact_quality_requires_every_fact_and_zero_is_not_applicable():
    passing = FactSourceQualitySnapshot("reviewed", ("source_confirmed",))
    failing = FactSourceQualitySnapshot("draft", ("reviewed",))

    assert evaluate_linked_facts_quality(()) is FactSourceQualityStatus.NOT_APPLICABLE
    assert evaluate_linked_facts_quality((passing,)) is FactSourceQualityStatus.PASS
    assert evaluate_linked_facts_quality((passing, failing)) is FactSourceQualityStatus.BLOCK


def test_common_quality_has_no_confidence_input_and_low_confidence_does_not_change_result():
    snapshot = FactSourceQualitySnapshot("reviewed", ("reviewed",))
    assert is_fact_source_quality_satisfied(snapshot)


def test_semantic_traceability_zero_one_and_multiple_link_contract():
    link = _link()
    second = replace(link, link_id=2, fact_model=SHRINE_DEITY, fact_id=21)

    assert not semantic_assignment_traceable(
        assignment_model=HISTORY_THEME_ASSIGNMENT,
        assignment_id=10,
        links=(),
    )
    assert semantic_assignment_traceable(
        assignment_model=HISTORY_THEME_ASSIGNMENT,
        assignment_id=10,
        links=(link,),
    )
    assert semantic_assignment_traceable(
        assignment_model=HISTORY_THEME_ASSIGNMENT,
        assignment_id=10,
        links=(link, second),
    )


@pytest.mark.parametrize(
    "invalid_link",
    [
        _link(link_id=None),
        _link(assignment_id=11),
        _link(fact_id=None),
        _link(rationale=""),
        _link(rationale=" \n"),
    ],
)
def test_semantic_traceability_rejects_nonpersistent_or_unrationalized_exact_edge(invalid_link):
    assert not semantic_assignment_traceable(
        assignment_model=HISTORY_THEME_ASSIGNMENT,
        assignment_id=10,
        links=(invalid_link,),
    )


def test_semantic_traceability_does_not_mix_same_shrine_or_quality_into_its_meaning():
    cross_shrine = _link(fact_shrine_id=999)
    assert semantic_assignment_traceable(
        assignment_model=HISTORY_THEME_ASSIGNMENT,
        assignment_id=10,
        links=(cross_shrine,),
    )
