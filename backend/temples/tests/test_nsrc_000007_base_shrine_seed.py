"""nsrc-000007 赤城社の Base Shrine materialization（G4 blocker BASE_SHRINE_NOT_MATERIALIZED の解消）。

canonical identity / 座標は G2 Position Resolution の凍結値
（docs/audit/shrine-position/niigata-h002-akagi-sha-position-resolution.md）。
G4 preflight: docs/audit/niigata-h002-nsrc-000007-g4-evidence-preflight.md。
goriyaku / goriyaku_tags / visit_style_tags は推測しない。Knowledge Seed は本 PR では作らない。

H002 には別実体の同名 `赤城社` が複数あるため、identity は必ず exact (name_jp, address) で扱う。
"""

from __future__ import annotations

import copy
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import Shrine
from temples.services.knowledge_seed import resolve_shrine

BASE_SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "shrines_seed_clean.json"

SHRINE_NAME = "赤城社"
SHRINE_ADDRESS = "新潟県十日町市四日町2534番地"
LATITUDE = 37.14755658
LONGITUDE = 138.76887612

EXPECTED_ROW = {
    "name_jp": SHRINE_NAME,
    "address": SHRINE_ADDRESS,
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "goriyaku": "",
    "kyusei": None,
    "astro_elements": [],
    "location": {"lat": LATITUDE, "lng": LONGITUDE},
}

# nsrc-000007 は Base Seed の historical cohort rows[122:123] を占める。
# 後続の append で総行数が増えても、この境界は変わらない。
NSRC_000007_EXISTING_BASE_ROW_COUNT = 122
NSRC_000007_BASE_ROW_END = 123
# 追加前の Base Seed 122行（develop 7f88f5e9）の fingerprint。
# rows[:NSRC_000007_EXISTING_BASE_ROW_COUNT] だけから計算する。
EXISTING_ROWS_SHA256 = "02983b6dcc54591c7a9a88923a9c5998cf942bbdf25e8589b623463a82c26efc"

# 他の H002 同名候補（本 PR の scope 外。Base Seed へは追加しない）。
OTHER_AKAGI_ADDRESSES = (
    "新潟県十日町市上組2059番地子",
    "新潟県十日町市伊達乙48番地",
    "新潟県南魚沼市芹田79番地",
)


def _rows() -> list[dict]:
    return json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))


def _target_rows(rows: list[dict]) -> list[dict]:
    return [
        row
        for row in rows
        if row.get("name_jp") == SHRINE_NAME and row.get("address") == SHRINE_ADDRESS
    ]


