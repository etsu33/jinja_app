# backend/temples/tests/services/test_signal_authority_knowledge_explanation_contract.py
"""Recommendation Signal Authority: Knowledge Authority (§8) + Explanation
Contract (§10).

Source of truth: docs/product/recommendation-signal-authority.md. This
module fixes two related Decisions as regression tests:

- §8 Knowledge Authority (Decision A, current-state Explanation-only):
  `deity` / `shrine_history` / `knowledge_deities` / `knowledge_histories`
  must never change the Candidate SET or Rank/score under the current
  Contract ("Rank Changed = No"). This is not a data-coverage limitation
  to work around -- it is a deliberate current decision (§8 reasons 1-4),
  and this test asserts the Authority Contract (Rank never changes), not
  private implementation detail of *how* knowledge is excluded from
  scoring (so that a future Knowledge Ranking promotion, §8 Future
  Candidate D, does not require touching this test).
- §10 Explanation Contract: the visible "why this shrine" explanation
  (`_reason_facts` / `_primary_reason_source` / `_explanation_payload`)
  must never attribute Candidate/Rank authorship to an Explanation-only
  Knowledge signal, even when a separate, independent pathway
  (`recommendation_reason_v4`) legitimately uses the same Knowledge data
  as a Fact layer.

This module does not change production code, ranking weight, candidate
filtering, reason generation, or UI.

Cross-reference (already covered, not duplicated here):
- Knowledge -> recommendation_reason_v4 Fact-layer wording rules:
  services/test_recommendation_reason_v4.py (extensive dedicated coverage)
- recommendation_reason_v4_detail is a separate field from reason/_reason_facts:
  services/test_concierge_chat_observation.py::test_build_chat_recommendations_attaches_recommendation_reason_v4_detail
- Internal consistency across primary_reason_source/_primary_reason_label/reason_facts:
  test_concierge_primary_reason_unification_contract.py::test_full_integration_primary_reason_is_unified_and_consultation_led
  test_concierge_primary_reason_unification_contract.py::test_no_consultation_match_visit_style_only_becomes_unified_primary_reason
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
        "knowledge_deities": [],
        "knowledge_histories": [],
    }
    base.update(overrides)
    return base


KNOWLEDGE_DEITIES = [{"display_name": "天照大神", "confidence": "high"}]
KNOWLEDGE_HISTORIES = [
    {"history_type": "founding", "title": "創建の由緒", "content": "天照大神を祀る由緒ある神社です。", "confidence": "high"}
]


@pytest.fixture
def deterministic(settings):
    settings.CONCIERGE_USE_LLM = False


@pytest.mark.django_db
def test_knowledge_fields_never_change_score_or_rank(deterministic):
    """§8 Decision A: knowledge_deities/knowledge_histories (and their
    Legacy-fallback counterparts deity/shrine_history) must contribute
    exactly zero to _score_total, regardless of whether the query text
    matches the knowledge content."""
    without_knowledge = _shrine(1, "A_no_knowledge")
    with_knowledge = _shrine(
        1, "A_no_knowledge",
        knowledge_deities=KNOWLEDGE_DEITIES,
        knowledge_histories=KNOWLEDGE_HISTORIES,
    )

    recs_without = build_chat_recommendations(
        query="天照大神にお参りしたいです", language="ja", candidates=[without_knowledge],
    )
    recs_with = build_chat_recommendations(
        query="天照大神にお参りしたいです", language="ja", candidates=[with_knowledge],
    )

    score_without = recs_without["recommendations"][0]["_score_total"]
    score_with = recs_with["recommendations"][0]["_score_total"]
    assert score_without == score_with


@pytest.mark.django_db
def test_knowledge_richness_does_not_overtake_a_context_favored_candidate(deterministic):
    """§8: a candidate with rich, query-matching Knowledge content but weak
    distance/popularity must not be able to overtake a Context-favored
    candidate purely on the strength of its Knowledge data -- Knowledge is
    Explanation-only, it carries no Candidate/Rank authority at all (unlike
    Primary-tier signals, which legitimately can order-flip, see
    test_signal_authority_primary_and_guard_contract.py)."""
    a_knowledge_rich = _shrine(
        1, "A_knowledge_rich",
        knowledge_deities=KNOWLEDGE_DEITIES, knowledge_histories=KNOWLEDGE_HISTORIES,
        distance_m=20000, popular_score=0.0,
    )
    b_context_favored = _shrine(2, "B_context_favored", distance_m=100, popular_score=8.0)

    recs = build_chat_recommendations(
        query="天照大神にお参りしたいです", language="ja",
        candidates=[a_knowledge_rich, b_context_favored],
    )
    assert recs["recommendations"][0]["name"] == "B_context_favored"


@pytest.mark.django_db
def test_explanation_never_attributes_ranking_to_knowledge_only_signal(deterministic):
    """§10 Explanation Contract: _reason_facts / _primary_reason_source /
    _explanation_payload must never contain a Knowledge-derived type
    ("deity"/"shrine_history"), even though the independent
    recommendation_reason_v4 pathway legitimately surfaces the same
    Knowledge content as a Fact layer. A candidate with rich Knowledge data
    but zero Consultation Meaning match must fall back to "fallback", not
    a Knowledge-flavored reason."""
    candidate = _shrine(
        1, "A_knowledge_only",
        knowledge_deities=KNOWLEDGE_DEITIES, knowledge_histories=KNOWLEDGE_HISTORIES,
    )
    recs = build_chat_recommendations(
        query="天照大神にお参りしたいです", language="ja", candidates=[candidate],
    )
    rec = recs["recommendations"][0]

    assert rec["_primary_reason_source"] == "fallback"
    fact_types = {f["type"] for f in rec["_reason_facts"]}
    assert fact_types.isdisjoint({"deity", "shrine_history", "knowledge", "knowledge_deities", "knowledge_histories"})
    assert rec["_explanation_payload"]["primary_reason"]["type"] == "fallback"

    # The separate recommendation_reason_v4 Fact-layer pathway is untouched
    # by this Contract and may legitimately reference the deity.
    assert rec.get("recommendation_reason_v4_detail", {}).get("fact") is not None
