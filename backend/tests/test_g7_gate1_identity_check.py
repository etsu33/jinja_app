"""Synthetic offline tests for `scripts/g7_gate1_identity_check.py`（G7-A1..A6, LOCAL_OFFLINE_REDACTED）.

Synthetic values only（`.invalid` hosts, fake passwords and references）. No database, DNS or network: socket
creation and name resolution are made to fail for every test in this module.
"""

from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "g7_gate1_identity_check.py"
_spec = importlib.util.spec_from_file_location("g7_gate1_identity_check", SCRIPT)
g7 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g7)

PROJECT = "synthprojref0001"
OTHER_PROJECT = "synthprojref0002"
HOST = "pooler-synthetic.example.invalid"
ROLE = "kamimusubi_audit_ro"
DB = "synthetic_db"
PASSWORD = "SYNTH-p@ss:/?#[]%&=+ word-7f1"  # reserved URL characters, percent-encoded in the URL
SECRETS = (
    PROJECT,
    OTHER_PROJECT,
    HOST,
    ROLE,
    DB,
    PASSWORD,
    quote(PASSWORD, safe=""),
    "pooler-synthetic",
)

TARGET = {
    "project_ref": PROJECT,
    "pooler_host": HOST,
    "endpoint_kind": "SESSION_POOLER",
    "port": 5432,
    "dbname": DB,
    "role": ROLE,
}
ALL_PASS = {field: "PASS" for field in g7.FIELDS}


def _url(
    *,
    user=f"{ROLE}.{PROJECT}",
    password=PASSWORD,
    host=HOST,
    port=5432,
    db=DB,
    query="",
    scheme="postgresql",
):
    auth = quote(user, safe="") if user is not None else ""
    if password is not None:
        auth += ":" + quote(password, safe="")
    netloc = f"{auth}@{host}" if user is not None else host
    if port is not None:
        netloc += f":{port}"
    url = f"{scheme}://{netloc}/{db}"
    return f"{url}?{query}" if query else url


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setattr(socket, "gethostbyname", refuse)


@pytest.fixture
def target_file(tmp_path):
    def _write(data=TARGET, mode=0o600, raw=None):
        path = tmp_path / "approved-target.json"
        path.write_text(raw if raw is not None else json.dumps(data), encoding="utf-8")
        os.chmod(path, mode)
        return str(path)

    return _write


def _assert_no_secrets(*texts):
    for text in texts:
        for secret in SECRETS:
            assert secret not in text


# --------------------------------------------------------------------------- #
# field evaluation
# --------------------------------------------------------------------------- #


def test_all_six_fields_match():
    result = g7.evaluate(_url(), TARGET)
    assert result == ALL_PASS
    assert g7.overall(result) == "PASS"


def test_transaction_pooler_matches_when_approved():
    target = dict(TARGET, endpoint_kind="TRANSACTION_POOLER", port=6543)
    assert g7.evaluate(_url(port=6543), target) == ALL_PASS


@pytest.mark.parametrize(
    "url_kwargs, target_changes, field",
    [
        ({"user": f"{ROLE}.{OTHER_PROJECT}"}, {}, "a1_project"),  # project mismatch
        (
            {"host": "other-pooler.example.invalid"},
            {},
            "a2_tenant",
        ),  # tenant (pooler host) mismatch
        (
            {"port": 6543},
            {"port": 6543},
            "a3_endpoint_kind",
        ),  # transaction port vs approved session kind
        ({"db": "other_db"}, {}, "a4_database_name"),
        ({"port": 6543}, {}, "a5_port"),
        ({"user": f"other_role.{PROJECT}"}, {}, "a6_username_format"),
        ({"user": ROLE}, {}, "a6_username_format"),  # no tenant suffix at all
    ],
)
def test_single_field_mismatch_is_fail(url_kwargs, target_changes, field):
    result = g7.evaluate(_url(**url_kwargs), dict(TARGET, **target_changes))
    assert result[field] == "FAIL"
    assert g7.overall(result) == "FAIL"


