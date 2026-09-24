"""F-5B で共有 resolver へ集約した consumer の identity hardening test。

対象（F-5A の site 番号）:
    #8  concierge_chat._build_score_v3_candidate_profile
    #18 recommendation_quality_measurement.build_shrine_reason_provenance
    #19 recommendation_score_components.calculate_shrine_profile_score

docs/audit/backend-shrine-identity-fallback-consolidation.md §14
"""
from __future__ import annotations

import pytest

from temples.services.concierge_chat import _build_score_v3_candidate_profile
from temples.services.recommendation_score_components import calculate_shrine_profile_score


def _rec(**kwargs):
    return {"name": "テスト神社", **kwargs}


def _with_source(shrine_id_value, **rec_kwargs):
    return _rec(meaning_payload={"source": {"shrineId": shrine_id_value}}, **rec_kwargs)


class TestScoreV3CandidateProfileIdentity:
    """#8: source.shrineId は live_candidate policy の許可 alias ではない。"""

    def test_resolved_rec_identity_is_used(self):
        profile = _build_score_v3_candidate_profile(_rec(shrine_id=42))

        assert profile["shrine_id"] == 42

    def test_generic_id_remains_a_compatibility_alias(self):
        profile = _build_score_v3_candidate_profile(_rec(id=42))

        assert profile["shrine_id"] == 42

    def test_conflict_plus_valid_source_shrine_id_yields_none(self):
        """必須回帰。rec が conflict のとき source.shrineId へ fallback しない。"""
        profile = _build_score_v3_candidate_profile(_with_source(7, shrine_id=42, id=999))

        assert profile["shrine_id"] is None

    def test_invalid_plus_valid_source_shrine_id_yields_none(self):
        """必須回帰。rec が invalid のとき source.shrineId へ fallback しない。"""
        profile = _build_score_v3_candidate_profile(_with_source(7, shrine_id="bad"))

        assert profile["shrine_id"] is None

    def test_zero_identity_plus_valid_source_shrine_id_yields_none(self):
        profile = _build_score_v3_candidate_profile(_with_source(7, shrine_id=0))

        assert profile["shrine_id"] is None

    def test_absent_identity_keeps_source_shrine_id_compatibility(self):
        """必須回帰。rec の identity が absent のときだけ source が互換参照される。"""
        profile = _build_score_v3_candidate_profile(_with_source(7))

        assert profile["shrine_id"] == 7

    def test_absent_identity_with_string_source_shrine_id(self):
        profile = _build_score_v3_candidate_profile(_with_source("7"))

        assert profile["shrine_id"] == 7

    def test_absent_identity_with_invalid_source_shrine_id_yields_none(self):
        for bad in (0, -1, 1.5, True, "", "abc", None):
            profile = _build_score_v3_candidate_profile(_with_source(bad))
            assert profile["shrine_id"] is None, bad

    def test_source_shrine_id_is_not_a_global_alias(self):
        """shrineId 単体は live candidate の identity として読まれない。"""
        profile = _build_score_v3_candidate_profile(_rec(shrineId=42))

        assert profile["shrine_id"] is None

    def test_no_identity_at_all_yields_none(self):
        assert _build_score_v3_candidate_profile(_rec())["shrine_id"] is None


class TestShrineReasonProvenanceIdentity:
    """#18: 0 = REPORTING_SENTINEL / 0 != VALID_SHRINE_IDENTITY。"""

    @staticmethod
    def _provenance(candidate):
        from temples.services.recommendation_quality_measurement import (
            build_shrine_reason_provenance,
        )

        return build_shrine_reason_provenance(candidate)

    def test_normal_positive_id_is_unchanged(self):
        assert self._provenance(_rec(shrine_id=42)).shrine_id == 42

    def test_generic_id_remains_compatible(self):
        assert self._provenance(_rec(id=42)).shrine_id == 42

    def test_invalid_string_no_longer_raises(self):
        """旧実装は unguarded int() で ValueError を投げていた（F-5A §3.1 D-3）。"""
        for bad in ("abc", "1.5", "42abc"):
            provenance = self._provenance(_rec(shrine_id=bad))
            assert provenance.shrine_id == 0

    def test_bool_no_longer_becomes_shrine_one(self):
        """int(True) == 1（F-5A §3.1 D-2）。"""
        assert self._provenance(_rec(shrine_id=True)).shrine_id == 0
        assert self._provenance(_rec(shrine_id=False)).shrine_id == 0

    def test_float_no_longer_truncates(self):
        assert self._provenance(_rec(shrine_id=1.5)).shrine_id == 0

    def test_conflict_maps_to_the_reporting_sentinel(self):
        assert self._provenance(_rec(shrine_id=42, id=999)).shrine_id == 0

    def test_absent_identity_keeps_the_existing_sentinel(self):
        assert self._provenance(_rec()).shrine_id == 0

    def test_zero_shrine_id_does_not_fall_through_to_generic_id(self):
        assert self._provenance(_rec(shrine_id=0, id=777)).shrine_id == 0

    def test_name_is_still_reported(self):
        assert self._provenance(_rec(shrine_id=42)).name == "テスト神社"


class TestShrineProfileScoreIdentityCredit:
    """#19: identity completeness は status == resolved のときだけ加点する。"""

    @staticmethod
    def _score(candidate_profile):
        return calculate_shrine_profile_score({"candidate_profile": candidate_profile})

    def test_resolved_identity_earns_the_credit(self):
        assert self._score({"shrine_id": 42}) == pytest.approx(0.2)

    def test_generic_id_still_earns_the_credit(self):
        assert self._score({"id": 42}) == pytest.approx(0.2)

    def test_conflict_earns_no_credit(self):
        assert self._score({"shrine_id": 42, "id": 999}) == pytest.approx(0.0)

    def test_invalid_identity_earns_no_credit(self):
        for bad in (0, -1, 1.5, True, "", "abc"):
            assert self._score({"shrine_id": bad}) == pytest.approx(0.0), bad

    def test_absent_identity_earns_no_credit(self):
        assert self._score({}) == pytest.approx(0.0)

    def test_other_score_components_are_unchanged(self):
        profile = {
            "shrine_id": 42,
            "name": "A神社",
            "history_theme": "再出発",
            "goriyaku": "厄除け",
            "visit_style_tags": ["静か"],
        }

        assert self._score(profile) == pytest.approx(1.0)

    def test_broken_identity_only_costs_the_identity_credit(self):
        profile = {
            "shrine_id": 0,
            "name": "A神社",
            "history_theme": "再出発",
            "goriyaku": "厄除け",
            "visit_style_tags": ["静か"],
        }

        assert self._score(profile) == pytest.approx(0.8)
