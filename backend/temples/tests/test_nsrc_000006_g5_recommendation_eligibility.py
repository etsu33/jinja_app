"""nsrc-000006 赤井神社（新潟県佐渡市加茂歌代2662番地）の G5 Shared Recommendation Eligibility。

authority:
docs/knowledge/recommendation-eligibility-contract.md

判定経路:
shrine_knowledge_selector
-> evidence_gate.decide_fact_usability()
-> is_recommendation_eligible()

新しい eligibility rule は作らない。
nsrc-000006 は usable Deity 0 / usable History 3。
goriyaku / goriyaku_tags の不在は G5 INELIGIBLE の理由ではない。

identity は exact (name_jp, address) だけで扱う。
researchで観測された noncanonical address は canonical target の eligibility を継承しない。
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
KNOWLEDGE_SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "nsrc_000006_seed.json"

SHRINE_NAME = "赤井神社"
SHRINE_ADDRESS = "新潟県佐渡市加茂歌代2662番地"
NON_CANONICAL_ADDRESSES = (
    "新潟県佐渡市加茂歌代2622番地",
    "新潟県佐渡市加茂歌代1164-7",
)
EXPECTED_HISTORIES = [
    ("regional_context", "4月16日の赤井神社例祭と鬼太鼓奉納"),
    ("tradition", "元日午前0時の鬼太鼓奉納"),
    ("regional_context", "加茂の五神社としての記録"),
]


def _import_current_seeds() -> None:
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    call_command(
        "import_shrine_knowledge",
        str(KNOWLEDGE_SEED_PATH),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )


@pytest.mark.django_db
def test_nsrc_000006_is_shared_recommendation_eligible_on_current_develop():
    _import_current_seeds()

    shrine = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)

    report = verify_recommendation_eligibility(
        shrine_identities=[ShrineIdentity(name=SHRINE_NAME, address=SHRINE_ADDRESS)]
    )

    assert report.summary_counts() == (1, 0, 0)
    assert report.all_eligible is True
    assert len(report.results) == 1

    result = report.results[0]
    assert result.status == ELIGIBLE
    assert result.name_jp == SHRINE_NAME
    assert result.shrine_id == shrine.pk
    assert result.usable_deity_fact_count == 0
    assert result.usable_history_fact_count == 3
    assert result.usable_fact_count == 3

    partition = partition_recommendation_eligible_shrines([shrine])
    assert partition.source_count == 1
    assert partition.eligible_count == 1
    assert partition.ineligible_count == 0
    assert len(partition.eligible) == 1
    assert partition.eligible[0].shrine.pk == shrine.pk
    assert len(partition.eligible[0].knowledge_deities) == 0

    histories = partition.eligible[0].knowledge_histories
    assert [(h["history_type"], h["title"]) for h in histories] == EXPECTED_HISTORIES

    candidate = {
        "id": shrine.pk,
        "shrine_id": shrine.pk,
        "name": shrine.name_jp,
    }
    assert filter_recommendation_eligible_candidates([candidate]) == [candidate]

    shrine.refresh_from_db()
    assert shrine.goriyaku in ("", None)
    assert shrine.goriyaku_tags.count() == 0


@pytest.mark.django_db
def test_noncanonical_akai_addresses_never_inherit_nsrc_000006_eligibility():
    _import_current_seeds()

    report = verify_recommendation_eligibility(
        shrine_identities=[
            ShrineIdentity(name=SHRINE_NAME, address=address)
            for address in NON_CANONICAL_ADDRESSES
        ]
    )

    assert report.summary_counts() == (0, 0, 2)
    assert [result.status for result in report.results] == [UNRESOLVED, UNRESOLVED]
    assert all(result.shrine_id is None for result in report.results)
