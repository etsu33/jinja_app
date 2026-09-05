# backend/temples/tests/test_domain_goriyaku_taxonomy_v1.py
"""Evidence Foundation G1: goriyaku v1 canonical registry tests.

PR-F3 kept `GORIYAKU_V1_CANONICAL_KEYS` intentionally empty (Mother Ship
Decision 1 = Option B). G1's DATA_REVIEW activated the registry with exactly
18 approved canonical semantic identities, so the former
"registry is intentionally empty" assertion is no longer a current fact and
has been replaced by the exact-18 contract below.

Alias resolution is deliberately NOT tested here: `resolve != validate`, and
the alias registry/resolver lives in `temples.domain.goriyaku_alias_v1`
(see test_domain_goriyaku_alias_v1.py).
"""
from __future__ import annotations

import pytest

from temples.domain.goriyaku_taxonomy_v1 import (
    GORIYAKU_TAXONOMY_NAMESPACE,
    GORIYAKU_TAXONOMY_VERSION,
    GORIYAKU_V1_CANONICAL_KEYS,
    GORIYAKU_V1_CANONICAL_KEY_SET,
    validate_goriyaku_v1_canonical_key,
)

# Mother Ship DATA_REVIEW FINAL (G1). Written out literally here -- this test
# file is the contract pin, so it must not be derived from the module under
# test.
_APPROVED_V1_MAPPING = {
    "relationship_bonding": "縁結び",
    "misfortune_warding": "厄除け",
    "traffic_safety": "交通安全",
    "business_prosperity": "商売繁盛",
    "good_fortune": "開運",
    "household_safety": "家内安全",
    "academic_success": "学業成就",
    "exam_success": "合格祈願",
    "victory_fortune": "勝運",
    "maritime_safety": "海上安全",
    "safe_childbirth": "安産",
    "all_direction_warding": "八方除",
    "career_advancement": "出世運",
    "financial_fortune": "金運",
    "strong_fortune_warding": "強運厄除け",
    "illness_recovery": "病気平癒",
    "wish_fulfillment": "心願成就",
    "leg_lower_back_health": "足腰健康",
}

# The single positive reference key used across Evidence Foundation tests.
POSITIVE_REFERENCE_CANONICAL_KEY = "goriyaku:misfortune_warding"


def test_namespace_is_goriyaku():
    assert GORIYAKU_TAXONOMY_NAMESPACE == "goriyaku"


def test_taxonomy_version_is_v1_string():
    assert GORIYAKU_TAXONOMY_VERSION == "v1"
    assert isinstance(GORIYAKU_TAXONOMY_VERSION, str)


# --- 1 / 2: exactly 18 approved canonical semantic identities ---


def test_canonical_registry_has_exactly_eighteen_entries():
    assert len(GORIYAKU_V1_CANONICAL_KEYS) == 18


def test_canonical_registry_matches_the_approved_mapping_exactly():
    # Renaming, alternative English keys, slug changes, additions and
    # removals are all forbidden -- equality (not superset) is the contract.
    assert GORIYAKU_V1_CANONICAL_KEYS == _APPROVED_V1_MAPPING


def test_canonical_key_set_matches_registry_keys():
    assert GORIYAKU_V1_CANONICAL_KEY_SET == set(_APPROVED_V1_MAPPING)


def test_display_labels_are_unique():
    # Display labels are display values, but two canonical identities sharing
    # one Japanese label would make the registry ambiguous for humans.
    assert len(set(GORIYAKU_V1_CANONICAL_KEYS.values())) == 18


# --- 3: all 18 canonical full keys validate ---


@pytest.mark.parametrize(("local_key", "display_label_ja"), sorted(_APPROVED_V1_MAPPING.items()))
def test_all_eighteen_canonical_full_keys_are_valid(local_key, display_label_ja):
    result = validate_goriyaku_v1_canonical_key(f"goriyaku:{local_key}")
    assert result.valid is True
    assert result.reason == "valid"
    assert result.canonical_key == f"goriyaku:{local_key}"
    assert result.display_label_ja == display_label_ja


# --- 4: positive reference key ---


def test_positive_reference_key_is_valid():
    result = validate_goriyaku_v1_canonical_key(POSITIVE_REFERENCE_CANONICAL_KEY)
    assert result.valid is True
    assert result.reason == "valid"
    assert result.canonical_key == POSITIVE_REFERENCE_CANONICAL_KEY
    assert result.display_label_ja == "厄除け"


# --- 5: unapproved keys stay fail-closed ---


@pytest.mark.parametrize(
    "candidate",
    [
        "goriyaku:enmusubi",
        "goriyaku:love",
        "goriyaku:money",
        "goriyaku:health",
        "goriyaku:test",
        "goriyaku:a",
        # DEFERRED concepts are not part of v1.
        "goriyaku:pet_health",
        "goriyaku:art_improvement",
        # Plausible-looking near misses of approved keys are still unapproved.
        "goriyaku:relationship_bond",
        "goriyaku:misfortune_ward",
        "goriyaku:all_direction_ward",
    ],
)
def test_unapproved_goriyaku_key_is_rejected_fail_closed(candidate):
    result = validate_goriyaku_v1_canonical_key(candidate)
    assert result.valid is False
    assert result.reason == "unknown_goriyaku_key"
    assert result.canonical_key is None
    assert result.display_label_ja is None


def test_validator_does_not_resolve_aliases_or_japanese_labels():
    # resolve != validate. The validator never accepts a surface alias or a
    # Japanese display label as a canonical key, and never performs alias
    # lookup on its own.
    for surface in ("goriyaku:八方除け", "goriyaku:八方除", "八方除け", "goriyaku:厄除け"):
        result = validate_goriyaku_v1_canonical_key(surface)
        assert result.valid is False
        assert result.canonical_key is None


def test_wrong_namespace_rejected():
    result = validate_goriyaku_v1_canonical_key("history_theme:restart")
    assert result.valid is False
    assert result.reason == "wrong_namespace"


def test_history_theme_key_is_not_accepted_via_goriyaku_registry():
    result = validate_goriyaku_v1_canonical_key("history_theme:protection")
    assert result.valid is False
    assert result.canonical_key is None


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
