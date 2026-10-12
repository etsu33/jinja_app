"""Pure unit tests for scripts/migration_safety/g7_sql_generator.py (G-7 Phase 1).

No database, no network, no Django. Run with:
    python3 -m pytest scripts/migration_safety/tests/test_g7_sql_generator.py -v
"""

import ast
import copy
import importlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import g7_sql_generator as g7  # noqa: E402
from g7_sql_generator import (  # noqa: E402
    SpecError,
    generate_sql,
    load_spec,
    load_specs,
    validate_spec,
)

SPEC_DIR = SCRIPT_DIR / "g7_specs"
SQL_DIR = SCRIPT_DIR / "sql"
N2 = SPEC_DIR / "nsrc_000002.json"
N4 = SPEC_DIR / "nsrc_000004.json"
GENERATOR = SCRIPT_DIR / "g7_sql_generator.py"
BLOCK_RE = re.compile(
    r"-- BEGIN nsrc_000002_source_identity\n(.*?)-- END nsrc_000002_source_identity\n",
    re.DOTALL,
)


def _raw(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _historical(slug: str) -> dict[str, str]:
    return {
        name: (SQL_DIR / f"{slug}_{name}").read_text(encoding="utf-8") for _, name in g7.ARTIFACTS
    }


# --- spec load / contract ------------------------------------------------------------------


def test_committed_specs_are_valid_and_unique():
    specs = load_specs(sorted(SPEC_DIR.glob("*.json")))
    assert [spec["candidate"]["candidate_id"] for spec in specs] == ["nsrc-000002", "nsrc-000004"]
    assert [spec["source_identity"]["strategy"] for spec in specs] == [
        "normalized_url_identity",
        "url_pattern_set",
    ]


def test_spec_dir_is_not_the_g5_test_only_manifest():
    for path in [*SPEC_DIR.glob("*.json"), GENERATOR]:
        assert "shrine_expansion_handoffs" not in path.read_text(encoding="utf-8")


def test_duplicate_candidate_spec_fails(tmp_path):
    copy_path = tmp_path / "copy.json"
    copy_path.write_text(N2.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(SpecError, match="duplicate candidate spec"):
        load_specs([N2, copy_path])


def _mutate(path: Path, mutate) -> dict:
    spec = _raw(path)
    mutate(spec)
    return spec


def _at(spec: dict, keys):
    target = spec
    for key in keys:
        target = target[key]
    return target


def _drop(*keys):
    return lambda spec: _at(spec, keys[:-1]).pop(keys[-1])


def _set(*keys, value):
    def mutate(spec):
        _at(spec, keys[:-1])[keys[-1]] = value

    return mutate


@pytest.mark.parametrize("path", [N2, N4], ids=["n2", "n4"])
@pytest.mark.parametrize(
    "keys",
    [
        ("candidate",),
        ("production_pre_state",),
        ("base",),
        ("knowledge",),
        ("post_state",),
        ("candidate", "address"),
        ("candidate", "alternate_names"),
        ("production_pre_state", "deity_total"),
        ("base", "expected_exact_after"),
        ("knowledge", "source_fact_stable_keys"),
        ("post_state", "history_total"),
        ("source_identity", "source_type"),
    ],
)
def test_missing_required_field_fails(path, keys):
    with pytest.raises(SpecError, match="missing field"):
        validate_spec(_mutate(path, _drop(*keys)))


@pytest.mark.parametrize(
    ("path", "keys"),
    [
        (N2, ("normalized_url_identity_sql",)),
        (N2, ("source_identity", "normalized_url")),
        (N2, ("source_identity", "accepted_source_count")),
        (N2, ("normalized_url_identity_sql", "frozen_evidence")),
        (N2, ("normalized_url_identity_sql", "history_attributes", 0, "period_text")),
        (N4, ("url_pattern_set_sql",)),
        (N4, ("source_identity", "url_patterns")),
        (N4, ("url_pattern_set_sql", "required_temples_migration")),
    ],
)
def test_missing_strategy_field_fails(path, keys):
    with pytest.raises(SpecError, match="missing field"):
        validate_spec(_mutate(path, _drop(*keys)))


@pytest.mark.parametrize("path", [N2, N4], ids=["n2", "n4"])
@pytest.mark.parametrize(
    "keys",
    [
        ("defaults",),
        ("candidate", "reading"),
        ("production_pre_state", "hostname"),
        ("base", "credential"),
        ("knowledge", "deity_sources"),
        ("post_state", "assignment_total"),
    ],
)
def test_unknown_field_fails(path, keys):
    with pytest.raises(SpecError, match="unknown field"):
        validate_spec(_mutate(path, _set(*keys, value="x")))


@pytest.mark.parametrize("value", [2, 0, "1", True, None])
def test_unknown_schema_version_fails(value):
    with pytest.raises(SpecError, match="schema_version"):
        validate_spec(_mutate(N2, _set("schema_version", value=value)))


@pytest.mark.parametrize(
    "candidate_id", ["nsrc-2", "wave0-010", "NSRC-000002", "nsrc-0000002", " nsrc-000002", 2]
)
def test_invalid_candidate_id_fails(candidate_id):
    with pytest.raises(SpecError, match="candidate_id"):
        validate_spec(_mutate(N2, _set("candidate", "candidate_id", value=candidate_id)))


# --- strategy split -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "strategy", ["normalized", "url_patterns", "", None, "NORMALIZED_URL_IDENTITY"]
)
def test_unknown_strategy_fails(strategy):
    with pytest.raises(SpecError, match="strategy"):
        validate_spec(_mutate(N2, _set("source_identity", "strategy", value=strategy)))


def test_missing_strategy_fails():
    with pytest.raises(SpecError, match="strategy"):
        validate_spec(_mutate(N2, _drop("source_identity", "strategy")))


@pytest.mark.parametrize(
    ("path", "keys", "value"),
    [
        # normalized_url_identity must not silently accept url_pattern_set fields
        (N2, ("source_identity", "url_patterns"), ["matsuri.geo-itoigawa.com/calendar/m04"]),
        (N2, ("url_pattern_set_sql",), {"required_temples_migration": "0120_x"}),
        # url_pattern_set must not silently accept normalized_url metadata fields
        (N4, ("source_identity", "normalized_url"), "https://www.aomi-jinjya.or.jp/"),
        (N4, ("source_identity", "publisher"), "青海神社"),
        (N4, ("source_identity", "verification_status"), "source_confirmed"),
        (N4, ("source_identity", "confidence"), "high"),
        (N4, ("source_identity", "language"), "ja"),
        (N4, ("source_identity", "bibliography"), ""),
        (N4, ("source_identity", "diagnostic_host_tokens"), ["aomi-jinjya.or.jp"]),
        (N4, ("source_identity", "accepted_source_count"), 0),
        (N4, ("normalized_url_identity_sql",), {}),
    ],
)
def test_fields_of_the_wrong_strategy_fail(path, keys, value):
    with pytest.raises(SpecError, match="unknown field"):
        validate_spec(_mutate(path, _set(*keys, value=value)))


def test_switching_strategy_without_fields_fails():
    with pytest.raises(SpecError):
        validate_spec(_mutate(N2, _set("source_identity", "strategy", value="url_pattern_set")))
    with pytest.raises(SpecError):
        validate_spec(
            _mutate(N4, _set("source_identity", "strategy", value="normalized_url_identity"))
        )


# --- invalid values / totals / deltas -------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "keys", "value", "message"),
    [
        (N2, ("candidate", "name_jp"), "", "empty"),
        (N2, ("candidate", "name_jp"), "   ", "empty"),
        (N4, ("candidate", "address"), "", "empty"),
        (N2, ("candidate", "name_jp"), " 青澤神社", "whitespace"),
        (N2, ("candidate", "address"), "新潟県\n糸魚川市", "control"),
        (N2, ("candidate", "latitude"), 91.0, "latitude"),
        (N2, ("candidate", "latitude"), "37.0", "latitude"),
        (N4, ("candidate", "longitude"), -181.0, "longitude"),
        (N4, ("candidate", "longitude"), float("nan"), "longitude"),
        (N2, ("candidate", "latitude"), True, "latitude"),
        (N2, ("candidate", "alternate_names"), ["青澤神社"], "repeat"),
        (N2, ("candidate", "alternate_names"), ["青沢神社", "青沢神社"], "duplicate"),
        (N4, ("candidate", "alternate_names"), ["青海社"], "alternate"),
        (N2, ("production_pre_state", "shrine_total"), -1, "non-negative"),
        (N4, ("production_pre_state", "source_total"), 1.5, "non-negative"),
        (N4, ("post_state", "deity_total"), -3, "non-negative"),
        (N2, ("post_state", "shrine_total"), 121, "delta"),
        (N2, ("post_state", "source_total"), 140, "delta"),
        (N2, ("post_state", "history_total"), 228, "delta"),
        (N4, ("post_state", "source_total"), 139, "delta"),
        (N4, ("post_state", "deity_total"), 294, "delta"),
        (N4, ("post_state", "source_fact_total"), 33, "delta"),
        (N4, ("production_pre_state", "shrine_total"), 121, "delta"),
        (N2, ("base", "expected_exact_before"), 1, "supported"),
        (N2, ("base", "expected_exact_after"), 2, "supported"),
        (N4, ("base", "expected_same_name_after"), 0, "supported"),
        (N4, ("base", "expected_goriyaku_tag_links_after"), 1, "supported"),
        (N4, ("base", "expected_goriyaku_text"), "家内安全", "supported"),
        (N4, ("base", "expected_exact_after"), True, "non-negative|supported"),
        (N4, ("knowledge", "expected_goriyaku_tag_links"), 1, "only 0"),
        (N4, ("knowledge", "expected_deity_count"), 3, "expected_deity_count"),
        (N4, ("knowledge", "expected_history_count"), 1, "expected_history_count"),
        (N4, ("knowledge", "expected_source_fact_count"), 10, "expected_source_fact_count"),
        (N4, ("knowledge", "expected_source_count"), 0, "at least 1"),
        (N4, ("knowledge", "deity_names"), ["椎根津彦命", "椎根津彦命"], "duplicate"),
        (N4, ("knowledge", "history_titles"), ["神亀3年の創建", "神亀3年の創建"], "duplicate"),
        (N2, ("knowledge", "expected_deity_count"), 1, "expected_deity_count"),
        (N2, ("source_identity", "accepted_source_count"), 2, "accepted_source_count"),
        (N2, ("source_identity", "source_type"), "web", "source_type"),
        (N2, ("source_identity", "verification_status"), "verified", "verification_status"),
        (N2, ("source_identity", "diagnostic_host_tokens"), [], "empty"),
        (N2, ("source_identity", "diagnostic_path_tokens"), ["Calendar"], "lowercase"),
        (N2, ("source_identity", "diagnostic_host_tokens"), ["a%b"], "lowercase"),
        (N4, ("source_identity", "url_patterns"), [], "empty"),
        (N4, ("source_identity", "url_patterns"), ["aomi'jinjya"], "lowercase"),
        (N4, ("source_identity", "url_patterns"), ["Aomi-jinjya.or.jp"], "lowercase"),
        (N4, ("source_identity", "source_type"), "website", "source_type"),
        (N4, ("url_pattern_set_sql", "required_temples_migration"), "latest", "invalid"),
        (
            N2,
            ("normalized_url_identity_sql", "frozen_evidence", "production_state_class"),
            "CONFLICT",
            "production_state_class",
        ),
        (
            N2,
            ("normalized_url_identity_sql", "frozen_evidence", "source_identity_state"),
            "REUSABLE",
            "source_identity_state",
        ),
        (
            N2,
            ("normalized_url_identity_sql", "frozen_evidence", "server_version"),
            "17",
            "server_version",
        ),
        (N2, ("normalized_url_identity_sql", "sql_labels", "alternates"), {}, "alternates"),
        (
            N2,
            ("normalized_url_identity_sql", "sql_labels", "canonical"),
            "shinji",
            "duplicate label",
        ),
        (
            N2,
            ("normalized_url_identity_sql", "history_attributes", 0, "title"),
            "別の祭礼",
            "title",
        ),
        (
            N2,
            ("normalized_url_identity_sql", "history_attributes", 0, "event_date"),
            "2026-04-19",
            "event_date",
        ),
        (
            N2,
            ("normalized_url_identity_sql", "source_identity_regression_test"),
            "../x.py",
            "repo-relative",
        ),
        (
            N2,
            ("normalized_url_identity_sql", "source_identity_regression_test"),
            "backend/missing.py",
            "exist",
        ),
    ],
)
def test_invalid_values_fail(path, keys, value, message):
    with pytest.raises(SpecError, match=message):
        validate_spec(_mutate(path, _set(*keys, value=value)))


