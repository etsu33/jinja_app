"""nsrc-000006 赤井神社の Base Shrine materialization。

canonical identity / 座標は G1 / G2 authority:
- docs/audit/niigata-h002-nsrc-000006-g1-identity-duplicate.md
- docs/audit/shrine-position/niigata-h002-akai-jinja-position-resolution.md

G4 Source Packet:
docs/audit/niigata-h002-nsrc-000006-g4-source-packet-freeze.md

goriyaku / goriyaku_tags / visit_style_tags は推測しない。
Knowledge Seed は本PRでは作らない。
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

SHRINE_NAME = "赤井神社"
SHRINE_ADDRESS = "新潟県佐渡市加茂歌代2662番地"
LATITUDE = 38.085938
LONGITUDE = 138.418312

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

# nsrc-000006 は Base Seed historical cohort rows[123:124] を占める。
# 後続appendで総行数が増えても、この境界は変えない。
EXISTING_BASE_ROW_COUNT = 123
BASE_ROW_END = 124

# nsrc-000007 materialization後の既存123行 fingerprint。
# docs/audit/niigata-h002-nsrc-000007-base-shrine-materialization.md §5。
EXISTING_ROWS_SHA256 = "85782dcb735fd695a8e8d79fc0ab21918347666c6127cee1f450210a6531e0dd"

# Researchで観測されたがcanonicalではない住所表記。
NON_CANONICAL_ADDRESSES = (
    "新潟県佐渡市加茂歌代2622番地",
    "新潟県佐渡市加茂歌代1164-7",
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
    start, end = EXISTING_BASE_ROW_COUNT, BASE_ROW_END
    violations = []
    if len(rows) < end:
        violations.append(f"base seed has {len(rows)} rows, fewer than cohort end {end}")
    if _prefix_fingerprint(rows[:start]) != EXISTING_ROWS_SHA256:
        violations.append("historical prefix fingerprint mismatch")
    if rows[start:end] != [EXPECTED_ROW]:
        violations.append(f"rows[{start}:{end}] is not the nsrc-000006 row")
    count = len(_target_rows(rows))
    if count != 1:
        violations.append(f"nsrc-000006 identity occurs {count} times")
    return violations


def test_nsrc_000006_identity_occurs_exactly_once():
    assert len(_target_rows(_rows())) == 1


def test_nsrc_000006_row_is_exactly_the_g2_values():
    row = _target_rows(_rows())[0]
    assert row == EXPECTED_ROW
    assert row["location"] == {"lat": row["latitude"], "lng": row["longitude"]}


def test_nsrc_000006_row_has_no_inferred_fields():
    row = _target_rows(_rows())[0]
    assert row["goriyaku"] == ""
    assert row["kyusei"] is None
    assert row["astro_elements"] == []
    for key in ("goriyaku_tags", "visit_style_tags", "history_theme"):
        assert key not in row


def test_nsrc_000006_occupies_historical_cohort_position_123():
    rows = _rows()
    assert len(rows) >= BASE_ROW_END
    assert rows[EXISTING_BASE_ROW_COUNT:BASE_ROW_END] == [EXPECTED_ROW]


def test_existing_123_rows_are_unchanged():
    prefix = _rows()[:EXISTING_BASE_ROW_COUNT]
    assert len(prefix) == EXISTING_BASE_ROW_COUNT
    assert _target_rows(prefix) == []
    assert _prefix_fingerprint(prefix) == EXISTING_ROWS_SHA256


def test_nsrc_000006_historical_cohort_is_append_safe():
    assert _violations(_rows()) == []


def test_nsrc_000006_accounting_allows_later_append():
    rows = copy.deepcopy(_rows())
    rows.append({"name_jp": "後続追加神社", "address": "架空県架空市1-1"})
    assert _violations(rows) == []


@pytest.mark.parametrize(
    ("mutate", "expected_violation"),
    [
        (lambda rows: rows.pop(123), "is not the nsrc-000006 row"),
        (
            lambda rows: rows[123].update(address="新潟県佐渡市加茂歌代2622番地"),
            "nsrc-000006 identity occurs 0 times",
        ),
        (lambda rows: rows[123].update(latitude=38.0859), "is not the nsrc-000006 row"),
        (
            lambda rows: rows.__setitem__(
                123, {"name_jp": "後続追加神社", "address": "架空県架空市1-1"}
            ),
            "is not the nsrc-000006 row",
        ),
        (
            lambda rows: (
                rows.append({"name_jp": "後続追加神社", "address": "架空県架空市1-1"}),
                rows.append(rows.pop(123)),
            ),
            "is not the nsrc-000006 row",
        ),
        (lambda rows: rows.pop(0), "historical prefix fingerprint mismatch"),
        (lambda rows: rows[0].update(goriyaku="変更"), "historical prefix fingerprint mismatch"),
        (
            lambda rows: rows.append(copy.deepcopy(rows[123])),
            "nsrc-000006 identity occurs 2 times",
        ),
    ],
    ids=[
        "remove-target",
        "change-address",
        "change-coordinate",
        "replace-target",
        "move-target",
        "remove-prefix-row",
        "mutate-prefix-row",
        "duplicate-target",
    ],
)
def test_nsrc_000006_accounting_rejects_mutation(mutate, expected_violation):
    rows = copy.deepcopy(_rows())
    mutate(rows)
    violations = _violations(rows)
    assert any(expected_violation in v for v in violations), violations


def test_base_seed_has_no_duplicate_identity():
    identities = Counter((row.get("name_jp"), row.get("address")) for row in _rows())
    assert {identity: n for identity, n in identities.items() if n > 1} == {}


def test_only_canonical_akai_jinja_is_in_base_seed():
    rows = [row for row in _rows() if row.get("name_jp") == SHRINE_NAME]
    assert [row["address"] for row in rows] == [SHRINE_ADDRESS]


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
def test_base_seed_import_resolves_exact_nsrc_000006_row():
    summary = _import_base_seed()
    assert "total_seed=124" in summary

    target = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    assert (target.latitude, target.longitude) == (LATITUDE, LONGITUDE)

    result = resolve_shrine(SHRINE_NAME, SHRINE_ADDRESS)
    assert result.status == "OK"
    assert result.shrine is not None
    assert result.shrine.pk == target.pk


@pytest.mark.django_db
@pytest.mark.parametrize("other_address", NON_CANONICAL_ADDRESSES)
def test_noncanonical_akai_address_never_resolves_to_target(other_address):
    _import_base_seed()
    target = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)

    result = resolve_shrine(SHRINE_NAME, other_address)
    assert result.status == "NOT_FOUND"
    assert result.shrine is None or result.shrine.pk != target.pk


@pytest.mark.django_db
def test_same_name_other_address_does_not_make_target_ambiguous():
    _import_base_seed()
    target = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    other = Shrine.objects.create(
        name_jp=SHRINE_NAME,
        kind="shrine",
        address="新潟県佐渡市架空町1番地",
    )

    exact = resolve_shrine(SHRINE_NAME, SHRINE_ADDRESS)
    assert exact.status == "OK"
    assert exact.shrine.pk == target.pk

    other_result = resolve_shrine(SHRINE_NAME, other.address)
    assert other_result.status == "OK"
    assert other_result.shrine.pk == other.pk != target.pk
