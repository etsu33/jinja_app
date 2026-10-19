"""nsrc-000021 荒川神社 G7 Production Import preflight regression（disposable test DB only）。

scripts/migration_safety/sql/nsrc_000021_g7_*.sql は同一の `nsrc_000021_source_identity` block を持ち、
Source（NIIGATA_PREF_KITAMAEBUNE02）を importer semantic identity（source_type + knowledge_seed.normalize_source_url()）として
数える。近似一致は使わない。

guard（pre-Base / post-Base / post-Knowledge）の FROZEN_PRE_STATE は UNSET（frozen_values_set = false、
数値はすべて NULL）で、committed のままでは必ず fail closed する。guard の意味論は、test 内メモリ上で
frozen block を disposable DB 自身の実測値へ置き換えて検証する。commit された SQL / Seed / DB 定義は
変更しない。Production には接続しない。
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
KNOWLEDGE_SEED_PATH = KNOWLEDGE_SEED_DIR / "nsrc_000021_seed.json"
# the other VPG001 Recommendation-track Knowledge Seeds（nsrc-000023 is excluded）
SIBLING_SEED_PATHS = [
    KNOWLEDGE_SEED_DIR / f"nsrc_{cid}_seed.json"
    for cid in ("000021", "000022", "000024", "000025")
    if cid != "000021"
]

PREFLIGHT = "nsrc_000021_g7_preflight.sql"
BACKUP_VERSION_CHECK = "nsrc_000021_g7_backup_version_check.sql"
PRE_BASE = "nsrc_000021_g7_pre_base_guard.sql"
POST_BASE = "nsrc_000021_g7_post_base_guard.sql"
POST_KNOWLEDGE = "nsrc_000021_g7_post_knowledge_verification.sql"
IDENTITY_FILES = (PREFLIGHT, PRE_BASE, POST_BASE, POST_KNOWLEDGE)
GUARD_FILES = (PRE_BASE, POST_BASE, POST_KNOWLEDGE)
ALL_SQL_FILES = (PREFLIGHT, BACKUP_VERSION_CHECK, PRE_BASE, POST_BASE, POST_KNOWLEDGE)
BLOCK_RE = re.compile(
    r"-- BEGIN nsrc_000021_source_identity\n(.*?)-- END nsrc_000021_source_identity\n",
    re.DOTALL,
)
TARGET_RE = re.compile(
    r"-- BEGIN nsrc_000021_target_facts\n(.*?)-- END nsrc_000021_target_facts\n",
    re.DOTALL,
)
FROZEN_RE = re.compile(
    r"-- BEGIN nsrc_000021_frozen_pre_state\n(.*?)-- END nsrc_000021_frozen_pre_state\n",
    re.DOTALL,
)
FROZEN_NAMES = [
    "shrine_total",
    "source_total",
    "deity_total",
    "history_total",
    "citation_total",
    "source_fact_total",
    "collective_total",
    "same_name_other_address_total",
    "foreign_fact_source_relation_total",
    "accepted_source_count",
]

SHRINE_NAME = "荒川神社"
SHRINE_ADDRESS = "新潟県胎内市桃崎浜187番地"
SHRINE_LAT = 38.1409456
SHRINE_LNG = 139.4073314
# G1 で記録済みの同名・別住所 identity（Base Seed には存在しない）
OTHER_SAME_NAME_ADDRESSES = (
    "新潟県新発田市荒川5431番地",
    "新潟県村上市小岩内463番地",
    "新潟県村上市荒川542番地",
)
# 同一住所の別 Fact owner（G1）。Shrine row は存在しない
FOREIGN_SAME_ADDRESS_NAMES = ()

SOURCE = {
    "key": "NIIGATA_PREF_KITAMAEBUNE02",
    "type": "government",
    "url": "https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html",
    "normalized": "https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html",
    "publisher": "新潟県",
    "title": "北前船の魅力を訪ねて",
}
EXPECTED_DEITIES = ["天鈿女命"]
# (history_type, title)
EXPECTED_HISTORIES = [("regional_context", "船主による船絵馬の奉納")]
EXCLUDED_DEITY_NAMES = ()
VERIFIED_AT = "2026-10-19T14:35:38+09:00"

# importer と同じ semantic identity になる表記揺れ
IDENTITY_VARIANTS = (
    "HTTPS://WWW.PREF.NIIGATA.LG.JP/site/shibata/kitamaebune02.html",
    "https://www.pref.niigata.lg.jp:443/site/shibata/kitamaebune02.html",
    "https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html/",
    "https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html#top",
    "  https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html  ",
    "https://u:p@www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html",
)
# importer の identity ではないが、lookalike 診断には必ず拾われる表記（再利用不可）
NON_IDENTITY_LOOKALIKE_VARIANTS = (
    "http://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html",
    "https://pref.niigata.lg.jp/site/shibata/kitamaebune02.html",
    "https://www.pref.niigata.lg.jp/site/shibata/kitamaebune01.html/../kitamaebune02.html",
    "https://www.pref.niigata.lg.jp/site/shibata/Kitamaebune02.html",
    "https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html?p=1",
    "https://www.pref.niigata.lg.jp:8443/site/shibata/kitamaebune02.html",
)
# importer が ValueError で停止する URL（SQL は NULL = identity にならない）
IMPORTER_UNPARSEABLE = (
    "https://www.pref.niigata.lg.jp:abc/site/shibata/kitamaebune02.html",
    "https://www.pref.niigata.lg.jp:99999/site/shibata/kitamaebune02.html",
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


def _foreign_relations() -> int:
    identity = [
        s.pk
        for s in ShrineKnowledgeSource.objects.filter(source_type=SOURCE["type"]).exclude(url="")
        if _python_normalized(s.url) == SOURCE["normalized"]
    ]
    target = Shrine.objects.filter(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    deity = ShrineDeity.sources.through.objects.filter(
        shrineknowledgesource_id__in=identity
    ).exclude(shrinedeity__shrine__in=target)
    history = ShrineHistory.sources.through.objects.filter(
        shrineknowledgesource_id__in=identity
    ).exclude(shrinehistory__shrine__in=target)
    return deity.count() + history.count()


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
        f"    {_foreign_relations()}::bigint AS foreign_fact_source_relation_total,\n"
        f"    {accepted}::bigint AS accepted_source_count\n),\n"
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
        if rows and len(rows[0]) == 9 and rows[0][0] == SOURCE["key"]:
            return rows[0]
    raise AssertionError("source state row missing")


def _create_source(
    url: str,
    *,
    compatible: bool = True,
    source_type: str = "",
    bibliography: str = "",
) -> ShrineKnowledgeSource:
    return ShrineKnowledgeSource.objects.create(
        source_type=source_type or SOURCE["type"],
        title=SOURCE["title"],
        url=url,
        publisher=SOURCE["publisher"] if compatible else "別の発行者",
        bibliography=bibliography,
        verification_status="source_confirmed",
        confidence="high",
        language="ja",
    )


def _base_state() -> None:
    """Disposable pre-state: Base Seed without the target row（Source ABSENT）。"""
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    Shrine.objects.filter(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS).delete()


def _sibling_state() -> None:
    """Repository lineage: the other VPG001 Knowledge Seeds are already materialized."""
    _base_state()
    for path in SIBLING_SEED_PATHS:
        call_command(
            "import_shrine_knowledge", str(path), stdout=io.StringIO(), stderr=io.StringIO()
        )


def _reusable_state() -> None:
    """A metadata-compatible Source identity already exists（Source REUSABLE）。"""
    _sibling_state()
    _create_source(SOURCE["url"])


def _extractor():
    spec = importlib.util.spec_from_file_location(
        "nsrc_000021_g7_extract_base_subset",
        SAFETY_DIR / "nsrc_000021_g7_extract_base_subset.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _guard_module():
    spec = importlib.util.spec_from_file_location(
        "_nsrc_000021_g7_migration_safety_guard", SAFETY_DIR / "guard.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _import_subset(tmp_path: Path, *args: str) -> str:
    module = _extractor()
    subset_path = tmp_path / "nsrc_000021_base_subset.json"
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


def _source() -> ShrineKnowledgeSource:
    (source,) = [
        s
        for s in ShrineKnowledgeSource.objects.filter(source_type=SOURCE["type"])
        if _python_normalized(s.url) == SOURCE["normalized"]
    ]
    return source


def _python_normalized(url: str) -> str | None:
    try:
        return normalize_source_url(url)
    except ValueError:
        return None


# --------------------------------------------------------------------------------------
# 1. SQL file contract
# --------------------------------------------------------------------------------------


def test_every_sql_file_passes_readonly_validation():
    is_readonly_sql = _guard_module().is_readonly_sql
    for name in ALL_SQL_FILES:
        ok, reason = is_readonly_sql(_sql(name))
        assert ok, (name, reason)


def test_sql_files_contain_no_connection_identifier_or_write():
    paths = sorted(SQL_DIR.glob("nsrc_000021_g7_*.sql"))
    assert [p.name for p in paths] == sorted(ALL_SQL_FILES)
    for path in paths:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for token in ("postgres://", "postgresql://", "password", "sslmode", "@localhost"):
            assert token not in lowered, (path.name, token)
        for statement in _statements(text):
            assert re.match(r"^(select|with)\b", statement, re.IGNORECASE), (path.name, statement)
            for verb in ("insert", "update", "delete", "truncate", "alter", "drop", "create"):
                assert not re.search(rf"\b{verb}\b", statement, re.IGNORECASE), (path.name, verb)


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
    assert f"WHERE source_type = '{SOURCE['type']}'" in block
    assert f"normalized_url = '{SOURCE['normalized']}'" in block
    assert f"btrim(COALESCE(publisher, '')) = '{SOURCE['publisher']}'" in block
    target = target_blocks[0]
    assert f"WHERE name_jp = '{SHRINE_NAME}'\n    AND address = '{SHRINE_ADDRESS}'" in target
    for name in EXPECTED_DEITIES:
        assert f"d.display_name = '{name}'" in target
    for history_type, title in EXPECTED_HISTORIES:
        assert f"h.history_type = '{history_type}' AND h.title = '{title}'" in target
    assert target.count(f"TIMESTAMPTZ '{VERIFIED_AT}'") == len(EXPECTED_DEITIES) + len(
        EXPECTED_HISTORIES
    )


def test_frozen_pre_state_is_identical_unset_and_fail_closed_in_every_guard():
    frozen = [FROZEN_RE.findall(_sql(name)) for name in GUARD_FILES]
    assert all(len(found) == 1 for found in frozen)
    assert len({found[0] for found in frozen}) == 1
    text = frozen[0][0]
    assert "    false AS frozen_values_set,\n" in text
    # no Production value is frozen yet: every numeric value is NULL
    assert re.findall(r"^\s+(\S+)::bigint AS (\w+)", text, re.MULTILINE) == [
        ("NULL", name) for name in FROZEN_NAMES
    ]
    assert "true" not in text
    for name in GUARD_FILES:
        assert "  f.frozen_values_set\n" in _sql(name)
    assert FROZEN_RE.findall(_sql(PREFLIGHT)) == []


@pytest.mark.django_db
def test_preflight_tables_are_the_real_model_tables():
    assert ShrineDeity.sources.through._meta.db_table == "temples_shrinedeity_sources"
    assert ShrineHistory.sources.through._meta.db_table == "temples_shrinehistory_sources"
    assert ShrineFactSourceCitation._meta.db_table == "temples_shrinefactsourcecitation"
    referenced = re.findall(r"to_regclass\('public\.(\w+)'\)", _sql(PREFLIGHT))
    existing = set(connection.introspection.table_names())
    assert set(referenced) <= existing


@pytest.mark.django_db
def test_preflight_and_backup_check_run_in_a_read_only_transaction():
    _sibling_state()
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
    # The pytest DB uses temples.migrations_nogis, so the 0121 flag reports exactly what the
    # ledger holds; Production must report True.
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
       EXISTS (SELECT 1 FROM source_identity i WHERE i.id = n.id),
       EXISTS (SELECT 1 FROM source_metadata_compatible m WHERE m.id = n.id),
       EXISTS (SELECT 1 FROM source_url_lookalike l WHERE l.id = n.id)
FROM source_url_norm n
"""
    )
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return {row[0]: tuple(row[1:]) for row in cursor.fetchall()}


