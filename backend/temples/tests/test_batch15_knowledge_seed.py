import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.knowledge_seed import parse_seed

SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_seeds" / "batch_15_seed.json"

TARGETS = [
    ("湯島天満宮", "東京都文京区湯島3-30-1"),
    ("報徳二宮神社", "神奈川県小田原市城内8-10"),
    ("箭弓稲荷神社", "埼玉県東松山市箭弓町2-5-14"),
    ("水戸東照宮", "茨城県水戸市宮町2-5-13"),
    ("葛西神社", "東京都葛飾区東金町6-10-5"),
]

# Names that must never appear as a Deity Fact: sub-shrine (末社) deities at
# other locations within the precinct, and grounds-shrines not on the main
# 御祭神 page.
EXCLUDED_DEITY_NAMES = [
    "宇迦之御魂神",  # 箭弓稲荷神社の末社「團十郎稲荷」の祭神
]


def test_batch15_seed_schema_counts_and_relations():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    assert seed.errors == []
    assert len(seed.sources) == 7
    assert len(seed.shrines) == 5
    assert sum(len(shrine.deities) for shrine in seed.shrines) == 9
    assert sum(len(shrine.histories) for shrine in seed.shrines) == 18
    assert sum(len(deity.source_keys) for shrine in seed.shrines for deity in shrine.deities) == 9
    assert (
        sum(len(history.source_keys) for shrine in seed.shrines for history in shrine.histories)
        == 18
    )

    identities = [(shrine.name_jp, shrine.address) for shrine in seed.shrines]
    assert identities == TARGETS
    assert len(identities) == len(set(identities))
    assert all(deity.source_keys for shrine in seed.shrines for deity in shrine.deities)
    assert all(history.source_keys for shrine in seed.shrines for history in shrine.histories)


def test_batch15_seed_yakyu_inari_excludes_sub_shrine_deity():
    """箭弓稲荷神社の末社「團十郎稲荷」（御祭神：宇迦之御魂神）は本社とは
    別の社であり、本社Factに混入していないことを固定化する。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    yakyu = next(shrine for shrine in seed.shrines if shrine.name_jp == "箭弓稲荷神社")
    deity_names = [d.display_name for d in yakyu.deities]
    assert deity_names == ["保食神"]
    assert "宇迦之御魂神" not in deity_names


def test_batch15_seed_kasai_excludes_grounds_sub_shrines():
    """葛西神社の境内社（招魂社・弁天・富士）は「ご祭神」ページに含まれず、
    年中行事名としてのみ言及されている。これらをFact化していないことを
    固定化する（三柱＝経津主神・日本武尊・徳川家康命のみ）。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    kasai = next(shrine for shrine in seed.shrines if shrine.name_jp == "葛西神社")
    deity_names = [d.display_name for d in kasai.deities]
    assert deity_names == ["経津主神", "日本武尊", "徳川家康命"]


