"""NIIGATA-001-H003 C6 Catalog Production preflight SQL regression（disposable test DB only）。

scripts/migration_safety/sql/niigata_h003_c6_catalog_preflight.sql は SELECT / WITH だけで、
4 target（nsrc-000011 / 000012 / 000013 / 000015）を exact (name_jp, address) で個別に
ABSENT / EXACT_EXISTING / CONFLICT に分類し、cohort を CLEAN_CREATE / ALREADY_MATERIALIZED /
PARTIAL_EXISTING / CONFLICT に分類する。nsrc-000014（G2 HOLD_POSITION_REVIEW）は diagnostics のみ。

ここでは committed SQL を変更せずに disposable DB の各 state で実行し、分類 contract と
importer（import_shrines_seed）の overwrite 挙動が一致することを確認する。
Production には接続しない。Production state はこの test から推論しない。
"""

from __future__ import annotations

import importlib.util
import io
import json
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.db import connection, transaction

from temples.management.commands.import_shrines_seed import COORDINATE_ABS_TOLERANCE
from temples.models import GoriyakuTag, Shrine, ShrineDeity
from temples.tests.support.recommendation_eligibility import attach_usable_history_fact

REPO_ROOT = Path(__file__).resolve().parents[3]
SAFETY_DIR = REPO_ROOT / "scripts" / "migration_safety"
SQL_PATH = SAFETY_DIR / "sql" / "niigata_h003_c6_catalog_preflight.sql"
BASE_SEED_PATH = REPO_ROOT / "backend" / "temples" / "data" / "shrines_seed_clean.json"
IMPORTER_PATH = (
    REPO_ROOT / "backend" / "temples" / "management" / "commands" / "import_shrines_seed.py"
)
BLOCK_RE = re.compile(
    r"-- BEGIN niigata_h003_c6_target_state\n(.*?)-- END niigata_h003_c6_target_state\n",
    re.DOTALL,
)

SHRINE_NAME = "赤城神社"
# candidate_id -> (canonical address, adopted latitude, adopted longitude)
TARGETS = {
    "nsrc-000011": ("新潟県新潟市江南区二本木1丁目7番16号", 37.841794, 139.118507),
    "nsrc-000012": ("新潟県長岡市四郎丸2丁目5番33号", 37.440743, 138.855238),
    "nsrc-000013": ("新潟県長岡市山屋314番地", 37.496407, 139.008620),
    "nsrc-000015": ("新潟県魚沼市湯之谷芋川311番地", 37.214543, 139.036468),
}
HOLD_ID = "nsrc-000014"
HOLD_ADDRESS = "新潟県五泉市上杉川1310番地2"
GUNMA_AKAGI_ADDRESS = "群馬県前橋市富士見町赤城山4-2"
MUTATED = "nsrc-000013"


# --------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------


def _text() -> str:
    return SQL_PATH.read_text(encoding="utf-8")


def _statements(text: str) -> list[str]:
    body = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("--"))
    return [part.strip() for part in body.split(";") if part.strip()]


def _run() -> list[tuple[tuple[str, ...], list[tuple]]]:
    results = []
    with connection.cursor() as cursor:
        for statement in _statements(_text()):
            cursor.execute(statement)
            columns = tuple(col.name for col in cursor.description)
            results.append((columns, cursor.fetchall()))
    return results


def _result(results, first_column: str) -> list[dict]:
    matches = [(cols, rows) for cols, rows in results if cols[0] == first_column]
    assert len(matches) == 1, first_column
    cols, rows = matches[0]
    return [dict(zip(cols, row, strict=True)) for row in rows]


def _cohort(results=None) -> dict:
    results = results or _run()
    assert results[-1][0][0] == "h003_cohort_state_class_candidate"
    (row,) = _result(results, "h003_cohort_state_class_candidate")
    return row


def _target_states(results) -> dict[str, tuple[str, str]]:
    rows = _results_with(results, "target_state_reason")
    return {r["candidate_id"]: (r["target_state"], r["target_state_reason"]) for r in rows}


def _results_with(results, column: str) -> list[dict]:
    out = []
    for cols, rows in results:
        if column in cols:
            out.extend(dict(zip(cols, row, strict=True)) for row in rows)
    return out


