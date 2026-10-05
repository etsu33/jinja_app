"""Pre-G6 U2 (Mother Ship OPTION_T): Channel B Recommendation Meaning in the distance tier.

DISTANCE_TIER_MATCH = has_primary_tier_reason(_reason_facts)
                      OR _channel_b_request_need_keys(rec, request Needs) is non-empty

The Channel B part exists only while computing the distance sort key. Reason semantics
(_reason_facts / reason / PRIMARY_TIER_REASON_TYPES / claim strength), scores, U1 and the
public API are unchanged; a B-only candidate may stay explained as fallback.
"""

from __future__ import annotations

import copy
import json

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from temples.domain import source_fact_mapping_registry_v1 as registry_module
from temples.domain.source_fact_mapping_registry_v1 import SourceFactMappingRecord, build_registry
from temples.models import GoriyakuTag, Shrine, ShrineKnowledgeSource, ShrineSourceFact
from temples.services.channel_b_typed_need_match import (
    CHANNEL_B_TYPED_NEED_MATCHES_KEY,
    TypedNeedMatch,
)
from temples.services.concierge_chat import _sort_chat_recommendations, build_chat_recommendations
from temples.services.concierge_chat_candidates import build_chat_candidates_with_eligibility
from temples.services.concierge_chat_ranking import (
    _attach_breakdown,
    has_primary_tier_reason,
    resolve_score_sort_key,
)
from temples.tests.support.recommendation_eligibility import attach_usable_deity_fact
from temples.tests.test_bootstrap_goriyaku_master_exact39_contract import CANONICAL_MASTER

WEIGHTS = {"element": 0.6, "need": 0.3, "popular": 0.1, "distance": 0.0}
PRAYER = "official_prayer_supported"
GUIDANCE = "official_current_guidance_supported"
COMBINED = "official_prayer_and_current_guidance_list_level"
DISTANCE = {"sort_distance"}
CANONICAL_ID_BY_NAME = {name: tag_id for tag_id, name in CANONICAL_MASTER}


def _m(need: str, signal: str = PRAYER) -> TypedNeedMatch:
    return TypedNeedMatch(need, "x", signal, f"k-{need}-{signal}", "x")


def _cand(name: str, *b_needs: str, distance: float, signal: str = PRAYER, **fields) -> dict:
    row = {
        "id": sum(map(ord, name)),
        "shrine_id": sum(map(ord, name)),
        "name": name,
        "goriyaku": "",
        "description": "",
        "astro_tags": [],
        "goriyaku_tag_ids": [],
        "popular_score": 0.0,
        "distance_m": float(distance),
    }
    row.update(fields)
    if b_needs:
        row[CHANNEL_B_TYPED_NEED_MATCHES_KEY] = tuple(_m(n, signal) for n in b_needs)
    return row


def _score(rows: list[dict], needs: list[str]) -> list[dict]:
    for r in rows:
        _attach_breakdown(
            r, birthdate=None, need_tags=needs, weights=WEIGHTS, astro_bonus_enabled=False
        )
    return rows


def _order(rows, needs, sort_tags=DISTANCE) -> list[str]:
    recs = _sort_chat_recommendations(
        {"recommendations": list(rows)}, sort_tags=sort_tags, need_tags=needs
    )
    return [r["name"] for r in recs["recommendations"]]


def _reference_distance_order(rows) -> list[str]:
    """develop の distance branch（_reason_facts だけの tier）をそのまま写したもの。"""
    ordered = sorted(
        rows,
        key=lambda r: (
            0 if has_primary_tier_reason(r.get("_reason_facts")) else 1,
            float(r.get("distance_m") or 1e12),
            -resolve_score_sort_key(r, score_v3_mode="shadow"),
            str(r.get("name") or ""),
        ),
    )
    return [r["name"] for r in ordered]


# ---------- U2-A〜H ----------


@pytest.mark.django_db
def test_u2_a_far_channel_a_vs_near_b_only_distance_decides():
    needs = ["money"]
    rows = _score(
        [
            _cand("A_money_far", distance=500, goriyaku_tag_ids=[4]),
            _cand("B_money_near", "money", distance=100),
        ],
        needs,
    )
    assert _reference_distance_order(rows) == ["A_money_far", "B_money_near"]
    assert _order(rows, needs) == ["B_money_near", "A_money_far"]


@pytest.mark.django_db
def test_u2_b_b_only_is_recommendation_meaning_tier_no_need_is_not():
    needs = ["money"]
    rows = _score(
        [_cand("N_no_need", distance=100), _cand("B_money", "money", distance=110)], needs
    )
    assert _reference_distance_order(rows) == ["N_no_need", "B_money"]
    assert _order(rows, needs) == ["B_money", "N_no_need"]