def test_duplicate_source_fact_stable_keys_fail():
    def mutate(spec):
        keys = spec["knowledge"]["source_fact_stable_keys"]
        keys[-1] = keys[0]

    with pytest.raises(SpecError, match="duplicate"):
        validate_spec(_mutate(N4, mutate))


def test_duplicate_url_patterns_fail():
    def mutate(spec):
        spec["source_identity"]["url_patterns"].append(spec["source_identity"]["url_patterns"][0])

    with pytest.raises(SpecError, match="duplicate"):
        validate_spec(_mutate(N4, mutate))


def test_accepted_source_count_changes_the_expected_source_delta():
    def reuse(spec):
        spec["source_identity"]["accepted_source_count"] = 1
        spec["normalized_url_identity_sql"]["frozen_evidence"]["source_identity_state"] = "REUSABLE"

    with pytest.raises(SpecError, match="delta"):
        validate_spec(_mutate(N2, reuse))
    spec = _mutate(N2, reuse)
    spec["post_state"]["source_total"] = 140
    validate_spec(spec)


# --- golden compatibility --------------------------------------------------------------------


@pytest.mark.parametrize("name", [name for _, name in g7.ARTIFACTS])
def test_nsrc_000002_golden_sql_is_byte_identical(name):
    generated = dict(generate_sql(load_spec(N2)))
    assert generated[name] == _historical("nsrc_000002")[name]