def _import_base_seed() -> None:
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )


def _target(candidate_id: str) -> Shrine:
    address = TARGETS[candidate_id][0]
    return Shrine.objects.get(name_jp=SHRINE_NAME, address=address)


def _delete_targets(*candidate_ids: str) -> None:
    for candidate_id in candidate_ids:
        _target(candidate_id).delete()


def _target_seed_rows() -> list[dict]:
    rows = json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))
    identities = {(SHRINE_NAME, address) for address, _, _ in TARGETS.values()}
    return [row for row in rows if (row["name_jp"], row["address"]) in identities]


def _importer_dry_run_on_targets(tmp_path) -> str:
    """Target 4 行だけの subset で importer dry-run を実行し、出力を返す（DB は変わらない）。"""
    subset = tmp_path / "h003_subset.json"
    subset.write_text(json.dumps(_target_seed_rows(), ensure_ascii=False), encoding="utf-8")
    out = io.StringIO()
    call_command(
        "import_shrines_seed",
        "--source",
        str(subset),
        "--skip-goriyaku-tags",
        "--dry-run",
        stdout=out,
        stderr=io.StringIO(),
    )
    return out.getvalue()


def _guard_module():
    spec = importlib.util.spec_from_file_location("migration_safety_guard", SAFETY_DIR / "guard.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------------------
# 1. Static SQL contract
# --------------------------------------------------------------------------------------


def test_sql_passes_the_readonly_guard():
    ok, reason = _guard_module().is_readonly_sql(_text())
    assert ok is True, reason


def test_every_statement_is_select_or_with_and_has_no_connection_identifier():
    text = _text()
    lowered = text.lower()
    for token in ("postgres://", "postgresql://", "password", "sslmode", "@localhost"):
        assert token not in lowered, token
    write_verbs = re.compile(
        r"\b(insert|update|delete|truncate|drop|alter|create|grant|revoke|copy|merge|call|"
        r"vacuum|lock|comment|refresh|reindex|cluster)\b",
        re.IGNORECASE,
    )
    for statement in _statements(text):
        assert re.match(r"^(select|with)\b", statement, re.IGNORECASE), statement
        assert not write_verbs.search(statement), statement


def test_target_state_block_is_byte_identical_in_every_with_statement():
    text = _text()
    blocks = BLOCK_RE.findall(text)
    with_statements = [s for s in _statements(text) if s.lower().startswith("with")]
    assert len(blocks) == len(with_statements) == 8
    assert len(set(blocks)) == 1


def _block_targets() -> dict[str, tuple[str, str, float, float]]:
    block = BLOCK_RE.search(_text()).group(1)
    rows = re.findall(
        r"\('(nsrc-\d{6})', '([^']+)', '([^']+)', ([0-9.]+)::double precision, "
        r"([0-9.]+)::double precision\)",
        block,
    )
    return {cid: (name, address, float(lat), float(lng)) for cid, name, address, lat, lng in rows}


def test_block_targets_are_exactly_the_frozen_cohort():
    assert _block_targets() == {
        cid: (SHRINE_NAME, address, lat, lng) for cid, (address, lat, lng) in TARGETS.items()
    }


def test_block_targets_equal_the_repository_base_seed_rows():
    seed = {
        (r["name_jp"], r["address"]): (r["latitude"], r["longitude"]) for r in _target_seed_rows()
    }
    assert len(seed) == 4
    for _cid, (name, address, lat, lng) in _block_targets().items():
        assert seed[(name, address)] == (lat, lng)


def test_hold_identity_never_appears_in_the_target_block_or_the_cohort():
    text = _text()
    block = BLOCK_RE.search(text).group(1)
    block_sql = "\n".join(ln for ln in block.splitlines() if not ln.lstrip().startswith("--"))
    assert HOLD_ID not in block_sql and HOLD_ADDRESS not in block
    for statement in _statements(text):
        if HOLD_ADDRESS in statement:
            # hold diagnostics statements only: never joined to the target block
            assert "target_state" not in statement
            assert "h003_cohort_state_class_candidate" not in statement


def test_coordinate_tolerance_is_the_importer_tolerance():
    block = BLOCK_RE.search(_text()).group(1)
    tolerances = set(re.findall(r"<= (1e-\d+)", block))
    assert tolerances == {"1e-12"}
    assert float("1e-12") == COORDINATE_ABS_TOLERANCE


def test_payload_neutral_covers_every_importer_payload_field():
    """importer が既存行へ書く payload field が増えたら、この SQL contract も更新が必要。"""
    source = IMPORTER_PATH.read_text(encoding="utf-8")
    payload_src = re.search(r"payload = \{(.*?)\n\s*\}", source, re.DOTALL).group(1)
    payload_fields = set(re.findall(r'"(\w+)":', payload_src))
    assert payload_fields == {
        "address",
        "latitude",
        "longitude",
        "goriyaku",
        "kyusei",
        "astro_elements",
        "name_romaji",
        "sajin",
        "description",
        "element",
    }
    block = BLOCK_RE.search(_text()).group(1)
    payload_sql = re.search(
        r"COALESCE\(\n\s+s\.goriyaku = ''(.*?)false\) AS payload_neutral", block, re.DOTALL
    )
    covered = {"goriyaku", *re.findall(r"s\.(\w+)", payload_sql.group(1))}
    # address = exact identity, latitude / longitude = coordinate_match
    assert payload_fields - {"address", "latitude", "longitude"} == covered


# --------------------------------------------------------------------------------------
# 2. Cohort classification on disposable DB states
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_empty_database_is_clean_create():
    cohort = _cohort()
    assert cohort["h003_cohort_state_class_candidate"] == "CLEAN_CREATE"
    assert cohort["absent_count"] == 4
    assert cohort["create_candidate_ids"] == ",".join(sorted(TARGETS))
    assert cohort["expected_shrine_delta_candidate"] == 4


@pytest.mark.django_db
def test_base_without_targets_is_clean_create_and_gunma_akagi_is_only_a_diagnostic():
    _import_base_seed()
    _delete_targets(*TARGETS)
    results = _run()
    cohort = _cohort(results)
    assert cohort["h003_cohort_state_class_candidate"] == "CLEAN_CREATE"
    assert cohort["expected_shrine_delta_candidate"] == 4
    assert set(_target_states(results).values()) == {("ABSENT", "NONE")}

    identity = _results_with(results, "same_name_other_address_count")
    assert {r["same_name_other_address_count"] for r in identity} == {1}  # 群馬県の別 Shrine
    akagi = _results_with(results, "exact_target_candidate_id")
    assert [(r["address"], r["exact_target_candidate_id"]) for r in akagi] == [
        (GUNMA_AKAGI_ADDRESS, None)
    ]


@pytest.mark.django_db
def test_base_seed_import_is_already_materialized(tmp_path):
    _import_base_seed()
    results = _run()
    cohort = _cohort(results)
    assert cohort["h003_cohort_state_class_candidate"] == "ALREADY_MATERIALIZED"
    assert cohort["exact_existing_count"] == 4
    assert cohort["expected_shrine_delta_candidate"] == 0
    assert set(_target_states(results).values()) == {("EXACT_EXISTING", "NONE")}
    # importer agrees: nothing to create or overwrite
    assert "created=0 updated=0 skipped=4 total_seed=4" in _importer_dry_run_on_targets(tmp_path)


@pytest.mark.django_db
def test_strict_subset_is_partial_existing():
    _import_base_seed()
    _delete_targets("nsrc-000012", "nsrc-000015")
    results = _run()
    cohort = _cohort(results)
    assert cohort["h003_cohort_state_class_candidate"] == "PARTIAL_EXISTING"
    assert cohort["create_candidate_ids"] == "nsrc-000012,nsrc-000015"
    assert cohort["expected_shrine_delta_candidate"] == 2
    assert _target_states(results) == {
        "nsrc-000011": ("EXACT_EXISTING", "NONE"),
        "nsrc-000012": ("ABSENT", "NONE"),
        "nsrc-000013": ("EXACT_EXISTING", "NONE"),
        "nsrc-000015": ("ABSENT", "NONE"),
    }


@pytest.mark.django_db
def test_coordinate_round_trip_within_importer_tolerance_is_not_a_conflict(tmp_path):
    _import_base_seed()
    lat = TARGETS[MUTATED][1]
    Shrine.objects.filter(pk=_target(MUTATED).pk).update(latitude=lat + 1e-13)
    assert _cohort()["h003_cohort_state_class_candidate"] == "ALREADY_MATERIALIZED"
    assert "created=0 updated=0 skipped=4" in _importer_dry_run_on_targets(tmp_path)


# Each mutation on an existing exact target -> CONFLICT with this reason.
# importer_overwrites: whether a subset import of the 4 seed rows would UPDATE the row.
_COLUMN_MUTATIONS = {
    "coordinate-drift": ({"latitude": TARGETS[MUTATED][1] + 1e-9}, "COORDINATE_MISMATCH", True),
    "coordinate-null": ({"latitude": None, "longitude": None}, "COORDINATE_MISMATCH", True),
    "goriyaku-set": ({"goriyaku": "開運"}, "IMPORT_WOULD_OVERWRITE_PAYLOAD", True),
    "goriyaku-null": ({"goriyaku": None}, "IMPORT_WOULD_OVERWRITE_PAYLOAD", True),
    "kyusei-set": ({"kyusei": "一白水星"}, "IMPORT_WOULD_OVERWRITE_PAYLOAD", True),
    "astro-set": ({"astro_elements": ["火"]}, "IMPORT_WOULD_OVERWRITE_PAYLOAD", True),
    "sajin-set": ({"sajin": "豊城入彦命"}, "IMPORT_WOULD_OVERWRITE_PAYLOAD", True),
    "description-set": ({"description": "説明"}, "IMPORT_WOULD_OVERWRITE_PAYLOAD", True),
    "romaji-set": ({"name_romaji": "Akagi Jinja"}, "IMPORT_WOULD_OVERWRITE_PAYLOAD", True),
    "element-set": ({"element": "火"}, "IMPORT_WOULD_OVERWRITE_PAYLOAD", True),
    "visit-style-set": ({"visit_style_tags": ["nature"]}, "UNEXPECTED_CATALOG_STATE", False),
    "history-theme-set": ({"history_theme": "military"}, "UNEXPECTED_CATALOG_STATE", False),
    "kind-changed": ({"kind": "temple"}, "UNEXPECTED_CATALOG_STATE", False),
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(_COLUMN_MUTATIONS))
def test_unexpected_exact_target_state_is_conflict(case, tmp_path):
    _import_base_seed()
    fields, reason, importer_overwrites = _COLUMN_MUTATIONS[case]
    Shrine.objects.filter(pk=_target(MUTATED).pk).update(**fields)

    results = _run()
    cohort = _cohort(results)
    assert cohort["h003_cohort_state_class_candidate"] == "CONFLICT"
    assert cohort["conflict_candidate_ids"] == MUTATED
    assert cohort["expected_shrine_delta_candidate"] is None
    states = _target_states(results)
    assert states.pop(MUTATED) == ("CONFLICT", reason)
    assert set(states.values()) == {("EXACT_EXISTING", "NONE")}

    # SQL reason and importer behaviour agree on "would overwrite"
    output = _importer_dry_run_on_targets(tmp_path)
    assert ("UPDATE id=" in output) is importer_overwrites, output


def _attach_goriyaku_tag(shrine: Shrine) -> None:
    shrine.goriyaku_tags.add(GoriyakuTag.objects.create(name="H003テスト用タグ"))


def _attach_deity(shrine: Shrine) -> None:
    ShrineDeity.objects.create(shrine=shrine, display_name="豊城入彦命")


_RELATION_MUTATIONS = {
    "goriyaku-tag-link": _attach_goriyaku_tag,
    "history-fact": attach_usable_history_fact,
    "deity": _attach_deity,
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(_RELATION_MUTATIONS))
def test_knowledge_or_relation_on_exact_target_is_conflict(case):
    _import_base_seed()
    _RELATION_MUTATIONS[case](_target(MUTATED))
    results = _run()
    assert _cohort(results)["h003_cohort_state_class_candidate"] == "CONFLICT"
    assert _target_states(results)[MUTATED] == ("CONFLICT", "UNEXPECTED_KNOWLEDGE_OR_RELATION")


@pytest.mark.django_db
def test_duplicate_exact_identity_is_conflict():
    _import_base_seed()
    address, lat, lng = TARGETS[MUTATED]
    Shrine.objects.create(
        name_jp=SHRINE_NAME, kind="shrine", address=address, latitude=lat + 0.01, longitude=lng
    )
    results = _run()
    assert _cohort(results)["h003_cohort_state_class_candidate"] == "CONFLICT"
    assert _target_states(results)[MUTATED] == ("CONFLICT", "DUPLICATE_EXACT_IDENTITY")


@pytest.mark.django_db
@pytest.mark.parametrize("target_present", [True, False], ids=["target-present", "target-absent"])
def test_same_address_other_name_is_conflict(target_present):
    _import_base_seed()
    if not target_present:
        _delete_targets(MUTATED)
    Shrine.objects.create(name_jp="山屋神社", kind="shrine", address=TARGETS[MUTATED][0])
    results = _run()
    cohort = _cohort(results)
    assert cohort["h003_cohort_state_class_candidate"] == "CONFLICT"
    assert cohort["expected_shrine_delta_candidate"] is None
    assert _target_states(results)[MUTATED] == ("CONFLICT", "SAME_ADDRESS_OTHER_NAME")


# --------------------------------------------------------------------------------------
# 3. Diagnostics that never change the classification
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_hold_identity_is_diagnostic_only():
    _import_base_seed()
    Shrine.objects.create(name_jp=SHRINE_NAME, kind="shrine", address=HOLD_ADDRESS)
    results = _run()
    (hold,) = _results_with(results, "hold_identity_state")
    assert hold["candidate_id"] == HOLD_ID
    assert hold["in_write_cohort"] is False
    assert hold["hold_exact_count"] == 1
    assert hold["hold_identity_state"] == "PRESENT"

    cohort = _cohort(results)
    assert cohort["h003_cohort_state_class_candidate"] == "ALREADY_MATERIALIZED"
    assert HOLD_ID not in cohort["create_candidate_ids"]
    assert HOLD_ID not in _target_states(results)


@pytest.mark.django_db
def test_hold_identity_absent_by_default():
    _import_base_seed()
    (hold,) = _results_with(_run(), "hold_identity_state")
    assert (hold["hold_exact_count"], hold["hold_identity_state"]) == (0, "ABSENT")


@pytest.mark.django_db
def test_other_same_name_rows_and_nearby_rows_are_diagnostics_only():
    _import_base_seed()
    address, lat, lng = TARGETS["nsrc-000011"]
    Shrine.objects.create(
        name_jp=SHRINE_NAME, kind="shrine", address="新潟県新潟市江南区二本木1-7-16"
    )
    Shrine.objects.create(
        name_jp="二本木赤城神社",
        kind="shrine",
        address="新潟県新潟市江南区二本木1丁目",
        latitude=lat + 0.0005,
        longitude=lng,
    )
    results = _run()
    assert _cohort(results)["h003_cohort_state_class_candidate"] == "ALREADY_MATERIALIZED"

    nearby = _results_with(results, "approx_distance_m")
    assert [(r["candidate_id"], r["name_jp"]) for r in nearby] == [
        ("nsrc-000011", "二本木赤城神社")
    ]
    assert 50 < float(nearby[0]["approx_distance_m"]) < 60

    lookalike = [
        r
        for cols, rows in results
        if cols == ("id", "name_jp", "address", "latitude", "longitude", "place_ref_id")
        for r in (dict(zip(cols, row, strict=True)) for row in rows)
    ]
    addresses = {r["address"] for r in lookalike}
    assert {"新潟県新潟市江南区二本木1-7-16", "新潟県新潟市江南区二本木1丁目"} <= addresses
    assert not addresses & {a for a, _, _ in TARGETS.values()}


@pytest.mark.django_db
def test_preflight_runs_inside_a_read_only_transaction_without_writing():
    _import_base_seed()
    before = Shrine.objects.count()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
        results = _run()
    assert _cohort(results)["h003_cohort_state_class_candidate"] == "ALREADY_MATERIALIZED"
    assert Shrine.objects.count() == before
