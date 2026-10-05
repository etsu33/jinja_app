"""W0-DB04 PR-D: 凍結した 23 件の ShrineSourceFact と 3 件の Source を Knowledge Seed 1.2 で持つ。

対象: wave0-021 大阪天満宮（7）/ wave0-025 大崎八幡宮（16）。
wave0-019 建勲神社（DIRECT_OFFICIAL_GOSHINTOKU_WORDING、Channel A 側）/ wave0-020 / wave0-022 は対象外。

stable_key（MS-1）: {shrine_slug}__{fact_type}__{fact_slug}
PR-D は data のみ。Source Fact Mapping Registry / goriyaku_tags / Recommendation は変えない
（mapping の有効化は PR-E）。既存の G4 Knowledge Seed（wave0_batch_04_seed.json）は変えない。
"""

from __future__ import annotations

import copy
import io
import json
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from temples.models import (
    GoriyakuTag,
    Shrine,
    ShrineGoriyakuAssignment,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.services.channel_b_typed_need_match import fetch_typed_need_matches
from temples.services.concierge_chat_candidates import build_chat_candidates_with_eligibility
from temples.services.knowledge_seed import (
    SOURCE_FACT_SCHEMA_VERSION,
    normalize_source_url,
    parse_seed,
)
from temples.domain.source_fact_mapping_registry_v1 import get_registry
from temples.tests.support.recommendation_eligibility import attach_usable_deity_fact

TEMPLES_DIR = Path(__file__).resolve().parents[1]
SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "wave0_batch_04_source_facts_seed.json"
G4_SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "wave0_batch_04_seed.json"

OSAKA = ("大阪天満宮", "大阪府大阪市北区天神橋2丁目1番8号")
OSAKI = ("大崎八幡宮", "宮城県仙台市青葉区八幡4-6-1")

SOURCE_A = "w0-db04-osaka-tenmangu-gokito-official"
SOURCE_B = "w0-db04-osaka-tenmangu-r8-torinuke-official"
SOURCE_C = "w0-db04-oosaki-hachiman-gokigan-official"

FROZEN_VERIFIED_AT = "2026-10-05T00:00:00+09:00"

# Mother Ship が凍結した Source（key: publisher / title / url）。
FROZEN_SOURCES = {
    SOURCE_A: ("大阪天満宮", "ご祈祷・ご祈願", "https://osakatemmangu.or.jp/gokito"),
    SOURCE_B: ("大阪天満宮", "令和8年の通り抜け参拝について", "https://osakatemmangu.or.jp/3944"),
    SOURCE_C: (
        "大崎八幡宮",
        "御祈願の神札",
        "https://www.oosaki-hachiman.or.jp/event/shinsyun/doc/ofuda.pdf",
    ),
}

# (stable_key, source_attested_wording, source_key) — 凍結順。
FROZEN_OSAKA = [
    ("osaka_tenmangu__prayer_and_current_guidance__shiken_gokaku", "試験合格", SOURCE_A),
    ("osaka_tenmangu__prayer_and_current_guidance__gakugyo_joju", "学業成就", SOURCE_A),
    ("osaka_tenmangu__prayer_and_current_guidance__yakuyoke", "厄除け", SOURCE_A),
    ("osaka_tenmangu__prayer_and_current_guidance__kotsu_anzen", "交通安全", SOURCE_A),
    ("osaka_tenmangu__prayer_and_current_guidance__shobai_hanjo", "商売繁昌", SOURCE_A),
    ("osaka_tenmangu__prayer_and_current_guidance__shushoku_joju", "就職成就", SOURCE_B),
    ("osaka_tenmangu__prayer_and_current_guidance__gakutoku_kojo", "学徳向上", SOURCE_B),
]
FROZEN_OSAKI = [
    (f"osaki_hachimangu__prayer__{slug}", wording, SOURCE_C)
    for slug, wording in [
        ("kanai_anzen", "家内安全"),
        ("shobai_hanjo", "商売繁昌"),
        ("kotsu_anzen", "交通安全"),
        ("yakuyoke", "厄除"),
        ("hoyoke", "方除"),
        ("gakugyo_joju", "学業成就"),
        ("gokaku_kigan", "合格祈願"),
        ("hissho", "必勝"),
        ("shintai_kengo", "身体堅固"),
        ("byoki_heiyu", "病気平癒"),
        ("kaiun_yakuyoke", "開運厄除"),
        ("sainan_shofuku", "災難招福"),
        ("shingan_joju", "心願成就"),
        ("ryoen", "良縁"),
        ("anzan", "安産"),
        ("ryoko_anzen", "旅行安全"),
    ]
]
FROZEN_ALL = FROZEN_OSAKA + FROZEN_OSAKI
OSAKA_CHARACTERIZATION = "official_prayer_and_current_guidance_list_level"
OSAKI_CHARACTERIZATION = "official_prayer_supported"

MS1_STABLE_KEY = re.compile(
    r"^[a-z0-9]+(?:_[a-z0-9]+)*__[a-z0-9]+(?:_[a-z0-9]+)*__[a-z0-9]+(?:_[a-z0-9]+)*$"
)


def _raw() -> dict:
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def _seed():
    parsed = parse_seed(_raw())
    assert parsed.errors == []
    return parsed


def _facts_by_shrine():
    return {(block.name_jp, block.address): block.source_facts for block in _seed().shrines}


# ---------- seed（A〜M）----------


def test_a_b_c_exactly_23_facts_7_osaka_16_osaki():
    seed = _seed()
    assert seed.schema_version == SOURCE_FACT_SCHEMA_VERSION
    by_shrine = _facts_by_shrine()
    assert list(by_shrine) == [OSAKA, OSAKI]
    assert len(by_shrine[OSAKA]) == 7
    assert len(by_shrine[OSAKI]) == 16
    assert sum(len(facts) for facts in by_shrine.values()) == 23
    for block in seed.shrines:
        assert (block.deities, block.histories, block.collectives) == ([], [], [])


def test_excluded_candidates_are_absent():
    raw_text = SEED_PATH.read_text(encoding="utf-8")
    for name in ("建勲神社", "水堂須佐男神社", "毛谷黒龍神社", "kenkun"):
        assert name not in raw_text


def test_d_e_f_stable_keys_and_wording_match_the_frozen_list_exactly():
    by_shrine = _facts_by_shrine()
    actual = [
        (fact.stable_key, fact.source_attested_wording, fact.source_keys)
        for facts in by_shrine.values()
        for fact in facts
    ]
    assert actual == [(key, wording, [source]) for key, wording, source in FROZEN_ALL]
    keys = [key for key, _w, _s in actual]
    assert len(set(keys)) == 23
    for key in keys:
        assert MS1_STABLE_KEY.match(key), key
        assert key.isascii() and key == key.lower(), key
        assert not re.search(r"wave0|w0|db04|batch|\d{3,}", key), key
    # 既存の Source Fact / seed と衝突しない
    for path in SEED_PATH.parent.glob("*.json"):
        if path != SEED_PATH:
            text = path.read_text(encoding="utf-8")
            assert not any(key in text for key in keys), path.name


def test_g_h_characterizations_are_the_frozen_ones():
    by_shrine = _facts_by_shrine()
    assert {f.evidence_characterization for f in by_shrine[OSAKA]} == {OSAKA_CHARACTERIZATION}
    assert {f.evidence_characterization for f in by_shrine[OSAKI]} == {OSAKI_CHARACTERIZATION}


def test_i_j_m_source_bindings_are_the_frozen_ones():
    by_shrine = _facts_by_shrine()
    osaka_sources = [f.source_keys for f in by_shrine[OSAKA]]
    assert osaka_sources.count([SOURCE_A]) == 5
    assert osaka_sources.count([SOURCE_B]) == 2
    assert all(f.source_keys == [SOURCE_C] for f in by_shrine[OSAKI])
    assert all(f.source_keys for facts in by_shrine.values() for f in facts)


def test_k_fact_verification_metadata():
    for block in _raw()["shrines"]:
        for fact in block["source_facts"]:
            assert fact["verification_status"] == "source_confirmed"
            assert fact["confidence"] == "high"
            assert fact["verified_at"] == FROZEN_VERIFIED_AT
    for facts in _facts_by_shrine().values():
        for fact in facts:
            assert fact.verified_at.isoformat() == FROZEN_VERIFIED_AT


def test_l_exactly_three_sources_with_frozen_metadata():
    raw_sources = {source["key"]: source for source in _raw()["sources"]}
    assert set(raw_sources) == set(FROZEN_SOURCES)
    parsed = _seed().sources
    for key, (publisher, title, url) in FROZEN_SOURCES.items():
        raw = raw_sources[key]
        source = parsed[key]
        assert (source.publisher, source.title, source.url) == (publisher, title, url)
        assert source.source_type == "shrine_official"
        assert source.language == "ja"
        assert (source.verification_status, source.confidence) == ("source_confirmed", "high")
        assert raw["verified_at"] == FROZEN_VERIFIED_AT
        assert source.verified_at.isoformat() == FROZEN_VERIFIED_AT
        # 凍結されていない値は作らない（accessed_at を verified_at から作らない、bibliography なし）。
        assert "accessed_at" not in raw and source.accessed_at is None
        assert source.bibliography == ""
        assert normalize_source_url(source.url) == url


def test_g4_knowledge_seed_is_not_modified_by_pr_d():
    raw = json.loads(G4_SEED_PATH.read_text(encoding="utf-8"))
    assert raw["schema_version"] == "1.0"
    assert all("source_facts" not in block for block in raw["shrines"])


# ---------- import（N / O / Source identity）----------


def _shrines() -> dict:
    out = {}
    for name, address in (OSAKA, OSAKI):
        shrine = Shrine.objects.create(
            name_jp=name, kind="shrine", address=address, latitude=35.0, longitude=139.0
        )
        attach_usable_deity_fact(shrine)
        out[name] = shrine
    return out


def _run(path) -> str:
    out = io.StringIO()
    call_command("import_shrine_knowledge", str(path), stdout=out, stderr=io.StringIO())
    return out.getvalue()


@pytest.mark.django_db
def test_import_materializes_23_facts_with_url_backed_sources():
    shrines = _shrines()
    sources_before = ShrineKnowledgeSource.objects.count()
    _run(SEED_PATH)

    assert ShrineKnowledgeSource.objects.count() == sources_before + 3
    by_url = {s.url: s for s in ShrineKnowledgeSource.objects.filter(source_type="shrine_official")}
    for publisher, title, url in FROZEN_SOURCES.values():
        source = by_url[url]
        assert (source.publisher, source.title, source.language) == (publisher, title, "ja")
        assert (source.verification_status, source.confidence) == ("source_confirmed", "high")
        assert source.verified_at.isoformat() == "2026-10-04T15:00:00+00:00"
        assert source.accessed_at is None

    facts = {f.stable_key: f for f in ShrineSourceFact.objects.all()}
    assert len(facts) == 23
    for key, wording, source_key in FROZEN_ALL:
        fact = facts[key]
        expected_shrine = shrines["大阪天満宮" if key.startswith("osaka_") else "大崎八幡宮"]
        assert fact.shrine_id == expected_shrine.id
        assert fact.source_attested_wording == wording
        assert [s.url for s in fact.sources.all()] == [FROZEN_SOURCES[source_key][2]]
        assert (fact.verification_status, fact.confidence) == ("source_confirmed", "high")
    assert ShrineSourceFact.objects.filter(shrine=shrines["大阪天満宮"]).count() == 7
    assert ShrineSourceFact.objects.filter(shrine=shrines["大崎八幡宮"]).count() == 16


@pytest.mark.django_db
def test_n_reimport_is_idempotent():
    _shrines()
    _run(SEED_PATH)
    facts_before = list(ShrineSourceFact.objects.order_by("id").values())
    sources_before = list(ShrineKnowledgeSource.objects.order_by("id").values())
    out = _run(SEED_PATH)
    assert "source_facts created=0" in out
    assert out.count("[source_fact] SKIP_EXISTS") == 23
    assert list(ShrineSourceFact.objects.order_by("id").values()) == facts_before
    assert list(ShrineKnowledgeSource.objects.order_by("id").values()) == sources_before


@pytest.mark.django_db
def test_o_stable_key_conflict_fails_closed(tmp_path):
    _shrines()
    _run(SEED_PATH)
    before = list(ShrineSourceFact.objects.order_by("id").values())
    changed = _raw()
    changed["shrines"][1]["source_facts"][3]["source_attested_wording"] = "厄除け"
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
    out, err = io.StringIO(), io.StringIO()
    with pytest.raises(CommandError, match="import blocked"):
        call_command("import_shrine_knowledge", str(path), stdout=out, stderr=err)
    assert "SOURCE_FACT_CONFLICT" in out.getvalue() + err.getvalue()
    assert list(ShrineSourceFact.objects.order_by("id").values()) == before


@pytest.mark.django_db
def test_existing_identical_url_source_is_reused_not_duplicated():
    _shrines()
    publisher, title, url = FROZEN_SOURCES[SOURCE_C]
    existing = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title=title,
        publisher=publisher,
        url=url,
        language="ja",
        verification_status="source_confirmed",
        confidence="high",
        verified_at="2026-10-05T00:00:00+09:00",
    )
    _run(SEED_PATH)
    assert ShrineKnowledgeSource.objects.filter(url=url).count() == 1
    fact = ShrineSourceFact.objects.get(stable_key="osaki_hachimangu__prayer__kanai_anzen")
    assert list(fact.sources.all()) == [existing]