@pytest.mark.django_db
def test_u2_c_near_b_only_is_no_longer_excluded_from_top3():
    needs = ["money", "study"]
    rows = _score(
        [
            _cand("B_study_near", "study", distance=50),
            _cand("A_money_1", distance=900, goriyaku_tag_ids=[4]),
            _cand("A_money_2", distance=950, goriyaku_tag_ids=[4]),
            _cand("A_study_far", distance=990, goriyaku_tag_ids=[9]),
        ],
        needs,
    )
    assert "B_study_near" not in _reference_distance_order(rows)[:3]
    assert _order(rows, needs)[:3] == ["B_study_near", "A_money_1", "A_money_2"]


@pytest.mark.django_db
def test_u2_d_mixed_a_and_b_stays_tier0_without_mutation():
    needs = ["money", "study"]
    rows = _score(
        [
            _cand("AB", "study", distance=300, goriyaku_tag_ids=[4]),
            _cand("N", distance=10),
        ],
        needs,
    )
    snapshot = copy.deepcopy(rows)
    assert _order(rows, needs) == ["AB", "N"]
    assert rows == snapshot
    assert [f["type"] for f in rows[0]["_reason_facts"]] == ["goriyaku_tag"]


@pytest.mark.django_db
@pytest.mark.parametrize("signal", [PRAYER, GUIDANCE, COMBINED])
def test_u2_e_f_every_valid_characterization_joins_the_same_binary_tier(signal):
    needs = ["money"]
    rows = _score(
        [
            _cand("N_near", distance=10),
            _cand("A_money_far", distance=900, goriyaku_tag_ids=[4]),
            _cand("B_money", "money", distance=100, signal=signal),
        ],
        needs,
    )
    assert _order(rows, needs) == ["B_money", "A_money_far", "N_near"]
    b = rows[2]
    # reason semantics / claim strength unchanged: still fallback, never goriyaku_tag / need_tag.
    types = [f["type"] for f in b["_reason_facts"]]
    assert "goriyaku_tag" not in types and "need_tag" not in types
    assert not has_primary_tier_reason(b["_reason_facts"])


@pytest.mark.django_db
@pytest.mark.parametrize("carrier", ["absent", "empty"])
def test_u2_g_without_channel_b_matches_previous_develop(carrier):
    needs = ["money", "study"]
    rows = [
        _cand("A_money_far", distance=900, goriyaku_tag_ids=[4]),
        _cand("A_text_mid", distance=500, goriyaku="金運"),
        _cand("N_near", distance=10),
        _cand("A_money_near", distance=100, goriyaku_tag_ids=[4]),
        _cand("N_far", distance=2000),
    ]
    if carrier == "empty":
        for r in rows:
            r[CHANNEL_B_TYPED_NEED_MATCHES_KEY] = ()
    rows = _score(rows, needs)
    assert _order(rows, needs) == _reference_distance_order(rows)
    assert _order(rows, None) == _reference_distance_order(rows)


@pytest.mark.django_db
def test_u2_h_same_tier_and_distance_keeps_score_tie_break():
    needs = ["money", "study"]
    rows = _score(
        [
            _cand("A_money_same", distance=100, goriyaku_tag_ids=[4]),
            _cand("B_study_same", "study", distance=100),
            _cand("AB_same", "study", distance=100, goriyaku_tag_ids=[4]),
        ],
        needs,
    )
    scores = {r["name"]: r["_score_total"] for r in rows}
    expected = sorted(scores, key=lambda n: (-scores[n], n))
    assert _order(rows, needs) == expected


# ---------- request boundary / 入力 ----------


@pytest.mark.django_db
def test_b_need_outside_request_is_ignored():
    needs = ["money"]
    rows = _score([_cand("N_near", distance=10), _cand("B_career", "career", distance=100)], needs)
    assert _order(rows, needs) == _reference_distance_order(rows) == ["N_near", "B_career"]


@pytest.mark.django_db
def test_exact_need_equality_without_alias_normalization():
    needs = ["money"]
    rows = _score(
        [_cand("N_near", distance=10), _cand("B_alias", "fortune", "Money", distance=100)],
        needs,
    )
    assert _order(rows, needs) == ["N_near", "B_alias"]


@pytest.mark.django_db
@pytest.mark.parametrize("bad", ["money", 3, ({"need": "money"},), (None,), [None, "money"]])
def test_malformed_carrier_is_ignored(bad):
    needs = ["money"]
    rows = _score([_cand("N_near", distance=10), _cand("B_bad", distance=100)], needs)
    rows[1][CHANNEL_B_TYPED_NEED_MATCHES_KEY] = bad
    assert _order(rows, needs) == ["N_near", "B_bad"]


