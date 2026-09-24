"""F-6B collision 検出の契約テスト。

    F6B_COLLISION_POLICY = CONSERVATIVE

    COLLISION_CANDIDATE =
      NORMALIZED_NAME_EXACT AND ( STRONG_ADDRESS_MATCH OR DISTANCE_M <= 500 )

    NAME_ONLY / BASE_NAME_ONLY / ADDRESS_ONLY / COORDINATE_ONLY = INSUFFICIENT

docs/audit/place-id-shadow-identity-hardening.md §14
"""
from __future__ import annotations

import pytest

from temples.models import Shrine
from temples.services.place_shrine_collision import (
    COLLISION_DISTANCE_M,
    find_place_shrine_collisions,
)

pytestmark = pytest.mark.django_db

# 給田六所神社（migration 0100 の監査済み座標）
LAT = 35.662443
LNG = 139.5920237
NAME = "給田六所神社"
ADDR = "日本、〒157-0064 東京都世田谷区給田１丁目３−７"


def _shrine(**kwargs):
    base = {"name_jp": NAME, "address": ADDR, "latitude": LAT, "longitude": LNG}
    base.update(kwargs)
    return Shrine.objects.create(**base)


def _find(**overrides):
    params = {"name": NAME, "address": ADDR, "latitude": LAT, "longitude": LNG}
    params.update(overrides)
    return find_place_shrine_collisions(**params)


class TestCollisionPositive:
    def test_exact_name_plus_exact_address_is_a_collision(self):
        s = _shrine()

        hits = _find()

        assert [h.shrine_id for h in hits] == [s.id]
        assert hits[0].matched_address is True

    def test_exact_name_plus_close_coordinate_is_a_collision(self):
        """住所が食い違っても 500m 以内なら collision。"""
        s = _shrine(address="まったく別の住所表記")

        hits = _find()

        assert [h.shrine_id for h in hits] == [s.id]
        assert hits[0].matched_address is False
        assert hits[0].matched_distance is True
        assert hits[0].distance_m is not None and hits[0].distance_m < 1.0

    def test_name_normalization_absorbs_whitespace_and_paren_width(self):
        s = _shrine(name_jp="給田六所神社（六所様）")

        hits = _find(name="給田六所神社(六所様)")

        assert [h.shrine_id for h in hits] == [s.id]

    def test_name_normalization_absorbs_ideographic_space_and_trim(self):
        s = _shrine(name_jp="  給田六所神社  ")

        assert [h.shrine_id for h in _find()] == [s.id]

    def test_address_normalization_absorbs_dash_and_space_variants(self):
        s = _shrine(
            address="日本、〒157-0064 東京都世田谷区給田１丁目３ー７",
            latitude=None,
            longitude=None,
        )

        hits = _find(latitude=None, longitude=None)

        assert [h.shrine_id for h in hits] == [s.id]
        assert hits[0].matched_address is True

    def test_multiple_candidates_are_all_returned(self):
        a = _shrine()
        b = _shrine(address="別表記でも近い")

        assert sorted(h.shrine_id for h in _find()) == sorted([a.id, b.id])

    def test_shrine_with_a_different_place_ref_is_still_a_collision(self):
        """別 place_id で既に登録済みでも、同じ実在神社なら collision。"""
        from temples.models import PlaceRef

        other = PlaceRef.objects.create(place_id="OTHER_PID", name=NAME, address=ADDR)
        s = _shrine(place_ref=other)

        assert [h.shrine_id for h in _find()] == [s.id]


class TestCollisionNegativeInsufficientSignals:
    def test_name_only_is_insufficient(self):
        """同名でも遠くて住所も違えば collision にしない。"""
        _shrine(address="北海道札幌市中央区1-1", latitude=43.06, longitude=141.35)

        assert _find() == []

    def test_base_name_only_is_insufficient(self):
        """base name key（括弧除去）だけの一致は採らない。"""
        _shrine(name_jp="給田六所神社(旧称)")

        assert _find(name="給田六所神社") == []

    def test_partial_name_is_insufficient(self):
        """部分一致（icontains 相当）は採らない。"""
        _shrine(name_jp="六所神社")

        assert _find(name="給田六所神社") == []
        assert _find(name="六所神社") != []  # 逆向きの完全一致は成立する

    def test_address_only_is_insufficient(self):
        _shrine(name_jp="まったく別の神社")

        assert _find() == []

    def test_coordinate_only_is_insufficient(self):
        _shrine(name_jp="まったく別の神社", address="別住所")

        assert _find() == []

    def test_distance_just_over_the_threshold_is_not_a_collision(self):
        """約 900m 北。名前は一致するが住所も一致しないので collision にしない。"""
        _shrine(address="別住所", latitude=LAT + 0.0081, longitude=LNG)

        assert _find() == []

    def test_distance_just_under_the_threshold_is_a_collision(self):
        """約 445m 北。"""
        s = _shrine(address="別住所", latitude=LAT + 0.0040, longitude=LNG)

        hits = _find()

        assert [h.shrine_id for h in hits] == [s.id]
        assert hits[0].distance_m is not None
        assert hits[0].distance_m <= COLLISION_DISTANCE_M

    def test_blank_place_name_never_collides(self):
        _shrine(name_jp="")

        assert _find(name="") == []
        assert _find(name=None) == []
        assert _find(name="   ") == []

    def test_blank_address_on_either_side_is_not_a_strong_address_match(self):
        _shrine(address="", latitude=None, longitude=None)

        assert _find(latitude=None, longitude=None) == []

    def test_missing_coordinates_disable_the_distance_signal(self):
        _shrine(address="別住所", latitude=None, longitude=None)

        assert _find() == []
        assert _find(latitude=None, longitude=None) == []

    def test_no_shrines_at_all(self):
        assert _find() == []