@pytest.mark.django_db
def test_title_only_source_of_another_shrine_is_never_reused():
    _shrines()
    other = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="御祈願の神札",  # 同じ title、URL なし（別神社の Source を想定）
        publisher="別の神社",
        verification_status="source_confirmed",
        confidence="high",
        verified_at="2026-10-05T00:00:00+09:00",
    )
    _run(SEED_PATH)
    fact = ShrineSourceFact.objects.get(stable_key="osaki_hachimangu__prayer__anzan")
    (source,) = fact.sources.all()
    assert source.pk != other.pk
    assert source.url == FROZEN_SOURCES[SOURCE_C][2]


@pytest.mark.django_db
def test_conflicting_existing_url_source_blocks_the_import():
    _shrines()
    publisher, title, url = FROZEN_SOURCES[SOURCE_A]
    ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title=title,
        publisher="別の発行者",
        url=url,
        verification_status="source_confirmed",
        confidence="high",
        verified_at="2026-10-05T00:00:00+09:00",
    )
    out, err = io.StringIO(), io.StringIO()
    with pytest.raises(CommandError, match="import blocked"):
        call_command("import_shrine_knowledge", str(SEED_PATH), stdout=out, stderr=err)
    assert ShrineSourceFact.objects.count() == 0


# ---------- Recommendation boundary（P / Q / R）----------


