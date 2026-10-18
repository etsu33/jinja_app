"""NIIGATA-001-H003 C5 Catalog Runtime QA（disposable test DB only）。

C4 PASS の4件（nsrc-000011 / 000012 / 000013 / 000015）は Base Seed に frozen identity と
adopted coordinate だけで materialize 済み。Base Seed を test DB に import し、exact
(name_jp, address) で解決した行に対して実際の runtime path を検証する。

- Shrine Detail / List API（ShrineViewSet）は Catalog-only Shrine を表示できる。
- Concierge / Compass は Shared Recommendation Eligibility（usable Deity / History Fact >= 1）の
  fail-closed path で4件を除外する。PRODUCT_SURFACE（audit-level）には依存しない。
- 4件には Deity / History / goriyaku / history_theme を作らない。Recommendation path が実際に
  候補を返すことは、別の対照 Shrine（usable History Fact 付き、H003 ではない）で確認する。
- nsrc-000014（G2 HOLD_POSITION_REVIEW）は materialize しない。

Production には接続しない。
"""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from temples.models import Shrine, ShrineDeity, ShrineHistory
from temples.services.compass_direction_only_core import (
    STATE_RECOMMENDATION_ELIGIBILITY_ZERO_CANDIDATES as DIRECTION_ONLY_ELIGIBILITY_ZERO,
)
from temples.services.compass_direction_only_core import get_compass_direction_only_candidates
from temples.services.compass_recommendation_orchestrator import get_compass_recommendations
from temples.services.concierge_chat_candidates import (
    build_chat_candidates,
    build_chat_candidates_with_eligibility,
)
from temples.services.recommendation_eligibility_verifier import (
    INELIGIBLE,
    verify_recommendation_eligibility,
)
from temples.tests.support.recommendation_eligibility import attach_usable_history_fact

REPO_ROOT = Path(__file__).resolve().parents[3]
QA_SCRIPT = REPO_ROOT / "scripts" / "migration_safety" / "niigata_h003_c5_catalog_runtime_qa.py"
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
CONTROL_NAME = "C5対照神社"


