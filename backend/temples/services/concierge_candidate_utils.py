"""
candidate の正規化・識別・重複排除を担当するユーティリティ群。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from temples.domain.shrine_identity import resolve_shrine_identity


def _to_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            return float(s)
        except Exception:
            return None
    return None


def _to_str_or_none(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _to_int_or_none(v: Any) -> Optional[int]:
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        if v.is_integer():
            return int(v)
        return None
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            if "." in s:
                f = float(s)
                return int(f) if f.is_integer() else None
            return int(s)
        except Exception:
            return None
    return None


def _to_str_list(value: Any, *, dedupe: bool = True, limit: Optional[int] = None) -> List[str]:
    if not isinstance(value, list):
        return []

    out: List[str] = []
    seen = set()

    for x in value:
        if not isinstance(x, str):
            continue
        s = x.strip()
        if not s:
            continue

        if dedupe:
            if s in seen:
                continue
            seen.add(s)

        out.append(s)

        if limit is not None and len(out) >= limit:
            break

    return out


def _normalize_candidate_fields(c: Dict[str, Any]) -> Dict[str, Any]:
    """
    候補1件を後段処理しやすい形に正規化して返す。

    方針:
    - 入力 dict は破壊しない
    - 不正値はなるべく None / 空配列へ寄せる
    - 既存キーは可能な限り保持する
    """
    row = dict(c)

    lat = _to_float(row.get("lat"))
    lng = _to_float(row.get("lng"))
    distance_m = _to_float(row.get("distance_m"))

    if lat is not None:
        row["lat"] = lat
    if lng is not None:
        row["lng"] = lng
    if distance_m is not None:
        row["distance_m"] = distance_m


    row["name"] = _to_str_or_none(row.get("name"))
    row["place_id"] = _to_str_or_none(row.get("place_id"))
    row["address"] = _to_str_or_none(row.get("address"))
    row["formatted_address"] = _to_str_or_none(row.get("formatted_address"))
    row["goriyaku"] = _to_str_or_none(row.get("goriyaku"))
    row["description"] = _to_str_or_none(row.get("description"))
    row["reason"] = _to_str_or_none(row.get("reason"))
    row["location"] = _to_str_or_none(row.get("location"))

    row["id"] = _to_int_or_none(row.get("id"))
    row["shrine_id"] = _to_int_or_none(row.get("shrine_id"))

    row["lat"] = _to_float(row.get("lat"))
    row["lng"] = _to_float(row.get("lng"))
    row["distance_m"] = _to_float(row.get("distance_m"))
    row["popular_score"] = _to_float(row.get("popular_score")) or 0.0

    astro_priority = _to_int_or_none(row.get("astro_priority"))
    row["astro_priority"] = astro_priority if astro_priority is not None else 0

    row["astro_tags"] = _to_str_list(row.get("astro_tags"), dedupe=True)
    row["astro_elements"] = _to_str_list(row.get("astro_elements"), dedupe=True)
    row["highlights"] = _to_str_list(row.get("highlights"), dedupe=True, limit=3)

    return row


def _candidate_key(c: Dict[str, Any]) -> Optional[tuple]:
    """重複排除キーを返す。identity が壊れている場合は None（F-5B #6）。

    place_id 優先の既存挙動は **未変更**（place_id は F-6 のスコープ）。

    place_id が無い場合の Shrine identity は共有 resolver に委ねる:

        resolved           -> ("shrine_id", 正規化済みの正の int)
        absent             -> 既存の ("name_address", ...) fallback
        invalid / conflict -> None

    None は「このitemに重複排除キーを与えない」ことを意味する。
    malformed な identity を name/address の同一性に読み替えて、別Shrineの
    2行を同一と宣言してしまうのを防ぐ（fail closed）。
    """
    if c.get("place_id"):
        return ("place_id", str(c["place_id"]))

    identity = resolve_shrine_identity(c, policy="live_candidate")
    if identity.status == "resolved":
        return ("shrine_id", identity.shrine_id)
    if identity.status != "absent":
        return None

    name = str(c.get("name") or "").strip()
    address = str(c.get("address") or c.get("formatted_address") or "").strip()
    return ("name_address", name, address)


def _dedupe_candidates(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen = set()

    for c in items:
        if not isinstance(c, dict):
            continue
        key = _candidate_key(c)
        # key is None: identity が invalid / conflict。重複排除の対象にせず、
        # item は落とさずそのまま残す（F-5B #6）。
        if key is None:
            out.append(c)
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(c)

    return out


__all__ = [
    "_to_float",
    "_to_str_or_none",
    "_to_int_or_none",
    "_to_str_list",
    "_normalize_candidate_fields",
    "_candidate_key",
    "_dedupe_candidates",
]
