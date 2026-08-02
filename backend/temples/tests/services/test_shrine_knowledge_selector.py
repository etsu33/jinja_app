from __future__ import annotations

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.shrine_knowledge_selector import (
    fetch_fact_ready_knowledge_deities,
    fetch_fact_ready_knowledge_histories,
)

pytestmark = pytest.mark.django_db


def _create_shrine(name: str = "Selector監査神社") -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )


def _create_source(verification_status: str = "source_confirmed", **kwargs) -> ShrineKnowledgeSource:
    defaults = dict(
        source_type="shrine_official",
        title=f"出典-{verification_status}",
        verification_status=verification_status,
    )
    if verification_status in ("source_confirmed", "reviewed"):
        defaults["verified_at"] = timezone.now()
    defaults.update(kwargs)
    return ShrineKnowledgeSource.objects.create(**defaults)


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


# --- ShrineDeity selector ---


@pytest.mark.parametrize("verification_status", ["source_confirmed", "reviewed"])
def test_fetch_fact_ready_knowledge_deities_includes_fact_ready_status(verification_status):
    shrine = _create_shrine()
    deity = _create_deity(shrine, verification_status)
    deity.sources.add(_create_source("source_confirmed"))

    result = fetch_fact_ready_knowledge_deities([shrine.id])

    assert len(result.get(shrine.id, [])) == 1
    assert result[shrine.id][0]["display_name"] == deity.display_name


@pytest.mark.parametrize(
    "verification_status", ["draft", "unverified", "disputed", "outdated", "rejected"]
)
def test_fetch_fact_ready_knowledge_deities_excludes_non_fact_ready_status(verification_status):
    shrine = _create_shrine()
    deity = _create_deity(shrine, verification_status)
    deity.sources.add(_create_source("source_confirmed"))

    result = fetch_fact_ready_knowledge_deities([shrine.id])

    assert result.get(shrine.id, []) == []


def test_fetch_fact_ready_knowledge_deities_excludes_deity_without_fact_ready_source():
    shrine = _create_shrine()
    deity = _create_deity(shrine, "source_confirmed")
    deity.sources.add(_create_source("draft"))

    result = fetch_fact_ready_knowledge_deities([shrine.id])

    assert result.get(shrine.id, []) == []


def test_fetch_fact_ready_knowledge_deities_preserves_sort_order():
    shrine = _create_shrine()
    source = _create_source("source_confirmed")
    d2 = _create_deity(shrine, "source_confirmed", sort_order=1, display_name="二番目")
    d1 = _create_deity(shrine, "source_confirmed", sort_order=0, display_name="一番目")
    for d in (d1, d2):
        d.sources.add(source)

    result = fetch_fact_ready_knowledge_deities([shrine.id])

    names = [item["display_name"] for item in result[shrine.id]]
    assert names == ["一番目", "二番目"]


def test_fetch_fact_ready_knowledge_deities_dedupes_when_deity_has_multiple_fact_ready_sources():
    shrine = _create_shrine()
    deity = _create_deity(shrine, "source_confirmed")
    deity.sources.add(_create_source("source_confirmed", title="出典A"))
    deity.sources.add(_create_source("reviewed", title="出典B"))

    result = fetch_fact_ready_knowledge_deities([shrine.id])

    assert len(result[shrine.id]) == 1


def test_fetch_fact_ready_knowledge_deities_batches_across_multiple_shrines_without_n_plus_1():
    shrines = [_create_shrine(f"神社{i}") for i in range(5)]
    source = _create_source("source_confirmed")
    for shrine in shrines:
        deity = _create_deity(shrine, "source_confirmed")
        deity.sources.add(source)

    with CaptureQueriesContext(connection) as ctx:
        result = fetch_fact_ready_knowledge_deities([s.id for s in shrines])

    assert all(len(result.get(s.id, [])) == 1 for s in shrines)
    # Evidence Gate導入後は「候補Deity取得」+「fact-ready Source prefetch」の
    # 合計2クエリで、対象Shrine数に関わらず一定であることを確認する
    # （N+1になっていないことが本質であり、クエリ数そのものは1固定ではない）。
    assert len(ctx.captured_queries) == 2


def test_fetch_fact_ready_knowledge_deities_empty_shrine_ids_returns_empty_dict():
    assert fetch_fact_ready_knowledge_deities([]) == {}


# --- ShrineHistory selector ---


@pytest.mark.parametrize("verification_status", ["source_confirmed", "reviewed"])
def test_fetch_fact_ready_knowledge_histories_includes_fact_ready_status(verification_status):
    shrine = _create_shrine()
    history = _create_history(shrine, verification_status)
    history.sources.add(_create_source("source_confirmed"))

    result = fetch_fact_ready_knowledge_histories([shrine.id])

    assert len(result.get(shrine.id, [])) == 1
    assert result[shrine.id][0]["content"] == history.content


@pytest.mark.parametrize(
    "verification_status", ["draft", "unverified", "disputed", "outdated", "rejected"]
)
def test_fetch_fact_ready_knowledge_histories_excludes_non_fact_ready_status(verification_status):
    shrine = _create_shrine()
    history = _create_history(shrine, verification_status)
    history.sources.add(_create_source("source_confirmed"))

    result = fetch_fact_ready_knowledge_histories([shrine.id])

    assert result.get(shrine.id, []) == []


def test_fetch_fact_ready_knowledge_histories_excludes_history_without_fact_ready_source():
    shrine = _create_shrine()
    history = _create_history(shrine, "source_confirmed")
    history.sources.add(_create_source("disputed"))

    result = fetch_fact_ready_knowledge_histories([shrine.id])

    assert result.get(shrine.id, []) == []


def test_fetch_fact_ready_knowledge_histories_preserves_sort_order():
    shrine = _create_shrine()
    source = _create_source("source_confirmed")
    h2 = _create_history(shrine, "source_confirmed", sort_order=1, title="1319年")
    h1 = _create_history(shrine, "source_confirmed", sort_order=0, title="1187年")
    for h in (h1, h2):
        h.sources.add(source)

    result = fetch_fact_ready_knowledge_histories([shrine.id])

    titles = [item["title"] for item in result[shrine.id]]
    assert titles == ["1187年", "1319年"]


def test_fetch_fact_ready_knowledge_histories_batches_across_multiple_shrines_without_n_plus_1():
    shrines = [_create_shrine(f"神社{i}") for i in range(5)]
    source = _create_source("source_confirmed")
    for shrine in shrines:
        history = _create_history(shrine, "source_confirmed")
        history.sources.add(source)

    with CaptureQueriesContext(connection) as ctx:
        result = fetch_fact_ready_knowledge_histories([s.id for s in shrines])

    assert all(len(result.get(s.id, [])) == 1 for s in shrines)
    # Evidence Gate導入後は「候補History取得」+「fact-ready Source prefetch」の
    # 合計2クエリで、対象Shrine数に関わらず一定であることを確認する
    # （N+1になっていないことが本質であり、クエリ数そのものは1固定ではない）。
    assert len(ctx.captured_queries) == 2


def test_fetch_fact_ready_knowledge_histories_empty_shrine_ids_returns_empty_dict():
    assert fetch_fact_ready_knowledge_histories([]) == {}
