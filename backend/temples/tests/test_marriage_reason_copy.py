# backend/temples/tests/test_marriage_reason_copy.py
"""Marriage Reason Copy.

Closes docs/audit/marriage-consultation-interpreter-coverage.md's final
open gap, MISSING_INTENT_COPY: `_build_need_reason_text`'s `intent_map`
(temples/services/concierge_chat_ranking.py) had no "marriage" entry, so
every marriage-tagged Reason fell to the generic "今の願い" fallback even
after marriage became independently reachable (PR #2586), gained its own
consultation axis (PR #2590), and gained full interpreter coverage
(PR #2591).

Scope: intent_map["marriage"] only. Does not touch Lead logic
(_build_need_lead, _resolve_matched_lead_evidence), marriage mapping
({1,18}), marriage axis (relationship_repair), marriage interpreter
vocabulary, C1, Ranking, Direction, or Distance -- see
docs/audit/marriage-reason-copy-implementation.md.
"""

from __future__ import annotations

import pytest

from temples.models import GoriyakuTag
from temples.services.concierge_chat import build_chat_recommendations


def _candidate(name, goriyaku_tag_ids, **overrides):
    base = {
        "name": name,
        "goriyaku_tag_ids": goriyaku_tag_ids,
        "goriyaku": "",
        "description": "",
        "astro_tags": [],
        "astro_elements": [],
        "astro_priority": 0,
        "popular_score": 5.0,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# The gap this PR closes
# ---------------------------------------------------------------------------


def test_marriage_reason_no_longer_uses_generic_fallback():
    """Before this PR: "縁結びのご利益で知られる〈shrine〉は、今の願いを
    願う参拝先として適しています。" (generic, intent_map had no "marriage"
    key). After: the marriage-specific user_intent clause appears."""
    recs = build_chat_recommendations(
        query="結婚したい",
        language="ja",
        candidates=[_candidate("縁結び神社", [1])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "今の願いを願う参拝先として" not in reason
    assert "良縁や夫婦円満を願う参拝先として" in reason


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("candidate_name", "goriyaku_tag_ids", "expected_lead"),
    [
        ("縁結び神社", [1], "縁結び"),
        ("夫婦円満神社", [18], "夫婦円満"),
    ],
)
def test_marriage_reason_compatible_with_both_evidence_ids(
    candidate_name, goriyaku_tag_ids, expected_lead
):
    """id=1 (縁結び) and id=18 (夫婦円満) are marriage's only two mapped
    GIDs (docs/audit/marriage-love-alias-boundary.md). The Lead clause
    (unmodified _build_need_lead) must cite whichever evidence actually
    matched -- the new user_intent clause is shared and must never claim
    evidence the winning shrine doesn't have. Creates the real canonical
    GoriyakuTag rows so Lead resolves the true label, not the generic
    "ご利益" fallback that a DB-less test would otherwise produce."""
    GoriyakuTag.objects.create(id=1, name="縁結び", category="ご利益")
    GoriyakuTag.objects.create(id=18, name="夫婦円満", category="ご利益")

    recs = build_chat_recommendations(
        query="結婚したい",
        language="ja",
        candidates=[_candidate(candidate_name, goriyaku_tag_ids)],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    reason = top1["reason"]

    assert top1["breakdown"]["matched_need_tags"] == ["marriage"]
    assert reason.startswith(f"{expected_lead}のご利益で知られる")
    assert "良縁や夫婦円満を願う参拝先として適しています。" in reason


def test_marriage_reason_does_not_collapse_into_love_copy():
    recs = build_chat_recommendations(
        query="結婚したい",
        language="ja",
        candidates=[_candidate("縁結び神社", [1])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "恋愛や良縁を願う" not in reason


def test_marriage_reason_makes_no_guaranteed_outcome_claim():
    """Constraint: must not claim guaranteed marriage, reconciliation, or
    relationship success -- same "〜を願う参拝先として適しています" hedge
    already used by every other Need's intent_map entry, not a stronger
    assertion."""
    recs = build_chat_recommendations(
        query="結婚したい",
        language="ja",
        candidates=[_candidate("縁結び神社", [1])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    for forbidden in ("必ず", "確実に", "叶います", "叶う", "成就します"):
        assert forbidden not in reason


# ---------------------------------------------------------------------------
# Existing-marriage phrasing also benefits (PR #2591 coverage)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query",
    ["夫婦円満を願いたい", "夫婦仲を良くしたい", "夫婦関係を整えたい"],
)
def test_existing_marriage_queries_get_marriage_reason(query):
    recs = build_chat_recommendations(
        query=query,
        language="ja",
        candidates=[_candidate("夫婦円満神社", [18])],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    assert "marriage" in top1["breakdown"]["matched_need_tags"]
    assert "良縁や夫婦円満を願う参拝先として" in top1["reason"]


# ---------------------------------------------------------------------------
# Cross-Need regression -- unrelated Needs' Reason copy is untouched
# ---------------------------------------------------------------------------


def test_love_reason_unchanged():
    recs = build_chat_recommendations(
        query="恋愛を成就させたい",
        language="ja",
        candidates=[_candidate("恋木神社", [1], goriyaku="恋愛成就")],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "恋愛や良縁を願う参拝先として適しています。" in reason


def test_relationship_reason_not_collapsed_into_marriage_copy():
    """Originally asserted relationship's Reason stayed on the generic
    "今の願い" fallback -- that assumption became stale once
    fix/reason-relationship-health gave relationship its own intent_map
    entry ("人間関係の改善や修復", docs/audit/reason-relationship-health-
    implementation.md). The invariant this test actually protects --
    relationship must never pick up marriage's own copy, since both share
    GoriyakuTag id=1 (縁結び) -- is unchanged and still asserted below."""
    recs = build_chat_recommendations(
        query="職場の人間関係を改善したい",
        language="ja",
        candidates=[_candidate("縁結び神社", [1])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "人間関係の改善や修復を願う参拝先として適しています。" in reason
    assert "良縁や夫婦円満" not in reason


def test_protection_reason_unchanged():
    recs = build_chat_recommendations(
        query="厄を落としたい",
        language="ja",
        candidates=[_candidate("厄除け神社", [2])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "厄除けや守りを願う参拝先として適しています。" in reason


def test_study_reason_unchanged():
    recs = build_chat_recommendations(
        query="合格祈願したい",
        language="ja",
        candidates=[_candidate("学業神社", [10])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "学業や合格を願う参拝先として適しています。" in reason
