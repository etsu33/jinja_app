"""G7 artifact generator（scripts/migration_safety/g7_artifacts.py）の DB 付き regression。

Production には接続しない。pytest の isolated test DB だけを使う。

- 入力 spec の enum / normalized_url / Knowledge / Base Seed が repository の正本と一致する
- 生成した SQL と Runtime QA を、実際の importer（import_shrines_seed / import_shrine_knowledge）で
  作った local state に対して実行し、G7 の各 phase で期待どおり PASS / fail-closed になる
"""

import copy
import importlib.util
import io
import json
import re
import sys
from pathlib import Path

import pytest
from django.core.management import call_command
from django.db import DataError, connection, transaction

from temples.models import (
    KNOWLEDGE_CONFIDENCE_CHOICES,
    KNOWLEDGE_VERIFICATION_STATUS_CHOICES,
    ShrineHistory,
    ShrineKnowledgeSource,
)
from temples.services.knowledge_seed import normalize_source_url

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_SAFETY_DIR = REPO_ROOT / "scripts" / "migration_safety"
sys.path.insert(0, str(MIGRATION_SAFETY_DIR))

import g7_artifacts as g7  # noqa: E402

KNOWLEDGE_SEED_DIR = REPO_ROOT / "backend" / "temples" / "data" / "knowledge_seeds"


def _spec() -> dict:
    return g7.load_spec()


def _base_rows() -> list:
    return json.loads(g7.BASE_SEED_PATH.read_text(encoding="utf-8"))


def test_generator_enums_equal_model_choices():
    assert g7.SOURCE_TYPES == {value for value, _ in ShrineKnowledgeSource.SOURCE_TYPE_CHOICES}
    assert g7.VERIFICATION_STATUSES == {value for value, _ in KNOWLEDGE_VERIFICATION_STATUS_CHOICES}
    assert g7.CONFIDENCES == {value for value, _ in KNOWLEDGE_CONFIDENCE_CHOICES}
    assert g7.HISTORY_TYPES == {value for value, _ in ShrineHistory.HISTORY_TYPE_CHOICES}


@pytest.mark.parametrize("candidate", _spec()["candidates"], ids=lambda c: c["candidate_id"])
def test_spec_normalized_url_equals_importer_identity(candidate):
    source = candidate["knowledge"]["source"]
    assert normalize_source_url(source["url"]) == source["normalized_url"]


@pytest.mark.parametrize("candidate", _spec()["candidates"], ids=lambda c: c["candidate_id"])
def test_spec_base_seed_row_is_the_canonical_base_seed_row(candidate):
    identity = candidate["identity"]
    matches = [
        row
        for row in _base_rows()
        if row.get("name_jp") == identity["official_name"]
        and row.get("address") == identity["official_address"]
    ]
    assert matches == [candidate["base_seed_row"]]


def test_nsrc_000002_spec_knowledge_equals_the_knowledge_seed():
    candidate = g7.candidate_spec(_spec(), "nsrc-000002")
    seed = json.loads((KNOWLEDGE_SEED_DIR / "nsrc_000002_seed.json").read_text(encoding="utf-8"))
    assert len(seed["sources"]) == 1
    seed_source = seed["sources"][0]
    spec_source = candidate["knowledge"]["source"]
    for key in ("source_type", "url", "publisher", "verification_status", "confidence", "language"):
        assert spec_source[key] == seed_source[key], key
    assert spec_source["bibliography"] == seed_source.get("bibliography", "")

    assert len(seed["shrines"]) == 1
    shrine = seed["shrines"][0]
    assert shrine["shrine_ref"] == {
        "name_jp": candidate["identity"]["official_name"],
        "address": candidate["identity"]["official_address"],
    }
    assert candidate["knowledge"]["deities"] == shrine.get("deities", [])
    assert candidate["knowledge"]["source_facts"] == shrine.get("source_facts", [])
    assert len(shrine["histories"]) == len(candidate["knowledge"]["histories"]) == 1
    seed_history = shrine["histories"][0]
    for key, value in candidate["knowledge"]["histories"][0].items():
        assert seed_history[key] == value, key


# --- end-to-end on the isolated test DB ------------------------------------------------------

COUNT_SQL = """
SELECT
  (SELECT COUNT(*) FROM temples_shrine),
  (SELECT COUNT(*) FROM temples_shrineknowledgesource),
  (SELECT COUNT(*) FROM temples_shrinedeity),
  (SELECT COUNT(*) FROM temples_shrinehistory),
  (SELECT COUNT(*) FROM temples_shrinesourcefact)
"""


