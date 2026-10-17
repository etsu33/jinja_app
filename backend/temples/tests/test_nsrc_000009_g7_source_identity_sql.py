"""nsrc-000009 赤城社 G7 Production Import preflight regression（disposable test DB only）。

scripts/migration_safety/sql/nsrc_000009_g7_*.sql は同一の `nsrc_000009_source_identity` block を持ち、
shared municipal Source（TOKAMACHI_REKIBUN_SHIRYOU）を importer semantic identity（source_type +
knowledge_seed.normalize_source_url()）として数える。近似一致は使わない。Fact locator は
ShrineFactSourceCitation.locator_text（中魚沼郡誌上 p.445）で、Source.bibliography（legacy p.398）ではない。

guard（pre-Base / post-Base / post-Knowledge）の FROZEN_PRE_STATE は、PR #3237 / temples 0121 Gate の後に
Mother Ship が Production で read-only 実行した nsrc_000009_g7_preflight.sql の実測値（PRODUCTION_PRESTATE）で
固定済み（CLEAN_CREATE / shared Source REUSABLE）。

- committed guard は、PRODUCTION_PRESTATE と aggregate を完全一致させた disposable DB の simulated
  pre-state に対してそのまま（frozen 値を変えずに）実行し、sequential rehearsal / drift / negative を検証する。
- Source-state / 状態分類の matrix は、test 内メモリ上で frozen block を disposable DB の実測値へ置き換えて
  検証する。
commit された SQL / Seed / DB 定義は変更しない。Production には接続しない。

通常 lineage（Production で nsrc-000007 が materialize 済み）を再現するときは、nsrc-000007 Knowledge Seed を
先に import して shared Source を作る。ただしそれは Production の状態を仮定するものではない。
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
from django.db.migrations.recorder import MigrationRecorder

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
KNOWLEDGE_SEED_PATH = DATA_DIR / "knowledge_seeds" / "nsrc_000009_seed.json"
LEGACY_KNOWLEDGE_SEED_PATH = DATA_DIR / "knowledge_seeds" / "nsrc_000007_seed.json"

PREFLIGHT = "nsrc_000009_g7_preflight.sql"
BACKUP_VERSION_CHECK = "nsrc_000009_g7_backup_version_check.sql"
PRE_BASE = "nsrc_000009_g7_pre_base_guard.sql"
POST_BASE = "nsrc_000009_g7_post_base_guard.sql"
POST_KNOWLEDGE = "nsrc_000009_g7_post_knowledge_verification.sql"
IDENTITY_FILES = (PREFLIGHT, PRE_BASE, POST_BASE, POST_KNOWLEDGE)
GUARD_FILES = (PRE_BASE, POST_BASE, POST_KNOWLEDGE)
ALL_SQL_FILES = (PREFLIGHT, BACKUP_VERSION_CHECK, PRE_BASE, POST_BASE, POST_KNOWLEDGE)
BLOCK_RE = re.compile(
    r"-- BEGIN nsrc_000009_source_identity\n(.*?)-- END nsrc_000009_source_identity\n",
    re.DOTALL,
)
TARGET_RE = re.compile(
    r"-- BEGIN nsrc_000009_target_facts\n(.*?)-- END nsrc_000009_target_facts\n",
    re.DOTALL,
)
FROZEN_RE = re.compile(
    r"-- BEGIN nsrc_000009_frozen_pre_state\n(.*?)-- END nsrc_000009_frozen_pre_state\n",
    re.DOTALL,
)
# Mother Ship が Production で read-only 実行した nsrc_000009_g7_preflight.sql の実測値。
PRODUCTION_PRESTATE = {
    "shrine_total": 124,
    "source_total": 145,
    "deity_total": 295,
    "history_total": 234,
    "citation_total": 0,
    "source_fact_total": 34,
    "collective_total": 6,
    "same_name_other_address_total": 1,
    "accepted_shared_source_count": 1,
}
AGGREGATE_KEYS = {
    "shrine": "shrine_total",
    "source": "source_total",
    "deity": "deity_total",
    "history": "history_total",
    "citation": "citation_total",
    "source_fact": "source_fact_total",
    "collective": "collective_total",
}
PRODUCTION_AGGREGATES = {key: PRODUCTION_PRESTATE[name] for key, name in AGGREGATE_KEYS.items()}
# Approved expected Production delta: Shrine +1 / Source +0 / History +2 / Citation +2, others +0.
EXPECTED_POST_BASE = {**PRODUCTION_AGGREGATES, "shrine": 125}
EXPECTED_POST_KNOWLEDGE = {
    **PRODUCTION_AGGREGATES,
    "shrine": 125,
    "source": 145,
    "history": 236,
    "citation": 2,
}
FROZEN_NAMES = [
    "shrine_total",
    "source_total",
    "deity_total",
    "history_total",
    "citation_total",
    "source_fact_total",
    "collective_total",
    "same_name_other_address_total",
    "accepted_shared_source_count",
]

SHRINE_NAME = "赤城社"
SHRINE_ADDRESS = "新潟県十日町市伊達乙48番地"
SHRINE_LAT = 37.089683
SHRINE_LNG = 138.748108
# nsrc-000007（G7 CLOSED）: same name, different shrine
LEGACY_AKAGI_ADDRESS = "新潟県十日町市四日町2534番地"
OTHER_AKAGI_ADDRESSES = (
    "新潟県十日町市上組2059番地子",
    "新潟県南魚沼市芹田79番地",
)

SOURCE = {
    "type": "government",
    "url": "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf",
    "normalized": "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf",
    "publisher": "十日町市",
    "bibliography": "中魚沼郡誌上 p.398",
    "title": "歴史文化基本構想 資料集",
}
LOCATOR = "中魚沼郡誌上 p.445"
H1_TITLE = "天明3年8月の創立記録"
H2_TITLE = "大正2年の改築記録"
LEGACY_H1_TITLE = "安政7年正月の再建"

# importer と同じ semantic identity になる表記揺れ
IDENTITY_VARIANTS = (
    SOURCE["url"],
    "HTTPS://WWW.CITY.TOKAMACHI.LG.JP/material/files/group/31/rekibun_shiryou.pdf",
    "https://www.city.tokamachi.lg.jp:443/material/files/group/31/rekibun_shiryou.pdf",
    "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf/",
    "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf#page=445",
    "  https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf  ",
    "https://u:p@www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf",
)
# importer の identity ではないが、lookalike 診断には必ず拾われる表記（再利用不可）
NON_IDENTITY_LOOKALIKE_VARIANTS = (
    "http://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf",
    "https://city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf",
    "https://www.city.tokamachi.lg.jp/material/files/group/32/rekibun_shiryou.pdf",
    "https://www.city.tokamachi.lg.jp/material/files/group/31/Rekibun_Shiryou.pdf",
    "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf?page=445",
    "https://www.city.tokamachi.lg.jp:8443/material/files/group/31/rekibun_shiryou.pdf",
)
# importer が ValueError で停止する URL（SQL は NULL = identity にならない）
IMPORTER_UNPARSEABLE = (
    "https://www.city.tokamachi.lg.jp:abc/material/files/group/31/rekibun_shiryou.pdf",
    "https://www.city.tokamachi.lg.jp:99999/material/files/group/31/rekibun_shiryou.pdf",
)
GENERAL_CORPUS = (
    "",
    "   ",
    "/",
    "https://example.com",
    "https://Example.com:8080/a/B/?Q=1&q=2#frag",
    "http://example.com:443/x",
    "mailto:someone@example.com",
    "relative/path/",
    "https://example.com//",
    "file:///tmp/x/",
    "git+ssh://Host.Example:22/repo/",
)


# --------------------------------------------------------------------------------------
# helpers（disposable DB だけで使う）
# --------------------------------------------------------------------------------------


def _sql(name: str) -> str:
    return (SQL_DIR / name).read_text(encoding="utf-8")


def _block() -> str:
    return BLOCK_RE.findall(_sql(PREFLIGHT))[0]


def _statements(text: str) -> list[str]:
    body = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("--"))
    return [part.strip() for part in body.split(";") if part.strip()]


def _run_all(text: str) -> list[list[tuple]]:
    results = []
    with connection.cursor() as cursor:
        for statement in _statements(text):
            cursor.execute(statement)
            results.append(cursor.fetchall())
    return results


def _aggregates() -> dict[str, int]:
    tables = {
        "shrine": "temples_shrine",
        "source": "temples_shrineknowledgesource",
        "deity": "temples_shrinedeity",
        "history": "temples_shrinehistory",
        "citation": "temples_shrinefactsourcecitation",
        "source_fact": "temples_shrinesourcefact",
        "collective": "temples_shrinedeitycollective",
    }
    out = {}
    with connection.cursor() as cursor:
        for key, table in tables.items():
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            out[key] = cursor.fetchone()[0]
    return out


def _frozen_values(*, accepted: int) -> str:
    """Rehearsal only: frozen block from the disposable DB's own pre-state, built in memory."""
    counts = _aggregates()
    same_name_other = Shrine.objects.filter(name_jp=SHRINE_NAME).exclude(address=SHRINE_ADDRESS)
    return (
        "frozen AS (\n  SELECT\n    true AS frozen_values_set,\n"
        f"    {counts['shrine']}::bigint AS shrine_total,\n"
        f"    {counts['source']}::bigint AS source_total,\n"
        f"    {counts['deity']}::bigint AS deity_total,\n"
        f"    {counts['history']}::bigint AS history_total,\n"
        f"    {counts['citation']}::bigint AS citation_total,\n"
        f"    {counts['source_fact']}::bigint AS source_fact_total,\n"
        f"    {counts['collective']}::bigint AS collective_total,\n"
        f"    {same_name_other.count()}::bigint AS same_name_other_address_total,\n"
        f"    {accepted}::bigint AS accepted_shared_source_count\n),\n"
    )


