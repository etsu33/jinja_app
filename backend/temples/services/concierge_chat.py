from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from django.conf import settings as dj_settings
from temples.domain.consultation_axis import resolve_consultation_axis
from temples.models import GoriyakuTag

from temples.services.concierge_candidate_utils import _normalize_candidate_fields
from temples.services.concierge_chat_extra_condition import (
    resolve_extra_condition_tags,
)
from temples.services.concierge_chat_llm_route import (
    resolve_llm_route,
)
from temples.services.concierge_chat_need import (
    resolve_need_payload,
)
from temples.services.concierge_chat_pool import (
    _ensure_pool_size,
    _merge_candidate_fields,
)
from temples.services.concierge_chat_presentation import (
    _fill_location_from_existing_address,
    _backfill_location_from_name,
    _apply_soft_signal_highlights,
    _attach_reason_source,
    _trim_to_top3_and_fill_message,
)
from temples.services.concierge_chat_ranking import (
    _attach_breakdown,
    _attach_rank_comparison,
    _diversify_by_need,
    _resolve_mode_weights,
    build_recommendation_reason,
    resolve_score_sort_key,
    resolve_score_v3_mode,
)
from temples.services.concierge_chat_response_meta import (
    attach_response_meta,
)
from temples.services.concierge_explanation_payload import (
    attach_explanation_payload,
)
from temples.services.concierge_explanations import (
    attach_explanations_for_chat,
)

from temples.services.concierge_chat_observation import (
    build_trim_observation,
    observe_candidate_pool,
    observe_candidate_pool_debug,
    observe_direction_signal,
    observe_profile_signal,
    observe_ranking_breakdown,
    observe_score_v3_shadow,
    observe_trim_after,
    observe_trim_before,
    observe_visit_style_before_trim,
)


log = logging.getLogger(__name__)


def _resolve_astro_profile(
    birthdate: Optional[str],
) -> Any:
    if not birthdate:
        return None

    try:
        from temples.domain.astrology import sun_sign_and_element  # type: ignore

        return sun_sign_and_element(birthdate)
    except Exception:
        return None


def _build_goriyaku_tag_label_by_id(goriyaku_tag_ids: Optional[List[int]]) -> Dict[int, str]:
    ids = [
        int(x)
        for x in (goriyaku_tag_ids or [])
        if isinstance(x, int) or (isinstance(x, str) and str(x).strip().isdigit())
    ]
    if not ids:
        return {}

    try:
        return dict(GoriyakuTag.objects.filter(id__in=ids).values_list("id", "name"))
    except Exception:
        return {}


def _normalize_int_list(values: Optional[List[int]]) -> List[int]:
    normalized: List[int] = []
    for value in values or []:
        try:
            normalized.append(int(value))
        except (TypeError, ValueError):
            continue
    return normalized


