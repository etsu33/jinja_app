"""nsrc-000009 赤城社 G4 Knowledge Seed / Evidence execution regression.

Authority:
- docs/audit/niigata-h002-nsrc-000009-g3-source-knowledge-fit.md
- docs/knowledge/fact-source-citation-contract.md
- docs/knowledge/shrine-expansion-gate-contract.md

The test reproduces the important legacy state by importing nsrc-000007 first, so the shared
municipal PDF Source already exists with bibliography "中魚沼郡誌上 p.398". nsrc-000009 must reuse
that Source while recording its own Fact locator as "中魚沼郡誌上 p.445".
"""

import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import (
    Shrine,
    ShrineDeity,
    ShrineDeityCollective,
    ShrineFactSourceCitation,
    ShrineHistory,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.services import evidence_gate
from temples.services.knowledge_seed import parse_seed

TEMPLES_DIR = Path(__file__).resolve().parents[1]
SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "nsrc_000009_seed.json"
LEGACY_SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "nsrc_000007_seed.json"
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"

SHRINE_NAME = "赤城社"
SHRINE_ADDRESS = "新潟県十日町市伊達乙48番地"
S2_KEY = "TOKAMACHI_REKIBUN_SHIRYOU"
S2_URL = "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf"
LEGACY_BIBLIOGRAPHY = "中魚沼郡誌上 p.398"
TARGET_LOCATOR = "中魚沼郡誌上 p.445"
FACT_VERIFIED_AT = "2026-10-16T00:00:00+09:00"

H1 = {
    "history_type": "historical_event",
    "title": "天明3年8月の創立記録",
    "content": "赤城社は天明3年8月に創立されたと記録されている。",
    "period_text": "天明3年8月",
    "event_date": None,
    "verification_status": "source_confirmed",
    "confidence": "high",
    "verified_at": FACT_VERIFIED_AT,
    "source_keys": [S2_KEY],
    "citations": [{"source_key": S2_KEY, "locator_text": TARGET_LOCATOR}],
}

H2 = {
    "history_type": "historical_event",
    "title": "大正2年の改築記録",
    "content": "赤城社は大正2年に改築されたと記録されている。",
    "period_text": "大正2年",
    "event_date": None,
    "verification_status": "source_confirmed",
    "confidence": "high",
    "verified_at": FACT_VERIFIED_AT,
    "source_keys": [S2_KEY],
    "citations": [{"source_key": S2_KEY, "locator_text": TARGET_LOCATOR}],
}

BLOCKED_CODES = (
    "NOT_FOUND",
    "IMPORT_IDENTITY_AMBIGUOUS",
    "SOURCE_REUSE_CONFLICT",
    "SOURCE_REUSE_AMBIGUOUS",
    "CITATION_SOURCE_NOT_RELATED",
)


def _raw() -> dict:
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def _import_base_seed() -> str:
    out = io.StringIO()
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=out,
        stderr=io.StringIO(),
    )
    return out.getvalue()


def _import_knowledge(path: Path, *args: str) -> tuple[str, str]:
    out = io.StringIO()
    err = io.StringIO()
    call_command("import_shrine_knowledge", str(path), *args, stdout=out, stderr=err)
    return out.getvalue(), err.getvalue()


def _prepare_legacy_source_state() -> None:
    _import_base_seed()
    _import_knowledge(LEGACY_SEED_PATH)


def _target() -> Shrine:
    return Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)


def _counts() -> dict:
    return {
        "source": ShrineKnowledgeSource.objects.count(),
        "deity": ShrineDeity.objects.count(),
        "history": ShrineHistory.objects.count(),
        "collective": ShrineDeityCollective.objects.count(),
        "source_fact": ShrineSourceFact.objects.count(),
        "citation": ShrineFactSourceCitation.objects.count(),
    }


def test_nsrc_000009_seed_parses_as_schema_1_3():
    raw = _raw()
    parsed = parse_seed(raw)

    assert parsed.errors == []
    assert parsed.schema_version == "1.3"
    assert len(parsed.sources) == 1
    assert len(parsed.shrines) == 1

    block = parsed.shrines[0]
    assert (block.name_jp, block.address) == (SHRINE_NAME, SHRINE_ADDRESS)
    assert len(block.deities) == 0
    assert len(block.histories) == 2
    assert list(block.collectives) == []
    assert list(block.source_facts) == []


def test_nsrc_000009_reuses_legacy_document_source_metadata():
    [source] = _raw()["sources"]

    assert source == {
        "key": S2_KEY,
        "source_type": "government",
        "title": "歴史文化基本構想 資料集",
        "publisher": "十日町市",
        "url": S2_URL,
        "bibliography": LEGACY_BIBLIOGRAPHY,
        "language": "ja",
        "accessed_at": "2026-10-13",
        "verified_at": "2026-10-13T00:00:00+09:00",
        "verification_status": "source_confirmed",
        "confidence": "high",
    }
    assert source["bibliography"] != TARGET_LOCATOR


def test_nsrc_000009_histories_and_fact_source_citations_are_frozen():
    raw = _raw()
    assert raw["shrines"][0]["histories"] == [H1, H2]

    parsed = parse_seed(raw)
    h1, h2 = parsed.shrines[0].histories

    for history in (h1, h2):
        assert history.source_keys == [S2_KEY]
        assert [(c.source_key, c.locator_text) for c in history.citations] == [
            (S2_KEY, TARGET_LOCATOR)
        ]
        assert history.event_date is None


