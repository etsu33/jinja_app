"""NIIGATA-001-H003 C6 target-only Production import artifact regression（disposable test DB only）。

- scripts/migration_safety/niigata_h003_c6_extract_base_subset.py は Base Seed から exact
  (name_jp, address) の4行だけを candidate 順に抽出する。nsrc-000014 は含めない。
- niigata_h003_c6_pre_base_guard.sql / niigata_h003_c6_post_base_verification.sql の frozen block は
  Mother Ship が Production で read-only 実行した niigata_h003_c6_catalog_preflight.sql の実測値
  （PRODUCTION_PRESTATE, CLEAN_CREATE）で固定済み。
- committed guard は変更せずに、aggregate を PRODUCTION_PRESTATE と完全一致させた disposable DB の
  simulated pre-state に対して実行する。

Production には接続しない。Production write は行わない。
"""

from __future__ import annotations

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
    HistoryThemeAssignment,
    Shrine,
    ShrineCanonicalAnchor,
    ShrineDeity,
    ShrineDeityCollective,
    ShrineFactSourceCitation,
    ShrineGoriyakuAssignment,
    ShrineHistory,
    ShrineKnowledgeSource,
    ShrineSourceFact,
)
from temples.tests.support.recommendation_eligibility import attach_usable_history_fact

REPO_ROOT = Path(__file__).resolve().parents[3]
SAFETY_DIR = REPO_ROOT / "scripts" / "migration_safety"
SQL_DIR = SAFETY_DIR / "sql"
BASE_SEED_PATH = REPO_ROOT / "backend" / "temples" / "data" / "shrines_seed_clean.json"
PREFLIGHT = "niigata_h003_c6_catalog_preflight.sql"
PRE_GUARD = "niigata_h003_c6_pre_base_guard.sql"
POST_VERIFY = "niigata_h003_c6_post_base_verification.sql"
GUARD_FILES = (PRE_GUARD, POST_VERIFY)

TARGET_BLOCK_RE = re.compile(
    r"-- BEGIN niigata_h003_c6_target_state\n.*?-- END niigata_h003_c6_target_state\n", re.DOTALL
)
FROZEN_BLOCK_RE = re.compile(
    r"-- BEGIN niigata_h003_c6_frozen_pre_state\n.*?-- END niigata_h003_c6_frozen_pre_state\n",
    re.DOTALL,
)

# Mother Ship read-only Production measurement（niigata_h003_c6_catalog_preflight.sql, PR #3254 後）
PRODUCTION_PRESTATE = {
    "shrine_total": 125,
    "source_total": 145,
    "deity_total": 295,
    "history_total": 236,
    "source_fact_total": 34,
    "collective_total": 6,
    "citation_total": 2,
    "shrine_nonempty_goriyaku_total": 116,
    "goriyaku_tag_master_total": 39,
    "goriyaku_tag_link_total": 366,
    "goriyaku_assignment_total": 0,
    "history_theme_assignment_total": 0,
    "canonical_anchor_total": 0,
}
EXPECTED_SHRINE_DELTA = 4

SHRINE_NAME = "赤城神社"
TARGET_IDS = ("nsrc-000011", "nsrc-000012", "nsrc-000013", "nsrc-000015")
TARGETS = {
    "nsrc-000011": ("新潟県新潟市江南区二本木1丁目7番16号", 37.841794, 139.118507),
    "nsrc-000012": ("新潟県長岡市四郎丸2丁目5番33号", 37.440743, 138.855238),
    "nsrc-000013": ("新潟県長岡市山屋314番地", 37.496407, 139.008620),
    "nsrc-000015": ("新潟県魚沼市湯之谷芋川311番地", 37.214543, 139.036468),
}
HOLD_ID = "nsrc-000014"
HOLD_ADDRESS = "新潟県五泉市上杉川1310番地2"
MUTATED = "nsrc-000013"


# --------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------


def _extractor():
    spec = importlib.util.spec_from_file_location(
        "niigata_h003_c6_extract_base_subset",
        SAFETY_DIR / "niigata_h003_c6_extract_base_subset.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _guard_module():
    spec = importlib.util.spec_from_file_location(
        "_niigata_h003_c6_migration_safety_guard", SAFETY_DIR / "guard.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seed_rows() -> list[dict]:
    return json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))


