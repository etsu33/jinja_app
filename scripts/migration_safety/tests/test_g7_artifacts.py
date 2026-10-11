"""Pure unit tests for scripts/migration_safety/g7_artifacts.py.

No database, no network, no Django. Run with:
    python3 -m pytest scripts/migration_safety/tests/test_g7_artifacts.py -v
"""

import ast
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import g7_artifacts as g7  # noqa: E402
from g7_artifacts import (  # noqa: E402
    SpecError,
    SubsetError,
    candidate_spec,
    extract_target_subset,
    generate_artifacts,
    load_spec,
    render_subset,
    validate_spec,
)

REPO_ROOT = SCRIPT_DIR.parents[1]
SQL_DIR = SCRIPT_DIR / "sql"
GOLDEN = {
    "preflight": SQL_DIR / "nsrc_000002_g7_preflight.sql",
    "pre_base_guard": SQL_DIR / "nsrc_000002_g7_pre_base_guard.sql",
    "post_base_guard": SQL_DIR / "nsrc_000002_g7_post_base_guard.sql",
    "post_knowledge_verification": SQL_DIR / "nsrc_000002_g7_post_knowledge_verification.sql",
    "runtime_qa": SCRIPT_DIR / "nsrc_000002_g7_runtime_qa.py",
}
# docs/audit/niigata-h001-nsrc-000002-g7-production-import-preflight.md §14.2（Production 適用時の値）
GOLDEN_SUBSET_SHA256 = "d5bcc3229b883314d54826f4381877102c4adcda7cb1e1b662ee876260bb7e40"
BLOCK_RE = re.compile(
    r"-- BEGIN nsrc_000002_source_identity\n(.*?)-- END nsrc_000002_source_identity\n",
    re.DOTALL,
)


def _base_rows() -> list:
    return json.loads(g7.BASE_SEED_PATH.read_text(encoding="utf-8"))


def _spec() -> dict:
    return json.loads(g7.SPEC_PATH.read_text(encoding="utf-8"))


def _n2() -> dict:
    return copy.deepcopy(candidate_spec(load_spec(), "nsrc-000002"))


def _generate(candidate=None, rows=None) -> dict:
    return generate_artifacts(candidate or _n2(), _base_rows() if rows is None else rows)


def _synthetic_candidate() -> tuple[dict, list]:
    """A fictional candidate (not a real shrine) used to exercise non-golden rendering."""
    candidate = _n2()
    candidate["candidate_id"] = "nsrc-999999"
    candidate["identity"] = {
        "official_name": "架空'神社",
        "official_address": "架空県架空市1-1",
        "identity_label": "kaku",
        "name_variants": [{"name_jp": "架空'神社", "label": "main"}],
    }
    row = {
        "name_jp": "架空'神社",
        "address": "架空県架空市1-1",
        "latitude": 35.5,
        "longitude": 139.25,
        "goriyaku": "",
        "kyusei": None,
        "astro_elements": [],
        "location": {"lat": 35.5, "lng": 139.25},
    }
    candidate["base_seed_row"] = row
    candidate["knowledge"]["histories"][0]["content"] = "架空の由緒が一文だけある。"
    candidate["runtime_qa"]["unsupported_deity_names"] = []
    candidate["runtime_qa"]["expect_history_background_sentence"] = False
    return candidate, [*_base_rows(), row]


# --- spec / input contract ------------------------------------------------------------------


def test_committed_spec_is_valid_and_unique():
    spec = load_spec()
    ids = [candidate["candidate_id"] for candidate in spec["candidates"]]
    assert ids == ["nsrc-000002"]
    assert len(ids) == len(set(ids))


def test_spec_is_not_the_g5_test_only_manifest():
    assert g7.SPEC_PATH.parent == SCRIPT_DIR
    assert "shrine_expansion_handoffs" not in g7.SPEC_PATH.read_text(encoding="utf-8")
    assert "shrine_expansion_handoffs" not in Path(g7.__file__).read_text(encoding="utf-8")


