"""nsrc-000009 赤城社 G5 Shared Recommendation Eligibility."""

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
LEGACY_SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "nsrc_000007_seed.json"
KNOWLEDGE_SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "nsrc_000009_seed.json"

SHRINE_NAME = "赤城社"
SHRINE_ADDRESS = "新潟県十日町市伊達乙48番地"
OTHER_AKAGI_ADDRESSES = (
    "新潟県十日町市上組2059番地子",
    "新潟県南魚沼市芹田79番地",
)
EXPECTED_HISTORIES = [
    ("historical_event", "天明3年8月の創立記録"),
    ("historical_event", "大正2年の改築記録"),
]


def _import_current_state() -> None:
    call_command(
        "import_shrines_seed",
        "--source",
        str(BASE_SEED_PATH),
        "--skip-goriyaku-tags",
        stdout=io.StringIO(),
        stderr=io.StringIO(),
    )
    # Shared municipal Source already exists in the real lineage via nsrc-000007.
    call_command(
        "import_shrine_knowledge",
        str(LEGACY_SEED_PATH),
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
def test_nsrc_000009_is_shared_recommendation_eligible():
    _import_current_state()

    shrine = Shrine.objects.get(name_jp=SHRINE_NAME, address=SHRINE_ADDRESS)

    report = verify_recommendation_eligibility(
        shrine_identities=[ShrineIdentity(name=SHRINE_NAME, address=SHRINE_ADDRESS)]
    )

    assert report.summary_counts() == (1, 0, 0)
    assert report.all_eligible is True
    [result] = report.results
    assert result.status == ELIGIBLE
    assert result.shrine_id == shrine.pk
    assert result.usable_deity_fact_count == 0
    assert result.usable_history_fact_count == 2
    assert result.usable_fact_count == 2

    partition = partition_recommendation_eligible_shrines([shrine])
    assert partition.source_count == 1
    assert partition.eligible_count == 1
    assert partition.ineligible_count == 0
    assert partition.eligible[0].shrine.pk == shrine.pk
    assert len(partition.eligible[0].knowledge_deities) == 0
    assert [
        (h["history_type"], h["title"])
        for h in partition.eligible[0].knowledge_histories
    ] == EXPECTED_HISTORIES

    candidate = {"id": shrine.pk, "shrine_id": shrine.pk, "name": shrine.name_jp}
    assert filter_recommendation_eligible_candidates([candidate]) == [candidate]

    shrine.refresh_from_db()
    assert shrine.goriyaku in ("", None)
    assert shrine.goriyaku_tags.count() == 0


@pytest.mark.django_db
def test_other_unmaterialized_akagi_identities_do_not_inherit_nsrc_000009_eligibility():
    _import_current_state()

    report = verify_recommendation_eligibility(
        shrine_identities=[
            ShrineIdentity(name=SHRINE_NAME, address=address)
            for address in OTHER_AKAGI_ADDRESSES
        ]
    )

    assert report.summary_counts() == (0, 0, 2)
    assert [result.status for result in report.results] == [UNRESOLVED, UNRESOLVED]
    assert all(result.shrine_id is None for result in report.results)
