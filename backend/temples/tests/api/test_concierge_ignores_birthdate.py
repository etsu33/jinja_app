"""コンシェルジュでは生年月日を使わない（生年月日との相性はコンパスの役割）。

相談の API（/api/concierge/chat/）のビューの入り口で、生年月日に関わる入力を外す:
- 本文の birthdate・filters.birthdate・日付だけの相談文
- profile_context.user_profile の生年月日・出生時刻・出生地
- profile_context の derived_profile（九星・五行・ライフパス）・direction_profile
- mode: "compat"（相性モード）

順位付けの共通部分（build_chat_recommendations）は変えない。コンパスは今までどおり生年月日を使う。
"""

from __future__ import annotations

import json
import logging

import pytest
from django.test import Client

from temples.models import Shrine
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_input_contract import (
    concierge_birthdate_request_sources,
    strip_concierge_profile_context_birthdate,
)
from temples.tests.support.recommendation_eligibility import attach_usable_deity_fact

TOKYO = {"lat": 35.681236, "lng": 139.767125}
BIRTHDATE = "1990-07-15"
PROFILE_CONTEXT = {
    "user_profile": {
        "birthday": BIRTHDATE,
        "birthdate": BIRTHDATE,
        "birthTime": "07:30",
        "birthPlace": "東京都",
    },
    "derived_profile": {"kyusei": "一白水星", "gogyo": "水", "lifePath": "5"},
    "direction_profile": {"luckyDirection": "南", "luckyDirections": ["南"], "source": "calculated"},
}


def _shrine(name: str, *, lat: float, lng: float, visit_style_tags: list[str], astro_elements: list[str]) -> Shrine:
    shrine = Shrine.objects.create(
        name_jp=name,
        address=f"東京都千代田区{name}",
        latitude=lat,
        longitude=lng,
        visit_style_tags=visit_style_tags,
        astro_elements=astro_elements,
    )
    attach_usable_deity_fact(shrine, display_name=f"{name}の祭神")
    return shrine


@pytest.fixture
def shrines(db, settings):
    settings.CONCIERGE_USE_LLM = False
    return [
        _shrine("近くの静かな神社", lat=35.6900, lng=139.7700, visit_style_tags=["quiet"], astro_elements=["風"]),
        _shrine("近くの街の神社", lat=35.6830, lng=139.7680, visit_style_tags=["urban"], astro_elements=["火"]),
        _shrine("遠くの杜の神社", lat=35.9000, lng=139.2000, visit_style_tags=["nature"], astro_elements=["水", "土"]),
    ]


def _post(body: dict):
    return Client().post(
        "/api/concierge/chat/", data=json.dumps(body), content_type="application/json", HTTP_HOST="localhost"
    )


def _view(response) -> dict:
    """比べる部分（順位・点数・主な根拠・説明の文・見出し）。"""
    data = response.json()["data"]
    recs = data["recommendations"]
    return {
        "mode": data.get("_meta", {}).get("mode") if isinstance(data.get("_meta"), dict) else data.get("mode"),
        "recs": [
            {
                "name": rec["name"],
                "score": rec.get("_score_total"),
                "primary": (rec.get("_primary_reason_source"), rec.get("_primary_reason_label")),
                "reason": rec.get("reason"),
                "reason_facts": rec.get("reason_facts"),
                "explanation": rec.get("explanation"),
                "rank_summary": (rec.get("rank_explanation") or {}).get("summary"),
                "interpretation": ((rec.get("recommendation_reason_v4_detail") or {}).get("interpretation") or {}).get(
                    "text"
                ),
                "score_element": (rec.get("breakdown") or {}).get("score_element"),
                "profile_signal": (rec.get("breakdown") or {}).get("profile_signal"),
            }
            for rec in recs
        ],
    }


# ---------- 入力の外し方 ----------


def test_strip_profile_context_removes_birth_and_derived_fields():
    cleaned, counts = strip_concierge_profile_context_birthdate(
        {**PROFILE_CONTEXT, "user_profile": {**PROFILE_CONTEXT["user_profile"], "nickname": "x"}, "other": 1}
    )
    assert cleaned == {"user_profile": {"nickname": "x"}, "other": 1}
    assert counts == {"profile_user_birth": 4, "profile_derived": 2}


def test_strip_profile_context_drops_empty_user_profile_and_handles_none():
    cleaned, counts = strip_concierge_profile_context_birthdate(PROFILE_CONTEXT)
    assert cleaned == {}
    assert counts["profile_user_birth"] == 4
    assert strip_concierge_profile_context_birthdate(None) == (None, {"profile_user_birth": 0, "profile_derived": 0})


def test_request_sources_detect_body_and_filters():
    assert concierge_birthdate_request_sources({"birthdate": BIRTHDATE}) == {"body": True, "filters": False}
    assert concierge_birthdate_request_sources({"filters": {"birthdate": BIRTHDATE}}) == {"body": False, "filters": True}
    assert concierge_birthdate_request_sources({"birthdate": ""}) == {"body": False, "filters": False}


