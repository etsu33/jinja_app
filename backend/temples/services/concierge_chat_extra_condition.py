from __future__ import annotations

from typing import Dict, Iterable, Optional, Set

from temples.domain.extra_condition_tags import extract_extra_tags, split_tags_by_kind
from temples.domain.visit_preference import VISIT_PREFERENCE_TAGS


def resolve_extra_condition_tags(
    extra_condition: Optional[str],
) -> Dict[str, Set[str]]:
    """
    extra_condition から sort / hard_filter / soft_signal / visit_style のタグ群を取り出す。
    失敗時は空集合を返す。
    """
    sort_tags: Set[str] = set()
    hard_filter_tags: Set[str] = set()
    soft_signal_tags: Set[str] = set()
    visit_style_tags: Set[str] = set()

    try:
        ex = extract_extra_tags(extra_condition or "", max_tags=3)
        kinds = split_tags_by_kind(ex.tags)
        sort_tags = set(kinds.get("sort_override") or [])
        hard_filter_tags = set(kinds.get("hard_filter") or [])
        soft_signal_tags = set(kinds.get("soft_signal") or [])
        visit_style_tags = set(kinds.get("visit_style") or [])
    except Exception:
        sort_tags = set()
        hard_filter_tags = set()
        soft_signal_tags = set()
        visit_style_tags = set()

    return {
        "sort_tags": sort_tags,
        "hard_filter_tags": hard_filter_tags,
        "soft_signal_tags": soft_signal_tags,
        "visit_style_tags": visit_style_tags,
    }


def resolve_visit_preference_tags(
    *,
    structured: Optional[Iterable[str]],
    legacy_visit_style_tags: Set[str],
) -> Set[str]:
    """Level 2 Visit Preference Compatibility Layer (Structured + Legacy).

    Merges a Structured `visit_preferences` selection (validated, canonical
    tags -- see temples/domain/visit_preference.py) with the Legacy
    extra_condition-derived `visit_style_tags` (free-text keyword parsing,
    resolve_extra_condition_tags() above).

    Both sides resolve into the *same* canonical tag vocabulary, so a plain
    set union is enough to dedupe: `score_visit_style` (concierge_chat_ranking
    ._attach_breakdown) counts distinct matched tag names, not occurrences,
    so a tag present in both Structured and Legacy still contributes once
    -- no double-counting regardless of which side(s) produced it.
    """
    structured_tags = {
        str(tag).strip()
        for tag in (structured or [])
        if str(tag).strip() in VISIT_PREFERENCE_TAGS
    }
    return structured_tags | (legacy_visit_style_tags or set())


__all__ = [
    "resolve_extra_condition_tags",
    "resolve_visit_preference_tags",
]
