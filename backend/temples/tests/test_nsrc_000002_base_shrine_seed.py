"""nsrc-000002 青澤神社の Base Shrine materialization（G4 blocker BASE_SHRINE_NOT_MATERIALIZED の解消）。

canonical identity / 座標は G2 / G3 / G4 preflight の凍結値
（docs/audit/niigata-h001-g2-position-gate.md、
docs/audit/niigata-h001-nsrc-000002-g4-evidence-preflight.md）。
goriyaku / goriyaku_tags / visit_style_tags は推測しない。Knowledge Seed は本 PR では作らない。
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

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

# nsrc-000002 は Base Seed の historical cohort rows[121:122] を占める。
# 後続の append で総行数が増えても、この境界は変わらない。
NSRC_000002_EXISTING_BASE_ROW_COUNT = 121
NSRC_000002_BASE_ROW_END = 122
# 追加前の Base Seed 121行（develop af025087）の fingerprint。
# rows[:NSRC_000002_EXISTING_BASE_ROW_COUNT] だけから計算する。
EXISTING_ROWS_SHA256 = "ed2dc758dba5b814ad6dfd005c4512638844947bbcb910fe2e2abcafcd5c2eda"


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


def _nsrc_000002_accounting_violations(
    rows: list[dict],
    *,
    expected_row: dict,
    existing_count: int,
    row_end: int,
    prefix_sha256: str,
) -> list[str]:
    """nsrc-000002 の historical cohort accounting。後続 append は許容する。"""
    violations = []
    if len(rows) < row_end:
        violations.append(f"base seed has {len(rows)} rows, fewer than cohort end {row_end}")
    if _prefix_fingerprint(rows[:existing_count]) != prefix_sha256:
        violations.append("historical prefix fingerprint mismatch")
    if rows[existing_count:row_end] != [expected_row]:
        violations.append(f"rows[{existing_count}:{row_end}] is not the nsrc-000002 row")
    identity = (expected_row["name_jp"], expected_row["address"])
    count = sum(1 for row in rows if (row.get("name_jp"), row.get("address")) == identity)
    if count != 1:
        violations.append(f"nsrc-000002 identity occurs {count} times")
    return violations


def _violations(rows: list[dict]) -> list[str]:
    return _nsrc_000002_accounting_violations(
        rows,
        expected_row=EXPECTED_ROW,
        existing_count=NSRC_000002_EXISTING_BASE_ROW_COUNT,
        row_end=NSRC_000002_BASE_ROW_END,
        prefix_sha256=EXISTING_ROWS_SHA256,
    )


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


def test_nsrc_000002_occupies_historical_cohort_position_121():
    rows = _rows()
    start, end = NSRC_000002_EXISTING_BASE_ROW_COUNT, NSRC_000002_BASE_ROW_END
    assert len(rows) >= end
    assert rows[start:end] == [EXPECTED_ROW]


def test_existing_121_rows_are_unchanged():
    rows = _rows()
    prefix = rows[:NSRC_000002_EXISTING_BASE_ROW_COUNT]
    assert len(prefix) == NSRC_000002_EXISTING_BASE_ROW_COUNT
    assert _target_rows(prefix) == []
    assert _prefix_fingerprint(prefix) == EXISTING_ROWS_SHA256


def test_nsrc_000002_historical_base_seed_cohort_is_append_safe():
    assert _violations(_rows()) == []


def test_nsrc_000002_accounting_allows_later_appended_rows():
    rows = copy.deepcopy(_rows())
    rows.append({"name_jp": "後続追加神社", "address": "架空県架空市1-1"})
    rows.append({"name_jp": "後続追加神社二", "address": "架空県架空市2-2"})
    assert _violations(rows) == []


def _remove_nsrc_000002_row(rows: list[dict]) -> None:
    del rows[NSRC_000002_EXISTING_BASE_ROW_COUNT]


def _change_nsrc_000002_identity(rows: list[dict]) -> None:
    rows[NSRC_000002_EXISTING_BASE_ROW_COUNT]["address"] = "新潟県糸魚川市大字青海9999番地"


def _replace_historical_row(rows: list[dict]) -> None:
    rows[NSRC_000002_EXISTING_BASE_ROW_COUNT] = {
        "name_jp": "後続追加神社",
        "address": "架空県架空市1-1",
    }


def _move_historical_row_to_end(rows: list[dict]) -> None:
    rows.append({"name_jp": "後続追加神社", "address": "架空県架空市1-1"})
    rows.append(rows.pop(NSRC_000002_EXISTING_BASE_ROW_COUNT))


def _remove_earlier_prefix_row(rows: list[dict]) -> None:
    del rows[0]


def _mutate_historical_prefix_row(rows: list[dict]) -> None:
    rows[0]["goriyaku"] = str(rows[0].get("goriyaku", "")) + "（変更）"


def _duplicate_nsrc_000002_later(rows: list[dict]) -> None:
    rows.append(copy.deepcopy(rows[NSRC_000002_EXISTING_BASE_ROW_COUNT]))


@pytest.mark.parametrize(
    ("mutate", "expected_violation"),
    [
        (_remove_nsrc_000002_row, "is not the nsrc-000002 row"),
        (_change_nsrc_000002_identity, "nsrc-000002 identity occurs 0 times"),
        (_replace_historical_row, "is not the nsrc-000002 row"),
        (_move_historical_row_to_end, "is not the nsrc-000002 row"),
        (_remove_earlier_prefix_row, "historical prefix fingerprint mismatch"),
        (_mutate_historical_prefix_row, "historical prefix fingerprint mismatch"),
        (_duplicate_nsrc_000002_later, "nsrc-000002 identity occurs 2 times"),
    ],
    ids=[
        "remove-nsrc-000002",
        "change-nsrc-000002-identity",
        "replace-historical-row",
        "move-historical-row",
        "remove-earlier-prefix-row",
        "mutate-historical-prefix-row",
        "duplicate-nsrc-000002-later",
    ],
)
def test_nsrc_000002_accounting_rejects_mutations(mutate, expected_violation):
    rows = copy.deepcopy(_rows())
    mutate(rows)
    violations = _violations(rows)
    assert any(expected_violation in violation for violation in violations), violations


def test_base_seed_has_no_duplicate_identity():
    identities = Counter((row.get("name_jp"), row.get("address")) for row in _rows())
    duplicates = {identity: count for identity, count in identities.items() if count > 1}
    assert duplicates == {}