def test_nsrc_000002_source_identity_block_is_identical_in_all_six_places():
    committed = {
        block for text in _historical("nsrc_000002").values() for block in BLOCK_RE.findall(text)
    }
    assert len(committed) == 1
    generated = dict(generate_sql(load_spec(N2)))
    found = [block for text in generated.values() for block in BLOCK_RE.findall(text)]
    assert len(found) == 6
    assert set(found) == committed


@pytest.mark.parametrize("name", [name for _, name in g7.ARTIFACTS])
def test_nsrc_000004_historical_sql_is_also_reproduced(name):
    generated = dict(generate_sql(load_spec(N4)))
    assert generated[name] == _historical("nsrc_000004")[name]


def test_nsrc_000004_spec_represents_its_g7_evidence():
    spec = load_spec(N4)
    assert spec["source_identity"] == {
        "strategy": "url_pattern_set",
        "source_type": "shrine_official",
        "url_patterns": [
            "aomi-jinjya.or.jp/history/gosaisin.html",
            "aomi-jinjya.or.jp/history/yuisyo.html",
            "aomi-jinjya.or.jp/gokitou/syurui.html",
        ],
    }
    knowledge = spec["knowledge"]
    assert knowledge["deity_names"] == ["椎根津彦命", "大国魂命"]
    assert knowledge["history_titles"] == ["神亀3年の創建", "明治5年の三社本殿合殿"]
    assert len(knowledge["source_fact_stable_keys"]) == 11
    # docs/audit/niigata-h001-g7-production-import.md: +1 / +3 / +2 / +2 / +11
    delta = {k: spec["post_state"][k] - spec["production_pre_state"][k] for k in g7.TOTAL_KEYS}
    assert delta == {
        "shrine_total": 1,
        "source_total": 3,
        "deity_total": 2,
        "history_total": 2,
        "source_fact_total": 11,
    }
    generated = "".join(text for _, text in generate_sql(spec))
    for pattern in spec["source_identity"]["url_patterns"]:
        assert f"LIKE '%{pattern}%'" in generated
    for key in knowledge["source_fact_stable_keys"]:
        assert f"'{key}'" in generated
    assert "normalize" not in generated
    assert "source_identity" not in generated


