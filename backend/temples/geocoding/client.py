from __future__ import annotations

import logging
import os
import typing as t
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

ParamValue = t.Union[str, int, float]



@dataclass
class GeocodeResult:
    lat: float
    lon: float
    formatted: str
    precision: str  # "rooftop" / "street" / "city" / "region" / "approx"
    provider: str
    raw: dict


class GeocodingError(Exception):
    pass


def _google_maps_api_key() -> str | None:
    key = (
        os.getenv("GOOGLE_MAPS_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("MAPS_API_KEY")
        or os.getenv("PLACES_API_KEY")
    )
    if key:
        return key
    try:
        from django.conf import settings as dj_settings

        return (
            getattr(dj_settings, "GOOGLE_MAPS_API_KEY", None)
            or getattr(dj_settings, "GOOGLE_API_KEY", None)
        )
    except Exception:
        return None

def geocode_google_point(
    area: str,
    *,
    language: str = "ja",
    region: str = "jp",
    timeout: float = 6.0,
) -> tuple[float, float] | None:
    area = (area or "").strip()
    key = _google_maps_api_key()
    if not key or not area:
        logger.info(
            "[geocode_google_point] skip has_key=%s has_area=%s area_length=%d",
            bool(key),
            bool(area),
            len(area),
        )
        return None

    try:
        r = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "key": key,
                "address": area,
                "language": language,
                "region": region,
            },
            timeout=timeout,
        )
        r.raise_for_status()

        payload = r.json()
        status = payload.get("status")
        results = payload.get("results") or []

        logger.info(
            "[geocode_google_point] response area_length=%d status=%s result_count=%d error_message=%s",
            len(area),
            status,
            len(results),
            payload.get("error_message"),
        )

        if status in {
            "ZERO_RESULTS",
            "OVER_QUERY_LIMIT",
            "REQUEST_DENIED",
            "INVALID_REQUEST",
            "UNKNOWN_ERROR",
        }:
            return None

        if not results:
            return None

        loc = (results[0].get("geometry") or {}).get("location") or {}
        lat, lng = loc.get("lat"), loc.get("lng")
        if lat is None or lng is None:
            logger.warning("[geocode_google_point] missing location area_length=%d", len(area))
            return None

        return float(lat), float(lng)

    except Exception as e:
        # str(e)は含めない: requestsの接続/タイムアウト系例外はURL全体
        # （API key・address含む）をメッセージへ埋め込むため（実測確認済み）。
        logger.warning(
            "[geocode_google_point] exception area_length=%d type=%s",
            len(area),
            type(e).__name__,
        )
        return None

GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

# Google の Geocoding API（v3）の status → 呼び出し側で見分けるための結果の名前。
_GOOGLE_STATUS_OUTCOMES = {
    "OK": "ok",
    "ZERO_RESULTS": "zero_results",
    "OVER_QUERY_LIMIT": "quota_exceeded",
    "OVER_DAILY_LIMIT": "quota_exceeded",
    "REQUEST_DENIED": "request_denied",
    "INVALID_REQUEST": "invalid_request",
    "UNKNOWN_ERROR": "unknown_error",
}


@dataclass(frozen=True)
class GoogleGeocodeResponse:
    """Google の地名検索の結果。

    outcome: ok / zero_results / quota_exceeded / request_denied / invalid_request /
             unknown_error / missing_key / http_error / timeout / network_error / bad_response
    """

    outcome: str
    results: list
    http_status: int | None = None


