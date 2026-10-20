"""NIIGATA-001-VPG001 G7 cohort freeze regression（disposable test DB only）。

PRODUCTION_EXECUTION_MODE = VPG001_4_CANDIDATE_BATCH
GUARD_BASELINE_MODE = SINGLE_FROZEN_PRESTATE + CUMULATIVE_STAGE_CHECKPOINTS

scripts/migration_safety/sql/niigata_vpg001_g7_*_guard.sql（6 stage × 5 statement）は、
Mother Ship が PR #3279 merge 後に Production で read-only 実測した唯一の pre-state（P0）を
frozen block として持つ。P1〜P5 は P0 + repository payload から導出した expected checkpoint で、
Production 実測値ではない。

- candidate statement の source_identity / target_facts block は #3279 の candidate 別 authority
  （nsrc_0000XX_g7_*.sql）と byte-identical。assertion は authority から aggregate 行だけを除き
  （cohort checkpoint statement が持つ）、accepted_source_count を測定値 0 に締めたもの。
- committed guard は、aggregate を P0 と完全一致させた disposable DB の simulated pre-state に対して
  そのまま（値を変えずに）実行する。
- #3279 の candidate 別 guard は UNSET のまま変更しない（独立測定 baseline に見せかけない）。
Production には接続しない。
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import io
import json
import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.db import DataError, connection, transaction
from django.utils import timezone

from temples.models import (
    GoriyakuTag,
    Shrine,
    ShrineDeity,
    ShrineDeityCollective,
    ShrineFactSourceCitation,
    ShrineGoriyakuAssignment,
    ShrineHistory,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.services.knowledge_seed import normalize_source_url

REPO_ROOT = Path(__file__).resolve().parents[3]
SAFETY_DIR = REPO_ROOT / "scripts" / "migration_safety"
SQL_DIR = SAFETY_DIR / "sql"
DATA_DIR = REPO_ROOT / "backend" / "temples" / "data"
BASE_SEED_PATH = DATA_DIR / "shrines_seed_clean.json"
KNOWLEDGE_SEED_DIR = DATA_DIR / "knowledge_seeds"

# deterministic candidate order（Mother Ship decision）
ORDER = ("000021", "000022", "000024", "000025")
CANDIDATES = {
    # cid: (name_jp, address, lat, lng, source_type, publisher, normalized Source URL)
    "000021": (
        "荒川神社",
        "新潟県胎内市桃崎浜187番地",
        38.1409456,
        139.4073314,
        "government",
        "新潟県",
        "https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html",
    ),
    "000022": (
        "五十嵐神社",
        "新潟県三条市大字飯田2283番地",
        37.573979,
        139.048758,
        "government",
        "三条市",
        "https://www.city.sanjo.niigata.jp/sanjonavi/see_do/history_culture/jinja_jisha_joshi/2289.html",
    ),
    "000024": (
        "秋葉神社",
        "新潟県新潟市秋葉区秋葉3丁目8番19号",
        37.7863255,
        139.1351949,
        "government",
        "新潟市",
        "https://www.city.niigata.lg.jp/kanko/bunka/shinko/bunkashigen/bunkaisannintei2.files/akihaku.pdf",
    ),
    "000025": (
        "天津神社",
        "新潟県糸魚川市一の宮1丁目3番34号",
        37.0397729,
        137.8644153,
        "shrine_official",
        "天津神社・奴奈川神社",
        "https://amatsujinja.com/story",
    ),
}
# 000025 shared-address foreign owner and excluded deities（G1 / G4）
NUNAKAWA_SHRINE = "奴奈川神社"
NUNAKAWA_DEITIES = ("奴奈川媛命", "八千矛命")

AGGREGATE_TABLES = {
    "shrine": "temples_shrine",
    "source": "temples_shrineknowledgesource",
    "deity": "temples_shrinedeity",
    "history": "temples_shrinehistory",
    "citation": "temples_shrinefactsourcecitation",
    "source_fact": "temples_shrinesourcefact",
    "collective": "temples_shrinedeitycollective",
}
# MEASURED: Mother Ship の Production read-only 実測（PR #3279 merge 後）。唯一の Production 値。
PRODUCTION_P0 = {
    "shrine": 129,
    "source": 145,
    "deity": 295,
    "history": 236,
    "citation": 2,
    "source_fact": 34,
    "collective": 6,
}
PRODUCTION_SERVER_VERSION_NUM = 170006
PRODUCTION_LATEST_TEMPLES_MIGRATION = "0121_shrine_fact_source_citation"


def _stage(shrine, source, deity, history) -> dict[str, int]:
    return {**PRODUCTION_P0, "shrine": shrine, "source": source, "deity": deity, "history": history}


# DERIVED / EXPECTED cumulative checkpoints（Mother Ship decision）。Production 実測値ではない。
CHECKPOINTS = {
    "P0": dict(PRODUCTION_P0),
    "P1": _stage(133, 145, 295, 236),
    "P2": _stage(133, 146, 296, 237),
    "P3": _stage(133, 147, 297, 237),
    "P4": _stage(133, 148, 300, 239),
    "P5": _stage(133, 149, 303, 244),
}
STAGES = ("P0", "P1", "P2", "P3", "P4", "P5")
GUARD_FILES = {
    "P0": "niigata_vpg001_g7_frozen_pre_base_guard.sql",
    "P1": "niigata_vpg001_g7_post_base_guard.sql",
    "P2": "niigata_vpg001_g7_post_000021_knowledge_guard.sql",
    "P3": "niigata_vpg001_g7_post_000022_knowledge_guard.sql",
    "P4": "niigata_vpg001_g7_post_000024_knowledge_guard.sql",
    "P5": "niigata_vpg001_g7_post_000025_knowledge_guard.sql",
}
# candidates whose Knowledge is complete at each stage
COMPLETED = {stage: ORDER[: max(0, index - 1)] for index, stage in enumerate(STAGES)}

FROZEN_RE = re.compile(
    r"-- BEGIN niigata_vpg001_g7_frozen_pre_state\n(.*?)-- END niigata_vpg001_g7_frozen_pre_state\n",
    re.DOTALL,
)
CHECKPOINT_RE = re.compile(
    r"-- BEGIN niigata_vpg001_g7_stage_checkpoint\n(.*?)-- END niigata_vpg001_g7_stage_checkpoint\n",
    re.DOTALL,
)
STATEMENT_MARK_RE = re.compile(r"^-- Statement (\d) / 5: ", re.MULTILINE)
AGGREGATE_LINE_RE = re.compile(
    r"^  AND \(SELECT COUNT\(\*\) FROM temples_(shrine|shrineknowledgesource|shrinedeity|"
    r"shrinehistory|shrinefactsourcecitation|shrinesourcefact|shrinedeitycollective)\) = "
)
AUTHORITY_FILE = {
    "ABSENT": "pre_base_guard",
    "BASE_ONLY": "post_base_guard",
    "KNOWLEDGE": "post_knowledge_verification",
}

FILLER_OWNER = "G7cohortfiller神社"
FILLER_ADDRESS = "架空県架空市G7cohort"
FILLER_URL = "https://example.invalid/g7-cohort-filler/"


# --------------------------------------------------------------------------------------
# helpers（disposable DB だけで使う）
# --------------------------------------------------------------------------------------


def _sql(name: str) -> str:
    return (SQL_DIR / name).read_text(encoding="utf-8")


def _statements(text: str) -> list[str]:
    body = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("--"))
    return [part.strip() for part in body.split(";") if part.strip()]


def _statement_sections(text: str) -> dict[int, str]:
    marks = list(STATEMENT_MARK_RE.finditer(text))
    return {
        int(m.group(1)): text[m.start() : marks[i + 1].start() if i + 1 < len(marks) else len(text)]
        for i, m in enumerate(marks)
    }


def _authority_block(cid: str, kind: str) -> str:
    pattern = re.compile(rf"-- BEGIN nsrc_{cid}_{kind}\n.*?-- END nsrc_{cid}_{kind}\n", re.DOTALL)
    found = set(pattern.findall(_sql(f"nsrc_{cid}_g7_preflight.sql")))
    assert len(found) == 1
    return found.pop()


def _authority_conditions(cid: str, state: str) -> list[str]:
    """#3279 authority assertion minus aggregates, frozen names prefixed, accepted count = 0."""
    text = _sql(f"nsrc_{cid}_g7_{AUTHORITY_FILE[state]}.sql")
    lines = text[text.rindex("SELECT 1 / CASE WHEN (\n") :].splitlines()[1:]
    lines = lines[: next(i for i, line in enumerate(lines) if line.startswith(") THEN 1"))]
    out = []
    for line in lines:
        if AGGREGATE_LINE_RE.match(line):
            continue
        if line == "  AND f.accepted_source_count IN (0, 1)":
            line = "  AND f.accepted_source_count = 0"
        out.append(
            re.sub(
                r"\bf\.(same_name_other_address_total|foreign_fact_source_relation_total|"
                r"accepted_source_count)\b",
                rf"f.nsrc_{cid}_\1",
                line,
            )
        )
    return out


