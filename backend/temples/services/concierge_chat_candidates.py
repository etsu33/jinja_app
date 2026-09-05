"""Recommendation候補の共有生成レイヤー。

ConciergeとCompassが各自のselection logicへ分岐する**手前**の共通層であり、
Shared Recommendation Eligibility gate（Knowledge Fact有無による候補適格性）は
ここに一本化する。Compass側へ同じ判定を複製しない。

不変条件（docs/knowledge/recommendation-eligibility-contract.md）:

    Shrine DB presence != Recommendation eligibility
    Recommendation eligibility = usable Deity Fact または usable History Fact が
                                 少なくとも1件存在すること

usable判定そのものは既存のKnowledge / Evidence Gate authority
（shrine_knowledge_selector -> evidence_gate.decide_fact_usability）へ委譲し、
本モジュールで新しいreadiness ruleを定義しない。
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, Iterable, List, Optional
from dataclasses import asdict

from django.db.models import Q

from temples.models import Shrine
from temples.services.concierge_candidate_utils import (
    _dedupe_candidates,
    _to_float,
)
from temples.services.shrine_trust_metadata import get_shrine_trust_metadata

from temples.services.shrine_meaning_composer import compose_shrine_meaning_payload
from temples.services.meaning_translation import translate_meaning
from temples.services.shrine_knowledge_selector import (
    fetch_fact_ready_knowledge_deities,
    fetch_fact_ready_knowledge_histories,
)
from temples.services.shrine_qa_fixture_exclusion import exclude_qa_fixture_shrines

log = logging.getLogger(__name__)

DEFAULT_LIMIT = 20


def is_recommendation_eligible(
    *,
    knowledge_deities: Any,
    knowledge_histories: Any,
) -> bool:
    """Shared Recommendation Eligibility rule（唯一の判定式）。

        usable Deity Fact OR usable History Fact

    引数は shrine_knowledge_selector.fetch_fact_ready_knowledge_*() が返す
    「usable判定を通過したFactのみ」のlistである。したがってここでは
    「1件以上あるか」だけを見る -- readiness ruleを新設せず、usable判定は
    evidence_gate.decide_fact_usability() を正本とする。

    legacy `goriyaku` / `history_theme` からeligibilityを推定しない。
    """
    return bool(knowledge_deities) or bool(knowledge_histories)


def _candidate_shrine_id(candidate: Dict[str, Any]) -> Optional[int]:
    for key in ("shrine_id", "id"):
        value = candidate.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().lstrip("-").isdigit():
            return int(value)
    return None


def filter_recommendation_eligible_candidates(
    candidates: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """候補listへShared Recommendation Eligibility gateを適用する。

    build_chat_candidates() が組み立てた候補は `knowledge_deities` /
    `knowledge_histories` を既に保持しているため、追加クエリなしで判定できる。
    外部由来（例: requestで持ち込まれた候補）でこれらのkeyを持たないものは、
    **同じ** shrine_knowledge_selector authorityでshrine idからまとめて解決する
    （判定式を二重に書かない）。

    shrine idを解決できない候補はineligible（fail closed）。ineligibleな候補を
    低スコアで残す・fallbackとして保持する・後から再投入する、のいずれも行わない。
    """
    rows = [c for c in candidates if isinstance(c, dict)]

    unresolved_ids = sorted(
        {
            shrine_id
            for c in rows
            if "knowledge_deities" not in c and "knowledge_histories" not in c
            for shrine_id in (_candidate_shrine_id(c),)
            if shrine_id is not None
        }
    )
    fetched_deities: Dict[int, List[Dict[str, Any]]] = {}
    fetched_histories: Dict[int, List[Dict[str, Any]]] = {}
    if unresolved_ids:
        fetched_deities = fetch_fact_ready_knowledge_deities(unresolved_ids)
        fetched_histories = fetch_fact_ready_knowledge_histories(unresolved_ids)

    eligible: List[Dict[str, Any]] = []
    for row in rows:
        if "knowledge_deities" in row or "knowledge_histories" in row:
            deities = row.get("knowledge_deities") or []
            histories = row.get("knowledge_histories") or []
        else:
            shrine_id = _candidate_shrine_id(row)
            deities = fetched_deities.get(shrine_id, []) if shrine_id is not None else []
            histories = fetched_histories.get(shrine_id, []) if shrine_id is not None else []
        if is_recommendation_eligible(
            knowledge_deities=deities,
            knowledge_histories=histories,
        ):
            eligible.append(row)
    return eligible


def _distance_m(
    lat1: Optional[float],
    lng1: Optional[float],
    lat2: Optional[float],
    lng2: Optional[float],
) -> Optional[int]:
    lat1f = _to_float(lat1)
    lng1f = _to_float(lng1)
    lat2f = _to_float(lat2)
    lng2f = _to_float(lng2)
    if None in (lat1f, lng1f, lat2f, lng2f):
        return None

    r = 6371000
    phi1 = math.radians(lat1f)
    phi2 = math.radians(lat2f)
    dphi = math.radians(lat2f - lat1f)
    dl = math.radians(lng2f - lng1f)
    a = (math.sin(dphi / 2) ** 2) + (
        math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    )
    return int(2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def build_chat_candidates(
    *,
    goriyaku_tag_ids: Optional[List[int]] = None,
    area: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    limit: int = DEFAULT_LIMIT,
    trace_id: str | None = None,
    interpretation_profile: dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    qs = Shrine.objects.all()

    if goriyaku_tag_ids:
        qs = qs.filter(goriyaku_tags__id__in=goriyaku_tag_ids).distinct()

    # area文字列フィルタは、座標が取れていない時だけ使う
    if area and (lat is None or lng is None):
        qs = qs.filter(
            Q(address__icontains=area)
            | Q(name_jp__icontains=area)
            | Q(name_romaji__icontains=area)
        )

    # QA用fixture Shrineの除外条件は shrine_qa_fixture_exclusion.py を正本とし、
    # Knowledge Coverage集計（knowledge_coverage_report command）と共有する。
    qs = exclude_qa_fixture_shrines(qs)

    qs = qs.select_related("place_ref")
    qs = qs.prefetch_related("goriyaku_tags")
    qs = qs.filter(latitude__isnull=False, longitude__isnull=False)
    qs = qs.exclude(address="")

    # 候補母集団は少し広めに取る
    if hasattr(Shrine, "popular_score"):
        qs = qs.order_by("-popular_score", "id")
    else:
        qs = qs.order_by("id")

    pool_limit = max(limit * 5, 50)
    shrines = list(qs[:pool_limit])
    shrine_ids = [s.id for s in shrines]
    knowledge_deities_by_shrine = fetch_fact_ready_knowledge_deities(shrine_ids)
    knowledge_histories_by_shrine = fetch_fact_ready_knowledge_histories(shrine_ids)

    candidates: List[Dict[str, Any]] = []
    ineligible_count = 0
    for s in shrines:
        # Shared Recommendation Eligibility gate。ConciergeとCompassが分岐する
        # 手前のこの1箇所だけで適用する（Compass側に同じ判定を複製しない）。
        # usable判定はshrine_knowledge_selector -> evidence_gateへ委譲済みで、
        # ここは「usable Deity Fact OR usable History Fact」の有無だけを見る。
        shrine_deities = knowledge_deities_by_shrine.get(s.id, [])
        shrine_histories = knowledge_histories_by_shrine.get(s.id, [])
        if not is_recommendation_eligible(
            knowledge_deities=shrine_deities,
            knowledge_histories=shrine_histories,
        ):
            # 除外した候補は低スコアで残さず、fallbackとしても保持しない。
            # pool_limitのスライスはこのgateより前にpoolへ効くため、gate後の
            # 候補数がpool_limitを下回ることがある。不足分をineligibleな
            # Shrineで埋め戻すことはしない（silent fallbackの禁止）。
            ineligible_count += 1
            continue

        dist = _distance_m(lat, lng, s.latitude, s.longitude)

        pref = getattr(s, "place_ref", None)
        place_id = getattr(pref, "place_id", None) if pref else None
        trust_metadata = get_shrine_trust_metadata(s.id)

        meaning_source = s
        if interpretation_profile is not None:
            translation_result = translate_meaning(interpretation_profile)
            setattr(meaning_source, "interpretation_profile", interpretation_profile)
            setattr(meaning_source, "translation_result", translation_result)

        meaning_payload = compose_shrine_meaning_payload(meaning_source)
        generated_meaning = meaning_payload.get("generated") or {}

        candidates.append(
            {
                "id": s.id,
                "shrine_id": s.id,
                "place_id": place_id,
                "name": s.name_jp or s.name_romaji,
                "address": s.address,
                "lat": s.latitude,
                "lng": s.longitude,
                "distance_m": dist,
                "goriyaku": getattr(s, "goriyaku", None),
                "sajin": getattr(s, "sajin", None),
                "description": getattr(s, "description", None),
                "knowledge_deities": shrine_deities,
                "knowledge_histories": shrine_histories,
                "astro_tags": getattr(s, "astro_tags", None),
                "astro_elements": getattr(s, "astro_elements", None),
                "visit_style_tags": getattr(s, "visit_style_tags", None),
                "history_theme": getattr(s, "history_theme", ""),
                "astro_priority": getattr(s, "astro_priority", None),
                # .values_list()はprefetch_relatedのcacheを使わず新規queryを発行するため、
                # .all()経由でPython側抽出する（N+1回避、shrine_meaning_composer.py
                # の_read_goriyaku_tags()と同じ理由）。
                "goriyaku_tag_ids": [tag.id for tag in s.goriyaku_tags.all()]
                if hasattr(s, "goriyaku_tags")
                else [],
                "popular_score": getattr(s, "popular_score", None),
                "trust_metadata": asdict(trust_metadata) if trust_metadata else None,
                "history_context": generated_meaning.get("historyContext"),
            }
        )

    # 座標がある場合は距離優先、ない場合は人気順
    if lat is not None and lng is not None:
        candidates.sort(
            key=lambda c: (
                float(c.get("distance_m") or 1e12),
                -float(c.get("popular_score") or 0),
                str(c.get("name") or ""),
            )
        )
    else:
        candidates.sort(
            key=lambda c: (
                -float(c.get("popular_score") or 0),
                str(c.get("name") or ""),
            )
        )

    candidates = candidates[:pool_limit]
    candidates = _dedupe_candidates(candidates)

    with_pid = sum(1 for c in candidates if c.get("place_id"))
    miss_latlng = sum(
        1 for c in candidates
        if c.get("lat") is None or c.get("lng") is None
    )
    dist_none = sum(1 for c in candidates if c.get("distance_m") is None)

    log.info(
        "[svc/chat_candidates] trace=%s count=%d eligible=%d ineligible=%d "
        "with_place_id=%d miss_latlng=%d dist_none=%d "
        "area=%r goriyaku=%s latlng_in=%s/%s limit=%d",
        trace_id,
        len(candidates),
        len(candidates),
        ineligible_count,
        with_pid,
        miss_latlng,
        dist_none,
        (area or "")[:20] if isinstance(area, str) else area,
        "Y" if goriyaku_tag_ids else "N",
        "Y" if lat is not None else "N",
        "Y" if lng is not None else "N",
        limit,
    )

    return candidates
