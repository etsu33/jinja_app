import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.knowledge_seed import parse_seed

SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_seeds" / "batch_13_seed.json"

TARGETS = [
    ("富岡八幡宮", "東京都江東区富岡1-20-3"),
    ("忌宮神社", "山口県下関市長府宮の内町1-18"),
    ("高良大社", "福岡県久留米市御井町1"),
    ("笠間稲荷神社", "茨城県笠間市笠間1"),
    ("鷲宮神社", "埼玉県久喜市鷲宮1-6-1"),
]

# Deity names that must never appear: unresolvable/unnamed placeholders or
# deities belonging to a different, merely-referenced shrine.
EXCLUDED_NAMES = ["他8柱", "外8柱", "大己貴命"]


def test_batch13_seed_schema_counts_and_relations():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    assert seed.errors == []
    assert len(seed.sources) == 5
    assert len(seed.shrines) == 5
    assert sum(len(shrine.deities) for shrine in seed.shrines) == 10
    assert sum(len(shrine.histories) for shrine in seed.shrines) == 10
    assert sum(len(deity.source_keys) for shrine in seed.shrines for deity in shrine.deities) == 10
    assert (
        sum(len(history.source_keys) for shrine in seed.shrines for history in shrine.histories)
        == 10
    )

    identities = [(shrine.name_jp, shrine.address) for shrine in seed.shrines]
    assert identities == TARGETS
    assert len(identities) == len(set(identities))
    assert all(deity.source_keys for shrine in seed.shrines for deity in shrine.deities)
    assert all(history.source_keys for shrine in seed.shrines for history in shrine.histories)


def test_batch13_seed_tomioka_hachimangu_has_only_named_deity():
    """富岡八幡宮の公式サイトは「応神天皇（誉田別命）外８柱」とのみ記載し、
    他8柱の個別名を明かしていない。未確認の8柱を推測登録せず、
    collective Factとしても作成していないことを固定化する。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    tomioka = next(shrine for shrine in seed.shrines if shrine.name_jp == "富岡八幡宮")
    deity_names = [d.display_name for d in tomioka.deities]
    assert deity_names == ["応神天皇"]
    for excluded in EXCLUDED_NAMES:
        assert excluded not in deity_names


def test_batch13_seed_washinomiya_excludes_referenced_shrine_deity():
    """鷲宮神社の由緒冒頭に登場する「神崎神社（大己貴命）」は、鷲宮神社
    創建以前に天穂日命父子が別途建てた他の神社の祭神であり、鷲宮神社
    自体の祭神ではない。誤って鷲宮神社の祭神としてFact化していないことを
    固定化する。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    washinomiya = next(shrine for shrine in seed.shrines if shrine.name_jp == "鷲宮神社")
    deity_names = [d.display_name for d in washinomiya.deities]
    assert deity_names == ["天穂日命", "武夷鳥命"]
    assert "大己貴命" not in deity_names


def test_batch13_seed_no_within_shrine_duplicates():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    for shrine in seed.shrines:
        names = [d.display_name for d in shrine.deities]
        assert len(names) == len(set(names)), shrine.name_jp

        history_keys = [(h.history_type, h.title) for h in shrine.histories]
        assert len(history_keys) == len(set(history_keys)), shrine.name_jp


def test_batch13_seed_all_facts_are_source_confirmed_high_confidence():
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


def test_batch13_seed_role_assignment_matches_official_hierarchy():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))
    by_name = {shrine.name_jp: shrine for shrine in seed.shrines}

    koura_roles = {d.display_name: d.role for d in by_name["高良大社"].deities}
    assert koura_roles["高良玉垂命"] == "primary"
    assert koura_roles["八幡大神"] == "secondary"
    assert koura_roles["住吉大神"] == "secondary"

    iminomiya_roles = {d.display_name: d.role for d in by_name["忌宮神社"].deities}
    assert iminomiya_roles["仲哀天皇"] == "primary"
    assert iminomiya_roles["神功皇后"] == "secondary"
    assert iminomiya_roles["応神天皇"] == "secondary"


def test_batch13_seed_source_semantic_identity_no_conflict_with_prior_batches():
    """Batch13の5 SourceはBatch11/12のSourceと異なるURLであるべき
    (source_type + normalized URLの衝突がないことをseed同士で確認)。"""
    seed_dir = SEED_PATH.parent
    batch11 = json.loads((seed_dir / "batch_11_seed.json").read_text(encoding="utf-8"))
    batch12 = json.loads((seed_dir / "batch_12_seed.json").read_text(encoding="utf-8"))
    batch13 = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    prior_urls = {s["url"] for s in batch11["sources"]} | {s["url"] for s in batch12["sources"]}
    batch13_urls = {s["url"] for s in batch13["sources"]}
    assert prior_urls.isdisjoint(batch13_urls)


@pytest.mark.django_db
def test_batch13_seed_import_is_idempotent_and_preserves_unrelated_knowledge():
    for name_jp, address in TARGETS:
        Shrine.objects.create(name_jp=name_jp, kind="shrine", address=address)

    unrelated = Shrine.objects.create(
        name_jp="既存Knowledge神社（Batch13無関係）", kind="shrine", address="東京都既存区5-5-5"
    )
    existing_source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="既存公式Source（Batch13無関係）",
        url="https://existing-batch13.example.jp/",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity = ShrineDeity.objects.create(
        shrine=unrelated,
        display_name="既存祭神（Batch13無関係）",
        role="primary",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity.sources.set([existing_source])
    existing_history = ShrineHistory.objects.create(
        shrine=unrelated,
        history_type="historical_event",
        title="既存沿革（Batch13無関係）",
        content="既存の沿革本文。",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_history.sources.set([existing_source])

    call_command("import_shrine_knowledge", str(SEED_PATH), stdout=io.StringIO())

    targets = Shrine.objects.filter(name_jp__in=[name for name, _ in TARGETS])
    assert ShrineKnowledgeSource.objects.count() == 6
    assert ShrineDeity.objects.filter(shrine__in=targets).count() == 10
    assert ShrineHistory.objects.filter(shrine__in=targets).count() == 10
    for excluded in EXCLUDED_NAMES:
        assert not ShrineDeity.objects.filter(shrine__in=targets, display_name=excluded).exists()
    assert all(deity.sources.exists() for deity in ShrineDeity.objects.filter(shrine__in=targets))
    assert all(
        history.sources.exists() for history in ShrineHistory.objects.filter(shrine__in=targets)
    )

    dry_run = io.StringIO()
    call_command("import_shrine_knowledge", str(SEED_PATH), "--dry-run", stdout=dry_run)
    output = dry_run.getvalue()
    assert "'source_REUSE_EXISTING': 5" in output
    assert "'deity_SKIP_EXISTS': 10" in output
    assert "'history_SKIP_EXISTS': 10" in output
    assert "CREATE" not in output

    existing_deity.refresh_from_db()
    existing_history.refresh_from_db()
    assert existing_deity.display_name == "既存祭神（Batch13無関係）"
    assert existing_history.content == "既存の沿革本文。"
    assert list(existing_deity.sources.all()) == [existing_source]
    assert list(existing_history.sources.all()) == [existing_source]


@pytest.mark.django_db
def test_batch13_seed_validate_only_fails_when_target_shrine_missing():
    # Only create 4 of the 5 targets — 鷲宮神社 is intentionally missing.
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
