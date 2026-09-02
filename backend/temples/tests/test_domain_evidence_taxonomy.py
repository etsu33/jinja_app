# backend/temples/tests/test_domain_evidence_taxonomy.py
from __future__ import annotations

import pytest

from temples.domain.evidence_taxonomy import (
    EVIDENCE_TAXONOMY_NAMESPACES,
    get_current_taxonomy_version,
    is_registered_taxonomy_namespace,
    validate_canonical_semantic_key,
)


def test_registered_namespaces_are_history_theme_and_goriyaku_only():
    assert EVIDENCE_TAXONOMY_NAMESPACES == ["history_theme", "goriyaku"]


@pytest.mark.parametrize(
    ("namespace", "expected"),
    [
        ("history_theme", True),
        ("goriyaku", True),
        ("need_tag", False),
        ("consultation_axis", False),
        ("", False),
    ],
)
def test_is_registered_taxonomy_namespace(namespace, expected):
    assert is_registered_taxonomy_namespace(namespace) is expected


def test_get_current_taxonomy_version_for_registered_namespace():
    version = get_current_taxonomy_version("history_theme")
    assert version.namespace == "history_theme"
    assert version.version == "v1"

    version = get_current_taxonomy_version("goriyaku")
    assert version.namespace == "goriyaku"
    assert version.version == "v1"


def test_taxonomy_version_is_string_not_integer():
    # Mother Ship FINAL contract: taxonomyVersion is a string end-to-end
    # (matches the future PR-F5 normalized_evidence transport contract).
    # No integer representation or integer<->string conversion helper exists.
    version = get_current_taxonomy_version("history_theme")
    assert isinstance(version.version, str)
    assert not isinstance(version.version, bool)


def test_get_current_taxonomy_version_rejects_unregistered_namespace():
    with pytest.raises(ValueError):
        get_current_taxonomy_version("unknown_namespace")


@pytest.mark.parametrize(
    ("value", "expected_namespace", "expected_key"),
    [
        ("history_theme:warrior", "history_theme", "warrior"),
        ("goriyaku:love", "goriyaku", "love"),
    ],
)
def test_validate_canonical_semantic_key_valid(value, expected_namespace, expected_key):
    result = validate_canonical_semantic_key(value)
    assert result.valid is True
    assert result.reason == "valid"
    assert result.namespace == expected_namespace
    assert result.key == expected_key


@pytest.mark.parametrize(
    ("value", "expected_reason"),
    [
        (None, "empty_key"),
        ("", "empty_key"),
        ("   ", "empty_key"),
        ("no_namespace_prefix", "malformed_key"),
        ("history_theme:a:b", "malformed_key"),
        (":warrior", "missing_namespace"),
        ("unknown_namespace:warrior", "unknown_namespace"),
        ("history_theme:", "empty_key"),
        ("goriyaku:", "empty_key"),
    ],
)
def test_validate_canonical_semantic_key_invalid(value, expected_reason):
    result = validate_canonical_semantic_key(value)
    assert result.valid is False
    assert result.reason == expected_reason
