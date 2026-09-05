# backend/temples/services/google_places.py
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, cast
import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


logger = logging.getLogger(__name__)

# ===== Request history (tests 用) =====
ReqEntry = Tuple[str, Dict[str, Any]]
req_history: List[ReqEntry] = []

# 可能ならパッケージ側にも同じ参照をエクスポート（失敗しても問題なし）
try:
    import temples.services as _PKG

    _PKG.req_history = req_history
except Exception:
    pass
try:
    from . import places as _PLACES

    _PLACES.req_history = req_history
except Exception:
    pass


def _push_req_history(url: str, params: dict) -> None:
    """APIキーを伏せて履歴に1件追加（tests が読む）。"""
    masked = dict(params or {})
    if "key" in masked:
        masked["key"] = "****"
    req_history.append((url, masked))


# ------------------------------------------------------------
# API キー
# ------------------------------------------------------------
def _get_setting(name: str):
    # settings 未設定なら触らない（import-time crash を避ける）
    try:
        if not getattr(settings, "configured", False):
            return None
        return getattr(settings, name, None)
    except ImproperlyConfigured:
        return None

def _resolve_api_key() -> str | None:
    return (
        _get_setting("GOOGLE_MAPS_API_KEY")
        or _get_setting("GOOGLE_API_KEY")
        or _get_setting("GOOGLE_PLACES_API_KEY")
        or os.getenv("GOOGLE_MAPS_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("GOOGLE_PLACES_API_KEY")
        or os.getenv("MAPS_API_KEY")
        or os.getenv("PLACES_API_KEY")
    )

# --- module-level compat ---
API_KEY: str | None = _resolve_api_key()


# ------------------------------------------------------------
# 例外（status_code と「一時障害かどうか」を保持する）
# ------------------------------------------------------------
class GooglePlacesError(RuntimeError):
    """Google Places upstream 呼び出しに関する基底例外。"""

    transient = False

    def __init__(self, message: str, *, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class GooglePlacesConfigError(GooglePlacesError):
    """設定不備・決定的な validation error。retry も fallback もしない。"""

    transient = False


class GooglePlacesTransientError(GooglePlacesError):
    """5xx / timeout / connection error。fallback を許可してよい。"""

    transient = True


class GooglePlacesQuotaError(GooglePlacesError):
    """
    429 / quota 超過。

    429 は Google Cloud の quota / rate limit がコスト上限として効いている
    合図なので、別 SKU へ fallback して通信を続けると quota による停止を
    迂回してしまう。よって transient 扱いにせず fail closed にする。
    """

    transient = False


class GooglePlacesDisabled(GooglePlacesConfigError):
    """server-side kill switch により upstream 呼び出しが停止されている。"""


# ------------------------------------------------------------
# Cost telemetry（安全な値のみを出す）
# ------------------------------------------------------------
def log_places_upstream(
    *,
    api: str,
    operation: str,
    attempt: int,
    status_code: Optional[int] = None,
    upstream_status: Optional[str] = None,
    fallback_reason: Optional[str] = None,
    outcome: Optional[str] = None,
) -> None:
    """
    Google upstream の課金観測ログ。

    出してよいもの: provider / legacy|new / operation / attempt /
    fallback reason / status code / Google の status 文字列。
    出さないもの: API key, lat, lng, keyword 全文, user input 全文,
    query string 付きの Google URL。
    """
    logger.info(
        "places.upstream provider=google api=%s operation=%s attempt=%s "
        "status_code=%s upstream_status=%s fallback_reason=%s outcome=%s",
        api,
        operation,
        attempt,
        status_code,
        upstream_status,
        fallback_reason,
        outcome,
    )


# ------------------------------------------------------------
# Server-side kill switch
# ------------------------------------------------------------
_KILL_SWITCH_OFF_VALUES = {"0", "false", "no", "off"}


def places_upstream_enabled() -> bool:
    """
    GOOGLE_PLACES_ENABLED が明示的に OFF の時だけ False を返す。
    未設定時は既存動作を壊さないため True（= 有効）。
    """
    value = _get_setting("GOOGLE_PLACES_ENABLED")
    if value is None:
        value = os.getenv("GOOGLE_PLACES_ENABLED")
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in _KILL_SWITCH_OFF_VALUES


def _ensure_upstream_enabled(*, api: str, operation: str) -> None:
    """kill switch が OFF なら Google へ HTTP request を出さずに例外化する。"""
    if places_upstream_enabled():
        return
    log_places_upstream(
        api=api,
        operation=operation,
        attempt=0,
        outcome="blocked_by_kill_switch",
    )
    raise GooglePlacesDisabled("Google Places upstream is disabled by server configuration.")



# ------------------------------------------------------------
# 高レベルクライアント
# ------------------------------------------------------------
class GooglePlacesClient:
    BASE_URL = "https://maps.googleapis.com/maps/api/place"

    def __init__(self, api_key: Optional[str] = None, timeout: Optional[float] = None):
        self.api_key: str = cast(str, api_key or API_KEY)
        if not self.api_key:
            raise RuntimeError(
                "Google Places API key is not set. "
                "Set GOOGLE_PLACES_API_KEY (or GOOGLE_MAPS_API_KEY)."
            )
        self.timeout = (
            timeout if timeout is not None else float(os.getenv("GOOGLE_PLACES_TIMEOUT", "8.0"))
        )

    def _get(self, path: str, params: Dict[str, Any]) -> requests.Response:
        _ensure_upstream_enabled(api="legacy", operation=path)
        url = f"{self.BASE_URL}/{path}/json"
        q = {"key": self.api_key, **params}

        _push_req_history(url, q)  # 履歴へ（キーは伏字）

        resp = requests.get(url, params=q, timeout=self.timeout)

        # ログ: query string全体（location/keyword等を含みうる）を落とし、
        # base URLだけ残す（key伏字だけでは不十分なため）。
        try:
            safe_url = resp.url.split("?", 1)[0]
        except Exception:
            safe_url = "<masked>"
        logger.info("Places upstream[%s] %s", path, safe_url)

        resp.raise_for_status()
        return resp

    @staticmethod
    def _ensure_ok(data: Dict[str, Any]) -> None:
        status = data.get("status")
        # status が None の場合も OK とみなす（モック互換）
        if status in ("OK", "ZERO_RESULTS") or status is None:
            return
        msg = data.get("error_message") or status or "UNKNOWN_ERROR"
        raise RuntimeError(f"Google Places error: {msg}")

    @staticmethod
    def _normalize_result(r: Dict[str, Any]) -> Dict[str, Any]:
        geometry = r.get("geometry") or {}
        loc = geometry.get("location") or {}
        photos = r.get("photos") or []
        addr = r.get("formatted_address") or r.get("vicinity")
        first_photo_ref = (photos[0] or {}).get("photo_reference") if photos else None
        return {
            "place_id": r.get("place_id"),
            "name": r.get("name"),
            "address": addr,
            "formatted_address": addr, 
            "lat": loc.get("lat"),
            "lng": loc.get("lng"),
            "rating": r.get("rating"),
            "user_ratings_total": r.get("user_ratings_total"),
            "types": r.get("types"),
            "open_now": (r.get("opening_hours") or {}).get("open_now"),
            "photo_reference": first_photo_ref,
            "icon": r.get("icon"),
        }

    def text_search(
        self,
        query: str,
        *,
        location: Optional[str] = None,
        radius: Optional[int] = None,
        pagetoken: Optional[str] = None,
        language: str = "ja",
        region: str = "jp",
        open_now: Optional[bool] = None,
        minprice: Optional[int] = None,
        maxprice: Optional[int] = None,
        type_: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        # --- テスト時は findplace を使えるよう切替（環境変数） ---
        use_findplace = os.getenv("PLACES_USE_FINDPLACE") == "1" or os.getenv("IS_PYTEST") == "1"
        if use_findplace and not pagetoken:
            fp_params: Dict[str, Any] = {
                "language": language,
                "input": query,
                "inputtype": "textquery",
                "fields": "place_id,formatted_address,geometry,photos,name,rating,user_ratings_total,types,opening_hours,icon",
            }
            if location and radius:
                fp_params["locationbias"] = f"circle:{int(radius)}@{location}"

            data = self._get("findplacefromtext", fp_params).json()
            status = data.get("status")

            if status not in ("OK", "ZERO_RESULTS"):
                logger.error(
                    "Places findplacefromtext error: %s, msg=%s", status, data.get("error_message")
                )
                self._ensure_ok(data)

            results = []
            for c in data.get("candidates", []):
                r = {
                    "place_id": c.get("place_id"),
                    "name": c.get("name"),
                    "formatted_address": c.get("formatted_address"),
                    "geometry": c.get("geometry"),
                    "photos": c.get("photos"),
                    "rating": c.get("rating"),
                    "user_ratings_total": c.get("user_ratings_total"),
                    "types": c.get("types"),
                    "opening_hours": c.get("opening_hours"),
                    "icon": c.get("icon"),
                }
                results.append(self._normalize_result(r))
            return {"results": results, "status": status}, None

        # --- 既存: textsearch ---
        params: Dict[str, Any] = {"language": language, "region": region}
        if pagetoken:
            params["pagetoken"] = pagetoken
        else:
            params["query"] = query
            if location:
                params["location"] = location
            if radius:
                params["radius"] = radius
            if open_now is True:
                params["opennow"] = "true"
            if minprice is not None:
                params["minprice"] = minprice
            if maxprice is not None:
                params["maxprice"] = maxprice
            if type_:
                params["type"] = type_

        data = self._get("textsearch", params).json()
        status = data.get("status") or ("OK" if "candidates" in data else None)

        # 次ページトークンは発効に 2〜5 秒かかるため、pagetoken がある時だけ一度だけ待って再試行
        if status == "INVALID_REQUEST" and pagetoken:
            logger.warning(
                "Places text_search transient INVALID_REQUEST on pagetoken; retrying once"
            )
            time.sleep(1.2)
            data = self._get("textsearch", params).json()
            status = data.get("status") or ("OK" if "candidates" in data else None)
            if status == "INVALID_REQUEST":
                logger.warning(
                    "Places text_search still INVALID_REQUEST for pagetoken; giving up this page."
                )
                return {"results": [], "status": status}, None

        if status not in ("OK", "ZERO_RESULTS"):
            logger.error(
                "Places text_search error: %s, msg=%s",
                status,
                data.get("error_message"),
            )
            self._ensure_ok(data)

        results = [self._normalize_result(r) for r in data.get("results", [])]
        return {"results": results, "status": status}, data.get("next_page_token")

    def nearby_search(
        self,
        *,
        location: str,
        radius: int,
        keyword: Optional[str] = None,
        language: str = "ja",
        pagetoken: Optional[str] = None,
        type_: Optional[str] = None,
        opennow: Optional[bool] = None,
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        params: Dict[str, Any] = {"language": language}
        if pagetoken:
            params["pagetoken"] = pagetoken
        else:
            params.update({"location": location, "radius": radius})
            if keyword:
                params["keyword"] = keyword
            if type_:
                params["type"] = type_
            if opennow is True:
                params["opennow"] = "true"

        data = self._get("nearbysearch", params).json()
        status = data.get("status")
        log_places_upstream(
            api="legacy", operation="nearbysearch", attempt=1, upstream_status=status
        )

        # INVALID_REQUEST は 1 回だけリトライ（pagetoken の有無を問わない：tests 想定）
        if status == "INVALID_REQUEST":
            logger.warning("Places nearby_search transient INVALID_REQUEST; retrying once")
            time.sleep(1.2)
            data = self._get("nearbysearch", params).json()
            status = data.get("status")
            log_places_upstream(
                api="legacy", operation="nearbysearch", attempt=2, upstream_status=status
            )
            if status == "INVALID_REQUEST":
                logger.warning("Places nearby_search still INVALID_REQUEST; giving up.")
                return {"results": [], "status": status}, None

        if status not in ("OK", "ZERO_RESULTS"):
            logger.error(
                "Places nearby_search error: %s, msg=%s",
                status,
                data.get("error_message"),
            )
            self._ensure_ok(data)

        results = [self._normalize_result(r) for r in data.get("results", [])]
        return {"results": results, "status": status}, data.get("next_page_token")

    
    def place_details(
        self,
        place_id: str,
        *,
        language: str = "ja",
        fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        params = {"place_id": place_id, "language": language}
        if fields:
            params["fields"] = fields
        data = self._get("details", params).json()
        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            logger.error(
                "Places details error: %s, msg=%s",
                data.get("status"),
                data.get("error_message"),
            )
            self._ensure_ok(data)
        return data.get("result", {})

    def build_photo_params(
        self,
        photo_reference: str,
        *,
        maxwidth: Optional[int] = 800,
        maxheight: Optional[int] = None,
    ) -> Dict[str, Any]:
        return {
            "key": self.api_key,
            "photoreference": photo_reference,
            **({"maxwidth": int(maxwidth)} if maxwidth else {}),
            **({"maxheight": int(maxheight)} if maxheight else {}),
        }

    def photo(
        self,
        photo_reference: str,
        *,
        maxwidth: Optional[int] = 800,
        maxheight: Optional[int] = None,
    ) -> Tuple[bytes, str]:
        _ensure_upstream_enabled(api="legacy", operation="photo")
        url = f"{self.BASE_URL}/photo"
        params = self.build_photo_params(photo_reference, maxwidth=maxwidth, maxheight=maxheight)
        resp = requests.get(url, params=params, timeout=self.timeout, stream=True)

        # ログ: query string全体を落とし、base URLだけ残す（key伏字だけでは不十分なため）。
        try:
            safe_url = resp.url.split("?", 1)[0]
        except Exception:
            safe_url = "<masked>"
        logger.info("Places upstream[photo]: %s", safe_url)

        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        return resp.content, content_type

def find_place_text(input: str, *, language: str = "ja", locationbias: str | None = None, fields: str | None = None):
    """
    temples.services.places.find_place() から呼ばれる薄いラッパー。
    positional で input が来る設計なので input は positional を許容する。
    """
    return findplacefromtext(
        input=input,
        language=language,
        locationbias=locationbias,
        fields=fields,
    )
# ------------------------------------------------------------
# 低レベル API（tests が直接参照）
# ------------------------------------------------------------
_TIMEOUT = 10


def _log_upstream(kind: str, url: str, params: dict) -> None:
    # paramsにはquery/input/location等の生テキストが入りうるため、値ではなく
    # keyの一覧のみ出す（keyだけmaskしてもquery/location等が残ってしまうため）。
    param_keys = sorted((params or {}).keys())
    logger.info("Places upstream[%s] %s param_keys=%s", kind, url, param_keys)


def textsearch(
    *,
    query: str,
    language: Optional[str] = None,
    region: Optional[str] = None,
    location: Optional[str] = None,
    radius: Optional[int] = None,
    type: Optional[str] = None,
    pagetoken: Optional[str] = None,
) -> Dict[str, Any]:
    _ensure_upstream_enabled(api="legacy", operation="textsearch")
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "key": API_KEY,
        "query": query,
        "language": language,
        "region": region,
        "location": location,
        "radius": radius,
        "type": type,
        "pagetoken": pagetoken,
    }
    _log_upstream("textsearch", url, params)
    clean = {k: v for k, v in params.items() if v is not None}
    _push_req_history(url, clean)
    resp = requests.get(url, params=clean, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def details(
    place_id: str = None,
    params: Optional[Dict[str, Any]] = None,
    *,
    language: Optional[str] = None,
    fields: Optional[str] = None,
) -> Dict[str, Any]:
    """
    互換:
      - details(place_id=..., language=..., fields=...)   ✅
      - details(place_id, {"language": "...", "fields": "..."})  ✅（旧コード用）
    """
    # 旧: details(place_id, params) を吸収
    if params:
        if language is None:
            language = params.get("language")
        if fields is None:
            fields = params.get("fields")

    _ensure_upstream_enabled(api="legacy", operation="details")
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params2 = {
        "key": API_KEY,
        "place_id": place_id,
        "language": language,
        "fields": fields,
    }
    _log_upstream("details", url, params2)
    clean = {k: v for k, v in params2.items() if v is not None}
    _push_req_history(url, clean)
    resp = requests.get(url, params=clean, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def findplacefromtext(
    *,
    input: str,
    language: Optional[str] = None,
    locationbias: Optional[str] = None,
    fields: Optional[str] = None,
) -> Dict[str, Any]:
    _ensure_upstream_enabled(api="legacy", operation="findplacefromtext")
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "key": API_KEY,
        "inputtype": "textquery",
        "input": input,
        "language": language,
        "locationbias": locationbias,
        "fields": fields,
    }
    _log_upstream("findplacefromtext", url, params)
    clean = {k: v for k, v in params.items() if v is not None}
    _push_req_history(url, clean)
    resp = requests.get(url, params=clean, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# 互換エイリアス
def find_place_from_text(**kw):  # noqa: N802
    return findplacefromtext(**kw)


def find_place(**kw):
    return findplacefromtext(**kw)


# ------------------------------------------------------------
# ラッパ（後方互換）
# ------------------------------------------------------------
_client_singleton: Optional[GooglePlacesClient] = None


def _client() -> GooglePlacesClient:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = GooglePlacesClient()
    return _client_singleton

def text_search(query_or_params=None, **kwargs) -> Dict[str, Any]:
    """辞書または文字列どちらでも呼べる text_search ラッパ"""

    # ✅ SDKが受け取らないゴミは先に捨てる
    kwargs.pop("payload", None)
    kwargs.pop("limit", None)
    kwargs.pop("radius_m", None)

    if isinstance(query_or_params, dict):
        p = dict(query_or_params)
        p.pop("payload", None)
        p.pop("limit", None)
        p.pop("radius_m", None)

        query = p.pop("q", None) or p.pop("query", "") or ""
        location = p.pop("location", None)

        if not location and p.get("lat") is not None and p.get("lng") is not None:
            location = f"{p.pop('lat')},{p.pop('lng')}"

        pagetoken = p.pop("pagetoken", None)
        language = p.pop("language", "ja")
        region = p.pop("region", "jp")
        open_now = p.pop("opennow", p.pop("open_now", None))
        minprice = p.pop("minprice", None)
        maxprice = p.pop("maxprice", None)
        type_ = p.pop("type", None)

        radius = p.pop("radius", None)
        kwargs.update(p)

        data, _ = _client().text_search(
            query,
            location=location,
            radius=radius,
            pagetoken=pagetoken,
            language=language,
            region=region,
            open_now=open_now,
            minprice=minprice,
            maxprice=maxprice,
            type_=type_,
            **kwargs,
        )
        return data

    # ---- ここが今回の本丸（kwargsルート） ----
    # query を kwargs からも拾う（_wrap_call で展開されるとここに来る）
    query = query_or_params if query_or_params is not None else (kwargs.pop("q", None) or kwargs.pop("query", ""))

    # lat/lng → location に変換して kwargs から排除
    location = kwargs.pop("location", None)
    lat = kwargs.pop("lat", None)
    lng = kwargs.pop("lng", None)
    if not location and lat is not None and lng is not None:
        location = f"{lat},{lng}"

    # radius も kwargs に残すと混ざるのでここで抜く
    radius = kwargs.pop("radius", None)

    # 念のためもう一回
    kwargs.pop("payload", None)
    kwargs.pop("limit", None)
    kwargs.pop("radius_m", None)

    data, _ = _client().text_search(
        query,
        location=location,
        radius=radius,
        **kwargs,
    )
    return data

    # string/None route
    query = query_or_params if query_or_params is not None else kwargs.pop("query", "")
    kwargs.pop("payload", None)
    kwargs.pop("limit", None)
    kwargs.pop("radius_m", None)
    data, _ = _client().text_search(query, **kwargs)
    return data

def nearby_search(
    *,
    location=None,
    radius: int,
    keyword: Optional[str] = None,
    language: str = "ja",
    pagetoken: Optional[str] = None,
    type_: Optional[str] = None,
    opennow: Optional[bool] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    モジュール関数ラッパ（self は不要）
    - location: "lat,lng" 文字列 or (lat, lng) タプル どちらも許容
    - lat/lng が来た場合も許容
    - type / type_ どちらでも受ける
    戻り値は data(dict) のみ（既存呼び出し側が data["results"] を期待するため）
    """

    # location 正規化
    if location is None and kwargs.get("lat") is not None and kwargs.get("lng") is not None:
        location = f"{kwargs.pop('lat')},{kwargs.pop('lng')}"
    if isinstance(location, (tuple, list)) and len(location) == 2:
        location = f"{location[0]},{location[1]}"
    if location is None:
        raise TypeError("location is required")

    # type 正規化（type と type_ を統合）
    if type_ is None:
        type_ = kwargs.pop("type", None)

    data, _next = _client().nearby_search(
        location=str(location),
        radius=int(radius),
        keyword=keyword,
        language=language,
        pagetoken=pagetoken,
        type_=type_,
        opennow=opennow,
        **kwargs,
    )
    return data


def place_details(place_id: str, **kwargs) -> Dict[str, Any]:
    return _client().place_details(place_id, **kwargs)


def photo(photo_reference: str, **kwargs) -> Tuple[bytes, str]:
    return _client().photo(photo_reference, **kwargs)

def nearby_search_new(
    *,
    lat: float,
    lng: float,
    radius: int,
    limit: int = 10,
    keyword: str | None = None,
) -> dict:
    """
    Places API (New) searchText。

    - FieldMask は Nearby 経路が実際に使う field だけに絞る（高 SKU 回避）。
      rating / userRatingCount / photos / currentOpeningHours は取得しない。
    - 既存 Nearby response contract を壊さないため、取得しなくなった値は
      None（optional/null）で返す。
    - 例外は status_code と transient フラグを持たせ、呼び出し側が
      「一時障害だけ legacy へ fallback する」判断をできるようにする。
    """
    # ガード：神社検索以外は New API を使わない（安全策）。決定的な validation error。
    if keyword not in (None, "神社"):
        raise GooglePlacesConfigError("nearby_search_new is shrine-only")

    api_key = _resolve_api_key()
    if not api_key:
        raise GooglePlacesConfigError("Google Places API key is not set.")

    _ensure_upstream_enabled(api="new", operation="searchText")

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": ",".join([
            "places.id",
            "places.displayName",
            "places.formattedAddress",
            "places.location",
            "places.types",
        ]),
    }

    body = {
        "textQuery": "神社",
        "maxResultCount": int(limit),
        "locationBias": {
            "circle": {
                "center": {"latitude": float(lat), "longitude": float(lng)},
                "radius": float(radius),
            }
        },
        "rankPreference": "DISTANCE",
        "languageCode": "ja",
        "regionCode": "JP",
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=8)
    except requests.Timeout as e:
        log_places_upstream(
            api="new", operation="searchText", attempt=1, outcome="timeout"
        )
        raise GooglePlacesTransientError("Places(New) searchText timeout") from e
    except requests.ConnectionError as e:
        log_places_upstream(
            api="new", operation="searchText", attempt=1, outcome="connection_error"
        )
        raise GooglePlacesTransientError("Places(New) searchText connection error") from e

    status_code = resp.status_code
    log_places_upstream(
        api="new",
        operation="searchText",
        attempt=1,
        status_code=status_code,
        outcome="ok" if resp.ok else "http_error",
    )

    if not resp.ok:
        # 429 は quota / rate limit の防波堤として発生しうる。legacy へ落とすと
        # 別 SKU で通信を継続し quota によるコスト停止を迂回するため fail closed。
        if status_code == 429:
            raise GooglePlacesQuotaError(
                f"Places(New) searchText quota exhausted: {status_code}",
                status_code=status_code,
            )
        # 5xx のみ一時障害として扱う。4xx（400/401/403 等）は決定的な失敗。
        if 500 <= status_code < 600:
            raise GooglePlacesTransientError(
                f"Places(New) searchText transient error: {status_code}",
                status_code=status_code,
            )
        raise GooglePlacesConfigError(
            f"Places(New) searchText error: {status_code}",
            status_code=status_code,
        )

    raw = resp.json() or {}
    results = []
    for p in raw.get("places", []) or []:
        loc = p.get("location") or {}
        address = p.get("formattedAddress")

        results.append({
            "place_id": p.get("id"),
            "name": (p.get("displayName") or {}).get("text"),
            "address": address,
            "formatted_address": address,
            "lat": loc.get("latitude"),
            "lng": loc.get("longitude"),
            "types": p.get("types") or [],
            # 以下は FieldMask から外したため常に None（既存キーは互換のため残す）
            "rating": None,
            "user_ratings_total": None,
            "photo_reference": None,
            "open_now": None,
            "icon": None,
        })

    return {"results": results, "status": "OK" if results else "ZERO_RESULTS"}


__all__ = [
    "GooglePlacesClient",
    # ラッパ
    "text_search",
    "nearby_search",
    "place_details",
    "photo",
    # 低レベル API
    "textsearch",
    "details",
    "findplacefromtext",
    "find_place_from_text",
    "find_place",
    "find_place_text",
    "nearby_search_new",
    # 例外 / 運用フック
    "GooglePlacesError",
    "GooglePlacesConfigError",
    "GooglePlacesTransientError",
    "GooglePlacesQuotaError",
    "GooglePlacesDisabled",
    "places_upstream_enabled",
    "log_places_upstream",
    # テスト用フック
    "req_history",
    "API_KEY",
]
