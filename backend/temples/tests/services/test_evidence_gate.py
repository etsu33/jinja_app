from __future__ import annotations

import pytest

from temples.services.evidence_gate import decide_fact_usability


# --- Case A: Fact ready / Source Relationなし ---


def test_case_a_fact_ready_without_any_source_is_not_usable():
    decision = decide_fact_usability(
        verification_status="source_confirmed",
        confidence="high",
        source_verification_statuses=[],
    )
    assert decision.usable is False
    assert decision.display_mode == "hidden"
    assert decision.reason_strength == "suppressed"


# --- Case B: Fact ready / Source draftのみ ---


def test_case_b_fact_ready_with_only_draft_source_is_not_usable():
    decision = decide_fact_usability(
        verification_status="source_confirmed",
        confidence="high",
        source_verification_statuses=["draft"],
    )
    assert decision.usable is False


# --- Case C: Fact draft / Source ready ---


def test_case_c_fact_draft_with_ready_source_is_not_usable():
    decision = decide_fact_usability(
        verification_status="draft",
        confidence="high",
        source_verification_statuses=["source_confirmed"],
    )
    assert decision.usable is False


# --- Case D: Fact ready / ready Source + draft Source ---


def test_case_d_fact_ready_with_ready_and_draft_source_is_usable():
    decision = decide_fact_usability(
        verification_status="source_confirmed",
        confidence="high",
        source_verification_statuses=["source_confirmed", "draft"],
    )
    assert decision.usable is True
    assert decision.display_mode == "full"
    assert decision.reason_strength == "assertive"


# --- Case E: Fact reviewed / Source reviewed ---


def test_case_e_fact_reviewed_with_reviewed_source_is_usable():
    decision = decide_fact_usability(
        verification_status="reviewed",
        confidence="medium",
        source_verification_statuses=["reviewed"],
    )
    assert decision.usable is True


# --- Case F: disputed ---


def test_case_f_disputed_fact_is_not_usable():
    decision = decide_fact_usability(
        verification_status="disputed",
        confidence="high",
        source_verification_statuses=["source_confirmed"],
    )
    assert decision.usable is False


@pytest.mark.parametrize(
    "verification_status", ["draft", "unverified", "disputed", "outdated", "rejected"]
)
def test_non_fact_ready_fact_status_is_never_usable_even_with_ready_source(verification_status):
    decision = decide_fact_usability(
        verification_status=verification_status,
        confidence="high",
        source_verification_statuses=["source_confirmed"],
    )
    assert decision.usable is False


@pytest.mark.parametrize(
    "source_status", ["draft", "unverified", "disputed", "outdated", "rejected"]
)
def test_non_fact_ready_source_status_alone_never_makes_fact_usable(source_status):
    decision = decide_fact_usability(
        verification_status="source_confirmed",
        confidence="high",
        source_verification_statuses=[source_status],
    )
    assert decision.usable is False


def test_confidence_does_not_affect_usable():
    # PR-Aではconfidenceによる利用可否の変更は行わない。metadataとして保持するのみ。
    for confidence in ("high", "medium", "low", ""):
        decision = decide_fact_usability(
            verification_status="source_confirmed",
            confidence=confidence,
            source_verification_statuses=["source_confirmed"],
        )
        assert decision.usable is True
        assert decision.confidence == confidence
