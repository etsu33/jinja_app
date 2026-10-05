"""Channel B typed Recommendation read（PR-C / Policy C）。

契約: docs/audit/shrine-expansion-wave0-db04-f1-goriyaku-mapping-boundary.md
§12.11（read boundary / verification gate）/ §12.13（Need mapping）/ §12.15.K〜M /
§12.17 Mother Ship Decision（carrier の公開禁止・Need key の exact equality）。

ShrineSourceFact と registry record はすべて synthetic。数値の関連性（PR-F）は無いので、
Channel B があっても推薦の数値と順序は変わらない。
"""

from __future__ import annotations

import json

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from temples.domain import source_fact_mapping_registry_v1 as registry_module
from temples.domain.need_to_goriyaku_tag_ids import NEED_TO_GORIYAKU_IDS
from temples.domain.source_fact_mapping_registry_v1 import (
    SourceFactMappingRecord,
    SourceFactMappingRegistryError,
    build_registry,
)
from temples.models import (
    GoriyakuTag,
    Shrine,
    ShrineGoriyakuAssignment,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.services import channel_b_typed_need_match as channel_b
from temples.services import concierge_chat
from temples.services.channel_b_typed_need_match import (
    CHANNEL_B_TYPED_NEED_MATCHES_KEY,
    TypedNeedMatch,
    fetch_typed_need_matches,
    strip_channel_b_carrier,
)
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_candidates import build_chat_candidates_with_eligibility
from temples.services.concierge_chat_pool import (
    _ensure_pool_size,
    _merge_candidate_fields,
    _seed_recs_from_candidates,
)
from temples.services.concierge_chat_ranking import _prefilter_candidates_for_need
from temples.tests.support.recommendation_eligibility import attach_usable_deity_fact
from temples.tests.test_bootstrap_goriyaku_master_exact39_contract import CANONICAL_MASTER

pytestmark = pytest.mark.django_db

CANONICAL_ID_BY_NAME = {name: tag_id for tag_id, name in CANONICAL_MASTER}
SHRINE_NAME = "経路B試験神社"
PRAYER = "official_prayer_supported"
GUIDANCE = "official_current_guidance_supported"
COMBINED = "official_prayer_and_current_guidance_list_level"
CONCIERGE_URL = "/api/concierge/chat/"


# ---------- helpers ----------


def _tag(name: str) -> GoriyakuTag:
    """canonical master の id と name で GoriyakuTag を用意する（Need mapping は id を参照する）。"""
    tag, _ = GoriyakuTag.objects.get_or_create(id=CANONICAL_ID_BY_NAME[name], name=name)
    return tag


def _source(status: str = "source_confirmed") -> ShrineKnowledgeSource:
    return ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="ご祈祷案内",
        verification_status=status,
        verified_at=timezone.now() if status in ("source_confirmed", "reviewed") else None,
    )


def _shrine(name: str = SHRINE_NAME, *, eligible: bool = True) -> Shrine:
    shrine = Shrine.objects.create(
        name_jp=name, kind="shrine", address="東京都試験区5-5-5", latitude=35.0, longitude=139.0
    )
    if eligible:
        attach_usable_deity_fact(shrine)
    return shrine


def _fact(
    shrine: Shrine,
    key: str = "synthetic-channel-b-0001",
    *,
    wording: str = "商売繁盛",
    characterization: str = PRAYER,
    status: str = "source_confirmed",
    sources: tuple = ("source_confirmed",),
    confidence: str = "",
) -> ShrineSourceFact:
    fact = ShrineSourceFact.objects.create(
        shrine=shrine,
        stable_key=key,
        source_attested_wording=wording,
        evidence_characterization=characterization,
        verification_status=status,
        confidence=confidence,
        verified_at=timezone.now() if status in ("source_confirmed", "reviewed") else None,
    )
    for source_status in sources:
        fact.sources.add(_source(source_status))
    return fact


def _record(key: str, concept: str, classification: str = "EXACT") -> SourceFactMappingRecord:
    return SourceFactMappingRecord(
        source_fact_key=key,
        canonical_concept_name=concept,
        mapping_classification=classification,
    )


@pytest.fixture
def install_registry(monkeypatch):
    def _install(*records: SourceFactMappingRecord):
        monkeypatch.setattr(registry_module, "_default_registry", build_registry(records))

    return _install


