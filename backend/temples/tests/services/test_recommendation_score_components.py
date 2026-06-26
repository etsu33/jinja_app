

from __future__ import annotations

from temples.services.recommendation_score_components import (
    calculate_behavior_score,
    calculate_history_score,
    calculate_meaning_match_score,
    calculate_recommendation_score_components,
    calculate_shrine_profile_score,
    calculate_state_match_score,
)


def _profile() -> dict:
    return {
        "interpretation_profile": {
            "state_profile": {
                "primary_state": "uncertain",
                "confidence": 0.8,
            },
            "need_profile": {
                "need_tags": ["career"],
            },
        },
        "translation_result": {
            "history_theme": "再出発",
            "action_context": "次に小さく動かすことを確認する",
            "reflection_question_seed": "何から始めますか？",
        },
        "candidate_profile": {
            "shrine_id": 1,
            "name": "再出発神社",
            "history_theme": "再出発",
            "goriyaku_tags": ["仕事運"],
            "visit_style_tags": ["静かに参拝"],
            "behavior_signals": {
                "detail_view_count": 1,
                "save_count": 1,
                "route_open_count": 1,
                "visit_done_count": 1,
                "reflection_saved_count": 1,
            },
        },
        "score_v2_fields": {
            "score_total": 12.5,
            "score_v2_total": 8.0,
        },
    }


def test_calculate_state_match_score_uses_state_and_candidate_context():
    assert calculate_state_match_score(_profile()) == 0.93


def test_calculate_meaning_match_score_uses_translation_result():
    assert calculate_meaning_match_score(_profile()) == 1.0


def test_calculate_shrine_profile_score_uses_candidate_completeness():
    assert calculate_shrine_profile_score(_profile()) == 1.0


def test_calculate_behavior_score_uses_behavior_signals():
    assert calculate_behavior_score(_profile()) == 1.0


def test_calculate_history_score_returns_full_score_when_theme_matches():
    assert calculate_history_score(_profile()) == 1.0


def test_calculate_history_score_returns_partial_score_when_both_themes_exist_but_do_not_match():
    profile = _profile()
    profile["candidate_profile"]["history_theme"] = "勝負"

    assert calculate_history_score(profile) == 0.35


def test_calculate_recommendation_score_components_returns_stable_schema():
    result = calculate_recommendation_score_components(_profile())

    assert set(result.keys()) == {
        "state_match_score",
        "meaning_match_score",
        "shrine_profile_score",
        "behavior_score",
        "history_score",
        "final_score",
    }
    assert result == {
        "state_match_score": 0.93,
        "meaning_match_score": 1.0,
        "shrine_profile_score": 1.0,
        "behavior_score": 1.0,
        "history_score": 1.0,
        "final_score": 4.93,
    }


def test_calculate_recommendation_score_components_handles_missing_profile_safely():
    assert calculate_recommendation_score_components(None) == {
        "state_match_score": 0.0,
        "meaning_match_score": 0.0,
        "shrine_profile_score": 0.0,
        "behavior_score": 0.0,
        "history_score": 0.0,
        "final_score": 0.0,
    }


def test_calculate_recommendation_score_components_does_not_require_score_v2_fields():
    profile = _profile()
    profile["score_v2_fields"] = {}

    result = calculate_recommendation_score_components(profile)

    assert result["final_score"] == 4.93
