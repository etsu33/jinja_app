import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services import evidence_gate
from temples.services.knowledge_seed import parse_seed

SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_seeds" / "batch_17_seed.json"

TARGETS = [
    ("北海道神宮", "北海道札幌市中央区宮ヶ丘474"),
    ("建部大社", "滋賀県大津市神領1-16-1"),
    ("波上宮", "沖縄県那覇市若狭1-25-11"),
]


def test_batch17_seed_schema_counts_and_relations():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    assert seed.errors == []
    assert len(seed.sources) == 5
    assert len(seed.shrines) == 3
    assert sum(len(shrine.deities) for shrine in seed.shrines) == 12
    assert sum(len(shrine.histories) for shrine in seed.shrines) == 13
    assert sum(len(deity.source_keys) for shrine in seed.shrines for deity in shrine.deities) == 14
    assert (
        sum(len(history.source_keys) for shrine in seed.shrines for history in shrine.histories)
        == 13
    )

    identities = [(shrine.name_jp, shrine.address) for shrine in seed.shrines]
    assert identities == TARGETS
    assert len(identities) == len(set(identities))
    assert all(deity.source_keys for shrine in seed.shrines for deity in shrine.deities)
    assert all(history.source_keys for shrine in seed.shrines for history in shrine.histories)


def test_batch17_seed_per_shrine_fact_counts():
    """Human Review Closure（PR #2536/#2538/#2540）確定の最終構造
    （北海道神宮7・建部大社6・波上宮12、合計25）を固定化する。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))
    by_name = {shrine.name_jp: shrine for shrine in seed.shrines}

    assert len(by_name["北海道神宮"].deities) == 4
    assert len(by_name["北海道神宮"].histories) == 3
    assert len(by_name["建部大社"].deities) == 2
    assert len(by_name["建部大社"].histories) == 4
    assert len(by_name["波上宮"].deities) == 6
    assert len(by_name["波上宮"].histories) == 6


def test_batch17_seed_hokkaidojingu_h1_is_founding_not_tradition():
    """北海道神宮H1はHuman Review（§3）でtradition→foundingへrevisionされた。
    旧Pilotのtraditionへ戻っていないことを固定化する。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))
    hokkaidojingu = next(shrine for shrine in seed.shrines if shrine.name_jp == "北海道神宮")

    h1 = next(h for h in hokkaidojingu.histories if "北海道鎮座神祭" in h.title)
    assert h1.history_type == "founding"
    assert h1.verification_status == "source_confirmed"
    assert h1.confidence == "high"


def test_batch17_seed_takebe_h2_disputed_multiple_fact():
    """建部大社H2は675年説（H2-A）・676年説（H2-B）のMultiple Factとして
    保持され、1 Factへ統合されていないこと、いずれもdisputed + confidence:
    highであることを固定化する（Human Review Audit §4.3・§6、Data Quality
    Closure §3・§4で確定）。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))
    takebe = next(shrine for shrine in seed.shrines if shrine.name_jp == "建部大社")

    disputed = [h for h in takebe.histories if h.verification_status == "disputed"]
    assert len(disputed) == 2

    h2a = next(h for h in disputed if "675年" in h.title)
    h2b = next(h for h in disputed if "676年" in h.title)

    assert h2a.history_type == "tradition"
    assert h2a.confidence == "high"
    assert h2a.event_date is None
    assert h2a.title == "白鳳4年（675年）に瀬田へ遷し祀られたとする由緒"

    assert h2b.history_type == "tradition"
    assert h2b.confidence == "high"
    assert h2b.event_date is None
    assert h2b.title == "天武天皇4年（676年）に現在地へ移されたと伝わる"


def test_batch17_seed_takebe_source_b_url_resolved():
    """建部大社Source B（見どころ）のURLが、Data Quality Closure
    （docs/audit/shrine-expansion-batch1-data-quality-closure.md §2）で
    RESOLVEDと確認された https://takebetaisha.jp/features/ であることを
    固定化する。"""
    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    source_b = next(s for s in raw["sources"] if s["title"] == "見どころ")
    assert source_b["url"] == "https://takebetaisha.jp/features/"
    assert source_b["publisher"] == "建部大社"


def test_batch17_seed_naminoue_h5b_excludes_keidai_seibi():
    """波上宮H5-Bの content に「境内整備」という表現が含まれていないことを
    固定化する（PR #2540のHuman Review Evidence Final Closureにより除去
    済み。Source本文との直接対応が確認できなかったため）。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))
    naminoue = next(shrine for shrine in seed.shrines if shrine.name_jp == "波上宮")

    h5b = next(h for h in naminoue.histories if "昭和28年以降の社殿再建" in h.title)
    assert "境内整備" not in h5b.content
    assert "境内整備" not in h5b.title
    assert h5b.history_type == "historical_event"
    assert h5b.verification_status == "source_confirmed"
    assert h5b.confidence == "high"


