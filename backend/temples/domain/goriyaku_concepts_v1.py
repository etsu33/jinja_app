# backend/temples/domain/goriyaku_concepts_v1.py
"""ご利益の概念の一覧（v1）。

ルールは docs/knowledge/goriyaku-concept-rules.md。この一覧がその正本である。

- 概念は「参拝する人の願いの単位」。識別子は言語に依存しない英語のスネークケース。
- 札（GoriyakuTag）の名前は、概念の表示名・別名・組み合わせの札・未分類のどれか。
- 承認済みの18件（goriyaku_taxonomy_v1.GORIYAKU_V1_CANONICAL_KEYS）の識別子はそのまま使う。

pure / DB 不要。この一覧はまだ推薦・相談の対応表から使われていない（次の作業でつなぐ）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from temples.domain.goriyaku_taxonomy_v1 import GORIYAKU_V1_CANONICAL_KEYS

# 識別子の書き方（英小文字・数字・アンダースコア）。
CONCEPT_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
# 新しく作る識別子は英単語1〜3語まで。承認済みの18件はそのまま使うため、この決まりの外。
NEW_CONCEPT_KEY_MAX_WORDS = 3


@dataclass(frozen=True)
class GoriyakuConcept:
    """ご利益の概念1件。

    key       言語に依存しない識別子（一度決めたら変えない）
    label_ja  日本語の表示名
    aliases   表記ゆれ・意味の近い札の名前（この概念にまとめる）
    """

    key: str
    label_ja: str
    aliases: Tuple[str, ...] = ()


# victory_fortune の表示名は、承認済みの一覧（goriyaku_taxonomy_v1）では「勝運」。
# 「勝負運」への変更は Mother Ship の確認待ち。確認が取れるまでは、画面などの表示を変えない。
VICTORY_FORTUNE_LABEL_PENDING_APPROVAL = True

GORIYAKU_CONCEPTS: Tuple[GoriyakuConcept, ...] = (
    # 縁・家庭
    GoriyakuConcept("relationship_bonding", "縁結び"),
    GoriyakuConcept("love_fulfillment", "恋愛成就"),
    GoriyakuConcept("marital_harmony", "夫婦円満"),
    GoriyakuConcept("family_harmony", "家庭円満"),
    # 守り
    GoriyakuConcept("misfortune_warding", "厄除け", ("八難除",)),
    GoriyakuConcept("all_direction_warding", "八方除", ("八方除け", "方除け")),
    GoriyakuConcept("strong_fortune_warding", "強運厄除け"),
    GoriyakuConcept("fire_prevention", "火防"),
    # 運・勝負
    GoriyakuConcept("good_fortune", "開運", ("開運招福", "福徳")),
    GoriyakuConcept("victory_fortune", "勝負運", ("勝運", "武運長久")),
    # 仕事・財
    GoriyakuConcept("work_fortune", "仕事運"),
    GoriyakuConcept("career_advancement", "出世運"),
    GoriyakuConcept("guidance", "導き"),
    GoriyakuConcept("business_prosperity", "商売繁盛"),
    GoriyakuConcept("financial_fortune", "金運"),
    GoriyakuConcept("harvest", "五穀豊穣", ("農業守護",)),
    # 学び・技
    GoriyakuConcept("academic_success", "学業成就"),
    GoriyakuConcept("exam_success", "合格祈願"),
    GoriyakuConcept("skill_improvement", "技芸上達"),
    GoriyakuConcept("performing_arts", "芸能", ("芸能運",)),
    # 健康
    GoriyakuConcept("longevity", "健康長寿", ("延命長寿",)),
    GoriyakuConcept("illness_recovery", "病気平癒"),
    GoriyakuConcept("leg_lower_back_health", "足腰健康"),
    GoriyakuConcept("beauty", "美容"),
    # 子ども
    GoriyakuConcept("safe_childbirth", "安産"),
    GoriyakuConcept("fertility", "子宝"),
    # 安全・安泰
    GoriyakuConcept("household_safety", "家内安全"),
    GoriyakuConcept("traffic_safety", "交通安全"),
    GoriyakuConcept("maritime_safety", "海上安全", ("航海安全",)),
    GoriyakuConcept("regional_peace", "地域安泰"),
    # 願い全般
    GoriyakuConcept("wish_fulfillment", "心願成就"),
)

# 願いが2つ入った札の名前 → 分けた先の概念の識別子（並びは札の名前の中の順）。
COMBINED_TAG_NAMES: Dict[str, Tuple[str, ...]] = {
    "子宝・安産": ("fertility", "safe_childbirth"),
    "金運・商売繁盛": ("financial_fortune", "business_prosperity"),
    "仕事運・出世": ("work_fortune", "career_advancement"),
    "厄除け・方除け": ("misfortune_warding", "all_direction_warding"),
    # 勝運も必勝祈願も勝負運の概念に入るため、分けた先は1つ。
    "勝運・必勝祈願": ("victory_fortune",),
}


def _build_indexes() -> Tuple[Dict[str, GoriyakuConcept], Dict[str, str]]:
    by_key: Dict[str, GoriyakuConcept] = {}
    key_by_name: Dict[str, str] = {}
    errors = []
    for concept in GORIYAKU_CONCEPTS:
        if not CONCEPT_KEY_PATTERN.match(concept.key):
            errors.append(f"invalid key: {concept.key!r}")
        elif (
            concept.key not in GORIYAKU_V1_CANONICAL_KEYS
            and len(concept.key.split("_")) > NEW_CONCEPT_KEY_MAX_WORDS
        ):
            errors.append(f"new key has too many words: {concept.key!r}")
        if concept.key in by_key:
            errors.append(f"duplicate key: {concept.key!r}")
        by_key[concept.key] = concept
        for name in (concept.label_ja, *concept.aliases):
            if name in key_by_name or name in COMBINED_TAG_NAMES:
                errors.append(f"name used twice: {name!r}")
            key_by_name[name] = concept.key
    for name, keys in COMBINED_TAG_NAMES.items():
        for key in keys:
            if key not in by_key:
                errors.append(f"combined tag {name!r} points to unknown key {key!r}")
    if errors:
        raise ValueError("goriyaku_concepts_v1 is inconsistent: " + "; ".join(errors))
    return by_key, key_by_name


CONCEPTS_BY_KEY, _CONCEPT_KEY_BY_NAME = _build_indexes()


def get_concept(key: str) -> Optional[GoriyakuConcept]:
    """識別子から概念を返す。無ければ None。"""
    return CONCEPTS_BY_KEY.get(key)


def concept_keys_for_tag_name(name: Optional[str]) -> Tuple[str, ...]:
    """札の名前から、結びつく概念の識別子を返す。

    表示名・別名なら1件、組み合わせの札なら分けた先の一覧、未分類なら空。
    名前は完全一致で比べる（前後の空白だけは取り除く）。
    """
    if not isinstance(name, str):
        return ()
    text = name.strip()
    if not text:
        return ()
    if text in COMBINED_TAG_NAMES:
        return COMBINED_TAG_NAMES[text]
    key = _CONCEPT_KEY_BY_NAME.get(text)
    return (key,) if key else ()


__all__ = [
    "COMBINED_TAG_NAMES",
    "CONCEPTS_BY_KEY",
    "CONCEPT_KEY_PATTERN",
    "GORIYAKU_CONCEPTS",
    "GoriyakuConcept",
    "NEW_CONCEPT_KEY_MAX_WORDS",
    "VICTORY_FORTUNE_LABEL_PENDING_APPROVAL",
    "concept_keys_for_tag_name",
    "get_concept",
]
