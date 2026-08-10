import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.knowledge_seed import parse_seed

SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_seeds" / "batch_10_seed.json"

TARGETS = [
    ("大國魂神社", "東京都府中市宮町3-1"),
    ("寒川神社", "神奈川県高座郡寒川町宮山3916"),
    ("浅草神社", "東京都台東区浅草2-3-1"),
    ("川越氷川神社", "埼玉県川越市宮下町2-11-3"),
    ("芝大神宮", "東京都港区芝大門1-12-7"),
]


def test_batch10_seed_schema_counts_and_relations():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    assert seed.errors == []
    assert len(seed.sources) == 6
    assert len(seed.shrines) == 5
    assert sum(len(shrine.deities) for shrine in seed.shrines) == 19
    assert sum(len(shrine.histories) for shrine in seed.shrines) == 10
    assert sum(len(deity.source_keys) for shrine in seed.shrines for deity in shrine.deities) == 19
    assert (
        sum(len(history.source_keys) for shrine in seed.shrines for history in shrine.histories)
        == 10
    )

    identities = [(shrine.name_jp, shrine.address) for shrine in seed.shrines]
    assert identities == TARGETS
    assert len(identities) == len(set(identities))
    assert all(deity.source_keys for shrine in seed.shrines for deity in shrine.deities)
    assert all(history.source_keys for shrine in seed.shrines for history in shrine.histories)


def test_batch10_seed_no_within_shrine_duplicates():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    for shrine in seed.shrines:
        names = [d.display_name for d in shrine.deities]
        assert len(names) == len(set(names)), shrine.name_jp

        history_keys = [(h.history_type, h.title) for h in shrine.histories]
        assert len(history_keys) == len(set(history_keys)), shrine.name_jp


def test_batch10_seed_all_facts_are_source_confirmed_high_confidence():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    for shrine in seed.shrines:
        for deity in shrine.deities:
            assert deity.verification_status == "source_confirmed", (shrine.name_jp, deity.display_name)
            assert deity.confidence == "high", (shrine.name_jp, deity.display_name)
            assert deity.verified_at is not None, (shrine.name_jp, deity.display_name)
        for history in shrine.histories:
            assert history.verification_status == "source_confirmed", (shrine.name_jp, history.title)
            assert history.confidence == "high", (shrine.name_jp, history.title)
            assert history.verified_at is not None, (shrine.name_jp, history.title)


@pytest.mark.django_db
def test_batch10_seed_import_is_idempotent_and_preserves_unrelated_knowledge():
    for name_jp, address in TARGETS:
        Shrine.objects.create(name_jp=name_jp, kind="shrine", address=address)

    unrelated = Shrine.objects.create(
        name_jp="既存Knowledge神社（Batch10無関係）", kind="shrine", address="東京都既存区2-2-2"
    )
    existing_source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="既存公式Source（Batch10無関係）",
        url="https://existing-batch10.example.jp/",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity = ShrineDeity.objects.create(
        shrine=unrelated,
        display_name="既存祭神（Batch10無関係）",
        role="primary",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity.sources.set([existing_source])
    existing_history = ShrineHistory.objects.create(
        shrine=unrelated,
        history_type="historical_event",
        title="既存沿革（Batch10無関係）",
        content="既存の沿革本文。",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_history.sources.set([existing_source])

    call_command("import_shrine_knowledge", str(SEED_PATH), stdout=io.StringIO())

    targets = Shrine.objects.filter(name_jp__in=[name for name, _ in TARGETS])
    assert ShrineKnowledgeSource.objects.count() == 7
    assert ShrineDeity.objects.filter(shrine__in=targets).count() == 19
    assert ShrineHistory.objects.filter(shrine__in=targets).count() == 10
    assert all(deity.sources.exists() for deity in ShrineDeity.objects.filter(shrine__in=targets))
    assert all(
        history.sources.exists() for history in ShrineHistory.objects.filter(shrine__in=targets)
    )

    dry_run = io.StringIO()
    call_command("import_shrine_knowledge", str(SEED_PATH), "--dry-run", stdout=dry_run)
    output = dry_run.getvalue()
    assert "'source_REUSE_EXISTING': 6" in output
    assert "'deity_SKIP_EXISTS': 19" in output
    assert "'history_SKIP_EXISTS': 10" in output
    assert "CREATE" not in output

    existing_deity.refresh_from_db()
    existing_history.refresh_from_db()
    assert existing_deity.display_name == "既存祭神（Batch10無関係）"
    assert existing_history.content == "既存の沿革本文。"
    assert list(existing_deity.sources.all()) == [existing_source]
    assert list(existing_history.sources.all()) == [existing_source]


@pytest.mark.django_db
def test_batch10_seed_validate_only_fails_when_target_shrine_missing():
    # Only create 4 of the 5 targets — 芝大神宮 is intentionally missing.
    for name_jp, address in TARGETS[:-1]:
        Shrine.objects.create(name_jp=name_jp, kind="shrine", address=address)

    with pytest.raises(Exception):
        call_command(
            "import_shrine_knowledge",
            str(SEED_PATH),
            "--validate-only",
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )
