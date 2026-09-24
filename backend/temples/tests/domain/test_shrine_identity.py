"""Canonical backend Shrine identity resolver の pure unit test（F-5B Phase 2）。

    VALID_SHRINE_ID         = POSITIVE_INTEGER_ONLY
    CANONICAL_RESOLVER_MODE = STRICT_FAIL_CLOSED
    LEGACY_FALSY_FALLBACK   = NO
    INVALID_ALLOWED_ALIAS   = INVALID_WINS
    DIFFERENT_VALID_ALIASES = CONFLICT

DB を引かない純粋関数のテスト。
"""
from __future__ import annotations

import pytest

from temples.domain.shrine_identity import (
    ShrineIdentityResolution,
    resolve_shrine_id,
    resolve_shrine_identity,
)

POLICIES = ("live_candidate", "historical_snapshot")

# F-5A §3 の matrix が使った入力集合を含む。
ACCEPTED = [42, "42", 1, "1", 100001, "100001", " 42 ", "042"]
REJECTED = [
    0, "0", -1, "-1", 1.5, "1.5", -1.5, "-1.5",
    True, False, "", "   ", "abc", "42abc", "1e3", "0x2a",
    "４２", [], {}, (), object(),
]


class TestNormalizationAccepted:
    @pytest.mark.parametrize("policy", POLICIES)
    @pytest.mark.parametrize("value", ACCEPTED)
    def test_accepted_values_resolve_to_positive_int(self, policy, value):
        result = resolve_shrine_identity({"shrine_id": value}, policy=policy)

        assert result.status == "resolved"
        assert isinstance(result.shrine_id, int)
        assert result.shrine_id == int(str(value).strip())
        assert result.shrine_id > 0


class TestNormalizationRejected:
    @pytest.mark.parametrize("policy", POLICIES)
    @pytest.mark.parametrize("value", REJECTED)
    def test_rejected_values_are_invalid_not_resolved(self, policy, value):
        result = resolve_shrine_identity({"shrine_id": value}, policy=policy)

        assert result.status == "invalid", f"{value!r} は invalid でなければならない"
        assert result.shrine_id is None

    @pytest.mark.parametrize("policy", POLICIES)
    def test_bool_never_becomes_shrine_one(self, policy):
        """int(True) == 1 による誤解決を構造的に塞ぐ（F-5A §3.1 D-2）。"""
        assert resolve_shrine_id({"shrine_id": True}, policy=policy) is None
        assert resolve_shrine_id({"id": True}, policy=policy) is None

    @pytest.mark.parametrize("policy", POLICIES)
    def test_float_never_truncates_into_a_shrine_id(self, policy):
        """int(1.5) == 1 による誤解決を塞ぐ（F-5A §3.1 D-2）。"""
        assert resolve_shrine_id({"shrine_id": 1.5}, policy=policy) is None
        assert resolve_shrine_id({"shrine_id": 42.0}, policy=policy) is None

    @pytest.mark.parametrize("policy", POLICIES)
    def test_zero_is_invalid_and_never_falls_through_to_generic_id(self, policy):
        """LEGACY_FALSY_FALLBACK = NO（F-5A §3.1 D-1）。"""
        result = resolve_shrine_identity({"shrine_id": 0, "id": 777}, policy=policy)

        assert result.status == "invalid"
        assert result.shrine_id is None
        assert result.shrine_id != 777


class TestPresence:
    @pytest.mark.parametrize("policy", POLICIES)
    def test_none_value_is_absent_not_invalid(self, policy):
        assert resolve_shrine_identity({"shrine_id": None}, policy=policy) == (
            ShrineIdentityResolution(status="absent", shrine_id=None)
        )

    def test_none_shrine_id_lets_generic_id_resolve(self):
        """{"shrine_id": None, "id": 42} -> shrine_id absent -> id が 42 へ解決。"""
        result = resolve_shrine_identity({"shrine_id": None, "id": 42}, policy="live_candidate")

        assert result.status == "resolved"
        assert result.shrine_id == 42

    @pytest.mark.parametrize("policy", POLICIES)
    def test_missing_keys_are_absent(self, policy):
        assert resolve_shrine_identity({}, policy=policy).status == "absent"
        assert resolve_shrine_identity({"name": "A神社"}, policy=policy).status == "absent"

    @pytest.mark.parametrize("policy", POLICIES)
    def test_all_none_is_absent(self, policy):
        source = {"shrine_id": None, "id": None, "shrineId": None, "shrine": None}

        assert resolve_shrine_identity(source, policy=policy).status == "absent"


