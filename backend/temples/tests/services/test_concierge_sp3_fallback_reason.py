"""SP3: 内部の fallback sentinel を Need 用の事実の文にしない。

_resolve_primary_reason() は一致する evidence がないとき type / label とも "fallback" を返す。
これは制御 sentinel であり Need label ではない。以前は build_recommendation_reason() が
_build_need_reason_text("fallback") へ流し、_build_need_lead("fallback") が "ご利益" に落ちて
「ご利益のご利益で知られる…」という根拠のない御利益の断定を作っていた。

本 file は文の literal ではなく、次の安全性を固定する:
- sentinel は Need label / Need evidence として扱われない
- 根拠のない神社固有の御利益の断定が出ない
- 実際の Need / Channel A の理由文は変わらない
"""

from __future__ import annotations

import pytest

from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_ranking import (
    FALLBACK_REASON_SENTINEL,
    build_recommendation_reason,
)

UNSUPPORTED_BENEFIT_CLAIMS = ("ご利益で知られる", "のご利益がある", "ご利益のご利益")
REASON_KWARGS = dict(public_mode="need", birthdate=None, need_tags=["money"])


def _rec(**overrides) -> dict:
    rec = {
        "name": "試験神社",
        "goriyaku": "",
        "goriyaku_tag_ids": [],
        "_prefilter_debug": {},
        "breakdown": {"matched_need_tags": []},
        "_primary_reason_label": "",
        "_primary_reason_source": "",
    }
    rec.update(overrides)
    return rec


def _candidate(name: str, **overrides) -> dict:
    row = {
        "id": sum(map(ord, name)),
        "shrine_id": sum(map(ord, name)),
        "name": name,
        "address": "東京都試験区1-1-1",
        "lat": 35.0,
        "lng": 139.0,
        "distance_m": 100.0,
        "goriyaku": "",
        "description": "",
        "astro_tags": [],
        "goriyaku_tag_ids": [],
        "popular_score": 0.0,
    }
    row.update(overrides)
    return row


def _assert_no_unsupported_claim(text: str) -> None:
    assert "fallback" not in text
    for claim in UNSUPPORTED_BENEFIT_CLAIMS:
        assert claim not in text


# ---------- A. fallback sentinel ----------


def test_sentinel_value_is_the_resolver_fallback_type():
    assert FALLBACK_REASON_SENTINEL == "fallback"


@pytest.mark.parametrize(
    "overrides",
    [
        {"_primary_reason_label": "fallback"},
        {"_primary_reason_source": "fallback", "_primary_reason_label": "fallback"},
        {"_primary_reason_source": "fallback", "_primary_reason_label": "近い候補"},
    ],
)
def test_a_fallback_sentinel_is_not_formatted_as_a_need_label(overrides):
    text = build_recommendation_reason(_rec(**overrides), **REASON_KWARGS)
    no_label = build_recommendation_reason(_rec(), **REASON_KWARGS)
    # sentinel は「label が無い」と同じ扱いになる（Need 用の文へ入らない）。
    assert text == no_label
    _assert_no_unsupported_claim(text)
    assert "試験神社" in text


def test_a_sentinel_does_not_pick_up_the_goriyaku_free_text_as_evidence():
    text = build_recommendation_reason(
        _rec(_primary_reason_label="fallback", goriyaku="商売繁盛・金運", goriyaku_tag_ids=[4]),
        **REASON_KWARGS,
    )
    _assert_no_unsupported_claim(text)
    assert "商売繁盛" not in text and "金運" not in text


# ---------- B. no-evidence candidate（end-to-end）----------


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["金運を上げたい", "", "近くの神社"])
def test_b_no_evidence_candidate_gets_a_safe_generic_fallback(query, settings):
    settings.CONCIERGE_USE_LLM = False
    recs = build_chat_recommendations(
        query=query,
        language="ja",
        candidates=[_candidate("根拠なし神社")],
        bias={"lat": 35.0, "lng": 139.0},
        public_mode="need",
        flow="A",
        llm_enabled=False,
    )
    rec = recs["recommendations"][0]
    assert rec["_primary_reason_label"] == FALLBACK_REASON_SENTINEL
    assert not rec["breakdown"]["matched_need_tags"]
    _assert_no_unsupported_claim(rec["reason"])
    assert "根拠なし神社" in rec["reason"]


# ---------- C. real Need / Channel A reason is unchanged ----------


@pytest.mark.django_db
def test_c_channel_a_goriyaku_tag_reason_is_unchanged(settings):
    settings.CONCIERGE_USE_LLM = False
    recs = build_chat_recommendations(
        query="金運を上げたい",
        language="ja",
        candidates=[_candidate("金運神社", goriyaku_tag_ids=[4])],
        bias={"lat": 35.0, "lng": 139.0},
        public_mode="need",
        flow="A",
        llm_enabled=False,
    )
    rec = recs["recommendations"][0]
    assert rec["_primary_reason_label"] == "money"
    # 実際の Need / Channel A の evidence があるときは、従来どおり Need 用の文を作る。
    assert (
        rec["reason"]
        == "金運のご利益で知られる金運神社は、金運向上を願う参拝先として適しています。"
    )


@pytest.mark.parametrize(
    "rec_overrides,expected",
    [
        (
            {"_primary_reason_label": "study", "_primary_reason_source": "need_tag"},
            "学業成就のご利益で知られる試験神社は、学業や合格を願う参拝先として適しています。",
        ),
        (
            {"breakdown": {"matched_need_tags": ["protection"]}},
            "厄除けのご利益で知られる試験神社は、厄除けや守りを願う参拝先として適しています。",
        ),
    ],
)
def test_c_real_need_labels_keep_the_need_reason(rec_overrides, expected):
    assert build_recommendation_reason(_rec(**rec_overrides), **REASON_KWARGS) == expected
