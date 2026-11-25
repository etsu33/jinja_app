#!/usr/bin/env python3
"""NIIGATA-001-H003 C5 Catalog Runtime QA.

Read-only verification of the Catalog-only runtime surfaces for the four H003
Candidates that passed C4（nsrc-000011 / 000012 / 000013 / 000015）against the
configured database. The entire verification runs inside a PostgreSQL READ ONLY
transaction, so any accidental write attempt fails closed.

Each target is resolved by its exact frozen (name_jp, address) identity. H003 has
five shrines named 赤城神社 and other 赤城神社 rows may exist; name-only matching is
never used. nsrc-000014 is G2 HOLD_POSITION_REVIEW and is not a target.

Checks per target（docs/knowledge/shrine-expansion-gate-contract.md §11A C5）:

    DETAIL_IDENTITY        Shrine Detail API returns the frozen identity
    LIST_API_PRESENCE      Shrine list API returns the row
    ADOPTED_COORDINATE     Detail / List return the adopted coordinate
    CONCIERGE_PARTICIPATION = NO   shared candidate path + request-carried path
    COMPASS_PARTICIPATION   = NO   legacy purpose path + Direction-only path

Recommendation non-participation is checked through the shared fail-closed
Recommendation Eligibility path（usable Deity Fact >= 1 OR usable History Fact >= 1）,
not inferred from the audit-level PRODUCT_SURFACE = CATALOG_ONLY. Product Surface is
not a runtime field.
"""

# Django must be configured before the temples imports below.
# ruff: noqa: E402

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shrine_project.settings")

import django

django.setup()

from django.db import connection, transaction
from rest_framework.test import APIRequestFactory
from temples.api.views.shrine import ShrineViewSet
from temples.models import Shrine, ShrineDeity, ShrineHistory
from temples.services.compass_direction_only_core import get_compass_direction_only_candidates
from temples.services.compass_recommendation_orchestrator import get_compass_recommendations
from temples.services.concierge_chat_candidates import (
    build_chat_candidates,
    filter_recommendation_eligible_candidates,
    is_recommendation_eligible,
    partition_recommendation_eligible_shrines,
)
from temples.services.direction_reference import _bearing, _direction_label
from temples.services.shrine_knowledge_selector import (
    fetch_fact_ready_knowledge_deities,
    fetch_fact_ready_knowledge_histories,
)

SHRINE_NAME = "赤城神社"
# candidate_id -> (canonical address, adopted latitude, adopted longitude)
# docs/audit/niigata-h003-c4-catalog-evidence.md / niigata-h003-position-hold-resolution.md
TARGETS = {
    "nsrc-000011": ("新潟県新潟市江南区二本木1丁目7番16号", 37.841794, 139.118507),
    "nsrc-000012": ("新潟県長岡市四郎丸2丁目5番33号", 37.440743, 138.855238),
    "nsrc-000013": ("新潟県長岡市山屋314番地", 37.496407, 139.008620),
    "nsrc-000015": ("新潟県魚沼市湯之谷芋川311番地", 37.214543, 139.036468),
}
# G2 HOLD_POSITION_REVIEW: not a C5 target, never materialized for C5.
EXCLUDED = {"nsrc-000014": "新潟県五泉市上杉川1310番地2"}
COORDINATE_TOLERANCE = 1e-6
# A point ~2 km due south of each target, so the target lies in the origin's 北 sector.
ORIGIN_SOUTH_OFFSET_DEG = 0.018
COMPASS_PURPOSE = "protection"


def _origin_for(lat: float, lng: float) -> dict:
    return {"lat": lat - ORIGIN_SOUTH_OFFSET_DEG, "lng": lng}


def _direction_context(origin: dict, lat: float, lng: float) -> dict:
    label = _direction_label(
        _bearing(from_lat=origin["lat"], from_lng=origin["lng"], to_lat=lat, to_lng=lng)
    )
    return {"referenceDirections": [label], "calculationMethod": "annual_monthly_kyusei_v1"}


def _ids(rows) -> set:
    return {row.get("shrine_id") or row.get("id") for row in rows if isinstance(row, dict)}


