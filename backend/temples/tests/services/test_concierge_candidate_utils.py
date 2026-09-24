from temples.services.concierge_candidate_utils import (
    _candidate_key,
    _dedupe_candidates,
    _normalize_candidate_fields,
    _to_float,
)

import pytest

from temples.domain.shrine_identity import resolve_shrine_identity


def test_to_float_handles_numbers_and_strings():
    assert _to_float(1) == 1.0
    assert _to_float(" 1.5 ") == 1.5
    assert _to_float("") is None
    assert _to_float(None) is None
    assert _to_float("x") is None


def test_candidate_key_prefers_place_id_then_shrine_id_then_name_address():
    assert _candidate_key({"place_id": "pid-1", "shrine_id": 3, "name": "A"}) == (
        "place_id",
        "pid-1",
    )
    # F-5B #6（意図的な契約修正、F-5A §3.1 D-5）: identity key は共有 resolver が
    # 正規化した **正の int** になる。旧実装は str(...) で "3" を返していた。
    assert _candidate_key({"shrine_id": 3, "name": "A"}) == ("shrine_id", 3)
    # "3" と 3 は正規化後に同一 key になる（旧実装も str 化で同一だった）。
    assert _candidate_key({"shrine_id": "3", "name": "A"}) == ("shrine_id", 3)
    assert _candidate_key({"name": "A", "formatted_address": "Tokyo"}) == (
        "name_address",
        "A",
        "Tokyo",
    )


def test_dedupe_candidates_keeps_first_item_for_same_key():
    first = {"place_id": "pid-1", "name": "A", "address": "addr-1"}
    second = {"place_id": "pid-1", "name": "B", "address": "addr-2"}

    assert _dedupe_candidates([first, second]) == [first]


def test_normalize_candidate_fields_keeps_distance_m():
    src = {"name": "A", "lat": "35.0", "lng": "139.0", "distance_m": "100"}
    out = _normalize_candidate_fields(src)

    assert out["lat"] == 35.0
    assert out["lng"] == 139.0
    assert out["distance_m"] == 100.0


# ---------------------------------------------------------------------------
# F-5B #6: identity が壊れている候補を name/address の同一性へ読み替えない。
#
#   resolved           -> ("shrine_id", 正の int)
#   absent             -> ("name_address", ...)
#   invalid / conflict -> None（重複排除キーを与えない = fail closed）
#
# place_id 優先の挙動は未変更（place_id は F-6 のスコープ）。
# docs/audit/backend-shrine-identity-fallback-consolidation.md §14
# ---------------------------------------------------------------------------


def test_candidate_key_id_only_positive_integer_remains_compatible():
    assert _candidate_key({"id": 3, "name": "A"}) == ("shrine_id", 3)


def test_candidate_key_absent_identity_uses_name_address():
    assert _candidate_key({"name": "A", "address": "Tokyo"}) == ("name_address", "A", "Tokyo")


def test_candidate_key_invalid_identity_returns_none():
    for bad in (0, -1, 1.5, True, "", "abc"):
        assert _candidate_key({"shrine_id": bad, "name": "A", "address": "Tokyo"}) is None


def test_candidate_key_conflicting_identity_returns_none():
    assert _candidate_key({"shrine_id": 42, "id": 999, "name": "A", "address": "Tokyo"}) is None


def test_candidate_key_place_id_still_wins_over_broken_identity():
    """place_id 優先は未変更（F-6 スコープ）。"""
    assert _candidate_key({"place_id": "pid-1", "shrine_id": 0}) == ("place_id", "pid-1")
    assert _candidate_key({"place_id": "pid-1", "shrine_id": 42, "id": 999}) == ("place_id", "pid-1")


def test_dedupe_keeps_both_rows_when_identity_is_broken():
    """malformed identity の2行が name/address 経由で同一Shrine扱いされない。"""
    first = {"shrine_id": 42, "id": 999, "name": "A", "address": "Tokyo"}
    second = {"shrine_id": 0, "name": "A", "address": "Tokyo"}

    out = _dedupe_candidates([first, second])

    assert out == [first, second]


def test_dedupe_still_collapses_the_same_resolved_shrine():
    first = {"shrine_id": 42, "name": "A"}
    second = {"id": "42", "name": "B"}

    assert _dedupe_candidates([first, second]) == [first]


def test_dedupe_still_collapses_absent_identity_by_name_address():
    first = {"name": "A", "address": "Tokyo"}
    second = {"name": "A", "address": "Tokyo"}

    assert _dedupe_candidates([first, second]) == [first]


