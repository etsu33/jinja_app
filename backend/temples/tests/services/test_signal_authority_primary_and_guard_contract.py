# backend/temples/tests/services/test_signal_authority_primary_and_guard_contract.py
"""Recommendation Signal Authority: Primary Recommendation Contract + Non-Primary Guard.

Source of truth: docs/product/recommendation-signal-authority.md (PR #2416,
"Recommendation Signal Authority Decision"). This module fixes the Decision
Document's §7 "Primary Recommendation Contract" as permanent regression
tests -- NOT because this happens to be current production behavior, but
because the Decision Document formally adopted this Authority.

Recommendation Meaning (§7):
    Recommendation Meaning
      = User Consultation Meaning (need_tags / consultation_axis / history_theme)
      x Shrine-side Meaning/Evidence (goriyaku match / history_theme)

§7 also fixes that distance / popularity / birthdate / direction / behavior /
visit_style must never, by themselves, constitute Primary Recommendation --
even when they visibly move score/ranking (score contribution and Primary
Recommendation Meaning are explicitly different claims per the Decision Doc).

This module does not change production code, ranking weight, candidate
filtering, reason generation, or UI. It only asserts against the existing
`build_chat_recommendations()` facade with synthetic candidate dicts.

Cross-references (already covered elsewhere, not duplicated here):
- distance alone never Primary:
  test_concierge_primary_reason_unification_contract.py::test_context_only_never_becomes_primary_meaning_reason
- visit_style priority tier / Intent vs Visit Preference:
  test_concierge_primary_reason_unification_contract.py::test_visit_style_is_a_priority_tier_below_element_above_fallback
  test_concierge_primary_reason_unification_contract.py::test_conflict_consultation_plus_visit_preference_meaning_wins_primary
- Intent vs Birth Profile (element):
  test_concierge_primary_reason_unification_contract.py::test_conflict_consultation_plus_profile_meaning_wins_primary
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from temples.models import Shrine, ShrineInteractionLog
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_ranking import (
    PRIMARY_REASON_PRIORITY,
    resolve_history_theme_candidate_boost,
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
        "knowledge_deities": [],
        "knowledge_histories": [],
    }
    base.update(overrides)
    return base


def _run(*, query="", candidates, **kwargs):
    kwargs.setdefault("language", "ja")
    kwargs.setdefault("public_mode", "need")
    kwargs.setdefault("flow", "A")
    return build_chat_recommendations(query=query, candidates=candidates, **kwargs)


@pytest.fixture
def deterministic(settings):
    settings.CONCIERGE_USE_LLM = False


# ---------------------------------------------------------------------------
# Primary Recommendation Contract (§7): Consultation Meaning x Shrine-side
# Evidence order-flips a Context/Secondary-favored candidate.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_need_tags_match_overtakes_context_favored_candidate(deterministic):
    """need_tags is the Primary Recommendation Meaning's User Consultation
    Meaning factor (§7). A candidate matching need_tags must be able to
    overtake a candidate favored purely by distance/popularity (Context/
    Secondary)."""
    a_meaningful = _shrine(1, "A_career", astro_tags=["career"], distance_m=20000, popular_score=0.0)
    b_context_favored = _shrine(2, "B_context_favored", distance_m=100, popular_score=8.0)
    candidates = [a_meaningful, b_context_favored]

    baseline = _run(candidates=candidates)
    assert baseline["recommendations"][0]["name"] == "B_context_favored"

    variant = _run(candidates=candidates, need_tags=["career"])
    assert variant["recommendations"][0]["name"] == "A_career"
    assert variant["recommendations"][0]["_primary_reason_source"] == "need_tag"


@pytest.mark.django_db
def test_goriyaku_free_text_semantic_match_overtakes_context_favored_candidate(deterministic):
    """goriyaku (free text) is the Shrine-side Meaning/Evidence factor of
    Recommendation Meaning (§7). A candidate whose goriyaku text
    semantically matches need_tags (text_hint) must be able to overtake a
    candidate favored purely by distance/popularity."""
    a_semantic = _shrine(
        1, "A_semantic_goriyaku",
        goriyaku="縁結び・恋愛成就のご利益で知られています",
        distance_m=20000, popular_score=0.0,
    )
    b_context_favored = _shrine(2, "B_context_favored", distance_m=100, popular_score=8.0)
    candidates = [a_semantic, b_context_favored]

    baseline = _run(candidates=candidates)
    assert baseline["recommendations"][0]["name"] == "B_context_favored"

    variant = _run(candidates=candidates, need_tags=["love"])
    assert variant["recommendations"][0]["name"] == "A_semantic_goriyaku"
    assert variant["recommendations"][0]["_primary_reason_source"] == "text_hint"


@pytest.mark.django_db
def test_consultation_axis_history_theme_boost_is_zero_when_axis_does_not_match():
    assert resolve_history_theme_candidate_boost(consultation_axis="other", history_theme="縁") == 0.0
    assert resolve_history_theme_candidate_boost(consultation_axis=None, history_theme="縁") == 0.0
    assert resolve_history_theme_candidate_boost(consultation_axis="relationship_repair", history_theme="") == 0.0


@pytest.mark.django_db
def test_consultation_axis_history_theme_correspondence_is_primary_authority(deterministic):
    """consultation_axis x history_theme correspondence (§6/§7): when the
    resolved consultation_axis matches a candidate's history_theme, (a) the
    history_theme_candidate_boost score contribution is nonzero, and (b) the
    resulting reason_facts primary reason is "history_theme" (priority 0,
    the doc's stated highest tier) rather than the weaker "need_tag" fact
    that is also present on the same candidate."""
    assert resolve_history_theme_candidate_boost(consultation_axis="relationship_repair", history_theme="縁") > 0.0

    a_theme_match = _shrine(
        1, "A_theme_match",
        astro_tags=["relationship"], history_theme="縁",
        distance_m=20000, popular_score=0.0,
    )
    b_context_favored = _shrine(2, "B_context_favored", distance_m=100, popular_score=8.0)
    candidates = [a_theme_match, b_context_favored]

    recs = _run(
        candidates=candidates,
        need_tags=["relationship"],
        consultation_axis="relationship_repair",
    )
    assert recs["recommendations"][0]["name"] == "A_theme_match"
    top = recs["recommendations"][0]
    assert top["_primary_reason_source"] == "history_theme"
    boost = top["breakdown_detail"]["features"]["history_theme_candidate_boost"]["raw"]
    assert boost > 0.0

    fact_types = {f["type"] for f in top["_reason_facts"]}
    assert "need_tag" in fact_types  # weaker fact still present, but not chosen as primary
    assert PRIMARY_REASON_PRIORITY["history_theme"] < PRIMARY_REASON_PRIORITY["need_tag"]


# ---------------------------------------------------------------------------
# Non-Primary Guard (§7): birthdate/direction/popularity/behavior never
# leak into reason_facts at all (they are structurally absent from the
# fact-building path); element/visit_style may appear as a fact but are
# fixed at the bottom of PRIMARY_REASON_PRIORITY, below every
# Consultation/Shrine-Evidence-derived type.
# ---------------------------------------------------------------------------


def test_non_primary_signal_priority_ordering_is_fixed():
    """§7: distance/popularity/birthdate/direction/behavior must never be
    presented as if they were a semantic match. The current implementation
    encodes this by placing element (birthdate) and visit_style at the
    bottom of PRIMARY_REASON_PRIORITY, below every Consultation-Meaning or
    Shrine-side-Evidence type."""
    primary_tier = ("history_theme", "culture_translation", "need_tag", "text_hint", "user_selected_tag", "goriyaku_tag")
    for reason_type in primary_tier:
        assert PRIMARY_REASON_PRIORITY[reason_type] < PRIMARY_REASON_PRIORITY["element"]
        assert PRIMARY_REASON_PRIORITY[reason_type] < PRIMARY_REASON_PRIORITY["visit_style"]
    assert PRIMARY_REASON_PRIORITY["element"] < PRIMARY_REASON_PRIORITY["fallback"]
    assert PRIMARY_REASON_PRIORITY["visit_style"] < PRIMARY_REASON_PRIORITY["fallback"]


@pytest.mark.django_db
def test_popularity_alone_never_produces_a_reason_fact(deterministic):
    """popularity (Secondary, §6) has no reason_facts type at all -- even a
    maximal popularity gap must not surface as a Primary Reason."""
    a_unpopular = _shrine(1, "A_unpopular", popular_score=0.0)
    b_popular = _shrine(2, "B_popular", popular_score=10.0)
    recs = _run(candidates=[a_unpopular, b_popular])

    for rec in recs["recommendations"]:
        assert rec["_primary_reason_source"] == "fallback"
        assert all(f["type"] != "popularity" for f in rec["_reason_facts"])


@pytest.mark.django_db
def test_direction_alone_never_produces_a_reason_fact(deterministic):
    """direction (Context, §6) can contribute up to DIRECTION_SIGNAL_MAX to
    score_total_ranked via direction_signal_score, but must never surface
    as a reason_facts type or Primary Reason."""
    direction_profile = {
        "visitDate": "2026-08-10",
        "luckyDirections": ["東"],
        "calculationMethod": "annual_monthly_kyusei_v1",
        "source": "calculated",
    }
    user_origin = {"lat": 35.0, "lng": 139.0}
    candidate = _shrine(1, "A_direction_match", lat=35.0, lng=140.0)

    recs = _run(
        candidates=[candidate],
        profile_context={"direction_profile": direction_profile},
        bias=user_origin,
    )
    rec = recs["recommendations"][0]
    assert rec["breakdown_detail"]["features"]["direction_signal"]["raw"] > 0.0
    assert rec["_primary_reason_source"] == "fallback"
    assert all(f["type"] != "direction" for f in rec["_reason_facts"])


@pytest.mark.django_db
def test_behavior_alone_never_produces_a_reason_fact(deterministic):
    """behavior (Personalization, §6) is capped at min(base*0.3, 0.5) and
    can move score_total_ranked, but must never surface as a reason_facts
    type or Primary Reason -- score contribution and Primary Recommendation
    Meaning are different claims (§7 explicit warning)."""
    shrine_row = Shrine.objects.create(
        name_jp="行動履歴神社", address="東京都千代田区", latitude=35.0, longitude=139.0,
    )
    user = get_user_model().objects.create_user(username="behavior_guard_user", password="x")
    for _ in range(5):
        ShrineInteractionLog.objects.create(
            user=user,
            shrine=shrine_row,
            action_type=ShrineInteractionLog.ActionType.DETAIL_VIEW,
            created_at=timezone.now(),
        )

    candidate = _shrine(shrine_row.id, "A_behavior_heavy")
    recs = _run(candidates=[candidate], user=user)
    rec = recs["recommendations"][0]

    assert rec["breakdown_detail"]["features"]["behavior"]["capped_contribution"] > 0.0
    assert rec["_primary_reason_source"] == "fallback"
    assert all(f["type"] != "behavior" for f in rec["_reason_facts"])
