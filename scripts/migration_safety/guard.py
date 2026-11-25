#!/usr/bin/env python3
"""Safety guard for manual Production backup/restore drills.

This module contains no network or DB code. It only answers two yes/no
questions from a connection URL/path, using an allow-list (not a deny-list):

- is a RESTORE target safe to write to? (must look like a disposable local
  isolation DB, never anything that could plausibly be Production)
- is a DUMP output path safe to write to? (must be outside this repository,
  so a Production dump can never end up committed)

An allow-list is used instead of a "does this look like production"
deny-list because this tooling does not know Production's real hostname.
A deny-list of guessed patterns would be incomplete by construction; an
allow-list of known-safe local targets fails closed instead.

No function here executes a command, opens a socket, or reads a secret
from a file. Callers (shell scripts) are responsible for actually running
pg_dump/psql; this module only decides whether that's safe to attempt.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import sys
from urllib.parse import parse_qs, urlparse

# Only these hosts are ever treated as "local" for restore purposes.
ALLOWED_RESTORE_HOSTS = {"localhost", "127.0.0.1", "::1"}

# Existing local databases that real developers rely on. Restoring into one
# of these would clobber someone's work, so they are blocked even though
# they're local.
PROTECTED_LOCAL_DB_NAMES = {
    "jinja_db",
    "jinja_app_dev",
    "jinja_test",
    "postgres",
    "template0",
    "template1",
}

# A restore target's database name must contain one of these markers.
# This is what makes a target "obviously disposable" rather than a
# same-named collision with something real.
REQUIRED_ISOLATION_MARKERS = ("audit", "restore_test", "migration_safety")

# A dump file's *contents* must never contain the connection string used to
# produce it. This redaction is defense in depth for anything that logs the
# URL a script was invoked with (e.g. `set -x` output, error messages).
_CREDENTIAL_RE = re.compile(r"://([^:/@]+)(:([^@/]*))?@")


def redact_url(url: str) -> str:
    """Return `url` with any userinfo (user:password) replaced by '***'."""
    return _CREDENTIAL_RE.sub("://***@", url)


def is_safe_restore_target(database_url: str) -> tuple[bool, str]:
    """Return (ok, reason). ok is True only for a disposable local DB."""
    try:
        parsed = urlparse(database_url)
    except ValueError as exc:
        return False, f"could not parse URL: {exc}"

    host = (parsed.hostname or "").lower()
    dbname = (parsed.path or "").lstrip("/")

    if host not in ALLOWED_RESTORE_HOSTS:
        return False, f"host {host!r} is not in the local allow-list {sorted(ALLOWED_RESTORE_HOSTS)}"

    if not dbname:
        return False, "database name is empty"

    if dbname.lower() in PROTECTED_LOCAL_DB_NAMES:
        return False, f"database name {dbname!r} is a protected existing local database"

    if not any(marker in dbname.lower() for marker in REQUIRED_ISOLATION_MARKERS):
        return False, (
            f"database name {dbname!r} does not contain a required isolation "
            f"marker {REQUIRED_ISOLATION_MARKERS}; refusing to restore into "
            "a database that wasn't clearly created for this drill"
        )

    return True, "ok"


def is_safe_dump_path(path: str, repo_root: str) -> tuple[bool, str]:
    """Return (ok, reason). ok is True only if `path` is outside `repo_root`.

    Also used to gate credential *files* (not just dump output) — the same
    "must not be inside this repository" property is what matters in both
    cases, so the check is reused rather than duplicated.
    """
    abs_path = os.path.realpath(path)
    abs_repo_root = os.path.realpath(repo_root)

    if abs_path == abs_repo_root or abs_path.startswith(abs_repo_root + os.sep):
        return False, f"{abs_path} is inside the repository ({abs_repo_root}); refusing to write a dump there"

    return True, "ok"


def describe_url_shape(database_url: str) -> dict:
    """Return only structural booleans about a URL — never the value, its
    length, or any substring (including hostname). Safe to print/log.
    """
    try:
        parsed = urlparse(database_url)
    except ValueError:
        return {"parses": False}

    return {
        "parses": True,
        "scheme_is_postgres": parsed.scheme in ("postgres", "postgresql"),
        "has_host": bool(parsed.hostname),
        "has_port": parsed.port is not None,
        "has_dbname": bool((parsed.path or "").lstrip("/")),
        "has_userinfo": bool(parsed.username),
    }


# Statement-start keywords this bridge will ever execute. Anything else is
# refused. This is a simple lexical check (split on ';', look at the first
# word), not a real SQL parser — it is deliberately conservative: anything
# it can't confidently classify as read-only is rejected, not allowed.
_ALLOWED_SQL_VERBS = {"select", "show", "explain", "with"}

# Explicit deny-list kept too, purely so a caller gets a clear reason
# ("this is a write verb") instead of a generic "not in the allow-list"
# message when someone tries something obviously unsafe.
_FORBIDDEN_SQL_VERBS = {
    "insert", "update", "delete", "merge", "alter", "create", "drop",
    "truncate", "grant", "revoke", "vacuum", "analyze", "call", "do",
    "copy", "refresh", "reindex", "cluster", "lock", "comment", "import",
    "export", "listen", "notify", "unlisten", "prepare", "execute",
    "deallocate", "checkpoint", "discard", "load", "security",
}


def _strip_sql_comments(sql_text: str) -> str:
    no_line_comments = re.sub(r"--[^\n]*", "", sql_text)
    return re.sub(r"/\*.*?\*/", "", no_line_comments, flags=re.DOTALL)


def is_readonly_sql(sql_text: str) -> tuple[bool, str]:
    """Return (ok, reason). ok is True only if every statement in
    `sql_text` starts with an allowed read-only verb, and no EXPLAIN
    statement contains ANALYZE (which actually executes the query and can
    have side effects for non-SELECT statements).
    """
    cleaned = _strip_sql_comments(sql_text)
    statements = [s.strip() for s in cleaned.split(";")]
    statements = [s for s in statements if s]

    if not statements:
        return False, "no SQL statements found"

    for stmt in statements:
        first_word = stmt.split(None, 1)[0].lower() if stmt.split() else ""
        if first_word in _FORBIDDEN_SQL_VERBS:
            return False, f"statement starts with a forbidden write/DDL verb: {first_word!r}"
        if first_word not in _ALLOWED_SQL_VERBS:
            return False, f"statement does not start with an allowed read-only verb {sorted(_ALLOWED_SQL_VERBS)}: {first_word!r}"
        if first_word == "explain" and re.search(r"\banalyze\b", stmt, re.IGNORECASE):
            return False, "EXPLAIN ANALYZE actually executes the query and is not allowed; use EXPLAIN without ANALYZE"

    return True, "ok"


def pg_env_exports(database_url: str) -> str:
    """Return shell `export` statements (PGHOST/PGPORT/PGUSER/PGPASSWORD/
    PGDATABASE/PGSSLMODE) for `database_url`, so a caller can `eval` them
    and then run `psql`/`pg_dump` with NO connection info on the command
    line at all (libpq reads these automatically). Output is meant to be
    consumed by `eval "$(...)"` only — never printed to a terminal or log,
    since it necessarily contains the credential.
    """
    parsed = urlparse(database_url)
    lines = []
    if parsed.hostname:
        lines.append(f"export PGHOST={shlex.quote(parsed.hostname)}")
    if parsed.port:
        lines.append(f"export PGPORT={shlex.quote(str(parsed.port))}")
    if parsed.username:
        lines.append(f"export PGUSER={shlex.quote(parsed.username)}")
    if parsed.password:
        lines.append(f"export PGPASSWORD={shlex.quote(parsed.password)}")
    dbname = (parsed.path or "").lstrip("/")
    if dbname:
        lines.append(f"export PGDATABASE={shlex.quote(dbname)}")
    sslmode = parse_qs(parsed.query).get("sslmode", [None])[0]
    if sslmode:
        lines.append(f"export PGSSLMODE={shlex.quote(sslmode)}")
    return "\n".join(lines)


def _cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_restore = sub.add_parser("check-restore-target", help="Exit 0 if URL is a safe restore target, else 1")
    p_restore.add_argument("database_url")

    p_dump = sub.add_parser("check-dump-path", help="Exit 0 if path is outside the repo, else 1")
    p_dump.add_argument("path")
    p_dump.add_argument("repo_root")

    p_redact = sub.add_parser("redact", help="Print URL with credentials masked")
    p_redact.add_argument("database_url")

    sub.add_parser(
        "describe-url-shape",
        help="Read a URL from stdin (never argv), print structural booleans only (no value, length, or host)",
    )

    p_sql = sub.add_parser("check-readonly-sql", help="Exit 0 if every statement in a SQL file is read-only, else 1")
    p_sql.add_argument("sql_file")

    sub.add_parser(
        "pg-env-exports",
        help="Read a URL from stdin (never argv), print PG* export statements (for eval only — contains the credential)",
    )

    args = parser.parse_args()

    if args.command == "check-restore-target":
        ok, reason = is_safe_restore_target(args.database_url)
        print(f"{'SAFE' if ok else 'BLOCKED'}: {reason}", file=sys.stderr)
        return 0 if ok else 1

    if args.command == "check-dump-path":
        ok, reason = is_safe_dump_path(args.path, args.repo_root)
        print(f"{'SAFE' if ok else 'BLOCKED'}: {reason}", file=sys.stderr)
        return 0 if ok else 1

    if args.command == "redact":
        print(redact_url(args.database_url))
        return 0

    if args.command == "describe-url-shape":
        url = sys.stdin.read().strip()
        print(describe_url_shape(url))
        return 0

    if args.command == "check-readonly-sql":
        with open(args.sql_file, encoding="utf-8") as f:
            sql_text = f.read()
        ok, reason = is_readonly_sql(sql_text)
        print(f"{'SAFE' if ok else 'BLOCKED'}: {reason}", file=sys.stderr)
        return 0 if ok else 1

    if args.command == "pg-env-exports":
        url = sys.stdin.read().strip()
        print(pg_env_exports(url))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
