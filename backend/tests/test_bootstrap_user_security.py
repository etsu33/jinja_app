"""SEC-B02: user bootstrap must be explicit, fail closed, never modify users and never create a superuser.

Mother Ship decision C-1 = Option C: the obsolete superuser script `backend/create_user_once.py` was deleted
（PR #3429）. The only surviving bootstrap is `manage.py create_initial_user`, which creates a **regular** user.

Synthetic credentials only（`.invalid` addresses, throwaway passwords）. Local test database only; no network.
Record: `docs/audit/sec-b02-bootstrap-exit-status-compatibility-2026-11-03.md`.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.management import call_command, get_commands
from django.core.management.base import CommandError

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
DELETED_SCRIPT = "create_user_once"

USERNAME = "bootstrap_initial_fixture"
EMAIL = "bootstrap-initial@example.invalid"
PASSWORD = "only-a-test-credential-not-for-production-3d9"
FULL_ENV = {
    "KAMIMUSUBI_BOOTSTRAP_INITIAL_USER": "1",
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


def _keep_test_db_connection():
    """`run_from_argv` closes every DB connection on exit; keep the test transaction's connection usable."""
    return patch("django.core.management.base.connections.close_all")


def _run_command_exit_code(env, capsys):
    from users.management.commands.create_initial_user import Command

    with patch.dict(os.environ, env, clear=True), _keep_test_db_connection():
        with pytest.raises(SystemExit) as excinfo:
            Command().run_from_argv(["manage.py", "create_initial_user"])
    return excinfo.value.code, capsys.readouterr()


# --------------------------------------------------------------------------- #
# C-1 / Option C: the obsolete superuser script is gone and nothing executable refers to it
# --------------------------------------------------------------------------- #


def test_obsolete_superuser_script_is_deleted():
    assert not (BACKEND / f"{DELETED_SCRIPT}.py").exists()


