# backend/temples/tests/test_need_labels_ja_completeness.py
"""NEED_LABELS_JA Completeness.

Closes docs/audit/recommendation-semantic-resolution-cross-need.md's
NEED_LABELS_JA finding: 5 of 15 canonical Need tags (marriage, relationship,
communication, health, family) were absent from every active Need-to-
Japanese-label dictionary, causing the raw English Need key to leak into
`label_ja`/`primary_label_ja`/`primary_need_label_ja` fields -- directly
observed live as `'label_ja': 'marriage'` in an earlier session even after
PR #2593 added marriage's `intent_map` Reason-sentence entry (a separate,
already-fixed gap).

Repository-wide search (A0) found THREE active copies, not the two the
prior audit named:
  - temples/services/concierge_chat_ranking.py: NEED_LABELS_JA
  - temples/services/concierge_chat_ranking.py: NEED_TAG_LABELS_JA
    (consumed by `_need_tag_to_ja()` -> rank_explanation.primary_label_ja /
    rank_comparison.shared_need_tags_ja -- missed by the prior audit
    because it only searched for the literal name "NEED_LABELS_JA")
  - temples/services/concierge_explanation_payload.py: NEED_LABELS_JA

Scope: dictionary entries only, in all three copies above. Does NOT touch
Need aliases, interpreter vocabulary, Axis mapping, GID mapping, Text
Evidence, C1, Ranking weights, Lead, or the `intent_map` Reason-sentence
dict (a distinct, already-synced-elsewhere dict) -- see
docs/audit/need-labels-ja-completeness-implementation.md.
"""

from __future__ import annotations

import pytest

from temples.domain.need_tags import NEED_TAGS
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_ranking import (
    NEED_LABELS_JA as RANKING_NEED_LABELS_JA,
)
from temples.services.concierge_chat_ranking import (
    NEED_TAG_LABELS_JA as RANKING_NEED_TAG_LABELS_JA,
)
from temples.services.concierge_explanation_payload import (
    NEED_LABELS_JA as EXPLANATION_NEED_LABELS_JA,
)

ACTIVE_NEED_LABEL_DICTS = {
    "concierge_chat_ranking.NEED_LABELS_JA": RANKING_NEED_LABELS_JA,
    "concierge_chat_ranking.NEED_TAG_LABELS_JA": RANKING_NEED_TAG_LABELS_JA,
    "concierge_explanation_payload.NEED_LABELS_JA": EXPLANATION_NEED_LABELS_JA,
}

# Pinned exact text for the 10 Needs that already had labels before this
# change -- guards point 3 ("existing labels are unchanged").
PRE_EXISTING_LABELS = {
    "study": "学業・合格",
    "career": "転機・仕事",
    "mental": "不安・心",
    "love": "恋愛",
    "money": "金運",
    "rest": "休息",
    "courage": "前進・後押し",
    "protection": "厄除け・守り",
    "focus": "集中・継続",
    "travel_safe": "移動・安全",
}

NEWLY_ADDED_NEEDS = {"marriage", "relationship", "communication", "health", "family"}


# ---------------------------------------------------------------------------
# 1. All 15 canonical Needs resolve to a Japanese label, in every active copy
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("dict_name", ACTIVE_NEED_LABEL_DICTS)
def test_all_canonical_needs_have_a_label(dict_name):
    labels = ACTIVE_NEED_LABEL_DICTS[dict_name]
    missing = [tag for tag in NEED_TAGS if tag not in labels]
    assert missing == [], f"{dict_name} is missing labels for: {missing}"
    assert len(NEED_TAGS) == 15, "canonical Need count drifted -- re-audit before trusting this test"


# ---------------------------------------------------------------------------
# 2. No canonical Need falls back to its raw (English) key
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("dict_name", ACTIVE_NEED_LABEL_DICTS)
def test_no_canonical_need_resolves_to_its_own_raw_key(dict_name):
    labels = ACTIVE_NEED_LABEL_DICTS[dict_name]
    raw_key_leaks = [tag for tag in NEED_TAGS if labels.get(tag) == tag]
    assert raw_key_leaks == [], f"{dict_name} leaks the raw English key for: {raw_key_leaks}"


# ---------------------------------------------------------------------------
# 3. Existing labels are unchanged
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("dict_name", ACTIVE_NEED_LABEL_DICTS)
def test_pre_existing_labels_unchanged(dict_name):
    labels = ACTIVE_NEED_LABEL_DICTS[dict_name]
    for tag, expected in PRE_EXISTING_LABELS.items():
        assert labels.get(tag) == expected, (
            f"{dict_name}[{tag!r}] changed: expected {expected!r}, got {labels.get(tag)!r}"
        )


# ---------------------------------------------------------------------------
# 4. Duplicate active label dictionaries remain synchronized
# ---------------------------------------------------------------------------