def test_strategies_render_different_source_logic():
    n2 = "".join(text for _, text in generate_sql(load_spec(N2)))
    n4 = "".join(text for _, text in generate_sql(load_spec(N4)))
    assert "source_url_norm" in n2 and "source_url_norm" not in n4
    assert "frozen AS (" in n2 and "frozen AS (" not in n4


# --- read-only / leakage --------------------------------------------------------------------

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
_LEAK_PATTERNS = re.compile(
    r"postgres(?:ql)?://|DATABASE_URL|PGPASSWORD|PGHOST|PGUSER|PGDATABASE|password\s*=|"
    r"\.rds\.amazonaws\.com|supabase\.co|neon\.tech|render\.com|inet_server_addr|inet_client_addr",
    re.IGNORECASE,
)


def _generated_params():
    return [
        pytest.param(name, text, id=f"{path.stem}-{name}")
        for path in (N2, N4)
        for name, text in generate_sql(load_spec(path))
    ]


@pytest.mark.parametrize(("name", "sql"), _generated_params())
def test_generated_sql_is_read_only(name, sql, tmp_path):
    code = re.sub(r"'(?:[^']|'')*'", "''", re.sub(r"--[^\n]*", "", sql))
    assert not _WRITE_TOKENS.search(code), _WRITE_TOKENS.search(code)
    assert not _SIDE_EFFECT_FUNCTIONS.search(code)
    statements = [part.strip() for part in code.split(";") if part.strip()]
    assert statements
    assert {statement.split(None, 1)[0].lower() for statement in statements} <= {"select", "with"}

    path = tmp_path / name
    path.write_text(sql, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "guard.py"), "check-readonly-sql", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(("name", "sql"), _generated_params())
