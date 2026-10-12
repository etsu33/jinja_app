"""G-7 Phase 1 SQL generator（scripts/migration_safety/g7_sql_generator.py）の DB 付き regression。

Production には接続しない。pytest の isolated test DB だけを使う。

- spec の enum / normalized_url / Knowledge が model・importer・Knowledge Seed の正本と一致する
- 2つの strategy それぞれで、生成 SQL を実際の importer で作った local state に対して実行し、
  G7 の各 phase で期待どおり PASS / fail-closed / 期待値どおりの報告になる
"""

import copy
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
sys.path.insert(0, str(REPO_ROOT / "scripts" / "migration_safety"))

import g7_sql_generator as g7  # noqa: E402

SPEC_DIR = REPO_ROOT / "scripts" / "migration_safety" / "g7_specs"
SEED_DIR = REPO_ROOT / "backend" / "temples" / "data" / "knowledge_seeds"
BASE_SEED_PATH = REPO_ROOT / "backend" / "temples" / "data" / "shrines_seed_clean.json"
CASES = {"nsrc-000002": "nsrc_000002", "nsrc-000004": "nsrc_000004"}


def _spec(candidate_id: str) -> dict:
    return g7.load_spec(SPEC_DIR / f"{CASES[candidate_id]}.json")


def _seed(candidate_id: str) -> dict:
    return json.loads((SEED_DIR / f"{CASES[candidate_id]}_seed.json").read_text(encoding="utf-8"))


def test_generator_enums_equal_model_choices():
    assert g7.SOURCE_TYPES == {value for value, _ in ShrineKnowledgeSource.SOURCE_TYPE_CHOICES}
    assert g7.VERIFICATION_STATUSES == {value for value, _ in KNOWLEDGE_VERIFICATION_STATUS_CHOICES}
    assert g7.CONFIDENCES == {value for value, _ in KNOWLEDGE_CONFIDENCE_CHOICES}
    assert g7.HISTORY_TYPES == {value for value, _ in ShrineHistory.HISTORY_TYPE_CHOICES}


@pytest.mark.parametrize("candidate_id", sorted(CASES))
def test_spec_candidate_and_knowledge_equal_the_seeds(candidate_id):
    spec, seed = _spec(candidate_id), _seed(candidate_id)
    candidate = spec["candidate"]
    base_rows = [
        row
        for row in json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))
        if row["name_jp"] == candidate["name_jp"] and row["address"] == candidate["address"]
    ]
    assert len(base_rows) == 1
    assert (base_rows[0]["latitude"], base_rows[0]["longitude"]) == (
        candidate["latitude"],
        candidate["longitude"],
    )
    assert base_rows[0]["goriyaku"] == spec["base"]["expected_goriyaku_text"]

    assert len(seed["shrines"]) == 1
    shrine = seed["shrines"][0]
    assert shrine["shrine_ref"] == {
        "name_jp": candidate["name_jp"],
        "address": candidate["address"],
    }
    knowledge = spec["knowledge"]
    assert len(seed["sources"]) == knowledge["expected_source_count"]
    assert [d["display_name"] for d in shrine.get("deities", [])] == knowledge["deity_names"]
    assert [h["title"] for h in shrine.get("histories", [])] == knowledge["history_titles"]
    assert [f["stable_key"] for f in shrine.get("source_facts", [])] == knowledge[
        "source_fact_stable_keys"
    ]


def test_normalized_url_identity_matches_the_importer_and_the_seed():
    spec, seed = _spec("nsrc-000002"), _seed("nsrc-000002")
    source = spec["source_identity"]
    seed_source = seed["sources"][0]
    assert normalize_source_url(seed_source["url"]) == source["normalized_url"]
    for key in ("source_type", "publisher", "verification_status", "confidence", "language"):
        assert seed_source[key] == source[key], key
    assert seed_source.get("bibliography", "") == source["bibliography"]
    attributes = spec["normalized_url_identity_sql"]["history_attributes"]
    seed_history = seed["shrines"][0]["histories"][0]
    for key, value in attributes[0].items():
        assert seed_history[key] == value, key


def test_url_pattern_set_matches_each_seed_source_exactly_once():
    spec, seed = _spec("nsrc-000004"), _seed("nsrc-000004")
    patterns = spec["source_identity"]["url_patterns"]
    for source in seed["sources"]:
        assert source["source_type"] == spec["source_identity"]["source_type"]
        assert sum(pattern in source["url"].lower() for pattern in patterns) == 1, source["url"]


# --- generated SQL on the isolated test DB ----------------------------------------------------

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
    """Run every statement in a READ ONLY transaction; return all result rows (or DataError).

    django_db(transaction=True) makes SET TRANSACTION READ ONLY the first statement of a
    real transaction, as with readonly_query.sh.
    """
    results = []
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            try:
                with transaction.atomic():
                    for statement in _statements(sql):
                        cursor.execute(statement)
                        results.append(cursor.fetchall())
            except DataError as error:
                assert "division by zero" in str(error)
                return DataError
    return results


def _rebased(spec: dict) -> dict:
    """Replace only the Production totals with measured test-DB totals (same deltas)."""
    spec = copy.deepcopy(spec)
    with connection.cursor() as cursor:
        cursor.execute(COUNT_SQL)
        measured = dict(zip(g7.TOTAL_KEYS, cursor.fetchone(), strict=True))
    delta = {k: spec["post_state"][k] - spec["production_pre_state"][k] for k in g7.TOTAL_KEYS}
    spec["production_pre_state"] = measured
    spec["post_state"] = {k: measured[k] + delta[k] for k in g7.TOTAL_KEYS}
    return g7.validate_spec(spec)


