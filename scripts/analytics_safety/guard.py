#!/usr/bin/env python3
"""Safety guard for PostHog read-only analytics queries.

Mirrors the design of scripts/migration_safety/guard.py: this module
contains no network code and never touches a real credential value. It
only answers safety questions using an allow-list (not a deny-list):

- is this HTTP method + path allowed to be called at all? (only the
  single HogQL query endpoint is permitted, regardless of what a caller
  asks for)
- does this HogQL query text contain a write/mutation keyword? (defense
  in depth on top of the endpoint allow-list — the query endpoint is
  itself read-only by PostHog's own API design, per
  https://posthog.com/docs/api/queries, but we do not rely on that
  alone)
- what is the structural shape of a credential value, without ever
  returning the value itself? (VAR_SET, non-empty, length bucket only)
- how should an error be redacted before it reaches stdout/stderr?

No function here executes an HTTP request, reads a credential from disk,
or prints a secret. Callers (posthog_readonly_query.py) are responsible
for the actual request; this module only decides whether it is safe to
attempt and how to describe the outcome without leaking anything.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# The only endpoint this tooling is ever allowed to call. PostHog's HogQL
# query endpoint is POST by HTTP method but semantically read-only (it
# executes a query and returns rows; it does not mutate state) per
# PostHog's own API documentation. No other PostHog endpoint — event
# capture, insights mutation, feature flags, project settings, person
# deletion, etc. — is reachable through this tooling, by construction:
# the wrapper never accepts a path, only a project_id substituted into
# this exact template.
ALLOWED_PATH_TEMPLATE = "/api/projects/{project_id}/query/"
ALLOWED_METHOD = "POST"

# Keywords that must never appear in a HogQL query string sent through
# this tooling, checked in addition to (not instead of) the endpoint
# allow-list above. HogQL is a read-only SQL dialect for PostHog's own
# query endpoint, but this list blocks anything that even superficially
# resembles a mutation statement, as defense in depth.
_FORBIDDEN_QUERY_KEYWORDS = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "grant",
    "revoke",
    "merge",
)

_QUERY_KEYWORD_RE = re.compile(
    r"\b(" + "|".join(_FORBIDDEN_QUERY_KEYWORDS) + r")\b", re.IGNORECASE
)


def is_endpoint_allowed(*, method: str, path: str) -> bool:
    """True only for POST to the exact HogQL query path shape."""
    if method.upper() != ALLOWED_METHOD:
        return False
    # path must match /api/projects/<something non-empty, no slash>/query/
    return bool(re.fullmatch(r"/api/projects/[^/]+/query/", path))


def build_allowed_path(project_id: str) -> str:
    if not project_id or "/" in project_id:
        raise ValueError("invalid project_id")
    return ALLOWED_PATH_TEMPLATE.format(project_id=project_id)


def is_readonly_hogql(query_text: str) -> bool:
    """True if query_text contains no forbidden mutation keyword.

    This is a coarse, conservative check (keyword search, not a real SQL
    parser) by design — the goal is to fail closed on anything
    ambiguous, not to be a complete HogQL grammar.
    """
    if not isinstance(query_text, str) or not query_text.strip():
        return False
    return _QUERY_KEYWORD_RE.search(query_text) is None


def describe_credential_shape(value: str | None) -> dict:
    """Structural-shape-only description of a credential value.

    Never includes the value, a prefix/suffix of it, or its exact
    length — only coarse booleans and a length bucket, matching the
    redaction level of migration_safety/guard.py's describe_url_shape().
    """
    if not value:
        return {"present": False}

    length = len(value)
    if length < 20:
        bucket = "short"
    elif length < 60:
        bucket = "typical"
    else:
        bucket = "long"

    return {
        "present": True,
        "length_bucket": bucket,
        "has_whitespace": bool(re.search(r"\s", value)),
    }


_REDACT_PATTERNS = (
    # "Bearer <token>" must be redacted before the more general
    # "Authorization: <token>" pattern below, otherwise the latter only
    # consumes the word "Bearer" and leaves the actual token untouched.
    (re.compile(r"(?i)bearer\s+\S+"), "bearer <redacted>"),
    # Authorization header values of any kind (non-Bearer schemes).
    (re.compile(r"(?i)authorization:\s*\S+"), "authorization: <redacted>"),
    # Anything that looks like a URL with a host, to avoid leaking the
    # configured PostHog host/project endpoint in error text.
    (re.compile(r"https?://\S+"), "<redacted-url>"),
)


def redact_error_text(text: str) -> str:
    """Best-effort redaction for exception text before it is ever printed.

    Callers should prefer generic, pre-written error messages (see
    posthog_readonly_query.py's ERROR_* constants) over surfacing
    exception text at all; this function is a defense-in-depth backstop
    for the rare case an exception message is included.
    """
    if not text:
        return text
    redacted = text
    for pattern, replacement in _REDACT_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    describe = sub.add_parser(
        "describe-credential-shape",
        help="Read a credential value from stdin and print only its shape as JSON.",
    )
    describe.set_defaults(command="describe-credential-shape")

    check_query = sub.add_parser(
        "check-readonly-hogql",
        help="Read a HogQL query from stdin; exit 0 if it looks read-only, 1 otherwise.",
    )
    check_query.set_defaults(command="check-readonly-hogql")

    args = parser.parse_args()

    if args.command == "describe-credential-shape":
        value = sys.stdin.read().rstrip("\n")
        print(json.dumps(describe_credential_shape(value or None), sort_keys=True))
        return 0

    if args.command == "check-readonly-hogql":
        query_text = sys.stdin.read()
        if is_readonly_hogql(query_text):
            print("READONLY_OK")
            return 0
        print("BLOCKED: query contains a forbidden keyword or is empty", file=sys.stderr)
        return 1

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
