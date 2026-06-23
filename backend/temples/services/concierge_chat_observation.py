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
            score_v2 = rec.get("score_v2") if isinstance(rec.get("score_v2"), dict) else {}
            score_v2_signals = (
                score_v2.get("signals")
                if isinstance(score_v2.get("signals"), dict)
                else {}
            )
            score_v2_components = (
                score_v2.get("components")
                if isinstance(score_v2.get("components"), dict)
                else {}
            )
            context_profile = (
                score_v2_signals.get("context_profile")
                if isinstance(score_v2_signals.get("context_profile"), dict)
                else {}
            )
            shrine_meaning_profile = (
                score_v2_signals.get("shrine_meaning_profile")
                if isinstance(score_v2_signals.get("shrine_meaning_profile"), dict)
                else {}
            )
            behavior_profile = (
                score_v2_signals.get("behavior_profile")
                if isinstance(score_v2_signals.get("behavior_profile"), dict)
                else {}
            )
            reflection_hint = rec.get("reflection_hint") or score_v2_signals.get("reflection_hint") or {}

            rows.append(
                {
                    "rank": idx,
                    "shrine_id": rec.get("shrine_id") or rec.get("id"),
                    "name": rec.get("name"),
                    "score_raw": float(rec.get("_score_total") or 0.0),
                    "score_total": float(breakdown.get("score_total") or 0.0),
                    "score_total_ranked": float(features.get("score_total_ranked") or 0.0),
                    "score_v2_total": float(score_v2.get("total") or 0.0),
                    "user_state_match": float(score_v2_components.get("user_state_match") or 0.0),
                    "shrine_meaning_match": float(score_v2_components.get("shrine_meaning_match") or 0.0),
                    "context_match": float(score_v2_components.get("context_match") or 0.0),
                    "score_need": int(breakdown.get("score_need") or 0),
                    "score_need_rank_weighted": float(need.get("rank_weighted") or 0.0),
                    "score_distance": float(distance.get("raw") or 0.0),
                    "score_popular": float(popular.get("raw") or 0.0),
                    "score_visit_style": int(visit_style.get("raw") or 0),
                    "score_element": int(element.get("raw") or 0),
                    "direction_bonus": float(context_profile.get("direction_bonus") or 0.0),
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
                    "context_profile": context_profile,
                    "shrine_meaning_profile": shrine_meaning_profile,
                    "behavior_profile": behavior_profile,
                    "reflection_hint": reflection_hint,
                    "reflection_hint_state_change_direction": reflection_hint.get("state_change_direction"),
                    "reflection_hint_next_need_hint": list(reflection_hint.get("next_need_hint") or []),
                    "reflection_hint_next_history_theme_hint": list(reflection_hint.get("next_history_theme_hint") or []),
                    "reflection_hint_source_history_theme": reflection_hint.get("source_history_theme"),
                }
            )

        recs_debug = recs.get("_debug") if isinstance(recs.get("_debug"), dict) else {}
        user_state_profile = (
            recs_debug.get("user_state_profile")
            if isinstance(recs_debug.get("user_state_profile"), dict)
            else {}
        )

        score_element_distribution: dict[str, int] = {}
        primary_reason_source_counts: dict[str, int] = {}
        for row in rows:
            score_element_key = str(int(row.get("score_element") or 0))
            score_element_distribution[score_element_key] = score_element_distribution.get(score_element_key, 0) + 1

            primary_reason_source = str(row.get("primary_reason_source") or "fallback")
            primary_reason_source_counts[primary_reason_source] = primary_reason_source_counts.get(primary_reason_source, 0) + 1

        row_count = len(rows)
        astro_bonus_hit_count = sum(
            1
            for row in rows
            if float((row.get("contributions") or {}).get("astro_bonus") or 0.0) > 0
        )
        direction_bonus_hit_count = sum(
            1
            for row in rows
            if float(row.get("direction_bonus") or 0.0) > 0
        )

        def _rate(count: int) -> float:
            return float(count / row_count) if row_count else 0.0

        score_audit = {
            "row_count": row_count,
            "score_element_distribution": score_element_distribution,
            "astro_bonus_hit_count": astro_bonus_hit_count,
            "astro_bonus_hit_rate": _rate(astro_bonus_hit_count),
            "direction_bonus_hit_count": direction_bonus_hit_count,
            "direction_bonus_hit_rate": _rate(direction_bonus_hit_count),
            "primary_reason_source_counts": primary_reason_source_counts,
            "top10_element_primary_count": primary_reason_source_counts.get("element", 0),
            "top10_element_primary_rate": _rate(primary_reason_source_counts.get("element", 0)),
            "history_theme_primary_count": primary_reason_source_counts.get("history_theme", 0),
            "history_theme_primary_rate": _rate(primary_reason_source_counts.get("history_theme", 0)),
            "culture_translation_primary_count": primary_reason_source_counts.get("culture_translation", 0),
            "culture_translation_primary_rate": _rate(primary_reason_source_counts.get("culture_translation", 0)),
            "need_tag_primary_count": primary_reason_source_counts.get("need_tag", 0),
            "need_tag_primary_rate": _rate(primary_reason_source_counts.get("need_tag", 0)),
        }

        debug = {
            "query": recs.get("_query") or "",
            "need_tags": recs.get("_need_tags") or [],
            "user_state_profile": user_state_profile,
            "score_audit": score_audit,
            "matched_need_tags": [r.get("matched_need_tags") or [] for r in rows],
            "visit_style_tags": [
                list(dict.fromkeys((r.get("visit_style_tags") or []) + (r.get("matched_visit_style_tags") or [])))
                for r in rows
            ],
            "matched_visit_style_tags": [r.get("matched_visit_style_tags") or [] for r in rows],
            "score_total_ranked_base": [r.get("score_total_ranked_base") for r in rows],
            "score_v2_total": [r.get("score_v2_total") for r in rows],
            "user_state_match": [r.get("user_state_match") for r in rows],
            "shrine_meaning_match": [r.get("shrine_meaning_match") for r in rows],
            "context_match": [r.get("context_match") for r in rows],
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
                "user_state_profile": {},
                "score_audit": {
                    "row_count": 0,
                    "score_element_distribution": {},
                    "astro_bonus_hit_count": 0,
                    "astro_bonus_hit_rate": 0.0,
                    "direction_bonus_hit_count": 0,
                    "direction_bonus_hit_rate": 0.0,
                    "primary_reason_source_counts": {},
                    "top10_element_primary_count": 0,
                    "top10_element_primary_rate": 0.0,
                    "history_theme_primary_count": 0,
                    "history_theme_primary_rate": 0.0,
                    "culture_translation_primary_count": 0,
                    "culture_translation_primary_rate": 0.0,
                    "need_tag_primary_count": 0,
                    "need_tag_primary_rate": 0.0,
                },
                "matched_need_tags": [],
                "visit_style_tags": [],
                "matched_visit_style_tags": [],
                "score_total_ranked_base": [],
                "score_v2_total": [],
                "user_state_match": [],
                "shrine_meaning_match": [],
                "context_match": [],
                "capped_behavior_contribution": [],
                "behavior_ratio": [],
                "reflection_hint_state_change_direction": [],
                "reflection_hint_next_need_hint": [],
                "reflection_hint_next_history_theme_hint": [],
                "reflection_hint_source_history_theme": [],
            },
        }


