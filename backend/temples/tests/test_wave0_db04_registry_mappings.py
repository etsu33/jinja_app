"""W0-DB04 PR-E: MS-2 で承認・凍結した Source Fact → canonical concept の mapping 16 件。

registry（source_fact_mapping_registry_v1）は repository が正本。concept は既存 GoriyakuTag.name の
exact name で参照し、DB の id は持たない。AMBIGUOUS 7 件は record を持たない（absence）。
方除 → 方除け は承認済みだが、方除け は現行のどの Need からも参照されないため Need 一致を作らない。

PR-E は registry の data だけを足す。Source Fact の wording・Need mapping・scoring・goriyaku_tags は変えない。
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.domain.need_to_goriyaku_tag_ids import NEED_TO_GORIYAKU_IDS
from temples.domain.source_fact_mapping_registry_v1 import (
    REGISTRY_VERSION,
    SOURCE_FACT_MAPPING_RECORDS,
    SourceFactMappingRecord,
    get_registry,
    lookup_source_fact_mapping,
    validate_registry_db_consistency,
    validate_registry_static,
)
from temples.models import GoriyakuTag, Shrine, ShrineGoriyakuAssignment, ShrineSourceFact
from temples.services.channel_b_typed_need_match import (
    CHANNEL_B_TYPED_NEED_MATCHES_KEY,
    fetch_typed_need_matches,
)
from temples.services.concierge_chat_candidates import build_chat_candidates_with_eligibility
from temples.services.knowledge_seed import parse_seed
from temples.tests.support.recommendation_eligibility import attach_usable_deity_fact
from temples.tests.test_bootstrap_goriyaku_master_exact39_contract import CANONICAL_MASTER

SEED_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "knowledge_seeds"
    / "wave0_batch_04_source_facts_seed.json"
)
OSAKA = ("大阪天満宮", "大阪府大阪市北区天神橋2丁目1番8号")
OSAKI = ("大崎八幡宮", "宮城県仙台市青葉区八幡4-6-1")
CANONICAL_ID_BY_NAME = {name: tag_id for tag_id, name in CANONICAL_MASTER}

# MS-2（Mother Ship 承認・凍結）。(source_fact_key, canonical_concept_name, classification)
FROZEN_EXACT = [
    ("osaka_tenmangu__prayer_and_current_guidance__gakugyo_joju", "学業成就"),
    ("osaka_tenmangu__prayer_and_current_guidance__yakuyoke", "厄除け"),
    ("osaka_tenmangu__prayer_and_current_guidance__kotsu_anzen", "交通安全"),
    ("osaki_hachimangu__prayer__kanai_anzen", "家内安全"),
    ("osaki_hachimangu__prayer__kotsu_anzen", "交通安全"),
    ("osaki_hachimangu__prayer__gakugyo_joju", "学業成就"),
    ("osaki_hachimangu__prayer__gokaku_kigan", "合格祈願"),
    ("osaki_hachimangu__prayer__byoki_heiyu", "病気平癒"),
    ("osaki_hachimangu__prayer__shingan_joju", "心願成就"),
    ("osaki_hachimangu__prayer__anzan", "安産"),
]
FROZEN_SAFE_NORMALIZATION = [
    ("osaka_tenmangu__prayer_and_current_guidance__shiken_gokaku", "合格祈願"),
    ("osaka_tenmangu__prayer_and_current_guidance__shobai_hanjo", "商売繁盛"),
    ("osaki_hachimangu__prayer__shobai_hanjo", "商売繁盛"),
    ("osaki_hachimangu__prayer__yakuyoke", "厄除け"),
    ("osaki_hachimangu__prayer__hoyoke", "方除け"),
    ("osaki_hachimangu__prayer__hissho", "勝運"),
]
FROZEN_RECORDS = [(k, c, "EXACT") for k, c in FROZEN_EXACT] + [
    (k, c, "SAFE_NORMALIZATION") for k, c in FROZEN_SAFE_NORMALIZATION
]
FROZEN_AMBIGUOUS = [
    "osaka_tenmangu__prayer_and_current_guidance__shushoku_joju",
    "osaka_tenmangu__prayer_and_current_guidance__gakutoku_kojo",
    "osaki_hachimangu__prayer__shintai_kengo",
    "osaki_hachimangu__prayer__kaiun_yakuyoke",
    "osaki_hachimangu__prayer__sainan_shofuku",
    "osaki_hachimangu__prayer__ryoen",
    "osaki_hachimangu__prayer__ryoko_anzen",
]
HOYOKE_KEY = "osaki_hachimangu__prayer__hoyoke"


def _records() -> list[tuple[str, str, str]]:
    return [
        (r.source_fact_key, r.canonical_concept_name, r.mapping_classification)
        for r in SOURCE_FACT_MAPPING_RECORDS
    ]


def _pr_d_wording_by_key() -> dict[str, str]:
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))
    assert seed.errors == []
    return {
        fact.stable_key: fact.source_attested_wording
        for block in seed.shrines
        for fact in block.source_facts
    }


def _need_reachable(concept_name: str) -> bool:
    tag_id = CANONICAL_ID_BY_NAME[concept_name]
    return any(tag_id in ids for ids in NEED_TO_GORIYAKU_IDS.values())


# ---------- registry の内容（1〜8 / 10）----------


def test_1_registry_contains_exactly_the_16_frozen_mappings():
    assert REGISTRY_VERSION == "source_fact_mapping_registry_v1"
    assert _records() == FROZEN_RECORDS
    assert validate_registry_static() == ()
    assert get_registry().records == SOURCE_FACT_MAPPING_RECORDS


def test_2_classification_counts():
    classes = [cls for _k, _c, cls in _records()]
    assert classes.count("EXACT") == 10
    assert classes.count("SAFE_NORMALIZATION") == 6
    assert len(classes) == 16


def test_3_source_fact_keys_are_unique():
    keys = [k for k, _c, _cls in _records()]
    assert len(set(keys)) == 16


def test_4_concepts_are_exact_canonical_names_not_ids():
    canonical_names = {name for _id, name in CANONICAL_MASTER}
    for record in SOURCE_FACT_MAPPING_RECORDS:
        assert isinstance(record.canonical_concept_name, str)
        assert record.canonical_concept_name in canonical_names, record


def test_5_every_mapping_key_is_a_pr_d_source_fact():
    pr_d_keys = set(_pr_d_wording_by_key())
    assert len(pr_d_keys) == 23
    assert {k for k, _c, _cls in _records()} <= pr_d_keys


def test_6_ambiguous_keys_have_no_registry_entry():
    pr_d_keys = set(_pr_d_wording_by_key())
    registry = get_registry()
    for key in FROZEN_AMBIGUOUS:
        assert key in pr_d_keys, key
        assert registry.lookup(key) is None, key
    assert pr_d_keys - {k for k, _c, _cls in _records()} == set(FROZEN_AMBIGUOUS)


def test_7_exact_lookup_returns_the_frozen_mapping():
    for key, concept, cls in FROZEN_RECORDS:
        assert lookup_source_fact_mapping(key) == SourceFactMappingRecord(key, concept, cls)


@pytest.mark.parametrize(
    "key",
    [
        "osaki_hachimangu__prayer__unknown",
        "OSAKI_HACHIMANGU__PRAYER__KANAI_ANZEN",
        " osaki_hachimangu__prayer__kanai_anzen",
        "家内安全",
        None,
        23,
    ],
)
def test_8_unknown_or_non_exact_key_is_no_signal(key):
    assert lookup_source_fact_mapping(key) is None


def test_10_hoyoke_maps_to_hoyoke_canonical_concept():
    record = lookup_source_fact_mapping(HOYOKE_KEY)
    assert record == SourceFactMappingRecord(HOYOKE_KEY, "方除け", "SAFE_NORMALIZATION")


def test_11_hoyoke_has_no_need_and_15_mappings_are_need_reachable():
    assert not _need_reachable("方除け")
    reachable = [k for k, concept, _cls in _records() if _need_reachable(concept)]
    assert len(reachable) == 15
    assert HOYOKE_KEY not in reachable


# ---------- DB（4 / 9 / 11 / 12 / 13）----------


def _tags() -> None:
    for tag_id, name in CANONICAL_MASTER:
        GoriyakuTag.objects.get_or_create(id=tag_id, name=name)


def _shrines() -> dict:
    out = {}
    for i, (name, address) in enumerate((OSAKA, OSAKI)):
        shrine = Shrine.objects.create(
            name_jp=name, kind="shrine", address=address, latitude=35.0 + i, longitude=139.0
        )
        attach_usable_deity_fact(shrine)
        out[name] = shrine
    return out


def _import() -> None:
    call_command(
        "import_shrine_knowledge", str(SEED_PATH), stdout=io.StringIO(), stderr=io.StringIO()
    )


@pytest.mark.django_db
def test_4_registry_is_consistent_with_the_db_after_pr_d_import():
    _tags()
    _shrines()
    _import()
    assert validate_registry_db_consistency() == ()


@pytest.mark.django_db
def test_9_safe_normalization_keeps_source_fact_wording():
    _tags()
    shrines = _shrines()
    _import()
    wording = _pr_d_wording_by_key()
    stored = dict(ShrineSourceFact.objects.values_list("stable_key", "source_attested_wording"))
    assert stored == wording  # 23 件とも PR-D の wording のまま
    matches = fetch_typed_need_matches([s.id for s in shrines.values()])
    by_key = {m.source_fact_key: m for ms in matches.values() for m in ms}
    for key, concept in FROZEN_SAFE_NORMALIZATION:
        if key == HOYOKE_KEY:
            continue
        match = by_key[key]
        assert match.canonical_concept_name == concept
        assert match.source_attested_wording == wording[key] != concept
    assert by_key["osaki_hachimangu__prayer__shobai_hanjo"].source_attested_wording == "商売繁昌"


@pytest.mark.django_db
def test_11_hoyoke_resolves_but_produces_no_need_match():
    _tags()
    shrines = _shrines()
    _import()
    matches = fetch_typed_need_matches([s.id for s in shrines.values()])
    keys_with_need = {m.source_fact_key for ms in matches.values() for m in ms}
    assert HOYOKE_KEY not in keys_with_need
    assert keys_with_need == {k for k, c, _cls in FROZEN_RECORDS if _need_reachable(c)}
    assert len(keys_with_need) == 15
    assert not keys_with_need & set(FROZEN_AMBIGUOUS)


@pytest.mark.django_db
def test_12_no_goriyaku_tag_assignment_or_tag_ids_are_written():
    _tags()
    shrines = _shrines()
    _import()
    candidates = build_chat_candidates_with_eligibility(
        lat=35.0, lng=139.0, trace_id="pr-e"
    ).candidates
    assert ShrineGoriyakuAssignment.objects.count() == 0
    for shrine in shrines.values():
        assert list(shrine.goriyaku_tags.all()) == []
    for candidate in candidates:
        assert candidate["goriyaku_tag_ids"] == []
        assert CHANNEL_B_TYPED_NEED_MATCHES_KEY in candidate


@pytest.mark.django_db
def test_13_channel_a_fields_are_unchanged_by_the_registry(monkeypatch):
    from temples.domain import source_fact_mapping_registry_v1 as registry_module

    _tags()
    _shrines()
    _import()
    with_registry = build_chat_candidates_with_eligibility(
        lat=35.0, lng=139.0, trace_id="pr-e"
    ).candidates
    monkeypatch.setattr(registry_module, "_default_registry", registry_module.build_registry(()))
    without_registry = build_chat_candidates_with_eligibility(
        lat=35.0, lng=139.0, trace_id="pr-e"
    ).candidates
    stripped = [
        {k: v for k, v in c.items() if k != CHANNEL_B_TYPED_NEED_MATCHES_KEY} for c in with_registry
    ]
    assert stripped == without_registry
    assert all(CHANNEL_B_TYPED_NEED_MATCHES_KEY not in c for c in without_registry)
