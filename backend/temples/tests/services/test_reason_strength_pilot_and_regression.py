"""Evidence Gate PR-B: Pilot回帰・Legacy fallback回帰・verification_status回帰。

confidenceによるRecommendation Reason表現強度制御(PR-B)が、
- Pilot相当データ(confidence=high)で現行Reason文と完全互換であること
- Legacy(sajin/description)にはconfidence制御を一切適用しないこと
- verification_status(Evidence Gate PR-A)のusable判定にconfidenceが影響しないこと
を固定するための回帰テスト。
"""

from __future__ import annotations

from temples.services.concierge_chat import _build_score_v3_candidate_profile
from temples.services.evidence_gate import decide_fact_usability
from temples.services.recommendation_reason_v4 import build_recommendation_reason_v4

# --- Pilot regression ---


def test_pilot_meiji_jingu_equivalent_reason_text_is_current_compatible():
    rec = {
        "shrine_id": 1,
        "name": "明治神宮",
        "knowledge_deities": [
            {"display_name": "明治天皇", "sort_order": 0, "confidence": "high"},
            {"display_name": "昭憲皇太后", "sort_order": 1, "confidence": "high"},
        ],
        "knowledge_histories": [
            {
                "history_type": "official_origin",
                "title": "明治神宮の創建",
                "content": "明治神宮は、東京都渋谷区代々木に大正9年（1920）に創建された。",
                "period_text": "大正9年（1920）",
                "sort_order": 0,
                "confidence": "high",
            }
        ],
    }

    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert profile["deity"] == "明治天皇、昭憲皇太后"
    assert profile["deity_confidence"] == "high"
    assert profile["shrine_history_confidence"] == "high"
    assert "明治神宮では、明治天皇、昭憲皇太后が祀られています。" in result["reason_text"]
    # weakened/suppressed表現が混入しない(high confidenceでは現行文体のまま)
    assert "とされています" not in result["reason_text"]
    assert "伝えられています" not in result["reason_text"]


def test_pilot_shinagawa_jinja_equivalent_reason_text_is_current_compatible():
    rec = {
        "shrine_id": 50,
        "name": "品川神社",
        "knowledge_deities": [
            {"display_name": "天比理乃咩命", "sort_order": 0, "confidence": "high"},
            {"display_name": "宇賀之売命", "sort_order": 1, "confidence": "high"},
            {"display_name": "素盞嗚尊", "sort_order": 2, "confidence": "high"},
        ],
        "knowledge_histories": [
            {
                "history_type": "founding",
                "title": "文治3年（1187年）の創始",
                "content": (
                    "源頼朝公が安房国の洲崎明神から天比理乃咩命を当地に迎え、"
                    "海上交通安全と祈願成就を祈ったことを創始とする。"
                ),
                "period_text": "文治3年（1187年）",
                "sort_order": 0,
                "confidence": "high",
            },
            {
                "history_type": "historical_event",
                "title": "元応元年（1319年）の宇賀之売命奉祀",
                "content": "二階堂道蘊公が宇賀之売命を祀った。",
                "period_text": "元応元年（1319年）",
                "sort_order": 1,
                "confidence": "high",
            },
        ],
    }

    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert profile["deity"] == "天比理乃咩命、宇賀之売命、素盞嗚尊"
    assert profile["deity_confidence"] == "high"
    # sort_order最小(1187年)のHistoryのみがshrine_historyへ採用される(既存契約通り)
    assert profile["shrine_history_confidence"] == "high"
    assert "二階堂道蘊公" not in profile["shrine_history"]
    assert (
        "品川神社では、天比理乃咩命、宇賀之売命、素盞嗚尊が祀られています。"
        in result["reason_text"]
    )
    assert "とされています" not in result["reason_text"]
    assert "伝えられています" not in result["reason_text"]


# --- Legacy fallback regression ---


def test_legacy_only_shrine_reason_text_unaffected_by_confidence_control():
    """Knowledge未登録(Legacy sajin/descriptionのみ)のShrineは、PR-B前後でReason文が変わらない。"""
    rec = {
        "shrine_id": 99,
        "name": "レガシー神社",
        "sajin": "レガシー祭神",
        "description": "レガシーの由緒文",
    }

    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert profile["deity"] == "レガシー祭神"
    assert profile["deity_confidence"] is None
    assert profile["shrine_history"] == "レガシーの由緒文"
    assert profile["shrine_history_confidence"] is None
    # Legacy由来のdeityは常にassertive表現(現行互換)のまま。weakened/suppressedにならない。
    assert "レガシー神社では、レガシー祭神が祀られています。" in result["reason_text"]
    assert "とされています" not in result["reason_text"]
    assert "レガシー祭神" in result["fact"]["deity"]


def test_legacy_only_shrine_with_empty_knowledge_lists_matches_pure_legacy_shrine():
    """knowledge_deities/knowledge_histories=[]のケースでもLegacy回帰は同一。"""
    rec_pure_legacy = {"shrine_id": 99, "sajin": "レガシー祭神", "description": "レガシーの由緒文"}
    rec_empty_knowledge = {
        "shrine_id": 99,
        "sajin": "レガシー祭神",
        "description": "レガシーの由緒文",
        "knowledge_deities": [],
        "knowledge_histories": [],
    }

    profile_a = _build_score_v3_candidate_profile(rec_pure_legacy)
    profile_b = _build_score_v3_candidate_profile(rec_empty_knowledge)
    result_a = build_recommendation_reason_v4(candidate_profile=profile_a)
    result_b = build_recommendation_reason_v4(candidate_profile=profile_b)

    assert profile_a["deity_confidence"] == profile_b["deity_confidence"] is None
    assert profile_a["shrine_history_confidence"] == profile_b["shrine_history_confidence"] is None
    assert result_a["reason_text"] == result_b["reason_text"]


# --- verification_status regression (Evidence Gate PR-A) ---


def test_disputed_high_confidence_is_still_unusable():
    """confidence=highでもverification_status=disputedならusable=Falseのまま(PR-A不変)。"""
    decision = decide_fact_usability(
        verification_status="disputed",
        confidence="high",
        source_verification_statuses=["source_confirmed"],
    )
    assert decision.usable is False


def test_draft_high_confidence_is_still_unusable():
    decision = decide_fact_usability(
        verification_status="draft",
        confidence="high",
        source_verification_statuses=["source_confirmed"],
    )
    assert decision.usable is False


def test_fact_ready_without_source_is_still_unusable_regardless_of_confidence():
    for confidence in ("high", "medium", "low", ""):
        decision = decide_fact_usability(
            verification_status="source_confirmed",
            confidence=confidence,
            source_verification_statuses=[],
        )
        assert (
            decision.usable is False
        ), f"confidence={confidence!r}でusableがTrueになってはいけない"


def test_fact_ready_with_draft_source_only_is_still_unusable_regardless_of_confidence():
    for confidence in ("high", "medium", "low", ""):
        decision = decide_fact_usability(
            verification_status="source_confirmed",
            confidence=confidence,
            source_verification_statuses=["draft"],
        )
        assert (
            decision.usable is False
        ), f"confidence={confidence!r}でusableがTrueになってはいけない"


def test_fact_ready_with_ready_source_is_usable_regardless_of_confidence():
    """usable=Trueになるかどうかはconfidenceに左右されない(low/emptyでもusableはTrue)。"""
    for confidence in ("high", "medium", "low", ""):
        decision = decide_fact_usability(
            verification_status="source_confirmed",
            confidence=confidence,
            source_verification_statuses=["source_confirmed"],
        )
        assert decision.usable is True, f"confidence={confidence!r}でもusableはTrueのはず"