def _build_user_state_profile(
    *,
    query: str,
    extra_condition: Optional[str],
    need_payload: Dict[str, Any],
    need_tags: List[str],
    consultation_axis: str,
    goriyaku_tag_ids: Optional[List[int]],
    recommendations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build a debug-only user state profile from current recommendation inputs.

    This payload keeps user-side state signals in one place.
    matched_need_tags and primary_need_tag are derived from the ranked top recommendation,
    because they are not pure user input; they are user × shrine match results.
    """
    top = recommendations[0] if recommendations else {}
    top_breakdown = top.get("breakdown") if isinstance(top.get("breakdown"), dict) else {}
    top_explanation_payload = (
        top.get("_explanation_payload")
        if isinstance(top.get("_explanation_payload"), dict)
        else {}
    )
    top_score_v2 = top.get("score_v2") if isinstance(top.get("score_v2"), dict) else {}
    top_score_v2_signals = (
        top_score_v2.get("signals")
        if isinstance(top_score_v2.get("signals"), dict)
        else {}
    )

    matched_need_tags = list(
        top_breakdown.get("matched_need_tags")
        or top_explanation_payload.get("matched_need_tags")
        or top_score_v2_signals.get("matched_need_tags")
        or []
    )
    primary_need_tag = (
        top_explanation_payload.get("primary_need_tag")
        or (matched_need_tags[0] if matched_need_tags else None)
    )

    return {
        "version": 1,
        "raw_query": query or "",
        "extra_condition": extra_condition or "",
        "need_tags": list(need_tags or []),
        "need_hits": need_payload.get("hits") or {},
        "consultation_axis": consultation_axis,
        "selected_goriyaku_tag_ids": _normalize_int_list(goriyaku_tag_ids),
        "matched_need_tags": matched_need_tags,
        "primary_need_tag": primary_need_tag,
    }


def _attach_chat_rec_enrichment(
    recs: Dict[str, Any],
    *,
    public_mode: str,
    query: str,
    birthdate: Optional[str],
    need_tags: List[str],
    weights: Dict[str, float],
    astro_bonus_enabled: bool,
    soft_signal_tags: set[str],
    visit_style_tags: set[str],
    goriyaku_tag_ids: Optional[List[int]],
    goriyaku_tag_label_by_id: Dict[int, str],
    user_origin: Optional[Dict[str, Any]] = None,
    user=None,
    profile_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    for rec in recs.get("recommendations") or []:
        if not isinstance(rec, dict):
            continue
        _attach_breakdown(
            rec,
            query=query,
            birthdate=birthdate,
            need_tags=need_tags,
            weights=weights,
            astro_bonus_enabled=astro_bonus_enabled,
            visit_style_tags=visit_style_tags,
            requested_goriyaku_tag_ids=goriyaku_tag_ids,
            goriyaku_tag_label_by_id=goriyaku_tag_label_by_id,
            user_origin=user_origin,
            user=user,
            profile_context=profile_context,
        )
        _apply_soft_signal_highlights(
            rec,
            soft_signal_tags=soft_signal_tags,
        )
        rec["reason"] = build_recommendation_reason(
            rec,
            public_mode=public_mode,  # type: ignore[arg-type]
            birthdate=birthdate,
            need_tags=need_tags,
        )
        _attach_reason_source(
            rec,
            public_mode=public_mode,
        )

    return recs


def _sort_chat_recommendations(
    recs: Dict[str, Any],
    *,
    sort_tags: set[str],
    score_v3_mode: str = "shadow",
) -> Dict[str, Any]:
    recommendations = [r for r in (recs.get("recommendations") or []) if isinstance(r, dict)]

    distance_mode = "sort_distance" in sort_tags

    if distance_mode:
        recommendations = sorted(
            recommendations,
            key=lambda r: (
                float(r.get("distance_m") or 1e12),
                -resolve_score_sort_key(r, score_v3_mode=score_v3_mode),
                str(r.get("name") or ""),
            ),
        )
    else:
        recommendations = sorted(
            recommendations,
            key=lambda r: (
                -resolve_score_sort_key(r, score_v3_mode=score_v3_mode),
                float(r.get("distance_m") or 1e12),
                str(r.get("name") or ""),
            ),
        )
        recommendations = _diversify_by_need(
            recommendations,
            limit=3,
        )

    recs["recommendations"] = recommendations
    return recs


def _attach_astro_meta(
    recs: Dict[str, Any],
    *,
    astro_profile: Any,
) -> Dict[str, Any]:
    if not astro_profile:
        return recs

    recs["_astro"] = {
        "sun_sign": getattr(astro_profile, "sign", None),
        "element": getattr(astro_profile, "element", None),
        "picked": [
            r.get("name")
            for r in (recs.get("recommendations") or [])
            if isinstance(r, dict) and r.get("name")
        ],
        "matched_count": sum(
            1
            for r in (recs.get("recommendations") or [])
            if isinstance(r, dict) and int(r.get("breakdown", {}).get("score_element", 0)) >= 2
        ),
    }
    return recs


def build_chat_recommendations(
    *,
    query: str,
    language: str,
    candidates: list[dict],
    bias=None,
    birthdate=None,
    goriyaku_tag_ids=None,
    extra_condition=None,
    public_mode="need",
    flow="A",
    need_tags: list[str] | None = None,
    consultation_axis: str | None = None,
    llm_enabled: bool | None = None,
    user=None,
    profile_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    候補リストからおすすめ神社を選んで返す関数。

    facade はこのファイルに残し、
    ranking / pool / presentation の責務は各モジュールへ分離する。

    Responsibility:
      - need_tags は相談テーマ由来の主推薦軸として扱う。
      - goriyaku_tag_ids はユーザー追加の補助条件として扱う。
      - extra_condition は参拝スタイルなどの補助条件として扱う。
      - birthdate / astro / direction は主軸を上書きしない補助シグナルとして扱う。
    """
    valid_candidates = [
        _normalize_candidate_fields(c) for c in (candidates or []) if isinstance(c, dict)
    ]

    need_payload = resolve_need_payload(
        query=query or "",
        need_tags=need_tags or [],
        max_tags=3,
    )
    need_tags = need_payload["tags"]
    consultation_axis_extract = resolve_consultation_axis(
        query=query or "",
        need_tags=need_tags,
        llm_axis=consultation_axis,
    )
    consultation_axis_value = consultation_axis_extract.axis
    need_payload["consultation_axis"] = consultation_axis_value
    need_payload["consultation_axis_source"] = consultation_axis_extract.source
    need_payload["consultation_axis_hits"] = consultation_axis_extract.hits

    log.info(
        "[dbg] need_tags has_query=%s query_len=%d tags=%r consultation_axis=%r language=%r flow=%r mode=%r has_extra=%s has_goriyaku=%s",
        bool(query),
        len(query or ""),
        need_tags,
        consultation_axis_value,
        language,
        flow,
        public_mode,
        bool(str(extra_condition or "").strip()),
        bool(goriyaku_tag_ids),
    )

    astro_profile = _resolve_astro_profile(birthdate)

    extra_tags = resolve_extra_condition_tags(
        " ".join(
            part
            for part in [query or "", extra_condition or ""]
            if str(part).strip()
        )
    )
    sort_tags = extra_tags["sort_tags"]
    hard_filter_tags = extra_tags["hard_filter_tags"]
    soft_signal_tags = extra_tags["soft_signal_tags"]
    visit_style_tags = extra_tags["visit_style_tags"]

    log.info(
        "[dbg] extra_tags resolved sort=%r soft=%r visit_style=%r raw_query=%r raw_extra=%r",
        sorted(sort_tags),
        sorted(soft_signal_tags),
        sorted(visit_style_tags),
        query,
        extra_condition,
    )

    observe_candidate_pool(
        valid_candidates=valid_candidates,
        visit_style_tags=visit_style_tags,
        need_tags=need_tags,
    )

    candidate_pool_observation = observe_candidate_pool_debug(
        valid_candidates=valid_candidates,
        filter_context={
            "public_mode": public_mode,
            "flow": flow,
            "has_query": bool(query),
            "query_len": len(query or ""),
            "has_extra_condition": bool(str(extra_condition or "").strip()),
            "has_goriyaku_tag_ids": bool(goriyaku_tag_ids),
            "need_tags": need_tags,
            "consultation_axis": consultation_axis_value,
            "sort_tags": sorted(sort_tags),
            "hard_filter_tags": sorted(hard_filter_tags),
            "visit_style_tags": sorted(visit_style_tags),
        },
    )

    weights = _resolve_mode_weights(
        public_mode=public_mode,  # type: ignore[arg-type]
        flow=flow,
        weights=None,
    )

    astro_bonus_enabled = public_mode == "compat"
    llm_enabled = bool(getattr(dj_settings, "CONCIERGE_USE_LLM", False))

    route = resolve_llm_route(
        query=query or "",
        valid_candidates=valid_candidates,
        need_tags=need_tags,
        llm_enabled=llm_enabled,
    )

    recs = route["recs"]
    recs.setdefault("_debug", {})["candidate_pool_observation"] = candidate_pool_observation
    requested_llm_enabled = bool(route["requested_llm_enabled"])
    effective_llm_enabled = bool(route["effective_llm_enabled"])
    llm_used = bool(route["llm_used"])
    llm_error = route["llm_error"]

    if llm_error:
        log.exception("[build_chat_recommendations] LLM exception traceback")

    log.info(
        "[dbg] route llm_requested=%r llm_effective=%r llm_used=%r seed=%r candidate_count=%d",
        requested_llm_enabled,
        effective_llm_enabled,
        llm_used,
        bool(recs.get("_seed")) if isinstance(recs, dict) else None,
        len(valid_candidates),
    )

    recs = _ensure_pool_size(
        recs,
        candidates=valid_candidates,
        size=20,
    )
    recs = _merge_candidate_fields(
        recs,
        candidates=valid_candidates,
    )

    log.info(
        "[dbg] pool_after_merge size=%d top_names=%r",
        len(recs.get("recommendations") or []),
        [r.get("name") for r in (recs.get("recommendations") or [])[:5] if isinstance(r, dict)],
    )

    goriyaku_tag_label_by_id = _build_goriyaku_tag_label_by_id(goriyaku_tag_ids)

    recs = _attach_chat_rec_enrichment(
        recs,
        public_mode=public_mode,
        query=query or "",
        birthdate=birthdate,
        need_tags=need_tags,
        weights=weights,
        astro_bonus_enabled=astro_bonus_enabled,
        soft_signal_tags=soft_signal_tags,
        visit_style_tags=visit_style_tags,
        goriyaku_tag_ids=goriyaku_tag_ids,
        goriyaku_tag_label_by_id=goriyaku_tag_label_by_id,
        user_origin=bias,
        user=user,
        profile_context=profile_context,
    )
    recs["consultation_axis"] = consultation_axis_value
    for rec in recs.get("recommendations") or []:
        if isinstance(rec, dict):
            rec["consultation_axis"] = consultation_axis_value

    recs = attach_explanation_payload(recs, birthdate=birthdate)

    try:
        log.info(
            "[dbg] explanation_payload_after=%r",
            [
                {
                    "shrine_id": r.get("shrine_id"),
                    "name": r.get("name"),
                    "breakdown_matched_need_tags": (r.get("breakdown") or {}).get(
                        "matched_need_tags"
                    ),
                    "visit_style": ((r.get("breakdown_detail") or {}).get("features") or {}).get("visit_style"),
                    "breakdown_score_need": (r.get("breakdown") or {}).get("score_need"),
                    "explanation_payload": r.get("_explanation_payload"),
                }
                for r in (recs.get("recommendations") or [])
                if isinstance(r, dict)
            ],
        )
    except Exception:
        pass

    score_v3_mode = resolve_score_v3_mode()
    recs = _sort_chat_recommendations(
        recs,
        sort_tags=sort_tags,
        score_v3_mode=score_v3_mode,
    )
    recs.setdefault("_debug", {})["score_v3_mode"] = score_v3_mode
    recs["recommendations"] = _attach_rank_comparison(recs.get("recommendations") or [])
    recs.setdefault("_debug", {})["user_state_profile"] = _build_user_state_profile(
        query=query or "",
        extra_condition=extra_condition,
        need_payload=need_payload,
        need_tags=need_tags,
        consultation_axis=consultation_axis_value,
        goriyaku_tag_ids=goriyaku_tag_ids,
        recommendations=[
            r
            for r in (recs.get("recommendations") or [])
            if isinstance(r, dict)
        ],
    )
    recs.setdefault("_debug", {})["ranking_breakdown_observation"] = observe_ranking_breakdown(
        recs=recs,
    )

    observation = observe_visit_style_before_trim(
        recs=recs,
        query=query or "",
        extra_condition=extra_condition,
        visit_style_tags=visit_style_tags,
    )
    recs.setdefault("_debug", {})["visit_style_observation"] = observation

    trim_before = observe_trim_before(recs)

    _fill_location_from_existing_address(recs)
    _backfill_location_from_name(
        recs,
        bias=bias,
        language=language,
    )
    _trim_to_top3_and_fill_message(recs)

    trim_after = observe_trim_after(recs)
    recs.setdefault("_debug", {})["trim_observation"] = build_trim_observation(
        before=trim_before,
        after=trim_after,
    )
    recs.setdefault("_debug", {})["profile_signal_observation"] = observe_profile_signal(
        recs=recs,
        profile_context=profile_context,
    )
    recs.setdefault("_debug", {})["direction_signal_observation"] = observe_direction_signal(
        recs=recs,
        profile_context=profile_context,
    )

    # Score v3 shadow observation（score_total との差分を観測のみ、ranking 変更なし）
    _v3_recs = [r for r in (recs.get("recommendations") or []) if isinstance(r, dict)]
    if any((r.get("breakdown") or {}).get("score_v3") is not None for r in _v3_recs):
        recs.setdefault("_debug", {})["score_v3_shadow_observation"] = observe_score_v3_shadow(
            recommendations=_v3_recs,
        )

    try:
        log.info(
            "[dbg] scored_pool=%r",
            [
                {
                    "name": r.get("name"),
                    "distance_m": r.get("distance_m"),
                    "score_total": r.get("_score_total"),
                    "score_need": (r.get("breakdown") or {}).get("score_need"),
                    "matched_need_tags": (r.get("breakdown") or {}).get("matched_need_tags"),
                    "visit_style": ((r.get("breakdown_detail") or {}).get("features") or {}).get("visit_style"),
                    "goriyaku": r.get("goriyaku"),
                    "reason": r.get("reason"),
                }
                for r in (recs.get("recommendations") or [])
                if isinstance(r, dict)
            ],
        )
    except Exception:
        pass

    if llm_error:
        log.warning("[build_chat_recommendations] LLM error: %s", llm_error)

    recs = _attach_astro_meta(
        recs,
        astro_profile=astro_profile,
    )

    recs["consultation_axis"] = consultation_axis_value
    for rec in recs.get("recommendations") or []:
        if isinstance(rec, dict):
            rec["consultation_axis"] = consultation_axis_value

    recs["_need"] = need_payload

    recs = attach_response_meta(
        recs,
        public_mode=public_mode,
        flow=flow,
        weights=weights,
        astro_bonus_enabled=astro_bonus_enabled,
        birthdate=birthdate,
        effective_llm_enabled=effective_llm_enabled,
        llm_used=llm_used,
        llm_error=llm_error,
        valid_candidates=valid_candidates,
        extra_condition=extra_condition,
        goriyaku_tag_ids=goriyaku_tag_ids,
        hard_filter_tags=hard_filter_tags,
        consultation_axis=consultation_axis_value,
    )

    recs = attach_explanations_for_chat(
        recs,
        query=query or "",
        bias=bias,
        birthdate=birthdate,
        extra_condition=extra_condition,
    )

    return recs
