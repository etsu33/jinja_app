import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.knowledge_seed import parse_seed

SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_seeds" / "batch_16_seed.json"

TARGETS = [
    ("平塚八幡宮", "神奈川県平塚市浅間町1-6"),
    ("櫻木神社", "千葉県野田市桜台210"),
    ("多摩川浅間神社", "東京都大田区田園調布1-55-12"),
    ("宇都宮二荒山神社", "栃木県宇都宮市馬場通り1-1-1"),
    ("白山神社", "東京都文京区白山5-31-26"),
]


def test_batch16_seed_schema_counts_and_relations():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    assert seed.errors == []
    assert len(seed.sources) == 5
    assert len(seed.shrines) == 5
    assert sum(len(shrine.deities) for shrine in seed.shrines) == 14
    assert sum(len(shrine.histories) for shrine in seed.shrines) == 15
    assert sum(len(deity.source_keys) for shrine in seed.shrines for deity in shrine.deities) == 14
    assert (
        sum(len(history.source_keys) for shrine in seed.shrines for history in shrine.histories)
        == 15
    )

    identities = [(shrine.name_jp, shrine.address) for shrine in seed.shrines]
    assert identities == TARGETS
    assert len(identities) == len(set(identities))
    assert all(deity.source_keys for shrine in seed.shrines for deity in shrine.deities)
    assert all(history.source_keys for shrine in seed.shrines for history in shrine.histories)


def test_batch16_seed_hiratsuka_hachimangu_excludes_sub_shrines():
    """平塚八幡宮の境内絵図に記載される「弁財天社」（七福神の一）・
    「末社三社」を本社Factへ混入させていないことを固定化する。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    hiratsuka = next(shrine for shrine in seed.shrines if shrine.name_jp == "平塚八幡宮")
    deity_names = [d.display_name for d in hiratsuka.deities]
    assert deity_names == ["応神天皇", "神功皇后", "武内宿禰"]


def test_batch16_seed_sengenjinja_excludes_absorbed_shrine_deities():
    """多摩川浅間神社が明治40年(1907)の合祀政令で統合した旧赤城神社・
    熊野神社の祭神を、現在の御祭神一覧に含まれていないことに基づき
    Fact化していないことを固定化する（木花咲耶姫命の一柱のみ）。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    sengen = next(shrine for shrine in seed.shrines if shrine.name_jp == "多摩川浅間神社")
    deity_names = [d.display_name for d in sengen.deities]
    assert deity_names == ["木花咲耶姫命"]


def test_batch16_seed_futaarayama_excludes_sub_shrines_and_is_utsunomiya():
    """宇都宮二荒山神社の境内十二末社を本社Factへ混入させていないこと、
    および日光二荒山神社と混同していないこと（address一致）を固定化する。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    futaarayama = next(shrine for shrine in seed.shrines if shrine.name_jp == "宇都宮二荒山神社")
    assert futaarayama.address == "栃木県宇都宮市馬場通り1-1-1"
    deity_names = [d.display_name for d in futaarayama.deities]
    assert deity_names == ["豊城入彦命", "大物主命", "事代主命"]


def test_batch16_seed_hakusan_identity_and_source():
    """白山神社（文京区）が正しいidentityで登録され、東京十社会の
    公式Sourceを使用していることを固定化する。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    hakusan = next(shrine for shrine in seed.shrines if shrine.name_jp == "白山神社")
    assert hakusan.address == "東京都文京区白山5-31-26"
    deity_names = [d.display_name for d in hakusan.deities]
    assert deity_names == ["菊理姫命", "伊弉諾命", "伊弉冊命"]
    for deity in hakusan.deities:
        assert deity.source_keys == ["batch16-hakusan-10jinja"]


def test_batch16_seed_no_within_shrine_duplicates():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    for shrine in seed.shrines:
        names = [d.display_name for d in shrine.deities]
        assert len(names) == len(set(names)), shrine.name_jp

        history_keys = [(h.history_type, h.title) for h in shrine.histories]
        assert len(history_keys) == len(set(history_keys)), shrine.name_jp


def test_batch16_seed_all_facts_are_source_confirmed_high_confidence():
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


