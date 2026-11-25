"""nsrc-000002 青澤神社の G4 Knowledge materialization regression。

Seed: backend/temples/data/knowledge_seeds/nsrc_000002_seed.json（Source 1 / Deity 0 / History 1）。
Deity は凍結 packet に Source-backed な祭神名が無いため 0 件のまま（沼河比賣命等を補完しない）。
SourceFact / collective / goriyaku は持たない。
"""

import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import (
    GoriyakuTag,
    Shrine,
    ShrineDeity,
    ShrineGoriyakuAssignment,
    ShrineHistory,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.services import evidence_gate
from temples.services.knowledge_seed import parse_seed, resolve_shrine

TEMPLES_DIR = Path(__file__).resolve().parents[1]
SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "nsrc_000002_seed.json"
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"

SHRINE_NAME = "青澤神社"
SHRINE_ADDRESS = "新潟県糸魚川市大字青海2696番地"

SOURCE_KEY = "ITOIGAWA_AOSAWA_SPRING_FESTIVAL"
SOURCE_URL = "https://matsuri.geo-itoigawa.com/calendar/m04/"
HISTORY_TYPE = "regional_context"
HISTORY_TITLE = "青沢神社の春季祭礼"
HISTORY_PERIOD_TEXT = "毎年4月第3日曜日"

BLOCKED_CODES = (
    "NOT_FOUND",
    "IMPORT_IDENTITY_AMBIGUOUS",
    "SOURCE_REUSE_CONFLICT",
    "SOURCE_REUSE_AMBIGUOUS",
)
UNSOURCED_DEITY_NAMES = ("沼河比賣命", "沼河比売命")


def _import_base_seed() -> None:
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )


def _import_knowledge(*args: str) -> tuple[str, str]:
    out = io.StringIO()
    err = io.StringIO()
    call_command("import_shrine_knowledge", str(SEED_PATH), *args, stdout=out, stderr=err)
    return out.getvalue(), err.getvalue()


def _target() -> Shrine:
    return Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)


def _knowledge_counts() -> dict:
    return {
        "source": ShrineKnowledgeSource.objects.count(),
        "deity": ShrineDeity.objects.count(),
        "history": ShrineHistory.objects.count(),
        "source_fact": ShrineSourceFact.objects.count(),
    }


# ---------- 1. seed parser contract ----------


def test_nsrc_000002_seed_parser_contract():
    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    parsed = parse_seed(raw)

    assert parsed.errors == []
    assert parsed.schema_version == "1.0"
    assert len(parsed.sources) == 1
    assert list(parsed.sources) == [SOURCE_KEY]
    assert len(parsed.shrines) == 1

    block = parsed.shrines[0]
    assert (block.name_jp, block.address) == (SHRINE_NAME, SHRINE_ADDRESS)
    assert len(block.deities) == 0
    assert len(block.histories) == 1
    assert list(block.collectives) == []
    assert list(block.source_facts) == []

    shrine_raw = raw["shrines"][0]
    assert set(shrine_raw) == {"shrine_ref", "deities", "histories"}
    assert shrine_raw["deities"] == []
    for key in ("goriyaku", "goriyaku_tags", "source_facts", "collectives"):
        assert key not in shrine_raw
        assert key not in raw


# ---------- 2. Base Shrine resolution ----------


