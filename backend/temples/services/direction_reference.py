from __future__ import annotations

import math
from typing import Any, Mapping, Optional, TypedDict


CALCULATION_METHOD = "annual_monthly_kyusei_v1"
DIRECTION_REFERENCE_NOTE = "年盤と月盤による参考情報です。日盤は使用していません。"
_DIRECTION_LABELS = ("北", "北東", "東", "南東", "南", "南西", "西", "北西")


class DirectionReference(TypedDict):
    visit_date: str
    actual_direction: str
    reference_directions: list[str]
    matched: bool
    calculation_method: str
    note: str


def _number(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _coordinate(source: Mapping[str, Any], primary: str, fallback: str) -> Optional[float]:
    value = source.get(primary)
    return _number(value if value is not None else source.get(fallback))


def _bearing(*, from_lat: float, from_lng: float, to_lat: float, to_lng: float) -> float:
    lat1 = math.radians(from_lat)
    lat2 = math.radians(to_lat)
    delta_lng = math.radians(to_lng - from_lng)
    y = math.sin(delta_lng) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lng)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def _direction_label(bearing: float) -> str:
    return _DIRECTION_LABELS[int((bearing + 22.5) // 45) % 8]


def build_direction_reference(
    *,
    direction_profile: Mapping[str, Any] | None,
    user_origin: Mapping[str, Any] | None,
    shrine: Mapping[str, Any] | None,
) -> Optional[DirectionReference]:
    """Build the optional, display-safe direction contract from grounded inputs only."""
    if not direction_profile or not user_origin or not shrine:
        return None
    if direction_profile.get("source") != "calculated":
        return None
    if direction_profile.get("calculationMethod") != CALCULATION_METHOD:
        return None

    visit_date = str(direction_profile.get("visitDate") or "").strip()
    reference_directions = [
        str(value).strip()
        for value in direction_profile.get("luckyDirections") or []
        if str(value).strip() in _DIRECTION_LABELS
    ]
    if not visit_date or not reference_directions:
        return None

    origin_lat = _coordinate(user_origin, "lat", "latitude")
    origin_lng = _coordinate(user_origin, "lng", "longitude")
    shrine_lat = _coordinate(shrine, "latitude", "lat")
    shrine_lng = _coordinate(shrine, "longitude", "lng")
    if None in (origin_lat, origin_lng, shrine_lat, shrine_lng):
        return None

    actual_direction = _direction_label(
        _bearing(
            from_lat=origin_lat,
            from_lng=origin_lng,
            to_lat=shrine_lat,
            to_lng=shrine_lng,
        )
    )
    return {
        "visit_date": visit_date,
        "actual_direction": actual_direction,
        "reference_directions": reference_directions,
        "matched": actual_direction in reference_directions,
        "calculation_method": CALCULATION_METHOD,
        "note": DIRECTION_REFERENCE_NOTE,
    }


def attach_direction_references(
    recommendations: list[Any],
    *,
    direction_profile: Mapping[str, Any] | None,
    user_origin: Mapping[str, Any] | None,
) -> None:
    for recommendation in recommendations:
        if not isinstance(recommendation, dict):
            continue
        reference = build_direction_reference(
            direction_profile=direction_profile,
            user_origin=user_origin,
            shrine=recommendation,
        )
        if reference is not None:
            recommendation["direction_reference"] = reference
        else:
            recommendation.pop("direction_reference", None)
