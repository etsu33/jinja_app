# -*- coding: utf-8 -*-
import copy

from temples.services.concierge_explanation_payload import attach_explanation_payload
from temples.services.concierge_explanations import attach_explanations_for_chat


def test_attach_explanations_keeps_recommendation_contract_fields_and_breakdown():
    recs = {
        "recommendations": [
            {
                "name": "神社A",
                "reason": "仕事運の願いと相性があります。",
                "reason_source": "reason:matched_need_tags",
                "breakdown": {
                    "score_need": 1.2,
                    "score_total": 0.6,
                    "matched_need_tags": ["career"],
                },
                "distance_m": 1200,
                "place_id": "PID_A",
                "popular_score": 7.5,
            },
            {
                "name": "神社B",
                "reason": "心を整えたい相談内容と相性があります。",
                "reason_source": "reason:normalized_original",
                "breakdown": {
                    "score_need": 1.0,
                    "score_total": 0.5,
                    "matched_need_tags": ["mental"],
                },
                "distance_m": 800,
                "place_id": "PID_B",
                "popular_score": 6.0,
            },
        ]
    }
    before = copy.deepcopy(recs["recommendations"])

    out = attach_explanations_for_chat(
        recs,
        query="近場で参拝したい",
        bias={"lat": 35.0, "lng": 139.0, "radius": 8000},
        birthdate=None,
        extra_condition="静か",
    )

    assert "recommendations" in out
    assert len(out["recommendations"]) == len(before)

    for idx, rec in enumerate(out["recommendations"]):
        assert "reason" in rec
        assert "reason_source" in rec
        assert rec["reason"] == before[idx]["reason"]
        assert rec["reason_source"] == before[idx]["reason_source"]
        assert rec["breakdown"] == before[idx]["breakdown"]

        for key, value in before[idx].items():
            assert key in rec
            assert rec[key] == value

        assert "explanation" in rec
        assert rec["explanation"]["version"] == 2
        assert isinstance(rec["explanation"]["summary"], str)
        assert isinstance(rec["explanation"]["reasons"], list)


def test_attach_explanations_chat_uses_primary_need_tag_for_summary_and_reason():
    recs = {
        "recommendations": [
            {
                "name": "神社A",
                "reason": "旧理由",
                "reason_source": "reason:need",
                "_explanation_payload": {
                    "version": 2,
                    "matched_need_tags": ["career"],
                    "highlights": [],
                    "primary_reason": {
                        "type": "need_tag",
                        "label": "career",
                        "label_ja": "転機・仕事",
                        "evidence": ["career"],
                        "score": 2.0,
                        "is_primary": True,
                    },
                    "secondary_reasons": [],
                    "original_reason": "旧理由",
                },
            }
        ]
    }

    out = attach_explanations_for_chat(
        recs,
        query="転職が不安",
        bias=None,
        birthdate=None,
        extra_condition=None,
    )

    rec = out["recommendations"][0]
    exp = rec["explanation"]

    assert exp["version"] == 2
    assert exp["summary"] == "転機・仕事に関わる願いごとと重なる神社です。"
    assert exp["reasons"][0]["code"] == "NEED_MATCH"
    assert exp["reasons"][0]["label"] == "相談との一致"

def test_attach_explanations_chat_uses_element_primary_reason():
    recs = {
        "recommendations": [
            {
                "name": "神社B",
                "reason": "旧理由",
                "reason_source": "reason:compat",
                "_explanation_payload": {
                    "version": 2,
                    "matched_need_tags": [],
                    "highlights": [],
                    "primary_reason": {
                        "type": "element",
                        "label": "element",
                        "label_ja": "生年月日との相性",
                        "evidence": ["score_element:2"],
                        "score": 2.0,
                        "is_primary": True,
                    },
                    "secondary_reasons": [],
                    "original_reason": "旧理由",
                },
            }
        ]
    }

    out = attach_explanations_for_chat(
        recs,
        query="",
        bias=None,
        birthdate="1984-05-15",
        extra_condition=None,
    )

    rec = out["recommendations"][0]
    exp = rec["explanation"]

    assert exp["version"] == 2
    assert exp["summary"] == "生年月日から見た傾向も、補助情報として重ねています。"
    assert exp["reasons"][0]["code"] == "ELEMENT_MATCH"
    assert exp["reasons"][0]["label"] == "生年月日との相性補助"

def test_attach_explanations_chat_uses_fallback_primary_reason():
    recs = {
        "recommendations": [
            {
                "name": "神社C",
                "reason": "",
                "reason_source": "reason:fallback",
                "_explanation_payload": {
                    "version": 2,
                    "matched_need_tags": [],
                    "highlights": [],
                    "primary_reason": {
                        "type": "fallback",
                        "label": "fallback",
                        "label_ja": "近い候補",
                        "evidence": [],
                        "score": 0.0,
                        "is_primary": True,
                    },
                    "secondary_reasons": [],
                    "original_reason": "",
                },
            }
        ]
    }

    out = attach_explanations_for_chat(
        recs,
        query="近場で参拝したい",
        bias=None,
        birthdate=None,
        extra_condition=None,
    )

    rec = out["recommendations"][0]
    exp = rec["explanation"]

    assert exp["version"] == 2
    assert exp["summary"] == "今の条件に近い神社として整理しています。"
    assert exp["reasons"][0]["code"] == "REASON_SOURCE"


