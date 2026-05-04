                       

# -*- coding: utf-8 -*-
import pytest

from temples.services.concierge_chat import build_chat_recommendations


@pytest.mark.django_db
def test_breakdown_score_total_is_contract_value_but_sort_uses_ranked_score(monkeypatch):
    """
    CR-003:
    APIの breakdown.score_total は契約用スコア。
    実際の並び順は rec['_score_total']（内部ランキング用）で決まる。

    つまり:
      - A/B の breakdown.score_total は同じ
      - ただし matched_by_tag の強さ差で A が上に来る
    という状態を固定する。
    """

    candidates = [
        {
            "id": 1,
            "shrine_id": 1,
            "name": "TAG優先神社",
            "distance_m": 1000,
            "astro_tags": ["career"],  # matched_by_tag=1 -> rank_raw=2
            "goriyaku": "",
            "description": "",
            "astro_elements": [],
            "popular_score": 0,
        },
        {
            "id": 2,
            "shrine_id": 2,
            "name": "TEXT優先神社",
            "distance_m": 1000,
            "astro_tags": [],          # matched_by_tag=0
            "goriyaku": "仕事運",       # matched_by_text=1 -> rank_raw=1
            "description": "",
            "astro_elements": [],
            "popular_score": 0,
        },
    ]

    recs = build_chat_recommendations(
        query="仕事で良い流れをつかみたい",
        language="ja",
        candidates=candidates,
        birthdate=None,
        flow="A",
        need_tags=["career"],  # need抽出の揺れを固定
        llm_enabled=False,
    )

    top = recs["recommendations"]
    assert [x["name"] for x in top[:2]] == ["TAG優先神社", "TEXT優先神社"]

    by_name = {x["name"]: x for x in top}
    a = by_name["TAG優先神社"]
    b = by_name["TEXT優先神社"]

    # 契約上の need score はどちらも 1
    assert a["breakdown"]["score_need"] == 1
    assert b["breakdown"]["score_need"] == 1

    # 契約上の total も同じ
    assert a["breakdown"]["score_total"] == pytest.approx(0.3, rel=1e-6)
    assert b["breakdown"]["score_total"] == pytest.approx(0.3, rel=1e-6)

    # ただし内部ランキングでは tag一致の方が強い
    assert a["_score_total"] > b["_score_total"]

    # 差分理由が detail に残っていること
    assert a["breakdown_detail"]["features"]["need"]["rank_raw"] == 2
    assert b["breakdown_detail"]["features"]["need"]["rank_raw"] == 1


@pytest.mark.django_db
def test_visit_style_weight_can_reorder_same_need_strength_candidates(monkeypatch):
    """
    visit_style は補助軸として、need の強さが同じ候補同士の順位を微調整できる。

    ここでは両候補とも need は同じ強さに固定し、
    visit_style_tags の一致がある候補だけが _score_total で上に来ることを確認する。
    """

    candidates = [
        {
            "id": 1,
            "shrine_id": 1,
            "name": "通常候補神社",
            "distance_m": 1000,
            "astro_tags": ["money"],
            "goriyaku": "金運",
            "description": "",
            "astro_elements": [],
            "visit_style_tags": ["classic"],
            "popular_score": 0,
        },
        {
            "id": 2,
            "shrine_id": 2,
            "name": "静かな候補神社",
            "distance_m": 1000,
            "astro_tags": ["money"],
            "goriyaku": "金運",
            "description": "",
            "astro_elements": [],
            "visit_style_tags": ["quiet"],
            "popular_score": 0,
        },
    ]

    recs = build_chat_recommendations(
        query="金運を整えたい",
        language="ja",
        candidates=candidates,
        birthdate=None,
        flow="A",
        need_tags=["money"],
        extra_condition="静かな場所がいい",
        llm_enabled=False,
    )

    top = recs["recommendations"]
    assert [x["name"] for x in top[:2]] == ["静かな候補神社", "通常候補神社"]

    by_name = {x["name"]: x for x in top}
    quiet = by_name["静かな候補神社"]
    normal = by_name["通常候補神社"]

    # 契約上の need score は同じ
    assert quiet["breakdown"]["score_need"] == normal["breakdown"]["score_need"] == 1

    # visit_style は breakdown_detail にだけ寄与し、内部ランキングを微調整する
    assert quiet["breakdown_detail"]["features"]["visit_style"] == {
        "raw": 1,
        "weight": 0.35,
        "matched_tags": ["quiet"],
        "contribution": 0.35,
    }
    assert normal["breakdown_detail"]["features"]["visit_style"] == {
        "raw": 0,
        "weight": 0.35,
        "matched_tags": [],
        "contribution": 0.0,
    }
    assert quiet["_score_total"] > normal["_score_total"]


@pytest.mark.django_db
def test_visit_style_weight_does_not_override_stronger_need_match(monkeypatch):
    """
    visit_style は補助軸であり、より強い need 一致を上書きしない。

    need が2件一致している候補は、visit_style 一致がない場合でも、
    need が1件一致 + visit_style 一致の候補より上位を維持する。
    """

    candidates = [
        {
            "id": 1,
            "shrine_id": 1,
            "name": "悩み一致が強い神社",
            "distance_m": 1000,
            "astro_tags": ["money", "career"],
            "goriyaku": "金運・仕事運",
            "description": "",
            "astro_elements": [],
            "visit_style_tags": ["classic"],
            "popular_score": 0,
        },
        {
            "id": 2,
            "shrine_id": 2,
            "name": "静かさ一致の神社",
            "distance_m": 1000,
            "astro_tags": ["money"],
            "goriyaku": "金運",
            "description": "",
            "astro_elements": [],
            "visit_style_tags": ["quiet"],
            "popular_score": 0,
        },
    ]

    recs = build_chat_recommendations(
        query="金運と仕事運を整えたい",
        language="ja",
        candidates=candidates,
        birthdate=None,
        flow="A",
        need_tags=["money", "career"],
        extra_condition="静かな場所がいい",
        llm_enabled=False,
    )

    top = recs["recommendations"]
    assert [x["name"] for x in top[:2]] == ["悩み一致が強い神社", "静かさ一致の神社"]

    by_name = {x["name"]: x for x in top}
    strong_need = by_name["悩み一致が強い神社"]
    quiet = by_name["静かさ一致の神社"]

    assert strong_need["breakdown"]["score_need"] == 2
    assert quiet["breakdown"]["score_need"] == 1

    assert strong_need["breakdown_detail"]["features"]["visit_style"]["raw"] == 0
    assert quiet["breakdown_detail"]["features"]["visit_style"] == {
        "raw": 1,
        "weight": 0.35,
        "matched_tags": ["quiet"],
        "contribution": 0.35,
    }

    assert strong_need["_score_total"] > quiet["_score_total"]