# ---------- 相談の API ----------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "extra",
    [
        {"birthdate": BIRTHDATE},
        {"filters": {"birthdate": BIRTHDATE}},
        {"profile_context": PROFILE_CONTEXT},
        {"mode": "compat"},
        {
            "birthdate": BIRTHDATE,
            "filters": {"birthdate": BIRTHDATE},
            "profile_context": PROFILE_CONTEXT,
            "mode": "compat",
        },
    ],
)
def test_birthdate_inputs_do_not_change_ranking_or_copy(shrines, extra):
    base = {"query": "休みたい", **TOKYO}
    plain = _post(base)
    with_birthdate = _post({**base, **extra})
    assert plain.status_code == with_birthdate.status_code == 200
    assert _view(with_birthdate) == _view(plain)


@pytest.mark.django_db
def test_response_has_no_birthdate_copy_even_with_birthdate(shrines):
    response = _post(
        {
            "query": "休みたい",
            **TOKYO,
            "birthdate": BIRTHDATE,
            "filters": {"birthdate": BIRTHDATE},
            "profile_context": PROFILE_CONTEXT,
            "mode": "compat",
        }
    )
    data = response.json()["data"]
    for rec in data["recommendations"]:
        # rank_explanation.contributors は、全部の項目（生年月日を含む）を0点でも並べる内部の一覧で、
        # Web・モバイルは表示しない（表示するのは summary と primary_axis_ja）。表示する文だけを見る。
        (rec.get("rank_explanation") or {}).pop("contributors", None)
    body = json.dumps(data, ensure_ascii=False)
    for word in ("生年月日", "相性", "誕生日"):
        assert word not in body
    for rec in response.json()["data"]["recommendations"]:
        assert rec["breakdown"]["score_element"] == 0
        assert rec["breakdown"]["profile_signal"]["score"] == 0.0
        assert rec["_primary_reason_source"] != "element"


@pytest.mark.django_db
def test_date_only_query_is_not_used_as_a_birthdate(shrines):
    response = _post({"query": BIRTHDATE, **TOKYO})
    assert response.status_code == 400  # 相談の文が無い扱い（生年月日だけでは相談にしない）


@pytest.mark.django_db
def test_ignored_inputs_are_logged_as_counts_only(shrines, caplog):
    with caplog.at_level(logging.INFO):
        _post(
            {
                "query": "休みたい",
                **TOKYO,
                "birthdate": BIRTHDATE,
                "filters": {"birthdate": BIRTHDATE},
                "profile_context": PROFILE_CONTEXT,
                "mode": "compat",
            }
        )
    lines = [r.getMessage() for r in caplog.records if "[concierge/birthdate_ignored]" in r.getMessage()]
    assert len(lines) == 1
    assert "body=1 filters=1 query_date=0 profile_user_birth=4 profile_derived=2 mode_compat=1" in lines[0]
    all_text = "\n".join(r.getMessage() for r in caplog.records)
    for secret in (BIRTHDATE, "1990", "07:30", "一白水星"):
        assert secret not in all_text


@pytest.mark.django_db
def test_no_ignored_log_without_birthdate_inputs(shrines, caplog):
    with caplog.at_level(logging.INFO):
        _post({"query": "休みたい", **TOKYO})
    assert not [r for r in caplog.records if "[concierge/birthdate_ignored]" in r.getMessage()]


# ---------- 共通部分とコンパスは変えない ----------


@pytest.mark.django_db
def test_shared_ranking_still_uses_birthdate_when_called_with_it(shrines):
    """コンパスが使う共通部分（build_chat_recommendations）は、生年月日を渡せば今までどおり使う。"""
    candidate = {
        "id": 1, "shrine_id": 1, "name": "水の神社", "address": "東京都", "lat": 35.68, "lng": 139.76,
        "distance_m": None, "goriyaku": "", "description": "", "astro_tags": [], "astro_elements": ["水", "土"],
        "goriyaku_tag_ids": [], "goriyaku_tag_names": [], "visit_style_tags": [], "popular_score": 0.0,
    }
    with_birthdate = build_chat_recommendations(
        query="休みたい", language="ja", candidates=[dict(candidate)], birthdate="1990-07-15", llm_enabled=False
    )["recommendations"][0]
    without = build_chat_recommendations(
        query="休みたい", language="ja", candidates=[dict(candidate)], llm_enabled=False
    )["recommendations"][0]
    assert with_birthdate["breakdown"]["score_element"] > 0
    assert without["breakdown"]["score_element"] == 0


@pytest.mark.django_db
def test_compass_view_still_passes_birthdate(monkeypatch):
    captured = {}

    def _capture(*, birthdate, target_date):
        captured["birthdate"] = birthdate
        raise RuntimeError("stop after capturing")

    monkeypatch.setattr("temples.api_views_compass.build_compass_direction_runtime", _capture)
    Client().post(
        "/api/compass/recommendations/",
        data=json.dumps({"purpose": "rest", "birthdate": BIRTHDATE}),
        content_type="application/json",
        HTTP_HOST="localhost",
    )
    assert captured["birthdate"] == BIRTHDATE
