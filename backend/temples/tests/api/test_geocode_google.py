"""出発地点の地名検索（Google の Geocoding API v3）の契約。

- Google を実際には呼ばない（requests_mock で返事を作る）。
- 外部のエラー・鍵なしでも 500 にせず、200 で候補なしを返す。
- 鍵の値・相談の言葉はログに出さない。上限・鍵の誤りはログの outcome で見分けられる。
- 保存・最低文字数・1分あたりの上限・一時停止で、Google を呼ぶ回数を抑える。
- 逆の検索は外部を呼ばず item: null を返す。
"""

from __future__ import annotations

import logging

import pytest
import requests
from django.core.cache import cache

from temples.services import geocode as svc

GOOGLE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
FAKE_KEY = "FAKE_GOOGLE_MAPS_KEY_FOR_GEOCODE_TEST"
SEARCH_URL = "/api/geocodes/search/"


def _component(long_name, short_name=None, types=()):
    return {"long_name": long_name, "short_name": short_name or long_name, "types": list(types)}


TOKYO_STATION = {
    "place_id": "PID_TOKYO_STATION",
    "formatted_address": "日本、〒100-0005 東京都千代田区丸の内１丁目",
    "types": ["establishment", "point_of_interest", "train_station", "transit_station"],
    "geometry": {"location": {"lat": 35.6812362, "lng": 139.7671248}},
    "address_components": [
        _component("東京駅", types=["establishment", "point_of_interest", "train_station", "transit_station"]),
        _component("千代田区", types=["locality", "political"]),
        _component("日本", "JP", ["country", "political"]),
    ],
}
SHIBUYA_WARD = {
    "place_id": "PID_SHIBUYA",
    "formatted_address": "日本、東京都渋谷区",
    "types": ["locality", "political"],
    "geometry": {"location": {"lat": 35.6619707, "lng": 139.703795}},
    "address_components": [
        _component("渋谷区", types=["locality", "political"]),
        _component("日本", "JP", ["country", "political"]),
    ],
}
TOKYO_STATION_EN = {
    "place_id": "PID_TOKYO_STATION",
    "formatted_address": "1 Chome Marunouchi, Chiyoda City, Tokyo 100-0005, Japan",
    "types": ["establishment", "point_of_interest", "train_station", "transit_station"],
    "geometry": {"location": {"lat": 35.6812362, "lng": 139.7671248}},
    "address_components": [
        _component("Tokyo Station", types=["establishment", "point_of_interest", "train_station", "transit_station"]),
        _component("Japan", "JP", ["country", "political"]),
    ],
}
FOREIGN_RESULT = {
    "place_id": "PID_FOREIGN",
    "formatted_address": "Shibuya, Somewhere, USA",
    "types": ["locality", "political"],
    "geometry": {"location": {"lat": 40.0, "lng": -75.0}},
    "address_components": [_component("United States", "US", ["country", "political"])],
}


