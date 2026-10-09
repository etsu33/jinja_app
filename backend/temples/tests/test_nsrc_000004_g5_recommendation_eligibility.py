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
    ShrineIdentity,
    verify_recommendation_eligibility,
)

TEMPLES_DIR = Path(__file__).resolve().parents[1]
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"
KNOWLEDGE_SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "nsrc_000004_seed.json"

SHRINE_NAME = "青海神社"
SHRINE_ADDRESS = "新潟県加茂市大字加茂字宮山229番地"


@pytest.mark.django_db
def test_nsrc_000004_is_shared_recommendation_eligible_on_current_develop():
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
    assert result.usable_deity_fact_count == 2
    assert result.usable_history_fact_count == 2
    assert result.usable_fact_count == 4

    partition = partition_recommendation_eligible_shrines([shrine])
    assert partition.source_count == 1
    assert partition.eligible_count == 1
    assert partition.ineligible_count == 0
    assert len(partition.eligible) == 1
    assert partition.eligible[0].shrine.pk == shrine.pk
    assert len(partition.eligible[0].knowledge_deities) == 2
    assert len(partition.eligible[0].knowledge_histories) == 2

    candidate = {
        "id": shrine.pk,
        "shrine_id": shrine.pk,
        "name": shrine.name_jp,
    }
    filtered = filter_recommendation_eligible_candidates([candidate])
    assert filtered == [candidate]

    shrine.refresh_from_db()
    assert shrine.goriyaku in ("", None)
    assert shrine.goriyaku_tags.count() == 0
