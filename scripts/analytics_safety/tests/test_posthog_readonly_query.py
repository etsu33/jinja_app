"""Tests for scripts/analytics_safety/posthog_readonly_query.py.

No real PostHog credential, no real network call — every HTTP
interaction is mocked with `requests_mock`. Run with:
    python3 -m pytest scripts/analytics_safety/tests/test_posthog_readonly_query.py -v
"""

import io
import json
import os
import sys
from contextlib import redirect_stderr, redirect_stdout

import pytest
import requests
import requests_mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from posthog_readonly_query import (  # noqa: E402
    DEFAULT_HOST,
    ERROR_AUTH,
    ERROR_CREDENTIAL_MISSING,
    ERROR_ENDPOINT_REJECTED,
    ERROR_MALFORMED_RESPONSE,
    ERROR_NETWORK,
    ERROR_QUERY_REJECTED,
    ERROR_TIMEOUT,
    ERROR_UPSTREAM,
    PostHogReadOnlyQueryError,
    run_readonly_hogql_query,
)

FAKE_KEY = "phx_fake_credential_for_tests_only"
FAKE_PROJECT_ID = "999999"
FAKE_QUERY = "SELECT count() FROM events WHERE event = 'recommendation_quality'"


@pytest.fixture(autouse=True)
def _set_fake_env(monkeypatch):
    # A fake, obviously-not-real credential — never a real PostHog value.
    monkeypatch.setenv("POSTHOG_PERSONAL_API_KEY", FAKE_KEY)
    monkeypatch.setenv("POSTHOG_PROJECT_ID", FAKE_PROJECT_ID)
    monkeypatch.delenv("POSTHOG_HOST", raising=False)


def _expected_url() -> str:
    return f"{DEFAULT_HOST}/api/projects/{FAKE_PROJECT_ID}/query/"


# --- success -----------------------------------------------------------------


def test_success_returns_json_result():
    with requests_mock.Mocker() as m:
        m.post(_expected_url(), json={"results": [[42]]}, status_code=200)
        result = run_readonly_hogql_query(FAKE_QUERY)
    assert result == {"results": [[42]]}


def test_success_sends_bearer_auth_header():
    with requests_mock.Mocker() as m:
        m.post(_expected_url(), json={"results": []}, status_code=200)
        run_readonly_hogql_query(FAKE_QUERY)
    sent_auth = m.last_request.headers.get("Authorization")
    assert sent_auth == f"Bearer {FAKE_KEY}"


def test_success_sends_hogql_query_body():
    with requests_mock.Mocker() as m:
        m.post(_expected_url(), json={"results": []}, status_code=200)
        run_readonly_hogql_query(FAKE_QUERY)
    sent_body = m.last_request.json()
    assert sent_body == {"query": {"kind": "HogQLQuery", "query": FAKE_QUERY}}


# --- auth failures -------------------------------------------------------------


def test_401_raises_generic_auth_error():
    with requests_mock.Mocker() as m:
        m.post(_expected_url(), status_code=401, json={"detail": "invalid token"})
        with pytest.raises(PostHogReadOnlyQueryError) as exc_info:
            run_readonly_hogql_query(FAKE_QUERY)
    assert str(exc_info.value) == ERROR_AUTH
    assert "invalid token" not in str(exc_info.value)


def test_403_raises_generic_auth_error():
    with requests_mock.Mocker() as m:
        m.post(_expected_url(), status_code=403, json={"detail": "insufficient scope"})
        with pytest.raises(PostHogReadOnlyQueryError) as exc_info:
            run_readonly_hogql_query(FAKE_QUERY)
    assert str(exc_info.value) == ERROR_AUTH
    assert "insufficient scope" not in str(exc_info.value)


# --- transport failures ---------------------------------------------------------


def test_timeout_raises_generic_timeout_error():
    with requests_mock.Mocker() as m:
        m.post(_expected_url(), exc=requests.exceptions.Timeout("connect timeout after 30s"))
        with pytest.raises(PostHogReadOnlyQueryError) as exc_info:
            run_readonly_hogql_query(FAKE_QUERY)
    assert str(exc_info.value) == ERROR_TIMEOUT


def test_dns_failure_raises_generic_network_error():
    with requests_mock.Mocker() as m:
        m.post(
            _expected_url(),
            exc=requests.exceptions.ConnectionError(
                "Failed to resolve 'us.posthog.com' ([Errno 8] nodename nor servname provided)"
            ),
        )
        with pytest.raises(PostHogReadOnlyQueryError) as exc_info:
            run_readonly_hogql_query(FAKE_QUERY)
    assert str(exc_info.value) == ERROR_NETWORK
    assert "us.posthog.com" not in str(exc_info.value)


def test_generic_connection_error_raises_generic_network_error():
    with requests_mock.Mocker() as m:
        m.post(_expected_url(), exc=requests.exceptions.ConnectionError("connection refused"))
        with pytest.raises(PostHogReadOnlyQueryError) as exc_info:
            run_readonly_hogql_query(FAKE_QUERY)
    assert str(exc_info.value) == ERROR_NETWORK


# --- malformed / upstream responses ---------------------------------------------


