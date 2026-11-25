# backend/temples/tests/services/test_l1_freetext_final_readiness_contract.py
"""L1 Free-text Recommendation Final Readiness Gate -- contract tests.

See docs/audit/concierge-l1-freetext-final-readiness.md for the full
audit (Before/After metrics across PR #2409/#2410/#2411, Fallback
Classification, Known Case Deep Dive, Semantic Sanity, Decision).

This file pins the audit's *conclusions* as regression guards, reusing
the existing `readiness_results` fixture (same 20-fixture set, same
representative_shrines.yaml pool, same deterministic
CONCIERGE_USE_LLM=False path) from test_concierge_l1_freetext_readiness.py
rather than duplicating fixture/candidate-loading logic. Thresholds are
the audit's own named GO/CONDITIONAL GO criteria (Task 7), not values
picked to make this suite pass -- a real regression here means the
Final Readiness Gate's Decision (CONDITIONAL GO) is no longer supported
by production behavior and the audit doc needs to be re-run, not that
these thresholds should be loosened.

No production code is changed by this file.
"""
from __future__ import annotations

import pytest

from temples.tests.services.test_concierge_l1_freetext_readiness import (
    EXPECTED_FALLBACK_CLASSIFICATION,
    readiness_results,  # noqa: F401 -- re-exported fixture, pytest discovers it via this import
)

# Task 6 severe-mismatch categories: a theme's Top1 reason text must
# never lean on another theme's *exclusive* vocabulary as its stated
# basis. Fallback cases are excluded (Task 6's own exclusion rule: a
# generic, explicitly-fallback reason is not a semantic claim).
LOVE_ONLY_PHRASES = ("恋愛", "良縁", "縁結び", "恋愛成就", "片思い", "復縁", "両思い")
MONEY_ONLY_PHRASES = ("商売繁盛", "金運向上", "金運")
STUDY_ONLY_PHRASES = ("学業成就", "学業や合格", "合格祈願")

FORBIDDEN_PHRASES_BY_THEME = {
    "career": LOVE_ONLY_PHRASES,  # 仕事相談 -> 恋愛意味
    "relationship": LOVE_ONLY_PHRASES,  # 人間関係 -> 恋愛専用意味
    "rest": MONEY_ONLY_PHRASES,  # 休息 -> 商売繁盛を主要根拠として断定
    "love": STUDY_ONLY_PHRASES,  # 恋愛 -> 学業理由
}


@pytest.mark.django_db
def test_l1_freetext_clear_intent_axis_other_rate_within_go_threshold(readiness_results):  # noqa: F811
    """Task 7 GO criterion: clear-intent consultation_axis="other" rate
    <= 10%. Real value at audit time was 6.25% (1/16, l1_courage_002
    only) -- PR #2411 brought this down from 31.25% (NO-GO) by wiring
    up relationship_repair. This guards against a future regression
    silently reopening Finding A for relationship/love (or any other
    theme)."""
    clear_cases = [
        (case_id, recs)
        for case_id, (case, recs) in readiness_results.items()
        if case["intent_clarity"] == "clear"
    ]
    other_count = sum(1 for _, recs in clear_cases if recs.get("consultation_axis") == "other")
    rate = other_count / len(clear_cases)
    assert rate <= 0.10, f"clear-intent axis=other rate={rate:.1%} exceeds Task 7 GO threshold (10%)"


@pytest.mark.django_db
def test_l1_freetext_fallback_classification_counts_match_audit(readiness_results):  # noqa: F811
    """Task 4: pins the audit's Fallback Classification counts (A/B/C/D)
    as a single explicit assertion, rather than only the per-case
    membership already covered by
    test_l1_freetext_fallback_cases_match_documented_set. A=2
    (l1_relationship_002, l1_courage_002, Interpretation Gap), B=0
    (Recommendation Matching Gap -- unobserved in this fixture set),
    C=1 (l1_relationship_003, Candidate Coverage Gap -- Taxonomy and
    Interpretation both succeeded, candidate data did not), D=4
    (l1_ambiguous_001-004, Expected Fallback)."""
    counts = {"interpretation_gap": 0, "candidate_coverage_gap": 0, "expected_fallback": 0}
    for category in EXPECTED_FALLBACK_CLASSIFICATION.values():
        counts[category] = counts.get(category, 0) + 1

    assert counts["interpretation_gap"] == 2
    assert counts["candidate_coverage_gap"] == 1
    assert counts["expected_fallback"] == 4
    # Recommendation Matching Gap (B): no case in EXPECTED_FALLBACK_CLASSIFICATION
    # is classified this way -- unobserved in this fixture set (Task 4).
    assert set(EXPECTED_FALLBACK_CLASSIFICATION.values()) == {
        "interpretation_gap",
        "candidate_coverage_gap",
        "expected_fallback",
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case_id",
    sorted(
        cid
        for cid in [
            "l1_career_001", "l1_career_002", "l1_career_003",
            "l1_rest_001", "l1_rest_002", "l1_rest_003",
            "l1_relationship_001",
            "l1_love_001", "l1_love_002",
        ]
    ),
)
def test_l1_freetext_semantic_sanity_no_cross_theme_severe_mismatch(case_id, readiness_results):  # noqa: F811
    """Task 6: none of the 4 named severe-mismatch categories (career->
    love meaning, relationship->love-only meaning, rest->money as
    primary basis, love->study reason) appear in the Top1 reason text
    for a non-fallback clear-intent case. Only themes with a defined
    forbidden-phrase set and a non-fallback result at audit time are
    checked here -- l1_relationship_002/003 are fallback (excluded by
    Task 6's own rule) and are covered instead by the Interpretation
    Gap / Candidate Coverage Gap classification tests."""
    case, recs = readiness_results[case_id]
    theme = case["theme"]
    forbidden = FORBIDDEN_PHRASES_BY_THEME.get(theme)
    if not forbidden:
        pytest.skip(f"no forbidden-phrase set defined for theme={theme!r}")

    top1 = recs["recommendations"][0]
    if top1.get("_primary_reason_source") == "fallback":
        pytest.skip(f"{case_id}: fallback reason is generic, not a semantic claim (Task 6 exclusion)")

    reason_text = top1.get("reason") or ""
    for phrase in forbidden:
        assert phrase not in reason_text, (
            f"{case_id} (theme={theme}): forbidden phrase {phrase!r} found in reason: {reason_text!r}"
        )
