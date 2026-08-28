# backend/temples/tests/test_reason_focus_travel_safe.py
"""Reason R1a: focus + travel_safe.

Closes docs/audit/semantic-followup-decision-and-pr-split.md's Section 9
SEMANTIC_SAFE candidates for `focus` and `travel_safe`: both had a clear,
unambiguous meaning and no open product question, but `intent_map` (inside
`_build_need_reason_text`, temples/services/concierge_chat_ranking.py) had
no entry for either, so every match fell to the generic "今の願い"
fallback.

Scope: intent_map["focus"] and intent_map["travel_safe"] only. Does not
touch Interpreter, Need normalization, Mapping, Axis, Text Evidence, C1,
Ranking, Lead, labels, or candidate filtering -- see
docs/audit/reason-focus-travel-safe-implementation.md.
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
# 1 & 2. Generic fallback removed
# 3. Correct Need-specific intent phrase appears
# ---------------------------------------------------------------------------


def test_focus_reason_no_longer_uses_generic_fallback():
    recs = build_chat_recommendations(
        query="集中力を高めたい",
        language="ja",
        candidates=[_candidate("集中神社", [9])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "今の願いを願う参拝先として" not in reason
    assert "集中や習慣づくりを願う参拝先として" in reason


def test_travel_safe_reason_no_longer_uses_generic_fallback():
    recs = build_chat_recommendations(
        query="交通安全を祈願したい",
        language="ja",
        candidates=[_candidate("交通安全神社", [3])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "今の願いを願う参拝先として" not in reason
    assert "移動や旅の安全を願う参拝先として" in reason


# ---------------------------------------------------------------------------
# 4 & 5. GID-winner and Text-winner flows remain correct
# (focus/travel_safe have no NEED_TEXT_WEIGHTS entry -- GID-only by
# current design; asserted explicitly so a future Text Evidence addition
# doesn't silently break this test's assumption)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("need", "query", "candidate_name", "goriyaku_tag_ids", "expected_lead", "expected_intent"),
    [
        ("focus", "集中力を高めたい", "学業成就神社", [9], "学業成就", "集中や習慣づくり"),
        ("focus", "習慣を身につけたい", "合格祈願神社", [10], "合格祈願", "集中や習慣づくり"),
        ("travel_safe", "交通安全を祈願したい", "交通安全神社", [3], "交通安全", "移動や旅の安全"),
        ("travel_safe", "出張が多いので安全を願いたい", "航海安全神社", [13], "航海安全", "移動や旅の安全"),
    ],
)
def test_gid_winner_flow_correct(
    need, query, candidate_name, goriyaku_tag_ids, expected_lead, expected_intent
):
    # Real canonical GoriyakuTag rows -- the pytest-django test DB starts
    # empty (migrations only), so without these _build_need_lead falls to
    # the generic "ご利益" label rather than the true GID name.
    for gid in goriyaku_tag_ids:
        GoriyakuTag.objects.get_or_create(id=gid, defaults={"name": expected_lead, "category": "ご利益"})
    recs = build_chat_recommendations(
        query=query,
        language="ja",
        candidates=[_candidate(candidate_name, goriyaku_tag_ids)],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    assert need in top1["breakdown"]["matched_need_tags"]
    assert top1["breakdown"]["need_evidence_winner_by_tag"].get(need) == "gid"
    assert top1["reason"].startswith(f"{expected_lead}のご利益で知られる")
    assert f"{expected_intent}を願う参拝先として適しています。" in top1["reason"]


def test_focus_and_travel_safe_have_no_text_evidence_entry():
    """Documents the current GID-only evidence shape these tests assume."""
    from temples.services.concierge_chat_ranking import NEED_TEXT_WEIGHTS

    assert "focus" not in NEED_TEXT_WEIGHTS
    assert "travel_safe" not in NEED_TEXT_WEIGHTS


# ---------------------------------------------------------------------------
# 6. Lead unchanged  7. score_need unchanged  9. total score unchanged
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("need", "query", "candidate_name", "goriyaku_tag_ids"),
    [
        ("focus", "集中力を高めたい", "集中神社", [9]),
        ("travel_safe", "交通安全を祈願したい", "交通安全神社", [3]),
    ],
)
def test_lead_score_and_matched_tags_unchanged(need, query, candidate_name, goriyaku_tag_ids):
    recs = build_chat_recommendations(
        query=query,
        language="ja",
        candidates=[_candidate(candidate_name, goriyaku_tag_ids)],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    bd = top1["breakdown"]
    assert bd["matched_need_tags"] == [need]
    assert bd["score_need"] == 1
    # Lead clause (before "、") only cites the real matched GID label --
    # unchanged mechanism, only the user_intent clause after it changed.
    lead_clause = top1["reason"].split("、", 1)[0]
    assert "のご利益で知られる" in lead_clause


# ---------------------------------------------------------------------------
# 8, 10. score_v3 / Top3 unchanged by this code path -- a single-candidate
# fixture proves ranking position and score composition are untouched;
# Reason text construction happens after scoring, never feeds back into it.
# ---------------------------------------------------------------------------


def test_focus_top3_composition_unchanged_by_reason_copy():
    candidates = [
        _candidate("集中神社", [9]),
        _candidate("無関係神社", []),
    ]
    recs = build_chat_recommendations(
        query="集中力を高めたい", language="ja", candidates=candidates, public_mode="need", flow="A"
    )
    names_in_order = [r["name"] for r in recs["recommendations"]]
    assert names_in_order[0] == "集中神社"
    assert recs["recommendations"][0]["_score_total"] > recs["recommendations"][1]["_score_total"]


# ---------------------------------------------------------------------------
# 11. Unrelated Reason outputs unchanged -- regression controls
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


def test_career_reason_unchanged():
    recs = build_chat_recommendations(
        query="転職を考えている",
        language="ja",
        candidates=[_candidate("導き神社", [21])],
        public_mode="need",
        flow="A",
    )
    reason = recs["recommendations"][0]["reason"]
    assert "仕事や転機を願う参拝先として適しています。" in reason