def google_geocode_search(
    address: str,
    *,
    language: str,
    region: str = "jp",
    timeout: float = 6.0,
) -> GoogleGeocodeResponse:
    """Geocoding API（v3）で地名・住所の候補を引く。例外は投げない。

    - region は優先する国の指定（その国に限る指定ではない）。
    - ログには鍵の値・相談の言葉・Google のエラーの説明文を出さない（結果の名前・HTTP の状態・
      件数・言葉の文字数だけ）。通信の例外は、文に URL（鍵入り）が入るので種類だけ出す。
    """
    address = (address or "").strip()
    key = _google_maps_api_key()
    if not key:
        logger.error("[google_geocode] outcome=missing_key query_length=%d", len(address))
        return GoogleGeocodeResponse(outcome="missing_key", results=[])

    try:
        r = requests.get(
            GOOGLE_GEOCODE_URL,
            params={"key": key, "address": address, "language": language, "region": region},
            timeout=timeout,
        )
    except requests.Timeout as e:
        logger.warning("[google_geocode] outcome=timeout type=%s query_length=%d", type(e).__name__, len(address))
        return GoogleGeocodeResponse(outcome="timeout", results=[])
    except Exception as e:
        logger.warning(
            "[google_geocode] outcome=network_error type=%s query_length=%d", type(e).__name__, len(address)
        )
        return GoogleGeocodeResponse(outcome="network_error", results=[])

    http_status = getattr(r, "status_code", None)
    if http_status != 200:
        outcome = {403: "request_denied", 429: "quota_exceeded"}.get(http_status, "http_error")
        logger.warning(
            "[google_geocode] outcome=%s http_status=%s query_length=%d", outcome, http_status, len(address)
        )
        return GoogleGeocodeResponse(outcome=outcome, results=[], http_status=http_status)

    try:
        payload = r.json()
        status = str(payload.get("status") or "")
        results = payload.get("results") or []
        if not isinstance(results, list):
            raise ValueError("results is not a list")
    except Exception as e:
        logger.warning(
            "[google_geocode] outcome=bad_response type=%s query_length=%d", type(e).__name__, len(address)
        )
        return GoogleGeocodeResponse(outcome="bad_response", results=[], http_status=http_status)

    outcome = _GOOGLE_STATUS_OUTCOMES.get(status, "unknown_error")
    log = logger.info if outcome in {"ok", "zero_results"} else logger.warning
    if outcome == "request_denied":
        log = logger.error
    log(
        "[google_geocode] outcome=%s google_status=%s result_count=%d query_length=%d",
        outcome,
        status or "-",
        len(results),
        len(address),
    )
    return GoogleGeocodeResponse(
        outcome=outcome,
        results=results if outcome == "ok" else [],
        http_status=http_status,
    )


