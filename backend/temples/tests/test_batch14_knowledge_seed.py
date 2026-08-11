import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.knowledge_seed import parse_seed

SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_seeds" / "batch_14_seed.json"

TARGETS = [
    ("王子神社", "東京都北区王子本町1-1-12"),
    ("足利織姫神社", "栃木県足利市西宮町3889"),
    ("鶴嶺八幡宮", "神奈川県茅ヶ崎市浜之郷462"),
    ("穴守稲荷神社", "東京都大田区羽田5-2-7"),
    ("玉前神社", "千葉県長生郡一宮町一宮3048"),
]

# Names that must never appear as a Deity Fact: collective/associated-shrine
# names, kenmusha (兼務社) deities at other addresses, and unnamed placeholders.
EXCLUDED_DEITY_NAMES = [
    "王子大神",  # collective name for 王子神社's 5 named kami; not a separate Fact
    "蝉丸公",  # 関神社（末社）の祭神
    "その一族の神々",  # 玉前神社: unnamed family gods, never Fact-ized
    "鵜茅葺不合命",  # 玉前神社公式サイト自身が考証中と明記、未確定のためFact化しない
    "天照大神",  # 鶴嶺八幡宮の兼務社（神明神社等、別法人）の祭神
    "市杵島姫命",  # 鶴嶺八幡宮の兼務社（厳島神社）の祭神
    "大山咋命",  # 鶴嶺八幡宮の兼務社（山王社等）の祭神
    "大山祗命",  # 鶴嶺八幡宮の兼務社（三島大神）の祭神
]


def test_batch14_seed_schema_counts_and_relations():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    assert seed.errors == []
    assert len(seed.sources) == 6
    assert len(seed.shrines) == 5
    assert sum(len(shrine.deities) for shrine in seed.shrines) == 13
    assert sum(len(shrine.histories) for shrine in seed.shrines) == 16
    assert sum(len(deity.source_keys) for shrine in seed.shrines for deity in shrine.deities) == 13
    assert (
        sum(len(history.source_keys) for shrine in seed.shrines for history in shrine.histories)
        == 16
    )

    identities = [(shrine.name_jp, shrine.address) for shrine in seed.shrines]
    assert identities == TARGETS
    assert len(identities) == len(set(identities))
    assert all(deity.source_keys for shrine in seed.shrines for deity in shrine.deities)
    assert all(history.source_keys for shrine in seed.shrines for history in shrine.histories)


def test_batch14_seed_oji_jinja_does_not_duplicate_collective_name():
    """王子神社の公式サイトは五柱を総称して「王子大神」と呼ぶが、この
    総称自体を別Factとして作成せず、5柱それぞれのみをFact化している
    ことを固定化する。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    oji = next(shrine for shrine in seed.shrines if shrine.name_jp == "王子神社")
    deity_names = [d.display_name for d in oji.deities]
    assert deity_names == ["伊邪那岐命", "伊邪那美命", "天照大御神", "速玉之男命", "事解之男命"]
    assert "王子大神" not in deity_names
    assert "蝉丸公" not in deity_names


def test_batch14_seed_tsurumine_excludes_kenmusha_and_only_includes_main_shrine_merger():
    """鶴嶺八幡宮の御由緒ページ自身が示す「鶴嶺天満宮 合祀 菅原道真」のみを
    Fact化し、ページ下部に別途列挙される兼務社（神明神社・厳島神社等、
    いずれも別住所の別法人神社）の祭神を混入させていないことを固定化する。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    tsurumine = next(shrine for shrine in seed.shrines if shrine.name_jp == "鶴嶺八幡宮")
    deity_names = [d.display_name for d in tsurumine.deities]
    assert deity_names == ["應神天皇", "仁徳天皇", "佐塚大神", "菅原道真"]
    for excluded in ("天照大神", "市杵島姫命", "大山咋命", "大山祗命"):
        assert excluded not in deity_names

    by_name = {d.display_name: d for d in tsurumine.deities}
    assert by_name["菅原道真"].role == "secondary"


def test_batch14_seed_tamasaki_excludes_unnamed_family_gods_and_unresolved_second_deity():
    """玉前神社は玉依姫命のみをFact化し、「その一族の神々」（個別名不明）を
    collective Factとして作成せず、公式サイト自身が考証中と明記する
    鵜茅葺不合命も確定Fact化していないことを固定化する。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    tamasaki = next(shrine for shrine in seed.shrines if shrine.name_jp == "玉前神社")
    deity_names = [d.display_name for d in tamasaki.deities]
    assert deity_names == ["玉依姫命"]
    assert "その一族の神々" not in deity_names
    assert "鵜茅葺不合命" not in deity_names


def test_batch14_seed_no_excluded_names_anywhere():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))
    all_names = [d.display_name for shrine in seed.shrines for d in shrine.deities]
    for excluded in EXCLUDED_DEITY_NAMES:
        assert excluded not in all_names


def test_batch14_seed_no_within_shrine_duplicates():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    for shrine in seed.shrines:
        names = [d.display_name for d in shrine.deities]
        assert len(names) == len(set(names)), shrine.name_jp

        history_keys = [(h.history_type, h.title) for h in shrine.histories]
        assert len(history_keys) == len(set(history_keys)), shrine.name_jp


def test_batch14_seed_all_facts_are_source_confirmed_with_valid_confidence():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    for shrine in seed.shrines:
        for deity in shrine.deities:
            assert deity.verification_status == "source_confirmed", (shrine.name_jp, deity.display_name)
            assert deity.confidence in ("high", "medium"), (shrine.name_jp, deity.display_name)
            assert deity.verified_at is not None, (shrine.name_jp, deity.display_name)
        for history in shrine.histories:
            assert history.verification_status == "source_confirmed", (shrine.name_jp, history.title)
            assert history.confidence == "high", (shrine.name_jp, history.title)
            assert history.verified_at is not None, (shrine.name_jp, history.title)


def test_batch14_seed_tamasaki_deity_confidence_is_medium_with_documented_reason():
    """玉前神社の玉依姫命は、公式サイト自身が『考証がなされているところ』と
    記す限定的な確からしさを反映してconfidence=mediumとしていることを
    固定化する（他4社のDeityはhigh）。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    by_name = {shrine.name_jp: shrine for shrine in seed.shrines}
    tamayori = by_name["玉前神社"].deities[0]
    assert tamayori.display_name == "玉依姫命"
    assert tamayori.confidence == "medium"
    assert "考証" in tamayori.note

    for shrine_name in ("王子神社", "足利織姫神社", "鶴嶺八幡宮", "穴守稲荷神社"):
        for deity in by_name[shrine_name].deities:
            assert deity.confidence == "high"


