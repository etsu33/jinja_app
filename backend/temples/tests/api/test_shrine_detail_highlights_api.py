"""Highlights PR-4: 神社詳細APIの highlights。"""

from __future__ import annotations

from datetime import date

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from temples.models import ShrineHistory
from temples.tests.highlight_factories import (
    link_history,
    link_source,
    make_displayable_highlight,
    make_highlight,
    make_shrine,
    make_source,
    make_translation,
)

pytestmark = pytest.mark.django_db


def _get(shrine) -> dict:
    resp = APIClient().get(f"/api/shrines/{shrine.id}/")
    assert resp.status_code == 200
    return resp.json()


def _history(shrine, *, verification_status="source_confirmed", sort_order=0, with_source=True):
    kwargs = {}
    if verification_status in ("source_confirmed", "reviewed"):
        kwargs["verified_at"] = timezone.now()
    history = ShrineHistory.objects.create(
        shrine=shrine,
        history_type="tradition",
        title=f"伝承-{sort_order}",
        content="本文",
        verification_status=verification_status,
        sort_order=sort_order,
        **kwargs,
    )
    if with_source:
        history.sources.add(make_source())
    return history


def test_shrine_without_highlights_returns_empty_list():
    assert _get(make_shrine())["highlights"] == []


def test_displayable_highlight_is_returned_with_text_and_sources():
    shrine = make_shrine()
    highlight = make_displayable_highlight(
        shrine,
        name="拝殿の彫刻",
        description="正面上部の龍の彫刻を見る。",
        historical_connection="再建のときに彫られた。",
        location_hint="鳥居をくぐって正面",
    )
    item = _get(shrine)["highlights"][0]
    assert item["id"] == highlight.id
    assert item["category"] == "architecture"
    assert item["name"] == "拝殿の彫刻"
    assert item["description"] == "正面上部の龍の彫刻を見る。"
    assert item["historical_connection"] == "再建のときに彫られた。"
    assert item["location_hint"] == "鳥居をくぐって正面"
    assert item["linked_history_ids"] == []
    assert item["observed_on"] is None
    assert [s["source_type"] for s in item["sources"]] == ["shrine_official"]


def test_hidden_highlights_are_not_returned():
    shrine = make_shrine()
    make_displayable_highlight(shrine, name="出す")
    draft = make_highlight(shrine, publication_status="draft")
    make_translation(draft, name="下書き")
    link_source(draft, make_source())
    unapproved = make_highlight(shrine)
    make_translation(unapproved, name="未承認", review_status="draft")
    link_source(unapproved, make_source())
    observation_only = make_highlight(shrine)
    make_translation(observation_only, name="観察だけ")
    link_source(observation_only, make_source(source_type="user_observation"))
    english_only = make_highlight(shrine)
    make_translation(english_only, language_code="en", name="English only")
    link_source(english_only, make_source())

    assert [h["name"] for h in _get(shrine)["highlights"]] == ["出す"]


def test_highlights_are_ordered_by_sort_order():
    shrine = make_shrine()
    for order, name in [(2, "拝殿"), (0, "鳥居"), (1, "手水舎")]:
        highlight = make_highlight(shrine, sort_order=order)
        make_translation(highlight, name=name)
        link_source(highlight, make_source())
    assert [h["name"] for h in _get(shrine)["highlights"]] == ["鳥居", "手水舎", "拝殿"]


def test_observation_is_returned_as_date_not_as_source():
    shrine = make_shrine()
    highlight = make_displayable_highlight(shrine)
    link_source(
        highlight, make_source(source_type="user_observation", accessed_at=date(2026, 11, 21))
    )
    item = _get(shrine)["highlights"][0]
    assert item["observed_on"] == "2026-11-21"
    assert [s["source_type"] for s in item["sources"]] == ["shrine_official"]


def test_unverified_sources_are_not_returned():
    shrine = make_shrine()
    highlight = make_displayable_highlight(shrine)
    link_source(highlight, make_source(verification_status="draft", title="未確認の出典"))
    titles = [s["title"] for s in _get(shrine)["highlights"][0]["sources"]]
    assert all("未確認の出典" not in t for t in titles)


def test_linked_history_ids_only_include_histories_shown_on_detail():
    shrine = make_shrine()
    shown_second = _history(shrine, sort_order=2)
    shown_first = _history(shrine, sort_order=1)
    hidden_draft = _history(shrine, verification_status="draft", sort_order=3)
    hidden_no_source = _history(shrine, sort_order=4, with_source=False)
    highlight = make_displayable_highlight(shrine)
    for history in (shown_second, shown_first, hidden_draft, hidden_no_source):
        link_history(highlight, history)

    body = _get(shrine)
    shown_ids = [h["id"] for h in body["histories"]]
    assert shown_ids == [shown_first.id, shown_second.id]
    # 由緒・歴史の表示順にそろえる
    assert body["highlights"][0]["linked_history_ids"] == [shown_first.id, shown_second.id]


def test_disputed_history_shown_on_detail_can_be_linked():
    shrine = make_shrine()
    disputed = ShrineHistory.objects.create(
        shrine=shrine,
        history_type="tradition",
        title="異説",
        content="本文",
        verification_status="disputed",
    )
    disputed.sources.add(make_source())
    highlight = make_displayable_highlight(shrine)
    link_history(highlight, disputed)
    assert _get(shrine)["highlights"][0]["linked_history_ids"] == [disputed.id]


def test_highlight_list_api_does_not_include_highlights():
    make_displayable_highlight(make_shrine())
    resp = APIClient().get("/api/shrines/")
    assert resp.status_code == 200
    payload = resp.json()
    items = payload.get("results", payload) if isinstance(payload, dict) else payload
    assert items and all("highlights" not in item for item in items)


def test_highlights_do_not_cause_n_plus_one():
    shrine = make_shrine()
    for order in range(5):
        highlight = make_displayable_highlight(shrine, name=f"見どころ{order}")
        link_history(highlight, _history(shrine, sort_order=order))
        link_source(highlight, make_source(source_type="user_observation"))

    with CaptureQueriesContext(connection) as one:
        APIClient().get(f"/api/shrines/{shrine.id}/")
    for order in range(5, 10):
        highlight = make_displayable_highlight(shrine, name=f"見どころ{order}")
        link_history(highlight, _history(shrine, sort_order=order))
    with CaptureQueriesContext(connection) as two:
        body = APIClient().get(f"/api/shrines/{shrine.id}/").json()

    assert len(body["highlights"]) == 10
    assert len(two.captured_queries) == len(one.captured_queries)