def test_batch17_seed_naminoue_role_assignment():
    """波上宮のrole割当（本殿祭神3柱=unknown、別鎮斎3柱=enshrined）を
    固定化する。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))
    naminoue = next(shrine for shrine in seed.shrines if shrine.name_jp == "波上宮")
    roles = {d.display_name: d.role for d in naminoue.deities}

    assert roles["伊弉冉尊"] == "unknown"
    assert roles["速玉男尊"] == "unknown"
    assert roles["事解男尊"] == "unknown"
    assert roles["火神"] == "enshrined"
    assert roles["産土神"] == "enshrined"
    assert roles["少彦名神"] == "enshrined"


def test_batch17_seed_no_within_shrine_duplicates():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    for shrine in seed.shrines:
        names = [d.display_name for d in shrine.deities]
        assert len(names) == len(set(names)), shrine.name_jp

        history_keys = [(h.history_type, h.title) for h in shrine.histories]
        assert len(history_keys) == len(set(history_keys)), shrine.name_jp


def test_batch17_seed_verified_at_present_for_all_facts():
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    for shrine in seed.shrines:
        for deity in shrine.deities:
            assert deity.confidence == "high", (shrine.name_jp, deity.display_name)
            assert deity.verified_at is not None, (shrine.name_jp, deity.display_name)
        for history in shrine.histories:
            assert history.confidence == "high", (shrine.name_jp, history.title)
            assert history.verified_at is not None, (shrine.name_jp, history.title)


def test_batch17_seed_source_semantic_identity_no_conflict_with_prior_batches():
    """Batch17の5 SourceはBatch14〜16のSourceと異なるURLであるべき
    (source_type + normalized URLの衝突がないことをseed同士で確認)。
    建部大社Source B（見どころ、URLなし旧値から解決済み）はURLを持つため
    本チェックの対象に含まれる。"""
    seed_dir = SEED_PATH.parent
    batch14 = json.loads((seed_dir / "batch_14_seed.json").read_text(encoding="utf-8"))
    batch15 = json.loads((seed_dir / "batch_15_seed.json").read_text(encoding="utf-8"))
    batch16 = json.loads((seed_dir / "batch_16_seed.json").read_text(encoding="utf-8"))
    batch17 = json.loads(SEED_PATH.read_text(encoding="utf-8"))

    prior_urls = (
        {s["url"] for s in batch14["sources"]}
        | {s["url"] for s in batch15["sources"]}
        | {s["url"] for s in batch16["sources"]}
    )
    batch17_urls = {s["url"] for s in batch17["sources"]}
    assert prior_urls.isdisjoint(batch17_urls)


def test_batch17_seed_evidence_gate_matches_data_quality_closure():
    """既存Evidence Gate（コード変更なし）を適用した結果が、Human Review
    Audit・Data Quality Closure・Post Review Validationが記録した期待値
    （25 Fact中23 usable、建部大社H2-A/H2-Bのみusable=False）と一致する
    ことを固定化する。confidence: highがdisputedを上書きしないことも
    合わせて固定化する。"""
    seed = parse_seed(json.loads(SEED_PATH.read_text(encoding="utf-8")))

    results = []
    for shrine in seed.shrines:
        for deity in shrine.deities:
            src_statuses = [seed.sources[k].verification_status for k in deity.source_keys]
            decision = evidence_gate.decide_fact_usability(
                verification_status=deity.verification_status,
                confidence=deity.confidence,
                source_verification_statuses=src_statuses,
            )
            results.append(decision)
        for history in shrine.histories:
            src_statuses = [seed.sources[k].verification_status for k in history.source_keys]
            decision = evidence_gate.decide_fact_usability(
                verification_status=history.verification_status,
                confidence=history.confidence,
                source_verification_statuses=src_statuses,
            )
            results.append(decision)

    assert len(results) == 25
    assert sum(1 for d in results if d.usable) == 23
    assert sum(1 for d in results if not d.usable) == 2

    takebe = next(shrine for shrine in seed.shrines if shrine.name_jp == "建部大社")
    for history in takebe.histories:
        if history.verification_status != "disputed":
            continue
        src_statuses = [seed.sources[k].verification_status for k in history.source_keys]
        decision = evidence_gate.decide_fact_usability(
            verification_status=history.verification_status,
            confidence=history.confidence,
            source_verification_statuses=src_statuses,
        )
        assert decision.usable is False
        assert history.confidence == "high"

        state = evidence_gate.decide_detail_display_state(
            verification_status=history.verification_status,
            source_verification_statuses=src_statuses,
        )
        assert state == "disputed"


@pytest.mark.django_db
def test_batch17_seed_import_is_idempotent_and_preserves_unrelated_knowledge():
    for name_jp, address in TARGETS:
        Shrine.objects.create(name_jp=name_jp, kind="shrine", address=address)

    unrelated = Shrine.objects.create(
        name_jp="既存Knowledge神社（Batch17無関係）", kind="shrine", address="東京都既存区9-9-9"
    )
    existing_source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="既存公式Source（Batch17無関係）",
        url="https://existing-batch17.example.jp/",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity = ShrineDeity.objects.create(
        shrine=unrelated,
        display_name="既存祭神（Batch17無関係）",
        role="primary",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_deity.sources.set([existing_source])
    existing_history = ShrineHistory.objects.create(
        shrine=unrelated,
        history_type="historical_event",
        title="既存沿革（Batch17無関係）",
        content="既存の沿革本文。",
        verification_status="source_confirmed",
        verified_at="2026-01-01T00:00:00Z",
        confidence="high",
    )
    existing_history.sources.set([existing_source])

    call_command("import_shrine_knowledge", str(SEED_PATH), stdout=io.StringIO())

    targets = Shrine.objects.filter(name_jp__in=[name for name, _ in TARGETS])
    assert ShrineKnowledgeSource.objects.count() == 6  # 5 batch17 + 1 unrelated
    assert ShrineDeity.objects.filter(shrine__in=targets).count() == 12
    assert ShrineHistory.objects.filter(shrine__in=targets).count() == 13
    assert all(deity.sources.exists() for deity in ShrineDeity.objects.filter(shrine__in=targets))
    assert all(
        history.sources.exists() for history in ShrineHistory.objects.filter(shrine__in=targets)
    )

    disputed = ShrineHistory.objects.filter(shrine__in=targets, verification_status="disputed")
    assert disputed.count() == 2

    dry_run = io.StringIO()
    call_command("import_shrine_knowledge", str(SEED_PATH), "--dry-run", stdout=dry_run)
    output = dry_run.getvalue()
    assert "'source_REUSE_EXISTING': 5" in output
    assert "'deity_SKIP_EXISTS': 12" in output
    assert "'history_SKIP_EXISTS': 13" in output
    assert "CREATE" not in output

    existing_deity.refresh_from_db()
    existing_history.refresh_from_db()
    assert existing_deity.display_name == "既存祭神（Batch17無関係）"
    assert existing_history.content == "既存の沿革本文。"
    assert list(existing_deity.sources.all()) == [existing_source]
    assert list(existing_history.sources.all()) == [existing_source]


@pytest.mark.django_db
def test_batch17_seed_validate_only_fails_when_target_shrine_missing():
    # Only create 2 of the 3 targets — 波上宮 is intentionally missing.
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