def test_all_active_copies_synchronized_for_every_canonical_need():
    mismatches = []
    for tag in NEED_TAGS:
        values = {name: d.get(tag) for name, d in ACTIVE_NEED_LABEL_DICTS.items()}
        if len(set(values.values())) != 1:
            mismatches.append((tag, values))
    assert mismatches == [], f"Need labels diverge across active copies: {mismatches}"


# ---------------------------------------------------------------------------
# 5 & 6. Live runtime proof: marriage no longer returns "marriage"; the
# other 4 previously-missing Needs are covered end to end (reason_facts,
# _explanation_payload.primary_reason, rank_explanation.primary_label_ja,
# and _explanation_payload.primary_need_label_ja -- all four surfaces that
# consume these dicts).
# ---------------------------------------------------------------------------


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


# NOTE: `communication` was previously exercised here via a candidate
# carrying GID 30. Mother Ship 2026-08-29 (Communication = EVIDENCE_LIMITED,
# Evidence Policy = DISABLE_GID_EVIDENCE --
# docs/audit/remaining-need-semantic-decision-packets.md) removed
# communication's GID mapping, so it can no longer produce a matched-via-GID
# recommendation and cannot be a case for this live path. communication's
# `label_ja` entry itself is still pinned by
# test_all_canonical_needs_have_a_label / test_no_canonical_need_resolves_to
# _its_own_raw_key (both parametrized over all 15 NEED_TAGS).
@pytest.mark.parametrize(
    ("need", "query", "candidate_name", "goriyaku_tag_ids"),
    [
        ("marriage", "結婚したい", "夫婦円満神社", [18]),
        ("relationship", "職場の人間関係を改善したい", "縁結び神社", [1]),
        ("health", "健康でいたい", "健康神社", [7]),
        ("family", "子宝に恵まれたい", "子宝神社", [2]),
    ],
)
def test_previously_missing_needs_resolve_to_real_japanese_label_live(
    need, query, candidate_name, goriyaku_tag_ids
):
    recs = build_chat_recommendations(
        query=query,
        language="ja",
        candidates=[_candidate(candidate_name, goriyaku_tag_ids)],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    assert need in top1["breakdown"]["matched_need_tags"]

    expected_label = RANKING_NEED_LABELS_JA[need]
    assert expected_label != need  # sanity: the expected label is not itself a raw key

    # Surface 1: reason_facts[].label_ja
    matched_facts = [
        rf for rf in (top1.get("reason_facts") or []) if rf.get("label") == need
    ]
    assert matched_facts, f"no reason_facts entry for matched Need {need!r}"
    for rf in matched_facts:
        assert rf.get("label_ja") == expected_label
        assert rf.get("label_ja") != need

    # Surface 2: _explanation_payload.primary_reason.label_ja +
    # primary_need_label_ja (only asserted when this candidate is primary)
    ep = top1.get("_explanation_payload") or {}
    if ep.get("primary_need_tag") == need:
        assert ep.get("primary_need_label_ja") == expected_label
        assert ep.get("primary_need_label_ja") != need
        primary_reason = ep.get("primary_reason") or {}
        if primary_reason.get("label") == need:
            assert primary_reason.get("label_ja") == expected_label

    # Surface 3: rank_explanation.primary_label_ja
    rank_explanation = top1.get("rank_explanation") or {}
    if rank_explanation.get("primary_label") == need:
        assert rank_explanation.get("primary_label_ja") == expected_label
        assert rank_explanation.get("primary_label_ja") != need


def test_marriage_label_ja_is_not_the_literal_string_marriage():
    """The exact regression this task closes: a real JSON dump earlier in
    this project's history showed `'label_ja': 'marriage'` even after
    marriage became independently reachable and gained its own Reason
    sentence (PR #2586-#2593). Confirms that specific defect is gone."""
    recs = build_chat_recommendations(
        query="結婚したい",
        language="ja",
        candidates=[_candidate("夫婦円満神社", [18])],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    matched_facts = [
        rf for rf in (top1.get("reason_facts") or []) if rf.get("label") == "marriage"
    ]
    assert matched_facts
    for rf in matched_facts:
        assert rf.get("label_ja") != "marriage"
        assert rf.get("label_ja") == "結婚・夫婦円満"


# ---------------------------------------------------------------------------
# Cross-Need regression -- unrelated Needs' labels are untouched
# ---------------------------------------------------------------------------


def test_love_label_unchanged():
    recs = build_chat_recommendations(
        query="いい出会いがほしい",
        language="ja",
        candidates=[_candidate("縁結び神社", [1])],
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]
    matched_facts = [
        rf for rf in (top1.get("reason_facts") or []) if rf.get("label") == "love"
    ]
    assert matched_facts
    for rf in matched_facts:
        assert rf.get("label_ja") == "恋愛"
