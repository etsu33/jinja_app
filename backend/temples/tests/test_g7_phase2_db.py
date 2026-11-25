"""G-7 Phase 2（generic subset + Runtime QA generator）の DB 付き regression。

Production には接続しない。pytest の isolated test DB だけを使う。

- spec の runtime_qa evidence が Knowledge Seed / importer の正本と一致する
- generic subset → import_shrines_seed → import_shrine_knowledge で作った state に対し、
  生成した Runtime QA（READ ONLY transaction）が PASS し、DB を変更しない
- 期待を崩した state では生成 Runtime QA が fail closed（AssertionError）になる
"""

import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest
from django.core.management import call_command
from django.db import connection

from temples.models import Shrine, ShrineDeity, ShrineHistory
from temples.services.knowledge_seed import normalize_source_url

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "migration_safety"))

import g7_extract_base_subset as subset_tool  # noqa: E402
import g7_runtime_qa_generator as runtime_tool  # noqa: E402
import g7_sql_generator as g7  # noqa: E402

SPEC_DIR = REPO_ROOT / "scripts" / "migration_safety" / "g7_specs"
SEED_DIR = REPO_ROOT / "backend" / "temples" / "data" / "knowledge_seeds"
CASES = {"nsrc-000002": "nsrc_000002", "nsrc-000004": "nsrc_000004"}
COUNT_TABLES = (
    "temples_shrine",
    "temples_shrineknowledgesource",
    "temples_shrinedeity",
    "temples_shrinehistory",
    "temples_shrinesourcefact",
    "temples_shrinedeity_sources",
    "temples_shrinehistory_sources",
    "temples_shrinesourcefact_sources",
    "temples_shrine_goriyaku_tags",
    "temples_shrinegoriyakuassignment",
)


def _spec(candidate_id: str) -> dict:
    return g7.load_spec(SPEC_DIR / f"{CASES[candidate_id]}.json")


def _seed(candidate_id: str) -> dict:
    return json.loads((SEED_DIR / f"{CASES[candidate_id]}_seed.json").read_text(encoding="utf-8"))


# --- runtime evidence vs canonical seeds --------------------------------------------------------


def test_history_only_runtime_evidence_equals_the_knowledge_seed():
    spec, seed = _spec("nsrc-000002"), _seed("nsrc-000002")
    qa = spec["runtime_qa"]
    assert qa["source_url"] == seed["sources"][0]["url"]
    assert normalize_source_url(qa["source_url"]) == spec["source_identity"]["normalized_url"]
    histories = seed["shrines"][0]["histories"]
    assert [h["content"] for h in histories] == [qa["primary_history_content"]]
    assert seed["shrines"][0].get("deities", []) == []


def test_deity_history_runtime_evidence_equals_the_knowledge_seed():
    spec, seed = _spec("nsrc-000004"), _seed("nsrc-000004")
    qa = spec["runtime_qa"]
    shrine = seed["shrines"][0]
    assert shrine["histories"][0]["content"] == qa["primary_history_content"]
    assert shrine["histories"][0]["title"] == spec["knowledge"]["history_titles"][0]
    deities = {d["display_name"] for d in shrine["deities"]}
    assert deities == set(spec["knowledge"]["deity_names"])
    assert not deities & set(qa["excluded_deity_names"])
    for row in [*shrine["deities"], *shrine["histories"]]:
        assert row["verification_status"] == qa["knowledge_row_verification_status"]
        assert len(row["source_keys"]) == qa["sources_per_knowledge_row"]
    assert {s["verification_status"] for s in seed["sources"]} == {qa["source_verification_status"]}


# --- isolated DB: generic subset + importers + generated Runtime QA -----------------------------


def _counts() -> tuple[int, ...]:
    counts = []
    with connection.cursor() as cursor:
        for table in COUNT_TABLES:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts.append(cursor.fetchone()[0])
    return tuple(counts)


def _materialize(candidate_id: str, tmp_path: Path) -> dict:
    spec = _spec(candidate_id)
    rows = json.loads(subset_tool.BASE_SEED_PATH.read_text(encoding="utf-8"))
    subset_path = tmp_path / "subset.json"
    subset_path.write_text(
        subset_tool.render(subset_tool.extract_subset(spec, rows)), encoding="utf-8"
    )
    call_command(
        "import_shrines_seed",
        "--source",
        str(subset_path),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    call_command(
        "import_shrine_knowledge",
        str(SEED_DIR / f"{CASES[candidate_id]}_seed.json"),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    return spec


def _load_runtime_qa(spec: dict, tmp_path: Path):
    path = tmp_path / f"{CASES[spec['candidate']['candidate_id']]}_generated_runtime_qa.py"
    path.write_text(runtime_tool.generate_runtime_qa(spec), encoding="utf-8")
    module_spec = importlib.util.spec_from_file_location(f"generated_{path.stem}", path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("candidate_id", sorted(CASES))
def test_generated_runtime_qa_passes_read_only_on_the_materialized_state(
    candidate_id, tmp_path, capsys
):
    spec = _materialize(candidate_id, tmp_path)
    shrine = Shrine.objects.get(
        name_jp=spec["candidate"]["name_jp"], address=spec["candidate"]["address"]
    )
    assert (
        ShrineDeity.objects.filter(shrine=shrine).count()
        == spec["knowledge"]["expected_deity_count"]
    )
    assert (
        ShrineHistory.objects.filter(shrine=shrine).count()
        == spec["knowledge"]["expected_history_count"]
    )

    module = _load_runtime_qa(spec, tmp_path)
    before = _counts()
    capsys.readouterr()
    module.main()
    out = capsys.readouterr().out
    assert _counts() == before
    for line in (
        "DETAIL_RUNTIME=PASS",
        "CONCIERGE_CANDIDATE_PATH=PASS",
        "RECOMMENDATION_REASON=PASS",
        "COMPASS_DISTANCE=PASS",
        "COMPASS_DIRECTION=PASS",
        "G7_PRODUCTION_RUNTIME_QA=PASS",
        "TRANSACTION_MODE=READ_ONLY",
    ):
        assert line in out, line


@pytest.mark.django_db(transaction=True)
def test_history_only_runtime_qa_fails_closed_when_the_history_source_is_missing(tmp_path):
    spec = _materialize("nsrc-000002", tmp_path)
    history = ShrineHistory.objects.get(shrine__name_jp=spec["candidate"]["name_jp"])
    history.sources.clear()
    module = _load_runtime_qa(spec, tmp_path)
    with pytest.raises(AssertionError):
        module.main()


@pytest.mark.django_db(transaction=True)
def test_deity_history_runtime_qa_fails_closed_on_an_excluded_deity(tmp_path):
    spec = _materialize("nsrc-000004", tmp_path)
    shrine = Shrine.objects.get(name_jp=spec["candidate"]["name_jp"])
    deity = ShrineDeity.objects.filter(shrine=shrine).first()
    deity.display_name = spec["runtime_qa"]["excluded_deity_names"][0]
    deity.save(update_fields=["display_name"])
    module = _load_runtime_qa(spec, tmp_path)
    with pytest.raises(AssertionError):
        module.main()


@pytest.mark.django_db(transaction=True)
def test_generated_runtime_qa_cannot_write_inside_its_transaction(tmp_path):
    """The READ ONLY transaction rejects writes at the database level."""
    from django.db import InternalError, transaction

    with pytest.raises(InternalError):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
            Shrine.objects.create(name_jp="書き込み検証", address="架空県架空市1-1")
    assert not Shrine.objects.filter(name_jp="書き込み検証").exists()