def _sql(name: str) -> str:
    return (SQL_DIR / name).read_text(encoding="utf-8")


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


def _committed_guard_passes(name: str) -> bool:
    """Run the committed guard file unchanged（frozen = Production measurement）."""
    try:
        with transaction.atomic():
            rows = _run_all(_sql(name))
    except DataError:  # division_by_zero = guard FAIL
        return False
    assert rows[-1] == [(1,)]
    return True


def _aggregates() -> dict[str, int]:
    return {
        "shrine_total": Shrine.objects.count(),
        "source_total": ShrineKnowledgeSource.objects.count(),
        "deity_total": ShrineDeity.objects.count(),
        "history_total": ShrineHistory.objects.count(),
        "source_fact_total": ShrineSourceFact.objects.count(),
        "collective_total": ShrineDeityCollective.objects.count(),
        "citation_total": ShrineFactSourceCitation.objects.count(),
        "shrine_nonempty_goriyaku_total": Shrine.objects.exclude(goriyaku__isnull=True)
        .exclude(goriyaku="")
        .count(),
        "goriyaku_tag_master_total": GoriyakuTag.objects.count(),
        "goriyaku_tag_link_total": Shrine.goriyaku_tags.through.objects.count(),
        "goriyaku_assignment_total": ShrineGoriyakuAssignment.objects.count(),
        "history_theme_assignment_total": HistoryThemeAssignment.objects.count(),
        "canonical_anchor_total": ShrineCanonicalAnchor.objects.count(),
    }


def _import(source: Path, *extra: str) -> str:
    out = io.StringIO()
    call_command(
        "import_shrines_seed",
        "--source",
        str(source),
        "--skip-goriyaku-tags",
        *extra,
        stdout=out,
        stderr=io.StringIO(),
    )
    return out.getvalue()


def _target(candidate_id: str) -> Shrine:
    return Shrine.objects.get(name_jp=SHRINE_NAME, address=TARGETS[candidate_id][0])


def _filler_holder() -> Shrine:
    """Filler Knowledge は既存の非 target Shrine に付ける（Shrine 数を増やさない）。"""
    return Shrine.objects.exclude(name_jp=SHRINE_NAME).order_by("id").first()


def _simulate_production_prestate() -> None:
    """Disposable DB の aggregate を Production 実測値と完全一致させる（frozen 値は変えない）。

    Base Seed（129行）から4 target を除き、test DB に migration 由来の余剰行があれば非 target 行を
    削って Shrine = 125 に合わせる。Knowledge 系は target と無関係な filler 行で実測値まで埋める。
    """
    _import(BASE_SEED_PATH)
    for candidate_id in TARGET_IDS:
        _target(candidate_id).delete()
    holder = _filler_holder()
    surplus = Shrine.objects.count() - PRODUCTION_PRESTATE["shrine_total"]
    if surplus > 0:
        removable = (
            Shrine.objects.exclude(pk=holder.pk).exclude(name_jp=SHRINE_NAME).order_by("-id")
        )[:surplus]
        Shrine.objects.filter(pk__in=list(removable.values_list("pk", flat=True))).delete()

    def missing(model, key: str) -> range:
        return range(PRODUCTION_PRESTATE[key] - model.objects.count())

    ShrineKnowledgeSource.objects.bulk_create(
        ShrineKnowledgeSource(
            source_type="internal_research",
            title=f"filler source {i}",
            url=f"https://example.invalid/h003-c6-filler/{i}",
        )
        for i in missing(ShrineKnowledgeSource, "source_total")
    )
    ShrineDeity.objects.bulk_create(
        ShrineDeity(shrine=holder, display_name=f"filler deity {i}")
        for i in missing(ShrineDeity, "deity_total")
    )
    ShrineHistory.objects.bulk_create(
        ShrineHistory(
            shrine=holder, history_type="tradition", title=f"filler history {i}", content="filler"
        )
        for i in missing(ShrineHistory, "history_total")
    )
    ShrineSourceFact.objects.bulk_create(
        ShrineSourceFact(
            shrine=holder,
            stable_key=f"h003-c6-filler-source-fact-{i}",
            source_attested_wording="filler",
            evidence_characterization="official_prayer_supported",
        )
        for i in missing(ShrineSourceFact, "source_fact_total")
    )
    ShrineDeityCollective.objects.bulk_create(
        ShrineDeityCollective(shrine=holder, source_attested_label=f"filler collective {i}")
        for i in missing(ShrineDeityCollective, "collective_total")
    )
    filler_source = ShrineKnowledgeSource.objects.filter(
        url__startswith="https://example.invalid/h003-c6-filler/"
    ).first()
    filler_histories = ShrineHistory.objects.filter(shrine=holder, title__startswith="filler")
    cited = list(
        filler_histories.order_by("id")[: len(missing(ShrineFactSourceCitation, "citation_total"))]
    )
    for history in cited:
        history.sources.add(filler_source)
        ShrineFactSourceCitation.objects.create(
            source=filler_source, shrine_history=history, locator_text="filler p.1"
        )
    _fill_goriyaku_aggregates()
    assert _aggregates() == PRODUCTION_PRESTATE


