# temples/services/geocode.py
"""出発地点の地名検索（/api/geocodes/search/）と逆の検索（/api/geocodes/reverse/）。

検索は Google の Geocoding API（v3、maps/api/geocode/json）を使う。
（以前は Nominatim を使っていたが、403 を処理せず 500 になっていたため置き換えた。）

- 外部のエラー（403・429・OVER_QUERY_LIMIT・REQUEST_DENIED・タイムアウトなど）や鍵が無いときは、
  例外を出さず「候補なし」（items: []）を返す。上限・鍵の誤りはログの outcome で見分ける。
- 連打で費用が増えないように:
  - 同じ言葉の結果は保存して使い回す（最長30日。GEOCODE_CACHE_TTL_S で短くはできるが、30日は超えない）
  - 短すぎる言葉では Google を呼ばない
  - Google を実際に呼ぶ回数を、1分あたりの上限で抑える（プロセスごと）
  - 上限・拒否の返事を受けたら、しばらく Google を呼ばない（プロセスごと）
  - 利用者ごとの上限は、入り口の throttle（scope "geocode"）がそのまま受け持つ
- 保存・上限・回数はプロセスのメモリ（LocMemCache とこのモジュールの変数）にあるため、
  再起動で消え、プロセスごとに別になる。本当の回数は Google Cloud の指標で見る。

逆の検索は、アプリの画面から呼ばれていないため、外部を呼ばず item: null を返す。
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import threading
import time
import unicodedata
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from temples.geocoding.client import google_geocode_search

logger = logging.getLogger(__name__)

PROVIDER = "google"

# 保存の期間。Google の利用の決まりでは、緯度・経度を一時的に保存してよい期間は30日まで
# （place_id は期限なし）。設定で短くはできるが、30日は超えない。
MAX_CACHE_TTL_S = 60 * 60 * 24 * 30
CACHE_TTL_S = min(int(getattr(settings, "GEOCODE_CACHE_TTL_S", MAX_CACHE_TTL_S)), MAX_CACHE_TTL_S)

# Google を実際に呼ぶ回数の上限（1分あたり、プロセスごと）。保存済みの結果を返すときは数えない。
GOOGLE_CALLS_PER_MIN = int(getattr(settings, "GEOCODE_GOOGLE_CALLS_PER_MIN", 10))
WINDOW_S = 60

# 上限・拒否の返事を受けたあと、Google を呼ばない時間（プロセスごと）。
PAUSE_AFTER_FAILURE_S = 600
PAUSE_OUTCOMES = frozenset({"quota_exceeded", "request_denied"})

# 保存してよい結果（失敗は保存しない）。
CACHEABLE_OUTCOMES = frozenset({"ok", "zero_results"})

# 短すぎる言葉では Google を呼ばない。英数字だけの言葉は少し長めにする（"To" などで呼ばない）。
MIN_QUERY_LENGTH = 2
MIN_ASCII_QUERY_LENGTH = 3

GOOGLE_TIMEOUT_S = 6.0
DEFAULT_LANG = "ja"
_LANG_RE = re.compile(r"^[a-z]{2,3}(?:-[a-z0-9]{2,8})?$")

# 駅として扱う Google の種類（画面は type == "station" のとき出発地点の種類を駅にする）。
STATION_TYPES = frozenset({"train_station", "subway_station", "transit_station", "light_rail_station"})
# 施設・駅などで、住所ではなく名前を出したい種類。
NAMED_PLACE_TYPES = STATION_TYPES | frozenset(
    {"establishment", "point_of_interest", "premise", "natural_feature", "park", "airport"}
)
_POSTAL_RE = re.compile(r"〒?\s*\d{3}-\d{4}\s*")

_lock = threading.Lock()
_call_times: List[float] = []
_paused_until = 0.0
_daily_counts: Dict[str, int] = {}


# ---------------------------------------------------------------- 入力の整え


def normalize_query(q: Any) -> str:
    """前後の空白・全角半角をそろえ、間の空白を1つにする（Google へ送る言葉）。"""
    text = unicodedata.normalize("NFKC", str(q or ""))
    return re.sub(r"\s+", " ", text).strip()


def normalize_lang(lang: Any) -> str:
    """画面から送られる lang に従う。形がおかしいときだけ既定（ja）にする。"""
    text = str(lang or "").strip().lower().replace("_", "-")
    return text if _LANG_RE.match(text) else DEFAULT_LANG


def is_query_too_short(query: str) -> bool:
    if len(query) < MIN_QUERY_LENGTH:
        return True
    return query.isascii() and len(query.replace(" ", "")) < MIN_ASCII_QUERY_LENGTH


def _cache_key(query: str, lang: str) -> str:
    # 英字の大小もそろえる（"Tokyo station" と "tokyo Station" を同じ扱いにする）。
    payload = {"q": query.casefold(), "lang": lang}
    digest = hashlib.sha1(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return f"geocode:google:search:{digest}"


# ---------------------------------------------------------------- 上限・一時停止・回数


def _is_paused(now: float) -> bool:
    return now < _paused_until


def _pause(now: float, outcome: str) -> None:
    global _paused_until
    _paused_until = now + PAUSE_AFTER_FAILURE_S
    logger.warning("[geocode] google_paused outcome=%s seconds=%d", outcome, PAUSE_AFTER_FAILURE_S)


def _take_call_slot(now: float) -> bool:
    while _call_times and now - _call_times[0] > WINDOW_S:
        _call_times.pop(0)
    if len(_call_times) >= GOOGLE_CALLS_PER_MIN:
        return False
    _call_times.append(now)
    return True


def _count_call_today() -> tuple[str, int]:
    """その日の何回目か（メモリで数える。再起動で0に戻り、プロセスごとに別）。"""
    day = timezone.localdate().isoformat()
    for old in [d for d in _daily_counts if d != day]:
        del _daily_counts[old]
    _daily_counts[day] = _daily_counts.get(day, 0) + 1
    return day, _daily_counts[day]


def reset_state_for_tests() -> None:
    """テスト用: 上限・一時停止・回数を初期化する。"""
    global _paused_until
    with _lock:
        _call_times.clear()
        _daily_counts.clear()
        _paused_until = 0.0


# ---------------------------------------------------------------- 候補の形


def _components(result: dict) -> list:
    comps = result.get("address_components")
    return comps if isinstance(comps, list) else []


def _country_code(result: dict) -> Optional[str]:
    for comp in _components(result):
        if isinstance(comp, dict) and "country" in (comp.get("types") or []):
            return str(comp.get("short_name") or "").upper() or None
    return None


def _clean_formatted_address(text: str) -> str:
    text = str(text or "").strip()
    for prefix in ("日本、", "日本 "):
        if text.startswith(prefix):
            text = text[len(prefix):]
    if text.endswith(", Japan"):
        text = text[: -len(", Japan")]
    return _POSTAL_RE.sub("", text).strip(" ,、")


def _display_name(result: dict, types: set) -> Optional[str]:
    """駅・施設なら施設名、住所なら住所（「日本、」と郵便番号を除く）。"""
    if types & NAMED_PLACE_TYPES:
        for comp in _components(result):
            if not isinstance(comp, dict):
                continue
            comp_types = set(comp.get("types") or [])
            if comp_types & NAMED_PLACE_TYPES and comp.get("long_name"):
                return str(comp["long_name"])
    formatted = _clean_formatted_address(result.get("formatted_address") or "")
    return formatted or None


def _to_item(result: Any) -> Optional[dict]:
    if not isinstance(result, dict):
        return None
    location = (result.get("geometry") or {}).get("location") or {}
    lat, lng = location.get("lat"), location.get("lng")
    place_id = result.get("place_id")
    if lat is None or lng is None or not place_id:
        return None
    types = {str(t) for t in (result.get("types") or []) if isinstance(t, str)}
    item = {
        "place_id": str(place_id),
        "name": _display_name(result, types),
        "lat": float(lat),
        "lng": float(lng),
        "type": "station" if types & STATION_TYPES else "address",
    }
    formatted = str(result.get("formatted_address") or "").strip()
    if formatted:
        item["address"] = {"formatted": formatted}
    return item


def build_items(results: list, *, limit: int) -> list:
    """Google の候補を返す形にする。日本の候補を先に並べる（それ以外は Google の順のまま）。"""
    ordered = sorted(
        (r for r in results if isinstance(r, dict)),
        key=lambda r: 0 if _country_code(r) == "JP" else 1,
    )
    items = [item for item in (_to_item(r) for r in ordered) if item is not None]
    return items[: max(1, int(limit))]


# ---------------------------------------------------------------- 入り口


def _empty(provider: str) -> dict:
    return {"items": [], "cached": False, "provider": provider}


def geocode_search(q: str, limit: int = 5, lang: str = DEFAULT_LANG) -> dict:
    """地名・住所の候補を返す。外部のエラーでも例外を出さず、候補なしを返す。"""
    query = normalize_query(q)
    lang_code = normalize_lang(lang)
    if is_query_too_short(query):
        return _empty("skipped")

    key = _cache_key(query, lang_code)
    hit = cache.get(key)
    if hit is not None:
        return {"items": list(hit)[: max(1, int(limit))], "cached": True, "provider": PROVIDER}

    now = time.time()
    with _lock:
        if _is_paused(now):
            logger.info("[geocode] google_skipped reason=paused query_length=%d", len(query))
            return _empty("paused")
        if not _take_call_slot(now):
            logger.warning("[geocode] google_skipped reason=per_minute_cap cap=%d", GOOGLE_CALLS_PER_MIN)
            return _empty("throttled")
        day, count_today = _count_call_today()
    logger.info("[geocode] google_call day=%s count_today=%d (memory, per process)", day, count_today)

    response = google_geocode_search(query, language=lang_code, region="jp", timeout=GOOGLE_TIMEOUT_S)

    if response.outcome in PAUSE_OUTCOMES:
        with _lock:
            _pause(time.time(), response.outcome)
    if response.outcome not in CACHEABLE_OUTCOMES:
        return _empty("unavailable")

    try:
        # 保存は上限の20件まで（limit が違う呼び出しでも使い回せるように）。
        items = build_items(response.results, limit=20)
    except Exception as e:  # Google の返事の形が想定外でも 500 にしない
        logger.warning("[geocode] outcome=bad_response type=%s", type(e).__name__)
        return _empty("unavailable")

    cache.set(key, items, CACHE_TTL_S)
    return {"items": items[: max(1, int(limit))], "cached": False, "provider": PROVIDER}


def geocode_reverse(lat: float, lng: float, lang: str = DEFAULT_LANG) -> dict:
    """緯度・経度から地名を出す入り口。アプリの画面から呼ばれていないため、外部を呼ばない。"""
    return {"item": None, "cached": False, "provider": "disabled"}
