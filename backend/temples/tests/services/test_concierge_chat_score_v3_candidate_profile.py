# backend/temples/tests/services/test_concierge_chat_score_v3_candidate_profile.py

from __future__ import annotations

from temples.services.concierge_chat import _build_score_v3_candidate_profile
from temples.services.recommendation_reason_v4 import CONFIDENCE_MIXED


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


# --- Deity正規化 ---


def test_candidate_profile_deity_falls_back_to_sajin_when_no_knowledge_deities():
    rec = {"shrine_id": 1, "sajin": "櫛真智命", "knowledge_deities": []}

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity"] == "櫛真智命"


def test_candidate_profile_deity_uses_single_knowledge_deity():
    rec = {
        "shrine_id": 1,
        "sajin": "レガシー祭神",
        "knowledge_deities": [{"display_name": "明治天皇", "sort_order": 0, "confidence": "high"}],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity"] == "明治天皇"


def test_candidate_profile_deity_joins_multiple_by_sort_order():
    rec = {
        "shrine_id": 50,
        "knowledge_deities": [
            {"display_name": "素盞嗚尊", "sort_order": 2, "confidence": "high"},
            {"display_name": "天比理乃咩命", "sort_order": 0, "confidence": "high"},
            {"display_name": "宇賀之売命", "sort_order": 1, "confidence": "high"},
        ],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity"] == "天比理乃咩命、宇賀之売命、素盞嗚尊"


def test_candidate_profile_deity_does_not_mix_knowledge_and_sajin():
    rec = {
        "shrine_id": 1,
        "sajin": "レガシー祭神",
        "knowledge_deities": [{"display_name": "明治天皇", "sort_order": 0, "confidence": "high"}],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert "レガシー祭神" not in profile["deity"]
    assert profile["deity"] == "明治天皇"


# --- History正規化 ---


def test_candidate_profile_shrine_history_falls_back_to_description_when_no_knowledge_histories():
    rec = {"shrine_id": 1, "description": "レガシー由緒", "knowledge_histories": []}

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["shrine_history"] == "レガシー由緒"


def test_candidate_profile_shrine_history_uses_single_knowledge_history_content():
    rec = {
        "shrine_id": 1,
        "description": "レガシー由緒",
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

    assert profile["shrine_history"] == "明治神宮は、東京都渋谷区代々木に大正9年（1920）に創建された。"


def test_candidate_profile_shrine_history_uses_only_lowest_sort_order_entry():
    rec = {
        "shrine_id": 50,
        "knowledge_histories": [
            {
                "history_type": "historical_event",
                "title": "1319年",
                "content": "二階堂道蘊公が宇賀之売命を祀った。",
                "period_text": "元応元年（1319年）",
                "sort_order": 1,
                "confidence": "high",
            },
            {
                "history_type": "founding",
                "title": "1187年",
                "content": "源頼朝公が安房国の洲崎明神から天比理乃咩命を当地に迎え、海上交通安全と祈願成就を祈ったことを創始とする。",
                "period_text": "文治3年（1187年）",
                "sort_order": 0,
                "confidence": "high",
            },
            {
                "history_type": "historical_event",
                "title": "1478年",
                "content": "太田道灌公が素盞嗚尊を祀った。",
                "period_text": "文明10年（1478年）",
                "sort_order": 2,
                "confidence": "high",
            },
        ],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["shrine_history"] == (
        "源頼朝公が安房国の洲崎明神から天比理乃咩命を当地に迎え、海上交通安全と祈願成就を祈ったことを創始とする。"
    )
    # 1319年/1478年のcontentはshrine_historyへ混入しない
    assert "二階堂道蘊公" not in profile["shrine_history"]
    assert "太田道灌公" not in profile["shrine_history"]


def test_candidate_profile_shrine_history_ignores_history_type_priority():
    """history_type独自の優先順位（founding優先等）は導入しない。sort_orderのみで決まる。"""
    rec = {
        "shrine_id": 1,
        "knowledge_histories": [
            {
                "history_type": "historical_event",
                "title": "sort_order 0",
                "content": "sort_order最小の内容",
                "sort_order": 0,
                "confidence": "high",
            },
            {
                "history_type": "founding",
                "title": "sort_order 1",
                "content": "foundingだがsort_orderは1",
                "sort_order": 1,
                "confidence": "high",
            },
        ],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["shrine_history"] == "sort_order最小の内容"


def test_candidate_profile_shrine_history_does_not_mix_knowledge_and_description():
    rec = {
        "shrine_id": 1,
        "description": "レガシー由緒",
        "knowledge_histories": [
            {"history_type": "official_origin", "content": "新Knowledgeの由緒", "sort_order": 0}
        ],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert "レガシー由緒" not in profile["shrine_history"]
    assert profile["shrine_history"] == "新Knowledgeの由緒"


# --- Field単位fallback ---


def test_candidate_profile_field_level_fallback_deity_new_history_legacy():
    rec = {
        "shrine_id": 1,
        "sajin": "レガシー祭神",
        "description": "レガシー由緒",
        "knowledge_deities": [{"display_name": "新祭神", "sort_order": 0}],
        "knowledge_histories": [],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity"] == "新祭神"
    assert profile["shrine_history"] == "レガシー由緒"


def test_candidate_profile_field_level_fallback_deity_legacy_history_new():
    rec = {
        "shrine_id": 1,
        "sajin": "レガシー祭神",
        "description": "レガシー由緒",
        "knowledge_deities": [],
        "knowledge_histories": [{"history_type": "official_origin", "content": "新由緒", "sort_order": 0}],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity"] == "レガシー祭神"
    assert profile["shrine_history"] == "新由緒"


def test_candidate_profile_field_level_fallback_both_new():
    rec = {
        "shrine_id": 1,
        "sajin": "レガシー祭神",
        "description": "レガシー由緒",
        "knowledge_deities": [{"display_name": "新祭神", "sort_order": 0}],
        "knowledge_histories": [{"history_type": "official_origin", "content": "新由緒", "sort_order": 0}],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity"] == "新祭神"
    assert profile["shrine_history"] == "新由緒"


def test_candidate_profile_field_level_fallback_both_legacy():
    rec = {
        "shrine_id": 1,
        "sajin": "レガシー祭神",
        "description": "レガシー由緒",
        "knowledge_deities": [],
        "knowledge_histories": [],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity"] == "レガシー祭神"
    assert profile["shrine_history"] == "レガシー由緒"


# --- Pilot fixtures ---


def test_candidate_profile_matches_pilot_1_meiji_jingu():
    rec = {
        "shrine_id": 1,
        "sajin": "",
        "description": None,
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

    assert profile["deity"] == "明治天皇、昭憲皇太后"
    assert profile["shrine_history"] == "明治神宮は、東京都渋谷区代々木に大正9年（1920）に創建された。"


def test_candidate_profile_matches_pilot_2_shinagawa():
    rec = {
        "shrine_id": 50,
        "sajin": "",
        "description": None,
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
            {
                "history_type": "historical_event",
                "title": "文明10年（1478年）の素盞嗚尊奉祀",
                "content": "太田道灌公が素盞嗚尊を祀った。",
                "period_text": "文明10年（1478年）",
                "sort_order": 2,
                "confidence": "high",
            },
        ],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity"] == "天比理乃咩命、宇賀之売命、素盞嗚尊"
    assert profile["shrine_history"] == (
        "源頼朝公が安房国の洲崎明神から天比理乃咩命を当地に迎え、海上交通安全と祈願成就を祈ったことを創始とする。"
    )
    # 1319年/1478年はcandidate structured arrayに存在するが、shrine_history projectionには混入しない
    assert "二階堂道蘊公" not in profile["shrine_history"]
    assert "太田道灌公" not in profile["shrine_history"]


def test_candidate_profile_zero_knowledge_shrine_matches_legacy_output():
    """新Knowledge未投入Shrineの回帰: 現行(sajin/description由来)のoutputと一致する。"""
    rec_without_knowledge_keys = {"shrine_id": 99, "sajin": "", "description": None}
    rec_with_empty_knowledge = {
        "shrine_id": 99,
        "sajin": "",
        "description": None,
        "knowledge_deities": [],
        "knowledge_histories": [],
    }

    profile_a = _build_score_v3_candidate_profile(rec_without_knowledge_keys)
    profile_b = _build_score_v3_candidate_profile(rec_with_empty_knowledge)

    assert profile_a["deity"] is None
    assert profile_a["shrine_history"] is None
    assert profile_a["deity"] == profile_b["deity"]
    assert profile_a["shrine_history"] == profile_b["shrine_history"]


# --- PR-B: confidence伝播 ---


def test_candidate_profile_deity_confidence_is_propagated_from_single_knowledge_deity():
    rec = {
        "shrine_id": 1,
        "knowledge_deities": [{"display_name": "明治天皇", "sort_order": 0, "confidence": "high"}],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity_confidence"] == "high"


def test_candidate_profile_deity_confidence_is_propagated_when_all_deities_share_same_value():
    rec = {
        "shrine_id": 50,
        "knowledge_deities": [
            {"display_name": "天比理乃咩命", "sort_order": 0, "confidence": "medium"},
            {"display_name": "宇賀之売命", "sort_order": 1, "confidence": "medium"},
            {"display_name": "素盞嗚尊", "sort_order": 2, "confidence": "medium"},
        ],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity_confidence"] == "medium"


def test_candidate_profile_deity_confidence_is_mixed_sentinel_when_confidences_differ():
    """複数Deityでconfidenceが混在する場合の集約ルールは契約上未確定のため、
    勝手にmin/max/average等を採用しない。ただしNone(confidence未設定/
    Legacy fallback相当)と混同してはならないため、専用sentinel(CONFIDENCE_MIXED)
    へ倒す(PR-B follow-up)。
    """
    rec = {
        "shrine_id": 1,
        "knowledge_deities": [
            {"display_name": "A神", "sort_order": 0, "confidence": "high"},
            {"display_name": "B神", "sort_order": 1, "confidence": "low"},
        ],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity_confidence"] == CONFIDENCE_MIXED
    assert profile["deity_confidence"] is not None
    # 集約せず(=特定の値を選ばず)mixed扱いにしているだけで、両Deityの名前は
    # 引き続き結合される(usable Factが消えるわけではない。Knowledge selector・
    # Detail APIから消えるわけでもない)。
    assert profile["deity"] == "A神、B神"


def test_candidate_profile_deity_confidence_is_none_when_unset():
    rec = {
        "shrine_id": 1,
        "knowledge_deities": [{"display_name": "明治天皇", "sort_order": 0}],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity_confidence"] is None


def test_candidate_profile_deity_confidence_is_none_when_legacy_fallback():
    """Legacy(sajin)Fieldにはconfidence概念が存在しないため常にNone。"""
    rec = {"shrine_id": 1, "sajin": "レガシー祭神", "knowledge_deities": []}

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity"] == "レガシー祭神"
    assert profile["deity_confidence"] is None


def test_candidate_profile_shrine_history_confidence_is_propagated_from_selected_history():
    rec = {
        "shrine_id": 1,
        "knowledge_histories": [
            {
                "history_type": "official_origin",
                "content": "明治神宮は、東京都渋谷区代々木に大正9年（1920）に創建された。",
                "sort_order": 0,
                "confidence": "high",
            }
        ],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["shrine_history_confidence"] == "high"


def test_candidate_profile_shrine_history_confidence_matches_the_selected_history_only():
    """sort_order最小の1件のconfidenceのみを採用し、他Historyのconfidenceを混ぜない。"""
    rec = {
        "shrine_id": 50,
        "knowledge_histories": [
            {
                "history_type": "historical_event",
                "content": "二階堂道蘊公が宇賀之売命を祀った。",
                "sort_order": 1,
                "confidence": "low",
            },
            {
                "history_type": "founding",
                "content": "源頼朝公が安房国の洲崎明神から天比理乃咩命を当地に迎えた。",
                "sort_order": 0,
                "confidence": "medium",
            },
        ],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["shrine_history"] == "源頼朝公が安房国の洲崎明神から天比理乃咩命を当地に迎えた。"
    assert profile["shrine_history_confidence"] == "medium"


def test_candidate_profile_shrine_history_confidence_is_none_when_unset():
    rec = {
        "shrine_id": 1,
        "knowledge_histories": [{"history_type": "official_origin", "content": "由緒", "sort_order": 0}],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["shrine_history_confidence"] is None


def test_candidate_profile_shrine_history_confidence_is_none_when_legacy_fallback():
    """Legacy(description)Fieldにはconfidence概念が存在しないため常にNone。"""
    rec = {"shrine_id": 1, "description": "レガシー由緒", "knowledge_histories": []}

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["shrine_history"] == "レガシー由緒"
    assert profile["shrine_history_confidence"] is None


def test_candidate_profile_pilot_1_meiji_jingu_confidence_is_high():
    rec = {
        "shrine_id": 1,
        "knowledge_deities": [
            {"display_name": "明治天皇", "sort_order": 0, "confidence": "high"},
            {"display_name": "昭憲皇太后", "sort_order": 1, "confidence": "high"},
        ],
        "knowledge_histories": [
            {
                "history_type": "official_origin",
                "content": "明治神宮は、東京都渋谷区代々木に大正9年（1920）に創建された。",
                "sort_order": 0,
                "confidence": "high",
            }
        ],
    }

    profile = _build_score_v3_candidate_profile(rec)

    assert profile["deity_confidence"] == "high"
    assert profile["shrine_history_confidence"] == "high"
