

from __future__ import annotations

import pytest

from temples.models import Shrine, ShrineReflection
from temples.services.concierge_chat import build_chat_recommendations


@pytest.mark.django_db
def test_reflection_hint_flows_into_recommendation_observation_contract(
    monkeypatch,
    user,
):
    shrine = Shrine.objects.create(
        name_jp="振り返り観測神社",
        address="東京都千代田区1-1-1",
    )
    ShrineReflection.objects.create(
        user=user,
        shrine=shrine,
        history_theme="静寂",
        prompt="参拝して、今どんな変化がありましたか？",
        answer="少し落ち着いたので、次は動きたい。",
        mood_before="不安",
        mood_after="落ち着いた",
    )

    def fake_resolve_llm_route(*, query, valid_candidates, need_tags, llm_enabled):
        return {
            "recs": {
                "recommendations": [
                    {
                        "name": shrine.name_jp,
                        "shrine_id": shrine.id,
                        "visit_style_tags": ["quiet", "nature"],
                        "goriyaku": "心願成就",
                        "goriyaku_tags": ["心願成就"],
                        "goriyaku_tag_ids": [1],
                        "history_theme": "静寂",
                        "distance_m": 1200,
                    }
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
        query="静かに気持ちを整えて、次に進みたい",
        language="ja",
        candidates=[
            {
                "name": shrine.name_jp,
                "shrine_id": shrine.id,
                "visit_style_tags": ["quiet", "nature"],
                "goriyaku": "心願成就",
                "goriyaku_tags": ["心願成就"],
                "goriyaku_tag_ids": [1],
                "history_theme": "静寂",
                "distance_m": 1200,
            }
        ],
        bias=None,
        birthdate=None,
        goriyaku_tag_ids=None,
        extra_condition="静かに過ごせる場所がいい",
        public_mode="need",
        flow="B",
        user=user,
    )

    top = result["recommendations"][0]
    signals = top["score_v2"]["signals"]
    reflection_hint = signals["reflection_hint"]

    assert reflection_hint["state_change_direction"] == "improved"
    assert reflection_hint["next_need_hint"] == ["courage", "mental"]
    assert reflection_hint["next_history_theme_hint"] == ["勝負", "再出発"]
    assert reflection_hint["source_shrine_id"] == shrine.id
    assert reflection_hint["source_shrine_name"] == shrine.name_jp
    assert reflection_hint["source_history_theme"] == "静寂"

    behavior_profile = signals["behavior_profile"]
    assert behavior_profile["reflection_hint"] == reflection_hint
    assert behavior_profile["action_state"] == "reflected"
    assert behavior_profile["behavior_breakdown"]["reflection_signal"] > 0.0

    ranking_breakdown = result["_debug"]["ranking_breakdown_observation"]
    assert ranking_breakdown["top10"]
    top_observation = ranking_breakdown["top10"][0]
    assert top_observation["reflection_hint_state_change_direction"] == "improved"
    assert top_observation["reflection_hint_next_need_hint"] == ["courage", "mental"]
    assert top_observation["reflection_hint_next_history_theme_hint"] == ["勝負", "再出発"]
    assert top_observation["reflection_hint_source_history_theme"] == "静寂"
    assert top_observation["behavior_profile"]["reflection_hint"] == reflection_hint
