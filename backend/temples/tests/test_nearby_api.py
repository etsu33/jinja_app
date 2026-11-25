"""`/api/shrines/nearby/`（`temples:nearby` → `NearestShrinesAPIView`）の現行契約。

マウントされているのはキーワード（`q`）で Google Places Text Search を呼ぶ互換 shim で、
緯度経度による近傍検索ではない（docs/audit/nearby-api-postgis-contract-audit-2026-10-31.md）。
`lat` / `lng` は使われない。Google Places への呼び出しはすべて差し替え、外部通信はしない。
"""

import pytest
from django.urls import resolve, reverse

from temples.api.views.shrine import NearestShrinesAPIView
from temples.services import places as places_service

pytestmark = pytest.mark.postgis  # PostGIS前提（marker 判定は conftest 側。ここでは変えない）

TEXT_SEARCH_PARAMS = {"language": "ja", "region": "jp"}


def url():
    return reverse("temples:nearby")


@pytest.fixture
def text_search(monkeypatch):
    """`places.places_text_search` を差し替え、呼び出しを記録する。"""
    calls = []
    response = {"results": []}

    def fake(params):
        calls.append(dict(params))
        return response

    monkeypatch.setattr(places_service, "places_text_search", fake)
    return calls, response


def _names(body):
    return [r["name"] for r in body["results"]]


def test_route_resolves_to_the_keyword_search_view():
    assert url() == "/api/shrines/nearby/"
    assert resolve(url()).func.cls is NearestShrinesAPIView


@pytest.mark.parametrize(
    "params",
    [
        pytest.param({}, id="no-params"),
        pytest.param({"q": ""}, id="empty-q"),
        pytest.param({"q": "宮"}, id="one-char-q"),
        pytest.param({"q": "   宮   "}, id="one-char-after-strip"),
        pytest.param({"lat": 35.6812, "lng": 139.7671, "limit": 10}, id="lat-lng-are-ignored"),
    ],
)
def test_missing_or_short_q_returns_empty_results_without_calling_places(
    client, text_search, params
):
    calls, _ = text_search

    r = client.get(url(), params)

    assert r.status_code == 200
    assert r.json() == {"results": []}
    assert calls == []


def test_valid_q_calls_text_search_and_returns_upstream_items_unchanged(client, text_search):
    calls, response = text_search
    item = {
        "name": "明治神宮",
        "place_id": "p-1",
        "formatted_address": "東京都渋谷区代々木神園町1-1",
    }
    response["results"] = [item]

    r = client.get(url(), {"q": "  明治神宮  "})

    assert r.status_code == 200
    assert calls == [{"query": "明治神宮", **TEXT_SEARCH_PARAMS}]
    # result mapping: upstream の要素はそのまま返す（フィールドの付け替え・削除なし）
    assert r.json() == {"results": [item]}


@pytest.mark.parametrize(
    "upstream",
    [
        pytest.param({"results": []}, id="empty-list"),
        pytest.param({}, id="no-results-key"),
        pytest.param(None, id="none"),
    ],
)
def test_empty_upstream_returns_empty_results(client, monkeypatch, upstream):
    monkeypatch.setattr(places_service, "places_text_search", lambda params: upstream)

    r = client.get(url(), {"q": "明治神宮"})

    assert r.status_code == 200
    assert r.json() == {"results": []}


@pytest.mark.parametrize(
    "limit,expected",
    [
        pytest.param(None, 5, id="default-5"),
        pytest.param("2", 2, id="explicit-2"),
        pytest.param("50", 10, id="capped-at-10"),
        pytest.param("0", 1, id="floored-at-1"),
    ],
)
def test_limit_defaults_to_five_and_is_clamped_between_one_and_ten(
    client, text_search, limit, expected
):
    _, response = text_search
    response["results"] = [{"name": f"候補{i:02d}"} for i in range(12)]
    params = {"q": "候補"}
    if limit is not None:
        params["limit"] = limit

    r = client.get(url(), params)

    assert r.status_code == 200
    assert len(r.json()["results"]) == expected


def test_full_rerank_when_the_top_result_is_not_a_parent_match(client, text_search):
    """クエリに親語（神社・宮など）が無いので、全件をスコア順に並べ替える。"""
    _, response = text_search
    response["results"] = [
        {"name": "渋谷駅"},
        {"name": "代々木公園"},
        {"name": "代々木八幡宮"},
    ]

    r = client.get(url(), {"q": "代々木 公園"})

    assert _names(r.json()) == ["代々木公園", "代々木八幡宮", "渋谷駅"]


def test_parent_top_result_keeps_google_order_except_the_best_match(client, text_search):
    """Google のトップが親語を含むときは、最良の 1 件だけ先頭に上げ、残りは Google 順を保つ。"""
    _, response = text_search
    response["results"] = [
        {"name": "明治神宮前駅"},
        {"name": "代々木公園"},
        {"name": "明治神宮", "formatted_address": "東京都渋谷区代々木神園町1-1 明治神宮"},
        {"name": "表参道"},
    ]

    r = client.get(url(), {"q": "明治神宮"})

    assert _names(r.json()) == ["明治神宮", "明治神宮前駅", "代々木公園", "表参道"]
