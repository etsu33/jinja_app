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


@pytest.mark.django_db
def test_nsrc_000004_knowledge_seed_dry_run_passes_without_writes():
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )

    before = {
        "source": ShrineKnowledgeSource.objects.count(),
        "deity": ShrineDeity.objects.count(),
        "history": ShrineHistory.objects.count(),
        "source_fact": ShrineSourceFact.objects.count(),
        "goriyaku_assignment": ShrineGoriyakuAssignment.objects.count(),
    }

    out = io.StringIO()
    call_command(
        "import_shrine_knowledge",
        str(SEED_PATH),
        "--dry-run",
        stdout=out,
        stderr=io.StringIO(),
    )
    output = out.getvalue()

    assert "[source] CREATE" in output
    assert output.count("[source] CREATE") == 3
    assert output.count("[deity] CREATE") == 2
    assert output.count("[history] CREATE") == 2
    assert output.count("[source_fact] CREATE") == 11
    assert "source_CREATE': 3" in output
    assert "deity_CREATE': 2" in output
    assert "history_CREATE': 2" in output
    assert "source_fact_CREATE': 11" in output
    assert "SOURCE_REUSE_CONFLICT" not in output
    assert "SOURCE_REUSE_AMBIGUOUS" not in output
    assert "IMPORT_IDENTITY_AMBIGUOUS" not in output
    assert "NOT_FOUND" not in output
    assert "dry-run: OK, no DB writes performed" in output

    after = {
        "source": ShrineKnowledgeSource.objects.count(),
        "deity": ShrineDeity.objects.count(),
        "history": ShrineHistory.objects.count(),
        "source_fact": ShrineSourceFact.objects.count(),
        "goriyaku_assignment": ShrineGoriyakuAssignment.objects.count(),
    }
    assert after == before


@pytest.mark.django_db
def test_nsrc_000004_knowledge_seed_apply_passes_with_no_identity_or_source_errors():
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )

    out = io.StringIO()
    err = io.StringIO()
    call_command(
        "import_shrine_knowledge",
        str(SEED_PATH),
        stdout=out,
        stderr=err,
    )
    output = out.getvalue()
    error_output = err.getvalue()
    combined = output + "\n" + error_output

    for blocked_code in (
        "NOT_FOUND",
        "IMPORT_IDENTITY_AMBIGUOUS",
        "SOURCE_REUSE_CONFLICT",
        "SOURCE_REUSE_AMBIGUOUS",
    ):
        assert blocked_code not in combined

    assert "import complete: sources created=3, deities created=2, histories created=2, collectives created=0, memberships created=0, source_facts created=11" in output

    shrine = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    deities = list(ShrineDeity.objects.filter(shrine=shrine).order_by("id"))
    histories = list(ShrineHistory.objects.filter(shrine=shrine).order_by("id"))

    assert [deity.display_name for deity in deities] == ["椎根津彦命", "大国魂命"]
    assert [history.title for history in histories] == ["神亀3年の創建", "明治5年の三社本殿合殿"]
    assert ShrineKnowledgeSource.objects.count() == 3
    assert ShrineSourceFact.objects.filter(shrine=shrine).count() == 11

    assert sum(1 for deity in deities if not deity.sources.exists()) == 0
    assert sum(1 for history in histories if not history.sources.exists()) == 0


@pytest.mark.django_db
def test_nsrc_000004_d1_d2_h1_h2_are_usable_under_evidence_gate():
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    call_command(
        "import_shrine_knowledge",
        str(SEED_PATH),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )

    shrine = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    facts = [
        (
            "D1",
            ShrineDeity.objects.get(shrine=shrine, display_name="椎根津彦命"),
            "https://www.aomi-jinjya.or.jp/history/gosaisin.html",
        ),
        (
            "D2",
            ShrineDeity.objects.get(shrine=shrine, display_name="大国魂命"),
            "https://www.aomi-jinjya.or.jp/history/gosaisin.html",
        ),
        (
            "H1",
            ShrineHistory.objects.get(shrine=shrine, title="神亀3年の創建"),
            "https://www.aomi-jinjya.or.jp/history/yuisyo.html",
        ),
        (
            "H2",
            ShrineHistory.objects.get(shrine=shrine, title="明治5年の三社本殿合殿"),
            "https://www.aomi-jinjya.or.jp/history/yuisyo.html",
        ),
    ]

    for label, fact, expected_source_url in facts:
        source_statuses = list(fact.sources.values_list("verification_status", flat=True))
        source_urls = list(fact.sources.values_list("url", flat=True))

        assert source_statuses == ["source_confirmed"], label
        assert source_urls == [expected_source_url], label

        decision = evidence_gate.decide_fact_usability(
            verification_status=fact.verification_status,
            confidence=fact.confidence,
            source_verification_statuses=source_statuses,
        )

        assert decision.usable is True, label
        assert decision.display_mode == "full", label
        assert decision.reason_strength == "assertive", label
        assert decision.reason == "fact_ready_with_source", label
        assert decision.verification_status == "source_confirmed", label
        assert decision.confidence == "high", label