@pytest.fixture(autouse=True)
def _no_llm(settings):
    settings.CONCIERGE_USE_LLM = False


def _matches(shrine: Shrine) -> tuple[TypedNeedMatch, ...]:
    return fetch_typed_need_matches([shrine.id]).get(shrine.id, ())


def _candidate(name: str = SHRINE_NAME) -> dict:
    result = build_chat_candidates_with_eligibility(lat=35.0, lng=139.0, area=None, trace_id="t")
    rows = [c for c in result.candidates if c.get("name") == name]
    assert len(rows) == 1
    return rows[0]


def _recommend(need: str = "money", candidates: list[dict] | None = None) -> dict:
    if candidates is None:
        result = build_chat_candidates_with_eligibility(
            lat=35.0, lng=139.0, area=None, trace_id="t"
        )
        candidates = result.candidates
    return build_chat_recommendations(
        query="",
        language="ja",
        candidates=candidates,
        bias={"lat": 35.0, "lng": 139.0},
        need_tags=[need],
        public_mode="need",
        flow="A",
        llm_enabled=False,
    )


# ---------- typed match（T1〜T15, R1〜R10） ----------


def test_t1_valid_prayer_fact_with_exact_mapping_yields_one_typed_match(install_registry):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine)
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    assert _matches(shrine) == (
        TypedNeedMatch(
            need="money",
            canonical_concept_name="商売繁盛",
            signal_type=PRAYER,
            source_fact_key="synthetic-channel-b-0001",
            source_attested_wording="商売繁盛",
        ),
    )


def test_typed_match_is_immutable_and_has_no_numeric_or_id_fields():
    import dataclasses

    names = [f.name for f in dataclasses.fields(TypedNeedMatch)]
    assert names == [
        "need",
        "canonical_concept_name",
        "signal_type",
        "source_fact_key",
        "source_attested_wording",
    ]
    match = TypedNeedMatch("money", "商売繁盛", PRAYER, "k", "商売繁盛")
    with pytest.raises(dataclasses.FrozenInstanceError):
        match.need = "career"


@pytest.mark.parametrize("characterization", [GUIDANCE, COMBINED, PRAYER])
def test_t2_t3_t32_signal_type_is_preserved_exactly(install_registry, characterization):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine, characterization=characterization)
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    (match,) = _matches(shrine)
    assert match.signal_type == characterization
    assert match.signal_type != "official_goriyaku_wording"


def test_t4_safe_normalization_uses_concept_and_keeps_source_wording(install_registry):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine, wording="商売繁昌")
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛", "SAFE_NORMALIZATION"))
    (match,) = _matches(shrine)
    assert match.canonical_concept_name == "商売繁盛"
    assert match.source_attested_wording == "商売繁昌"


def test_t5_t39_r2_unmapped_fact_is_no_signal_not_error(install_registry):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine)
    _fact(shrine, key="synthetic-channel-b-unmapped")
    install_registry(_record("synthetic-channel-b-other", "商売繁盛"))
    assert _matches(shrine) == ()


@pytest.mark.parametrize("status", ["draft", "unverified", "disputed", "outdated", "rejected"])
def test_t6_r8_unverified_fact_is_no_signal(install_registry, status):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine, status=status)
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    assert _matches(shrine) == ()


def test_t7_fact_without_verified_source_is_no_signal(install_registry):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine, sources=("draft", "unverified"))
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    assert _matches(shrine) == ()


def test_t8_r9_fact_without_sources_is_no_signal(install_registry):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine, sources=())
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    assert _matches(shrine) == ()


def test_t9_blank_wording_is_no_signal(install_registry):
    _tag("商売繁盛")
    shrine = _shrine()
    fact = _fact(shrine)
    ShrineSourceFact.objects.filter(pk=fact.pk).update(source_attested_wording="   ")
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    assert _matches(shrine) == ()


def test_invalid_characterization_is_no_signal(install_registry):
    _tag("商売繁盛")
    shrine = _shrine()
    fact = _fact(shrine)
    ShrineSourceFact.objects.filter(pk=fact.pk).update(
        evidence_characterization="official_goriyaku_wording"
    )
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    assert _matches(shrine) == ()


def test_confidence_does_not_gate_readability(install_registry):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine, confidence="low")
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    assert len(_matches(shrine)) == 1


