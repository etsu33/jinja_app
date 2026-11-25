"""SPH-02: DJANGO_SECRET_KEY は未設定なら起動を止める（shrine_project/secret_key.py）."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from shrine_project.secret_key import ci_tooling_fallback_allowed, resolve_secret_key

BACKEND = Path(__file__).resolve().parents[1]
GHA_TOOLING = {"GITHUB_ACTIONS": "true", "IS_PYTEST": "1"}


def test_present_key_is_returned_unchanged():
    value = "  configured-value-with-surrounding-space  "
    assert resolve_secret_key({"DJANGO_SECRET_KEY": value}) == value


def test_present_key_wins_over_ci_tooling_fallback():
    assert resolve_secret_key({**GHA_TOOLING, "DJANGO_SECRET_KEY": "configured"}) == "configured"


@pytest.mark.parametrize(
    "environ",
    [
        pytest.param({}, id="missing"),
        pytest.param({"DJANGO_SECRET_KEY": ""}, id="empty"),
        pytest.param({"DJANGO_SECRET_KEY": "   \t\n"}, id="whitespace-only"),
        pytest.param({"CI": "true"}, id="generic-ci-flag-alone"),
        pytest.param(
            {"CI": "true", "IS_PYTEST": "1"}, id="ci-and-is-pytest-without-github-actions"
        ),
        pytest.param({"IS_PYTEST": "1"}, id="is-pytest-alone"),
        pytest.param({"GITHUB_ACTIONS": "true"}, id="github-actions-without-is-pytest"),
        pytest.param(
            {"GITHUB_ACTIONS": "1", "IS_PYTEST": "1"}, id="github-actions-not-literal-true"
        ),
        pytest.param({**GHA_TOOLING, "RENDER": "true"}, id="github-tooling-on-render"),
        pytest.param(
            {**GHA_TOOLING, "RENDER_EXTERNAL_HOSTNAME": "svc.example"},
            id="github-tooling-render-host",
        ),
        pytest.param(
            {**GHA_TOOLING, "RENDER_SERVICE_ID": "srv-x"}, id="github-tooling-render-service"
        ),
        pytest.param(
            {**GHA_TOOLING, "DJANGO_SECRET_KEY": " ", "RENDER": "true"}, id="blank-on-render"
        ),
    ],
)
def test_missing_or_blank_key_fails_closed(environ):
    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY is not set"):
        resolve_secret_key(environ)


def test_github_actions_tooling_gets_a_random_per_call_key():
    first = resolve_secret_key(GHA_TOOLING)
    second = resolve_secret_key({**GHA_TOOLING, "DJANGO_SECRET_KEY": "  "})

    assert len(first) >= 50 and len(second) >= 50
    assert first != second
    assert not first.startswith("django-insecure")


@pytest.mark.parametrize("is_pytest", ["1", "true", "yes", "on", "TRUE"])
def test_ci_tooling_fallback_accepts_truthy_is_pytest(is_pytest):
    assert ci_tooling_fallback_allowed({"GITHUB_ACTIONS": "true", "IS_PYTEST": is_pytest})


def test_error_message_does_not_echo_configured_values():
    with pytest.raises(ImproperlyConfigured) as exc:
        resolve_secret_key({"DJANGO_SECRET_KEY": "   ", "RENDER_EXTERNAL_HOSTNAME": "svc.example"})
    assert "svc.example" not in str(exc.value)


# --- startup path（gunicorn と同じく shrine_project.wsgi を import する） -------------------------------------


def _import_wsgi(secret: str) -> subprocess.CompletedProcess:
    drop = {
        "GITHUB_ACTIONS",
        "IS_PYTEST",
        "PYTEST_CURRENT_TEST",
        "CI",
        "RENDER",
        "RENDER_EXTERNAL_HOSTNAME",
        "RENDER_SERVICE_ID",
        "THROTTLE_TRUSTED_EDGE",
        "KM_CLIENT_IDENTITY_SECRET",
    }
    env = {k: v for k, v in os.environ.items() if k not in drop}
    # 空文字は「設定されているが空」。backend/.env.local は既存の環境変数を上書きしないため、開発機でも再現性がある
    env["DJANGO_SECRET_KEY"] = secret
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(BACKEND), env.get("PYTHONPATH", "")]))
    return subprocess.run(
        [sys.executable, "-c", "import shrine_project.wsgi"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_normal_runtime_startup_refuses_blank_key():
    result = _import_wsgi("")

    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr
    assert "DJANGO_SECRET_KEY is not set" in result.stderr


def test_normal_runtime_startup_succeeds_with_a_configured_key():
    result = _import_wsgi("startup-probe-secret-not-used-elsewhere")

    assert result.returncode == 0, result.stderr
    assert "startup-probe-secret-not-used-elsewhere" not in result.stdout + result.stderr
