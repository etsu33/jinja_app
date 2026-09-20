"""Compass Monthly Public Projection の単体テスト。

docs/audit/compass-monthly-api-boundary.md Section 12（Response Shape
Regression Test Contract）。DBもHTTPも使わず、投影そのものの性質だけを固定する。
"""

from __future__ import annotations

import copy

from temples.api.compass_public_projection import (
    COMPASS_MONTHLY_PUBLIC_ITEM_ALLOWLIST,
    project_compass_recommendation,
    project_compass_recommendations,
)

INSTANCE_ID = "abcd1234"

# 既知の非公開field（audit Section 7 の Confirmed leakage 一覧）。
KNOWN_INTERNAL_FIELDS = {
    "_explanation_payload": {"prompt": "internal"},
    "_prefilter_debug": {"stage": "debug"},
    "_primary_reason_label": "内部ラベル",
    "_primary_reason_source": "goriyaku_tag",
    "_reason_facts": [{"type": "element", "label": "内部", "evidence": ["x"]}],
    "_score_total": 12.5,
    "breakdown_detail": {"a": 1},
    "score_v2": {"total": 9.9},
    "popular_score": 3.0,
    "rank_comparison": {"rank": 1},
    "rank_explanation": {"why": "internal"},
    "recommendation_reason_quality": {"score": 0.8},
    "recommendation_reason_v4_detail": {"draft": "internal"},
}

# 実装が知らない将来field（allowlistであることの証明）。
UNKNOWN_FUTURE_FIELDS = {
    "future_internal_field": "leak?",
    "new_experiment_score": 42,
    "future_debug_payload": {"nested": "leak?"},
}


def _full_source_recommendation() -> dict:
    return {
        "shrine_id": 101,
        "id": 101,
        "name": "北西の神社",
        "address": "東京都千代田区",
        "distance_m": 35900.0,
        "reason": "仕事運の後押し",
        "breakdown": {
            "matched_need_tags": ["career"],
            "score_total": 88.0,
            "weights": {"need": 1.0},
            "need_evidence_winner_by_tag": {"career": "gid"},
        },
        "reason_facts": [
            {
                "type": "history_theme",
                "label": "守り",
                "label_ja": "守り",
                "is_primary": True,
                "evidence": ["history_theme"],
                "score": 1.0,
            }
        ],
        **KNOWN_INTERNAL_FIELDS,
        **UNKNOWN_FUTURE_FIELDS,
    }


def test_public_fields_survive_unchanged():
    source = _full_source_recommendation()

    projected = project_compass_recommendation(source, recommendation_instance_id=INSTANCE_ID)

    assert projected["shrine_id"] == 101
    assert projected["id"] == 101
    assert projected["name"] == "北西の神社"
    assert projected["address"] == "東京都千代田区"
    assert projected["distance_m"] == 35900.0
    assert projected["reason"] == "仕事運の後押し"
    assert projected["breakdown"] == {"matched_need_tags": ["career"]}
    assert projected["reason_facts"] == [{"type": "history_theme", "label": "守り"}]
    assert projected["recommendation_instance_id"] == INSTANCE_ID


def test_projected_keys_are_subset_of_public_allowlist():
    projected = project_compass_recommendation(
        _full_source_recommendation(), recommendation_instance_id=INSTANCE_ID
    )

    assert set(projected).issubset(COMPASS_MONTHLY_PUBLIC_ITEM_ALLOWLIST)


def test_known_internal_fields_do_not_leak():
    projected = project_compass_recommendation(
        _full_source_recommendation(), recommendation_instance_id=INSTANCE_ID
    )

    for field in KNOWN_INTERNAL_FIELDS:
        assert field not in projected


def test_unknown_future_fields_do_not_leak():
    """denylistではなくallowlistであることの証明（Section 12）。"""
    projected = project_compass_recommendation(
        _full_source_recommendation(), recommendation_instance_id=INSTANCE_ID
    )

    for field in UNKNOWN_FUTURE_FIELDS:
        assert field not in projected