class TestLiveCandidatePolicy:
    def test_shrine_id_resolves(self):
        assert resolve_shrine_id({"shrine_id": 42}, policy="live_candidate") == 42

    def test_generic_id_resolves_as_compatibility_alias(self):
        assert resolve_shrine_id({"id": 42}, policy="live_candidate") == 42

    def test_equal_normalized_aliases_resolve(self):
        result = resolve_shrine_identity({"shrine_id": "42", "id": 42}, policy="live_candidate")

        assert result.status == "resolved"
        assert result.shrine_id == 42

    def test_different_valid_aliases_conflict(self):
        result = resolve_shrine_identity({"shrine_id": 42, "id": 999}, policy="live_candidate")

        assert result.status == "conflict"
        assert result.shrine_id is None

    def test_invalid_wins_over_a_valid_alias(self):
        result = resolve_shrine_identity({"shrine_id": 42, "id": "bad"}, policy="live_candidate")

        assert result.status == "invalid"
        assert result.shrine_id is None

    def test_historical_aliases_are_not_read(self):
        """live_candidate は shrineId / shrine を identity として読まない。"""
        assert resolve_shrine_identity({"shrineId": 42}, policy="live_candidate").status == "absent"
        assert resolve_shrine_identity({"shrine": 42}, policy="live_candidate").status == "absent"

    def test_historical_alias_does_not_create_a_conflict(self):
        result = resolve_shrine_identity({"shrine_id": 42, "shrineId": 999}, policy="live_candidate")

        assert result.status == "resolved"
        assert result.shrine_id == 42


class TestHistoricalSnapshotPolicy:
    @pytest.mark.parametrize("key", ["shrine_id", "shrineId", "shrine", "id"])
    def test_every_allowed_alias_resolves(self, key):
        assert resolve_shrine_id({key: 42}, policy="historical_snapshot") == 42

    def test_all_four_aliases_agreeing_resolve(self):
        source = {"shrine_id": 42, "shrineId": "42", "shrine": 42, "id": "42"}

        assert resolve_shrine_id(source, policy="historical_snapshot") == 42

    def test_any_disagreement_conflicts(self):
        source = {"shrine_id": 42, "shrine": 999}

        assert resolve_shrine_identity(source, policy="historical_snapshot").status == "conflict"

    def test_invalid_wins(self):
        source = {"shrine_id": 42, "shrine": 0}

        assert resolve_shrine_identity(source, policy="historical_snapshot").status == "invalid"

    def test_id_only_snapshot_shape_remains_readable(self):
        """F-5A §4.1 の id-only 履歴形状。"""
        assert resolve_shrine_id({"id": 42, "name": "A神社"}, policy="historical_snapshot") == 42


class TestProhibitedSources:
    @pytest.mark.parametrize("policy", POLICIES)
    @pytest.mark.parametrize(
        "key", ["place_id", "placeId", "google_place_id", "shrine_pk", "target_id"]
    )
    def test_prohibited_keys_never_participate(self, policy, key):
        assert resolve_shrine_identity({key: 42}, policy=policy).status == "absent"

    @pytest.mark.parametrize("policy", POLICIES)
    def test_place_id_does_not_disturb_a_valid_identity(self, policy):
        source = {"shrine_id": 42, "place_id": "ChIJxxx"}

        assert resolve_shrine_id(source, policy=policy) == 42

    @pytest.mark.parametrize("policy", POLICIES)
    def test_place_id_only_stays_absent(self, policy):
        assert resolve_shrine_identity({"place_id": "ChIJxxx"}, policy=policy).status == "absent"

    @pytest.mark.parametrize("policy", POLICIES)
    def test_name_and_address_never_participate(self, policy):
        source = {"name": "A神社", "address": "東京都千代田区"}

        assert resolve_shrine_identity(source, policy=policy).status == "absent"


