# backend/temples/domain/need_to_goriyaku_tag_ids.py
from __future__ import annotations

from typing import Iterable, Set, Dict

# need_tag -> goriyaku_tag_ids
# TODO: ここにDBのgoriyaku tag idを入れていく（未確定は空でOK）
NEED_TO_GORIYAKU_IDS: Dict[str, Set[int]] = {
    # love/career/money/study/protection corrected against real GoriyakuTag
    # labels; see docs/audit/compass-purpose-goriyaku-mapping.md for the
    # per-ID VALID/QUESTIONABLE/INVALID/MISSING classification this is
    # based on. Other purposes intentionally left untouched (out of scope).
    #
    # ids 42/43/44/45 removed (stale references to ids absent from the
    # current 39-row canonical master; travel_safe corrected to the
    # canonical master's actual travel-safety labels; see
    # docs/audit/goriyaku-mapping-master-integrity.md and
    # docs/audit/goriyaku-mapping-master-integrity-correction.md. Remaining
    # QUESTIONABLE/broken mappings for the other Purposes are unchanged and
    # out of scope for this correction.
    "love": {1, 20},
    "relationship": {1, 27, 34},
    "marriage": {1, 27, 29},
    "communication": {30, 33, 37, 39},
    "career": {6, 21, 30, 12, 27},
    "money": {5, 36, 4, 28},
    "study": {9, 10},
    "health": {7, 8},
    "mental": {11, 16, 26, 28, 38},
    "protection": {11, 32, 2},
    "courage": {12, 15, 18, 20, 24, 30, 38},
    "focus": {3, 4, 39},
    "rest": {7, 8},
    "family": {2, 25, 27, 34},
    "travel_safe": {3, 13, 14},
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
