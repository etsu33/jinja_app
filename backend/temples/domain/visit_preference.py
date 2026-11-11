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


# 相談の種類から自動で足す参拝の好み。休息・不安の相談では、ご利益・歴史のテーマなどの
# 手がかりが少ないため、場の性質（静か・自然・人が少なめ）を順位にだけ効かせる。
# - 自動で足した好みは点数にだけ使い、主な根拠・説明の文には使わない
#   （concierge_chat_ranking._attach_breakdown の implied_visit_style_tags）。
# - 利用者が選んだ好み・相談文の言葉から拾った好みと同じものは足さない（重ねて数えない）。
# - 何個一致しても、点数は IMPLIED_VISIT_STYLE_MAX_MATCHES 個分まで。
NEED_IMPLIED_VISIT_STYLE_TAGS: dict[str, FrozenSet[str]] = {
    "rest": frozenset({"quiet", "nature", "less_crowded"}),
    "mental": frozenset({"quiet", "nature", "less_crowded"}),
}
IMPLIED_VISIT_STYLE_MAX_MATCHES = 1


def implied_visit_style_tags_for_needs(
    need_tags: Iterable[object] | None,
    *,
    explicit_tags: Iterable[object] | None = None,
) -> FrozenSet[str]:
    """相談の種類から自動で足す参拝の好み（explicit_tags にあるものは除く）。"""
    implied: set[str] = set()
    for need in need_tags or []:
        implied |= NEED_IMPLIED_VISIT_STYLE_TAGS.get(str(need or "").strip(), frozenset())
    explicit = {str(tag or "").strip() for tag in (explicit_tags or [])}
    return frozenset(implied - explicit)


__all__ = [
    "VISIT_PREFERENCE_TAGS",
    "MAX_VISIT_PREFERENCES",
    "NEED_IMPLIED_VISIT_STYLE_TAGS",
    "IMPLIED_VISIT_STYLE_MAX_MATCHES",
    "implied_visit_style_tags_for_needs",
    "normalize_visit_preferences",
]