def _conditions(section: str) -> list[str]:
    lines = section[section.rindex("SELECT 1 / CASE WHEN (\n") :].splitlines()[1:]
    return lines[: next(i for i, line in enumerate(lines) if line.startswith(") THEN 1"))]


def _state(stage: str, cid: str) -> str:
    if cid in COMPLETED[stage]:
        return "KNOWLEDGE"
    return "ABSENT" if stage == "P0" else "BASE_ONLY"


def _run_all(text: str) -> list[list[tuple]]:
    results = []
    with connection.cursor() as cursor:
        for statement in _statements(text):
            cursor.execute(statement)
            results.append(cursor.fetchall())
    return results


def _committed_guard_passes(stage: str) -> bool:
    """Run the committed cohort guard file unchanged."""
    try:
        with transaction.atomic():
            rows = _run_all(_sql(GUARD_FILES[stage]))
    except DataError:  # division_by_zero = guard FAIL
        return False
    assert rows == [[(1,)]] * 5
    return True


def _failing_statements(stage: str) -> set[int]:
    """1-based statements of the committed stage file that raise（each in its own savepoint）."""
    failing = set()
    for number, statement in enumerate(_statements(_sql(GUARD_FILES[stage])), start=1):
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(statement)
                    assert cursor.fetchall() == [(1,)]
        except DataError:
            failing.add(number)
    return failing


def _passing_stages() -> set[str]:
    return {stage for stage in STAGES if _committed_guard_passes(stage)}


def _aggregates() -> dict[str, int]:
    out = {}
    with connection.cursor() as cursor:
        for key, table in AGGREGATE_TABLES.items():
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            out[key] = cursor.fetchone()[0]
    return out


def _seed(cid: str) -> dict:
    return json.loads((KNOWLEDGE_SEED_DIR / f"nsrc_{cid}_seed.json").read_text(encoding="utf-8"))


def _payload(cid: str) -> dict[str, int]:
    seed = _seed(cid)
    (shrine,) = seed["shrines"]
    return {
        "source": len(seed["sources"]),
        "deity": len(shrine["deities"]),
        "history": len(shrine["histories"]),
    }


