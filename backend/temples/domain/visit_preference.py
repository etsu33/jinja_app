# backend/temples/domain/visit_preference.py
"""Level 2 Visit Preference canonical tag vocabulary (Structured Signal Mapping).

Per docs/product/concierge-input-architecture.md (Addendum: Level 2 Visit
Preference Signal Redesign) and docs/product/visit-style-taxonomy.md, this
module defines the canonical, UI-facing tag vocabulary a client may send
directly (no keyword parsing) as `visit_preferences` on the Concierge Chat
request.

This is a *subset* of `EXTRA_TAG_META`'s `visit_style`-kind tags
(temples/domain/extra_condition_tags.py): `business`/`study`/`urban` remain
valid legacy visit_style tags reachable via free-text `extra_condition`, but
are excluded here because visit-style-taxonomy.md does not treat them as
UI-facing MVP selections. Nothing in this module removes, renames, or
changes the scoring behavior of any existing tag.
"""

from __future__ import annotations

from typing import FrozenSet, Iterable, List

# Canonical Level 2 Visit Preference tags. Every tag here is also a
# `visit_style`-kind tag in EXTRA_TAG_META, so a Structured value here and a
# Legacy free-text-derived tag of the same name feed the exact same
# `score_visit_style` ranking computation (concierge_chat_ranking._attach_breakdown) --
# see resolve_visit_preference_tags() in concierge_chat_extra_condition.py for
# the Compatibility Layer that merges the two without double-counting.
VISIT_PREFERENCE_TAGS: FrozenSet[str] = frozenset(
    {
        "quiet",
        "nature",
        "reset",
        "less_crowded",
        "nearby",
        "classic",
    }
)

# Product decision (Level 2 Redesign, Task 7): the legacy keyword parser's
# `max_tags=3` is an artifact of how `extract_extra_tags()` scores free-text
# hits, not a deliberate Product limit on how many Visit Preferences a user
# may express. Structured input selects tags directly (no parsing), so it
# does not inherit that number. The cap below equals the full canonical
# vocabulary size -- i.e. "no artificial limit below the full vocabulary" --
# while still bounding request size.
MAX_VISIT_PREFERENCES = 6


def normalize_visit_preferences(values: Iterable[object] | None) -> List[str]:
    """Validate + dedupe a raw Structured Visit Preference input.

    Unknown tags are dropped, not raised -- consistent with the rest of the
    Concierge Chat input contract's fail-open compatibility posture (see
    concierge_input_contract.py). Order is preserved, duplicates removed,
    capped at MAX_VISIT_PREFERENCES.
    """
    if not values:
        return []

    out: List[str] = []
    seen: set[str] = set()

    for value in values:
        tag = str(value or "").strip()
        if not tag or tag not in VISIT_PREFERENCE_TAGS or tag in seen:
            continue
        seen.add(tag)
        out.append(tag)
        if len(out) >= MAX_VISIT_PREFERENCES:
            break

    return out


__all__ = [
    "VISIT_PREFERENCE_TAGS",
    "MAX_VISIT_PREFERENCES",
    "normalize_visit_preferences",
]
