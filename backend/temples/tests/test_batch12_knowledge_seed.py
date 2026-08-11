import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.knowledge_seed import parse_seed

SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_seeds" / "batch_12_seed.json"

TARGETS = [
    ("二荒山神社", "栃木県日光市山内2307"),
    ("住吉神社（博多）", "福岡県福岡市博多区住吉3-1-51"),
    ("枚岡神社", "大阪府東大阪市出雲井町7-16"),
    ("安房神社", "千葉県館山市大神宮589"),
    ("越中一宮 高瀬神社", "富山県南砺市高瀬291"),
]

# Collective/umbrella names that must never appear as their own Deity Fact
# (they are labels for a group of individually-named deities, not separate kami).
COLLECTIVE_NAMES = ["二荒山大神", "住吉五所大神", "忌部五部神"]


def test_batch12_seed_schema_counts_and_relations():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    assert seed.errors == []
    assert len(seed.sources) == 5
    assert len(seed.shrines) == 5
    assert sum(len(shrine.deities) for shrine in seed.shrines) == 22
    assert sum(len(shrine.histories) for shrine in seed.shrines) == 10
    assert sum(len(deity.source_keys) for shrine in seed.shrines for deity in shrine.deities) == 22
    assert (
        sum(len(history.source_keys) for shrine in seed.shrines for history in shrine.histories)
        == 10
    )

    identities = [(shrine.name_jp, shrine.address) for shrine in seed.shrines]
    assert identities == TARGETS
    assert len(identities) == len(set(identities))
    assert all(deity.source_keys for shrine in seed.shrines for deity in shrine.deities)
    assert all(history.source_keys for shrine in seed.shrines for history in shrine.histories)


def test_batch12_seed_excludes_collective_names_as_deity_facts():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    all_deity_names = [d.display_name for shrine in seed.shrines for d in shrine.deities]
    for collective in COLLECTIVE_NAMES:
        assert collective not in all_deity_names


def test_batch12_seed_excludes_sub_shrine_deities():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    # 摂社/末社 deities excluded: 安房神社の下の宮(天富命・天忍日命)・厳島社(市杵島姫命)・
    # 琴平社(大物主神)、高瀬神社の末社(天照皇大神・級長戸辺命・宇迦之御魂大神・菅原道真公)。
    excluded_names = [
        "天富命", "天忍日命", "市杵島姫命", "大物主神",
        "級長戸辺命", "宇迦之御魂大神",
    ]
    all_deity_names = [d.display_name for shrine in seed.shrines for d in shrine.deities]
    for name in excluded_names:
        assert name not in all_deity_names


def test_batch12_seed_no_within_shrine_duplicates():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    for shrine in seed.shrines:
        names = [d.display_name for d in shrine.deities]
        assert len(names) == len(set(names)), shrine.name_jp

        history_keys = [(h.history_type, h.title) for h in shrine.histories]
        assert len(history_keys) == len(set(history_keys)), shrine.name_jp


def test_batch12_seed_all_facts_are_source_confirmed_high_confidence():
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


def test_batch12_seed_role_assignment_matches_official_hierarchy():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))
    by_name = {shrine.name_jp: shrine for shrine in seed.shrines}

    # 二荒山神社: 公式に序列記載がないため全柱role=unknown。
    futarasan_roles = {d.display_name: d.role for d in by_name["二荒山神社"].deities}
    assert set(futarasan_roles.values()) == {"unknown"}

    # 住吉神社: 住吉三神=primary、相殿2柱=secondary。
    sumiyoshi_roles = {d.display_name: d.role for d in by_name["住吉神社（博多）"].deities}
    assert sumiyoshi_roles["底筒男神"] == "primary"
    assert sumiyoshi_roles["中筒男神"] == "primary"
    assert sumiyoshi_roles["表筒男神"] == "primary"
    assert sumiyoshi_roles["天照皇大神"] == "secondary"
    assert sumiyoshi_roles["神功皇后"] == "secondary"

    # 枚岡神社: 天児屋根命のみprimary（公式に「主祭神」と明言）、他3柱はsecondary。
    hiraoka_roles = {d.display_name: d.role for d in by_name["枚岡神社"].deities}
    assert hiraoka_roles["天児屋根命"] == "primary"
    assert hiraoka_roles["比売御神"] == "secondary"
    assert hiraoka_roles["武甕槌命"] == "secondary"
    assert hiraoka_roles["経津主命"] == "secondary"


def test_batch12_seed_source_semantic_identity_no_conflict_with_batch11():
    """Batch12の5 SourceはBatch11の5 Sourceと異なるURL/shrineであるべき
    (source_type + normalized URLの衝突がないことをseed同士で確認)。"""
    batch11_path = SEED_PATH.parent / "batch_11_seed.json"
    batch11 = json.loads(batch11_path.read_text(encoding="utf-8"))
    batch12 = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    batch11_urls = {s["url"] for s in batch11["sources"]}
    batch12_urls = {s["url"] for s in batch12["sources"]}
    assert batch11_urls.isdisjoint(batch12_urls)


@pytest.mark.django_db
def test_batch12_seed_import_is_idempotent_and_preserves_unrelated_knowledge():
    for name_jp, address in TARGETS:
        Shrine.objects.create(name_jp=name_jp, kind="shrine", address=address)

    unrelated = Shrine.objects.create(
        name_jp="既存Knowledge神社（Batch12無関係）", kind="shrine", address="東京都既存区4-4-4"
    )
    existing_source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="既存公式Source（Batch12無関係）",
        url="https://existing-batch12.example.jp/",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity = ShrineDeity.objects.create(
        shrine=unrelated,
        display_name="既存祭神（Batch12無関係）",
        role="primary",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity.sources.set([existing_source])
    existing_history = ShrineHistory.objects.create(
        shrine=unrelated,
        history_type="historical_event",
        title="既存沿革（Batch12無関係）",
        content="既存の沿革本文。",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_history.sources.set([existing_source])

    call_command("import_shrine_knowledge", str(SEED_PATH), stdout=io.StringIO())

    targets = Shrine.objects.filter(name_jp__in=[name for name, _ in TARGETS])
    assert ShrineKnowledgeSource.objects.count() == 6
    assert ShrineDeity.objects.filter(shrine__in=targets).count() == 22
    assert ShrineHistory.objects.filter(shrine__in=targets).count() == 10
    for collective in COLLECTIVE_NAMES:
        assert not ShrineDeity.objects.filter(shrine__in=targets, display_name=collective).exists()
    assert all(deity.sources.exists() for deity in ShrineDeity.objects.filter(shrine__in=targets))
    assert all(
        history.sources.exists() for history in ShrineHistory.objects.filter(shrine__in=targets)
    )

    dry_run = io.StringIO()
    call_command("import_shrine_knowledge", str(SEED_PATH), "--dry-run", stdout=dry_run)
    output = dry_run.getvalue()
    assert "'source_REUSE_EXISTING': 5" in output
    assert "'deity_SKIP_EXISTS': 22" in output
    assert "'history_SKIP_EXISTS': 10" in output
    assert "CREATE" not in output

    existing_deity.refresh_from_db()
    existing_history.refresh_from_db()
    assert existing_deity.display_name == "既存祭神（Batch12無関係）"
    assert existing_history.content == "既存の沿革本文。"
    assert list(existing_deity.sources.all()) == [existing_source]
    assert list(existing_history.sources.all()) == [existing_source]


@pytest.mark.django_db
def test_batch12_seed_validate_only_fails_when_target_shrine_missing():
    # Only create 4 of the 5 targets — 越中一宮 高瀬神社 is intentionally missing.
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
