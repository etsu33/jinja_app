"""Knowledge Seed 1.2 ShrineSourceFact foundation（PR-A / Policy C / Channel B）。

契約: docs/audit/shrine-expansion-wave0-db04-f1-goriyaku-mapping-boundary.md
§12.15.A〜G（model / stable_key / CONFLICT / characterization / Source / seed schema / importer）。

Recommendation（候補・G5・scoring）は ShrineSourceFact を読まない（PR-A の範囲外）。
"""

from __future__ import annotations

import copy
import io
import json

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.utils import timezone

from temples.models import (
    GoriyakuTag,
    Shrine,
    ShrineGoriyakuAssignment,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.services.concierge_chat_candidates import build_chat_candidates_with_eligibility
from temples.services.knowledge_seed import SOURCE_FACT_SCHEMA_VERSION, parse_seed
from temples.tests.support.recommendation_eligibility import attach_usable_deity_fact

pytestmark = pytest.mark.django_db

SHRINE_NAME = "出典事実試験神社"
SHRINE_ADDRESS = "東京都試験区2-2-2"
OTHER_SHRINE_NAME = "出典事実別試験神社"
OTHER_SHRINE_ADDRESS = "東京都試験区3-3-3"
VERIFIED_AT = "2026-10-01T00:00:00+09:00"

CHARACTERIZATIONS = (
    "official_prayer_supported",
    "official_current_guidance_supported",
    "official_prayer_and_current_guidance_list_level",
)


def _source(key: str, url: str) -> dict:
    return {
        "key": key,
        "source_type": "shrine_official",
        "title": f"ご祈祷案内 {key}",
        "publisher": SHRINE_NAME,
        "url": url,
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": VERIFIED_AT,
    }


def _fact(**overrides) -> dict:
    fact = {
        "stable_key": "test-source-fact-0001",
        "source_attested_wording": "商売繁盛",
        "evidence_characterization": "official_prayer_supported",
        "source_keys": ["src-prayer"],
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": VERIFIED_AT,
    }
    fact.update(overrides)
    return fact


def _block(*, name: str = SHRINE_NAME, address: str = SHRINE_ADDRESS, **overrides) -> dict:
    block = {
        "shrine_ref": {"name_jp": name, "address": address},
        "deities": [],
        "histories": [],
        "source_facts": [_fact()],
    }
    block.update(overrides)
    return block


def _seed(*blocks: dict, version: str = SOURCE_FACT_SCHEMA_VERSION) -> dict:
    return {
        "schema_version": version,
        "sources": [
            _source("src-prayer", "https://source-fact.example.jp/kitou"),
            _source("src-guidance", "https://source-fact.example.jp/annai"),
        ],
        "shrines": list(blocks) or [_block()],
    }


def _errors(seed: dict) -> list[str]:
    return parse_seed(seed).errors


def _write(tmp_path, seed: dict, name: str = "seed.json") -> str:
    path = tmp_path / name
    path.write_text(json.dumps(seed, ensure_ascii=False), encoding="utf-8")
    return str(path)


def _run(path: str, *args: str) -> str:
    out = io.StringIO()
    call_command("import_shrine_knowledge", path, *args, stdout=out, stderr=io.StringIO())
    return out.getvalue()


def _run_blocked(path: str, *args: str) -> str:
    out, err = io.StringIO(), io.StringIO()
    with pytest.raises(CommandError, match="import blocked"):
        call_command("import_shrine_knowledge", path, *args, stdout=out, stderr=err)
    return out.getvalue() + err.getvalue()


def _shrine(name: str = SHRINE_NAME, address: str = SHRINE_ADDRESS) -> Shrine:
    return Shrine.objects.create(name_jp=name, kind="shrine", address=address)


def _model_fact(shrine: Shrine, **overrides) -> ShrineSourceFact:
    values = {
        "shrine": shrine,
        "stable_key": "model-source-fact-0001",
        "source_attested_wording": "厄除け",
        "evidence_characterization": "official_prayer_supported",
        "verification_status": "draft",
    }
    values.update(overrides)
    return ShrineSourceFact(**values)


# ---------- model ----------


def test_t1_valid_source_fact_saves_with_all_frozen_fields():
    shrine = _shrine()
    source = ShrineKnowledgeSource.objects.create(source_type="shrine_official", title="案内")
    fact = _model_fact(
        shrine,
        verification_status="source_confirmed",
        confidence="medium",
        verified_at=timezone.now(),
    )
    fact.full_clean()
    fact.save()
    fact.sources.add(source)
    fact.refresh_from_db()
    assert fact.stable_key == "model-source-fact-0001"
    assert fact.source_attested_wording == "厄除け"
    assert list(fact.sources.all()) == [source]
    assert list(shrine.source_facts.all()) == [fact]


def test_model_has_only_the_frozen_minimum_fields():
    names = {f.name for f in ShrineSourceFact._meta.get_fields() if f.concrete or f.many_to_many}
    assert names == {
        "id",
        "shrine",
        "stable_key",
        "source_attested_wording",
        "evidence_characterization",
        "sources",
        "verification_status",
        "confidence",
        "verified_at",
        "created_at",
        "updated_at",
    }


def test_three_characterizations_are_representable_and_goriyaku_wording_is_not():
    values = {v for v, _ in ShrineSourceFact.EVIDENCE_CHARACTERIZATION_CHOICES}
    assert values == set(CHARACTERIZATIONS)
    shrine = _shrine()
    for i, value in enumerate(CHARACTERIZATIONS):
        _model_fact(shrine, stable_key=f"char-{i}", evidence_characterization=value).full_clean()
    with pytest.raises(ValidationError):
        _model_fact(
            shrine, stable_key="char-x", evidence_characterization="official_goriyaku_wording"
        ).full_clean()


def test_t2_stable_key_is_globally_unique_across_shrines():
    _model_fact(_shrine()).save()
    other = _shrine(OTHER_SHRINE_NAME, OTHER_SHRINE_ADDRESS)
    with pytest.raises(IntegrityError), transaction.atomic():
        _model_fact(other).save()


@pytest.mark.parametrize("key", ["", "   "])
def test_t3_blank_stable_key_rejected_by_clean_and_db(key):
    shrine = _shrine()
    with pytest.raises(ValidationError):
        _model_fact(shrine, stable_key=key).full_clean()
    with pytest.raises(IntegrityError), transaction.atomic():
        _model_fact(shrine, stable_key=key).save()


def test_verified_at_required_for_fact_ready_status():
    with pytest.raises(ValidationError):
        _model_fact(_shrine(), verification_status="reviewed", verified_at=None).full_clean()


# ---------- seed parser (schema 1.2) ----------


def test_schema_1_2_seed_parses_source_facts():
    parsed = parse_seed(_seed())
    assert parsed.errors == []
    (fact,) = parsed.shrines[0].source_facts
    assert fact.stable_key == "test-source-fact-0001"
    assert fact.source_keys == ["src-prayer"]


def test_t16_schema_1_2_without_source_facts_block_is_valid():
    block = _block()
    del block["source_facts"]
    parsed = parse_seed(_seed(block))
    assert parsed.errors == []
    assert parsed.shrines[0].source_facts == []


@pytest.mark.parametrize("version", ["1.0", "1.1"])
@pytest.mark.parametrize("facts", [[], [_fact()]])
def test_old_schema_versions_reject_source_facts_even_when_empty(version, facts):
    errors = _errors(_seed(_block(source_facts=facts), version=version))
    assert any(
        f"shrines[0].source_facts: not allowed in schema_version {version!r}" in e for e in errors
    )


def test_t15_old_schema_versions_keep_their_unknown_key_behavior():
    """1.0 / 1.1 は未知 key を従来どおり無視する（さかのぼって厳格にしない）。"""
    for version in ("1.0", "1.1"):
        block = _block(note="legacy extra key")
        del block["source_facts"]
        assert _errors(_seed(block, version=version)) == []


def test_schema_1_2_still_accepts_collectives():
    block = _block(
        deities=[
            {
                "display_name": "祭神A",
                "verification_status": "source_confirmed",
                "verified_at": VERIFIED_AT,
                "source_keys": ["src-prayer"],
            }
        ],
        collectives=[
            {
                "source_attested_label": "祭神A等",
                "verification_status": "source_confirmed",
                "verified_at": VERIFIED_AT,
                "source_keys": ["src-prayer"],
            }
        ],
    )
    parsed = parse_seed(_seed(block))
    assert parsed.errors == []
    assert len(parsed.shrines[0].collectives) == 1


def test_t14_unknown_shrine_block_key_fails_closed_in_schema_1_2():
    errors = _errors(_seed(_block(note="x")))
    assert any("shrines[0]: unknown key(s) ['note']" in e for e in errors)


@pytest.mark.parametrize(
    "extra", ["canonical_concept", "need", "mapping_classification", "sort_order", "note"]
)
def test_t14_unknown_source_fact_key_fails_closed(extra):
    errors = _errors(_seed(_block(source_facts=[_fact(**{extra: "x"})])))
    assert any(f"shrines[0].source_facts[0]: unknown key(s) [{extra!r}]" in e for e in errors)


def test_t12_duplicate_stable_key_within_seed_fails_closed_across_blocks():
    seed = _seed(
        _block(),
        _block(
            name=OTHER_SHRINE_NAME,
            address=OTHER_SHRINE_ADDRESS,
            source_facts=[_fact(source_attested_wording="家内安全")],
        ),
    )
    errors = _errors(seed)
    assert any(
        "shrines[1].source_facts[0].stable_key: duplicate 'test-source-fact-0001'" in e
        for e in errors
    )


@pytest.mark.parametrize("key", [None, "", "   ", " leading", "trailing ", 12])
def test_blank_or_untrimmed_stable_key_fails_closed(key):
    errors = _errors(_seed(_block(source_facts=[_fact(stable_key=key)])))
    assert any("shrines[0].source_facts[0].stable_key:" in e for e in errors)


@pytest.mark.parametrize("wording", [None, "", "  ", " 商売繁盛"])
def test_blank_or_untrimmed_wording_fails_closed(wording):
    errors = _errors(_seed(_block(source_facts=[_fact(source_attested_wording=wording)])))
    assert any("shrines[0].source_facts[0].source_attested_wording:" in e for e in errors)


@pytest.mark.parametrize(
    "value", [None, "", "official_goriyaku_wording", "OFFICIAL_PRAYER_SUPPORTED", "prayer"]
)
def test_t13_unknown_or_missing_characterization_fails_closed(value):
    fact = _fact(evidence_characterization=value)
    if value is None:
        del fact["evidence_characterization"]
    errors = _errors(_seed(_block(source_facts=[fact])))
    assert any("shrines[0].source_facts[0].evidence_characterization:" in e for e in errors)


@pytest.mark.parametrize("source_keys", [None, [], "src-prayer"])
def test_source_keys_required_and_non_empty(source_keys):
    fact = _fact(source_keys=source_keys)
    if source_keys is None:
        del fact["source_keys"]
    errors = _errors(_seed(_block(source_facts=[fact])))
    assert any("source_keys: required, must be a non-empty list" in e for e in errors)


def test_t11_unknown_source_key_fails_closed():
    errors = _errors(_seed(_block(source_facts=[_fact(source_keys=["src-missing"])])))
    assert any("unknown source key 'src-missing'" in e for e in errors)


def test_invalid_verification_fields_fail_closed():
    errors = _errors(
        _seed(_block(source_facts=[_fact(verification_status="reviewed", verified_at=None)]))
    )
    assert any("verified_at: required" in e for e in errors)
    errors = _errors(_seed(_block(source_facts=[_fact(confidence="very_high")])))
    assert any("confidence: invalid value" in e for e in errors)


# ---------- importer ----------


def test_t1_import_creates_source_fact_with_sources(tmp_path):
    shrine = _shrine()
    out = _run(_write(tmp_path, _seed()))
    assert "source_facts created=1" in out
    fact = ShrineSourceFact.objects.get(stable_key="test-source-fact-0001")
    assert fact.shrine == shrine
    assert fact.source_attested_wording == "商売繁盛"
    assert fact.evidence_characterization == "official_prayer_supported"
    assert fact.verification_status == "source_confirmed"
    assert fact.confidence == "high"
    assert fact.verified_at is not None
    assert [s.url for s in fact.sources.all()] == ["https://source-fact.example.jp/kitou"]


def test_combined_list_level_characterization_is_stored_without_splitting(tmp_path):
    _shrine()
    value = "official_prayer_and_current_guidance_list_level"
    seed = _seed(_block(source_facts=[_fact(evidence_characterization=value)]))
    _run(_write(tmp_path, seed))
    assert list(ShrineSourceFact.objects.values_list("evidence_characterization", flat=True)) == [
        value
    ]


def test_t10_multiple_sources_on_one_fact_and_no_inheritance(tmp_path):
    _shrine()
    seed = _seed(
        _block(
            source_facts=[
                _fact(source_keys=["src-prayer", "src-guidance"]),
                _fact(stable_key="test-source-fact-0002", source_attested_wording="家内安全"),
            ]
        )
    )
    _run(_write(tmp_path, seed))
    first = ShrineSourceFact.objects.get(stable_key="test-source-fact-0001")
    second = ShrineSourceFact.objects.get(stable_key="test-source-fact-0002")
    assert first.sources.count() == 2
    # 他の Fact の Source を継承しない。
    assert [s.url for s in second.sources.all()] == ["https://source-fact.example.jp/kitou"]


def test_t4_t18_identical_reimport_is_skip_exists_and_idempotent(tmp_path):
    _shrine()
    path = _write(tmp_path, _seed())
    _run(path)
    before = list(ShrineSourceFact.objects.values())
    out = _run(path)
    assert "[source_fact] SKIP_EXISTS" in out
    assert "source_facts created=0" in out
    assert list(ShrineSourceFact.objects.values()) == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_attested_wording", "商売繁昌"),  # T5
        ("evidence_characterization", "official_current_guidance_supported"),  # T6
        ("verification_status", "reviewed"),  # T9
        ("confidence", "low"),  # T9
        ("verified_at", "2026-10-02T00:00:00+09:00"),  # T9
    ],
)
def test_t5_t6_t9_same_stable_key_with_different_payload_is_conflict(tmp_path, field, value):
    _shrine()
    _run(_write(tmp_path, _seed()))
    before = list(ShrineSourceFact.objects.values())
    changed = _seed(_block(source_facts=[_fact(**{field: value})]))
    out = _run_blocked(_write(tmp_path, changed, "changed.json"))
    assert "SOURCE_FACT_CONFLICT" in out
    assert field in out
    # 黙って更新しない。
    assert list(ShrineSourceFact.objects.values()) == before


