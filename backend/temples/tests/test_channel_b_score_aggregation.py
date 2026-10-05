"""Channel B score / aggregation（PR-F / Policy C）。

契約: docs/audit/shrine-expansion-wave0-db04-f1-goriyaku-mapping-boundary.md
§12.16.10（SCORE_AGGREGATION_BOUNDARY）/ §12.17 / §12.18（PR-F 実装指示）。

- B だけの Need: prefilter +PREFILTER_CHANNEL_B_WEIGHT(2) / ranking +CHANNEL_B_RANKING_WEIGHT(2.0)
- 同じ Need に Channel A（astro / gid / text）があれば B は 0（AG1 / R1）
- 違う Need は加算（DN1）。Need の中の Fact / Source / concept の数は寄与を増やさない
- score_need / matched_all / rank_raw は Channel A のまま（S2）
"""

from __future__ import annotations

import json

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from temples.domain import source_fact_mapping_registry_v1 as registry_module
from temples.domain.source_fact_mapping_registry_v1 import SourceFactMappingRecord, build_registry
from temples.models import GoriyakuTag, Shrine, ShrineGoriyakuAssignment, ShrineKnowledgeSource
from temples.models import ShrineSourceFact
from temples.services import concierge_chat_ranking as ranking
from temples.services.channel_b_typed_need_match import (
    CHANNEL_B_TYPED_NEED_MATCHES_KEY,
    TypedNeedMatch,
)
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_candidates import build_chat_candidates_with_eligibility
from temples.services.concierge_chat_ranking import (
    CHANNEL_B_RANKING_WEIGHT,
    PREFILTER_CHANNEL_B_WEIGHT,
    _attach_breakdown,
    _channel_b_request_need_keys,
    _prefilter_candidates_for_need,
)
from temples.tests.support.recommendation_eligibility import attach_usable_deity_fact
from temples.tests.test_bootstrap_goriyaku_master_exact39_contract import CANONICAL_MASTER

PRAYER = "official_prayer_supported"
GUIDANCE = "official_current_guidance_supported"
WEIGHTS = {"element": 0.6, "need": 0.3, "popular": 0.1, "distance": 0.0}
CANONICAL_ID_BY_NAME = {name: tag_id for tag_id, name in CANONICAL_MASTER}


def _match(need: str, concept: str = "商売繁盛", key: str = "k-0001", **kw) -> TypedNeedMatch:
    return TypedNeedMatch(
        need=need,
        canonical_concept_name=concept,
        signal_type=kw.get("signal_type", PRAYER),
        source_fact_key=key,
        source_attested_wording=kw.get("wording", concept),
    )


def _candidate(*matches, **fields) -> dict:
    row = {
        "id": 101,
        "shrine_id": 101,
        "name": "数値試験神社",
        "goriyaku": "",
        "description": "",
        "astro_tags": [],
        "goriyaku_tag_ids": [],
        "popular_score": 0.0,
    }
    row.update(fields)
    if matches:
        row[CHANNEL_B_TYPED_NEED_MATCHES_KEY] = tuple(matches)
    return row


def _prefilter_score(row: dict, needs: list[str]) -> float:
    (out,) = _prefilter_candidates_for_need([row], need_tags=needs)
    return out["_prefilter_debug"]["score"]


def _breakdown(row: dict, needs: list[str]) -> dict:
    rec = dict(row)
    _attach_breakdown(
        rec, birthdate=None, need_tags=needs, weights=WEIGHTS, astro_bonus_enabled=False
    )
    need = rec["breakdown_detail"]["features"]["need"]
    return {
        "rank_weighted": need["rank_weighted"],
        "rank_raw": need["rank_raw"],
        "score_need": rec["breakdown"]["score_need"],
        "score_total": rec["breakdown"]["score_total"],
        "matched_all": list(rec["breakdown"]["matched_need_tags"]),
        "matched_tags": list(need["matched_tags"]),
        "gid_count": need["matched_by_gid_count"],
        "text_count": need["matched_by_text_count"],
        "_score_total": rec["_score_total"],
    }


