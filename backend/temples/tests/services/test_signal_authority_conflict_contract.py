# backend/temples/tests/services/test_signal_authority_conflict_contract.py
"""Recommendation Signal Authority: Conflict Rules (§9).

Source of truth: docs/product/recommendation-signal-authority.md §9
"Conflict Rules", which extends the 5 existing Priority/Override Rules of
docs/product/concierge-input-architecture.md §9 with the Signals newly
measured in the audit (PR #2415) and formally decided in PR #2416.

This module covers the two Conflict Rules that had no existing regression
test as of PR #2416 (confirmed by a dedicated test-coverage survey before
writing this module):

- Semantic Fit vs Distance: "現行default weights（public_mode="need",
  flow="A"）でSemantic Fitが優位" -- a Semantic Fit match (need_tags) must
  not be structurally dominated by Distance (Context) under current
  default weights.
- Semantic Fit vs Popularity: same relationship for Popularity (Secondary).

The other 3 Conflict Rules already have dedicated regression coverage and
are intentionally NOT duplicated here (Phase 9: "既存テストとの重複が多い
場合は、既存テストを正本Decisionへ接続する形でも構いません"):

- Intent vs Birth Profile (Intent wins):
  test_concierge_primary_reason_unification_contract.py::test_conflict_consultation_plus_profile_meaning_wins_primary
- Intent vs Visit Preference (Intent wins, need_tag priority(2) < visit_style priority(7)):
  test_concierge_primary_reason_unification_contract.py::test_conflict_consultation_plus_visit_preference_meaning_wins_primary
  test_concierge_primary_reason_unification_contract.py::test_visit_style_is_a_priority_tier_below_element_above_fallback
- Intent vs Explicit Constraint (Explicit Constraint excludes at the
  Candidate SET level, not a ranking-priority competition):
  services/test_signal_authority_eligibility_contract.py::test_goriyaku_tag_ids_is_a_db_level_candidate_eligibility_filter

This module does not change production code, ranking weight, candidate
filtering, or reason generation.
"""

from __future__ import annotations

import pytest

from temples.services.concierge_chat import build_chat_recommendations


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


@pytest.mark.django_db
def test_semantic_fit_vs_distance_conflict_favors_semantic_fit(deterministic):
    """§9 Semantic Fit vs Distance: a candidate with a genuine need_tags
    match must not be structurally dominated by a far-but-empty candidate's
    proximity advantage alone, under current default weights (public_mode
    ="need", flow="A")."""
    a_semantic_far = _shrine(1, "A_semantic_far", astro_tags=["career"], distance_m=30000, popular_score=1.0)
    b_weak_near = _shrine(2, "B_weak_near", astro_tags=[], distance_m=200, popular_score=1.0)

    recs = build_chat_recommendations(
        query="", language="ja", candidates=[a_semantic_far, b_weak_near], need_tags=["career"],
    )
    assert recs["recommendations"][0]["name"] == "A_semantic_far"
    assert recs["recommendations"][0]["_primary_reason_source"] == "need_tag"


@pytest.mark.django_db
def test_semantic_fit_vs_popularity_conflict_favors_semantic_fit(deterministic):
    """§9 Semantic Fit vs Popularity: a candidate with a genuine need_tags
    match must not be structurally dominated by a popular-but-empty
    candidate's popularity advantage alone, under current default weights."""
    a_semantic_unpopular = _shrine(1, "A_semantic_unpopular", astro_tags=["career"], popular_score=0.0, distance_m=1000)
    b_weak_popular = _shrine(2, "B_weak_popular", astro_tags=[], popular_score=10.0, distance_m=1000)

    recs = build_chat_recommendations(
        query="", language="ja", candidates=[a_semantic_unpopular, b_weak_popular], need_tags=["career"],
    )
    assert recs["recommendations"][0]["name"] == "A_semantic_unpopular"
    assert recs["recommendations"][0]["_primary_reason_source"] == "need_tag"
