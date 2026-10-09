import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import (
    Shrine,
    ShrineDeity,
    ShrineGoriyakuAssignment,
    ShrineHistory,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.services.knowledge_seed import parse_seed, resolve_shrine

TEMPLES_DIR = Path(__file__).resolve().parents[1]
SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "nsrc_000004_seed.json"
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"

SHRINE_NAME = "青海神社"
SHRINE_ADDRESS = "新潟県加茂市大字加茂字宮山229番地"


def test_nsrc_000004_seed_parses_cleanly_and_writes_no_goriyaku_fields():
    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    parsed = parse_seed(raw)

    assert parsed.errors == []
    assert parsed.schema_version == "1.2"
    assert len(parsed.sources) == 3
    assert len(parsed.shrines) == 1

    shrine_raw = raw["shrines"][0]
    assert "goriyaku" not in shrine_raw
    assert "goriyaku_tags" not in shrine_raw
    assert len(shrine_raw["source_facts"]) == 11
    assert all(
        fact["evidence_characterization"] == "official_prayer_supported"
        for fact in shrine_raw["source_facts"]
    )


@pytest.mark.django_db
def test_nsrc_000004_seed_validate_only_passes_without_writes():
    Shrine.objects.create(name_jp=SHRINE_NAME, kind="shrine", address=SHRINE_ADDRESS)

    out = io.StringIO()
    call_command(
        "import_shrine_knowledge",
        str(SEED_PATH),
        "--validate-only",
        stdout=out,
        stderr=io.StringIO(),
    )

    assert "validate-only: OK, no errors" in out.getvalue()
    assert ShrineKnowledgeSource.objects.count() == 0
    assert ShrineDeity.objects.count() == 0
    assert ShrineHistory.objects.count() == 0
    assert ShrineSourceFact.objects.count() == 0
    assert ShrineGoriyakuAssignment.objects.count() == 0


@pytest.mark.django_db
def test_nsrc_000004_base_seed_imports_into_isolated_db():
    out = io.StringIO()
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=out,
        stderr=io.StringIO(),
    )

    summary = [line for line in out.getvalue().splitlines() if line.startswith("done ")][-1]
    assert "total_seed=121" in summary

    exact_qs = Shrine.objects.filter(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    assert exact_qs.count() == 1

    result = resolve_shrine(SHRINE_NAME, SHRINE_ADDRESS)
    assert result.status == "OK"
    assert result.shrine is not None
    assert result.shrine.pk == exact_qs.get().pk
    assert result.shrine.name_jp == SHRINE_NAME
    assert result.shrine.address == SHRINE_ADDRESS
