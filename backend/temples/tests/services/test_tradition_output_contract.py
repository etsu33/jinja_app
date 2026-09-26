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


# --- 二重hedge防止（docs/audit/recommendation-reason-tradition-double-hedge-track.md） ---
#
# weakened分岐は本文へ「と伝えられています」を付加する。本文が既に伝承・伝聞として
# hedge済みの語尾で終わる場合、同義hedgeを重ねない。表現強度（weakened）の判定は
# 引き続きhistory_type + _apply_tradition_hedge_floor()だけが決める。

import json  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402

from temples.services.recommendation_reason_v4 import _build_fact  # noqa: E402

_APPENDED_HEDGE = "と伝えられています"
_ASSERTIVE_HISTORY = "という背景があります"


def _rec_with_history_content(
    *, content: str, history_type: str, confidence: str, deities=None
) -> dict:
    return {
        "shrine_id": 902,
        "name": "検証神社",
        "knowledge_deities": deities or [],
        "knowledge_histories": [
            {
                "history_type": history_type,
                "title": "検証用由緒",
                "content": content,
                "period_text": "不詳",
                "sort_order": 0,
                "confidence": confidence,
            }
        ],
    }


def _reason(rec: dict) -> tuple[dict, dict, dict]:
    profile = _build_score_v3_candidate_profile(rec)
    _fact, strength = _build_fact(profile, {})
    return profile, strength, build_recommendation_reason_v4(candidate_profile=profile)


@pytest.mark.parametrize(
    "content, hedged_tail",
    [
        ("この地に祀られたと伝えられている。", "と伝えられている"),  # Case A
        ("この地に祀られたとされています。", "とされています"),  # Case B
        ("この地に祀られたという伝承がある。", "という伝承がある"),  # Case C
        ("この地に祀られたと伝えられています。", "と伝えられています"),
        ("この地に祀られたとされている。", "とされている"),
        ("この地に祀られたのが創祀とされる。", "とされる"),
        ("この地に祀られたと伝わる。", "と伝わる"),
        ("白鳥にまつわる創始の由緒が伝えられている。", "が伝えられている"),
        ("この地に祀られたと伝わる、", "と伝わる"),  # 末尾読点
        ("この地に祀られたと伝わる", "と伝わる"),  # 句点なし
    ],
)
def test_already_hedged_tradition_is_not_double_hedged(content, hedged_tail):
    """Case A/B/C: hedge済み本文へ同義hedgeを重ねない。hedge自体は本文に残る。"""
    rec = _rec_with_history_content(content=content, history_type="tradition", confidence="high")

    profile, strength, result = _reason(rec)
    text = result["reason_text"]

    assert profile["shrine_history_type"] == "tradition"
    assert strength["shrine_history"] == "weakened"
    assert f"{hedged_tail}{_APPENDED_HEDGE}" not in text
    # hedgeは本文由来の1回だけ（テンプレートのhedgeを追加しない）。
    assert text.count(_APPENDED_HEDGE) == (1 if hedged_tail == _APPENDED_HEDGE else 0)
    assert f"検証神社には、{content.rstrip('。、')}。" in text
    assert _ASSERTIVE_HISTORY not in text


def test_unhedged_tradition_high_confidence_gets_runtime_hedge():
    """Case D: 本文が断定文でも、tradition + highはruntimeがhedgeを付与する。"""
    rec = _rec_with_history_content(
        content="この地に祀られた。", history_type="tradition", confidence="high"
    )

    _profile, strength, result = _reason(rec)

    assert strength["shrine_history"] == "weakened"
    assert "検証神社には、この地に祀られたと伝えられています。" in result["reason_text"]
    assert _ASSERTIVE_HISTORY not in result["reason_text"]


