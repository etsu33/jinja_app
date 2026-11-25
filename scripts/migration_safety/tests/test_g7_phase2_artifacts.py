"""Pure unit tests for G-7 Phase 2: target-only Base subset + Runtime QA generation.

No database, no network, no Django. Run with:
    python3 -m pytest scripts/migration_safety/tests/test_g7_phase2_artifacts.py -v
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

import g7_extract_base_subset as subset_tool  # noqa: E402
import g7_runtime_qa_generator as runtime_tool  # noqa: E402
import g7_sql_generator as g7  # noqa: E402
from g7_sql_generator import SpecError, load_spec, validate_spec  # noqa: E402

REPO_ROOT = SCRIPT_DIR.parents[1]
SPEC_DIR = SCRIPT_DIR / "g7_specs"
N2 = SPEC_DIR / "nsrc_000002.json"
N4 = SPEC_DIR / "nsrc_000004.json"
SPECS = {"nsrc_000002": N2, "nsrc_000004": N4}
SUBSET_TOOL = SCRIPT_DIR / "g7_extract_base_subset.py"
RUNTIME_TOOL = SCRIPT_DIR / "g7_runtime_qa_generator.py"
# docs/audit/niigata-h001-nsrc-000002-g7-production-import-preflight.md §14.2（Production 適用値）
N2_SUBSET_SHA256 = "d5bcc3229b883314d54826f4381877102c4adcda7cb1e1b662ee876260bb7e40"


def _raw(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows() -> list:
    return json.loads(subset_tool.BASE_SEED_PATH.read_text(encoding="utf-8"))


def _mutate(path: Path, mutate) -> dict:
    spec = _raw(path)
    mutate(spec)
    return spec


def _at(spec, keys):
    for key in keys:
        spec = spec[key]
    return spec


def _drop(*keys):
    return lambda spec: _at(spec, keys[:-1]).pop(keys[-1])


def _set(*keys, value):
    def mutate(spec):
        _at(spec, keys[:-1])[keys[-1]] = value

    return mutate


def _env():
    return {k: v for k, v in os.environ.items() if not k.startswith(("PG", "DATABASE"))}


def _run(tool: Path, *args):
    return subprocess.run(
        [sys.executable, str(tool), *args], capture_output=True, text=True, check=False, env=_env()
    )


# --- spec extension -------------------------------------------------------------------------


def test_committed_specs_carry_phase_2_sections():
    for path in SPECS.values():
        spec = load_spec(path)
        assert set(spec["base_subset"]) == {"expected_row"}
        assert spec["runtime_qa"]["family"] in {"history_only_v1", "deity_history_v1"}


@pytest.mark.parametrize("path", [N2, N4], ids=["n2", "n4"])
@pytest.mark.parametrize(
    "keys",
    [
        ("base_subset",),
        ("runtime_qa",),
        ("base_subset", "expected_row"),
        ("runtime_qa", "trace_id"),
        ("runtime_qa", "qa_origin"),
        ("runtime_qa", "primary_history_content"),
        ("runtime_qa", "excluded_deity_names"),
        ("runtime_qa", "forbidden_guarantee_phrases"),
        ("base_subset", "expected_row", "kyusei"),
        ("base_subset", "expected_row", "location"),
    ],
)
def test_missing_phase_2_field_fails(path, keys):
    with pytest.raises(SpecError, match="missing field"):
        validate_spec(_mutate(path, _drop(*keys)))


@pytest.mark.parametrize(
    ("path", "keys"),
    [
        (N2, ("runtime_qa", "source_url")),
        (N4, ("runtime_qa", "knowledge_row_verification_status")),
        (N4, ("runtime_qa", "sources_per_knowledge_row")),
        (N4, ("runtime_qa", "source_verification_status")),
    ],
)
def test_missing_runtime_family_field_fails(path, keys):
    with pytest.raises(SpecError, match="missing field"):
        validate_spec(_mutate(path, _drop(*keys)))


@pytest.mark.parametrize(
    ("path", "keys", "value"),
    [
        (N2, ("runtime_qa", "expected_deities"), ["x"]),
        (N2, ("runtime_qa", "sources_per_knowledge_row"), 1),
        (N4, ("runtime_qa", "source_url"), "https://www.aomi-jinjya.or.jp/"),
        (N4, ("runtime_qa", "history_type"), "founding"),
        (N2, ("base_subset", "frozen_at"), "2026-10-12"),
        (N2, ("base_subset", "expected_row", "reading"), "あおさわじんじゃ"),
        (N4, ("base_subset", "expected_row", "official_name"), "青海神社"),
    ],
)
def test_unknown_phase_2_field_fails(path, keys, value):
    with pytest.raises(SpecError, match="unknown field"):
        validate_spec(_mutate(path, _set(*keys, value=value)))


@pytest.mark.parametrize(
    ("path", "keys", "value", "message"),
    [
        (N2, ("runtime_qa", "family"), "universal_v1", "family"),
        (N2, ("runtime_qa", "family"), None, "family"),
        (N2, ("runtime_qa", "trace_id"), "nsrc-000002 runtime", "trace_id"),
        (N2, ("runtime_qa", "trace_id"), 'x"); import os; ("', "trace_id"),
        (N2, ("runtime_qa", "qa_origin", "lat"), 95.0, "lat"),
        (N2, ("runtime_qa", "primary_history_content"), "", "empty"),
        (N2, ("runtime_qa", "excluded_deity_names"), [], "requires >= 1"),
        (N4, ("runtime_qa", "excluded_deity_names"), ["椎根津彦命"], "overlap"),
        (N4, ("runtime_qa", "excluded_deity_names"), ["賀茂別雷命", "賀茂別雷命"], "duplicate"),
        (N2, ("runtime_qa", "forbidden_guarantee_phrases"), [], "must not be empty"),
        (N4, ("runtime_qa", "sources_per_knowledge_row"), 0, "positive"),
        (N4, ("runtime_qa", "knowledge_row_verification_status"), "ok", "knowledge_row"),
        (N2, ("base_subset", "expected_row", "latitude"), 37.0, "candidate.latitude"),
        (N2, ("base_subset", "expected_row", "name_jp"), "青沢神社", "candidate.name_jp"),
        (N2, ("base_subset", "expected_row", "location"), {"lat": 0.0, "lng": 0.0}, "mirror"),
        (N4, ("base_subset", "expected_row", "goriyaku"), "家内安全", "goriyaku"),
        (N4, ("base_subset", "expected_row", "astro_elements"), "火", "list of strings"),
        (N4, ("base_subset", "expected_row", "kyusei"), 1, "kyusei"),
    ],
)
def test_invalid_phase_2_values_fail(path, keys, value, message):
    with pytest.raises(SpecError, match=message):
        validate_spec(_mutate(path, _set(*keys, value=value)))


@pytest.mark.parametrize(
    ("path", "family", "fields", "message"),
    [
        # history_only_v1 compares Sources with normalize_source_url(): normalized strategy only
        (
            N4,
            "history_only_v1",
            {"source_url": "https://www.aomi-jinjya.or.jp/history/yuisyo.html"},
            "requires normalized_url_identity",
        ),
        # deity_history_v1 needs Deities: nsrc-000002 (Deity 0) cannot use it
        (
            N2,
            "deity_history_v1",
            {
                "knowledge_row_verification_status": "source_confirmed",
                "sources_per_knowledge_row": 1,
                "source_verification_status": "source_confirmed",
            },
            "requires >= 1 Deity",
        ),
    ],
)
def test_unsupported_runtime_shape_fails(path, family, fields, message):
    def mutate(spec):
        qa = spec["runtime_qa"]
        for key in ("source_url", *runtime_tool_family_fields()):
            qa.pop(key, None)
        qa["family"] = family
        qa.update(fields)

    with pytest.raises(SpecError, match=message):
        validate_spec(_mutate(path, mutate))


def runtime_tool_family_fields():
    return (
        "knowledge_row_verification_status",
        "sources_per_knowledge_row",
        "source_verification_status",
    )


def test_phase_1_sql_is_unchanged_by_the_spec_extension():
    for slug, path in SPECS.items():
        for name, text in g7.generate_sql(load_spec(path)):
            assert text == (SCRIPT_DIR / "sql" / f"{slug}_{name}").read_text(encoding="utf-8")


# --- generic target-only subset ------------------------------------------------------------


@pytest.mark.parametrize("path", [N2, N4], ids=["n2", "n4"])
def test_subset_is_the_exact_frozen_row(path):
    spec = load_spec(path)
    rows = _rows()
    subset = subset_tool.extract_subset(spec, rows)
    assert subset == [spec["base_subset"]["expected_row"]]
    source = [
        r
        for r in rows
        if r["name_jp"] == spec["candidate"]["name_jp"]
        and r["address"] == spec["candidate"]["address"]
    ]
    assert subset == source
    assert list(subset[0]) == list(source[0])
    subset[0]["goriyaku"] = "mutated"
    assert source[0]["goriyaku"] == ""


def test_nsrc_000002_subset_is_byte_identical_to_the_historical_extractor():
    text = subset_tool.render(subset_tool.extract_subset(load_spec(N2), _rows()))
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == N2_SUBSET_SHA256
    import nsrc_000002_g7_extract_base_subset as historical

    assert text == historical.render(historical.extract_subset())


def test_nsrc_000004_subset_is_the_canonical_aomi_row():
    subset = subset_tool.extract_subset(load_spec(N4), _rows())
    assert subset == [
        {
            "name_jp": "青海神社",
            "address": "新潟県加茂市大字加茂字宮山229番地",
            "latitude": 37.65657387,
            "longitude": 139.0536436,
            "goriyaku": "",
            "kyusei": None,
            "astro_elements": [],
            "location": {"lat": 37.65657387, "lng": 139.0536436},
        }
    ]


@pytest.mark.parametrize("path", [N2, N4], ids=["n2", "n4"])
def test_subset_zero_rows_blocked(path):
    spec = load_spec(path)
    rows = [r for r in _rows() if r["name_jp"] != spec["candidate"]["name_jp"]]
    with pytest.raises(subset_tool.SubsetBlocked, match="found 0"):
        subset_tool.extract_subset(spec, rows)


@pytest.mark.parametrize("path", [N2, N4], ids=["n2", "n4"])
def test_subset_duplicate_rows_blocked(path):
    spec = load_spec(path)
    rows = _rows()
    rows.append(copy.deepcopy(spec["base_subset"]["expected_row"]))
    with pytest.raises(subset_tool.SubsetBlocked, match="found 2"):
        subset_tool.extract_subset(spec, rows)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("latitude", 37.0),
        ("goriyaku", "家内安全"),
        ("kyusei", "一白水星"),
        ("astro_elements", ["火"]),
        ("location", {"lat": 0.0, "lng": 0.0}),
        ("visit_style_tags", ["quiet"]),
        ("goriyaku_tags", ["家内安全"]),
    ],
)
def test_subset_frozen_row_drift_blocked(key, value):
    spec = load_spec(N2)
    rows = copy.deepcopy(_rows())
    for row in rows:
        if row["name_jp"] == "青澤神社":
            row[key] = value
    with pytest.raises(subset_tool.SubsetBlocked, match="differs"):
        subset_tool.extract_subset(spec, rows)


@pytest.mark.parametrize(
    ("name", "address"),
    [
        ("青澤神社 ", "新潟県糸魚川市大字青海2696番地"),
        ("青沢神社", "新潟県糸魚川市大字青海2696番地"),
        ("青澤神社", "新潟県糸魚川市大字青海２６９６番地"),
        ("青澤神社", "糸魚川市大字青海2696番地"),
    ],
)
def test_subset_never_normalizes_identity(name, address):
    spec = load_spec(N2)
    rows = [r for r in _rows() if r["name_jp"] != "青澤神社"]
    rows.append({**spec["base_subset"]["expected_row"], "name_jp": name, "address": address})
    with pytest.raises(subset_tool.SubsetBlocked, match="found 0"):
        subset_tool.extract_subset(spec, rows)


def test_unrelated_seed_rows_do_not_affect_output():
    spec = load_spec(N2)
    baseline = subset_tool.render(subset_tool.extract_subset(spec, _rows()))
    rows = list(reversed(_rows()))
    rows.insert(0, {"name_jp": "後続追加神社", "address": "架空県架空市1-1"})
    rows.append({"name_jp": "青澤神社", "address": "別住所"})
    for row in rows:
        if row["name_jp"] == "明治神宮":
            row["goriyaku"] = "changed"
    assert subset_tool.render(subset_tool.extract_subset(spec, rows)) == baseline


def test_subset_render_is_one_row_only_and_deterministic():
    spec = load_spec(N4)
    first = subset_tool.render(subset_tool.extract_subset(spec, _rows()))
    assert first == subset_tool.render(subset_tool.extract_subset(spec, _rows()))
    assert len(json.loads(first)) == 1
    for bad in (_rows(), [], [{}, {}], "x"):
        with pytest.raises(subset_tool.SubsetBlocked):
            subset_tool.render(bad)
    with pytest.raises(subset_tool.SubsetBlocked):
        subset_tool.extract_subset(spec, {"rows": []})


@pytest.mark.parametrize("path", [N2, N4], ids=["n2", "n4"])
def test_subset_cli_writes_one_row_outside_repo(path, tmp_path):
    out = tmp_path / "subset.json"
    result = _run(SUBSET_TOOL, "--spec", str(path), "--output", str(out))
    assert result.returncode == 0, result.stderr
    assert "SUBSET_ROWS=1" in result.stdout
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data == [load_spec(path)["base_subset"]["expected_row"]]
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    assert f"SUBSET_SHA256={sha}" in result.stdout


@pytest.mark.parametrize("inside", ["scripts/migration_safety/subset.json", "subset.json"])
def test_subset_cli_refuses_output_inside_repo(inside):
    result = _run(SUBSET_TOOL, "--spec", str(N2), "--output", str(REPO_ROOT / inside))
    assert result.returncode == 1
    assert "BLOCKED" in result.stderr
    assert not (REPO_ROOT / inside).exists()


def test_subset_cli_does_not_silently_overwrite(tmp_path):
    out = tmp_path / "subset.json"
    out.write_text("keep\n", encoding="utf-8")
    result = _run(SUBSET_TOOL, "--spec", str(N2), "--output", str(out))
    assert result.returncode == 1
    assert out.read_text(encoding="utf-8") == "keep\n"
    assert _run(SUBSET_TOOL, "--spec", str(N2), "--output", str(out), "--overwrite").returncode == 0
    assert hashlib.sha256(out.read_bytes()).hexdigest() == N2_SUBSET_SHA256


def test_subset_cli_refuses_symlink_and_directory_targets(tmp_path):
    target = tmp_path / "real.json"
    target.write_text("keep\n", encoding="utf-8")
    link = tmp_path / "link.json"
    link.symlink_to(target)
    assert (
        _run(SUBSET_TOOL, "--spec", str(N2), "--output", str(link), "--overwrite").returncode == 1
    )
    assert target.read_text(encoding="utf-8") == "keep\n"
    folder = tmp_path / "dir"
    folder.mkdir()
    assert (
        _run(SUBSET_TOOL, "--spec", str(N2), "--output", str(folder), "--overwrite").returncode == 1
    )


def test_subset_cli_blocks_invalid_spec(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(_mutate(N2, _drop("base_subset"))), encoding="utf-8")
    out = tmp_path / "out.json"
    result = _run(SUBSET_TOOL, "--spec", str(bad), "--output", str(out))
    assert result.returncode == 1
    assert not out.exists()


# --- Runtime QA generation -------------------------------------------------------------------


@pytest.mark.parametrize("slug", sorted(SPECS))
def test_runtime_qa_is_byte_identical_to_the_historical_script(slug):
    generated = runtime_tool.generate_runtime_qa(load_spec(SPECS[slug]))
    assert generated == (SCRIPT_DIR / f"{slug}_g7_runtime_qa.py").read_text(encoding="utf-8")


@pytest.mark.parametrize("path", [N2, N4], ids=["n2", "n4"])
def test_runtime_qa_generation_is_deterministic_and_does_not_mutate_spec(path):
    spec = load_spec(path)
    before = copy.deepcopy(spec)
    first = runtime_tool.generate_runtime_qa(spec)
    assert runtime_tool.generate_runtime_qa(spec) == first
    reordered = json.loads(json.dumps(spec, sort_keys=True))
    assert runtime_tool.generate_runtime_qa(reordered) == first
    assert spec == before


def test_runtime_qa_families_keep_their_historical_assertions():
    n2 = runtime_tool.generate_runtime_qa(load_spec(N2))
    n4 = runtime_tool.generate_runtime_qa(load_spec(N4))
    # nsrc-000002: History-only, normalize_source_url-compatible Source, background sentence
    for snippet in (
        'assert list(body["deities"]) == []',
        'assert len(body["histories"]) == 1',
        'normalize_source_url(history["sources"][0]["url"]) == normalize_source_url(',
        'assert candidate["knowledge_deities"] == []',
        'assert preview["fact"]["deity"] is None',
        "という背景があります。",
        "for name in UNSUPPORTED_DEITY_NAMES:",
    ):
        assert snippet in n2, snippet
    # nsrc-000004: exact Deity / History sets, per-row verification, deities in reason
    for snippet in (
        'assert {row["display_name"] for row in body["deities"]} == EXPECTED_DEITIES',
        'assert {row["title"] for row in body["histories"]} == EXPECTED_HISTORY_TITLES',
        'assert row["sources"][0]["verification_status"] == "source_confirmed"',
        "for excluded in EXCLUDED_DEITIES:",
        'assert preview["fact"]["deity"] == deity_text',
        "for deity in EXPECTED_DEITIES:\n            assert deity in reason_text",
    ):
        assert snippet in n4, snippet
    for text in (n2, n4):
        for surface in (
            "DETAIL_RUNTIME=PASS",
            "CONCIERGE_CANDIDATE_PATH=PASS",
            "RECOMMENDATION_REASON=PASS",
            "COMPASS_DISTANCE=PASS",
            "COMPASS_DIRECTION=PASS",
            "for phrase in FORBIDDEN_GUARANTEE_PHRASES:",
        ):
            assert surface in text


# --- generated Runtime QA safety ---------------------------------------------------------------

_WRITE_METHODS = {
    "save",
    "create",
    "update",
    "delete",
    "bulk_create",
    "bulk_update",
    "get_or_create",
    "update_or_create",
    "add",
    "remove",
    "clear",
    "set",
    "raw",
    "executemany",
    "call_command",
    "system",
    "popen",
    "run",
    "check_call",
    "check_output",
}
_LEAK = re.compile(
    r"postgres(?:ql)?://|DATABASE_URL|PGPASSWORD|PGHOST|PGUSER|PGDATABASE|password\s*=|"
    r"\.rds\.amazonaws\.com|supabase\.co|neon\.tech|render\.com",
    re.IGNORECASE,
)


def _generated():
    return [
        pytest.param(slug, runtime_tool.generate_runtime_qa(load_spec(path)), id=slug)
        for slug, path in sorted(SPECS.items())
    ]


@pytest.mark.parametrize(("slug", "text"), _generated())
def test_generated_runtime_qa_is_read_only(slug, text):
    tree = ast.parse(text)
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    first = main.body[0]
    # main() starts with `with transaction.atomic():` whose first statement sets READ ONLY
    assert isinstance(first, ast.With)
    assert ast.unparse(first.items[0].context_expr) == "transaction.atomic()"
    inner = first.body[0]
    assert ast.unparse(inner) == (
        "with connection.cursor() as cursor:\n    cursor.execute('SET TRANSACTION READ ONLY')"
    )
    executes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in _WRITE_METHODS, (slug, ast.unparse(node))
            if node.func.attr == "execute":
                executes.append(ast.unparse(node))
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] + [getattr(node, "module", None) or ""]
            for name in names:
                assert not name.startswith(
                    ("subprocess", "psycopg", "socket", "requests", "urllib")
                ), name
                assert "call_command" not in name and "migrat" not in name, name
    assert executes == ["cursor.execute('SET TRANSACTION READ ONLY')"]
    assert "migrate" not in text


@pytest.mark.parametrize(("slug", "text"), _generated())
def test_generated_runtime_qa_has_no_credential_or_hostname(slug, text):
    assert not _LEAK.search(text), _LEAK.search(text)
    assert "environ[" not in text
    assert 'os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shrine_project.settings")' in text


def test_runtime_cli_writes_and_refuses_silent_overwrite(tmp_path):
    out = tmp_path / "qa.py"
    result = _run(RUNTIME_TOOL, "--spec", str(N4), "--output", str(out))
    assert result.returncode == 0, result.stderr
    assert "PRODUCTION_CONNECTION=NONE" in result.stdout
    assert out.read_text(encoding="utf-8") == (
        SCRIPT_DIR / "nsrc_000004_g7_runtime_qa.py"
    ).read_text(encoding="utf-8")
    out.write_text("keep\n", encoding="utf-8")
    assert _run(RUNTIME_TOOL, "--spec", str(N4), "--output", str(out)).returncode == 1
    assert out.read_text(encoding="utf-8") == "keep\n"
    assert (
        _run(RUNTIME_TOOL, "--spec", str(N4), "--output", str(out), "--overwrite").returncode == 0
    )


def test_runtime_cli_blocks_invalid_spec(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(_mutate(N2, _drop("runtime_qa", "trace_id"))), encoding="utf-8")
    result = _run(RUNTIME_TOOL, "--spec", str(bad), "--output", str(tmp_path / "qa.py"))
    assert result.returncode == 1
    assert "BLOCKED" in result.stderr
    assert not (tmp_path / "qa.py").exists()


# --- tools: no DB / network / credential ------------------------------------------------------


@pytest.mark.parametrize("tool", [SUBSET_TOOL, RUNTIME_TOOL], ids=["subset", "runtime"])
def test_tools_import_no_database_or_network_module(tool):
    source = tool.read_text(encoding="utf-8")
    imported = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert imported <= {
        "__future__",
        "argparse",
        "copy",
        "hashlib",
        "json",
        "re",
        "sys",
        "pathlib",
        "g7_sql_generator",
    }, imported
    assert "environ" not in source
    assert "subprocess" not in source
    assert "django" not in source.split('"""', 2)[2]


