#!/usr/bin/env python3
"""G-7 Gate 1: local-only, credential-safe identity comparison of the audit connection (G7-A1 to G7-A6).

Mother Ship decision (2026-11-02): G7_PARSER_POLICY = LOCAL_OFFLINE_REDACTED.
Readiness doc: `docs/audit/evidence-coverage-production-readiness-2026-11-01.md` §9.3, §10.3, §12.
Contract: `docs/audit/sph21-production-db-connection-verification-2026-11-01.md` "Gate 1".

What it does
------------
It compares the audit connection URL, read from an environment variable (never from argv), with an owner-approved
target read from a private JSON file. It prints only PASS / FAIL / UNKNOWN per field, an overall result and fixed
tokens.

- No database connection, DNS lookup or network call. Standard library only; no socket or driver import.
- Never prints the URL, password, host, user name, project reference, tenant identifier, file paths or exception
  text.
- Supported endpoint formats: SESSION_POOLER and TRANSACTION_POOLER only, with a `<role>.<project_ref>` user name.
  Anything else (direct connections, multiple hosts, missing ports, ambiguous user names) is UNKNOWN.
- G-7 is never marked satisfied: G7-B1 (catalog comparison) and G7-B2 (owner confirmation) are separate.

Fields
------
- A1 project:       the user-name suffix equals the approved `project_ref`. The host name is never used for this.
- A2 tenant:        the host equals the approved pooler host for that tenant (exact, case-insensitive).
- A3 endpoint kind: derived only for the approved pooler host with an explicit port
                    (5432 -> SESSION_POOLER, 6543 -> TRANSACTION_POOLER) and a `<role>.<ref>` user name.
- A4 database name: the single path segment equals the approved `dbname`.
- A5 port:          the explicit port equals the approved `port`.
- A6 user format:   the user name is exactly `<approved role>.<suffix>`.

Target file (JSON, owner-held, outside the repository, not readable by group or others):
    {"project_ref": "...", "pooler_host": "...", "endpoint_kind": "SESSION_POOLER",
     "port": 5432, "dbname": "...", "role": "..."}

Usage:
    python scripts/g7_gate1_identity_check.py --target <private target file> [--url-env DATABASE_URL]
Exit status: 0 only when every field is PASS; 1 otherwise; 2 when the inputs cannot be evaluated.
"""

from __future__ import annotations

import argparse
import hmac
import json
import os
import re
import stat
import sys
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

PASS, FAIL, UNKNOWN = "PASS", "FAIL", "UNKNOWN"
FIELDS = (
    "a1_project",
    "a2_tenant",
    "a3_endpoint_kind",
    "a4_database_name",
    "a5_port",
    "a6_username_format",
)
SUPPORTED_ENDPOINT_KINDS = {"SESSION_POOLER": 5432, "TRANSACTION_POOLER": 6543}
_PORT_TO_KIND = {port: kind for kind, port in SUPPORTED_ENDPOINT_KINDS.items()}
_TARGET_KEYS = ("project_ref", "pooler_host", "endpoint_kind", "port", "dbname", "role")
_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_-]+$")  # role / project ref / suffix: no dots, no separators
# libpq URI query parameters that would override what the URL authority / path says.
_OVERRIDES = {
    "host": ("a2_tenant", "a3_endpoint_kind"),
    "hostaddr": ("a2_tenant", "a3_endpoint_kind"),
    "port": ("a3_endpoint_kind", "a5_port"),
    "user": ("a1_project", "a6_username_format"),
    "dbname": ("a4_database_name",),
    "service": FIELDS,
}
REPO_ROOT = Path(__file__).resolve().parent.parent


