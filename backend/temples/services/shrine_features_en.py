"""travel モードの相談の語と、推薦された神社の英語の特徴語との重なりを数える（記録用）。

- 神社側の語は ShrineFeatureWordEn（import_feature_words_en で取り込んだもの）から読む。
  神社の結びつけは取り込みのときに済んでいるので、ここでは神社IDで1回だけ問い合わせる。
- 並び順には使わない。応答と ConciergeRecommendationLog に残すだけ。
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence

from temples.models import ShrineFeatureWordEn


def _shrine_id_of(recommendation: Dict[str, Any]) -> int | None:
    raw = recommendation.get("shrine_id")
    if raw is None:
        raw = recommendation.get("id")
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _load_feature_ids(shrine_ids: List[int]) -> tuple[Dict[int, List[str]], str]:
    """神社IDごとの語ID（重複なし・取り込んだ順）と、語彙のバージョンを返す。"""
    by_shrine: Dict[int, List[str]] = {}
    versions = set()
    rows = (
        ShrineFeatureWordEn.objects.filter(shrine_id__in=shrine_ids)
        .order_by("shrine_id", "id")
        .values_list("shrine_id", "word_id", "vocabulary_version")
    )
    for shrine_id, word_id, version in rows:
        ids = by_shrine.setdefault(shrine_id, [])
        if word_id not in ids:
            ids.append(word_id)
        versions.add(version)
    return by_shrine, ",".join(sorted(versions))


def build_shrine_feature_matches(
    recommendations: Iterable[Any],
    request_feature_ids: Sequence[str],
) -> Dict[str, Any]:
    """推薦された神社ごとに、相談の語と神社の語の重なりを返す。

    covered=False は「神社側の語がまだ無い神社」（取り込んだ10社以外）。
    """
    items = [r for r in (recommendations or []) if isinstance(r, dict)]
    shrine_ids = [sid for sid in (_shrine_id_of(r) for r in items) if sid is not None]
    by_shrine, version = _load_feature_ids(shrine_ids) if shrine_ids else ({}, "")
    wanted = list(request_feature_ids or [])

    matches: List[Dict[str, Any]] = []
    for recommendation in items:
        shrine_id = _shrine_id_of(recommendation)
        shrine_feature_ids = by_shrine.get(shrine_id) if shrine_id is not None else None
        if not shrine_feature_ids:
            matches.append({"shrine_id": shrine_id, "covered": False})
            continue
        overlap = [feature_id for feature_id in wanted if feature_id in shrine_feature_ids]
        matches.append(
            {
                "shrine_id": shrine_id,
                "covered": True,
                "shrine_feature_ids": shrine_feature_ids,
                "overlap_ids": overlap,
                "overlap_count": len(overlap),
            }
        )

    return {"version": version, "matches": matches}
