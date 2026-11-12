"""英語の相談の語と、推薦された神社の英語の特徴語との重なりを数える（記録用）。

- 神社側の語は temples/domain/shrine_features_en.py の定数（10社）。
- 本番の神社への結びつけは、神社の知識データと同じ resolve_shrine（正式名称＋住所）。
  結びつけられなかった神社は推測で埋めず、unresolved に名前を残す。
- 並び順には使わない。応答と ConciergeRecommendationLog に残すだけ。
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Tuple

from temples.domain.shrine_features_en import (
    SHRINE_FEATURES,
    SHRINE_FEATURES_VERSION,
    ShrineFeatureEntry,
)
from temples.services.knowledge_seed import resolve_shrine


def resolve_shrine_feature_index() -> Tuple[Dict[int, ShrineFeatureEntry], List[str]]:
    """定数の10社を本番の神社IDに結びつける。戻り値は（ID→定数、結びつけられなかった名前）。"""
    index: Dict[int, ShrineFeatureEntry] = {}
    unresolved: List[str] = []
    for entry in SHRINE_FEATURES:
        result = resolve_shrine(entry.name_jp, entry.address)
        if result.shrine is None:
            unresolved.append(entry.name_jp)
            continue
        index[int(result.shrine.pk)] = entry
    return index, unresolved


def _shrine_id_of(recommendation: Dict[str, Any]) -> int | None:
    raw = recommendation.get("shrine_id")
    if raw is None:
        raw = recommendation.get("id")
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def build_shrine_feature_matches(
    recommendations: Iterable[Any],
    request_feature_ids: Sequence[str],
) -> Dict[str, Any]:
    """推薦された神社ごとに、相談の語と神社の語の重なりを返す。

    covered=False は「神社側の語がまだ無い神社」（10社以外、または結びつけられなかった神社）。
    """
    index, unresolved = resolve_shrine_feature_index()
    wanted = list(request_feature_ids or [])

    matches: List[Dict[str, Any]] = []
    for recommendation in recommendations or []:
        if not isinstance(recommendation, dict):
            continue
        shrine_id = _shrine_id_of(recommendation)
        entry = index.get(shrine_id) if shrine_id is not None else None
        if entry is None:
            matches.append({"shrine_id": shrine_id, "covered": False})
            continue
        overlap = [feature_id for feature_id in wanted if feature_id in entry.feature_ids]
        matches.append(
            {
                "shrine_id": shrine_id,
                "name_jp": entry.name_jp,
                "covered": True,
                "shrine_feature_ids": list(entry.feature_ids),
                "overlap_ids": overlap,
                "overlap_count": len(overlap),
            }
        )

    return {
        "version": SHRINE_FEATURES_VERSION,
        "matches": matches,
        "unresolved": unresolved,
    }