@pytest.mark.django_db
def test_nsrc_000002_base_shrine_resolves_exactly_once():
    _import_base_seed()

    exact = Shrine.objects.filter(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    assert exact.count() == 1

    result = resolve_shrine(SHRINE_NAME, SHRINE_ADDRESS)
    assert result.status == "OK"
    assert result.shrine is not None
    assert result.shrine.pk == exact.get().pk


# ---------- 3. validate-only ----------


@pytest.mark.django_db
def test_nsrc_000002_validate_only_passes_without_writes():
    _import_base_seed()
    before = _knowledge_counts()

    output, _ = _import_knowledge("--validate-only")

    assert "validate-only: OK, no errors" in output
    assert _knowledge_counts() == before
    assert before["source"] == before["deity"] == before["history"] == 0


# ---------- 4. dry-run ----------


@pytest.mark.django_db
def test_nsrc_000002_dry_run_plans_one_source_and_one_history_without_writes():
    _import_base_seed()
    before = _knowledge_counts()

    output, error_output = _import_knowledge("--dry-run")
    combined = output + "\n" + error_output

    assert output.count("[source] CREATE") == 1
    assert output.count("[deity] CREATE") == 0
    assert output.count("[history] CREATE") == 1
    assert "'source_CREATE': 1" in output
    assert "'history_CREATE': 1" in output
    assert "deity_CREATE" not in output
    for code in BLOCKED_CODES:
        assert code not in combined
    assert "dry-run: OK, no DB writes performed" in output
    assert _knowledge_counts() == before


# ---------- 5. isolated apply ----------


@pytest.mark.django_db
def test_nsrc_000002_apply_materializes_one_sourced_history():
    _import_base_seed()
    before = _knowledge_counts()

    output, error_output = _import_knowledge()
    combined = output + "\n" + error_output

    for code in BLOCKED_CODES:
        assert code not in combined
    assert (
        "import complete: sources created=1, deities created=0, histories created=1, "
        "collectives created=0, memberships created=0, source_facts created=0"
    ) in output

    after = _knowledge_counts()
    assert after["source"] - before["source"] == 1
    assert after["deity"] - before["deity"] == 0
    assert after["history"] - before["history"] == 1
    assert after["source_fact"] - before["source_fact"] == 0

    shrine = _target()
    histories = list(ShrineHistory.objects.filter(shrine=shrine))
    assert len(histories) == 1
    assert ShrineDeity.objects.filter(shrine=shrine).count() == 0

    history = histories[0]
    assert history.title == HISTORY_TITLE
    assert history.history_type == HISTORY_TYPE
    assert history.event_date is None
    assert history.period_text == HISTORY_PERIOD_TEXT
    assert history.verification_status == "source_confirmed"
    assert history.confidence == "high"

    sources = list(history.sources.all())
    assert len(sources) == 1
    assert sources[0].url == SOURCE_URL
    assert sources[0].source_type == "government"
    assert sources[0].verification_status == "source_confirmed"

    assert (
        sum(1 for h in ShrineHistory.objects.filter(shrine=shrine) if not h.sources.exists()) == 0
    )


# ---------- 6. actual Evidence Gate ----------


@pytest.mark.django_db
def test_nsrc_000002_history_is_usable_under_evidence_gate_from_persisted_relations():
    _import_base_seed()
    _import_knowledge()

    history = ShrineHistory.objects.get(shrine=_target(), title=HISTORY_TITLE)
    source_statuses = list(history.sources.values_list("verification_status", flat=True))
    assert source_statuses == ["source_confirmed"]

    decision = evidence_gate.decide_fact_usability(
        verification_status=history.verification_status,
        confidence=history.confidence,
        source_verification_statuses=source_statuses,
    )

    assert decision.usable is True
    assert decision.display_mode == "full"
    assert decision.reason_strength == "assertive"
    assert decision.reason == "fact_ready_with_source"
    assert decision.verification_status == "source_confirmed"
    assert decision.confidence == "high"


# ---------- 7. Deity boundary ----------


@pytest.mark.django_db
def test_nsrc_000002_has_no_deity_and_no_unsourced_deity_name():
    raw_text = SEED_PATH.read_text(encoding="utf-8")
    for name in UNSOURCED_DEITY_NAMES:
        assert name not in raw_text

    _import_base_seed()
    _import_knowledge()

    shrine = _target()
    assert ShrineDeity.objects.filter(shrine=shrine).count() == 0
    for name in UNSOURCED_DEITY_NAMES:
        assert not ShrineDeity.objects.filter(display_name=name).exists()


# ---------- 8. idempotency ----------


@pytest.mark.django_db
def test_nsrc_000002_second_import_is_idempotent():
    _import_base_seed()
    _import_knowledge()

    shrine = _target()

    def snapshot() -> dict:
        histories = list(ShrineHistory.objects.filter(shrine=shrine).order_by("id"))
        return {
            "source_ids": list(
                ShrineKnowledgeSource.objects.order_by("id").values_list("id", flat=True)
            ),
            "source_urls": list(
                ShrineKnowledgeSource.objects.order_by("id").values_list("url", flat=True)
            ),
            "history_ids": [h.pk for h in histories],
            "history_sources": {
                h.pk: tuple(h.sources.order_by("id").values_list("id", flat=True))
                for h in histories
            },
            "deity_ids": list(
                ShrineDeity.objects.filter(shrine=shrine).values_list("id", flat=True)
            ),
        }

    before = snapshot()
    assert len(before["source_ids"]) == 1
    assert len(before["history_ids"]) == 1

    output, error_output = _import_knowledge()
    combined = output + "\n" + error_output

    assert "'source_REUSE_EXISTING': 1" in output
    assert "'history_SKIP_EXISTS': 1" in output
    assert "CREATE" not in output
    for code in (*BLOCKED_CODES, "SOURCE_FACT_CONFLICT"):
        assert code not in combined
    assert (
        "import complete: sources created=0, deities created=0, histories created=0, "
        "collectives created=0, memberships created=0, source_facts created=0"
    ) in output

    after = snapshot()
    assert after == before
    assert ShrineHistory.objects.filter(shrine=shrine, title=HISTORY_TITLE).count() == 1
    assert ShrineKnowledgeSource.objects.filter(url=SOURCE_URL).count() == 1


# ---------- 9. goriyaku isolation ----------


@pytest.mark.django_db
def test_nsrc_000002_knowledge_import_keeps_goriyaku_state_unchanged():
    _import_base_seed()
    shrine = _target()

    def snapshot() -> dict:
        shrine.refresh_from_db()
        return {
            "goriyaku": shrine.goriyaku,
            "goriyaku_tag_ids": tuple(
                shrine.goriyaku_tags.order_by("id").values_list("id", flat=True)
            ),
            "goriyaku_tag_master": tuple(
                GoriyakuTag.objects.order_by("id").values_list("id", "name", "category")
            ),
            "goriyaku_assignments": tuple(
                ShrineGoriyakuAssignment.objects.order_by("id").values_list(
                    "id",
                    "shrine_id",
                    "canonical_key",
                    "taxonomy_version",
                    "lifecycle",
                    "producer",
                    "mechanism",
                    "assigned_at",
                )
            ),
        }

    before = snapshot()
    assert before["goriyaku"] == ""
    assert before["goriyaku_tag_ids"] == ()

    _import_knowledge()

    assert snapshot() == before
    assert ShrineSourceFact.objects.filter(shrine=shrine).count() == 0