def test_no_executable_reference_to_the_deleted_script():
    """Tracked code, startup, CI, Docker, Makefile and deployment files must not call the deleted script."""
    proc = subprocess.run(
        ["git", "grep", "-n", "-I", DELETED_SCRIPT, "--", "."],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode in (0, 1), "git grep failed"
    allowed = (
        "docs/",  # audit records describe the deletion
        "backend/tests/test_bootstrap_user_security.py",  # this guard
    )
    offenders = [
        line.split(":", 1)[0]
        for line in proc.stdout.splitlines()
        if line and not line.startswith(allowed)
    ]
    assert offenders == []


def test_no_superuser_bootstrap_command_or_flag_remains():
    """No management command creates a superuser from bootstrap variables; the old flag is obsolete."""
    commands = get_commands()
    assert "create_initial_user" in commands
    proc = subprocess.run(
        ["git", "grep", "-n", "-I", "KAMIMUSUBI_BOOTSTRAP_SUPERUSER", "--", "."],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode in (0, 1), "git grep failed"
    offenders = [
        line.split(":", 1)[0]
        for line in proc.stdout.splitlines()
        if line and not line.startswith(("docs/", "backend/tests/test_bootstrap_user_security.py"))
    ]
    assert offenders == []


@pytest.mark.django_db
def test_obsolete_superuser_flag_does_not_authorize_anything(django_user_model):
    env = {k: v for k, v in FULL_ENV.items() if k != "KAMIMUSUBI_BOOTSTRAP_INITIAL_USER"}
    env["KAMIMUSUBI_BOOTSTRAP_SUPERUSER"] = "1"
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(CommandError, match="^explicit_bootstrap_authorization_required$"):
            call_command("create_initial_user")
    assert not django_user_model.objects.filter(username=USERNAME).exists()


# --------------------------------------------------------------------------- #
# Surviving command: explicit opt-in
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
@pytest.mark.parametrize("flag", [None, "", "0", "true", "yes", " 1", "1 ", "01"])
def test_missing_or_non_exact_authorization_is_refused(django_user_model, flag):
    env = {k: v for k, v in FULL_ENV.items() if k != "KAMIMUSUBI_BOOTSTRAP_INITIAL_USER"}
    if flag is not None:
        env["KAMIMUSUBI_BOOTSTRAP_INITIAL_USER"] = flag
    before = django_user_model.objects.count()
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(CommandError, match="^explicit_bootstrap_authorization_required$"):
            call_command("create_initial_user")
    assert django_user_model.objects.count() == before


# --------------------------------------------------------------------------- #
# Surviving command: missing credentials
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
        with pytest.raises(CommandError, match="^bootstrap_credentials_missing$"):
            call_command("create_initial_user")
    assert django_user_model.objects.count() == before


# --------------------------------------------------------------------------- #
# Surviving command: existing user is refused and never modified, escalated or demoted
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_existing_regular_user_is_refused_and_unchanged(django_user_model):
    existing = django_user_model.objects.create_user(
        username=USERNAME, email="existing@example.invalid", password="pre-existing-test-password"
    )
    before = _snapshot(existing)
    count = django_user_model.objects.count()
    with patch.dict(os.environ, FULL_ENV, clear=True):
        with pytest.raises(CommandError, match="^bootstrap_user_already_exists$"):
            call_command("create_initial_user")
    after = django_user_model.objects.get(pk=existing.pk)
    assert _snapshot(after) == before
    assert not after.check_password(PASSWORD)  # the bootstrap password was not applied
    assert django_user_model.objects.count() == count


@pytest.mark.django_db
def test_existing_superuser_is_refused_and_not_demoted(django_user_model):
    existing = django_user_model.objects.create_superuser(
        username=USERNAME,
        email="existing-admin@example.invalid",
        password="pre-existing-admin-test",
    )
    before = _snapshot(existing)
    with patch.dict(os.environ, FULL_ENV, clear=True):
        with pytest.raises(CommandError, match="^bootstrap_user_already_exists$"):
            call_command("create_initial_user")
    assert _snapshot(django_user_model.objects.get(pk=existing.pk)) == before


# --------------------------------------------------------------------------- #
# Surviving command: success creates a regular user only
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_success_creates_a_regular_user_never_a_superuser(django_user_model, capsys):
    with patch.dict(os.environ, FULL_ENV, clear=True):
        call_command("create_initial_user")
    user = django_user_model.objects.get(username=USERNAME)
    assert not user.is_superuser and not user.is_staff  # no privileged bootstrap remains
    assert user.is_active and user.email == EMAIL
    assert user.check_password(PASSWORD) and user.password != PASSWORD  # stored hashed
    out = capsys.readouterr()
    assert "initial_user_created" in out.out
    for secret in (PASSWORD, USERNAME, EMAIL):
        assert secret not in out.out and secret not in out.err


@pytest.mark.django_db
def test_second_run_is_refused_and_keeps_the_first_user(django_user_model):
    with patch.dict(os.environ, FULL_ENV, clear=True):
        call_command("create_initial_user")
        first = _snapshot(django_user_model.objects.get(username=USERNAME))
        with patch.dict(os.environ, {"KAMIMUSUBI_BOOTSTRAP_PASSWORD": "a-different-test-password"}):
            with pytest.raises(CommandError, match="bootstrap_user_already_exists"):
                call_command("create_initial_user")
    assert _snapshot(django_user_model.objects.get(username=USERNAME)) == first


# --------------------------------------------------------------------------- #
# Surviving command: exit status（compatibility record）
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_existing_user_exits_with_status_1(django_user_model, capsys):
    """`manage.py create_initial_user` with an existing user: exit status 1（it was 0 before PR #3429）."""
    existing = django_user_model.objects.create_user(
        username=USERNAME, email="existing@example.invalid", password="pre-existing-test-password"
    )
    before = _snapshot(existing)
    code, out = _run_command_exit_code(FULL_ENV, capsys)
    assert code == 1
    assert "bootstrap_user_already_exists" in out.err
    assert _snapshot(django_user_model.objects.get(pk=existing.pk)) == before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "env,token",
    [
        ({}, "explicit_bootstrap_authorization_required"),
        ({"KAMIMUSUBI_BOOTSTRAP_INITIAL_USER": "1"}, "bootstrap_credentials_missing"),
    ],
)
def test_refusals_exit_with_status_1_without_leaking(django_user_model, capsys, env, token):
    code, out = _run_command_exit_code(env, capsys)
    assert code == 1
    assert token in out.err
    assert PASSWORD not in out.out + out.err
    assert not django_user_model.objects.filter(username=USERNAME).exists()


def test_command_source_contains_no_fixed_credentials():
    source = (BACKEND / "users/management/commands/create_initial_user.py").read_text(
        encoding="utf-8"
    )
    assert "create_superuser" not in source  # regular-user bootstrap only
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(("username =", "email =", "password =")):
            assert "os.environ.get(" in stripped
