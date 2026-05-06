# backend/temples/tests/services/test_concierge_chat_observation.py

from __future__ import annotations

import logging

from temples.services.concierge_chat_observation import (
    build_trim_observation,
    observe_candidate_pool,
    observe_candidate_pool_debug,
    observe_trim_after,
    observe_trim_before,
    observe_visit_style_before_trim,
)

from temples.services.concierge_chat import build_chat_recommendations


def assert_visit_style_observation_schema(observation):
    assert set(observation.keys()) == {
        "pool_size",
        "hit_count",
        "matched_tag_counts",
        "rows",
    }
    assert isinstance(observation["pool_size"], int)
    assert isinstance(observation["hit_count"], int)
    assert isinstance(observation["matched_tag_counts"], dict)
    assert isinstance(observation["rows"], list)


def assert_visit_style_observation_row_schema(row):
    assert set(row.keys()) == {
        "rank",
        "shrine_id",
        "name",
        "visit_style_tags",
        "matched_tags",
        "contribution",
        "score_total_ranked",
        "score_need",
        "matched_need_tags",
    }
    assert isinstance(row["rank"], int)
    assert isinstance(row["visit_style_tags"], list)
    assert isinstance(row["matched_tags"], list)
    assert isinstance(row["contribution"], float)
    assert isinstance(row["score_total_ranked"], float)
    assert isinstance(row["matched_need_tags"], list)


def assert_trim_observation_schema(observation):
    assert set(observation.keys()) == {
        "before_count",
        "after_count",
        "dropped_count",
        "before",
        "after",
        "dropped",
    }
    assert isinstance(observation["before_count"], int)
    assert isinstance(observation["after_count"], int)
    assert isinstance(observation["dropped_count"], int)
    assert isinstance(observation["before"], list)
    assert isinstance(observation["after"], list)
    assert isinstance(observation["dropped"], list)


def assert_trim_observation_row_schema(row):
    assert set(row.keys()) == {
        "rank",
        "id",
        "shrine_id",
        "place_id",
        "name",
        "display_name",
    }
    assert isinstance(row["rank"], int)


def assert_candidate_pool_observation_schema(observation):
    assert set(observation.keys()) == {
        "valid_candidate_count",
        "with_place_id",
        "missing_latlng",
        "distance_none",
        "score_top10",
        "filter_context",
    }
    assert isinstance(observation["valid_candidate_count"], int)
    assert isinstance(observation["with_place_id"], int)
    assert isinstance(observation["missing_latlng"], int)
    assert isinstance(observation["distance_none"], int)
    assert isinstance(observation["score_top10"], list)
    assert isinstance(observation["filter_context"], dict)


def assert_candidate_pool_top_row_schema(row):
    assert set(row.keys()) == {
        "rank",
        "shrine_id",
        "place_id",
        "name",
        "distance_m",
        "popular_score",
        "score_total",
        "visit_style_tags",
        "goriyaku_tag_ids",
    }
    assert isinstance(row["rank"], int)
    assert isinstance(row["visit_style_tags"], list)
    assert isinstance(row["goriyaku_tag_ids"], list)


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
    assert_visit_style_observation_schema(result)
    assert_visit_style_observation_row_schema(result["rows"][0])
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
    assert_visit_style_observation_schema(result)
    assert_visit_style_observation_row_schema(result["rows"][0])
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
    assert_visit_style_observation_schema(result)

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
    assert_visit_style_observation_schema(observation)
    assert_visit_style_observation_row_schema(observation["rows"][0])

    assert observation["pool_size"] >= 2
    assert observation["hit_count"] >= 1
    assert observation["matched_tag_counts"]["nature"] >= 1
    assert observation["rows"][0]["name"] == "根津神社"
    assert observation["rows"][0]["matched_tags"] == ["nature"]

    trim_observation = result["_debug"]["trim_observation"]
    assert_trim_observation_schema(trim_observation)
    assert_trim_observation_row_schema(trim_observation["before"][0])
    assert_trim_observation_row_schema(trim_observation["after"][0])
    assert trim_observation["before_count"] >= trim_observation["after_count"]
    assert trim_observation["after_count"] == len(result["recommendations"])

    candidate_pool_observation = result["_debug"]["candidate_pool_observation"]
    assert_candidate_pool_observation_schema(candidate_pool_observation)
    assert_candidate_pool_top_row_schema(candidate_pool_observation["score_top10"][0])
    assert candidate_pool_observation["valid_candidate_count"] == 2
    assert candidate_pool_observation["filter_context"]["flow"] == "B"
    assert candidate_pool_observation["filter_context"]["has_extra_condition"] is True
    assert candidate_pool_observation["score_top10"][0]["name"] == "根津神社"