def _fill_goriyaku_aggregates() -> None:
    """non-empty goriyaku / GoriyakuTag master / tag link を target 以外の行だけで実測値に合わせる。"""
    nonempty = Shrine.objects.exclude(goriyaku__isnull=True).exclude(goriyaku="")
    gap = PRODUCTION_PRESTATE["shrine_nonempty_goriyaku_total"] - nonempty.count()
    if gap > 0:
        empty = Shrine.objects.exclude(name_jp=SHRINE_NAME).filter(goriyaku="").order_by("id")
        Shrine.objects.filter(pk__in=list(empty.values_list("pk", flat=True)[:gap])).update(
            goriyaku="フィラー"
        )
    elif gap < 0:
        Shrine.objects.filter(
            pk__in=list(nonempty.order_by("-id").values_list("pk", flat=True)[:-gap])
        ).update(goriyaku="")

    through = Shrine.goriyaku_tags.through
    through.objects.all().delete()
    GoriyakuTag.objects.all().delete()
    tags = GoriyakuTag.objects.bulk_create(
        GoriyakuTag(name=f"H003C6フィラー{i:02d}")
        for i in range(PRODUCTION_PRESTATE["goriyaku_tag_master_total"])
    )
    # link は non-empty goriyaku の少数 Shrine に集中させ、他の行は link なしのまま残す
    shrines = list(
        Shrine.objects.exclude(name_jp=SHRINE_NAME)
        .exclude(goriyaku="")
        .exclude(goriyaku__isnull=True)
        .order_by("id")[:10]
    )
    pairs = [(shrine, tag) for shrine in shrines for tag in tags]
    through.objects.bulk_create(
        through(shrine_id=shrine.pk, goriyakutag_id=tag.pk)
        for shrine, tag in pairs[: PRODUCTION_PRESTATE["goriyaku_tag_link_total"]]
    )


def _write_subset(tmp_path: Path) -> Path:
    output = tmp_path / "h003_c6_subset.json"
    assert _extractor().main(["--output", str(output)]) == 0
    return output


def _apply_subset(tmp_path: Path) -> str:
    return _import(_write_subset(tmp_path))


# --------------------------------------------------------------------------------------
# 1. Extractor（no DB）
# --------------------------------------------------------------------------------------


def test_extractor_emits_exactly_the_four_frozen_rows_in_candidate_order():
    module = _extractor()
    assert module.TARGET_IDS == TARGET_IDS
    subset = module.extract_subset(_seed_rows())
    assert [(r["name_jp"], r["address"]) for r in subset] == [
        (SHRINE_NAME, TARGETS[cid][0]) for cid in TARGET_IDS
    ]
    seed = {(r["name_jp"], r["address"]): r for r in _seed_rows()}
    for candidate_id, row in zip(TARGET_IDS, subset, strict=True):
        address, lat, lng = TARGETS[candidate_id]
        assert row == seed[(SHRINE_NAME, address)] == module.EXPECTED_ROWS[candidate_id]
        assert (row["latitude"], row["longitude"]) == (lat, lng)
        assert row["location"] == {"lat": lat, "lng": lng}
        assert (row["goriyaku"], row["kyusei"], row["astro_elements"]) == ("", None, [])
        for key in ("goriyaku_tags", "visit_style_tags", "history_theme"):
            assert key not in row