def _statements(sql: str) -> list[str]:
    code = re.sub(r"--[^\n]*", "", sql)
    assert ";" not in re.sub(r";\s*$", "", code, flags=re.MULTILINE)
    return [part for part in re.split(r";\s*$", sql, flags=re.MULTILINE) if part.strip()]


def _run(sql: str):
    """Run every statement in a READ ONLY transaction; return the last row (or DataError).

    The tests use django_db(transaction=True) so that SET TRANSACTION READ ONLY is the
    first statement of a real transaction, exactly as in readonly_query.sh.
    """
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            try:
                with transaction.atomic():
                    row = None
                    for statement in _statements(sql):
                        cursor.execute(statement)
                        row = cursor.fetchone()
            except DataError as error:
                assert "division by zero" in str(error)
                return DataError
    return row


def _rebased(candidate: dict) -> dict:
    """Replace only the frozen Production totals with the measured test-DB totals."""
    candidate = copy.deepcopy(candidate)
    with connection.cursor() as cursor:
        cursor.execute(COUNT_SQL)
        shrine, source, deity, history, source_fact = cursor.fetchone()
    candidate["frozen_pre_state"].update(
        shrine_total=shrine,
        source_total=source,
        deity_total=deity,
        history_total=history,
        source_fact_total=source_fact,
    )
    return candidate


def _synthetic(tmp_path: Path) -> tuple[dict, list, Path]:
    candidate = copy.deepcopy(g7.candidate_spec(_spec(), "nsrc-000002"))
    name, address = "架空'神社", "架空県架空市1-1"
    candidate["candidate_id"] = "nsrc-999999"
    candidate["identity"] = {
        "official_name": name,
        "official_address": address,
        "identity_label": "kaku",
        "name_variants": [
            {"name_jp": name, "label": "main"},
            {"name_jp": "架空神社", "label": "alt"},
        ],
    }
    row = {
        "name_jp": name,
        "address": address,
        "latitude": 35.5,
        "longitude": 139.25,
        "goriyaku": "",
        "kyusei": None,
        "astro_elements": [],
        "location": {"lat": 35.5, "lng": 139.25},
    }
    candidate["base_seed_row"] = row
    candidate["knowledge"]["source"].update(
        source_type="tourism_official",
        url="https://example.invalid/kakuu/m01/",
        normalized_url="https://example.invalid/kakuu/m01",
        publisher="架空観光協会",
        lookalike_like_patterns=["%example.invalid%", "%kakuu%m01%"],
    )
    history = candidate["knowledge"]["histories"][0]
    history.update(
        history_type="tradition",
        title="架空の例祭",
        content="架空神社では毎年秋に例祭が行われる。",
        period_text="毎年秋",
    )
    candidate["runtime_qa"]["unsupported_deity_names"] = ["架空命"]
    candidate["runtime_qa"]["expect_history_background_sentence"] = False

    source = candidate["knowledge"]["source"]
    seed = {
        "schema_version": "1.0",
        "sources": [
            {
                "key": "SYNTHETIC_SOURCE",
                "source_type": source["source_type"],
                "title": "架空の例祭案内",
                "publisher": source["publisher"],
                "url": source["url"],
                "language": source["language"],
                "accessed_at": "2026-10-10",
                "verified_at": "2026-10-10T18:00:00+09:00",
                "verification_status": source["verification_status"],
                "confidence": source["confidence"],
            }
        ],
        "shrines": [
            {
                "shrine_ref": {"name_jp": name, "address": address},
                "deities": [],
                "histories": [
                    {
                        **{key: history[key] for key in history},
                        "verified_at": "2026-10-10T18:00:00+09:00",
                        "source_keys": ["SYNTHETIC_SOURCE"],
                    }
                ],
            }
        ],
    }
    seed_path = tmp_path / "synthetic_knowledge_seed.json"
    seed_path.write_text(json.dumps(seed, ensure_ascii=False), encoding="utf-8")
    return candidate, [*_base_rows(), row], seed_path


def _import_base(subset_text: str, tmp_path: Path) -> None:
    subset_path = tmp_path / "subset.json"
    subset_path.write_text(subset_text, encoding="utf-8")
    call_command(
        "import_shrines_seed",
        "--source",
        str(subset_path),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )


def _import_knowledge(seed_path: Path) -> None:
    call_command(
        "import_shrine_knowledge", str(seed_path), stdout=io.StringIO(), stderr=io.StringIO()
    )