def test_visit_style_observation_empty_contract_has_stable_schema():
    observation = observe_visit_style_before_trim(
        recs={"recommendations": []},
        query="",
        extra_condition=None,
        visit_style_tags=set(),
    )

    assert_visit_style_observation_schema(observation)
    assert observation == {
        "pool_size": 0,
        "hit_count": 0,
        "matched_tag_counts": {},
        "rows": [],
    }


def test_build_trim_observation_returns_before_after_and_dropped_candidates():
    before = observe_trim_before(
        {
            "recommendations": [
                {"shrine_id": 101, "name": "根津神社"},
                {"shrine_id": 102, "name": "小網神社"},
                {"shrine_id": 103, "name": "神田明神"},
            ]
        }
    )
    after = observe_trim_after(
        {
            "recommendations": [
                {"shrine_id": 101, "name": "根津神社"},
                {"shrine_id": 103, "name": "神田明神"},
            ]
        }
    )

    observation = build_trim_observation(before=before, after=after)

    assert_trim_observation_schema(observation)
    assert_trim_observation_row_schema(observation["before"][0])
    assert_trim_observation_row_schema(observation["after"][0])
    assert_trim_observation_row_schema(observation["dropped"][0])
    assert observation["before_count"] == 3
    assert observation["after_count"] == 2
    assert observation["dropped_count"] == 1
    assert observation["dropped"][0]["shrine_id"] == 102
    assert observation["dropped"][0]["name"] == "小網神社"


def test_trim_observation_empty_contract_has_stable_schema():
    observation = build_trim_observation(before=[], after=[])

    assert_trim_observation_schema(observation)
    assert observation == {
        "before_count": 0,
        "after_count": 0,
        "dropped_count": 0,
        "before": [],
        "after": [],
        "dropped": [],
    }


def test_observe_candidate_pool_debug_returns_stable_schema():
    observation = observe_candidate_pool_debug(
        valid_candidates=[
            {
                "id": 1,
                "shrine_id": 101,
                "place_id": "place-101",
                "name": "根津神社",
                "lat": 35.1,
                "lng": 139.1,
                "distance_m": 1200,
                "popular_score": 42,
                "_score_total": 0.91,
                "visit_style_tags": ["nature", "quiet"],
                "goriyaku_tag_ids": [1, 2],
            },
            {
                "id": 2,
                "shrine_id": 102,
                "place_id": None,
                "name": "小網神社",
                "lat": None,
                "lng": 139.2,
                "distance_m": None,
                "popular_score": 30,
                "visit_style_tags": None,
                "goriyaku_tag_ids": None,
            },
        ],
        filter_context={"flow": "B", "public_mode": "need"},
    )

    assert_candidate_pool_observation_schema(observation)
    assert_candidate_pool_top_row_schema(observation["score_top10"][0])
    assert observation["valid_candidate_count"] == 2
    assert observation["with_place_id"] == 1
    assert observation["missing_latlng"] == 1
    assert observation["distance_none"] == 1
    assert observation["filter_context"] == {"flow": "B", "public_mode": "need"}
    assert observation["score_top10"][0]["name"] == "根津神社"
    assert observation["score_top10"][1]["visit_style_tags"] == []
    assert observation["score_top10"][1]["goriyaku_tag_ids"] == []


def test_observe_candidate_pool_debug_empty_contract_has_stable_schema():
    observation = observe_candidate_pool_debug(
        valid_candidates=[],
        filter_context={"flow": "A"},
    )

    assert_candidate_pool_observation_schema(observation)
    assert observation == {
        "valid_candidate_count": 0,
        "with_place_id": 0,
        "missing_latlng": 0,
        "distance_none": 0,
        "score_top10": [],
        "filter_context": {"flow": "A"},
    }
