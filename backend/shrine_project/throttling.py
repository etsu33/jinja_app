"""DRF throttle client identity（WS-04）.

Design record: docs/audit/ws04-throttle-client-identity-design-2026-10-25.md（MD-1〜MD-4）.

DRF の既定 `get_ident()` は `NUM_PROXIES` 未設定のとき X-Forwarded-For ヘッダ全体を識別子にするため、
クライアントが任意の値を送るだけで匿名 throttle の bucket を増やせた。ここでは匿名リクエストの識別子を
次の順で決める（認証済みユーザーは DRF 既定どおり `user.pk` のまま。`get_ident()` は呼ばれない）:

1. `bff:<ip>`  — Web BFF が HMAC 署名した client IP（MD-2 = C）。署名・時刻・IP のどれかが不正なら無視する。
2. `edge:<ip>` — `CF-Connecting-IP`。`THROTTLE_TRUSTED_EDGE=render-cloudflare` が設定された
   デプロイ（Render の edge が値を上書きする境界の内側）でのみ使う（MD-1）。
3. `remote:<REMOTE_ADDR>` — 上記がどれも使えないときの fail-safe。Render では platform proxy の
   アドレスになり、クライアントを分割せずまとめる（偽装で bucket を増やせない代わりに共有される）。

X-Forwarded-For は一切使わない。生の IP・署名・secret はログに出さない。
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import logging
import re
import time

from django.conf import settings
from rest_framework import throttling

logger = logging.getLogger(__name__)

TRUSTED_EDGE_RENDER_CLOUDFLARE = "render-cloudflare"

CLIENT_IP_META = "HTTP_X_KM_CLIENT_IP"
CLIENT_TS_META = "HTTP_X_KM_CLIENT_TS"
CLIENT_SIG_META = "HTTP_X_KM_CLIENT_SIG"
EDGE_IP_META = "HTTP_CF_CONNECTING_IP"

MAX_CLOCK_SKEW_SECONDS = 60
MIN_SECRET_LENGTH = 32
_MAX_IP_LENGTH = 45
_TS_RE = re.compile(r"[0-9]{1,12}")
_SIG_RE = re.compile(r"[0-9a-f]{64}")
_IP_CHARS_RE = re.compile(r"[0-9A-Fa-f:.]+")

_IDENT_ATTR = "_km_throttle_ident"
_warned: set[str] = set()


def _warn_once(key: str, message: str) -> None:
    if key not in _warned:
        _warned.add(key)
        logger.warning(message)


def parse_client_ip(value: object) -> str | None:
    """厳格な IP 検証。単一の IPv4 / IPv6 アドレスだけを受け付け、正規形で返す。"""
    if not isinstance(value, str) or not value or len(value) > _MAX_IP_LENGTH:
        return None
    # 空白・カンマ（リスト）・zone id（%）・ポート付き表記などは拒否する
    if not _IP_CHARS_RE.fullmatch(value):
        return None
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return None
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return str(ip)


def client_identity_secret() -> bytes | None:
    secret = getattr(settings, "THROTTLE_CLIENT_IDENTITY_SECRET", "") or ""
    if not secret:
        return None
    if len(secret) < MIN_SECRET_LENGTH:
        _warn_once("short_secret", "throttle client identity secret is too short; BFF attestation disabled")
        return None
    return secret.encode("utf-8")


def sign_client_identity(secret: bytes, ts: str, method: str, path: str, ip: str) -> str:
    """BFF と同じ署名方式（apps/web/src/lib/server/clientIdentity.ts）。"""
    message = f"{ts}\n{method.upper()}\n{path}\n{ip}".encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def verified_bff_client_ip(request, *, now: float | None = None) -> str | None:
    """有効な BFF attestation の client IP。不在・不正・期限切れ・secret 未設定なら None。"""
    meta = request.META
    raw_ip = meta.get(CLIENT_IP_META)
    raw_ts = meta.get(CLIENT_TS_META)
    raw_sig = meta.get(CLIENT_SIG_META)
    if raw_ip is None and raw_ts is None and raw_sig is None:
        return None

    secret = client_identity_secret()
    if secret is None:
        return None
    if not (isinstance(raw_ts, str) and _TS_RE.fullmatch(raw_ts)):
        return None
    if not (isinstance(raw_sig, str) and _SIG_RE.fullmatch(raw_sig)):
        return None
    ip = parse_client_ip(raw_ip)
    if ip is None:
        return None
    current = time.time() if now is None else now
    if abs(current - int(raw_ts)) > MAX_CLOCK_SKEW_SECONDS:
        return None

    expected = sign_client_identity(secret, raw_ts, request.method or "", request.path, raw_ip)
    if not hmac.compare_digest(expected, raw_sig):
        return None
    return ip


def trusted_edge_client_ip(request) -> str | None:
    """信頼できる edge 境界の内側でのみ `CF-Connecting-IP` を返す。"""
    edge = getattr(settings, "THROTTLE_TRUSTED_EDGE", "") or ""
    if edge != TRUSTED_EDGE_RENDER_CLOUDFLARE:
        if edge:
            _warn_once("unknown_edge", "unknown THROTTLE_TRUSTED_EDGE value; CF-Connecting-IP is not trusted")
        return None
    ip = parse_client_ip(request.META.get(EDGE_IP_META))
    if ip is None:
        _warn_once("edge_missing", "trusted edge identity missing or malformed; using fail-safe throttle identity")
    return ip


def resolve_client_ident(request) -> str:
    """匿名 throttle の識別子。1 リクエストにつき 1 回だけ解決する。"""
    base = getattr(request, "_request", request)
    cached = getattr(base, _IDENT_ATTR, None)
    if cached is not None:
        return cached

    ip = verified_bff_client_ip(request)
    if ip is not None:
        ident = f"bff:{ip}"
    else:
        ip = trusted_edge_client_ip(request)
        if ip is not None:
            ident = f"edge:{ip}"
        else:
            ident = f"remote:{parse_client_ip(request.META.get('REMOTE_ADDR')) or 'unknown'}"

    setattr(base, _IDENT_ATTR, ident)
    return ident


class ClientIdentityMixin:
    def get_ident(self, request):
        return resolve_client_ident(request)


class AnonRateThrottle(ClientIdentityMixin, throttling.AnonRateThrottle):
    pass


class UserRateThrottle(ClientIdentityMixin, throttling.UserRateThrottle):
    pass


class ScopedRateThrottle(ClientIdentityMixin, throttling.ScopedRateThrottle):
    pass
