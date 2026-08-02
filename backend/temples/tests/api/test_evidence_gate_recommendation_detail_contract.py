"""Evidence Gate Foundation: Recommendation / Shrine Detail 非対称性解消テスト。

導入前は「Fact ready + fact-ready Sourceなし」の場合に
Recommendation selector = 除外（usable=False相当）
Shrine Detail API      = 表示（sourcesが空配列のまま表示）
という非対称な挙動だった。

Evidence Gate導入後は、同じFactに対してRecommendation selectorの利用可否と
Shrine Detail APIの利用可否が常に一致することを固定する。
"""

from __future__ import annotations

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from temples.models import Shrine, ShrineDeity, ShrineKnowledgeSource
from temples.services.shrine_knowledge_selector import fetch_fact_ready_knowledge_deities

pytestmark = pytest.mark.django_db


def _create_shrine(name: str = "非対称性監査神社") -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )


def _create_source(verification_status: str, **kwargs) -> ShrineKnowledgeSource:
    defaults = dict(
        source_type="shrine_official",
        title=f"出典-{verification_status}",
        verification_status=verification_status,
    )
    if verification_status in ("source_confirmed", "reviewed"):
        defaults["verified_at"] = timezone.now()
    defaults.update(kwargs)
    return ShrineKnowledgeSource.objects.create(**defaults)


def _create_deity(shrine: Shrine, verification_status: str, **kwargs) -> ShrineDeity:
    defaults = dict(display_name="祭神", verification_status=verification_status)
    if verification_status in ("source_confirmed", "reviewed"):
        defaults["verified_at"] = timezone.now()
    defaults.update(kwargs)
    return ShrineDeity.objects.create(shrine=shrine, **defaults)


def _is_recommendation_usable(shrine: Shrine) -> bool:
    result = fetch_fact_ready_knowledge_deities([shrine.id])
    return len(result.get(shrine.id, [])) == 1


def _is_detail_usable(shrine: Shrine) -> bool:
    client = APIClient()
    resp = client.get(f"/api/shrines/{shrine.id}/")
    assert resp.status_code == 200
    return len(resp.json()["deities"]) == 1


def test_fact_ready_without_any_source_is_unusable_on_both_paths():
    # 旧: Recommendation=False, Detail=True という非対称の再発防止テスト。
    shrine = _create_shrine()
    _create_deity(shrine, "source_confirmed")

    assert _is_recommendation_usable(shrine) is False
    assert _is_detail_usable(shrine) is False


def test_fact_ready_with_only_draft_source_is_unusable_on_both_paths():
    shrine = _create_shrine()
    deity = _create_deity(shrine, "source_confirmed")
    deity.sources.add(_create_source("draft"))

    assert _is_recommendation_usable(shrine) is False
    assert _is_detail_usable(shrine) is False


def test_fact_ready_with_ready_source_is_usable_on_both_paths():
    shrine = _create_shrine()
    deity = _create_deity(shrine, "source_confirmed")
    deity.sources.add(_create_source("source_confirmed"))

    assert _is_recommendation_usable(shrine) is True
    assert _is_detail_usable(shrine) is True


@pytest.mark.parametrize("fact_status", ["draft", "unverified", "disputed", "outdated", "rejected"])
def test_non_fact_ready_fact_is_unusable_on_both_paths_even_with_ready_source(fact_status):
    shrine = _create_shrine()
    deity = _create_deity(shrine, fact_status)
    deity.sources.add(_create_source("source_confirmed"))

    assert _is_recommendation_usable(shrine) is False
    assert _is_detail_usable(shrine) is False


@pytest.mark.parametrize(
    "case",
    [
        {"fact_status": "source_confirmed", "source_statuses": []},
        {"fact_status": "source_confirmed", "source_statuses": ["draft"]},
        {"fact_status": "source_confirmed", "source_statuses": ["draft", "disputed"]},
        {"fact_status": "draft", "source_statuses": ["source_confirmed"]},
        {"fact_status": "disputed", "source_statuses": ["source_confirmed"]},
        {"fact_status": "source_confirmed", "source_statuses": ["source_confirmed"]},
        {"fact_status": "reviewed", "source_statuses": ["reviewed"]},
        {"fact_status": "source_confirmed", "source_statuses": ["source_confirmed", "draft"]},
    ],
)
def test_recommendation_and_detail_agree_for_every_combination(case):
    shrine = _create_shrine()
    deity = _create_deity(shrine, case["fact_status"])
    for i, status in enumerate(case["source_statuses"]):
        deity.sources.add(_create_source(status, title=f"出典{i}-{status}"))

    recommendation_usable = _is_recommendation_usable(shrine)
    detail_usable = _is_detail_usable(shrine)

    assert recommendation_usable == detail_usable, (
        f"非対称: case={case} recommendation={recommendation_usable} " f"detail={detail_usable}"
    )
