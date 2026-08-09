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
import sys
from urllib.parse import urlparse

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
    """Return (ok, reason). ok is True only if `path` is outside `repo_root`."""
    abs_path = os.path.realpath(path)
    abs_repo_root = os.path.realpath(repo_root)

    if abs_path == abs_repo_root or abs_path.startswith(abs_repo_root + os.sep):
        return False, f"{abs_path} is inside the repository ({abs_repo_root}); refusing to write a dump there"

    return True, "ok"


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

    return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
