# backend/temples/tests/test_marriage_interpreter_coverage.py
"""Marriage Interpreter Coverage.

Implements docs/audit/marriage-consultation-interpreter-coverage.md Section
13's SAFE candidates ("夫婦関係"/"夫婦仲", both drawn from the existing
夫婦-root family already present via 夫婦円満 -- no broader vocabulary
invented). Closes the two remaining interpreter gaps documented there:

- "夫婦仲を良くしたい": MISSING_MARRIAGE_KEYWORD -- previously matched
  nothing at all.
- "夫婦関係を整えたい": OVERBROAD_MENTAL_KEYWORD + OVERBROAD_REST_KEYWORD
  -- previously extracted only mental/rest, marriage never appeared.

Verifies the existing (unmodified) NEED_PRIORITY contract
(temples/domain/need_tags.py) -- which already ranks "marriage" above
"mental"/"rest" -- resolves the multi-Need case correctly on its own: no
new priority model was invented, and mental/rest are not suppressed.

Scope: temples/domain/need_tags.py KEYWORDS["marriage"] and
temples/services/consultation_interpreter.py NEED_KEYWORDS["marriage"]
only. marriage mapping ({1,18}), marriage axis (relationship_repair),
love, relationship, mental, rest, courage, communication mappings, C1,
Ranking, Lead, Reason, Direction, Distance are all unchanged.
"""

from __future__ import annotations

import pytest

from temples.domain.need_tags import KEYWORDS, extract_need_tags
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_need import resolve_need_payload
from temples.services.consultation_interpreter import NEED_KEYWORDS


# ---------------------------------------------------------------------------
# Keyword table contract
# ---------------------------------------------------------------------------


def test_marriage_keyword_lists_include_new_existing_marriage_phrases():
    for word in ("夫婦関係", "夫婦仲"):
        assert word in KEYWORDS["marriage"]
        assert word in NEED_KEYWORDS["marriage"]


def test_marriage_keyword_lists_remain_identical_across_both_copies():
    """temples/domain/need_tags.py and temples/services/consultation_interpreter.py
    independently define this vocabulary (docs/audit/marriage-love-alias-
    boundary.md) -- this PR keeps both in sync, same invariant as before."""
    assert set(KEYWORDS["marriage"]) == set(NEED_KEYWORDS["marriage"])


def test_marriage_keyword_addition_is_narrow_not_generic():
    """Constraint: no broad relationship vocabulary was added -- both new
    words are exact members of the 夫婦-root family already anchored by
    the pre-existing 夫婦円満 keyword, not a generic 関係/仲 token."""
    for word in ("夫婦関係", "夫婦仲"):
        assert word.startswith("夫婦")
    assert "関係" not in KEYWORDS["marriage"]
    assert "仲" not in KEYWORDS["marriage"]


# ---------------------------------------------------------------------------
# Case 6: 夫婦仲を良くしたい -- clean addition, no collision
# ---------------------------------------------------------------------------


def test_previously_missed_existing_marriage_phrase_now_resolves_to_marriage():
    result = extract_need_tags("夫婦仲を良くしたい", max_tags=3)
    assert result.tags == ["marriage"]
    assert result.hits == {"marriage": ["夫婦仲"]}

    payload = resolve_need_payload(query="夫婦仲を良くしたい", need_tags=[], max_tags=3)
    assert payload["tags"] == ["marriage"]


# ---------------------------------------------------------------------------
# Case 5: 夫婦関係を整えたい -- multi-Need, existing NEED_PRIORITY contract
# ---------------------------------------------------------------------------


