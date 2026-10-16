"""nsrc-000007 赤城社（新潟県十日町市四日町2534番地）の G5 Shared Recommendation Eligibility。

authority（docs/knowledge/recommendation-eligibility-contract.md）をそのまま使う:
shrine_knowledge_selector -> evidence_gate.decide_fact_usability() -> is_recommendation_eligible()。
新しい eligibility rule は作らない。

赤城社は usable Deity 0 / usable History 2。goriyaku_tags が無いことは INELIGIBLE の理由ではない
（usable History が G5 の authority）。

H002 には別実体の同名 `赤城社` があるため、identity は exact (name_jp, address) のみで扱う。
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
    INELIGIBLE,
    UNRESOLVED,
    ShrineIdentity,
    verify_recommendation_eligibility,
)

TEMPLES_DIR = Path(__file__).resolve().parents[1]
BASE_SEED_PATH = TEMPLES_DIR / "data" / "shrines_seed_clean.json"
KNOWLEDGE_SEED_PATH = TEMPLES_DIR / "data" / "knowledge_seeds" / "nsrc_000007_seed.json"

SHRINE_NAME = "赤城社"
SHRINE_ADDRESS = "新潟県十日町市四日町2534番地"
OTHER_AKAGI_ADDRESSES = (
    "新潟県十日町市上組2059番地子",
    "新潟県十日町市伊達乙48番地",
    "新潟県南魚沼市芹田79番地",
)
EXPECTED_HISTORIES = [
    ("historical_event", "安政7年正月の再建"),
    ("regional_context", "赤城社に伝わった越後縮幡"),
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
def test_nsrc_000007_is_shared_recommendation_eligible_on_current_develop():
    _import_current_seeds()

    # exact canonical identity（name-only では解決しない）。
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
    assert result.usable_history_fact_count == 2
    assert result.usable_fact_count == 2

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
    filtered = filter_recommendation_eligible_candidates([candidate])
    assert filtered == [candidate]

    # goriyaku_tags が無くても ELIGIBLE のまま（usable History が G5 の authority）。
    shrine.refresh_from_db()
    assert shrine.goriyaku in ("", None)
    assert shrine.goriyaku_tags.count() == 0


@pytest.mark.django_db
def test_other_akagi_identities_never_inherit_nsrc_000007_eligibility():
    """同名・別住所の identity は nsrc-000007 へ解決されず、その eligibility を引き継がない。"""
    _import_current_seeds()

    report = verify_recommendation_eligibility(
        shrine_identities=[
            ShrineIdentity(name=SHRINE_NAME, address=a) for a in OTHER_AKAGI_ADDRESSES
        ]
    )

    assert report.summary_counts() == (0, 1, 2)
    assert [r.status for r in report.results] == [UNRESOLVED, INELIGIBLE, UNRESOLVED]

    # 伊達乙48番地（nsrc-000009）は Base Shrine として materialize 済みだが、
    # この helper では nsrc-000009 Knowledge を投入しないため INELIGIBLE。
    # 同名別住所が nsrc-000007 の usable History を継承していないことを確認する。
    ineligible = report.results[1]
    assert ineligible.shrine_id is not None
    assert ineligible.usable_fact_count == 0
    assert report.results[0].shrine_id is None
    assert report.results[2].shrine_id is None
