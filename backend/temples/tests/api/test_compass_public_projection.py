"""Compass Monthly Public Projection の単体テスト。

docs/audit/compass-monthly-api-boundary.md Section 12（Response Shape
Regression Test Contract）。DBもHTTPも使わず、投影そのものの性質だけを固定する。
"""

from __future__ import annotations

import copy

import pytest

from temples.api.compass_public_projection import (
    COMPASS_MONTHLY_PUBLIC_ITEM_ALLOWLIST,
    CompassPublicProjectionContractError,
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
        # Shared Recommendation Candidate が保持する Knowledge（selector順）。
        "knowledge_deities": [
            {"display_name": "天照大神", "sort_order": 0, "confidence": "high"},
            {"display_name": "豊受大神", "sort_order": 1, "confidence": "high"},
        ],
        "knowledge_histories": [
            {
                "history_type": "official_origin",
                "title": "創建",
                "content": "古くより地域の守りとして祀られてきた。",
                "period_text": "奈良時代",
                "sort_order": 0,
                "confidence": "high",
            },
            {
                "history_type": "legend",
                "title": "伝承",
                "content": "二件目の由緒。",
                "period_text": None,
                "sort_order": 1,
                "confidence": "high",
            },
        ],
        **KNOWN_INTERNAL_FIELDS,
        **UNKNOWN_FUTURE_FIELDS,
    }


