"""Throttle client identity の起動時設定検証（WS-04 B-1）.

settings.py の import 時に呼ばれるため、gunicorn が `shrine_project.wsgi` を読み込む本番起動経路と、
すべての `manage.py` コマンドで必ず実行される。Django の設定や app registry には依存しない。

- `THROTTLE_TRUSTED_EDGE` は空か `render-cloudflare` のみ。それ以外の値はどの環境でも起動を止める。
- Render 上（`RENDER_EXTERNAL_HOSTNAME` が設定されている）では `render-cloudflare` を必須にする。
  未設定のまま起動すると、匿名クライアント全員が platform proxy のアドレス 1 つの bucket を共有するため。
- `KM_CLIENT_IDENTITY_SECRET` は未設定なら許可（BFF attestation を使わないだけ）。設定されているのに
  32 文字未満、または前後に空白がある場合は起動を止める（Vercel 側と一致しない設定ミスを早期に検出する）。

エラーメッセージには設定値を含めない。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from django.core.exceptions import ImproperlyConfigured

TRUSTED_EDGE_RENDER_CLOUDFLARE = "render-cloudflare"
ALLOWED_TRUSTED_EDGES = frozenset({"", TRUSTED_EDGE_RENDER_CLOUDFLARE})
MIN_SECRET_LENGTH = 32
RENDER_PLATFORM_ENV = "RENDER_EXTERNAL_HOSTNAME"


@dataclass(frozen=True)
class ThrottleIdentityConfig:
    trusted_edge: str
    client_identity_secret: str


def load_throttle_identity_config(environ: Mapping[str, str]) -> ThrottleIdentityConfig:
    edge = (environ.get("THROTTLE_TRUSTED_EDGE") or "").strip()
    secret = environ.get("KM_CLIENT_IDENTITY_SECRET") or ""
    on_render = bool((environ.get(RENDER_PLATFORM_ENV) or "").strip())

    if edge not in ALLOWED_TRUSTED_EDGES:
        raise ImproperlyConfigured(
            "THROTTLE_TRUSTED_EDGE has an unsupported value; "
            f"use '{TRUSTED_EDGE_RENDER_CLOUDFLARE}' or leave it unset"
        )
    if on_render and edge != TRUSTED_EDGE_RENDER_CLOUDFLARE:
        raise ImproperlyConfigured(
            f"THROTTLE_TRUSTED_EDGE must be '{TRUSTED_EDGE_RENDER_CLOUDFLARE}' on Render "
            "(docs/audit/ws04-throttle-client-identity-design-2026-10-25.md §13)"
        )
    if secret and (len(secret) < MIN_SECRET_LENGTH or secret != secret.strip()):
        raise ImproperlyConfigured(
            f"KM_CLIENT_IDENTITY_SECRET must be at least {MIN_SECRET_LENGTH} characters "
            "without surrounding whitespace, or unset"
        )
    return ThrottleIdentityConfig(trusted_edge=edge, client_identity_secret=secret)


# --- Local throttle relaxation（DISABLE_THROTTLE）--------------------------------------------
#: `DISABLE_THROTTLE=1` でも緩めない scope。どちらも外部 API 呼び出し（Google Places）と DB 書き込みを
#: 伴うため、ローカル用の一括緩和が誤って有効になっても専用制限を残す。個別に緩めたい場合は
#: `THROTTLE_SHRINES_INGEST` / `THROTTLE_PLACES_RESOLVE` で上書きする。
DISABLE_THROTTLE_EXEMPT_SCOPES = frozenset({"shrines_ingest", "places-resolve"})
DISABLE_THROTTLE_RELAXED_RATE = "1000/min"


def relax_rates_for_disable_throttle(rates: dict[str, str]) -> None:
    """`DISABLE_THROTTLE=1` 用に、除外 scope 以外の rate を in-place で緩める。"""
    for scope in list(rates.keys()):
        if scope not in DISABLE_THROTTLE_EXEMPT_SCOPES:
            rates[scope] = DISABLE_THROTTLE_RELAXED_RATE
