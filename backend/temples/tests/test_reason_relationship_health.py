# backend/temples/tests/test_reason_relationship_health.py
"""Reason R1b: relationship + health.

Closes docs/audit/semantic-followup-decision-and-pr-split.md's Section 8
SEMANTIC_SAFE_WITH_LIMITATION candidates for `relationship` and `health`:
both had a stable, unambiguous core meaning but a documented evidence-fit
limitation (see module docstring notes on the `intent_map` entries
themselves, temples/services/concierge_chat_ranking.py), so no generic
Reason had been written for either despite the limitation not blocking one.

IMPORTANT: this PR does NOT claim relationship/health are now fully
semantically resolved. Both remain SEMANTIC_SAFE_WITH_LIMITATION -- see
docs/audit/reason-relationship-health-implementation.md Section 5.

Scope: intent_map["relationship"] and intent_map["health"] only. Does not
touch Interpreter, Need normalization, Mapping, Axis, Text Evidence, C1,
Ranking, or Lead.
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
# Generic fallback removed for both Needs
# ---------------------------------------------------------------------------


def test_relationship_reason_no_longer_uses_generic_fallback():
    recs = build_chat_recommendations(
        query="職場の人間関係を改善したい",
        language="ja",
        candidates=[_candidate("縁結び神社", [1])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "今の願いを願う参拝先として" not in reason
    assert "人間関係の改善や修復を願う参拝先として" in reason


def test_health_reason_no_longer_uses_generic_fallback():
    recs = build_chat_recommendations(
        query="健康でいたい",
        language="ja",
        candidates=[_candidate("健康神社", [7])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "今の願いを願う参拝先として" not in reason
    assert "健康や体調の安定を願う参拝先として" in reason


# ---------------------------------------------------------------------------
# Copy remains compatible across multiple representative sub-intents
# (relationship: workplace framing per KEYWORDS; health: general health AND
# illness-recovery framing, both within health's own current GID mapping)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("query", "candidate_name", "goriyaku_tag_ids"),
    [
        ("職場の人間関係を改善したい", "縁結び神社A", [1]),
        ("親子関係を良くしたい", "縁結び神社B", [1]),
    ],
)
def test_relationship_copy_compatible_with_multiple_sub_intents(
    query, candidate_name, goriyaku_tag_ids
):
    recs = build_chat_recommendations(
        query=query,
        language="ja",
        candidates=[_candidate(candidate_name, goriyaku_tag_ids)],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    assert "relationship" in top1["breakdown"]["matched_need_tags"]
    assert "人間関係の改善や修復を願う参拝先として" in top1["reason"]


@pytest.mark.parametrize(
    ("query", "candidate_name", "goriyaku_tag_ids"),
    [
        ("健康でいたい", "健康神社", [7]),
        ("病気が治りますように", "病気平癒神社", [33]),
        ("体力をつけたい", "足腰健康神社", [38]),
    ],
)
def test_health_copy_compatible_with_multiple_sub_intents(
    query, candidate_name, goriyaku_tag_ids
):
    recs = build_chat_recommendations(
        query=query,
        language="ja",
        candidates=[_candidate(candidate_name, goriyaku_tag_ids)],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    assert "health" in top1["breakdown"]["matched_need_tags"]
    assert "健康や体調の安定を願う参拝先として" in top1["reason"]


# ---------------------------------------------------------------------------
# No change to Need extraction / mapping / Axis / candidate count / ranking
# ---------------------------------------------------------------------------


def test_relationship_need_extraction_unchanged():
    from temples.domain.need_tags import extract_need_tags

    result = extract_need_tags("職場の人間関係を改善したい", max_tags=3)
    assert result.tags == ["relationship"]


def test_health_need_extraction_unchanged():
    from temples.domain.need_tags import extract_need_tags

    result = extract_need_tags("健康でいたい", max_tags=3)
    assert result.tags == ["health"]


def test_relationship_gid_mapping_unchanged():
    from temples.domain.need_to_goriyaku_tag_ids import NEED_TO_GORIYAKU_IDS

    assert NEED_TO_GORIYAKU_IDS["relationship"] == {1}


def test_health_gid_mapping_unchanged():
    from temples.domain.need_to_goriyaku_tag_ids import NEED_TO_GORIYAKU_IDS

    assert NEED_TO_GORIYAKU_IDS["health"] == {7, 8, 24, 33, 38}


def test_relationship_axis_unchanged():
    from temples.domain.consultation_axis import resolve_consultation_axis

    result = resolve_consultation_axis(
        query="職場の人間関係を改善したい", need_tags=["relationship"]
    )
    assert result.axis == "relationship_repair"


def test_health_axis_still_falls_back_to_other():
    """health has no NEED_TAG_TO_CONSULTATION_AXIS entry -- unchanged known
    limitation, not addressed by this Reason-only PR."""
    from temples.domain.consultation_axis import resolve_consultation_axis

    result = resolve_consultation_axis(query="健康でいたい", need_tags=["health"])
    assert result.axis == "other"


@pytest.mark.django_db
def test_health_lead_may_cite_household_flavored_evidence_known_limitation():
    """Documents the SEMANTIC_SAFE_WITH_LIMITATION note verbatim: health's
    GID set includes id=7 (家内安全, household safety) -- Lead may cite
    non-personal-health-flavored evidence even though the Reason's
    user_intent clause is correct. This is expected, not a regression."""
    GoriyakuTag.objects.create(id=7, name="家内安全", category="ご利益")
    recs = build_chat_recommendations(
        query="健康でいたい",
        language="ja",
        candidates=[_candidate("健康神社", [7])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert reason.startswith("家内安全のご利益で知られる")
    assert "健康や体調の安定を願う参拝先として適しています。" in reason


def test_health_gid_winner_flow_correct():
    recs = build_chat_recommendations(
        query="病気が治りますように",
        language="ja",
        candidates=[_candidate("病気平癒神社", [33])],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    assert top1["breakdown"]["need_evidence_winner_by_tag"].get("health") == "gid"


def test_relationship_top3_composition_unchanged_by_reason_copy():
    candidates = [
        _candidate("縁結び神社", [1]),
        _candidate("無関係神社", []),
    ]
    recs = build_chat_recommendations(
        query="職場の人間関係を改善したい",
        language="ja",
        candidates=candidates,
        public_mode="need",
        flow="A",
    )
    names_in_order = [r["name"] for r in recs["recommendations"]]
    assert names_in_order[0] == "縁結び神社"


# ---------------------------------------------------------------------------
# Unrelated Reason outputs unchanged -- regression controls
# ---------------------------------------------------------------------------


def test_love_reason_unchanged():
    recs = build_chat_recommendations(
        query="いい出会いがほしい",
        language="ja",
        candidates=[_candidate("縁結び神社", [1])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "恋愛や良縁を願う参拝先として適しています。" in reason


def test_marriage_reason_unchanged():
    recs = build_chat_recommendations(
        query="結婚したい",
        language="ja",
        candidates=[_candidate("夫婦円満神社", [18])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "良縁や夫婦円満を願う参拝先として適しています。" in reason


def test_mental_reason_unchanged():
    recs = build_chat_recommendations(
        query="不安な気持ちを落ち着けたい",
        language="ja",
        candidates=[_candidate("厄除け神社", [11])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "不安や心の安定を願う参拝先として適しています。" in reason


def test_rest_reason_unchanged():
    recs = build_chat_recommendations(
        query="少し休みたい",
        language="ja",
        candidates=[_candidate("休息神社", [7])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "休息や気持ちの切り替えを願う参拝先として適しています。" in reason


def test_family_reason_generic_without_valid_family_evidence():
    """family now has M1 mapping {16, 35} + R2 intent_map copy "子宝や安産".
    A family-intent query still falls back to the generic copy when the
    candidate carries no valid family GID -- here the former family GID 2,
    which M1 removed. The family-specific copy is covered in
    test_reason_family.py."""
    recs = build_chat_recommendations(
        query="子宝に恵まれたい",
        language="ja",
        candidates=[_candidate("子宝神社", [2])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "今の願いを願う参拝先として適しています。" in reason
    assert "子宝や安産を願う参拝先として" not in reason