def test_extractor_output_and_sha256_are_deterministic(tmp_path, capsys):
    module = _extractor()
    first = module.render(module.extract_subset(_seed_rows()))
    assert first == module.render(module.extract_subset(_seed_rows()))

    a, b = tmp_path / "a.json", tmp_path / "b.json"
    assert module.main(["--output", str(a)]) == 0
    out_a = capsys.readouterr().out
    assert module.main(["--output", str(b)]) == 0
    out_b = capsys.readouterr().out
    assert a.read_bytes() == b.read_bytes() == first.encode("utf-8")
    sha = hashlib.sha256(first.encode("utf-8")).hexdigest()
    for out in (out_a, out_b):
        assert out.splitlines() == [
            "SUBSET_ROWS=4",
            f"candidate_ids={','.join(TARGET_IDS)}",
            f"SUBSET_SHA256={sha}",
        ]


def test_full_base_seed_is_never_the_production_payload():
    module = _extractor()
    full = _seed_rows()
    subset = json.loads(module.render(module.extract_subset(full)))
    assert len(full) == 129
    assert len(subset) == 4
    target_identities = {(SHRINE_NAME, address) for address, _, _ in TARGETS.values()}
    others = [r for r in full if (r["name_jp"], r["address"]) not in target_identities]
    assert len(others) == 125
    assert all(row not in subset for row in others)
    # 群馬県の別の赤城神社（同名・別住所）は抽出されない
    assert not [r for r in subset if r["address"].startswith("群馬県")]


@pytest.mark.parametrize(
    "target_ids",
    [
        (*TARGET_IDS, HOLD_ID),
        ("nsrc-000011", "nsrc-000012", "nsrc-000013", HOLD_ID),
        (HOLD_ID,),
    ],
    ids=["hold-appended", "hold-substituted", "hold-only"],
)
def test_extractor_blocks_nsrc_000014(target_ids):
    module = _extractor()
    with pytest.raises(module.SubsetBlocked, match="nsrc-000014"):
        module.extract_subset(_seed_rows(), target_ids)


@pytest.mark.parametrize(
    "target_ids",
    [
        (*TARGET_IDS, "nsrc-000016"),
        TARGET_IDS[:3],
        tuple(reversed(TARGET_IDS)),
        (),
    ],
    ids=["extra-target", "missing-target", "reordered", "empty"],
)
def test_extractor_blocks_any_other_target_set(target_ids):
    module = _extractor()
    with pytest.raises(module.SubsetBlocked, match="target set must be exactly"):
        module.extract_subset(_seed_rows(), target_ids)


def test_extractor_blocks_a_hold_row_in_rendered_output():
    module = _extractor()
    subset = module.extract_subset(_seed_rows())
    subset[-1] = {**subset[-1], "address": HOLD_ADDRESS}
    with pytest.raises(module.SubsetBlocked, match="nsrc-000014"):
        module.render(subset)
    with pytest.raises(module.SubsetBlocked, match="exactly 4"):
        module.render(subset[:3])


def _without(rows: list[dict], address: str) -> list[dict]:
    return [r for r in rows if not (r["name_jp"] == SHRINE_NAME and r["address"] == address)]


def test_extractor_fails_closed_on_missing_or_duplicated_target():
    module = _extractor()
    rows = _seed_rows()
    address = TARGETS[MUTATED][0]
    with pytest.raises(module.SubsetBlocked, match=f"{MUTATED} expected exactly 1.*found 0"):
        module.extract_subset(_without(rows, address))
    duplicated = [*rows, dict(module.EXPECTED_ROWS[MUTATED])]
    with pytest.raises(module.SubsetBlocked, match=f"{MUTATED} expected exactly 1.*found 2"):
        module.extract_subset(duplicated)
    with pytest.raises(module.SubsetBlocked, match="exactly 1"):
        module.extract_subset([r for r in rows if r["name_jp"] != SHRINE_NAME])
    with pytest.raises(module.SubsetBlocked, match="JSON list"):
        module.extract_subset({"rows": rows})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("latitude", 37.4964),
        ("longitude", 139.0086),
        ("location", {"lat": 37.4964, "lng": 139.00862}),
        ("goriyaku", "開運"),
        ("kyusei", "一白水星"),
        ("astro_elements", ["火"]),
        ("visit_style_tags", ["nature"]),
        ("history_theme", "military"),
    ],
)
def test_extractor_fails_closed_on_mutated_target_row(field, value):
    module = _extractor()
    rows = _seed_rows()
    address = TARGETS[MUTATED][0]
    for row in rows:
        if row["name_jp"] == SHRINE_NAME and row["address"] == address:
            row[field] = value
    with pytest.raises(module.SubsetBlocked, match=f"{MUTATED} Base Seed row differs"):
        module.extract_subset(rows)


