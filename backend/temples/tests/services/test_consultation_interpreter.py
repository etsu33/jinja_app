from __future__ import annotations

from temples.services.consultation_interpreter import interpret_consultation


def test_interpret_consultation_returns_stable_schema():
    profile = interpret_consultation(
        "仕事で迷っていて、気持ちを切り替えて前に進みたい。神社に行きたい。"
    )

    assert set(profile.keys()) == {
        "raw_query",
        "state_profile",
        "need_profile",
        "direction_profile",
        "emotion_profile",
        "action_intent",
        "decision_context",
        "constraint_profile",
        "outcome_hint",
    }
    assert profile["raw_query"] == "仕事で迷っていて、気持ちを切り替えて前に進みたい。神社に行きたい。"
    assert isinstance(profile["state_profile"], dict)
    assert isinstance(profile["need_profile"], dict)
    assert isinstance(profile["direction_profile"], dict)
    assert isinstance(profile["emotion_profile"], dict)
    assert isinstance(profile["action_intent"], dict)
    assert isinstance(profile["decision_context"], dict)
    assert isinstance(profile["constraint_profile"], dict)
    assert isinstance(profile["outcome_hint"], dict)


def test_interpret_consultation_extracts_state_need_direction_and_action():
    profile = interpret_consultation(
        "仕事で迷っていて、気持ちを切り替えて前に進みたい。神社に行きたい。"
    )

    assert profile["state_profile"]["primary_state"] == "uncertain"
    assert "career" in profile["need_profile"]["need_tags"]
    assert "courage" in profile["need_profile"]["need_tags"]
    assert profile["direction_profile"] == {
        "direction": "review",
        "themes": ["静寂", "再出発"],
        "source_state": "uncertain",
    }
    assert profile["action_intent"]["intent"] == "visit"
    assert profile["action_intent"]["strength"] == "soft"


def test_interpret_consultation_extracts_v4_fields():
    profile = interpret_consultation(
        "転職するか迷っている。お金が不安で、時間がないけど、前に進むために決めたい。"
    )

    assert profile["decision_context"] == {
        "primary_decision": "career_decision",
        "decision_candidates": ["career_decision", "money_decision", "rest_or_action"],
        "decision_hits": {
            "career_decision": ["転職"],
            "money_decision": ["お金"],
            "rest_or_action": ["前に進"],
        },
    }
    assert profile["constraint_profile"] == {
        "primary_constraint": "time",
        "constraints": ["time", "money"],
        "constraint_hits": {
            "time": ["時間がない"],
            "money": ["お金が不安"],
        },
    }
    assert profile["outcome_hint"] == {
        "primary_outcome": "decide",
        "outcome_candidates": ["decide", "move_forward"],
        "outcome_hits": {
            "decide": ["決めたい"],
            "move_forward": ["前に進"],
        },
    }


def test_interpret_consultation_merges_explicit_need_tags_before_extracted_need_tags():
    profile = interpret_consultation(
        "仕事とお金のことで迷っている",
        need_tags=["mental", "career"],
    )

    assert profile["need_profile"]["need_tags"] == ["mental", "career", "money"]
    assert profile["need_profile"]["primary_need_tag"] == "mental"
    assert profile["need_profile"]["need_hits"] == {
        "career": ["仕事"],
        "money": ["お金"],
    }


def test_interpret_consultation_keeps_selected_goriyaku_tag_ids():
    profile = interpret_consultation(
        "恋愛と人間関係について整理したい",
        selected_goriyaku_tag_ids=[1, 7, 9],
    )

    assert profile["need_profile"]["selected_goriyaku_tag_ids"] == [1, 7, 9]
    assert "love" in profile["need_profile"]["need_tags"]


def test_interpret_consultation_handles_empty_query_safely():
    profile = interpret_consultation(None)

    assert profile == {
        "raw_query": "",
        "state_profile": {
            "primary_state": None,
            "secondary_states": [],
            "state_hits": {},
            "confidence": 0.0,
        },
        "need_profile": {
            "need_tags": [],
            "need_hits": {},
            "primary_need_tag": None,
            "selected_goriyaku_tag_ids": [],
        },
        "direction_profile": {
            "direction": None,
            "themes": [],
            "source_state": None,
        },
        "emotion_profile": {
            "tone": "unknown",
            "intensity": "unknown",
            "signals": [],
        },
        "action_intent": {
            "intent": None,
            "strength": "unknown",
            "candidates": [],
            "intent_hits": {},
        },
        "decision_context": {
            "primary_decision": None,
            "decision_candidates": [],
            "decision_hits": {},
        },
        "constraint_profile": {
            "primary_constraint": None,
            "constraints": [],
            "constraint_hits": {},
        },
        "outcome_hint": {
            "primary_outcome": None,
            "outcome_candidates": [],
            "outcome_hits": {},
        },
    }