@pytest.mark.django_db
def test_non_distance_order_is_unchanged_by_u2():
    needs = ["money", "study"]
    rows = _score(
        [
            _cand("B_study", "study", distance=50),
            _cand("A_money", distance=900, goriyaku_tag_ids=[4]),
            _cand("N", distance=10),
        ],
        needs,
    )
    from temples.services.concierge_chat_ranking import _diversify_by_need

    expected = [
        r["name"]
        for r in _diversify_by_need(
            sorted(
                rows,
                key=lambda r: (
                    -resolve_score_sort_key(r, score_v3_mode="shadow"),
                    float(r["distance_m"]),
                    r["name"],
                ),
            ),
            limit=3,
            need_tags=needs,
        )
    ]
    assert _order(rows, needs, sort_tags=set()) == expected


@pytest.mark.django_db
def test_distance_sort_mutates_nothing_and_issues_no_query():
    needs = ["money", "study"]
    rows = _score(
        [
            _cand("B_study", "study", distance=50),
            _cand("A_money", distance=900, goriyaku_tag_ids=[4]),
            _cand("N", distance=10),
        ],
        needs,
    )
    snapshot = copy.deepcopy(rows)
    with CaptureQueriesContext(connection) as ctx:
        _order(rows, needs)
    assert len(ctx) == 0
    assert rows == snapshot  # _reason_facts / reason / matched_* / breakdown / scores / carrier


# ---------- 統合（build_chat_recommendations / 公開 response / LLM） ----------


def _tag(name: str) -> GoriyakuTag:
    tag, _ = GoriyakuTag.objects.get_or_create(id=CANONICAL_ID_BY_NAME[name], name=name)
    return tag


def _shrine(name: str, lat: float) -> Shrine:
    shrine = Shrine.objects.create(
        name_jp=name, kind="shrine", address="東京都試験区8-8-8", latitude=lat, longitude=139.0
    )
    attach_usable_deity_fact(shrine)
    return shrine


def _fact(shrine: Shrine, key: str, wording: str) -> None:
    fact = ShrineSourceFact.objects.create(
        shrine=shrine,
        stable_key=key,
        source_attested_wording=wording,
        evidence_characterization=PRAYER,
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
def test_end_to_end_distance_query_keeps_near_b_only_in_top3(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    for name in ("商売繁盛", "学業成就"):
        _tag(name)
    for i, lat in enumerate((35.05, 35.06, 35.07)):
        far = _shrine(f"遠方A{i}", lat)
        far.goriyaku_tags.add(_tag("商売繁盛"))
    near_b = _shrine("近接B神社", 35.0005)
    _fact(near_b, "u2-0001", "学業成就")
    _install(monkeypatch, ("u2-0001", "学業成就"))

    candidates = build_chat_candidates_with_eligibility(
        lat=35.0, lng=139.0, area=None, trace_id="t"
    ).candidates
    recs = build_chat_recommendations(
        query="近い神社",
        language="ja",
        candidates=candidates,
        bias={"lat": 35.0, "lng": 139.0},
        need_tags=["money", "study"],
        public_mode="need",
        flow="A",
        llm_enabled=False,
    )
    names = [r["name"] for r in recs["recommendations"]]
    assert names[0] == "近接B神社"
    row = recs["recommendations"][0]
    assert row["breakdown"]["matched_need_tags"] == []
    assert row["breakdown"]["score_need"] == 0
    assert not has_primary_tier_reason(row.get("_reason_facts"))
    assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in row


@pytest.mark.django_db
def test_carrier_still_absent_from_public_response(client, monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    _tag("金運")
    shrine = _shrine("公開距離神社", 35.0005)
    _fact(shrine, "u2-0100", "金運祈願")
    _install(monkeypatch, ("u2-0100", "金運"))
    response = client.post(
        "/api/concierge/chat/",
        data=json.dumps({"query": "近くで金運", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert response.status_code == 200
    raw = json.dumps(response.json(), ensure_ascii=False)
    assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in raw
    assert "_channel_b_reason_provenance" not in raw
    assert "source_fact_key" not in raw
    assert "u2-0100" not in raw
    # MS-5: source wording は Source-backed の理由文の中にだけ現れる（carrier としては出ない）。
    reason = next(
        r for r in response.json()["data"]["recommendations"] if r.get("name") == "公開距離神社"
    )["reason"]
    assert "『金運祈願』" in reason
    assert "金運祈願" not in raw.replace(reason, "")


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
        query="近くで金運",
        valid_candidates=[_cand("B", "money", distance=10)],
        need_tags=["money"],
        llm_enabled=True,
    )
    assert received and all(CHANNEL_B_TYPED_NEED_MATCHES_KEY not in c for c in received)