def test_extractor_refuses_repository_output_path(capsys):
    module = _extractor()
    for path in (REPO_ROOT / "h003_c6_subset.json", SQL_DIR / "h003_c6_subset.json"):
        assert module.main(["--output", str(path)]) == 1
        assert not path.exists()
        assert "inside the repository" in capsys.readouterr().err


def test_extractor_never_silently_overwrites_existing_output(tmp_path, capsys):
    module = _extractor()
    output = tmp_path / "subset.json"
    output.write_text("existing", encoding="utf-8")
    assert module.main(["--output", str(output)]) == 1
    assert "exists" in capsys.readouterr().err
    assert output.read_text(encoding="utf-8") == "existing"
    assert module.main(["--output", str(output), "--overwrite"]) == 0
    assert json.loads(output.read_text(encoding="utf-8")) == module.extract_subset(_seed_rows())


def test_extractor_has_no_db_or_credential_access():
    source = (SAFETY_DIR / "niigata_h003_c6_extract_base_subset.py").read_text(encoding="utf-8")
    for token in ("django", "psycopg", "DATABASE_URL", "connection", "environ", "getenv", "socket"):
        assert token not in source, token


# --------------------------------------------------------------------------------------
# 2. Static SQL contract
# --------------------------------------------------------------------------------------


def test_guard_sql_is_readonly_select_or_with_only():
    is_readonly_sql = _guard_module().is_readonly_sql
    write_verbs = re.compile(
        r"\b(insert|update|delete|truncate|drop|alter|create|grant|revoke|copy|merge|call|"
        r"vacuum|lock|comment|refresh|reindex|cluster)\b",
        re.IGNORECASE,
    )
    for name in GUARD_FILES:
        text = _sql(name)
        ok, reason = is_readonly_sql(text)
        assert ok is True, (name, reason)
        lowered = text.lower()
        for token in ("postgres://", "postgresql://", "password", "sslmode", "@localhost"):
            assert token not in lowered, (name, token)
        for statement in _statements(text):
            assert re.match(r"^(select|with)\b", statement, re.IGNORECASE), (name, statement)
            assert not write_verbs.search(statement), (name, statement)


def test_target_state_block_is_byte_identical_to_the_preflight():
    preflight_block = TARGET_BLOCK_RE.search(_sql(PREFLIGHT)).group(0)
    for name in GUARD_FILES:
        blocks = TARGET_BLOCK_RE.findall(_sql(name))
        assert blocks and set(blocks) == {preflight_block}, name


def test_frozen_block_is_identical_and_equals_the_production_measurement():
    blocks = {FROZEN_BLOCK_RE.search(_sql(name)).group(0) for name in GUARD_FILES}
    assert len(blocks) == 1
    (block,) = blocks
    frozen = dict(
        (name, int(value)) for value, name in re.findall(r"(\d+)::bigint AS (\w+)", block)
    )
    assert frozen == {**PRODUCTION_PRESTATE, "expected_shrine_delta": EXPECTED_SHRINE_DELTA}
    for name in GUARD_FILES:
        assert len(FROZEN_BLOCK_RE.findall(_sql(name))) == _sql(name).count("WITH\n")


def test_hold_identity_is_never_a_guard_target():
    for name in GUARD_FILES:
        for block in TARGET_BLOCK_RE.findall(_sql(name)):
            sql_only = "\n".join(
                ln for ln in block.splitlines() if not ln.lstrip().startswith("--")
            )
            assert HOLD_ID not in sql_only and HOLD_ADDRESS not in sql_only


# --------------------------------------------------------------------------------------
# 3. Committed pre-Base guard on the simulated exact Production pre-state
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_committed_pre_base_guard_passes_on_the_exact_production_prestate():
    _simulate_production_prestate()
    assert _committed_guard_passes(PRE_GUARD) is True
    assert _committed_guard_passes(POST_VERIFY) is False
    # the preflight itself still classifies this state as CLEAN_CREATE
    assert _run_all(_sql(PREFLIGHT))[-1][0][0] == "CLEAN_CREATE"