def test_project_is_never_inferred_from_the_host():
    # the reference appears in the host name only; the user name has no suffix
    result = g7.evaluate(
        _url(user=ROLE, host=f"{PROJECT}.example.invalid"),
        dict(TARGET, pooler_host=f"{PROJECT}.example.invalid"),
    )
    assert result["a1_project"] == "UNKNOWN"
    assert g7.overall(result) != "PASS"


@pytest.mark.parametrize(
    "url",
    [
        "not a url",
        "",
        "mysql://u.r:p@h:5432/db",
        _url() + "#fragment",
        _url(port=None).replace(f"@{HOST}", f"@{HOST}:notaport"),
        _url(port=99999),
        f"postgresql://{ROLE}.{PROJECT}:raw@at@{HOST}:5432/{DB}",  # unencoded '@' in the password
        f"postgresql://{HOST}:5432/{DB}",  # no user
        f" {_url()}",
    ],
)
def test_malformed_url_is_unknown_everywhere(url):
    result = g7.evaluate(url, TARGET)
    assert result == {field: "UNKNOWN" for field in g7.FIELDS}
    assert g7.overall(result) == "UNKNOWN"


@pytest.mark.parametrize(
    "url, unknown_fields",
    [
        (_url(port=None), {"a3_endpoint_kind", "a5_port"}),  # libpq default port is not evidence
        (_url(port=5433), {"a3_endpoint_kind"}),  # unsupported port for the pooler formats
        (
            _url(user=f"{ROLE}.{PROJECT}.extra"),
            {"a1_project", "a3_endpoint_kind", "a6_username_format"},
        ),
        (_url(query="host=other.example.invalid"), {"a2_tenant", "a3_endpoint_kind"}),
        (_url(query="user=someone"), {"a1_project", "a6_username_format"}),
        (_url(query="dbname=other"), {"a4_database_name"}),
        (_url(query="service=svc"), set(g7.FIELDS)),
    ],
)
def test_ambiguous_or_unsupported_values_are_unknown(url, unknown_fields):
    result = g7.evaluate(url, TARGET)
    for field in unknown_fields:
        assert result[field] == "UNKNOWN", field
    assert g7.overall(result) != "PASS"


@pytest.mark.parametrize(
    "url",
    [
        f"postgresql://{ROLE}.{PROJECT}:x@host-a.example.invalid,host-b.example.invalid:5432/{DB}",  # multi-host
        f"postgresql://{ROLE}.{PROJECT}:x@[2001:db8::1]:5432/{DB}",  # IPv6 literal
    ],
)
def test_unsupported_endpoint_format_is_unknown(url):
    assert g7.evaluate(url, TARGET) == {field: "UNKNOWN" for field in g7.FIELDS}


def test_direct_style_endpoint_is_not_supported():
    """A direct-connection style (host differs from the approved pooler, user without suffix) never PASSes."""
    result = g7.evaluate(_url(user=ROLE, host=f"db.{PROJECT}.example.invalid"), TARGET)
    assert result["a1_project"] == "UNKNOWN"
    assert result["a3_endpoint_kind"] == "UNKNOWN"
    assert g7.overall(result) != "PASS"


@pytest.mark.parametrize(
    "changes",
    [
        {"project_ref": None},
        {"project_ref": "has.dot"},
        {"pooler_host": ""},
        {"endpoint_kind": "DIRECT"},
        {"port": "5432"},
        {"port": True},
        {"dbname": " padded"},
        {"role": None},
    ],
)
def test_missing_or_invalid_target_values_are_unknown(changes):
    target = {k: v for k, v in dict(TARGET, **changes).items() if v is not None}
    result = g7.evaluate(_url(), target)
    assert "UNKNOWN" in result.values()
    assert g7.overall(result) != "PASS"


def test_missing_target_inventory_is_unknown_everywhere():
    assert g7.evaluate(_url(), None) == {field: "UNKNOWN" for field in g7.FIELDS}


def test_reserved_characters_in_credentials_are_handled_and_never_returned():
    result = g7.evaluate(_url(), TARGET)
    assert result == ALL_PASS
    _assert_no_secrets(json.dumps(result), g7.render(result))


# --------------------------------------------------------------------------- #
# CLI: inputs, redaction and fail-closed exit status
# --------------------------------------------------------------------------- #


