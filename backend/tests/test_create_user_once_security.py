"""SEC-B02: `backend/create_user_once.py` superuser bootstrap must be explicit, fail closed and never modify users.

Synthetic credentials only（`.invalid` addresses, throwaway passwords）. Local test database only; no network.
Covers: missing explicit authorization, missing credentials, an existing user（rejected and left unchanged）, a
successful creation（superuser）, and the invocation paths recorded in
`docs/audit/sec-b02-bootstrap-exit-status-compatibility-2026-11-03.md`.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

BACKEND = Path(__file__).resolve().parents[1]
SCRIPT = BACKEND / "create_user_once.py"
_spec = importlib.util.spec_from_file_location("create_user_once_under_test", SCRIPT)
cuo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cuo)

USERNAME = "bootstrap_once_fixture"
EMAIL = "bootstrap-once@example.invalid"
PASSWORD = "only-a-test-credential-not-for-production-7c1"
FULL_ENV = {
    "KAMIMUSUBI_BOOTSTRAP_SUPERUSER": "1",
    "KAMIMUSUBI_BOOTSTRAP_USERNAME": USERNAME,
    "KAMIMUSUBI_BOOTSTRAP_EMAIL": EMAIL,
    "KAMIMUSUBI_BOOTSTRAP_PASSWORD": PASSWORD,
}


def _snapshot(user):
    """Every field a bootstrap could plausibly touch; the hashed password includes its salt."""
    return (
        user.username,
        user.email,
        user.password,
        user.is_superuser,
        user.is_staff,
        user.is_active,
        user.last_login,
    )


# --------------------------------------------------------------------------- #
# 1. No explicit authorization
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
@pytest.mark.parametrize("flag", [None, "", "0", "true", "yes", " 1", "1 ", "01"])
def test_missing_or_non_exact_authorization_is_refused(django_user_model, flag):
    env = {k: v for k, v in FULL_ENV.items() if k != "KAMIMUSUBI_BOOTSTRAP_SUPERUSER"}
    if flag is not None:
        env["KAMIMUSUBI_BOOTSTRAP_SUPERUSER"] = flag
    before = django_user_model.objects.count()
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(RuntimeError, match="^explicit_bootstrap_authorization_required$"):
            cuo.create_user_once()
    assert django_user_model.objects.count() == before


@pytest.mark.django_db
def test_initial_user_flag_does_not_authorize_superuser_bootstrap(django_user_model):
    """The two bootstrap paths use separate flags; the weaker one never grants a superuser."""
    env = {k: v for k, v in FULL_ENV.items() if k != "KAMIMUSUBI_BOOTSTRAP_SUPERUSER"}
    env["KAMIMUSUBI_BOOTSTRAP_INITIAL_USER"] = "1"
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(RuntimeError, match="explicit_bootstrap_authorization_required"):
            cuo.create_user_once()
    assert not django_user_model.objects.filter(username=USERNAME).exists()


# --------------------------------------------------------------------------- #
# 2. Missing credentials
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
@pytest.mark.parametrize(
    "key,value",
    [
        ("KAMIMUSUBI_BOOTSTRAP_USERNAME", None),
        ("KAMIMUSUBI_BOOTSTRAP_USERNAME", ""),
        ("KAMIMUSUBI_BOOTSTRAP_USERNAME", "   "),
        ("KAMIMUSUBI_BOOTSTRAP_EMAIL", None),
        ("KAMIMUSUBI_BOOTSTRAP_EMAIL", "  "),
        ("KAMIMUSUBI_BOOTSTRAP_PASSWORD", None),
        ("KAMIMUSUBI_BOOTSTRAP_PASSWORD", ""),
    ],
)
def test_missing_credentials_are_refused(django_user_model, key, value):
    env = dict(FULL_ENV)
    if value is None:
        del env[key]
    else:
        env[key] = value
    before = django_user_model.objects.count()
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(RuntimeError, match="^bootstrap_credentials_missing$"):
            cuo.create_user_once()
    assert django_user_model.objects.count() == before


# --------------------------------------------------------------------------- #
# 3. Existing user: refused, and never modified or escalated
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_existing_regular_user_is_refused_and_not_escalated(django_user_model):
    existing = django_user_model.objects.create_user(
        username=USERNAME, email="existing@example.invalid", password="pre-existing-test-password"
    )
    before = _snapshot(existing)
    count = django_user_model.objects.count()
    with patch.dict(os.environ, FULL_ENV, clear=True):
        with pytest.raises(RuntimeError, match="^bootstrap_user_already_exists$"):
            cuo.create_user_once()
    after = django_user_model.objects.get(pk=existing.pk)
    assert _snapshot(after) == before
    assert not after.is_superuser and not after.is_staff  # no privilege escalation
    assert not after.check_password(PASSWORD)  # the bootstrap password was not applied
    assert django_user_model.objects.count() == count


@pytest.mark.django_db
def test_existing_superuser_is_refused_and_unchanged(django_user_model):
    existing = django_user_model.objects.create_superuser(
        username=USERNAME,
        email="existing-admin@example.invalid",
        password="pre-existing-admin-test",
    )
    before = _snapshot(existing)
    with patch.dict(os.environ, FULL_ENV, clear=True):
        with pytest.raises(RuntimeError, match="^bootstrap_user_already_exists$"):
            cuo.create_user_once()
    assert _snapshot(django_user_model.objects.get(pk=existing.pk)) == before


# --------------------------------------------------------------------------- #
# 4. Success: a superuser, created once
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_success_creates_a_superuser_and_prints_no_credentials(django_user_model, capsys):
    with patch.dict(os.environ, FULL_ENV, clear=True):
        cuo.create_user_once()
    user = django_user_model.objects.get(username=USERNAME)
    assert user.is_superuser and user.is_staff and user.is_active
    assert user.email == EMAIL
    assert user.check_password(PASSWORD)
    assert user.password != PASSWORD  # stored hashed
    out = capsys.readouterr()
    assert out.out.strip() == "bootstrap_user_created"
    for secret in (PASSWORD, USERNAME, EMAIL):
        assert secret not in out.out and secret not in out.err


@pytest.mark.django_db
def test_second_run_after_success_is_refused_and_keeps_the_first_user(django_user_model):
    with patch.dict(os.environ, FULL_ENV, clear=True):
        cuo.create_user_once()
        first = _snapshot(django_user_model.objects.get(username=USERNAME))
        with patch.dict(os.environ, {"KAMIMUSUBI_BOOTSTRAP_PASSWORD": "a-different-test-password"}):
            with pytest.raises(RuntimeError, match="bootstrap_user_already_exists"):
                cuo.create_user_once()
    assert _snapshot(django_user_model.objects.get(username=USERNAME)) == first


def test_script_contains_no_fixed_credentials():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "create_superuser(username=username, email=email, password=password)" in source
    for line in source.splitlines():
        stripped = line.strip()
        # Credentials only ever come from os.environ; no string literal is assigned to them.
        if stripped.startswith(("username =", "email =", "password =")):
            assert "os.environ.get(" in stripped


def _keep_test_db_connection():
    """`run_from_argv` closes every DB connection on exit; keep the test transaction's connection usable."""
    return patch("django.core.management.base.connections.close_all")