# ---------------------------------------------------------------------------
# F-6B 距離しきい値の境界回帰。
#
#   契約: DISTANCE_M <= 500 -> collision
#
# 「<=」であって「<」ではないこと、および 500 をわずかに超えたら collision に
# しないことを固定する。保守的 policy は一切緩めない（名前一致は常に必須条件）。
#
# docs/audit/place-id-shadow-identity-hardening.md §14.1
# ---------------------------------------------------------------------------


class TestCollisionDistanceBoundary:
    def test_threshold_constant_is_500_metres(self):
        assert COLLISION_DISTANCE_M == 500.0

    @staticmethod
    def _offset_deg(metres: float) -> float:
        """子午線に沿って `metres` だけ北へずらす緯度差[deg]。"""
        from math import degrees

        from temples.services.place_shrine_collision import _EARTH_RADIUS_M

        return degrees(metres / _EARTH_RADIUS_M)

    def test_just_inside_the_threshold_is_a_collision(self):
        """実測 499.99999999967525 m（500 m 狙い）。住所は一致させない。"""
        from temples.services.place_shrine_collision import _distance_m

        lat = LAT + self._offset_deg(500.0)
        s = _shrine(address="別住所", latitude=lat, longitude=LNG)

        measured = _distance_m(LAT, LNG, lat, LNG)
        assert measured <= COLLISION_DISTANCE_M
        assert COLLISION_DISTANCE_M - measured < 1e-6, measured

        hits = _find()

        assert [h.shrine_id for h in hits] == [s.id]
        assert hits[0].matched_distance is True
        assert hits[0].matched_address is False

    def test_just_outside_the_threshold_is_not_a_collision(self):
        """実測 501.00000000014387 m。"""
        from temples.services.place_shrine_collision import _distance_m

        lat = LAT + self._offset_deg(501.0)
        _shrine(address="別住所", latitude=lat, longitude=LNG)

        measured = _distance_m(LAT, LNG, lat, LNG)
        assert measured > COLLISION_DISTANCE_M

        assert _find() == []

    def test_one_metre_inside_the_threshold_is_a_collision(self):
        s = _shrine(address="別住所", latitude=LAT + self._offset_deg(499.0), longitude=LNG)

        assert [h.shrine_id for h in _find()] == [s.id]

    def test_comparison_is_inclusive_at_exactly_the_threshold(self, monkeypatch):
        """`<=` であって `<` ではないことを、距離関数を固定して直接確かめる。

        実座標では浮動小数の都合で「ちょうど 500.0」を作れないため、
        距離計算だけを差し替えて比較演算子そのものを検証する。
        policy は変更していない（名前一致は依然として必須条件）。
        """
        import temples.services.place_shrine_collision as mod

        s = _shrine(address="別住所", latitude=LAT + 1.0, longitude=LNG)

        monkeypatch.setattr(mod, "_distance_m", lambda *a, **k: 500.0)
        hits = _find()

        assert [h.shrine_id for h in hits] == [s.id]
        assert hits[0].distance_m == 500.0
        assert hits[0].matched_distance is True

    def test_comparison_excludes_anything_above_the_threshold(self, monkeypatch):
        import temples.services.place_shrine_collision as mod

        _shrine(address="別住所", latitude=LAT + 1.0, longitude=LNG)

        monkeypatch.setattr(mod, "_distance_m", lambda *a, **k: 500.0000001)

        assert _find() == []

    def test_distance_beyond_the_threshold_still_collides_on_a_strong_address_match(self):
        """距離が外れても住所が完全一致すれば collision（OR 条件）。"""
        s = _shrine(latitude=LAT + self._offset_deg(5000.0), longitude=LNG)

        hits = _find()

        assert [h.shrine_id for h in hits] == [s.id]
        assert hits[0].matched_address is True
        assert hits[0].matched_distance is False
