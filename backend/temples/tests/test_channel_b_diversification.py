"""Pre-G6 U1: Channel B の Need 被覆を多様化（_diversify_by_need）で数える。

Mother Ship decision:
    DIVERSIFICATION_CHANNEL_B_POLICY = COUNT_AS_NEED_COVERAGE
    DIVERSIFICATION_COVERAGE = CHANNEL_A_MATCHED_NEEDS ∪ CHANNEL_B_REQUEST_NEED_KEYS

和集合は多様化の判断の中だけで使い、matched_all / matched_need_tags / 数値 / 理由文 /
carrier には書き戻さない。Channel B が無ければ、従来の Channel A だけの挙動と同じ。
"""

from __future__ import annotations

import copy
import json
from typing import Any, Dict, List, Optional

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from temples.domain import source_fact_mapping_registry_v1 as registry_module
from temples.domain.source_fact_mapping_registry_v1 import SourceFactMappingRecord, build_registry
from temples.models import GoriyakuTag, Shrine, ShrineKnowledgeSource, ShrineSourceFact
from temples.services import concierge_chat
from temples.services.channel_b_typed_need_match import (
    CHANNEL_B_TYPED_NEED_MATCHES_KEY,
    TypedNeedMatch,
)
from temples.services.concierge_chat import _sort_chat_recommendations, build_chat_recommendations
from temples.services.concierge_chat_candidates import build_chat_candidates_with_eligibility
from temples.services.concierge_chat_ranking import _attach_breakdown, _diversify_by_need
from temples.tests.support.recommendation_eligibility import attach_usable_deity_fact
from temples.tests.test_bootstrap_goriyaku_master_exact39_contract import CANONICAL_MASTER

WEIGHTS = {"element": 0.6, "need": 0.3, "popular": 0.1, "distance": 0.0}
CANONICAL_ID_BY_NAME = {name: tag_id for tag_id, name in CANONICAL_MASTER}


# ---------- reference: develop の _diversify_by_need（Channel A だけ）をそのまま写したもの ----------