def _delta(row_with_b: dict, needs: list[str]) -> tuple[float, float]:
    """(prefilter の差, rank_weighted の差)。carrier を除いた同じ候補との比較。"""
    base = {k: v for k, v in row_with_b.items() if k != CHANNEL_B_TYPED_NEED_MATCHES_KEY}
    return (
        _prefilter_score(row_with_b, needs) - _prefilter_score(base, needs),
        _breakdown(row_with_b, needs)["rank_weighted"] - _breakdown(base, needs)["rank_weighted"],
    )


# ---------- constants / helper ----------


def test_constants_are_pinned_and_separately_owned():
    assert PREFILTER_CHANNEL_B_WEIGHT == 2
    assert isinstance(PREFILTER_CHANNEL_B_WEIGHT, int)
    assert CHANNEL_B_RANKING_WEIGHT == 2.0
    assert isinstance(CHANNEL_B_RANKING_WEIGHT, float)
    source = open(ranking.__file__, encoding="utf-8").read()
    assert "PREFILTER_CHANNEL_B_WEIGHT = 2\n" in source
    assert "CHANNEL_B_RANKING_WEIGHT = 2.0\n" in source


def test_projection_is_exact_deduped_and_non_mutating():
    matches = (
        _match("money", key="a"),
        _match("money", key="b"),
        _match("money", concept="五穀豊穣", key="c"),
        _match("career", key="d"),
    )
    row = _candidate(*matches)
    assert _channel_b_request_need_keys(row, ["money", "study"]) == {"money"}
    assert row[CHANNEL_B_TYPED_NEED_MATCHES_KEY] == matches


@pytest.mark.parametrize(
    "carrier",
    [None, (), [], "money", 3, ({"need": "money"},), (None, "money", 1)],
)
def test_sa_q15_q16_missing_empty_or_malformed_carrier_contributes_zero(carrier):
    row = _candidate()
    if carrier is not None:
        row[CHANNEL_B_TYPED_NEED_MATCHES_KEY] = carrier
    assert _channel_b_request_need_keys(row, ["money"]) == set()
    assert _delta(row, ["money"]) == (0, 0.0)


def test_malformed_items_are_skipped_but_valid_items_still_count():
    row = _candidate()
    row[CHANNEL_B_TYPED_NEED_MATCHES_KEY] = ({"need": "money"}, None, _match("money"))
    assert _delta(row, ["money"]) == (2, 2.0)


def test_sa_q18_exact_need_equality_without_alias_normalization():
    # "fortune" は request 側では money の alias だが、B の key は正規化しない。
    row = _candidate(_match("fortune"), _match("Money"), _match(" money"))
    assert _channel_b_request_need_keys(row, ["money"]) == set()
    assert _delta(row, ["money"]) == (0, 0.0)


@pytest.mark.django_db
def test_projection_issues_no_db_query():
    row = _candidate(_match("money"), _match("study", concept="学業成就"))
    with CaptureQueriesContext(connection) as ctx:
        _channel_b_request_need_keys(row, ["money", "study"])
    assert len(ctx) == 0


# ---------- B only（SAQ1〜3, SAQ17, SAQ22, SAQ23） ----------


@pytest.mark.django_db
def test_sa_q1_q22_q23_b_only_one_need():
    assert _delta(_candidate(_match("money")), ["money"]) == (2, 2.0)


@pytest.mark.django_db
def test_sa_q2_b_only_two_distinct_needs():
    row = _candidate(_match("money"), _match("study", concept="学業成就", key="k-2"))
    assert _delta(row, ["money", "study"]) == (4, 4.0)


@pytest.mark.django_db
def test_sa_q3_b_only_three_distinct_needs():
    row = _candidate(
        _match("money"),
        _match("study", concept="学業成就", key="k-2"),
        _match("protection", concept="厄除け", key="k-3"),
    )
    assert _delta(row, ["money", "study", "protection"]) == (6, 6.0)


