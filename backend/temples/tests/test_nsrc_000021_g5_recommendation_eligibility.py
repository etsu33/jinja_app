"""nsrc-000021 荒川神社 G5 Shared Recommendation Eligibility.

Authority:
- docs/knowledge/recommendation-eligibility-contract.md
- docs/audit/niigata-vpg001-nsrc-000021-g4-formal-pass.md
- docs/audit/niigata-vpg001-nsrc-000021-g5-recommendation-eligibility.md

G5 は shared Recommendation candidate set への参加可否だけを固定する。
Ranking / purpose match / goriyaku は判定に使わない。
"""

import io
from pathlib import Path

import pytest
from django.core.management import call_command

from temples.models import Shrine
from temples.services.concierge_chat_candidates import (
    filter_recommendation_eligible_candidates,
    partition_recommendation_eligible_shrines,
)
from temples.services.recommendation_eligibility_verifier import (
    ELIGIBLE,
    UNRESOLVED,
    ShrineIdentity,
    verify_recommendation_eligibility,
)

TEMPLES_DIR = Path(__file__).resolve().parents[1]
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"
KNOWLEDGE_SEED_DIR = TEMPLES_DIR / "data" / "knowledge_seeds"
KNOWLEDGE_SEED_PATH = KNOWLEDGE_SEED_DIR / "nsrc_000021_seed.json"
VPG001_KNOWLEDGE_SEED_PATHS = [
    KNOWLEDGE_SEED_DIR / f"nsrc_{cid}_seed.json" for cid in ("000021", "000022", "000024", "000025")
]

SHRINE_NAME = "荒川神社"
SHRINE_ADDRESS = "新潟県胎内市桃崎浜187番地"
# G1 で記録済みの同名・別住所 identity（Base Seed には materialize されていない）。
OTHER_SAME_NAME_ADDRESSES = (
    "新潟県新発田市荒川5431番地",
    "新潟県村上市小岩内463番地",
    "新潟県村上市荒川542番地",
)
EXPECTED_DEITIES = ["天鈿女命"]
EXPECTED_HISTORIES = [("regional_context", "船主による船絵馬の奉納")]


def _import_current_state(*knowledge_seed_paths: Path) -> None:
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    for path in knowledge_seed_paths or (KNOWLEDGE_SEED_PATH,):
        call_command(
            "import_shrine_knowledge",
            str(path),
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )


def _target() -> Shrine:
    return Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)


def _verify():
    return verify_recommendation_eligibility(
        shrine_identities=[ShrineIdentity(name=SHRINE_NAME, address=SHRINE_ADDRESS)]
    )


def _partition_entry():
    partition = partition_recommendation_eligible_shrines([_target()])
    assert partition.eligible_count == 1
    return partition.eligible[0]


@pytest.mark.django_db
def test_nsrc_000021_is_shared_recommendation_eligible():
    _import_current_state()

    shrine = _target()

    report = _verify()

    assert report.summary_counts() == (1, 0, 0)
    assert report.all_eligible is True
    [result] = report.results
    assert result.status == ELIGIBLE
    assert result.shrine_id == shrine.pk
    assert result.usable_deity_fact_count == 1
    assert result.usable_history_fact_count == 1
    assert result.usable_fact_count == 2

    partition = partition_recommendation_eligible_shrines([shrine])
    assert partition.source_count == 1
    assert partition.eligible_count == 1
    assert partition.ineligible_count == 0
    assert partition.eligible[0].shrine.pk == shrine.pk
    assert [d["display_name"] for d in partition.eligible[0].knowledge_deities] == EXPECTED_DEITIES
    assert [
        (h["history_type"], h["title"]) for h in partition.eligible[0].knowledge_histories
    ] == EXPECTED_HISTORIES

    candidate = {"id": shrine.pk, "shrine_id": shrine.pk, "name": shrine.name_jp}
    assert filter_recommendation_eligible_candidates([candidate]) == [candidate]


@pytest.mark.django_db
def test_goriyaku_absence_does_not_affect_eligibility():
    _import_current_state()
    shrine = _target()
    assert shrine.goriyaku in ("", None)
    assert shrine.goriyaku_tags.count() == 0
    assert (shrine.history_theme or "") == ""
    assert _verify().results[0].status == ELIGIBLE


@pytest.mark.django_db
def test_eligibility_is_unchanged_with_all_vpg001_seeds_imported():
    _import_current_state(*VPG001_KNOWLEDGE_SEED_PATHS)
    [result] = _verify().results
    assert result.status == ELIGIBLE
    assert (result.usable_deity_fact_count, result.usable_history_fact_count) == (1, 1)
    entry = _partition_entry()
    assert [d["display_name"] for d in entry.knowledge_deities] == EXPECTED_DEITIES
    assert [
        (h["history_type"], h["title"]) for h in entry.knowledge_histories
    ] == EXPECTED_HISTORIES


@pytest.mark.django_db
def test_other_same_name_identities_do_not_inherit_eligibility():
    _import_current_state()

    report = verify_recommendation_eligibility(
        shrine_identities=[
            ShrineIdentity(name=SHRINE_NAME, address=address)
            for address in OTHER_SAME_NAME_ADDRESSES
        ]
    )

    assert report.summary_counts() == (0, 0, len(OTHER_SAME_NAME_ADDRESSES))
    assert all(result.status == UNRESOLVED for result in report.results)
    assert all(result.shrine_id is None for result in report.results)


@pytest.mark.django_db
def test_chronology_conflict_is_not_part_of_the_eligible_knowledge():
    _import_current_state()
    entry = _partition_entry()
    text = repr(entry.knowledge_deities) + repr(entry.knowledge_histories)
    for needle in ("1814", "1841", "天保12"):
        assert needle not in text
