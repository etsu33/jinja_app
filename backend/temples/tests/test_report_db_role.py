"""Contract of the read-only database role probe (`report_db_role` + start.sh gate)."""

import os
import subprocess
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test.utils import CaptureQueriesContext

from temples.management.commands import report_db_role as probe_module
from temples.management.commands.report_db_role import MARKER, PROBE_SQL, probe_db_role

START_SH = Path(__file__).resolve().parents[2] / "start.sh"
FLAG = "RUN_DB_ROLE_PROBE_ON_START"


class _FakeCursor:
    def __init__(self, row=("app_role", "login_role"), error=None):
        self.row = row
        self.error = error
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if self.error is not None:
            raise self.error

    def fetchone(self):
        return self.row


class _FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


def _run_command_with(monkeypatch, cursor):
    monkeypatch.setattr(probe_module, "connections", {"default": _FakeConnection(cursor)})
    out = StringIO()
    call_command("report_db_role", stdout=out)
    return out.getvalue()


def test_probe_sql_is_the_single_permitted_select():
    assert PROBE_SQL == "SELECT current_user, session_user"


def test_probe_executes_exactly_one_statement_without_params():
    cursor = _FakeCursor()

    assert probe_db_role(_FakeConnection(cursor)) == ("app_role", "login_role")
    assert cursor.executed == [(PROBE_SQL, None)]


def test_command_prints_only_the_marker_and_role_names(monkeypatch):
    cursor = _FakeCursor(row=("app_role", "login_role"))

    output = _run_command_with(monkeypatch, cursor)

    assert output.splitlines() == [f"{MARKER} current_user=app_role session_user=login_role"]
    assert cursor.executed == [(PROBE_SQL, None)]


def test_failure_prints_only_the_error_class_name(monkeypatch):
    secret_message = (
        'connection to server at "secret-host.example" port 6543, database "secretdb" failed'
    )
    cursor = _FakeCursor(error=RuntimeError(secret_message))
    monkeypatch.setattr(probe_module, "connections", {"default": _FakeConnection(cursor)})
    out = StringIO()

    with pytest.raises(CommandError) as excinfo:
        call_command("report_db_role", stdout=out)

    assert out.getvalue().splitlines() == [f"{MARKER} status=error error_type=RuntimeError"]
    for leaked in ("secret-host", "6543", "secretdb"):
        assert leaked not in out.getvalue()
        assert leaked not in str(excinfo.value)
    assert excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__ is True


@pytest.mark.django_db
def test_command_runs_one_select_on_the_real_connection():
    out = StringIO()

    with CaptureQueriesContext(connection) as ctx:
        call_command("report_db_role", stdout=out)

    assert [q["sql"] for q in ctx.captured_queries] == [PROBE_SQL]
    lines = out.getvalue().splitlines()
    assert len(lines) == 1
    with connection.cursor() as cur:
        cur.execute(PROBE_SQL)
        current_user, session_user = cur.fetchone()
    assert lines[0] == f"{MARKER} current_user={current_user} session_user={session_user}"
    assert connection.settings_dict["NAME"] not in lines[0]
    if connection.settings_dict.get("HOST"):
        assert connection.settings_dict["HOST"] not in lines[0]
    if connection.settings_dict.get("PASSWORD"):
        assert connection.settings_dict["PASSWORD"] not in lines[0]


# --------------------------------------------------------------------------- #
# start.sh gate: opt-in, one invocation, failure does not abort startup
# --------------------------------------------------------------------------- #

GUNICORN_MARKER = "STUB-GUNICORN-REACHED"
PROBE_INVOKED = "STUB-DB-ROLE-PROBE-INVOKED"

_PYTHON_STUB = """#!/usr/bin/env bash
if [ "$2" = "report_db_role" ]; then
  echo "{invoked} $*"
  exit {probe_exit}
fi
exit 0
"""

_GUNICORN_STUB = f"""#!/usr/bin/env bash
echo "{GUNICORN_MARKER}"
exit 0
"""


def _run_start_sh(tmp_path, *, probe_exit=0, env=None):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    (bin_dir / "python").write_text(
        _PYTHON_STUB.format(invoked=PROBE_INVOKED, probe_exit=probe_exit)
    )
    (bin_dir / "gunicorn").write_text(_GUNICORN_STUB)
    for name in ("python", "gunicorn"):
        (bin_dir / name).chmod(0o755)
    child_env = {"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}", "HOME": str(tmp_path)}
    child_env.update(env or {})
    return subprocess.run(
        ["bash", str(START_SH)],
        cwd=str(tmp_path),
        env=child_env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_start_sh_gate_is_opt_in_with_default_zero():
    script = START_SH.read_text(encoding="utf-8")

    assert f'if [ "${{{FLAG}:-0}}" = "1" ]; then' in script
    assert script.count("manage.py report_db_role") == 1


def test_probe_is_not_run_by_default(tmp_path):
    result = _run_start_sh(tmp_path)

    assert result.returncode == 0
    assert PROBE_INVOKED not in result.stdout
    assert "Skipping database role probe." in result.stdout
    assert GUNICORN_MARKER in result.stdout


def test_probe_runs_once_when_enabled(tmp_path):
    result = _run_start_sh(tmp_path, env={FLAG: "1"})

    assert result.returncode == 0
    assert result.stdout.count(PROBE_INVOKED) == 1
    assert "Database role probe completed." in result.stdout
    assert GUNICORN_MARKER in result.stdout


def test_probe_failure_does_not_abort_startup(tmp_path):
    result = _run_start_sh(tmp_path, probe_exit=1, env={FLAG: "1"})

    assert result.returncode == 0
    assert "ERROR: Database role probe failed (exit=1); startup continues." in result.stdout
    assert "Database role probe completed." not in result.stdout
    assert GUNICORN_MARKER in result.stdout
