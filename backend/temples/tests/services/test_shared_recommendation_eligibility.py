"""Shared Recommendation Eligibility gate の契約テスト。

不変条件（docs/knowledge/recommendation-eligibility-contract.md）:

    Shrine DB presence != Recommendation eligibility
    Recommendation eligibility = usable Deity Fact または usable History Fact が
                                 1件以上存在すること

    Shared eligibility != F5 Qualified Evidence gating
    Shared eligibility != ranking signal
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.utils import timezone

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services import compass_recommendation_orchestrator as compass_orch
from temples.services.compass_direction_filter import filter_candidates_by_direction
from temples.services.compass_recommendation_orchestrator import (
    STATE_DIRECTION_FILTER_UNAVAILABLE,
    STATE_DIRECTION_ZERO_CANDIDATES,
    STATE_EVIDENCE_ZERO_CANDIDATES,
    STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES,
    STATE_RECOMMENDATION_SUCCESS,
    _apply_compass_distance_stage,
    get_compass_recommendations,
)
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_candidates import (
    build_chat_candidates,
    build_chat_candidates_with_eligibility,
    filter_recommendation_eligible_candidates,
    is_recommendation_eligible,
)
from temples.tests.support.recommendation_eligibility import (
    attach_usable_deity_fact,
    attach_usable_history_fact,
    create_fact_ready_source,
)

pytestmark = pytest.mark.django_db

CONCIERGE_URL = "/api/concierge/chat/"
COMPASS_URL = "/api/compass/recommendations/"
ORIGIN = {"lat": 35.0, "lng": 135.0}
NORTH_DIRECTION_CONTEXT = {
    "referenceDirections": ["北"],
    "calculationMethod": "annual_monthly_kyusei_v1",
}


def _shrine(name: str, *, latitude: float = 35.0, longitude: float = 139.0) -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都千代田区1-1",
        latitude=latitude,
        longitude=longitude,
    )


def _candidate_names(**kwargs) -> list[str]:
    kwargs.setdefault("lat", 35.0)
    kwargs.setdefault("lng", 139.0)
    kwargs.setdefault("area", None)
    kwargs.setdefault("goriyaku_tag_ids", None)
    kwargs.setdefault("trace_id", "test")
    return [c["name"] for c in build_chat_candidates(**kwargs)]


# --------------------------------------------------------------------------
# 1-4: eligibility rule
# --------------------------------------------------------------------------


def test_usable_deity_only_is_eligible():
    attach_usable_deity_fact(_shrine("祭神のみ神社"))
    assert "祭神のみ神社" in _candidate_names()


def test_usable_history_only_is_eligible():
    attach_usable_history_fact(_shrine("由緒のみ神社"))
    assert "由緒のみ神社" in _candidate_names()


def test_both_usable_is_eligible():
    shrine = _shrine("両方あり神社")
    attach_usable_deity_fact(shrine)
    attach_usable_history_fact(shrine)
    assert "両方あり神社" in _candidate_names()


def test_neither_usable_is_excluded():
    _shrine("Knowledgeなし神社")
    assert "Knowledgeなし神社" not in _candidate_names()


def test_fact_ready_fact_without_fact_ready_source_is_not_usable():
    # eligibility判定は既存Evidence Gate authorityへ委譲しており、
    # 新しいreadiness ruleを定義していない: Fact自身がfact-readyでも
    # fact-ready Sourceが無ければusableではない。
    shrine = _shrine("出典なし神社")
    ShrineDeity.objects.create(
        shrine=shrine,
        display_name="出典なし祭神",
        sort_order=0,
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    assert "出典なし神社" not in _candidate_names()


def test_draft_fact_with_fact_ready_source_is_not_usable():
    shrine = _shrine("下書き神社")
    history = ShrineHistory.objects.create(
        shrine=shrine,
        history_type="official_origin",
        title="下書き由緒",
        content="下書き",
        sort_order=0,
        verification_status="draft",
    )
    history.sources.add(create_fact_ready_source())
    assert "下書き神社" not in _candidate_names()


def test_legacy_goriyaku_and_history_theme_do_not_confer_eligibility():
    shrine = _shrine("legacyのみ神社")
    shrine.goriyaku = "縁結び・厄除け"
    shrine.history_theme = "再出発"
    shrine.save(update_fields=["goriyaku", "history_theme"])
    assert "legacyのみ神社" not in _candidate_names()


@pytest.mark.parametrize(
    ("deities", "histories", "expected"),
    [
        ([{"display_name": "祭神"}], [], True),
        ([], [{"title": "由緒"}], True),
        ([{"display_name": "祭神"}], [{"title": "由緒"}], True),
        ([], [], False),
        (None, None, False),
    ],
)
def test_eligibility_predicate_is_deity_or_history(deities, histories, expected):
    assert (
        is_recommendation_eligible(
            knowledge_deities=deities, knowledge_histories=histories
        )
        is expected
    )


# --------------------------------------------------------------------------
# 5: Concierge and Compass share one rule
# --------------------------------------------------------------------------


def test_compass_candidate_pool_comes_from_the_same_shared_builder():
    # Compassは自前でeligibilityを判定せず、共有層build_chat_candidates()の
    # 返り値をそのまま受け取る。
    attach_usable_deity_fact(_shrine("適格神社", latitude=35.2, longitude=135.0))
    _shrine("不適格神社", latitude=35.3, longitude=135.0)

    captured: dict[str, object] = {}
    original = compass_orch.build_chat_candidates_with_eligibility

    def _spy(**kwargs):
        result = original(**kwargs)
        captured["names"] = [c["name"] for c in result.candidates]
        return result

    compass_orch.build_chat_candidates_with_eligibility = _spy  # type: ignore[assignment]
    try:
        get_compass_recommendations(
            purpose="career",
            origin=ORIGIN,
            direction_context=NORTH_DIRECTION_CONTEXT,
        )
    finally:
        compass_orch.build_chat_candidates_with_eligibility = original  # type: ignore[assignment]

    assert captured["names"] == ["適格神社"]


def test_compass_module_contains_no_eligibility_logic():
    # eligibility判定はCompass側へ複製しない（共有層に一本化する）。
    source = Path(compass_orch.__file__).read_text(encoding="utf-8")
    for marker in (
        "knowledge_deities",
        "knowledge_histories",
        "is_recommendation_eligible",
        "decide_fact_usability",
        "fetch_fact_ready_knowledge",
    ):
        assert marker not in source, f"compass must not re-implement eligibility: {marker}"


def test_concierge_and_compass_agree_on_the_same_shrine_set():
    attach_usable_history_fact(_shrine("共通適格神社", latitude=35.2, longitude=135.0))
    _shrine("共通不適格神社", latitude=35.25, longitude=135.0)

    concierge_pool = build_chat_candidates(
        lat=ORIGIN["lat"], lng=ORIGIN["lng"], area=None, goriyaku_tag_ids=None, trace_id="t"
    )
    compass_pool = build_chat_candidates(
        lat=ORIGIN["lat"],
        lng=ORIGIN["lng"],
        limit=compass_orch.DEFAULT_CANDIDATE_POOL_LIMIT,
        trace_id="t",
    )
    assert {c["name"] for c in concierge_pool} == {c["name"] for c in compass_pool}
    assert {c["name"] for c in concierge_pool} == {"共通適格神社"}


# --------------------------------------------------------------------------
# 6: no re-entry through fallback
# --------------------------------------------------------------------------


def test_ineligible_shrine_cannot_re_enter_through_request_candidates(client, settings):
    settings.CONCIERGE_USE_LLM = False
    ineligible = _shrine("再流入神社")

    response = client.post(
        CONCIERGE_URL,
        data=json.dumps(
            {
                "message": "近場で参拝したい",
                "lat": 35.0,
                "lng": 139.0,
                "candidates": [
                    {
                        "shrine_id": ineligible.id,
                        "name": "再流入神社",
                        "address": "東京都千代田区1-1",
                        "lat": 35.0,
                        "lng": 139.0,
                        "popular_score": 99.0,
                    }
                ],
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 200
    body = response.json()
    names = [
        r.get("name") for r in (body.get("data", {}).get("recommendations") or [])
    ]
    assert "再流入神社" not in names


def test_ineligible_candidate_without_shrine_id_is_excluded_fail_closed():
    # shrine idを解決できない候補はeligibilityを証明できないためineligible。
    assert filter_recommendation_eligible_candidates([{"name": "無名候補"}]) == []


def test_filter_is_idempotent_and_never_re_adds():
    eligible = {"name": "適格", "knowledge_deities": [{"display_name": "祭神"}], "knowledge_histories": []}
    ineligible = {"name": "不適格", "knowledge_deities": [], "knowledge_histories": []}
    once = filter_recommendation_eligible_candidates([eligible, ineligible])
    twice = filter_recommendation_eligible_candidates(once)
    assert once == [eligible]
    assert twice == [eligible]


# --------------------------------------------------------------------------
# 7: Concierge zero-candidate safety
# --------------------------------------------------------------------------


def test_concierge_returns_safe_empty_response_when_all_candidates_are_ineligible(
    client, settings
):
    settings.CONCIERGE_USE_LLM = False
    _shrine("不適格A")
    _shrine("不適格B", latitude=35.01, longitude=139.01)

    response = client.post(
        CONCIERGE_URL,
        data=json.dumps({"message": "近場で参拝したい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body.get("ok") is True
    data = body.get("data") or {}
    # 既存の安全な空レスポンス形（fallbackの神社をでっち上げない）。
    assert data.get("recommendations") == []
    assert isinstance(data.get("message"), str) and data["message"].strip()


def test_concierge_empty_pool_produces_no_fabricated_recommendation(settings):
    # LLMを使わない決定的な経路で、空poolが空recommendationsのままであること。
    # （conftestのautouse fixtureはConciergeOrchestrator.suggestを固定応答へ
    #  差し替えるため、LLM経路ではその固定応答が観測されてしまう。ここでは
    #  gate直後の非LLM経路を固定する。LLM側のプレースホルダ生成そのものは
    #  下のtest_llm_orchestrator_...で塞いでいる。）
    settings.CONCIERGE_USE_LLM = False
    recs = build_chat_recommendations(query="近場で参拝したい", language="ja", candidates=[])
    assert recs.get("recommendations") == []



def test_llm_orchestrator_does_not_fabricate_a_shrine_from_an_empty_pool():
    from temples.llm.orchestrator import ConciergeOrchestrator

    assert ConciergeOrchestrator._fallback_from_candidates(
        ConciergeOrchestrator(), []
    ) == {"recommendations": []}


# --------------------------------------------------------------------------
# 8: Compass state separation
# --------------------------------------------------------------------------


def test_compass_evidence_zero_state_is_not_converted(monkeypatch):
    """direction/distanceは候補を残したのにRecommendationが0件になった場合、
    direction_zero_candidates / direction_filter_unavailable / fallbackへ
    変換せず STATE_EVIDENCE_ZERO_CANDIDATES を返す（state分離の維持）。"""
    attach_usable_deity_fact(_shrine("北の神社", latitude=35.2, longitude=135.0))

    monkeypatch.setattr(
        compass_orch, "build_chat_recommendations", lambda **kwargs: {"recommendations": []}
    )
    result = get_compass_recommendations(
        purpose="career", origin=ORIGIN, direction_context=NORTH_DIRECTION_CONTEXT
    )

    assert result.state == STATE_EVIDENCE_ZERO_CANDIDATES
    assert result.state != STATE_DIRECTION_FILTER_UNAVAILABLE
    assert result.direction_candidate_count == 1
    assert result.distance_candidate_count == 1
    assert result.recommendations == []


def test_compass_eligibility_removal_never_fabricates_or_reports_unavailable():
    """eligibility gateが候補を全て落とした場合、専用stateを返すだけで
    fallback推薦を作らず、direction_filter_unavailable（入力不正）にもしない。"""
    _shrine("北の不適格神社", latitude=35.2, longitude=135.0)

    result = get_compass_recommendations(
        purpose="career", origin=ORIGIN, direction_context=NORTH_DIRECTION_CONTEXT
    )

    assert result.state == STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES
    assert result.recommendations == []
    assert result.state != STATE_DIRECTION_FILTER_UNAVAILABLE
    assert result.state != STATE_RECOMMENDATION_SUCCESS


# --------------------------------------------------------------------------
# Compass zero-candidate state separation
# --------------------------------------------------------------------------


def test_all_source_candidates_ineligible_reports_eligibility_zero_state():
    # 1: 候補sourceは存在するが、全てeligibilityで除外される。
    for i in range(3):
        _shrine(f"不適格{i}", latitude=35.2 + i * 0.01, longitude=135.0)

    result = get_compass_recommendations(
        purpose="career", origin=ORIGIN, direction_context=NORTH_DIRECTION_CONTEXT
    )

    assert result.state == STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES
    assert result.state != STATE_DIRECTION_ZERO_CANDIDATES
    assert result.state != STATE_EVIDENCE_ZERO_CANDIDATES
    # このstateの成立条件は source_count > 0 AND eligible_count == 0。
    # 「Shrineが1件も無い」ではなくgateが落とした、と区別できる。
    assert result.source_candidate_count == 3
    assert result.source_candidate_count > 0
    assert result.eligible_candidate_count == 0
    # Direction / Distance stageへは到達していない。
    assert result.direction_candidate_count is None
    assert result.distance_candidate_count is None
    assert result.distance_stage_km is None


def test_no_source_candidates_is_not_classified_as_eligibility_failure():
    # 2: source_count == 0（候補sourceそのものが0件）はeligibility failureでは
    # ない。既存のzero-candidate flowへそのまま流し、新しいstateも追加しない。
    result = get_compass_recommendations(
        purpose="career", origin=ORIGIN, direction_context=NORTH_DIRECTION_CONTEXT
    )

    assert result.state != STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES
    assert result.state == STATE_DIRECTION_ZERO_CANDIDATES
    assert result.source_candidate_count == 0
    assert result.eligible_candidate_count == 0
    assert result.recommendations == []


def test_eligibility_zero_state_restores_no_ineligible_shrine():
    # 2: ineligibleなShrineは静かに復活しない。
    _shrine("北の不適格神社", latitude=35.2, longitude=135.0)

    result = get_compass_recommendations(
        purpose="career", origin=ORIGIN, direction_context=NORTH_DIRECTION_CONTEXT
    )

    assert result.state == STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES
    assert result.recommendations == []


def test_eligible_candidates_removed_by_direction_report_direction_zero():
    # 3: eligibleな候補は存在するが、方位で全て落ちる。
    attach_usable_deity_fact(_shrine("南の適格神社", latitude=34.8, longitude=135.0))

    result = get_compass_recommendations(
        purpose="career", origin=ORIGIN, direction_context=NORTH_DIRECTION_CONTEXT
    )

    assert result.state == STATE_DIRECTION_ZERO_CANDIDATES
    assert result.state != STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES
    assert result.eligible_candidate_count == 1
    assert result.direction_candidate_count == 0


def test_direction_candidates_but_no_recommendations_report_evidence_zero(monkeypatch):
    # 4: 方位候補は残ったが、Rankingが0件を返す。
    attach_usable_deity_fact(_shrine("北の適格神社", latitude=35.2, longitude=135.0))
    monkeypatch.setattr(
        compass_orch, "build_chat_recommendations", lambda **kwargs: {"recommendations": []}
    )

    result = get_compass_recommendations(
        purpose="career", origin=ORIGIN, direction_context=NORTH_DIRECTION_CONTEXT
    )

    assert result.state == STATE_EVIDENCE_ZERO_CANDIDATES
    assert result.state != STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES
    assert result.state != STATE_DIRECTION_ZERO_CANDIDATES
    assert result.eligible_candidate_count == 1
    assert result.direction_candidate_count == 1


def test_successful_flow_still_reports_recommendation_success():
    # 5: 成功パスは変わらない。
    attach_usable_deity_fact(_shrine("北の適格神社", latitude=35.2, longitude=135.0))

    result = get_compass_recommendations(
        purpose="career", origin=ORIGIN, direction_context=NORTH_DIRECTION_CONTEXT
    )

    assert result.state == STATE_RECOMMENDATION_SUCCESS
    assert result.recommendations
    assert result.eligible_candidate_count == 1


def test_all_four_zero_and_success_states_are_distinct_strings():
    states = {
        STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES,
        STATE_DIRECTION_ZERO_CANDIDATES,
        STATE_EVIDENCE_ZERO_CANDIDATES,
        STATE_DIRECTION_FILTER_UNAVAILABLE,
        STATE_RECOMMENDATION_SUCCESS,
    }
    assert len(states) == 5
    assert (
        STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES
        == "recommendation_eligibility_zero_candidates"
    )


def test_invalid_input_still_wins_over_eligibility_zero():
    # Group A（入力/runtime不成立）はGroup B（product result）より先。
    _shrine("不適格神社", latitude=35.2, longitude=135.0)

    result = get_compass_recommendations(
        purpose="career", origin=None, direction_context=NORTH_DIRECTION_CONTEXT
    )

    assert result.state == STATE_DIRECTION_FILTER_UNAVAILABLE
    assert result.state != STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES


def test_shared_builder_reports_eligibility_breakdown():
    attach_usable_deity_fact(_shrine("適格神社"))
    _shrine("不適格神社", latitude=35.01, longitude=139.01)

    built = build_chat_candidates_with_eligibility(
        lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="t"
    )

    assert built.source_count == 2
    assert built.eligible_count == 1
    assert built.ineligible_count == 1
    assert [c["name"] for c in built.candidates] == ["適格神社"]
    # 既存の公開APIは候補listのみを返す形のまま（Concierge側の呼び出しは不変）。
    assert build_chat_candidates(
        lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="t"
    ) == built.candidates


def test_compass_invalid_origin_still_reports_direction_filter_unavailable():
    attach_usable_deity_fact(_shrine("北の神社", latitude=35.2, longitude=135.0))
    result = get_compass_recommendations(
        purpose="career", origin=None, direction_context=NORTH_DIRECTION_CONTEXT
    )
    assert result.state == STATE_DIRECTION_FILTER_UNAVAILABLE


# --------------------------------------------------------------------------
# 9: Direction / Distance behaviour unchanged
# --------------------------------------------------------------------------


def test_direction_and_distance_results_for_eligible_shrines_are_unchanged_by_gate():
    """ineligibleなShrineがDBに増えても、eligibleなShrineのdirection/distance
    結果は変化しない（gateはdirection/distanceロジックに触れていない）。"""
    attach_usable_deity_fact(_shrine("適格北神社", latitude=35.2, longitude=135.0))

    before = get_compass_recommendations(
        purpose="career", origin=ORIGIN, direction_context=NORTH_DIRECTION_CONTEXT
    )

    for i in range(5):
        _shrine(f"不適格北神社{i}", latitude=35.21 + i * 0.01, longitude=135.0)

    after = get_compass_recommendations(
        purpose="career", origin=ORIGIN, direction_context=NORTH_DIRECTION_CONTEXT
    )

    assert before.state == after.state == STATE_RECOMMENDATION_SUCCESS
    assert before.direction_candidate_count == after.direction_candidate_count == 1
    assert before.distance_candidate_count == after.distance_candidate_count == 1
    assert before.distance_stage_km == after.distance_stage_km
    assert [r["name"] for r in before.recommendations] == [
        r["name"] for r in after.recommendations
    ]


def test_direction_filter_and_distance_stage_remain_pure_and_unmodified():
    candidates = [
        {"name": "北15km", "latitude": 35.1349, "longitude": 135.0, "distance_m": 15000},
        {"name": "北60km", "latitude": 35.5396, "longitude": 135.0, "distance_m": 60000},
        {"name": "北61km", "latitude": 35.5486, "longitude": 135.0, "distance_m": 60001},
        {"name": "南", "latitude": 34.5, "longitude": 135.0, "distance_m": 10000},
    ]
    filtered = filter_candidates_by_direction(
        candidates, origin=ORIGIN, reference_directions=["北"]
    )
    assert [c["name"] for c in filtered] == ["北15km", "北60km", "北61km"]

    staged, stage_km = _apply_compass_distance_stage(filtered)
    assert stage_km == compass_orch.DISTANCE_STAGE_3_KM
    assert [c["name"] for c in staged] == ["北15km", "北60km"]


# --------------------------------------------------------------------------
# 10: Ranking behaviour unchanged / eligibility is not a ranking signal
# --------------------------------------------------------------------------


def test_ranking_order_of_eligible_shrines_is_unchanged_by_the_gate():
    for name, score, lat in (("人気高", 100.0, 35.0), ("人気中", 50.0, 35.01), ("人気低", 1.0, 35.02)):
        shrine = Shrine.objects.create(
            name_jp=name,
            address="東京都千代田区1-1",
            latitude=lat,
            longitude=139.0,
            popular_score=score,
        )
        attach_usable_deity_fact(shrine)

    before = [
        r["name"]
        for r in build_chat_recommendations(
            query="近場で参拝したい",
            language="ja",
            candidates=build_chat_candidates(
                lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="t"
            ),
        )["recommendations"]
    ]

    for i in range(3):
        Shrine.objects.create(
            name_jp=f"不適格{i}",
            address="東京都千代田区1-1",
            latitude=35.0,
            longitude=139.0,
            popular_score=999.0,
        )

    after = [
        r["name"]
        for r in build_chat_recommendations(
            query="近場で参拝したい",
            language="ja",
            candidates=build_chat_candidates(
                lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="t"
            ),
        )["recommendations"]
    ]

    assert before == after
    assert all(not name.startswith("不適格") for name in after)


def test_eligibility_is_not_a_ranking_signal():
    # eligibilityはcandidate setの境界であり、scoreへは一切寄与しない。
    # 同一のeligibleな候補listを直接rankingへ渡した結果と、gateを通した
    # poolを渡した結果が一致することで、gateがscoreを変えていないことを示す。
    shrine = Shrine.objects.create(
        name_jp="単独適格神社",
        address="東京都千代田区1-1",
        latitude=35.0,
        longitude=139.0,
        popular_score=10.0,
    )
    attach_usable_deity_fact(shrine)
    pool = build_chat_candidates(
        lat=35.0, lng=139.0, area=None, goriyaku_tag_ids=None, trace_id="t"
    )

    gated = build_chat_recommendations(query="参拝したい", language="ja", candidates=pool)
    direct = build_chat_recommendations(
        query="参拝したい", language="ja", candidates=[dict(c) for c in pool]
    )

    assert [r["name"] for r in gated["recommendations"]] == [
        r["name"] for r in direct["recommendations"]
    ]
    assert [r.get("score") for r in gated["recommendations"]] == [
        r.get("score") for r in direct["recommendations"]
    ]


def test_eligibility_does_not_reference_f5_qualified_evidence():
    from temples.services import concierge_chat_candidates

    source = Path(concierge_chat_candidates.__file__).read_text(encoding="utf-8")
    for marker in (
        "qualify_evidence",
        "evaluate_evidence_qualification",
        "normalized_evidence",
        "EvidenceLink",
        "ShrineGoriyakuAssignment",
        "goriyaku_taxonomy_v1",
        "goriyaku_alias_v1",
    ):
        assert marker not in source, (
            f"shared eligibility must not depend on Evidence Foundation F5: {marker}"
        )


# --------------------------------------------------------------------------
# shrine browsing visibility is unaffected
# --------------------------------------------------------------------------


def test_ineligible_shrine_remains_visible_in_normal_shrine_browsing(client):
    ineligible = _shrine("閲覧可能な不適格神社")

    response = client.get(f"/api/shrines/{ineligible.id}/")

    assert response.status_code == 200
    assert response.json()["name_jp"] == "閲覧可能な不適格神社"
    assert "閲覧可能な不適格神社" not in _candidate_names()