def test_tools_do_not_register_a_top_level_guard_module():
    code = (
        "import sys; sys.path.insert(0, %r);"
        "import g7_extract_base_subset, g7_runtime_qa_generator;"
        "print('guard' in sys.modules)"
    ) % str(SCRIPT_DIR)
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False, env=_env()
    )
    assert result.stdout.strip() == "False", result.stderr


# --- complete artifact reproducibility ---------------------------------------------------------


@pytest.mark.parametrize("slug", sorted(SPECS))
def test_one_spec_reproduces_every_g7_artifact(slug, tmp_path):
    """One validated spec -> 4 SQL + subset + Runtime QA, all equal to the reviewed artifacts."""
    spec_path = SPECS[slug]
    sql_dir = tmp_path / "sql"
    assert (
        _run(
            SCRIPT_DIR / "g7_sql_generator.py",
            "generate",
            "--spec",
            str(spec_path),
            "--output-dir",
            str(sql_dir),
        ).returncode
        == 0
    )
    subset = tmp_path / "subset.json"
    assert _run(SUBSET_TOOL, "--spec", str(spec_path), "--output", str(subset)).returncode == 0
    runtime = tmp_path / "runtime_qa.py"
    assert _run(RUNTIME_TOOL, "--spec", str(spec_path), "--output", str(runtime)).returncode == 0

    for _, name in g7.ARTIFACTS:
        assert (sql_dir / name).read_text(encoding="utf-8") == (
            SCRIPT_DIR / "sql" / f"{slug}_{name}"
        ).read_text(encoding="utf-8"), name
    assert runtime.read_text(encoding="utf-8") == (
        SCRIPT_DIR / f"{slug}_g7_runtime_qa.py"
    ).read_text(encoding="utf-8")
    assert json.loads(subset.read_text(encoding="utf-8")) == [
        load_spec(spec_path)["base_subset"]["expected_row"]
    ]
    if slug == "nsrc_000002":
        assert hashlib.sha256(subset.read_bytes()).hexdigest() == N2_SUBSET_SHA256