def test_nsrc_000009_seed_contains_no_unauthorized_current_deity_or_derived_data():
    raw = _raw()
    shrine = raw["shrines"][0]
    text = SEED_PATH.read_text(encoding="utf-8")

    assert shrine["deities"] == []
    assert "大山祇命" not in text

    for key in ("goriyaku", "goriyaku_tags", "source_facts", "collectives", "history_theme"):
        assert key not in raw
        assert key not in shrine


@pytest.mark.django_db
def test_nsrc_000009_validate_only_passes_without_writes():
    _prepare_legacy_source_state()
    before = _counts()

    output, error_output = _import_knowledge(SEED_PATH, "--validate-only")

    assert "validate-only: OK, no errors" in output
    assert error_output == ""
    assert _counts() == before


@pytest.mark.django_db
def test_nsrc_000009_dry_run_reuses_source_and_plans_histories_and_citations_without_writes():
    _prepare_legacy_source_state()
    before = _counts()

    output, error_output = _import_knowledge(SEED_PATH, "--dry-run")
    combined = output + "\n" + error_output

    assert output.count("[source] REUSE_EXISTING") == 1
    assert output.count("[history] CREATE") == 2
    assert output.count("[citation] CREATE") == 2
    for code in BLOCKED_CODES:
        assert code not in combined
    assert "dry-run: OK, no DB writes performed" in output
    assert _counts() == before


@pytest.mark.django_db
def test_nsrc_000009_apply_materializes_two_histories_and_two_p445_citations():
    _prepare_legacy_source_state()
    before = _counts()

    output, error_output = _import_knowledge(SEED_PATH)
    combined = output + "\n" + error_output

    for code in BLOCKED_CODES:
        assert code not in combined
    assert "sources created=0" in output
    assert "deities created=0" in output
    assert "histories created=2" in output
    assert "citations created=2" in output

    after = _counts()
    assert after["source"] - before["source"] == 0
    assert after["history"] - before["history"] == 2
    assert after["citation"] - before["citation"] == 2
    assert after["deity"] - before["deity"] == 0
    assert after["collective"] - before["collective"] == 0
    assert after["source_fact"] - before["source_fact"] == 0

    shrine = _target()
    histories = {h.title: h for h in ShrineHistory.objects.filter(shrine=shrine)}
    assert set(histories) == {H1["title"], H2["title"]}

    source = ShrineKnowledgeSource.objects.get(url=S2_URL)
    assert source.bibliography == LEGACY_BIBLIOGRAPHY

    for history in histories.values():
        assert list(history.sources.all()) == [source]
        citations = list(history.source_citations.all())
        assert len(citations) == 1
        assert citations[0].source_id == source.pk
        assert citations[0].locator_text == TARGET_LOCATOR
        assert history.event_date is None

    assert ShrineDeity.objects.filter(shrine=shrine).count() == 0
    assert ShrineDeityCollective.objects.filter(shrine=shrine).count() == 0
    assert ShrineSourceFact.objects.filter(shrine=shrine).count() == 0
    assert not any(not h.sources.exists() for h in histories.values())


@pytest.mark.django_db
@pytest.mark.parametrize("title", [H1["title"], H2["title"]], ids=["H1", "H2"])
def test_nsrc_000009_history_is_usable_from_persisted_source_relation(title):
    _prepare_legacy_source_state()
    _import_knowledge(SEED_PATH)

    history = ShrineHistory.objects.get(shrine=_target(), title=title)
    source_statuses = list(history.sources.values_list("verification_status", flat=True))

    decision = evidence_gate.decide_fact_usability(
        verification_status=history.verification_status,
        confidence=history.confidence,
        source_verification_statuses=source_statuses,
    )

    assert source_statuses == ["source_confirmed"]
    assert decision.usable is True
    assert decision.display_mode == "full"
    assert decision.reason_strength == "assertive"
    assert decision.reason == "fact_ready_with_source"
    assert decision.verification_status == "source_confirmed"
    assert decision.confidence == "high"


@pytest.mark.django_db
def test_nsrc_000009_second_import_is_idempotent():
    _prepare_legacy_source_state()
    _import_knowledge(SEED_PATH)

    shrine = _target()

    def snapshot() -> dict:
        histories = list(ShrineHistory.objects.filter(shrine=shrine).order_by("id"))
        return {
            "counts": _counts(),
            "history_ids": [h.pk for h in histories],
            "history_sources": {
                h.pk: tuple(h.sources.order_by("id").values_list("id", flat=True))
                for h in histories
            },
            "citations": tuple(
                ShrineFactSourceCitation.objects.filter(shrine_history__shrine=shrine)
                .order_by("id")
                .values_list("shrine_history_id", "source_id", "locator_text")
            ),
        }

    before = snapshot()
    output, error_output = _import_knowledge(SEED_PATH)
    combined = output + "\n" + error_output

    assert output.count("[source] REUSE_EXISTING") == 1
    assert output.count("[history] SKIP_EXISTS") == 2
    assert output.count("[citation] SKIP_EXISTS") == 2
    assert "[history] CREATE" not in output
    assert "[citation] CREATE" not in output
    for code in BLOCKED_CODES:
        assert code not in combined
    assert "sources created=0" in output
    assert "histories created=0" in output
    assert "citations created=0" in output
    assert snapshot() == before
