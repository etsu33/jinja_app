"""nsrc-000007 赤城社 G7 Production Import preflight regression（disposable test DB only）。

scripts/migration_safety/sql/nsrc_000007_g7_*.sql は同一の `nsrc_000007_source_identity`
block を持ち、S2 / S3 を独立した importer semantic identity（source_type +
knowledge_seed.normalize_source_url()）として数える。近似一致は使わない。

guard（pre-Base / post-Base / post-Knowledge）の FROZEN_PRE_STATE は Production 実測前のため
UNSET（NULL / frozen_values_set=false）であり、常に fail closed する。rehearsal では
test 内メモリ上だけで frozen block を disposable DB の実測値へ置き換えて guard の意味を検証する。
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
    ShrineGoriyakuAssignment,
    ShrineHistory,
    ShrineKnowledgeSource,
)
from temples.services.knowledge_seed import normalize_source_url

REPO_ROOT = Path(__file__).resolve().parents[3]
SAFETY_DIR = REPO_ROOT / "scripts" / "migration_safety"
SQL_DIR = SAFETY_DIR / "sql"
DATA_DIR = REPO_ROOT / "backend" / "temples" / "data"
BASE_SEED_PATH = DATA_DIR / "shrines_seed_clean.json"
KNOWLEDGE_SEED_PATH = DATA_DIR / "knowledge_seeds" / "nsrc_000007_seed.json"

SQL_FILES = (
    "nsrc_000007_g7_preflight.sql",
    "nsrc_000007_g7_pre_base_guard.sql",
    "nsrc_000007_g7_post_base_guard.sql",
    "nsrc_000007_g7_post_knowledge_verification.sql",
)
GUARD_FILES = SQL_FILES[1:]
BLOCK_RE = re.compile(
    r"-- BEGIN nsrc_000007_source_identity\n(.*?)-- END nsrc_000007_source_identity\n",
    re.DOTALL,
)
FROZEN_RE = re.compile(
    r"-- BEGIN nsrc_000007_frozen_pre_state\n(.*?)-- END nsrc_000007_frozen_pre_state\n",
    re.DOTALL,
)

SHRINE_NAME = "赤城社"
SHRINE_ADDRESS = "新潟県十日町市四日町2534番地"
OTHER_AKAGI_ADDRESSES = (
    "新潟県十日町市上組2059番地子",
    "新潟県十日町市伊達乙48番地",
    "新潟県南魚沼市芹田79番地",
)

S2 = {
    "label": "s2",
    "type": "government",
    "url": "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf",
    "normalized": "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf",
    "publisher": "十日町市",
    "bibliography": "中魚沼郡誌上 p.398",
    "title": "歴史文化基本構想 資料集",
}
S3 = {
    "label": "s3",
    "type": "museum_or_archive",
    "url": "https://www.tokamachi-museum.jp/archives/bunka023/",
    "normalized": "https://www.tokamachi-museum.jp/archives/bunka023",
    "publisher": "十日町市博物館",
    "bibliography": "",
    "title": "越後縮幡",
}
SOURCES = (S2, S3)

# importer と同じ semantic identity になる表記揺れ
IDENTITY_VARIANTS = {
    "s2": (
        S2["url"],
        "HTTPS://WWW.CITY.TOKAMACHI.LG.JP/material/files/group/31/rekibun_shiryou.pdf",
        "https://www.city.tokamachi.lg.jp:443/material/files/group/31/rekibun_shiryou.pdf",
        "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf/",
        "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf#page=3",
        "  https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf  ",
        "https://u:p@www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf",
    ),
    "s3": (
        S3["url"],
        "https://www.tokamachi-museum.jp/archives/bunka023",
        "HTTPS://WWW.TOKAMACHI-MUSEUM.JP/archives/bunka023/",
        "https://www.tokamachi-museum.jp:443/archives/bunka023/",
        "https://www.tokamachi-museum.jp/archives/bunka023///",
        "https://www.tokamachi-museum.jp/archives/bunka023/#top",
        "　https://www.tokamachi-museum.jp/archives/bunka023/　",
    ),
}
# importer の identity ではないが、lookalike 診断には必ず拾われる表記（再利用不可）
NON_IDENTITY_LOOKALIKE_VARIANTS = {
    "s2": (
        "http://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf",
        "https://city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf",
        "https://www.city.tokamachi.lg.jp/material/files/group/32/rekibun_shiryou.pdf",
        "https://www.city.tokamachi.lg.jp/material/files/group/31/Rekibun_Shiryou.pdf",
        "https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf?v=2",
        "https://www.city.tokamachi.lg.jp:8443/material/files/group/31/rekibun_shiryou.pdf",
    ),
    "s3": (
        "http://www.tokamachi-museum.jp/archives/bunka023/",
        "https://tokamachi-museum.jp/archives/bunka023/",
        "https://www.tokamachi-museum.jp/Archives/bunka023/",
        "https://www.tokamachi-museum.jp/archives/bunka023/?lang=ja",
        "https://www.tokamachi-museum.jp/archives/bunka0234/",
        "www.tokamachi-museum.jp/archives/bunka023/",
    ),
}
# importer が ValueError で停止する URL（SQL は NULL = identity にならない）
IMPORTER_UNPARSEABLE = {
    "s2": ("https://www.city.tokamachi.lg.jp:abc/material/files/group/31/rekibun_shiryou.pdf",),
    "s3": ("https://www.tokamachi-museum.jp:99999/archives/bunka023/",),
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
    found = BLOCK_RE.findall(_sql(SQL_FILES[0]))
    return found[0]


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


def _frozen_values(*, s2_accepted: int, s3_accepted: int) -> str:
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


def _guard_passes(name: str, frozen: str) -> bool:
    try:
        with transaction.atomic():
            rows = _run_all(_with_frozen(name, frozen))
    except DataError:  # division_by_zero = guard FAIL
        return False
    assert rows[-1] == [(1,)]
    return True


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


def _state_class() -> tuple:
    return _run_all(_sql("nsrc_000007_g7_preflight.sql"))[-1][0]


def _source_states() -> dict[str, str]:
    results = _run_all(_sql("nsrc_000007_g7_preflight.sql"))
    states = {}
    for rows in results:
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
        "nsrc_000007_g7_extract_base_subset",
        SAFETY_DIR / "nsrc_000007_g7_extract_base_subset.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _import_subset(tmp_path: Path, *args: str) -> str:
    module = _extractor()
    subset_path = tmp_path / "nsrc_000007_base_subset.json"
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


def test_frozen_pre_state_is_identical_unset_and_fail_closed_in_every_guard():
    frozen = [FROZEN_RE.findall(_sql(name)) for name in GUARD_FILES]
    assert all(len(found) == 1 for found in frozen)
    assert len({found[0] for found in frozen}) == 1
    text = frozen[0][0]
    assert "false AS frozen_values_set" in text
    # no Production value is frozen yet: every numeric value is NULL
    assert re.findall(r"^\s+(\S+)::bigint AS", text, re.MULTILINE) == ["NULL"] * 9
    for name in GUARD_FILES:
        assert "  f.frozen_values_set\n" in _sql(name)


def test_sql_files_contain_no_connection_identifier_or_write():
    for path in sorted(SQL_DIR.glob("nsrc_000007_g7_*.sql")):
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
            source_type="government", title=f"t{i}", url=url
        ).pk: url
        for i, url in enumerate(urls)
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
    # 同じ URL でも source_type が違えば identity ではない（lookalike としてだけ拾う）
    assert rows[wrong_type][1] is False and rows[wrong_type][3] is True
    # S2 と S3 は互いの identity / lookalike にならない
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
# 3. Preflight state class + negative Source-state simulations（guard FAIL -> STOP）
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_unset_guards_always_fail_closed():
    _base_state()
    for name in GUARD_FILES:
        with pytest.raises(DataError, match="division by zero"):
            with transaction.atomic():
                _run_all(_sql(name))


SOURCE_STATE_CASES = {
    # case -> (s2 rows, s3 rows, expected S2 state, expected S3 state, class, s2/s3 accepted)
    "both-absent": ([], [], "ABSENT", "ABSENT", "CLEAN_CREATE", (0, 0)),
    "s2-reusable": ([("compatible",)], [], "REUSABLE", "ABSENT", "CLEAN_CREATE", (1, 0)),
    "s3-reusable": ([], [("compatible",)], "ABSENT", "REUSABLE", "CLEAN_CREATE", (0, 1)),
    "both-reusable": (
        [("compatible",)],
        [("compatible",)],
        "REUSABLE",
        "REUSABLE",
        "CLEAN_CREATE",
        (1, 1),
    ),
    "s2-metadata-drift": (
        [("drift",)],
        [],
        "CONFLICT_METADATA_DRIFT",
        "ABSENT",
        "CONFLICT",
        None,
    ),
    "s3-metadata-drift": (
        [("compatible",)],
        [("drift",)],
        "REUSABLE",
        "CONFLICT_METADATA_DRIFT",
        "CONFLICT",
        None,
    ),
    "s2-identity-ambiguous": (
        [("compatible",), ("compatible-variant",)],
        [],
        "CONFLICT_IDENTITY_AMBIGUOUS",
        "ABSENT",
        "CONFLICT",
        None,
    ),
    "s3-identity-ambiguous": (
        [],
        [("compatible",), ("compatible-variant",)],
        "ABSENT",
        "CONFLICT_IDENTITY_AMBIGUOUS",
        "CONFLICT",
        None,
    ),
    "s2-non-identity-lookalike": (
        [("lookalike",)],
        [],
        "CONFLICT_NON_IDENTITY_LOOKALIKE",
        "ABSENT",
        "CONFLICT",
        None,
    ),
    "s3-non-identity-lookalike": (
        [("compatible",)],
        [("lookalike",)],
        "REUSABLE",
        "CONFLICT_NON_IDENTITY_LOOKALIKE",
        "CONFLICT",
        None,
    ),
    "s2-importer-unparseable": (
        [("unparseable",)],
        [],
        "CONFLICT_IMPORTER_UNPARSEABLE_URL",
        "ABSENT",
        "CONFLICT",
        None,
    ),
    "s3-importer-unparseable": (
        [],
        [("unparseable",)],
        "ABSENT",
        "CONFLICT_IMPORTER_UNPARSEABLE_URL",
        "CONFLICT",
        None,
    ),
}


def _seed_source_rows(spec: dict, kinds: list[tuple]) -> None:
    label = spec["label"]
    for (kind,) in kinds:
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
                assert _guard_passes("nsrc_000007_g7_pre_base_guard.sql", frozen) is False
    else:
        s2_accepted, s3_accepted = accepted
        frozen = _frozen_values(s2_accepted=s2_accepted, s3_accepted=s3_accepted)
        assert _guard_passes("nsrc_000007_g7_pre_base_guard.sql", frozen) is True
        # a wrong frozen accepted count must fail
        wrong = _frozen_values(s2_accepted=1 - s2_accepted, s3_accepted=s3_accepted)
        assert _guard_passes("nsrc_000007_g7_pre_base_guard.sql", wrong) is False


@pytest.mark.django_db
def test_pre_base_guard_fails_on_aggregate_or_target_drift():
    _base_state()
    frozen = _frozen_values(s2_accepted=0, s3_accepted=0)
    assert _guard_passes("nsrc_000007_g7_pre_base_guard.sql", frozen) is True

    Shrine.objects.create(name_jp="無関係神社", kind="shrine", address="架空県架空市1-1")
    assert _guard_passes("nsrc_000007_g7_pre_base_guard.sql", frozen) is False


@pytest.mark.django_db
def test_same_name_other_address_rows_are_diagnostics_not_the_target():
    _base_state()
    for address in OTHER_AKAGI_ADDRESSES:
        Shrine.objects.create(name_jp=SHRINE_NAME, kind="shrine", address=address)

    state_class = _state_class()[0]
    assert state_class == "CLEAN_CREATE"
    frozen = _frozen_values(s2_accepted=0, s3_accepted=0)
    assert "3::bigint AS same_name_other_address_total" in frozen
    assert _guard_passes("nsrc_000007_g7_pre_base_guard.sql", frozen) is True

    # a same-address collision is a CONFLICT, whatever the name
    Shrine.objects.create(name_jp="赤城神社", kind="shrine", address=SHRINE_ADDRESS)
    assert _state_class()[0] == "CONFLICT"
    assert _guard_passes("nsrc_000007_g7_pre_base_guard.sql", frozen) is False


# --------------------------------------------------------------------------------------
# 4. Target-only Base subset
# --------------------------------------------------------------------------------------


def test_extractor_emits_exactly_one_canonical_row_deterministically():
    module = _extractor()
    first = module.render(module.extract_subset())
    second = module.render(module.extract_subset())
    assert first == second
    rows = json.loads(first)
    assert rows == [module.EXPECTED_ROW]
    assert (rows[0]["latitude"], rows[0]["longitude"]) == (37.14755658, 138.76887612)
    assert rows[0]["goriyaku"] == ""
    assert (
        hashlib.sha256(first.encode("utf-8")).hexdigest()
        == hashlib.sha256(second.encode("utf-8")).hexdigest()
    )


def test_extractor_fails_closed_on_missing_or_drifted_row(tmp_path):
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
            row["latitude"] = 37.147573
    path = tmp_path / "drifted.json"
    path.write_text(json.dumps(drifted, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit, match="differs"):
        module.extract_subset(path)

    # a different-address 赤城社 alone is never extracted
    other = [{**module.EXPECTED_ROW, "address": OTHER_AKAGI_ADDRESSES[0]}]
    path = tmp_path / "other.json"
    path.write_text(json.dumps(other, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit, match="exactly 1"):
        module.extract_subset(path)


def test_extractor_refuses_repository_output_path():
    module = _extractor()
    assert module.main(["x", str(REPO_ROOT / "nsrc_000007_subset.json")]) == 1
    assert not (REPO_ROOT / "nsrc_000007_subset.json").exists()


# --------------------------------------------------------------------------------------
# 5. Base + Knowledge rehearsal with post guards
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("reuse", "expected_source_create"),
    [((0, 0), 2), ((1, 0), 1), ((1, 1), 0)],
    ids=["sources-absent", "s2-reused", "both-reused"],
)
def test_base_and_knowledge_rehearsal(tmp_path, reuse, expected_source_create):
    _base_state()
    if reuse[0]:
        _create_source(S2, S2["url"])
    if reuse[1]:
        _create_source(S3, S3["url"])
    frozen = _frozen_values(s2_accepted=reuse[0], s3_accepted=reuse[1])
    goriyaku_before = _goriyaku_snapshot()
    assert _guard_passes("nsrc_000007_g7_pre_base_guard.sql", frozen) is True
    assert _guard_passes("nsrc_000007_g7_post_base_guard.sql", frozen) is False

    # Base subset: dry-run -> apply -> second dry-run
    before = _aggregates()
    _import_subset(tmp_path, "--dry-run")
    assert _aggregates() == before
    applied = _import_subset(tmp_path)
    assert "created=1 updated=0 skipped=0 total_seed=1" in applied
    second = _import_subset(tmp_path, "--dry-run")
    assert "created=0" in second and "total_seed=1" in second
    assert _goriyaku_snapshot() == goriyaku_before
    assert _guard_passes("nsrc_000007_g7_post_base_guard.sql", frozen) is True
    assert _guard_passes("nsrc_000007_g7_pre_base_guard.sql", frozen) is False
    assert _guard_passes("nsrc_000007_g7_post_knowledge_verification.sql", frozen) is False

    # Knowledge: dry-run -> apply -> second dry-run
    reuse_count = sum(reuse)
    dry = _import_knowledge("--dry-run")
    plan = {"history_CREATE": 2}
    if expected_source_create:
        plan["source_CREATE"] = expected_source_create
    if reuse_count:
        plan["source_REUSE_EXISTING"] = reuse_count
    for key, value in plan.items():
        assert f"'{key}': {value}" in dry, (key, dry)
    _import_knowledge()
    second_dry = _import_knowledge("--dry-run")
    assert "plan summary: {'source_REUSE_EXISTING': 2, 'history_SKIP_EXISTS': 2}" in second_dry
    assert "CREATE" not in second_dry

    assert _guard_passes("nsrc_000007_g7_post_knowledge_verification.sql", frozen) is True
    assert _goriyaku_snapshot() == goriyaku_before
    shrine = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    assert ShrineDeity.objects.filter(shrine=shrine).count() == 0
    assert ShrineHistory.objects.filter(shrine=shrine).count() == 2


@pytest.mark.django_db
def test_post_knowledge_verification_fails_on_wrong_relation(tmp_path):
    _base_state()
    frozen = _frozen_values(s2_accepted=0, s3_accepted=0)
    _import_subset(tmp_path)
    _import_knowledge()
    assert _guard_passes("nsrc_000007_g7_post_knowledge_verification.sql", frozen) is True

    shrine = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    h1 = ShrineHistory.objects.get(shrine=shrine, title="安政7年正月の再建")
    s3 = ShrineKnowledgeSource.objects.get(url=S3["url"])
    h1.sources.add(s3)  # H1 -> S2 + S3 is not "S2 exactly"
    assert _guard_passes("nsrc_000007_g7_post_knowledge_verification.sql", frozen) is False
    h1.sources.remove(s3)
    assert _guard_passes("nsrc_000007_g7_post_knowledge_verification.sql", frozen) is True

    ShrineDeity.objects.create(shrine=shrine, display_name="土田岐入彦命")
    assert _guard_passes("nsrc_000007_g7_post_knowledge_verification.sql", frozen) is False


# --------------------------------------------------------------------------------------
# 6. Runtime QA rehearsal（READ ONLY transaction）
# --------------------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_runtime_qa_rehearsal_passes_read_only(tmp_path, capsys):
    _base_state()
    _import_subset(tmp_path)
    _import_knowledge()

    spec = importlib.util.spec_from_file_location(
        "nsrc_000007_g7_runtime_qa", SAFETY_DIR / "nsrc_000007_g7_runtime_qa.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    before = _aggregates()
    capsys.readouterr()
    module.main()
    out = capsys.readouterr().out
    assert _aggregates() == before
    for line in (
        "DETAIL_RUNTIME=PASS",
        "CONCIERGE_CANDIDATE_PATH=PASS",
        "RECOMMENDATION_REASON=PASS",
        "COMPASS_DISTANCE=PASS",
        "COMPASS_DIRECTION=PASS",
        "G7_PRODUCTION_RUNTIME_QA=PASS",
        "TRANSACTION_MODE=READ_ONLY",
    ):
        assert line in out, line