def _reference_diversify(recs: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    pool = [r for r in recs if isinstance(r, dict)]
    if len(pool) <= 1:
        return pool
    picked: List[Dict[str, Any]] = []
    used_tags: set[str] = set()
    while pool and len(picked) < limit:
        best_index: Optional[int] = None
        for i, r in enumerate(pool):
            tags = (r.get("breakdown") or {}).get("matched_need_tags") or []
            normalized = [str(t).strip() for t in tags if isinstance(t, str) and str(t).strip()]
            if not normalized:
                continue
            if any(t not in used_tags for t in normalized):
                best_index = i
                break
        if best_index is None:
            best_index = 0
        row = pool.pop(best_index)
        picked.append(row)
        tags = (row.get("breakdown") or {}).get("matched_need_tags") or []
        used_tags.update(str(t).strip() for t in tags if isinstance(t, str) and str(t).strip())
    picked.extend(pool)
    return picked


# ---------- helpers ----------


def _m(need: str, concept: str = "x") -> TypedNeedMatch:
    return TypedNeedMatch(need, concept, "official_prayer_supported", f"k-{need}", concept)


def _cand(name: str, *b_needs: str, **fields) -> dict:
    row = {
        "id": sum(ord(c) for c in name),
        "shrine_id": sum(ord(c) for c in name),
        "name": name,
        "goriyaku": "",
        "description": "",
        "astro_tags": [],
        "goriyaku_tag_ids": [],
        "popular_score": 0.0,
        "distance_m": 100.0,
    }
    row.update(fields)
    if b_needs:
        row[CHANNEL_B_TYPED_NEED_MATCHES_KEY] = tuple(_m(n) for n in b_needs)
    return row


def _score(rows: list[dict], needs: list[str]) -> list[dict]:
    for r in rows:
        _attach_breakdown(
            r, birthdate=None, need_tags=needs, weights=WEIGHTS, astro_bonus_enabled=False
        )
    return rows


def _order(rows: list[dict], needs: list[str] | None, sort_tags: set[str] | None = None):
    recs = _sort_chat_recommendations(
        {"recommendations": list(rows)}, sort_tags=sort_tags or set(), need_tags=needs
    )
    return [r["name"] for r in recs["recommendations"]]


def _pre_order(rows: list[dict]) -> list[str]:
    return [
        r["name"]
        for r in sorted(rows, key=lambda r: (-r["_score_total"], r["distance_m"], r["name"]))
    ]


def _frozen_numbers(rows: list[dict]) -> dict:
    out = {}
    for r in rows:
        need = r["breakdown_detail"]["features"]["need"]
        out[r["name"]] = (
            list(r["breakdown"]["matched_need_tags"]),
            r["breakdown"]["score_need"],
            need["rank_raw"],
            need["rank_weighted"],
            r["_score_total"],
            r.get("reason"),
            r.get("_reason_facts"),
        )
    return out


# ---------- U1-A〜U1-F ----------


@pytest.mark.django_db
def test_u1_a_channel_b_study_is_recognized_as_coverage():
    needs = ["money", "study"]
    rows = _score(
        [
            _cand("A_money_A", goriyaku_tag_ids=[4], popular_score=50),
            _cand("B_study_B", "study", popular_score=40),
            _cand("D_study_A_low", goriyaku_tag_ids=[9], distance_m=300.0),
        ],
        needs,
    )
    b = next(r for r in rows if r["name"] == "B_study_B")
    d = next(r for r in rows if r["name"] == "D_study_A_low")
    assert b["_score_total"] > d["_score_total"]
    # 修正前は D が B より前に上がっていた。
    assert _order(rows, None) == ["A_money_A", "D_study_A_low", "B_study_B"]
    assert _order(rows, needs) == ["A_money_A", "B_study_B", "D_study_A_low"]


@pytest.mark.django_db
def test_u1_a2_top_ranked_b_only_candidate_stays_in_top3():
    needs = ["money", "study", "protection"]
    rows = _score(
        [
            _cand("A_money_A", goriyaku_tag_ids=[4]),
            _cand("B_study_protection", "study", "protection"),
            _cand("D_study_A_low", goriyaku_tag_ids=[9], distance_m=300.0),
            _cand("G_protection_A_low", goriyaku_tag_ids=[2], distance_m=400.0),
        ],
        needs,
    )
    assert _pre_order(rows)[0] == "B_study_protection"
    assert "B_study_protection" not in _order(rows, None)[:3]  # 修正前の挙動
    assert _order(rows, needs)[:3] == ["B_study_protection", "A_money_A", "D_study_A_low"]


@pytest.mark.django_db
def test_u1_b_distinguishes_different_channel_b_needs():
    needs = ["money", "study"]
    rows = _score(
        [
            _cand("B_money_1", "money", distance_m=100.0),
            _cand("B_money_2", "money", distance_m=200.0),
            _cand("B_study", "study", distance_m=300.0),
        ],
        needs,
    )
    assert _order(rows, None) == ["B_money_1", "B_money_2", "B_study"]
    assert _order(rows, needs) == ["B_money_1", "B_study", "B_money_2"]


@pytest.mark.django_db
def test_u1_c_mixed_a_and_b_cover_both_needs_transiently():
    needs = ["money", "study"]
    rows = _score(
        [
            _cand("AB_money_A_study_B", "study", goriyaku_tag_ids=[4]),
            _cand("A_money_2", goriyaku_tag_ids=[4], distance_m=200.0),
            _cand("A_study_low", goriyaku_tag_ids=[9], distance_m=300.0),
        ],
        needs,
    )
    ab = rows[0]
    assert ab["breakdown"]["matched_need_tags"] == ["money"]
    # 修正前は study が未被覆と見なされ、低い A_study_low が上がっていた。
    assert _order(rows, None) == ["AB_money_A_study_B", "A_study_low", "A_money_2"]
    assert _order(rows, needs) == ["AB_money_A_study_B", "A_money_2", "A_study_low"]
    # matched_need_tags は Channel A のまま。
    assert ab["breakdown"]["matched_need_tags"] == ["money"]


@pytest.mark.django_db
def test_u1_d_equal_rank_weighted_prefers_new_channel_b_need():
    needs = ["money", "study"]
    rows = _score(
        [
            _cand("A_money_top", goriyaku_tag_ids=[4], distance_m=50.0),
            _cand("B_money", "money", distance_m=100.0),
            _cand("B_study", "study", distance_m=200.0),
        ],
        needs,
    )
    rw = {r["name"]: r["breakdown_detail"]["features"]["need"]["rank_weighted"] for r in rows}
    assert rw["B_money"] == rw["B_study"] == 2.0
    assert _order(rows, None) == ["A_money_top", "B_money", "B_study"]
    assert _order(rows, needs) == ["A_money_top", "B_study", "B_money"]


@pytest.mark.django_db
@pytest.mark.parametrize("carrier", ["absent", "empty"])
def test_u1_e_without_channel_b_matches_develop_reference(carrier):
    needs = ["money", "study", "protection"]
    pools = [
        [
            _cand("A1", goriyaku_tag_ids=[4]),
            _cand("A2", goriyaku_tag_ids=[4], distance_m=200.0),
            _cand("A3", goriyaku_tag_ids=[9], distance_m=300.0),
            _cand("A4", goriyaku_tag_ids=[2], distance_m=400.0),
            _cand("N1", distance_m=500.0),
        ],
        [
            _cand("N1"),
            _cand("A1", goriyaku_tag_ids=[4, 9], distance_m=200.0),
            _cand("A2", goriyaku="金運", distance_m=300.0),
        ],
    ]
    for pool in pools:
        if carrier == "empty":
            for r in pool:
                r[CHANNEL_B_TYPED_NEED_MATCHES_KEY] = ()
        rows = _score(pool, needs)
        sorted_rows = sorted(rows, key=lambda r: (-r["_score_total"], r["distance_m"], r["name"]))
        expected = [r["name"] for r in _reference_diversify(sorted_rows, limit=3)]
        assert _order(rows, needs) == expected
        assert _order(rows, None) == expected


@pytest.mark.django_db
def test_u1_f_compass_like_one_need_b_only_top_is_not_demoted():
    needs = ["money"]
    rows = _score(
        [
            _cand("B_money_only", "money", distance_m=50.0),
            _cand("A_money_low", goriyaku_tag_ids=[4], distance_m=300.0),
            _cand("A_money_low2", goriyaku_tag_ids=[4], distance_m=400.0),
        ],
        needs,
    )
    rows[0]["_score_total"] += 0.5
    assert _order(rows, None) == ["A_money_low", "B_money_only", "A_money_low2"]
    assert _order(rows, needs) == ["B_money_only", "A_money_low", "A_money_low2"]


# ---------- request boundary / 入力 ----------


@pytest.mark.django_db
def test_channel_b_need_outside_request_is_ignored():
    needs = ["money"]
    rows = _score(
        [
            _cand("A_money", goriyaku_tag_ids=[4]),
            _cand("A_money_2", goriyaku_tag_ids=[4], distance_m=200.0),
            _cand("B_career", "career", distance_m=300.0),
        ],
        needs,
    )
    assert _order(rows, needs) == _order(rows, None)


@pytest.mark.django_db
def test_exact_equality_without_alias_normalization():
    needs = ["money", "study"]
    rows = _score(
        [
            _cand("A_money", goriyaku_tag_ids=[4]),
            _cand("A_money_2", goriyaku_tag_ids=[4], distance_m=200.0),
            _cand("B_alias", "fortune", "Study", " study", distance_m=300.0),
        ],
        needs,
    )
    assert _order(rows, needs) == _order(rows, None)


@pytest.mark.django_db
def test_malformed_carrier_is_ignored():
    needs = ["money", "study"]
    rows = _score(
        [
            _cand("A_money", goriyaku_tag_ids=[4]),
            _cand("A_money_2", goriyaku_tag_ids=[4], distance_m=200.0),
            _cand("B_bad", distance_m=300.0),
        ],
        needs,
    )
    for bad in ("study", 3, ({"need": "study"},), (None,), [None, "study"]):
        rows[2][CHANNEL_B_TYPED_NEED_MATCHES_KEY] = bad
        assert _order(rows, needs) == _order(rows, None)


@pytest.mark.django_db
def test_coverage_calculation_issues_no_db_query():
    needs = ["money", "study"]
    rows = _score(
        [_cand("A", goriyaku_tag_ids=[4]), _cand("B", "study"), _cand("C", "money")], needs
    )
    with CaptureQueriesContext(connection) as ctx:
        _diversify_by_need(rows, limit=3, need_tags=needs)
    assert len(ctx) == 0


@pytest.mark.django_db
def test_diversification_mutates_nothing():
    needs = ["money", "study", "protection"]
    rows = _score(
        [
            _cand("AB", "study", goriyaku_tag_ids=[4]),
            _cand("B", "study", "protection", distance_m=200.0),
            _cand("A", goriyaku_tag_ids=[9], distance_m=300.0),
        ],
        needs,
    )
    snapshot = copy.deepcopy(rows)
    numbers = _frozen_numbers(rows)
    _order(rows, needs)
    assert rows == snapshot
    assert _frozen_numbers(rows) == numbers
    assert rows[0]["breakdown"]["matched_need_tags"] == ["money"]
    assert {m.need for m in rows[0][CHANNEL_B_TYPED_NEED_MATCHES_KEY]} == {"study"}


@pytest.mark.django_db
def test_distance_mode_is_unchanged():
    needs = ["money", "study", "protection"]
    rows = _score(
        [
            _cand("A_money_A", goriyaku_tag_ids=[4], distance_m=300.0),
            _cand("B_study_protection", "study", "protection", distance_m=100.0),
            _cand("D_study_A_low", goriyaku_tag_ids=[9], distance_m=200.0),
        ],
        needs,
    )
    # U1 の多様化は distance mode では使われない（tier 内は距離順のまま）。
    # Pre-G6 U2（OPTION_T）以降、request Need に一致する Channel B は distance tier 0 に入る。
    assert _order(rows, needs, {"sort_distance"}) == [
        "B_study_protection",
        "D_study_A_low",
        "A_money_A",
    ]
    assert _order(rows, None, {"sort_distance"}) == [
        "D_study_A_low",
        "A_money_A",
        "B_study_protection",
    ]


# ---------- 統合（build_chat_recommendations / 公開 response / LLM） ----------


def _tag(name: str) -> GoriyakuTag:
    tag, _ = GoriyakuTag.objects.get_or_create(id=CANONICAL_ID_BY_NAME[name], name=name)
    return tag


def _shrine(name: str, *, lat_offset: float = 0.0) -> Shrine:
    shrine = Shrine.objects.create(
        name_jp=name,
        kind="shrine",
        address="東京都試験区7-7-7",
        latitude=35.0 + lat_offset,
        longitude=139.0,
    )
    attach_usable_deity_fact(shrine)
    return shrine


def _fact(shrine: Shrine, key: str, wording: str) -> None:
    fact = ShrineSourceFact.objects.create(
        shrine=shrine,
        stable_key=key,
        source_attested_wording=wording,
        evidence_characterization="official_prayer_supported",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    fact.sources.add(
        ShrineKnowledgeSource.objects.create(
            source_type="shrine_official",
            title="案内",
            verification_status="source_confirmed",
            verified_at=timezone.now(),
        )
    )


def _install(monkeypatch, *pairs):
    records = tuple(
        SourceFactMappingRecord(
            source_fact_key=k, canonical_concept_name=c, mapping_classification="EXACT"
        )
        for k, c in pairs
    )
    monkeypatch.setattr(registry_module, "_default_registry", build_registry(records))


@pytest.mark.django_db
def test_build_chat_recommendations_passes_request_needs_and_keeps_numbers(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    for name in ("商売繁盛", "学業成就", "厄除け"):
        _tag(name)
    a_money = _shrine("全体A金運神社")
    a_money.goriyaku_tags.add(_tag("商売繁盛"))
    a_study = _shrine("全体A学業神社", lat_offset=0.01)
    a_study.goriyaku_tags.add(_tag("学業成就"))
    a_protect = _shrine("全体A厄除神社", lat_offset=0.02)
    a_protect.goriyaku_tags.add(_tag("厄除け"))
    b_only = _shrine("全体B神社", lat_offset=0.005)
    _fact(b_only, "div-0001", "学業成就")
    _fact(b_only, "div-0002", "厄除け")
    _install(monkeypatch, ("div-0001", "学業成就"), ("div-0002", "厄除け"))

    seen: list = []
    original = concierge_chat._diversify_by_need

    def _spy(recs, limit=3, need_tags=None):
        seen.append(list(need_tags or []))
        return original(recs, limit=limit, need_tags=need_tags)

    monkeypatch.setattr(concierge_chat, "_diversify_by_need", _spy)
    candidates = build_chat_candidates_with_eligibility(
        lat=35.0, lng=139.0, area=None, trace_id="t"
    ).candidates
    recs = build_chat_recommendations(
        query="",
        language="ja",
        candidates=candidates,
        bias={"lat": 35.0, "lng": 139.0},
        need_tags=["money", "study", "protection"],
        public_mode="need",
        flow="A",
        llm_enabled=False,
    )
    assert seen == [["money", "study", "protection"]]
    names = [r["name"] for r in recs["recommendations"]]
    assert "全体B神社" in names[:3]
    b_row = next(r for r in recs["recommendations"] if r["name"] == "全体B神社")
    assert b_row["breakdown"]["matched_need_tags"] == []
    assert b_row["breakdown"]["score_need"] == 0
    assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in b_row


@pytest.mark.django_db
def test_carrier_still_absent_from_public_response(client, monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    _tag("金運")
    shrine = _shrine("公開多様化神社")
    _fact(shrine, "div-0100", "金運祈願")
    _install(monkeypatch, ("div-0100", "金運"))
    response = client.post(
        "/api/concierge/chat/",
        data=json.dumps({"query": "金運を上げたい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert response.status_code == 200
    raw = json.dumps(response.json(), ensure_ascii=False)
    assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in raw
    assert "div-0100" not in raw
    assert "金運祈願" not in raw


@pytest.mark.django_db
def test_carrier_still_excluded_from_llm_input(monkeypatch, settings):
    from temples.llm import orchestrator as orch_mod
    from temples.services.concierge_chat_llm_route import resolve_llm_route

    received: list = []

    class _FakeOrchestrator:
        def suggest(self, *, query, candidates):
            received.extend(candidates)
            return {"recommendations": [dict(c) for c in candidates]}

    monkeypatch.setattr(orch_mod, "ConciergeOrchestrator", _FakeOrchestrator)
    settings.CONCIERGE_USE_LLM = True
    resolve_llm_route(
        query="金運",
        valid_candidates=[_cand("B", "money")],
        need_tags=["money"],
        llm_enabled=True,
    )
    assert received and all(CHANNEL_B_TYPED_NEED_MATCHES_KEY not in c for c in received)
