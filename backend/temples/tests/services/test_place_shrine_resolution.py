"""F-6B: get_or_create_shrine_by_place_id / resolve_shrine_by_place_id の契約。

F-6A §10.1 が設計した test matrix を実装する。F-6A 時点の被覆は
「0 dedicated unit tests / 3 indirect（ALREADY_LINKED 分岐のみ）」だった。

    ON_COLLISION:
      CREATE_NEW_SHRINE         = NO
      AUTO_BIND_EXISTING_SHRINE = NO
      RESULT                    = REVIEW_REQUIRED
      HTTP_STATUS               = 409

docs/audit/place-id-shadow-identity-hardening.md §14
"""
from __future__ import annotations

import threading

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from temples.models import PlaceRef, Shrine
from temples.services.places import (
    PlacesError,
    ShrineCollisionReviewRequired,
    get_or_create_shrine_by_place_id,
    resolve_shrine_by_place_id,
)

pytestmark = pytest.mark.django_db(transaction=True)

# migration 0100 の監査済み shadow / primary ペア（給田六所神社）
HISTORICAL_PLACE_ID = "ChIJl-MEepfxGGAR1Eo44p__GaE"
NAME = "給田六所神社"
ADDR = "日本、〒157-0064 東京都世田谷区給田１丁目３−７"
LAT = 35.662443
LNG = 139.5920237


def _place_ref(place_id, **kwargs):
    base = {"name": NAME, "address": ADDR, "latitude": LAT, "longitude": LNG}
    base.update(kwargs)
    return PlaceRef.objects.create(place_id=place_id, **base)


def _shrine(**kwargs):
    base = {"name_jp": NAME, "address": ADDR, "latitude": LAT, "longitude": LNG}
    base.update(kwargs)
    return Shrine.objects.create(**base)


class TestAlreadyLinked:
    def test_1_already_linked_place_ref_returns_the_same_shrine(self):
        pr = _place_ref("PID_LINKED")
        existing = _shrine(place_ref=pr)

        before = Shrine.objects.count()
        result = get_or_create_shrine_by_place_id("PID_LINKED")

        assert result.id == existing.id
        assert Shrine.objects.count() == before

    def test_1b_resolution_status_is_already_linked(self):
        pr = _place_ref("PID_LINKED2")
        existing = _shrine(place_ref=pr)

        resolution = resolve_shrine_by_place_id("PID_LINKED2")

        assert resolution.status == "already_linked"
        assert resolution.shrine.id == existing.id
        assert resolution.candidates == ()
        assert resolution.is_review_required is False

    def test_already_linked_wins_even_when_other_shrines_would_collide(self):
        """既にリンク済みなら collision 検出まで行かない。"""
        pr = _place_ref("PID_LINKED3")
        linked = _shrine(place_ref=pr)
        _shrine()  # 同名・同住所の別 Shrine

        assert get_or_create_shrine_by_place_id("PID_LINKED3").id == linked.id


class TestUnlinkedNoCollision:
    def test_2_genuinely_new_place_ref_creates_exactly_one_shrine(self):
        _place_ref("PID_NEW", name="新規神社", address="東京都新規区1-1")

        before = Shrine.objects.count()
        shrine = get_or_create_shrine_by_place_id("PID_NEW")

        assert Shrine.objects.count() == before + 1
        assert shrine.place_ref_id == "PID_NEW"
        assert shrine.name_jp == "新規神社"

    def test_3_repeated_resolve_does_not_create_a_second_shrine(self):
        _place_ref("PID_REPEAT", name="反復神社", address="東京都反復区1-1")

        first = get_or_create_shrine_by_place_id("PID_REPEAT")
        count_after_first = Shrine.objects.count()
        second = get_or_create_shrine_by_place_id("PID_REPEAT")

        assert second.id == first.id
        assert Shrine.objects.count() == count_after_first

    def test_unrelated_existing_shrine_does_not_block_creation(self):
        _shrine(name_jp="無関係神社", address="北海道札幌市1-1", latitude=43.06, longitude=141.35)
        _place_ref("PID_OK", name="別の新規神社", address="東京都新規区2-2")

        shrine = get_or_create_shrine_by_place_id("PID_OK")

        assert shrine.place_ref_id == "PID_OK"


