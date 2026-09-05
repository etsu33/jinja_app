# backend/temples/tests/test_domain_goriyaku_alias_v1.py
"""Evidence Foundation G1: goriyaku v1 alias registry / resolver tests.

Pins the Mother Ship FINAL alias contract:

- the alias registry holds exactly one approved entry
  (`八方除け -> all_direction_warding`),
- alias resolution is exact-string-equality only (no strip / lower /
  replace / Unicode normalization / prefix / suffix / substring / regex /
  delimiter split, and no fuzzy or semantic similarity),
- an unknown alias is a normal "unresolved in v1" result, not an exception,
- invalid input fails closed,
- a broken alias target never produces a canonical identity,
- `resolve != validate` -- the resolver's output is what gets handed to the
  existing canonical validator.
"""
from __future__ import annotations

import dataclasses

import pytest

from temples.domain import goriyaku_alias_v1
from temples.domain.goriyaku_alias_v1 import (
    GORIYAKU_V1_ALIASES,
    GoriyakuAliasResolutionResult,
    resolve_goriyaku_alias,
)
from temples.domain.goriyaku_taxonomy_v1 import (
    GORIYAKU_V1_CANONICAL_KEYS,
    validate_goriyaku_v1_canonical_key,
)

APPROVED_ALIAS = "八方除け"
APPROVED_ALIAS_TARGET_LOCAL_KEY = "all_direction_warding"
APPROVED_ALIAS_CANONICAL_KEY = "goriyaku:all_direction_warding"
APPROVED_ALIAS_DISPLAY_LABEL_JA = "八方除"


# --- 6 / 7: alias registry is exactly one approved entry ---


def test_alias_registry_has_exactly_one_entry():
    assert len(GORIYAKU_V1_ALIASES) == 1


def test_alias_registry_matches_the_approved_mapping_exactly():
    assert GORIYAKU_V1_ALIASES == {APPROVED_ALIAS: APPROVED_ALIAS_TARGET_LOCAL_KEY}


# --- 8: every alias target exists in the canonical registry ---


def test_every_alias_target_exists_in_the_canonical_registry():
    unknown_targets = sorted(
        target for target in GORIYAKU_V1_ALIASES.values() if target not in GORIYAKU_V1_CANONICAL_KEYS
    )
    assert unknown_targets == []


# --- 9: canonical display labels are not alias surfaces ---


def test_canonical_display_label_is_not_registered_as_an_alias():
    # 八方除 is the canonical display label, not a surface alias.
    assert APPROVED_ALIAS_DISPLAY_LABEL_JA not in GORIYAKU_V1_ALIASES


def test_no_canonical_display_label_is_registered_as_an_alias():
    overlaps = sorted(set(GORIYAKU_V1_CANONICAL_KEYS.values()) & set(GORIYAKU_V1_ALIASES))
    assert overlaps == []


def test_no_canonical_local_key_is_registered_as_an_alias():
    overlaps = sorted(set(GORIYAKU_V1_CANONICAL_KEYS) & set(GORIYAKU_V1_ALIASES))
    assert overlaps == []


# --- 10: exact alias resolution succeeds ---


def test_approved_alias_resolves_exactly():
    result = resolve_goriyaku_alias(APPROVED_ALIAS)
    assert result.resolved is True
    assert result.reason == "resolved"
    assert result.input_alias == APPROVED_ALIAS
    assert result.canonical_key == APPROVED_ALIAS_CANONICAL_KEY
    assert result.display_label_ja == APPROVED_ALIAS_DISPLAY_LABEL_JA


def test_resolution_result_is_immutable():
    result = resolve_goriyaku_alias(APPROVED_ALIAS)
    assert isinstance(result, GoriyakuAliasResolutionResult)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.canonical_key = "goriyaku:relationship_bonding"  # type: ignore[misc]


def test_resolver_is_deterministic():
    assert resolve_goriyaku_alias(APPROVED_ALIAS) == resolve_goriyaku_alias(APPROVED_ALIAS)


# --- 11: resolver output feeds the existing canonical validator ---


def test_resolver_output_passes_the_existing_canonical_validator():
    resolution = resolve_goriyaku_alias(APPROVED_ALIAS)
    validation = validate_goriyaku_v1_canonical_key(resolution.canonical_key)
    assert validation.valid is True
    assert validation.reason == "valid"
    assert validation.canonical_key == APPROVED_ALIAS_CANONICAL_KEY
    assert validation.display_label_ja == APPROVED_ALIAS_DISPLAY_LABEL_JA


# --- 12: whitespace variants are NOT stripped ---


@pytest.mark.parametrize(
    "surface",
    [
        " 八方除け",
        "八方除け ",
        " 八方除け ",
        "　八方除け",  # full-width space, leading
        "八方除け　",  # full-width space, trailing
        "\t八方除け",
        "八方除け\n",
        "八方 除け",  # internal whitespace
        "八方　除け",  # internal full-width space
    ],
)
def test_whitespace_variants_are_unknown_alias(surface):
    result = resolve_goriyaku_alias(surface)
    assert result.resolved is False
    assert result.reason == "unknown_alias"
    assert result.canonical_key is None
    assert result.display_label_ja is None


@pytest.mark.parametrize("surface", [" ", "   ", "　", "\t", "\n"])
def test_whitespace_only_input_is_unknown_alias_not_invalid_input(surface):
    # Whitespace-only strings are never stripped, so they are simply
    # surfaces that the registry does not contain.
    result = resolve_goriyaku_alias(surface)
    assert result.resolved is False
    assert result.reason == "unknown_alias"
    assert result.canonical_key is None


# --- 13: prefix / suffix variants ---


