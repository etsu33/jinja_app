

from __future__ import annotations

from temples.services.concierge_chat import build_chat_recommendations


def test_build_chat_recommendations_exposes_profile_observation_contracts(monkeypatch):
    def fake_resolve_llm_route(*, query, valid_candidates, need_tags, llm_enabled, consultation_axis=None):
        return {
            "recs": {
                "recommendations": [
                    {
                        "name": "根津神社",
                        "shrine_id": 101,
                        "visit_style_tags": ["nature", "quiet"],
                        "goriyaku": "縁結び・厄除け",
                        "goriyaku_tags": ["縁結び", "厄除け"],
                        "goriyaku_tag_ids": [1, 2],
                        "history_theme": "静寂",
                        "distance_m": 1200,
                    },
                    {
                        "name": "小網神社",
                        "shrine_id": 102,
                        "visit_style_tags": ["business", "reset"],
                        "goriyaku": "強運厄除け・金運",
                        "goriyaku_tags": ["金運", "厄除け"],
                        "goriyaku_tag_ids": [3, 2],
                        "history_theme": "勝負",
                        "distance_m": 800,
                    },
                ],
                "_seed": True,
            },
            "requested_llm_enabled": False,
            "effective_llm_enabled": False,
            "llm_used": False,
            "llm_error": None,
        }

    monkeypatch.setattr(
        "temples.services.concierge_chat.resolve_llm_route",
        fake_resolve_llm_route,
    )
    monkeypatch.setattr(
        "temples.services.concierge_chat._backfill_location_from_name",
        lambda recs, *, bias, language: None,
    )

    result = build_chat_recommendations(
        query="自然を感じながら静かに参拝したい",
        language="ja",
        candidates=[
            {
                "name": "根津神社",
                "shrine_id": 101,
                "visit_style_tags": ["nature", "quiet"],
                "goriyaku": "縁結び・厄除け",
                "goriyaku_tags": ["縁結び", "厄除け"],
                "goriyaku_tag_ids": [1, 2],
                "history_theme": "静寂",
                "distance_m": 1200,
            },
            {
                "name": "小網神社",
                "shrine_id": 102,
                "visit_style_tags": ["business", "reset"],
                "goriyaku": "強運厄除け・金運",
                "goriyaku_tags": ["金運", "厄除け"],
                "goriyaku_tag_ids": [3, 2],
                "history_theme": "勝負",
                "distance_m": 800,
            },
        ],
        bias=None,
        birthdate=None,
        goriyaku_tag_ids=None,
        extra_condition="自然があり、静かに過ごせる場所がいい",
        public_mode="need",
        flow="B",
        user=None,
    )

    debug = result["_debug"]
    user_state_profile = debug["user_state_profile"]
    assert user_state_profile["version"] == 1
    assert user_state_profile["raw_query"] == "自然を感じながら静かに参拝したい"
    assert isinstance(user_state_profile["need_tags"], list)
    assert isinstance(user_state_profile["need_hits"], dict)
    assert isinstance(user_state_profile["selected_goriyaku_tag_ids"], list)

    top = result["recommendations"][0]
    score_v2 = top["score_v2"]
    assert isinstance(score_v2["total"], float)

    signals = score_v2["signals"]
    shrine_meaning_profile = signals["shrine_meaning_profile"]
    context_profile = signals["context_profile"]
    behavior_profile = signals["behavior_profile"]

    assert shrine_meaning_profile["version"] == 1
    assert shrine_meaning_profile["name"] == top["name"]
    assert isinstance(shrine_meaning_profile["goriyaku"], str)
    assert isinstance(shrine_meaning_profile["goriyaku_tags"], list)
    assert isinstance(shrine_meaning_profile["goriyaku_tag_ids"], list)
    assert isinstance(shrine_meaning_profile["history_theme"], str)

    assert context_profile["version"] == 1
    assert isinstance(context_profile["score_distance"], float)
    assert isinstance(context_profile["requested_visit_style_tags"], list)
    assert isinstance(context_profile["visit_style_tags"], list)
    assert isinstance(context_profile["matched_visit_style_tags"], list)
    assert isinstance(context_profile["score_visit_style"], int)
    assert isinstance(context_profile["direction_bonus"], float)

    assert behavior_profile["version"] == 1
    assert behavior_profile["action_state"] == "none"
    assert isinstance(behavior_profile["behavior_breakdown"], dict)
    assert isinstance(behavior_profile["behavior_signal"], float)
    assert isinstance(behavior_profile["behavior_contribution"], float)
    assert isinstance(behavior_profile["capped_behavior_contribution"], float)
    assert isinstance(behavior_profile["behavior_ratio"], float)
    assert isinstance(behavior_profile["visit_signal"], float)
    assert isinstance(behavior_profile["reflection_signal"], float)

    ranking_breakdown = debug["ranking_breakdown_observation"]
    assert ranking_breakdown["top10"]
    top_observation = ranking_breakdown["top10"][0]
    assert isinstance(top_observation["context_profile"], dict)
    assert isinstance(top_observation["shrine_meaning_profile"], dict)
    assert isinstance(top_observation["behavior_profile"], dict)
