"""Culture Translation Primary Attribution Guard (PR #2421 follow-up)."""

from __future__ import annotations

import copy

import pytest

from temples.services.concierge_chat import build_chat_recommendations


def _shrine(id_: int, name: str, **overrides):
    candidate = {
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
    candidate.update(overrides)
    return candidate


def _run(candidates, **overrides):
    params = {
        "query": "仕事を見直したい",
        "language": "ja",
        "candidates": candidates,
        "need_tags": ["career"],
        "public_mode": "need",
        "flow": "A",
    }
    params.update(overrides)
    return build_chat_recommendations(**params)


def _rank_snapshot(result):
    return [
        (
            rec["shrine_id"],
            rec["_score_total"],
        )
        for rec in result["recommendations"]
    ]


@pytest.fixture
def deterministic(settings):
    settings.CONCIERGE_USE_LLM = False


@pytest.mark.django_db
def test_culture_translation_does_not_change_candidates_rank_or_primary_authority(deterministic):
    candidates = [
        _shrine(1, "A", astro_tags=["career"], popular_score=1.0),
        _shrine(2, "B", astro_tags=["career"], popular_score=0.2),
    ]
    variant_candidates = copy.deepcopy(candidates)
    variant_candidates[0]["culture_translation"] = {"present": True}

    baseline = _run(candidates)
    variant = _run(variant_candidates)

    assert [rec["shrine_id"] for rec in baseline["recommendations"]] == [1, 2]
    assert [rec["shrine_id"] for rec in variant["recommendations"]] == [1, 2]
    assert _rank_snapshot(variant) == _rank_snapshot(baseline)

    baseline_top = baseline["recommendations"][0]
    variant_top = variant["recommendations"][0]
    assert baseline_top["_primary_reason_source"] == "need_tag"
    assert variant_top["_primary_reason_source"] == "need_tag"
    assert variant_top["rank_explanation"]["primary_reason_source"] == "need_tag"
    assert variant_top["_explanation_payload"]["primary_reason"]["type"] == "need_tag"

    culture_fact = next(
        fact
        for fact in variant_top["reason_facts"]
        if fact["type"] == "culture_translation"
    )
    assert culture_fact["is_primary"] is False
    assert culture_fact["evidence"] == ["culture_translation_present", "matched_need_tags"]

    # Explanation-only material remains available without leaking into the
    # independent Reason v4 or Action Suggestion pathways.
    assert variant_top["recommendation_reason_v4"] == baseline_top["recommendation_reason_v4"]
    assert (
        variant_top["_explanation_payload"]["action_suggestions"]
        == baseline_top["_explanation_payload"]["action_suggestions"]
    )


@pytest.mark.django_db
def test_culture_translation_without_a_semantic_match_stays_fallback(deterministic):
    candidate = _shrine(1, "Fallback", culture_translation={"present": True})

    result = _run([candidate], query="", need_tags=[])
    rec = result["recommendations"][0]

    assert rec["_primary_reason_source"] == "fallback"
    assert rec["rank_explanation"]["primary_reason_source"] == "fallback"
    assert rec["_explanation_payload"]["primary_reason"]["type"] == "fallback"
    assert all(fact["type"] != "culture_translation" for fact in rec["reason_facts"])
