"""place_id -> Shrine 作成前の collision 検出（F-6B）。

    SHRINE_IDENTITY_AUTHORITY   = Shrine.id
    PLACE_ID_IDENTITY_AUTHORITY = NO
    F6B_COLLISION_POLICY        = CONSERVATIVE

契約記録:
    docs/audit/place-id-shadow-identity-hardening.md  (F-6A / F-6B)
    docs/audit/shrine-identity-compass-concierge-contract.md §5

**COLLISION_DETECTION != IDENTITY_RESOLUTION**

本 module は「この Place は既に登録済みの Shrine かもしれない」という
**シグナル**だけを返す。canonical Shrine identity を選ばない。返り値は
候補の list であり、要素が 1 件であってもそれを identity として採用しては
ならない（AUTO_BIND_ON_SINGLE_CANDIDATE = PROHIBITED）。

判定式（F-6B で固定）:

    COLLISION_CANDIDATE =
      NORMALIZED_NAME_EXACT
      AND ( STRONG_ADDRESS_MATCH OR DISTANCE_M <= 500 )

    NORMALIZED_NAME_EXACT =
      normalize_shrine_name_for_duplicate(PlaceRef.name)
      == normalize_shrine_name_for_duplicate(Shrine.name_jp)

    STRONG_ADDRESS_MATCH =
      両方の address が非空 AND
      normalize_shrine_address_for_duplicate(PlaceRef.address)
      == normalize_shrine_address_for_duplicate(Shrine.address)

単独では不十分（INSUFFICIENT）なもの:

    NAME_ONLY / BASE_NAME_ONLY / ADDRESS_ONLY / COORDINATE_ONLY

とくに base name key（`shrine_name_duplicate_base_key`）は **使わない**。
「稲荷神社」のような base key は全国の別神社に一致してしまう。
"""
from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import Any, Optional

from django.db.models import Value
from django.db.models.functions import Replace
from temples.models import Shrine
from temples.services.shrine_duplicate_normalize import (
    normalize_shrine_address_for_duplicate,
    normalize_shrine_name_for_duplicate,
)

__all__ = [
    "COLLISION_DISTANCE_M",
    "PlaceShrineCollision",
    "find_place_shrine_collisions",
]

#: F-6B で固定した近接しきい値[m]。これ単独では collision を成立させない
#: （必ず NORMALIZED_NAME_EXACT との AND）。
COLLISION_DISTANCE_M = 500.0

_EARTH_RADIUS_M = 6371000.0

#: SQL 側の粗い絞り込みで落とす空白類。
_STRIPPED_SPACES = ("　", " ", "\t", "\n", "\r")


@dataclass(frozen=True)
class PlaceShrineCollision:
    """「この Place かもしれない」登録済み Shrine 1 件。

    identity ではない。レビュー用のシグナルである。
    """

    shrine_id: int
    name_jp: str
    address: str
    distance_m: Optional[float]
    matched_address: bool
    matched_distance: bool


def _strip_for_lookup(value: Any) -> str:
    """SQL 側の粗い絞り込みと同じ変換（空白全除去 + 全角括弧を半角へ）。

    `normalize_shrine_name_for_duplicate` で等しい 2 つの文字列は、この変換でも
    必ず等しい（normalize は空白を潰すだけで、本変換はさらに全除去するため）。
    したがってこの条件は **superset** であり、絞り込みに使っても
    NORMALIZED_NAME_EXACT の判定を緩めない。最終判定は Python 側で行う。
    """
    s = str(value or "")
    for space in _STRIPPED_SPACES:
        s = s.replace(space, "")
    return s.replace("（", "(").replace("）", ")")


def _distance_m(
    lat1: Optional[float],
    lng1: Optional[float],
    lat2: Optional[float],
    lng2: Optional[float],
) -> Optional[float]:
    """2 点間の距離[m]。いずれかの座標が欠けていれば None。

    repository には既に複数の haversine 実装が散在しているが
    （places.py / queries.py / route_service.py など）、本 module を
    低レベル leaf に保ち circular import を避けるためここに置く。
    距離は identity ではないので、この重複は identity 実装の重複には当たらない。
    """
    if lat1 is None or lng1 is None or lat2 is None or lng2 is None:
        return None
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    h = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    )
    return 2 * _EARTH_RADIUS_M * asin(min(1.0, sqrt(h)))


def _name_lookup_expression():
    """`Shrine.name_jp` に `_strip_for_lookup` と同じ変換をかける式。"""
    expression: Any = "name_jp"
    for space in _STRIPPED_SPACES:
        expression = Replace(expression, Value(space), Value(""))
    expression = Replace(expression, Value("（"), Value("("))
    return Replace(expression, Value("）"), Value(")"))


def find_place_shrine_collisions(
    *,
    name: Optional[str],
    address: Optional[str],
    latitude: Optional[float],
    longitude: Optional[float],
) -> list[PlaceShrineCollision]:
    """この Place を表しうる登録済み Shrine を返す（identity ではない）。

    名前が空、あるいは正規化後に空になる場合は NORMALIZED_NAME_EXACT が
    成立しえないため、必ず空 list を返す（名前以外だけで collision を
    立てない = NAME は必須条件）。
    """
    normalized_name = normalize_shrine_name_for_duplicate(name or "")
    if not normalized_name:
        return []

    normalized_address = normalize_shrine_address_for_duplicate(address or "")

    # SQL 側は superset で粗く絞るだけ。確定判定は下の Python 側で行う。
    rows = (
        Shrine.objects.annotate(_collision_name_key=_name_lookup_expression())
        .filter(_collision_name_key=_strip_for_lookup(name))
        .only("id", "name_jp", "address", "latitude", "longitude")
        .order_by("id")
    )

    collisions: list[PlaceShrineCollision] = []
    for shrine in rows:
        # NORMALIZED_NAME_EXACT（必須条件）
        if normalize_shrine_name_for_duplicate(shrine.name_jp or "") != normalized_name:
            continue

        # STRONG_ADDRESS_MATCH — 両方が非空で、正規化後に完全一致すること。
        shrine_address = normalize_shrine_address_for_duplicate(shrine.address or "")
        matched_address = bool(
            normalized_address and shrine_address and normalized_address == shrine_address
        )

        # DISTANCE_M <= 500
        distance = _distance_m(latitude, longitude, shrine.latitude, shrine.longitude)
        matched_distance = distance is not None and distance <= COLLISION_DISTANCE_M

        if not (matched_address or matched_distance):
            # NAME_ONLY は INSUFFICIENT。
            continue

        collisions.append(
            PlaceShrineCollision(
                shrine_id=shrine.id,
                name_jp=shrine.name_jp or "",
                address=shrine.address or "",
                distance_m=distance,
                matched_address=matched_address,
                matched_distance=matched_distance,
            )
        )

    return collisions