@pytest.mark.django_db
def test_committed_guards_fail_on_a_non_production_state():
    _import(BASE_SEED_PATH)
    assert _committed_guard_passes(PRE_GUARD) is False
    assert _committed_guard_passes(POST_VERIFY) is False


def _holder_deity() -> None:
    ShrineDeity.objects.create(shrine=_filler_holder(), display_name="drift")


def _citation_elsewhere() -> None:
    history = (
        ShrineHistory.objects.filter(shrine=_filler_holder(), title__startswith="filler")
        .exclude(source_citations__isnull=False)
        .first()
    )
    source = ShrineKnowledgeSource.objects.filter(
        url__startswith="https://example.invalid/h003-c6-filler/"
    ).first()
    history.sources.add(source)
    ShrineFactSourceCitation.objects.create(
        source=source, shrine_history=history, locator_text="drift"
    )


def _non_target_rows():
    return Shrine.objects.exclude(name_jp=SHRINE_NAME)


def _nonempty_goriyaku_plus_one() -> None:
    row = _non_target_rows().filter(goriyaku="").order_by("id").first()
    Shrine.objects.filter(pk=row.pk).update(goriyaku="ドリフト")


def _nonempty_goriyaku_minus_one() -> None:
    row = _non_target_rows().exclude(goriyaku="").exclude(goriyaku__isnull=True).first()
    Shrine.objects.filter(pk=row.pk).update(goriyaku="")


def _unused_link_pair() -> tuple[Shrine, GoriyakuTag]:
    through = Shrine.goriyaku_tags.through
    for tag in GoriyakuTag.objects.order_by("-id"):
        for shrine in _non_target_rows().order_by("-id"):
            if not through.objects.filter(shrine_id=shrine.pk, goriyakutag_id=tag.pk).exists():
                return shrine, tag
    raise AssertionError("no unused (shrine, tag) pair")


def _goriyaku_tag_link_elsewhere() -> None:
    shrine, tag = _unused_link_pair()
    shrine.goriyaku_tags.add(tag)


def _assignment_kwargs() -> dict:
    return {
        "shrine": _filler_holder(),
        "canonical_key": "h003-c6-drift",
        "taxonomy_version": "v1",
        "lifecycle": "ACTIVE",
        "producer": "curator",
        "mechanism": "manual_review",
        "assigned_at": timezone.now(),
    }


AGGREGATE_DRIFT_EXTENDED = {
    "citation+1": _citation_elsewhere,
    "nonempty-goriyaku+1": _nonempty_goriyaku_plus_one,
    "nonempty-goriyaku-1": _nonempty_goriyaku_minus_one,
    "goriyaku-tag-master+1": lambda: GoriyakuTag.objects.create(name="H003C6ドリフト"),
    "goriyaku-tag-link+1": _goriyaku_tag_link_elsewhere,
    "goriyaku-assignment+1": lambda: ShrineGoriyakuAssignment.objects.create(
        **_assignment_kwargs()
    ),
    "history-theme-assignment+1": lambda: HistoryThemeAssignment.objects.create(
        **_assignment_kwargs()
    ),
    "canonical-anchor+1": lambda: ShrineCanonicalAnchor.objects.create(
        shrine=_filler_holder(), status="HOLD_POSITION_REVIEW"
    ),
}


PRESTATE_DRIFT = {
    "shrine+1": lambda: Shrine.objects.create(
        name_jp="無関係神社", kind="shrine", address="架空県1"
    ),
    "shrine-1": lambda: (
        Shrine.objects.exclude(pk=_filler_holder().pk)
        .exclude(name_jp=SHRINE_NAME)
        .order_by("-id")
        .first()
        .delete()
    ),
    "source+1": lambda: ShrineKnowledgeSource.objects.create(
        source_type="internal_research", title="x", url="https://example.invalid/drift"
    ),
    "deity+1": _holder_deity,
    "history+1": lambda: ShrineHistory.objects.create(
        shrine=_filler_holder(), history_type="tradition", title="drift", content="drift"
    ),
    "source-fact+1": lambda: ShrineSourceFact.objects.create(
        shrine=_filler_holder(),
        stable_key="h003-c6-drift",
        source_attested_wording="drift",
        evidence_characterization="official_prayer_supported",
    ),
    "collective+1": lambda: ShrineDeityCollective.objects.create(
        shrine=_filler_holder(), source_attested_label="drift"
    ),
    **AGGREGATE_DRIFT_EXTENDED,
}


