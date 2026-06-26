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
    }
    assert profile["raw_query"] == "仕事で迷っていて、気持ちを切り替えて前に進みたい。神社に行きたい。"
    assert isinstance(profile["state_profile"], dict)
    assert isinstance(profile["need_profile"], dict)
    assert isinstance(profile["direction_profile"], dict)
    assert isinstance(profile["emotion_profile"], dict)
    assert isinstance(profile["action_intent"], dict)


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
    }
