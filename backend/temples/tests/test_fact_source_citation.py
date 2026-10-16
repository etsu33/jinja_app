"""Fact 単位の Source citation provenance（ShrineFactSourceCitation / Knowledge Seed 1.3）。

契約: docs/knowledge/fact-source-citation-contract.md

- ShrineKnowledgeSource は document-level のまま。Fact ごとの頁・節は citation の locator_text に持つ。
- ShrineHistory.sources / ShrineDeity.sources M2M は置き換えない。
- Evidence Gate / Recommendation eligibility は citation を読まない（M2M だけを読む）。
- SOURCE_REUSE_CONFLICT は弱めない。
"""

from __future__ import annotations

import copy
import importlib
import io
import json
from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, migrations, transaction
from django.utils import timezone

from temples.models import (
    Shrine,
    ShrineDeity,
    ShrineFactSourceCitation,
    ShrineHistory,
    ShrineKnowledgeSource,
)
from temples.services.concierge_chat_candidates import partition_recommendation_eligible_shrines
from temples.services.evidence_gate import decide_fact_usability
from temples.services.knowledge_seed import (
    CITATION_SCHEMA_VERSION,
    SOURCE_FACT_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    parse_seed,
)
from temples.services.recommendation_eligibility_verifier import (
    ShrineIdentity,
    verify_recommendation_eligibility,
)

pytestmark = pytest.mark.django_db

BACKEND_DIR = Path(__file__).resolve().parents[2]
SEED_DIR = BACKEND_DIR / "temples" / "data" / "knowledge_seeds"
MAIN_MIGRATION = "temples.migrations.0121_shrine_fact_source_citation"
NOGIS_MIGRATION = "temples.migrations_nogis.0020_shrine_fact_source_citation"

SHRINE_NAME = "出典位置試験神社"
SHRINE_ADDRESS = "新潟県試験市出典位置1-1"
VERIFIED_AT = "2026-10-01T00:00:00+09:00"
PDF_URL = "https://city.example.jp/bunka/gunshi.pdf"
DOC_BIBLIOGRAPHY = "中魚沼郡誌上"
LOC_A = "中魚沼郡誌上 p.398"
LOC_B = "中魚沼郡誌上 p.445"
TITLE_A = "郡誌上の記録A"
TITLE_B = "郡誌上の記録B"


# ---------- helpers ----------


def _shrine() -> Shrine:
    return Shrine.objects.create(name_jp=SHRINE_NAME, kind="shrine", address=SHRINE_ADDRESS)


def _db_source(status: str = "source_confirmed") -> ShrineKnowledgeSource:
    return ShrineKnowledgeSource.objects.create(
        source_type="local_history",
        title="郡誌",
        url=PDF_URL,
        bibliography=DOC_BIBLIOGRAPHY,
        verification_status=status,
        verified_at=timezone.now() if status == "source_confirmed" else None,
    )


def _db_history(shrine: Shrine, title: str = TITLE_A, status="source_confirmed") -> ShrineHistory:
    return ShrineHistory.objects.create(
        shrine=shrine,
        history_type="regional_context",
        title=title,
        content=f"{title}の本文。",
        verification_status=status,
        verified_at=timezone.now() if status == "source_confirmed" else None,
    )


def _db_deity(shrine: Shrine) -> ShrineDeity:
    return ShrineDeity.objects.create(
        shrine=shrine,
        display_name="出典位置試験命",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )


def _source_entry(**overrides) -> dict:
    entry = {
        "key": "src-gunshi",
        "source_type": "local_history",
        "title": "郡誌",
        "url": PDF_URL,
        "bibliography": DOC_BIBLIOGRAPHY,
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": VERIFIED_AT,
    }
    entry.update(overrides)
    return entry


def _history_entry(title: str = TITLE_A, locator: str | None = LOC_A, **overrides) -> dict:
    entry = {
        "history_type": "regional_context",
        "title": title,
        "content": f"{title}の本文。",
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": VERIFIED_AT,
        "source_keys": ["src-gunshi"],
    }
    if locator is not None:
        entry["citations"] = [{"source_key": "src-gunshi", "locator_text": locator}]
    entry.update(overrides)
    return entry


