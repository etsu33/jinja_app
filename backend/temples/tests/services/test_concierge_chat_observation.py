

# backend/temples/tests/services/test_concierge_chat_observation.py

from __future__ import annotations

import logging

from temples.services.concierge_chat_observation import (
    observe_candidate_pool,
    observe_visit_style_before_trim,
)


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

    observe_visit_style_before_trim(
        recs=recs,
        query="自然を感じながら参拝したい",
        extra_condition="自然や緑を感じられる神社がいい",
        visit_style_tags={"nature"},
    )

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

    observe_visit_style_before_trim(
        recs={"recommendations": [None, "invalid", {"name": "有効な候補"}]},
        query="",
        extra_condition=None,
        visit_style_tags=set(),
    )

    assert "[visit_style_observation_before_trim]" in caplog.text
    assert "has_query=False" in caplog.text
    assert "has_extra=False" in caplog.text
    assert "pool_size=1" in caplog.text
    assert "有効な候補" in caplog.text
