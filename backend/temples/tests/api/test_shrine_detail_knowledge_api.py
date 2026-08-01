from __future__ import annotations

from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.utils import timezone

import pytest
from rest_framework.test import APIClient

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource

pytestmark = pytest.mark.django_db


def _create_shrine(name: str = "Contract監査神社") -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )


def _create_deity(shrine: Shrine, verification_status: str, sort_order: int = 0, **kwargs) -> ShrineDeity:
    defaults = dict(
        display_name=f"祭神-{verification_status}-{sort_order}",
        verification_status=verification_status,
        sort_order=sort_order,
    )
    if verification_status in ("source_confirmed", "reviewed"):
        defaults["verified_at"] = timezone.now()
    defaults.update(kwargs)
    return ShrineDeity.objects.create(shrine=shrine, **defaults)


def _create_history(shrine: Shrine, verification_status: str, sort_order: int = 0, **kwargs) -> ShrineHistory:
    defaults = dict(
        history_type="official_origin",
        title=f"由緒-{verification_status}-{sort_order}",
        content="内容",
        verification_status=verification_status,
        sort_order=sort_order,
    )
    if verification_status in ("source_confirmed", "reviewed"):
        defaults["verified_at"] = timezone.now()
    defaults.update(kwargs)
    return ShrineHistory.objects.create(shrine=shrine, **defaults)


def _create_source(verification_status: str, title: str = "出典", **kwargs) -> ShrineKnowledgeSource:
    defaults = dict(
        source_type="shrine_official",
        title=f"{title}-{verification_status}",
        verification_status=verification_status,
    )
    if verification_status in ("source_confirmed", "reviewed"):
        defaults["verified_at"] = timezone.now()
    defaults.update(kwargs)
    return ShrineKnowledgeSource.objects.create(**defaults)


def test_shrine_detail_api_returns_only_fact_ready_knowledge():
    shrine = _create_shrine()
    _create_deity(shrine, "source_confirmed", sort_order=0)
    _create_deity(shrine, "draft", sort_order=1)
    _create_history(shrine, "reviewed", sort_order=0)
    _create_history(shrine, "unverified", sort_order=1)

    client = APIClient()
    resp = client.get(f"/api/shrines/{shrine.id}/")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["deities"]) == 1
    assert body["deities"][0]["verification_status"] == "source_confirmed"
    assert len(body["histories"]) == 1
    assert body["histories"][0]["verification_status"] == "reviewed"


def test_shrine_detail_api_returns_empty_arrays_when_no_knowledge():
    shrine = _create_shrine()

    client = APIClient()
    resp = client.get(f"/api/shrines/{shrine.id}/")

    assert resp.status_code == 200
    body = resp.json()
    assert body["deities"] == []
    assert body["histories"] == []


def test_shrine_list_api_does_not_expose_knowledge_fields():
    shrine = _create_shrine()
    _create_deity(shrine, "source_confirmed")

    client = APIClient()
    resp = client.get("/api/shrines/")

    assert resp.status_code == 200
    body = resp.json()
    items = body.get("results", body) if isinstance(body, dict) else body
    assert len(items) >= 1
    for item in items:
        assert "deities" not in item
        assert "histories" not in item


def test_shrine_detail_api_prefetches_knowledge_without_n_plus_1():
    shrine = _create_shrine()
    source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="公式サイト",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    for i in range(5):
        deity = _create_deity(shrine, "source_confirmed", sort_order=i)
        deity.sources.add(source)
    for i in range(5):
        history = _create_history(shrine, "reviewed", sort_order=i)
        history.sources.add(source)

    client = APIClient()
    with CaptureQueriesContext(connection) as ctx:
        resp = client.get(f"/api/shrines/{shrine.id}/")
    assert resp.status_code == 200

    # deities/historiesそれぞれのsourcesアクセスがN+1にならないこと。
    # (神社取得+prefetch数本+関連クエリ) 目安として20クエリ未満であることを確認する。
    assert len(ctx.captured_queries) < 20, (
        f"expected prefetch to avoid N+1, got {len(ctx.captured_queries)} queries"
    )


@pytest.mark.parametrize("verification_status", ["source_confirmed", "reviewed"])
def test_shrine_detail_api_returns_fact_ready_source(verification_status):
    shrine = _create_shrine()
    deity = _create_deity(shrine, "source_confirmed")
    source = _create_source(verification_status)
    deity.sources.add(source)

    client = APIClient()
    resp = client.get(f"/api/shrines/{shrine.id}/")

    assert resp.status_code == 200
    body = resp.json()
    assert [s["verification_status"] for s in body["deities"][0]["sources"]] == [verification_status]


@pytest.mark.parametrize(
    "verification_status",
    ["draft", "unverified", "disputed", "outdated", "rejected"],
)
def test_shrine_detail_api_excludes_non_fact_ready_source(verification_status):
    shrine = _create_shrine()
    deity = _create_deity(shrine, "source_confirmed")
    source = _create_source(verification_status)
    deity.sources.add(source)

    client = APIClient()
    resp = client.get(f"/api/shrines/{shrine.id}/")

    assert resp.status_code == 200
    body = resp.json()
    assert body["deities"][0]["sources"] == []


def test_shrine_detail_api_returns_empty_sources_when_no_fact_ready_source_for_history():
    shrine = _create_shrine()
    history = _create_history(shrine, "reviewed")
    source = _create_source("unverified")
    history.sources.add(source)

    client = APIClient()
    resp = client.get(f"/api/shrines/{shrine.id}/")

    assert resp.status_code == 200
    body = resp.json()
    assert body["histories"][0]["sources"] == []


def test_shrine_detail_api_keeps_knowledge_when_all_its_sources_are_excluded():
    shrine = _create_shrine()
    deity = _create_deity(shrine, "source_confirmed")
    deity.sources.add(_create_source("draft"), _create_source("disputed"))

    client = APIClient()
    resp = client.get(f"/api/shrines/{shrine.id}/")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["deities"]) == 1
    assert body["deities"][0]["verification_status"] == "source_confirmed"
    assert body["deities"][0]["sources"] == []


def test_shrine_detail_api_source_filtering_does_not_increase_query_count():
    shrine = _create_shrine()
    deity = _create_deity(shrine, "source_confirmed")
    history = _create_history(shrine, "reviewed")
    for status_ in ["source_confirmed", "reviewed", "draft", "unverified", "disputed"]:
        source = _create_source(status_, title=f"deity-{status_}")
        deity.sources.add(source)
        source2 = _create_source(status_, title=f"history-{status_}")
        history.sources.add(source2)

    client = APIClient()
    with CaptureQueriesContext(connection) as ctx:
        resp = client.get(f"/api/shrines/{shrine.id}/")
    assert resp.status_code == 200

    assert len(ctx.captured_queries) < 20, (
        f"expected source-level filtering via Prefetch to avoid N+1, "
        f"got {len(ctx.captured_queries)} queries"
    )