def test_malformed_json_response_raises_generic_error():
    with requests_mock.Mocker() as m:
        m.post(_expected_url(), text="not json {{{", status_code=200)
        with pytest.raises(PostHogReadOnlyQueryError) as exc_info:
            run_readonly_hogql_query(FAKE_QUERY)
    assert str(exc_info.value) == ERROR_MALFORMED_RESPONSE


def test_500_raises_generic_upstream_error():
    with requests_mock.Mocker() as m:
        m.post(_expected_url(), status_code=500, text="internal server error, traceback...")
        with pytest.raises(PostHogReadOnlyQueryError) as exc_info:
            run_readonly_hogql_query(FAKE_QUERY)
    assert str(exc_info.value) == ERROR_UPSTREAM


def test_unexpected_status_code_raises_generic_upstream_error():
    with requests_mock.Mocker() as m:
        m.post(_expected_url(), status_code=302)
        with pytest.raises(PostHogReadOnlyQueryError) as exc_info:
            run_readonly_hogql_query(FAKE_QUERY)
    assert str(exc_info.value) == ERROR_UPSTREAM


# --- credential / query / endpoint gates (no HTTP call reached) -----------------


def test_missing_credential_raises_before_any_request(monkeypatch):
    monkeypatch.delenv("POSTHOG_PERSONAL_API_KEY", raising=False)
    with requests_mock.Mocker() as m:
        with pytest.raises(PostHogReadOnlyQueryError) as exc_info:
            run_readonly_hogql_query(FAKE_QUERY)
        assert m.call_count == 0
    assert str(exc_info.value) == ERROR_CREDENTIAL_MISSING


def test_missing_project_id_raises_before_any_request(monkeypatch):
    monkeypatch.delenv("POSTHOG_PROJECT_ID", raising=False)
    with requests_mock.Mocker() as m:
        with pytest.raises(PostHogReadOnlyQueryError):
            run_readonly_hogql_query(FAKE_QUERY)
        assert m.call_count == 0


@pytest.mark.parametrize(
    "mutation_query",
    [
        "INSERT INTO events VALUES (1)",
        "UPDATE events SET event = 'x'",
        "DELETE FROM events",
        "DROP TABLE events",
        "",
    ],
)
def test_mutation_attempt_rejected_before_any_request(mutation_query):
    with requests_mock.Mocker() as m:
        with pytest.raises(PostHogReadOnlyQueryError) as exc_info:
            run_readonly_hogql_query(mutation_query)
        assert m.call_count == 0
    assert str(exc_info.value) == ERROR_QUERY_REJECTED


# --- secret non-exposure across the whole flow -----------------------------------


def test_no_secret_leaks_into_any_raised_error_message():
    with requests_mock.Mocker() as m:
        m.post(_expected_url(), status_code=401, json={"detail": FAKE_KEY})
        with pytest.raises(PostHogReadOnlyQueryError) as exc_info:
            run_readonly_hogql_query(FAKE_QUERY)
    assert FAKE_KEY not in str(exc_info.value)


def test_no_secret_leaks_via_cli_stderr_on_failure(monkeypatch):
    import posthog_readonly_query as module

    monkeypatch.setattr(sys, "argv", ["posthog_readonly_query.py", "--query", FAKE_QUERY])
    with requests_mock.Mocker() as m:
        m.post(_expected_url(), status_code=401, json={"detail": "nope"})
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = module._main()
    assert exit_code == 1
    assert FAKE_KEY not in stderr.getvalue()
    assert stderr.getvalue().strip() == ERROR_AUTH


# --- endpoint allow-list enforcement (defense in depth) --------------------------


def test_run_query_never_calls_any_endpoint_other_than_query(monkeypatch):
    """Even if project_id contained something unexpected, only the query
    path shape is ever assembled — guard.build_allowed_path() raises
    before a request could be built with anything else."""
    monkeypatch.setenv("POSTHOG_PROJECT_ID", "123/evil")
    with requests_mock.Mocker() as m:
        with pytest.raises(PostHogReadOnlyQueryError) as exc_info:
            run_readonly_hogql_query(FAKE_QUERY)
        assert m.call_count == 0
    assert str(exc_info.value) == ERROR_ENDPOINT_REJECTED


# --- fixture mode: no network call at all ----------------------------------------


def test_fixture_mode_prints_fixture_without_network_call(tmp_path, monkeypatch):
    import posthog_readonly_query as module

    fixture = tmp_path / "sample.json"
    fixture.write_text(json.dumps({"results": [["FULLY_KNOWLEDGE_BACKED", 5]]}))

    monkeypatch.setattr(sys, "argv", ["posthog_readonly_query.py", "--fixture", str(fixture)])
    with requests_mock.Mocker() as m:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = module._main()
        assert m.call_count == 0
    assert exit_code == 0
    printed = json.loads(stdout.getvalue())
    assert printed == {"results": [["FULLY_KNOWLEDGE_BACKED", 5]]}


def test_fixture_mode_missing_file_fails_generically(tmp_path):
    import posthog_readonly_query as module

    missing_path = str(tmp_path / "does_not_exist.json")
    import sys as _sys

    orig_argv = _sys.argv
    _sys.argv = ["posthog_readonly_query.py", "--fixture", missing_path]
    try:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = module._main()
    finally:
        _sys.argv = orig_argv
    assert exit_code == 1
    assert missing_path not in stderr.getvalue()
