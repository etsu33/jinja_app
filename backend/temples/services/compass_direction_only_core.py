"""Compass Monthly Direction-only candidate core.

Direction-only Compass の候補集合を、次の入力だけから決める。

    origin
    + direction runtime（referenceDirections）
    + geographic distance
    + Shared Recommendation Eligibility

正本:
    docs/product/compass-product-contract.md（Section 0.1 / 3 / 3-A / 10 / 11）
    docs/product/compass-direction-only-candidate-universe-decision.md
    docs/product/compass-direction-only-ranking-weekly-theme-decision.md
    docs/knowledge/recommendation-eligibility-contract.md

Pipeline（順序が契約の本体）:

    STRUCTURAL_BASE（QA fixture除外 / 座標あり / address非空）
      -> lossless 60km coarse bounding box（DB側）
      -> exact distance_m <= 60000（Python側、既存 Haversine authority）
      -> Shared Recommendation Eligibility（共有層）
      -> Direction Sector Match（filter_candidates_by_direction）
      -> 15 / 30 / 60km distance stage（compass_distance_stage）
      -> ranking: distance_m ASC、完全一致時のみ shrine_id ASC

このmoduleは purpose / need_tag / goriyaku / 相談解釈 / Recommendation score /
popular_score / Knowledge量 / 角度差 を一切入力しない。候補 membership を
人気順や件数上限で先に切ることもしない（COMPASS_POPULARITY_PREFILTER /
COMPASS_PRE_GEOGRAPHIC_COUNT_LIMIT = PROHIBITED）。

Eligibility の判定式と Knowledge の usable 判定は共有層
（concierge_chat_candidates.partition_recommendation_eligible_shrines）に
委譲し、ここでは再実装しない。方位計算は filter_candidates_by_direction、
距離 stage は compass_distance_stage、距離計算は共有候補層の Haversine を使う。

旧 Monthly API（compass_recommendation_orchestrator.get_compass_recommendations）の
配線は変更しない。HTTP への接続（cutover）は別PRで行う。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from temples.models import Shrine
from temples.services.compass_direction_filter import filter_candidates_by_direction
from temples.services.compass_distance_stage import (
    DISTANCE_STAGE_3_KM,
    apply_compass_distance_stage,
)
from temples.services.compass_runtime import NoCommonDirectionResult
from temples.services.concierge_chat_candidates import (
    _distance_m,
    partition_recommendation_eligible_shrines,
)
from temples.services.direction_reference import _coordinate
from temples.services.shrine_qa_fixture_exclusion import exclude_qa_fixture_shrines

# State 名は旧 Monthly orchestrator と同じ文字列を使う（cutover 時に公開 state を
# 変えないため）。Direction-only Core には purpose も semantic Recommendation も
# 無いので、invalid_purpose / evidence_zero_candidates はここでは発生しない。
STATE_DIRECTION_FILTER_UNAVAILABLE = "direction_filter_unavailable"
STATE_NO_COMMON_DIRECTION = "no_common_direction"
STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES = "recommendation_eligibility_zero_candidates"
STATE_DIRECTION_ZERO_CANDIDATES = "direction_zero_candidates"
STATE_RECOMMENDATION_SUCCESS = "recommendation_success"

# COMPASS_MAX_CANDIDATE_RADIUS_KM = 60。distance stage の terminal ring と同じ値であり、
# 別の定数を持たない（二つの 60km がずれないようにする）。
MAX_CANDIDATE_RADIUS_M = DISTANCE_STAGE_3_KM * 1000

# 共有候補層の _distance_m() と同じ地球半径（球面 Haversine）。bounding box は
# この球面上での距離に対して lossless である必要がある。
_EARTH_RADIUS_M = 6371000.0

# bounding box の安全余裕。
# - _distance_m() は距離を int へ切り捨てるため、真の距離が radius + 1m 未満の
#   Shrine も distance_m <= radius と判定される。その分を +1m で含める。
# - 浮動小数点誤差に対して、角度へ 0.1% の余裕を掛ける。
# 余裕は「広げる」方向にしか働かない（余分に拾った Shrine は exact distance で落ちる）。
_BBOX_EXTRA_METERS = 1.0
_BBOX_SAFETY_FACTOR = 1.001


@dataclass(frozen=True)
class GeographicBoundingBox:
    """60km 判定の前に DB で使う粗い座標範囲。

    `min_lng` / `max_lng` が None の場合は経度で絞らない（極付近や日付変更線を
    またぐ場合。絞らないことは常に lossless である）。
    """

    min_lat: float
    max_lat: float
    min_lng: Optional[float]
    max_lng: Optional[float]


def lossless_bounding_box(*, lat: float, lng: float, radius_m: float) -> GeographicBoundingBox:
    """origin から球面距離 radius_m 以内の点を**必ず**含む緯度経度範囲を返す。

    球面上で origin (φ0, λ0) から角距離 d 以内の点は、

        |Δφ| <= d
        |Δλ| <= asin(sin d / cos φ0)      （球冠が極を含まない場合）

    を満たす（球冠の経度方向の最大幅。origin の緯度ではなく、やや極側で最大になる
    ことを含めた厳密な上界）。ここへ _BBOX_EXTRA_METERS と _BBOX_SAFETY_FACTOR の
    余裕を足すので、範囲外の点が 60km 以内になることはない。範囲内でも 60km を
    超える点（四隅など）は、呼び出し側の exact distance 判定で除外する。
    """
    angular = (radius_m + _BBOX_EXTRA_METERS) / _EARTH_RADIUS_M * _BBOX_SAFETY_FACTOR
    phi0 = math.radians(lat)

    min_lat = lat - math.degrees(angular)
    max_lat = lat + math.degrees(angular)

    # 球冠が極を含む（または極に接する）場合、経度は全周になり得る。
    if abs(phi0) + angular >= math.pi / 2:
        return GeographicBoundingBox(
            min_lat=max(min_lat, -90.0), max_lat=min(max_lat, 90.0), min_lng=None, max_lng=None
        )

    delta_lng = math.degrees(math.asin(min(1.0, math.sin(angular) / math.cos(phi0))))
    min_lng = lng - delta_lng
    max_lng = lng + delta_lng
    if min_lng < -180.0 or max_lng > 180.0:
        # 日付変更線をまたぐ範囲は分割せず、経度では絞らない（lossless を優先）。
        return GeographicBoundingBox(min_lat=min_lat, max_lat=max_lat, min_lng=None, max_lng=None)

    return GeographicBoundingBox(min_lat=min_lat, max_lat=max_lat, min_lng=min_lng, max_lng=max_lng)


@dataclass(frozen=True)
class CompassDirectionOnlyResult:
    """Direction-only Core の内部結果（HTTP schema ではない）。

    - `candidates`: 成功時のみ非空。ranking 済み（distance_m ASC、完全一致時 shrine_id ASC）。
    - `source_candidate_count`: STRUCTURAL_BASE ∩ exact distance <= 60km（= U60）の件数。
    - `eligible_candidate_count`: U60 のうち Shared Recommendation Eligibility 通過数。
    - `direction_candidate_count`: そのうち Direction Sector Match 通過数。
    - `distance_candidate_count`: distance stage で確定した ACTIVE_SET の件数。
    - `distance_stage_km`: ACTIVE_SET を決めた ring（15 / 30 / 60）。

    候補生成まで到達しない fail-safe state（direction_filter_unavailable /
    no_common_direction）では件数はすべて None。
    """

    state: str
    candidates: list[dict[str, Any]] = field(default_factory=list)
    direction_context: Optional[Mapping[str, Any]] = None
    source_candidate_count: Optional[int] = None
    eligible_candidate_count: Optional[int] = None
    direction_candidate_count: Optional[int] = None
    distance_candidate_count: Optional[int] = None
    distance_stage_km: Optional[int] = None


def _valid_origin(origin: Any) -> Optional[tuple[float, float]]:
    if not isinstance(origin, Mapping):
        return None
    lat = _coordinate(origin, "lat", "latitude")
    lng = _coordinate(origin, "lng", "longitude")
    if lat is None or lng is None:
        return None
    if not (math.isfinite(lat) and math.isfinite(lng)):
        return None
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        return None
    return lat, lng


def _structural_base_within_bounding_box(box: GeographicBoundingBox):
    """STRUCTURAL_BASE を coarse bounding box で DB 側に絞った queryset。

    membership 条件は構造条件だけ（QA fixture除外は既存 authority を使う）。
    人気順・件数上限・意味 signal による絞り込みはしない。並び順も付けない
    （並び順は ACTIVE_SET 確定後の ranking でだけ決める）。
    """
    qs = exclude_qa_fixture_shrines(Shrine.objects.all())
    qs = qs.filter(latitude__isnull=False, longitude__isnull=False).exclude(address="")
    qs = qs.filter(latitude__gte=box.min_lat, latitude__lte=box.max_lat)
    if box.min_lng is not None and box.max_lng is not None:
        qs = qs.filter(longitude__gte=box.min_lng, longitude__lte=box.max_lng)
    return qs


def load_structural_universe_within_60km(
    *, origin_lat: float, origin_lng: float
) -> list[tuple[Shrine, int]]:
    """U60 = STRUCTURAL_BASE ∩ exact distance_m <= 60000 を (Shrine, distance_m) で返す。

    順序は意味を持たない（shrine id 順で安定化するだけ）。
    """
    box = lossless_bounding_box(lat=origin_lat, lng=origin_lng, radius_m=MAX_CANDIDATE_RADIUS_M)
    universe: list[tuple[Shrine, int]] = []
    for shrine in _structural_base_within_bounding_box(box).order_by("id"):
        distance = _distance_m(origin_lat, origin_lng, shrine.latitude, shrine.longitude)
        if distance is None or distance > MAX_CANDIDATE_RADIUS_M:
            continue
        universe.append((shrine, distance))
    return universe


def _candidate_payload(eligible_shrine, distance_m: int) -> dict[str, Any]:
    """後段の Public Projection が使う最小限の事実・位置 field だけを持つ候補 dict。

    推薦理由（semantic reason）は生成しない。Knowledge Fact は事実表示のために
    運ぶだけで、ranking には使わない。
    """
    shrine = eligible_shrine.shrine
    return {
        "shrine_id": shrine.id,
        "id": shrine.id,
        "name": shrine.name_jp or shrine.name_romaji,
        "address": shrine.address,
        "latitude": shrine.latitude,
        "longitude": shrine.longitude,
        "distance_m": distance_m,
        "knowledge_deities": eligible_shrine.knowledge_deities,
        "knowledge_histories": eligible_shrine.knowledge_histories,
    }


def rank_active_set(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """DIRECTION_SET_RANKING_POLICY = DISTANCE_ASC / TIE_BREAK = SHRINE_ID_ASC.

    ACTIVE_SET 確定後にだけ呼ぶ。membership は変えない。
    """
    return sorted(candidates, key=lambda c: (c["distance_m"], c["shrine_id"]))


def get_compass_direction_only_candidates(
    *,
    origin: Optional[Mapping[str, Any]],
    direction_context: Optional[Mapping[str, Any]] | NoCommonDirectionResult,
) -> CompassDirectionOnlyResult:
    """Direction-only Compass の候補集合を返す（purpose を受け取らない）。

    state 判定順（docs/knowledge/recommendation-eligibility-contract.md）:

        no_common_direction            direction runtime が Group B（有効な方位なし）
        direction_filter_unavailable   origin / referenceDirections が不正（Group A）
        recommendation_eligibility_zero_candidates
                                       U60 に Shrine はあるが Eligibility を満たすものが0
        direction_zero_candidates      Eligibility 通過はあるが方位内に0 / U60 自体が0
        recommendation_success         1件以上

    Group A は DB を読む前に判定する（候補件数によって unavailable が変わらない）。
    """
    if isinstance(direction_context, NoCommonDirectionResult):
        return CompassDirectionOnlyResult(state=STATE_NO_COMMON_DIRECTION)

    if not isinstance(direction_context, Mapping):
        return CompassDirectionOnlyResult(state=STATE_DIRECTION_FILTER_UNAVAILABLE)

    reference_directions = direction_context.get("referenceDirections")
    valid_origin = _valid_origin(origin)
    # Direction Filter authority 自身に「実行可能か」を判定させる（None 契約）。
    # 方位ラベルの検証を Compass 側へ複製しない。
    direction_filter_available = (
        valid_origin is not None
        and filter_candidates_by_direction(
            [], origin=origin, reference_directions=reference_directions
        )
        is not None
    )
    if not direction_filter_available:
        return CompassDirectionOnlyResult(
            state=STATE_DIRECTION_FILTER_UNAVAILABLE,
            direction_context=direction_context,
        )

    origin_lat, origin_lng = valid_origin
    universe = load_structural_universe_within_60km(origin_lat=origin_lat, origin_lng=origin_lng)
    distance_by_shrine_id = {shrine.id: distance for shrine, distance in universe}

    eligibility = partition_recommendation_eligible_shrines(shrine for shrine, _ in universe)
    counts = dict(
        source_candidate_count=eligibility.source_count,
        eligible_candidate_count=eligibility.eligible_count,
    )

    if eligibility.source_count > 0 and eligibility.eligible_count == 0:
        return CompassDirectionOnlyResult(
            state=STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES,
            direction_context=direction_context,
            **counts,
        )

    eligible_candidates = [
        _candidate_payload(item, distance_by_shrine_id[item.shrine.id])
        for item in eligibility.eligible
    ]
    direction_candidates = filter_candidates_by_direction(
        eligible_candidates,
        origin=origin,
        reference_directions=reference_directions,
    )
    if direction_candidates is None:  # pragma: no cover - 上で実行可能性を確認済み
        return CompassDirectionOnlyResult(
            state=STATE_DIRECTION_FILTER_UNAVAILABLE,
            direction_context=direction_context,
            **counts,
        )

    if not direction_candidates:
        return CompassDirectionOnlyResult(
            state=STATE_DIRECTION_ZERO_CANDIDATES,
            direction_context=direction_context,
            direction_candidate_count=0,
            distance_candidate_count=0,
            distance_stage_km=None,
            **counts,
        )

    active_set, distance_stage_km = apply_compass_distance_stage(direction_candidates)
    if not active_set:  # pragma: no cover - U60 は 60km 以内なので空にならない
        return CompassDirectionOnlyResult(
            state=STATE_DIRECTION_ZERO_CANDIDATES,
            direction_context=direction_context,
            direction_candidate_count=len(direction_candidates),
            distance_candidate_count=0,
            distance_stage_km=distance_stage_km,
            **counts,
        )

    return CompassDirectionOnlyResult(
        state=STATE_RECOMMENDATION_SUCCESS,
        candidates=rank_active_set([dict(c) for c in active_set]),
        direction_context=direction_context,
        direction_candidate_count=len(direction_candidates),
        distance_candidate_count=len(active_set),
        distance_stage_km=distance_stage_km,
        **counts,
    )


__all__ = [
    "MAX_CANDIDATE_RADIUS_M",
    "STATE_DIRECTION_FILTER_UNAVAILABLE",
    "STATE_DIRECTION_ZERO_CANDIDATES",
    "STATE_NO_COMMON_DIRECTION",
    "STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES",
    "STATE_RECOMMENDATION_SUCCESS",
    "CompassDirectionOnlyResult",
    "GeographicBoundingBox",
    "get_compass_direction_only_candidates",
    "load_structural_universe_within_60km",
    "lossless_bounding_box",
    "rank_active_set",
]