def test_t7_same_stable_key_on_different_shrine_is_conflict(tmp_path):
    _shrine()
    _shrine(OTHER_SHRINE_NAME, OTHER_SHRINE_ADDRESS)
    _run(_write(tmp_path, _seed()))
    moved = _seed(_block(name=OTHER_SHRINE_NAME, address=OTHER_SHRINE_ADDRESS))
    out = _run_blocked(_write(tmp_path, moved, "moved.json"))
    assert "SOURCE_FACT_CONFLICT" in out
    assert "shrine differs" in out
    assert ShrineSourceFact.objects.get().shrine.name_jp == SHRINE_NAME


@pytest.mark.parametrize("source_keys", [["src-guidance"], ["src-prayer", "src-guidance"]])
def test_t8_same_stable_key_with_different_source_set_is_conflict(tmp_path, source_keys):
    _shrine()
    _run(_write(tmp_path, _seed()))
    changed = _seed(_block(source_facts=[_fact(source_keys=source_keys)]))
    out = _run_blocked(_write(tmp_path, changed, "changed.json"))
    assert "SOURCE_FACT_CONFLICT" in out
    fact = ShrineSourceFact.objects.get()
    assert [s.url for s in fact.sources.all()] == ["https://source-fact.example.jp/kitou"]


def test_conflict_blocks_the_whole_import(tmp_path):
    _shrine()
    _run(_write(tmp_path, _seed()))
    seed = _seed(
        _block(
            source_facts=[
                _fact(stable_key="test-source-fact-0002", source_attested_wording="家内安全"),
                _fact(source_attested_wording="商売繁昌"),
            ]
        )
    )
    _run_blocked(_write(tmp_path, seed, "mixed.json"))
    assert not ShrineSourceFact.objects.filter(stable_key="test-source-fact-0002").exists()