def observe_direction_signal(
    *,
    recs: dict[str, Any],
    profile_context: dict[str, Any] | None,
) -> dict[str, Any]:
    """direction_profile が推薦に使われたかを記録する。"""
    try:
        direction_profile = (profile_context or {}).get("direction_profile") or {}
        lucky = str(direction_profile.get("luckyDirection") or "").strip() if isinstance(direction_profile, dict) else ""
        hit_count = 0
        total_score = 0.0

        for rec in (recs.get("recommendations") or []):
            if not isinstance(rec, dict):
                continue
            ds = (rec.get("breakdown") or {}).get("direction_signal") or {}
            if isinstance(ds, dict) and ds.get("matched"):
                hit_count += 1
                total_score += float(ds.get("score") or 0.0)

        return {
            "has_direction_profile": bool(lucky),
            "lucky_direction": lucky or None,
            "hit_count": hit_count,
            "total_score": round(total_score, 6),
        }
    except Exception:
        log.exception("[observe_direction_signal] failed")
        return {"has_direction_profile": False, "lucky_direction": None, "hit_count": 0, "total_score": 0.0}


def observe_profile_signal(
    *,
    recs: dict[str, Any],
    profile_context: dict[str, Any] | None,
) -> dict[str, Any]:
    """profile_context が推薦に使われたかを記録する。"""
    try:
        has_context = isinstance(profile_context, dict)
        hit_count = 0
        total_score = 0.0

        for rec in (recs.get("recommendations") or []):
            if not isinstance(rec, dict):
                continue
            ps = (rec.get("breakdown") or {}).get("profile_signal") or {}
            if isinstance(ps, dict) and ps.get("matched"):
                hit_count += 1
                total_score += float(ps.get("score") or 0.0)

        return {
            "has_profile_context": has_context,
            "hit_count": hit_count,
            "total_score": round(total_score, 6),
        }
    except Exception:
        log.exception("[observe_profile_signal] failed")
        return {"has_profile_context": False, "hit_count": 0, "total_score": 0.0}