def test_previously_mental_rest_only_phrase_now_includes_marriage_first():
    """"夫婦関係を整えたい" still also hits mental/rest's own "整えたい"
    keyword (unmodified, not suppressed) -- but NEED_PRIORITY already
    ranks marriage (index 1) above mental (index 8) and rest (index 13),
    so marriage is picked first among the 3 matched tags. This is the
    existing contract doing its job, not a new priority rule."""
    result = extract_need_tags("夫婦関係を整えたい", max_tags=3)
    assert result.tags == ["marriage", "mental", "rest"]
    assert result.hits == {
        "marriage": ["夫婦関係"],
        "mental": ["整えたい"],
        "rest": ["整えたい"],
    }

    payload = resolve_need_payload(query="夫婦関係を整えたい", need_tags=[], max_tags=3)
    assert payload["tags"] == ["marriage", "mental", "rest"]


def test_marriage_and_mental_rest_coexist_as_real_matches_in_recommendations():
    """End-to-end: a candidate carrying marriage's own real GID evidence
    (id=1) for a "夫婦関係を整えたい" query genuinely matches "marriage"
    (not merely appears first in a list that never reaches scoring)."""
    recs = build_chat_recommendations(
        query="夫婦関係を整えたい",
        language="ja",
        candidates=[
            {
                "name": "縁結び神社",
                "goriyaku_tag_ids": [1],
                "goriyaku": "",
                "description": "",
                "astro_tags": [],
                "astro_elements": [],
                "astro_priority": 0,
                "popular_score": 5.0,
            }
        ],
        public_mode="need",
        flow="A",
    )

    assert recs["_need"]["tags"] == ["marriage", "mental", "rest"]
    top1 = recs["recommendations"][0]
    assert "marriage" in top1["breakdown"]["matched_need_tags"]


# ---------------------------------------------------------------------------
# Marriage-seeking regression -- must remain 100% coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query",
    [
        "結婚したい",
        "結婚につながる良縁がほしい",
        "結婚相手とのご縁がほしい",
        "良い人と結婚したい",
    ],
)
def test_marriage_seeking_queries_remain_correctly_extracted(query):
    payload = resolve_need_payload(query=query, need_tags=[], max_tags=3)
    assert "marriage" in payload["tags"]
    assert "love" not in payload["tags"]


@pytest.mark.parametrize(
    "query",
    [
        "夫婦円満を願いたい",
        "結婚生活を良くしたい",
        "パートナーとの結婚生活に悩んでいる",
    ],
)
def test_existing_marriage_queries_already_correct_remain_unaffected(query):
    payload = resolve_need_payload(query=query, need_tags=[], max_tags=3)
    assert payload["tags"] == ["marriage"]


# ---------------------------------------------------------------------------
# Cross-Need regression -- love / relationship / mental / rest controls
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query",
    ["恋愛を成就させたい", "復縁したい"],
)
def test_love_controls_unaffected(query):
    payload = resolve_need_payload(query=query, need_tags=[], max_tags=3)
    assert payload["tags"] == ["love"]
    assert "marriage" not in payload["tags"]


@pytest.mark.parametrize(
    "query",
    ["職場の人間関係を改善したい"],
)
def test_relationship_control_unaffected(query):
    payload = resolve_need_payload(query=query, need_tags=[], max_tags=3)
    assert payload["tags"] == ["relationship"]
    assert "marriage" not in payload["tags"]


@pytest.mark.parametrize(
    "query",
    ["気持ちを整えたい"],
)
def test_mental_and_rest_controls_do_not_gain_marriage(query):
    """Guards against the constraint "do not weaken mental/rest controls
    merely to force marriage extraction": a genuinely mental/rest-only
    query (no 夫婦-root word present) must not gain "marriage"."""
    payload = resolve_need_payload(query=query, need_tags=[], max_tags=3)
    assert payload["tags"] == ["mental", "rest"]
    assert "marriage" not in payload["tags"]


@pytest.mark.parametrize(
    "query",
    ["少し休みたい"],
)
def test_rest_only_control_unaffected(query):
    payload = resolve_need_payload(query=query, need_tags=[], max_tags=3)
    assert payload["tags"] == ["rest"]
    assert "marriage" not in payload["tags"]