def _qa_module():
    spec = importlib.util.spec_from_file_location("niigata_h003_c5_catalog_runtime_qa", QA_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_targets() -> dict[str, Shrine]:
    """Base Seed 由来の Catalog-only rows を exact identity で取得する（Knowledge / goriyaku なし）。"""
    targets = {}
    for candidate_id, (address, lat, lng) in TARGETS.items():
        shrine = Shrine.objects.get(name_jp=SHRINE_NAME, address=address)
        assert (shrine.latitude, shrine.longitude) == (lat, lng), candidate_id
        targets[candidate_id] = shrine
    return targets


def _base_state() -> dict[str, Shrine]:
    # Base Seed（4 target + 群馬県の別の赤城神社を含む）を入れ、名前だけで解決しないことも確認する。
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    return _resolve_targets()


def _control_near(lat: float, lng: float) -> Shrine:
    """Eligible な対照 Shrine（H003 ではない）。target と同じ方位 sector の少し手前に置く。"""
    control = Shrine.objects.create(
        name_jp=CONTROL_NAME,
        kind="shrine",
        address=f"架空県C5対照{lat:.4f}",
        latitude=lat - 0.009,
        longitude=lng,
    )
    attach_usable_history_fact(control)
    return control


def _ids(rows) -> set:
    return {row.get("shrine_id") or row.get("id") for row in rows if isinstance(row, dict)}


@pytest.mark.django_db
def test_catalog_only_rows_carry_no_recommendation_knowledge():
    targets = _base_state()
    for candidate_id, shrine in targets.items():
        assert not ShrineDeity.objects.filter(shrine=shrine).exists(), candidate_id
        assert not ShrineHistory.objects.filter(shrine=shrine).exists(), candidate_id
        assert (shrine.goriyaku or "") == ""
        assert (shrine.history_theme or "") == ""
        assert not shrine.goriyaku_tags.exists()
    assert not Shrine.objects.filter(address=EXCLUDED_ADDRESS).exists()
    # 同名の既存 Base Seed 赤城神社（別 Shrine）は target ではない。
    assert Shrine.objects.filter(name_jp=SHRINE_NAME).count() == len(TARGETS) + 1


@pytest.mark.django_db
def test_detail_and_list_expose_catalog_identity_and_adopted_coordinate():
    targets = _base_state()
    client = APIClient()
    listing = client.get("/api/shrines/", {"name": SHRINE_NAME, "page_size": 100})
    assert listing.status_code == 200
    body = listing.json()
    rows = body.get("results", body) if isinstance(body, dict) else body
    listed = {row["id"]: row for row in rows}

    for candidate_id, shrine in targets.items():
        address, lat, lng = TARGETS[candidate_id]
        detail = client.get(f"/api/shrines/{shrine.pk}/")
        assert detail.status_code == 200, candidate_id
        data = detail.json()
        assert (data["name_jp"], data["address"]) == (SHRINE_NAME, address)
        assert data["deities"] == [] and data["histories"] == []
        assert float(data["latitude"]) == pytest.approx(lat, abs=1e-6)
        assert float(data["longitude"]) == pytest.approx(lng, abs=1e-6)

        assert shrine.pk in listed, candidate_id
        assert (listed[shrine.pk]["name_jp"], listed[shrine.pk]["address"]) == (
            SHRINE_NAME,
            address,
        )
        assert float(listed[shrine.pk]["latitude"]) == pytest.approx(lat, abs=1e-6)
        assert float(listed[shrine.pk]["longitude"]) == pytest.approx(lng, abs=1e-6)


@pytest.mark.django_db
def test_shared_eligibility_verifier_reports_ineligible():
    targets = _base_state()
    report = verify_recommendation_eligibility(shrine_ids=[s.pk for s in targets.values()])
    statuses = {row.shrine_id: row.status for row in report.results}
    assert statuses == {s.pk: INELIGIBLE for s in targets.values()}


@pytest.mark.django_db
def test_concierge_excludes_catalog_only_while_control_participates():
    targets = _base_state()
    for candidate_id, shrine in targets.items():
        _, lat, lng = TARGETS[candidate_id]
        control = _control_near(lat, lng)
        result = build_chat_candidates_with_eligibility(
            lat=lat, lng=lng, apply_popularity_pool_limit=False
        )
        ids = _ids(result.candidates)
        assert shrine.pk not in ids, candidate_id
        assert control.pk in ids, candidate_id  # the path is live and returns eligible shrines
        assert result.ineligible_count >= 1
        assert shrine.pk not in _ids(build_chat_candidates(lat=lat, lng=lng))


@pytest.mark.django_db
def test_concierge_view_does_not_readmit_request_carried_catalog_candidates():
    targets = _base_state()
    shrine = targets["nsrc-000011"]
    _, lat, lng = TARGETS["nsrc-000011"]
    control = _control_near(lat, lng)

    from temples.api_views_concierge import _build_chat_candidates_pipeline

    class _Request:
        data = {"candidates": [{"shrine_id": shrine.pk, "id": shrine.pk, "name": SHRINE_NAME}]}
        _concierge_trace_id = "h003-c5"

    candidates, user_count, _built, _merged = _build_chat_candidates_pipeline(
        _Request(), lat, lng, None, "ja"
    )
    assert user_count == 1
    ids = _ids(candidates)
    assert shrine.pk not in ids
    assert control.pk in ids


@pytest.mark.django_db
def test_compass_excludes_catalog_only_on_both_paths():
    qa = _qa_module()
    targets = _base_state()
    for candidate_id, shrine in targets.items():
        _, lat, lng = TARGETS[candidate_id]
        origin = qa._origin_for(lat, lng)
        context = qa._direction_context(origin, lat, lng)

        # Catalog-only target alone in range: both paths report eligibility-zero, never the target.
        legacy = get_compass_recommendations(
            purpose="protection", origin=origin, direction_context=context
        )
        direction_only = get_compass_direction_only_candidates(
            origin=origin, direction_context=context
        )
        assert shrine.pk not in _ids(legacy.recommendations), candidate_id
        assert shrine.pk not in _ids(direction_only.candidates), candidate_id
        assert direction_only.state == DIRECTION_ONLY_ELIGIBILITY_ZERO, candidate_id
        assert direction_only.source_candidate_count >= 1

        # With an eligible control in the same sector the paths return results, still without the target.
        control = _control_near(lat, lng)
        legacy = get_compass_recommendations(
            purpose="protection", origin=origin, direction_context=context
        )
        direction_only = get_compass_direction_only_candidates(
            origin=origin, direction_context=context
        )
        assert shrine.pk not in _ids(legacy.recommendations), candidate_id
        assert shrine.pk not in _ids(direction_only.candidates), candidate_id
        assert control.pk in _ids(direction_only.candidates), candidate_id
        control.delete()


@pytest.mark.django_db(transaction=True)
def test_c5_runtime_qa_script_passes_read_only(capsys):
    targets = _base_state()
    qa = _qa_module()
    before = (
        Shrine.objects.count(),
        ShrineDeity.objects.count(),
        ShrineHistory.objects.count(),
    )
    capsys.readouterr()
    rows = qa.main()
    out = capsys.readouterr().out
    assert (
        Shrine.objects.count(),
        ShrineDeity.objects.count(),
        ShrineHistory.objects.count(),
    ) == before
    assert [row["candidate"] for row in rows] == list(TARGETS)
    for row in rows:
        assert row["detail_identity"] == "PASS"
        assert row["list_api_presence"] == "PASS"
        assert row["adopted_coordinate"].startswith("PASS")
        assert row["concierge_participation"] == "NO"
        assert row["compass_participation"] == "NO"
        assert row["C5_STATUS"] == "PASS"
    for line in (
        "H003_C5_CATALOG_RUNTIME_QA=PASS",
        "TRANSACTION_MODE=READ_ONLY",
    ):
        assert line in out
    assert set(targets) == set(TARGETS)


@pytest.mark.django_db(transaction=True)
def test_c5_runtime_qa_script_fails_closed_when_a_target_becomes_eligible():
    """Mutation sanity: if a Catalog-only target ever had usable Knowledge, the QA must FAIL."""
    targets = _base_state()
    attach_usable_history_fact(targets["nsrc-000012"])
    with pytest.raises(AssertionError):
        _qa_module().main()


@pytest.mark.django_db(transaction=True)
def test_c5_runtime_qa_script_fails_closed_on_coordinate_drift():
    targets = _base_state()
    Shrine.objects.filter(pk=targets["nsrc-000013"].pk).update(latitude=37.4970)
    with pytest.raises(AssertionError):
        _qa_module().main()