def test_seed_source_matches_the_sql_identity():
    seed = json.loads(KNOWLEDGE_SEED_PATH.read_text(encoding="utf-8"))
    (source,) = seed["sources"]
    assert (source["key"], source["source_type"], source["url"], source["publisher"]) == (
        SOURCE["key"],
        SOURCE["type"],
        SOURCE["url"],
        SOURCE["publisher"],
    )
    assert normalize_source_url(source["url"]) == SOURCE["normalized"]
    assert source.get("bibliography", "") == ""
    (shrine,) = seed["shrines"]
    assert [d["display_name"] for d in shrine["deities"]] == EXPECTED_DEITIES
    assert [(h["history_type"], h["title"]) for h in shrine["histories"]] == EXPECTED_HISTORIES
    for name in EXCLUDED_DEITY_NAMES:
        assert name not in json.dumps(seed, ensure_ascii=False)


@pytest.mark.django_db
def test_sql_normalized_url_equals_importer_normalize_source_url():
    urls = [
        *GENERAL_CORPUS,
        SOURCE["url"],
        *IDENTITY_VARIANTS,
        *NON_IDENTITY_LOOKALIKE_VARIANTS,
        *IMPORTER_UNPARSEABLE,
    ]
    created = {
        ShrineKnowledgeSource.objects.create(
            source_type=SOURCE["type"], title=f"t{i}", url=url
        ).pk: url
        for i, url in enumerate(urls)
    }
    rows = _sql_rows()
    for pk, url in created.items():
        assert rows[pk][0] == _python_normalized(url), url