def _mutated_spec(mutate) -> dict:
    spec = _spec()
    mutate(spec["candidates"][0], spec)
    return spec


def _drop(*path):
    def mutate(candidate, spec):
        target = candidate
        for key in path[:-1]:
            target = target[key]
        del target[path[-1]]

    return mutate


def _set(*path, value):
    def mutate(candidate, spec):
        target = candidate
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    return mutate


@pytest.mark.parametrize("field", sorted(g7._CANDIDATE_FIELDS))
def test_missing_candidate_field_fails(field):
    with pytest.raises(SpecError, match="missing field"):
        validate_spec(_mutated_spec(_drop(field)))


@pytest.mark.parametrize(
    "path",
    [
        ("identity", "official_address"),
        ("frozen_pre_state", "accepted_source_count"),
        ("expected_delta", "history"),
        ("knowledge", "source", "normalized_url"),
        ("knowledge", "histories", 0, "title"),
        ("runtime_qa", "compass_origin"),
        ("base_seed_row", "location"),
    ],
)
def test_missing_nested_field_fails(path):
    with pytest.raises(SpecError, match="missing field"):
        validate_spec(_mutated_spec(_drop(*path)))


@pytest.mark.parametrize(
    "path",
    [
        ("inferred_reading",),
        ("identity", "reading"),
        ("frozen_pre_state", "hostname"),
        ("knowledge", "source", "credential"),
        ("knowledge", "histories", 0, "sort_order"),
        ("runtime_qa", "extra"),
    ],
)
def test_unknown_field_fails(path):
    with pytest.raises(SpecError, match="unknown field"):
        validate_spec(_mutated_spec(_set(*path, value="x")))


def test_unknown_top_level_field_fails():
    spec = _spec()
    spec["defaults"] = {}
    with pytest.raises(SpecError, match="unknown field"):
        validate_spec(spec)


@pytest.mark.parametrize(
    "candidate_id", ["nsrc-2", "wave0-010", "NSRC-000002", "nsrc-0000002", " nsrc-000002", 2]
)
def test_invalid_candidate_id_fails(candidate_id):
    with pytest.raises(SpecError, match="candidate_id"):
        validate_spec(_mutated_spec(_set("candidate_id", value=candidate_id)))


def test_duplicate_candidate_spec_fails():
    spec = _spec()
    spec["candidates"].append(copy.deepcopy(spec["candidates"][0]))
    with pytest.raises(SpecError, match="duplicate candidate_id"):
        validate_spec(spec)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("shrine", 0),
        ("shrine", 2),
        ("source", 0),
        ("source", 2),
        ("deity", 1),
        ("history", 0),
        ("history", 2),
        ("source_fact", 1),
        ("history", -1),
        ("history", True),
        ("history", "1"),
    ],
)
def test_invalid_expected_delta_fails(key, value):
    with pytest.raises(SpecError, match="expected_delta"):
        validate_spec(_mutated_spec(_set("expected_delta", key, value=value)))


