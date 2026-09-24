"""concierge_chat_pool の現行挙動を固定する characterization test（F-5A §7.4）。

F-5A は `_ensure_pool_size()` / `_merge_candidate_fields()` に専用 test が
1 件も存在しないことを記録した（UNPROTECTED_SITES = 5 のうち 4 件）。
F-5B で共有 resolver へ集約する前に、**現在の well-formed な挙動**を先に固定する。

固定するのは valid な入力に対する挙動のみである。malformed legacy 挙動
（`shrine_id=0` が generic id へ落ちる、`int(True) -> 1` 等）は F-5A §3 の
matrix が記録済みであり、望ましい挙動として凍結しない。
"""
from __future__ import annotations

from temples.services.concierge_chat_pool import (
    _ensure_pool_size,
    _merge_candidate_fields,
)


def _rec(**kwargs):
    return {**kwargs}


class TestEnsurePoolSize:
    def test_valid_shrine_id_prevents_duplicate_insertion(self):
        """1. 有効な正の shrine_id を持つ候補は pool に重複投入されない。"""
        recs = {"recommendations": [_rec(shrine_id=42, name="既存神社")]}
        candidates = [_rec(shrine_id=42, name="別名だが同一Shrine")]

        out = _ensure_pool_size(recs, candidates=candidates, size=12)

        assert len(out["recommendations"]) == 1
        assert out["recommendations"][0]["shrine_id"] == 42

    def test_distinct_shrine_ids_are_both_kept(self):
        recs = {"recommendations": [_rec(shrine_id=42, name="A神社")]}
        candidates = [_rec(shrine_id=43, name="B神社")]

        out = _ensure_pool_size(recs, candidates=candidates, size=12)

        assert [r["shrine_id"] for r in out["recommendations"]] == [42, 43]

    def test_id_only_positive_integer_candidate_remains_compatible(self):
        """2. generic `id` のみの正整数候補は互換として扱われ続ける。"""
        recs = {"recommendations": [_rec(id=42, name="既存神社")]}
        candidates = [_rec(id=42, name="同一Shrineの別表現")]

        out = _ensure_pool_size(recs, candidates=candidates, size=12)

        assert len(out["recommendations"]) == 1

    def test_id_only_candidate_is_appended_when_pool_has_no_match(self):
        recs = {"recommendations": [_rec(shrine_id=42, name="A神社")]}
        candidates = [_rec(id=43, name="B神社")]

        out = _ensure_pool_size(recs, candidates=candidates, size=12)

        assert len(out["recommendations"]) == 2
        assert out["recommendations"][1]["id"] == 43

    def test_size_limit_is_unchanged(self):
        """3. size 上限の挙動は不変。上限に達したら以降を追加しない。"""
        recs = {"recommendations": [_rec(shrine_id=1, name="神社1")]}
        candidates = [_rec(shrine_id=i, name=f"神社{i}") for i in range(2, 10)]

        out = _ensure_pool_size(recs, candidates=candidates, size=3)

        assert len(out["recommendations"]) == 3
        assert [r["shrine_id"] for r in out["recommendations"]] == [1, 2, 3]

    def test_existing_over_size_pool_is_not_truncated(self):
        """既に size を超えている pool を切り詰めることはしない（現行挙動）。"""
        recs = {"recommendations": [_rec(shrine_id=i, name=f"神社{i}") for i in range(1, 6)]}

        out = _ensure_pool_size(recs, candidates=[], size=3)

        assert len(out["recommendations"]) == 5

    def test_name_dedupe_is_independent_of_identity(self):
        """identity が無くても name による重複排除は従来どおり効く。"""
        recs = {"recommendations": [_rec(name="同名神社")]}
        candidates = [_rec(name="同名神社")]

        out = _ensure_pool_size(recs, candidates=candidates, size=12)

        assert len(out["recommendations"]) == 1

    def test_non_dict_rows_are_skipped(self):
        recs = {"recommendations": [_rec(shrine_id=42, name="A"), "ゴミ", None]}

        out = _ensure_pool_size(recs, candidates=[], size=12)

        assert len(out["recommendations"]) == 1

    def test_other_recs_keys_are_preserved(self):
        recs = {"recommendations": [], "_seed": True, "meta": {"x": 1}}

        out = _ensure_pool_size(recs, candidates=[], size=12)

        assert out["_seed"] is True
        assert out["meta"] == {"x": 1}


class TestMergeCandidateFields:
    def test_valid_matching_shrine_identity_merges_candidate_fields(self):
        """4. 有効な shrine_id が一致する候補の field が merge される。"""
        recs = {"recommendations": [_rec(shrine_id=42, name="A神社")]}
        candidates = [_rec(shrine_id=42, name="A神社", address="東京都千代田区", goriyaku="厄除け")]

        out = _merge_candidate_fields(recs, candidates=candidates)

        row = out["recommendations"][0]
        assert row["shrine_id"] == 42
        assert row["address"] == "東京都千代田区"
        assert row["goriyaku"] == "厄除け"

    def test_recommendation_values_win_over_candidate_values(self):
        recs = {"recommendations": [_rec(shrine_id=42, name="A神社", reason="相談に一致")]}
        candidates = [_rec(shrine_id=42, name="A神社", reason="候補側の理由", address="東京")]

        out = _merge_candidate_fields(recs, candidates=candidates)

        row = out["recommendations"][0]
        assert row["reason"] == "相談に一致"
        assert row["address"] == "東京"

    def test_id_only_positive_integer_identity_merges(self):
        recs = {"recommendations": [_rec(id=42, name="A神社")]}
        candidates = [_rec(id=42, name="A神社", address="東京都")]

        out = _merge_candidate_fields(recs, candidates=candidates)

        assert out["recommendations"][0]["address"] == "東京都"

    def test_identity_absent_recommendation_may_use_name_fallback(self):
        """5. identity を持たない recommendation は既存の name fallback を使える。"""
        recs = {"recommendations": [_rec(name="A神社")]}
        candidates = [_rec(shrine_id=42, name="A神社", address="東京都")]

        out = _merge_candidate_fields(recs, candidates=candidates)

        row = out["recommendations"][0]
        assert row["address"] == "東京都"
        assert row["shrine_id"] == 42

    def test_unrelated_recommendation_remains_unchanged(self):
        """6. 無関係な recommendation は変更されない。"""
        recs = {"recommendations": [_rec(shrine_id=99, name="Z神社", reason="そのまま")]}
        candidates = [_rec(shrine_id=42, name="A神社", address="東京都")]

        out = _merge_candidate_fields(recs, candidates=candidates)

        row = out["recommendations"][0]
        assert row["shrine_id"] == 99
        assert row["name"] == "Z神社"
        assert row["reason"] == "そのまま"
        assert row.get("address") is None

    def test_non_dict_recommendation_rows_are_dropped(self):
        recs = {"recommendations": [_rec(shrine_id=42, name="A"), "ゴミ"]}

        out = _merge_candidate_fields(recs, candidates=[])

        assert len(out["recommendations"]) == 1

    def test_other_recs_keys_are_preserved(self):
        recs = {"recommendations": [], "_seed": True}

        out = _merge_candidate_fields(recs, candidates=[])

        assert out["_seed"] is True
