"""TRADITION_ALWAYS_HEDGED契約の回帰テスト。

docs/core/recommendation-reason-contract.md「Tradition Output Contract」に従い、
history_type="tradition"のShrineHistory Factは、confidence（Source信頼度）に
関わらずassertive表現（断定的な言い回し）を出してはならない。

confidenceとhistory_typeは責務が別軸であることを確認するため、各テストは
知識としての確度（confidence）を固定し、記述種別（history_type）だけを
変えて出力文体（weakened/assertive）が変わることを確認する。

deityの存在は_build_fact_text()の優先順位でshrine_history文を上書きするため、
ここでは全テストでknowledge_deitiesを空にし、shrine_history表現だけを
単独で観測できるようにする。
"""

from __future__ import annotations

from temples.services.concierge_chat import _build_score_v3_candidate_profile
from temples.services.recommendation_reason_v4 import build_recommendation_reason_v4


def _rec_with_single_history(*, history_type: str, confidence: str) -> dict:
    return {
        "shrine_id": 900,
        "name": "検証神社",
        "knowledge_deities": [],
        "knowledge_histories": [
            {
                "history_type": history_type,
                "title": "検証用由緒",
                "content": "検証神社は古くからこの地にあったという由緒を持つ。",
                "period_text": "不詳",
                "sort_order": 0,
                "confidence": confidence,
            }
        ],
    }


def test_tradition_high_confidence_is_hedged_not_assertive():
    """tradition + high: confidenceが高くても断定表現を出してはならない(新契約)。"""
    rec = _rec_with_single_history(history_type="tradition", confidence="high")

    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert profile["shrine_history_type"] == "tradition"
    assert profile["shrine_history_confidence"] == "high"
    assert "伝えられています" in result["reason_text"]
    assert "という背景があります" not in result["reason_text"]


def test_tradition_medium_confidence_is_hedged():
    """tradition + medium: 既存のconfidence由来hedgeと同じ表現のまま(回帰なし)。"""
    rec = _rec_with_single_history(history_type="tradition", confidence="medium")

    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert "伝えられています" in result["reason_text"]
    assert "という背景があります" not in result["reason_text"]


def test_historical_event_high_confidence_stays_assertive():
    """tradition以外のhistory_typeはfloorの対象外(高confidenceなら現行通り断定表現)。"""
    rec = _rec_with_single_history(history_type="historical_event", confidence="high")

    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert "という背景があります" in result["reason_text"]
    assert "伝えられています" not in result["reason_text"]


def test_founding_high_confidence_keeps_current_contract():
    """founding(祭神と対の由緒として既存Pilotで使われてきた種別)はfloor対象外のまま。"""
    rec = _rec_with_single_history(history_type="founding", confidence="high")

    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert "という背景があります" in result["reason_text"]
    assert "伝えられています" not in result["reason_text"]


def test_tradition_low_confidence_stays_suppressed_not_upgraded_to_hedged():
    """tradition + low: floorはassertiveをweakenedへ引き下げるだけで、
    suppressed(低confidenceによる非表示)をweakenedへ引き上げはしない。
    """
    rec = _rec_with_single_history(history_type="tradition", confidence="low")

    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert profile["shrine_history_type"] == "tradition"
    assert result["fact"]["shrine_history"] is None
    assert "検証神社は古くからこの地にあった" not in result["reason_text"]


def test_legacy_fallback_history_has_no_history_type_and_is_unaffected():
    """Legacy(description)フォールバック時はKnowledge history_type概念が存在しないため
    shrine_history_typeはNoneになり、floorは一切作用しない(PR-B契約と同じ扱い)。
    """
    rec = {
        "shrine_id": 901,
        "name": "レガシー神社",
        "description": "レガシーの由緒文",
    }

    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert profile["shrine_history_type"] is None
    assert profile["shrine_history_confidence"] is None
    assert "レガシーの由緒文という背景があります" in result["reason_text"]
    assert "伝えられています" not in result["reason_text"]