def _load(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, SAFETY_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extractor():
    return _load(
        "niigata_vpg001_g7_extract_base_subset", "niigata_vpg001_g7_extract_base_subset.py"
    )


def _target(cid: str) -> Shrine:
    name, address = CANDIDATES[cid][:2]
    return Shrine.objects.get(name_jp=name, address=address)


def _python_normalized(url: str) -> str | None:
    try:
        return normalize_source_url(url)
    except ValueError:
        return None


def _source(cid: str) -> ShrineKnowledgeSource:
    stype, _, normalized = CANDIDATES[cid][4:]
    (source,) = [
        s
        for s in ShrineKnowledgeSource.objects.filter(source_type=stype)
        if _python_normalized(s.url) == normalized
    ]
    return source


def _facts(cid: str) -> list:
    shrine = _target(cid)
    return [
        *ShrineDeity.objects.filter(shrine=shrine).order_by("id"),
        *ShrineHistory.objects.filter(shrine=shrine).order_by("id"),
    ]


def _fact_snapshot() -> tuple:
    """Every Fact id / field and every Fact-Source relation row（ids included）。"""
    return (
        tuple(ShrineDeity.objects.order_by("id").values_list()),
        tuple(ShrineHistory.objects.order_by("id").values_list()),
        tuple(ShrineDeity.sources.through.objects.order_by("id").values_list()),
        tuple(ShrineHistory.sources.through.objects.order_by("id").values_list()),
        tuple(ShrineKnowledgeSource.objects.order_by("id").values_list()),
    )


def _goriyaku_snapshot() -> tuple:
    return (
        tuple(GoriyakuTag.objects.order_by("id").values_list("id", "name")),
        tuple(ShrineGoriyakuAssignment.objects.order_by("id").values_list("id", "shrine_id")),
        tuple(
            Shrine.goriyaku_tags.through.objects.order_by("id").values_list(
                "shrine_id", "goriyakutag_id"
            )
        ),
        tuple(Shrine.objects.order_by("id").values_list("id", "goriyaku")),
    )


def _plan_summary(output: str) -> dict[str, int]:
    (line,) = [line for line in output.splitlines() if line.startswith("plan summary: ")]
    return ast.literal_eval(line.removeprefix("plan summary: "))


def _import_rows(tmp_path: Path, rows_text: str, *args: str) -> str:
    path = tmp_path / f"subset-{hashlib.sha256(rows_text.encode()).hexdigest()[:12]}.json"
    path.write_text(rows_text, encoding="utf-8")
    out = io.StringIO()
    call_command(
        "import_shrines_seed",
        "--source",
        str(path),
        "--skip-goriyaku-tags",
        *args,
        stdout=out,
        stderr=io.StringIO(),
    )
    return out.getvalue()


def _import_base_subset(tmp_path: Path, *args: str) -> str:
    module = _extractor()
    rows = json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))
    return _import_rows(tmp_path, module.render(module.extract_subset(rows)), *args)


def _import_knowledge(cid: str, *args: str) -> str:
    out = io.StringIO()
    call_command(
        "import_shrine_knowledge",
        str(KNOWLEDGE_SEED_DIR / f"nsrc_{cid}_seed.json"),
        *args,
        stdout=out,
        stderr=io.StringIO(),
    )
    return out.getvalue()


# --------------------------------------------------------------------------------------
# simulated exact Production P0（aggregate を実測値と完全一致させる。frozen 値は変えない）
# --------------------------------------------------------------------------------------


def _filler_owner() -> Shrine:
    return Shrine.objects.get(name_jp=FILLER_OWNER, address=FILLER_ADDRESS)


def _target_keys() -> set[tuple[str, str]]:
    return {CANDIDATES[cid][:2] for cid in ORDER}


def _removable_shrines():
    """Base rows that are neither a target nor the filler owner and own nothing."""
    ids = [
        s.pk
        for s in Shrine.objects.exclude(name_jp=FILLER_OWNER).order_by("-id")
        if (s.name_jp, s.address) not in _target_keys()
        and not s.name_jp.startswith("G7cohort")
        and s.name_jp != NUNAKAWA_SHRINE
        and s.name_jp not in {CANDIDATES[cid][0] for cid in ORDER}
    ]
    return Shrine.objects.filter(pk__in=ids).order_by("-id")


def _filler_sources():
    return ShrineKnowledgeSource.objects.filter(
        url__startswith=FILLER_URL, title__startswith="filler"
    )


def _filler_citation(index: int) -> None:
    history = ShrineHistory.objects.create(
        shrine=_filler_owner(),
        history_type="tradition",
        title=f"citation filler history {index}",
        content="filler",
    )
    source = ShrineKnowledgeSource.objects.create(
        source_type="internal_research",
        title=f"citation filler source {index}",
        url=f"{FILLER_URL}citation/{index}",
    )
    history.sources.add(source)
    ShrineFactSourceCitation.objects.create(
        shrine_history=history, source=source, locator_text=f"p.{index}"
    )


def _rebalance(expected: dict[str, int]) -> None:
    """Add or remove unrelated filler rows until every aggregate equals `expected`."""
    owner = _filler_owner()
    counter = {"n": 0}

    def tag() -> str:
        counter["n"] += 1
        return f"{timezone.now().timestamp()}-{counter['n']}"

    while ShrineFactSourceCitation.objects.count() < expected["citation"]:
        _filler_citation(ShrineFactSourceCitation.objects.count() + 1000)
    while ShrineFactSourceCitation.objects.count() > expected["citation"]:
        ShrineFactSourceCitation.objects.order_by("-id").first().delete()

    diff = expected["shrine"] - Shrine.objects.count()
    for _ in range(diff):
        Shrine.objects.create(
            name_jp=f"G7cohort追加{tag()}", kind="shrine", address=f"架空県{tag()}"
        )
    if diff < 0:
        Shrine.objects.filter(
            pk__in=list(_removable_shrines().values_list("pk", flat=True)[:-diff])
        ).delete()

    def balance(model, key: str, make, removable) -> None:
        diff = expected[key] - model.objects.count()
        if diff > 0:
            model.objects.bulk_create(make(i) for i in range(diff))
        elif diff < 0:
            model.objects.filter(
                pk__in=list(removable.order_by("-id").values_list("pk", flat=True)[:-diff])
            ).delete()

    balance(
        ShrineKnowledgeSource,
        "source",
        lambda i: ShrineKnowledgeSource(
            source_type="internal_research",
            title=f"filler source {tag()}",
            url=f"{FILLER_URL}{tag()}",
        ),
        _filler_sources(),
    )
    balance(
        ShrineDeity,
        "deity",
        lambda i: ShrineDeity(shrine=owner, display_name=f"filler deity {tag()}"),
        ShrineDeity.objects.filter(shrine=owner, display_name__startswith="filler"),
    )
    balance(
        ShrineHistory,
        "history",
        lambda i: ShrineHistory(
            shrine=owner,
            history_type="tradition",
            title=f"filler history {tag()}",
            content="filler",
        ),
        ShrineHistory.objects.filter(shrine=owner, title__startswith="filler"),
    )
    balance(
        ShrineSourceFact,
        "source_fact",
        lambda i: ShrineSourceFact(
            shrine=owner,
            stable_key=f"g7-cohort-filler-{tag()}",
            source_attested_wording="filler",
            evidence_characterization="official_prayer_supported",
        ),
        ShrineSourceFact.objects.filter(shrine=owner),
    )
    balance(
        ShrineDeityCollective,
        "collective",
        lambda i: ShrineDeityCollective(shrine=owner, source_attested_label=f"filler {tag()}"),
        ShrineDeityCollective.objects.filter(shrine=owner),
    )
    assert _aggregates() == expected