def test_generated_sql_has_no_credential_or_connection_target(name, sql):
    assert not _LEAK_PATTERNS.search(sql), _LEAK_PATTERNS.search(sql)
    for function in ("current_database()", "current_user"):
        for match in re.finditer(re.escape(function), sql):
            assert sql[match.end() : match.end() + 12] == " IS NOT NULL", name


# --- determinism / output --------------------------------------------------------------------


def _reverse_key_order(value):
    if isinstance(value, dict):
        return {key: _reverse_key_order(value[key]) for key in reversed(list(value))}
    if isinstance(value, list):
        return [_reverse_key_order(item) for item in value]
    return value


@pytest.mark.parametrize("path", [N2, N4], ids=["n2", "n4"])
def test_same_input_gives_byte_identical_output(path):
    spec = load_spec(path)
    before = copy.deepcopy(spec)
    assert generate_sql(spec) == generate_sql(spec)
    assert generate_sql(_reverse_key_order(spec)) == generate_sql(spec)
    assert spec == before


@pytest.mark.parametrize("path", [N2, N4], ids=["n2", "n4"])
def test_output_order_is_stable(path):
    assert [name for name, _ in generate_sql(load_spec(path))] == [
        "g7_preflight.sql",
        "g7_pre_base_guard.sql",
        "g7_post_base_guard.sql",
        "g7_post_knowledge_verification.sql",
    ]


