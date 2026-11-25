"""ご利益の概念の一覧（v1）の契約。docs/knowledge/goriyaku-concept-rules.md。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from temples.domain.goriyaku_alias_v1 import GORIYAKU_V1_ALIASES
from temples.domain.goriyaku_concepts_v1 import (
    COMBINED_TAG_NAMES,
    CONCEPT_KEY_PATTERN,
    CONCEPTS_BY_KEY,
    GORIYAKU_CONCEPTS,
    NEW_CONCEPT_KEY_MAX_WORDS,
    concept_keys_for_tag_name,
    get_concept,
)
from temples.domain.goriyaku_taxonomy_v1 import GORIYAKU_V1_CANONICAL_KEYS

# 本番の札（39件。docs/audit/goriyaku-mapping-master-integrity.md の正本）。
PRODUCTION_TAG_NAMES = (
    "縁結び", "厄除け", "交通安全", "商売繁盛", "五穀豊穣", "開運", "家内安全", "福徳",
    "学業成就", "合格祈願", "勝運", "仕事運", "航海安全", "海上安全", "武運長久", "安産",
    "八方除", "夫婦円満", "八難除", "恋愛成就", "導き", "美容", "方除け", "健康長寿",
    "芸能", "家庭円満", "出世運", "金運", "芸能運", "強運厄除け", "技芸上達", "八方除け",
    "病気平癒", "火防", "子宝", "心願成就", "延命長寿", "足腰健康", "農業守護",
)
# 手元の開発用の札（46件）にだけある古い7件。
LEGACY_DEV_TAG_NAMES = (
    "子宝・安産", "金運・商売繁盛", "仕事運・出世", "厄除け・方除け", "勝運・必勝祈願", "地域安泰", "開運招福",
)


def test_there_are_31_concepts_with_unique_valid_keys():
    keys = [concept.key for concept in GORIYAKU_CONCEPTS]
    assert len(keys) == 31
    assert len(set(keys)) == 31
    for key in keys:
        assert CONCEPT_KEY_PATTERN.match(key), key
        assert "variant" not in key and "legacy" not in key


def test_new_keys_have_at_most_three_words_and_approved_keys_are_exempt():
    new_keys = [c.key for c in GORIYAKU_CONCEPTS if c.key not in GORIYAKU_V1_CANONICAL_KEYS]
    assert len(new_keys) == 13
    for key in new_keys:
        assert len(key.split("_")) <= NEW_CONCEPT_KEY_MAX_WORDS, key
    # 承認済みの leg_lower_back_health は4語だが、変えずに使う。
    assert get_concept("leg_lower_back_health") is not None


def test_all_approved_keys_are_kept_with_their_labels_except_the_pending_one():
    for key, label in GORIYAKU_V1_CANONICAL_KEYS.items():
        concept = get_concept(key)
        assert concept is not None, key
        if key == "victory_fortune":
            # 「勝負運」は Mother Ship の確認待ち。承認済みの名前は別名に残す。
            assert concept.label_ja == "勝負運"
            assert label in concept.aliases
        else:
            assert concept.label_ja == label


def test_approved_alias_points_to_the_same_concept():
    for name, key in GORIYAKU_V1_ALIASES.items():
        assert concept_keys_for_tag_name(name) == (key,)


@pytest.mark.parametrize("name", PRODUCTION_TAG_NAMES + LEGACY_DEV_TAG_NAMES)
def test_every_known_tag_name_resolves_to_at_least_one_concept(name):
    keys = concept_keys_for_tag_name(name)
    assert keys
    assert all(key in CONCEPTS_BY_KEY for key in keys)


def test_seed_tag_names_are_all_known():
    seed_path = Path(__file__).resolve().parents[1] / "data" / "shrines_seed_clean.json"
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    names = set()
    for item in seed:
        for part in str(item.get("goriyaku") or "").replace("、", "・").replace("/", "・").split("・"):
            if part.strip():
                names.add(part.strip())
    unknown = sorted(name for name in names if not concept_keys_for_tag_name(name))
    assert unknown == []


@pytest.mark.parametrize(
    "name,expected",
    [
        ("八方除け", ("all_direction_warding",)),
        ("方除け", ("all_direction_warding",)),
        ("八難除", ("misfortune_warding",)),
        ("福徳", ("good_fortune",)),
        ("武運長久", ("victory_fortune",)),
        ("勝運", ("victory_fortune",)),
        ("農業守護", ("harvest",)),
        ("延命長寿", ("longevity",)),
        ("航海安全", ("maritime_safety",)),
        ("芸能運", ("performing_arts",)),
        ("金運・商売繁盛", ("financial_fortune", "business_prosperity")),
        ("勝運・必勝祈願", ("victory_fortune",)),
    ],
)
def test_decided_merges(name, expected):
    assert concept_keys_for_tag_name(name) == expected


@pytest.mark.parametrize("value", [None, "", "  ", "必勝", "勝負", 7])
def test_unknown_or_invalid_names_are_unclassified(value):
    assert concept_keys_for_tag_name(value) == ()


def test_names_are_matched_exactly_except_surrounding_spaces():
    assert concept_keys_for_tag_name(" 厄除け ") == ("misfortune_warding",)
    assert concept_keys_for_tag_name("厄除") == ()


def test_combined_tags_only_point_to_known_concepts():
    for keys in COMBINED_TAG_NAMES.values():
        assert keys and all(key in CONCEPTS_BY_KEY for key in keys)
