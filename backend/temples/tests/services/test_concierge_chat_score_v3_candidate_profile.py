# backend/temples/tests/services/test_concierge_chat_score_v3_candidate_profile.py

from __future__ import annotations

from temples.services.concierge_chat import _build_score_v3_candidate_profile


def test_build_score_v3_candidate_profile_maps_deity_history_and_place_context():
    rec = {
        "shrine_id": 1,
        "name": "武蔵御嶽神社",
        "history_theme": "勝負",
        "goriyaku": "勝負運",
        "sajin": "櫛真智命",
        "description": "古くから武運長久の祈願で知られる。",
        "address": "東京都青梅市御岳山",
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity"] == "櫛真智命"
    assert profile["shrine_history"] == "古くから武運長久の祈願で知られる。"
    assert profile["place_context"] == "東京都青梅市御岳山"


def test_build_score_v3_candidate_profile_handles_missing_shrine_fields():
    rec = {"shrine_id": 1, "name": "候補神社"}

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity"] is None
    assert profile["shrine_history"] is None
    assert profile["place_context"] is None