def _with_frozen(name: str, frozen: str) -> str:
    """Replace the frozen block in memory. The committed file is untouched."""
    text = _sql(name)
    assert len(FROZEN_RE.findall(text)) == 1
    return FROZEN_RE.sub(lambda _: frozen, text)


def _guard_passes(name: str, frozen: str) -> bool:
    try:
        with transaction.atomic():
            rows = _run_all(_with_frozen(name, frozen))
    except DataError:  # division_by_zero = guard FAIL
        return False
    assert rows[-1] == [(1,)]
    return True


def _preflight_results() -> list[list[tuple]]:
    return _run_all(_sql(PREFLIGHT))


def _state_class() -> str:
    return _preflight_results()[-1][0][0]


def _source_state() -> tuple:
    for rows in _preflight_results():
        if rows and len(rows[0]) == 9 and rows[0][0] == "TOKAMACHI_REKIBUN_SHIRYOU":
            return rows[0]
    raise AssertionError("source state row missing")


def _create_source(
    url: str,
    *,
    compatible: bool = True,
    source_type: str = "",
    bibliography: str | None = None,
) -> ShrineKnowledgeSource:
    return ShrineKnowledgeSource.objects.create(
        source_type=source_type or SOURCE["type"],
        title=SOURCE["title"],
        url=url,
        publisher=SOURCE["publisher"] if compatible else "別の発行者",
        bibliography=SOURCE["bibliography"] if bibliography is None else bibliography,
        verification_status="source_confirmed",
        confidence="high",
        language="ja",
    )


def _base_state() -> None:
    """Disposable pre-state: Base Seed without the nsrc-000009 target row（Source ABSENT）。"""
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    Shrine.objects.filter(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS).delete()


def _lineage_state() -> None:
    """Normal lineage: nsrc-000007 Knowledge materialized first（shared Source REUSABLE）。"""
    _base_state()
    call_command(
        "import_shrine_knowledge",
        str(LEGACY_KNOWLEDGE_SEED_PATH),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )


def _extractor():
    spec = importlib.util.spec_from_file_location(
        "nsrc_000009_g7_extract_base_subset",
        SAFETY_DIR / "nsrc_000009_g7_extract_base_subset.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _guard_module():
    spec = importlib.util.spec_from_file_location(
        "_nsrc_000009_g7_migration_safety_guard", SAFETY_DIR / "guard.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _import_subset(tmp_path: Path, *args: str) -> str:
    module = _extractor()
    subset_path = tmp_path / "nsrc_000009_base_subset.json"
    subset_path.write_text(module.render(module.extract_subset()), encoding="utf-8")
    out = io.StringIO()
    call_command(
        "import_shrines_seed",
        "--source",
        str(subset_path),
        "--skip-goriyaku-tags",
        *args,
        stdout=out,
        stderr=io.StringIO(),
    )
    return out.getvalue()


def _import_knowledge(*args: str) -> str:
    out = io.StringIO()
    call_command(
        "import_shrine_knowledge",
        str(KNOWLEDGE_SEED_PATH),
        *args,
        stdout=out,
        stderr=io.StringIO(),
    )
    return out.getvalue()


def _plan_summary(output: str) -> dict[str, int]:
    (line,) = [line for line in output.splitlines() if line.startswith("plan summary: ")]
    return ast.literal_eval(line.removeprefix("plan summary: "))


def _goriyaku_snapshot() -> tuple:
    return (
        tuple(GoriyakuTag.objects.order_by("id").values_list("id", "name")),
        tuple(ShrineGoriyakuAssignment.objects.order_by("id").values_list("id", "shrine_id")),
        tuple(
            Shrine.goriyaku_tags.through.objects.order_by("id").values_list(
                "shrine_id", "goriyakutag_id"
            )
        ),
    )


def _target() -> Shrine:
    return Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)


def _history(title: str) -> ShrineHistory:
    return ShrineHistory.objects.get(shrine=_target(), title=title)


def _shared_source() -> ShrineKnowledgeSource:
    return ShrineKnowledgeSource.objects.get(source_type=SOURCE["type"], url=SOURCE["url"])


# --------------------------------------------------------------------------------------
# 1. SQL file contract
# --------------------------------------------------------------------------------------


def test_every_sql_file_passes_readonly_validation():
    is_readonly_sql = _guard_module().is_readonly_sql
    for name in ALL_SQL_FILES:
        ok, reason = is_readonly_sql(_sql(name))
        assert ok, (name, reason)


def test_sql_files_contain_no_connection_identifier_or_write():
    paths = sorted(SQL_DIR.glob("nsrc_000009_g7_*.sql"))
    assert [p.name for p in paths] == sorted(ALL_SQL_FILES)
    for path in paths:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for token in ("postgres://", "postgresql://", "password", "sslmode", "@localhost"):
            assert token not in lowered, (path.name, token)
        for statement in _statements(text):
            assert re.match(r"^(select|with)\b", statement, re.IGNORECASE), (path.name, statement)


def test_identity_and_target_blocks_are_identical_in_every_g7_sql_file():
    identity_blocks = []
    target_blocks = []
    for name in IDENTITY_FILES:
        found = BLOCK_RE.findall(_sql(name))
        assert found, name
        identity_blocks += found
        target_blocks += TARGET_RE.findall(_sql(name))
    assert len(set(identity_blocks)) == 1
    assert len(set(target_blocks)) == 1
    for name in GUARD_FILES:
        assert len(TARGET_RE.findall(_sql(name))) >= 1, name
    block = identity_blocks[0]
    assert f"normalized_url = '{SOURCE['normalized']}'" in block
    assert "btrim(COALESCE(bibliography, '')) = '中魚沼郡誌上 p.398'" in block
    # the Fact locator is never a Source reuse condition
    assert f"'{LOCATOR}'" not in block
    target = target_blocks[0]
    assert f"WHERE name_jp = '{SHRINE_NAME}'\n    AND address = '{SHRINE_ADDRESS}'" in target
    assert f"c.locator_text = '{LOCATOR}'" in target


def test_frozen_pre_state_is_identical_and_equals_the_production_measurement():
    frozen = [FROZEN_RE.findall(_sql(name)) for name in GUARD_FILES]
    assert all(len(found) == 1 for found in frozen)
    assert len({found[0] for found in frozen}) == 1
    text = frozen[0][0]
    assert "    true AS frozen_values_set,\n" in text
    assert re.findall(r"^\s+(\S+)::bigint AS (\w+)", text, re.MULTILINE) == [
        (str(PRODUCTION_PRESTATE[name]), name) for name in FROZEN_NAMES
    ]
    assert "NULL" not in text
    assert "UNSET" not in text
    # CLEAN_CREATE with a REUSABLE shared Source: expected Source delta is +0
    assert PRODUCTION_PRESTATE["accepted_shared_source_count"] == 1
    for name in GUARD_FILES:
        assert "  f.frozen_values_set\n" in _sql(name)
    assert FROZEN_RE.findall(_sql(PREFLIGHT)) == []


@pytest.mark.django_db
def test_preflight_tables_are_the_real_model_tables():
    assert ShrineFactSourceCitation._meta.db_table == "temples_shrinefactsourcecitation"
    assert ShrineHistory.sources.through._meta.db_table == "temples_shrinehistory_sources"
    referenced = re.findall(r"to_regclass\('public\.(\w+)'\)", _sql(PREFLIGHT))
    assert "temples_shrinefactsourcecitation" in referenced
    existing = set(connection.introspection.table_names())
    assert set(referenced) <= existing
    assert "'0121_shrine_fact_source_citation'" in _sql(PREFLIGHT)


@pytest.mark.django_db
def test_preflight_and_backup_check_run_in_a_read_only_transaction():
    _lineage_state()
    before = _aggregates()
    for name in (PREFLIGHT, BACKUP_VERSION_CHECK):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
            results = _run_all(_sql(name))
        assert results
    assert _aggregates() == before
    metadata = _preflight_results()
    assert metadata[0] == [(True, True, True)]
    # The pytest DB uses temples.migrations_nogis (0020_shrine_fact_source_citation), so the
    # 0121 flag reports exactly what the ledger holds; Production must report True.
    applied = MigrationRecorder.Migration.objects.filter(
        app="temples", name="0121_shrine_fact_source_citation"
    ).exists()
    assert metadata[2][0][1] is applied
    assert all(metadata[3][0])  # every required table exists


# --------------------------------------------------------------------------------------
# 2. Source identity = importer semantics
# --------------------------------------------------------------------------------------


def _sql_rows() -> dict[int, tuple]:
    sql = (
        "WITH "
        + _block()
        + """
SELECT n.id, n.normalized_url,
       EXISTS (SELECT 1 FROM shared_identity i WHERE i.id = n.id),
       EXISTS (SELECT 1 FROM shared_metadata_compatible m WHERE m.id = n.id),
       EXISTS (SELECT 1 FROM shared_url_lookalike l WHERE l.id = n.id)
FROM source_url_norm n
"""
    )
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return {row[0]: tuple(row[1:]) for row in cursor.fetchall()}


def _python_normalized(url: str) -> str | None:
    try:
        return normalize_source_url(url)
    except ValueError:
        return None


@pytest.mark.django_db
def test_sql_normalized_url_equals_importer_normalize_source_url():
    urls = [
        *GENERAL_CORPUS,
        *IDENTITY_VARIANTS,
        *NON_IDENTITY_LOOKALIKE_VARIANTS,
        *IMPORTER_UNPARSEABLE,
    ]
    created = {
        ShrineKnowledgeSource.objects.create(
            source_type="government", title=f"t{i}", url=url
        ).pk: url
        for i, url in enumerate(urls)
    }
    rows = _sql_rows()
    for pk, url in created.items():
        assert rows[pk][0] == _python_normalized(url), url


@pytest.mark.django_db
def test_identity_count_uses_importer_semantics_only():
    identity = {_create_source(u).pk: u for u in IDENTITY_VARIANTS}
    lookalike = {_create_source(u).pk: u for u in NON_IDENTITY_LOOKALIKE_VARIANTS}
    unparseable = {_create_source(u).pk: u for u in IMPORTER_UNPARSEABLE}
    wrong_type = _create_source(SOURCE["url"], source_type="secondary_editorial").pk
    rows = _sql_rows()

    # rows[pk] = (normalized_url, is_identity, is_metadata_compatible, is_lookalike)
    for pk, url in identity.items():
        assert normalize_source_url(url) == SOURCE["normalized"], url
        assert rows[pk][1:] == (True, True, True), url
    for pk, url in lookalike.items():
        assert normalize_source_url(url) != SOURCE["normalized"], url
        assert rows[pk][1] is False and rows[pk][3] is True, url
    for pk, url in unparseable.items():
        assert _python_normalized(url) is None, url
        assert rows[pk][0] is None and rows[pk][1] is False, url
    # 同じ URL でも source_type が違えば identity ではない（lookalike としてだけ拾う）
    assert rows[wrong_type][1] is False and rows[wrong_type][3] is True


@pytest.mark.django_db
def test_metadata_compatibility_preserves_the_legacy_bibliography():
    compatible = _create_source(SOURCE["url"]).pk
    drifted = _create_source(SOURCE["url"], compatible=False).pk
    # the Fact locator must never be the Source bibliography for reuse
    rewritten = _create_source(SOURCE["url"], bibliography=LOCATOR).pk
    rows = _sql_rows()
    assert rows[compatible][1:3] == (True, True)
    assert rows[drifted][1:3] == (True, False)
    assert rows[rewritten][1:3] == (True, False)


# --------------------------------------------------------------------------------------
# 3. Fail-closed guards + Source-state simulations
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_committed_guards_fail_closed_on_a_non_production_state(tmp_path):
    # Disposable lineage aggregates differ from the Production measurement: every guard fails.
    _lineage_state()
    assert _aggregates() != PRODUCTION_AGGREGATES
    for name in GUARD_FILES:
        with pytest.raises(DataError, match="division by zero"):
            with transaction.atomic():
                _run_all(_sql(name))
    _import_subset(tmp_path)
    _import_knowledge()
    for name in GUARD_FILES:
        with pytest.raises(DataError, match="division by zero"):
            with transaction.atomic():
                _run_all(_sql(name))


def _legacy_lineage_source() -> None:
    call_command(
        "import_shrine_knowledge",
        str(LEGACY_KNOWLEDGE_SEED_PATH),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )


SOURCE_STATE_CASES = {
    # case -> (setup, expected source state, expected class, accepted count or None)
    "absent": (lambda: None, "ABSENT", "CLEAN_CREATE", 0),
    "reusable-nsrc-000007-lineage": (_legacy_lineage_source, "REUSABLE", "CLEAN_CREATE", 1),
    "reusable-url-variant": (
        lambda: _create_source(IDENTITY_VARIANTS[2]),
        "REUSABLE",
        "CLEAN_CREATE",
        1,
    ),
    "metadata-drift": (
        lambda: _create_source(SOURCE["url"], compatible=False),
        "CONFLICT_METADATA_DRIFT",
        "CONFLICT",
        None,
    ),
    "bibliography-rewritten-to-locator": (
        lambda: _create_source(SOURCE["url"], bibliography=LOCATOR),
        "CONFLICT_METADATA_DRIFT",
        "CONFLICT",
        None,
    ),
    "identity-ambiguous": (
        lambda: (_legacy_lineage_source(), _create_source(IDENTITY_VARIANTS[1])),
        "CONFLICT_IDENTITY_AMBIGUOUS",
        "CONFLICT",
        None,
    ),
    "non-identity-lookalike": (
        lambda: _create_source(NON_IDENTITY_LOOKALIKE_VARIANTS[0]),
        "CONFLICT_NON_IDENTITY_LOOKALIKE",
        "CONFLICT",
        None,
    ),
    "lineage-plus-lookalike": (
        lambda: (_legacy_lineage_source(), _create_source(NON_IDENTITY_LOOKALIKE_VARIANTS[4])),
        "CONFLICT_NON_IDENTITY_LOOKALIKE",
        "CONFLICT",
        None,
    ),
    "importer-unparseable-url": (
        lambda: _create_source(IMPORTER_UNPARSEABLE[0]),
        "CONFLICT_IMPORTER_UNPARSEABLE_URL",
        "CONFLICT",
        None,
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(SOURCE_STATE_CASES))
def test_source_state_simulation(case):
    setup, source_state, state_class, accepted = SOURCE_STATE_CASES[case]
    _base_state()
    setup()

    assert _source_state()[-1] == source_state
    assert _state_class() == state_class

    if accepted is None:
        # Unexpected Production state: no accepted count can make the pre-Base guard pass.
        for candidate in (0, 1):
            assert _guard_passes(PRE_BASE, _frozen_values(accepted=candidate)) is False
    else:
        assert _source_state()[3] == accepted  # source_identity_count
        assert _guard_passes(PRE_BASE, _frozen_values(accepted=accepted)) is True
        # a wrong frozen accepted count must fail
        assert _guard_passes(PRE_BASE, _frozen_values(accepted=1 - accepted)) is False


def _filler_shrine() -> Shrine:
    return Shrine.objects.get_or_create(
        name_jp="G7filler神社", address="架空県架空市0-0", defaults={"kind": "shrine"}
    )[0]


def _extra_citation_elsewhere() -> None:
    legacy = ShrineHistory.objects.get(title=LEGACY_H1_TITLE)
    ShrineFactSourceCitation.objects.create(
        shrine_history=legacy, source=legacy.sources.get(), locator_text="中魚沼郡誌上 p.999"
    )


PRESTATE_DRIFT = {
    "shrine+1": lambda: Shrine.objects.create(
        name_jp="無関係神社", kind="shrine", address="架空県1"
    ),
    "source+1": lambda: ShrineKnowledgeSource.objects.create(
        source_type="internal_research", title="x", url="https://example.invalid/extra"
    ),
    "deity+1": lambda: ShrineDeity.objects.create(shrine=_filler_shrine(), display_name="extra"),
    "history+1": lambda: ShrineHistory.objects.create(
        shrine=_filler_shrine(), history_type="tradition", title="extra", content="x"
    ),
    "citation+1": _extra_citation_elsewhere,
    "source-fact+1": lambda: ShrineSourceFact.objects.create(
        shrine=_filler_shrine(),
        stable_key="g7-extra",
        source_attested_wording="x",
        evidence_characterization="official_prayer_supported",
    ),
    "collective+1": lambda: ShrineDeityCollective.objects.create(
        shrine=_filler_shrine(), source_attested_label="extra"
    ),
    "same-name-other-address+1": lambda: Shrine.objects.create(
        name_jp=SHRINE_NAME, kind="shrine", address=OTHER_AKAGI_ADDRESSES[0]
    ),
    "shared-source-metadata-drift": lambda: ShrineKnowledgeSource.objects.filter(
        url=SOURCE["url"]
    ).update(publisher="別の発行者"),
    "shared-source-bibliography-p445": lambda: ShrineKnowledgeSource.objects.filter(
        url=SOURCE["url"]
    ).update(bibliography=LOCATOR),
    "shared-source-lookalike": lambda: _create_source(NON_IDENTITY_LOOKALIKE_VARIANTS[1]),
}


@pytest.mark.django_db
def test_lineage_frozen_guard_passes_only_on_the_frozen_prestate():
    _lineage_state()
    frozen = _frozen_values(accepted=1)
    assert "1::bigint AS same_name_other_address_total" in frozen  # nsrc-000007 赤城社
    assert _guard_passes(PRE_BASE, frozen) is True
    assert _guard_passes(POST_BASE, frozen) is False
    assert _guard_passes(POST_KNOWLEDGE, frozen) is False


@pytest.mark.django_db
@pytest.mark.parametrize("drift", sorted(PRESTATE_DRIFT))
def test_pre_base_guard_fails_on_any_prestate_drift(drift):
    _lineage_state()
    _filler_shrine()
    frozen = _frozen_values(accepted=1)
    assert _guard_passes(PRE_BASE, frozen) is True
    PRESTATE_DRIFT[drift]()
    assert _guard_passes(PRE_BASE, frozen) is False


# --------------------------------------------------------------------------------------
# 4. Exact target identity
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_same_name_other_address_rows_never_become_the_target():
    _lineage_state()
    for address in OTHER_AKAGI_ADDRESSES:
        Shrine.objects.create(name_jp=SHRINE_NAME, kind="shrine", address=address)

    results = _preflight_results()
    identity = results[5][0]
    assert identity == (0, 3, 3, 0)  # target / same-name / same-name other address / same-address
    listing = results[6]
    assert {row[2] for row in listing} == {LEGACY_AKAGI_ADDRESS, *OTHER_AKAGI_ADDRESSES}
    assert all(row[-1] is False for row in listing)
    # nsrc-000007's History / relation / Source never count as target Knowledge
    assert _state_class() == "CLEAN_CREATE"
    assert _preflight_results()[-1][0][1:] == (1, 1, 0, 0, 0, 0)

    frozen = _frozen_values(accepted=1)
    assert "3::bigint AS same_name_other_address_total" in frozen
    assert _guard_passes(PRE_BASE, frozen) is True

    # a same-address collision is a CONFLICT, whatever the name
    Shrine.objects.create(name_jp="赤城神社", kind="shrine", address=SHRINE_ADDRESS)
    assert _state_class() == "CONFLICT"
    assert _guard_passes(PRE_BASE, frozen) is False


# --------------------------------------------------------------------------------------
# 5. Target state classification
# --------------------------------------------------------------------------------------


def _materialize(tmp_path) -> Shrine:
    _import_subset(tmp_path)
    _import_knowledge()
    return _target()


def _citation(title: str) -> ShrineFactSourceCitation:
    return ShrineFactSourceCitation.objects.get(shrine_history=_history(title))


def _other_source() -> ShrineKnowledgeSource:
    return ShrineKnowledgeSource.objects.create(
        source_type="internal_research", title="other", url="https://example.invalid/other"
    )


def _extra_relation() -> None:
    _history(H1_TITLE).sources.add(_other_source())


def _citation_to_unrelated_source() -> None:
    # bypasses clean() on purpose: the guard must catch it even if application validation did not
    ShrineFactSourceCitation.objects.filter(pk=_citation(H1_TITLE).pk).update(
        source=_other_source()
    )


def _citation_to_related_wrong_source() -> None:
    other = _other_source()
    h1 = _history(H1_TITLE)
    h1.sources.set([other])
    ShrineFactSourceCitation.objects.filter(shrine_history=h1).update(source=other)


def _extra_citation() -> None:
    ShrineFactSourceCitation.objects.create(
        shrine_history=_history(H1_TITLE),
        source=_shared_source(),
        locator_text="中魚沼郡誌上 p.446",
    )


def _citation_moved_to_wrong_history() -> None:
    legacy = ShrineHistory.objects.get(title=LEGACY_H1_TITLE)
    ShrineFactSourceCitation.objects.filter(pk=_citation(H2_TITLE).pk).update(shrine_history=legacy)


def _goriyaku_tag_link() -> None:
    _target().goriyaku_tags.add(GoriyakuTag.objects.create(name="G7テストタグ"))


# shared by the preflight CONFLICT matrix and the post-Knowledge negative matrix
CONFLICTING_MUTATIONS = {
    "wrong-citation-locator": lambda: ShrineFactSourceCitation.objects.filter(
        pk=_citation(H1_TITLE).pk
    ).update(locator_text="中魚沼郡誌上 p.398"),
    "extra-citation": _extra_citation,
    "citation-to-unrelated-source": _citation_to_unrelated_source,
    "citation-and-relation-to-wrong-source": _citation_to_related_wrong_source,
    "extra-history-source-relation": _extra_relation,
    "current-deity-created": lambda: ShrineDeity.objects.create(
        shrine=_target(), display_name="大山祇命"
    ),
    "extra-history": lambda: ShrineHistory.objects.create(
        shrine=_target(), history_type="tradition", title="extra", content="x"
    ),
    "h1-content-drift": lambda: ShrineHistory.objects.filter(pk=_history(H1_TITLE).pk).update(
        content="赤城社は天明3年に創立された。"
    ),
    "source-fact-created": lambda: ShrineSourceFact.objects.create(
        shrine=_target(),
        stable_key="g7-nsrc-000009-extra",
        source_attested_wording="x",
        evidence_characterization="official_prayer_supported",
    ),
    "collective-created": lambda: ShrineDeityCollective.objects.create(
        shrine=_target(), source_attested_label="extra"
    ),
    "goriyaku-text-drift": lambda: Shrine.objects.filter(pk=_target().pk).update(goriyaku="縁結び"),
    "goriyaku-tag-drift": _goriyaku_tag_link,
    "coordinate-drift": lambda: Shrine.objects.filter(pk=_target().pk).update(latitude=37.0897),
    "shared-source-bibliography-p445": lambda: ShrineKnowledgeSource.objects.filter(
        pk=_shared_source().pk
    ).update(bibliography=LOCATOR),
}
# A missing citation / a citation moved away from the target is incomplete, not contradictory:
# the preflight reports PARTIAL_EXISTING, and the post-Knowledge verification fails.
INCOMPLETE_MUTATIONS = {
    "missing-citation": lambda: _citation(H1_TITLE).delete(),
    "citation-moved-to-wrong-history": _citation_moved_to_wrong_history,
    "missing-h2": lambda: _history(H2_TITLE).delete(),
}


@pytest.mark.django_db
def test_state_class_follows_the_target_lifecycle(tmp_path):
    _lineage_state()
    assert _state_class() == "CLEAN_CREATE"
    _import_subset(tmp_path)
    assert _state_class() == "PARTIAL_EXISTING"  # Base only, Knowledge absent
    _import_knowledge()
    assert _state_class() == "ALREADY_MATERIALIZED"
    assert _preflight_results()[-1][0] == ("ALREADY_MATERIALIZED", 1, 1, 1, 2, 2, 2)


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", sorted(CONFLICTING_MUTATIONS))
def test_preflight_classifies_contradicting_target_state_as_conflict(tmp_path, mutation):
    _lineage_state()
    _materialize(tmp_path)
    CONFLICTING_MUTATIONS[mutation]()
    assert _state_class() == "CONFLICT"


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", sorted(INCOMPLETE_MUTATIONS))
def test_preflight_classifies_incomplete_target_state_as_partial(tmp_path, mutation):
    _lineage_state()
    _materialize(tmp_path)
    INCOMPLETE_MUTATIONS[mutation]()
    assert _state_class() == "PARTIAL_EXISTING"


@pytest.mark.django_db
def test_preflight_conflict_when_another_shrine_shares_the_target_address(tmp_path):
    _lineage_state()
    _import_subset(tmp_path)
    Shrine.objects.create(name_jp="赤城神社", kind="shrine", address=SHRINE_ADDRESS)
    assert _state_class() == "CONFLICT"


# --------------------------------------------------------------------------------------
# 6. Target-only Base subset
# --------------------------------------------------------------------------------------


def test_extractor_emits_exactly_one_canonical_row_deterministically():
    module = _extractor()
    first = module.render(module.extract_subset())
    second = module.render(module.extract_subset())
    assert first == second
    rows = json.loads(first)
    assert rows == [module.EXPECTED_ROW]
    assert (rows[0]["name_jp"], rows[0]["address"]) == (SHRINE_NAME, SHRINE_ADDRESS)
    assert (rows[0]["latitude"], rows[0]["longitude"]) == (SHRINE_LAT, SHRINE_LNG)
    assert rows[0]["location"] == {"lat": SHRINE_LAT, "lng": SHRINE_LNG}
    assert rows[0]["goriyaku"] == ""
    assert (
        hashlib.sha256(first.encode("utf-8")).hexdigest()
        == hashlib.sha256(second.encode("utf-8")).hexdigest()
    )


def test_full_base_seed_is_never_the_production_payload():
    module = _extractor()
    full = json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))
    subset = json.loads(module.render(module.extract_subset()))
    assert len(full) > 1
    assert len(subset) == 1
    # the subset never carries any other row, including the same-name nsrc-000007 shrine
    others = [r for r in full if (r["name_jp"], r["address"]) != (SHRINE_NAME, SHRINE_ADDRESS)]
    assert len(others) == len(full) - 1
    assert all(row not in subset for row in others)
    assert module.BASE_SEED_PATH == BASE_SEED_PATH