EXPECTED_SHRINE_FACTS = {
    "deity": {"display_name": "天照大神"},
    "history": {
        "history_type": "official_origin",
        "content": "古くより地域の守りとして祀られてきた。",
    },
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
    assert projected["reason_facts"] == [
        {"type": "history_theme", "label": "守り", "label_ja": "守り", "is_primary": True}
    ]
    assert projected["shrine_facts"] == EXPECTED_SHRINE_FACTS
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


def test_reason_facts_expose_only_public_meaning_fields():
    """reason_facts は type / label / label_ja / is_primary だけを公開する。"""
    projected = project_compass_recommendation(
        _full_source_recommendation(), recommendation_instance_id=INSTANCE_ID
    )

    for fact in projected["reason_facts"]:
        assert set(fact) == {"type", "label", "label_ja", "is_primary"}


def test_reason_facts_do_not_expose_evidence_or_score():
    projected = project_compass_recommendation(
        _full_source_recommendation(), recommendation_instance_id=INSTANCE_ID
    )

    for fact in projected["reason_facts"]:
        assert "evidence" not in fact
        assert "score" not in fact


def test_reason_facts_copy_only_present_public_fields():
    """source に無い公開fieldは捏造しない（既存fail-safeの維持）。"""
    projected = project_compass_recommendation(
        {"reason_facts": [{"type": "element", "label": "水", "future_field": "x"}]},
        recommendation_instance_id=INSTANCE_ID,
    )

    assert projected["reason_facts"] == [{"type": "element", "label": "水"}]


def test_absent_public_fields_are_not_invented():
    """任意の公開fieldは、単体item投影helperによって捏造されない（Section 11）。

    R-3 以後の scope:
      本testが守るのは「投影は値をでっち上げない」という fail-safe であり、
      「shrine_id が無くてもよい」という許可ではない。
      Monthly の recommendation_success における shrine_id 必須化は
      list境界の project_compass_recommendations(require_shrine_id=True) が
      担う（R-3。本file下部の Identity Gate testsを参照）。
      単体helperは identity gate を持たないため、ここでの shrine_id 不在は
      「捏造しない」ことの確認対象として有効なまま残る。
    """
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


# ---------------------------------------------------------------------------
# shrine_facts（Shrine Fact）
#
# reason_facts   = なぜ今回この神社を推薦候補にしたのか（Meaning）
# shrine_facts   = ユーザーの相談とは独立した、その神社そのものの確認済みFact
# ---------------------------------------------------------------------------


def test_shrine_facts_projects_at_most_one_deity_from_many():
    projected = project_compass_recommendation(
        _full_source_recommendation(), recommendation_instance_id=INSTANCE_ID
    )

    # 複数件あっても selector 順の先頭1件だけ。
    assert projected["shrine_facts"]["deity"] == {"display_name": "天照大神"}


def test_shrine_facts_projects_at_most_one_history_from_many():
    projected = project_compass_recommendation(
        _full_source_recommendation(), recommendation_instance_id=INSTANCE_ID
    )

    assert projected["shrine_facts"]["history"] == {
        "history_type": "official_origin",
        "content": "古くより地域の守りとして祀られてきた。",
    }


def test_shrine_facts_deity_public_shape_is_display_name_only():
    projected = project_compass_recommendation(
        _full_source_recommendation(), recommendation_instance_id=INSTANCE_ID
    )

    assert set(projected["shrine_facts"]["deity"]) == {"display_name"}


def test_shrine_facts_history_public_shape_is_type_and_content_only():
    projected = project_compass_recommendation(
        _full_source_recommendation(), recommendation_instance_id=INSTANCE_ID
    )

    assert set(projected["shrine_facts"]["history"]) == {"history_type", "content"}


def test_shrine_facts_do_not_leak_knowledge_internal_fields():
    source = _full_source_recommendation()
    for entry in source["knowledge_deities"] + source["knowledge_histories"]:
        entry["verification_status"] = "verified"
        entry["sources"] = [{"title": "出典", "url": "https://example.com"}]

    projected = project_compass_recommendation(source, recommendation_instance_id=INSTANCE_ID)

    internal = {
        "confidence",
        "sort_order",
        "verification_status",
        "sources",
        "title",
        "period_text",
    }
    assert set(projected["shrine_facts"]) == {"deity", "history"}
    for fact in projected["shrine_facts"].values():
        assert not (set(fact) & internal), sorted(set(fact) & internal)


def test_raw_knowledge_keys_do_not_leak():
    projected = project_compass_recommendation(
        _full_source_recommendation(), recommendation_instance_id=INSTANCE_ID
    )

    assert "knowledge_deities" not in projected
    assert "knowledge_histories" not in projected
    assert "knowledge_deities" not in COMPASS_MONTHLY_PUBLIC_ITEM_ALLOWLIST
    assert "knowledge_histories" not in COMPASS_MONTHLY_PUBLIC_ITEM_ALLOWLIST


@pytest.mark.parametrize(
    "knowledge",
    [
        {},
        {"knowledge_deities": [], "knowledge_histories": []},
        {"knowledge_deities": None, "knowledge_histories": None},
    ],
)
def test_shrine_facts_is_omitted_when_neither_deity_nor_history_exists(knowledge):
    projected = project_compass_recommendation(
        {"shrine_id": 1, **knowledge}, recommendation_instance_id=INSTANCE_ID
    )

    assert "shrine_facts" not in projected


def test_shrine_facts_is_not_backfilled_from_other_fields():
    """goriyaku / description / reason / reason_facts 等から Fact を補完しない。"""
    projected = project_compass_recommendation(
        {
            "shrine_id": 1,
            "goriyaku": "仕事運",
            "description": "説明文",
            "sajin": "天照大神",
            "history_theme": "守り",
            "reason": "仕事運の後押し",
            "reason_facts": [{"type": "history_theme", "label": "守り"}],
        },
        recommendation_instance_id=INSTANCE_ID,
    )

    assert "shrine_facts" not in projected


def test_shrine_facts_deity_only_partial_shape():
    projected = project_compass_recommendation(
        {"knowledge_deities": [{"display_name": "天照大神"}]},
        recommendation_instance_id=INSTANCE_ID,
    )

    assert projected["shrine_facts"] == {"deity": {"display_name": "天照大神"}}


def test_shrine_facts_history_only_partial_shape():
    projected = project_compass_recommendation(
        {"knowledge_histories": [{"history_type": "legend", "content": "伝承の由緒。"}]},
        recommendation_instance_id=INSTANCE_ID,
    )

    assert projected["shrine_facts"] == {
        "history": {"history_type": "legend", "content": "伝承の由緒。"}
    }


def test_malformed_knowledge_values_are_not_exposed_raw():
    """list でない / mapping でない / 公開fieldが不正な要素は生のまま出さない。"""
    projected = project_compass_recommendation(
        {
            "knowledge_deities": {"display_name": "listではない"},
            "knowledge_histories": "official_origin: 文字列",
        },
        recommendation_instance_id=INSTANCE_ID,
    )

    assert "shrine_facts" not in projected


def test_invalid_knowledge_entries_are_skipped_until_first_valid_one():
    projected = project_compass_recommendation(
        {
            "knowledge_deities": [
                "天照大神",
                None,
                {"display_name": ""},
                {"display_name": "   "},
                {"display_name": 123},
                {"sort_order": 0},
                {"display_name": "有効な祭神", "confidence": "high"},
                {"display_name": "二件目"},
            ],
            "knowledge_histories": [
                ["official_origin", "内容"],
                {"history_type": "official_origin", "content": ""},
                {"history_type": "", "content": "型が空"},
                {"history_type": "official_origin"},
                {"content": "typeが無い"},
                {"history_type": {"nested": 1}, "content": "型がmapping"},
                {"history_type": "legend", "content": "有効な由緒", "title": "内部"},
            ],
        },
        recommendation_instance_id=INSTANCE_ID,
    )

    assert projected["shrine_facts"] == {
        "deity": {"display_name": "有効な祭神"},
        "history": {"history_type": "legend", "content": "有効な由緒"},
    }


def test_shrine_facts_do_not_share_objects_with_source():
    source = _full_source_recommendation()
    snapshot = copy.deepcopy(source)

    projected = project_compass_recommendation(source, recommendation_instance_id=INSTANCE_ID)
    projected["shrine_facts"]["deity"]["display_name"] = "書き換え"
    projected["shrine_facts"]["history"]["content"] = "書き換え"

    assert source == snapshot


def test_shrine_facts_preserve_recommendation_order_and_count():
    sources = [
        {"shrine_id": 1, "knowledge_deities": [{"display_name": "一の祭神"}]},
        {"shrine_id": 2},
        {"shrine_id": 3, "knowledge_histories": [{"history_type": "legend", "content": "三"}]},
    ]

    projected = project_compass_recommendations(
        sources, recommendation_instance_id=INSTANCE_ID, require_shrine_id=True
    )

    assert [item["shrine_id"] for item in projected] == [1, 2, 3]
    assert projected[0]["shrine_facts"] == {"deity": {"display_name": "一の祭神"}}
    assert "shrine_facts" not in projected[1]
    assert projected[2]["shrine_facts"] == {"history": {"history_type": "legend", "content": "三"}}


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

    projected = project_compass_recommendations(
        sources, recommendation_instance_id=INSTANCE_ID, require_shrine_id=False
    )

    assert len(projected) == len(sources)
    assert [item["shrine_id"] for item in projected] == [1, 2, 3]


def test_every_item_carries_the_request_level_instance_id():
    projected = project_compass_recommendations(
        [{"shrine_id": 1}, {"shrine_id": 2, "recommendation_instance_id": "stale999"}],
        recommendation_instance_id=INSTANCE_ID,
        require_shrine_id=False,
    )

    assert [item["recommendation_instance_id"] for item in projected] == [INSTANCE_ID, INSTANCE_ID]


def test_empty_recommendations_project_to_empty_list():
    for require in (False, True):
        assert (
            project_compass_recommendations(
                [], recommendation_instance_id=INSTANCE_ID, require_shrine_id=require
            )
            == []
        )
        assert (
            project_compass_recommendations(
                None, recommendation_instance_id=INSTANCE_ID, require_shrine_id=require
            )
            == []
        )


# ---------------------------------------------------------------------------
# R-3 Identity Gate
# docs/audit/compass-shrine-id-presence-audit.md §11
#
#   R-3_BEHAVIOR = FAIL_CLOSED_WHOLE_RESPONSE_ON_MISSING_OR_NULL_SHRINE_ID
#
# require_shrine_id=True（= state recommendation_success）のとき、
# recommendations[] の全itemが shrine_id を持ち、non-null であることを要求する。
# `id` は COMPATIBILITY_FIELD であり identity authority ではない（R-2 / #2952）。
# 本moduleはDBを引かないため、ここで検証するのは存在と非nullのみ。
# shrine_id が実在Shrine行へ解決することは HTTP 境界の DB-backed regression
# （R-1 / #2951）が担う。
# ---------------------------------------------------------------------------


def test_identity_gate_passes_with_valid_shrine_id():
    """(1) require_shrine_id=True + 有効な shrine_id -> 通過する。"""
    projected = project_compass_recommendations(
        [{"shrine_id": 101, "name": "一"}, {"shrine_id": 102, "name": "二"}],
        recommendation_instance_id=INSTANCE_ID,
        require_shrine_id=True,
    )

    assert [item["shrine_id"] for item in projected] == [101, 102]
    assert [item["name"] for item in projected] == ["一", "二"]


def test_identity_gate_raises_when_shrine_id_is_missing():
    """(2) shrine_id 不在 -> CompassPublicProjectionContractError。"""
    with pytest.raises(CompassPublicProjectionContractError):
        project_compass_recommendations(
            [{"name": "shrine_idの無い神社"}],
            recommendation_instance_id=INSTANCE_ID,
            require_shrine_id=True,
        )


def test_identity_gate_raises_when_shrine_id_is_none():
    """(3) shrine_id=None -> CompassPublicProjectionContractError。"""
    with pytest.raises(CompassPublicProjectionContractError):
        project_compass_recommendations(
            [{"shrine_id": None, "name": "shrine_idがnullの神社"}],
            recommendation_instance_id=INSTANCE_ID,
            require_shrine_id=True,
        )


def test_identity_gate_does_not_accept_id_as_shrine_id_fallback():
    """(4) id はあるが shrine_id が無い -> それでも raise。

    `id` を identity として代用しないことの証明。R-2 が定めたとおり
    `id` は COMPATIBILITY_FIELD であって identity authority ではない。
    """
    with pytest.raises(CompassPublicProjectionContractError):
        project_compass_recommendations(
            [{"id": 101, "name": "idだけの神社"}],
            recommendation_instance_id=INSTANCE_ID,
            require_shrine_id=True,
        )


def test_identity_gate_fails_whole_projection_when_one_item_is_invalid():
    """(5) 1件でも不正なら投影全体が raise する。

    部分成功を作らない / 不正itemだけを落とさないことの証明。
    """
    sources = [
        {"shrine_id": 101, "name": "有効1"},
        {"name": "不正"},
        {"shrine_id": 103, "name": "有効2"},
    ]

    with pytest.raises(CompassPublicProjectionContractError):
        project_compass_recommendations(
            sources,
            recommendation_instance_id=INSTANCE_ID,
            require_shrine_id=True,
        )


def test_identity_gate_fails_whole_projection_when_a_later_item_is_null():
    """(5-b) 違反が末尾にあっても、先行itemの投影結果は返らない。"""
    sources = [
        {"shrine_id": 101, "name": "有効1"},
        {"shrine_id": 102, "name": "有効2"},
        {"shrine_id": None, "name": "末尾が不正"},
    ]

    with pytest.raises(CompassPublicProjectionContractError):
        project_compass_recommendations(
            sources,
            recommendation_instance_id=INSTANCE_ID,
            require_shrine_id=True,
        )


def test_identity_gate_rejects_non_mapping_item():
    """(5-c) Mapping でない item も identity を持ちえないため raise する。"""
    with pytest.raises(CompassPublicProjectionContractError):
        project_compass_recommendations(
            [{"shrine_id": 101}, "not a recommendation"],
            recommendation_instance_id=INSTANCE_ID,
            require_shrine_id=True,
        )


def test_identity_gate_does_not_mutate_source():
    """(6) gate を通しても source は書き換えられない（成功時・失敗時とも）。"""
    valid_sources = [{"shrine_id": 101, "name": "一"}, {"shrine_id": 102, "name": "二"}]
    valid_snapshot = copy.deepcopy(valid_sources)

    project_compass_recommendations(
        valid_sources,
        recommendation_instance_id=INSTANCE_ID,
        require_shrine_id=True,
    )

    assert valid_sources == valid_snapshot

    invalid_sources = [{"shrine_id": 101, "name": "一"}, {"id": 102, "name": "二"}]
    invalid_snapshot = copy.deepcopy(invalid_sources)

    with pytest.raises(CompassPublicProjectionContractError):
        project_compass_recommendations(
            invalid_sources,
            recommendation_instance_id=INSTANCE_ID,
            require_shrine_id=True,
        )

    assert invalid_sources == invalid_snapshot


def test_identity_gate_is_not_applied_when_require_shrine_id_is_false():
    """非success状態では gate を課さない（direction_zero_candidates 等）。

    require_shrine_id=False のときは従来どおり allowlist 投影のみを行う。
    """
    projected = project_compass_recommendations(
        [{"name": "shrine_idの無い神社"}],
        recommendation_instance_id=INSTANCE_ID,
        require_shrine_id=False,
    )

    assert projected == [{"name": "shrine_idの無い神社", "recommendation_instance_id": INSTANCE_ID}]