def test_t11_import_blocks_on_unknown_source_key(tmp_path):
    _shrine()
    seed = _seed(_block(source_facts=[_fact(source_keys=["src-missing"])]))
    _run_blocked(_write(tmp_path, seed))
    assert ShrineSourceFact.objects.count() == 0


def test_unresolved_shrine_blocks_import(tmp_path):
    _run_blocked(_write(tmp_path, _seed()))
    assert ShrineSourceFact.objects.count() == 0


def test_t17_dry_run_and_validate_only_do_not_write(tmp_path):
    _shrine()
    path = _write(tmp_path, _seed())
    out = _run(path, "--dry-run")
    assert "[source_fact] CREATE" in out
    assert "dry-run: OK, no DB writes performed" in out
    _run(path, "--validate-only")
    assert ShrineSourceFact.objects.count() == 0
    assert ShrineKnowledgeSource.objects.count() == 0


def test_dry_run_reports_conflict_without_writing(tmp_path):
    _shrine()
    _run(_write(tmp_path, _seed()))
    before = list(ShrineSourceFact.objects.values())
    changed = _seed(_block(source_facts=[_fact(source_attested_wording="商売繁昌")]))
    out = _run_blocked(_write(tmp_path, changed, "changed.json"), "--dry-run")
    assert "SOURCE_FACT_CONFLICT" in out
    assert list(ShrineSourceFact.objects.values()) == before