def check_target(candidate_id: str, factory: APIRequestFactory) -> dict:
    address, lat, lng = TARGETS[candidate_id]
    matches = list(Shrine.objects.filter(name_jp=SHRINE_NAME, address=address))
    assert len(matches) == 1, (candidate_id, len(matches))
    shrine = matches[0]

    # Catalog-only payload boundary: no Recommendation Knowledge, no legacy signals.
    assert not ShrineDeity.objects.filter(shrine=shrine).exists(), candidate_id
    assert not ShrineHistory.objects.filter(shrine=shrine).exists(), candidate_id
    assert (shrine.goriyaku or "") == "", candidate_id
    assert (getattr(shrine, "history_theme", "") or "") == "", candidate_id
    assert not shrine.goriyaku_tags.exists(), candidate_id

    # 1. Shrine Detail basic identity（real ShrineViewSet.retrieve）
    detail_view = ShrineViewSet.as_view({"get": "retrieve"})
    detail = detail_view(factory.get(f"/api/shrines/{shrine.pk}/"), pk=shrine.pk)
    assert detail.status_code == 200, (candidate_id, detail.status_code)
    body = detail.data
    assert body["id"] == shrine.pk
    assert body["name_jp"] == SHRINE_NAME
    assert body["address"] == address
    assert list(body["deities"]) == []
    assert list(body["histories"]) == []

    # 2. Shrine list API presence（real ShrineViewSet.list, exact name search）
    list_view = ShrineViewSet.as_view({"get": "list"})
    listing = list_view(factory.get("/api/shrines/", {"name": SHRINE_NAME, "page_size": 100}))
    assert listing.status_code == 200, (candidate_id, listing.status_code)
    results = (
        listing.data.get("results", listing.data) if hasattr(listing.data, "get") else listing.data
    )
    listed = [row for row in results if row["id"] == shrine.pk]
    assert len(listed) == 1, candidate_id
    assert listed[0]["name_jp"] == SHRINE_NAME
    assert listed[0]["address"] == address

    # 3. Map / navigation coordinate（the web Detail page builds directions from these）
    for payload in (body, listed[0]):
        assert abs(float(payload["latitude"]) - lat) < COORDINATE_TOLERANCE, candidate_id
        assert abs(float(payload["longitude"]) - lng) < COORDINATE_TOLERANCE, candidate_id

    # Shared Recommendation Eligibility（the single authority both surfaces use）
    deities = fetch_fact_ready_knowledge_deities([shrine.pk]).get(shrine.pk, [])
    histories = fetch_fact_ready_knowledge_histories([shrine.pk]).get(shrine.pk, [])
    assert deities == [] and histories == [], candidate_id
    assert (
        is_recommendation_eligible(knowledge_deities=deities, knowledge_histories=histories)
        is False
    )
    partition = partition_recommendation_eligible_shrines([shrine])
    assert partition.eligible == [] and partition.ineligible_count == 1, candidate_id

    # 4. Concierge participation = NO
    concierge = build_chat_candidates(lat=lat, lng=lng, trace_id=f"h003-c5-{candidate_id}")
    assert shrine.pk not in _ids(concierge), candidate_id
    # request-carried candidates go through the same shared gate in the Concierge view
    carried = filter_recommendation_eligible_candidates(
        [{"shrine_id": shrine.pk, "id": shrine.pk, "name": SHRINE_NAME}]
    )
    assert carried == [], candidate_id

    # 5. Compass participation = NO（target placed inside the queried direction sector）
    origin = _origin_for(lat, lng)
    context = _direction_context(origin, lat, lng)
    legacy = get_compass_recommendations(
        purpose=COMPASS_PURPOSE, origin=origin, direction_context=context
    )
    assert shrine.pk not in _ids(legacy.recommendations), candidate_id
    direction_only = get_compass_direction_only_candidates(origin=origin, direction_context=context)
    assert shrine.pk not in _ids(direction_only.candidates), candidate_id

    return {
        "candidate": candidate_id,
        "detail_identity": "PASS",
        "list_api_presence": "PASS",
        "adopted_coordinate": f"PASS ({lat:.6f}, {lng:.6f})",
        "concierge_participation": "NO",
        "compass_participation": "NO",
        "compass_legacy_state": legacy.state,
        "compass_direction_only_state": direction_only.state,
        "C5_STATUS": "PASS",
    }


def main() -> list[dict]:
    factory = APIRequestFactory()
    rows = []
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")

        for candidate_id, address in EXCLUDED.items():
            assert not Shrine.objects.filter(name_jp=SHRINE_NAME, address=address).exists(), (
                candidate_id
            )

        for candidate_id in TARGETS:
            row = check_target(candidate_id, factory)
            rows.append(row)
            print(" ".join(f"{key}={value}" for key, value in row.items()))

    print("H003_C5_TARGETS=" + ",".join(TARGETS))
    print("H003_C5_EXCLUDED=nsrc-000014(G2_HOLD_POSITION_REVIEW)")
    print("H003_C5_CATALOG_RUNTIME_QA=PASS")
    print("TRANSACTION_MODE=READ_ONLY")
    return rows


if __name__ == "__main__":
    main()
