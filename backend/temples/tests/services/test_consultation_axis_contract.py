from __future__ import annotations

import pytest

from temples.domain.consultation_axis import (
    CONSULTATION_AXES,
    normalize_consultation_axis,
    resolve_consultation_axis,
)
from temples.llm.intent_schema import normalize_intent
from temples.llm.schemas import complete_recommendations, normalize_recs
from temples.services.concierge_chat import build_chat_recommendations


def test_consultation_axis_taxonomy_has_seven_axes_plus_other():
    assert CONSULTATION_AXES == [
        "money_growth",
        "career_change",
        "independence",
        "rest_healing",
        "restart_mindset",
        "nature_reset",
        "study_success",
        "other",
    ]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("money_growth", "money_growth"),
        ("money", "money_growth"),
        ("career", "career_change"),
        ("work", "career_change"),
        ("freelance", "independence"),
        ("rest", "rest_healing"),
        ("mental", "restart_mindset"),
        ("nature", "nature_reset"),
        ("study", "study_success"),
        ("unknown", "other"),
    ],
)
def test_normalize_consultation_axis(raw, expected):
    assert normalize_consultation_axis(raw) == expected


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("年収を上げたい", "money_growth"),
        ("売上と収益を伸ばしたい", "money_growth"),
        ("転職と仕事の方向性を相談したい", "career_change"),
        ("今の仕事を辞めたい", "career_change"),
        ("独立して自由に働きたい", "independence"),
        ("会社を作りたい", "independence"),
        ("疲れていて静かに回復したい", "rest_healing"),
        ("最近落ち込んでいて、立て直したい", "rest_healing"),
        ("気分が沈んでいるので静かに整えたい", "rest_healing"),
        ("気持ちを切り替えて前向きになれる参拝がしたい", "restart_mindset"),
        ("自然を感じながら参拝したい", "nature_reset"),
        ("資格試験に合格したい", "study_success"),
    ],
)
def test_resolve_consultation_axis_from_query(query, expected):
    result = resolve_consultation_axis(query=query, need_tags=[])

    assert result.axis == expected
    assert result.source == "query"


def test_resolve_consultation_axis_prefers_valid_llm_axis():
    result = resolve_consultation_axis(
        query="仕事の相談",
        need_tags=["career"],
        llm_axis="money_growth",
    )

    assert result.axis == "money_growth"
    assert result.source == "llm"


def test_intent_schema_accepts_and_normalizes_consultation_axis():
    payload = normalize_intent(
        {
            "goriyaku": ["仕事運"],
            "tone": "soft",
            "atmosphere": [],
            "avoid": [],
            "summary": "仕事の相談",
            "consultation_axis": "work",
        }
    )

    assert payload["consultation_axis"] == "career_change"


def test_llm_recommendation_schema_carries_consultation_axis():
    normalized = normalize_recs(
        {
            "consultation_axis": "restart_mindset",
            "recommendations": [{"name": "A", "reason": "ok"}],
        }
    )
    completed = complete_recommendations(normalized)

    assert normalized["recommendations"][0]["consultation_axis"] == "restart_mindset"
    assert completed["recommendations"][0]["consultation_axis"] == "restart_mindset"


def test_build_chat_recommendations_attaches_consultation_axis_to_payload(settings):
    settings.CONCIERGE_USE_LLM = False
    recs = build_chat_recommendations(
        query="気持ちを切り替えて前向きになれる参拝がしたい",
        language="ja",
        candidates=[
            {
                "name": "再出発の神社",
                "astro_tags": ["mental"],
                "popular_score": 1.0,
            }
        ],
    )

    assert recs["consultation_axis"] == "restart_mindset"
    assert recs["_need"]["consultation_axis"] == "restart_mindset"
    assert recs["_signals"]["consultation_axis"] == "restart_mindset"
    assert recs["_signals"]["result_state"]["consultation_axis"] == "restart_mindset"
    assert recs["recommendations"][0]["consultation_axis"] == "restart_mindset"
