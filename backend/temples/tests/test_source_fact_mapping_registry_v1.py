"""S3a versioned code registry foundation（PR-B / Policy C / Channel B）。

契約: docs/audit/shrine-expansion-wave0-db04-f1-goriyaku-mapping-boundary.md
§12.9.8（S3a）/ §12.12.8（concept = canonical name）/ §12.15.H〜J（record / validator）。

registry は Recommendation から読まれない（PR-C 以降）。W0-DB04 の実 mapping は持たない（PR-E）。
test の record と ShrineSourceFact はすべて synthetic である。
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
from django.utils import timezone

from temples.domain import source_fact_mapping_registry_v1 as registry_module
from temples.domain.source_fact_mapping_registry_v1 import (
    ALLOWED_MAPPING_CLASSIFICATIONS,
    REGISTRY_VERSION,
    SOURCE_FACT_MAPPING_RECORD_FIELDS,
    SOURCE_FACT_MAPPING_RECORDS,
    SourceFactMappingRecord,
    SourceFactMappingRegistryError,
    build_registry,
    get_registry,
    lookup_source_fact_mapping,
    validate_registry_db_consistency,
    validate_registry_static,
)
from temples.models import (
    GoriyakuTag,
    Shrine,
    ShrineGoriyakuAssignment,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.services.concierge_chat_candidates import build_chat_candidates_with_eligibility
from temples.tests.support.recommendation_eligibility import attach_usable_deity_fact
from temples.tests.test_bootstrap_goriyaku_master_exact39_contract import CANONICAL_MASTER

SHRINE_NAME = "対応表試験神社"
CONCEPT_NAME = "商売繁盛"
FACT_KEY = "synthetic-registry-fact-0001"


def _record(**overrides) -> SourceFactMappingRecord:
    values = {
        "source_fact_key": FACT_KEY,
        "canonical_concept_name": CONCEPT_NAME,
        "mapping_classification": "EXACT",
    }
    values.update(overrides)
    return SourceFactMappingRecord(**values)


def _shrine() -> Shrine:
    return Shrine.objects.create(name_jp=SHRINE_NAME, kind="shrine", address="東京都試験区4-4-4")


def _fact(shrine: Shrine, key: str = FACT_KEY) -> ShrineSourceFact:
    fact = ShrineSourceFact.objects.create(
        shrine=shrine,
        stable_key=key,
        source_attested_wording=CONCEPT_NAME,
        evidence_characterization="official_prayer_supported",
        verification_status="source_confirmed",
        confidence="high",
        verified_at=timezone.now(),
    )
    fact.sources.add(
        ShrineKnowledgeSource.objects.create(
            source_type="shrine_official",
            title="ご祈祷案内",
            verification_status="source_confirmed",
            verified_at=timezone.now(),
        )
    )
    return fact


# ---------- version / repository registry ----------


def test_t1_registry_version_is_pinned():
    assert REGISTRY_VERSION == "source_fact_mapping_registry_v1"
    assert get_registry().version == REGISTRY_VERSION


def test_repository_registry_is_an_empty_foundation():
    """PR-B は W0-DB04 の実 mapping を持たない（PR-E が Mother Ship の承認後に追加する）。"""
    assert SOURCE_FACT_MAPPING_RECORDS == ()
    assert isinstance(SOURCE_FACT_MAPPING_RECORDS, tuple)
    assert validate_registry_static() == ()
    assert get_registry().records == ()


def test_repository_registry_concepts_are_within_the_canonical_master():
    """record が追加されたとき（PR-E）、concept は既存の canonical 39 の name に限る。"""
    canonical_names = {name for _, name in CANONICAL_MASTER}
    assert len(canonical_names) == 39
    assert {r.canonical_concept_name for r in SOURCE_FACT_MAPPING_RECORDS} <= canonical_names


@pytest.mark.parametrize("version", ["", "  ", None, 1, " source_fact_mapping_registry_v1"])
def test_invalid_registry_version_fails(version):
    errors = validate_registry_static((), version)
    assert any(e.startswith("registry_version:") for e in errors)


# ---------- record shape ----------


def test_t23_t24_t25_record_has_exactly_the_three_frozen_fields():
    assert SOURCE_FACT_MAPPING_RECORD_FIELDS == (
        "source_fact_key",
        "canonical_concept_name",
        "mapping_classification",
    )
    forbidden = {
        "need",
        "need_key",
        "goriyaku_tag_id",
        "concept_id",
        "id",
        "wording",
        "source_attested_wording",
        "evidence_characterization",
        "url",
        "publisher",
        "confidence",
        "verified_at",
        "shrine",
        "lifecycle",
        "rationale",
        "score",
    }
    assert not forbidden & set(SOURCE_FACT_MAPPING_RECORD_FIELDS)


def test_record_and_registry_are_immutable():
    record = _record()
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.canonical_concept_name = "厄除け"
    registry = build_registry((record,))
    with pytest.raises(TypeError):
        registry._by_key["other"] = record
    with pytest.raises(dataclasses.FrozenInstanceError):
        registry.records = ()
    for name in ("create", "update", "delete", "register", "add", "set"):
        assert not hasattr(registry, name)
        assert not hasattr(registry_module, name)


def test_allowed_classifications_are_exactly_exact_and_safe_normalization():
    assert ALLOWED_MAPPING_CLASSIFICATIONS == frozenset({"EXACT", "SAFE_NORMALIZATION"})


# ---------- static validation ----------


def test_t2_valid_exact_record_passes_static_validation():
    assert validate_registry_static((_record(),)) == ()


def test_t3_valid_safe_normalization_record_passes_static_validation():
    assert validate_registry_static((_record(mapping_classification="SAFE_NORMALIZATION"),)) == ()


@pytest.mark.parametrize("key", ["", "   ", None, 12, " leading", "trailing "])
def test_t4_blank_or_invalid_source_fact_key_fails(key):
    errors = validate_registry_static((_record(source_fact_key=key),))
    assert any("records[0].source_fact_key:" in e for e in errors)


def test_t5_duplicate_source_fact_key_fails_and_is_not_overwritten():
    records = (_record(), _record(canonical_concept_name="厄除け"))
    errors = validate_registry_static(records)
    assert any(
        "records[1].source_fact_key: duplicate 'synthetic-registry-fact-0001'" in e for e in errors
    )
    with pytest.raises(SourceFactMappingRegistryError):
        build_registry(records)


@pytest.mark.parametrize("name", ["", "   ", None, 4, " 商売繁盛"])
def test_t6_blank_or_non_name_concept_fails(name):
    """concept は canonical name（文字列）だけ。DB の id（int）は受け付けない（V10）。"""
    errors = validate_registry_static((_record(canonical_concept_name=name),))
    assert any("records[0].canonical_concept_name:" in e for e in errors)


@pytest.mark.parametrize("classification", ["", None, "exact", "UNKNOWN", "PARTIAL", "NEGATIVE"])
def test_t7_unknown_classification_fails(classification):
    errors = validate_registry_static((_record(mapping_classification=classification),))
    assert any("records[0].mapping_classification: invalid value" in e for e in errors)


@pytest.mark.parametrize("classification", ["AMBIGUOUS", "NO_CANONICAL_TAG"])
def test_t8_t9_ambiguous_and_no_canonical_tag_are_rejected(classification):
    errors = validate_registry_static((_record(mapping_classification=classification),))
    assert any("must not be a positive mapping" in e for e in errors)


def test_non_record_element_fails():
    errors = validate_registry_static(({"source_fact_key": FACT_KEY},))
    assert any("must be a SourceFactMappingRecord" in e for e in errors)


def test_invalid_registry_fails_closed_without_skipping_entries():
    with pytest.raises(SourceFactMappingRegistryError) as exc:
        build_registry((_record(source_fact_key="ok-0001"), _record(mapping_classification="X")))
    assert exc.value.errors


def test_invalid_repository_registry_blocks_lookup(monkeypatch):
    monkeypatch.setattr(
        registry_module, "SOURCE_FACT_MAPPING_RECORDS", (_record(mapping_classification="X"),)
    )
    monkeypatch.setattr(registry_module, "_default_registry", None)
    with pytest.raises(SourceFactMappingRegistryError):
        lookup_source_fact_mapping(FACT_KEY)


# ---------- lookup ----------


def test_t13_lookup_returns_the_approved_record():
    record = _record()
    assert build_registry((record,)).lookup(FACT_KEY) is record


def test_t14_unmapped_key_returns_none():
    registry = build_registry((_record(),))
    assert registry.lookup("synthetic-registry-fact-unmapped") is None
    assert lookup_source_fact_mapping("synthetic-registry-fact-unmapped") is None


def test_lookup_is_exact_without_normalization():
    registry = build_registry((_record(),))
    for variant in (FACT_KEY.upper(), f" {FACT_KEY}", f"{FACT_KEY} ", FACT_KEY[:-1]):
        assert registry.lookup(variant) is None


@pytest.mark.django_db
def test_t15_lookup_does_not_use_database_primary_key():
    fact = _fact(_shrine())
    registry = build_registry((_record(),))
    assert registry.lookup(fact.pk) is None
    assert registry.lookup(str(fact.pk)) is None
    assert registry.lookup(fact.stable_key).source_fact_key == fact.stable_key


# ---------- DB consistency ----------


@pytest.mark.django_db
def test_t10_valid_fact_and_canonical_concept_pass_db_validation():
    _fact(_shrine())
    GoriyakuTag.objects.create(name=CONCEPT_NAME)
    assert validate_registry_db_consistency((_record(),)) == ()


@pytest.mark.django_db
def test_t11_missing_source_fact_fails_db_validation():
    GoriyakuTag.objects.create(name=CONCEPT_NAME)
    errors = validate_registry_db_consistency((_record(),))
    assert any("resolves to 0 ShrineSourceFact rows" in e for e in errors)


@pytest.mark.django_db
def test_t12_missing_canonical_concept_fails_db_validation():
    _fact(_shrine())
    errors = validate_registry_db_consistency((_record(),))
    assert any("resolves to 0 GoriyakuTag rows by exact name" in e for e in errors)


@pytest.mark.django_db
@pytest.mark.parametrize("similar", ["商売繁昌", "商売繁盛祈願", "商売"])
def test_t16_concept_resolution_is_exact_name_only(similar):
    _fact(_shrine())
    GoriyakuTag.objects.create(name=similar)
    errors = validate_registry_db_consistency((_record(),))
    assert any("resolves to 0 GoriyakuTag rows by exact name" in e for e in errors)
    GoriyakuTag.objects.create(name=CONCEPT_NAME)
    assert validate_registry_db_consistency((_record(),)) == ()


@pytest.mark.django_db
def test_db_validation_reports_static_errors_first():
    errors = validate_registry_db_consistency((_record(mapping_classification="AMBIGUOUS"),))
    assert any("must not be a positive mapping" in e for e in errors)


@pytest.mark.django_db
def test_t17_t18_t19_validation_and_lookup_write_nothing():
    fact = _fact(_shrine())
    GoriyakuTag.objects.create(name=CONCEPT_NAME)
    tag_count = GoriyakuTag.objects.count()
    fact_before = list(ShrineSourceFact.objects.values())
    sources_before = list(fact.sources.values_list("id", flat=True))

    records = (_record(), _record(source_fact_key="missing", canonical_concept_name="存在しない"))
    validate_registry_db_consistency(records)
    build_registry((_record(),)).lookup(FACT_KEY)

    assert GoriyakuTag.objects.count() == tag_count
    assert ShrineGoriyakuAssignment.objects.count() == 0
    assert fact.shrine.goriyaku_tags.count() == 0
    assert list(ShrineSourceFact.objects.values()) == fact_before
    assert list(fact.sources.values_list("id", flat=True)) == sources_before


@pytest.mark.django_db
def test_t26_validation_and_build_are_deterministic():
    _fact(_shrine())
    records = (
        _record(),
        _record(source_fact_key="missing-0002", mapping_classification="SAFE_NORMALIZATION"),
        _record(source_fact_key=FACT_KEY),
    )
    assert validate_registry_static(records) == validate_registry_static(records)
    ok = (_record(), _record(source_fact_key="other-0002"))
    assert validate_registry_db_consistency(ok) == validate_registry_db_consistency(ok)
    assert build_registry(ok) == build_registry(ok)


# ---------- Recommendation / public API に影響しない ----------


def _candidates() -> list[dict]:
    result = build_chat_candidates_with_eligibility(lat=None, lng=None, area=None, trace_id="t")
    return [c for c in result.candidates if c.get("name") == SHRINE_NAME]


@pytest.mark.django_db
def test_t20_t21_registry_entry_does_not_change_candidates_or_eligibility(monkeypatch):
    """registry の entry は、候補に Channel B の内部 carrier（PR-C）を付ける以外の変更をしない。"""
    from temples.services.channel_b_typed_need_match import CHANNEL_B_TYPED_NEED_MATCHES_KEY

    eligible = _shrine()
    attach_usable_deity_fact(eligible)
    _fact(eligible)
    GoriyakuTag.objects.create(name=CONCEPT_NAME)
    before = _candidates()
    assert len(before) == 1

    mapped = build_registry((_record(),))
    monkeypatch.setattr(registry_module, "_default_registry", mapped)
    assert lookup_source_fact_mapping(FACT_KEY) is not None
    after = _candidates()
    assert [
        {k: v for k, v in row.items() if k != CHANNEL_B_TYPED_NEED_MATCHES_KEY} for row in after
    ] == before

    # Source Fact と mapping だけの神社は、G5 で適格にならない。
    only_fact = Shrine.objects.create(name_jp="対応表のみ神社", kind="shrine", address="東京都")
    _fact(only_fact, key="synthetic-registry-fact-0002")
    result = build_chat_candidates_with_eligibility(lat=None, lng=None, area=None, trace_id="t")
    assert all(c.get("name") != "対応表のみ神社" for c in result.candidates)


def test_t22_registry_is_only_read_by_the_channel_b_read_layer():
    """registry を読む runtime module は Channel B の typed read（PR-C）だけである。

    API / serializer / ranking / reason の module は registry を直接 import しない（公開しない）。
    """
    root = Path(__file__).resolve().parents[1]
    module_name = "source_fact_mapping_registry_v1"
    readers = sorted(
        str(path.relative_to(root))
        for path in root.rglob("*.py")
        if "tests" not in path.parts
        and path.name != f"{module_name}.py"
        and module_name in path.read_text(encoding="utf-8")
    )
    assert readers == ["services/channel_b_typed_need_match.py"]
