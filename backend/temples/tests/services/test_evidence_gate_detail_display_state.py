"""PR-C4B1: Shrine Detail専用のdecide_detail_display_state()単体テスト。

Recommendation側のdecide_fact_usability()/EvidenceDecisionは変更していない
ため、既存のtest_evidence_gate.pyでの回帰テストと合わせて確認する。
"""

from __future__ import annotations

import pytest

from temples.services.evidence_gate import (
    DETAIL_CANDIDATE_VERIFICATION_STATUSES,
    DETAIL_DISPUTED_VERIFICATION_STATUS,
    FACT_READY_VERIFICATION_STATUSES,
    decide_detail_display_state,
)


@pytest.mark.parametrize("verification_status", ["source_confirmed", "reviewed"])
def test_full_verification_status_with_ready_source_is_full(verification_status):
    result = decide_detail_display_state(
        verification_status=verification_status,
        source_verification_statuses=["source_confirmed"],
    )
    assert result == "full"


def test_disputed_with_ready_source_is_disputed():
    result = decide_detail_display_state(
        verification_status="disputed",
        source_verification_statuses=["source_confirmed"],
    )
    assert result == "disputed"


@pytest.mark.parametrize("verification_status", ["draft", "unverified", "outdated", "rejected"])
def test_non_ready_non_disputed_verification_status_is_hidden(verification_status):
    result = decide_detail_display_state(
        verification_status=verification_status,
        source_verification_statuses=["source_confirmed"],
    )
    assert result == "hidden"


def test_disputed_without_any_source_is_hidden():
    result = decide_detail_display_state(
        verification_status="disputed",
        source_verification_statuses=[],
    )
    assert result == "hidden"


def test_disputed_with_only_draft_source_is_hidden():
    result = decide_detail_display_state(
        verification_status="disputed",
        source_verification_statuses=["draft"],
    )
    assert result == "hidden"


def test_full_verification_status_without_ready_source_is_hidden():
    result = decide_detail_display_state(
        verification_status="source_confirmed",
        source_verification_statuses=["draft"],
    )
    assert result == "hidden"


def test_disputed_with_ready_and_non_ready_source_mixed_is_disputed():
    result = decide_detail_display_state(
        verification_status="disputed",
        source_verification_statuses=["draft", "source_confirmed"],
    )
    assert result == "disputed"


def test_confidence_is_not_a_parameter():
    """confidenceはdisplay state判定に使わない契約（PR-C4A）。
    そもそも関数シグネチャに存在しないことを確認する。
    """
    import inspect

    params = inspect.signature(decide_detail_display_state).parameters
    assert "confidence" not in params
    assert "history_type" not in params


def test_detail_disputed_verification_status_constant_value():
    assert DETAIL_DISPUTED_VERIFICATION_STATUS == "disputed"


def test_detail_candidate_verification_statuses_is_fact_ready_plus_disputed():
    assert set(DETAIL_CANDIDATE_VERIFICATION_STATUSES) == set(FACT_READY_VERIFICATION_STATUSES) | {
        "disputed"
    }


def test_fact_ready_verification_statuses_unchanged():
    """Recommendation側の定数は本PRで変更しない（回帰の固定）。"""
    assert set(FACT_READY_VERIFICATION_STATUSES) == {"source_confirmed", "reviewed"}
