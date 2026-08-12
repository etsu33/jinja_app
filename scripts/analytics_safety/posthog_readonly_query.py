#!/usr/bin/env python3
"""Safe, read-only PostHog HogQL query wrapper.

Sends exactly one kind of request — POST to PostHog's HogQL query
endpoint (POST {host}/api/projects/{project_id}/query/, semantically
read-only per https://posthog.com/docs/api/queries) — and nothing else.
No other PostHog endpoint is reachable through this module.

Credential contract (never accepted as a CLI argument, only read from
the environment, so a token never appears in `ps` or shell history):

    POSTHOG_PERSONAL_API_KEY   Personal API Key, `query:read` scope only.
    POSTHOG_PROJECT_ID         Numeric PostHog project id.
    POSTHOG_HOST               Optional. Defaults to https://us.posthog.com.

See README.md for how a human provisions these locally, outside the
repository. This module never creates, prompts for, or persists a
credential — it only reads one that already exists in the environment
when invoked.

On any failure (auth, network, malformed response, disallowed query),
this module prints one of the fixed ERROR_* messages below and exits
non-zero. It never prints the exception text, the request URL, the
Authorization header, or the raw response body — see
guard.redact_error_text() for the defense-in-depth backstop if an
unexpected exception text ever needs to surface.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from guard import (  # noqa: E402
    build_allowed_path,
    is_endpoint_allowed,
    is_readonly_hogql,
    redact_error_text,
)

DEFAULT_HOST = "https://us.posthog.com"
REQUEST_TIMEOUT_SECONDS = 30

ERROR_CREDENTIAL_MISSING = "PostHog read-only query failed: credential not configured."
ERROR_QUERY_REJECTED = "PostHog read-only query failed: query rejected (not read-only)."
ERROR_ENDPOINT_REJECTED = "PostHog read-only query failed: endpoint not permitted."
ERROR_AUTH = "PostHog read-only query failed: authentication or authorization error."
ERROR_NETWORK = "PostHog read-only query failed: network error."
ERROR_TIMEOUT = "PostHog read-only query failed: request timed out."
ERROR_MALFORMED_RESPONSE = "PostHog read-only query failed: malformed response."
ERROR_UPSTREAM = "PostHog read-only query failed: upstream error."


class PostHogReadOnlyQueryError(Exception):
    """Raised with one of the ERROR_* constants only — never raw detail."""


def _load_credentials_from_env() -> tuple[str, str, str]:
    key = os.environ.get("POSTHOG_PERSONAL_API_KEY", "")
    project_id = os.environ.get("POSTHOG_PROJECT_ID", "")
    host = os.environ.get("POSTHOG_HOST", "") or DEFAULT_HOST
    if not key or not project_id:
        raise PostHogReadOnlyQueryError(ERROR_CREDENTIAL_MISSING)
    return key, project_id, host


def run_readonly_hogql_query(
    query_text: str,
    *,
    session: Any = None,
) -> dict:
    """Execute one read-only HogQL query against PostHog and return the JSON result.

    `session` is injectable for tests (a `requests`-compatible object);
    production callers should leave it as None to use `requests` directly.
    """
    if not is_readonly_hogql(query_text):
        raise PostHogReadOnlyQueryError(ERROR_QUERY_REJECTED)

    key, project_id, host = _load_credentials_from_env()
    try:
        path = build_allowed_path(project_id)
    except ValueError:
        raise PostHogReadOnlyQueryError(ERROR_ENDPOINT_REJECTED) from None
    if not is_endpoint_allowed(method="POST", path=path):
        raise PostHogReadOnlyQueryError(ERROR_ENDPOINT_REJECTED)

    url = f"{host.rstrip('/')}{path}"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    body = {"query": {"kind": "HogQLQuery", "query": query_text}}

    http = session
    if http is None:
        import requests  # local import: only required at actual call time

        http = requests

    try:
        response = http.post(url, headers=headers, json=body, timeout=REQUEST_TIMEOUT_SECONDS)
    except Exception as exc:  # network error, DNS failure, connection refused, etc.
        _classify_and_raise_transport_error(exc)
        raise  # unreachable, _classify_and_raise_transport_error always raises

    if response.status_code in (401, 403):
        raise PostHogReadOnlyQueryError(ERROR_AUTH)
    if response.status_code >= 500:
        raise PostHogReadOnlyQueryError(ERROR_UPSTREAM)
    if response.status_code != 200:
        raise PostHogReadOnlyQueryError(ERROR_UPSTREAM)

    try:
        return response.json()
    except (ValueError, json.JSONDecodeError):
        raise PostHogReadOnlyQueryError(ERROR_MALFORMED_RESPONSE) from None


def _classify_and_raise_transport_error(exc: Exception) -> None:
    """Map a transport-layer exception to a generic ERROR_* message.

    Deliberately does not inspect or forward exc's message text (it may
    contain the request URL, hostname, or other identifying detail);
    only the exception's class shape is used to pick timeout vs.
    generic network error.
    """
    type_name = type(exc).__name__
    if "Timeout" in type_name:
        raise PostHogReadOnlyQueryError(ERROR_TIMEOUT) from None
    raise PostHogReadOnlyQueryError(ERROR_NETWORK) from None


def _load_fixture(fixture_path: str) -> dict:
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--query",
        required=False,
        help="HogQL query text. Ignored if --fixture is given.",
    )
    parser.add_argument(
        "--fixture",
        required=False,
        help=(
            "Path to a local fixture JSON file to print instead of calling "
            "the real PostHog API. Use this for dry runs / tests without a "
            "credential. No network request is made in this mode."
        ),
    )
    args = parser.parse_args()

    if args.fixture:
        try:
            result = _load_fixture(args.fixture)
        except (OSError, json.JSONDecodeError) as exc:
            print(redact_error_text(f"failed to load fixture: {type(exc).__name__}"), file=sys.stderr)
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if not args.query:
        print("usage: --query '<HogQL>' or --fixture <path>", file=sys.stderr)
        return 2

    try:
        result = run_readonly_hogql_query(args.query)
    except PostHogReadOnlyQueryError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
