"""nsrc-000007 赤城社（新潟県十日町市四日町2534番地）の G4 Knowledge materialization regression。

Seed: backend/temples/data/knowledge_seeds/nsrc_000007_seed.json（Source 2 / Deity 0 / History 2）。
Authority: docs/audit/niigata-h002-nsrc-000007-g4-source-packet-freeze.md（H1 -> S2、H2 -> S3）。

- S1（新潟県神社庁）は identity / listing provenance のみで H1 / H2 と relation を持たないため serialize しない。
- 土田岐入彦命（S2 の historical 記載）/ 経津主命（research lead）は current ShrineDeity にしない。
- SourceFact / collective / goriyaku は持たない。
- verified_at の `2026-10-13T00:00:00+09:00` は date-level serialization placeholder。
  upstream が記録したのは日付 2026-10-13 のみで、`00:00:00` は時刻の事実を表さない。
- H002 には別実体の同名 `赤城社` があるため、identity は exact (name_jp, address) のみで扱う。
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
SEED_PATH = SEED_DIR / "nsrc_000007_seed.json"
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"

SHRINE_NAME = "赤城社"
SHRINE_ADDRESS = "新潟県十日町市四日町2534番地"
OTHER_AKAGI_ADDRESSES = (
    "新潟県十日町市上組2059番地子",
    "新潟県十日町市伊達乙48番地",
    "新潟県南魚沼市芹田79番地",
)

S2_KEY = "TOKAMACHI_REKIBUN_SHIRYOU"
S3_KEY = "TOKAMACHI_MUSEUM_ECHIGO_CHIJIMI_BAN"
S2_URL = "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf"
S3_URL = "https://www.tokamachi-museum.jp/archives/bunka023/"
S1_URL = "https://niigata-jinjacho.jp/shrine_niigata/search.php?area=15210&num=50"
VERIFIED_AT_PLACEHOLDER = "2026-10-13T00:00:00+09:00"

EXPECTED_SOURCES = {
    S2_KEY: {
        "key": S2_KEY,
        "source_type": "government",
        "title": "歴史文化基本構想 資料集",
        "publisher": "十日町市",
        "url": S2_URL,
        "bibliography": "中魚沼郡誌上 p.398",
        "language": "ja",
        "accessed_at": "2026-10-13",
        "verified_at": VERIFIED_AT_PLACEHOLDER,
        "verification_status": "source_confirmed",
        "confidence": "high",
    },
    S3_KEY: {
        "key": S3_KEY,
        "source_type": "museum_or_archive",
        "title": "越後縮幡",
        "publisher": "十日町市博物館",
        "url": S3_URL,
        "language": "ja",
        "accessed_at": "2026-10-13",
        "verified_at": VERIFIED_AT_PLACEHOLDER,
        "verification_status": "source_confirmed",
        "confidence": "high",
    },
}

H1 = {
    "history_type": "historical_event",
    "title": "安政7年正月の再建",
    "content": "赤城社は安政7年正月に再建された。",
    "period_text": "安政7年正月",
    "event_date": None,
    "verification_status": "source_confirmed",
    "confidence": "high",
    "verified_at": VERIFIED_AT_PLACEHOLDER,
    "source_keys": [S2_KEY],
}
H2 = {
    "history_type": "regional_context",
    "title": "赤城社に伝わった越後縮幡",
    "content": "越後縮幡のうち20旒が赤城社（四日町）に奉納されていた。",
    "period_text": "",
    "event_date": None,
    "verification_status": "source_confirmed",
    "confidence": "high",
    "verified_at": VERIFIED_AT_PLACEHOLDER,
    "source_keys": [S3_KEY],
}
# title -> exactly one related Source URL
EXPECTED_RELATIONS = {H1["title"]: S2_URL, H2["title"]: S3_URL}

BLOCKED_CODES = (
    "NOT_FOUND",
    "IMPORT_IDENTITY_AMBIGUOUS",
    "SOURCE_REUSE_CONFLICT",
    "SOURCE_REUSE_AMBIGUOUS",
)
UNAUTHORIZED_DEITY_NAMES = ("土田岐入彦命", "経津主命")


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
    }


# ---------- 1. seed file / parser contract ----------


def test_nsrc_000007_seed_exists_exactly_once():
    hits = [p for p in SEED_DIR.glob("*.json") if SHRINE_ADDRESS in p.read_text(encoding="utf-8")]
    assert hits == [SEED_PATH]


def test_nsrc_000007_seed_parser_contract():
    raw = _raw()
    parsed = parse_seed(raw)

    assert parsed.errors == []
    assert parsed.schema_version == "1.0"
    assert list(parsed.sources) == [S2_KEY, S3_KEY]
    assert len(parsed.shrines) == 1

    block = parsed.shrines[0]
    assert (block.name_jp, block.address) == (SHRINE_NAME, SHRINE_ADDRESS)
    assert len(block.deities) == 0
    assert len(block.histories) == 2
    assert list(block.collectives) == []
    assert list(block.source_facts) == []

    assert set(raw) == {"schema_version", "sources", "shrines"}
    shrine_raw = raw["shrines"][0]
    assert shrine_raw["shrine_ref"] == {"name_jp": SHRINE_NAME, "address": SHRINE_ADDRESS}
    assert set(shrine_raw) == {"shrine_ref", "deities", "histories"}
    assert shrine_raw["deities"] == []


def test_nsrc_000007_sources_are_exactly_the_frozen_s2_and_s3():
    sources = {source["key"]: source for source in _raw()["sources"]}
    assert sources == EXPECTED_SOURCES
    assert S1_URL not in SEED_PATH.read_text(encoding="utf-8")


def test_nsrc_000007_histories_are_exactly_the_frozen_wording():
    assert _raw()["shrines"][0]["histories"] == [H1, H2]


def test_nsrc_000007_fact_source_relations_are_exact():
    h1, h2 = parse_seed(_raw()).shrines[0].histories
    assert h1.title == H1["title"] and h1.source_keys == [S2_KEY]
    assert h2.title == H2["title"] and h2.source_keys == [S3_KEY]
    assert h1.event_date is None and h2.event_date is None


def test_nsrc_000007_verified_at_is_date_level_placeholder():
    """upstream authority は日付 2026-10-13 のみ。00:00:00 は時刻の事実を表さない placeholder。"""
    raw = _raw()
    values = [s["verified_at"] for s in raw["sources"]] + [
        h["verified_at"] for h in raw["shrines"][0]["histories"]
    ]
    assert values == [VERIFIED_AT_PLACEHOLDER] * 4
    assert {v.split("T")[0] for v in values} == {"2026-10-13"}
    assert {v.split("T")[1] for v in values} == {"00:00:00+09:00"}


def test_nsrc_000007_seed_has_no_unauthorized_deity_or_derived_data():
    text = SEED_PATH.read_text(encoding="utf-8")
    for name in UNAUTHORIZED_DEITY_NAMES:
        assert name not in text
    raw = _raw()
    for key in ("goriyaku", "goriyaku_tags", "source_facts", "collectives", "history_theme"):
        assert key not in raw
        assert key not in raw["shrines"][0]


# ---------- 2. exact Base Shrine resolution ----------


@pytest.mark.django_db
def test_nsrc_000007_base_shrine_resolves_exactly():
    base_count = len(json.loads(BASE_SEED_PATH.read_text(encoding="utf-8")))
    assert f"total_seed={base_count}" in _import_base_seed()

    exact = Shrine.objects.filter(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    assert exact.count() == 1

    result = resolve_shrine(SHRINE_NAME, SHRINE_ADDRESS)
    assert result.status == "OK"
    assert result.shrine is not None
    assert result.shrine.pk == exact.get().pk


@pytest.mark.django_db
def test_wrong_address_never_resolves_to_nsrc_000007():
    _import_base_seed()
    target = _target()

    others = []
    for address in OTHER_AKAGI_ADDRESSES:
        result = resolve_shrine(SHRINE_NAME, address)
        if result.shrine is not None:
            assert result.shrine.pk != target.pk
        other, _ = Shrine.objects.get_or_create(
            name_jp=SHRINE_NAME, kind="shrine", address=address
        )
        others.append(other)

    for other in others:
        result = resolve_shrine(SHRINE_NAME, other.address)
        assert result.status == "OK"
        assert result.shrine.pk == other.pk != target.pk

    assert resolve_shrine(SHRINE_NAME, SHRINE_ADDRESS).shrine.pk == target.pk


# ---------- 3. validate-only ----------


@pytest.mark.django_db
def test_nsrc_000007_validate_only_passes_without_writes():
    _import_base_seed()
    before = _knowledge_counts()

    output, error_output = _import_knowledge("--validate-only")

    assert "validate-only: OK, no errors" in output
    assert error_output == ""
    assert _knowledge_counts() == before


# ---------- 4. dry-run ----------


@pytest.mark.django_db
def test_nsrc_000007_dry_run_plans_two_sources_and_two_histories_without_writes():
    _import_base_seed()
    before = _knowledge_counts()

    output, error_output = _import_knowledge("--dry-run")
    combined = output + "\n" + error_output

    assert output.count("[source] CREATE") == 2
    assert output.count("[history] CREATE") == 2
    assert output.count("[deity] CREATE") == 0
    assert "plan summary: {'source_CREATE': 2, 'history_CREATE': 2}" in output
    for code in BLOCKED_CODES:
        assert code not in combined
    assert "dry-run: OK, no DB writes performed" in output
    assert _knowledge_counts() == before


# ---------- 5. isolated apply ----------


@pytest.mark.django_db
def test_nsrc_000007_apply_materializes_two_sourced_histories():
    _import_base_seed()
    before = _knowledge_counts()

    output, error_output = _import_knowledge()
    combined = output + "\n" + error_output

    for code in BLOCKED_CODES:
        assert code not in combined
    assert (
        "import complete: sources created=2, deities created=0, histories created=2, "
        "collectives created=0, memberships created=0, source_facts created=0"
    ) in output

    after = _knowledge_counts()
    assert {k: after[k] - before[k] for k in after} == {
        "source": 2,
        "deity": 0,
        "history": 2,
        "collective": 0,
        "source_fact": 0,
    }

    shrine = _target()
    histories = {h.title: h for h in ShrineHistory.objects.filter(shrine=shrine)}
    assert set(histories) == {H1["title"], H2["title"]}
    assert ShrineDeity.objects.filter(shrine=shrine).count() == 0
    assert ShrineDeityCollective.objects.filter(shrine=shrine).count() == 0
    assert ShrineSourceFact.objects.filter(shrine=shrine).count() == 0

    for expected in (H1, H2):
        history = histories[expected["title"]]
        assert history.history_type == expected["history_type"]
        assert history.content == expected["content"]
        assert history.period_text == expected["period_text"]
        assert history.event_date is None
        assert history.verification_status == "source_confirmed"
        assert history.confidence == "high"
        assert [s.url for s in history.sources.all()] == [EXPECTED_RELATIONS[history.title]]

    source_less = [h for h in histories.values() if not h.sources.exists()]
    assert source_less == []

    for name in UNAUTHORIZED_DEITY_NAMES:
        assert not ShrineDeity.objects.filter(display_name=name).exists()


# ---------- 6. actual Evidence Gate ----------


@pytest.mark.django_db
@pytest.mark.parametrize("title", [H1["title"], H2["title"]], ids=["H1", "H2"])
def test_nsrc_000007_history_is_usable_from_persisted_relations(title):
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


# ---------- 7. idempotency ----------


@pytest.mark.django_db
def test_nsrc_000007_second_import_is_idempotent():
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
            "history_ids": [h.pk for h in histories],
            "history_sources": {
                h.pk: tuple(h.sources.order_by("id").values_list("id", flat=True))
                for h in histories
            },
        }

    before = snapshot()
    output, error_output = _import_knowledge()
    combined = output + "\n" + error_output

    assert "plan summary: {'source_REUSE_EXISTING': 2, 'history_SKIP_EXISTS': 2}" in output
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
    for title in (H1["title"], H2["title"]):
        assert ShrineHistory.objects.filter(shrine=shrine, title=title).count() == 1


# ---------- 8. goriyaku isolation ----------


@pytest.mark.django_db
def test_nsrc_000007_knowledge_import_keeps_goriyaku_state_unchanged():
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