@pytest.mark.django_db
@pytest.mark.parametrize("drift", sorted(PRESTATE_DRIFT))
def test_committed_pre_base_guard_fails_on_aggregate_drift(drift):
    _simulate_production_prestate()
    assert _committed_guard_passes(PRE_GUARD) is True
    PRESTATE_DRIFT[drift]()
    assert _committed_guard_passes(PRE_GUARD) is False


def _swap_in(**fields) -> None:
    """Shrine 総数を frozen 値のまま保ち、非 target の1行を指定行に置き換える。"""
    # 削除する行は goriyaku 空・tag link なし（aggregate を変えない）
    Shrine.objects.exclude(pk=_filler_holder().pk).exclude(name_jp=SHRINE_NAME).filter(
        goriyaku="", goriyaku_tags__isnull=True
    ).order_by("-id").first().delete()
    Shrine.objects.create(kind="shrine", **fields)


UNEXPECTED_ROWS = {
    "target-already-present": lambda: _swap_in(
        name_jp=SHRINE_NAME,
        address=TARGETS[MUTATED][0],
        latitude=TARGETS[MUTATED][1],
        longitude=TARGETS[MUTATED][2],
    ),
    "same-address-other-name": lambda: _swap_in(name_jp="山屋神社", address=TARGETS[MUTATED][0]),
    "hold-identity-present": lambda: _swap_in(name_jp=SHRINE_NAME, address=HOLD_ADDRESS),
    "hold-address-other-name": lambda: _swap_in(name_jp="上杉川神社", address=HOLD_ADDRESS),
}


@pytest.mark.django_db
@pytest.mark.parametrize("case", sorted(UNEXPECTED_ROWS))
def test_committed_pre_base_guard_fails_on_unexpected_row(case):
    _simulate_production_prestate()
    assert _committed_guard_passes(PRE_GUARD) is True
    UNEXPECTED_ROWS[case]()
    assert _aggregates() == PRODUCTION_PRESTATE  # only the identity changed, not the counts
    assert _committed_guard_passes(PRE_GUARD) is False


# --------------------------------------------------------------------------------------
# 4. Target-only import rehearsal + committed post-Base verification
# --------------------------------------------------------------------------------------


@pytest.mark.django_db
def test_target_only_import_rehearsal(tmp_path):
    _simulate_production_prestate()
    assert _committed_guard_passes(PRE_GUARD) is True

    subset = _write_subset(tmp_path)
    dry = _import(subset, "--dry-run")
    assert "done created=4 updated=0 skipped=0 total_seed=4" in dry
    assert _aggregates() == PRODUCTION_PRESTATE

    applied = _import(subset)
    assert "done created=4 updated=0 skipped=0 total_seed=4" in applied
    assert _aggregates() == {
        **PRODUCTION_PRESTATE,
        "shrine_total": PRODUCTION_PRESTATE["shrine_total"] + EXPECTED_SHRINE_DELTA,
    }
    assert _committed_guard_passes(POST_VERIFY) is True
    assert _committed_guard_passes(PRE_GUARD) is False

    # second import is a no-op
    second = _import(subset, "--dry-run")
    assert "done created=0 updated=0 skipped=4 total_seed=4" in second
    assert _import(subset).count("done created=0 updated=0 skipped=4 total_seed=4") == 1
    assert _committed_guard_passes(POST_VERIFY) is True

    for candidate_id in TARGET_IDS:
        address, lat, lng = TARGETS[candidate_id]
        shrine = _target(candidate_id)
        assert (shrine.latitude, shrine.longitude) == (lat, lng)
        assert (shrine.goriyaku, shrine.visit_style_tags, shrine.history_theme) == ("", [], "")
        assert not shrine.goriyaku_tags.exists()
    assert not Shrine.objects.filter(address=HOLD_ADDRESS).exists()
    assert _run_all(_sql(PREFLIGHT))[-1][0][0] == "ALREADY_MATERIALIZED"


def _post_state(tmp_path) -> None:
    _simulate_production_prestate()
    _apply_subset(tmp_path)
    assert _committed_guard_passes(POST_VERIFY) is True


