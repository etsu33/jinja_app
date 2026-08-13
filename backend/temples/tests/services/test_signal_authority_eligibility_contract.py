# backend/temples/tests/services/test_signal_authority_eligibility_contract.py
"""Recommendation Signal Authority: Eligibility Contract (goriyaku_tag_ids).

Source of truth: docs/product/recommendation-signal-authority.md §5/§6/§9.
`goriyaku_tag_ids` is the only Signal classified as **Eligibility**: it is
the only current DB-level hard filter that can change the Candidate SET
(§5 Eligibility Definition), and by design it contributes **zero** Rank
score once a candidate has already passed that filter (§6 Decision Table
row: "Eligibility + Explanation, Rank非寄与を維持"; §9 "Intent vs Explicit
Constraint"). This module fixes both halves of that asymmetric contract as
regression tests, plus the visible-reason condition under which the
constraint shows up in Explanation.

This module does not change production code, ranking weight, candidate
filtering, or reason generation -- it only asserts against the existing
`build_chat_candidates()` / `build_chat_recommendations()` facades.

Cross-reference (already covered, not duplicated here): the general
user_selected_tag reason-fact/priority behavior is covered by
test_concierge_chat_observation.py::test_build_reason_facts_generates_user_selected_tag_reason,
::test_resolve_primary_reason_prefers_need_tag_over_user_selected_tag,
::test_attach_breakdown_sets_user_selected_tag_as_primary_reason, and
test_concierge_primary_reason_unification_contract.py::test_conflict_consultation_plus_constraint_meaning_wins_when_present.
"""

from __future__ import annotations

import pytest

from temples.models import GoriyakuTag, Shrine
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_candidates import build_chat_candidates


@pytest.fixture
def shrine_factory(db):
    def _factory(*, name: str, goriyaku_tags=None, **overrides) -> Shrine:
        base = dict(
            name_jp=name,
            address="東京都千代田区1-1",
            latitude=35.0,
            longitude=139.0,
            popular_score=1.0,
        )
        base.update(overrides)
        shrine = Shrine.objects.create(**base)
        if goriyaku_tags:
            shrine.goriyaku_tags.set(goriyaku_tags)
        return shrine

    return _factory


@pytest.mark.django_db
def test_goriyaku_tag_ids_is_a_db_level_candidate_eligibility_filter(shrine_factory):
    """§5/§9: requesting goriyaku_tag_ids removes non-matching shrines from
    the Candidate SET itself (Eligibility), not just from the ranked
    order."""
    tag = GoriyakuTag.objects.create(name="健康祈願")
    shrine_factory(name="条件を満たす神社", goriyaku_tags=[tag])
    shrine_factory(name="条件を満たさない神社")

    unfiltered = build_chat_candidates(lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="test")
    unfiltered_names = [c["name"] for c in unfiltered]
    assert "条件を満たす神社" in unfiltered_names
    assert "条件を満たさない神社" in unfiltered_names

    filtered = build_chat_candidates(lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=[tag.id], trace_id="test")
    filtered_names = [c["name"] for c in filtered]
    assert "条件を満たす神社" in filtered_names
    assert "条件を満たさない神社" not in filtered_names


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


@pytest.mark.django_db
def test_goriyaku_tag_ids_match_is_not_double_rewarded_in_rank_score(settings):
    """§6: once a candidate has already passed the goriyaku_tag_ids hard
    filter, matching it must not additionally raise
    score_need_rank_weighted -- the only two rank contributors matched_by_tag
    (need_tags <-> astro_tags) and matched_by_gid (need_tags <-> shrine's own
    goriyaku_tag_ids) are untouched by matched_by_user_selected_gid
    (requested goriyaku_tag_ids)."""
    settings.CONCIERGE_USE_LLM = False
    REQUESTED_GID = 501

    matching = _shrine(1, "A_matches_requested_gid", goriyaku_tag_ids=[REQUESTED_GID])
    non_matching = _shrine(2, "B_does_not_match", goriyaku_tag_ids=[])

    recs = build_chat_recommendations(
        query="", language="ja", candidates=[matching, non_matching],
        goriyaku_tag_ids=[REQUESTED_GID],
    )
    by_name = {r["name"]: r for r in recs["recommendations"]}

    a_need = by_name["A_matches_requested_gid"]["breakdown_detail"]["features"]["need"]
    b_need = by_name["B_does_not_match"]["breakdown_detail"]["features"]["need"]
    assert a_need["rank_weighted"] == b_need["rank_weighted"] == 0.0
    assert a_need["matched_by_gid_count"] == b_need["matched_by_gid_count"] == 0
    assert a_need["matched_by_tag_count"] == b_need["matched_by_tag_count"] == 0

    # The Explicit Constraint match is still visible as a fact (Explanation
    # half of the contract, score=3.0 fixed weight) -- it is Eligibility +
    # Explanation, not silently invisible.
    a_fact_types = {f["type"]: f for f in by_name["A_matches_requested_gid"]["_reason_facts"]}
    assert "user_selected_tag" in a_fact_types
    assert a_fact_types["user_selected_tag"]["score"] == 3.0
    b_fact_types = {f["type"] for f in by_name["B_does_not_match"]["_reason_facts"]}
    assert "user_selected_tag" not in b_fact_types