def test_t10_r10_concept_without_need_mapping_yields_no_match(install_registry):
    _tag("方除け")
    shrine = _shrine()
    _fact(shrine, wording="方除")
    install_registry(_record("synthetic-channel-b-0001", "方除け", "SAFE_NORMALIZATION"))
    assert _matches(shrine) == ()


def test_t11_multi_need_concept_yields_one_match_per_need(install_registry):
    _tag("金運")
    shrine = _shrine()
    _fact(shrine, wording="金運")
    install_registry(_record("synthetic-channel-b-0001", "金運"))
    matches = _matches(shrine)
    assert [m.need for m in matches] == ["mental", "money"]
    assert {(m.source_fact_key, m.canonical_concept_name, m.signal_type) for m in matches} == {
        ("synthetic-channel-b-0001", "金運", PRAYER)
    }


def test_t12_multiple_facts_same_need_keep_separate_provenance(install_registry):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine, key="synthetic-channel-b-0001")
    _fact(shrine, key="synthetic-channel-b-0002", characterization=GUIDANCE)
    install_registry(
        _record("synthetic-channel-b-0001", "商売繁盛"),
        _record("synthetic-channel-b-0002", "商売繁盛"),
    )
    matches = _matches(shrine)
    assert [(m.need, m.source_fact_key, m.signal_type) for m in matches] == [
        ("money", "synthetic-channel-b-0001", PRAYER),
        ("money", "synthetic-channel-b-0002", GUIDANCE),
    ]


def test_t13_multiple_concepts_same_need_keep_separate_provenance(install_registry):
    _tag("商売繁盛")
    _tag("五穀豊穣")
    shrine = _shrine()
    _fact(shrine, key="synthetic-channel-b-0001")
    _fact(shrine, key="synthetic-channel-b-0002", wording="五穀豊穣")
    install_registry(
        _record("synthetic-channel-b-0001", "商売繁盛"),
        _record("synthetic-channel-b-0002", "五穀豊穣"),
    )
    matches = _matches(shrine)
    assert [(m.need, m.canonical_concept_name) for m in matches] == [
        ("money", "商売繁盛"),
        ("money", "五穀豊穣"),
    ]


def test_t14_t15_need_keys_are_the_shared_keys_without_alias_normalization(install_registry):
    _tag("縁結び")
    shrine = _shrine()
    _fact(shrine, wording="縁結び")
    install_registry(_record("synthetic-channel-b-0001", "縁結び"))
    needs = [m.need for m in _matches(shrine)]
    expected = sorted(k for k, ids in NEED_TO_GORIYAKU_IDS.items() if 1 in ids)
    assert needs == expected == ["love", "marriage", "relationship"]
    assert set(needs) <= set(NEED_TO_GORIYAKU_IDS)


def test_needs_for_concept_does_not_call_alias_normalizer(monkeypatch):
    def _boom(*_args, **_kwargs):
        raise AssertionError("alias normalizer must not be called")

    monkeypatch.setattr("temples.services.concierge_chat_ranking._normalize_need_tag", _boom)
    monkeypatch.setattr("temples.services.concierge_chat_need.normalize_need_tag", _boom)
    assert channel_b.needs_for_concept_id(28) == ("mental", "money")


# ---------- fail-closed（R3 / R4 / R5 / R6 / R7, T37 / T38） ----------


def test_t37_r4_invalid_repository_registry_fails_closed(monkeypatch):
    shrine = _shrine()
    monkeypatch.setattr(
        registry_module,
        "SOURCE_FACT_MAPPING_RECORDS",
        (
            _record("synthetic-channel-b-0001", "商売繁盛"),
            _record("synthetic-channel-b-0001", "厄除け"),
        ),
    )
    monkeypatch.setattr(registry_module, "_default_registry", None)
    with pytest.raises(SourceFactMappingRegistryError):
        fetch_typed_need_matches([shrine.id])


@pytest.mark.parametrize("classification", ["AMBIGUOUS", "NO_CANONICAL_TAG"])
def test_r5_r6_ambiguous_or_no_canonical_tag_cannot_be_a_positive_entry(classification):
    with pytest.raises(SourceFactMappingRegistryError):
        build_registry((_record("synthetic-channel-b-0001", "商売繁盛", classification),))


def test_r5_r6_fact_without_positive_entry_is_no_signal(install_registry):
    shrine = _shrine()
    _fact(shrine)
    install_registry()
    assert _matches(shrine) == ()