def test_batch16_seed_role_assignment_matches_official_hierarchy():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))
    by_name = {shrine.name_jp: shrine for shrine in seed.shrines}

    futaarayama_roles = {d.display_name: d.role for d in by_name["宇都宮二荒山神社"].deities}
    assert futaarayama_roles["豊城入彦命"] == "primary"
    assert futaarayama_roles["大物主命"] == "secondary"
    assert futaarayama_roles["事代主命"] == "secondary"

    sengen_roles = {d.display_name: d.role for d in by_name["多摩川浅間神社"].deities}
    assert sengen_roles["木花咲耶姫命"] == "primary"

    # 序列の記載がない神社は role=unknown で対等に列挙する
    hiratsuka_roles = {d.role for d in by_name["平塚八幡宮"].deities}
    assert hiratsuka_roles == {"unknown"}
    sakuragi_roles = {d.role for d in by_name["櫻木神社"].deities}
    assert sakuragi_roles == {"unknown"}
    hakusan_roles = {d.role for d in by_name["白山神社"].deities}
    assert hakusan_roles == {"unknown"}


def test_batch16_seed_source_semantic_identity_no_conflict_with_prior_batches():
    """Batch16の5 SourceはBatch14/15のSourceと異なるURLであるべき
    (source_type + normalized URLの衝突がないことをseed同士で確認)。"""
    seed_dir = SEED_PATH.parent
    batch14 = json.loads((seed_dir / "batch_14_seed.json").read_text(encoding="utf-8"))
    batch15 = json.loads((seed_dir / "batch_15_seed.json").read_text(encoding="utf-8"))
    batch16 = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    prior_urls = {s["url"] for s in batch14["sources"]} | {s["url"] for s in batch15["sources"]}
    batch16_urls = {s["url"] for s in batch16["sources"]}
    assert prior_urls.isdisjoint(batch16_urls)


@pytest.mark.django_db
def test_batch16_seed_import_is_idempotent_and_preserves_unrelated_knowledge():
    for name_jp, address in TARGETS:
        Shrine.objects.create(name_jp=name_jp, kind="shrine", address=address)

    unrelated = Shrine.objects.create(
        name_jp="既存Knowledge神社（Batch16無関係）", kind="shrine", address="東京都既存区8-8-8"
    )
    existing_source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="既存公式Source（Batch16無関係）",
        url="https://existing-batch16.example.jp/",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity = ShrineDeity.objects.create(
        shrine=unrelated,
        display_name="既存祭神（Batch16無関係）",
        role="primary",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity.sources.set([existing_source])
    existing_history = ShrineHistory.objects.create(
        shrine=unrelated,
        history_type="historical_event",
        title="既存沿革（Batch16無関係）",
        content="既存の沿革本文。",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_history.sources.set([existing_source])

    call_command("import_shrine_knowledge", str(SEED_PATH), stdout=io.StringIO())

    targets = Shrine.objects.filter(name_jp__in=[name for name, _ in TARGETS])
    assert ShrineKnowledgeSource.objects.count() == 6  # 5 batch16 + 1 unrelated
    assert ShrineDeity.objects.filter(shrine__in=targets).count() == 14
    assert ShrineHistory.objects.filter(shrine__in=targets).count() == 15
    assert all(deity.sources.exists() for deity in ShrineDeity.objects.filter(shrine__in=targets))
    assert all(
        history.sources.exists() for history in ShrineHistory.objects.filter(shrine__in=targets)
    )

    dry_run = io.StringIO()
    call_command("import_shrine_knowledge", str(SEED_PATH), "--dry-run", stdout=dry_run)
    output = dry_run.getvalue()
    assert "'source_REUSE_EXISTING': 5" in output
    assert "'deity_SKIP_EXISTS': 14" in output
    assert "'history_SKIP_EXISTS': 15" in output
    assert "CREATE" not in output

    existing_deity.refresh_from_db()
    existing_history.refresh_from_db()
    assert existing_deity.display_name == "既存祭神（Batch16無関係）"
    assert existing_history.content == "既存の沿革本文。"
    assert list(existing_deity.sources.all()) == [existing_source]
    assert list(existing_history.sources.all()) == [existing_source]


@pytest.mark.django_db
def test_batch16_seed_validate_only_fails_when_target_shrine_missing():
    # Only create 4 of the 5 targets — 白山神社 is intentionally missing.
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
