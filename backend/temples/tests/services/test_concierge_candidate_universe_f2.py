"""Pre-G6 F2 (F2-C, Concierge only): 候補母集団を Recommendation relevance より前に正しく作る。

Concierge Stage 1:
    構造条件 -> 明示条件（area / goriyaku_tag_ids）-> Shared Recommendation Eligibility
    -> 人気順の件数上限で membership を切らない

旧挙動では order_by("-popular_score", "id")[:100] が gate / 距離 / request relevance より前に
効き、人気上位100件の外の Shrine は条件に関係なく Recommendation へ到達しなかった。
Compass（build_chat_candidates_with_eligibility の既定）は別 PR で扱うため、この file では
既定が従来どおりであることも固定する。
"""

from __future__ import annotations

import json

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from temples.domain import source_fact_mapping_registry_v1 as registry_module
from temples.domain.source_fact_mapping_registry_v1 import SourceFactMappingRecord, build_registry
from temples.models import GoriyakuTag, Shrine, ShrineKnowledgeSource, ShrineSourceFact
from temples.services.channel_b_typed_need_match import CHANNEL_B_TYPED_NEED_MATCHES_KEY
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_candidates import (
    build_chat_candidates,
    build_chat_candidates_with_eligibility,
)
from temples.tests.support.recommendation_eligibility import (
    attach_usable_deity_fact,
    create_fact_ready_source,
)
from temples.tests.test_bootstrap_goriyaku_master_exact39_contract import CANONICAL_MASTER

ID_BY_NAME = {name: tag_id for tag_id, name in CANONICAL_MASTER}
ORIGIN = {"lat": 35.0, "lng": 139.0}
OLD_CONCIERGE_POOL = 100  # 旧 pool_limit = max(DEFAULT_LIMIT(20) * 5, 50)
TARGET = "対象神社"


def _tag(name: str) -> GoriyakuTag:
    tag, _ = GoriyakuTag.objects.get_or_create(id=ID_BY_NAME[name], name=name)
    return tag


def _fillers(
    n: int, *, eligible: bool = True, address: str = "東京都試験区1-1-1", prefix: str = "人気"
) -> list[Shrine]:
    """人気の高い（旧 pool の上位を占める）関連性なしの Shrine を n 件作る。"""
    rows = Shrine.objects.bulk_create(
        [
            Shrine(
                name_jp=f"{prefix}{i:04d}",
                kind="shrine",
                address=address,
                latitude=35.2 + i * 0.001,
                longitude=139.0,
                popular_score=1000.0 - i,
            )
            for i in range(n)
        ]
    )
    if eligible:
        source = create_fact_ready_source()
        for shrine in rows:
            attach_usable_deity_fact(shrine, source=source)
    return rows


def _target(
    *, lat: float = 36.5, address: str = "東京都試験区9-9-9", goriyaku: str = "", eligible=True
) -> Shrine:
    """旧 pool の外に落ちる（popular_score=0.0、id 最大）対象 Shrine。"""
    shrine = Shrine.objects.create(
        name_jp=TARGET,
        kind="shrine",
        address=address,
        latitude=lat,
        longitude=139.0,
        popular_score=0.0,
        goriyaku=goriyaku,
    )
    if eligible:
        attach_usable_deity_fact(shrine)
    return shrine


