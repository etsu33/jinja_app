from temples.services.concierge_chat import _attach_recommendation_reason_quality


def _rec(**overrides):
    base = {
        "id": 1,
        "shrine_id": 1,
        "name": "テスト神社",
        "sajin": None,
        "description": None,
        "knowledge_deities": [],
        "knowledge_histories": [],
        "meaning_payload": {},
    }
    base.update(overrides)
    return base


def _attach(recs, interpretation_profile=None):
    payload = {"recommendations": recs}
    _attach_recommendation_reason_quality(
        recs=payload, interpretation_profile=interpretation_profile or {}
    )
    return payload["recommendations"]


def test_fully_knowledge_backed_deity_only():
    recs = _attach(
        [
            _rec(
                knowledge_deities=[
                    {"display_name": "経津主大神", "sort_order": 0, "confidence": "high"}
                ],
            )
        ]
    )
    quality = recs[0]["recommendation_reason_quality"]
    assert quality["knowledge_backing_class"] == "FULLY_KNOWLEDGE_BACKED"
    assert quality["deity_knowledge_used"] is True
    assert quality["history_knowledge_used"] is False


def test_fully_knowledge_backed_history_only():
    recs = _attach(
        [
            _rec(
                knowledge_histories=[
                    {
                        "history_type": "founding",
                        "title": "創建",
                        "content": "由緒本文",
                        "period_text": "",
                        "sort_order": 0,
                        "confidence": "high",
                    }
                ],
            )
        ]
    )
    quality = recs[0]["recommendation_reason_quality"]
    assert quality["knowledge_backing_class"] == "FULLY_KNOWLEDGE_BACKED"
    assert quality["deity_knowledge_used"] is False
    assert quality["history_knowledge_used"] is True


def test_partially_knowledge_backed():
    recs = _attach(
        [
            _rec(
                description="由緒本文レガシー",
                knowledge_deities=[
                    {"display_name": "祭神A", "sort_order": 0, "confidence": "high"}
                ],
            )
        ]
    )
    quality = recs[0]["recommendation_reason_quality"]
    assert quality["knowledge_backing_class"] == "PARTIALLY_KNOWLEDGE_BACKED"
    assert quality["deity_knowledge_used"] is True
    assert quality["history_knowledge_used"] is False


def test_legacy_backed():
    recs = _attach([_rec(sajin="天照大神", description="由緒本文レガシー")])
    quality = recs[0]["recommendation_reason_quality"]
    assert quality["knowledge_backing_class"] == "LEGACY_BACKED"
    assert quality["deity_knowledge_used"] is False
    assert quality["history_knowledge_used"] is False


def test_unknown_when_no_facts():
    recs = _attach([_rec()])
    quality = recs[0]["recommendation_reason_quality"]
    assert quality["knowledge_backing_class"] == "UNKNOWN"
    assert quality["deity_knowledge_used"] is False
    assert quality["history_knowledge_used"] is False


def test_both_deity_and_history_knowledge_used():
    recs = _attach(
        [
            _rec(
                knowledge_deities=[
                    {"display_name": "祭神B", "sort_order": 0, "confidence": "high"}
                ],
                knowledge_histories=[
                    {
                        "history_type": "founding",
                        "title": "創建",
                        "content": "由緒本文",
                        "period_text": "",
                        "sort_order": 0,
                        "confidence": "high",
                    }
                ],
            )
        ]
    )
    quality = recs[0]["recommendation_reason_quality"]
    assert quality["knowledge_backing_class"] == "FULLY_KNOWLEDGE_BACKED"
    assert quality["deity_knowledge_used"] is True
    assert quality["history_knowledge_used"] is True


def test_history_theme_alone_does_not_flip_knowledge_backing_class():
    """history_theme（Legacy分類タグ）のみが存在する場合、Knowledge由来と
    誤分類しないことを固定化する（knowledge-recommendation-analytics-contract.md
    Quality Property Gap対応の回帰ガード）。"""
    recs = _attach([_rec(history_theme="学び")])
    quality = recs[0]["recommendation_reason_quality"]
    assert quality["knowledge_backing_class"] == "UNKNOWN"
    assert quality["history_knowledge_used"] is False


def test_existing_quality_keys_are_preserved():
    recs = _attach(
        [
            _rec(
                goriyaku="縁結び",
                knowledge_deities=[
                    {"display_name": "祭神C", "sort_order": 0, "confidence": "high"}
                ],
            )
        ]
    )
    quality = recs[0]["recommendation_reason_quality"]
    for key in (
        "shrine_data_rate",
        "consultation_reflection_rate",
        "fallback_reason_rate",
        "evidence_rate",
        "action_grounding_rate",
        "is_ai_inference_only",
        "fallback_source",
    ):
        assert key in quality


def test_quality_payload_does_not_leak_source_url_or_raw_fact_text():
    recs = _attach(
        [
            _rec(
                knowledge_deities=[
                    {"display_name": "祭神D", "sort_order": 0, "confidence": "high"}
                ],
            )
        ]
    )
    quality = recs[0]["recommendation_reason_quality"]
    assert "source_url" not in quality
    assert "deity" not in quality
    assert "shrine_history" not in quality


def test_recommendations_v2_receives_same_knowledge_properties():
    payload = {
        "recommendations": [
            _rec(
                knowledge_deities=[
                    {"display_name": "祭神E", "sort_order": 0, "confidence": "high"}
                ],
            )
        ],
        "recommendations_v2": [{"shrine_id": 1, "id": 1, "name": "テスト神社"}],
    }
    _attach_recommendation_reason_quality(recs=payload, interpretation_profile={})
    v2_quality = payload["recommendations_v2"][0]["recommendation_reason_quality"]
    assert v2_quality["knowledge_backing_class"] == "FULLY_KNOWLEDGE_BACKED"
