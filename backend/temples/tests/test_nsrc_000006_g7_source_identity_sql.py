"""nsrc-000006 赤井神社 G7 Production Import preflight regression（disposable test DB only）。

scripts/migration_safety/sql/nsrc_000006_g7_*.sql は同一の `nsrc_000006_source_identity`
block を持ち、S2 / S3 を独立した importer semantic identity（source_type +
knowledge_seed.normalize_source_url()）として数える。近似一致は使わない。

guard（pre-Base / post-Base / post-Knowledge）の FROZEN_PRE_STATE は Mother Ship が
Production で read-only 実行した nsrc_000006_g7_preflight.sql の実測値（PRODUCTION_PRESTATE）で固定済み。

- committed guard は、PRODUCTION_PRESTATE と完全一致させた disposable DB の simulated pre-state に対して
  そのまま（frozen 値を変えずに）実行し、sequential rehearsal / drift / negative を検証する。
- Source-state の conflict matrix と既存 rehearsal / negative は、test 内メモリ上だけで frozen block を
  disposable DB の実測値へ置き換え、guard の意味を引き続き検証する。
commit された SQL / Seed / DB 定義は変更しない。Production には接続しない。
"""

from __future__ import annotations

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
from temples.models import (
    GoriyakuTag,
    Shrine,
    ShrineDeity,
    ShrineDeityCollective,
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
KNOWLEDGE_SEED_PATH = DATA_DIR / "knowledge_seeds" / "nsrc_000006_seed.json"

SQL_FILES = (
    "nsrc_000006_g7_preflight.sql",
    "nsrc_000006_g7_pre_base_guard.sql",
    "nsrc_000006_g7_post_base_guard.sql",
    "nsrc_000006_g7_post_knowledge_verification.sql",
)
GUARD_FILES = SQL_FILES[1:]
PRE = "nsrc_000006_g7_pre_base_guard.sql"
POST_BASE = "nsrc_000006_g7_post_base_guard.sql"
POST_KNOWLEDGE = "nsrc_000006_g7_post_knowledge_verification.sql"
BLOCK_RE = re.compile(
    r"-- BEGIN nsrc_000006_source_identity\n(.*?)-- END nsrc_000006_source_identity\n",
    re.DOTALL,
)
FROZEN_RE = re.compile(
    r"-- BEGIN nsrc_000006_frozen_pre_state\n(.*?)-- END nsrc_000006_frozen_pre_state\n",
    re.DOTALL,
)

SHRINE_NAME = "赤井神社"
SHRINE_ADDRESS = "新潟県佐渡市加茂歌代2662番地"
SHRINE_LAT = 38.085938
SHRINE_LNG = 138.418312
NON_CANONICAL_ADDRESSES = (
    "新潟県佐渡市加茂歌代2622番地",
    "新潟県佐渡市加茂歌代1164-7",
)

S2 = {
    "label": "s2",
    "type": "tourism_official",
    "url": "https://sado-geinou.com/geinou/kamoutashiro/",
    "normalized": "https://sado-geinou.com/geinou/kamoutashiro",
    "publisher": "佐渡芸能アーカイブ",
    "bibliography": "",
    "title": "加茂歌代まつりの鬼太鼓",
}
S3 = {
    "label": "s3",
    "type": "local_history",
    "url": "https://dl.ndl.go.jp/pid/971197",
    "normalized": "https://dl.ndl.go.jp/pid/971197",
    "publisher": "新潟県神職会佐渡支部",
    "bibliography": "新潟県神職会佐渡支部 編, 1926（大正15）, NDL書誌ID 000000585602",
    "title": "佐渡神社誌",
}
SOURCES = (S2, S3)

H1_TITLE = "4月16日の赤井神社例祭と鬼太鼓奉納"
H2_TITLE = "元日午前0時の鬼太鼓奉納"
H3_TITLE = "加茂の五神社としての記録"
EXPECTED_RELATIONS = {H1_TITLE: [S2["url"]], H2_TITLE: [S2["url"]], H3_TITLE: [S3["url"]]}

# Mother Ship が Production で read-only 実行した nsrc_000006_g7_preflight.sql の実測値（PR #3210 後）。
PRODUCTION_PRESTATE = {
    "shrine_total": 123,
    "source_total": 143,
    "deity_total": 295,
    "history_total": 231,
    "source_fact_total": 34,
    "collective_total": 6,
    "same_name_other_address_total": 0,
    "s2_accepted_source_count": 0,
    "s3_accepted_source_count": 0,
}
AGGREGATE_KEYS = {
    "shrine": "shrine_total",
    "source": "source_total",
    "deity": "deity_total",
    "history": "history_total",
    "source_fact": "source_fact_total",
    "collective": "collective_total",
}
PRODUCTION_AGGREGATES = {key: PRODUCTION_PRESTATE[name] for key, name in AGGREGATE_KEYS.items()}
EXPECTED_POST_BASE = {**PRODUCTION_AGGREGATES, "shrine": 124}
EXPECTED_POST_KNOWLEDGE = {
    **PRODUCTION_AGGREGATES,
    "shrine": 124,
    "source": 145,
    "history": 234,
}

# importer と同じ semantic identity になる表記揺れ
IDENTITY_VARIANTS = {
    "s2": (
        S2["url"],
        "https://sado-geinou.com/geinou/kamoutashiro",
        "HTTPS://SADO-GEINOU.COM/geinou/kamoutashiro/",
        "https://sado-geinou.com:443/geinou/kamoutashiro/",
        "https://sado-geinou.com/geinou/kamoutashiro///",
        "https://sado-geinou.com/geinou/kamoutashiro/#movie",
        "  https://sado-geinou.com/geinou/kamoutashiro/  ",
    ),
    "s3": (
        S3["url"],
        "https://dl.ndl.go.jp/pid/971197/",
        "HTTPS://DL.NDL.GO.JP/pid/971197",
        "https://dl.ndl.go.jp:443/pid/971197",
        "https://dl.ndl.go.jp/pid/971197#page",
        "https://u:p@dl.ndl.go.jp/pid/971197",
        "　https://dl.ndl.go.jp/pid/971197　",
    ),
}
# importer の identity ではないが、lookalike 診断には必ず拾われる表記（再利用不可）
NON_IDENTITY_LOOKALIKE_VARIANTS = {
    "s2": (
        "http://sado-geinou.com/geinou/kamoutashiro/",
        "https://www.sado-geinou.com/geinou/kamoutashiro/",
        "https://sado-geinou.com/Geinou/kamoutashiro/",
        "https://sado-geinou.com/geinou/kamoutashiro/?lang=en",
        "https://sado-geinou.com/geinou/kamoutashiro2/",
        "https://sado-geinou.com:8443/geinou/kamoutashiro/",
    ),
    "s3": (
        "http://dl.ndl.go.jp/pid/971197",
        "https://dl.ndl.go.jp/pid/9711970",
        "https://dl.ndl.go.jp/pid/971197/1/5",
        "https://dl.ndl.go.jp/ja/pid/971197",
        "https://dl.ndl.go.jp/pid/971197?page=3",
        "dl.ndl.go.jp/pid/971197",
    ),
}
# importer が ValueError で停止する URL（SQL は NULL = identity にならない）
IMPORTER_UNPARSEABLE = {
    "s2": ("https://sado-geinou.com:abc/geinou/kamoutashiro/",),
    "s3": ("https://dl.ndl.go.jp:99999/pid/971197",),
}
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
# SQL text helpers（disposable DB だけで使う）
# --------------------------------------------------------------------------------------


def _sql(name: str) -> str:
    return (SQL_DIR / name).read_text(encoding="utf-8")


def _block() -> str:
    return BLOCK_RE.findall(_sql(SQL_FILES[0]))[0]


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
        "source_fact": "temples_shrinesourcefact",
        "collective": "temples_shrinedeitycollective",
    }
    out = {}
    with connection.cursor() as cursor:
        for key, table in tables.items():
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            out[key] = cursor.fetchone()[0]
    return out


def _frozen_values(*, s2_accepted: int, s3_accepted: int) -> str:
    """Disposable-DB pre-state as a frozen block（rehearsal only; never Production values）."""
    counts = _aggregates()
    same_name_other = Shrine.objects.filter(name_jp=SHRINE_NAME).exclude(address=SHRINE_ADDRESS)
    return (
        "frozen AS (\n  SELECT\n    true AS frozen_values_set,\n"
        f"    {counts['shrine']}::bigint AS shrine_total,\n"
        f"    {counts['source']}::bigint AS source_total,\n"
        f"    {counts['deity']}::bigint AS deity_total,\n"
        f"    {counts['history']}::bigint AS history_total,\n"
        f"    {counts['source_fact']}::bigint AS source_fact_total,\n"
        f"    {counts['collective']}::bigint AS collective_total,\n"
        f"    {same_name_other.count()}::bigint AS same_name_other_address_total,\n"
        f"    {s2_accepted}::bigint AS s2_accepted_source_count,\n"
        f"    {s3_accepted}::bigint AS s3_accepted_source_count\n),\n"
    )


def _with_frozen(name: str, frozen: str) -> str:
    """Rehearsal only: replace the UNSET frozen block in memory. The committed file is untouched."""
    text = _sql(name)
    assert len(FROZEN_RE.findall(text)) == 1
    return FROZEN_RE.sub(lambda _: frozen, text)


def _passes(text: str) -> bool:
    try:
        with transaction.atomic():
            rows = _run_all(text)
    except DataError:  # division_by_zero = guard FAIL
        return False
    assert rows[-1] == [(1,)]
    return True


def _guard_passes(name: str, frozen: str) -> bool:
    return _passes(_with_frozen(name, frozen))


def _committed_guard_passes(name: str) -> bool:
    """Run the committed guard file unchanged（frozen = Production measurement）."""
    return _passes(_sql(name))


def _state_class() -> tuple:
    return _run_all(_sql("nsrc_000006_g7_preflight.sql"))[-1][0]


def _source_states() -> dict[str, str]:
    states = {}
    for rows in _run_all(_sql("nsrc_000006_g7_preflight.sql")):
        if rows and len(rows[0]) == 9 and rows[0][0] in ("S2", "S3"):
            states[rows[0][0]] = rows[0][-1]
    return states


def _create_source(spec: dict, url: str, *, compatible: bool = True, source_type: str = "") -> int:
    return ShrineKnowledgeSource.objects.create(
        source_type=source_type or spec["type"],
        title=spec["title"],
        url=url,
        publisher=spec["publisher"] if compatible else "別の発行者",
        bibliography=spec["bibliography"],
        verification_status="source_confirmed",
        confidence="high",
        language="ja",
    ).pk


