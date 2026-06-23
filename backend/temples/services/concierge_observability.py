# temples/services/concierge_observability.py
from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Optional
from temples.models_concierge_analytics import ConciergeRecommendationLog


def summarize_score_v3_ab_observations(observations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """score_v3_ab_observation のリストを集計して重み調整判断用サマリを返す。

    Weight Optimization の判断基準:
    - top1_changed_rate_avg が高い → state weight を上げる
    - max_abs_delta_max が大きい  → 補助シグナルの weight を下げる
    - activation_candidate_rate が安定して高い → active 化を検討する
    """
    valid = [o for o in (observations or []) if isinstance(o, dict)]
    count = len(valid)

    if count == 0:
        return {
            "count": 0,
            "top1_changed_rate_avg": 0.0,
            "activation_candidate_rate": 0.0,
            "avg_delta": 0.0,
            "max_abs_delta_avg": 0.0,
            "max_abs_delta_max": 0.0,
        }

    top1_changed_rate_avg = round(
        sum(float(o.get("top1_changed_rate") or 0.0) for o in valid) / count, 6
    )
    activation_candidate_rate = round(
        sum(1 for o in valid if o.get("activation_candidate")) / count, 6
    )
    avg_delta = round(
        sum(float(o.get("avg_delta") or 0.0) for o in valid) / count, 6
    )
    max_abs_delta_values = [float(o.get("max_abs_delta") or 0.0) for o in valid]
    max_abs_delta_avg = round(sum(max_abs_delta_values) / count, 6)
    max_abs_delta_max = round(max(max_abs_delta_values), 6)

    return {
        "count": count,
        "top1_changed_rate_avg": top1_changed_rate_avg,
        "activation_candidate_rate": activation_candidate_rate,
        "avg_delta": avg_delta,
        "max_abs_delta_avg": max_abs_delta_avg,
        "max_abs_delta_max": max_abs_delta_max,
    }

logger = logging.getLogger("concierge.observability")


def _top3_snapshot(recs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in recs[:3]:
        if not isinstance(r, dict):
            continue

        exp = r.get("explanation") or {}
        reasons = exp.get("reasons") or []
        first_reason_text = None
        if reasons and isinstance(reasons[0], dict):
            first_reason_text = reasons[0].get("text")

        bullets = r.get("bullets") or []
        bullets0 = bullets[0] if isinstance(bullets, list) and bullets else None

        out.append({
            "shrine_id": r.get("shrine_id"),
            "place_id": r.get("place_id"),
            "name": r.get("display_name") or r.get("name"),

            # 本丸
            "reason": r.get("reason"),
            "bullets0": bullets0,
            "ex_summary": exp.get("summary"),
            "ex_reason0": first_reason_text,

            # もし入ってたら見る（後述の reason_source を仕込む用）
            "reason_source": r.get("reason_source"),

            # 既存の補助情報も残すと便利
            "distance_m": r.get("distance_m"),
            "score_total": r.get("_score_total"),
        })
    return out


def concierge_request_summary_log(
    *,
    endpoint: str,  # "chat" or "plan"
    trace_id: str,
    query_len: int,
    flow_requested: Optional[str],
    flow_effective: Optional[str],
    stats: Dict[str, Any],
    recommendations: List[Dict[str, Any]],
) -> None:
    payload = {
        "event": "concierge_result",
        "endpoint": endpoint,
        "trace_id": trace_id,
        "query_len": query_len,
        "flow_requested": flow_requested,
        "flow_effective": flow_effective,
        "result_state": {
            "fallback_mode": stats.get("fallback_mode"),
            "matched_count": stats.get("matched_count"),
            "pool_count": stats.get("pool_count"),
            "displayed_count": stats.get("displayed_count"),
        },
        "top3": _top3_snapshot(recommendations),
    }

    # 1リクエスト1行JSON
    logger.info(json.dumps(payload, ensure_ascii=False))


def save_concierge_recommendation_log(
    *,
    user,
    thread,
    query: str,
    need_tags,
    flow,
    llm_enabled,
    llm_used,
    recommendations,
    result_state,
    lat=None,
    lng=None,
    radius_m=None,
    score_v3_mode: Optional[str] = None,
    score_v3_ab_observation: Optional[Dict[str, Any]] = None,
):
    try:
        debug_payload: Dict[str, Any] = {}
        if score_v3_mode is not None:
            debug_payload["score_v3_mode"] = score_v3_mode
        if score_v3_ab_observation is not None:
            debug_payload["score_v3_ab_observation"] = score_v3_ab_observation

        ConciergeRecommendationLog.objects.create(
            user=user,
            thread=thread,
            query=query or "",
            need_tags=need_tags or [],
            flow=flow or "",
            llm_enabled=bool(llm_enabled),
            llm_used=bool(llm_used),
            recommendations=recommendations or [],
            result_state={**(result_state or {}), **({"_score_v3_debug": debug_payload} if debug_payload else {})},
            lat=lat,
            lng=lng,
            radius_m=radius_m,
        )
    except Exception:
        logger.exception("failed_to_save_concierge_log")


def correlate_score_v3_with_funnel(
    *,
    score_v3_observations: List[Dict[str, Any]],
    funnel: Dict[str, Any],
) -> Dict[str, Any]:
    """score_v3_ab_observation のリストと behavior_funnel 指標を突合する。

    DB 再クエリなし。既存 dict を受け取って合成するのみ。
    summarize_score_v3_ab_observations() + build_score_v3_funnel_correlation_summary() の組み合わせ。
    """
    from temples.services.behavior_funnel import build_score_v3_funnel_correlation_summary

    score_v3_summary = summarize_score_v3_ab_observations(score_v3_observations)
    return build_score_v3_funnel_correlation_summary(
        funnel=funnel,
        score_v3_summary=score_v3_summary,
    )
