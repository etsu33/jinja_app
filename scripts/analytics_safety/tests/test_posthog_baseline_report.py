"""Tests for scripts/analytics_safety/posthog_baseline_report.py.

No real PostHog credential, no real network call. Run with:
    python3 -m pytest scripts/analytics_safety/tests/test_posthog_baseline_report.py -v
"""

import io
import json
import os
import sys
from contextlib import redirect_stderr, redirect_stdout

import pytest
import requests_mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import posthog_baseline_report as module  # noqa: E402
from posthog_readonly_query import DEFAULT_HOST  # noqa: E402

FAKE_KEY = "phx_fake_credential_for_tests_only"
FAKE_PROJECT_ID = "999999"
FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "fixtures",
    "sample_baseline",
)


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    monkeypatch.delenv("POSTHOG_PERSONAL_API_KEY", raising=False)
    monkeypatch.delenv("POSTHOG_PROJECT_ID", raising=False)
    monkeypatch.delenv("POSTHOG_HOST", raising=False)


# --- fixture mode: no network, no credential required ------------------------


def test_fixture_mode_builds_report_without_credential():
    report = module.build_report(since="2026-08-12T00:00:00Z", until="2026-08-12T12:00:00Z", fixture_dir=FIXTURE_DIR)
    assert report["period"] == {"since": "2026-08-12T00:00:00Z", "until": "2026-08-12T12:00:00Z"}
    assert set(module.QUERY_CONTRACT) <= set(report["queries"])
    assert report["queries"]["recommendation_quality_count"] == {"results": [[0]], "columns": ["count"]}


def test_fixture_mode_cli_makes_no_network_call(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["posthog_baseline_report.py", "--fixture", FIXTURE_DIR, "--since", "2026-08-12T00:00:00Z", "--until", "2026-08-12T12:00:00Z"],
    )
    with requests_mock.Mocker() as m:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = module._main()
        assert m.call_count == 0
    assert exit_code == 0
    printed = json.loads(stdout.getvalue())
    assert printed["period"]["since"] == "2026-08-12T00:00:00Z"


def test_fixture_mode_missing_query_file_is_null_not_fabricated(tmp_path):
    empty_dir = str(tmp_path)
    report = module.build_report(since="2026-08-12T00:00:00Z", until="2026-08-12T12:00:00Z", fixture_dir=empty_dir)
    for name in module.QUERY_CONTRACT:
        assert report["queries"][name] is None


# --- credential gate: real mode without env vars never fabricates data -------


def test_real_mode_without_credential_exits_with_required_marker():
    with requests_mock.Mocker() as m:
        stderr = io.StringIO()
        orig_argv = sys.argv
        sys.argv = ["posthog_baseline_report.py"]
        try:
            with redirect_stderr(stderr):
                exit_code = module._main()
        finally:
            sys.argv = orig_argv
        assert m.call_count == 0
    assert exit_code == 1
    assert stderr.getvalue().strip() == "POSTHOG_READ_CREDENTIAL_REQUIRED"


# --- real mode: mocked HTTP, every query in the contract gets called ---------


def test_real_mode_calls_every_contract_query_once(monkeypatch):
    monkeypatch.setenv("POSTHOG_PERSONAL_API_KEY", FAKE_KEY)
    monkeypatch.setenv("POSTHOG_PROJECT_ID", FAKE_PROJECT_ID)
    expected_url = f"{DEFAULT_HOST}/api/projects/{FAKE_PROJECT_ID}/query/"

    with requests_mock.Mocker() as m:
        m.post(expected_url, json={"results": [[1]]}, status_code=200)
        report = module.build_report(since="2026-08-12T00:00:00Z", until="2026-08-12T12:00:00Z", fixture_dir=None)

    assert m.call_count == len(module.QUERY_CONTRACT)
    for name in module.QUERY_CONTRACT:
        assert report["queries"][name] == {"results": [[1]]}


def test_real_mode_default_since_is_rollout_timestamp(monkeypatch):
    monkeypatch.setenv("POSTHOG_PERSONAL_API_KEY", FAKE_KEY)
    monkeypatch.setenv("POSTHOG_PROJECT_ID", FAKE_PROJECT_ID)
    expected_url = f"{DEFAULT_HOST}/api/projects/{FAKE_PROJECT_ID}/query/"

    monkeypatch.setattr(sys, "argv", ["posthog_baseline_report.py"])
    with requests_mock.Mocker() as m:
        m.post(expected_url, json={"results": []}, status_code=200)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = module._main()

    assert exit_code == 0
    printed = json.loads(stdout.getvalue())
    assert printed["period"]["since"] == module.DEFAULT_ROLLOUT_SINCE


def test_real_mode_query_upstream_error_propagates_generic_message(monkeypatch):
    monkeypatch.setenv("POSTHOG_PERSONAL_API_KEY", FAKE_KEY)
    monkeypatch.setenv("POSTHOG_PROJECT_ID", FAKE_PROJECT_ID)
    expected_url = f"{DEFAULT_HOST}/api/projects/{FAKE_PROJECT_ID}/query/"

    with requests_mock.Mocker() as m:
        m.post(expected_url, status_code=401)
        with pytest.raises(module.PostHogReadOnlyQueryError):
            module.build_report(since="2026-08-12T00:00:00Z", until="2026-08-12T12:00:00Z", fixture_dir=None)


# --- output minimization: report never contains a raw per-row dump -----------


def test_report_note_documents_unverified_segmented_queries_are_excluded():
    report = module.build_report(since="2026-08-12T00:00:00Z", until="2026-08-12T12:00:00Z", fixture_dir=FIXTURE_DIR)
    assert "note" in report
    assert "ctr_by_classification" not in report["queries"]


def test_query_contract_never_selects_free_text_properties():
    """PII guard: every query template must reference only enum/boolean/
    count fields, never free-text properties like consultation raw text,
    email, or name."""
    forbidden_substrings = (
        "consultation",
        "raw_text",
        "email",
        "moodBefore",
        "moodAfter",
        "answer",
        "person.email",
        "person.name",
    )
    for name, template in {**module.QUERY_CONTRACT, **module.UNVERIFIED_SEGMENTED_QUERY_CONTRACT}.items():
        lowered = template.lower()
        for forbidden in forbidden_substrings:
            assert forbidden.lower() not in lowered, f"{name} references forbidden field {forbidden}"


def test_all_query_contract_templates_are_readonly_hogql():
    from guard import is_readonly_hogql

    for name, template in {**module.QUERY_CONTRACT, **module.UNVERIFIED_SEGMENTED_QUERY_CONTRACT}.items():
        rendered = module._render_query(template, since="'2026-01-01T00:00:00Z'", until="'2026-01-02T00:00:00Z'")
        assert is_readonly_hogql(rendered), f"{name} failed the read-only HogQL check"