def _run_runtime_qa(text: str, tmp_path: Path, capsys) -> str:
    path = tmp_path / "generated_runtime_qa.py"
    path.write_text(text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("generated_g7_runtime_qa", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()
    return capsys.readouterr().out


def _case(name: str, tmp_path: Path):
    if name == "synthetic":
        return _synthetic(tmp_path)
    candidate = copy.deepcopy(g7.candidate_spec(_spec(), "nsrc-000002"))
    return candidate, _base_rows(), KNOWLEDGE_SEED_DIR / "nsrc_000002_seed.json"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("case", ["nsrc-000002-rebased", "synthetic"])
def test_generated_artifacts_drive_the_g7_sequence_on_an_isolated_db(case, tmp_path, capsys):
    candidate, base_rows, seed_path = _case(case, tmp_path)
    candidate = _rebased(candidate)
    artifacts = {
        kind: text for kind, (_, text) in g7.generate_artifacts(candidate, base_rows).items()
    }

    # Phase 1: read-only preflight on the clean state
    assert _run(artifacts["preflight"]) == ("CLEAN_CREATE", 0, 0)
    assert _run(artifacts["pre_base_guard"]) == (1,)
    assert _run(artifacts["post_base_guard"]) is DataError

    # Phase 2: target-only Base import
    _import_base(artifacts["base_subset"], tmp_path)
    assert _run(artifacts["post_base_guard"]) == (1,)
    assert _run(artifacts["pre_base_guard"]) is DataError
    assert _run(artifacts["post_knowledge_verification"]) is DataError

    # Phase 3: Knowledge import
    _import_knowledge(seed_path)
    assert _run(artifacts["post_knowledge_verification"]) == (1,)
    assert _run(artifacts["post_base_guard"]) is DataError
    assert _run(artifacts["preflight"]) == ("ALREADY_MATERIALIZED", 1, 1)

    # Idempotency: a second Knowledge import keeps the verified final state
    _import_knowledge(seed_path)
    assert _run(artifacts["post_knowledge_verification"]) == (1,)

    # Runtime QA runs inside a READ ONLY transaction against the materialized state
    out = _run_runtime_qa(artifacts["runtime_qa"], tmp_path, capsys)
    assert "G7_PRODUCTION_RUNTIME_QA=PASS" in out
    assert "TRANSACTION_MODE=READ_ONLY" in out


@pytest.mark.django_db(transaction=True)
def test_generated_guards_fail_closed_on_frozen_state_drift(tmp_path):
    candidate, base_rows, _ = _case("synthetic", tmp_path)
    candidate = _rebased(candidate)
    candidate["frozen_pre_state"]["history_total"] += 1
    artifacts = {
        kind: text for kind, (_, text) in g7.generate_artifacts(candidate, base_rows).items()
    }
    assert _run(artifacts["pre_base_guard"]) is DataError


@pytest.mark.django_db(transaction=True)
def test_generated_preflight_reports_conflict_for_non_identity_lookalike(tmp_path):
    candidate, base_rows, _ = _case("synthetic", tmp_path)
    candidate = _rebased(candidate)
    ShrineKnowledgeSource.objects.create(
        source_type=candidate["knowledge"]["source"]["source_type"],
        title="lookalike",
        url="https://example.invalid/kakuu/m01/?lang=ja",
        verification_status="draft",
    )
    candidate = _rebased(candidate)
    artifacts = {
        kind: text for kind, (_, text) in g7.generate_artifacts(candidate, base_rows).items()
    }
    assert _run(artifacts["preflight"])[0] == "CONFLICT"
    assert _run(artifacts["pre_base_guard"]) is DataError


@pytest.mark.django_db(transaction=True)
def test_generated_runtime_qa_rejects_writes(tmp_path):
    """Runtime QA の READ ONLY transaction では write が DB 側で拒否される。"""
    from django.db import InternalError

    with pytest.raises(InternalError):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute(
                    "INSERT INTO temples_shrineknowledgesource "
                    "(source_type, title, publisher, url, bibliography, verification_status, "
                    "confidence, language, note, created_at, updated_at) "
                    "VALUES ('government', 't', '', '', '', 'draft', '', '', '', now(), now())"
                )
    runtime = g7.generate_artifacts(g7.candidate_spec(_spec(), "nsrc-000002"), _base_rows())[
        "runtime_qa"
    ][1]
    assert 'cursor.execute("SET TRANSACTION READ ONLY")' in runtime