def test_p_no_mapping_registry_entry_for_any_pr_d_stable_key():
    registry = get_registry()
    for key, _wording, _source in FROZEN_ALL:
        assert registry.lookup(key) is None, key


@pytest.mark.django_db
def test_q_no_goriyaku_tag_or_assignment_is_created():
    shrines = _shrines()
    tags_before = GoriyakuTag.objects.count()
    _run(SEED_PATH)
    assert GoriyakuTag.objects.count() == tags_before
    assert ShrineGoriyakuAssignment.objects.count() == 0
    for shrine in shrines.values():
        assert list(shrine.goriyaku_tags.all()) == []


@pytest.mark.django_db
def test_r_recommendation_candidates_unchanged_before_pr_e():
    shrines = _shrines()
    before = build_chat_candidates_with_eligibility(lat=35.0, lng=139.0, trace_id="pr-d").candidates
    _run(SEED_PATH)
    after = build_chat_candidates_with_eligibility(lat=35.0, lng=139.0, trace_id="pr-d").candidates
    assert after == before
    assert fetch_typed_need_matches([s.id for s in shrines.values()]) == {}


def test_seed_inputs_are_not_mutated_by_parsing():
    raw = _raw()
    snapshot = copy.deepcopy(raw)
    parse_seed(raw)
    assert raw == snapshot