def _simulate_production_p0() -> None:
    """Base Seed minus the four targets, one row swapped for the filler owner, then fillers."""
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    for name, address in _target_keys():
        Shrine.objects.filter(name_jp=name, address=address).delete()
    _removable_shrines().first().delete()
    Shrine.objects.create(name_jp=FILLER_OWNER, kind="shrine", address=FILLER_ADDRESS)
    _rebalance(PRODUCTION_P0)
    for cid in ORDER:
        name, address = CANDIDATES[cid][:2]
        assert Shrine.objects.filter(address=address).count() == 0
        assert Shrine.objects.filter(name_jp=name).count() == 0


def _build(stage: str, tmp_path: Path) -> None:
    _simulate_production_p0()
    if stage != "P0":
        _import_base_subset(tmp_path)
    for cid in COMPLETED[stage]:
        _import_knowledge(cid)
    assert _aggregates() == CHECKPOINTS[stage]


# --------------------------------------------------------------------------------------
# 1. SQL file contract
# --------------------------------------------------------------------------------------


def test_cohort_guard_file_set_is_explicit_and_read_only():
    paths = sorted(p.name for p in SQL_DIR.glob("niigata_vpg001_g7_*.sql"))
    assert paths == sorted(GUARD_FILES.values())
    is_readonly_sql = _load("_vpg001_cohort_guard", "guard.py").is_readonly_sql
    for name in GUARD_FILES.values():
        text = _sql(name)
        ok, reason = is_readonly_sql(text)
        assert ok, (name, reason)
        lowered = text.lower()
        for token in ("postgres://", "postgresql://", "password", "sslmode", "@localhost"):
            assert token not in lowered, (name, token)
        statements = _statements(text)
        assert len(statements) == 5, name
        for statement in statements:
            assert re.match(r"^with\b", statement, re.IGNORECASE), name
            for verb in ("insert", "update", "delete", "truncate", "alter", "drop", "create"):
                assert not re.search(rf"\b{verb}\b", statement, re.IGNORECASE), (name, verb)
            # fail closed: every statement is a division-by-zero assertion over one row
            assert re.search(r"^SELECT 1 / CASE WHEN \($", statement, re.MULTILINE), name
            assert statement.rstrip().endswith(("FROM frozen f", "CROSS JOIN checkpoint c"))
        # no runtime parameter that could weaken a guard（authority blocks are checked byte-equal
        # to #3279 separately; their regex literals contain ':' and '$'）
        own = text
        for cid in ORDER:
            for kind in ("source_identity", "target_facts"):
                own = own.replace(_authority_block(cid, kind), "")
        own = "\n".join(_statements(own))
        assert not re.search(r"(?<!:):[A-Za-z_'\"]|\$\d|current_setting", own), name
        assert not re.search(r"^\s*\\", text, re.MULTILINE), name  # no psql meta-command


def test_frozen_block_is_single_measured_p0_in_every_statement():
    blocks = [block for name in GUARD_FILES.values() for block in FROZEN_RE.findall(_sql(name))]
    assert len(blocks) == 6 * 5
    assert len(set(blocks)) == 1
    text = blocks[0]
    assert "    true AS frozen_values_set,\n" in text
    assert "NULL" not in text and "UNSET" not in text
    values = re.findall(r"^\s+(\d+)::bigint AS (\w+)", text, re.MULTILINE)
    expected = [(str(PRODUCTION_P0[key]), f"{key}_total") for key in AGGREGATE_TABLES]
    for cid in ORDER:
        expected += [
            ("0", f"nsrc_{cid}_same_name_other_address_total"),
            ("0", f"nsrc_{cid}_accepted_source_count"),
            ("0", f"nsrc_{cid}_foreign_fact_source_relation_total"),
        ]
    assert values == expected
    assert "MEASURED = Stage P0 only" in text
    assert "PostgreSQL 17.6 / server_version_num 170006" in text
    assert PRODUCTION_LATEST_TEMPLES_MIGRATION in text
    assert str(PRODUCTION_SERVER_VERSION_NUM) in text


