# backend/temples/tests/services/test_concierge_chat_observation.py

from __future__ import annotations

import logging

from temples.services.concierge_chat_observation import (
    build_trim_observation,
    observe_candidate_pool,
    observe_candidate_pool_debug,
    observe_ranking_breakdown,
    observe_trim_after,
    observe_trim_before,
    observe_visit_style_before_trim,
)

from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_ranking import (
    DIRECTION_BONUS_MAX,
    _attach_breakdown,
    _build_reason_facts,
    _resolve_direction_bonus,
    _resolve_primary_reason,
)


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


def assert_ranking_breakdown_observation_schema(observation):
    assert set(observation.keys()) == {
        "ranked_count",
        "top10",
        "_debug",
    }
    assert isinstance(observation["ranked_count"], int)
    assert isinstance(observation["top10"], list)
    assert isinstance(observation["_debug"], dict)
    assert set(observation["_debug"].keys()) == {
        "query",
        "need_tags",
        "matched_need_tags",
        "visit_style_tags",
        "matched_visit_style_tags",
        "score_total_ranked_base",
        "capped_behavior_contribution",
        "behavior_ratio",
        "reflection_hint_state_change_direction",
        "reflection_hint_next_need_hint",
        "reflection_hint_next_history_theme_hint",
        "reflection_hint_source_history_theme",
    }


def assert_ranking_breakdown_top_row_schema(row):
    assert set(row.keys()) == {
        "rank",
        "shrine_id",
        "name",
        "score_raw",
        "score_total",
        "score_total_ranked",
        "score_total_ranked_base",
        "capped_behavior_contribution",
        "behavior_ratio",
        "score_need",
        "score_need_rank_weighted",
        "score_distance",
        "score_popular",
        "score_visit_style",
        "score_element",
        "visit_style_tags",
        "behavior_signal",
        "behavior_contribution",
        "contributions",
        "matched_need_tags",
        "matched_visit_style_tags",
        "primary_reason_source",
        "primary_reason_label",
        "reflection_hint",
        "reflection_hint_state_change_direction",
        "reflection_hint_next_need_hint",
        "reflection_hint_next_history_theme_hint",
        "reflection_hint_source_history_theme",
    }
    assert isinstance(row["rank"], int)
    assert isinstance(row["score_raw"], float)
    assert isinstance(row["score_total"], float)
    assert isinstance(row["score_total_ranked"], float)
    assert isinstance(row["score_total_ranked_base"], float)
    assert isinstance(row["capped_behavior_contribution"], float)
    assert isinstance(row["behavior_ratio"], float)
    assert isinstance(row["score_need"], int)
    assert isinstance(row["score_need_rank_weighted"], float)
    assert isinstance(row["score_distance"], float)
    assert isinstance(row["score_popular"], float)
    assert isinstance(row["score_visit_style"], int)
    assert isinstance(row["score_element"], int)
    assert isinstance(row["visit_style_tags"], list)
    assert isinstance(row["behavior_signal"], float)
    assert isinstance(row["behavior_contribution"], float)
    assert isinstance(row["contributions"], dict)
    assert isinstance(row["matched_need_tags"], list)
    assert isinstance(row["matched_visit_style_tags"], list)
    assert isinstance(row["reflection_hint"], dict)
    assert isinstance(row["reflection_hint_next_need_hint"], list)
    assert isinstance(row["reflection_hint_next_history_theme_hint"], list)


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

    ranking_breakdown = result["_debug"]["ranking_breakdown_observation"]
    assert_ranking_breakdown_observation_schema(ranking_breakdown)
    assert_ranking_breakdown_top_row_schema(ranking_breakdown["top10"][0])
    assert ranking_breakdown["ranked_count"] >= len(result["recommendations"])
    assert ranking_breakdown["top10"][0]["name"] == "根津神社"
    assert ranking_breakdown["top10"][0]["score_total_ranked"] >= 0.0


