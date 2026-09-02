# backend/temples/tests/test_domain_evidence_qualification.py
from __future__ import annotations

import pytest

from temples.domain.evidence_qualification import (
    EVIDENCE_QUALIFICATION_CONTRACT_VERSION,
    EvidenceQualificationInput,
    evaluate_evidence_qualification,
)


def _all_true() -> EvidenceQualificationInput:
    return EvidenceQualificationInput(
        identifiable=True,
        taxonomy_stable=True,
        provenance_satisfied=True,
        semantic_assignment_traceable=True,
        transport_traceable=True,
    )


def test_qualified_when_all_five_dimensions_true():
    result = evaluate_evidence_qualification(_all_true())
    assert result.qualified is True
    assert result.unmet_dimensions == ()
    assert result.qualification_version == EVIDENCE_QUALIFICATION_CONTRACT_VERSION


@pytest.mark.parametrize(
    "field_to_flip",
    [
        "identifiable",
        "taxonomy_stable",
        "provenance_satisfied",
        "semantic_assignment_traceable",
        "transport_traceable",
    ],
)
def test_rejected_when_any_single_dimension_false(field_to_flip):
    values = {
        "identifiable": True,
        "taxonomy_stable": True,
        "provenance_satisfied": True,
        "semantic_assignment_traceable": True,
        "transport_traceable": True,
    }
    values[field_to_flip] = False
    result = evaluate_evidence_qualification(EvidenceQualificationInput(**values))
    assert result.qualified is False
    assert result.unmet_dimensions == (field_to_flip,)


def test_rejected_when_all_five_dimensions_false():
    result = evaluate_evidence_qualification(
        EvidenceQualificationInput(
            identifiable=False,
            taxonomy_stable=False,
            provenance_satisfied=False,
            semantic_assignment_traceable=False,
            transport_traceable=False,
        )
    )
    assert result.qualified is False
    assert len(result.unmet_dimensions) == 5


def test_deterministic_same_input_same_result():
    input_value = _all_true()
    first = evaluate_evidence_qualification(input_value)
    second = evaluate_evidence_qualification(input_value)
    assert first == second


def test_invalid_input_non_bool_dimension_is_rejected_not_raised():
    result = evaluate_evidence_qualification(
        EvidenceQualificationInput(
            identifiable="yes",  # not a bool
            taxonomy_stable=True,
            provenance_satisfied=True,
            semantic_assignment_traceable=True,
            transport_traceable=True,
        )
    )
    assert result.qualified is False
    assert "invalid_input" in result.reason
    assert result.unmet_dimensions == ("identifiable",)


def test_invalid_input_none_dimension_is_rejected():
    result = evaluate_evidence_qualification(
        EvidenceQualificationInput(
            identifiable=True,
            taxonomy_stable=None,
            provenance_satisfied=True,
            semantic_assignment_traceable=True,
            transport_traceable=True,
        )
    )
    assert result.qualified is False
    assert "invalid_input" in result.reason


def test_unsupported_qualification_version_is_rejected():
    result = evaluate_evidence_qualification(_all_true(), qualification_version=999)
    assert result.qualified is False
    assert "unsupported_qualification_version" in result.reason
