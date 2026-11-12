# -*- coding: utf-8 -*-
"""英語の特徴語辞書（temples/domain/feature_words_en.py）の単体テスト。"""

import pytest

from temples.domain.feature_words_en import (
    CATEGORIES,
    FEATURE_WORDS,
    extract_feature_words,
    is_english_request,
)


def test_vocabulary_matches_the_spreadsheet_shape():
    # スプレッドシート「語彙」タブ（2026-11-12）の41語・4分類と一致すること
    assert len(FEATURE_WORDS) == 41
    ids = [w.id for w in FEATURE_WORDS]
    assert len(ids) == len(set(ids))
    counts = {c: sum(1 for w in FEATURE_WORDS if w.category == c) for c in CATEGORIES}
    assert counts == {"Sight": 10, "Craft": 9, "Story": 11, "Feel": 11}
    assert all(w.synonyms for w in FEATURE_WORDS)


def test_each_synonym_belongs_to_only_one_feature_word():
    # 同じ言葉が2つの特徴語に入っていると、どちらに当たるかが辞書の並び順で決まってしまう
    seen = {}
    for w in FEATURE_WORDS:
        for syn in w.synonyms:
            key = syn.lower()
            assert key not in seen, f"{syn!r} is in both {seen[key]} and {w.id}"
            seen[key] = w.id


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Somewhere quiet with old trees", ["S_FOREST", "F_QUIET"]),
        ("dog friendly hike with a view", ["S_VIEW", "F_HIKE", "F_DOG"]),
        ("I love anime", ["ST_POP_CULTURE"]),
        ("Any café near Akasaka?", ["F_CAFE"]),
        ("TOKUGAWA SHOGUNS", ["ST_SHOGUN"]),
    ],
)
def test_extracts_feature_words(text, expected):
    assert extract_feature_words(text).ids == expected


def test_matches_on_word_boundaries_only():
    # red は tired に、tea は steam に、eat は great に当たらない
    assert extract_feature_words("I feel tired after a great steam bath").ids == []
    assert extract_feature_words("red gates").ids == ["C_VERMILION"]


def test_longer_phrase_wins_over_the_shorter_word_inside_it():
    # national treasure（国宝）の中の treasure（宝物殿）を重ねて拾わない
    result = extract_feature_words("Where can I see a national treasure?")
    assert result.ids == ["C_NATIONAL_TREASURE"]
    assert result.hits == {"C_NATIONAL_TREASURE": ["national treasure"]}
    # treasure 単独なら宝物殿
    assert extract_feature_words("treasure museum").ids == ["C_TREASURE_HALL"]


def test_no_match_and_empty_input():
    for text in ["I want to rest", "", "   ", None, "静かな神社"]:
        result = extract_feature_words(text)
        assert result.ids == []
        assert result.matched is False


def test_payload_shape():
    payload = extract_feature_words("quiet forest").as_payload()
    assert set(payload) == {"version", "ids", "hits", "matched"}
    assert payload["ids"] == ["S_FOREST", "F_QUIET"]
    assert payload["matched"] is True


@pytest.mark.parametrize(
    "language, expected",
    [
        ("en", True),
        ("EN", True),
        ("en-US", True),
        (" en ", True),
        ("ja", False),
        ("", False),
        (None, False),
        ("eng", False),
    ],
)
def test_is_english_request(language, expected):
    assert is_english_request(language) is expected
