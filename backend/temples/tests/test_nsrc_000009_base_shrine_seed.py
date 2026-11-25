"""nsrc-000009 赤城社の Base Shrine materialization regression。

Authority:
- docs/audit/niigata-h002-nsrc-000009-g1-identity-duplicate.md
- docs/audit/shrine-position/niigata-h002-nsrc-000009-akagi-sha-position-review.md

Knowledge / goriyaku / Recommendation はこのPRでは扱わない。
H002には別実体の同名「赤城社」が複数あるため、exact (name_jp, address) でのみ解決する。
"""

from __future__ import annotations

import copy
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
SHRINE_ADDRESS = "新潟県十日町市伊達乙48番地"
LATITUDE = 37.089683
LONGITUDE = 138.748108

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

# develop before this materialization has 124 rows.
EXISTING_BASE_ROW_COUNT = 124
TARGET_ROW_END = 125

OTHER_AKAGI_ADDRESSES = (
    "新潟県十日町市四日町2534番地",
    "新潟県十日町市上組2059番地子",
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


def test_nsrc_000009_identity_occurs_exactly_once():
    assert len(_target_rows(_rows())) == 1


def test_nsrc_000009_row_is_exactly_the_frozen_values():
    assert _target_rows(_rows()) == [EXPECTED_ROW]


def test_nsrc_000009_row_has_no_inferred_fields():
    row = _target_rows(_rows())[0]
    assert row["goriyaku"] == ""
    assert row["kyusei"] is None
    assert row["astro_elements"] == []
    for key in ("goriyaku_tags", "visit_style_tags", "history_theme"):
        assert key not in row


def test_nsrc_000009_is_appended_after_existing_124_rows():
    rows = _rows()
    assert len(rows) >= TARGET_ROW_END
    assert rows[EXISTING_BASE_ROW_COUNT:TARGET_ROW_END] == [EXPECTED_ROW]


def test_accounting_allows_later_appends_but_target_stays_once():
    rows = copy.deepcopy(_rows())
    rows.append({"name_jp": "後続追加神社", "address": "架空県架空市1-1"})
    assert rows[EXISTING_BASE_ROW_COUNT:TARGET_ROW_END] == [EXPECTED_ROW]
    assert len(_target_rows(rows)) == 1


def test_base_seed_has_no_duplicate_identity():
    identities = Counter((row.get("name_jp"), row.get("address")) for row in _rows())
    assert {identity: n for identity, n in identities.items() if n > 1} == {}


def test_akagi_rows_are_distinct_exact_addresses():
    addresses = [row["address"] for row in _rows() if row.get("name_jp") == SHRINE_NAME]
    assert SHRINE_ADDRESS in addresses
    assert "新潟県十日町市四日町2534番地" in addresses
    assert len(addresses) == len(set(addresses))


@pytest.mark.django_db
def test_base_seed_import_resolves_exact_nsrc_000009():
    summary = _import_base_seed()
    assert f"total_seed={len(_rows())}" in summary
    target = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    assert (target.latitude, target.longitude) == (LATITUDE, LONGITUDE)

    result = resolve_shrine(SHRINE_NAME, SHRINE_ADDRESS)
    assert result.status == "OK"
    assert result.shrine is not None
    assert result.shrine.pk == target.pk


@pytest.mark.django_db
@pytest.mark.parametrize("other_address", OTHER_AKAGI_ADDRESSES)
def test_other_akagi_address_never_resolves_to_nsrc_000009(other_address):
    _import_base_seed()
    target = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    result = resolve_shrine(SHRINE_NAME, other_address)
    if result.shrine is not None:
        assert result.shrine.pk != target.pk


@pytest.mark.django_db
def test_same_name_rows_do_not_make_nsrc_000009_ambiguous():
    _import_base_seed()
    target = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)
    for address in OTHER_AKAGI_ADDRESSES:
        Shrine.objects.get_or_create(name_jp=SHRINE_NAME, kind="shrine", address=address)

    result = resolve_shrine(SHRINE_NAME, SHRINE_ADDRESS)
    assert result.status == "OK"
    assert result.shrine is not None
    assert result.shrine.pk == target.pk
