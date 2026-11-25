"""nsrc-000025 天津神社 の G4 Knowledge materialization regression。

Seed:
backend/temples/data/knowledge_seeds/nsrc_000025_seed.json
（Source 1 / Deity 3 / History 5）

Authority:
docs/audit/niigata-vpg001-nsrc-000025-g4-source-packet-freeze.md
docs/audit/niigata-vpg001-g4-knowledge-materialization.md

Frozen Source Packet の Fact だけを materialize する。verified_at は Mother Ship の Source verification
session 時刻（2026-10-19T14:35:38+09:00）であり、公開日でも midnight placeholder でもない。
FORMAL_G4 / G5 以降はこのテストの範囲外。
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import (
    GoriyakuTag,
    Shrine,
    ShrineDeity,
    ShrineDeityCollective,
    ShrineFactSourceCitation,
    ShrineGoriyakuAssignment,
    ShrineHistory,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.services import evidence_gate
from temples.services.knowledge_seed import parse_seed, resolve_shrine

TEMPLES_DIR = Path(__file__).resolve().parents[1]
SEED_DIR = TEMPLES_DIR / "data" / "knowledge_seeds"
SEED_PATH = SEED_DIR / "nsrc_000025_seed.json"
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"

SHRINE_NAME = "天津神社"
SHRINE_ADDRESS = "新潟県糸魚川市一の宮1丁目3番34号"
NON_CANONICAL_ADDRESSES = ("新潟県上越市大字東京田34番地1",)

S1_KEY = "AMATSU_JINJA_OFFICIAL_STORY"
S1_URL = "https://amatsujinja.com/story/"
VERIFIED_AT = "2026-10-19T14:35:38+09:00"

EXPECTED_SOURCE = {
    "key": "AMATSU_JINJA_OFFICIAL_STORY",
    "source_type": "shrine_official",
    "title": "御由緒・御祭神",
    "publisher": "天津神社・奴奈川神社",
    "url": "https://amatsujinja.com/story/",
    "language": "ja",
    "accessed_at": "2026-10-19",
    "verified_at": "2026-10-19T14:35:38+09:00",
    "verification_status": "source_confirmed",
    "confidence": "high",
}
EXPECTED_DEITIES = [
    {
        "display_name": "天津彦々火瓊々杵尊",
        "role": "unknown",
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": "2026-10-19T14:35:38+09:00",
        "source_keys": ["AMATSU_JINJA_OFFICIAL_STORY"],
    },
    {
        "display_name": "天児屋根命",
        "role": "unknown",
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": "2026-10-19T14:35:38+09:00",
        "source_keys": ["AMATSU_JINJA_OFFICIAL_STORY"],
    },
    {
        "display_name": "天太玉命",
        "role": "unknown",
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": "2026-10-19T14:35:38+09:00",
        "source_keys": ["AMATSU_JINJA_OFFICIAL_STORY"],
    },
]
EXPECTED_HISTORIES = [
    {
        "history_type": "tradition",
        "title": "景行天皇御代の創設（公式由緒）",
        "content": "天津神社の公式由緒では、第12代景行天皇の御代に創設されたと伝えられている。",
        "period_text": "第12代景行天皇の御代",
        "event_date": None,
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": "2026-10-19T14:35:38+09:00",
        "source_keys": ["AMATSU_JINJA_OFFICIAL_STORY"],
    },
    {
        "history_type": "tradition",
        "title": "孝徳天皇の勅願所（公式由緒）",
        "content": "天津神社の公式由緒では、第36代孝徳天皇の勅願所であったとされている。",
        "period_text": "第36代孝徳天皇",
        "event_date": None,
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": "2026-10-19T14:35:38+09:00",
        "source_keys": ["AMATSU_JINJA_OFFICIAL_STORY"],
    },
    {
        "history_type": "historical_event",
        "title": "本殿の建立",
        "content": "天津神社の本殿は寛政9年（1797）に建立された。",
        "period_text": "寛政9年（1797）",
        "event_date": None,
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": "2026-10-19T14:35:38+09:00",
        "source_keys": ["AMATSU_JINJA_OFFICIAL_STORY"],
    },
    {
        "history_type": "historical_event",
        "title": "拝殿の改築",
        "content": "天津神社の拝殿は寛文2年（1662）に改築された。",
        "period_text": "寛文2年（1662）",
        "event_date": None,
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": "2026-10-19T14:35:38+09:00",
        "source_keys": ["AMATSU_JINJA_OFFICIAL_STORY"],
    },
    {
        "history_type": "historical_event",
        "title": "幣殿の増築",
        "content": "天津神社の幣殿は天明2年（1782）に増築された。",
        "period_text": "天明2年（1782）",
        "event_date": None,
        "verification_status": "source_confirmed",
        "confidence": "high",
        "verified_at": "2026-10-19T14:35:38+09:00",
        "source_keys": ["AMATSU_JINJA_OFFICIAL_STORY"],
    },
]
FORBIDDEN_DEITY_NAMES = ("奴奈川媛命", "八千矛命")
FORBIDDEN_TEXT = ("奴奈川媛命", "八千矛命")
BLOCKED_CODES = (
    "SOURCE_REUSE_CONFLICT",
    "SOURCE_REUSE_AMBIGUOUS",
    "SHRINE_NOT_FOUND",
    "SHRINE_AMBIGUOUS",
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
        "collective": ShrineDeityCollective.objects.count(),
        "source_fact": ShrineSourceFact.objects.count(),
        "citation": ShrineFactSourceCitation.objects.count(),
    }


# ---------- seed / parser / frozen payload -------------------------------------------------------


def test_seed_parses_as_schema_1_0_without_errors():
    raw = _raw()
    assert raw["schema_version"] == "1.0"
    parse_seed(raw)


def test_seed_is_exactly_the_frozen_payload():
    raw = _raw()
    assert raw["sources"] == [EXPECTED_SOURCE]
    assert len(raw["shrines"]) == 1
    shrine = raw["shrines"][0]
    assert shrine["shrine_ref"] == {"name_jp": SHRINE_NAME, "address": SHRINE_ADDRESS}
    assert shrine["deities"] == EXPECTED_DEITIES
    assert shrine["histories"] == EXPECTED_HISTORIES
    assert set(shrine) == {"shrine_ref", "deities", "histories"}


def test_every_fact_uses_the_session_verified_at_and_s1():
    shrine = _raw()["shrines"][0]
    for fact in [*shrine["deities"], *shrine["histories"]]:
        assert fact["verified_at"] == VERIFIED_AT
        assert fact["source_keys"] == [S1_KEY]
    assert "T00:00:00" not in SEED_PATH.read_text(encoding="utf-8")


def test_histories_have_no_event_date():
    for history in _raw()["shrines"][0]["histories"]:
        assert history["event_date"] is None


def test_seed_contains_no_forbidden_or_derived_material():
    text = SEED_PATH.read_text(encoding="utf-8")
    for needle in FORBIDDEN_TEXT:
        assert needle not in text, needle
    for key in ("goriyaku", "goriyaku_tags", "collectives", "source_facts", "citations"):
        assert f'"{key}"' not in text, key


def test_source_url_is_not_used_by_other_seed_files():
    hits = [p.name for p in SEED_DIR.rglob("*.json") if S1_URL in p.read_text(encoding="utf-8")]
    assert hits == [SEED_PATH.name]


def test_seed_exists_exactly_once_for_this_address():
    hits = [p for p in SEED_DIR.rglob("*.json") if SHRINE_ADDRESS in p.read_text(encoding="utf-8")]
    assert hits == [SEED_PATH]


def test_tradition_and_historical_event_types_are_preserved():
    types = {h["title"]: h["history_type"] for h in _raw()["shrines"][0]["histories"]}
    assert types == {
        "景行天皇御代の創設（公式由緒）": "tradition",
        "孝徳天皇の勅願所（公式由緒）": "tradition",
        "本殿の建立": "historical_event",
        "拝殿の改築": "historical_event",
        "幣殿の増築": "historical_event",
    }


@pytest.mark.django_db
def test_nunagawa_jinja_is_never_a_fact_owner():
    _import_base_seed()
    _import_knowledge()
    assert not Shrine.objects.filter(name_jp="奴奈川神社").exists()
    assert resolve_shrine("奴奈川神社", SHRINE_ADDRESS).status == "NOT_FOUND"
    owners = set(ShrineDeity.objects.values_list("shrine_id", flat=True)) | set(
        ShrineHistory.objects.values_list("shrine_id", flat=True)
    )
    assert owners == {_target().pk}


# ---------- shrine resolution --------------------------------------------------------------------


@pytest.mark.django_db
def test_base_shrine_resolves_exactly():
    _import_base_seed()
    result = resolve_shrine(SHRINE_NAME, SHRINE_ADDRESS)
    assert result.status == "OK"
    assert result.shrine is not None and result.shrine.pk == _target().pk


@pytest.mark.django_db
@pytest.mark.parametrize("address", NON_CANONICAL_ADDRESSES)
def test_same_name_other_address_never_resolves(address):
    _import_base_seed()
    assert resolve_shrine(SHRINE_NAME, address).status == "NOT_FOUND"


# ---------- validate-only / dry-run / apply ------------------------------------------------------


@pytest.mark.django_db
def test_validate_only_passes_without_writes():
    _import_base_seed()
    before = _knowledge_counts()
    output, error_output = _import_knowledge("--validate-only")
    assert "validate-only: OK, no errors" in output
    assert error_output == ""
    assert _knowledge_counts() == before


@pytest.mark.django_db
def test_dry_run_plans_exactly_the_frozen_rows_without_writes():
    _import_base_seed()
    before = _knowledge_counts()
    output, error_output = _import_knowledge("--dry-run")
    assert output.count("[source] CREATE") == 1
    assert output.count("[deity] CREATE") == 3
    assert output.count("[history] CREATE") == 5
    assert "plan summary: {'source_CREATE': 1, 'deity_CREATE': 3, 'history_CREATE': 5}" in output
    for code in BLOCKED_CODES:
        assert code not in output + error_output
    assert "dry-run: OK, no DB writes performed" in output
    assert _knowledge_counts() == before


@pytest.mark.django_db
def test_apply_materializes_exactly_the_frozen_facts():
    _import_base_seed()
    before = _knowledge_counts()
    output, error_output = _import_knowledge()
    for code in BLOCKED_CODES:
        assert code not in output + error_output
    assert (
        "import complete: sources created=1, deities created=3, histories created=5, "
        "collectives created=0, memberships created=0, source_facts created=0"
    ) in output
    after = _knowledge_counts()
    assert {k: after[k] - before[k] for k in after} == {
        "source": 1,
        "deity": 3,
        "history": 5,
        "collective": 0,
        "source_fact": 0,
        "citation": 0,
    }

    source = ShrineKnowledgeSource.objects.get(url=S1_URL)
    assert (source.source_type, source.title, source.publisher, source.language) == (
        EXPECTED_SOURCE["source_type"],
        EXPECTED_SOURCE["title"],
        EXPECTED_SOURCE["publisher"],
        "ja",
    )
    assert source.verified_at.isoformat() == "2026-10-19T05:35:38+00:00"
    assert (source.verification_status, source.confidence) == ("source_confirmed", "high")

    shrine = _target()
    deities = list(ShrineDeity.objects.filter(shrine=shrine).order_by("id"))
    assert [d.display_name for d in deities] == [d["display_name"] for d in EXPECTED_DEITIES]
    assert {d.role for d in deities} <= {"unknown"}
    histories = list(ShrineHistory.objects.filter(shrine=shrine).order_by("id"))
    assert [
        (h.history_type, h.title, h.content, h.period_text, h.event_date) for h in histories
    ] == [
        (h["history_type"], h["title"], h["content"], h["period_text"], None)
        for h in EXPECTED_HISTORIES
    ]
    for fact in [*deities, *histories]:
        assert [s.url for s in fact.sources.all()] == [S1_URL]
    for name in FORBIDDEN_DEITY_NAMES:
        assert not ShrineDeity.objects.filter(display_name=name).exists()
    assert ShrineDeity.objects.exclude(shrine=shrine).count() == 0
    assert ShrineHistory.objects.exclude(shrine=shrine).count() == 0


# ---------- actual Evidence Gate -----------------------------------------------------------------


@pytest.mark.django_db
def test_every_persisted_fact_is_usable_through_the_evidence_gate():
    _import_base_seed()
    _import_knowledge()
    shrine = _target()
    facts = [
        *ShrineDeity.objects.filter(shrine=shrine),
        *ShrineHistory.objects.filter(shrine=shrine),
    ]
    assert len(facts) == 8
    for fact in facts:
        statuses = list(fact.sources.values_list("verification_status", flat=True))
        assert statuses == ["source_confirmed"]
        decision = evidence_gate.decide_fact_usability(
            verification_status=fact.verification_status,
            confidence=fact.confidence,
            source_verification_statuses=statuses,
        )
        assert decision.usable is True
        assert decision.display_mode == "full"
        assert decision.reason_strength == "assertive"
        assert decision.reason == "fact_ready_with_source"


# ---------- idempotency / goriyaku isolation -----------------------------------------------------


@pytest.mark.django_db
def test_second_import_is_idempotent():
    _import_base_seed()
    _import_knowledge()

    def snapshot():
        return (
            _knowledge_counts(),
            list(ShrineKnowledgeSource.objects.order_by("id").values_list("id", flat=True)),
            list(ShrineDeity.objects.order_by("id").values_list("id", flat=True)),
            list(ShrineHistory.objects.order_by("id").values_list("id", flat=True)),
        )

    before = snapshot()
    output, error_output = _import_knowledge()
    assert (
        "plan summary: {'source_REUSE_EXISTING': 1, 'deity_SKIP_EXISTS': 3, 'history_SKIP_EXISTS': 5}"
        in output
    )
    assert "CREATE" not in output
    assert (
        "import complete: sources created=0, deities created=0, histories created=0, "
        "collectives created=0, memberships created=0, source_facts created=0"
    ) in output
    assert snapshot() == before


@pytest.mark.django_db
def test_knowledge_import_keeps_goriyaku_state_unchanged():
    _import_base_seed()
    shrine = _target()
    before = (
        shrine.goriyaku,
        list(shrine.goriyaku_tags.values_list("id", flat=True)),
        GoriyakuTag.objects.count(),
        ShrineGoriyakuAssignment.objects.count(),
    )
    _import_knowledge()
    shrine.refresh_from_db()
    after = (
        shrine.goriyaku,
        list(shrine.goriyaku_tags.values_list("id", flat=True)),
        GoriyakuTag.objects.count(),
        ShrineGoriyakuAssignment.objects.count(),
    )
    assert after == before