def _run(capsys, argv, url=None):
    env = {"DATABASE_URL": url} if url is not None else {}
    code = g7.main(argv, environ=env)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_cli_all_pass_prints_tokens_only(capsys, target_file):
    code, out, err = _run(capsys, ["--target", target_file()], _url())
    assert code == 0
    assert "g7_gate1_overall=PASS" in out
    assert "g7_satisfied=false" in out  # G7-B1 / B2 stay separate
    assert "g7_b1_catalog=not_evaluated" in out
    _assert_no_secrets(out, err)
    for line in out.strip().splitlines():
        key, _, value = line.partition("=")
        assert key.startswith("g7_") and value.replace("_", "").isalnum()


def test_cli_mismatch_fails_closed(capsys, target_file):
    code, out, err = _run(capsys, ["--target", target_file()], _url(user=f"{ROLE}.{OTHER_PROJECT}"))
    assert code == 1
    assert "g7_a1_project=FAIL" in out and "g7_gate1_overall=FAIL" in out
    _assert_no_secrets(out, err)


@pytest.mark.parametrize(
    "argv_factory, url, reason",
    [
        (lambda f: [], _url(), "target_missing"),
        (lambda f: ["--target", "/nonexistent/synthetic/target.json"], _url(), "target_missing"),
        (lambda f: ["--target", f(mode=0o644)], _url(), "target_permissions_too_open"),
        (lambda f: ["--target", f(raw="{not json")], _url(), "target_malformed"),
        (lambda f: ["--target", f(raw="[1, 2]")], _url(), "target_malformed"),
        (lambda f: ["--target", f()], None, "url_missing"),
        (lambda f: ["--target", f(), "--url-env", "BAD NAME"], _url(), "url_env_name_invalid"),
    ],
)
def test_cli_input_problems_are_unknown_with_fixed_tokens(
    capsys, target_file, argv_factory, url, reason
):
    code, out, err = _run(capsys, argv_factory(target_file), url)
    assert code == 2
    assert f"g7_gate1_input={reason}" in out
    assert "g7_gate1_overall=UNKNOWN" in out
    _assert_no_secrets(out, err)
    assert "/nonexistent" not in out + err


def test_cli_target_inside_repository_is_rejected(capsys, tmp_path):
    inside = g7.REPO_ROOT / ".g7_synthetic_target_test.json"
    inside.write_text(json.dumps(TARGET), encoding="utf-8")
    os.chmod(inside, 0o600)
    try:
        code, out, err = _run(capsys, ["--target", str(inside)], _url())
    finally:
        inside.unlink()
    assert code == 2
    assert "g7_gate1_input=target_inside_repository" in out
    _assert_no_secrets(out, err)


def test_cli_unexpected_exception_is_redacted(capsys, target_file, monkeypatch):
    def boom(url, target):
        raise RuntimeError(f"failure for {_url()} host={HOST} password={PASSWORD}")

    monkeypatch.setattr(g7, "evaluate", boom)
    code, out, err = _run(capsys, ["--target", target_file()], _url())
    assert code == 2
    assert "g7_gate1_input=internal_error" in out
    _assert_no_secrets(out, err)
    assert "Traceback" not in out + err


def test_cli_usage_error_does_not_echo_arguments(capsys):
    with pytest.raises(SystemExit) as excinfo:
        g7.main(["--unknown-flag", _url()], environ={})
    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert "usage_error" in captured.err
    _assert_no_secrets(captured.out, captured.err)


def test_subprocess_stdout_and_stderr_are_redacted(target_file):
    """End to end in a separate interpreter: the URL comes only from the environment."""
    env = {"PATH": os.environ.get("PATH", ""), "DATABASE_URL": _url(user=f"{ROLE}.{OTHER_PROJECT}")}
    proc = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--target", target_file()],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert proc.returncode == 1
    assert "g7_gate1_overall=FAIL" in proc.stdout
    _assert_no_secrets(proc.stdout, proc.stderr)
    assert proc.stderr == ""


def test_script_has_no_network_or_driver_imports():
    source = SCRIPT.read_text(encoding="utf-8")
    for forbidden in (
        "import socket",
        "psycopg",
        "import requests",
        "urllib.request",
        "http.client",
        "django",
    ):
        assert forbidden not in source
