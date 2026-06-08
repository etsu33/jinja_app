# backend/temples/domain/need_to_goriyaku_tag_ids.py
from __future__ import annotations

from typing import Iterable, Set, Dict

# need_tag -> goriyaku_tag_ids
# TODO: ここにDBのgoriyaku tag idを入れていく（未確定は空でOK）
NEED_TO_GORIYAKU_IDS: Dict[str, Set[int]] = {
    "love": {1, 29},
    "relationship": {1, 27, 34, 43},
    "marriage": {1, 27, 29},
    "communication": {30, 33, 37, 39},
    "career": {6, 21, 30, 35},
    "money": {5, 17, 19, 36},
    "study": {3, 4, 39},
    "health": {7, 8, 44, 45},
    "mental": {11, 16, 26, 28, 38, 43},
    "protection": {11, 16, 26, 28, 32, 38},
    "courage": {12, 15, 18, 20, 24, 30, 38},
    "focus": {3, 4, 39},
    "rest": {7, 8, 43, 44, 45},
    "family": {2, 25, 27, 34, 42},
    "travel_safe": {10, 22, 23},
}

def need_tags_to_goriyaku_ids(tags: Iterable[str]) -> Set[int]:
    """
    need_tags(list[str]) を goriyaku_tag_ids(set[int]) に変換する。
    未定義タグは無視。未割当は空セット。
    """
    out: Set[int] = set()
    for t in tags or []:
        key = str(t).strip()
        if not key:
            continue
        out |= NEED_TO_GORIYAKU_IDS.get(key, set())
    return out