@pytest.mark.django_db
def test_identity_count_uses_importer_semantics_only():
    identity = {_create_source(u).pk: u for u in (SOURCE["url"], *IDENTITY_VARIANTS)}
    lookalike = {_create_source(u).pk: u for u in NON_IDENTITY_LOOKALIKE_VARIANTS}
    unparseable = {_create_source(u).pk: u for u in IMPORTER_UNPARSEABLE}
    wrong_type = _create_source(SOURCE["url"], source_type="secondary_editorial").pk
    rows = _sql_rows()

    # rows[pk] = (normalized_url, is_identity, is_metadata_compatible, is_lookalike)
    for pk, url in identity.items():
        assert normalize_source_url(url) == SOURCE["normalized"], url
        assert rows[pk][1:] == (True, True, True), url
    for pk, url in lookalike.items():
        assert _python_normalized(url) != SOURCE["normalized"], url
        assert rows[pk][1] is False and rows[pk][3] is True, url
    for pk, url in unparseable.items():
        assert _python_normalized(url) is None, url
        assert rows[pk][0] is None and rows[pk][1] is False, url
    # 同じ URL でも source_type が違えば identity ではない（lookalike としてだけ拾う）
    assert rows[wrong_type][1] is False and rows[wrong_type][3] is True


@pytest.mark.django_db
def test_metadata_compatibility_follows_the_importer_reuse_fields():
    compatible = _create_source(SOURCE["url"]).pk
    drifted = _create_source(SOURCE["url"], compatible=False).pk
    with_bibliography = _create_source(SOURCE["url"], bibliography="p.1").pk
    rows = _sql_rows()
    assert rows[compatible][1:3] == (True, True)
    assert rows[drifted][1:3] == (True, False)
    assert rows[with_bibliography][1:3] == (True, False)


