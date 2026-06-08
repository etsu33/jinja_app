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


def observe_candidate_pool_debug(
    *,
    valid_candidates: list[dict[str, Any]],
    filter_context: dict[str, Any] | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    try:
        candidates = [
            c
            for c in (valid_candidates or [])
            if isinstance(c, dict)
        ]

        with_place_id = sum(1 for c in candidates if c.get("place_id"))
        missing_latlng = sum(
            1
            for c in candidates
            if c.get("lat") is None or c.get("lng") is None
        )
        distance_none = sum(1 for c in candidates if c.get("distance_m") is None)

        score_top10 = [
            {
                "rank": idx,
                "shrine_id": c.get("shrine_id") or c.get("id"),
                "place_id": c.get("place_id"),
                "name": c.get("name"),
                "distance_m": c.get("distance_m"),
                "popular_score": c.get("popular_score"),
                "score_total": c.get("_score_total"),
                "visit_style_tags": c.get("visit_style_tags") or [],
                "goriyaku_tag_ids": c.get("goriyaku_tag_ids") or [],
            }
            for idx, c in enumerate(candidates[:limit], start=1)
        ]

        return {
            "valid_candidate_count": len(candidates),
            "with_place_id": with_place_id,
            "missing_latlng": missing_latlng,
            "distance_none": distance_none,
            "score_top10": score_top10,
            "filter_context": filter_context or {},
        }
    except Exception:
        log.exception("[candidate_pool_debug] observation failed")
        return {
            "valid_candidate_count": 0,
            "with_place_id": 0,
            "missing_latlng": 0,
            "distance_none": 0,
            "score_top10": [],
            "filter_context": filter_context or {},
        }


def observe_ranking_breakdown(
    *,
    recs: dict[str, Any],
    limit: int = 10,
) -> dict[str, Any]:
    try:
        recommendations = [
            r
            for r in (recs.get("recommendations") or [])
            if isinstance(r, dict)
        ]

        rows = []
        for idx, rec in enumerate(recommendations[:limit], start=1):
            breakdown = rec.get("breakdown") or {}
            features = (rec.get("breakdown_detail") or {}).get("features") or {}
            need = features.get("need") or {}
            popular = features.get("popular") or {}
            distance = features.get("distance") or {}
            visit_style = features.get("visit_style") or {}
            element = features.get("element") or {}
            behavior = features.get("behavior") or {}
            reflection_hint = rec.get("reflection_hint") or {}

            rows.append(
                {
                    "rank": idx,
                    "shrine_id": rec.get("shrine_id") or rec.get("id"),
                    "name": rec.get("name"),
                    "score_raw": float(rec.get("_score_total") or 0.0),
                    "score_total": float(breakdown.get("score_total") or 0.0),
                    "score_total_ranked": float(features.get("score_total_ranked") or 0.0),
                    "score_need": int(breakdown.get("score_need") or 0),
                    "score_need_rank_weighted": float(need.get("rank_weighted") or 0.0),
                    "score_distance": float(distance.get("raw") or 0.0),
                    "score_popular": float(popular.get("raw") or 0.0),
                    "score_visit_style": int(visit_style.get("raw") or 0),
                    "score_element": int(element.get("raw") or 0),
                    "behavior_signal": float(behavior.get("raw") or 0.0),
                    "behavior_contribution": float(behavior.get("contribution") or 0.0),
                    "contributions": {
                        "need": float(need.get("rank_weighted_contribution") or 0.0),
                        "distance": float(distance.get("contribution") or 0.0),
                        "popular": float(popular.get("contribution") or 0.0),
                        "visit_style": float(visit_style.get("contribution") or 0.0),
                        "behavior": float(behavior.get("contribution") or 0.0),
                        "element": float(element.get("contribution") or 0.0),
                        "astro_bonus": float(features.get("astro_bonus") or 0.0),
                    },
                    "matched_need_tags": list(breakdown.get("matched_need_tags") or []),
                    "matched_visit_style_tags": list(visit_style.get("matched_tags") or []),
                    "primary_reason_source": rec.get("_primary_reason_source"),
                    "primary_reason_label": rec.get("_primary_reason_label"),
                    "score_total_ranked_base": float(features.get("score_total_ranked_base") or 0.0),
                    "capped_behavior_contribution": float(features.get("capped_behavior_contribution") or 0.0),
                    "behavior_ratio": float(features.get("behavior_ratio") or 0.0),
                    "visit_style_tags": list(rec.get("visit_style_tags") or []),
                    "reflection_hint": reflection_hint,
                    "reflection_hint_state_change_direction": reflection_hint.get("state_change_direction"),
                    "reflection_hint_next_need_hint": list(reflection_hint.get("next_need_hint") or []),
                    "reflection_hint_next_history_theme_hint": list(reflection_hint.get("next_history_theme_hint") or []),
                    "reflection_hint_source_history_theme": reflection_hint.get("source_history_theme"),
                }
            )

        debug = {
            "query": recs.get("_query") or "",
            "need_tags": recs.get("_need_tags") or [],
            "matched_need_tags": [r.get("matched_need_tags") or [] for r in rows],
            "visit_style_tags": [
                list(dict.fromkeys((r.get("visit_style_tags") or []) + (r.get("matched_visit_style_tags") or [])))
                for r in rows
            ],
            "matched_visit_style_tags": [r.get("matched_visit_style_tags") or [] for r in rows],
            "score_total_ranked_base": [r.get("score_total_ranked_base") for r in rows],
            "capped_behavior_contribution": [r.get("capped_behavior_contribution") for r in rows],
            "behavior_ratio": [r.get("behavior_ratio") or 0.0 for r in rows],
            "reflection_hint_state_change_direction": [
                r.get("reflection_hint_state_change_direction")
                for r in rows
            ],
            "reflection_hint_next_need_hint": [
                r.get("reflection_hint_next_need_hint") or []
                for r in rows
            ],
            "reflection_hint_next_history_theme_hint": [
                r.get("reflection_hint_next_history_theme_hint") or []
                for r in rows
            ],
            "reflection_hint_source_history_theme": [
                r.get("reflection_hint_source_history_theme")
                for r in rows
            ],
        }

        return {
            "ranked_count": len(recommendations),
            "top10": rows,
            "_debug": debug,
        }
    except Exception:
        log.exception("[ranking_breakdown_observation] failed")
        return {
            "ranked_count": 0,
            "top10": [],
            "_debug": {
                "query": "",
                "need_tags": [],
                "matched_need_tags": [],
                "visit_style_tags": [],
                "matched_visit_style_tags": [],
                "score_total_ranked_base": [],
                "capped_behavior_contribution": [],
                "behavior_ratio": [],
                "reflection_hint_state_change_direction": [],
                "reflection_hint_next_need_hint": [],
                "reflection_hint_next_history_theme_hint": [],
                "reflection_hint_source_history_theme": [],
            },
        }


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
