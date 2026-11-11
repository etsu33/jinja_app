"""inspect_concierge_ranking（本番の順位を読むだけの管理コマンド）の契約。

- 相談の API と同じ道筋で順位を付ける（上位3社の並びと点数が API と同じ）。
- データベースに書き込まない・キャッシュに書き込まない・外部につながない。
- 書き込みや外部の呼び出しが起きようとしたら止めて、失敗として終わる。
- Web の画面や API からは呼べない（URL を持たない）。
"""

from __future__ import annotations

import io
import json
import socket

import pytest
from django.apps import apps
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError
from django.test import Client
from django.urls import URLPattern, URLResolver, get_resolver

from temples.management.commands import inspect_concierge_ranking as command_module
from temples.management.commands.inspect_concierge_ranking import (
    ReadOnlyViolation,
    read_only_guard,
    run_inspection,
)
from temples.models import Shrine
from temples.tests.support.recommendation_eligibility import attach_usable_deity_fact

TOKYO = (35.681236, 139.767125)


def _shrine(name: str, *, lat: float, lng: float, visit_style_tags: list[str], popular: float = 0.0) -> Shrine:
    shrine = Shrine.objects.create(
        name_jp=name,
        address=f"東京都千代田区{name}",
        latitude=lat,
        longitude=lng,
        visit_style_tags=visit_style_tags,
        popular_score=popular,
    )
    attach_usable_deity_fact(shrine, display_name=f"{name}の祭神")
    return shrine


@pytest.fixture
def shrines(db, settings):
    settings.CONCIERGE_USE_LLM = False
    return [
        _shrine("近くの街の神社", lat=35.6830, lng=139.7680, visit_style_tags=["urban"]),
        _shrine("近くの静かな神社", lat=35.6900, lng=139.7700, visit_style_tags=["quiet"]),
        _shrine("遠くの杜の神社", lat=35.9000, lng=139.2000, visit_style_tags=["quiet", "nature"]),
        _shrine("遠くの古い神社", lat=34.9000, lng=135.7000, visit_style_tags=["classic"]),
    ]


def _row_counts() -> dict[str, int]:
    return {
        model._meta.label: model.objects.count()
        for model in apps.get_models()
        if model._meta.managed and not model._meta.proxy and model._meta.app_label in {"temples", "users"}
    }


def _run(*args: str) -> dict:
    out = io.StringIO()
    call_command("inspect_concierge_ranking", *args, "--json", stdout=out)
    return json.loads(out.getvalue())


# ---------- 相談の API と同じ道筋 ----------


@pytest.mark.django_db
@pytest.mark.parametrize("location", [TOKYO, None])
@pytest.mark.parametrize("query", ["休みたい", "仕事で前に進みたい"])
def test_top3_matches_the_concierge_api(shrines, query, location):
    body = {"query": query}
    if location:
        body.update(lat=location[0], lng=location[1])
    response = Client().post(
        "/api/concierge/chat/", data=json.dumps(body), content_type="application/json", HTTP_HOST="localhost"
    )
    api_recs = response.json()["data"]["recommendations"]

    with read_only_guard():
        result = run_inspection(query=query, lat=location[0] if location else None, lng=location[1] if location else None)

    assert [row["name"] for row in result["rows"][:3]] == [rec["name"] for rec in api_recs[:3]]
    assert [row["score_total"] for row in result["rows"][:3]] == [round(rec["_score_total"], 3) for rec in api_recs[:3]]


@pytest.mark.django_db
def test_output_has_the_breakdown_and_implied_visit_style(shrines):
    payload = _run("--query", "休みたい", "--lat", str(TOKYO[0]), "--lng", str(TOKYO[1]), "--include-no-location")

    assert [r["location"] is None for r in payload["results"]] == [False, True]
    result = payload["results"][0]
    assert result["need_tags"] == ["rest"]
    assert result["implied_visit_style_tags"] == ["less_crowded", "nature", "quiet"]
    assert len(result["rows"]) == 4  # 候補が4社なので、上位5社の指定でも4社
    assert [row["displayed"] for row in result["rows"]] == [True, True, True, False]
    row = next(r for r in result["rows"] if r["name"] == "遠くの杜の神社")
    assert set(row["contributions"]) == {
        "distance", "need", "visit_style", "implied_visit_style", "popular", "element", "behavior",
    }
    assert row["implied_visit_style_matched"] == ["nature", "quiet"]
    assert row["contributions"]["implied_visit_style"] == pytest.approx(0.35)  # 何個一致しても1つ分
    assert payload["overview"]["visit_style_tag_counts"]["quiet"] == 2
    assert payload["overview"]["concierge_use_llm"] is False


@pytest.mark.django_db
def test_expect_compares_with_the_located_result(shrines):
    payload = _run(
        "--query", "休みたい", "--lat", str(TOKYO[0]), "--lng", str(TOKYO[1]),
        "--include-no-location", "--expect", "近くの静かな神社,存在しない神社",
    )
    comparison = payload["comparison"]
    assert comparison["location"] == {"lat": TOKYO[0], "lng": TOKYO[1]}
    assert comparison["matches"][0] == {
        "rank": 1, "expected": "近くの静かな神社", "actual": comparison["actual"][0],
        "same": comparison["actual"][0] == "近くの静かな神社",
    }
    assert comparison["matches"][1]["same"] is False


