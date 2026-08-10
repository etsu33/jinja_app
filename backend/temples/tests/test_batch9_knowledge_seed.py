import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.knowledge_seed import parse_seed


SEED_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "knowledge_seeds" / "batch_9_seed.json"
)

TARGETS = [
    ("宇佐神宮", "大分県宇佐市南宇佐2859"),
    ("氷川神社（大宮）", "埼玉県さいたま市大宮区高鼻町1-407"),
    ("貴船神社", "京都府京都市左京区鞍馬貴船町180"),
    ("大洗磯前神社", "茨城県東茨城郡大洗町磯浜町6890"),
    ("箱根神社", "神奈川県足柄下郡箱根町元箱根80-1"),
]


def test_batch9_seed_schema_counts_and_relations():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    assert seed.errors == []
    assert len(seed.sources) == 6
    assert len(seed.shrines) == 5
    assert sum(len(shrine.deities) for shrine in seed.shrines) == 13
    assert sum(len(shrine.histories) for shrine in seed.shrines) == 5
    assert sum(len(deity.source_keys) for shrine in seed.shrines for deity in shrine.deities) == 13
    assert (
        sum(len(history.source_keys) for shrine in seed.shrines for history in shrine.histories)
        == 5
    )

    identities = [(shrine.name_jp, shrine.address) for shrine in seed.shrines]
    assert identities == TARGETS
    assert len(identities) == len(set(identities))
    assert all(deity.source_keys for shrine in seed.shrines for deity in shrine.deities)
    assert all(history.source_keys for shrine in seed.shrines for history in shrine.histories)


@pytest.mark.django_db
def test_batch9_seed_import_is_idempotent_and_preserves_unrelated_knowledge():
    for name_jp, address in TARGETS:
        Shrine.objects.create(name_jp=name_jp, kind="shrine", address=address)

    unrelated = Shrine.objects.create(
        name_jp="既存Knowledge神社", kind="shrine", address="東京都既存区1-1-1"
    )
    existing_source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="既存公式Source",
        url="https://existing.example.jp/",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity = ShrineDeity.objects.create(
        shrine=unrelated,
        display_name="既存祭神",
        role="primary",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity.sources.set([existing_source])
    existing_history = ShrineHistory.objects.create(
        shrine=unrelated,
        history_type="historical_event",
        title="既存沿革",
        content="既存の沿革本文。",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_history.sources.set([existing_source])

    call_command("import_shrine_knowledge", str(SEED_PATH), stdout=io.StringIO())

    targets = Shrine.objects.filter(name_jp__in=[name for name, _ in TARGETS])
    assert ShrineKnowledgeSource.objects.count() == 7
    assert ShrineDeity.objects.filter(shrine__in=targets).count() == 13
    assert ShrineHistory.objects.filter(shrine__in=targets).count() == 5
    assert all(deity.sources.exists() for deity in ShrineDeity.objects.filter(shrine__in=targets))
    assert all(
        history.sources.exists() for history in ShrineHistory.objects.filter(shrine__in=targets)
    )

    dry_run = io.StringIO()
    call_command("import_shrine_knowledge", str(SEED_PATH), "--dry-run", stdout=dry_run)
    output = dry_run.getvalue()
    assert "'source_SKIP_EXISTS': 6" in output
    assert "'deity_SKIP_EXISTS': 13" in output
    assert "'history_SKIP_EXISTS': 5" in output
    assert "CREATE" not in output

    existing_deity.refresh_from_db()
    existing_history.refresh_from_db()
    assert existing_deity.display_name == "既存祭神"
    assert existing_history.content == "既存の沿革本文。"
    assert list(existing_deity.sources.all()) == [existing_source]
    assert list(existing_history.sources.all()) == [existing_source]
