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
    # docs/audit/goriyaku-mapping-master-integrity-correction.md.
    #
    # relationship/health/focus/family corrected against real GoriyakuTag
    # labels; see docs/audit/remaining-need-goriyaku-semantic-mapping.md
    # (SAFE_CORRECTIONS, Section 19) for the VALID/QUESTIONABLE/INVALID/
    # CLEAR_MISSING classification this is based on. communication/mental/
    # courage remain unchanged pending Mother Ship product decisions (same
    # document, Section 20).
    #
    # marriage corrected to {1, 18} (縁結び VALID + 夫婦円満 CLEAR_MISSING;
    # 27/29 INVALID, fresh-classified) and is now independently reachable --
    # NEED_TAG_ALIASES["marriage"]="love" was removed, see
    # docs/audit/marriage-love-alias-boundary.md and
    # docs/audit/marriage-need-independence-implementation.md.
    "love": {1, 20},
    "relationship": {1},
    "marriage": {1, 18},
    "communication": {30, 33, 37, 39},
    "career": {6, 21, 30, 12, 27},
    "money": {5, 36, 4, 28},
    "study": {9, 10},
    "health": {7, 8, 24, 33, 38},
    "mental": {11, 16, 26, 28, 38},
    "protection": {11, 32, 2},
    "courage": {12, 15, 18, 20, 24, 30, 38},
    "focus": {9, 10},
    "rest": {7, 8},
    "family": {2, 26, 34},
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
