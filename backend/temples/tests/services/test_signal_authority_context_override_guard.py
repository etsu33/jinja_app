# backend/temples/tests/services/test_signal_authority_context_override_guard.py
"""Context Override Guard: Primary Semantic Authority Protection.

Audit follow-up to docs/product/recommendation-signal-authority.md (#2416)
and its regression tests (#2417). Phase 2 conflict experiments found one
Contract Violation not covered by the existing Signal Authority Contract
Tests: `_sort_chat_recommendations()`'s `distance_mode` (triggered when
free text matches a "sort_distance" trigger word -- "近い"/"近く"/"徒歩"/
"できるだけ近"/"最寄り"/"距離優先", see temples/domain/extra_condition_tags.py)
sorted purely by `distance_m`, demoting `_score_total` (which carries 100%
of Consultation Meaning / Shrine-side Evidence) to a tiebreaker. That let a
candidate with zero semantic connection to the user's stated need (
`_primary_reason_source == "fallback"`) outrank a candidate with a genuine
`need_tags` match, purely because it happened to sit closer.

Fix (`has_primary_tier_reason()` in concierge_chat_ranking.py, used only
inside `_sort_chat_recommendations()`'s distance_mode branch): tier
distance_mode candidates by whether they have an established Primary
Recommendation Meaning (§7) first, then sort by distance within each tier.
This still gives Context (distance) full authority to *reorder* -- both
within the Primary tier, and across all candidates when nobody has
established Primary Recommendation Meaning at all (the legitimate "just
show me something nearby" case) -- but Context can no longer *decide*
Recommendation Meaning by promoting a semantically-empty candidate over a
genuine match.

This module does not change ranking weight, candidate filtering, Primary
Reason resolution logic (`_resolve_primary_reason`/`_build_reason_facts`
are untouched), or the API response shape -- only the sort comparator used
inside the pre-existing distance_mode branch.
"""

from __future__ import annotations

import pytest

from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_ranking import (
    PRIMARY_TIER_REASON_TYPES,
    has_primary_tier_reason,
)


def _shrine(id_, name, **overrides):
    base = {
        "id": id_,
        "shrine_id": id_,
        "name": name,
        "address": f"テスト所在地{id_}",
        "lat": 35.0,
        "lng": 139.0,
        "distance_m": 1000,
        "goriyaku": "",
        "description": "",
        "goriyaku_tag_ids": [],
        "astro_tags": [],
        "astro_elements": [],
        "astro_priority": 0,
        "visit_style_tags": [],
        "history_theme": "",
        "popular_score": 0.5,
    }
    base.update(overrides)
    return base


@pytest.fixture
def deterministic(settings):
    settings.CONCIERGE_USE_LLM = False


def test_primary_tier_reason_types_excludes_element_and_visit_style():
    """has_primary_tier_reason() must only recognize the Consultation
    Meaning / Shrine-side Evidence types (§7) -- element (birthdate) and
    visit_style must never count, since §7 fixes that neither alone
    constitutes Recommendation Meaning."""
    assert PRIMARY_TIER_REASON_TYPES == {
        "history_theme", "culture_translation", "need_tag", "text_hint", "user_selected_tag", "goriyaku_tag",
    }
    assert has_primary_tier_reason([{"type": "element"}]) is False
    assert has_primary_tier_reason([{"type": "visit_style"}]) is False
    assert has_primary_tier_reason([{"type": "fallback"}]) is False
    assert has_primary_tier_reason([{"type": "need_tag"}]) is True
    assert has_primary_tier_reason([]) is False
    assert has_primary_tier_reason(None) is False


@pytest.mark.django_db
def test_sort_distance_does_not_override_a_genuine_need_tags_match(deterministic):
    """Reproduces the Contract Violation found in Phase 2 Case A2: a query
    that both establishes a real need_tags match AND triggers the
    sort_distance override ("近くの神社で仕事の相談をしたいです") must
    still keep the semantically-matched candidate on top, even though a
    semantically-empty candidate is much closer."""
    a_semantic_far = _shrine(1, "A_semantic_far", astro_tags=["career"], distance_m=30000)
    b_near_empty = _shrine(2, "B_near_empty", distance_m=200)

    recs = build_chat_recommendations(
        query="近くの神社で仕事の相談をしたいです", language="ja",
        candidates=[a_semantic_far, b_near_empty],
    )
    assert recs["recommendations"][0]["name"] == "A_semantic_far"
    assert recs["recommendations"][0]["_primary_reason_source"] == "need_tag"


@pytest.mark.django_db
def test_sort_distance_does_not_let_personalization_hijack_primary_reason(deterministic):
    """Phase 2 Case D2: once distance_mode incorrectly won the sort, a
    Personalization signal (birthdate/element) on the semantically-empty
    near candidate opportunistically became the visible Primary Reason.
    The tiering fix must prevent this too."""
    a_semantic_far = _shrine(1, "A_semantic_far", astro_tags=["career"], distance_m=30000, astro_elements=["水"])
    b_near_birth_match = _shrine(2, "B_near_birth_match", distance_m=200, astro_elements=["火"])

    recs = build_chat_recommendations(
        query="近くの神社で仕事の相談をしたいです", language="ja",
        candidates=[a_semantic_far, b_near_birth_match],
        birthdate="1990-08-01", public_mode="compat",
    )
    assert recs["recommendations"][0]["name"] == "A_semantic_far"
    assert recs["recommendations"][0]["_primary_reason_source"] == "need_tag"


@pytest.mark.django_db
def test_sort_distance_still_orders_purely_by_distance_when_nothing_is_semantically_matched(deterministic):
    """Legitimate Context authority is preserved: when no candidate has
    established Primary Recommendation Meaning at all, distance_mode must
    still sort purely by distance -- the guard only activates when there
    is a genuine conflict to protect, not unconditionally."""
    a_far = _shrine(1, "A_far_no_semantic", distance_m=30000)
    b_near = _shrine(2, "B_near_no_semantic", distance_m=200)

    recs = build_chat_recommendations(
        query="近くの神社を教えて", language="ja", candidates=[a_far, b_near],
    )
    names = [r["name"] for r in recs["recommendations"]]
    assert names == ["B_near_no_semantic", "A_far_no_semantic"]


@pytest.mark.django_db
def test_sort_distance_orders_by_distance_within_the_primary_tier(deterministic):
    """Within the Primary tier, distance_mode must still fully control
    order (Context legitimately re-ranks among candidates that already
    have Recommendation Meaning)."""
    near_match = _shrine(1, "Near_match", astro_tags=["career"], distance_m=300)
    far_match = _shrine(2, "Far_match", astro_tags=["career"], distance_m=3000)

    recs = build_chat_recommendations(
        query="近くの神社で仕事の相談をしたいです", language="ja",
        candidates=[far_match, near_match],
    )
    names = [r["name"] for r in recs["recommendations"]]
    assert names == ["Near_match", "Far_match"]