@pytest.mark.django_db
def test_sa_q17_b_need_outside_the_request_contributes_nothing():
    row = _candidate(_match("career", concept="仕事運"))
    assert _delta(row, ["money"]) == (0, 0.0)


@pytest.mark.django_db
def test_b_only_study_need_does_not_trigger_study_bonus():
    row = _candidate(_match("study", concept="学業成就"))
    # study の text bonus（prefilter +2 / ranking +1）は material の STUDY_SHRINE_HINTS だけで決まる。
    assert _delta(row, ["study"]) == (2, 2.0)


# ---------- A + B 同じ Need（SAQ4〜7, SAQ11） ----------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fields",
    [
        {"goriyaku_tag_ids": [4]},  # SAQ4 gid（商売繁盛 → money）
        {"goriyaku": "金運"},  # SAQ5 text
        {"astro_tags": ["money"]},  # SAQ6 astro
        {"goriyaku_tag_ids": [4], "goriyaku": "金運"},  # SAQ7 gid + text
        {"astro_tags": ["money"], "goriyaku_tag_ids": [4], "goriyaku": "商売繁盛 金運"},
    ],
)
def test_sa_q4_to_q7_channel_a_on_same_need_gets_no_b_bonus(fields):
    row = _candidate(_match("money"), **fields)
    assert _delta(row, ["money"]) == (0, 0.0)


@pytest.mark.django_db
def test_sa_q11_channel_a_plus_multiple_b_provenance_adds_nothing():
    row = _candidate(
        _match("money", key="a"),
        _match("money", key="b", signal_type=GUIDANCE),
        _match("money", concept="五穀豊穣", key="c"),
        goriyaku_tag_ids=[4],
    )
    assert _delta(row, ["money"]) == (0, 0.0)


@pytest.mark.django_db
def test_a_text_plus_b_keeps_current_a_text_value_even_below_b_only():
    """K1（凍結済み）: A text + B は A の text の値のまま。B だけ（2 / 2.0）より低くてよい。"""
    a_text = _candidate(_match("money"), goriyaku="収入")
    b_only = _candidate(_match("money"))
    assert _prefilter_score(a_text, ["money"]) == 1
    assert _prefilter_score(b_only, ["money"]) == 2
    assert _breakdown(a_text, ["money"])["rank_weighted"] == pytest.approx(1.2)
    assert _breakdown(b_only, ["money"])["rank_weighted"] == pytest.approx(2.0)


# ---------- 多重度（SAQ8〜10） ----------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "matches",
    [
        (_match("money", key="a"), _match("money", key="b")),  # SAQ8 Facts
        (_match("money"), _match("money", concept="五穀豊穣", key="c")),  # SAQ9 concepts
        (_match("money"), _match("money"), _match("money")),  # SAQ10 重複した provenance
    ],
)
def test_sa_q8_q9_q10_same_need_multiplicity_counts_once(matches):
    assert _delta(_candidate(*matches), ["money"]) == (2, 2.0)


# ---------- 違う Need（SAQ12, SAQ13） ----------


@pytest.mark.django_db
def test_sa_q12_a_need1_plus_b_need2_is_additive():
    row = _candidate(_match("study", concept="学業成就"), goriyaku_tag_ids=[4])
    assert _delta(row, ["money", "study"]) == (2, 2.0)


@pytest.mark.django_db
def test_sa_q13_a_need1_plus_b_need2_and_need3_is_additive():
    row = _candidate(
        _match("money", key="same-need"),
        _match("study", concept="学業成就", key="k-2"),
        _match("protection", concept="厄除け", key="k-3"),
        goriyaku_tag_ids=[4],
    )
    assert _delta(row, ["money", "study", "protection"]) == (4, 4.0)


# ---------- Channel A の値と診断 field は変わらない（SAQ14, SAQ19〜21, SAQ24） ----------


