# backend/temples/tests/test_domain_goriyaku_taxonomy_v1.py
from __future__ import annotations

import pytest

from temples.domain.goriyaku_taxonomy_v1 import (
    GORIYAKU_TAXONOMY_NAMESPACE,
    GORIYAKU_TAXONOMY_VERSION,
    GORIYAKU_V1_CANONICAL_KEYS,
    validate_goriyaku_v1_canonical_key,
)


def test_namespace_is_goriyaku():
    assert GORIYAKU_TAXONOMY_NAMESPACE == "goriyaku"


def test_taxonomy_version_is_v1_string():
    assert GORIYAKU_TAXONOMY_VERSION == "v1"
    assert isinstance(GORIYAKU_TAXONOMY_VERSION, str)


def test_canonical_key_registry_is_intentionally_empty():
    # Mother Ship FINAL (Decision 1 = Option B): the 46-tag canonical
    # mapping is a DATA_REVIEW item, not implemented in PR-F3. This is a
    # fail-closed precondition, not a placeholder to fill in later inside
    # this test file.
    assert GORIYAKU_V1_CANONICAL_KEYS == {}


@pytest.mark.parametrize(
    "candidate",
    [
        "goriyaku:enmusubi",
        "goriyaku:love",
        "goriyaku:money",
        "goriyaku:health",
        "goriyaku:test",
        "goriyaku:a",
    ],
)
def test_any_plausible_goriyaku_key_is_rejected_fail_closed(candidate):
    result = validate_goriyaku_v1_canonical_key(candidate)
    assert result.valid is False
    assert result.reason == "unknown_goriyaku_key"
    assert result.canonical_key is None


def test_wrong_namespace_rejected():
    result = validate_goriyaku_v1_canonical_key("history_theme:restart")
    assert result.valid is False
    assert result.reason == "wrong_namespace"


@pytest.mark.parametrize(
    ("value", "expected_reason"),
    [
        (None, "empty_key"),
        ("", "empty_key"),
        ("no_namespace_prefix", "malformed_key"),
        ("goriyaku:", "empty_key"),
        ("goriyaku:a:b", "malformed_key"),
        (":enmusubi", "missing_namespace"),
    ],
)
def test_format_errors_propagate_from_shared_validator(value, expected_reason):
    # Confirms goriyaku_taxonomy_v1 reuses evidence_taxonomy's format
    # validator rather than re-implementing format parsing.
    result = validate_goriyaku_v1_canonical_key(value)
    assert result.valid is False
    assert result.reason == expected_reason