def _channel_b(monkeypatch, shrine: Shrine, concept: str = "商売繁盛") -> None:
    _tag(concept)
    fact = ShrineSourceFact.objects.create(
        shrine=shrine,
        stable_key="f2-0001",
        source_attested_wording=concept,
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
    monkeypatch.setattr(
        registry_module,
        "_default_registry",
        build_registry(
            (
                SourceFactMappingRecord(
                    source_fact_key="f2-0001",
                    canonical_concept_name=concept,
                    mapping_classification="EXACT",
                ),
            )
        ),
    )


def _names(cands) -> list[str]:
    return [c["name"] for c in cands]


def _concierge(query: str, *, need_tags=None, with_location: bool = True) -> list[str]:
    candidates = build_chat_candidates(
        lat=ORIGIN["lat"] if with_location else None,
        lng=ORIGIN["lng"] if with_location else None,
        trace_id="f2",
    )
    recs = build_chat_recommendations(
        query=query,
        language="ja",
        candidates=candidates,
        bias=dict(ORIGIN) if with_location else None,
        need_tags=need_tags,
        public_mode="need",
        flow="A",
        llm_enabled=False,
    )
    return [r["name"] for r in recs["recommendations"]]


@pytest.fixture(autouse=True)
def _no_llm(settings):
    settings.CONCIERGE_USE_LLM = False


# ---------- A〜E: 旧 popularity top 100 の外にいる候補が Recommendation へ到達する ----------


@pytest.mark.django_db
def test_a_request_relevant_candidate_outside_old_top100_survives():
    _fillers(OLD_CONCIERGE_POOL)
    _target(goriyaku="商売繁盛")  # Channel A の text 一致（金運）

    assert TARGET in _names(build_chat_candidates(**ORIGIN, trace_id="f2"))
    assert _concierge("金運を上げたい")[0] == TARGET


@pytest.mark.django_db
def test_b_channel_a_only_candidate_outside_old_top100_survives():
    _fillers(OLD_CONCIERGE_POOL)
    _target().goriyaku_tags.add(_tag("商売繁盛"))

    row = next(c for c in build_chat_candidates(**ORIGIN, trace_id="f2") if c["name"] == TARGET)
    assert row["goriyaku_tag_ids"] == [ID_BY_NAME["商売繁盛"]]
    assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in row
    assert _concierge("金運を上げたい")[0] == TARGET


@pytest.mark.django_db
def test_c_channel_b_only_candidate_outside_old_top100_survives(monkeypatch):
    _fillers(OLD_CONCIERGE_POOL)
    target = _target()
    _channel_b(monkeypatch, target)

    row = next(c for c in build_chat_candidates(**ORIGIN, trace_id="f2") if c["name"] == TARGET)
    assert row["goriyaku_tag_ids"] == []
    assert [m.need for m in row[CHANNEL_B_TYPED_NEED_MATCHES_KEY]] == ["money"]
    assert _concierge("金運を上げたい")[0] == TARGET


@pytest.mark.django_db
def test_d_nearest_candidate_outside_old_top100_reaches_distance_logic():
    _fillers(OLD_CONCIERGE_POOL)
    _target(lat=35.0001)

    candidates = build_chat_candidates(**ORIGIN, trace_id="f2")
    assert candidates[0]["name"] == TARGET  # 既存の距離順 sort が見えている
    assert _concierge("近くの神社")[0] == TARGET


@pytest.mark.django_db
def test_e_ineligible_high_popularity_rows_cannot_starve_an_eligible_candidate():
    _fillers(OLD_CONCIERGE_POOL, eligible=False)
    _target(goriyaku="商売繁盛")

    result = build_chat_candidates_with_eligibility(
        **ORIGIN, trace_id="f2", apply_popularity_pool_limit=False
    )
    assert _names(result.candidates) == [TARGET]
    assert (result.source_count, result.eligible_count, result.ineligible_count) == (101, 1, 100)
    assert _concierge("金運を上げたい") == [TARGET]


@pytest.mark.django_db
def test_old_boundary_is_gone_at_larger_scale():
    _fillers(OLD_CONCIERGE_POOL + 20)
    _target()
    names = _names(build_chat_candidates(**ORIGIN, trace_id="f2"))
    assert len(names) == OLD_CONCIERGE_POOL + 21
    assert TARGET in names


# ---------- F / G: 既存の明示条件は Stage 1 のまま ----------


@pytest.mark.django_db
def test_f_explicit_goriyaku_tag_ids_still_restricts_the_universe_before_relevance():
    tag = _tag("商売繁盛")
    fillers = _fillers(OLD_CONCIERGE_POOL)
    for shrine in fillers[:3]:
        shrine.goriyaku_tags.add(tag)
    _target().goriyaku_tags.add(tag)

    names = _names(build_chat_candidates(**ORIGIN, goriyaku_tag_ids=[tag.id], trace_id="f2"))
    assert sorted(names) == sorted(["人気0000", "人気0001", "人気0002", TARGET])


@pytest.mark.django_db
def test_g_area_filter_keeps_existing_semantics_without_coordinates():
    _fillers(OLD_CONCIERGE_POOL, address="東京都試験区1-1-1")
    _fillers(2, address="試験県北市2-2-2")  # name は重複するが別行
    _target(address="試験県南市3-3-3")

    names = _names(build_chat_candidates(area="試験県", trace_id="f2"))
    assert len(names) == 3 and TARGET in names
    # 座標がある場合は従来どおり area 文字列で絞らない
    assert len(build_chat_candidates(**ORIGIN, area="試験県", trace_id="f2")) == 103


# ---------- H: popularity は後段の並び順 / tie-break として残る ----------


@pytest.mark.django_db
def test_h_popularity_remains_ordering_and_tie_break_signal():
    source = create_fact_ready_source()
    for name, popular in (("低", 1.0), ("高", 9.0), ("中", 5.0)):
        shrine = Shrine.objects.create(
            name_jp=name,
            kind="shrine",
            address="東京都試験区5-5-5",
            latitude=35.01,
            longitude=139.0,
            popular_score=popular,
        )
        attach_usable_deity_fact(shrine, source=source)

    # 座標なし: 人気順。座標あり・同距離: 人気が tie-break。
    assert _names(build_chat_candidates(trace_id="f2")) == ["高", "中", "低"]
    assert _names(build_chat_candidates(**ORIGIN, trace_id="f2")) == ["高", "中", "低"]


# ---------- I / J: U1 / U2 は変えず、到達できるようになった候補にそのまま効く ----------


@pytest.mark.django_db
def test_i_u1_diversification_unchanged_and_sees_the_new_candidate(monkeypatch):
    money = _tag("商売繁盛")
    fillers = _fillers(OLD_CONCIERGE_POOL)
    for shrine in fillers[:5]:
        shrine.goriyaku_tags.add(money)
    target = _target()
    _channel_b(monkeypatch, target, concept="学業成就")

    top3 = _concierge("", need_tags=["money", "study"])
    assert TARGET in top3  # U1 が Channel B の study 被覆を数える
    assert len(top3) == 3


@pytest.mark.django_db
def test_j_u2_distance_tier_unchanged_and_sees_the_new_candidate(monkeypatch):
    money = _tag("商売繁盛")
    fillers = _fillers(OLD_CONCIERGE_POOL)
    fillers[0].goriyaku_tags.add(money)  # 0.2度先の Channel A 一致
    target = _target(lat=35.05)  # Channel B-only、Channel A より近い
    _channel_b(monkeypatch, target)

    top3 = _concierge("近くで金運を上げたい")
    assert top3[:2] == [TARGET, "人気0000"]  # 両方 Recommendation Meaning tier、距離順


# ---------- K: 公開 response schema ----------


def _post(client):
    response = client.post(
        "/api/concierge/chat/",
        data=json.dumps({"query": "金運を上げたい", **ORIGIN}),
        content_type="application/json",
    )
    assert response.status_code == 200
    body = response.json()
    return body, [set(r) for r in body["data"]["recommendations"]]


@pytest.mark.django_db
def test_k_public_response_schema_unchanged_across_old_boundary(client):
    _fillers(OLD_CONCIERGE_POOL - 1)
    _target(goriyaku="商売繁盛")
    inside_body, inside_rows = _post(client)

    _fillers(1, prefix="追加")  # 101件目: 旧挙動なら対象が pool 外へ落ちる境界
    outside_body, outside_rows = _post(client)

    assert set(outside_body) == set(inside_body)
    assert set(outside_body["data"]) == set(inside_body["data"])
    assert outside_rows and outside_rows == inside_rows
    raw = json.dumps(outside_body, ensure_ascii=False)
    assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in raw
    assert outside_body["data"]["recommendations"][0]["name"] == TARGET


# ---------- query count / Compass 既定 ----------


def _query_count(**kwargs) -> int:
    with CaptureQueriesContext(connection) as ctx:
        build_chat_candidates(**ORIGIN, trace_id="f2", **kwargs)
    return len(ctx.captured_queries)


@pytest.mark.django_db
def test_concierge_query_count_does_not_grow_with_universe_size(monkeypatch):
    _fillers(30)
    target = _target()
    _channel_b(monkeypatch, target)
    small = _query_count()
    _fillers(150, prefix="追加")
    assert _query_count() == small  # 件数は行数に比例しない（N+1 なし）


@pytest.mark.django_db
def test_shared_builder_default_keeps_legacy_pool_for_compass():
    _fillers(50)
    _target()
    # limit=10 -> 旧 pool_limit = 50。既定（Compass の現行経路）は従来どおり人気順で切る。
    legacy = build_chat_candidates_with_eligibility(**ORIGIN, limit=10, trace_id="f2")
    assert legacy.source_count == 50 and TARGET not in _names(legacy.candidates)
    concierge = build_chat_candidates(**ORIGIN, limit=10, trace_id="f2")
    assert TARGET in _names(concierge) and len(concierge) == 51