# --------------------------------------------------------------------------- #
# Invocation paths and exit status（compatibility record）
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_shell_command_import_and_call_is_the_working_path(django_user_model):
    """`manage.py shell -c "from create_user_once import create_user_once; create_user_once()"` creates."""
    with patch.dict(os.environ, FULL_ENV, clear=True):
        call_command(
            "shell",
            command=(
                "import importlib.util\n"
                f"spec = importlib.util.spec_from_file_location('cuo_shell', {str(SCRIPT)!r})\n"
                "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
                "m.create_user_once()\n"
            ),
        )
    assert django_user_model.objects.get(username=USERNAME).is_superuser


@pytest.mark.django_db
def test_shell_command_existing_user_raises_so_manage_py_exits_non_zero(django_user_model):
    django_user_model.objects.create_user(username=USERNAME, password="pre-existing-test-password")
    with patch.dict(os.environ, FULL_ENV, clear=True):
        with pytest.raises(RuntimeError, match="bootstrap_user_already_exists"):
            call_command(
                "shell",
                command=(
                    "import importlib.util\n"
                    f"spec = importlib.util.spec_from_file_location('cuo_shell', {str(SCRIPT)!r})\n"
                    "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
                    "m.create_user_once()\n"
                ),
            )


@pytest.mark.django_db
def test_characterization_piping_the_file_into_shell_creates_nothing(django_user_model):
    """Characterization, not endorsement: `manage.py shell < create_user_once.py` is a silent no-op.

    The shell executes the source with `__name__` set to the shell module, so the `__main__` guard never calls
    `create_user_once()`. The pre-PR script ran at module level on this path. Recorded as a compatibility finding.
    """
    with patch.dict(os.environ, FULL_ENV, clear=True):
        call_command("shell", command=SCRIPT.read_text(encoding="utf-8"))
    assert not django_user_model.objects.filter(username=USERNAME).exists()


def test_standalone_script_without_django_settings_exits_non_zero_without_leaking():
    """`python create_user_once.py` cannot configure Django; it fails（as the pre-PR script also did）."""
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), **FULL_ENV}
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        cwd=BACKEND,
        timeout=120,
    )
    assert proc.returncode != 0
    assert "ImproperlyConfigured" in proc.stderr
    for secret in (PASSWORD, EMAIL):
        assert secret not in proc.stdout and secret not in proc.stderr


@pytest.mark.django_db
def test_initial_user_command_existing_user_exits_with_status_1(django_user_model, capsys):
    """`manage.py create_initial_user` with an existing user: exit status 1 now（was 0 before the PR）."""
    from users.management.commands.create_initial_user import Command

    existing = django_user_model.objects.create_user(
        username=USERNAME, email="existing@example.invalid", password="pre-existing-test-password"
    )
    before = _snapshot(existing)
    env = {
        "KAMIMUSUBI_BOOTSTRAP_INITIAL_USER": "1",
        "KAMIMUSUBI_BOOTSTRAP_USERNAME": USERNAME,
        "KAMIMUSUBI_BOOTSTRAP_EMAIL": EMAIL,
        "KAMIMUSUBI_BOOTSTRAP_PASSWORD": PASSWORD,
    }
    with patch.dict(os.environ, env, clear=True), _keep_test_db_connection():
        with pytest.raises(SystemExit) as excinfo:
            Command().run_from_argv(["manage.py", "create_initial_user"])
    assert excinfo.value.code == 1
    assert "bootstrap_user_already_exists" in capsys.readouterr().err
    assert _snapshot(django_user_model.objects.get(pk=existing.pk)) == before


@pytest.mark.django_db
def test_initial_user_command_refusals_also_exit_with_status_1():
    from users.management.commands.create_initial_user import Command

    with patch.dict(os.environ, {}, clear=True), _keep_test_db_connection():
        with pytest.raises(SystemExit) as excinfo:
            Command().run_from_argv(["manage.py", "create_initial_user"])
    assert excinfo.value.code == 1
    with patch.dict(os.environ, {"KAMIMUSUBI_BOOTSTRAP_INITIAL_USER": "1"}, clear=True):
        with pytest.raises(CommandError, match="bootstrap_credentials_missing"):
            call_command("create_initial_user")