def test_stage_checkpoints_are_derived_from_p0_plus_repository_payload():
    expected_final = {**PRODUCTION_P0, "shrine": 133}
    for cid in ORDER:
        for key, value in _payload(cid).items():
            expected_final[key] += value
    assert expected_final == CHECKPOINTS["P5"] == _stage(133, 149, 303, 244)
    assert [_payload(cid) for cid in ORDER] == [
        {"source": 1, "deity": 1, "history": 1},
        {"source": 1, "deity": 1, "history": 0},
        {"source": 1, "deity": 3, "history": 2},
        {"source": 1, "deity": 3, "history": 5},
    ]
    for stage in STAGES:
        derived = dict(PRODUCTION_P0)
        if stage != "P0":
            derived["shrine"] += 4
        for cid in COMPLETED[stage]:
            for key, value in _payload(cid).items():
                derived[key] += value
        assert derived == CHECKPOINTS[stage], stage

        (block,) = CHECKPOINT_RE.findall(_sql(GUARD_FILES[stage]))
        assert f"    '{stage}'::text AS stage,\n" in block
        values = dict(
            (name, int(value))
            for value, name in re.findall(r"^\s+(\d+)::bigint AS (\w+)", block, re.MULTILINE)
        )
        for key in AGGREGATE_TABLES:
            assert values[f"{key}_total"] == CHECKPOINTS[stage][key], (stage, key)
            assert values[f"{key}_delta"] == CHECKPOINTS[stage][key] - PRODUCTION_P0[key]
        if stage == "P0":
            assert "MEASURED Production pre-state" in block
        else:
            # P1-P5 are never labelled as Production measurements
            assert "DERIVED / EXPECTED cumulative checkpoint, NOT a Production measurement" in block
            assert "MEASURED" not in block
            assert "DERIVED / EXPECTED cumulative checkpoint" in _sql(GUARD_FILES[stage])[:800]


def test_cohort_statement_checks_aggregates_and_schema_contract():
    for stage in STAGES:
        section = _statement_sections(_sql(GUARD_FILES[stage]))[1]
        conditions = _conditions(section)
        for key, table in AGGREGATE_TABLES.items():
            assert f"  AND c.{key}_total = f.{key}_total + c.{key}_delta" in conditions
            assert f"  AND (SELECT COUNT(*) FROM {table}) = c.{key}_total" in conditions
        for table in (
            "temples_shrine",
            "temples_shrineknowledgesource",
            "temples_shrinedeity",
            "temples_shrinedeity_sources",
            "temples_shrinehistory",
            "temples_shrinehistory_sources",
            "temples_shrinefactsourcecitation",
            "temples_shrinesourcefact",
            "temples_shrinedeitycollective",
            "temples_shrine_goriyaku_tags",
            "temples_shrinegoriyakuassignment",
        ):
            assert f"  AND to_regclass('public.{table}') IS NOT NULL" in conditions
        assert "  f.frozen_values_set" in conditions
        assert f"  AND c.stage = '{stage}'" in conditions


def test_candidate_statements_reuse_the_3279_authority_without_loosening():
    for stage in STAGES:
        sections = _statement_sections(_sql(GUARD_FILES[stage]))
        assert sorted(sections) == [1, 2, 3, 4, 5]
        for number, cid in enumerate(ORDER, start=2):
            section = sections[number]
            state = _state(stage, cid)
            assert section.startswith(f"-- Statement {number} / 5: nsrc-{cid} = {state}")
            for kind in ("source_identity", "target_facts"):
                block = _authority_block(cid, kind)
                assert section.count(block) == 1, (stage, cid, kind)
            for other in ORDER:
                if other != cid:
                    assert f"nsrc_{other}_source_identity" not in section
                    assert f"nsrc_{other}_target_facts" not in section
            assert _conditions(section) == _authority_conditions(cid, state), (stage, cid)
            # the measured accepted count is asserted, never the looser IN (0, 1)
            assert f"  AND f.nsrc_{cid}_accepted_source_count = 0" in _conditions(section)
            assert "IN (0, 1)" not in "\n".join(_conditions(section))


def test_3279_candidate_guards_stay_unset_and_are_not_fake_baselines():
    for cid in ORDER:
        for kind in ("pre_base_guard", "post_base_guard", "post_knowledge_verification"):
            text = _sql(f"nsrc_{cid}_g7_{kind}.sql")
            assert "    false AS frozen_values_set,\n" in text
            assert "FROZEN_PRE_STATE: UNSET." in text


# --------------------------------------------------------------------------------------
# 2. Disposable sequential cohort rehearsal（committed guards, simulated exact P0）
# --------------------------------------------------------------------------------------


def _knowledge_plans(cid: str) -> tuple[dict, dict]:
    payload = _payload(cid)
    first = {"source_CREATE": 1}
    second = {"source_REUSE_EXISTING": 1}
    for kind in ("deity", "history"):
        if payload[kind]:
            first[f"{kind}_CREATE"] = payload[kind]
            second[f"{kind}_SKIP_EXISTS"] = payload[kind]
    return first, second


@pytest.mark.django_db
def test_committed_guards_fail_closed_on_a_non_production_state(tmp_path):
    # the plain repository lineage differs from the Production measurement: every stage fails
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    assert _aggregates() != PRODUCTION_P0
    assert _passing_stages() == set()
    for cid in ORDER:
        _import_knowledge(cid)
    assert _passing_stages() == set()