def test_expected_source_delta_follows_accepted_source_count():
    spec = _mutated_spec(_set("frozen_pre_state", "accepted_source_count", value=1))
    spec["candidates"][0]["frozen_pre_state"]["source_identity_state"] = "REUSABLE"
    with pytest.raises(SpecError, match="expected_delta"):
        validate_spec(spec)
    spec["candidates"][0]["expected_delta"]["source"] = 0
    validate_spec(spec)


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("schema_version_placeholder",), None, None),
        (("knowledge_profile",), "DEITY_AND_HISTORY", "knowledge_profile"),
        (("knowledge", "deities"), [{"display_name": "x"}], "deities"),
        (("knowledge", "source_facts"), [{"stable_key": "x"}], "source_facts"),
        (("knowledge", "histories"), [], "histories"),
        (("knowledge", "histories", 0, "event_date"), "2026-04-19", "event_date"),
        (("knowledge", "histories", 0, "history_type"), "legend", "history_type"),
        (("knowledge", "histories", 0, "confidence"), "very_high", "confidence"),
        (("knowledge", "source", "source_type"), "web", "source_type"),
        (("knowledge", "source", "verification_status"), "verified", "verification_status"),
        (("knowledge", "source", "lookalike_like_patterns"), [], "lookalike_like_patterns"),
        (("knowledge", "source", "lookalike_like_patterns"), ["%Calendar%"], "lowercase"),
        (("knowledge", "source", "lookalike_like_patterns"), ["%a'b%"], "lowercase"),
        (("knowledge", "source", "lookalike_like_patterns"), ["calendar"], "lowercase"),
        (("frozen_pre_state", "accepted_source_count"), 2, "accepted_source_count"),
        (("frozen_pre_state", "shrine_total"), -1, "shrine_total"),
        (("frozen_pre_state", "shrine_total"), 121.0, "shrine_total"),
        (("frozen_pre_state", "source_identity_state"), "REUSABLE", "source_identity_state"),
        (("frozen_pre_state", "production_state_class"), "ALREADY_MATERIALIZED", "state_class"),
        (("frozen_pre_state", "preflight_result"), "HOLD", "preflight_result"),
        (("frozen_pre_state", "server_version"), "17", "server_version"),
        (("frozen_pre_state", "latest_temples_migration"), "latest", "latest_temples_migration"),
        (("identity", "official_name"), "青沢神社", "official_name"),
        (("identity", "official_name"), " 青澤神社", "whitespace"),
        (("identity", "official_address"), "新潟県糸魚川市\n大字青海2696番地", "control"),
        (("identity", "identity_label"), "Aosawa", "identity_label"),
        (("identity", "name_variants"), [], "name_variants"),
        (("identity", "name_variants", 0, "name_jp"), "青沢神社", "official_name"),
        (("identity", "name_variants", 1, "label"), "kyuji", "duplicate label"),
        (("identity", "name_variants", 1, "name_jp"), "青澤神社", "duplicate name_jp"),
        (("base_seed_row", "latitude"), 91.0, "latitude"),
        (("base_seed_row", "location"), {"lat": 0.0, "lng": 0.0}, "location"),
        (("base_seed_row", "goriyaku"), "家内安全", "goriyaku"),
        (("runtime_qa", "expect_history_background_sentence"), "yes", "bool"),
        (("runtime_qa", "unsupported_deity_names"), "沼河比賣命", "list"),
        (("source_identity_regression_test",), "/etc/passwd", "repo-relative"),
        (("source_identity_regression_test",), "../outside.py", "repo-relative"),
        (("source_identity_regression_test",), "backend/temples/tests/missing.py", "exist"),
    ],
)
def test_invalid_spec_values_fail(path, value, message):
    if path == ("schema_version_placeholder",):
        spec = _spec()
        spec["schema_version"] = 2
        with pytest.raises(SpecError, match="schema_version"):
            validate_spec(spec)
        return
    with pytest.raises(SpecError, match=message):
        validate_spec(_mutated_spec(_set(*path, value=value)))


def test_unknown_candidate_lookup_fails():
    with pytest.raises(SpecError, match="exactly 1 spec"):
        candidate_spec(load_spec(), "nsrc-000004")


# --- golden compatibility (nsrc-000002) -------------------------------------------------------


@pytest.mark.parametrize("kind", sorted(GOLDEN))
def test_nsrc_000002_golden_output_is_byte_identical(kind):
    artifacts = _generate()
    name, text = artifacts[kind]
    assert name == GOLDEN[kind].name
    assert text == GOLDEN[kind].read_text(encoding="utf-8")


def test_nsrc_000002_subset_is_identical_to_the_applied_subset():
    name, text = _generate()["base_subset"]
    assert name == "nsrc_000002_g7_base_subset.json"
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == GOLDEN_SUBSET_SHA256
    import nsrc_000002_g7_extract_base_subset as extractor

    assert extractor.render(extractor.extract_subset()) == text