# ---------------------------------------------------------------------------
# NORMALIZATION_MUST_NOT_DOWNGRADE
#
# _normalize_candidate_fields() は candidate の presentation field を整える層で
# あり、Shrine identity の意味論を**再解釈してはならない**。正規化の前後で
# canonical identity status が一致しなければならない。
#
#   invalid  -> absent    PROHIBITED
#   invalid  -> resolved  PROHIBITED
#   conflict -> absent    PROHIBITED
#   conflict -> resolved  PROHIBITED
#
# docs/audit/backend-shrine-identity-fallback-consolidation.md §20
# ---------------------------------------------------------------------------

def _status(source):
    return resolve_shrine_identity(source, policy="live_candidate").status


@pytest.mark.parametrize(
    ("raw", "expected_status"),
    [
        ({"shrine_id": 42, "name": "A"}, "resolved"),
        ({"shrine_id": "42", "name": "A"}, "resolved"),
        ({"id": 42, "name": "A"}, "resolved"),
        ({"shrine_id": 1.0, "name": "A"}, "invalid"),
        ({"shrine_id": "1.0", "name": "A"}, "invalid"),
        ({"shrine_id": True, "name": "A"}, "invalid"),
        ({"shrine_id": "bad", "name": "A"}, "invalid"),
        ({"shrine_id": 42, "id": 999, "name": "A"}, "conflict"),
    ],
)
def test_normalize_candidate_fields_preserves_identity_status(raw, expected_status):
    before = _status(raw)
    assert before == expected_status, f"前提が誤り: {raw!r}"

    after = _status(_normalize_candidate_fields(raw))

    assert after == before, (
        f"{raw!r}: 正規化が identity status を {before} -> {after} へ downgrade した"
    )


@pytest.mark.parametrize(
    ("raw", "expected_status"),
    [
        ({"id": 1.0, "name": "A"}, "invalid"),
        ({"id": "1.0", "name": "A"}, "invalid"),
        ({"id": True, "name": "A"}, "invalid"),
        ({"id": "bad", "name": "A"}, "invalid"),
        ({"shrine_id": 0, "id": 777, "name": "A"}, "invalid"),
        ({"shrine_id": -1, "name": "A"}, "invalid"),
        ({"shrine_id": "-1", "name": "A"}, "invalid"),
        ({"shrine_id": None, "id": 42, "name": "A"}, "resolved"),
        ({"shrine_id": None, "name": "A"}, "absent"),
        ({"name": "A"}, "absent"),
        ({"shrine_id": "42", "id": 42, "name": "A"}, "resolved"),
    ],
)
def test_normalize_candidate_fields_preserves_identity_status_extended(raw, expected_status):
    before = _status(raw)
    assert before == expected_status, f"前提が誤り: {raw!r}"

    assert _status(_normalize_candidate_fields(raw)) == before


def test_normalize_candidate_fields_still_normalizes_valid_identity_to_int():
    out = _normalize_candidate_fields({"shrine_id": "42", "id": "42", "name": "A"})

    assert out["shrine_id"] == 42
    assert out["id"] == 42
    assert isinstance(out["shrine_id"], int)
    assert isinstance(out["id"], int)


def test_normalize_candidate_fields_keeps_identity_keys_present():
    """presence rule（key があり値が None でない）を壊さない。"""
    out = _normalize_candidate_fields({"name": "A"})

    assert "shrine_id" in out
    assert "id" in out
    assert out["shrine_id"] is None
    assert out["id"] is None


def test_normalize_candidate_fields_does_not_mutate_the_input():
    src = {"shrine_id": "bad", "name": "A"}

    _normalize_candidate_fields(src)

    assert src == {"shrine_id": "bad", "name": "A"}


def test_normalize_candidate_fields_does_not_change_place_id_behavior():
    """place_id の扱いは未変更（F-6 のスコープ）。"""
    assert _normalize_candidate_fields({"place_id": " pid-1 "})["place_id"] == "pid-1"
    assert _normalize_candidate_fields({"place_id": ""})["place_id"] is None
    assert _normalize_candidate_fields({"place_id": "pid-1", "shrine_id": "bad"})["place_id"] == "pid-1"


def test_normalize_candidate_fields_still_normalizes_non_identity_ints():
    """identity 以外の int 正規化は _to_int_or_none() のまま。"""
    out = _normalize_candidate_fields({"name": "A", "astro_priority": "3"})

    assert out["astro_priority"] == 3
