# backend/temples/tests/test_domain_evidence_provenance.py
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from temples.domain.evidence_provenance import (
    EVIDENCE_MECHANISMS,
    EVIDENCE_PRODUCERS,
    build_evidence_provenance,
    is_valid_evidence_mechanism,
    is_valid_evidence_producer,
)


def test_producers_match_mother_ship_final_values():
    assert EVIDENCE_PRODUCERS == [
        "admin",
        "curator",
        "migration",
        "verified_import",
        "controlled_automation",
    ]


def test_mechanisms_match_mother_ship_final_v1_values():
    assert EVIDENCE_MECHANISMS == [
        "manual_review",
        "source_backed_import",
        "verified_migration",
        "controlled_rule",
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("admin", True),
        ("curator", True),
        ("migration", True),
        ("verified_import", True),
        ("controlled_automation", True),
        ("human", False),
        ("system", False),
        ("ai", False),
        ("unknown", False),
        ("", False),
        (None, False),
        (123, False),
    ],
)
def test_is_valid_evidence_producer(value, expected):
    assert is_valid_evidence_producer(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("manual_review", True),
        ("source_backed_import", True),
        ("verified_migration", True),
        ("controlled_rule", True),
        ("admin_manual", False),
        ("import_script", False),
        ("import", False),
        ("unknown", False),
        ("", False),
        (None, False),
    ],
)
def test_is_valid_evidence_mechanism(value, expected):
    assert is_valid_evidence_mechanism(value) is expected


def test_build_evidence_provenance_valid():
    assigned_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = build_evidence_provenance(
        producer="admin",
        mechanism="manual_review",
        assigned_at=assigned_at,
    )
    assert result.valid is True
    assert result.provenance is not None
    assert result.provenance.producer == "admin"
    assert result.provenance.mechanism == "manual_review"
    assert result.provenance.assigned_at == assigned_at


@pytest.mark.parametrize(
    ("producer", "mechanism"),
    [
        ("migration", "verified_migration"),
        ("verified_import", "source_backed_import"),
        ("controlled_automation", "controlled_rule"),
    ],
)
def test_build_evidence_provenance_accepts_mother_ship_example_combinations(producer, mechanism):
    result = build_evidence_provenance(
        producer=producer,
        mechanism=mechanism,
        assigned_at=datetime.now(timezone.utc),
    )
    assert result.valid is True
    assert result.provenance.producer == producer
    assert result.provenance.mechanism == mechanism


def test_build_evidence_provenance_rejects_invalid_producer():
    result = build_evidence_provenance(
        producer="ai",
        mechanism="manual_review",
        assigned_at=datetime.now(timezone.utc),
    )
    assert result.valid is False
    assert result.provenance is None
    assert "invalid_producer" in result.reason


def test_build_evidence_provenance_rejects_invalid_mechanism():
    result = build_evidence_provenance(
        producer="admin",
        mechanism="unknown_mechanism",
        assigned_at=datetime.now(timezone.utc),
    )
    assert result.valid is False
    assert result.provenance is None
    assert "invalid_mechanism" in result.reason


def test_build_evidence_provenance_rejects_non_datetime_assigned_at():
    result = build_evidence_provenance(
        producer="admin",
        mechanism="manual_review",
        assigned_at="2026-01-01",
    )
    assert result.valid is False
    assert result.provenance is None
    assert "invalid_assigned_at" in result.reason


def test_valid_provenance_does_not_by_itself_imply_qualification():
    """A valid producer/mechanism combination is one candidate input toward
    the `provenance_satisfied` dimension only -- it must never, by itself,
    make EvidenceQualification return qualified=True. Qualification still
    requires all five dimensions (evidence_qualification.py)."""
    from temples.domain.evidence_qualification import (
        EvidenceQualificationInput,
        evaluate_evidence_qualification,
    )

    provenance_result = build_evidence_provenance(
        producer="migration",
        mechanism="verified_migration",
        assigned_at=datetime.now(timezone.utc),
    )
    assert provenance_result.valid is True

    qualification_result = evaluate_evidence_qualification(
        EvidenceQualificationInput(
            identifiable=False,
            taxonomy_stable=False,
            provenance_satisfied=True,
            semantic_assignment_traceable=False,
            transport_traceable=False,
        )
    )
    assert qualification_result.qualified is False
    assert "provenance_satisfied" not in qualification_result.unmet_dimensions