def test_generated_source_identity_block_is_identical_to_the_committed_block():
    committed = {
        BLOCK_RE.findall(path.read_text(encoding="utf-8"))[0]
        for path in GOLDEN.values()
        if path.suffix == ".sql"
    }
    assert len(committed) == 1
    artifacts = _generate()
    generated = set()
    for kind in g7.SQL_KINDS:
        found = BLOCK_RE.findall(artifacts[kind][1])
        assert found, kind
        generated.update(found)
    assert generated == committed
    assert len(BLOCK_RE.findall(artifacts["preflight"][1])) == 3


# --- read-only / leakage ----------------------------------------------------------------------

_WRITE_TOKENS = re.compile(
    r"\b(insert|update|delete|merge|upsert|alter|create|drop|truncate|grant|revoke|copy|call|do"
    r"|lock|execute|prepare|vacuum|analyze|refresh|reindex|cluster|comment|set|reset|into|begin"
    r"|commit|rollback|savepoint|listen|notify|load|import|security)\b",
    re.IGNORECASE,
)
_SIDE_EFFECT_FUNCTIONS = re.compile(
    r"\b(nextval|setval|set_config|pg_advisory\w*|pg_terminate_backend|pg_cancel_backend"
    r"|pg_reload_conf|pg_sleep|lo_\w+|dblink\w*|pg_read_file|pg_ls_dir|pg_stat_reset\w*)\s*\(",
    re.IGNORECASE,
)


def _code_only(sql: str) -> str:
    no_comments = re.sub(r"--[^\n]*", "", sql)
    return re.sub(r"'(?:[^']|'')*'", "''", no_comments)


def _all_sql_texts() -> list[tuple[str, str]]:
    synthetic, rows = _synthetic_candidate()
    texts = []
    for label, candidate, base in (
        ("nsrc-000002", _n2(), _base_rows()),
        ("synthetic", synthetic, rows),
    ):
        artifacts = generate_artifacts(candidate, base)
        texts += [
            pytest.param(f"{label}:{kind}", artifacts[kind][1], id=f"{label}-{kind}")
            for kind in g7.SQL_KINDS
        ]
    return texts


@pytest.mark.parametrize(("label", "sql"), _all_sql_texts())
def test_generated_sql_is_strictly_read_only(label, sql, tmp_path):
    code = _code_only(sql)
    assert not _WRITE_TOKENS.search(code), (label, _WRITE_TOKENS.search(code))
    assert not _SIDE_EFFECT_FUNCTIONS.search(code), label
    statements = [part.strip() for part in code.split(";") if part.strip()]
    assert statements
    assert all(
        statement.split(None, 1)[0].lower() in {"select", "with"} for statement in statements
    )

    path = tmp_path / "generated.sql"
    path.write_text(sql, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "guard.py"), "check-readonly-sql", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (label, result.stdout, result.stderr)


_LEAK_PATTERNS = re.compile(
    r"postgres(?:ql)?://|DATABASE_URL|PGPASSWORD|PGHOST|PGUSER|PGDATABASE|password\s*=|"
    r"\.rds\.amazonaws\.com|supabase\.co|neon\.tech|render\.com|inet_server_addr|"
    r"inet_client_addr",
    re.IGNORECASE,
)


def test_generated_artifacts_contain_no_credential_or_connection_target():
    synthetic, rows = _synthetic_candidate()
    for candidate, base in ((_n2(), _base_rows()), (synthetic, rows)):
        for kind, (name, text) in generate_artifacts(candidate, base).items():
            assert not _LEAK_PATTERNS.search(text), (name, _LEAK_PATTERNS.search(text))
            if kind in g7.SQL_KINDS:
                # database / user identity is only ever reported as a boolean
                for function in ("current_database()", "current_user"):
                    for match in re.finditer(re.escape(function), text):
                        assert text[match.end() : match.end() + 12] == " IS NOT NULL", name


# --- determinism ------------------------------------------------------------------------------


