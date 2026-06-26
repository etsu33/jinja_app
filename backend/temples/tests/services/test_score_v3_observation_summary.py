

from __future__ import annotations

from temples.services.score_v3_observation_summary import (
    build_score_v3_observation_summary,
    summarize_score_v3_components,
)


def _score_v3_item(**overrides) -> dict:
    components = {
        "state_match_score": 0.5,
        "meaning_match_score": 0.6,
        "shrine_profile_score": 0.7,
        "behavior_score": 0.2,
        "history_score": 0.4,
        "final_score": 2.4,
    }
    components.update(overrides)
    return {
        "mode": "shadow",
        "ranking_applied": False,
        "components": components,
        "observation": {
            "top1_changed": False,
            "delta": 0.0,
            "reason": [],
        },
    }


def test_summarize_score_v3_components_returns_average_components():
    summary = summarize_score_v3_components(
        [
            _score_v3_item(
                state_match_score=0.4,
                meaning_match_score=0.6,
                final_score=2.0,
            ),
            _score_v3_item(
                state_match_score=0.8,
                meaning_match_score=1.0,
                final_score=4.0,
            ),
        ]
    )

    assert summary == {
        "state_match_score": 0.6,
        "meaning_match_score": 0.8,
        "shrine_profile_score": 0.7,
        "behavior_score": 0.2,
        "history_score": 0.4,
        "final_score": 3.0,
    }


def test_summarize_score_v3_components_handles_empty_items_safely():
    assert summarize_score_v3_components([]) == {
        "state_match_score": 0.0,
        "meaning_match_score": 0.0,
        "shrine_profile_score": 0.0,
        "behavior_score": 0.0,
        "history_score": 0.0,
        "final_score": 0.0,
    }


def test_build_score_v3_observation_summary_returns_stable_schema():
    summary = build_score_v3_observation_summary(
        current_top_id=1,
        score_v3_top_id=2,
        current_top_score=3.0,
        score_v3_top_score=4.25,
        score_v3_items=[_score_v3_item()],
    )

    assert set(summary.keys()) == {
        "top1_changed",
        "delta",
        "component_summary",
        "reason",
    }
    assert summary["top1_changed"] is True
    assert summary["delta"] == 1.25
    assert summary["component_summary"] == {
        "state_match_score": 0.5,
        "meaning_match_score": 0.6,
        "shrine_profile_score": 0.7,
        "behavior_score": 0.2,
        "history_score": 0.4,
        "final_score": 2.4,
    }
    assert summary["reason"] == [
        "top1_changed",
        "score_delta",
        "component_summary_available",
    ]


def test_build_score_v3_observation_summary_keeps_top1_unchanged_when_ids_match():
    summary = build_score_v3_observation_summary(
        current_top_id=1,
        score_v3_top_id="1",
        current_top_score=4.0,
        score_v3_top_score=4.0,
        score_v3_items=[_score_v3_item()],
    )

    assert summary["top1_changed"] is False
    assert summary["delta"] == 0.0
    assert summary["reason"] == ["component_summary_available"]


def test_build_score_v3_observation_summary_handles_missing_inputs_safely():
    summary = build_score_v3_observation_summary()

    assert summary == {
        "top1_changed": False,
        "delta": 0.0,
        "component_summary": {
            "state_match_score": 0.0,
            "meaning_match_score": 0.0,
            "shrine_profile_score": 0.0,
            "behavior_score": 0.0,
            "history_score": 0.0,
            "final_score": 0.0,
        },
        "reason": [],
    }


def test_build_score_v3_observation_summary_does_not_mutate_score_items():
    items = [_score_v3_item()]
    before = [item.copy() for item in items]

    build_score_v3_observation_summary(score_v3_items=items)

    assert items == before
