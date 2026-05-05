# backend/temples/tests/services/test_concierge_chat_observation.py

from __future__ import annotations

import logging

from temples.services.concierge_chat_observation import (
    observe_candidate_pool,
    observe_visit_style_before_trim,
)

from temples.services.concierge_chat import build_chat_recommendations


def test_observe_candidate_pool_logs_counts(caplog):
    caplog.set_level(logging.DEBUG, logger="temples.services.concierge_chat_observation")

    valid_candidates = [
        {
            "id": 1,
            "shrine_id": 101,
            "visit_style_tags": ["nature", "quiet"],
            "matched_need_tags": ["rest"],
        },
        {
            "id": 2,
            "shrine_id": 102,
            "visit_style_tags": ["urban"],
            "matched_need_tags": ["career"],
        },
    ]

    observe_candidate_pool(
        valid_candidates=valid_candidates,
        visit_style_tags={"nature"},
        need_tags=["rest"],
    )

    assert "[pool] size=2 visit_style_hits=1 need_hits=1" in caplog.text
    assert "[pool_detail]" in caplog.text
    assert "101" in caplog.text
    assert "nature" in caplog.text


def test_observe_visit_style_before_trim_logs_summary(caplog):
    caplog.set_level(logging.INFO, logger="temples.services.concierge_chat_observation")

    recs = {
        "recommendations": [
            {
                "shrine_id": 101,
                "name": "根津神社",
                "visit_style_tags": ["nature", "quiet"],
                "breakdown": {
                    "score_need": 0,
                    "matched_need_tags": [],
                },
                "breakdown_detail": {
                    "features": {
                        "score_total_ranked": 0.42,
                        "visit_style": {
                            "matched_tags": ["nature"],
                            "contribution": 0.35,
                        },
                    }
                },
            },
            {
                "shrine_id": 102,
                "name": "小網神社",
                "visit_style_tags": ["business", "reset"],
                "breakdown": {
                    "score_need": 0,
                    "matched_need_tags": [],
                },
                "breakdown_detail": {
                    "features": {
                        "score_total_ranked": 0.19,
                        "visit_style": {
                            "matched_tags": [],
                            "contribution": 0.0,
                        },
                    }
                },
            },
        ]
    }

    result = observe_visit_style_before_trim(
        recs=recs,
        query="自然を感じながら参拝したい",
        extra_condition="自然や緑を感じられる神社がいい",
        visit_style_tags={"nature"},
    )
    assert result["pool_size"] == 2
    assert result["hit_count"] == 1
    assert result["matched_tag_counts"] == {"nature": 1}
    assert result["rows"][0]["shrine_id"] == 101
    assert result["rows"][0]["name"] == "根津神社"
    assert result["rows"][0]["matched_tags"] == ["nature"]
    assert result["rows"][0]["contribution"] == 0.35

    assert "[visit_style_observation_before_trim]" in caplog.text
    assert "has_query=True" in caplog.text
    assert "query_len=13" in caplog.text
    assert "has_extra=True" in caplog.text
    assert "pool_size=2" in caplog.text
    assert "hit_count=1" in caplog.text
    assert "matched_tag_counts={'nature': 1}" in caplog.text
    assert "根津神社" in caplog.text


def test_observe_visit_style_before_trim_ignores_non_dict_recommendations(caplog):
    caplog.set_level(logging.INFO, logger="temples.services.concierge_chat_observation")

    result = observe_visit_style_before_trim(
        recs={"recommendations": [None, "invalid", {"name": "有効な候補"}]},
        query="",
        extra_condition=None,
        visit_style_tags=set(),
    )
    assert result["pool_size"] == 1
    assert result["hit_count"] == 0
    assert result["matched_tag_counts"] == {}
    assert result["rows"][0]["name"] == "有効な候補"

    assert "[visit_style_observation_before_trim]" in caplog.text
    assert "has_query=False" in caplog.text
    assert "has_extra=False" in caplog.text
    assert "pool_size=1" in caplog.text
    assert "有効な候補" in caplog.text


def test_observe_visit_style_before_trim_returns_empty_result_on_invalid_recs(caplog):
    caplog.set_level(logging.INFO, logger="temples.services.concierge_chat_observation")

    result = observe_visit_style_before_trim(
        recs={"recommendations": None},
        query="自然",
        extra_condition="自然がいい",
        visit_style_tags={"nature"},
    )

    assert result == {
        "pool_size": 0,
        "hit_count": 0,
        "matched_tag_counts": {},
        "rows": [],
    }

    assert "[visit_style_observation_before_trim]" in caplog.text
    assert "pool_size=0" in caplog.text


def test_build_chat_recommendations_attaches_visit_style_observation_debug(monkeypatch):
    def fake_resolve_llm_route(*, query, valid_candidates, need_tags, llm_enabled):
        return {
            "recs": {
                "recommendations": [
                    {
                        "name": "根津神社",
                        "shrine_id": 101,
                        "visit_style_tags": ["nature", "quiet"],
                        "goriyaku": "縁結び・厄除け",
                        "distance_m": 1200,
                    },
                    {
                        "name": "小網神社",
                        "shrine_id": 102,
                        "visit_style_tags": ["business", "reset"],
                        "goriyaku": "強運厄除け・金運",
                        "distance_m": 800,
                    },
                ],
                "_seed": True,
            },
            "requested_llm_enabled": False,
            "effective_llm_enabled": False,
            "llm_used": False,
            "llm_error": None,
        }

    monkeypatch.setattr(
        "temples.services.concierge_chat.resolve_llm_route",
        fake_resolve_llm_route,
    )
    monkeypatch.setattr(
        "temples.services.concierge_chat._backfill_location_from_name",
        lambda recs, *, bias, language: None,
    )

    result = build_chat_recommendations(
        query="自然を感じながら参拝したい",
        language="ja",
        candidates=[
            {
                "name": "根津神社",
                "shrine_id": 101,
                "visit_style_tags": ["nature", "quiet"],
                "goriyaku": "縁結び・厄除け",
                "distance_m": 1200,
            },
            {
                "name": "小網神社",
                "shrine_id": 102,
                "visit_style_tags": ["business", "reset"],
                "goriyaku": "強運厄除け・金運",
                "distance_m": 800,
            },
        ],
        bias=None,
        birthdate=None,
        goriyaku_tag_ids=None,
        extra_condition="自然や緑を感じられる神社がいい",
        public_mode="need",
        flow="B",
    )

    observation = result["_debug"]["visit_style_observation"]

    assert observation["pool_size"] >= 2
    assert observation["hit_count"] >= 1
    assert observation["matched_tag_counts"]["nature"] >= 1
    assert observation["rows"][0]["name"] == "根津神社"
    assert observation["rows"][0]["matched_tags"] == ["nature"]
