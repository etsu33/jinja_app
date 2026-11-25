"""DJANGO_SECRET_KEY の起動時解決（SPH-02）.

settings.py の import 時に呼ばれるため、gunicorn が `shrine_project.wsgi` を読み込む本番起動経路と、
すべての `manage.py` コマンドで必ず実行される。Django の設定や app registry には依存しない。

- `DJANGO_SECRET_KEY` が空白以外を含む値なら、その値を変更せずに使う。
- 未設定・空・空白のみなら起動を止める（fail-closed）。ローカル開発も `backend/.env.local` 等で明示設定する。
- 例外は GitHub Actions の backend test job が pytest 以外で settings を読む工程（`makemigrations --check` 等）
  だけ。`GITHUB_ACTIONS=true` かつ `IS_PYTEST` が真で、Render 上ではない場合に限り、プロセスごとの
  ランダム値を使う。値は保存も出力もしないため、署名済みデータはそのプロセスの外では検証できない。
  `CI` のような汎用フラグ単独、`IS_PYTEST` 単独では許可しない。
- pytest 自体は `pytest.ini` の pytest-env が既定値を与えるため、この例外に依存しない。

エラーメッセージには設定値を含めない。
"""

from __future__ import annotations

import secrets
from collections.abc import Mapping

from django.core.exceptions import ImproperlyConfigured

SECRET_KEY_ENV = "DJANGO_SECRET_KEY"
# Render が全 service に設定する変数。どれか 1 つでもあれば Render 上とみなし、例外を許可しない。
RENDER_PLATFORM_ENVS = ("RENDER", "RENDER_EXTERNAL_HOSTNAME", "RENDER_SERVICE_ID")
_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in _TRUTHY


def _on_render(environ: Mapping[str, str]) -> bool:
    return any((environ.get(name) or "").strip() for name in RENDER_PLATFORM_ENVS)


def ci_tooling_fallback_allowed(environ: Mapping[str, str]) -> bool:
    if _on_render(environ):
        return False
    return environ.get("GITHUB_ACTIONS") == "true" and _is_truthy(environ.get("IS_PYTEST"))


def resolve_secret_key(environ: Mapping[str, str]) -> str:
    value = environ.get(SECRET_KEY_ENV) or ""
    if value.strip():
        return value
    if ci_tooling_fallback_allowed(environ):
        return secrets.token_urlsafe(50)
    raise ImproperlyConfigured(
        f"{SECRET_KEY_ENV} is not set. Set it in the service environment "
        "(for local development, in backend/.env.local; see backend/.env.example)."
    )