def test_breakdown_exposes_only_matched_need_tags():
    projected = project_compass_recommendation(
        _full_source_recommendation(), recommendation_instance_id=INSTANCE_ID
    )

    assert set(projected["breakdown"]) == {"matched_need_tags"}


def test_reason_facts_expose_only_type_and_label():
    projected = project_compass_recommendation(
        _full_source_recommendation(), recommendation_instance_id=INSTANCE_ID
    )

    for fact in projected["reason_facts"]:
        assert set(fact) <= {"type", "label"}


def test_absent_public_fields_are_not_invented():
    projected = project_compass_recommendation(
        {"name": "名前だけの神社"}, recommendation_instance_id=INSTANCE_ID
    )

    assert projected == {"name": "名前だけの神社", "recommendation_instance_id": INSTANCE_ID}


def test_non_mapping_breakdown_is_dropped_not_exposed():
    projected = project_compass_recommendation(
        {"breakdown": "matched_need_tags=career"}, recommendation_instance_id=INSTANCE_ID
    )

    assert "breakdown" not in projected


def test_non_list_matched_need_tags_is_dropped_not_exposed():
    projected = project_compass_recommendation(
        {"breakdown": {"matched_need_tags": {"career": True}, "score_total": 1.0}},
        recommendation_instance_id=INSTANCE_ID,
    )

    assert projected["breakdown"] == {}


def test_non_list_reason_facts_is_dropped_not_exposed():
    projected = project_compass_recommendation(
        {"reason_facts": {"type": "element", "label": "水"}},
        recommendation_instance_id=INSTANCE_ID,
    )

    assert "reason_facts" not in projected


def test_non_mapping_reason_facts_entries_are_skipped():
    projected = project_compass_recommendation(
        {"reason_facts": ["element", None, 3, {"type": "element", "label": "水", "score": 1.0}]},
        recommendation_instance_id=INSTANCE_ID,
    )

    assert projected["reason_facts"] == [{"type": "element", "label": "水"}]


def test_non_mapping_recommendation_yields_instance_id_only():
    projected = project_compass_recommendation(
        "not a recommendation", recommendation_instance_id=INSTANCE_ID
    )

    assert projected == {"recommendation_instance_id": INSTANCE_ID}


def test_source_recommendation_is_not_mutated():
    source = _full_source_recommendation()
    snapshot = copy.deepcopy(source)

    projected = project_compass_recommendation(source, recommendation_instance_id=INSTANCE_ID)
    # 投影結果を触っても source 側が巻き込まれない（list を共有していない）。
    projected["breakdown"]["matched_need_tags"].append("money")
    projected["reason_facts"].append({"type": "injected", "label": "injected"})

    assert source == snapshot


def test_order_and_count_are_preserved():
    sources = [
        {"shrine_id": 1, "name": "一"},
        {"shrine_id": 2, "name": "二"},
        {"shrine_id": 3, "name": "三"},
    ]

    projected = project_compass_recommendations(sources, recommendation_instance_id=INSTANCE_ID)

    assert len(projected) == len(sources)
    assert [item["shrine_id"] for item in projected] == [1, 2, 3]


def test_every_item_carries_the_request_level_instance_id():
    projected = project_compass_recommendations(
        [{"shrine_id": 1}, {"shrine_id": 2, "recommendation_instance_id": "stale999"}],
        recommendation_instance_id=INSTANCE_ID,
    )

    assert [item["recommendation_instance_id"] for item in projected] == [INSTANCE_ID, INSTANCE_ID]


def test_empty_recommendations_project_to_empty_list():
    assert project_compass_recommendations([], recommendation_instance_id=INSTANCE_ID) == []
    assert project_compass_recommendations(None, recommendation_instance_id=INSTANCE_ID) == []