@pytest.mark.parametrize(
    "surface",
    [
        "八方除けの",
        "八方除けお守り",
        "御八方除け",
        "厄除け八方除け",
        "八方除けです",
    ],
)
def test_prefix_and_suffix_variants_are_unknown_alias(surface):
    result = resolve_goriyaku_alias(surface)
    assert result.resolved is False
    assert result.reason == "unknown_alias"
    assert result.canonical_key is None


# --- 14: substring / compound inputs ---


@pytest.mark.parametrize(
    "surface",
    [
        "八方除け・厄除け",
        "厄除け・八方除け",
        "八方除け/方除け",
        "八方除け、金運",
        "八方",
        "除け",
    ],
)
def test_substring_and_compound_inputs_are_unknown_alias(surface):
    result = resolve_goriyaku_alias(surface)
    assert result.resolved is False
    assert result.reason == "unknown_alias"
    assert result.canonical_key is None


# --- 15 / 16 / 17: near-miss surfaces stay unresolved ---


def test_spelling_variant_hachihou_yoke_is_unknown_alias():
    result = resolve_goriyaku_alias("八方よけ")
    assert result.resolved is False
    assert result.reason == "unknown_alias"
    assert result.canonical_key is None


def test_partial_hou_yoke_is_unknown_alias():
    result = resolve_goriyaku_alias("方除け")
    assert result.resolved is False
    assert result.reason == "unknown_alias"
    assert result.canonical_key is None


def test_canonical_display_label_is_unknown_to_the_alias_resolver():
    # 八方除 is a canonical display label, not a registered alias. The
    # resolver resolves aliases, not display labels.
    result = resolve_goriyaku_alias(APPROVED_ALIAS_DISPLAY_LABEL_JA)
    assert result.resolved is False
    assert result.reason == "unknown_alias"
    assert result.canonical_key is None


@pytest.mark.parametrize(
    "surface",
    sorted(GORIYAKU_V1_CANONICAL_KEYS.values()),
)
def test_no_canonical_display_label_resolves_through_the_alias_resolver(surface):
    result = resolve_goriyaku_alias(surface)
    assert result.resolved is False
    assert result.reason == "unknown_alias"


@pytest.mark.parametrize(
    "surface",
    sorted(GORIYAKU_V1_CANONICAL_KEYS),
)
def test_canonical_local_keys_do_not_resolve_through_the_alias_resolver(surface):
    result = resolve_goriyaku_alias(surface)
    assert result.resolved is False
    assert result.reason == "unknown_alias"


# --- 18: arbitrary unknown strings ---


@pytest.mark.parametrize(
    "surface",
    [
        "縁結び祈願",
        "ペット健康",
        "unknown",
        "all_direction_warding ",
        "goriyaku:all_direction_warding",
        "はっぽうよけ",
        "ハッポウヨケ",
        "八方除ケ",
        "🎌",
    ],
)
def test_arbitrary_unknown_strings_are_unknown_alias(surface):
    result = resolve_goriyaku_alias(surface)
    assert result.resolved is False
    assert result.reason == "unknown_alias"
    assert result.canonical_key is None
    assert result.display_label_ja is None


def test_unknown_alias_does_not_raise():
    # An unknown alias means "unresolved in v1", not "invalid concept".
    assert resolve_goriyaku_alias("存在しない表記").resolved is False


# --- 19: invalid input fails closed ---


@pytest.mark.parametrize("value", [None, "", 0, 1, 1.5, True, [], {}, set(), object(), b"\xe5\x85\xab"])
def test_invalid_input_fails_closed(value):
    result = resolve_goriyaku_alias(value)
    assert result.resolved is False
    assert result.reason == "invalid_input"
    assert result.canonical_key is None
    assert result.display_label_ja is None


def test_invalid_input_does_not_echo_a_non_string_as_input_alias():
    assert resolve_goriyaku_alias(123).input_alias is None
    assert resolve_goriyaku_alias("").input_alias == ""


# --- 20 / 21: broken alias target ---


def test_broken_alias_target_is_reported_as_invalid_alias_target(monkeypatch):
    monkeypatch.setattr(
        goriyaku_alias_v1,
        "GORIYAKU_V1_ALIASES",
        {"壊れた別名": "not_an_approved_canonical_key"},
    )
    result = goriyaku_alias_v1.resolve_goriyaku_alias("壊れた別名")
    assert result.resolved is False
    assert result.reason == "invalid_alias_target"
    assert result.input_alias == "壊れた別名"


def test_broken_alias_target_never_produces_a_canonical_key(monkeypatch):
    monkeypatch.setattr(
        goriyaku_alias_v1,
        "GORIYAKU_V1_ALIASES",
        {"壊れた別名": "not_an_approved_canonical_key"},
    )
    result = goriyaku_alias_v1.resolve_goriyaku_alias("壊れた別名")
    assert result.canonical_key is None
    assert result.display_label_ja is None
    # And no fake full key leaks into the canonical validator either.
    assert validate_goriyaku_v1_canonical_key(
        "goriyaku:not_an_approved_canonical_key"
    ).valid is False


def test_alias_registry_is_restored_after_monkeypatching():
    # Guards the two tests above against leaking a broken registry.
    assert GORIYAKU_V1_ALIASES == {APPROVED_ALIAS: APPROVED_ALIAS_TARGET_LOCAL_KEY}


# --- resolver purity ---


def test_resolver_needs_no_database():
    # This module-level test is intentionally NOT marked django_db: the
    # resolver must be pure / deterministic / DB-free.
    assert resolve_goriyaku_alias(APPROVED_ALIAS).canonical_key == APPROVED_ALIAS_CANONICAL_KEY
