"""場所ごとの物差しで候補の範囲を決める（2026-11-23 えつこさん決定）。

決まり：docs/product/recommendation-signal-authority.md §9「Semantic Fit vs Distance」
N＝10（近い方から10社目までの距離が物差し）、倍率＝3（物差しの3倍まで残す）。
"""

import pytest

from temples.services.concierge_adaptive_radius import (
    ADAPTIVE_RADIUS_MULTIPLIER,
    ADAPTIVE_RADIUS_RANK,
    apply_adaptive_radius,
)
from temples.services.concierge_chat import build_chat_recommendations


def _c(i, distance_m, **extra):
    return {"shrine_id": i, "id": i, "name": f"社{i}", "distance_m": distance_m, **extra}


def test_decided_numbers():
    assert ADAPTIVE_RADIUS_RANK == 10
    assert ADAPTIVE_RADIUS_MULTIPLIER == 3.0


def test_far_candidates_are_removed_by_the_tenth_nearest_scale():
    # 近い10社は 1〜10km。物差しは10km、範囲は30km
    near = [_c(i, i * 1000) for i in range(1, 11)]
    middle = _c(20, 29_000)
    far = _c(30, 310_000)
    kept, info = apply_adaptive_radius(near + [middle, far])

    assert [c["shrine_id"] for c in kept] == list(range(1, 11)) + [20]
    assert info["applied"] is True
    assert info["scale_m"] == 10_000
    assert info["cutoff_m"] == 30_000
    assert info["candidates_before"] == 12
    assert info["candidates_after"] == 11


def test_rural_scale_keeps_far_candidates():
    # 地方：10社目が200km先なら、範囲は600kmで遠い神社も残る
    items = [_c(i, i * 20_000) for i in range(1, 11)] + [_c(99, 500_000)]
    kept, info = apply_adaptive_radius(items)
    assert len(kept) == 11
    assert info["cutoff_m"] == 600_000


def test_no_location_is_not_filtered():
    items = [_c(i, None) for i in range(1, 15)]
    kept, info = apply_adaptive_radius(items)
    assert kept == items
    assert info["applied"] is False
    assert info["reason"] == "no_location"


def test_too_few_candidates_with_distance_is_not_filtered():
    # 距離つきが9社しかないので物差しを作れない（900km先の候補も残る）
    items = [_c(i, i * 1000) for i in range(1, 9)] + [_c(50, 900_000), _c(51, None)]
    kept, info = apply_adaptive_radius(items)
    assert info["reason"] == "too_few_candidates_with_distance"
    assert kept == items


def test_candidates_without_distance_are_kept_when_filtering():
    items = [_c(i, i * 1000) for i in range(1, 11)] + [_c(77, None), _c(88, 400_000)]
    kept, _ = apply_adaptive_radius(items)
    ids = [c["shrine_id"] for c in kept]
    assert 77 in ids
    assert 88 not in ids


def test_order_is_kept():
    items = [_c(i, d) for i, d in [(3, 3000), (1, 1000), (2, 2000)]] + [
        _c(i, i * 1000) for i in range(4, 11)
    ]
    kept, _ = apply_adaptive_radius(items)
    assert [c["shrine_id"] for c in kept][:3] == [3, 1, 2]


@pytest.mark.parametrize("bad", [-1, "abc", float("nan")])
def test_invalid_distance_is_treated_as_unknown(bad):
    items = [_c(i, i * 1000) for i in range(1, 11)] + [_c(66, bad)]
    kept, info = apply_adaptive_radius(items)
    assert info["candidates_with_distance"] == 10
    assert 66 in [c["shrine_id"] for c in kept]


# --- build_chat_recommendations との結合 -------------------------------------


def _candidate(i, distance_m, goriyaku):
    return {
        "id": i,
        "shrine_id": i,
        "name": f"結合の社{i}",
        "address": "",
        "distance_m": distance_m,
        "lat": 35.0,
        "lng": 139.0,
        "popular_score": 0,
        "goriyaku": goriyaku,
    }


def _ids(recs):
    return [r["shrine_id"] for r in recs["recommendations"]]


@pytest.mark.django_db
def test_far_better_match_does_not_win_in_a_dense_area(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")
    near = [_candidate(i, 500 + i * 300, "家内安全") for i in range(1, 11)]
    far = _candidate(99, 310_000, "仕事運・出世")
    recs = build_chat_recommendations(query="転職したい", language="ja", candidates=near + [far])
    assert 99 not in _ids(recs)
    assert recs["_debug"]["adaptive_radius"]["applied"] is True


@pytest.mark.django_db
def test_without_location_the_far_candidate_can_still_win(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")
    near = [_candidate(i, None, "家内安全") for i in range(1, 11)]
    far = _candidate(99, None, "仕事運・出世")
    recs = build_chat_recommendations(query="転職したい", language="ja", candidates=near + [far])
    assert _ids(recs)[0] == 99
    assert recs["_debug"]["adaptive_radius"]["reason"] == "no_location"
