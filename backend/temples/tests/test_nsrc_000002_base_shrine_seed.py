"""nsrc-000002 青澤神社の Base Shrine materialization（G4 blocker BASE_SHRINE_NOT_MATERIALIZED の解消）。

canonical identity / 座標は G2 / G3 / G4 preflight の凍結値
（docs/audit/niigata-h001-g2-position-gate.md、
docs/audit/niigata-h001-nsrc-000002-g4-evidence-preflight.md）。
goriyaku / goriyaku_tags / visit_style_tags は推測しない。Knowledge Seed は本 PR では作らない。
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

BASE_SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "shrines_seed_clean.json"

SHRINE_NAME = "青澤神社"
SHRINE_ADDRESS = "新潟県糸魚川市大字青海2696番地"
LATITUDE = 37.00763484
LONGITUDE = 137.79024297

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

EXPECTED_TOTAL_ROWS = 122
EXISTING_ROW_COUNT = 121
# 追加前の Base Seed 121行（develop af025087）の fingerprint。
EXISTING_ROWS_SHA256 = "ed2dc758dba5b814ad6dfd005c4512638844947bbcb910fe2e2abcafcd5c2eda"


def _rows() -> list[dict]:
    return json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))


def _target_rows(rows: list[dict]) -> list[dict]:
    return [
        row
        for row in rows
        if row.get("name_jp") == SHRINE_NAME and row.get("address") == SHRINE_ADDRESS
    ]


def test_nsrc_000002_identity_occurs_exactly_once():
    assert len(_target_rows(_rows())) == 1


def test_nsrc_000002_row_is_exactly_the_frozen_canonical_values():
    row = _target_rows(_rows())[0]
    assert row == EXPECTED_ROW
    assert row["latitude"] == LATITUDE
    assert row["longitude"] == LONGITUDE
    assert row["location"] == {"lat": row["latitude"], "lng": row["longitude"]}
    assert row["goriyaku"] == ""
    assert row["kyusei"] is None
    assert row["astro_elements"] == []


def test_nsrc_000002_row_has_no_inferred_tags():
    row = _target_rows(_rows())[0]
    assert "goriyaku_tags" not in row
    assert "visit_style_tags" not in row


def test_nsrc_000002_is_appended_after_the_existing_rows():
    rows = _rows()
    assert len(rows) == EXPECTED_TOTAL_ROWS
    assert rows[-1] == EXPECTED_ROW


def test_existing_121_rows_are_unchanged():
    rows = _rows()
    existing = [
        row
        for row in rows
        if not (row.get("name_jp") == SHRINE_NAME and row.get("address") == SHRINE_ADDRESS)
    ]
    assert len(existing) == EXISTING_ROW_COUNT
    assert existing == rows[:EXISTING_ROW_COUNT]
    canonical = json.dumps(
        sorted(existing, key=lambda row: (row.get("name_jp", ""), row.get("address", ""))),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == EXISTING_ROWS_SHA256


def test_base_seed_has_no_duplicate_identity():
    identities = Counter((row.get("name_jp"), row.get("address")) for row in _rows())
    duplicates = {identity: count for identity, count in identities.items() if count > 1}
    assert duplicates == {}
