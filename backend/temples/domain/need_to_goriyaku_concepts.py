# backend/temples/domain/need_to_goriyaku_concepts.py
"""相談の種類（need_tag）→ ご利益の概念の識別子 の対応表。

ルールは docs/knowledge/goriyaku-concept-rules.md（ルール5・6）。

- 対応表には概念の識別子だけを書く。札（GoriyakuTag）の番号・札の名前は書かない。
  札の番号は環境や作る順番で変わるため、番号で結ぶと本番の札とずれる（以前の
  need_to_goriyaku_tag_ids.py で、休息 → 家内安全 などのずれが起きた）。
- 札は、札の名前から goriyaku_concepts_v1.concept_keys_for_tag_name で概念を引き、
  対応表の概念に入っていれば一致とする。未分類の札は一致に使わない。

pure / DB 不要。
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Iterable, List, Optional, Tuple

from temples.domain.goriyaku_concepts_v1 import CONCEPTS_BY_KEY, concept_keys_for_tag_name
from temples.domain.need_tags import NEED_TAGS

# 相談の種類 → 概念の識別子。中身の決め方は docs/knowledge/goriyaku-concept-rules.md の
# 「相談の種類との対応（v1）」を参照。空の行は「札では結ばない」（言葉の一覧や場の性質で選ぶ）。
NEED_TO_GORIYAKU_CONCEPTS: Dict[str, FrozenSet[str]] = {
    "love": frozenset({"love_fulfillment", "relationship_bonding"}),
    "relationship": frozenset({"relationship_bonding"}),
    "marriage": frozenset({"relationship_bonding", "marital_harmony"}),
    # Mother Ship 2026-08-29：Communication = EVIDENCE_LIMITED（札では結ばない）。
    "communication": frozenset(),
    "career": frozenset({"work_fortune", "career_advancement", "guidance"}),
    "money": frozenset({"financial_fortune", "business_prosperity"}),
    "study": frozenset({"academic_success", "exam_success"}),
    "focus": frozenset({"skill_improvement", "academic_success"}),
    # 無病息災（illness_prevention）は、出典を確かめてから概念の一覧と一緒に足す。
    "health": frozenset({"illness_recovery", "longevity", "leg_lower_back_health"}),
    # ご利益ではなく、場の性質で選ぶ。
    "mental": frozenset(),
    "protection": frozenset({"misfortune_warding", "all_direction_warding", "strong_fortune_warding"}),
    "courage": frozenset({"good_fortune", "victory_fortune"}),
    # ご利益ではなく、場の性質で選ぶ。
    "rest": frozenset(),
    # Mother Ship 2026-08-29：Family = NARROW（安産・子宝だけ）。家内安全は結ばない。
    "family": frozenset({"safe_childbirth", "fertility"}),
    "travel_safe": frozenset({"traffic_safety", "maritime_safety"}),
}


def _validate() -> None:
    errors: List[str] = []
    missing = sorted(set(NEED_TAGS) - set(NEED_TO_GORIYAKU_CONCEPTS))
    extra = sorted(set(NEED_TO_GORIYAKU_CONCEPTS) - set(NEED_TAGS))
    if missing:
        errors.append(f"need tags without a row: {missing}")
    if extra:
        errors.append(f"rows for unknown need tags: {extra}")
    for need, keys in NEED_TO_GORIYAKU_CONCEPTS.items():
        unknown = sorted(key for key in keys if key not in CONCEPTS_BY_KEY)
        if unknown:
            errors.append(f"{need}: unknown concept keys {unknown}")
    if errors:
        raise ValueError("need_to_goriyaku_concepts is inconsistent: " + "; ".join(errors))


_validate()


def need_concept_keys(need: object) -> FrozenSet[str]:
    """相談の種類に結びつく概念の識別子。知らない相談の種類は空。"""
    if not isinstance(need, str):
        return frozenset()
    return NEED_TO_GORIYAKU_CONCEPTS.get(need.strip(), frozenset())


def tag_matches_need(tag_name: object, need: object) -> bool:
    """札の名前が、相談の種類に結びつく概念のどれかに入るか。未分類の札は False。"""
    keys = need_concept_keys(need)
    if not keys:
        return False
    return any(key in keys for key in concept_keys_for_tag_name(tag_name if isinstance(tag_name, str) else None))


def matching_tag_names(tag_names: Optional[Iterable[object]], need: object) -> List[str]:
    """札の名前の一覧のうち、相談の種類に一致するもの（並び順はそのまま、同じ名前は1回）。"""
    out: List[str] = []
    for name in tag_names or []:
        if not isinstance(name, str):
            continue
        text = name.strip()
        if text and text not in out and tag_matches_need(text, need):
            out.append(text)
    return out


def needs_for_tag_name(tag_name: object) -> Tuple[str, ...]:
    """札の名前が一致する相談の種類（昇順）。未分類の札は空。"""
    keys = set(concept_keys_for_tag_name(tag_name if isinstance(tag_name, str) else None))
    if not keys:
        return ()
    return tuple(sorted(need for need, need_keys in NEED_TO_GORIYAKU_CONCEPTS.items() if keys & need_keys))


__all__ = [
    "NEED_TO_GORIYAKU_CONCEPTS",
    "matching_tag_names",
    "need_concept_keys",
    "needs_for_tag_name",
    "tag_matches_need",
]
