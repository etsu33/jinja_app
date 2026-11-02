"""Fail-closed contract for Source URL normalization.

normalize_source_url must either return the existing normalized identity or
raise SourceUrlError (a ValueError). It must never raise anything else and
never collapse malformed input into an identity.
See docs/audit/source-url-fail-closed-hardening.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from temples.services.knowledge_seed import SourceUrlError, normalize_source_url, parse_seed
from temples.tests.test_source_url_sheet_parity import BOUNDARY_CASES

SEED_DIR = Path(__file__).resolve().parents[1] / "data" / "knowledge_seeds"


@pytest.mark.parametrize(("raw_url", "backend_expected", "_sheet"), BOUNDARY_CASES)
def test_existing_16_boundary_cases_keep_their_contract(raw_url, backend_expected, _sheet):
    """Valid cases keep their exact normalized value; the one invalid case
    now fails with the typed, actionable error instead of a bare ValueError."""
    if backend_expected is ValueError:
        with pytest.raises(SourceUrlError, match=r"port 'abc' is not a number"):
            normalize_source_url(raw_url)
    else:
        assert normalize_source_url(raw_url) == backend_expected


VALID_UNCHANGED = (
    (None, ""),
    ("", ""),
    ("   ", ""),
    ("https://example.com:65535/a", "https://example.com:65535/a"),
    ("https://example.com:0/a", "https://example.com:0/a"),
    ("https://example.com:80/a", "https://example.com:80/a"),
    ("http://example.com:443/a", "http://example.com:443/a"),
    ("http://example.com:80/a", "http://example.com/a"),
    ("https://example.com/a b", "https://example.com/a b"),
    ("https://example.com/a?b=%20&c", "https://example.com/a?b=%20&c"),
    ("example.com/a", "example.com/a"),
    ("file:///etc/x", "file:///etc/x"),
)


@pytest.mark.parametrize(("raw_url", "expected"), VALID_UNCHANGED)
def test_additional_valid_inputs_keep_existing_normalization(raw_url, expected):
    assert normalize_source_url(raw_url) == expected


MALFORMED = (
    # malformed ports
    ("https://example.com:99999/a", "out of range"),
    ("https://example.com:65536/a", "out of range"),
    ("https://example.com:+443/a", "not a number"),
    ("https://example.com:-1/a", "not a number"),
    ("https://example.com:４４３/a", "not a number"),
    ("https://example.com:443:80/a", "not a number"),
    ("https://a:b:c/", "not a number"),
    ("https://[2001:db8::1]:abc/a", "not a number"),
    ("https://example.com: 443/a", "whitespace"),
    # broken IPv6 / bracket structure
    ("https://[2001:db8::1/a", "invalid URL structure"),
    ("https://[2001:db8::1]x/a", "invalid URL structure"),
    ("https://[zzz]/a", "invalid URL structure"),
    ("https://[v1.x]/a", "not an IPv6 address"),
    ("https://[::1%25eth0]/a", "zone identifiers"),
    # empty host: these all used to collapse to 'https:///a'
    ("https://:443/a", "host is empty"),
    ("https://user@/a", "host is empty"),
    ("//:80/x", "host is empty"),
    ("https:///a", "must have a host"),
    ("https:/a", "must have a host"),
    ("https:example.com", "must have a host"),
    ("http://", "must have a host"),
    # characters urlsplit would silently drop or keep inside the host
    ("https://exa\nmple.com/a", "control characters"),
    ("https://example.com/a\tb", "control characters"),
    ("https://example.com/a\rb", "control characters"),
    ("https://example.com/a\x00b", "control characters"),
    ("https://example.com/a\x7fb", "control characters"),
    ("https://ex ample.com/a", "whitespace"),
    ("https://example.com\\a", "backslashes"),
    # non-string input
    (123, "must be a string"),
    (["https://example.com/"], "must be a string"),
)


@pytest.mark.parametrize(("raw_url", "message"), MALFORMED)
def test_malformed_inputs_fail_closed_with_actionable_error(raw_url, message):
    with pytest.raises(SourceUrlError, match=message):
        normalize_source_url(raw_url)


def test_source_url_error_is_a_value_error_and_does_not_echo_credentials():
    with pytest.raises(ValueError) as excinfo:
        normalize_source_url("https://user:s3cret@[::1/a")
    assert isinstance(excinfo.value, SourceUrlError)
    assert "s3cret" not in str(excinfo.value)


def _seed_with_url(url) -> dict:
    return {
        "schema_version": "1.0",
        "sources": [
            {
                "key": "src-1",
                "source_type": "shrine_official",
                "title": "公式サイト",
                "url": url,
                "verification_status": "draft",
            }
        ],
        "shrines": [],
    }


@pytest.mark.parametrize(("raw_url", "message"), MALFORMED)
def test_parse_seed_reports_malformed_url_without_raising(raw_url, message):
    parsed = parse_seed(_seed_with_url(raw_url))
    url_errors = [e for e in parsed.errors if e.startswith("sources[0].url: ")]
    assert len(url_errors) == 1
    assert message in url_errors[0]


@pytest.mark.parametrize("raw_url", [None, "", "https://EXAMPLE.jp/a/"])
def test_parse_seed_accepts_empty_and_valid_urls(raw_url):
    parsed = parse_seed(_seed_with_url(raw_url))
    assert parsed.errors == []
    assert parsed.sources["src-1"].url == (raw_url or "")


def test_parse_seed_keeps_non_string_url_for_identity_check():
    parsed = parse_seed(_seed_with_url(123))
    assert parsed.sources["src-1"].url == 123


def test_every_committed_seed_url_still_normalizes():
    """Impact check: the hardening rejects no Source URL already in the repo."""
    checked = 0
    for path in sorted(SEED_DIR.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        for source in raw.get("sources") or []:
            if "url" in source:
                normalize_source_url(source["url"])
                checked += 1
    assert checked > 0