class TestNonMappingAndRobustness:
    @pytest.mark.parametrize("policy", POLICIES)
    @pytest.mark.parametrize(
        "source", [None, 42, "42", True, False, [], ["shrine_id"], (), 1.5]
    )
    def test_non_mapping_is_absent(self, policy, source):
        assert resolve_shrine_identity(source, policy=policy).status == "absent"

    @pytest.mark.parametrize("policy", POLICIES)
    @pytest.mark.parametrize(
        "source",
        [None, 42, "x", [], {}, {"shrine_id": object()}, {"shrine_id": float("nan")},
         {"shrine_id": float("inf")}, {"id": b"42"}, {"shrine_id": {"nested": 1}}],
    )
    def test_never_raises(self, policy, source):
        resolve_shrine_identity(source, policy=policy)
        resolve_shrine_id(source, policy=policy)

    def test_unknown_policy_fails_closed_as_invalid(self):
        """未知 policy を absent にすると呼び出し側の非 identity fallback が開く。"""
        result = resolve_shrine_identity({"shrine_id": 42}, policy="nope")  # type: ignore[arg-type]

        assert result.status == "invalid"
        assert result.shrine_id is None

    @pytest.mark.parametrize("policy", POLICIES)
    def test_source_is_not_mutated(self, policy):
        source = {"shrine_id": "42", "id": 42, "name": "A神社"}
        before = dict(source)

        resolve_shrine_identity(source, policy=policy)

        assert source == before

    def test_resolution_is_frozen(self):
        result = resolve_shrine_identity({"shrine_id": 42}, policy="live_candidate")

        with pytest.raises(Exception):
            result.shrine_id = 99  # type: ignore[misc]


class TestWrapperDelegation:
    @pytest.mark.parametrize("policy", POLICIES)
    @pytest.mark.parametrize(
        "source",
        [
            {"shrine_id": 42},
            {"id": 42},
            {"shrine_id": "42", "id": 42},
            {"shrine_id": 42, "id": 999},
            {"shrine_id": 42, "id": "bad"},
            {"shrine_id": 0, "id": 777},
            {"shrine_id": None, "id": 42},
            {"place_id": "ChIJxxx"},
            {},
            None,
            "not-a-mapping",
        ],
    )
    def test_wrapper_returns_exactly_the_resolution_shrine_id(self, policy, source):
        assert resolve_shrine_id(source, policy=policy) == (
            resolve_shrine_identity(source, policy=policy).shrine_id
        )

    @pytest.mark.parametrize("policy", POLICIES)
    def test_wrapper_returns_none_for_every_non_resolved_status(self, policy):
        for source in ({}, {"shrine_id": "bad"}, {"shrine_id": 42, "id": 999}):
            resolution = resolve_shrine_identity(source, policy=policy)
            assert resolution.status != "resolved"
            assert resolve_shrine_id(source, policy=policy) is None


class TestTaskSpecifiedExamples:
    """タスク本文が明示した例をそのまま固定する。"""

    def test_examples(self):
        assert resolve_shrine_identity({"shrine_id": 42}, policy="live_candidate") == (
            ShrineIdentityResolution(status="resolved", shrine_id=42)
        )
        assert resolve_shrine_identity({"id": 42}, policy="live_candidate") == (
            ShrineIdentityResolution(status="resolved", shrine_id=42)
        )
        assert resolve_shrine_identity({"shrine_id": "42", "id": 42}, policy="live_candidate") == (
            ShrineIdentityResolution(status="resolved", shrine_id=42)
        )
        assert resolve_shrine_identity({"shrine_id": 0, "id": 777}, policy="live_candidate") == (
            ShrineIdentityResolution(status="invalid", shrine_id=None)
        )
        assert resolve_shrine_identity({"shrine_id": True, "id": 777}, policy="live_candidate") == (
            ShrineIdentityResolution(status="invalid", shrine_id=None)
        )
        assert resolve_shrine_identity({"shrine_id": 42, "id": 999}, policy="live_candidate") == (
            ShrineIdentityResolution(status="conflict", shrine_id=None)
        )
        assert resolve_shrine_identity({"shrine_id": 42, "id": "bad"}, policy="live_candidate") == (
            ShrineIdentityResolution(status="invalid", shrine_id=None)
        )