def _seed(
    *,
    histories: list[dict] | None = None,
    deities: list[dict] | None = None,
    sources: list[dict] | None = None,
    version: str = CITATION_SCHEMA_VERSION,
) -> dict:
    return {
        "schema_version": version,
        "sources": sources if sources is not None else [_source_entry()],
        "shrines": [
            {
                "shrine_ref": {"name_jp": SHRINE_NAME, "address": SHRINE_ADDRESS},
                "deities": deities or [],
                "histories": histories if histories is not None else [_history_entry()],
            }
        ],
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


def _counts() -> tuple[int, int, int, int]:
    return (
        ShrineKnowledgeSource.objects.count(),
        ShrineHistory.objects.count(),
        ShrineDeity.objects.count(),
        ShrineFactSourceCitation.objects.count(),
    )


# ---------- model ----------


def test_model_fields_are_the_contract_minimum():
    assert {f.name for f in ShrineFactSourceCitation._meta.concrete_fields} == {
        "id",
        "source",
        "shrine_history",
        "shrine_deity",
        "locator_text",
        "created_at",
    }
    # M2M は through model に置き換えていない。
    assert ShrineHistory._meta.get_field("sources").remote_field.through._meta.auto_created
    assert ShrineDeity._meta.get_field("sources").remote_field.through._meta.auto_created


def test_history_and_deity_citations_save_when_source_is_related():
    shrine = _shrine()
    source = _db_source()
    history = _db_history(shrine)
    deity = _db_deity(shrine)
    history.sources.add(source)
    deity.sources.add(source)

    h_cite = ShrineFactSourceCitation.objects.create(
        source=source, shrine_history=history, locator_text=LOC_A
    )
    d_cite = ShrineFactSourceCitation.objects.create(
        source=source, shrine_deity=deity, locator_text=LOC_A
    )
    assert h_cite.fact == history
    assert d_cite.fact == deity
    assert list(history.source_citations.all()) == [h_cite]
    assert list(source.fact_citations.order_by("id")) == [h_cite, d_cite]


def test_same_fact_and_source_with_different_locators_is_allowed():
    shrine = _shrine()
    source = _db_source()
    history = _db_history(shrine)
    history.sources.add(source)
    ShrineFactSourceCitation.objects.create(
        source=source, shrine_history=history, locator_text=LOC_A
    )
    ShrineFactSourceCitation.objects.create(
        source=source, shrine_history=history, locator_text=LOC_B
    )
    assert history.source_citations.count() == 2


@pytest.mark.parametrize("selector", ["none", "both"])
def test_exactly_one_fact_selector_rejected_by_clean(selector):
    shrine = _shrine()
    source = _db_source()
    history = _db_history(shrine)
    deity = _db_deity(shrine)
    history.sources.add(source)
    deity.sources.add(source)
    kwargs = {} if selector == "none" else {"shrine_history": history, "shrine_deity": deity}
    with pytest.raises(ValidationError):
        ShrineFactSourceCitation(source=source, locator_text=LOC_A, **kwargs).save()
    assert ShrineFactSourceCitation.objects.count() == 0


@pytest.mark.parametrize("selector", ["none", "both"])
def test_exactly_one_fact_selector_rejected_by_db(selector):
    shrine = _shrine()
    source = _db_source()
    history = _db_history(shrine)
    deity = _db_deity(shrine)
    kwargs = {} if selector == "none" else {"shrine_history": history, "shrine_deity": deity}
    with pytest.raises(IntegrityError), transaction.atomic():
        ShrineFactSourceCitation.objects.bulk_create(
            [ShrineFactSourceCitation(source=source, locator_text=LOC_A, **kwargs)]
        )


@pytest.mark.parametrize("locator", ["", "   ", "　"])
def test_blank_locator_rejected_by_clean_and_db(locator):
    shrine = _shrine()
    source = _db_source()
    history = _db_history(shrine)
    history.sources.add(source)
    with pytest.raises(ValidationError):
        ShrineFactSourceCitation(source=source, shrine_history=history, locator_text=locator).save()
    if locator == "　":
        # 全角空白は PostgreSQL の \S 判定に依存しないよう clean 側だけを契約とする。
        return
    with pytest.raises(IntegrityError), transaction.atomic():
        ShrineFactSourceCitation.objects.bulk_create(
            [ShrineFactSourceCitation(source=source, shrine_history=history, locator_text=locator)]
        )


def test_source_required():
    shrine = _shrine()
    history = _db_history(shrine)
    with pytest.raises(ValidationError):
        ShrineFactSourceCitation(shrine_history=history, locator_text=LOC_A).save()
    with pytest.raises(IntegrityError), transaction.atomic():
        ShrineFactSourceCitation.objects.bulk_create(
            [ShrineFactSourceCitation(shrine_history=history, locator_text=LOC_A)]
        )


@pytest.mark.parametrize("fact_kind", ["history", "deity"])
def test_duplicate_fact_source_locator_rejected_by_clean_and_db(fact_kind):
    shrine = _shrine()
    source = _db_source()
    fact = _db_history(shrine) if fact_kind == "history" else _db_deity(shrine)
    fact.sources.add(source)
    selector = {f"shrine_{fact_kind}": fact}
    ShrineFactSourceCitation.objects.create(source=source, locator_text=LOC_A, **selector)
    with pytest.raises(ValidationError):
        ShrineFactSourceCitation(source=source, locator_text=LOC_A, **selector).save()
    with pytest.raises(IntegrityError), transaction.atomic():
        ShrineFactSourceCitation.objects.bulk_create(
            [ShrineFactSourceCitation(source=source, locator_text=LOC_A, **selector)]
        )


@pytest.mark.parametrize("fact_kind", ["history", "deity"])
def test_citation_source_must_be_in_fact_sources(fact_kind):
    shrine = _shrine()
    related = _db_source()
    unrelated = ShrineKnowledgeSource.objects.create(source_type="other", title="無関係な出典")
    fact = _db_history(shrine) if fact_kind == "history" else _db_deity(shrine)
    fact.sources.add(related)
    with pytest.raises(ValidationError) as exc:
        ShrineFactSourceCitation(
            source=unrelated, locator_text=LOC_A, **{f"shrine_{fact_kind}": fact}
        ).save()
    assert "source" in exc.value.message_dict
    assert ShrineFactSourceCitation.objects.count() == 0


def test_citation_cascades_with_fact_and_source():
    shrine = _shrine()
    source = _db_source()
    history = _db_history(shrine)
    history.sources.add(source)
    ShrineFactSourceCitation.objects.create(
        source=source, shrine_history=history, locator_text=LOC_A
    )
    history.delete()
    assert ShrineFactSourceCitation.objects.count() == 0


# ---------- migration ----------


@pytest.mark.parametrize(
    ("module_path", "expected_dependency"),
    [
        (MAIN_MIGRATION, "0120_shrine_source_fact_foundation"),
        (NOGIS_MIGRATION, "0019_shrine_source_fact_foundation"),
    ],
)
def test_migration_is_schema_only(module_path, expected_dependency):
    migration = importlib.import_module(module_path).Migration
    assert migration.dependencies == [("temples", expected_dependency)]
    assert len(migration.operations) == 1
    operation = migration.operations[0]
    assert isinstance(operation, migrations.CreateModel)
    assert operation.name == "ShrineFactSourceCitation"
    assert {name for name, _ in operation.fields} == {
        "id",
        "source",
        "shrine_history",
        "shrine_deity",
        "locator_text",
        "created_at",
    }
    assert not any(
        isinstance(op, (migrations.RunPython, migrations.RunSQL)) for op in migration.operations
    )


def _normalized_operations(module_path):
    normalized = []
    for operation in importlib.import_module(module_path).Migration.operations:
        name, args, kwargs = operation.deconstruct()
        if "fields" in kwargs:
            kwargs = dict(kwargs)
            kwargs["fields"] = [(n, f.deconstruct()[1:]) for n, f in kwargs["fields"]]
        normalized.append((name, args, kwargs))
    return normalized


def test_standard_and_nogis_migrations_are_logically_identical():
    assert _normalized_operations(MAIN_MIGRATION) == _normalized_operations(NOGIS_MIGRATION)


# ---------- parser ----------


def test_schema_1_3_is_supported_and_older_versions_are_kept():
    assert SUPPORTED_SCHEMA_VERSIONS == ("1.0", "1.1", "1.2", "1.3")
    assert CITATION_SCHEMA_VERSION == "1.3"


def test_all_repository_seeds_still_parse_without_citations():
    paths = sorted(SEED_DIR.glob("*.json"))
    assert paths
    for path in paths:
        raw = json.loads(path.read_text(encoding="utf-8"))
        parsed = parse_seed(raw)
        assert parsed.errors == [], (path.name, parsed.errors)
        for block in parsed.shrines:
            assert all(h.citations == [] for h in block.histories), path.name
            assert all(d.citations == [] for d in block.deities), path.name


def test_schema_1_3_parses_history_and_deity_citations():
    deity = {
        "display_name": "出典位置試験命",
        "verification_status": "source_confirmed",
        "verified_at": VERIFIED_AT,
        "source_keys": ["src-gunshi"],
        "citations": [{"source_key": "src-gunshi", "locator_text": LOC_B}],
    }
    parsed = parse_seed(_seed(deities=[deity]))
    assert parsed.errors == []
    [history] = parsed.shrines[0].histories
    [d] = parsed.shrines[0].deities
    assert [(c.source_key, c.locator_text) for c in history.citations] == [("src-gunshi", LOC_A)]
    assert [(c.source_key, c.locator_text) for c in d.citations] == [("src-gunshi", LOC_B)]


def test_schema_1_3_without_citations_is_valid_and_keeps_1_2_features():
    seed = _seed(histories=[_history_entry(locator=None)])
    seed["shrines"][0]["source_facts"] = []
    seed["shrines"][0]["collectives"] = []
    assert _errors(seed) == []


def test_schema_1_3_keeps_strict_shrine_block_keys():
    seed = _seed()
    seed["shrines"][0]["unexpected"] = []
    assert any("shrines[0]: unknown key(s) ['unexpected']" in e for e in _errors(seed))


@pytest.mark.parametrize("version", ["1.0", "1.1", SOURCE_FACT_SCHEMA_VERSION])
@pytest.mark.parametrize("citations", [[], [{"source_key": "src-gunshi", "locator_text": LOC_A}]])
def test_older_schema_versions_reject_citations_even_when_empty(version, citations):
    seed = _seed(histories=[_history_entry(locator=None, citations=citations)], version=version)
    assert any(
        f"shrines[0].histories[0].citations: not allowed in schema_version {version!r}" in e
        for e in _errors(seed)
    )


@pytest.mark.parametrize(
    ("citations", "expected"),
    [
        ("not-a-list", "citations: must be a list"),
        (["not-an-object"], "citations[0]: must be an object"),
        (
            [{"source_key": "src-gunshi", "locator_text": LOC_A, "page": 398}],
            "citations[0]: unknown key(s) ['page']",
        ),
        ([{"locator_text": LOC_A}], "citations[0].source_key: required"),
        (
            [{"source_key": "src-other", "locator_text": LOC_A}],
            "citations[0].source_key: 'src-other' is not in this fact's source_keys",
        ),
        ([{"source_key": "src-gunshi"}], "citations[0].locator_text: required"),
        ([{"source_key": "src-gunshi", "locator_text": "  "}], "citations[0].locator_text"),
        (
            [{"source_key": "src-gunshi", "locator_text": f" {LOC_A}"}],
            "citations[0].locator_text: must not have leading/trailing whitespace",
        ),
        (
            [
                {"source_key": "src-gunshi", "locator_text": LOC_A},
                {"source_key": "src-gunshi", "locator_text": LOC_A},
            ],
            "citations[1]: duplicate citation",
        ),
    ],
)
def test_invalid_citations_fail_closed(citations, expected):
    seed = _seed(
        histories=[_history_entry(locator=None, citations=citations)],
        sources=[_source_entry(), _source_entry(key="src-other", url="https://other.example.jp/")],
    )
    errors = _errors(seed)
    assert any(f"shrines[0].histories[0].{expected}" in e for e in errors), errors


# ---------- importer ----------


def test_validate_only_and_dry_run_write_nothing(tmp_path):
    _shrine()
    path = _write(tmp_path, _seed())
    before = _counts()
    assert "validate-only: OK" in _run(path, "--validate-only")
    out = _run(path, "--dry-run")
    assert "[citation] CREATE" in out
    assert "dry-run: OK, no DB writes performed" in out
    assert _counts() == before


def test_validate_only_reports_citation_parse_errors(tmp_path):
    _shrine()
    seed = _seed(histories=[_history_entry(locator=" p.1")])
    err = io.StringIO()
    with pytest.raises(CommandError, match="validation failed"):
        call_command(
            "import_shrine_knowledge",
            _write(tmp_path, seed),
            "--validate-only",
            stdout=io.StringIO(),
            stderr=err,
        )
    assert "locator_text: must not have leading/trailing whitespace" in err.getvalue()


def test_apply_creates_citation_and_keeps_fact_sources(tmp_path):
    _shrine()
    out = _run(_write(tmp_path, _seed()))
    assert "histories created=1" in out
    assert out.rstrip().endswith("citations created=1")
    history = ShrineHistory.objects.get(title=TITLE_A)
    source = ShrineKnowledgeSource.objects.get()
    assert list(history.sources.all()) == [source]
    assert source.bibliography == DOC_BIBLIOGRAPHY
    [citation] = ShrineFactSourceCitation.objects.all()
    assert (citation.shrine_history, citation.shrine_deity, citation.source) == (
        history,
        None,
        source,
    )
    assert citation.locator_text == LOC_A


def test_apply_is_idempotent(tmp_path):
    _shrine()
    path = _write(tmp_path, _seed())
    _run(path)
    before = _counts()
    out = _run(path)
    assert "[citation] SKIP_EXISTS" in out
    assert out.rstrip().endswith("citations created=0")
    assert _counts() == before


def test_deity_citation_import(tmp_path):
    _shrine()
    deity = {
        "display_name": "出典位置試験命",
        "verification_status": "source_confirmed",
        "verified_at": VERIFIED_AT,
        "source_keys": ["src-gunshi"],
        "citations": [{"source_key": "src-gunshi", "locator_text": LOC_B}],
    }
    _run(_write(tmp_path, _seed(histories=[], deities=[deity])))
    [citation] = ShrineFactSourceCitation.objects.all()
    assert citation.shrine_deity.display_name == "出典位置試験命"
    assert citation.shrine_history is None


def test_same_source_url_reused_by_two_facts_with_different_locators(tmp_path):
    """nsrc-000007（p.398）と後続 Fact（p.445）が同じ normalized PDF を参照する形。"""
    _shrine()
    _run(_write(tmp_path, _seed(histories=[_history_entry(TITLE_A, LOC_A)]), "a.json"))
    # 後続 seed は Source を同一の document-level 値で再宣言する（URL の構文差のみ）。
    second = _seed(
        histories=[_history_entry(TITLE_B, LOC_B)],
        sources=[_source_entry(url=PDF_URL + "#page=445")],
    )
    out = _run(_write(tmp_path, second, "b.json"))
    assert "[source] REUSE_EXISTING" in out
    assert "SOURCE_REUSE_CONFLICT" not in out

    source = ShrineKnowledgeSource.objects.get()
    assert source.bibliography == DOC_BIBLIOGRAPHY
    history_a = ShrineHistory.objects.get(title=TITLE_A)
    history_b = ShrineHistory.objects.get(title=TITLE_B)
    assert list(history_a.sources.all()) == [source]
    assert list(history_b.sources.all()) == [source]
    assert sorted(
        ShrineFactSourceCitation.objects.values_list("shrine_history__title", "locator_text")
    ) == sorted([(TITLE_A, LOC_A), (TITLE_B, LOC_B)])


def test_source_reuse_conflict_is_not_weakened(tmp_path):
    """bibliography に Fact 固有の頁を入れた Source は従来どおり CONFLICT で止まる。"""
    _shrine()
    _run(_write(tmp_path, _seed(), "a.json"))
    before = _counts()
    conflicting = _seed(
        histories=[_history_entry(TITLE_B, locator=None)],
        sources=[_source_entry(bibliography=LOC_B)],
    )
    out = _run_blocked(_write(tmp_path, conflicting, "b.json"))
    assert "SOURCE_REUSE_CONFLICT" in out
    assert _counts() == before


def test_existing_fact_gains_citation_when_source_already_related(tmp_path):
    _shrine()
    _run(_write(tmp_path, _seed(histories=[_history_entry(locator=None)], version="1.2"), "a.json"))
    history = ShrineHistory.objects.get(title=TITLE_A)
    sources_before = list(history.sources.values_list("id", flat=True))
    out = _run(_write(tmp_path, _seed(), "b.json"))
    assert "[history] SKIP_EXISTS" in out
    assert "[citation] CREATE" in out
    assert list(history.sources.values_list("id", flat=True)) == sources_before
    assert ShrineFactSourceCitation.objects.get().shrine_history == history


def test_existing_fact_with_unrelated_source_fails_closed(tmp_path):
    """既存 Fact の sources を importer は変更しない。cited Source が未関連なら全体を止める。"""
    shrine = _shrine()
    existing = _db_history(shrine)
    existing.sources.add(
        ShrineKnowledgeSource.objects.create(source_type="other", title="既存の別出典")
    )
    before = _counts()
    out = _run_blocked(_write(tmp_path, _seed()))
    assert "CITATION_SOURCE_NOT_RELATED" in out
    assert _counts() == before
    assert existing.sources.count() == 1


def test_existing_fact_with_newly_created_source_fails_closed(tmp_path):
    shrine = _shrine()
    _db_history(shrine)
    before = _counts()
    out = _run_blocked(_write(tmp_path, _seed()))
    assert "CITATION_SOURCE_NOT_RELATED" in out
    assert "would be newly created" in out
    assert _counts() == before


def test_seed_without_citations_keeps_byte_identical_summary(tmp_path):
    _shrine()
    out = _run(_write(tmp_path, _seed(histories=[_history_entry(locator=None)], version="1.2")))
    assert out.rstrip().endswith("source_facts created=0")
    assert "citation" not in out


# ---------- Evidence Gate / Recommendation eligibility unchanged ----------


@pytest.mark.parametrize(
    ("fact_status", "source_status"),
    [
        ("source_confirmed", "source_confirmed"),
        ("source_confirmed", "draft"),
        ("draft", "source_confirmed"),
    ],
)
def test_citation_does_not_change_evidence_gate_or_eligibility(fact_status, source_status):
    shrine = _shrine()
    source = _db_source(status=source_status)
    history = _db_history(shrine, status=fact_status)
    history.sources.add(source)

    def snapshot():
        decision = decide_fact_usability(
            verification_status=history.verification_status,
            confidence=history.confidence,
            source_verification_statuses=[s.verification_status for s in history.sources.all()],
        )
        report = verify_recommendation_eligibility(
            shrine_identities=[ShrineIdentity(name=SHRINE_NAME, address=SHRINE_ADDRESS)]
        )
        partition = partition_recommendation_eligible_shrines([shrine])
        return (
            decision.usable,
            decision.reason,
            report.summary_counts(),
            report.results[0].status,
            partition.eligible_count,
        )

    before = snapshot()
    ShrineFactSourceCitation.objects.create(
        source=source, shrine_history=history, locator_text=LOC_A
    )
    ShrineFactSourceCitation.objects.create(
        source=source, shrine_history=history, locator_text=LOC_B
    )
    assert snapshot() == before
    assert before[0] is (fact_status == source_status == "source_confirmed")


def test_runtime_and_gate_modules_do_not_read_citations():
    services = BACKEND_DIR / "temples" / "services"
    for name in (
        "evidence_gate.py",
        "recommendation_eligibility_verifier.py",
        "concierge_chat_candidates.py",
    ):
        text = (services / name).read_text(encoding="utf-8")
        for token in ("ShrineFactSourceCitation", "source_citations", "fact_citations"):
            assert token not in text, (name, token)


def test_seed_copy_is_not_mutated_by_parse():
    seed = _seed()
    original = copy.deepcopy(seed)
    parse_seed(seed)
    assert seed == original
