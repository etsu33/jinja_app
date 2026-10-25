"""WS-04 B-1: throttle client identity の起動時設定検証（shrine_project/throttle_config.py）。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from shrine_project.throttle_config import load_throttle_identity_config

BACKEND = Path(__file__).resolve().parents[1]
RENDER = {"RENDER_EXTERNAL_HOSTNAME": "jinja-backend.onrender.com"}
EDGE = {"THROTTLE_TRUSTED_EDGE": "render-cloudflare"}
SECRET = "s" * 48


# --- valid ----------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "environ, edge, secret",
    [
        pytest.param({}, "", "", id="local-default"),
        pytest.param({**EDGE}, "render-cloudflare", "", id="local-with-edge"),
        pytest.param({**RENDER, **EDGE}, "render-cloudflare", "", id="render-without-secret"),
        pytest.param({**RENDER, **EDGE, "KM_CLIENT_IDENTITY_SECRET": SECRET}, "render-cloudflare", SECRET, id="render-full"),
        pytest.param({**RENDER, "THROTTLE_TRUSTED_EDGE": " render-cloudflare \n"}, "render-cloudflare", "", id="edge-trimmed"),
        pytest.param({"RENDER_EXTERNAL_HOSTNAME": "  "}, "", "", id="blank-render-hostname"),
        pytest.param({"KM_CLIENT_IDENTITY_SECRET": ""}, "", "", id="empty-secret-is-unset"),
    ],
)
def test_valid_configuration(environ, edge, secret):
    config = load_throttle_identity_config(environ)
    assert config.trusted_edge == edge
    assert config.client_identity_secret == secret


# --- missing --------------------------------------------------------------------------------------


@pytest.mark.parametrize("edge", [None, "", "   "])
def test_missing_trusted_edge_on_render_is_rejected(edge):
    environ = dict(RENDER)
    if edge is not None:
        environ["THROTTLE_TRUSTED_EDGE"] = edge
    with pytest.raises(ImproperlyConfigured, match="must be 'render-cloudflare' on Render"):
        load_throttle_identity_config(environ)


# --- malformed ------------------------------------------------------------------------------------


@pytest.mark.parametrize("on_render", [False, True])
@pytest.mark.parametrize("edge", ["Render-Cloudflare", "cloudflare", "render", "true", "1", "render-cloudflare,x"])
def test_unsupported_trusted_edge_is_rejected_everywhere(on_render, edge):
    environ = {"THROTTLE_TRUSTED_EDGE": edge, **(RENDER if on_render else {})}
    with pytest.raises(ImproperlyConfigured, match="unsupported value") as exc:
        load_throttle_identity_config(environ)
    assert edge not in str(exc.value).replace("render-cloudflare", "")


@pytest.mark.parametrize(
    "secret",
    [
        pytest.param("k" * 31, id="too-short"),
        pytest.param(" " + "k" * 40, id="leading-space"),
        pytest.param("k" * 40 + "\n", id="trailing-newline"),
    ],
)
@pytest.mark.parametrize("on_render", [False, True])
def test_insufficient_secret_is_rejected(on_render, secret):
    environ = {**EDGE, "KM_CLIENT_IDENTITY_SECRET": secret, **(RENDER if on_render else {})}
    with pytest.raises(ImproperlyConfigured, match="KM_CLIENT_IDENTITY_SECRET") as exc:
        load_throttle_identity_config(environ)
    assert secret.strip() not in str(exc.value)


# --- actual production startup path ---------------------------------------------------------------


def _import_wsgi(extra_env: dict[str, str]) -> subprocess.CompletedProcess:
    """gunicorn と同じく `shrine_project.wsgi` を import する（settings の import 時に検証が走る）。"""
    env = {k: v for k, v in os.environ.items() if k not in {"THROTTLE_TRUSTED_EDGE", "KM_CLIENT_IDENTITY_SECRET"}}
    env.pop("RENDER_EXTERNAL_HOSTNAME", None)
    env.update(extra_env)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(BACKEND), env.get("PYTHONPATH", "")]))
    return subprocess.run(
        [sys.executable, "-c", "import shrine_project.wsgi"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.parametrize(
    "extra_env, error",
    [
        pytest.param({**RENDER, **EDGE, "KM_CLIENT_IDENTITY_SECRET": SECRET}, None, id="render-valid"),
        pytest.param({}, None, id="local-unset"),
        pytest.param({**RENDER}, "THROTTLE_TRUSTED_EDGE must be", id="render-missing-edge"),
        pytest.param({**RENDER, "THROTTLE_TRUSTED_EDGE": "cloudflare"}, "unsupported value", id="render-malformed-edge"),
        pytest.param(
            {**RENDER, **EDGE, "KM_CLIENT_IDENTITY_SECRET": "short-secret-value"},
            "KM_CLIENT_IDENTITY_SECRET must be",
            id="render-short-secret",
        ),
    ],
)
def test_wsgi_startup_enforces_the_configuration(extra_env, error):
    result = _import_wsgi(extra_env)
    if error is None:
        assert result.returncode == 0, result.stderr[-2000:]
    else:
        assert result.returncode != 0
        assert "ImproperlyConfigured" in result.stderr
        assert error in result.stderr
        assert "short-secret-value" not in result.stderr + result.stdout