def _import_base(spec: dict, tmp_path: Path) -> None:
    candidate = spec["candidate"]
    rows = [
        row
        for row in json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))
        if row["name_jp"] == candidate["name_jp"] and row["address"] == candidate["address"]
    ]
    assert len(rows) == 1
    path = tmp_path / "base_row.json"
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    call_command(
        "import_shrines_seed",
        "--source",
        str(path),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )


def _import_knowledge(candidate_id: str) -> None:
    call_command(
        "import_shrine_knowledge",
        str(SEED_DIR / f"{CASES[candidate_id]}_seed.json"),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )


@pytest.mark.django_db(transaction=True)
def test_normalized_url_identity_sql_drives_the_g7_sequence(tmp_path):
    spec = _rebased(_spec("nsrc-000002"))
    sql = dict(g7.generate_sql(spec))

    assert _run(sql["g7_preflight.sql"])[-1] == [("CLEAN_CREATE", 0, 0)]
    assert _run(sql["g7_pre_base_guard.sql"]) == [[(1,)]]
    assert _run(sql["g7_post_base_guard.sql"]) is DataError

    _import_base(spec, tmp_path)
    assert _run(sql["g7_post_base_guard.sql"]) == [[(1,)]]
    assert _run(sql["g7_pre_base_guard.sql"]) is DataError
    assert _run(sql["g7_post_knowledge_verification.sql"]) is DataError

    _import_knowledge("nsrc-000002")
    assert _run(sql["g7_post_knowledge_verification.sql"])[-1] == [(1,)]
    assert _run(sql["g7_post_base_guard.sql"]) is DataError
    assert _run(sql["g7_preflight.sql"])[-1] == [("ALREADY_MATERIALIZED", 1, 1)]

    _import_knowledge("nsrc-000002")
    assert _run(sql["g7_post_knowledge_verification.sql"])[-1] == [(1,)]


@pytest.mark.django_db(transaction=True)
def test_url_pattern_set_sql_drives_the_g7_sequence(tmp_path):
    spec = _rebased(_spec("nsrc-000004"))
    sql = dict(g7.generate_sql(spec))
    knowledge = spec["knowledge"]
    post = spec["post_state"]

    preflight = _run(sql["g7_preflight.sql"])
    # The non-GIS test DB uses temples.migrations_nogis, where the Production migration
    # 0120_shrine_source_fact_foundation exists as 0019_shrine_source_fact_foundation.
    assert spec["url_pattern_set_sql"]["required_temples_migration"] == (
        "0120_shrine_source_fact_foundation"
    )
    assert preflight[2] == [(False,)]
    test_db_spec = copy.deepcopy(spec)
    test_db_spec["url_pattern_set_sql"]["required_temples_migration"] = (
        "0019_shrine_source_fact_foundation"
    )
    assert _run(dict(g7.generate_sql(test_db_spec))["g7_preflight.sql"])[2] == [(True,)]
    assert preflight[5] == [(0, 0)]  # target exact / same name
    assert _run(sql["g7_pre_base_guard.sql"]) == [[(1,)]]
    assert _run(sql["g7_post_base_guard.sql"]) is DataError

    _import_base(spec, tmp_path)
    assert _run(sql["g7_post_base_guard.sql"]) == [[(1,)]]
    assert _run(sql["g7_pre_base_guard.sql"]) is DataError

    _import_knowledge("nsrc-000004")
    assert _run(sql["g7_post_base_guard.sql"]) is DataError
    report = _run(sql["g7_post_knowledge_verification.sql"])
    assert report[0] == [tuple(post[k] for k in g7.TOTAL_KEYS)]
    assert report[1] == [
        (
            1,
            knowledge["expected_deity_count"],
            knowledge["expected_history_count"],
            knowledge["expected_source_fact_count"],
            knowledge["expected_goriyaku_tag_links"],
        )
    ]
    assert report[2] == [(knowledge["expected_source_count"],)]
    assert report[3] == [(0, 0, 0)]  # no sourceless Deity / History / SourceFact
    assert all(count > 0 for count in report[4][0])
    keys = len(knowledge["source_fact_stable_keys"])
    assert report[5] == [(keys, keys)]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("candidate_id", sorted(CASES))
def test_generated_pre_base_guard_fails_closed_on_pre_state_drift(candidate_id):
    spec = _rebased(_spec(candidate_id))
    spec["production_pre_state"]["history_total"] += 1
    spec["post_state"]["history_total"] += 1
    sql = dict(g7.generate_sql(spec))
    assert _run(sql["g7_pre_base_guard.sql"]) is DataError


@pytest.mark.django_db(transaction=True)
def test_normalized_preflight_reports_conflict_for_non_identity_lookalike():
    ShrineKnowledgeSource.objects.create(
        source_type="government",
        title="lookalike",
        url="https://matsuri.geo-itoigawa.com/calendar/m04/?lang=ja",
        verification_status="draft",
    )
    spec = _rebased(_spec("nsrc-000002"))
    sql = dict(g7.generate_sql(spec))
    assert _run(sql["g7_preflight.sql"])[-1][0][0] == "CONFLICT"
    assert _run(sql["g7_pre_base_guard.sql"]) is DataError


@pytest.mark.django_db(transaction=True)
def test_url_pattern_set_pre_base_guard_blocks_existing_pattern_source():
    ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="existing",
        url="https://www.aomi-jinjya.or.jp/history/yuisyo.html",
        verification_status="draft",
    )
    spec = _rebased(_spec("nsrc-000004"))
    sql = dict(g7.generate_sql(spec))
    assert _run(sql["g7_pre_base_guard.sql"]) is DataError