@pytest.fixture(autouse=True)
def _fresh_state(monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", FAKE_KEY)
    cache.clear()
    svc.reset_state_for_tests()
    yield
    cache.clear()
    svc.reset_state_for_tests()


def _google(requests_mock, *, results=(), status="OK", http_status=200, exc=None):
    if exc is not None:
        return requests_mock.get(GOOGLE_URL, exc=exc)
    return requests_mock.get(GOOGLE_URL, json={"status": status, "results": list(results)}, status_code=http_status)


def _logged(caplog) -> str:
    return "\n".join(record.getMessage() for record in caplog.records)


# ---------- 候補の形 ----------


def test_station_result_keeps_the_response_shape(client, requests_mock):
    _google(requests_mock, results=[TOKYO_STATION])
    resp = client.get(SEARCH_URL, {"q": "東京駅", "limit": 5, "lang": "ja"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "google"
    assert body["cached"] is False
    item = body["items"][0]
    assert {k: item[k] for k in ("place_id", "name", "lat", "lng", "type")} == {
        "place_id": "PID_TOKYO_STATION",
        "name": "東京駅",
        "lat": 35.6812362,
        "lng": 139.7671248,
        "type": "station",
    }


def test_address_result_uses_the_cleaned_formatted_address(client, requests_mock):
    _google(requests_mock, results=[SHIBUYA_WARD])
    item = client.get(SEARCH_URL, {"q": "渋谷"}).json()["items"][0]
    assert item["name"] == "東京都渋谷区"
    assert item["type"] == "address"


def test_language_follows_the_lang_parameter(client, requests_mock):
    mock = _google(requests_mock, results=[TOKYO_STATION_EN])
    item = client.get(SEARCH_URL, {"q": "Tokyo Station", "lang": "en"}).json()["items"][0]
    query = mock.last_request.qs
    assert query["language"] == ["en"]
    assert query["region"] == ["jp"]
    assert query["address"] == ["tokyo station"]  # requests_mock は qs を小文字にする
    assert item["name"] == "Tokyo Station"
    assert item["type"] == "station"


def test_japanese_lang_is_sent_as_is(client, requests_mock):
    mock = _google(requests_mock, results=[TOKYO_STATION])
    client.get(SEARCH_URL, {"q": "Tokyo Station", "lang": "ja"})
    assert mock.last_request.qs["language"] == ["ja"]


def test_japan_results_come_first_and_limit_applies(client, requests_mock):
    _google(requests_mock, results=[FOREIGN_RESULT, SHIBUYA_WARD, TOKYO_STATION])
    items = client.get(SEARCH_URL, {"q": "渋谷", "limit": 2}).json()["items"]
    assert [i["place_id"] for i in items] == ["PID_SHIBUYA", "PID_TOKYO_STATION"]


def test_results_without_location_or_place_id_are_skipped(client, requests_mock):
    broken = dict(SHIBUYA_WARD, place_id=None)
    no_location = dict(TOKYO_STATION, geometry={})
    _google(requests_mock, results=[broken, no_location, TOKYO_STATION])
    items = client.get(SEARCH_URL, {"q": "東京駅"}).json()["items"]
    assert [i["place_id"] for i in items] == ["PID_TOKYO_STATION"]


# ---------- エラーでも 200 で候補なし ----------


@pytest.mark.parametrize(
    "kwargs,outcome",
    [
        ({"status": "OVER_QUERY_LIMIT"}, "quota_exceeded"),
        ({"status": "OVER_DAILY_LIMIT"}, "quota_exceeded"),
        ({"status": "REQUEST_DENIED"}, "request_denied"),
        ({"status": "INVALID_REQUEST"}, "invalid_request"),
        ({"status": "UNKNOWN_ERROR"}, "unknown_error"),
        ({"http_status": 403}, "request_denied"),
        ({"http_status": 429}, "quota_exceeded"),
        ({"http_status": 500}, "http_error"),
        ({"exc": requests.exceptions.ConnectTimeout}, "timeout"),
        ({"exc": requests.exceptions.ConnectionError}, "network_error"),
    ],
)
def test_external_errors_return_empty_items_with_200(client, requests_mock, caplog, kwargs, outcome):
    _google(requests_mock, **kwargs)
    with caplog.at_level(logging.INFO):
        resp = client.get(SEARCH_URL, {"q": "東京駅"})
    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert f"outcome={outcome}" in _logged(caplog)


def test_bad_json_returns_empty_items(client, requests_mock, caplog):
    requests_mock.get(GOOGLE_URL, text="not json", status_code=200)
    with caplog.at_level(logging.INFO):
        resp = client.get(SEARCH_URL, {"q": "東京駅"})
    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert "outcome=bad_response" in _logged(caplog)


def test_missing_key_returns_empty_without_calling_google(client, requests_mock, monkeypatch, caplog, settings):
    for name in ("GOOGLE_MAPS_API_KEY", "GOOGLE_API_KEY", "MAPS_API_KEY", "PLACES_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    settings.GOOGLE_MAPS_API_KEY = ""
    settings.GOOGLE_API_KEY = ""
    mock = _google(requests_mock, results=[TOKYO_STATION])
    with caplog.at_level(logging.INFO):
        resp = client.get(SEARCH_URL, {"q": "東京駅"})
    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert mock.call_count == 0
    assert "outcome=missing_key" in _logged(caplog)


def test_zero_results_returns_empty_and_is_cached(client, requests_mock):
    mock = _google(requests_mock, status="ZERO_RESULTS")
    assert client.get(SEARCH_URL, {"q": "あいうえおかきくけこ"}).json()["items"] == []
    assert client.get(SEARCH_URL, {"q": "あいうえおかきくけこ"}).json()["cached"] is True
    assert mock.call_count == 1


def test_errors_are_not_cached(client, requests_mock):
    mock = _google(requests_mock, status="UNKNOWN_ERROR")
    client.get(SEARCH_URL, {"q": "東京駅"})
    client.get(SEARCH_URL, {"q": "東京駅"})
    assert mock.call_count == 2


# ---------- 鍵と相談の言葉をログに出さない ----------
# 本番のログの水準（settings.LOGGING の root）は INFO。HTTP の部品（urllib3 など）の DEBUG の
# 記録は本番では出ないため、本番と同じ INFO で確かめる。


def test_key_and_query_are_not_logged_on_connection_error(client, requests_mock, caplog):
    secret_query = "東京都_SECRET_QUERY_MARKER"
    _google(
        requests_mock,
        exc=requests.exceptions.ConnectionError(f"Max retries exceeded with url: /geocode/json?key={FAKE_KEY}&address=x"),
    )
    with caplog.at_level(logging.INFO):
        resp = client.get(SEARCH_URL, {"q": secret_query})
    assert resp.status_code == 200
    text = _logged(caplog)
    assert FAKE_KEY not in text
    assert secret_query not in text
    assert "outcome=network_error" in text


def test_google_error_message_is_not_logged(client, requests_mock, caplog):
    requests_mock.get(
        GOOGLE_URL,
        json={"status": "REQUEST_DENIED", "results": [], "error_message": f"bad key {FAKE_KEY}"},
        status_code=200,
    )
    with caplog.at_level(logging.INFO):
        client.get(SEARCH_URL, {"q": "東京駅"})
    text = _logged(caplog)
    assert FAKE_KEY not in text
    assert "outcome=request_denied" in text


# ---------- 呼ぶ回数を抑える ----------


def test_same_query_uses_the_cache(client, requests_mock):
    mock = _google(requests_mock, results=[TOKYO_STATION_EN])
    first = client.get(SEARCH_URL, {"q": "Tokyo Station", "lang": "en"}).json()
    second = client.get(SEARCH_URL, {"q": "  tokyo　station ", "lang": "en"}).json()
    assert mock.call_count == 1
    assert first["cached"] is False and second["cached"] is True
    assert second["items"] == first["items"]


def test_cache_is_separate_per_lang(client, requests_mock):
    mock = _google(requests_mock, results=[TOKYO_STATION])
    client.get(SEARCH_URL, {"q": "Tokyo Station", "lang": "ja"})
    client.get(SEARCH_URL, {"q": "Tokyo Station", "lang": "en"})
    assert mock.call_count == 2


def test_cache_ttl_never_exceeds_30_days():
    assert svc.CACHE_TTL_S <= 60 * 60 * 24 * 30


@pytest.mark.parametrize("q", ["東", "To", "a b", " 　"])
def test_too_short_queries_do_not_call_google(client, requests_mock, q):
    mock = _google(requests_mock, results=[TOKYO_STATION])
    resp = client.get(SEARCH_URL, {"q": q})
    assert resp.status_code in (200, 400)  # 空白だけは入力の検査で 400 になる
    if resp.status_code == 200:
        assert resp.json()["items"] == []
    assert mock.call_count == 0


def test_two_character_japanese_query_calls_google(client, requests_mock):
    mock = _google(requests_mock, results=[SHIBUYA_WARD])
    client.get(SEARCH_URL, {"q": "渋谷"})
    assert mock.call_count == 1


def test_per_minute_cap_stops_calling_google(requests_mock, monkeypatch, caplog):
    monkeypatch.setattr(svc, "GOOGLE_CALLS_PER_MIN", 2)
    mock = _google(requests_mock, results=[TOKYO_STATION])
    with caplog.at_level(logging.INFO):
        results = [svc.geocode_search(q=f"東京駅{i}") for i in range(3)]
    assert mock.call_count == 2
    assert results[2] == {"items": [], "cached": False, "provider": "throttled"}
    assert "reason=per_minute_cap" in _logged(caplog)


@pytest.mark.parametrize("status", ["OVER_QUERY_LIMIT", "REQUEST_DENIED"])
def test_quota_or_denied_pauses_google_calls(requests_mock, caplog, status):
    mock = _google(requests_mock, status=status)
    with caplog.at_level(logging.INFO):
        first = svc.geocode_search(q="東京駅")
        second = svc.geocode_search(q="渋谷駅")
    assert mock.call_count == 1
    assert first["items"] == [] and second == {"items": [], "cached": False, "provider": "paused"}
    assert "google_paused" in _logged(caplog)


def test_pause_ends_after_the_pause_period(requests_mock, monkeypatch):
    clock = [1_000_000.0]
    monkeypatch.setattr(svc.time, "time", lambda: clock[0])
    _google(requests_mock, status="OVER_QUERY_LIMIT")
    svc.geocode_search(q="東京駅")
    clock[0] += svc.PAUSE_AFTER_FAILURE_S + 1
    mock = _google(requests_mock, results=[TOKYO_STATION])
    assert svc.geocode_search(q="渋谷駅")["provider"] == "google"
    assert mock.call_count == 1


def test_daily_count_is_logged_per_google_call(requests_mock, caplog):
    _google(requests_mock, results=[TOKYO_STATION])
    with caplog.at_level(logging.INFO):
        svc.geocode_search(q="東京駅")
        svc.geocode_search(q="東京駅")  # 2回目は保存済みの結果なので数えない
        svc.geocode_search(q="渋谷駅")
    counts = [line for line in _logged(caplog).splitlines() if "google_call" in line]
    assert len(counts) == 2
    assert "count_today=1" in counts[0] and "count_today=2" in counts[1]


# ---------- 入力の整え ----------


@pytest.mark.parametrize("lang,expected", [("ja", "ja"), ("EN", "en"), ("zh_TW", "zh-tw"), ("", "ja"), ("x;y", "ja")])
def test_normalize_lang(lang, expected):
    assert svc.normalize_lang(lang) == expected


# ---------- 逆の検索 ----------


def test_reverse_returns_null_without_calling_anything(client, requests_mock):
    resp = client.get("/api/geocodes/reverse/", {"lat": 35.68, "lng": 139.76, "lang": "ja"})
    assert resp.status_code == 200
    assert resp.json() == {"item": None, "cached": False, "provider": "disabled"}
    assert requests_mock.call_count == 0


def test_legacy_paths_still_work(client, requests_mock):
    _google(requests_mock, results=[TOKYO_STATION])
    assert client.get("/api/geocode/search/", {"q": "東京駅"}).json()["items"][0]["type"] == "station"
    assert client.get("/api/geocode/reverse/", {"lat": 35.68, "lng": 139.76}).json()["item"] is None


# ---------- Nominatim を使わない ----------


def test_nominatim_is_not_referenced():
    import inspect

    source = inspect.getsource(svc)
    assert "nominatim.openstreetmap.org" not in source
    assert "NOMINATIM_BASE" not in source and "NOMINATIM_EMAIL" not in source
