

from __future__ import annotations

from temples.services.recommendation_input_profile import (
    build_recommendation_input_profile,
)


def test_build_recommendation_input_profile_returns_stable_schema():
    profile = build_recommendation_input_profile(
        interpretation_profile={
            "raw_query": "仕事で迷っている",
            "state_profile": {"primary_state": "uncertain"},
            "need_profile": {"need_tags": ["career"]},
        },
        translation_result={
            "history_theme": "再出発",
            "action_context": "次に小さく動かすことを確認する",
            "reflection_question_seed": "何から始めますか？",
        },
        candidate_profile={
            "shrine_id": 1,
            "name": "例の神社",
            "history_theme": "勝負",
            "goriyaku_tags": ["仕事運"],
        },
        score_v2_fields={
            "score_total": 12.5,
            "score_v2_total": 8.0,
        },
    )

    assert set(profile.keys()) == {
        "interpretation_profile",
        "translation_result",
        "candidate_profile",
        "score_v2_fields",
    }
    assert profile["interpretation_profile"]["raw_query"] == "仕事で迷っている"
    assert profile["translation_result"]["history_theme"] == "再出発"
    assert profile["candidate_profile"]["shrine_id"] == 1
    assert profile["score_v2_fields"]["score_total"] == 12.5


def test_build_recommendation_input_profile_accepts_all_expected_inputs():
    profile = build_recommendation_input_profile(
        interpretation_profile={"state_profile": {"primary_state": "tired"}},
        translation_result={"action_context": "休む前提を整える"},
        candidate_profile={"name": "静寂神社"},
        score_v2_fields={"score_v2_total": 3.2},
    )

    assert profile["interpretation_profile"] == {"state_profile": {"primary_state": "tired"}}
    assert profile["translation_result"] == {"action_context": "休む前提を整える"}
    assert profile["candidate_profile"] == {"name": "静寂神社"}
    assert profile["score_v2_fields"] == {"score_v2_total": 3.2}


def test_build_recommendation_input_profile_normalizes_missing_inputs_to_empty_dicts():
    profile = build_recommendation_input_profile()

    assert profile == {
        "interpretation_profile": {},
        "translation_result": {},
        "candidate_profile": {},
        "score_v2_fields": {},
    }


def test_build_recommendation_input_profile_ignores_non_dict_inputs_safely():
    profile = build_recommendation_input_profile(
        interpretation_profile=None,
        translation_result=["not", "dict"],
        candidate_profile="not-dict",
        score_v2_fields=123,
    )

    assert profile == {
        "interpretation_profile": {},
        "translation_result": {},
        "candidate_profile": {},
        "score_v2_fields": {},
    }