class GeocodingClient:
    def __init__(self, session: t.Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.provider = (os.getenv("GEOCODER_PROVIDER") or "opencage").lower()

        # 共通キー > プロバイダ別キー（google用の別名も拾う）
        self.api_key = (
            os.getenv("GEOCODER_API_KEY")
            or (
                self.provider == "google"
                and (os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_PLACES_API_KEY"))
            )
            or ""
        )
        if not self.api_key:
            need = (
                "GEOCODER_API_KEY もしくは（googleの場合）GOOGLE_MAPS_API_KEY/GOOGLE_PLACES_API_KEY"
            )
            raise GeocodingError(f"{need} が設定されていません。")

        self.timeout = float(os.getenv("GEOCODER_TIMEOUT", "10"))

    # --- 単発（もっとも確からしい1件） -------------------------------------
    def geocode(self, address: str) -> GeocodeResult:
        address = (address or "").strip()
        if not address:
            raise ValueError("address は必須です。")
        if self.provider == "opencage":
            return self._geocode_opencage(address)
        if self.provider == "google":
            return self._geocode_google(address)
        raise GeocodingError(f"未対応のプロバイダ: {self.provider}")

    # --- 複数候補（あいまい検索） -------------------------------------------
    def geocode_candidates(self, address: str, limit: int = 5) -> list[GeocodeResult]:
        address = (address or "").strip()
        if not address:
            raise ValueError("address は必須です。")
        limit = max(1, min(int(limit or 1), 10))
        if self.provider == "opencage":
            return self._geocode_opencage_multi(address, limit=limit)
        if self.provider == "google":
            return self._geocode_google_multi(address, limit=limit)
        raise GeocodingError(f"未対応のプロバイダ: {self.provider}")

    # ===================== Google =====================
    def _geocode_google(self, address: str) -> GeocodeResult:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params: dict[str, ParamValue] = {  # ★ 型を明示
            "address": address,
            "key": self.api_key,
            "language": "ja",
            "region": "jp",
        }
        r = self.session.get(url, params=params, timeout=self.timeout)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise GeocodingError(f"Google Geocoding HTTP {r.status_code}: {r.text[:200]}") from e

        data = r.json()
        self._assert_google_ok(data)

        top = data["results"][0]
        loc = top["geometry"]["location"]
        loc_type = (top["geometry"].get("location_type") or "APPROXIMATE").upper()

        return GeocodeResult(
            lat=float(loc["lat"]),
            lon=float(loc["lng"]),
            formatted=top.get("formatted_address") or address,
            precision=self._google_loc_type_to_precision(loc_type),
            provider="google",
            raw=top,
        )

    def _geocode_google_multi(self, address: str, limit: int = 5) -> list[GeocodeResult]:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params: dict[str, ParamValue] = {
            "address": address,
            "key": self.api_key,
            "language": "ja",
            "region": "jp",
        }
        r = self.session.get(url, params=params, timeout=self.timeout)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise GeocodingError(f"Google Geocoding HTTP {r.status_code}: {r.text[:200]}") from e

        data = r.json()
        self._assert_google_ok(data)

        out: list[GeocodeResult] = []
        for top in data.get("results", [])[:limit]:
            loc = top["geometry"]["location"]
            loc_type = (top["geometry"].get("location_type") or "APPROXIMATE").upper()
            out.append(
                GeocodeResult(
                    lat=float(loc["lat"]),
                    lon=float(loc["lng"]),
                    formatted=top.get("formatted_address") or address,
                    precision=self._google_loc_type_to_precision(loc_type),
                    provider="google",
                    raw=top,
                )
            )
        return out

    @staticmethod
    def _google_loc_type_to_precision(loc_type: str) -> str:
        # ROOFTOP, RANGE_INTERPOLATED, GEOMETRIC_CENTER, APPROXIMATE
        if loc_type == "ROOFTOP":
            return "rooftop"
        if loc_type == "RANGE_INTERPOLATED":
            return "street"
        if loc_type == "GEOMETRIC_CENTER":
            return "city"
        return "approx"

    @staticmethod
    def _assert_google_ok(data: dict) -> None:
        status = data.get("status")
        if status == "OK" and data.get("results"):
            return
        if status in {
            "ZERO_RESULTS",
            "OVER_QUERY_LIMIT",
            "REQUEST_DENIED",
            "INVALID_REQUEST",
            "UNKNOWN_ERROR",
        }:
            msg = data.get("error_message") or status
            raise GeocodingError(f"Google Geocoding: {status}: {msg}")
        raise GeocodingError(f"Google Geocoding: {status} {str(data)[:200]}")

    # ===================== OpenCage =====================
    def _geocode_opencage(self, address: str) -> GeocodeResult:
        url = "https://api.opencagedata.com/geocode/v1/json"
        params: dict[str, ParamValue] = {
            "q": address,
            "key": self.api_key,
            "language": "ja",
            "limit": 1,
            "no_annotations": 1,
            "countrycode": "jp",
        }
        resp = self.session.get(url, params=params, timeout=self.timeout)
        if resp.status_code != 200:
            text = getattr(resp, "text", "")[:200]
            raise GeocodingError(f"OpenCage HTTP {resp.status_code}: {text}")

        data = resp.json()
        results = data.get("results", []) or []
        if not results:
            raise GeocodingError("該当するジオコーディング結果が見つかりませんでした。")

        top = results[0]
        geom = top.get("geometry") or {}
        lat, lng = geom.get("lat"), geom.get("lng")
        if lat is None or lng is None:
            raise GeocodingError("座標を抽出できませんでした。")

        components = top.get("components") or {}
        confidence = top.get("confidence")  # 1-10 or None
        precision = self._infer_precision_from_opencage(components, confidence)
        formatted = top.get("formatted") or address

        return GeocodeResult(
            lat=float(lat),
            lon=float(lng),
            formatted=formatted,
            precision=precision,
            provider="opencage",
            raw=top,
        )

    def _geocode_opencage_multi(self, address: str, limit: int = 5) -> list[GeocodeResult]:
        url = "https://api.opencagedata.com/geocode/v1/json"
        params: dict[str, ParamValue] = {
            "q": address,
            "key": self.api_key,
            "language": "ja",
            "limit": max(1, min(int(limit or 1), 10)),
            "no_annotations": 1,
            "countrycode": "jp",
        }
        resp = self.session.get(url, params=params, timeout=self.timeout)
        if resp.status_code != 200:
            text = getattr(resp, "text", "")[:200]
            raise GeocodingError(f"OpenCage HTTP {resp.status_code}: {text}")

        data = resp.json()
        out: list[GeocodeResult] = []
        for top in data.get("results") or []:
            geom = top.get("geometry") or {}
            lat, lng = geom.get("lat"), geom.get("lng")
            if lat is None or lng is None:
                continue
            components = top.get("components") or {}
            conf = top.get("confidence")  # 1-10 or None
            precision = self._infer_precision_from_opencage(components, conf)
            formatted = top.get("formatted") or address
            out.append(
                GeocodeResult(
                    lat=float(lat),
                    lon=float(lng),
                    formatted=formatted,
                    precision=precision,
                    provider="opencage",
                    raw=top,
                )
            )
        return out

    @staticmethod
    def _infer_precision_from_opencage(components: dict, confidence: t.Optional[int]) -> str:
        if "house_number" in components or "building" in components:
            return "rooftop"
        if "road" in components:
            return "street"
        if any(k in components for k in ("city", "town", "village")):
            return "city"
        if any(k in components for k in ("state", "region")):
            return "region"
        if confidence is not None and confidence >= 8:
            return "street"
        return "approx"
