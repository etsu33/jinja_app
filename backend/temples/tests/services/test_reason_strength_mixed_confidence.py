"""PR #2228 follow-up: mixed Deity confidence fail-safe修正の回帰テスト。

複数DeityのconfidenceがReason文へ連結される際に一致しない場合、
"confidence未設定"や"Legacy fallback"と同じNoneへ丸めてしまうと、
low相当のKnowledge Factが誤ってassertive表現でReasonへ出てしまう。

CONFIDENCE_MIXED(内部専用sentinel)により、以下を明確に区別する。
- confidence未設定（空文字のみで一致）: None → legacy-compatible assertive
- 複数Deityでconfidenceが一致しない（空文字を含む混在も含む）: CONFIDENCE_MIXED → suppressed
"""

from __future__ import annotations

import pytest

from temples.services.concierge_chat import _build_score_v3_candidate_profile
from temples.services.evidence_gate import decide_fact_usability
from temples.services.recommendation_reason_v4 import (
    CONFIDENCE_MIXED,
    build_recommendation_reason_v4,
)
from temples.services.shrine_knowledge_selector import fetch_fact_ready_knowledge_deities


def _deities_rec(shrine_id: int, confidences: list[str], **extra) -> dict:
    rec = {
        "shrine_id": shrine_id,
        "name": "テスト神社",
        "knowledge_deities": [
            {"display_name": f"祭神{i}", "sort_order": i, "confidence": c}
            for i, c in enumerate(confidences)
        ],
    }
    rec.update(extra)
    return rec


# --- 同一confidence（既存PR実装を維持） ---


def test_case1_high_high_keeps_deity_and_uses_assertive():
    rec = _deities_rec(1, ["high", "high"])
    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert profile["deity_confidence"] == "high"
    assert result["fact"]["deity"] == "祭神0、祭神1"
    assert "祭神0、祭神1が祀られています。" in result["reason_text"]


def test_case2_medium_medium_keeps_deity_and_uses_weakened():
    rec = _deities_rec(1, ["medium", "medium"])
    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert profile["deity_confidence"] == "medium"
    assert result["fact"]["deity"] == "祭神0、祭神1"
    assert "祭神0、祭神1が祀られているとされています。" in result["reason_text"]


def test_case3_low_low_suppresses_deity_from_reason():
    rec = _deities_rec(1, ["low", "low"])
    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert profile["deity_confidence"] == "low"
    assert result["fact"]["deity"] is None
    assert "祭神0" not in result["reason_text"]
    assert "祭神1" not in result["reason_text"]


def test_case4_empty_empty_keeps_deity_and_uses_legacy_compatible_assertive():
    rec = _deities_rec(1, ["", ""])
    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert profile["deity_confidence"] is None
    assert result["fact"]["deity"] == "祭神0、祭神1"
    assert "祭神0、祭神1が祀られています。" in result["reason_text"]


@pytest.mark.parametrize("confidence", ["high", "medium", "low", ""])
def test_single_deity_confidence_matches_multi_deity_uniform_behavior(confidence):
    rec = _deities_rec(1, [confidence])
    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    if confidence == "low":
        assert result["fact"]["deity"] is None
        assert "祭神0" not in result["reason_text"]
    else:
        assert result["fact"]["deity"] == "祭神0"
        if confidence == "medium":
            assert "祭神0が祀られているとされています。" in result["reason_text"]
        else:
            assert "祭神0が祀られています。" in result["reason_text"]


# --- mixed confidence ---


@pytest.mark.parametrize(
    "confidences",
    [
        ["high", "medium"],  # case5
        ["high", "low"],  # case6
        ["medium", "low"],  # case7
        ["high", ""],  # case8
        ["medium", ""],  # case9
        ["low", ""],  # case10
    ],
)
def test_mixed_confidence_suppresses_knowledge_deity_from_reason(confidences):
    rec = _deities_rec(1, confidences)
    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert profile["deity_confidence"] == CONFIDENCE_MIXED
    assert profile["deity_confidence"] is not None
    assert result["fact"]["deity"] is None
    assert result["used_fact"]["deity"] is None
    assert "祭神0" not in result["reason_text"]
    assert "祭神1" not in result["reason_text"]
    assert "神社固有情報が十分でないため" in result["reason_text"]


# --- 契約回帰 ---


def test_mixed_confidence_does_not_change_evidence_gate_usable():
    """case11: mixedでもEvidence Gate usable判定は変更されない。"""
    for confidence in ("high", "medium", "low", ""):
        decision = decide_fact_usability(
            verification_status="source_confirmed",
            confidence=confidence,
            source_verification_statuses=["source_confirmed"],
        )
        assert decision.usable is True


