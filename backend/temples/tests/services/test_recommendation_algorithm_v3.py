

from __future__ import annotations

from temples.services.recommendation_algorithm_v3 import (
    build_score_v3_debug,
    run_recommendation_algorithm_v3_shadow,
)


def _recommendation_input_profile() -> dict:
    return {
        "interpretation_profile": {
            "state_profile": {
                "primary_state": "uncertain",
                "confidence": 0.8,
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


def test_build_score_v3_debug_returns_stable_schema():
    debug = build_score_v3_debug(_recommendation_input_profile())

    assert set(debug.keys()) == {
        "mode",
        "ranking_applied",
        "components",
        "observation",
    }
    assert debug["mode"] == "shadow"
    assert debug["ranking_applied"] is False
    assert set(debug["components"].keys()) == {
        "state_match_score",
        "meaning_match_score",
        "shrine_profile_score",
        "behavior_score",
        "history_score",
        "final_score",
    }
    assert debug["observation"] == {
        "top1_changed": False,
        "delta": 0.0,
        "reason": [],
    }


def test_build_score_v3_debug_uses_score_components():
    debug = build_score_v3_debug(_recommendation_input_profile())

    assert debug["components"] == {
        "state_match_score": 0.93,
        "meaning_match_score": 1.0,
        "shrine_profile_score": 1.0,
        "behavior_score": 1.0,
        "history_score": 1.0,
        "final_score": 4.93,
    }


def test_run_recommendation_algorithm_v3_shadow_returns_shadow_result():
    result = run_recommendation_algorithm_v3_shadow(_recommendation_input_profile())

    assert set(result.keys()) == {
        "mode",
        "shadow_mode",
        "ranking_applied",
        "score_v3",
    }
    assert result["mode"] == "shadow"
    assert result["shadow_mode"] is True
    assert result["ranking_applied"] is False
    assert result["score_v3"]["mode"] == "shadow"
    assert result["score_v3"]["ranking_applied"] is False


def test_run_recommendation_algorithm_v3_shadow_handles_missing_profile_safely():
    result = run_recommendation_algorithm_v3_shadow(None)

    assert result == {
        "mode": "shadow",
        "shadow_mode": True,
        "ranking_applied": False,
        "score_v3": {
            "mode": "shadow",
            "ranking_applied": False,
            "components": {
                "state_match_score": 0.0,
                "meaning_match_score": 0.0,
                "shrine_profile_score": 0.0,
                "behavior_score": 0.0,
                "history_score": 0.0,
                "final_score": 0.0,
            },
            "observation": {
                "top1_changed": False,
                "delta": 0.0,
                "reason": [],
            },
        },
    }


def test_recommendation_algorithm_v3_shadow_does_not_mutate_input_profile():
    profile = _recommendation_input_profile()
    before = profile.copy()

    run_recommendation_algorithm_v3_shadow(profile)

    assert profile == before