class InputRejected(Exception):
    """Raised with a fixed, non-sensitive reason token."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def _all(value: str) -> dict[str, str]:
    return {field: value for field in FIELDS}


# --------------------------------------------------------------------------- #
# inputs
# --------------------------------------------------------------------------- #


def load_target(path_str: str | None) -> dict:
    """Read and validate the owner-approved target. Raises InputRejected with a fixed token."""
    if not path_str:
        raise InputRejected("target_missing")
    path = Path(path_str).expanduser()
    try:
        real = path.resolve(strict=True)
    except (OSError, RuntimeError):
        raise InputRejected("target_missing") from None
    if real == REPO_ROOT or REPO_ROOT in real.parents:
        raise InputRejected("target_inside_repository")
    try:
        st = real.stat()
    except OSError:
        raise InputRejected("target_unreadable") from None
    if not stat.S_ISREG(st.st_mode):
        raise InputRejected("target_not_a_file")
    if st.st_mode & 0o077:
        raise InputRejected("target_permissions_too_open")
    try:
        data = json.loads(real.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        raise InputRejected("target_malformed") from None
    if not isinstance(data, dict):
        raise InputRejected("target_malformed")
    return data


def _target_value(target: dict, key: str):
    """Validated target value, or None (that field becomes UNKNOWN)."""
    value = target.get(key)
    if key == "port":
        return (
            value
            if isinstance(value, int) and not isinstance(value, bool) and 0 < value < 65536
            else None
        )
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        return None
    if key in ("project_ref", "role") and not _SAFE_TOKEN.match(value):
        return None
    if key == "endpoint_kind" and value not in SUPPORTED_ENDPOINT_KINDS:
        return None
    return value


# --------------------------------------------------------------------------- #
# evaluation
# --------------------------------------------------------------------------- #


def _parse_url(url: str) -> dict | None:
    """Structural parse. None means malformed or unsupported as a whole."""
    if not isinstance(url, str) or not url or url != url.strip():
        return None
    try:
        parts = urlsplit(url)
        if parts.scheme not in ("postgres", "postgresql") or parts.fragment:
            return None
        netloc = parts.netloc
        if netloc.count("@") != 1:  # no user, or an unencoded reserved character in the credentials
            return None
        hostport = netloc.rpartition("@")[2]
        if "," in hostport or not hostport or hostport.startswith("["):
            return None  # multiple hosts or IPv6 literals: unsupported
        host = parts.hostname
        port = parts.port  # ValueError on a malformed port
        raw_user = parts.username
        query = parse_qsl(parts.query, keep_blank_values=True, strict_parsing=False)
    except ValueError:
        return None
    user = unquote(raw_user) if raw_user else None
    path = parts.path
    dbname = None
    if path.startswith("/") and len(path) > 1 and "/" not in path[1:]:
        dbname = unquote(path[1:])
    return {
        "host": host.rstrip(".").lower() if host else None,
        "port": port,
        "user": user,
        "dbname": dbname,
        "query_keys": {key.lower() for key, _ in query},
    }


def _split_user(user: str | None):
    """('ok', role, suffix) | ('no_suffix', ...) | ('ambiguous', ...) | ('missing', ...)."""
    if not user:
        return "missing", None, None
    if user.count(".") == 0:
        return "no_suffix", user, None
    if user.count(".") > 1:
        return "ambiguous", None, None
    role, suffix = user.split(".")
    if not role or not suffix or not _SAFE_TOKEN.match(role) or not _SAFE_TOKEN.match(suffix):
        return "ambiguous", None, None
    return "ok", role, suffix


def evaluate(url: str | None, target: dict | None) -> dict[str, str]:
    """Return {field: PASS|FAIL|UNKNOWN} for G7-A1..A6. Never raises; never returns input values."""
    if target is None:
        return _all(UNKNOWN)
    parsed = _parse_url(url) if url else None
    if parsed is None:
        return _all(UNKNOWN)

    t = {key: _target_value(target, key) for key in _TARGET_KEYS}
    status, role, suffix = _split_user(parsed["user"])
    host, port = parsed["host"], parsed["port"]
    approved_host = t["pooler_host"].rstrip(".").lower() if t["pooler_host"] else None
    result: dict[str, str] = {}

    # A1 project: the user-name suffix only. The host never identifies the project.
    if status != "ok" or t["project_ref"] is None:
        result["a1_project"] = UNKNOWN
    else:
        result["a1_project"] = PASS if _eq(suffix, t["project_ref"]) else FAIL

    # A2 tenant: exact approved pooler host.
    if not host or approved_host is None:
        result["a2_tenant"] = UNKNOWN
    else:
        result["a2_tenant"] = PASS if _eq(host, approved_host) else FAIL

    # A3 endpoint kind: only for the approved pooler host, an explicit supported port and a <role>.<ref> user.
    observed_kind = None
    if (
        host
        and approved_host
        and _eq(host, approved_host)
        and status == "ok"
        and port in _PORT_TO_KIND
    ):
        observed_kind = _PORT_TO_KIND[port]
    if observed_kind is None or t["endpoint_kind"] is None:
        result["a3_endpoint_kind"] = UNKNOWN
    else:
        result["a3_endpoint_kind"] = PASS if observed_kind == t["endpoint_kind"] else FAIL

    # A4 database name.
    if not parsed["dbname"] or t["dbname"] is None:
        result["a4_database_name"] = UNKNOWN
    else:
        result["a4_database_name"] = PASS if _eq(parsed["dbname"], t["dbname"]) else FAIL

    # A5 port: explicit only (a libpq default is not evidence).
    if port is None or t["port"] is None:
        result["a5_port"] = UNKNOWN
    else:
        result["a5_port"] = PASS if port == t["port"] else FAIL

    # A6 user-name format: exactly <approved role>.<suffix>.
    if status in ("missing", "ambiguous") or t["role"] is None:
        result["a6_username_format"] = UNKNOWN
    elif status == "no_suffix":
        result["a6_username_format"] = FAIL
    else:
        result["a6_username_format"] = PASS if _eq(role, t["role"]) else FAIL

    # Query parameters that override the authority / path make the affected fields ambiguous.
    for key in parsed["query_keys"]:
        for field in _OVERRIDES.get(key, ()):
            result[field] = UNKNOWN
    return result


def overall(result: dict[str, str]) -> str:
    values = [result.get(field, UNKNOWN) for field in FIELDS]
    if all(v == PASS for v in values):
        return PASS
    if any(v == FAIL for v in values):
        return FAIL
    return UNKNOWN


def render(result: dict[str, str], reason: str | None = None) -> str:
    lines = [f"g7_{field}={result.get(field, UNKNOWN)}" for field in FIELDS]
    lines.append(f"g7_gate1_overall={overall(result)}")
    if reason:
        lines.append(f"g7_gate1_input={reason}")
    lines.append("g7_b1_catalog=not_evaluated")
    lines.append("g7_b2_owner_confirmation=not_evaluated")
    lines.append("g7_satisfied=false")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


class _QuietParser(argparse.ArgumentParser):
    def error(self, message):  # argparse would echo argv; print a fixed token instead
        sys.stderr.write("g7_gate1_input=usage_error\n")
        raise SystemExit(2)


def main(argv: list[str] | None = None, environ: dict | None = None) -> int:
    environ = os.environ if environ is None else environ
    try:
        parser = _QuietParser(
            add_help=True, description="G-7 Gate 1 offline identity check (redacted)"
        )
        parser.add_argument("--target", required=False)
        parser.add_argument("--url-env", default="DATABASE_URL")
        args = parser.parse_args(argv)
        if not _SAFE_TOKEN.match(args.url_env or ""):
            sys.stdout.write(render(_all(UNKNOWN), "url_env_name_invalid") + "\n")
            return 2
        try:
            target = load_target(args.target)
        except InputRejected as exc:
            sys.stdout.write(render(_all(UNKNOWN), exc.reason) + "\n")
            return 2
        url = environ.get(args.url_env)
        if not url:
            sys.stdout.write(render(_all(UNKNOWN), "url_missing") + "\n")
            return 2
        result = evaluate(url, target)
        sys.stdout.write(render(result) + "\n")
        return 0 if overall(result) == PASS else 1
    except SystemExit:
        raise
    except BaseException:  # noqa: BLE001 - never print a traceback or exception text
        sys.stdout.write(render(_all(UNKNOWN), "internal_error") + "\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