@pytest.mark.django_db
def test_text_output_lists_ranks_and_read_only_summary(shrines):
    out = io.StringIO()
    call_command("inspect_concierge_ranking", "--query", "休みたい", stdout=out)
    text = out.getvalue()
    assert "== 相談「休みたい」 / 場所なし" in text
    assert "自動で足した好み" in text
    assert "読むだけでない文 0件" in text
    assert "外部への接続 0件" in text


# ---------- 書き込まない・外部につながない ----------


@pytest.mark.django_db
def test_command_writes_nothing(shrines):
    before = _row_counts()
    cache.set("inspect-probe", "before")

    payload = _run(
        "--query", "休みたい", "--query", "気持ちを落ち着けて休みたい", "--query", "仕事で前に進みたい",
        "--lat", str(TOKYO[0]), "--lng", str(TOKYO[1]), "--include-no-location",
    )

    assert _row_counts() == before
    assert cache.get("inspect-probe") == "before"
    read_only = payload["read_only"]
    assert read_only["sql_statements"] > 0
    assert read_only["non_read_sql_statements"] == 0
    assert read_only["cache_write_attempts"] == 0
    assert read_only["network_attempts"] == 0


@pytest.mark.django_db
def test_guard_blocks_database_writes(shrines):
    with pytest.raises(DatabaseError):
        with read_only_guard():
            Shrine.objects.create(name_jp="書き込みの試し", address="どこか")
    assert not Shrine.objects.filter(name_jp="書き込みの試し").exists()


@pytest.mark.django_db
def test_guard_records_non_read_sql(shrines):
    with read_only_guard() as guard:
        try:
            Shrine.objects.filter(name_jp="近くの街の神社").update(popular_score=9.0)
        except DatabaseError:
            pass
    assert guard.write_statements and guard.write_statements[0].upper().startswith("UPDATE")
    assert not guard.ok


@pytest.mark.django_db
def test_guard_blocks_cache_writes_and_network(shrines):
    with read_only_guard() as guard:
        with pytest.raises(ReadOnlyViolation):
            cache.set("inspect-probe", "x")
        with pytest.raises(ReadOnlyViolation):
            socket.create_connection(("nominatim.openstreetmap.org", 443), timeout=1)
        with pytest.raises(ReadOnlyViolation):
            socket.getaddrinfo("api.openai.com", 443)
    assert guard.cache_writes == ["set"]
    assert len(guard.network_attempts) == 2
    assert not guard.ok


@pytest.mark.django_db
def test_command_fails_when_network_is_attempted(shrines, monkeypatch):
    def _calls_out(**kwargs):
        try:
            socket.create_connection(("maps.googleapis.com", 443), timeout=1)
        except ReadOnlyViolation:
            pass  # 呼び出し側が例外を握りつぶしても、失敗として数える
        return {"query": kwargs["query"], "location": None, "rows": [], "need_tags": [],
                "consultation_axis": None, "visit_style_tags": [], "implied_visit_style_tags": [],
                "candidate_count": 0}

    monkeypatch.setattr(command_module, "run_inspection", _calls_out)
    with pytest.raises(CommandError):
        call_command("inspect_concierge_ranking", "--query", "休みたい", stdout=io.StringIO())


@pytest.mark.django_db
def test_llm_is_never_called_even_if_enabled(shrines, settings, monkeypatch):
    settings.CONCIERGE_USE_LLM = True

    def _boom(*args, **kwargs):
        raise AssertionError("LLM must not be called")

    monkeypatch.setattr("temples.llm.orchestrator.ConciergeOrchestrator.suggest", _boom)
    payload = _run("--query", "休みたい")
    assert payload["overview"]["concierge_use_llm"] is True
    assert payload["read_only"]["network_attempts"] == 0


# ---------- 引数 ----------


@pytest.mark.django_db
def test_lat_and_lng_must_be_given_together(shrines):
    with pytest.raises(CommandError):
        call_command("inspect_concierge_ranking", "--query", "休みたい", "--lat", "35.6", stdout=io.StringIO())


@pytest.mark.django_db
def test_query_is_required(shrines):
    with pytest.raises(CommandError):
        call_command("inspect_concierge_ranking", stdout=io.StringIO())


# ---------- Web・API から呼べない ----------


def _all_callbacks(patterns):
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            yield from _all_callbacks(pattern.url_patterns)
        elif isinstance(pattern, URLPattern):
            yield pattern.callback


def test_command_is_not_reachable_from_any_url():
    modules = {
        getattr(callback, "__module__", "") or ""
        for callback in _all_callbacks(get_resolver().url_patterns)
    }
    modules |= {
        getattr(getattr(callback, "view_class", None), "__module__", "") or ""
        for callback in _all_callbacks(get_resolver().url_patterns)
    }
    assert not any("inspect_concierge_ranking" in module for module in modules)