def test_same_input_gives_byte_identical_output():
    first = _generate()
    second = _generate()
    assert first == second


def test_output_order_is_stable():
    artifacts = _generate()
    assert list(artifacts) == [kind for kind, _ in g7.ARTIFACT_KINDS]
    assert [name for name, _ in artifacts.values()] == [
        "nsrc_000002_g7_preflight.sql",
        "nsrc_000002_g7_pre_base_guard.sql",
        "nsrc_000002_g7_post_base_guard.sql",
        "nsrc_000002_g7_post_knowledge_verification.sql",
        "nsrc_000002_g7_base_subset.json",
        "nsrc_000002_g7_runtime_qa.py",
    ]


def _reverse_key_order(value):
    if isinstance(value, dict):
        return {key: _reverse_key_order(value[key]) for key in reversed(list(value))}
    if isinstance(value, list):
        return [_reverse_key_order(item) for item in value]
    return value


def test_spec_key_order_does_not_change_sql_or_runtime_qa():
    baseline = _generate()
    reordered = _generate(_reverse_key_order(_n2()))
    for kind in (*g7.SQL_KINDS, "runtime_qa"):
        assert reordered[kind] == baseline[kind], kind


def test_generation_does_not_mutate_inputs():
    candidate, rows = _n2(), _base_rows()
    before = (copy.deepcopy(candidate), copy.deepcopy(rows))
    generate_artifacts(candidate, rows)
    assert (candidate, rows) == before


# --- target-only subset -------------------------------------------------------------------------


def _subset(rows, candidate=None):
    candidate = candidate or _n2()
    return extract_target_subset(
        rows,
        name_jp=candidate["identity"]["official_name"],
        address=candidate["identity"]["official_address"],
        expected_row=candidate["base_seed_row"],
    )


def test_subset_contains_only_the_requested_row_with_data_preserved():
    rows = _base_rows()
    subset = _subset(rows)
    assert len(rows) > 1
    assert len(subset) == 1
    source = [r for r in rows if r["name_jp"] == "青澤神社"][0]
    assert subset == [source]
    assert list(subset[0]) == list(source)
    subset[0]["goriyaku"] = "mutated"
    assert source["goriyaku"] == ""


def test_subset_zero_match_fails():
    rows = [r for r in _base_rows() if r["name_jp"] != "青澤神社"]
    with pytest.raises(SubsetError, match="found 0"):
        _subset(rows)


def test_subset_multiple_exact_matches_fail():
    rows = _base_rows()
    target = [r for r in rows if r["name_jp"] == "青澤神社"][0]
    with pytest.raises(SubsetError, match="found 2"):
        _subset([*rows, copy.deepcopy(target)])


def test_subset_row_drift_fails():
    rows = copy.deepcopy(_base_rows())
    for row in rows:
        if row["name_jp"] == "青澤神社":
            row["latitude"] = 37.0
    with pytest.raises(SubsetError, match="differs"):
        _subset(rows)


@pytest.mark.parametrize(
    ("name", "address"),
    [
        ("青澤神社 ", "新潟県糸魚川市大字青海2696番地"),
        ("青沢神社", "新潟県糸魚川市大字青海2696番地"),
        ("青澤神社", "新潟県糸魚川市大字青海２６９６番地"),
        ("青澤神社", "糸魚川市大字青海2696番地"),
    ],
)
def test_subset_does_not_normalize_identity(name, address):
    rows = [r for r in _base_rows() if r["name_jp"] != "青澤神社"]
    rows.append({**_n2()["base_seed_row"], "name_jp": name, "address": address})
    with pytest.raises(SubsetError, match="found 0"):
        _subset(rows)


def test_subset_never_renders_more_than_one_row():
    with pytest.raises(SubsetError):
        render_subset(_base_rows())
    with pytest.raises(SubsetError):
        render_subset([])
    with pytest.raises(SubsetError):
        extract_target_subset({"rows": []}, name_jp="x", address="y", expected_row={})


