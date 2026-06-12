from __future__ import annotations

from temples.services.concierge_chat import _build_user_state_profile
from temples.services.concierge_chat_need import resolve_need_payload
from temples.services.concierge_chat_ranking import _attach_breakdown
from temples.services.concierge_explanation_payload import attach_explanation_payload


def test_need_tags_are_resolved_as_user_state_source_of_truth():
    payload = resolve_need_payload(
        query="転職で迷っていて、仕事の流れを整えたい",
        max_tags=3,
    )

    assert "career" in payload["tags"]
    assert isinstance(payload["hits"], dict)


def test_consultation_theme_job_resolves_to_career():
    payload = resolve_need_payload(
        query="仕事の方向性で迷っていて、転職も含めて考えたい",
        max_tags=3,
    )

    assert "career" in payload["tags"]


def test_consultation_theme_money_resolves_to_money():
    payload = resolve_need_payload(
        query="お金や収入の不安があり、金運を整えたい",
        max_tags=3,
    )

    assert "money" in payload["tags"]


def test_consultation_theme_rest_resolves_to_rest():
    payload = resolve_need_payload(
        query="最近疲れていて、静かに休みたい",
        max_tags=3,
    )

    assert "rest" in payload["tags"]


def test_consultation_theme_study_resolves_to_study():
    payload = resolve_need_payload(
        query="資格試験の勉強と合格祈願について相談したい",
        max_tags=3,
    )

    assert "study" in payload["tags"]


def test_consultation_theme_relationship_is_currently_mapped_to_love_not_relationship():
    payload = resolve_need_payload(
        query="人間関係や職場の関係を整えたい",
        max_tags=3,
    )

    assert "relationship" not in payload["tags"]
    assert "love" in payload["tags"] or "mental" in payload["tags"] or "career" in payload["tags"]


def test_consultation_theme_challenge_resolves_to_courage():
    payload = resolve_need_payload(
        query="新しい挑戦に踏み出す勇気がほしい",
        max_tags=3,
    )

    assert "courage" in payload["tags"]


def test_explicit_need_tags_override_query_extraction():
    payload = resolve_need_payload(
        query="転職で迷っていて、仕事の流れを整えたい",
        need_tags=["rest", "career", "rest"],
        max_tags=3,
    )

    assert payload == {
        "tags": ["rest", "career"],
        "hits": {},
    }


def test_matched_need_tags_are_user_shrine_match_result_not_raw_user_input():
    profile = _build_user_state_profile(
        query="転職で迷っている",
        extra_condition="静かな場所がいい",
        need_payload={"tags": ["career"], "hits": {"career": ["転職"]}},
        need_tags=["career"],
        goriyaku_tag_ids=[1, "2", "invalid"],
        recommendations=[
            {
                "breakdown": {
                    "matched_need_tags": ["career"],
                }
            }
        ],
    )

    assert profile["need_tags"] == ["career"]
    assert profile["need_hits"] == {"career": ["転職"]}
    assert profile["selected_goriyaku_tag_ids"] == [1, 2]
    assert profile["matched_need_tags"] == ["career"]
    assert profile["primary_need_tag"] == "career"


def test_primary_need_tag_is_display_representative_from_matched_need_tags():
    recs = {
        "recommendations": [
            {
                "name": "仕事の神社",
                "breakdown": {
                    "matched_need_tags": ["career", "rest"],
                    "score_element": 0,
                    "score_need": 2,
                    "score_total": 2.0,
                },
            }
        ]
    }

    attach_explanation_payload(recs, birthdate=None)

    payload = recs["recommendations"][0]["_explanation_payload"]
    assert payload["matched_need_tags"] == ["career", "rest"]
    assert payload["primary_need_tag"] == "career"
    assert payload["primary_need_label_ja"] is not None


def test_score_v2_contains_recommendation_core_signals():
    rec = {
        "id": 1,
        "name": "仕事の神社",
        "astro_tags": ["career"],
        "astro_elements": [],
        "goriyaku": "仕事運 出世運",
        "description": "転職や挑戦の節目に向き合う神社",
        "goriyaku_tag_ids": [],
        "popular_score": 0,
    }

    _attach_breakdown(
        rec,
        birthdate=None,
        need_tags=["career"],
        weights={"element": 0.0, "need": 1.0, "popular": 0.0, "distance": 0.0},
        astro_bonus_enabled=False,
        visit_style_tags=set(),
        query="転職で迷っている",
        requested_goriyaku_tag_ids=None,
        goriyaku_tag_label_by_id={},
        user=None,
    )

    assert rec["breakdown"]["matched_need_tags"] == ["career"]
    assert rec["score_v2"]["components"]["user_state_match"] > 0
    assert rec["score_v2"]["components"]["shrine_meaning_match"] > 0
    assert rec["score_v2"]["signals"]["matched_need_tags"] == ["career"]
    assert rec["score_v2"]["signals"]["shrine_meaning_profile"]["matched_need_tags"] == ["career"]