def _update_target(**fields) -> None:
    Shrine.objects.filter(pk=_target(MUTATED).pk).update(**fields)


def _goriyaku_tag_link() -> None:
    """tag link 総数を保ったまま、filler link 1件を target の link に置き換える。"""
    through = Shrine.goriyaku_tags.through
    link = through.objects.exclude(shrine__name_jp=SHRINE_NAME).order_by("-id").first()
    tag_id = link.goriyakutag_id
    link.delete()
    through.objects.create(shrine_id=_target(MUTATED).pk, goriyakutag_id=tag_id)


def _swap_holder_history_for_target_history() -> None:
    """History / Source / Citation 総数を保ったまま target に usable History Fact を付ける。"""
    ShrineHistory.objects.filter(shrine=_filler_holder(), source_citations__isnull=True).order_by(
        "-id"
    ).first().delete()
    attach_usable_history_fact(_target(MUTATED))
    ShrineKnowledgeSource.objects.filter(
        url__startswith="https://example.invalid/h003-c6-filler/", fact_citations__isnull=True
    ).order_by("-id").first().delete()


def _swap_holder_deity_for_target_deity() -> None:
    ShrineDeity.objects.filter(shrine=_filler_holder()).order_by("-id").first().delete()
    ShrineDeity.objects.create(shrine=_target(MUTATED), display_name="豊城入彦命")


POST_DRIFT = {
    "coordinate-drift": lambda: _update_target(latitude=TARGETS[MUTATED][1] + 1e-9),
    "coordinate-null": lambda: _update_target(latitude=None, longitude=None),
    "goriyaku-set": lambda: _update_target(goriyaku="開運"),
    "goriyaku-null": lambda: _update_target(goriyaku=None),
    "kyusei-set": lambda: _update_target(kyusei="一白水星"),
    "astro-set": lambda: _update_target(astro_elements=["火"]),
    "sajin-set": lambda: _update_target(sajin="豊城入彦命"),
    "visit-style-set": lambda: _update_target(visit_style_tags=["nature"]),
    "history-theme-set": lambda: _update_target(history_theme="military"),
    "kind-changed": lambda: _update_target(kind="temple"),
    "goriyaku-tag-link": _goriyaku_tag_link,
    "target-history-fact": _swap_holder_history_for_target_history,
    "target-deity": _swap_holder_deity_for_target_deity,
    "unrelated-shrine+1": lambda: Shrine.objects.create(
        name_jp="無関係神社", kind="shrine", address="架空県2"
    ),
    "target-missing": lambda: _target(MUTATED).delete(),
    "hold-identity-added": lambda: _swap_in(name_jp=SHRINE_NAME, address=HOLD_ADDRESS),
    "same-address-other-name": lambda: _swap_in(name_jp="山屋神社", address=TARGETS[MUTATED][0]),
    "deity+1-elsewhere": _holder_deity,
    **AGGREGATE_DRIFT_EXTENDED,
}


POST_AGGREGATES = {
    **PRODUCTION_PRESTATE,
    "shrine_total": PRODUCTION_PRESTATE["shrine_total"] + EXPECTED_SHRINE_DELTA,
}
POST_DRIFT_SAME_AGGREGATES = set(POST_DRIFT) - {
    "unrelated-shrine+1",
    "target-missing",
    "deity+1-elsewhere",
    "goriyaku-set",  # target goriyaku '' -> 開運 also moves shrine_nonempty_goriyaku_total
    *AGGREGATE_DRIFT_EXTENDED,
}


@pytest.mark.django_db
@pytest.mark.parametrize("drift", sorted(POST_DRIFT))
def test_committed_post_base_verification_fails_closed(drift, tmp_path):
    _post_state(tmp_path)
    POST_DRIFT[drift]()
    if drift in POST_DRIFT_SAME_AGGREGATES:
        # the verification must fail on the target state itself, not on an aggregate count
        assert _aggregates() == POST_AGGREGATES
    assert _committed_guard_passes(POST_VERIFY) is False


@pytest.mark.django_db
def test_post_base_verification_tolerates_importer_round_trip_only(tmp_path):
    _post_state(tmp_path)
    _update_target(latitude=TARGETS[MUTATED][1] + 1e-13)
    assert _committed_guard_passes(POST_VERIFY) is True