def test_t38_r7_positive_mapping_to_missing_concept_fails_closed(install_registry):
    shrine = _shrine()
    _fact(shrine)
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    with pytest.raises(SourceFactMappingRegistryError):
        fetch_typed_need_matches([shrine.id])


def test_r3_registry_entry_for_missing_fact_is_a_db_consistency_error(install_registry):
    _tag("商売繁盛")
    errors = registry_module.validate_registry_db_consistency(
        (_record("synthetic-channel-b-missing", "商売繁盛"),)
    )
    assert any("ShrineSourceFact" in e for e in errors)


# ---------- bulk read（T23 / T24） ----------


def test_t23_bulk_load_query_count_is_independent_of_candidate_count(install_registry):
    _tag("商売繁盛")
    shrines = [_shrine(f"{SHRINE_NAME}{i}") for i in range(4)]
    records = []
    for i, shrine in enumerate(shrines):
        _fact(shrine, key=f"synthetic-channel-b-{i:04d}")
        records.append(_record(f"synthetic-channel-b-{i:04d}", "商売繁盛"))
    install_registry(*records)

    with CaptureQueriesContext(connection) as one:
        fetch_typed_need_matches([shrines[0].id])
    with CaptureQueriesContext(connection) as four:
        result = fetch_typed_need_matches([s.id for s in shrines])
    assert len(result) == 4
    assert len(four) == len(one) == 3


def test_empty_registry_issues_no_query(install_registry):
    install_registry()  # registry が空のとき（W0-DB04 PR-E 以降は repository の registry は空ではない）
    shrine = _shrine()
    _fact(shrine)
    with CaptureQueriesContext(connection) as ctx:
        assert fetch_typed_need_matches([shrine.id]) == {}
    assert len(ctx) == 0


def test_t24_lookup_does_not_run_db_consistency_validation(install_registry, monkeypatch):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine)
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))

    def _boom(*_a, **_k):
        raise AssertionError("runtime read must not run registry DB consistency validation")

    monkeypatch.setattr(registry_module, "validate_registry_db_consistency", _boom)
    assert len(_matches(shrine)) == 1


# ---------- carrier（T25〜T30） ----------


def test_t26_carrier_is_attached_at_candidate_construction(install_registry):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine)
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    candidate = _candidate()
    assert candidate[CHANNEL_B_TYPED_NEED_MATCHES_KEY] == _matches(shrine)
    # Channel A の field には入らない。
    assert candidate["goriyaku_tag_ids"] == []


def test_carrier_absent_without_matches():
    _shrine()
    assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in _candidate()


def test_t27_carrier_survives_prefilter_seed_refill_and_merge(install_registry):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine)
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    candidates = [_candidate()]
    expected = _matches(shrine)

    prefiltered = _prefilter_candidates_for_need(candidates, need_tags=["money"])
    assert prefiltered[0][CHANNEL_B_TYPED_NEED_MATCHES_KEY] == expected
    seeded = _seed_recs_from_candidates(prefiltered, size=12)
    assert seeded["recommendations"][0][CHANNEL_B_TYPED_NEED_MATCHES_KEY] == expected
    refilled = _ensure_pool_size({"recommendations": []}, candidates=candidates, size=20)
    assert refilled["recommendations"][0][CHANNEL_B_TYPED_NEED_MATCHES_KEY] == expected
    merged = _merge_candidate_fields(
        {"recommendations": [{"shrine_id": shrine.id, "name": SHRINE_NAME}]},
        candidates=candidates,
    )
    assert merged["recommendations"][0][CHANNEL_B_TYPED_NEED_MATCHES_KEY] == expected


def test_t27_carrier_reaches_breakdown_and_is_stripped_at_exit(install_registry, monkeypatch):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine)
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))

    seen: list = []
    original = concierge_chat._attach_chat_rec_enrichment

    def _spy(recs, **kwargs):
        seen.extend(
            r.get(CHANNEL_B_TYPED_NEED_MATCHES_KEY)
            for r in recs.get("recommendations") or []
            if r.get("name") == SHRINE_NAME
        )
        return original(recs, **kwargs)

    monkeypatch.setattr(concierge_chat, "_attach_chat_rec_enrichment", _spy)
    recs = _recommend()
    assert seen == [_matches(shrine)]
    for row in recs["recommendations"]:
        assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in row


