"""NIIGATA-001-VPG001 4件の Base Shrine materialization regression。

Authority:
- docs/audit/niigata-vpg001-g1-identity-duplicate.md（G1 canonical identity）
- docs/audit/niigata-vpg001-g2-position-review.md（G2 CLOSED / PASS, FROZEN）
- docs/audit/niigata-vpg001-g3-source-knowledge-fit.md
- docs/audit/niigata-vpg001-base-shrine-materialization.md

対象は nsrc-000021 / 000022 / 000024 / 000025 のみ。
nsrc-000023（G3 RESEARCH_REQUIRED_BEFORE_RELEASE）は materialize しない。
Knowledge / goriyaku / Recommendation はこのPRでは扱わない。
同名神社が Frozen Ready Set に複数あるため、exact (name_jp, address) でのみ解決する。
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
from temples.services.knowledge_seed import resolve_shrine

BASE_SEED_PATH = Path(__file__).resolve().parents[1] / "data" / "shrines_seed_clean.json"

# candidate_id -> (name_jp, canonical address, adopted latitude, adopted longitude)
TARGETS = {
    "nsrc-000021": ("荒川神社", "新潟県胎内市桃崎浜187番地", 38.1409456, 139.4073314),
    "nsrc-000022": ("五十嵐神社", "新潟県三条市大字飯田2283番地", 37.573979, 139.048758),
    "nsrc-000024": ("秋葉神社", "新潟県新潟市秋葉区秋葉3丁目8番19号", 37.7863255, 139.1351949),
    "nsrc-000025": ("天津神社", "新潟県糸魚川市一の宮1丁目3番34号", 37.0397729, 137.8644153),
}
# nsrc-000023, G3 RESEARCH_REQUIRED_BEFORE_RELEASE
EXCLUDED_IDENTITY = ("熱串彦神社", "新潟県佐渡市長江854番地")
# 同名・別住所（Frozen Ready Set の別 Source row）と、同一境内の別 Fact owner。
OTHER_IDENTITIES = [
    ("荒川神社", "新潟県新発田市荒川5431番地"),
    ("荒川神社", "新潟県村上市小岩内463番地"),
    ("荒川神社", "新潟県村上市荒川542番地"),
    ("秋葉神社", "新潟県新潟市中央区古町通11番町1688番地"),
    ("天津神社", "新潟県上越市大字東京田34番地1"),
    ("奴奈川神社", "新潟県糸魚川市一の宮1丁目3番34号"),
]


def _expected_row(name: str, address: str, lat: float, lng: float) -> dict:
    return {
        "name_jp": name,
        "address": address,
        "latitude": lat,
        "longitude": lng,
        "goriyaku": "",
        "kyusei": None,
        "astro_elements": [],
        "location": {"lat": lat, "lng": lng},
    }


EXPECTED_ROWS = [_expected_row(*TARGETS[cid]) for cid in sorted(TARGETS)]

# develop before this materialization has 129 rows.
EXISTING_BASE_ROW_COUNT = 129
TARGET_ROW_END = 133
# sha256 of json.dumps(rows[:129], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
# on develop@4e476076（materialization 前）。
EXISTING_PREFIX_SHA256 = "5932f7a8afcf608c8591c826bef5f2b0310861be496147c869d221575655685d"


def _rows() -> list[dict]:
    return json.loads(BASE_SEED_PATH.read_text(encoding="utf-8"))


def _identity_rows(rows: list[dict], name: str, address: str) -> list[dict]:
    return [row for row in rows if row.get("name_jp") == name and row.get("address") == address]


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
        cid: Shrine.objects.get(name_jp=name, address=address)
        for cid, (name, address, _lat, _lng) in TARGETS.items()
    }


# --- Seed file -----------------------------------------------------------------------------------


@pytest.mark.parametrize("candidate_id", sorted(TARGETS))
def test_target_identity_occurs_exactly_once(candidate_id):
    name, address, _lat, _lng = TARGETS[candidate_id]
    assert len(_identity_rows(_rows(), name, address)) == 1


@pytest.mark.parametrize("candidate_id", sorted(TARGETS))
def test_target_row_is_exactly_the_frozen_values(candidate_id):
    name, address, lat, lng = TARGETS[candidate_id]
    assert _identity_rows(_rows(), name, address) == [_expected_row(name, address, lat, lng)]


@pytest.mark.parametrize("candidate_id", sorted(TARGETS))
def test_target_location_mirrors_latitude_longitude(candidate_id):
    name, address, _lat, _lng = TARGETS[candidate_id]
    row = _identity_rows(_rows(), name, address)[0]
    assert row["location"] == {"lat": row["latitude"], "lng": row["longitude"]}


@pytest.mark.parametrize("candidate_id", sorted(TARGETS))
def test_target_row_has_neutral_fields_only(candidate_id):
    name, address, _lat, _lng = TARGETS[candidate_id]
    row = _identity_rows(_rows(), name, address)[0]
    assert row["goriyaku"] == ""
    assert row["kyusei"] is None
    assert row["astro_elements"] == []
    for key in (
        "goriyaku_tags",
        "visit_style_tags",
        "history_theme",
        "deities",
        "histories",
        "sources",
        "element",
        "popular_score",
    ):
        assert key not in row
    assert set(row) == set(_expected_row(name, address, 0.0, 0.0))


def test_targets_are_appended_after_existing_129_rows_in_candidate_order():
    rows = _rows()
    assert len(rows) >= TARGET_ROW_END
    assert rows[EXISTING_BASE_ROW_COUNT:TARGET_ROW_END] == EXPECTED_ROWS


def test_existing_129_row_prefix_is_unchanged():
    prefix = _rows()[:EXISTING_BASE_ROW_COUNT]
    digest = hashlib.sha256(
        json.dumps(prefix, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert digest == EXISTING_PREFIX_SHA256


def test_accounting_allows_later_appends_but_targets_stay_once():
    rows = copy.deepcopy(_rows())
    rows.append({"name_jp": "後続追加神社", "address": "架空県架空市1-1"})
    assert rows[EXISTING_BASE_ROW_COUNT:TARGET_ROW_END] == EXPECTED_ROWS
    for name, address, _lat, _lng in TARGETS.values():
        assert len(_identity_rows(rows, name, address)) == 1


def test_duplicate_target_append_is_detected():
    rows = copy.deepcopy(_rows())
    rows.append(copy.deepcopy(EXPECTED_ROWS[0]))
    identities = Counter((row.get("name_jp"), row.get("address")) for row in rows)
    duplicated = {identity for identity, n in identities.items() if n > 1}
    assert duplicated == {(EXPECTED_ROWS[0]["name_jp"], EXPECTED_ROWS[0]["address"])}


def test_nsrc_000023_is_not_materialized():
    name, address = EXCLUDED_IDENTITY
    assert not [row for row in _rows() if row.get("name_jp") == name]
    assert not [row for row in _rows() if row.get("address") == address]


def test_other_same_name_or_same_precinct_identities_are_not_materialized():
    rows = _rows()
    for name, address in OTHER_IDENTITIES:
        assert _identity_rows(rows, name, address) == [], (name, address)


def test_base_seed_has_no_duplicate_identity():
    identities = Counter((row.get("name_jp"), row.get("address")) for row in _rows())
    assert {identity: n for identity, n in identities.items() if n > 1} == {}


# --- isolated import rehearsal (disposable test DB) ----------------------------------------------


@pytest.mark.django_db
def test_base_seed_import_materializes_targets_and_is_idempotent():
    rows = _rows()
    first = _import_base_seed()
    assert f"created={len(rows)} updated=0 skipped=0 total_seed={len(rows)}" in first

    for cid, shrine in _targets().items():
        _name, _address, lat, lng = TARGETS[cid]
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
def test_imported_targets_carry_no_knowledge_or_inferred_data():
    _import_base_seed()
    for cid, shrine in _targets().items():
        assert not ShrineDeity.objects.filter(shrine=shrine).exists(), cid
        assert not ShrineHistory.objects.filter(shrine=shrine).exists(), cid
        assert (shrine.goriyaku or "") == ""
        assert (shrine.history_theme or "") == ""
        assert not shrine.goriyaku_tags.exists()
        assert shrine.visit_style_tags in (None, [])
    assert not Shrine.objects.filter(name_jp=EXCLUDED_IDENTITY[0]).exists()


# --- exact identity / same-name isolation --------------------------------------------------------


@pytest.mark.django_db
def test_each_target_resolves_to_its_own_row():
    _import_base_seed()
    targets = _targets()
    assert len({shrine.pk for shrine in targets.values()}) == len(TARGETS)
    for cid, shrine in targets.items():
        name, address, _lat, _lng = TARGETS[cid]
        result = resolve_shrine(name, address)
        assert result.status == "OK", cid
        assert result.shrine is not None and result.shrine.pk == shrine.pk, cid


@pytest.mark.django_db
def test_same_name_other_addresses_and_shared_precinct_never_resolve_to_a_target():
    _import_base_seed()
    for name, address in [*OTHER_IDENTITIES, EXCLUDED_IDENTITY]:
        result = resolve_shrine(name, address)
        assert result.status == "NOT_FOUND", (name, address)
        assert result.shrine is None
