from __future__ import annotations

from temples.services.concierge_explanation_payload import build_explanation_payload
from temples.services.concierge_explanations import build_explanation_for_chat_rec


def test_build_explanation_payload_prefers_visit_style_over_fallback_primary_reason():
    payload = build_explanation_payload(
        {
            "reason": "候補としておすすめしています。",
            "_reason_facts": [
                {
                    "type": "fallback",
                    "label": "fallback",
                    "label_ja": "近い候補",
                    "evidence": [],
                    "score": 0.0,
                    "is_primary": True,
                }
            ],
            "breakdown": {
                "score_need": 0,
                "score_total": 0.0,
                "matched_need_tags": [],
            },
            "breakdown_detail": {
                "features": {
                    "visit_style": {
                        "raw": 1,
                        "matched_tags": ["quiet"],
                        "contribution": 0.35,
                    },
                    "score_total_ranked": 0.35,
                }
            },
        }
    )

    assert payload["primary_reason"] == {
        "type": "visit_style",
        "label": "quiet",
        "label_ja": "参拝スタイル",
        "evidence": ["quiet"],
        "score": 0.35,
        "is_primary": True,
    }
    assert payload["matched_need_tags"] == []


# New test for user_selected_tag primary reason
def test_build_explanation_payload_keeps_user_selected_tag_primary_reason():
    payload = build_explanation_payload(
        {
            "reason": "候補としておすすめしています。",
            "_reason_facts": [
                {
                    "type": "user_selected_tag",
                    "label": "goriyaku_tag:1",
                    "label_ja": "goriyaku_tag:1",
                    "evidence": ["requested_goriyaku_tag_ids"],
                    "score": 3.0,
                    "is_primary": True,
                },
                {
                    "type": "text_hint",
                    "label": "rest",
                    "label_ja": "休息",
                    "evidence": ["text_score:3"],
                    "score": 3.0,
                    "is_primary": False,
                },
            ],
            "breakdown": {
                "score_need": 1,
                "score_total": 0.3,
                "matched_need_tags": ["rest"],
            },
            "breakdown_detail": {
                "features": {
                    "score_total_ranked": 0.9,
                }
            },
        }
    )

    assert payload["primary_reason"] == {
        "type": "user_selected_tag",
        "label": "goriyaku_tag:1",
        "label_ja": "goriyaku_tag:1",
        "evidence": ["requested_goriyaku_tag_ids"],
        "score": 3.0,
        "is_primary": True,
    }
    assert payload["secondary_reasons"] == [
        {
            "type": "text_hint",
            "label": "rest",
            "label_ja": "休息",
            "evidence": ["text_score:3"],
            "score": 3.0,
            "is_primary": False,
        }
    ]


def test_build_explanation_for_chat_rec_adds_quiet_visit_style_reason():
    result = build_explanation_for_chat_rec(
        {
            "reason": "候補としておすすめしています。",
            "_explanation_payload": {
                "primary_reason": {
                    "type": "fallback",
                    "label": "fallback",
                    "label_ja": "近い候補",
                    "evidence": [],
                    "score": 0.0,
                    "is_primary": True,
                },
                "highlights": [],
            },
            "breakdown_detail": {
                "features": {
                    "visit_style": {
                        "raw": 1,
                        "matched_tags": ["quiet"],
                        "contribution": 0.35,
                    }
                }
            },
        },
        query="静かな場所でお参りしたいです",
        bias=None,
        birthdate=None,
        extra_condition=None,
    )

    reasons = result["reasons"]
    visit_style_reason = next(r for r in reasons if r["code"] == "VISIT_STYLE_MATCH")

    assert visit_style_reason["label"] == "参拝スタイルとの一致"
    assert visit_style_reason["text"] == "静かで落ち着いた雰囲気を求める条件と重なっています。"
    assert visit_style_reason["strength"] == "high"
    assert visit_style_reason["evidence"]["matched_visit_style_tags"] == ["quiet"]


def test_build_explanation_for_chat_rec_adds_less_crowded_visit_style_reason():
    result = build_explanation_for_chat_rec(
        {
            "reason": "候補としておすすめしています。",
            "_explanation_payload": {
                "primary_reason": {
                    "type": "fallback",
                    "label": "fallback",
                    "label_ja": "近い候補",
                    "evidence": [],
                    "score": 0.0,
                    "is_primary": True,
                },
                "highlights": [],
            },
            "breakdown_detail": {
                "features": {
                    "visit_style": {
                        "raw": 1,
                        "matched_tags": ["less_crowded"],
                        "contribution": 0.35,
                    }
                }
            },
        },
        query="人が少ない場所でお参りしたいです",
        bias=None,
        birthdate=None,
        extra_condition=None,
    )

    reasons = result["reasons"]
    visit_style_reason = next(r for r in reasons if r["code"] == "VISIT_STYLE_MATCH")

    assert visit_style_reason["label"] == "参拝スタイルとの一致"
    assert visit_style_reason["text"] == "人が少なめで落ち着いて参拝したい条件と重なっています。"
    assert visit_style_reason["strength"] == "high"
    assert visit_style_reason["evidence"]["matched_visit_style_tags"] == ["less_crowded"]

def test_build_explanation_for_chat_rec_prioritizes_user_selected_beauty_over_gogyou():
    exp = build_explanation_for_chat_rec(
        {
            "name": "美容神社",
            "_explanation_payload": {
                "primary_reason": {
                    "type": "user_selected_tag",
                    "label": "美容",
                    "label_ja": "美容",
                    "evidence": ["requested_goriyaku_tag_ids"],
                    "score": 3.0,
                    "is_primary": True,
                },
                "gogyou_context": {
                    "gogyou": "土",
                    "tone": "足元を固め、落ち着いて整えやすい流れ",
                },
            },
        },
        query="美容で整えたい",
        bias=None,
        birthdate="1984-05-15",
    )

    assert "美容" in exp["summary"]
    assert exp["reasons"][0]["code"] == "USER_SELECTED_TAG"


def test_recommendation_reason_never_promotes_direction_or_assertive_copy():
    exp = build_explanation_for_chat_rec(
        {
            "reason": "仕事の迷いを整理する候補です。",
            "direction_reference": {
                "actual_direction": "東",
                "reference_directions": ["東"],
                "matched": True,
            },
            "_explanation_payload": {
                "primary_reason": {
                    "type": "need_tag",
                    "label": "career",
                    "label_ja": "仕事",
                    "evidence": ["matched_need_tags"],
                    "score": 3.0,
                    "is_primary": True,
                },
                "matched_need_tags": ["career"],
            },
        },
        query="仕事の迷いを整理したい",
        bias=None,
    )

    visible_reason = " ".join(
        [exp["summary"], *[reason["text"] for reason in exp["reasons"]]]
    )
    for prohibited in ("方位", "方角", "吉方位", "行くべき", "必ず", "運気が上がる", "願いが叶う"):
        assert prohibited not in visible_reason