class TestCollisionFailsClosed:
    def test_4_collision_candidate_creates_no_shrine(self):
        existing = _shrine()
        _place_ref("PID_COLLIDE")

        before = Shrine.objects.count()
        with pytest.raises(ShrineCollisionReviewRequired):
            get_or_create_shrine_by_place_id("PID_COLLIDE")

        assert Shrine.objects.count() == before
        existing.refresh_from_db()
        assert existing.place_ref_id is None

    def test_5_collision_candidate_is_not_automatically_selected(self):
        """AUTO_BIND_ON_SINGLE_CANDIDATE = PROHIBITED。

        候補が 1 件でも、その Shrine を返したり束縛したりしない。
        """
        existing = _shrine()
        _place_ref("PID_SINGLE")

        resolution = resolve_shrine_by_place_id("PID_SINGLE")

        assert resolution.status == "collision_review_required"
        assert resolution.shrine is None
        assert resolution.is_review_required is True
        assert [c.shrine_id for c in resolution.candidates] == [existing.id]
        existing.refresh_from_db()
        assert existing.place_ref_id is None

    def test_8_ambiguous_multiple_candidates_fail_closed(self):
        a = _shrine()
        b = _shrine(address="別表記だが近い")
        _place_ref("PID_AMBIGUOUS")

        before = Shrine.objects.count()
        resolution = resolve_shrine_by_place_id("PID_AMBIGUOUS")

        assert resolution.status == "collision_review_required"
        assert resolution.shrine is None
        assert sorted(c.shrine_id for c in resolution.candidates) == sorted([a.id, b.id])
        assert Shrine.objects.count() == before

    def test_collision_error_carries_409_and_a_stable_code(self):
        _shrine()
        _place_ref("PID_409")

        with pytest.raises(ShrineCollisionReviewRequired) as exc:
            get_or_create_shrine_by_place_id("PID_409")

        assert exc.value.status == 409
        assert exc.value.code == "shrine_collision_review_required"
        assert exc.value.place_id == "PID_409"
        assert isinstance(exc.value, PlacesError)

    def test_10_historical_place_ids_cannot_recreate_a_shadow_row(self):
        """migration 0100 の孤立 PlaceRef から shadow 行を作らない。

        F-6A §2.2 が「作れてしまう」と証明した経路をここで閉じる。
        """
        primary = _shrine()  # 0100 の primary Shrine 22 相当
        _place_ref(HISTORICAL_PLACE_ID)  # 0100 が孤立させた PlaceRef

        before = Shrine.objects.count()
        with pytest.raises(ShrineCollisionReviewRequired):
            get_or_create_shrine_by_place_id(HISTORICAL_PLACE_ID)

        assert Shrine.objects.count() == before
        primary.refresh_from_db()
        assert primary.place_ref_id is None


class TestGeometryContractPreserved:
    def test_9_missing_geometry_still_raises_502(self):
        _place_ref("PID_NOGEO", latitude=None, longitude=None)

        with pytest.raises(PlacesError) as exc:
            get_or_create_shrine_by_place_id("PID_NOGEO")

        assert exc.value.status == 502
        assert not isinstance(exc.value, ShrineCollisionReviewRequired)

    def test_geometry_check_runs_before_collision_detection(self):
        """座標が無い場合は既存の 502 を維持する（409 に変えない）。"""
        _shrine()
        _place_ref("PID_NOGEO2", latitude=None, longitude=None)

        with pytest.raises(PlacesError) as exc:
            get_or_create_shrine_by_place_id("PID_NOGEO2")

        assert exc.value.status == 502


class TestConcurrency:
    def test_11_concurrent_resolve_creates_one_shrine_and_both_callers_get_it(self):
        """F-6A §9: ロック前は 2 並行 resolve の敗者が 500 になっていた。

        実スレッド 2 本を同じ place_id へ同時に走らせる。select_for_update が
        効いていれば、片方が PlaceRef 行をロックしている間もう片方は待ち、
        ロック取得後は reverse O2O から勝者の Shrine を読む。
        """
        _place_ref("PID_RACE", name="競合神社", address="東京都競合区1-1")

        results: dict[str, int] = {}
        errors: dict[str, BaseException] = {}
        start = threading.Barrier(2, timeout=15)

        def worker(key: str) -> None:
            try:
                start.wait()
                results[key] = get_or_create_shrine_by_place_id("PID_RACE").id
            except BaseException as exc:  # noqa: BLE001 - 失敗内容ごと記録する
                errors[key] = exc
            finally:
                connection.close()

        threads = [threading.Thread(target=worker, args=(k,)) for k in ("a", "b")]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert errors == {}, errors
        assert Shrine.objects.filter(place_ref_id="PID_RACE").count() == 1
        assert results["a"] == results["b"]

    # NOTE: places.resolve_shrine_by_place_id() の IntegrityError 復帰分岐は
    # **防御的な実装であり、専用 test を持たない**。
    #
    # select_for_update() が PlaceRef 行を保持している間、別 connection から
    # 同じ place_ref_id で Shrine を INSERT しようとすると FK share lock が
    # 必要になり、こちらの FOR UPDATE と相互待機して deadlock する
    # （実際に試して `deadlock detected` を確認した）。つまりロックが効いて
    # いる限りこの分岐へは到達しない。ロックが失われた環境（将来の backend
    # 変更など）のための保険としてコードは残す。
    #
    # docs/audit/place-id-shadow-identity-hardening.md §14.4

    def test_place_ref_row_is_locked_before_the_reverse_o2o_read(self):
        """select_for_update が実際に発行されることを SQL で確認する。"""
        _place_ref("PID_LOCK", name="ロック神社", address="東京都ロック区1-1")

        with CaptureQueriesContext(connection) as ctx:
            get_or_create_shrine_by_place_id("PID_LOCK")

        sql = " ".join(q["sql"].upper() for q in ctx.captured_queries)
        assert "FOR UPDATE" in sql
