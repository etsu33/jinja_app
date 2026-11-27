"""本番の管理画面で /static/ が 404 になった件の回帰テスト。

原因は3つ: WhiteNoise がミドルウェアに無い / collectstatic がどこでも走らない /
staticfiles ストレージが WhiteNoise 用でない。ここではその3つと、実際に
collectstatic した管理画面の CSS が DEBUG=False で 200 になることを確かめる。
"""

import os
import subprocess
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command
from django.test import Client, override_settings

START_SH = Path(__file__).resolve().parents[1] / "start.sh"
WHITENOISE_MIDDLEWARE = "whitenoise.middleware.WhiteNoiseMiddleware"
WHITENOISE_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"


def test_whitenoise_middleware_sits_right_after_security_middleware():
    middleware = list(settings.MIDDLEWARE)
    assert WHITENOISE_MIDDLEWARE in middleware
    assert middleware.index(WHITENOISE_MIDDLEWARE) == (
        middleware.index("django.middleware.security.SecurityMiddleware") + 1
    )


def test_staticfiles_storage_is_whitenoise():
    assert settings.STORAGES["staticfiles"]["BACKEND"] == WHITENOISE_STORAGE


def test_static_root_is_set():
    assert settings.STATIC_ROOT


def test_admin_css_is_served_with_debug_false_after_collectstatic(tmp_path):
    with override_settings(DEBUG=False, STATIC_ROOT=tmp_path):
        call_command("collectstatic", "--noinput", verbosity=0)
        assert (tmp_path / "admin" / "css" / "base.css").is_file()

        # WhiteNoise は起動時に STATIC_ROOT を読むので、設定を変えたあとで新しい Client を作る。
        response = Client().get("/static/admin/css/base.css")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/css")


# --------------------------------------------------------------------------- #
# start.sh: collectstatic は毎回 gunicorn の前に走り、失敗しても起動を止めない
# --------------------------------------------------------------------------- #

GUNICORN_MARKER = "STUB-GUNICORN-REACHED"

_PYTHON_STUB = """#!/usr/bin/env bash
if [ "$2" = "collectstatic" ]; then
  echo "STUB-COLLECTSTATIC $*"
  exit {collectstatic_exit}
fi
exit 0
"""

_GUNICORN_STUB = f"""#!/usr/bin/env bash
echo "{GUNICORN_MARKER}"
exit 0
"""


def _run_start_sh(tmp_path, *, collectstatic_exit: int):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    (bin_dir / "python").write_text(_PYTHON_STUB.format(collectstatic_exit=collectstatic_exit))
    (bin_dir / "gunicorn").write_text(_GUNICORN_STUB)
    for name in ("python", "gunicorn"):
        (bin_dir / name).chmod(0o755)

    return subprocess.run(
        ["bash", str(START_SH)],
        cwd=str(tmp_path),
        env={"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}", "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_start_sh_runs_collectstatic_once_before_gunicorn():
    text = START_SH.read_text(encoding="utf-8")
    assert text.count("python manage.py collectstatic --noinput") == 1
    assert text.index("python manage.py collectstatic --noinput") < text.index("exec gunicorn")


def test_start_sh_collectstatic_runs_by_default(tmp_path):
    result = _run_start_sh(tmp_path, collectstatic_exit=0)

    assert result.returncode == 0
    assert "STUB-COLLECTSTATIC manage.py collectstatic --noinput" in result.stdout
    assert "Static files collected." in result.stdout
    assert result.stdout.index("STUB-COLLECTSTATIC") < result.stdout.index(GUNICORN_MARKER)


@pytest.mark.parametrize("exit_code", (1, 2))
def test_start_sh_collectstatic_failure_does_not_stop_startup(tmp_path, exit_code):
    result = _run_start_sh(tmp_path, collectstatic_exit=exit_code)

    assert result.returncode == 0
    assert f"ERROR: collectstatic failed (exit={exit_code})" in result.stdout
    assert "Static files collected." not in result.stdout
    assert GUNICORN_MARKER in result.stdout
