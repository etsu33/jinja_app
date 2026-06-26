

from __future__ import annotations

from temples.services.score_v3_observer import (
    build_score_v3_shadow_observation_payload,
)


def _observation(
    *,
    top1_changed: bool = False,
    delta: float = 0.0,
    final_score: float = 2.0,
) -> dict:
    return {
        "top1_changed": top1_changed,
        "delta": delta,
        "component_summary": {
            "state_match_score": 0.4,
            "meaning_match_score": 0.5,
            "shrine_profile_score": 0.6,
            "behavior_score": 0.1,
            "history_score": 0.2,
            "final_score": final_score,
        },
        "reason": [],
    }


def test_build_score_v3_shadow_observation_payload_returns_stable_schema():
    payload = build_score_v3_shadow_observation_payload(
        [
            _observation(top1_changed=False, delta=0.1, final_score=2.0),
            _observation(top1_changed=True, delta=-0.2, final_score=3.0),
        ]
    )

    assert set(payload.keys()) == {
        "session_count",
        "top1_changed_count",
        "top1_changed_rate",
        "avg_delta",
        "max_abs_delta",
        "activation_candidate",
        "component_summary",
    }


def test_build_score_v3_shadow_observation_payload_calculates_rates_and_delta():
    payload = build_score_v3_shadow_observation_payload(
        [
            _observation(top1_changed=False, delta=0.1),
            _observation(top1_changed=True, delta=-0.2),
            _observation(top1_changed=False, delta=0.4),
            _observation(top1_changed=True, delta=-0.3),
        ]
    )

    assert payload["session_count"] == 4
    assert payload["top1_changed_count"] == 2
    assert payload["top1_changed_rate"] == 0.5
    assert payload["avg_delta"] == 0.0
    assert payload["max_abs_delta"] == 0.4


def test_build_score_v3_shadow_observation_payload_calculates_component_summary_average():
    payload = build_score_v3_shadow_observation_payload(
        [
            _observation(delta=0.1, final_score=2.0),
            _observation(delta=0.2, final_score=4.0),
        ]
    )

    assert payload["component_summary"] == {
        "state_match_score": 0.4,
        "meaning_match_score": 0.5,
        "shrine_profile_score": 0.6,
        "behavior_score": 0.1,
        "history_score": 0.2,
        "final_score": 3.0,
    }


def test_build_score_v3_shadow_observation_payload_marks_activation_candidate_when_stable():
    payload = build_score_v3_shadow_observation_payload(
        [
            _observation(top1_changed=False, delta=0.1),
            _observation(top1_changed=False, delta=0.2),
            _observation(top1_changed=True, delta=0.0),
        ]
    )

    assert payload["top1_changed_rate"] == 0.3333
    assert payload["avg_delta"] == 0.1
    assert payload["max_abs_delta"] == 0.2
    assert payload["activation_candidate"] is True


def test_build_score_v3_shadow_observation_payload_rejects_activation_candidate_when_unstable():
    payload = build_score_v3_shadow_observation_payload(
        [
            _observation(top1_changed=True, delta=0.9),
            _observation(top1_changed=True, delta=-0.8),
            _observation(top1_changed=False, delta=0.2),
        ]
    )

    assert payload["top1_changed_rate"] == 0.6667
    assert payload["max_abs_delta"] == 0.9
    assert payload["activation_candidate"] is False


def test_build_score_v3_shadow_observation_payload_handles_empty_input_safely():
    payload = build_score_v3_shadow_observation_payload([])

    assert payload == {
        "session_count": 0,
        "top1_changed_count": 0,
        "top1_changed_rate": 0.0,
        "avg_delta": 0.0,
        "max_abs_delta": 0.0,
        "activation_candidate": False,
        "component_summary": {
            "state_match_score": 0.0,
            "meaning_match_score": 0.0,
            "shrine_profile_score": 0.0,
            "behavior_score": 0.0,
            "history_score": 0.0,
            "final_score": 0.0,
        },
    }


def test_build_score_v3_shadow_observation_payload_ignores_non_dict_items():
    payload = build_score_v3_shadow_observation_payload(
        [
            _observation(top1_changed=True, delta=0.2),
            None,
            "not-dict",
        ]
    )

    assert payload["session_count"] == 1
    assert payload["top1_changed_count"] == 1
    assert payload["top1_changed_rate"] == 1.0


def test_build_score_v3_shadow_observation_payload_does_not_mutate_input():
    observations = [_observation(top1_changed=True, delta=0.2)]
    before = [item.copy() for item in observations]

    build_score_v3_shadow_observation_payload(observations)

    assert observations == before