@pytest.mark.django_db
def test_sequential_cohort_rehearsal(tmp_path):
    _simulate_production_p0()
    goriyaku_before = _goriyaku_snapshot()

    # P0 frozen pre-Base guard
    assert _aggregates() == CHECKPOINTS["P0"]
    assert _passing_stages() == {"P0"}

    # 4-row Base subset: dry-run -> apply -> second dry-run / apply（idempotency）
    assert "created=4 updated=0 skipped=0 total_seed=4" in _import_base_subset(
        tmp_path, "--dry-run"
    )
    assert _aggregates() == CHECKPOINTS["P0"]
    assert "created=4 updated=0 skipped=0 total_seed=4" in _import_base_subset(tmp_path)
    assert _passing_stages() == {"P1"}
    base_rows = tuple(Shrine.objects.order_by("id").values_list())
    assert "created=0 updated=0 skipped=4 total_seed=4" in _import_base_subset(
        tmp_path, "--dry-run"
    )
    assert "created=0 updated=0 skipped=4 total_seed=4" in _import_base_subset(tmp_path)
    assert tuple(Shrine.objects.order_by("id").values_list()) == base_rows
    assert _passing_stages() == {"P1"}
    assert _goriyaku_snapshot()[:3] == goriyaku_before[:3]

    for index, cid in enumerate(ORDER):
        stage = STAGES[index + 2]
        first_plan, second_plan = _knowledge_plans(cid)
        before = _fact_snapshot()
        assert "validate-only: OK, no errors" in _import_knowledge(cid, "--validate-only")
        dry = _import_knowledge(cid, "--dry-run")
        assert _plan_summary(dry) == first_plan
        assert _fact_snapshot() == before
        applied = _import_knowledge(cid)
        assert _plan_summary(applied) == first_plan
        payload = _payload(cid)
        assert (
            f"import complete: sources created=1, deities created={payload['deity']}, "
            f"histories created={payload['history']}, collectives created=0, "
            "memberships created=0, source_facts created=0"
        ) in applied
        assert _aggregates() == CHECKPOINTS[stage]
        assert _passing_stages() == {stage}

        # previously imported candidates stay byte / field-equivalent
        after = _fact_snapshot()
        for part_before, part_after in zip(before, after, strict=True):
            assert part_after[: len(part_before)] == part_before

        # idempotency: second import creates nothing and changes nothing
        second = _import_knowledge(cid)
        assert _plan_summary(second) == second_plan
        assert "CREATE" not in second
        assert _fact_snapshot() == after
        assert _aggregates() == CHECKPOINTS[stage]
        assert _passing_stages() == {stage}

        source = _source(cid)
        for fact in _facts(cid):
            assert list(fact.sources.all()) == [source]

    # final P5: rerunning all four Knowledge imports preserves P5 exactly
    final = _fact_snapshot()
    for cid in ORDER:
        rerun = _import_knowledge(cid)
        assert "CREATE" not in rerun
    assert _fact_snapshot() == final
    assert _aggregates() == CHECKPOINTS["P5"] == _stage(133, 149, 303, 244)
    assert _passing_stages() == {"P5"}
    assert _goriyaku_snapshot()[:3] == goriyaku_before[:3]
    for cid in ORDER:
        assert _target(cid).goriyaku == ""
        assert not ShrineDeity.objects.filter(
            shrine=_target(cid), display_name__in=NUNAKAWA_DEITIES
        )


# --------------------------------------------------------------------------------------
# 3. Mutation / negative matrix（every stage fails closed）
# --------------------------------------------------------------------------------------


def _last_completed(stage: str) -> str:
    return COMPLETED[stage][-1]


def _next_candidate(stage: str) -> str:
    return ORDER[len(COMPLETED[stage])]


def _other_source() -> ShrineKnowledgeSource:
    return ShrineKnowledgeSource.objects.create(
        source_type="internal_research", title="other", url="https://example.invalid/other"
    )


def _import_single_base(tmp_path: Path, cid: str) -> None:
    module = _load(f"nsrc_{cid}_g7_extract_base_subset", f"nsrc_{cid}_g7_extract_base_subset.py")
    _import_rows(tmp_path, module.render(module.extract_subset()))


def _remove_knowledge(cid: str) -> None:
    for fact in _facts(cid):
        fact.delete()
    _source(cid).delete()


def _assignment(shrine: Shrine) -> None:
    ShrineGoriyakuAssignment.objects.create(
        shrine=shrine,
        canonical_key="goriyaku:misfortune_warding",
        taxonomy_version="v1",
        lifecycle=ShrineGoriyakuAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=timezone.now(),
    )


def _drifted_source(cid: str) -> None:
    stype, _, normalized = CANDIDATES[cid][4:]
    ShrineKnowledgeSource.objects.create(
        source_type=stype, title="drift", url=normalized, publisher="別の発行者"
    )


def _aggregate_drift(key: str):
    """One extra unrelated row of `key`; every other aggregate stays at the checkpoint."""
    return lambda stage, tmp: _rebalance({**CHECKPOINTS[stage], key: CHECKPOINTS[stage][key] + 1})