def test_t25_request_supplied_candidate_gets_no_fabricated_carrier(install_registry):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine)
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    request_candidate = {"name": SHRINE_NAME, "address": "東京都試験区5-5-5"}
    recs = _recommend(candidates=[request_candidate])
    serialized = json.dumps(recs, ensure_ascii=False, default=str)
    assert "synthetic-channel-b-0001" not in serialized
    assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in serialized


def test_llm_route_input_excludes_carrier_and_merge_restores_it(
    install_registry, monkeypatch, settings
):
    """LLM 成功経路の入力は Channel B 導入前と同じ（carrier を外部 provider へ渡さない）。"""
    from temples.llm import orchestrator as orch_mod
    from temples.services.concierge_chat_llm_route import resolve_llm_route

    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine)
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    candidates = [_candidate()]
    received: list = []

    class _FakeOrchestrator:
        def suggest(self, *, query, candidates):
            received.extend(candidates)
            return {"recommendations": [dict(c) for c in candidates]}

    monkeypatch.setattr(orch_mod, "ConciergeOrchestrator", _FakeOrchestrator)
    settings.CONCIERGE_USE_LLM = True
    route = resolve_llm_route(
        query="金運", valid_candidates=candidates, need_tags=["money"], llm_enabled=True
    )
    assert route["llm_used"] is True
    assert received and all(CHANNEL_B_TYPED_NEED_MATCHES_KEY not in c for c in received)
    # 元の候補は変えない。merge で carrier が戻る。
    assert CHANNEL_B_TYPED_NEED_MATCHES_KEY in candidates[0]
    merged = _merge_candidate_fields(route["recs"], candidates=candidates)
    assert merged["recommendations"][0][CHANNEL_B_TYPED_NEED_MATCHES_KEY] == _matches(shrine)


def test_strip_channel_b_carrier_handles_both_lists():
    row = {"name": "x", CHANNEL_B_TYPED_NEED_MATCHES_KEY: ()}
    recs = {"recommendations": [row], "recommendations_v2": [dict(row)]}
    strip_channel_b_carrier(recs)
    assert all(CHANNEL_B_TYPED_NEED_MATCHES_KEY not in r for r in recs["recommendations"])
    assert all(CHANNEL_B_TYPED_NEED_MATCHES_KEY not in r for r in recs["recommendations_v2"])