# --------------------------------------------------------------------------------------
# 3. Fail-closed guards + Source-state simulations
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_committed_unset_guards_always_fail_closed(tmp_path):
    _sibling_state()
    for name in GUARD_FILES:
        with pytest.raises(DataError, match="division by zero"):
            with transaction.atomic():
                _run_all(_sql(name))
    # still fail closed in the states each guard is written for
    _import_subset(tmp_path)
    for name in GUARD_FILES:
        with pytest.raises(DataError, match="division by zero"):
            with transaction.atomic():
                _run_all(_sql(name))
    _import_knowledge()
    for name in GUARD_FILES:
        with pytest.raises(DataError, match="division by zero"):
            with transaction.atomic():
                _run_all(_sql(name))


SOURCE_STATE_CASES = {
    # case -> (setup, expected source state, expected class, accepted count or None)
    "absent": (lambda: None, "ABSENT", "CLEAN_CREATE", 0),
    "reusable": (lambda: _create_source(SOURCE["url"]), "REUSABLE", "CLEAN_CREATE", 1),
    "reusable-url-variant": (
        lambda: _create_source(IDENTITY_VARIANTS[1]),
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
    "bibliography-drift": (
        lambda: _create_source(SOURCE["url"], bibliography="p.1"),
        "CONFLICT_METADATA_DRIFT",
        "CONFLICT",
        None,
    ),
    "identity-ambiguous": (
        lambda: (_create_source(SOURCE["url"]), _create_source(IDENTITY_VARIANTS[1])),
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
    "reusable-plus-lookalike": (
        lambda: (_create_source(SOURCE["url"]), _create_source(NON_IDENTITY_LOOKALIKE_VARIANTS[4])),
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
    _sibling_state()
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


def _filler_history() -> ShrineHistory:
    return ShrineHistory.objects.get_or_create(
        shrine=_filler_shrine(), history_type="tradition", title="filler", content="x"
    )[0]


def _citation_elsewhere() -> None:
    history = _filler_history()
    source = ShrineKnowledgeSource.objects.create(
        source_type="internal_research", title="c", url="https://example.invalid/citation"
    )
    history.sources.add(source)
    ShrineFactSourceCitation.objects.create(
        shrine_history=history, source=source, locator_text="p.1"
    )


def _foreign_relation_to_source() -> None:
    _filler_history().sources.add(_source())


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
    "citation+1": _citation_elsewhere,
    "source-fact+1": lambda: ShrineSourceFact.objects.create(
        shrine=_filler_shrine(),
        stable_key="g7-extra",
        source_attested_wording="x",
        evidence_characterization="official_prayer_supported",
    ),
    "collective+1": lambda: ShrineDeityCollective.objects.create(
        shrine=_filler_shrine(), source_attested_label="extra"
    ),
    "existing-target-row": lambda: Shrine.objects.create(
        name_jp=SHRINE_NAME, kind="shrine", address=SHRINE_ADDRESS
    ),
    "same-address-different-name": lambda: Shrine.objects.create(
        name_jp="G7別名神社", kind="shrine", address=SHRINE_ADDRESS
    ),
    "source-metadata-drift": lambda: ShrineKnowledgeSource.objects.filter(pk=_source().pk).update(
        publisher="別の発行者"
    ),
    "source-identity-ambiguous": lambda: _create_source(IDENTITY_VARIANTS[1]),
    "source-lookalike": lambda: _create_source(NON_IDENTITY_LOOKALIKE_VARIANTS[1]),
    "source-unparseable": lambda: _create_source(IMPORTER_UNPARSEABLE[1]),
    "foreign-relation-to-source": _foreign_relation_to_source,
}
if OTHER_SAME_NAME_ADDRESSES:
    PRESTATE_DRIFT["same-name-other-address+1"] = lambda: Shrine.objects.create(
        name_jp=SHRINE_NAME, kind="shrine", address=OTHER_SAME_NAME_ADDRESSES[0]
    )


@pytest.mark.django_db
def test_frozen_guard_passes_only_on_the_frozen_prestate():
    _reusable_state()
    frozen = _frozen_values(accepted=1)
    assert _guard_passes(PRE_BASE, frozen) is True
    assert _guard_passes(POST_BASE, frozen) is False
    assert _guard_passes(POST_KNOWLEDGE, frozen) is False


@pytest.mark.django_db
@pytest.mark.parametrize("drift", sorted(PRESTATE_DRIFT))
def test_pre_base_guard_fails_on_any_prestate_drift(drift):
    _reusable_state()
    _filler_history()
    frozen = _frozen_values(accepted=1)
    assert _guard_passes(PRE_BASE, frozen) is True
    PRESTATE_DRIFT[drift]()
    assert _guard_passes(PRE_BASE, frozen) is False


# --------------------------------------------------------------------------------------
# 4. Exact target identity
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_same_name_other_address_rows_never_become_the_target():
    _sibling_state()
    for address in OTHER_SAME_NAME_ADDRESSES:
        Shrine.objects.create(name_jp=SHRINE_NAME, kind="shrine", address=address)

    results = _preflight_results()
    n = len(OTHER_SAME_NAME_ADDRESSES)
    # target / same-name / same-name other address / same-address / same-address other name
    assert results[5][0] == (0, n, n, 0, 0)
    assert {row[2] for row in results[6]} == set(OTHER_SAME_NAME_ADDRESSES)
    assert all(row[-1] is False for row in results[6])
    assert _state_class() == "CLEAN_CREATE"

    frozen = _frozen_values(accepted=0)
    assert f"{n}::bigint AS same_name_other_address_total" in frozen
    assert _guard_passes(PRE_BASE, frozen) is True

    # a same-address collision is a CONFLICT, whatever the name
    Shrine.objects.create(name_jp="G7別名神社", kind="shrine", address=SHRINE_ADDRESS)
    assert _state_class() == "CONFLICT"
    assert _guard_passes(PRE_BASE, frozen) is False


@pytest.mark.django_db
@pytest.mark.parametrize("name", FOREIGN_SAME_ADDRESS_NAMES or ("G7別名神社",))
def test_same_address_foreign_owner_is_a_conflict(tmp_path, name):
    _sibling_state()
    _import_subset(tmp_path)
    Shrine.objects.create(name_jp=name, kind="shrine", address=SHRINE_ADDRESS)
    assert _state_class() == "CONFLICT"


# --------------------------------------------------------------------------------------
# 5. Target state classification
# --------------------------------------------------------------------------------------


def _materialize(tmp_path) -> Shrine:
    _import_subset(tmp_path)
    _import_knowledge()
    return _target()


def _first_fact():
    deity = ShrineDeity.objects.filter(shrine=_target()).order_by("id").first()
    return deity or ShrineHistory.objects.filter(shrine=_target()).order_by("id").first()


def _other_source() -> ShrineKnowledgeSource:
    return ShrineKnowledgeSource.objects.create(
        source_type="internal_research", title="other", url="https://example.invalid/other"
    )


def _goriyaku_tag_link() -> None:
    _target().goriyaku_tags.add(GoriyakuTag.objects.create(name="G7テストタグ"))


def _goriyaku_assignment() -> None:
    ShrineGoriyakuAssignment.objects.create(
        shrine=_target(),
        canonical_key="goriyaku:misfortune_warding",
        taxonomy_version="v1",
        lifecycle=ShrineGoriyakuAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=timezone.now(),
    )


def _move_first_fact_to_other_shrine() -> None:
    fact = _first_fact()
    type(fact).objects.filter(pk=fact.pk).update(shrine=_filler_shrine())


# shared by the preflight CONFLICT matrix and the post-Knowledge negative matrix
CONFLICTING_MUTATIONS = {
    "unexpected-deity": lambda: ShrineDeity.objects.create(
        shrine=_target(), display_name=(EXCLUDED_DEITY_NAMES or ("G7余分祭神",))[0]
    ),
    "deity-name-drift": lambda: ShrineDeity.objects.filter(
        shrine=_target(), display_name=EXPECTED_DEITIES[0]
    ).update(display_name=EXPECTED_DEITIES[0] + "x"),
    "unexpected-history": lambda: ShrineHistory.objects.create(
        shrine=_target(), history_type="tradition", title="extra", content="x"
    ),
    "extra-fact-source-relation": lambda: _first_fact().sources.add(_other_source()),
    "relation-moved-to-other-source": lambda: _first_fact().sources.set([_other_source()]),
    "citation-created": lambda: ShrineFactSourceCitation.objects.create(
        shrine_deity=ShrineDeity.objects.filter(shrine=_target()).first(),
        source=_source(),
        locator_text="p.1",
    ),
    "source-fact-created": lambda: ShrineSourceFact.objects.create(
        shrine=_target(),
        stable_key="g7-nsrc-000021-extra",
        source_attested_wording="x",
        evidence_characterization="official_prayer_supported",
    ),
    "collective-created": lambda: ShrineDeityCollective.objects.create(
        shrine=_target(), source_attested_label="extra"
    ),
    "goriyaku-text-drift": lambda: Shrine.objects.filter(pk=_target().pk).update(goriyaku="縁結び"),
    "goriyaku-tag-drift": _goriyaku_tag_link,
    "goriyaku-assignment-drift": _goriyaku_assignment,
    "coordinate-drift": lambda: Shrine.objects.filter(pk=_target().pk).update(
        latitude=SHRINE_LAT + 0.0001
    ),
    "source-metadata-drift": lambda: ShrineKnowledgeSource.objects.filter(pk=_source().pk).update(
        publisher="別の発行者"
    ),
}
if EXPECTED_HISTORIES:
    CONFLICTING_MUTATIONS["history-content-drift"] = lambda: ShrineHistory.objects.filter(
        shrine=_target(), title=EXPECTED_HISTORIES[0][1]
    ).update(content="x")
    CONFLICTING_MUTATIONS["history-type-drift"] = lambda: ShrineHistory.objects.filter(
        shrine=_target(), title=EXPECTED_HISTORIES[0][1]
    ).update(history_type="editorial_summary")
# A missing Fact / relation is incomplete, not contradictory: the preflight reports
# PARTIAL_EXISTING, and the post-Knowledge verification fails.
INCOMPLETE_MUTATIONS = {
    "missing-deity": lambda: (
        ShrineDeity.objects.filter(shrine=_target()).order_by("id").last().delete()
    ),
    "source-less-fact": lambda: _first_fact().sources.clear(),
    "wrong-fact-owner": _move_first_fact_to_other_shrine,
}
if EXPECTED_HISTORIES:
    INCOMPLETE_MUTATIONS["missing-history"] = lambda: (
        ShrineHistory.objects.filter(shrine=_target()).order_by("id").last().delete()
    )


@pytest.mark.django_db
def test_state_class_follows_the_target_lifecycle(tmp_path):
    _sibling_state()
    assert _state_class() == "CLEAN_CREATE"
    _import_subset(tmp_path)
    assert _state_class() == "PARTIAL_EXISTING"  # Base only, Knowledge absent
    _import_knowledge()
    assert _state_class() == "ALREADY_MATERIALIZED"
    n_deity, n_history = len(EXPECTED_DEITIES), len(EXPECTED_HISTORIES)
    assert _preflight_results()[-1][0] == (
        "ALREADY_MATERIALIZED",
        1,
        1,
        1,
        n_deity,
        n_history,
        n_deity + n_history,
        0,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", sorted(CONFLICTING_MUTATIONS))
def test_preflight_classifies_contradicting_target_state_as_conflict(tmp_path, mutation):
    _sibling_state()
    _materialize(tmp_path)
    CONFLICTING_MUTATIONS[mutation]()
    assert _state_class() == "CONFLICT"


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", sorted(INCOMPLETE_MUTATIONS))
def test_preflight_classifies_incomplete_target_state_as_partial(tmp_path, mutation):
    _sibling_state()
    _materialize(tmp_path)
    INCOMPLETE_MUTATIONS[mutation]()
    assert _state_class() == "PARTIAL_EXISTING"


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
    assert (rows[0]["goriyaku"], rows[0]["kyusei"], rows[0]["astro_elements"]) == ("", None, [])
    assert (
        hashlib.sha256(first.encode("utf-8")).hexdigest()
        == hashlib.sha256(second.encode("utf-8")).hexdigest()
        == "9a608bc049ff4e6c4bfa2ca851c38df7f7d22f839eef49b3fb31f0cdcf5564b2"
    )


def test_full_base_seed_is_never_the_production_payload():
    module = _extractor()
    full = json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))
    subset = json.loads(module.render(module.extract_subset()))
    assert len(full) > 1
    assert len(subset) == 1
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
        ("latitude", SHRINE_LAT + 0.0001),
        ("longitude", SHRINE_LNG + 0.0001),
        ("location", {"lat": SHRINE_LAT + 0.0001, "lng": SHRINE_LNG}),
        ("goriyaku", "縁結び"),
        ("kyusei", "一白水星"),
        ("astro_elements", ["火"]),
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

    # a same-name row at another address alone is never extracted
    path = tmp_path / "other.json"
    other = {**module.EXPECTED_ROW, "address": "架空県架空市9-9"}
    path.write_text(json.dumps([other], ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit, match="exactly 1"):
        module.extract_subset(path)


def test_extractor_refuses_repository_output_path():
    module = _extractor()
    assert module.main(["x", str(REPO_ROOT / "nsrc_000021_subset.json")]) == 1
    assert not (REPO_ROOT / "nsrc_000021_subset.json").exists()


def test_extractor_writes_outside_the_repository(tmp_path, capsys):
    module = _extractor()
    output = tmp_path / "subset.json"
    assert module.main(["x", str(output)]) == 0
    out = capsys.readouterr().out
    assert "SUBSET_ROWS=1" in out
    assert "SUBSET_SHA256=9a608bc049ff4e6c4bfa2ca851c38df7f7d22f839eef49b3fb31f0cdcf5564b2" in out
    assert json.loads(output.read_text(encoding="utf-8")) == [module.EXPECTED_ROW]


# --------------------------------------------------------------------------------------
# 7. Sequential rehearsal（in-memory frozen values from the disposable pre-state）
# --------------------------------------------------------------------------------------

_FIRST_PLAN = {
    k: v
    for k, v in {
        "deity_CREATE": len(EXPECTED_DEITIES),
        "history_CREATE": len(EXPECTED_HISTORIES),
    }.items()
    if v
}
_SECOND_PLAN = {
    k: v
    for k, v in {
        "source_REUSE_EXISTING": 1,
        "deity_SKIP_EXISTS": len(EXPECTED_DEITIES),
        "history_SKIP_EXISTS": len(EXPECTED_HISTORIES),
    }.items()
    if v
}
REHEARSALS = {
    # lineage -> (setup, accepted, first Knowledge plan, second Knowledge plan)
    "source-absent-base-only": (_base_state, 0, {"source_CREATE": 1, **_FIRST_PLAN}, _SECOND_PLAN),
    "source-absent-vpg001-siblings": (
        _sibling_state,
        0,
        {"source_CREATE": 1, **_FIRST_PLAN},
        _SECOND_PLAN,
    ),
    "source-reusable": (
        _reusable_state,
        1,
        {"source_REUSE_EXISTING": 1, **_FIRST_PLAN},
        _SECOND_PLAN,
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
    source_before = list(ShrineKnowledgeSource.objects.filter(url=SOURCE["url"]).values())

    # pre-Base guard
    assert _guard_passes(PRE_BASE, frozen) is True
    assert _guard_passes(POST_BASE, frozen) is False
    assert _guard_passes(POST_KNOWLEDGE, frozen) is False

    # target-only Base: dry-run -> apply -> second dry-run / apply（idempotency）
    _import_subset(tmp_path, "--dry-run")
    assert _aggregates() == pre
    assert "created=1 updated=0 skipped=0 total_seed=1" in _import_subset(tmp_path)
    assert "created=0 updated=0 skipped=1 total_seed=1" in _import_subset(tmp_path, "--dry-run")
    assert "created=0 updated=0 skipped=1 total_seed=1" in _import_subset(tmp_path)
    assert _aggregates() == {**pre, "shrine": pre["shrine"] + 1}

    # post-Base guard
    assert _guard_passes(POST_BASE, frozen) is True
    assert _guard_passes(PRE_BASE, frozen) is False
    assert _guard_passes(POST_KNOWLEDGE, frozen) is False
    assert _goriyaku_snapshot() == goriyaku_before

    # Knowledge: validate-only -> dry-run -> apply -> second import（idempotency）
    assert "validate-only: OK, no errors" in _import_knowledge("--validate-only")
    dry = _import_knowledge("--dry-run")
    assert _plan_summary(dry) == first_plan
    assert "dry-run: OK, no DB writes performed" in dry
    assert _aggregates() == {**pre, "shrine": pre["shrine"] + 1}
    applied = _import_knowledge()
    assert _plan_summary(applied) == first_plan
    assert (
        f"import complete: sources created={1 - accepted}, deities created={len(EXPECTED_DEITIES)}, "
        f"histories created={len(EXPECTED_HISTORIES)}, collectives created=0, "
        "memberships created=0, source_facts created=0"
    ) in applied
    expected_post = {
        **pre,
        "shrine": pre["shrine"] + 1,
        "source": pre["source"] + (1 - accepted),
        "deity": pre["deity"] + len(EXPECTED_DEITIES),
        "history": pre["history"] + len(EXPECTED_HISTORIES),
    }
    assert _aggregates() == expected_post
    ids_after_first = (
        list(ShrineDeity.objects.order_by("id").values_list("id", flat=True)),
        list(ShrineHistory.objects.order_by("id").values_list("id", flat=True)),
    )

    second_dry = _import_knowledge("--dry-run")
    assert _plan_summary(second_dry) == second_plan
    assert "CREATE" not in second_dry
    second_apply = _import_knowledge()
    assert "CREATE" not in second_apply
    assert _aggregates() == expected_post
    assert ids_after_first == (
        list(ShrineDeity.objects.order_by("id").values_list("id", flat=True)),
        list(ShrineHistory.objects.order_by("id").values_list("id", flat=True)),
    )

    # post-Knowledge verification
    assert _guard_passes(POST_KNOWLEDGE, frozen) is True
    assert _guard_passes(POST_BASE, frozen) is False
    assert _guard_passes(PRE_BASE, frozen) is False
    assert _state_class() == "ALREADY_MATERIALIZED"
    assert _goriyaku_snapshot() == goriyaku_before

    shrine = _target()
    source = _source()
    if accepted:
        # the reused pre-existing Source row is byte-unchanged
        assert list(ShrineKnowledgeSource.objects.filter(url=SOURCE["url"]).values()) == (
            source_before
        )
    deities = list(ShrineDeity.objects.filter(shrine=shrine).order_by("id"))
    assert [d.display_name for d in deities] == EXPECTED_DEITIES
    histories = list(ShrineHistory.objects.filter(shrine=shrine).order_by("id"))
    assert [(h.history_type, h.title) for h in histories] == EXPECTED_HISTORIES
    for fact in [*deities, *histories]:
        assert list(fact.sources.all()) == [source]
        assert fact.verified_at.isoformat() == "2026-10-19T05:35:38+00:00"


# --------------------------------------------------------------------------------------
# 8. Post-Base / post-Knowledge negatives
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", sorted({**CONFLICTING_MUTATIONS, **INCOMPLETE_MUTATIONS}))
def test_post_knowledge_verification_fails_closed(tmp_path, mutation):
    _sibling_state()
    frozen = _frozen_values(accepted=0)
    _materialize(tmp_path)
    assert _guard_passes(POST_KNOWLEDGE, frozen) is True
    {**CONFLICTING_MUTATIONS, **INCOMPLETE_MUTATIONS}[mutation]()
    assert _guard_passes(POST_KNOWLEDGE, frozen) is False


@pytest.mark.django_db
@pytest.mark.parametrize(
    "drift", ["shrine+1", "citation+1", "foreign-relation-to-source", "same-address-different-name"]
)
def test_post_knowledge_verification_fails_on_aggregate_or_foreign_drift(tmp_path, drift):
    _sibling_state()
    frozen = _frozen_values(accepted=0)
    _materialize(tmp_path)
    assert _guard_passes(POST_KNOWLEDGE, frozen) is True
    PRESTATE_DRIFT[drift]()
    assert _guard_passes(POST_KNOWLEDGE, frozen) is False


@pytest.mark.django_db
@pytest.mark.parametrize(
    "mutation",
    [
        "shrine+1",
        "coordinate-drift",
        "goriyaku-text-drift",
        "goriyaku-tag-drift",
        "goriyaku-assignment-drift",
        "unexpected-deity",
        "same-address-different-name",
    ],
)
def test_post_base_guard_fails_closed(tmp_path, mutation):
    _sibling_state()
    frozen = _frozen_values(accepted=0)
    _import_subset(tmp_path)
    assert _guard_passes(POST_BASE, frozen) is True
    {**PRESTATE_DRIFT, **CONFLICTING_MUTATIONS}[mutation]()
    assert _guard_passes(POST_BASE, frozen) is False


# --------------------------------------------------------------------------------------
# 9. Runtime QA rehearsal（READ ONLY transaction）
# --------------------------------------------------------------------------------------


def _runtime_qa():
    spec = importlib.util.spec_from_file_location(
        "nsrc_000021_g7_runtime_qa", SAFETY_DIR / "nsrc_000021_g7_runtime_qa.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_qa_script_is_read_only_by_construction():
    tree = ast.parse((SAFETY_DIR / "nsrc_000021_g7_runtime_qa.py").read_text(encoding="utf-8"))
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    first = main.body[0]
    assert isinstance(first, ast.With)
    assert ast.unparse(first.items[0].context_expr) == "transaction.atomic()"
    executes = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "execute"
    ]
    assert [ast.unparse(n) for n in executes] == ["cursor.execute('SET TRANSACTION READ ONLY')"]
    forbidden = {
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
    }
    calls = {
        n.func.attr
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
    }
    assert not calls & forbidden
    text = (SAFETY_DIR / "nsrc_000021_g7_runtime_qa.py").read_text(encoding="utf-8")
    for token in ("subprocess", "psycopg", "socket", "requests", "urllib", "environ["):
        assert token not in text


@pytest.mark.django_db(transaction=True)
def test_runtime_qa_rehearsal_passes_read_only(tmp_path, capsys):
    _sibling_state()
    _materialize(tmp_path)

    module = _runtime_qa()
    before = _aggregates()
    capsys.readouterr()
    module.main()
    out = capsys.readouterr().out
    assert _aggregates() == before
    for line in (
        "TARGET_IDENTITY=PASS",
        "DETAIL_RUNTIME=PASS",
        "SOURCE_RELATION_INTEGRITY=PASS",
        "SHARED_ELIGIBILITY=PASS",
        "CONCIERGE_CANDIDATE_PATH=PASS",
        "RECOMMENDATION_REASON=PASS",
        "COMPASS_DISTANCE=PASS",
        "COMPASS_DIRECTION=PASS",
        "GORIYAKU_ISOLATION=PASS",
        "FACT_OWNERSHIP_ISOLATION=PASS",
        "AGGREGATES_UNCHANGED=PASS",
        "G7_PRODUCTION_RUNTIME_QA=PASS",
        "TRANSACTION_MODE=READ_ONLY",
    ):
        assert line in out, line


@pytest.mark.django_db(transaction=True)
def test_runtime_qa_transaction_rejects_writes(tmp_path):
    _sibling_state()
    _materialize(tmp_path)
    from django.db import InternalError

    with pytest.raises(InternalError, match="read-only transaction"):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
            Shrine.objects.filter(pk=_target().pk).update(goriyaku="x")


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "mutation",
    [
        "unexpected-deity",
        "deity-name-drift",
        "source-metadata-drift",
        "goriyaku-text-drift",
        "coordinate-drift",
        "same-address-different-name",
    ],
)
def test_runtime_qa_fails_closed(tmp_path, mutation):
    _sibling_state()
    _materialize(tmp_path)
    {**PRESTATE_DRIFT, **CONFLICTING_MUTATIONS}[mutation]()
    with pytest.raises((AssertionError, Shrine.DoesNotExist)):
        _runtime_qa().main()
