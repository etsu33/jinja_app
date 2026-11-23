"""場所ごとの物差しで、コンシェルジュの候補の範囲を決める（2026-11-23 えつこさん決定）。

決まりの正本：docs/product/recommendation-signal-authority.md §9「Semantic Fit vs Distance」
試算：ドライブ KAMIMUSUBI「KAMI MUSUBI 場所ごとの物差しの試算（2026-11-23）」

- 物差し：相談した人の位置から近い方に ADAPTIVE_RADIUS_RANK 社目の神社までの距離
- 候補に残す範囲：物差しの ADAPTIVE_RADIUS_MULTIPLIER 倍以内。外の神社は候補から外す
- 決まったkmにしないのは、神社の数が地域で大きく違うため（地方で候補が無くならないように）
- 位置が無い相談（候補に distance_m が無い）や、位置の付いた候補が N 社に満たないときは絞らない
- distance_m が無い候補は外さない
- 点数（近さの点の式を含む）は変えない。候補の範囲だけを決める
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

ADAPTIVE_RADIUS_RANK = 10
ADAPTIVE_RADIUS_MULTIPLIER = 3.0


def _distance_of(candidate: Dict[str, Any]) -> Optional[float]:
    raw = candidate.get("distance_m")
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value != value or value < 0:  # NaN または負の値
        return None
    return value


def apply_adaptive_radius(
    candidates: Iterable[Dict[str, Any]],
    *,
    rank: int = ADAPTIVE_RADIUS_RANK,
    multiplier: float = ADAPTIVE_RADIUS_MULTIPLIER,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """候補を範囲で絞る。戻り値は（残った候補, 記録用の情報）。並び順は変えない。"""
    items = list(candidates or [])
    distances = sorted(d for d in (_distance_of(c) for c in items) if d is not None)

    info: Dict[str, Any] = {
        "applied": False,
        "rank": rank,
        "multiplier": multiplier,
        "candidates_with_distance": len(distances),
        "candidates_before": len(items),
    }

    if len(distances) < rank:
        info["reason"] = "no_location" if not distances else "too_few_candidates_with_distance"
        info["candidates_after"] = len(items)
        return items, info

    scale_m = distances[rank - 1]
    if scale_m <= 0:
        info["reason"] = "zero_scale"
        info["candidates_after"] = len(items)
        return items, info

    cutoff_m = scale_m * multiplier
    kept = [c for c in items if (_distance_of(c) is None or _distance_of(c) <= cutoff_m)]

    info.update(
        {
            "applied": True,
            "reason": "applied",
            "scale_m": round(scale_m),
            "cutoff_m": round(cutoff_m),
            "candidates_after": len(kept),
        }
    )
    return kept, info