def _concierge_body(client) -> dict:
    response = client.post(
        CONCIERGE_URL,
        data=json.dumps({"query": "金運を上げたい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert response.status_code == 200
    return response.json()


def test_t28_t29_t30_t40_carrier_does_not_leak_into_public_concierge_response(
    client, install_registry
):
    _tag("商売繁盛")
    shrine = _shrine()
    _fact(shrine, wording="商売繁昌")
    install_registry()
    baseline = _concierge_body(client)

    install_registry(_record("synthetic-channel-b-0001", "商売繁盛", "SAFE_NORMALIZATION"))
    body = _concierge_body(client)
    raw = json.dumps(body, ensure_ascii=False)
    assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in raw
    assert "synthetic-channel-b-0001" not in raw
    assert "source_fact_key" not in raw
    assert "商売繁昌" not in raw
    # 公開 schema は変わらない（top-level と recommendation の key が同じ）。
    assert set(body) == set(baseline)
    assert set(body["data"]) == set(baseline["data"])
    assert [set(r) for r in body["data"]["recommendations"]] == [
        set(r) for r in baseline["data"]["recommendations"]
    ]


# ---------- Channel A / 数値 / G5 / goriyaku は変わらない（T16〜T22, T31, T33〜T36） ----------


# Channel A 側の値と理由文（PR-F の後も Channel B で変わらないもの）。
_CHANNEL_A_KEYS = ("goriyaku_tag_ids", "reason", "_reason_facts")


def _snapshot(recs: dict) -> dict:
    """name → (Channel A の値, rank_weighted)。PR-F は rank_weighted（と _score_total・順序）だけを変える。"""
    out = {}
    for row in recs["recommendations"]:
        breakdown = row.get("breakdown") or {}
        need = ((row.get("breakdown_detail") or {}).get("features") or {}).get("need") or {}
        channel_a = (
            tuple(repr(row.get(k)) for k in _CHANNEL_A_KEYS),
            breakdown.get("score_need"),
            breakdown.get("score_total"),
            tuple(breakdown.get("matched_need_tags") or []),
            need.get("rank_raw"),
            tuple(need.get("matched_tags") or []),
            need.get("matched_by_gid_count"),
            need.get("matched_by_text_count"),
        )
        out[row.get("name")] = (channel_a, need.get("rank_weighted"))
    return out


def test_t16_to_t21_t35_t36_channel_a_results_unchanged_and_only_pr_f_moves_rank_weighted(
    install_registry,
):
    """Channel B は Channel A の値（score_need / matched_all / rank_raw / gid / text / 理由文）を
    変えない。数値の効果は PR-F の規則だけ: B だけの Need は rank_weighted +2.0、
    同じ Need に Channel A がある候補は +0。
    """
    _tag("商売繁盛")
    _tag("金運")
    b_only = _shrine()
    _fact(b_only, wording="金運")
    a_only = _shrine("経路A試験神社")
    a_only.goriyaku_tags.add(_tag("商売繁盛"))
    _fact(a_only, key="synthetic-channel-b-0002")

    install_registry()
    before = _snapshot(_recommend())

    install_registry(
        _record("synthetic-channel-b-0001", "金運"),
        _record("synthetic-channel-b-0002", "商売繁盛"),
    )
    assert _matches(b_only) and _matches(a_only)
    after = _snapshot(_recommend())

    assert set(after) == set(before)
    for name in before:
        assert after[name][0] == before[name][0], name
    assert after[SHRINE_NAME][1] - before[SHRINE_NAME][1] == pytest.approx(2.0)
    assert after["経路A試験神社"][1] == before["経路A試験神社"][1]


def test_t31_channel_b_does_not_enter_the_legacy_goriyaku_reason_path(install_registry):
    """Channel B は理由文に入らない（「ご利益で知られる」へ格上げしない）。

    注: Need の一致が無い候補にも Channel A の既存の fallback（SP3）が「〜のご利益で知られる」を
    出すことがある。これは Channel B の有無と無関係な既存の挙動であり、PR-C では直さない。
    ここでは、Channel B があっても理由文と reason fact が変わらず、B の provenance がそこへ
    流れ込まないことを確認する。
    """
    _tag("金運")
    shrine = _shrine()
    _fact(shrine, wording="金運祈願")

    def _row():
        return next(r for r in _recommend()["recommendations"] if r.get("name") == SHRINE_NAME)

    install_registry()
    before = _row()
    install_registry(_record("synthetic-channel-b-0001", "金運", "SAFE_NORMALIZATION"))
    after = _row()

    assert after.get("reason") == before.get("reason")
    assert after.get("_reason_facts") == before.get("_reason_facts")
    reason_blob = json.dumps(
        [after.get("reason"), after.get("_reason_facts")], ensure_ascii=False, default=str
    )
    assert "金運祈願" not in reason_blob
    assert "synthetic-channel-b-0001" not in reason_blob
    assert all(fact.get("type") != "goriyaku_tag" for fact in after.get("_reason_facts") or [])


def test_t22_source_fact_with_mapping_does_not_make_shrine_g5_eligible(install_registry):
    _tag("商売繁盛")
    only_fact = _shrine("経路Bのみ神社", eligible=False)
    _fact(only_fact)
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    assert _matches(only_fact)
    result = build_chat_candidates_with_eligibility(lat=35.0, lng=139.0, area=None, trace_id="t")
    assert all(c.get("name") != "経路Bのみ神社" for c in result.candidates)


def test_t33_t34_read_writes_no_goriyaku_tag_or_assignment(install_registry):
    tag = _tag("商売繁盛")
    shrine = _shrine()
    fact = _fact(shrine)
    install_registry(_record("synthetic-channel-b-0001", "商売繁盛"))
    tag_count = GoriyakuTag.objects.count()
    fact_before = list(ShrineSourceFact.objects.filter(pk=fact.pk).values())
    _recommend()
    assert GoriyakuTag.objects.count() == tag_count
    assert shrine.goriyaku_tags.count() == 0
    assert not tag.shrine_set.exists() if hasattr(tag, "shrine_set") else True
    assert ShrineGoriyakuAssignment.objects.count() == 0
    assert list(ShrineSourceFact.objects.filter(pk=fact.pk).values()) == fact_before