# mutation -> (stages it applies to, function(stage, tmp_path), rebalance to the checkpoint?)
ALL = STAGES
AFTER_BASE = STAGES[1:]
WITH_KNOWLEDGE = STAGES[2:]
MUTATIONS = {
    **{
        f"aggregate-drift-{key}": (
            ALL,
            _aggregate_drift(key),
            False,
        )
        for key in AGGREGATE_TABLES
    },
    "early-base-import": (
        ("P0",),
        lambda stage, tmp: _import_single_base(tmp, "000021"),
        True,
    ),
    "early-knowledge-import": (
        STAGES[1:5],
        lambda stage, tmp: _import_knowledge(_next_candidate(stage)),
        True,
    ),
    "expected-base-missing": (
        ("P1",),
        lambda stage, tmp: _target("000025").delete(),
        True,
    ),
    "expected-knowledge-missing": (
        WITH_KNOWLEDGE,
        lambda stage, tmp: _remove_knowledge(_last_completed(stage)),
        True,
    ),
    "extra-fact": (
        AFTER_BASE,
        lambda stage, tmp: ShrineDeity.objects.create(
            shrine=_target(COMPLETED[stage][-1] if COMPLETED[stage] else "000021"),
            display_name="G7余分祭神",
        ),
        True,
    ),
    "missing-fact": (
        WITH_KNOWLEDGE,
        lambda stage, tmp: _facts(_last_completed(stage))[-1].delete(),
        True,
    ),
    "wrong-source-relation": (
        WITH_KNOWLEDGE,
        lambda stage, tmp: _facts(_last_completed(stage))[0].sources.set([_other_source()]),
        True,
    ),
    "extra-source-relation": (
        WITH_KNOWLEDGE,
        lambda stage, tmp: _facts(_last_completed(stage))[0].sources.add(_other_source()),
        True,
    ),
    "source-metadata-drift": (
        WITH_KNOWLEDGE,
        lambda stage, tmp: ShrineKnowledgeSource.objects.filter(
            pk=_source(_last_completed(stage)).pk
        ).update(publisher="別の発行者"),
        True,
    ),
    "source-identity-appears-early": (
        STAGES[:5],
        lambda stage, tmp: _drifted_source(_next_candidate(stage)),
        True,
    ),
    "coordinate-drift": (
        AFTER_BASE,
        lambda stage, tmp: Shrine.objects.filter(pk=_target("000024").pk).update(
            latitude=CANDIDATES["000024"][2] + 0.0001
        ),
        True,
    ),
    "goriyaku-text": (
        AFTER_BASE,
        lambda stage, tmp: Shrine.objects.filter(pk=_target("000022").pk).update(goriyaku="縁結び"),
        True,
    ),
    "goriyaku-tag": (
        AFTER_BASE,
        lambda stage, tmp: _target("000021").goriyaku_tags.add(
            GoriyakuTag.objects.create(name="G7cohortタグ")
        ),
        True,
    ),
    "goriyaku-assignment": (
        AFTER_BASE,
        lambda stage, tmp: _assignment(_target("000025")),
        True,
    ),
    "cross-candidate-fact-owner": (
        WITH_KNOWLEDGE,
        lambda stage, tmp: (
            type(fact := _facts(_last_completed(stage))[0])
            .objects.filter(pk=fact.pk)
            .update(shrine=_target("000025" if _last_completed(stage) != "000025" else "000021"))
        ),
        True,
    ),
    "cross-candidate-source-relation": (
        STAGES[3:],
        lambda stage, tmp: _facts(COMPLETED[stage][-1])[0].sources.add(
            _source(COMPLETED[stage][0])
        ),
        True,
    ),
    "same-name-other-address": (
        ALL,
        lambda stage, tmp: Shrine.objects.create(
            name_jp=CANDIDATES["000024"][0], kind="shrine", address="新潟県架空市1-1"
        ),
        True,
    ),
    "same-address-other-name": (
        ALL,
        lambda stage, tmp: Shrine.objects.create(
            name_jp="G7cohort別名神社", kind="shrine", address=CANDIDATES["000022"][1]
        ),
        True,
    ),
    "nunakawa-shrine-at-000025-address": (
        ALL,
        lambda stage, tmp: Shrine.objects.create(
            name_jp=NUNAKAWA_SHRINE, kind="shrine", address=CANDIDATES["000025"][1]
        ),
        True,
    ),
    "nunakawa-deity-on-000025": (
        AFTER_BASE,
        lambda stage, tmp: ShrineDeity.objects.create(
            shrine=_target("000025"), display_name=NUNAKAWA_DEITIES[0]
        ),
        True,
    ),
    "nunakawa-deity-renamed-from-000025-fact": (
        ("P5",),
        lambda stage, tmp: ShrineDeity.objects.filter(
            shrine=_target("000025"), display_name="天太玉命"
        ).update(display_name=NUNAKAWA_DEITIES[1]),
        True,
    ),
    "nunakawa-fact-related-to-000025-source": (
        ("P5",),
        lambda stage, tmp: ShrineDeity.objects.create(
            shrine=_filler_owner(), display_name=NUNAKAWA_DEITIES[0]
        ).sources.add(_source("000025")),
        True,
    ),
}
CASES = [(stage, name) for name, (stages, _, _) in sorted(MUTATIONS.items()) for stage in stages]


@pytest.mark.django_db
@pytest.mark.parametrize(("stage", "mutation"), CASES, ids=[f"{s}-{m}" for s, m in CASES])
def test_every_stage_guard_fails_closed(tmp_path, stage, mutation):
    _build(stage, tmp_path)
    assert _passing_stages() == {stage}
    _, mutate, rebalance = MUTATIONS[mutation]
    mutate(stage, tmp_path)
    if rebalance:
        # count-preserving: the cohort checkpoint still holds, a candidate statement rejects it
        _rebalance(CHECKPOINTS[stage])
        assert _aggregates() == CHECKPOINTS[stage]
        failing = _failing_statements(stage)
        assert failing and 1 not in failing, failing
    else:
        assert _aggregates() != CHECKPOINTS[stage]
        assert _failing_statements(stage) == {1}
    assert _committed_guard_passes(stage) is False


def test_mutation_matrix_covers_every_stage():
    for stage in STAGES:
        names = {name for s, name in CASES if s == stage}
        assert {f"aggregate-drift-{key}" for key in AGGREGATE_TABLES} <= names
        assert "same-address-other-name" in names and "nunakawa-shrine-at-000025-address" in names
        assert names & {"early-base-import", "early-knowledge-import"} or stage == "P5"
        if stage != "P0":
            assert {
                "coordinate-drift",
                "goriyaku-text",
                "goriyaku-tag",
                "goriyaku-assignment",
            } <= names
            assert names & {"expected-base-missing", "expected-knowledge-missing"}
        if stage in WITH_KNOWLEDGE:
            assert {
                "extra-fact",
                "missing-fact",
                "wrong-source-relation",
                "source-metadata-drift",
                "cross-candidate-fact-owner",
            } <= names


# --------------------------------------------------------------------------------------
# 4. 4-row cohort Base subset
# --------------------------------------------------------------------------------------

SUBSET_SHA256 = "7dafa5e1243c50b0c46a5a4f02762e533326b0fac956acc7dfe979b182691c03"