def test_attach_explanation_payload_adds_gogyou_context_from_birthdate():
    recs = {
        "recommendations": [
            {
                "name": "神社D",
                "reason": "旧理由",
                "reason_source": "reason:compat",
                "breakdown": {
                    "score_element": 2,
                    "score_need": 0,
                    "score_total": 1.6,
                    "matched_need_tags": [],
                },
            }
        ]
    }

    out = attach_explanation_payload(recs, birthdate="1984-05-15")

    payload = out["recommendations"][0]["_explanation_payload"]
    assert payload["version"] == 2
    assert payload["gogyou_context"] == {
        "gogyou": "水",
        "eto": "子",
        "tone": "静かに整え直す流れ",
    }


def test_attach_explanations_chat_uses_gogyou_and_history_context_for_summary_and_reason():
    recs = {
        "recommendations": [
            {
                "name": "神社E",
                "reason": "旧理由",
                "reason_source": "reason:compat",
                "_explanation_payload": {
                    "version": 2,
                    "matched_need_tags": [],
                    "highlights": [],
                    "primary_reason": {
                        "type": "element",
                        "label": "element",
                        "label_ja": "生年月日との相性",
                        "evidence": ["score_element:2"],
                        "score": 2.0,
                        "is_primary": True,
                    },
                    "secondary_reasons": [],
                    "original_reason": "旧理由",
                    "gogyou_context": {
                        "gogyou": "水",
                        "eto": "子",
                        "tone": "静かに整え直す流れ",
                    },
                    "history_context": {
                        "theme": "静寂",
                        "label": "静寂",
                        "tone": "静かに心を整える文脈",
                    },
                },
            }
        ]
    }

    out = attach_explanations_for_chat(
        recs,
        query="",
        bias=None,
        birthdate="1984-05-15",
        extra_condition=None,
    )

    exp = out["recommendations"][0]["explanation"]
    assert exp["version"] == 2
    assert exp["summary"] == "今は「水」の傾向として、静かに整え直す流れと、静かに心を整える文脈が重なる神社です。"
    assert exp["reasons"][0]["code"] == "GOGYOU_CONTEXT"
    assert exp["reasons"][0]["label"] == "今の巡り"
    assert exp["reasons"][0]["evidence"]["gogyou_context"]["gogyou"] == "水"
    assert exp["reasons"][0]["evidence"]["history_context"]["theme"] == "静寂"


def test_attach_explanation_payload_adds_action_suggestions_from_history_theme():
    recs = {
        "recommendations": [
            {
                "name": "神社Action",
                "reason": "旧理由",
                "reason_source": "reason:history_theme",
                "history_theme": "勝負",
                "breakdown": {
                    "score_element": 0,
                    "score_need": 1,
                    "score_total": 1.0,
                    "matched_need_tags": ["career"],
                },
                # history_context/action_suggestions only surface when
                # history_theme actually had ranking authority (Explanation
                # Alignment Hardening: docs/product/recommendation-signal-
                # authority.md §6, history_theme_candidate_boost > 0 means
                # consultation_axis corresponded to this theme).
                "breakdown_detail": {
                    "features": {
                        "history_theme_candidate_boost": {"raw": 0.8},
                    },
                },
            }
        ]
    }

    out = attach_explanation_payload(recs, birthdate=None)

    payload = out["recommendations"][0]["_explanation_payload"]
    assert payload["version"] == 2
    assert payload["action_suggestions"]
    assert payload["action_suggestions"][0]["history_theme"] == "勝負"
    assert payload["action_suggestions"][0]["id"] == "challenge_choose_this_week"
    assert payload["action_suggestions"][0]["category"] == "prepare"


def test_attach_explanation_payload_action_suggestions_fallback_when_history_theme_missing():
    recs = {
        "recommendations": [
            {
                "name": "神社FallbackAction",
                "reason": "旧理由",
                "reason_source": "reason:fallback",
                "breakdown": {
                    "score_element": 0,
                    "score_need": 0,
                    "score_total": 0.0,
                    "matched_need_tags": [],
                },
            }
        ]
    }

    out = attach_explanation_payload(recs, birthdate=None)

    payload = out["recommendations"][0]["_explanation_payload"]
    assert payload["version"] == 2
    assert payload["history_context"] is None
    assert payload["action_suggestions"]
    assert payload["action_suggestions"][0]["history_theme"] == "静寂"
