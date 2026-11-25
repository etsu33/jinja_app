"""W0-DB01 eligibility 結果の再現テスト。

`docs/audit/shrine-expansion-wave0-db01-core-ready-gate.md` §9.1 は、W0-DB01の
5社について手動実行で per-shrine `ELIGIBLE` を確認し
`W0_DB01_SHARED_RECOMMENDATION_ELIGIBILITY_GATE = PASS` と記録した。同Auditは
「再利用可能な automated read-only verifier はまだ存在しない」とも記録している。

本テストは、Productionへ投入したものと**同一のseed成果物**

    backend/temples/data/shrines_seed_clean.json          （Base Shrine）
    backend/temples/data/knowledge_seeds/wave0_batch_01_seed.json （Knowledge）

からローカルへ同じ状態を組み立て、verifierが同じ結論（5社すべてELIGIBLE）へ
到達することを固定する。

注意: 本テストはProduction DBへ接続しない。Production実測値そのものの再現では
なく、**同一seedからverifierが同一結論へ到達すること**の再現である。
"""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.utils.dateparse import parse_datetime

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.recommendation_eligibility_verifier import (
    ELIGIBLE,
    count_batch_candidates,
    load_batch_shrine_identities,
    verify_recommendation_eligibility,
)

pytestmark = pytest.mark.django_db

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
BASE_SEED = DATA_DIR / "shrines_seed_clean.json"
KNOWLEDGE_SEED = DATA_DIR / "knowledge_seeds" / "wave0_batch_01_seed.json"

W0_DB01_EXPECTED_NAMES = {
    "三輪神社",
    "大鳥大社",
    "御岩神社",
    "烏森神社",
    "榴岡天満宮",
}


def _load_base_shrines(names: set[str]) -> dict[str, Shrine]:
    """Base Shrine seedから対象Shrineだけを作る（同一seed成果物を使用）。"""
    payload = json.loads(BASE_SEED.read_text(encoding="utf-8"))
    rows = payload.get("shrines") if isinstance(payload, dict) else payload

    created: dict[str, Shrine] = {}
    for row in rows:
        name = row.get("name_jp")
        if name not in names or name in created:
            continue
        created[name] = Shrine.objects.create(
            name_jp=name,
            address=row.get("address") or "",
            latitude=row.get("latitude"),
            longitude=row.get("longitude"),
        )
    return created


def _load_wave0_batch01_knowledge(shrines_by_name: dict[str, Shrine]) -> None:
    """W0-DB01 Knowledge seedをそのままローカルへ組み立てる。"""
    payload = json.loads(KNOWLEDGE_SEED.read_text(encoding="utf-8"))

    sources: dict[str, ShrineKnowledgeSource] = {}
    for entry in payload["sources"]:
        sources[entry["key"]] = ShrineKnowledgeSource.objects.create(
            source_type=entry["source_type"],
            title=entry["title"],
            publisher=entry.get("publisher") or "",
            url=entry.get("url") or "",
            verification_status=entry["verification_status"],
            verified_at=parse_datetime(entry["verified_at"]) if entry.get("verified_at") else None,
        )

    for shrine_entry in payload["shrines"]:
        name = shrine_entry["shrine_ref"]["name_jp"]
        shrine = shrines_by_name.get(name)
        if shrine is None:
            continue

        for deity_entry in shrine_entry.get("deities", []):
            deity = ShrineDeity.objects.create(
                shrine=shrine,
                display_name=deity_entry["display_name"],
                sort_order=deity_entry.get("sort_order", 0),
                verification_status=deity_entry["verification_status"],
                confidence=deity_entry.get("confidence") or "",
                verified_at=(
                    parse_datetime(deity_entry["verified_at"])
                    if deity_entry.get("verified_at")
                    else None
                ),
            )
            for key in deity_entry.get("source_keys", []):
                if key in sources:
                    deity.sources.add(sources[key])

        for history_entry in shrine_entry.get("histories", []):
            history = ShrineHistory.objects.create(
                shrine=shrine,
                history_type=history_entry["history_type"],
                title=history_entry["title"],
                content=history_entry["content"],
                sort_order=history_entry.get("sort_order", 0),
                verification_status=history_entry["verification_status"],
                confidence=history_entry.get("confidence") or "",
                verified_at=(
                    parse_datetime(history_entry["verified_at"])
                    if history_entry.get("verified_at")
                    else None
                ),
            )
            for key in history_entry.get("source_keys", []):
                if key in sources:
                    history.sources.add(sources[key])


@pytest.fixture
def w0_db01_state() -> dict[str, Shrine]:
    shrines = _load_base_shrines(W0_DB01_EXPECTED_NAMES)
    assert set(shrines) == W0_DB01_EXPECTED_NAMES, (
        f"base seedからW0-DB01の5社を構成できなかった: {sorted(shrines)}"
    )
    _load_wave0_batch01_knowledge(shrines)
    return shrines


def test_candidate_master_resolves_w0_db01_to_the_five_known_shrines():
    identities = load_batch_shrine_identities("W0-DB01")

    assert count_batch_candidates("W0-DB01") == 5
    assert len(identities) == 5
    assert {i.name for i in identities} == W0_DB01_EXPECTED_NAMES
    # canonical identityはaddressを必ず持つ（name-onlyへ退化しない）
    assert all(i.address.strip() for i in identities)


def test_candidate_master_addresses_match_the_base_seed(w0_db01_state):
    """Candidate Masterのofficial_addressがProduction Shrineのaddressと一致する。

    一致しなければ --batch は解決できない。identity契約の前提を固定する。
    """
    for identity in load_batch_shrine_identities("W0-DB01"):
        shrine = w0_db01_state[identity.name]
        assert shrine.address == identity.address


def test_w0_db01_five_shrines_are_all_eligible(w0_db01_state):
    """W0-DB01 CORE READY Gate §9.1 の結論を再現する。"""
    report = verify_recommendation_eligibility(
        shrine_identities=load_batch_shrine_identities("W0-DB01"),
    )

    assert report.summary_counts() == (5, 0, 0)
    assert report.all_eligible is True
    for result in report.results:
        assert result.status == ELIGIBLE, f"{result.requested} -> {result.status}"
        assert result.usable_fact_count >= 1


def test_w0_db01_batch_command_reports_all_eligible(w0_db01_state):
    out = StringIO()
    call_command(
        "verify_recommendation_eligibility",
        "--batch",
        "W0-DB01",
        "--json",
        "--require-all-eligible",
        stdout=out,
    )

    payload = json.loads(out.getvalue())
    assert payload["summary"]["requested_count"] == 5
    assert payload["summary"]["eligible_count"] == 5
    assert payload["summary"]["ineligible_count"] == 0
    assert payload["summary"]["unresolved_count"] == 0
    assert payload["summary"]["all_eligible"] is True
    assert {r["name_jp"] for r in payload["results"]} == W0_DB01_EXPECTED_NAMES


def test_w0_db01_shrines_without_knowledge_would_be_ineligible():
    """同じ5社でもKnowledge未投入ならINELIGIBLEになる（gateが実際に効いている）。"""
    _load_base_shrines(W0_DB01_EXPECTED_NAMES)

    report = verify_recommendation_eligibility(
        shrine_identities=load_batch_shrine_identities("W0-DB01"),
    )

    assert report.eligible_count == 0
    assert report.ineligible_count == 5
    assert report.all_eligible is False
