"""nsrc-000006 赤井神社の G4 Knowledge materialization regression。

Seed:
backend/temples/data/knowledge_seeds/nsrc_000006_seed.json
（Source 2 / Deity 0 / History 3）

Authority:
docs/audit/niigata-h002-nsrc-000006-g4-source-packet-freeze.md

- S1 新潟県神社庁は identity / listing provenance のみでKnowledge Seedへserializeしない。
- 1926年『佐渡神社誌』の祭神・合祀記録はcurrent ShrineDeityへ昇格させない。
- SourceFact / collective / goriyaku / derived knowledgeは持たない。
- verified_at の 00:00:00+09:00 はdate-level serialization placeholderであり、
  source verification時刻を意味しない。
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
    ShrineGoriyakuAssignment,
    ShrineHistory,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.services import evidence_gate
from temples.services.knowledge_seed import parse_seed, resolve_shrine

TEMPLES_DIR = Path(__file__).resolve().parents[1]
SEED_DIR = TEMPLES_DIR / "data" / "knowledge_seeds"
SEED_PATH = SEED_DIR / "nsrc_000006_seed.json"
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"

SHRINE_NAME = "赤井神社"
SHRINE_ADDRESS = "新潟県佐渡市加茂歌代2662番地"
NON_CANONICAL_ADDRESSES = (
    "新潟県佐渡市加茂歌代2622番地",
    "新潟県佐渡市加茂歌代1164-7",
)

S2_KEY = "SADO_GEINOU_KAMOUTASHIRO_ONIDAIKO"
S3_KEY = "SADO_JINJASHI_1926"
S2_URL = "https://sado-geinou.com/geinou/kamoutashiro/"
S3_URL = "https://dl.ndl.go.jp/pid/971197"
S1_URL = "https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15224"
VERIFIED_AT_PLACEHOLDER = "2026-10-14T00:00:00+09:00"

EXPECTED_SOURCES = {
    S2_KEY: {
        "key": S2_KEY,
        "source_type": "tourism_official",
        "title": "加茂歌代まつりの鬼太鼓",
        "publisher": "佐渡芸能アーカイブ",
        "url": S2_URL,
        "language": "ja",
        "accessed_at": "2026-10-14",
        "verified_at": VERIFIED_AT_PLACEHOLDER,
        "verification_status": "source_confirmed",
        "confidence": "high",
    },
    S3_KEY: {
        "key": S3_KEY,
        "source_type": "local_history",
        "title": "佐渡神社誌",
        "publisher": "新潟県神職会佐渡支部",
        "url": S3_URL,
        "bibliography": "新潟県神職会佐渡支部 編, 1926（大正15）, NDL書誌ID 000000585602",
        "language": "ja",
        "accessed_at": "2026-10-14",
        "verified_at": VERIFIED_AT_PLACEHOLDER,
        "verification_status": "source_confirmed",
        "confidence": "high",
    },
}

H1 = {
    "history_type": "regional_context",
    "title": "4月16日の赤井神社例祭と鬼太鼓奉納",
    "content": (
        "赤井神社の4月16日の例祭では、加茂歌代の上組・中組・下組の鬼太鼓が"
        "神社で舞を奉納した後、各地区を門付けする。"
    ),
    "period_text": "",
    "event_date": None,
    "verification_status": "source_confirmed",
    "confidence": "high",
    "verified_at": VERIFIED_AT_PLACEHOLDER,
    "source_keys": [S2_KEY],
}
H2 = {
    "history_type": "tradition",
    "title": "元日午前0時の鬼太鼓奉納",
    "content": "加茂歌代の鬼太鼓は、元日の午前0時にも赤井神社で舞を奉納する。",
    "period_text": "",
    "event_date": None,
    "verification_status": "source_confirmed",
    "confidence": "high",
    "verified_at": VERIFIED_AT_PLACEHOLDER,
    "source_keys": [S2_KEY],
}
H3 = {
    "history_type": "regional_context",
    "title": "加茂の五神社としての記録",
    "content": (
        "1926年刊『佐渡神社誌』は、堀内・春日・歌代・諏訪・赤井を"
        "「加茂の五神社」と記録している。"
    ),
    "period_text": "",
    "event_date": None,
    "verification_status": "source_confirmed",
    "confidence": "high",
    "verified_at": VERIFIED_AT_PLACEHOLDER,
    "source_keys": [S3_KEY],
}

EXPECTED_RELATIONS = {
    H1["title"]: S2_URL,
    H2["title"]: S2_URL,
    H3["title"]: S3_URL,
}

BLOCKED_CODES = (
    "NOT_FOUND",
    "IMPORT_IDENTITY_AMBIGUOUS",
    "SOURCE_REUSE_CONFLICT",
    "SOURCE_REUSE_AMBIGUOUS",
)

UNAUTHORIZED_DEITY_NAMES = (
    "素盞嗚尊",
    "別雷尊",
    "倉稲魂命",
    "菅原道真公",
    "大己貴尊",
    "大国主命",
)


def _raw() -> dict:
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def _base_count() -> int:
    return len(json.loads(BASE_SEED_PATH.read_text(encoding="utf-8")))


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
    }


# ---------- 1. seed / parser / frozen payload ---------------------------------------------------


def test_nsrc_000006_seed_exists_exactly_once():
    hits = [p for p in SEED_DIR.glob("*.json") if SHRINE_ADDRESS in p.read_text(encoding="utf-8")]
    assert hits == [SEED_PATH]


def test_nsrc_000006_seed_parser_contract():
    raw = _raw()
    parsed = parse_seed(raw)

    assert parsed.errors == []
    assert parsed.schema_version == "1.0"
    assert list(parsed.sources) == [S2_KEY, S3_KEY]
    assert len(parsed.shrines) == 1

    block = parsed.shrines[0]
    assert (block.name_jp, block.address) == (SHRINE_NAME, SHRINE_ADDRESS)
    assert len(block.deities) == 0
    assert len(block.histories) == 3
    assert list(block.collectives) == []
    assert list(block.source_facts) == []

    assert set(raw) == {"schema_version", "sources", "shrines"}
    shrine_raw = raw["shrines"][0]
    assert shrine_raw["shrine_ref"] == {"name_jp": SHRINE_NAME, "address": SHRINE_ADDRESS}
    assert set(shrine_raw) == {"shrine_ref", "deities", "histories"}
    assert shrine_raw["deities"] == []


def test_nsrc_000006_sources_are_exactly_the_frozen_s2_and_s3():
    sources = {source["key"]: source for source in _raw()["sources"]}
    assert sources == EXPECTED_SOURCES

    text = SEED_PATH.read_text(encoding="utf-8")
    assert S1_URL not in text


def test_nsrc_000006_source_urls_are_not_reused_by_other_seed_files():
    other_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(SEED_DIR.glob("*.json"))
        if path != SEED_PATH
    )
    assert S2_URL not in other_text
    assert S3_URL not in other_text


def test_nsrc_000006_histories_are_exactly_the_frozen_wording():
    assert _raw()["shrines"][0]["histories"] == [H1, H2, H3]


def test_nsrc_000006_fact_source_relations_are_exact():
    histories = parse_seed(_raw()).shrines[0].histories
    assert len(histories) == 3

    by_title = {history.title: history for history in histories}
    assert set(by_title) == {H1["title"], H2["title"], H3["title"]}

    assert by_title[H1["title"]].source_keys == [S2_KEY]
    assert by_title[H2["title"]].source_keys == [S2_KEY]
    assert by_title[H3["title"]].source_keys == [S3_KEY]
    assert all(history.event_date is None for history in histories)


def test_nsrc_000006_verified_at_is_date_level_placeholder():
    raw = _raw()
    values = [source["verified_at"] for source in raw["sources"]] + [
        history["verified_at"] for history in raw["shrines"][0]["histories"]
    ]
    assert values == [VERIFIED_AT_PLACEHOLDER] * 5
    assert {value.split("T")[0] for value in values} == {"2026-10-14"}
    assert {value.split("T")[1] for value in values} == {"00:00:00+09:00"}


def test_nsrc_000006_seed_has_no_current_deity_or_derived_data():
    text = SEED_PATH.read_text(encoding="utf-8")
    for name in UNAUTHORIZED_DEITY_NAMES:
        assert name not in text

    raw = _raw()
    for key in ("goriyaku", "goriyaku_tags", "source_facts", "collectives", "history_theme"):
        assert key not in raw
        assert key not in raw["shrines"][0]


# ---------- 2. exact Base Shrine resolution ------------------------------------------------------


@pytest.mark.django_db
def test_nsrc_000006_base_shrine_resolves_exactly():
    summary = _import_base_seed()
    assert f"total_seed={_base_count()}" in summary

    exact = Shrine.objects.filter(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    assert exact.count() == 1

    result = resolve_shrine(SHRINE_NAME, SHRINE_ADDRESS)
    assert result.status == "OK"
    assert result.shrine is not None
    assert result.shrine.pk == exact.get().pk


@pytest.mark.django_db
@pytest.mark.parametrize("address", NON_CANONICAL_ADDRESSES)
def test_noncanonical_address_never_resolves_to_nsrc_000006(address):
    _import_base_seed()
    target = _target()

    result = resolve_shrine(SHRINE_NAME, address)
    assert result.status == "NOT_FOUND"
    assert result.shrine is None or result.shrine.pk != target.pk


# ---------- 3. validate-only ---------------------------------------------------------------------


@pytest.mark.django_db
def test_nsrc_000006_validate_only_passes_without_writes():
    _import_base_seed()
    before = _knowledge_counts()

    output, error_output = _import_knowledge("--validate-only")

    assert "validate-only: OK, no errors" in output
    assert error_output == ""
    assert _knowledge_counts() == before


# ---------- 4. dry-run ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_nsrc_000006_dry_run_plans_two_sources_and_three_histories_without_writes():
    _import_base_seed()
    before = _knowledge_counts()

    output, error_output = _import_knowledge("--dry-run")
    combined = output + "\n" + error_output

    assert output.count("[source] CREATE") == 2
    assert output.count("[history] CREATE") == 3
    assert output.count("[deity] CREATE") == 0
    assert "plan summary: {'source_CREATE': 2, 'history_CREATE': 3}" in output
    for code in BLOCKED_CODES:
        assert code not in combined
    assert "dry-run: OK, no DB writes performed" in output
    assert _knowledge_counts() == before


# ---------- 5. isolated apply --------------------------------------------------------------------


@pytest.mark.django_db
def test_nsrc_000006_apply_materializes_three_sourced_histories():
    _import_base_seed()
    before = _knowledge_counts()

    output, error_output = _import_knowledge()
    combined = output + "\n" + error_output

    for code in BLOCKED_CODES:
        assert code not in combined
    assert (
        "import complete: sources created=2, deities created=0, histories created=3, "
        "collectives created=0, memberships created=0, source_facts created=0"
    ) in output

    after = _knowledge_counts()
    assert {key: after[key] - before[key] for key in after} == {
        "source": 2,
        "deity": 0,
        "history": 3,
        "collective": 0,
        "source_fact": 0,
    }

    shrine = _target()
    histories = {history.title: history for history in ShrineHistory.objects.filter(shrine=shrine)}
    assert set(histories) == {H1["title"], H2["title"], H3["title"]}

    assert ShrineDeity.objects.filter(shrine=shrine).count() == 0
    assert ShrineDeityCollective.objects.filter(shrine=shrine).count() == 0
    assert ShrineSourceFact.objects.filter(shrine=shrine).count() == 0

    for expected in (H1, H2, H3):
        history = histories[expected["title"]]
        assert history.history_type == expected["history_type"]
        assert history.content == expected["content"]
        assert history.period_text == ""
        assert history.event_date is None
        assert history.verification_status == "source_confirmed"
        assert history.confidence == "high"
        assert [source.url for source in history.sources.all()] == [
            EXPECTED_RELATIONS[history.title]
        ]

    assert [history for history in histories.values() if not history.sources.exists()] == []

    for name in UNAUTHORIZED_DEITY_NAMES:
        assert not ShrineDeity.objects.filter(display_name=name).exists()


# ---------- 6. actual Evidence Gate ---------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "title",
    [H1["title"], H2["title"], H3["title"]],
    ids=["H1", "H2", "H3"],
)
def test_nsrc_000006_history_is_usable_from_persisted_relations(title):
    _import_base_seed()
    _import_knowledge()

    history = ShrineHistory.objects.get(shrine=_target(), title=title)
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


# ---------- 7. idempotency -----------------------------------------------------------------------


@pytest.mark.django_db
def test_nsrc_000006_second_import_is_idempotent():
    _import_base_seed()
    _import_knowledge()
    shrine = _target()

    def snapshot() -> dict:
        histories = list(ShrineHistory.objects.filter(shrine=shrine).order_by("id"))
        return {
            "counts": _knowledge_counts(),
            "source_ids": list(
                ShrineKnowledgeSource.objects.order_by("id").values_list("id", flat=True)
            ),
            "history_ids": [history.pk for history in histories],
            "history_sources": {
                history.pk: tuple(history.sources.order_by("id").values_list("id", flat=True))
                for history in histories
            },
        }

    before = snapshot()
    output, error_output = _import_knowledge()
    combined = output + "\n" + error_output

    assert "plan summary: {'source_REUSE_EXISTING': 2, 'history_SKIP_EXISTS': 3}" in output
    assert "CREATE" not in output
    for code in (*BLOCKED_CODES, "SOURCE_FACT_CONFLICT"):
        assert code not in combined
    assert (
        "import complete: sources created=0, deities created=0, histories created=0, "
        "collectives created=0, memberships created=0, source_facts created=0"
    ) in output

    assert snapshot() == before
    assert ShrineKnowledgeSource.objects.filter(url=S2_URL).count() == 1
    assert ShrineKnowledgeSource.objects.filter(url=S3_URL).count() == 1
    for title in (H1["title"], H2["title"], H3["title"]):
        assert ShrineHistory.objects.filter(shrine=shrine, title=title).count() == 1


# ---------- 8. goriyaku isolation ----------------------------------------------------------------


@pytest.mark.django_db
def test_nsrc_000006_knowledge_import_keeps_goriyaku_state_unchanged():
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
    _import_knowledge()

    assert snapshot() == before