def test_batch15_seed_ninomiya_history_excludes_biography_content():
    """報徳二宮神社のHistory Factは神社自体の由緒（創建・社殿整備等）のみを
    根拠とし、二宮尊徳翁個人の伝記的内容（財政再建の功績・五常講等）を
    Shrine Historyとして混同していないことを固定化する。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    ninomiya = next(shrine for shrine in seed.shrines if shrine.name_jp == "報徳二宮神社")
    for history in ninomiya.histories:
        assert history.source_keys == ["batch15-ninomiya-yuisho"]
        assert "五常講" not in history.content
        assert "内村鑑三" not in history.content


def test_batch15_seed_no_within_shrine_duplicates():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    for shrine in seed.shrines:
        names = [d.display_name for d in shrine.deities]
        assert len(names) == len(set(names)), shrine.name_jp

        history_keys = [(h.history_type, h.title) for h in shrine.histories]
        assert len(history_keys) == len(set(history_keys)), shrine.name_jp


def test_batch15_seed_all_facts_are_source_confirmed_high_confidence():
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


def test_batch15_seed_role_assignment_matches_official_hierarchy():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))
    by_name = {shrine.name_jp: shrine for shrine in seed.shrines}

    ninomiya_roles = {d.display_name: d.role for d in by_name["報徳二宮神社"].deities}
    assert ninomiya_roles["二宮尊徳翁"] == "primary"

    yakyu_roles = {d.display_name: d.role for d in by_name["箭弓稲荷神社"].deities}
    assert yakyu_roles["保食神"] == "primary"

    mito_roles = {d.display_name: d.role for d in by_name["水戸東照宮"].deities}
    assert mito_roles["徳川家康公"] == "primary"
    assert mito_roles["徳川頼房公"] == "secondary"

    # 序列の記載がない神社は role=unknown で対等に列挙する
    yushima_roles = {d.role for d in by_name["湯島天満宮"].deities}
    assert yushima_roles == {"unknown"}
    kasai_roles = {d.role for d in by_name["葛西神社"].deities}
    assert kasai_roles == {"unknown"}


def test_batch15_seed_source_semantic_identity_no_conflict_with_prior_batches():
    """Batch15の7 SourceはBatch13/14のSourceと異なるURLであるべき
    (source_type + normalized URLの衝突がないことをseed同士で確認)。"""
    seed_dir = SEED_PATH.parent
    batch13 = json.loads((seed_dir / "batch_13_seed.json").read_text(encoding="utf-8"))
    batch14 = json.loads((seed_dir / "batch_14_seed.json").read_text(encoding="utf-8"))
    batch15 = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    prior_urls = {s["url"] for s in batch13["sources"]} | {s["url"] for s in batch14["sources"]}
    batch15_urls = {s["url"] for s in batch15["sources"]}
    assert prior_urls.isdisjoint(batch15_urls)


@pytest.mark.django_db
def test_batch15_seed_import_is_idempotent_and_preserves_unrelated_knowledge():
    for name_jp, address in TARGETS:
        Shrine.objects.create(name_jp=name_jp, kind="shrine", address=address)

    unrelated = Shrine.objects.create(
        name_jp="既存Knowledge神社（Batch15無関係）", kind="shrine", address="東京都既存区7-7-7"
    )
    existing_source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="既存公式Source（Batch15無関係）",
        url="https://existing-batch15.example.jp/",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity = ShrineDeity.objects.create(
        shrine=unrelated,
        display_name="既存祭神（Batch15無関係）",
        role="primary",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity.sources.set([existing_source])
    existing_history = ShrineHistory.objects.create(
        shrine=unrelated,
        history_type="historical_event",
        title="既存沿革（Batch15無関係）",
        content="既存の沿革本文。",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_history.sources.set([existing_source])

    call_command("import_shrine_knowledge", str(SEED_PATH), stdout=io.StringIO())

    targets = Shrine.objects.filter(name_jp__in=[name for name, _ in TARGETS])
    assert ShrineKnowledgeSource.objects.count() == 8  # 7 batch15 + 1 unrelated
    assert ShrineDeity.objects.filter(shrine__in=targets).count() == 9
    assert ShrineHistory.objects.filter(shrine__in=targets).count() == 18
    for excluded in EXCLUDED_DEITY_NAMES:
        assert not ShrineDeity.objects.filter(shrine__in=targets, display_name=excluded).exists()
    assert all(deity.sources.exists() for deity in ShrineDeity.objects.filter(shrine__in=targets))
    assert all(
        history.sources.exists() for history in ShrineHistory.objects.filter(shrine__in=targets)
    )

    dry_run = io.StringIO()
    call_command("import_shrine_knowledge", str(SEED_PATH), "--dry-run", stdout=dry_run)
    output = dry_run.getvalue()
    assert "'source_REUSE_EXISTING': 7" in output
    assert "'deity_SKIP_EXISTS': 9" in output
    assert "'history_SKIP_EXISTS': 18" in output
    assert "CREATE" not in output

    existing_deity.refresh_from_db()
    existing_history.refresh_from_db()
    assert existing_deity.display_name == "既存祭神（Batch15無関係）"
    assert existing_history.content == "既存の沿革本文。"
    assert list(existing_deity.sources.all()) == [existing_source]
    assert list(existing_history.sources.all()) == [existing_source]


@pytest.mark.django_db
def test_batch15_seed_validate_only_fails_when_target_shrine_missing():
    # Only create 4 of the 5 targets — 葛西神社 is intentionally missing.
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