@pytest.mark.django_db
def test_mixed_confidence_does_not_remove_deity_from_knowledge_selector():
    """case12: mixedでもKnowledge selector結果からDeity自体は消えない。"""
    from django.utils import timezone

    from temples.models import Shrine, ShrineDeity, ShrineKnowledgeSource

    shrine = Shrine.objects.create(
        name_jp="mixed confidence監査神社",
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )
    source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="出典",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    deity_high = ShrineDeity.objects.create(
        shrine=shrine,
        display_name="高confidence祭神",
        verification_status="source_confirmed",
        confidence="high",
        sort_order=0,
        verified_at=timezone.now(),
    )
    deity_low = ShrineDeity.objects.create(
        shrine=shrine,
        display_name="低confidence祭神",
        verification_status="source_confirmed",
        confidence="low",
        sort_order=1,
        verified_at=timezone.now(),
    )
    for deity in (deity_high, deity_low):
        deity.sources.add(source)

    result = fetch_fact_ready_knowledge_deities([shrine.id])[shrine.id]

    # selectorはFact単位で返す(Reason文字列結合の責務は持たない)ため、
    # confidence混在(高+低)でも両Deityともそのまま返る。
    names = {item["display_name"] for item in result}
    assert names == {"高confidence祭神", "低confidence祭神"}


@pytest.mark.django_db
def test_mixed_confidence_does_not_affect_shrine_detail_api():
    """case13: mixedでもShrine Detail APIには影響しない。"""
    from django.utils import timezone

    from rest_framework.test import APIClient

    from temples.models import Shrine, ShrineDeity, ShrineKnowledgeSource

    shrine = Shrine.objects.create(
        name_jp="mixed confidence Detail監査神社",
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )
    source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="出典",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    deity_high = ShrineDeity.objects.create(
        shrine=shrine,
        display_name="高confidence祭神",
        verification_status="source_confirmed",
        confidence="high",
        sort_order=0,
        verified_at=timezone.now(),
    )
    deity_low = ShrineDeity.objects.create(
        shrine=shrine,
        display_name="低confidence祭神",
        verification_status="source_confirmed",
        confidence="low",
        sort_order=1,
        verified_at=timezone.now(),
    )
    for deity in (deity_high, deity_low):
        deity.sources.add(source)

    client = APIClient(SERVER_NAME="127.0.0.1")
    resp = client.get(f"/api/shrines/{shrine.id}/")

    assert resp.status_code == 200
    body = resp.json()
    names = {d["display_name"] for d in body["deities"]}
    assert names == {"高confidence祭神", "低confidence祭神"}


def test_mixed_confidence_does_not_fallback_to_legacy_sajin():
    """case14: mixed suppression後にLegacy sajinへfallbackしない。

    Knowledge deityが存在する(usable)場合、confidenceがmixedであっても
    candidate_profile["deity"]はKnowledge由来のまま(Legacy sajinへは
    切り替わらない)。suppressionはReason生成内部(fact.deity)のみで起きる。
    """
    rec = _deities_rec(1, ["high", "low"], sajin="レガシー祭神(混入してはいけない)")
    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity"] == "祭神0、祭神1"
    assert "レガシー祭神" not in profile["deity"]

    result = build_recommendation_reason_v4(candidate_profile=profile)
    assert "レガシー祭神" not in result["reason_text"]
    assert "祭神0" not in result["reason_text"]
    assert "祭神1" not in result["reason_text"]


def test_mixed_confidence_does_not_change_interpretation_or_action():
    """case15: Interpretation/Actionは変更しない。"""
    rec = _deities_rec(1, ["high", "low"])
    profile = _build_score_v3_candidate_profile(rec)

    result_mixed = build_recommendation_reason_v4(
        candidate_profile=profile,
        interpretation_profile={"state_profile": {"primary_state": "uncertain"}},
    )
    result_uniform = build_recommendation_reason_v4(
        candidate_profile={**profile, "deity_confidence": "high"},
        interpretation_profile={"state_profile": {"primary_state": "uncertain"}},
    )

    assert result_mixed["interpretation"] == result_uniform["interpretation"]
    assert result_mixed["action"] == result_uniform["action"]


# --- Pilot regression(全high、mixedとは無関係だが回帰確認として明記) ---


def test_pilot_meiji_jingu_uniform_high_is_unaffected_by_mixed_confidence_change():
    """case17: 明治神宮相当Pilot(全high)回帰PASS。"""
    rec = {
        "shrine_id": 1,
        "name": "明治神宮",
        "knowledge_deities": [
            {"display_name": "明治天皇", "sort_order": 0, "confidence": "high"},
            {"display_name": "昭憲皇太后", "sort_order": 1, "confidence": "high"},
        ],
    }
    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert profile["deity_confidence"] == "high"
    assert "明治神宮では、明治天皇、昭憲皇太后が祀られています。" in result["reason_text"]


def test_pilot_shinagawa_jinja_uniform_high_is_unaffected_by_mixed_confidence_change():
    """case18: 品川神社相当Pilot(全high)回帰PASS。"""
    rec = {
        "shrine_id": 50,
        "name": "品川神社",
        "knowledge_deities": [
            {"display_name": "天比理乃咩命", "sort_order": 0, "confidence": "high"},
            {"display_name": "宇賀之売命", "sort_order": 1, "confidence": "high"},
            {"display_name": "素盞嗚尊", "sort_order": 2, "confidence": "high"},
        ],
    }
    profile = _build_score_v3_candidate_profile(rec)
    result = build_recommendation_reason_v4(candidate_profile=profile)

    assert profile["deity_confidence"] == "high"
    assert (
        "品川神社では、天比理乃咩命、宇賀之売命、素盞嗚尊が祀られています。"
        in result["reason_text"]
    )