@pytest.mark.django_db
def test_sa_q19_q20_q21_score_need_matched_all_rank_raw_unchanged_with_b_only():
    with_b = _candidate(_match("money"), _match("study", concept="学業成就", key="k-2"))
    base = _candidate()
    a, b = _breakdown(with_b, ["money", "study"]), _breakdown(base, ["money", "study"])
    for key in ("score_need", "matched_all", "matched_tags", "rank_raw", "gid_count", "text_count"):
        assert a[key] == b[key], key
    # 公開の breakdown.score_total は score_need から作るので変わらない。
    assert a["score_total"] == b["score_total"]
    assert a["rank_weighted"] - b["rank_weighted"] == pytest.approx(4.0)
    assert a["_score_total"] > b["_score_total"]


@pytest.mark.django_db
def test_prefilter_channel_a_debug_fields_unchanged_with_b():
    with_b = _candidate(_match("money"), goriyaku="")
    (out_b,) = _prefilter_candidates_for_need([with_b], need_tags=["money"])
    (out_a,) = _prefilter_candidates_for_need([_candidate()], need_tags=["money"])
    for key in ("matched", "text_score_by_tag", "matched_text_hints_by_tag", "matched_gid_tags"):
        assert out_b["_prefilter_debug"][key] == out_a["_prefilter_debug"][key]
    assert out_b[CHANNEL_B_TYPED_NEED_MATCHES_KEY] == with_b[CHANNEL_B_TYPED_NEED_MATCHES_KEY]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fields",
    [
        {},
        {"goriyaku_tag_ids": [4]},
        {"goriyaku": "金運 商売繁盛 学業成就"},
        {"astro_tags": ["money"], "goriyaku_tag_ids": [4, 9]},
    ],
)
def test_sa_q14_q24_channel_a_only_values_are_the_pinned_formula(fields):
    """carrier の無い候補は、Channel A の現行の式どおりの値（B の項は 0）。"""
    row = _candidate(**fields)
    needs = ["money", "study"]
    out = _breakdown(row, needs)
    assert _channel_b_request_need_keys(row, needs) == set()
    # B の carrier が空でも同じ値。
    empty = dict(row, **{CHANNEL_B_TYPED_NEED_MATCHES_KEY: ()})
    assert _breakdown(empty, needs) == out
    assert _prefilter_score(empty, needs) == _prefilter_score(row, needs)


# ---------- 統合（Compass 1 Need / Concierge 3 Need, G5, 公開 / LLM, goriyaku） ----------


def _tag(name: str) -> GoriyakuTag:
    tag, _ = GoriyakuTag.objects.get_or_create(id=CANONICAL_ID_BY_NAME[name], name=name)
    return tag


def _shrine(name: str, *, eligible: bool = True) -> Shrine:
    shrine = Shrine.objects.create(
        name_jp=name, kind="shrine", address="東京都試験区6-6-6", latitude=35.0, longitude=139.0
    )
    if eligible:
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
            source_fact_key=key, canonical_concept_name=concept, mapping_classification="EXACT"
        )
        for key, concept in pairs
    )
    monkeypatch.setattr(registry_module, "_default_registry", build_registry(records))


def _recommend(needs: list[str]) -> dict:
    result = build_chat_candidates_with_eligibility(lat=35.0, lng=139.0, area=None, trace_id="t")
    return build_chat_recommendations(
        query="",
        language="ja",
        candidates=result.candidates,
        bias={"lat": 35.0, "lng": 139.0},
        need_tags=needs,
        public_mode="need",
        flow="A",
        llm_enabled=False,
    )


def _row(recs: dict, name: str) -> dict:
    return next(r for r in recs["recommendations"] if r.get("name") == name)


def _rank_weighted(row: dict) -> float:
    return row["breakdown_detail"]["features"]["need"]["rank_weighted"]


@pytest.fixture
def _no_llm(settings):
    settings.CONCIERGE_USE_LLM = False