def test_batch14_seed_role_assignment_matches_official_hierarchy():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))
    by_name = {shrine.name_jp: shrine for shrine in seed.shrines}

    anamori_roles = {d.display_name: d.role for d in by_name["穴守稲荷神社"].deities}
    assert anamori_roles["豊受姫命"] == "primary"

    tamasaki_roles = {d.display_name: d.role for d in by_name["玉前神社"].deities}
    assert tamasaki_roles["玉依姫命"] == "primary"

    # 序列の記載がない神社は role=unknown で対等に列挙する
    oji_roles = {d.role for d in by_name["王子神社"].deities}
    assert oji_roles == {"unknown"}
    orihime_roles = {d.role for d in by_name["足利織姫神社"].deities}
    assert orihime_roles == {"unknown"}


def test_batch14_seed_source_semantic_identity_no_conflict_with_prior_batches():
    """Batch14の6 SourceはBatch12/13のSourceと異なるURLであるべき
    (source_type + normalized URLの衝突がないことをseed同士で確認)。"""
    seed_dir = SEED_PATH.parent
    batch12 = json.loads((seed_dir / "batch_12_seed.json").read_text(encoding="utf-8"))
    batch13 = json.loads((seed_dir / "batch_13_seed.json").read_text(encoding="utf-8"))
    batch14 = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    prior_urls = {s["url"] for s in batch12["sources"]} | {s["url"] for s in batch13["sources"]}
    batch14_urls = {s["url"] for s in batch14["sources"]}
    assert prior_urls.isdisjoint(batch14_urls)


@pytest.mark.django_db
def test_batch14_seed_import_is_idempotent_and_preserves_unrelated_knowledge():
    for name_jp, address in TARGETS:
        Shrine.objects.create(name_jp=name_jp, kind="shrine", address=address)

    unrelated = Shrine.objects.create(
        name_jp="既存Knowledge神社（Batch14無関係）", kind="shrine", address="東京都既存区6-6-6"
    )
    existing_source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="既存公式Source（Batch14無関係）",
        url="https://existing-batch14.example.jp/",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity = ShrineDeity.objects.create(
        shrine=unrelated,
        display_name="既存祭神（Batch14無関係）",
        role="primary",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity.sources.set([existing_source])
    existing_history = ShrineHistory.objects.create(
        shrine=unrelated,
        history_type="historical_event",
        title="既存沿革（Batch14無関係）",
        content="既存の沿革本文。",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_history.sources.set([existing_source])

    call_command("import_shrine_knowledge", str(SEED_PATH), stdout=io.StringIO())

    targets = Shrine.objects.filter(name_jp__in=[name for name, _ in TARGETS])
    assert ShrineKnowledgeSource.objects.count() == 7  # 6 batch14 + 1 unrelated
    assert ShrineDeity.objects.filter(shrine__in=targets).count() == 13
    assert ShrineHistory.objects.filter(shrine__in=targets).count() == 16
    for excluded in EXCLUDED_DEITY_NAMES:
        assert not ShrineDeity.objects.filter(shrine__in=targets, display_name=excluded).exists()
    assert all(deity.sources.exists() for deity in ShrineDeity.objects.filter(shrine__in=targets))
    assert all(
        history.sources.exists() for history in ShrineHistory.objects.filter(shrine__in=targets)
    )

    dry_run = io.StringIO()
    call_command("import_shrine_knowledge", str(SEED_PATH), "--dry-run", stdout=dry_run)
    output = dry_run.getvalue()
    assert "'source_REUSE_EXISTING': 6" in output
    assert "'deity_SKIP_EXISTS': 13" in output
    assert "'history_SKIP_EXISTS': 16" in output
    assert "CREATE" not in output

    existing_deity.refresh_from_db()
    existing_history.refresh_from_db()
    assert existing_deity.display_name == "既存祭神（Batch14無関係）"
    assert existing_history.content == "既存の沿革本文。"
    assert list(existing_deity.sources.all()) == [existing_source]
    assert list(existing_history.sources.all()) == [existing_source]


@pytest.mark.django_db
def test_batch14_seed_validate_only_fails_when_target_shrine_missing():
    # Only create 4 of the 5 targets — 玉前神社 is intentionally missing.
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