def _prefix_fingerprint(rows: list[dict]) -> str:
    canonical = json.dumps(
        sorted(rows, key=lambda row: (row.get("name_jp", ""), row.get("address", ""))),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _violations(rows: list[dict]) -> list[str]:
    """nsrc-000007 の historical cohort accounting。後続 append は許容する。"""
    start, end = NSRC_000007_EXISTING_BASE_ROW_COUNT, NSRC_000007_BASE_ROW_END
    violations = []
    if len(rows) < end:
        violations.append(f"base seed has {len(rows)} rows, fewer than cohort end {end}")
    if _prefix_fingerprint(rows[:start]) != EXISTING_ROWS_SHA256:
        violations.append("historical prefix fingerprint mismatch")
    if rows[start:end] != [EXPECTED_ROW]:
        violations.append(f"rows[{start}:{end}] is not the nsrc-000007 row")
    count = len(_target_rows(rows))
    if count != 1:
        violations.append(f"nsrc-000007 identity occurs {count} times")
    return violations


# --- Base Seed file ----------------------------------------------------------------------------


def test_nsrc_000007_identity_occurs_exactly_once():
    assert len(_target_rows(_rows())) == 1


def test_nsrc_000007_row_is_exactly_the_frozen_canonical_values():
    row = _target_rows(_rows())[0]
    assert row == EXPECTED_ROW
    assert row["location"] == {"lat": row["latitude"], "lng": row["longitude"]}


def test_nsrc_000007_row_has_no_inferred_fields():
    row = _target_rows(_rows())[0]
    assert row["goriyaku"] == ""
    assert row["kyusei"] is None
    assert row["astro_elements"] == []
    for key in ("goriyaku_tags", "visit_style_tags", "history_theme"):
        assert key not in row


def test_nsrc_000007_occupies_historical_cohort_position_122():
    rows = _rows()
    start, end = NSRC_000007_EXISTING_BASE_ROW_COUNT, NSRC_000007_BASE_ROW_END
    assert len(rows) >= end
    assert rows[start:end] == [EXPECTED_ROW]


def test_existing_122_rows_are_unchanged():
    prefix = _rows()[:NSRC_000007_EXISTING_BASE_ROW_COUNT]
    assert len(prefix) == NSRC_000007_EXISTING_BASE_ROW_COUNT
    assert _target_rows(prefix) == []
    assert _prefix_fingerprint(prefix) == EXISTING_ROWS_SHA256


def test_nsrc_000007_historical_base_seed_cohort_is_append_safe():
    assert _violations(_rows()) == []


def test_nsrc_000007_accounting_allows_later_appended_rows():
    rows = copy.deepcopy(_rows())
    rows.append({"name_jp": "後続追加神社", "address": "架空県架空市1-1"})
    assert _violations(rows) == []


@pytest.mark.parametrize(
    ("mutate", "expected_violation"),
    [
        (lambda rows: rows.pop(122), "is not the nsrc-000007 row"),
        (
            lambda rows: rows[122].update(address="新潟県十日町市四日町2534"),
            "nsrc-000007 identity occurs 0 times",
        ),
        (lambda rows: rows[122].update(latitude=37.147573), "is not the nsrc-000007 row"),
        (lambda rows: rows.pop(0), "historical prefix fingerprint mismatch"),
        (lambda rows: rows[0].update(goriyaku="変更"), "historical prefix fingerprint mismatch"),
        (
            lambda rows: rows.append(copy.deepcopy(rows[122])),
            "nsrc-000007 identity occurs 2 times",
        ),
    ],
    ids=[
        "remove-nsrc-000007",
        "change-nsrc-000007-address",
        "change-nsrc-000007-coordinate",
        "remove-earlier-prefix-row",
        "mutate-historical-prefix-row",
        "duplicate-nsrc-000007-later",
    ],
)
def test_nsrc_000007_accounting_rejects_mutation(mutate, expected_violation):
    rows = copy.deepcopy(_rows())
    mutate(rows)
    violations = _violations(rows)
    assert any(expected_violation in v for v in violations), violations


def test_base_seed_has_no_duplicate_identity():
    identities = Counter((row.get("name_jp"), row.get("address")) for row in _rows())
    assert {identity: n for identity, n in identities.items() if n > 1} == {}


def test_only_the_nsrc_000007_akagi_sha_is_in_the_base_seed():
    rows = [row for row in _rows() if row.get("name_jp") == SHRINE_NAME]
    assert [row["address"] for row in rows] == [SHRINE_ADDRESS]


# --- exact-address resolution on an isolated test DB ---------------------------------------------


def _import_base_seed() -> str:
    out = io.StringIO()
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=out,
        stderr=io.StringIO(),
    )
    return out.getvalue()


@pytest.mark.django_db
def test_base_seed_import_resolves_the_exact_nsrc_000007_row():
    summary = _import_base_seed()
    assert "total_seed=123" in summary
    target = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    assert (target.latitude, target.longitude) == (LATITUDE, LONGITUDE)

    result = resolve_shrine(SHRINE_NAME, SHRINE_ADDRESS)
    assert result.status == "OK"
    assert result.shrine.pk == target.pk


@pytest.mark.django_db
@pytest.mark.parametrize("other_address", OTHER_AKAGI_ADDRESSES)
def test_other_akagi_address_never_resolves_to_nsrc_000007(other_address):
    _import_base_seed()
    target = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    result = resolve_shrine(SHRINE_NAME, other_address)
    assert result.status == "NOT_FOUND"
    assert result.shrine is None or result.shrine.pk != target.pk


@pytest.mark.django_db
def test_same_name_rows_do_not_make_nsrc_000007_ambiguous():
    _import_base_seed()
    target = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    others = [
        Shrine.objects.create(name_jp=SHRINE_NAME, kind="shrine", address=address)
        for address in OTHER_AKAGI_ADDRESSES
    ]
    result = resolve_shrine(SHRINE_NAME, SHRINE_ADDRESS)
    assert result.status == "OK"
    assert result.shrine.pk == target.pk
    for other in others:
        assert resolve_shrine(SHRINE_NAME, other.address).shrine.pk == other.pk
