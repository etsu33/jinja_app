"""Regression: `resolve_shrine()` must never accept a different-address Shrine
when the seed `shrine_ref` supplies an address.

Found during the nsrc-000007 G4 preflight: H002 tracks several distinct real-world
Shrines named `赤城社`. Before this fix, an exact-address miss fell back to the
name-only candidate set, so a single same-name Shrine at another address resolved
as `OK`.

Contract（address non-empty）:
  exact-address matches = 0 -> NOT_FOUND
  exact-address matches = 1 -> OK
  exact-address matches > 1 -> place_ref_id IS NULL preference inside that set only
                               (0091 remediation) -> OK_CANONICAL_PREFERRED / AMBIGUOUS
Address empty: unchanged name-only / canonical-preference behavior.
"""

from __future__ import annotations

import io
import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from temples.models import (
    PlaceRef,
    Shrine,
    ShrineDeity,
    ShrineHistory,
    ShrineKnowledgeSource,
)
from temples.services.knowledge_seed import resolve_shrine

pytestmark = pytest.mark.django_db

NAME = "赤城社"
ADDRESS_A = "新潟県十日町市四日町2534番地"
ADDRESS_B = "新潟県十日町市上組2059番地子"
ADDRESS_C = "新潟県十日町市伊達乙48番地"


def _shrine(
    name_jp: str,
    address: str,
    place_ref: PlaceRef | None = None,
    latitude: float | None = None,
) -> Shrine:
    # Same name + same address rows need a location (uq_shrine_name_addr_when_loc_null).
    coords = {} if latitude is None else {"latitude": latitude, "longitude": 138.0}
    return Shrine.objects.create(
        name_jp=name_jp, kind="shrine", address=address, place_ref=place_ref, **coords
    )


def _place_ref(suffix: str) -> PlaceRef:
    return PlaceRef.objects.create(place_id=f"dummy-place-{suffix}", name=NAME)


# --- address supplied --------------------------------------------------------------------------


def test_exact_name_and_exact_address_is_ok():
    target = _shrine(NAME, ADDRESS_A)
    _shrine(NAME, ADDRESS_B)
    result = resolve_shrine(NAME, ADDRESS_A)
    assert result.status == "OK"
    assert result.shrine == target


def test_single_same_name_shrine_with_different_address_is_not_found():
    _shrine(NAME, ADDRESS_B)
    result = resolve_shrine(NAME, ADDRESS_A)
    assert result.status == "NOT_FOUND"
    assert result.shrine is None


def test_single_same_name_canonical_row_with_different_address_is_not_found():
    # place_ref_id IS NULL preference must not rescue an address miss either.
    _shrine(NAME, ADDRESS_B)
    _shrine(NAME, ADDRESS_C, place_ref=_place_ref("c"))
    result = resolve_shrine(NAME, ADDRESS_A)
    assert result.status == "NOT_FOUND"
    assert result.shrine is None


def test_multiple_same_name_shrines_without_exact_address_is_not_found():
    _shrine(NAME, ADDRESS_B)
    _shrine(NAME, ADDRESS_C)
    result = resolve_shrine(NAME, ADDRESS_A)
    assert result.status == "NOT_FOUND"
    assert result.shrine is None


def test_same_name_same_address_duplicates_prefer_unique_canonical():
    """0091 remediation: canonical row + place-resolved duplicate sharing name and address."""
    canonical = _shrine(NAME, ADDRESS_A)
    _shrine(NAME, ADDRESS_A, place_ref=_place_ref("dup"))
    _shrine(NAME, ADDRESS_B)  # other-address canonical row must not compete
    result = resolve_shrine(NAME, ADDRESS_A)
    assert result.status == "OK_CANONICAL_PREFERRED"
    assert result.shrine == canonical


def test_same_name_same_address_duplicates_without_unique_canonical_is_ambiguous():
    _shrine(NAME, ADDRESS_A, latitude=37.1)
    _shrine(NAME, ADDRESS_A, latitude=37.2)
    result = resolve_shrine(NAME, ADDRESS_A)
    assert result.status == "AMBIGUOUS"
    assert result.shrine is None