def test_extractor_composes_exactly_the_four_canonical_rows_deterministically():
    module = _extractor()
    rows = json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))
    first = module.render(module.extract_subset(rows))
    second = module.render(module.extract_subset(copy.deepcopy(rows)))
    assert first == second
    assert hashlib.sha256(first.encode("utf-8")).hexdigest() == SUBSET_SHA256
    subset = json.loads(first)
    assert len(subset) == 4
    assert module.TARGET_IDS == tuple(f"nsrc-{cid}" for cid in ORDER)
    for row, cid in zip(subset, ORDER, strict=True):
        name, address, lat, lng = CANDIDATES[cid][:4]
        authority = _load(
            f"nsrc_{cid}_g7_extract_base_subset", f"nsrc_{cid}_g7_extract_base_subset.py"
        )
        assert row == authority.EXPECTED_ROW
        assert (row["name_jp"], row["address"]) == (name, address)
        assert (row["latitude"], row["longitude"]) == (lat, lng)
        assert row["location"] == {"lat": lat, "lng": lng}
        assert (row["goriyaku"], row["kyusei"], row["astro_elements"]) == ("", None, [])


def test_full_base_seed_is_never_the_production_payload():
    module = _extractor()
    full = json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))
    subset = module.extract_subset(full)
    assert len(full) == 133 and len(subset) == 4
    others = [r for r in full if (r["name_jp"], r["address"]) not in _target_keys()]
    assert len(others) == 129
    assert all(row not in subset for row in others)
    assert module.BASE_SEED_PATH == BASE_SEED_PATH


def test_extractor_fails_closed_on_missing_duplicate_drifted_or_foreign_target():
    module = _extractor()
    rows = json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))
    for cid in ORDER:
        name, address, lat, lng = CANDIDATES[cid][:4]
        missing = [r for r in rows if (r["name_jp"], r["address"]) != (name, address)]
        with pytest.raises(module.SubsetBlocked, match="exactly 1"):
            module.extract_subset(missing)
        duplicated = [*rows, copy.deepcopy(module.EXPECTED_ROWS[f"nsrc-{cid}"])]
        with pytest.raises(module.SubsetBlocked, match="exactly 1"):
            module.extract_subset(duplicated)
        for field, value in (
            ("latitude", lat + 0.0001),
            ("longitude", lng + 0.0001),
            ("location", {"lat": lat, "lng": lng + 0.0001}),
            ("goriyaku", "縁結び"),
            ("kyusei", "一白水星"),
            ("astro_elements", ["火"]),
        ):
            drifted = copy.deepcopy(rows)
            for row in drifted:
                if (row["name_jp"], row["address"]) == (name, address):
                    row[field] = value
            with pytest.raises(module.SubsetBlocked, match="differs"):
                module.extract_subset(drifted)
    for requested in (
        ("nsrc-000021", "nsrc-000022", "nsrc-000024"),
        ("nsrc-000022", "nsrc-000021", "nsrc-000024", "nsrc-000025"),
        ("nsrc-000021", "nsrc-000022", "nsrc-000023", "nsrc-000024", "nsrc-000025"),
    ):
        with pytest.raises(module.SubsetBlocked):
            module.extract_subset(rows, requested)
    with pytest.raises(module.SubsetBlocked, match="exactly 4"):
        module.render(module.extract_subset(rows)[:3])
    with pytest.raises(module.SubsetBlocked, match="order"):
        module.render(list(reversed(module.extract_subset(rows))))


def test_extractor_fails_closed_when_the_frozen_coordinate_cross_check_drifts(monkeypatch):
    module = _extractor()
    rows = json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))
    monkeypatch.setitem(module.FROZEN_G2_COORDINATES, "nsrc-000025", (37.0397729, 137.8644154))
    with pytest.raises(module.SubsetBlocked, match="frozen G2 coordinate"):
        module.extract_subset(rows)


def test_extractor_refuses_repository_output_and_existing_files(tmp_path, capsys):
    module = _extractor()
    assert module.main(["--output", str(REPO_ROOT / "vpg001_subset.json")]) == 1
    assert not (REPO_ROOT / "vpg001_subset.json").exists()
    output = tmp_path / "subset.json"
    assert module.main(["--output", str(output)]) == 0
    out = capsys.readouterr().out
    assert "SUBSET_ROWS=4" in out
    assert "candidate_ids=nsrc-000021,nsrc-000022,nsrc-000024,nsrc-000025" in out
    assert f"SUBSET_SHA256={SUBSET_SHA256}" in out
    assert module.main(["--output", str(output)]) == 1
    assert module.main(["--output", str(output), "--overwrite"]) == 0


def test_extractor_has_no_db_or_network_access():
    text = (SAFETY_DIR / "niigata_vpg001_g7_extract_base_subset.py").read_text(encoding="utf-8")
    for token in ("django", "psycopg", "socket", "requests", "urllib", "subprocess", "environ"):
        assert token not in text
    # the one-row extractors stay in place as the row authority
    for cid in ORDER:
        assert (SAFETY_DIR / f"nsrc_{cid}_g7_extract_base_subset.py").exists()


# --------------------------------------------------------------------------------------
# 5. Final Runtime QA rehearsal on P5（READ ONLY transaction）
# --------------------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_final_runtime_qa_rehearsal_on_p5(tmp_path, capsys):
    _build("P5", tmp_path)
    assert _passing_stages() == {"P5"}
    for cid in ORDER:
        module = _load(f"nsrc_{cid}_g7_runtime_qa", f"nsrc_{cid}_g7_runtime_qa.py")
        capsys.readouterr()
        module.main()
        out = capsys.readouterr().out
        for line in (
            "TARGET_IDENTITY=PASS",
            "SOURCE_RELATION_INTEGRITY=PASS",
            "GORIYAKU_ISOLATION=PASS",
            "FACT_OWNERSHIP_ISOLATION=PASS",
            "AGGREGATES_UNCHANGED=PASS",
            "G7_PRODUCTION_RUNTIME_QA=PASS",
            "TRANSACTION_MODE=READ_ONLY",
        ):
            assert line in out, (cid, line)
    assert _aggregates() == CHECKPOINTS["P5"]
    assert _passing_stages() == {"P5"}