def test_write_sql_writes_only_the_four_files(tmp_path):
    other = tmp_path / "keep.txt"
    other.write_text("untouched", encoding="utf-8")
    g7.write_sql(load_spec(N2), tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(
        ["keep.txt", *(name for _, name in g7.ARTIFACTS)]
    )
    assert other.read_text(encoding="utf-8") == "untouched"
    for name, text in _historical("nsrc_000002").items():
        assert (tmp_path / name).read_text(encoding="utf-8") == text


def test_write_sql_refuses_overwrite_unless_flagged(tmp_path):
    g7.write_sql(load_spec(N2), tmp_path)
    (tmp_path / "g7_preflight.sql").write_text("-- stale\nSELECT 1;\n", encoding="utf-8")
    with pytest.raises(SpecError, match="overwrite"):
        g7.write_sql(load_spec(N4), tmp_path)
    assert (tmp_path / "g7_preflight.sql").read_text(encoding="utf-8") == "-- stale\nSELECT 1;\n"
    g7.write_sql(load_spec(N4), tmp_path, overwrite=True)
    assert (tmp_path / "g7_preflight.sql").read_text(encoding="utf-8") == _historical(
        "nsrc_000004"
    )["g7_preflight.sql"]


def _cli(*args):
    env = {
        key: value for key, value in os.environ.items() if not key.startswith(("PG", "DATABASE"))
    }
    return subprocess.run(
        [sys.executable, str(GENERATOR), *args],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_cli_validate_and_generate(tmp_path):
    result = _cli("validate", str(N2), str(N4))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "VALID nsrc-000002 normalized_url_identity",
        "VALID nsrc-000004 url_pattern_set",
    ]
    out = tmp_path / "out"
    result = _cli("generate", "--spec", str(N4), "--output-dir", str(out))
    assert result.returncode == 0, result.stderr
    assert "PRODUCTION_CONNECTION=NONE" in result.stdout
    blocked = _cli("generate", "--spec", str(N4), "--output-dir", str(out))
    assert blocked.returncode == 1
    assert "overwrite" in blocked.stderr
    assert (
        _cli("generate", "--spec", str(N4), "--output-dir", str(out), "--overwrite").returncode == 0
    )


def test_cli_blocks_invalid_spec(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(_mutate(N2, _set("schema_version", value=9))), encoding="utf-8")
    result = _cli("generate", "--spec", str(bad), "--output-dir", str(tmp_path / "x"))
    assert result.returncode == 1
    assert "BLOCKED" in result.stderr
    assert not (tmp_path / "x").exists()


# --- no Production connection ------------------------------------------------------------------

_ALLOWED_IMPORTS = {
    "__future__",
    "argparse",
    "hashlib",
    "json",
    "math",
    "re",
    "sys",
    "pathlib",
    "importlib",
}


def test_generator_imports_no_database_or_network_module():
    source = GENERATOR.read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert imported <= _ALLOWED_IMPORTS, imported - _ALLOWED_IMPORTS
    assert "environ" not in source
    assert "subprocess" not in source
    # guard.py is loaded from this directory under a private module name only
    assert '"_g7_migration_safety_guard", SCRIPT_DIR / "guard.py"' in source


def test_importing_the_generator_does_not_register_a_top_level_guard_module():
    """scripts/analytics_safety also has guard.py; the generator must not shadow either."""
    before = sys.modules.get("guard")
    importlib.reload(g7)
    assert sys.modules.get("guard") is before
    assert g7.is_readonly_sql("SELECT 1;") == (True, "ok")


def test_sql_generator_generates_only_the_four_sql_artifacts():
    """The SQL generator stays SQL-only; Phase 2 subset / Runtime QA live in their own tools."""
    assert [name for _, name in g7.ARTIFACTS] == [
        "g7_preflight.sql",
        "g7_pre_base_guard.sql",
        "g7_post_base_guard.sql",
        "g7_post_knowledge_verification.sql",
    ]
    templates = sorted(
        p.relative_to(g7.TEMPLATE_DIR).as_posix()
        for p in g7.TEMPLATE_DIR.rglob("*")
        if p.is_file()
    )
    for name in templates:
        family = name.split("/", 1)[0]
        if family in g7.STRATEGIES:
            assert name.endswith(".sql.tmpl"), name
        else:
            assert family == "runtime_qa" and name.endswith(".py.tmpl"), name
    for spec_path in (N2, N4):
        assert all(name.endswith(".sql") for name, _ in generate_sql(load_spec(spec_path)))