def test_extractor_fails_closed_on_missing_or_drifted_row(tmp_path):
    module = _extractor()
    rows = json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))

    missing = [r for r in rows if r.get("address") != SHRINE_ADDRESS]
    path = tmp_path / "missing.json"
    path.write_text(json.dumps(missing, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit, match="exactly 1"):
        module.extract_subset(path)

    for field, value in (
        ("latitude", 37.0897),
        ("longitude", 138.7481),
        ("location", {"lat": 37.0897, "lng": 138.748108}),
        ("goriyaku", "縁結び"),
    ):
        drifted = copy.deepcopy(rows)
        for row in drifted:
            if row.get("name_jp") == SHRINE_NAME and row.get("address") == SHRINE_ADDRESS:
                row[field] = value
        path = tmp_path / f"drifted-{field}.json"
        path.write_text(json.dumps(drifted, ensure_ascii=False), encoding="utf-8")
        with pytest.raises(SystemExit, match="differs"):
            module.extract_subset(path)

    duplicated = [*rows, copy.deepcopy(module.EXPECTED_ROW)]
    path = tmp_path / "duplicated.json"
    path.write_text(json.dumps(duplicated, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit, match="exactly 1"):
        module.extract_subset(path)

    # a same-name row at another address alone (e.g. nsrc-000007) is never extracted
    same_name_only = [r for r in rows if r.get("name_jp") == SHRINE_NAME]
    same_name_only = [r for r in same_name_only if r.get("address") != SHRINE_ADDRESS]
    assert same_name_only
    path = tmp_path / "other.json"
    path.write_text(json.dumps(same_name_only, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit, match="exactly 1"):
        module.extract_subset(path)


def test_extractor_refuses_repository_output_path():
    module = _extractor()
    assert module.main(["x", str(REPO_ROOT / "nsrc_000009_subset.json")]) == 1
    assert not (REPO_ROOT / "nsrc_000009_subset.json").exists()


# --------------------------------------------------------------------------------------
# 7. Sequential rehearsal（in-memory frozen values from the disposable pre-state）
# --------------------------------------------------------------------------------------

REHEARSALS = {
    # lineage -> (setup, accepted, first Knowledge plan, second Knowledge plan)
    "nsrc-000007-lineage-shared-source-reused": (
        _lineage_state,
        1,
        {"source_REUSE_EXISTING": 1, "history_CREATE": 2, "citation_CREATE": 2},
        {"source_REUSE_EXISTING": 1, "history_SKIP_EXISTS": 2, "citation_SKIP_EXISTS": 2},
    ),
    "shared-source-absent": (
        _base_state,
        0,
        {"source_CREATE": 1, "history_CREATE": 2, "citation_CREATE": 2},
        {"source_REUSE_EXISTING": 1, "history_SKIP_EXISTS": 2, "citation_SKIP_EXISTS": 2},
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("lineage", sorted(REHEARSALS))
def test_sequential_rehearsal(tmp_path, lineage):
    setup, accepted, first_plan, second_plan = REHEARSALS[lineage]
    setup()
    assert _source_state()[-1] == ("REUSABLE" if accepted else "ABSENT")
    assert _state_class() == "CLEAN_CREATE"
    pre = _aggregates()
    frozen = _frozen_values(accepted=accepted)
    goriyaku_before = _goriyaku_snapshot()
    shared_before = (
        list(ShrineKnowledgeSource.objects.filter(url=SOURCE["url"]).values()) if accepted else []
    )

    # pre-Base guard
    assert _guard_passes(PRE_BASE, frozen) is True
    assert _guard_passes(POST_BASE, frozen) is False
    assert _guard_passes(POST_KNOWLEDGE, frozen) is False

    # target-only Base: dry-run -> apply -> second dry-run（idempotency）
    _import_subset(tmp_path, "--dry-run")
    assert _aggregates() == pre
    assert "created=1 updated=0 skipped=0 total_seed=1" in _import_subset(tmp_path)
    second = _import_subset(tmp_path, "--dry-run")
    assert "created=0 updated=0 skipped=1 total_seed=1" in second
    assert _aggregates() == {**pre, "shrine": pre["shrine"] + 1}

    # post-Base guard
    assert _guard_passes(POST_BASE, frozen) is True
    assert _guard_passes(PRE_BASE, frozen) is False
    assert _guard_passes(POST_KNOWLEDGE, frozen) is False
    assert _goriyaku_snapshot() == goriyaku_before

    # Knowledge: dry-run -> apply -> second import（idempotency）
    dry = _import_knowledge("--dry-run")
    assert _plan_summary(dry) == first_plan
    assert _aggregates() == {**pre, "shrine": pre["shrine"] + 1}
    applied = _import_knowledge()
    assert _plan_summary(applied) == first_plan
    assert (
        f"import complete: sources created={1 - accepted}, deities created=0, "
        "histories created=2, collectives created=0, memberships created=0, "
        "source_facts created=0, citations created=2"
    ) in applied
    expected_post = {
        **pre,
        "shrine": pre["shrine"] + 1,
        "source": pre["source"] + (1 - accepted),
        "history": pre["history"] + 2,
        "citation": pre["citation"] + 2,
    }
    assert _aggregates() == expected_post

    second_dry = _import_knowledge("--dry-run")
    assert _plan_summary(second_dry) == second_plan
    assert "CREATE" not in second_dry.replace("REUSE_EXISTING", "")
    second_apply = _import_knowledge()
    assert "citations created=0" in second_apply
    assert _aggregates() == expected_post

    # post-Knowledge verification
    assert _guard_passes(POST_KNOWLEDGE, frozen) is True
    assert _guard_passes(POST_BASE, frozen) is False
    assert _guard_passes(PRE_BASE, frozen) is False
    assert _state_class() == "ALREADY_MATERIALIZED"
    assert _goriyaku_snapshot() == goriyaku_before

    shrine = _target()
    assert ShrineDeity.objects.filter(shrine=shrine).count() == 0
    shared = _shared_source()
    assert shared.bibliography == SOURCE["bibliography"]
    if accepted:
        # the reused legacy Source row is byte-unchanged
        assert list(ShrineKnowledgeSource.objects.filter(url=SOURCE["url"]).values()) == (
            shared_before
        )
    for title in (H1_TITLE, H2_TITLE):
        history = _history(title)
        assert list(history.sources.all()) == [shared]
        citation = _citation(title)
        assert (citation.source_id, citation.locator_text) == (shared.pk, LOCATOR)


# --------------------------------------------------------------------------------------
# 8. Post-Knowledge negatives
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", sorted({**CONFLICTING_MUTATIONS, **INCOMPLETE_MUTATIONS}))
def test_post_knowledge_verification_fails_closed(tmp_path, mutation):
    _lineage_state()
    frozen = _frozen_values(accepted=1)
    _materialize(tmp_path)
    assert _guard_passes(POST_KNOWLEDGE, frozen) is True
    {**CONFLICTING_MUTATIONS, **INCOMPLETE_MUTATIONS}[mutation]()
    assert _guard_passes(POST_KNOWLEDGE, frozen) is False


@pytest.mark.django_db
def test_post_base_guard_requires_exactly_target_plus_one(tmp_path):
    _lineage_state()
    frozen = _frozen_values(accepted=1)
    _import_subset(tmp_path)
    assert _guard_passes(POST_BASE, frozen) is True
    Shrine.objects.create(name_jp="無関係神社", kind="shrine", address="架空県2")
    assert _guard_passes(POST_BASE, frozen) is False


@pytest.mark.django_db
@pytest.mark.parametrize(
    "mutation",
    ["coordinate-drift", "goriyaku-text-drift", "goriyaku-tag-drift", "citation+1"],
)
def test_post_base_guard_fails_closed(tmp_path, mutation):
    _lineage_state()
    frozen = _frozen_values(accepted=1)
    _import_subset(tmp_path)
    assert _guard_passes(POST_BASE, frozen) is True
    if mutation == "citation+1":
        _extra_citation_elsewhere()
    else:
        CONFLICTING_MUTATIONS[mutation]()
    assert _guard_passes(POST_BASE, frozen) is False


# --------------------------------------------------------------------------------------
# 9. Runtime QA rehearsal（READ ONLY transaction）
# --------------------------------------------------------------------------------------


def _runtime_qa():
    spec = importlib.util.spec_from_file_location(
        "nsrc_000009_g7_runtime_qa", SAFETY_DIR / "nsrc_000009_g7_runtime_qa.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.django_db(transaction=True)
def test_runtime_qa_rehearsal_passes_read_only(tmp_path, capsys):
    _lineage_state()
    _materialize(tmp_path)

    module = _runtime_qa()
    before = _aggregates()
    capsys.readouterr()
    module.main()
    out = capsys.readouterr().out
    assert _aggregates() == before
    for line in (
        "DETAIL_RUNTIME=PASS",
        "FACT_CITATION_INTEGRITY=PASS",
        "CONCIERGE_CANDIDATE_PATH=PASS",
        "RECOMMENDATION_REASON=PASS",
        "COMPASS_DISTANCE=PASS",
        "COMPASS_DIRECTION=PASS",
        "G7_PRODUCTION_RUNTIME_QA=PASS",
        "TRANSACTION_MODE=READ_ONLY",
    ):
        assert line in out, line


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "mutation",
    ["wrong-citation-locator", "shared-source-bibliography-p445", "current-deity-created"],
)
def test_runtime_qa_fails_closed(tmp_path, mutation):
    _lineage_state()
    _materialize(tmp_path)
    CONFLICTING_MUTATIONS[mutation]()
    with pytest.raises(AssertionError):
        _runtime_qa().main()


# --------------------------------------------------------------------------------------
# 10. Committed frozen guards on the simulated exact Production pre-state
# --------------------------------------------------------------------------------------

FILLER_SHRINE = "G7filler神社"


def _committed_guard_passes(name: str) -> bool:
    """Run the committed guard file unchanged（frozen = Production measurement）."""
    try:
        with transaction.atomic():
            rows = _run_all(_sql(name))
    except DataError:  # division_by_zero = guard FAIL
        return False
    assert rows[-1] == [(1,)]
    return True


def _simulate_production_prestate() -> None:
    """Disposable DB の aggregate を Production 実測値と完全一致させる（frozen 値は変えない）。

    nsrc-000007 lineage（shared Source REUSABLE、四日町の 赤城社 1行）を再現し、Shrine 数を合わせ、
    Knowledge 系は target / shared Source と無関係な filler 行で実測値まで埋める。filler は lookalike に
    ならない。
    """
    _lineage_state()
    filler = _filler_shrine()
    surplus = Shrine.objects.count() - PRODUCTION_PRESTATE["shrine_total"]
    if surplus > 0:
        removable = (
            Shrine.objects.exclude(pk=filler.pk)
            .exclude(name_jp=SHRINE_NAME)
            .exclude(address=SHRINE_ADDRESS)
            .order_by("-id")[:surplus]
        )
        Shrine.objects.filter(pk__in=list(removable.values_list("pk", flat=True))).delete()
    for index in range(PRODUCTION_PRESTATE["shrine_total"] - Shrine.objects.count()):
        Shrine.objects.create(
            name_jp=f"G7filler追加{index}", kind="shrine", address=f"架空県{index}"
        )

    def missing(model, key: str) -> range:
        return range(PRODUCTION_PRESTATE[key] - model.objects.count())

    ShrineKnowledgeSource.objects.bulk_create(
        ShrineKnowledgeSource(
            source_type="internal_research",
            title=f"filler source {i}",
            url=f"https://example.invalid/g7-filler/{i}",
        )
        for i in missing(ShrineKnowledgeSource, "source_total")
    )
    ShrineDeity.objects.bulk_create(
        ShrineDeity(shrine=filler, display_name=f"filler deity {i}")
        for i in missing(ShrineDeity, "deity_total")
    )
    ShrineHistory.objects.bulk_create(
        ShrineHistory(
            shrine=filler,
            history_type="tradition",
            title=f"filler history {i}",
            content="filler",
        )
        for i in missing(ShrineHistory, "history_total")
    )
    ShrineSourceFact.objects.bulk_create(
        ShrineSourceFact(
            shrine=filler,
            stable_key=f"g7-filler-source-fact-{i}",
            source_attested_wording="filler",
            evidence_characterization="official_prayer_supported",
        )
        for i in missing(ShrineSourceFact, "source_fact_total")
    )
    ShrineDeityCollective.objects.bulk_create(
        ShrineDeityCollective(shrine=filler, source_attested_label=f"filler collective {i}")
        for i in missing(ShrineDeityCollective, "collective_total")
    )
    assert _aggregates() == PRODUCTION_AGGREGATES
    assert (
        Shrine.objects.filter(name_jp=SHRINE_NAME).exclude(address=SHRINE_ADDRESS).count()
        == PRODUCTION_PRESTATE["same_name_other_address_total"]
    )
    assert _state_class() == "CLEAN_CREATE"
    assert _source_state()[-1] == "REUSABLE"


def _swap_filler_source(url: str, **kwargs) -> None:
    """Keep source_total equal to the frozen value while changing the shared Source state."""
    ShrineKnowledgeSource.objects.filter(
        url__startswith="https://example.invalid/g7-filler/"
    ).order_by("id").first().delete()
    _create_source(url, **kwargs)


def _swap_filler_shrine(name_jp: str, address: str) -> None:
    """Keep shrine_total equal to the frozen value while changing identity state."""
    Shrine.objects.exclude(name_jp__in=(SHRINE_NAME, FILLER_SHRINE)).exclude(
        address=SHRINE_ADDRESS
    ).order_by("-id").first().delete()
    Shrine.objects.create(name_jp=name_jp, kind="shrine", address=address)


@pytest.mark.django_db
def test_committed_pre_base_guard_passes_on_the_exact_production_prestate():
    _simulate_production_prestate()
    assert _committed_guard_passes(PRE_BASE) is True
    assert _committed_guard_passes(POST_BASE) is False
    assert _committed_guard_passes(POST_KNOWLEDGE) is False


COMMITTED_PRESTATE_DRIFT = {
    **PRESTATE_DRIFT,
    "source-1": lambda: (
        ShrineKnowledgeSource.objects.filter(url__startswith="https://example.invalid/g7-filler/")
        .order_by("id")
        .first()
        .delete()
    ),
    # target identity drift（shrine_total unchanged）
    "target-exists": lambda: _swap_filler_shrine(SHRINE_NAME, SHRINE_ADDRESS),
    "same-address-other-name": lambda: _swap_filler_shrine("赤城神社", SHRINE_ADDRESS),
    "same-name-other-address-swap": lambda: _swap_filler_shrine(
        SHRINE_NAME, OTHER_AKAGI_ADDRESSES[0]
    ),
    # shared Source conflicts / accepted count drift（source_total unchanged）
    "shared-source-identity-ambiguous": lambda: _swap_filler_source(IDENTITY_VARIANTS[1]),
    "shared-source-non-identity-lookalike-swap": lambda: _swap_filler_source(
        NON_IDENTITY_LOOKALIKE_VARIANTS[0]
    ),
    "shared-source-importer-unparseable": lambda: _swap_filler_source(IMPORTER_UNPARSEABLE[0]),
    "shared-source-absent": lambda: (
        ShrineKnowledgeSource.objects.filter(url=SOURCE["url"]).delete(),
        ShrineKnowledgeSource.objects.create(
            source_type="internal_research", title="x", url="https://example.invalid/refill"
        ),
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("drift", sorted(COMMITTED_PRESTATE_DRIFT))
def test_committed_pre_base_guard_fails_on_any_drift(drift):
    _simulate_production_prestate()
    assert _committed_guard_passes(PRE_BASE) is True
    COMMITTED_PRESTATE_DRIFT[drift]()
    assert _committed_guard_passes(PRE_BASE) is False


@pytest.mark.django_db
def test_committed_sequential_rehearsal(tmp_path):
    _simulate_production_prestate()
    goriyaku_before = _goriyaku_snapshot()
    shared_before = list(ShrineKnowledgeSource.objects.filter(url=SOURCE["url"]).values())
    assert _committed_guard_passes(PRE_BASE) is True

    # Base: target-only subset dry-run -> apply -> second dry-run
    _import_subset(tmp_path, "--dry-run")
    assert _aggregates() == PRODUCTION_AGGREGATES
    assert "created=1 updated=0 skipped=0 total_seed=1" in _import_subset(tmp_path)
    assert "created=0 updated=0 skipped=1 total_seed=1" in _import_subset(tmp_path, "--dry-run")
    assert _aggregates() == EXPECTED_POST_BASE
    assert _committed_guard_passes(POST_BASE) is True
    assert _committed_guard_passes(PRE_BASE) is False
    assert _committed_guard_passes(POST_KNOWLEDGE) is False

    # Knowledge: dry-run -> apply -> second dry-run / apply（idempotent）
    first_plan = {"source_REUSE_EXISTING": 1, "history_CREATE": 2, "citation_CREATE": 2}
    assert _plan_summary(_import_knowledge("--dry-run")) == first_plan
    assert _aggregates() == EXPECTED_POST_BASE
    applied = _import_knowledge()
    assert (
        "import complete: sources created=0, deities created=0, histories created=2, "
        "collectives created=0, memberships created=0, source_facts created=0, "
        "citations created=2"
    ) in applied
    assert _aggregates() == EXPECTED_POST_KNOWLEDGE
    assert _committed_guard_passes(POST_KNOWLEDGE) is True
    assert _committed_guard_passes(POST_BASE) is False

    second_dry = _import_knowledge("--dry-run")
    assert _plan_summary(second_dry) == {
        "source_REUSE_EXISTING": 1,
        "history_SKIP_EXISTS": 2,
        "citation_SKIP_EXISTS": 2,
    }
    assert "CREATE" not in second_dry.replace("REUSE_EXISTING", "")
    assert "citations created=0" in _import_knowledge()
    assert _aggregates() == EXPECTED_POST_KNOWLEDGE
    assert _committed_guard_passes(POST_KNOWLEDGE) is True
    assert _state_class() == "ALREADY_MATERIALIZED"
    assert _goriyaku_snapshot() == goriyaku_before
    # the reused legacy Source row（bibliography p.398）is byte-unchanged
    assert list(ShrineKnowledgeSource.objects.filter(url=SOURCE["url"]).values()) == shared_before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "mutation",
    ["coordinate-drift", "goriyaku-text-drift", "goriyaku-tag-drift", "citation+1", "shrine+1"],
)
def test_committed_post_base_guard_fails_closed(tmp_path, mutation):
    _simulate_production_prestate()
    _import_subset(tmp_path)
    assert _committed_guard_passes(POST_BASE) is True
    if mutation == "citation+1":
        _extra_citation_elsewhere()
    elif mutation == "shrine+1":
        Shrine.objects.create(name_jp="無関係神社", kind="shrine", address="架空県2")
    else:
        CONFLICTING_MUTATIONS[mutation]()
    assert _committed_guard_passes(POST_BASE) is False


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", sorted({**CONFLICTING_MUTATIONS, **INCOMPLETE_MUTATIONS}))
def test_committed_post_knowledge_verification_fails_closed(tmp_path, mutation):
    _simulate_production_prestate()
    _materialize(tmp_path)
    assert _committed_guard_passes(POST_KNOWLEDGE) is True
    {**CONFLICTING_MUTATIONS, **INCOMPLETE_MUTATIONS}[mutation]()
    assert _committed_guard_passes(POST_KNOWLEDGE) is False
