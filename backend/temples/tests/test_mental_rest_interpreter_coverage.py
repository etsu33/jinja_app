# backend/temples/tests/test_mental_rest_interpreter_coverage.py
"""Mental interpreter coverage for calming-intent language (Track D1a).

Implements the Mother Ship decision Mental/Rest = ``EXPAND_MENTAL``
(docs/audit/remaining-need-semantic-decision-packets.md, Sections 16-17
Option C / Section 28 Track D1a).

Gap: the natural-language query ``気持ちを落ち着けたい`` resolved to
``['rest']`` only -- ``mental`` was entirely absent -- because ``rest``
owns the bare ``落ち着`` root REGEX while ``mental`` had no coverage for the
desiderative calming form ``落ち着けたい`` / ``落ち着けたく``.

Fix (additive, interpreter-only): one new ``mental`` REGEX entry
``re.compile(r"落ち着け(たい|たく)")`` in temples/domain/need_tags.py. It is
deliberately limited to the desiderative form so that:

- ``落ち着けたい`` (intent to calm oneself) -> adds ``mental``;
- ``落ち着ける（場所）`` (potential/adnominal, e.g. "落ち着ける場所に行きたい")
  and ``落ち着けて`` (connective) are NOT matched -- existing ``rest``-only
  behavior for those is preserved.

Scope: temples/domain/need_tags.py REGEX["mental"] only. ``rest``
KEYWORDS/REGEX, NEED_PRIORITY, NEED_TO_GORIYAKU_IDS, consultation axis,
Reason copy, C1 scoring, Ranking and Lead are all unchanged.
"""

from __future__ import annotations

import pytest

from temples.domain.need_tags import KEYWORDS, REGEX, extract_need_tags


# ---------------------------------------------------------------------------
# Target: the recorded interpreter gap is closed
# ---------------------------------------------------------------------------


def test_calming_intent_query_now_extracts_both_mental_and_rest():
    result = extract_need_tags("気持ちを落ち着けたい", max_tags=3)
    assert result.tags == ["mental", "rest"]
    assert "落ち着けたい" in result.hits["mental"]


@pytest.mark.parametrize(
    "query",
    [
        "気持ちを落ち着けたい",
        "気持ちを落ち着けたくて仕方ない",
    ],
)
def test_desiderative_calming_forms_add_mental(query):
    result = extract_need_tags(query, max_tags=3)
    assert "mental" in result.tags
    assert "rest" in result.tags


# ---------------------------------------------------------------------------
# The recorded Section 16 seven-query mental/rest corpus: the target row
# changes as intended; the other six rows are byte-for-byte unchanged.
# ---------------------------------------------------------------------------


SECTION_16_CORPUS_AFTER = [
    ("気持ちを落ち着けたい", ["mental", "rest"]),  # intended change (was ['rest'])
    ("心を整えたい", ["mental", "rest"]),
    ("不安を和らげたい", ["mental"]),
    ("少し休みたい", ["rest"]),
    ("静かに過ごしたい", ["rest"]),
    ("疲れを癒したい", ["mental", "rest"]),
    ("落ち着ける場所に行きたい", ["rest"]),
]


@pytest.mark.parametrize(("query", "expected"), SECTION_16_CORPUS_AFTER)
def test_section_16_corpus(query, expected):
    assert extract_need_tags(query, max_tags=3).tags == expected


# ---------------------------------------------------------------------------
# Regression guards: forms that must NOT newly gain mental
# ---------------------------------------------------------------------------


def test_potential_adnominal_form_stays_rest_only():
    """'落ち着ける場所' is locational (a place one can settle), not calming
    intent -- it must keep resolving to rest only."""
    result = extract_need_tags("落ち着ける場所に行きたい", max_tags=3)
    assert result.tags == ["rest"]
    assert "mental" not in result.hits


def test_connective_form_is_not_force_flipped_to_mental():
    """'気持ちを落ち着けて静かに過ごしたい' (連用/接続形) is not covered by the
    desiderative-only pattern; its existing rest resolution is unchanged."""
    result = extract_need_tags("気持ちを落ち着けて静かに過ごしたい", max_tags=3)
    assert result.tags == ["rest"]
    assert "mental" not in result.hits


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("転職を考えている", ["career"]),
        ("子宝に恵まれたい", ["family"]),
        ("試験に合格したい", ["study"]),
        ("いい出会いがほしい", ["love"]),
    ],
)
def test_unrelated_queries_do_not_gain_mental(query, expected):
    result = extract_need_tags(query, max_tags=3)
    assert result.tags == expected
    assert "mental" not in result.tags


def test_existing_mental_rest_collision_unchanged():
    assert extract_need_tags("心を整えたい", max_tags=3).tags == ["mental", "rest"]
    assert extract_need_tags("夫婦関係を整えたい", max_tags=3).tags == [
        "marriage",
        "mental",
        "rest",
    ]


# ---------------------------------------------------------------------------
# rest's own configuration is untouched
# ---------------------------------------------------------------------------


def test_rest_keyword_and_regex_config_unchanged():
    assert KEYWORDS["rest"] == [
        "休みたい", "休息", "疲れ", "回復", "睡眠", "眠れない", "リセット",
        "穏やか", "静か", "落ち着きたい", "落ち着く", "心を整えたい",
        "整えたい", "自然", "ゆっくり", "過ごしたい", "癒し",
        "ひと息", "ひと息つきたい", "日常から離れたい", "離れて", "慌ただしい",
    ]
    assert [p.pattern for p in REGEX["rest"]] == [
        r"(穏やか|静か|落ち着|リセット|休息|癒し|ひと息|一息)"
    ]


def test_new_mental_pattern_is_desiderative_only():
    mental_patterns = [p.pattern for p in REGEX["mental"]]
    assert r"落ち着け(たい|たく)" in mental_patterns
    import re

    pat = re.compile(r"落ち着け(たい|たく)")
    assert pat.search("気持ちを落ち着けたい")
    assert pat.search("落ち着けたくなる")
    assert not pat.search("落ち着ける場所に行きたい")
    assert not pat.search("気持ちを落ち着けて過ごす")
