"""migration 0100 の 3 ペア全件に対する shadow 再発回帰（F-6B）。

F-6A §2.2 は「孤立 PlaceRef から同じ place_id を resolve すると shadow Shrine を
再作成できる」ことをコードから証明した。ここではその 3 ペア **すべて** について
経路が閉じていることを固定する。

    給田六所神社  ChIJl-MEepfxGGAR1Eo44p__GaE  -> primary Shrine 22
    長太稲荷神社  ChIJX19mq8nxGGARsA2kP4gX90M  -> primary Shrine 21
    富岡八幡宮    ChIJK11I4BGJGGAR5mZswigcu58  -> primary Shrine 49

座標・名称・住所は migration 0100 の静的監査 snapshot（`PAIRS`）から採った。

本 test は PlaceRef を backfill しない。migration 0100 も変更しない。

docs/audit/place-id-shadow-identity-hardening.md §14.3
"""
from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from temples.models import PlaceRef, Shrine
from temples.services.places import (
    SHRINE_COLLISION_PUBLIC_CODE,
    ShrineCollisionReviewRequired,
    get_or_create_shrine_by_place_id,
    resolve_shrine_by_place_id,
)

pytestmark = pytest.mark.django_db

# migration 0100 `PAIRS` の静的 snapshot（shadow 側の place_ref_id / 座標と、
# primary 側の name_jp / address）。
HISTORICAL_PAIRS = [
    pytest.param(
        "ChIJl-MEepfxGGAR1Eo44p__GaE",
        "給田六所神社",
        "日本、〒157-0064 東京都世田谷区給田１丁目３−７",
        "給田六所神社",
        "日本、〒157-0064 東京都世田谷区給田１丁目３−７",
        35.662443,
        139.5920237,
        id="kyuden-rokusho-22",
    ),
    pytest.param(
        "ChIJX19mq8nxGGARsA2kP4gX90M",
        "長太稲荷神社",
        "日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０",
        "長太稲荷神社",
        "日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０",
        35.660614,
        139.6017688,
        id="chota-inari-21",
    ),
    pytest.param(
        # primary 49 は address 表記が shadow と異なる（0100 snapshot のとおり）。
        # STRONG_ADDRESS_MATCH は成立しないが DISTANCE_M <= 500 で collision になる。
        "ChIJK11I4BGJGGAR5mZswigcu58",
        "富岡八幡宮",
        "日本、〒135-0047 東京都江東区富岡１丁目２０−３",
        "富岡八幡宮",
        "東京都江東区富岡1-20-3",
        35.6717809,
        139.799519,
        id="tomioka-hachiman-49",
    ),
]


def _seed(place_id, pr_name, pr_address, primary_name, primary_address, lat, lng):
    """0100 forward 後の状態を再現する。

    - primary Shrine は存在し、place_ref は NULL
    - PlaceRef は存在し、どの Shrine からも参照されていない（孤立）
    """
    primary = Shrine.objects.create(
        name_jp=primary_name, address=primary_address, latitude=lat, longitude=lng
    )
    place_ref = PlaceRef.objects.create(
        place_id=place_id, name=pr_name, address=pr_address, latitude=lat, longitude=lng
    )
    assert primary.place_ref_id is None
    assert not Shrine.objects.filter(place_ref_id=place_id).exists()
    return primary, place_ref


def _assert_state_unchanged(primary, place_id, shrine_count_before):
    primary.refresh_from_db()
    # primary は一切変更されない
    assert primary.place_ref_id is None
    # 孤立 PlaceRef は未束縛のまま
    assert not Shrine.objects.filter(place_ref_id=place_id).exists()
    assert PlaceRef.objects.filter(pk=place_id).exists()
    # 新しい Shrine は作られない
    assert Shrine.objects.count() == shrine_count_before


@pytest.mark.parametrize(
    ("place_id", "pr_name", "pr_address", "primary_name", "primary_address", "lat", "lng"),
    HISTORICAL_PAIRS,
)
class TestHistoricalShadowCannotBeRecreated:
    def test_service_returns_collision_review_required(
        self, place_id, pr_name, pr_address, primary_name, primary_address, lat, lng
    ):
        primary, _ = _seed(place_id, pr_name, pr_address, primary_name, primary_address, lat, lng)
        before = Shrine.objects.count()

        resolution = resolve_shrine_by_place_id(place_id)

        assert resolution.status == "collision_review_required"
        assert resolution.shrine is None
        assert resolution.is_review_required is True
        assert [c.shrine_id for c in resolution.candidates] == [primary.id]
        _assert_state_unchanged(primary, place_id, before)

    def test_wrapper_raises_409_without_creating_a_shadow(
        self, place_id, pr_name, pr_address, primary_name, primary_address, lat, lng
    ):
        primary, _ = _seed(place_id, pr_name, pr_address, primary_name, primary_address, lat, lng)
        before = Shrine.objects.count()

        with pytest.raises(ShrineCollisionReviewRequired) as exc:
            get_or_create_shrine_by_place_id(place_id)

        assert exc.value.status == 409
        assert exc.value.place_id == place_id
        _assert_state_unchanged(primary, place_id, before)

    def test_places_resolve_endpoint_returns_409(
        self, place_id, pr_name, pr_address, primary_name, primary_address, lat, lng
    ):
        primary, _ = _seed(place_id, pr_name, pr_address, primary_name, primary_address, lat, lng)
        before = Shrine.objects.count()

        res = APIClient().post("/api/places/resolve/", {"place_id": place_id}, format="json")

        assert res.status_code == 409
        assert res.json()["code"] == SHRINE_COLLISION_PUBLIC_CODE
        _assert_state_unchanged(primary, place_id, before)

    def test_shrines_ingest_endpoint_returns_409(
        self, place_id, pr_name, pr_address, primary_name, primary_address, lat, lng
    ):
        primary, _ = _seed(place_id, pr_name, pr_address, primary_name, primary_address, lat, lng)
        before = Shrine.objects.count()

        res = APIClient().post("/api/shrines/ingest/", {"place_id": place_id}, format="json")

        assert res.status_code == 409
        assert res.json()["code"] == SHRINE_COLLISION_PUBLIC_CODE
        _assert_state_unchanged(primary, place_id, before)

    def test_409_body_never_leaks_the_primary_shrine_id(
        self, place_id, pr_name, pr_address, primary_name, primary_address, lat, lng
    ):
        primary, _ = _seed(place_id, pr_name, pr_address, primary_name, primary_address, lat, lng)

        for path in ("/api/places/resolve/", "/api/shrines/ingest/"):
            res = APIClient().post(path, {"place_id": place_id}, format="json")
            body = res.json()
            assert set(body) == {"detail", "code"}, path
            assert str(primary.id) not in str(body), path
