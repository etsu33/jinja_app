"""NIIGATA-001-H003 Catalog-only 4件の Base Shrine materialization regression。

Authority:
- docs/audit/niigata-h003-c4-catalog-evidence.md
- docs/audit/niigata-h003-position-hold-resolution.md
- docs/audit/niigata-h003-c5-catalog-runtime-qa.md
- docs/audit/niigata-h003-catalog-base-shrine-materialization.md

対象は C4 / C5 PASS の nsrc-000011 / 000012 / 000013 / 000015 のみ。
nsrc-000014（G2 HOLD_POSITION_REVIEW）は materialize しない。
Knowledge / goriyaku / Recommendation はこのPRでは扱わない。
同名「赤城神社」が複数あるため、exact (name_jp, address) でのみ解決する。
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

from temples.models import Shrine, ShrineDeity, ShrineHistory
from temples.services.concierge_chat_candidates import partition_recommendation_eligible_shrines
from temples.services.knowledge_seed import resolve_shrine
from temples.services.recommendation_eligibility_verifier import (
    INELIGIBLE,
    UNRESOLVED,
    ShrineIdentity,
    verify_recommendation_eligibility,
)

BASE_SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "shrines_seed_clean.json"

SHRINE_NAME = "赤城神社"
# candidate_id -> (canonical address, adopted latitude, adopted longitude)
TARGETS = {
    "nsrc-000011": ("新潟県新潟市江南区二本木1丁目7番16号", 37.841794, 139.118507),
    "nsrc-000012": ("新潟県長岡市四郎丸2丁目5番33号", 37.440743, 138.855238),
    "nsrc-000013": ("新潟県長岡市山屋314番地", 37.496407, 139.008620),
    "nsrc-000015": ("新潟県魚沼市湯之谷芋川311番地", 37.214543, 139.036468),
}
EXCLUDED_ADDRESS = "新潟県五泉市上杉川1310番地2"  # nsrc-000014, G2 HOLD_POSITION_REVIEW
# 既存 Base Seed の別実体（H003 Candidate ではない）。
GUNMA_AKAGI_ADDRESS = "群馬県前橋市富士見町赤城山4-2"


def _expected_row(address: str, lat: float, lng: float) -> dict:
    return {
        "name_jp": SHRINE_NAME,
        "address": address,
        "latitude": lat,
        "longitude": lng,
        "goriyaku": "",
        "kyusei": None,
        "astro_elements": [],
        "location": {"lat": lat, "lng": lng},
    }


EXPECTED_ROWS = [_expected_row(*TARGETS[cid]) for cid in sorted(TARGETS)]

# develop before this materialization has 125 rows.
EXISTING_BASE_ROW_COUNT = 125
TARGET_ROW_END = 129
# sha256 of json.dumps(rows[:125], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
# on develop@c1806db（materialization 前）。
EXISTING_PREFIX_SHA256 = "1e79d9f992b76ae26c2b862094d4592d3e754a2917c7b239d0e567a56740307b"


def _rows() -> list[dict]:
    return json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))


def _identity_rows(rows: list[dict], address: str) -> list[dict]:
    return [
        row for row in rows if row.get("name_jp") == SHRINE_NAME and row.get("address") == address
    ]


def _import_base_seed(*extra: str) -> str:
    out = io.StringIO()
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        *extra,
        stdout=out,
        stderr=io.StringIO(),
    )
    return out.getvalue()


def _targets() -> dict[str, Shrine]:
    return {
        cid: Shrine.objects.get(name_jp=SHRINE_NAME, address=address)
        for cid, (address, _lat, _lng) in TARGETS.items()
    }


# --- Seed file -----------------------------------------------------------------------------------


@pytest.mark.parametrize("candidate_id", sorted(TARGETS))
def test_target_identity_occurs_exactly_once(candidate_id):
    address, _lat, _lng = TARGETS[candidate_id]
    assert len(_identity_rows(_rows(), address)) == 1


@pytest.mark.parametrize("candidate_id", sorted(TARGETS))
def test_target_row_is_exactly_the_frozen_values(candidate_id):
    address, lat, lng = TARGETS[candidate_id]
    assert _identity_rows(_rows(), address) == [_expected_row(address, lat, lng)]


@pytest.mark.parametrize("candidate_id", sorted(TARGETS))
def test_target_row_has_no_inferred_fields(candidate_id):
    row = _identity_rows(_rows(), TARGETS[candidate_id][0])[0]
    assert row["goriyaku"] == ""
    assert row["kyusei"] is None
    assert row["astro_elements"] == []
    for key in ("goriyaku_tags", "visit_style_tags", "history_theme"):
        assert key not in row


def test_targets_are_appended_after_existing_125_rows_in_candidate_order():
    rows = _rows()
    assert len(rows) >= TARGET_ROW_END
    assert rows[EXISTING_BASE_ROW_COUNT:TARGET_ROW_END] == EXPECTED_ROWS


def test_existing_125_row_prefix_is_unchanged():
    prefix = _rows()[:EXISTING_BASE_ROW_COUNT]
    digest = hashlib.sha256(
        json.dumps(prefix, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert digest == EXISTING_PREFIX_SHA256


def test_accounting_allows_later_appends_but_targets_stay_once():
    rows = copy.deepcopy(_rows())
    rows.append({"name_jp": "後続追加神社", "address": "架空県架空市1-1"})
    assert rows[EXISTING_BASE_ROW_COUNT:TARGET_ROW_END] == EXPECTED_ROWS
    for address, _lat, _lng in TARGETS.values():
        assert len(_identity_rows(rows, address)) == 1


def test_nsrc_000014_is_not_materialized():
    assert not [row for row in _rows() if row.get("address") == EXCLUDED_ADDRESS]


def test_base_seed_has_no_duplicate_identity():
    identities = Counter((row.get("name_jp"), row.get("address")) for row in _rows())
    assert {identity: n for identity, n in identities.items() if n > 1} == {}


def test_akagi_rows_are_distinct_exact_addresses():
    addresses = [row["address"] for row in _rows() if row.get("name_jp") == SHRINE_NAME]
    assert sorted(addresses) == sorted([GUNMA_AKAGI_ADDRESS, *(a for a, _, _ in TARGETS.values())])
    assert len(addresses) == len(set(addresses))


# --- isolated import rehearsal (disposable test DB) ----------------------------------------------


@pytest.mark.django_db
def test_base_seed_import_materializes_targets_and_is_idempotent():
    rows = _rows()
    first = _import_base_seed()
    assert f"created={len(rows)} updated=0 skipped=0 total_seed={len(rows)}" in first

    for cid, shrine in _targets().items():
        _address, lat, lng = TARGETS[cid]
        assert (shrine.latitude, shrine.longitude) == (lat, lng), cid
        assert shrine.kind == "shrine"

    before = sorted(Shrine.objects.values_list("pk", "name_jp", "address", "latitude", "longitude"))
    dry = _import_base_seed("--dry-run")
    assert f"created=0 updated=0 skipped={len(rows)} total_seed={len(rows)}" in dry
    second = _import_base_seed()
    assert f"created=0 updated=0 skipped={len(rows)} total_seed={len(rows)}" in second
    after = sorted(Shrine.objects.values_list("pk", "name_jp", "address", "latitude", "longitude"))
    assert after == before


@pytest.mark.django_db
def test_imported_targets_carry_no_recommendation_knowledge():
    _import_base_seed()
    for cid, shrine in _targets().items():
        assert not ShrineDeity.objects.filter(shrine=shrine).exists(), cid
        assert not ShrineHistory.objects.filter(shrine=shrine).exists(), cid
        assert (shrine.goriyaku or "") == ""
        assert (shrine.history_theme or "") == ""
        assert not shrine.goriyaku_tags.exists()
        assert shrine.visit_style_tags in (None, [])
    assert not Shrine.objects.filter(address=EXCLUDED_ADDRESS).exists()


# --- exact identity / same-name isolation --------------------------------------------------------


@pytest.mark.django_db
def test_each_target_resolves_to_its_own_row():
    _import_base_seed()
    targets = _targets()
    assert len({shrine.pk for shrine in targets.values()}) == len(TARGETS)
    for cid, shrine in targets.items():
        result = resolve_shrine(SHRINE_NAME, TARGETS[cid][0])
        assert result.status == "OK", cid
        assert result.shrine is not None and result.shrine.pk == shrine.pk, cid


@pytest.mark.django_db
def test_same_name_other_addresses_never_resolve_to_a_target():
    _import_base_seed()
    target_pks = {shrine.pk for shrine in _targets().values()}

    gunma = resolve_shrine(SHRINE_NAME, GUNMA_AKAGI_ADDRESS)
    assert gunma.status == "OK"
    assert gunma.shrine is not None and gunma.shrine.pk not in target_pks

    excluded = resolve_shrine(SHRINE_NAME, EXCLUDED_ADDRESS)
    assert excluded.status == "NOT_FOUND"
    assert excluded.shrine is None


# --- Recommendation eligibility stays fail-closed ------------------------------------------------


@pytest.mark.django_db
def test_catalog_only_targets_remain_recommendation_ineligible():
    _import_base_seed()
    report = verify_recommendation_eligibility(
        shrine_identities=[
            *(ShrineIdentity(SHRINE_NAME, address) for address, _, _ in TARGETS.values()),
            ShrineIdentity(SHRINE_NAME, EXCLUDED_ADDRESS),
        ]
    )
    assert [r.status for r in report.results] == [INELIGIBLE] * 4 + [UNRESOLVED]
    for result in report.results[:4]:
        assert result.shrine_id is not None
        assert result.usable_fact_count == 0
    assert report.summary_counts() == (0, 4, 1)

    partition = partition_recommendation_eligible_shrines(list(_targets().values()))
    assert partition.source_count == 4
    assert partition.eligible == []
    assert partition.ineligible_count == 4