def _base_state() -> None:
    """Disposable pre-state: Base Seed without the target row（CLEAN_CREATE 前提の再現）。"""
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    Shrine.objects.filter(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS).delete()


def _extractor():
    spec = importlib.util.spec_from_file_location(
        "nsrc_000006_g7_extract_base_subset",
        SAFETY_DIR / "nsrc_000006_g7_extract_base_subset.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _import_subset(tmp_path: Path, *args: str) -> str:
    module = _extractor()
    subset_path = tmp_path / "nsrc_000006_base_subset.json"
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


# --------------------------------------------------------------------------------------
# 1. SQL file contract
# --------------------------------------------------------------------------------------


def test_identity_block_is_identical_in_every_g7_sql_file():
    blocks = []
    for name in SQL_FILES:
        found = BLOCK_RE.findall(_sql(name))
        assert found, name
        assert len(set(found)) == 1, name
        blocks.append(found[0])
    assert len(set(blocks)) == 1


def test_frozen_pre_state_is_identical_and_equals_the_production_measurement():
    frozen = [FROZEN_RE.findall(_sql(name)) for name in GUARD_FILES]
    assert all(len(found) == 1 for found in frozen)
    assert len({found[0] for found in frozen}) == 1
    text = frozen[0][0]
    assert "    true AS frozen_values_set,\n" in text
    values = {
        name: int(value)
        for value, name in re.findall(r"^\s+(\d+)::bigint AS (\w+)", text, re.MULTILINE)
    }
    assert values == PRODUCTION_PRESTATE
    assert "NULL" not in text
    for name in GUARD_FILES:
        assert "  f.frozen_values_set\n" in _sql(name)


def test_sql_files_contain_no_connection_identifier_or_write():
    for path in sorted(SQL_DIR.glob("nsrc_000006_g7_*.sql")):
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for token in ("postgres://", "postgresql://", "password", "sslmode", "@localhost"):
            assert token not in lowered, (path.name, token)
        for statement in _statements(text):
            assert re.match(r"^(select|with)\b", statement, re.IGNORECASE), (path.name, statement)


# --------------------------------------------------------------------------------------
# 2. Source identity = importer semantics（S2 / S3 independent）
# --------------------------------------------------------------------------------------


def _sql_rows(label: str) -> dict[int, tuple]:
    sql = (
        "WITH "
        + _block()
        + f"""
SELECT n.id, n.normalized_url,
       EXISTS (SELECT 1 FROM {label}_identity i WHERE i.id = n.id),
       EXISTS (SELECT 1 FROM {label}_metadata_compatible m WHERE m.id = n.id),
       EXISTS (SELECT 1 FROM {label}_url_lookalike l WHERE l.id = n.id)
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
    urls = [*GENERAL_CORPUS]
    for label in ("s2", "s3"):
        urls += [
            *IDENTITY_VARIANTS[label],
            *NON_IDENTITY_LOOKALIKE_VARIANTS[label],
            *IMPORTER_UNPARSEABLE[label],
        ]
    created = {
        ShrineKnowledgeSource.objects.create(
            source_type="local_history", title=f"t{i}", url=u
        ).pk: u
        for i, u in enumerate(urls)
    }
    rows = _sql_rows("s2")
    for pk, url in created.items():
        assert rows[pk][0] == _python_normalized(url), url


@pytest.mark.django_db
@pytest.mark.parametrize("spec", SOURCES, ids=["S2", "S3"])
def test_identity_count_uses_importer_semantics_only(spec):
    label = spec["label"]
    other = S3 if spec is S2 else S2
    identity = {_create_source(spec, u): u for u in IDENTITY_VARIANTS[label]}
    lookalike = {_create_source(spec, u): u for u in NON_IDENTITY_LOOKALIKE_VARIANTS[label]}
    unparseable = {_create_source(spec, u): u for u in IMPORTER_UNPARSEABLE[label]}
    wrong_type = _create_source(spec, spec["url"], source_type="secondary_editorial")
    other_identity = _create_source(other, other["url"])
    rows = _sql_rows(label)

    # rows[pk] = (normalized_url, is_identity, is_metadata_compatible, is_lookalike)
    for pk, url in identity.items():
        assert normalize_source_url(url) == spec["normalized"], url
        assert rows[pk][1:] == (True, True, True), url
    for pk, url in lookalike.items():
        assert normalize_source_url(url) != spec["normalized"], url
        assert rows[pk][1] is False and rows[pk][3] is True, url
    for pk, url in unparseable.items():
        assert _python_normalized(url) is None, url
        assert rows[pk][0] is None and rows[pk][1] is False, url
    assert rows[wrong_type][1] is False and rows[wrong_type][3] is True
    assert rows[other_identity][1:] == (False, False, False)


@pytest.mark.django_db
@pytest.mark.parametrize("spec", SOURCES, ids=["S2", "S3"])
def test_metadata_compatibility_is_a_subset_of_identity(spec):
    compatible = _create_source(spec, spec["url"])
    drifted = _create_source(spec, spec["url"], compatible=False)
    rows = _sql_rows(spec["label"])
    assert rows[compatible][1:3] == (True, True)
    assert rows[drifted][1:3] == (True, False)


# --------------------------------------------------------------------------------------
# 3. Committed guards fail closed + Source-state classification
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_committed_frozen_guards_reject_non_production_local_state(tmp_path):
    _base_state()
    for name in GUARD_FILES:
        assert _committed_guard_passes(name) is False
    _import_subset(tmp_path)
    _import_knowledge()
    for name in GUARD_FILES:
        assert _committed_guard_passes(name) is False


SOURCE_STATE_CASES = {
    # case -> (s2 rows, s3 rows, expected S2 state, expected S3 state, class, s2/s3 accepted)
    "both-absent": ([], [], "ABSENT", "ABSENT", "CLEAN_CREATE", (0, 0)),
    "s2-reusable": (["compatible"], [], "REUSABLE", "ABSENT", "CLEAN_CREATE", (1, 0)),
    "s3-reusable": ([], ["compatible"], "ABSENT", "REUSABLE", "CLEAN_CREATE", (0, 1)),
    "both-reusable": (
        ["compatible"],
        ["compatible"],
        "REUSABLE",
        "REUSABLE",
        "CLEAN_CREATE",
        (1, 1),
    ),
    "s2-metadata-drift": (["drift"], [], "CONFLICT_METADATA_DRIFT", "ABSENT", "CONFLICT", None),
    "s3-metadata-drift": (
        ["compatible"],
        ["drift"],
        "REUSABLE",
        "CONFLICT_METADATA_DRIFT",
        "CONFLICT",
        None,
    ),
    "s2-identity-ambiguous": (
        ["compatible", "compatible-variant"],
        [],
        "CONFLICT_IDENTITY_AMBIGUOUS",
        "ABSENT",
        "CONFLICT",
        None,
    ),
    "s3-identity-ambiguous": (
        [],
        ["compatible", "compatible-variant"],
        "ABSENT",
        "CONFLICT_IDENTITY_AMBIGUOUS",
        "CONFLICT",
        None,
    ),
    "s2-non-identity-lookalike": (
        ["lookalike"],
        [],
        "CONFLICT_NON_IDENTITY_LOOKALIKE",
        "ABSENT",
        "CONFLICT",
        None,
    ),
    "s3-non-identity-lookalike": (
        ["compatible"],
        ["lookalike"],
        "REUSABLE",
        "CONFLICT_NON_IDENTITY_LOOKALIKE",
        "CONFLICT",
        None,
    ),
    "s2-importer-unparseable": (
        ["unparseable"],
        [],
        "CONFLICT_IMPORTER_UNPARSEABLE_URL",
        "ABSENT",
        "CONFLICT",
        None,
    ),
    "s3-importer-unparseable": (
        [],
        ["unparseable"],
        "ABSENT",
        "CONFLICT_IMPORTER_UNPARSEABLE_URL",
        "CONFLICT",
        None,
    ),
}


def _seed_source_rows(spec: dict, kinds: list[str]) -> None:
    label = spec["label"]
    for kind in kinds:
        if kind == "compatible":
            _create_source(spec, spec["url"])
        elif kind == "compatible-variant":
            _create_source(spec, IDENTITY_VARIANTS[label][1])
        elif kind == "drift":
            _create_source(spec, spec["url"], compatible=False)
        elif kind == "lookalike":
            _create_source(spec, NON_IDENTITY_LOOKALIKE_VARIANTS[label][0])
        elif kind == "unparseable":
            _create_source(spec, IMPORTER_UNPARSEABLE[label][0])


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(SOURCE_STATE_CASES))
def test_source_state_simulation(case):
    s2_rows, s3_rows, s2_state, s3_state, state_class, accepted = SOURCE_STATE_CASES[case]
    _base_state()
    _seed_source_rows(S2, s2_rows)
    _seed_source_rows(S3, s3_rows)

    assert _source_states() == {"S2": s2_state, "S3": s3_state}
    assert _state_class()[0] == state_class

    if accepted is None:
        # Unexpected Production state: no accepted count can make the pre-Base guard pass.
        for s2_accepted in (0, 1):
            for s3_accepted in (0, 1):
                frozen = _frozen_values(s2_accepted=s2_accepted, s3_accepted=s3_accepted)
                assert _guard_passes(PRE, frozen) is False
    else:
        s2_accepted, s3_accepted = accepted
        frozen = _frozen_values(s2_accepted=s2_accepted, s3_accepted=s3_accepted)
        assert _guard_passes(PRE, frozen) is True
        wrong = _frozen_values(s2_accepted=1 - s2_accepted, s3_accepted=s3_accepted)
        assert _guard_passes(PRE, wrong) is False
        wrong = _frozen_values(s2_accepted=s2_accepted, s3_accepted=1 - s3_accepted)
        assert _guard_passes(PRE, wrong) is False


# --------------------------------------------------------------------------------------
# 4. Exact identity diagnostics
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_noncanonical_address_rows_are_diagnostics_not_the_target():
    _base_state()
    for address in NON_CANONICAL_ADDRESSES:
        Shrine.objects.create(name_jp=SHRINE_NAME, kind="shrine", address=address)

    assert _state_class()[0] == "CLEAN_CREATE"
    frozen = _frozen_values(s2_accepted=0, s3_accepted=0)
    assert "2::bigint AS same_name_other_address_total" in frozen
    assert _guard_passes(PRE, frozen) is True
    rows = _run_all(_sql("nsrc_000006_g7_preflight.sql"))
    identity_row = next(r for r in rows if r and len(r[0]) == 4 and isinstance(r[0][0], int))
    assert identity_row[0] == (0, 2, 2, 0)  # target / same-name / same-name-other / same-address


@pytest.mark.django_db
def test_different_name_row_at_target_address_is_conflict():
    _base_state()
    frozen = _frozen_values(s2_accepted=0, s3_accepted=0)
    Shrine.objects.create(name_jp="赤井社", kind="shrine", address=SHRINE_ADDRESS)
    assert _state_class()[0] == "CONFLICT"
    assert _guard_passes(PRE, frozen) is False


# --------------------------------------------------------------------------------------
# 5. Target-only Base subset
# --------------------------------------------------------------------------------------


def test_extractor_emits_exactly_one_canonical_row_deterministically():
    module = _extractor()
    first = module.render(module.extract_subset())
    second = module.render(module.extract_subset())
    assert first == second
    rows = json.loads(first)
    assert rows == [module.EXPECTED_ROW]
    assert (rows[0]["latitude"], rows[0]["longitude"]) == (SHRINE_LAT, SHRINE_LNG)
    assert rows[0]["location"] == {"lat": SHRINE_LAT, "lng": SHRINE_LNG}
    assert rows[0]["goriyaku"] == ""
    assert rows[0]["kyusei"] is None
    assert rows[0]["astro_elements"] == []
    assert (
        hashlib.sha256(first.encode("utf-8")).hexdigest()
        == hashlib.sha256(second.encode("utf-8")).hexdigest()
    )


def test_extractor_fails_closed_on_missing_drifted_or_noncanonical_row(tmp_path):
    module = _extractor()
    rows = json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))

    missing = [r for r in rows if r.get("name_jp") != SHRINE_NAME]
    path = tmp_path / "missing.json"
    path.write_text(json.dumps(missing, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit, match="exactly 1"):
        module.extract_subset(path)

    drifted = copy.deepcopy(rows)
    for row in drifted:
        if row.get("name_jp") == SHRINE_NAME and row.get("address") == SHRINE_ADDRESS:
            row["latitude"] = 38.0859
    path = tmp_path / "drifted.json"
    path.write_text(json.dumps(drifted, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit, match="differs"):
        module.extract_subset(path)

    for address in NON_CANONICAL_ADDRESSES:
        other = [{**module.EXPECTED_ROW, "address": address}]
        path = tmp_path / "noncanonical.json"
        path.write_text(json.dumps(other, ensure_ascii=False), encoding="utf-8")
        with pytest.raises(SystemExit, match="exactly 1"):
            module.extract_subset(path)


def test_extractor_refuses_repository_output_path():
    module = _extractor()
    assert module.main(["x", str(REPO_ROOT / "nsrc_000006_subset.json")]) == 1
    assert not (REPO_ROOT / "nsrc_000006_subset.json").exists()


# --------------------------------------------------------------------------------------
# 6. Base + Knowledge sequential rehearsal（in-memory frozen = disposable-DB pre-state）
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("reuse", "expected_source_create"),
    [((0, 0), 2), ((1, 0), 1), ((0, 1), 1), ((1, 1), 0)],
    ids=["sources-absent", "s2-reused", "s3-reused", "both-reused"],
)
def test_base_and_knowledge_rehearsal(tmp_path, reuse, expected_source_create):
    _base_state()
    if reuse[0]:
        _create_source(S2, S2["url"])
    if reuse[1]:
        _create_source(S3, S3["url"])
    frozen = _frozen_values(s2_accepted=reuse[0], s3_accepted=reuse[1])
    pre_counts = _aggregates()
    goriyaku_before = _goriyaku_snapshot()
    assert _guard_passes(PRE, frozen) is True
    assert _guard_passes(POST_BASE, frozen) is False

    # Base subset: dry-run -> apply -> second dry-run
    _import_subset(tmp_path, "--dry-run")
    assert _aggregates() == pre_counts
    assert "created=1 updated=0 skipped=0 total_seed=1" in _import_subset(tmp_path)
    second = _import_subset(tmp_path, "--dry-run")
    assert "created=0" in second and "total_seed=1" in second
    assert _aggregates() == {**pre_counts, "shrine": pre_counts["shrine"] + 1}
    assert _goriyaku_snapshot() == goriyaku_before
    assert _guard_passes(POST_BASE, frozen) is True
    assert _guard_passes(PRE, frozen) is False
    assert _guard_passes(POST_KNOWLEDGE, frozen) is False

    # Knowledge: dry-run -> apply -> second import（idempotent）
    dry = _import_knowledge("--dry-run")
    plan = {"history_CREATE": 3}
    if expected_source_create:
        plan["source_CREATE"] = expected_source_create
    if sum(reuse):
        plan["source_REUSE_EXISTING"] = sum(reuse)
    for key, value in plan.items():
        assert f"'{key}': {value}" in dry, (key, dry)
    _import_knowledge()
    assert _aggregates() == {
        **pre_counts,
        "shrine": pre_counts["shrine"] + 1,
        "source": pre_counts["source"] + expected_source_create,
        "history": pre_counts["history"] + 3,
    }
    assert _guard_passes(POST_KNOWLEDGE, frozen) is True
    assert _guard_passes(POST_BASE, frozen) is False

    second_dry = _import_knowledge("--dry-run")
    assert "plan summary: {'source_REUSE_EXISTING': 2, 'history_SKIP_EXISTS': 3}" in second_dry
    assert "CREATE" not in second_dry
    after = _aggregates()
    _import_knowledge()
    assert _aggregates() == after
    assert _guard_passes(POST_KNOWLEDGE, frozen) is True
    assert _goriyaku_snapshot() == goriyaku_before

    shrine = _target()
    assert ShrineDeity.objects.filter(shrine=shrine).count() == 0
    relations = {
        h.title: [s.url for s in h.sources.all()]
        for h in ShrineHistory.objects.filter(shrine=shrine)
    }
    if not sum(reuse):
        assert relations == EXPECTED_RELATIONS
    assert all(h.sources.exists() for h in ShrineHistory.objects.filter(shrine=shrine))


# --------------------------------------------------------------------------------------
# 7. Negative tests（in-memory frozen; every case must fail closed）
# --------------------------------------------------------------------------------------


def _swap_shrine(name_jp: str, address: str) -> None:
    """Keep shrine_total equal while changing identity state."""
    Shrine.objects.exclude(name_jp=SHRINE_NAME).exclude(address=SHRINE_ADDRESS).order_by(
        "-id"
    ).first().delete()
    Shrine.objects.create(name_jp=name_jp, kind="shrine", address=address)


PRE_BASE_NEGATIVES = {
    "aggregate-shrine": lambda: Shrine.objects.create(
        name_jp="無関係神社", kind="shrine", address="架空県1"
    ),
    "aggregate-source": lambda: ShrineKnowledgeSource.objects.create(
        source_type="internal_research", title="x", url="https://example.invalid/x"
    ),
    "aggregate-deity": lambda: ShrineDeity.objects.create(
        shrine=Shrine.objects.exclude(name_jp=SHRINE_NAME).first(), display_name="x"
    ),
    "aggregate-history": lambda: ShrineHistory.objects.create(
        shrine=Shrine.objects.exclude(name_jp=SHRINE_NAME).first(),
        history_type="tradition",
        title="x",
        content="x",
    ),
    "aggregate-collective": lambda: ShrineDeityCollective.objects.create(
        shrine=Shrine.objects.exclude(name_jp=SHRINE_NAME).first(), source_attested_label="x"
    ),
    "target-already-exists": lambda: _swap_shrine(SHRINE_NAME, SHRINE_ADDRESS),
    "different-name-same-address": lambda: _swap_shrine("赤井社", SHRINE_ADDRESS),
    "noncanonical-address-2622": lambda: _swap_shrine(SHRINE_NAME, NON_CANONICAL_ADDRESSES[0]),
    "noncanonical-address-1164-7": lambda: _swap_shrine(SHRINE_NAME, NON_CANONICAL_ADDRESSES[1]),
    "s2-accepted-count-drift": lambda: _create_source(S2, S2["url"]),
    "s3-accepted-count-drift": lambda: _create_source(S3, S3["url"]),
    "s2-metadata-drift": lambda: _create_source(S2, S2["url"], compatible=False),
    "s3-identity-ambiguous": lambda: (
        _create_source(S3, S3["url"]),
        _create_source(S3, IDENTITY_VARIANTS["s3"][1]),
    ),
    "s2-lookalike": lambda: _create_source(S2, NON_IDENTITY_LOOKALIKE_VARIANTS["s2"][1]),
    "s3-lookalike": lambda: _create_source(S3, NON_IDENTITY_LOOKALIKE_VARIANTS["s3"][1]),
    "s3-importer-unparseable": lambda: _create_source(S3, IMPORTER_UNPARSEABLE["s3"][0]),
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(PRE_BASE_NEGATIVES))
def test_pre_base_guard_fails_closed(case):
    _base_state()
    frozen = _frozen_values(s2_accepted=0, s3_accepted=0)
    assert _guard_passes(PRE, frozen) is True
    PRE_BASE_NEGATIVES[case]()
    assert _guard_passes(PRE, frozen) is False


POST_BASE_NEGATIVES = {
    "extra-unrelated-shrine": lambda s: Shrine.objects.create(
        name_jp="無関係神社", kind="shrine", address="架空県2"
    ),
    "coordinate-drift": lambda s: Shrine.objects.filter(pk=s.pk).update(latitude=38.0859),
    "goriyaku-text": lambda s: Shrine.objects.filter(pk=s.pk).update(goriyaku="縁結び"),
    "goriyaku-tag": lambda s: s.goriyaku_tags.add(GoriyakuTag.objects.create(name="G7タグ6")),
    "knowledge-too-early": lambda s: ShrineHistory.objects.create(
        shrine=s, history_type="tradition", title="x", content="x"
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(POST_BASE_NEGATIVES))
def test_post_base_guard_fails_closed(tmp_path, case):
    _base_state()
    frozen = _frozen_values(s2_accepted=0, s3_accepted=0)
    _import_subset(tmp_path)
    assert _guard_passes(POST_BASE, frozen) is True
    POST_BASE_NEGATIVES[case](_target())
    assert _guard_passes(POST_BASE, frozen) is False


def _history(shrine: Shrine, title: str) -> ShrineHistory:
    return ShrineHistory.objects.get(shrine=shrine, title=title)


def _source(spec: dict) -> ShrineKnowledgeSource:
    return ShrineKnowledgeSource.objects.get(url=spec["url"])


POST_KNOWLEDGE_NEGATIVES = {
    "extra-deity": lambda s: ShrineDeity.objects.create(shrine=s, display_name="素盞嗚尊"),
    "extra-relation-h1-s3": lambda s: _history(s, H1_TITLE).sources.add(_source(S3)),
    "extra-relation-h3-s2": lambda s: _history(s, H3_TITLE).sources.add(_source(S2)),
    "swapped-h1-to-s3": lambda s: _history(s, H1_TITLE).sources.set([_source(S3)]),
    "swapped-h2-to-s3": lambda s: _history(s, H2_TITLE).sources.set([_source(S3)]),
    "swapped-h3-to-s2": lambda s: _history(s, H3_TITLE).sources.set([_source(S2)]),
    "source-less-history": lambda s: _history(s, H2_TITLE).sources.clear(),
    "goriyaku-text": lambda s: Shrine.objects.filter(pk=s.pk).update(goriyaku="縁結び"),
    "goriyaku-tag": lambda s: s.goriyaku_tags.add(GoriyakuTag.objects.create(name="G7タグ6k")),
    "coordinate-drift": lambda s: Shrine.objects.filter(pk=s.pk).update(longitude=138.4183),
    "extra-unrelated-shrine": lambda s: Shrine.objects.create(
        name_jp="無関係神社", kind="shrine", address="架空県3"
    ),
    "source-fact": lambda s: ShrineSourceFact.objects.create(
        shrine=s,
        stable_key="g7-nsrc-000006-extra",
        source_attested_wording="x",
        evidence_characterization="official_prayer_supported",
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(POST_KNOWLEDGE_NEGATIVES))
def test_post_knowledge_verification_fails_closed(tmp_path, case):
    _base_state()
    frozen = _frozen_values(s2_accepted=0, s3_accepted=0)
    _import_subset(tmp_path)
    _import_knowledge()
    assert _guard_passes(POST_KNOWLEDGE, frozen) is True
    POST_KNOWLEDGE_NEGATIVES[case](_target())
    assert _guard_passes(POST_KNOWLEDGE, frozen) is False


# --------------------------------------------------------------------------------------
# 8. Runtime QA rehearsal（READ ONLY transaction）
# --------------------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_runtime_qa_rehearsal_passes_read_only(tmp_path, capsys):
    _base_state()
    for address in NON_CANONICAL_ADDRESSES:
        Shrine.objects.create(name_jp=SHRINE_NAME, kind="shrine", address=address)
    _import_subset(tmp_path)
    _import_knowledge()

    spec = importlib.util.spec_from_file_location(
        "nsrc_000006_g7_runtime_qa", SAFETY_DIR / "nsrc_000006_g7_runtime_qa.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    before = _aggregates()
    capsys.readouterr()
    module.main()
    out = capsys.readouterr().out
    assert _aggregates() == before
    for line in (
        "EXACT_TARGET=PASS",
        "DETAIL_RUNTIME=PASS",
        "SHARED_RECOMMENDATION_ELIGIBILITY=PASS",
        "CONCIERGE_CANDIDATE_PATH=PASS",
        "RECOMMENDATION_REASON=PASS",
        "COMPASS_DISTANCE=PASS",
        "COMPASS_DIRECTION=PASS",
        "AGGREGATES_UNCHANGED=PASS",
        "G7_PRODUCTION_RUNTIME_QA=PASS",
        "TRANSACTION_MODE=READ_ONLY",
    ):
        assert line in out, line

# --------------------------------------------------------------------------------------
# 9. Committed frozen guards（Production measurement）on a simulated exact Production pre-state
# --------------------------------------------------------------------------------------

FILLER_SHRINE = "G7filler赤井神社"


def _filler_shrine() -> Shrine:
    return Shrine.objects.get_or_create(
        name_jp=FILLER_SHRINE, address="架空県架空市0-0", defaults={"kind": "shrine"}
    )[0]


def _simulate_production_prestate() -> None:
    """Disposable DB の aggregate を Production 実測値と完全一致させる（frozen 値は変えない）。"""
    _base_state()
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
        count = PRODUCTION_PRESTATE[key] - model.objects.count()
        assert count >= 0, (key, model.objects.count(), PRODUCTION_PRESTATE[key])
        return range(count)

    ShrineKnowledgeSource.objects.bulk_create(
        ShrineKnowledgeSource(
            source_type="internal_research",
            title=f"filler source {i}",
            url=f"https://example.invalid/g7-nsrc-000006-filler/{i}",
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
            stable_key=f"g7-nsrc-000006-filler-source-fact-{i}",
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
    assert _state_class()[0] == "CLEAN_CREATE"
    assert _source_states() == {"S2": "ABSENT", "S3": "ABSENT"}


def _swap_filler_source(spec: dict, url: str, *, compatible: bool = True) -> None:
    """Keep source_total equal to the frozen value while changing S2 / S3 state."""
    filler = (
        ShrineKnowledgeSource.objects.filter(
            url__startswith="https://example.invalid/g7-nsrc-000006-filler/"
        )
        .order_by("id")
        .first()
    )
    assert filler is not None
    filler.delete()
    _create_source(spec, url, compatible=compatible)


def _swap_filler_shrine(name_jp: str, address: str) -> None:
    """Keep shrine_total equal to the frozen value while changing identity state."""
    removable = (
        Shrine.objects.exclude(name_jp__in=(SHRINE_NAME, FILLER_SHRINE))
        .exclude(address=SHRINE_ADDRESS)
        .order_by("-id")
        .first()
    )
    assert removable is not None
    removable.delete()
    Shrine.objects.create(name_jp=name_jp, kind="shrine", address=address)


@pytest.mark.django_db
def test_committed_pre_base_guard_passes_on_the_exact_production_prestate():
    _simulate_production_prestate()
    assert _committed_guard_passes(PRE) is True
    assert _committed_guard_passes(POST_BASE) is False
    assert _committed_guard_passes(POST_KNOWLEDGE) is False


COMMITTED_PRESTATE_DRIFT = {
    "shrine+1": lambda: Shrine.objects.create(
        name_jp="無関係神社", kind="shrine", address="架空県drift1"
    ),
    "source+1": lambda: ShrineKnowledgeSource.objects.create(
        source_type="internal_research", title="x", url="https://example.invalid/g7-extra"
    ),
    "source-1": lambda: ShrineKnowledgeSource.objects.order_by("id").first().delete(),
    "deity+1": lambda: ShrineDeity.objects.create(shrine=_filler_shrine(), display_name="extra"),
    "history+1": lambda: ShrineHistory.objects.create(
        shrine=_filler_shrine(), history_type="tradition", title="extra", content="x"
    ),
    "source-fact+1": lambda: ShrineSourceFact.objects.create(
        shrine=_filler_shrine(),
        stable_key="g7-nsrc-000006-extra",
        source_attested_wording="x",
        evidence_characterization="official_prayer_supported",
    ),
    "collective+1": lambda: ShrineDeityCollective.objects.create(
        shrine=_filler_shrine(), source_attested_label="extra"
    ),
    "target-exists": lambda: _swap_filler_shrine(SHRINE_NAME, SHRINE_ADDRESS),
    "same-address-other-name": lambda: _swap_filler_shrine("赤井社", SHRINE_ADDRESS),
    "same-name-other-address": lambda: _swap_filler_shrine(
        SHRINE_NAME, NON_CANONICAL_ADDRESSES[0]
    ),
    "s2-accepted-drift": lambda: _swap_filler_source(S2, S2["url"]),
    "s3-accepted-drift": lambda: _swap_filler_source(S3, S3["url"]),
    "s2-metadata-drift": lambda: _swap_filler_source(S2, S2["url"], compatible=False),
    "s3-metadata-drift": lambda: _swap_filler_source(S3, S3["url"], compatible=False),
    "s2-non-identity-lookalike": lambda: _swap_filler_source(
        S2, NON_IDENTITY_LOOKALIKE_VARIANTS["s2"][0]
    ),
    "s3-non-identity-lookalike": lambda: _swap_filler_source(
        S3, NON_IDENTITY_LOOKALIKE_VARIANTS["s3"][0]
    ),
    "s2-importer-unparseable": lambda: _swap_filler_source(
        S2, IMPORTER_UNPARSEABLE["s2"][0]
    ),
}


@pytest.mark.django_db
@pytest.mark.parametrize("drift", sorted(COMMITTED_PRESTATE_DRIFT))
def test_committed_pre_base_guard_fails_on_any_drift(drift):
    _simulate_production_prestate()
    assert _committed_guard_passes(PRE) is True
    COMMITTED_PRESTATE_DRIFT[drift]()
    assert _committed_guard_passes(PRE) is False


@pytest.mark.django_db
def test_committed_sequential_rehearsal(tmp_path):
    _simulate_production_prestate()
    goriyaku_before = _goriyaku_snapshot()
    assert _committed_guard_passes(PRE) is True

    _import_subset(tmp_path, "--dry-run")
    assert _aggregates() == PRODUCTION_AGGREGATES
    assert "created=1 updated=0 skipped=0 total_seed=1" in _import_subset(tmp_path)
    second = _import_subset(tmp_path, "--dry-run")
    assert "created=0" in second and "total_seed=1" in second
    assert _aggregates() == EXPECTED_POST_BASE
    assert _committed_guard_passes(POST_BASE) is True
    assert _committed_guard_passes(PRE) is False
    assert _committed_guard_passes(POST_KNOWLEDGE) is False

    dry = _import_knowledge("--dry-run")
    assert "plan summary: {'source_CREATE': 2, 'history_CREATE': 3}" in dry
    _import_knowledge()
    assert _aggregates() == EXPECTED_POST_KNOWLEDGE
    assert _committed_guard_passes(POST_KNOWLEDGE) is True
    assert _committed_guard_passes(POST_BASE) is False

    second_dry = _import_knowledge("--dry-run")
    assert "plan summary: {'source_REUSE_EXISTING': 2, 'history_SKIP_EXISTS': 3}" in second_dry
    assert "CREATE" not in second_dry
    _import_knowledge()
    assert _aggregates() == EXPECTED_POST_KNOWLEDGE
    assert _committed_guard_passes(POST_KNOWLEDGE) is True
    assert _goriyaku_snapshot() == goriyaku_before

    relations = {
        h.title: [s.url for s in h.sources.all()]
        for h in ShrineHistory.objects.filter(shrine=_target())
    }
    assert relations == EXPECTED_RELATIONS


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(POST_KNOWLEDGE_NEGATIVES))
def test_committed_post_knowledge_verification_fails_closed(tmp_path, case):
    _simulate_production_prestate()
    _import_subset(tmp_path)
    _import_knowledge()
    assert _committed_guard_passes(POST_KNOWLEDGE) is True
    POST_KNOWLEDGE_NEGATIVES[case](_target())
    assert _committed_guard_passes(POST_KNOWLEDGE) is False

