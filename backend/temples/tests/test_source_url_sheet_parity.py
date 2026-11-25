"""Contract tests for Source URL normalization and observed Sheet parity.

The spreadsheet observations were captured from 神社のDB / Knowledge出典!R480:R495
on 2026-11-02. They are snapshots, not a live Sheets integration.
Django's normalize_source_url remains the source of truth. Known mismatches
must remain explicit until the spreadsheet gate is changed and re-audited.
"""

from __future__ import annotations

import pytest

from temples.services.knowledge_seed import normalize_source_url


# input, backend expectation, spreadsheet observation (without source_type prefix)
BOUNDARY_CASES = (
    ("https://[2001:db8::1]/path", "https://2001:db8::1/path", "https://[2001:db8::1]/path"),
    ("https://[2001:db8::1]:443/path", "https://2001:db8::1/path", "https://[2001:db8::1]/path"),
    ("https://user:secret@EXAMPLE.com/path", "https://example.com/path", "https://example.com/path"),
    ("https://example.com:0443/a", "https://example.com/a", "https://example.com:0443/a"),
    ("https://example.com:abc/a", ValueError, "https://example.com:abc/a"),
    ("https://example.com:/a", "https://example.com/a", "https://example.com:/a"),
    ("https://example.com/a?", "https://example.com/a", "https://example.com/a?"),
    ("https://example.com/a?x=1&y=2", "https://example.com/a?x=1&y=2", "https://example.com/a?x=1&y=2"),
    ("https://example.com/a%2Fb", "https://example.com/a%2Fb", "https://example.com/a%2Fb"),
    ("HTTPS://EXAMPLE.COM//a///#frag", "https://example.com//a", "https://example.com//a"),
    ("https://例え.テスト/資料", "https://例え.テスト/資料", "https://例え.テスト/資料"),
    ("//example.com/path", "//example.com/path", "BACKEND_REVIEW"),
    ("ftp://Example.COM:21/a", "ftp://example.com:21/a", "BACKEND_REVIEW"),
    ("https://example.com/a#fragment", "https://example.com/a", "https://example.com/a"),
    ("https://example.com/a?x=1#frag", "https://example.com/a?x=1", "https://example.com/a?x=1"),
    (" https://EXAMPLE.com/a/ ", "https://example.com/a", "https://example.com/a"),
)


@pytest.mark.parametrize(
    ("raw_url", "backend_expected", "sheet_observed"),
    BOUNDARY_CASES,
    ids=[
        "ipv6", "ipv6-default-port", "userinfo", "zero-padded-default-port",
        "invalid-port", "empty-port", "empty-query", "multi-query",
        "percent-encoding", "repeated-slashes", "unicode", "schemeless",
        "ftp-scheme", "fragment", "query-and-fragment", "surrounding-whitespace",
    ],
)
def test_backend_url_normalization_contract(raw_url, backend_expected, sheet_observed):
    if backend_expected is ValueError:
        with pytest.raises(ValueError):
            normalize_source_url(raw_url)
    else:
        assert normalize_source_url(raw_url) == backend_expected


def test_spreadsheet_parity_snapshot_has_exactly_eight_known_mismatches():
    """Prevent silently treating the Sheet helper as authoritative.

    Refresh the observed values from the live Sheet before changing this snapshot.
    ValueError is a backend failure and therefore cannot count as parity.
    """
    mismatch_urls = {
        raw_url
        for raw_url, backend_expected, sheet_observed in BOUNDARY_CASES
        if backend_expected is ValueError or backend_expected != sheet_observed
    }
    assert len(BOUNDARY_CASES) == 16
    assert len(mismatch_urls) == 8
    assert {
        "https://[2001:db8::1]/path",
        "https://[2001:db8::1]:443/path",
        "https://example.com:0443/a",
        "https://example.com:abc/a",
        "https://example.com:/a",
        "https://example.com/a?",
        "//example.com/path",
        "ftp://Example.COM:21/a",
    } == mismatch_urls