# ---------- Policy C: goriyaku / Recommendation に影響しない ----------


def test_t19_t20_import_writes_no_goriyaku_tag_or_assignment(tmp_path):
    shrine = _shrine()
    tag_count = GoriyakuTag.objects.count()
    _run(_write(tmp_path, _seed()))
    shrine.refresh_from_db()
    assert shrine.goriyaku_tags.count() == 0
    assert GoriyakuTag.objects.count() == tag_count
    assert ShrineGoriyakuAssignment.objects.count() == 0


def _candidate_build(shrine_name: str):
    result = build_chat_candidates_with_eligibility(lat=None, lng=None, area=None, trace_id="t")
    rows = [c for c in result.candidates if c.get("name") == shrine_name]
    return result, rows


def test_t21_source_fact_alone_does_not_make_a_shrine_recommendation_eligible():
    shrine = _shrine()
    fact = _model_fact(
        shrine, verification_status="source_confirmed", verified_at=timezone.now()
    )
    fact.save()
    fact.sources.add(
        ShrineKnowledgeSource.objects.create(
            source_type="shrine_official",
            title="案内",
            verification_status="source_confirmed",
            verified_at=timezone.now(),
        )
    )
    _, rows = _candidate_build(SHRINE_NAME)
    assert rows == []


def test_t22_source_fact_does_not_change_candidate_payload():
    shrine = _shrine()
    attach_usable_deity_fact(shrine)
    _, before = _candidate_build(SHRINE_NAME)
    assert len(before) == 1

    fact = _model_fact(
        shrine, verification_status="source_confirmed", verified_at=timezone.now()
    )
    fact.save()
    _, after = _candidate_build(SHRINE_NAME)
    assert after == before
    assert not any("source_fact" in key for key in after[0])


def test_seed_inputs_are_not_mutated_by_parsing():
    seed = _seed()
    snapshot = copy.deepcopy(seed)
    parse_seed(seed)
    assert seed == snapshot