@pytest.mark.django_db
def test_nsrc_000004_source_facts_all_link_exactly_to_s4():
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    call_command(
        "import_shrine_knowledge",
        str(SEED_PATH),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )

    shrine = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    facts = list(ShrineSourceFact.objects.filter(shrine=shrine).order_by("stable_key"))

    expected_stable_keys = {
        "aomi_jinja_kamo__prayer__kanai_anzen",
        "aomi_jinja_kamo__prayer__kosazuke_kigan",
        "aomi_jinja_kamo__prayer__anzan_kigan",
        "aomi_jinja_kamo__prayer__kotsu_anzen",
        "aomi_jinja_kamo__prayer__yakubarai",
        "aomi_jinja_kamo__prayer__hoi_barai",
        "aomi_jinja_kamo__prayer__byoki_heiyu_kigan",
        "aomi_jinja_kamo__prayer__mi_no_anzen_kigan",
        "aomi_jinja_kamo__prayer__gokaku_kigan",
        "aomi_jinja_kamo__prayer__shobai_hanjo",
        "aomi_jinja_kamo__prayer__hissho_kigan",
    }

    assert len(facts) == 11
    assert {fact.stable_key for fact in facts} == expected_stable_keys

    s4_url = "https://www.aomi-jinjya.or.jp/gokitou/syurui.html"
    s4 = ShrineKnowledgeSource.objects.get(
        source_type="shrine_official",
        url=s4_url,
    )
    assert s4.verification_status == "source_confirmed"

    for fact in facts:
        linked_sources = list(fact.sources.all())
        assert len(linked_sources) == 1, fact.stable_key
        assert linked_sources[0].pk == s4.pk, fact.stable_key
        assert linked_sources[0].url == s4_url, fact.stable_key
        assert linked_sources[0].source_type == "shrine_official", fact.stable_key
        assert linked_sources[0].verification_status == "source_confirmed", fact.stable_key


@pytest.mark.django_db
def test_nsrc_000004_second_import_is_idempotent():
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    call_command(
        "import_shrine_knowledge",
        str(SEED_PATH),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )

    shrine = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)

    def snapshot():
        deities = list(ShrineDeity.objects.filter(shrine=shrine).order_by("id"))
        histories = list(ShrineHistory.objects.filter(shrine=shrine).order_by("id"))
        source_facts = list(ShrineSourceFact.objects.filter(shrine=shrine).order_by("id"))
        sources = list(ShrineKnowledgeSource.objects.order_by("id"))

        return {
            "source_ids": [source.pk for source in sources],
            "deity_ids": [deity.pk for deity in deities],
            "history_ids": [history.pk for history in histories],
            "source_fact_ids": [fact.pk for fact in source_facts],
            "deity_sources": {
                deity.pk: tuple(deity.sources.order_by("id").values_list("id", flat=True))
                for deity in deities
            },
            "history_sources": {
                history.pk: tuple(history.sources.order_by("id").values_list("id", flat=True))
                for history in histories
            },
            "source_fact_sources": {
                fact.pk: tuple(fact.sources.order_by("id").values_list("id", flat=True))
                for fact in source_facts
            },
        }

    before = snapshot()

    out = io.StringIO()
    err = io.StringIO()
    call_command(
        "import_shrine_knowledge",
        str(SEED_PATH),
        stdout=out,
        stderr=err,
    )
    output = out.getvalue()
    combined = output + "\n" + err.getvalue()

    assert "'source_REUSE_EXISTING': 3" in output
    assert "'deity_SKIP_EXISTS': 2" in output
    assert "'history_SKIP_EXISTS': 2" in output
    assert "'source_fact_SKIP_EXISTS': 11" in output
    assert "CREATE" not in output

    for blocked_code in (
        "NOT_FOUND",
        "IMPORT_IDENTITY_AMBIGUOUS",
        "SOURCE_REUSE_CONFLICT",
        "SOURCE_REUSE_AMBIGUOUS",
        "SOURCE_FACT_CONFLICT",
    ):
        assert blocked_code not in combined

    assert "import complete: sources created=0, deities created=0, histories created=0, collectives created=0, memberships created=0, source_facts created=0" in output
    assert snapshot() == before


@pytest.mark.django_db
def test_nsrc_000004_knowledge_import_keeps_goriyaku_state_unchanged():
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )

    shrine = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)

    before = {
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

    assert before["goriyaku"] == ""
    assert before["goriyaku_tag_ids"] == ()

    call_command(
        "import_shrine_knowledge",
        str(SEED_PATH),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )

    shrine.refresh_from_db()
    after = {
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

    assert ShrineSourceFact.objects.filter(shrine=shrine).count() == 11
    assert after == before
