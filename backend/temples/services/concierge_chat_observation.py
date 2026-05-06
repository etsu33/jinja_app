from __future__ import annotations

import logging
from typing import Any


log = logging.getLogger(__name__)


def _recommendation_identity(rec: dict[str, Any], *, rank: int) -> dict[str, Any]:
    return {
        "rank": rank,
        "id": rec.get("id"),
        "shrine_id": rec.get("shrine_id"),
        "place_id": rec.get("place_id"),
        "name": rec.get("name"),
        "display_name": rec.get("display_name"),
    }


def _recommendation_key(row: dict[str, Any]) -> str:
    for key in ("shrine_id", "place_id", "id", "name"):
        value = row.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    return f"rank:{row.get('rank')}"


def observe_trim_before(recs: dict[str, Any]) -> list[dict[str, Any]]:
    recommendations = [
        r
        for r in (recs.get("recommendations") or [])
        if isinstance(r, dict)
    ]
    return [
        _recommendation_identity(rec, rank=idx)
        for idx, rec in enumerate(recommendations, start=1)
    ]


def observe_trim_after(recs: dict[str, Any]) -> list[dict[str, Any]]:
    recommendations = [
        r
        for r in (recs.get("recommendations") or [])
        if isinstance(r, dict)
    ]
    return [
        _recommendation_identity(rec, rank=idx)
        for idx, rec in enumerate(recommendations, start=1)
    ]


def build_trim_observation(
    *,
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
) -> dict[str, Any]:
    after_keys = {_recommendation_key(row) for row in after}
    dropped = [
        row
        for row in before
        if _recommendation_key(row) not in after_keys
    ]

    return {
        "before_count": len(before),
        "after_count": len(after),
        "dropped_count": len(dropped),
        "before": before,
        "after": after,
        "dropped": dropped,
    }


def observe_candidate_pool(
    *,
    valid_candidates: list[dict[str, Any]],
    visit_style_tags: set[str],
    need_tags: list[str],
) -> None:
    try:
        visit_style_hit_count = sum(
            1
            for c in valid_candidates
            if set(c.get("visit_style_tags") or []) & set(visit_style_tags)
        )
        need_hit_count = sum(
            1
            for c in valid_candidates
            if set(c.get("matched_need_tags") or []) & set(need_tags)
        )
        pool_detail = [
            (
                c.get("shrine_id") or c.get("id"),
                c.get("visit_style_tags") or [],
                sorted(set(c.get("visit_style_tags") or []) & set(visit_style_tags)),
            )
            for c in valid_candidates
        ]

        log.debug(
            "[pool] size=%d visit_style_hits=%d need_hits=%d",
            len(valid_candidates),
            visit_style_hit_count,
            need_hit_count,
        )
        log.debug(
            "[pool_detail] %s",
            pool_detail,
        )
    except Exception:
        log.exception("[pool] observation failed")


def observe_visit_style_before_trim(
    *,
    recs: dict[str, Any],
    query: str,
    extra_condition: Any,
    visit_style_tags: set[str],
) -> dict[str, Any]:
    try:
        pool = [
            r
            for r in (recs.get("recommendations") or [])
            if isinstance(r, dict)
        ]
        visit_style_pool_rows = []
        for idx, r in enumerate(pool, start=1):
            features = (r.get("breakdown_detail") or {}).get("features") or {}
            visit_style = features.get("visit_style") or {}
            visit_style_pool_rows.append(
                {
                    "rank": idx,
                    "shrine_id": r.get("shrine_id"),
                    "name": r.get("name"),
                    "visit_style_tags": r.get("visit_style_tags") or [],
                    "matched_tags": visit_style.get("matched_tags") or [],
                    "contribution": float(visit_style.get("contribution") or 0.0),
                    "score_total_ranked": float(features.get("score_total_ranked") or 0.0),
                    "score_need": (r.get("breakdown") or {}).get("score_need"),
                    "matched_need_tags": (r.get("breakdown") or {}).get("matched_need_tags") or [],
                }
            )

        hit_count = sum(1 for row in visit_style_pool_rows if row["contribution"] > 0)
        matched_tag_counts: dict[str, int] = {}
        for row in visit_style_pool_rows:
            for tag in row["matched_tags"]:
                tag_key = str(tag)
                matched_tag_counts[tag_key] = matched_tag_counts.get(tag_key, 0) + 1

        result = {
            "pool_size": len(visit_style_pool_rows),
            "hit_count": hit_count,
            "matched_tag_counts": matched_tag_counts,
            "rows": visit_style_pool_rows,
        }

        log.info(
            "[visit_style_observation_before_trim] has_query=%s query_len=%d has_extra=%s user_visit_style_tags=%r pool_size=%d hit_count=%d matched_tag_counts=%r rows=%r",
            bool(query),
            len(query or ""),
            bool(str(extra_condition or "").strip()),
            sorted(visit_style_tags),
            result["pool_size"],
            result["hit_count"],
            result["matched_tag_counts"],
            result["rows"],
        )

        return result
    except Exception:
        log.exception("[visit_style_observation_before_trim] failed")
        return {
            "pool_size": 0,
            "hit_count": 0,
            "matched_tag_counts": {},
            "rows": [],
        }