def test_generation_fails_closed_when_target_row_is_missing():
    rows = [r for r in _base_rows() if r["name_jp"] != "青澤神社"]
    with pytest.raises(SubsetError):
        _generate(rows=rows)


# --- synthetic candidate rendering -------------------------------------------------------------


def test_synthetic_candidate_escapes_literals_and_uses_explicit_runtime_expectations():
    candidate, rows = _synthetic_candidate()
    artifacts = generate_artifacts(candidate, rows)
    assert "'架空''神社'" in artifacts["preflight"][1]
    assert "nsrc_999999_source_identity" in artifacts["pre_base_guard"][1]
    runtime = artifacts["runtime_qa"][1]
    compile(runtime, "nsrc_999999_g7_runtime_qa.py", "exec")
    assert 'H1_CONTENT = "架空の由緒が一文だけある。"' in runtime
    assert "UNSUPPORTED_DEITY_NAMES = ()" in runtime
    assert "という背景があります" not in runtime
    assert 'trace_id="nsrc-999999-g7-production-runtime"' in runtime
    assert json.loads(artifacts["base_subset"][1]) == [candidate["base_seed_row"]]


def test_golden_runtime_qa_keeps_read_only_transaction_and_exact_identity():
    runtime = _generate()["runtime_qa"][1]
    assert 'cursor.execute("SET TRANSACTION READ ONLY")' in runtime
    assert "with transaction.atomic():" in runtime
    assert "Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)" in runtime
    assert 'print("TRANSACTION_MODE=READ_ONLY")' in runtime
    assert 'assert list(body["deities"]) == []' in runtime
    assert 'assert len(body["histories"]) == 1' in runtime


# --- no Production connection --------------------------------------------------------------------

_ALLOWED_IMPORTS = {
    "__future__",
    "argparse",
    "copy",
    "hashlib",
    "json",
    "math",
    "re",
    "sys",
    "pathlib",
    "guard",
}


def test_generator_imports_no_database_or_network_module():
    tree = ast.parse(Path(g7.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert imported <= _ALLOWED_IMPORTS, imported - _ALLOWED_IMPORTS
    source = Path(g7.__file__).read_text(encoding="utf-8")
    assert "environ" not in source
    assert "subprocess" not in source


def test_cli_validate_and_generate_outside_repo(tmp_path):
    env = {
        key: value for key, value in os.environ.items() if not key.startswith(("PG", "DATABASE"))
    }
    validate = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "g7_artifacts.py"), "validate"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert validate.returncode == 0, validate.stderr
    out = tmp_path / "g7"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "g7_artifacts.py"),
            "generate",
            "--candidate",
            "nsrc-000002",
            "--output-dir",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert "PRODUCTION_CONNECTION=NONE" in result.stdout
    assert sorted(path.name for path in out.iterdir()) == sorted(
        name for name, _ in _generate().values()
    )
    for kind, path in GOLDEN.items():
        assert (out / path.name).read_text(encoding="utf-8") == path.read_text(encoding="utf-8"), (
            kind
        )


@pytest.mark.parametrize("inside", ["scripts/migration_safety/out", "out"])
def test_cli_refuses_output_inside_repo(inside):
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "g7_artifacts.py"),
            "generate",
            "--candidate",
            "nsrc-000002",
            "--output-dir",
            str(REPO_ROOT / inside),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "BLOCKED" in result.stderr
    assert not (REPO_ROOT / inside).exists()


def test_cli_refuses_non_empty_output_dir(tmp_path):
    (tmp_path / "stale.sql").write_text("SELECT 1;\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "g7_artifacts.py"),
            "generate",
            "--candidate",
            "nsrc-000002",
            "--output-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "new or empty" in result.stderr


def test_cli_blocks_unknown_candidate(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_DIR / "g7_artifacts.py"),
            "generate",
            "--candidate",
            "nsrc-000004",
            "--output-dir",
            str(tmp_path / "x"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "BLOCKED" in result.stderr
    assert not (tmp_path / "x").exists()