def test_same_address_duplicates_all_place_resolved_is_ambiguous():
    _shrine(NAME, ADDRESS_A, place_ref=_place_ref("1"))
    _shrine(NAME, ADDRESS_A, place_ref=_place_ref("2"))
    _shrine(NAME, ADDRESS_B)  # unique canonical exists only at another address
    result = resolve_shrine(NAME, ADDRESS_A)
    assert result.status == "AMBIGUOUS"
    assert result.shrine is None


def test_address_is_compared_exactly_without_normalization():
    _shrine(NAME, ADDRESS_A)
    for variant in ("十日町市四日町2534番地", ADDRESS_A + " ", "新潟県十日町市四日町２５３４番地"):
        assert resolve_shrine(NAME, variant).status == "NOT_FOUND", variant


# --- address empty: unchanged ------------------------------------------------------------------


def test_empty_address_single_name_match_is_ok():
    target = _shrine(NAME, ADDRESS_B)
    result = resolve_shrine(NAME, "")
    assert result.status == "OK"
    assert result.shrine == target


def test_empty_address_prefers_unique_canonical_across_addresses():
    canonical = _shrine(NAME, ADDRESS_A)
    _shrine(NAME, ADDRESS_B, place_ref=_place_ref("b"))
    result = resolve_shrine(NAME, "")
    assert result.status == "OK_CANONICAL_PREFERRED"
    assert result.shrine == canonical


def test_empty_address_multiple_canonical_is_ambiguous():
    _shrine(NAME, ADDRESS_A)
    _shrine(NAME, ADDRESS_B)
    result = resolve_shrine(NAME, "")
    assert result.status == "AMBIGUOUS"


def test_empty_address_no_name_match_is_not_found():
    assert resolve_shrine(NAME, "").status == "NOT_FOUND"


# --- importer fails closed ---------------------------------------------------------------------


def _seed(address: str) -> dict:
    return {
        "schema_version": "1.0",
        "sources": [
            {
                "key": "src-1",
                "source_type": "government",
                "title": "テスト資料",
                "url": "https://example.jp/akagi",
                "verification_status": "source_confirmed",
                "verified_at": "2026-01-01T00:00:00Z",
                "confidence": "high",
            }
        ],
        "shrines": [
            {
                "shrine_ref": {"name_jp": NAME, "address": address},
                "deities": [],
                "histories": [
                    {
                        "history_type": "historical_event",
                        "title": "テスト履歴",
                        "content": "テスト内容。",
                        "verification_status": "source_confirmed",
                        "verified_at": "2026-01-01T00:00:00Z",
                        "confidence": "high",
                        "source_keys": ["src-1"],
                    }
                ],
            }
        ],
    }


def _counts() -> tuple[int, int, int]:
    return (
        ShrineKnowledgeSource.objects.count(),
        ShrineDeity.objects.count(),
        ShrineHistory.objects.count(),
    )


@pytest.mark.parametrize("mode", ["--validate-only", "--dry-run", None])
def test_importer_fails_closed_on_wrong_address_with_single_same_name_shrine(tmp_path, mode):
    other = _shrine(NAME, ADDRESS_B)
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(_seed(ADDRESS_A), ensure_ascii=False), encoding="utf-8")
    err = io.StringIO()
    args = [str(seed_path)] + ([mode] if mode else [])

    with pytest.raises(CommandError):
        call_command("import_shrine_knowledge", *args, stdout=io.StringIO(), stderr=err)

    assert "NOT_FOUND" in err.getvalue()
    assert _counts() == (0, 0, 0)
    assert not other.histories.exists()


def test_importer_validate_only_passes_on_exact_address(tmp_path):
    _shrine(NAME, ADDRESS_B)
    _shrine(NAME, ADDRESS_A)
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(_seed(ADDRESS_A), ensure_ascii=False), encoding="utf-8")
    out = io.StringIO()
    call_command("import_shrine_knowledge", str(seed_path), "--validate-only", stdout=out)
    assert "validate-only: OK" in out.getvalue()