@pytest.mark.parametrize(
    "content, expected",
    [
        ("この地に祀られたと伝えられている。", "検証神社には、この地に祀られたと伝えられている。"),
        ("この地に祀られた。", "検証神社には、この地に祀られたと伝えられています。"),
    ],
)
def test_tradition_medium_confidence_stays_hedged_without_duplicate(content, expected):
    """Case E: tradition + medium。hedgeを維持し、二重hedgeにしない。"""
    rec = _rec_with_history_content(content=content, history_type="tradition", confidence="medium")

    _profile, strength, result = _reason(rec)

    assert strength["shrine_history"] == "weakened"
    assert expected in result["reason_text"]
    assert f"伝えられている{_APPENDED_HEDGE}" not in result["reason_text"]
    assert _ASSERTIVE_HISTORY not in result["reason_text"]


def test_hedged_tradition_low_confidence_stays_suppressed():
    """Case F: tradition + lowはsuppressedのまま。hedge済み本文でもweakenedへ昇格しない。"""
    content = "この地に祀られたと伝えられている。"
    rec = _rec_with_history_content(content=content, history_type="tradition", confidence="low")

    _profile, strength, result = _reason(rec)

    assert strength["shrine_history"] == "suppressed"
    assert result["fact"]["shrine_history"] is None
    assert "この地に祀られた" not in result["reason_text"]


@pytest.mark.parametrize("history_type", ["historical_event", "founding"])
def test_non_tradition_high_confidence_behavior_is_unchanged(history_type):
    """Case G/H: historical_event / founding + highは現行assertiveのまま。

    本文末尾がhedge語尾でも、assertive分岐は変更していない（本文をそのまま使う）。
    """
    for content in ("この地に祀られた。", "この地に祀られたとされている。"):
        rec = _rec_with_history_content(
            content=content, history_type=history_type, confidence="high"
        )

        _profile, strength, result = _reason(rec)

        assert strength["shrine_history"] == "assertive"
        assert (
            f"検証神社には、{content.rstrip('。')}{_ASSERTIVE_HISTORY}。" in result["reason_text"]
        )
        assert _APPENDED_HEDGE not in result["reason_text"]


def test_deity_first_priority_is_unchanged_with_tradition_history():
    """Case I: deityとtradition historyが併存する場合、deity文が優先される。"""
    rec = _rec_with_history_content(
        content="この地に祀られたと伝えられている。",
        history_type="tradition",
        confidence="high",
        deities=[{"display_name": "検証大神", "sort_order": 0, "confidence": "high"}],
    )

    _profile, strength, result = _reason(rec)
    text = result["reason_text"]

    assert text.startswith("検証神社では、検証大神が祀られています。")
    assert "この地に祀られた" not in text
    assert strength["shrine_history"] == "weakened"
    assert result["fact"]["shrine_history"] == "この地に祀られたと伝えられている。"


_OKADA_CONTENT = (
    "『古事記』等に結びつく伝承として、神武天皇と五瀬命が東征の途中に"
    "岡田宮の地に滞在したと伝えられている。"
)
_W0_DB03_SEED = (
    Path(__file__).resolve().parents[2] / "data" / "knowledge_seeds" / "wave0_batch_03_seed.json"
)


def test_w0_db03_okadagu_real_wording_has_no_double_hedge():
    """Case J: W0-DB03 岡田宮の実データ文言。二重hedgeなし・hedge保持・Seed不変。"""
    seed = json.loads(_W0_DB03_SEED.read_text(encoding="utf-8"))
    okada = next(s for s in seed["shrines"] if s["shrine_ref"]["name_jp"] == "岡田宮")
    stored = okada["histories"][0]
    # Stored Factは変更しない（presentation側だけで対処する）。
    assert stored["content"] == _OKADA_CONTENT
    assert stored["history_type"] == "tradition"
    assert stored["confidence"] == "high"

    rec = _rec_with_history_content(
        content=_OKADA_CONTENT, history_type="tradition", confidence="high"
    )
    rec["name"] = "岡田宮"

    _profile, strength, result = _reason(rec)
    text = result["reason_text"]

    assert strength["shrine_history"] == "weakened"
    assert "伝えられていると伝えられています" not in text
    assert f"岡田宮には、{_OKADA_CONTENT}" in text
    assert _ASSERTIVE_HISTORY not in text