def observe_score_v3_shadow(
    *,
    recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    """score_v3 と score_total の差分を観測する（shadow モード）。

    既存の ranking / sort 順には影響しない。
    """
    try:
        items: list[dict[str, Any]] = []
        for idx, rec in enumerate(recommendations or [], start=1):
            if not isinstance(rec, dict):
                continue
            breakdown = rec.get("breakdown") or {}
            score_total = float(breakdown.get("score_total") or 0.0)
            score_v3 = float(breakdown.get("score_v3") or 0.0)
            items.append(
                {
                    "rank": idx,
                    "name": rec.get("name"),
                    "score_total": round(score_total, 6),
                    "score_v3": round(score_v3, 6),
                    "delta": round(score_v3 - score_total, 6),
                }
            )

        if not items:
            return {
                "mode": "shadow",
                "count": 0,
                "top1_changed": False,
                "score_total_top1": None,
                "score_v3_top1": None,
                "items": [],
            }

        # score_total 順（現在の ranking 順）で top1
        score_total_top1_item = max(items, key=lambda x: x["score_total"])
        # score_v3 順で top1
        score_v3_sorted = sorted(items, key=lambda x: -x["score_v3"])
        score_v3_top1_item = score_v3_sorted[0]

        top1_changed = score_total_top1_item["name"] != score_v3_top1_item["name"]

        score_total_top1 = {
            "rank": score_total_top1_item["rank"],
            "name": score_total_top1_item["name"],
            "score_total": score_total_top1_item["score_total"],
        }
        score_v3_top1 = {
            "rank": score_v3_top1_item["rank"],
            "name": score_v3_top1_item["name"],
            "score_v3": score_v3_top1_item["score_v3"],
        }

        log.info(
            "[score_v3_shadow] count=%s top1_changed=%s score_total_top1=%s score_v3_top1=%s",
            len(items),
            top1_changed,
            score_total_top1,
            score_v3_top1,
        )

        return {
            "mode": "shadow",
            "count": len(items),
            "top1_changed": top1_changed,
            "score_total_top1": score_total_top1,
            "score_v3_top1": score_v3_top1,
            "items": items,
        }
    except Exception:
        log.exception("[observe_score_v3_shadow] failed")
        return {
            "mode": "shadow",
            "count": 0,
            "top1_changed": False,
            "score_total_top1": None,
            "score_v3_top1": None,
            "items": [],
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