@pytest.mark.django_db
def test_compass_like_one_need_path_adds_exactly_two(monkeypatch, _no_llm):
    _tag("商売繁盛")
    shrine = _shrine("一Need試験神社")
    _fact(shrine, "pf-0001", "商売繁盛")

    _install(monkeypatch)
    before = _row(_recommend(["money"]), "一Need試験神社")
    _install(monkeypatch, ("pf-0001", "商売繁盛"))
    after = _row(_recommend(["money"]), "一Need試験神社")

    assert _rank_weighted(after) - _rank_weighted(before) == pytest.approx(2.0)
    for key in ("score_need", "matched_need_tags"):
        assert after["breakdown"][key] == before["breakdown"][key]
    need_after = after["breakdown_detail"]["features"]["need"]
    need_before = before["breakdown_detail"]["features"]["need"]
    assert need_after["rank_raw"] == need_before["rank_raw"]
    # MS-5: request の Need（money）は Channel B だけが一致するので、Source-backed の理由文になる。
    assert after.get("reason") == (
        "一Need試験神社の公式の祈願案内に『商売繁盛』の記載があります。"
        "今の悩みや願いに合わせて参拝先の候補に入れています。"
    )
    assert after.get("_reason_facts") == before.get("_reason_facts")
    assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in after


@pytest.mark.django_db
def test_concierge_like_three_need_path_is_additive(monkeypatch, _no_llm):
    for name in ("商売繁盛", "学業成就", "厄除け"):
        _tag(name)
    shrine = _shrine("三Need試験神社")
    _fact(shrine, "pf-0001", "商売繁盛")
    _fact(shrine, "pf-0002", "学業成就")
    _fact(shrine, "pf-0003", "厄除け")
    needs = ["money", "study", "protection"]

    _install(monkeypatch)
    before = _row(_recommend(needs), "三Need試験神社")
    _install(monkeypatch, ("pf-0001", "商売繁盛"), ("pf-0002", "学業成就"), ("pf-0003", "厄除け"))
    after = _row(_recommend(needs), "三Need試験神社")
    # money / study / protection はそれぞれ B だけ（study は focus にも属するが request に無い）。
    assert _rank_weighted(after) - _rank_weighted(before) == pytest.approx(6.0)
    assert after["breakdown"]["score_need"] == before["breakdown"]["score_need"]


@pytest.mark.django_db
def test_g5_and_goriyaku_writes_are_unchanged(monkeypatch, _no_llm):
    _tag("商売繁盛")
    only_fact = _shrine("Bのみ不適格神社", eligible=False)
    _fact(only_fact, "pf-0009", "商売繁盛")
    _install(monkeypatch, ("pf-0009", "商売繁盛"))
    recs = _recommend(["money"])
    assert all(r.get("name") != "Bのみ不適格神社" for r in recs["recommendations"])
    assert only_fact.goriyaku_tags.count() == 0
    assert ShrineGoriyakuAssignment.objects.count() == 0


@pytest.mark.django_db
def test_carrier_still_stripped_from_public_concierge_response(client, monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    _tag("金運")
    shrine = _shrine("公開試験神社")
    _fact(shrine, "pf-0100", "金運祈願")
    _install(monkeypatch, ("pf-0100", "金運"))
    response = client.post(
        "/api/concierge/chat/",
        data=json.dumps({"query": "金運を上げたい", "lat": 35.0, "lng": 139.0}),
        content_type="application/json",
    )
    assert response.status_code == 200
    raw = json.dumps(response.json(), ensure_ascii=False)
    assert CHANNEL_B_TYPED_NEED_MATCHES_KEY not in raw
    assert "_channel_b_reason_provenance" not in raw
    assert "source_fact_key" not in raw
    assert "pf-0100" not in raw
    # MS-5: source wording は Source-backed の理由文の中にだけ現れる（carrier としては出ない）。
    reason = next(
        r for r in response.json()["data"]["recommendations"] if r.get("name") == "公開試験神社"
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
    row = _candidate(_match("money"))
    resolve_llm_route(query="金運", valid_candidates=[row], need_tags=["money"], llm_enabled=True)
    assert received and all(CHANNEL_B_TYPED_NEED_MATCHES_KEY not in c for c in received)
