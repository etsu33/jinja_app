# backend/temples/tests/test_communication_interpreter_coverage.py
"""Communication Interpreter C1.

Closes part of docs/audit/semantic-followup-decision-and-pr-split.md's
Section 17/18 Track C1: `communication`'s interpreter vocabulary
(KEYWORDS["communication"] in temples/domain/need_tags.py, and the
identical NEED_KEYWORDS["communication"] in
temples/services/consultation_interpreter.py) omitted the Need's own
literal name ("コミュニケーション") and common conjugations/negations of
its own existing roots ("話す" -> "話せる"/"話せない", "伝える" ->
"伝えられない"/"伝わらない"), causing real communication-intent queries to
extract no Need at all, or the wrong Need (relationship, via the
co-occurring word "職場").

IMPORTANT -- this PR is INTERPRETER-ONLY. It does NOT fix Recommendation
evidence, taxonomy, GID mapping, consultation Axis, or Reason for
`communication` -- those remain BLOCKED_BY_UPSTREAM per the same audit
document (Section 8). See
docs/audit/communication-interpreter-coverage-implementation.md's
INTERPRETER_IMPROVED_RECOMMENDATION_NOT_FULLY_RESOLVED statement.

Scope: KEYWORDS["communication"] and NEED_KEYWORDS["communication"] only
(5 new entries each, kept synchronized per established convention). Does
not touch Mapping, Axis, Text Evidence, C1 scoring, Ranking, or Lead.
"""

from __future__ import annotations

import pytest

from temples.domain.need_tags import extract_need_tags
from temples.services.concierge_chat_need import resolve_need_payload
from temples.services.consultation_interpreter import NEED_KEYWORDS


# ---------------------------------------------------------------------------
# Coverage: previously-missing / wrong-Need communication phrasings now
# correctly extract "communication"
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("query", "concept"),
    [
        ("人とうまく話せるようになりたい", "difficulty communicating"),
        ("コミュニケーション能力を上げたい", "communication (Need's own name)"),
        ("自分の気持ちをうまく伝えられない", "expressing oneself"),
        ("人と話すのが怖い", "difficulty communicating"),
    ],
)
def test_previously_missed_phrases_now_extract_communication(query, concept):
    result = extract_need_tags(query, max_tags=3)
    assert "communication" in result.tags, f"{concept}: {query!r} -> {result.tags}"


def test_previously_wrong_need_phrase_now_correctly_multi_need():
    """'職場でのコミュニケーションを改善したい' previously extracted only
    ['relationship'] (via 職場), missing communication entirely. It should
    now extract both -- NEED_PRIORITY ranks relationship (index 9) above
    communication (index 10), so relationship stays primary; communication
    is correctly added alongside it, not replacing it."""
    result = extract_need_tags("職場でのコミュニケーションを改善したい", max_tags=3)
    assert result.tags == ["relationship", "communication"]
    assert result.hits["communication"] == ["コミュニケーション"]


# ---------------------------------------------------------------------------
# Already-correct cases remain correct (no regression to existing recall)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query",
    [
        "営業で成果を出したい",
        "プレゼンが苦手で克服したい",
        "初対面の人と話すのが苦手",
        "会話が続かない",
    ],
)
def test_already_correct_phrases_still_extract_communication(query):
    result = extract_need_tags(query, max_tags=3)
    assert result.tags == ["communication"]


# ---------------------------------------------------------------------------
# Negative controls: no new false positives / cross-Need collisions for
# relationship, love, marriage, family, mental
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("query", "expected_tags", "control_need"),
    [
        ("職場の人間関係を改善したい", ["relationship"], "relationship"),
        ("いい出会いがほしい", ["love"], "love"),
        ("結婚したい", ["marriage"], "marriage"),
        ("子宝に恵まれたい", ["family"], "family"),
        ("不安な気持ちを落ち着けたい", ["mental", "rest"], "mental"),
    ],
)
def test_control_needs_unaffected_by_vocabulary_expansion(query, expected_tags, control_need):
    result = extract_need_tags(query, max_tags=3)
    assert result.tags == expected_tags, (
        f"{control_need} control regressed: {query!r} -> {result.tags}"
    )
    assert "communication" not in result.tags


def test_no_new_word_collides_with_any_other_need_keyword():
    """Each of the 5 newly-added words must be absent from every other
    Need's own KEYWORDS list -- proves this is a precise, non-generic
    vocabulary addition, not overmatching."""
    from temples.domain.need_tags import KEYWORDS

    new_words = {"コミュニケーション", "話せる", "話せない", "伝えられない", "伝わらない"}
    for tag, words in KEYWORDS.items():
        if tag == "communication":
            continue
        overlap = new_words & set(words)
        assert not overlap, f"New communication word(s) {overlap} also present in {tag!r}"


# ---------------------------------------------------------------------------
# Multi-Need extraction behavior and primary Need selection unaffected for
# every other collision case documented in the source audit
# ---------------------------------------------------------------------------


def test_mental_rest_collision_unaffected():
    result = extract_need_tags("心を整えたい", max_tags=3)
    assert result.tags == ["mental", "rest"]


def test_marriage_mental_rest_collision_unaffected():
    result = extract_need_tags("夫婦関係を整えたい", max_tags=3)
    assert result.tags == ["marriage", "mental", "rest"]


# ---------------------------------------------------------------------------
# Normalized payload (resolve_need_payload, the real production entry
# point via concierge_chat_need.py) reflects the same improvement
# ---------------------------------------------------------------------------


def test_resolve_need_payload_reflects_communication_coverage_improvement():
    payload = resolve_need_payload(
        query="コミュニケーション能力を上げたい", need_tags=None, max_tags=3
    )
    assert "communication" in payload["tags"]


# ---------------------------------------------------------------------------
# Synchronization: NEED_KEYWORDS (consultation_interpreter.py, shadow-only)
# stays identical to KEYWORDS (need_tags.py, production) for communication
# ---------------------------------------------------------------------------


def test_shadow_interpreter_vocabulary_stays_synchronized():
    from temples.domain.need_tags import KEYWORDS

    assert list(NEED_KEYWORDS["communication"]) == KEYWORDS["communication"]