def test_build_chat_recommendations_uses_query_for_visit_style_tags(monkeypatch):
    def fake_resolve_llm_route(*, query, valid_candidates, need_tags, llm_enabled):
        return {
            "recs": {
                "recommendations": [
                    {
                        "name": "静かな神社",
                        "shrine_id": 201,
                        "visit_style_tags": ["quiet", "reset"],
                        "goriyaku": "心願成就",
                        "distance_m": 1200,
                    },
                    {
                        "name": "賑やかな神社",
                        "shrine_id": 202,
                        "visit_style_tags": ["business", "classic"],
                        "goriyaku": "商売繁盛",
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
        query="人が少なくて静かな場所でお参りしたいです",
        language="ja",
        candidates=[
            {
                "name": "静かな神社",
                "shrine_id": 201,
                "visit_style_tags": ["quiet", "reset"],
                "goriyaku": "心願成就",
                "distance_m": 1200,
            },
            {
                "name": "賑やかな神社",
                "shrine_id": 202,
                "visit_style_tags": ["business", "classic"],
                "goriyaku": "商売繁盛",
                "distance_m": 800,
            },
        ],
        bias=None,
        birthdate=None,
        goriyaku_tag_ids=None,
        extra_condition=None,
        public_mode="need",
        flow="A",
    )

    observation = result["_debug"]["visit_style_observation"]
    assert_visit_style_observation_schema(observation)
    assert observation["hit_count"] >= 1
    assert observation["matched_tag_counts"]["quiet"] >= 1

    quiet_row = next(row for row in observation["rows"] if row["name"] == "静かな神社")
    assert "quiet" in quiet_row["matched_tags"]
    assert quiet_row["contribution"] > 0.0

    ranking_breakdown = result["_debug"]["ranking_breakdown_observation"]
    assert_ranking_breakdown_observation_schema(ranking_breakdown)
    quiet_rank = next(row for row in ranking_breakdown["top10"] if row["name"] == "静かな神社")
    assert "quiet" in quiet_rank["matched_visit_style_tags"]
    assert quiet_rank["score_visit_style"] >= 1
    assert quiet_rank["contributions"]["visit_style"] > 0.0


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


def test_observe_ranking_breakdown_returns_stable_schema():
    observation = observe_ranking_breakdown(
        recs={
            "_query": "",
            "_need_tags": [],
            "recommendations": [
                {
                    "id": 1,
                    "shrine_id": 101,
                    "name": "根津神社",
                    "visit_style_tags": ["nature"],
                    "_score_total": 1.23,
                    "breakdown": {
                        "score_need": 1,
                        "score_total": 0.5,
                        "matched_need_tags": ["rest"],
                    },
                    "breakdown_detail": {
                        "features": {
                            "need": {
                                "rank_weighted": 2.0,
                                "rank_weighted_contribution": 0.6,
                            },
                            "distance": {
                                "raw": 0.7,
                                "contribution": 0.2,
                            },
                            "popular": {
                                "raw": 0.4,
                                "contribution": 0.04,
                            },
                            "visit_style": {
                                "raw": 1,
                                "matched_tags": ["nature"],
                                "contribution": 0.35,
                            },
                            "element": {
                                "raw": 0,
                                "contribution": 0.0,
                            },
                            "astro_bonus": 0.0,
                            "score_total_ranked": 1.23,
                            "score_total_ranked_base": 1.23,
                            "capped_behavior_contribution": 0.0,
                            "behavior_ratio": 0.0,
                        }
                    },
                    "_primary_reason_source": "text_hint",
                    "_primary_reason_label": "rest",
                }
            ]
        }
    )

    # Assert _debug fields
    _debug = observation.get("_debug", {})
    assert _debug["query"] == ""
    assert _debug["need_tags"] == []
    assert _debug["matched_need_tags"] == [["rest"]]
    assert _debug["visit_style_tags"] == [["nature"]]
    assert _debug["matched_visit_style_tags"] == [["nature"]]
    assert _debug["score_total_ranked_base"] == [1.23]
    assert _debug["capped_behavior_contribution"] == [0.0]
    assert _debug["behavior_ratio"] == [0.0]

    assert_ranking_breakdown_observation_schema(observation)
    assert_ranking_breakdown_top_row_schema(observation["top10"][0])
    assert observation["ranked_count"] == 1
    row = observation["top10"][0]
    assert row["name"] == "根津神社"
    assert row["score_raw"] == 1.23
    assert row["score_total"] == 0.5
    assert row["score_total_ranked"] == 1.23
    assert row["score_need"] == 1
    assert row["score_need_rank_weighted"] == 2.0
    assert row["score_distance"] == 0.7
    assert row["score_popular"] == 0.4
    assert row["score_visit_style"] == 1
    assert row["contributions"]["visit_style"] == 0.35
    assert row["matched_need_tags"] == ["rest"]
    assert row["matched_visit_style_tags"] == ["nature"]
    assert row["primary_reason_source"] == "text_hint"
    assert row["primary_reason_label"] == "rest"


def test_observe_ranking_breakdown_supports_user_selected_tag_reason():
    observation = observe_ranking_breakdown(
        recs={
            "recommendations": [
                {
                    "shrine_id": 101,
                    "name": "美容神社",
                    "_score_total": 1.5,
                    "breakdown": {
                        "score_need": 0,
                        "score_total": 0.5,
                        "matched_need_tags": [],
                    },
                    "breakdown_detail": {
                        "features": {
                            "need": {
                                "rank_weighted": 0.0,
                                "rank_weighted_contribution": 0.0,
                            },
                            "distance": {
                                "raw": 0.0,
                                "contribution": 0.0,
                            },
                            "popular": {
                                "raw": 0.0,
                                "contribution": 0.0,
                            },
                            "visit_style": {
                                "raw": 0,
                                "matched_tags": [],
                                "contribution": 0.0,
                            },
                            "element": {
                                "raw": 0,
                                "contribution": 0.0,
                            },
                            "astro_bonus": 0.0,
                            "score_total_ranked": 1.5,
                        }
                    },
                    "_reason_facts": [
                        {
                            "type": "user_selected_tag",
                            "label": "goriyaku_tag:1",
                            "label_ja": "美容",
                            "evidence": ["requested_goriyaku_tag_ids"],
                            "score": 3.0,
                            "is_primary": True,
                        }
                    ],
                    "_primary_reason_source": "user_selected_tag",
                    "_primary_reason_label": "goriyaku_tag:1",
                }
            ]
        }
    )

    row = observation["top10"][0]
    assert row["primary_reason_source"] == "user_selected_tag"
    assert row["primary_reason_label"] == "goriyaku_tag:1"


def test_build_reason_facts_generates_user_selected_tag_reason():
    facts = _build_reason_facts(
        matched_by_tag=[],
        matched_by_gid=[],
        matched_by_text=[],
        matched_by_user_selected_gid=[1],
        goriyaku_tag_label_by_id={1: "美容"},
        text_score_by_tag={},
        score_element=0,
        astro_bonus_enabled=False,
    )

    assert facts[0] == {
        "type": "user_selected_tag",
        "label": "美容",
        "label_ja": "美容",
        "evidence": ["requested_goriyaku_tag_ids"],
        "score": 3.0,
        "is_primary": False,
    }


def test_resolve_primary_reason_prefers_user_selected_tag():
    facts = _build_reason_facts(
        matched_by_tag=["rest"],
        matched_by_gid=["money"],
        matched_by_text=["mental"],
        matched_by_user_selected_gid=[1],
        goriyaku_tag_label_by_id={1: "美容"},
        text_score_by_tag={"mental": 5},
        score_element=2,
        astro_bonus_enabled=True,
    )

    primary = _resolve_primary_reason(facts)

    assert primary["type"] == "user_selected_tag"
    assert primary["label"] == "美容"
    assert primary["evidence"] == ["requested_goriyaku_tag_ids"]


def test_attach_breakdown_sets_user_selected_tag_as_primary_reason():
    rec = {
        "shrine_id": 101,
        "name": "美容神社",
        "goriyaku_tag_ids": [1],
        "astro_elements": [],
        "astro_tags": [],
        "goriyaku": "",
        "description": "",
        "popular_score": 0,
        "distance_m": None,
        "visit_style_tags": [],
    }

    _attach_breakdown(
        rec,
        birthdate=None,
        need_tags=["rest"],
        weights={"element": 0.0, "need": 0.3, "popular": 0.0, "distance": 0.0},
        astro_bonus_enabled=False,
        visit_style_tags=set(),
        query="美容で整えたい",
        requested_goriyaku_tag_ids=[1],
        goriyaku_tag_label_by_id={1: "美容"},
    )

    assert rec["_primary_reason_source"] == "user_selected_tag"
    assert rec["_primary_reason_label"] == "美容"
    assert rec["_reason_facts"][0]["type"] == "user_selected_tag"
    assert rec["_reason_facts"][0]["is_primary"] is True
    assert rec["_reason_facts"][0]["evidence"] == ["requested_goriyaku_tag_ids"]


def test_resolve_direction_bonus_returns_zero_without_birthdate_or_location():
    assert _resolve_direction_bonus(
        rec={"shrine_id": 101, "name": "方位未設定神社"},
        birthdate=None,
    ) == {"bonus": 0.0, "reason": None}

    assert _resolve_direction_bonus(
        rec={"shrine_id": 101, "name": "方位未設定神社", "latitude": 35.0, "longitude": 139.0},
        birthdate="",
    ) == {"bonus": 0.0, "reason": None}


def test_resolve_direction_bonus_returns_bonus_with_user_origin_birthdate_and_location():
    result = _resolve_direction_bonus(
        rec={"shrine_id": 101, "name": "東方面神社", "latitude": 35.0, "longitude": 140.0},
        birthdate="1990-01-01",
        user_origin={"lat": 35.0, "lng": 139.0},
    )

    assert result["bonus"] == 0.1
    assert result["reason"] == "現在地から見て東方面の候補です"


def test_attach_breakdown_reflects_direction_bonus_in_score_v2_and_breakdown_detail():
    rec = {
        "shrine_id": 101,
        "name": "東方面神社",
        "latitude": 35.0,
        "longitude": 140.0,
        "goriyaku_tag_ids": [],
        "astro_elements": [],
        "astro_tags": [],
        "goriyaku": "",
        "description": "",
        "popular_score": 0,
        "distance_m": None,
        "visit_style_tags": [],
    }

    _attach_breakdown(
        rec,
        birthdate="1990-01-01",
        need_tags=[],
        weights={"element": 0.0, "need": 0.3, "popular": 0.0, "distance": 0.0},
        astro_bonus_enabled=False,
        visit_style_tags=set(),
        query=None,
        user_origin={"lat": 35.0, "lng": 139.0},
    )

    assert rec["score_v2"]["components"]["direction_bonus"] == 0.1
    assert rec["score_v2"]["components"]["direction_reason"] == "現在地から見て東方面の候補です"

    direction_feature = rec["breakdown_detail"]["features"]["direction_bonus"]
    assert direction_feature["raw"] == 0.1
    assert direction_feature["contribution"] == 0.1
    assert direction_feature["reason"] == "現在地から見て東方面の候補です"

def test_resolve_direction_bonus_stays_zero_without_user_origin_even_with_birthdate_and_location():
    # direction calculation stays zero when user origin lat/lng is absent.
    result = _resolve_direction_bonus(
        rec={"shrine_id": 101, "name": "方位候補神社", "latitude": 35.0, "longitude": 139.0},
        birthdate="1990-01-01",
    )

    assert result == {"bonus": 0.0, "reason": None}
    assert result["bonus"] <= DIRECTION_BONUS_MAX


def test_attach_breakdown_attaches_direction_bonus_contract():
    rec = {
        "shrine_id": 101,
        "name": "方位候補神社",
        "latitude": 35.0,
        "longitude": 139.0,
        "goriyaku_tag_ids": [],
        "astro_elements": [],
        "astro_tags": [],
        "goriyaku": "",
        "description": "",
        "popular_score": 0,
        "distance_m": None,
        "visit_style_tags": [],
    }

    _attach_breakdown(
        rec,
        birthdate="1990-01-01",
        need_tags=[],
        weights={"element": 0.0, "need": 0.3, "popular": 0.0, "distance": 0.0},
        astro_bonus_enabled=False,
        visit_style_tags=set(),
        query=None,
    )

    assert rec["breakdown"]["direction_bonus"] == 0.0
    assert rec["breakdown"]["weights"]["direction_bonus"] == 0.0

    direction_feature = rec["breakdown_detail"]["features"]["direction_bonus"]
    assert direction_feature == {
        "raw": 0.0,
        "weight": 1.0,
        "contribution": 0.0,
        "reason": None,
        "max": DIRECTION_BONUS_MAX,
    }

    assert rec["score_v2"]["components"]["direction_bonus"] == 0.0
    assert rec["score_v2"]["components"]["direction_reason"] is None


def test_observe_ranking_breakdown_empty_contract_has_stable_schema():
    observation = observe_ranking_breakdown(recs={"recommendations": []})

    assert_ranking_breakdown_observation_schema(observation)
    assert observation == {
        "ranked_count": 0,
        "top10": [],
        "_debug": {
            "query": "",
            "need_tags": [],
            "matched_need_tags": [],
            "visit_style_tags": [],
            "matched_visit_style_tags": [],
            "score_total_ranked_base": [],
            "capped_behavior_contribution": [],
            "behavior_ratio": [],
            "reflection_hint_state_change_direction": [],
            "reflection_hint_next_need_hint": [],
            "reflection_hint_next_history_theme_hint": [],
            "reflection_hint_source_history_theme": [],
        },
    }
