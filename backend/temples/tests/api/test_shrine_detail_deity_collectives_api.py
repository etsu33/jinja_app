"""A6-02 Step 2: Shrine Detail への admitted deity_collectives 接続の test。

Runtime admission の唯一の authority は fetch_runtime_admitted_collectives()。
Detail（単一 Shrine）でのみ呼ばれ、List 経路では呼ばれないことを固定する。
"""

from __future__ import annotations

import json

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from temples.api.serializers import shrine as shrine_serializers
from temples.api.serializers.shrine import ShrineDetailSerializer, ShrineListSerializer
from temples.models import (
    CollectiveRuntimeActivation,
    Shrine,
    ShrineDeity,
    ShrineDeityCollective,
    ShrineDeityCollectiveMembership,
    ShrineHistory,
    ShrineKnowledgeSource,
)
from temples.services import collective_runtime_selector

pytestmark = pytest.mark.django_db

_seq = {"n": 0}


# ---------- helpers ----------


def _shrine(name: str = "集合祭神Detail神社") -> Shrine:
    _seq["n"] += 1
    return Shrine.objects.create(
        name_jp=f"{name}{_seq['n']}",
        address="東京都千代田区1-2-3",
        latitude=35.0 + _seq["n"] * 0.001,
        longitude=139.0,
    )


def _source(status: str = "source_confirmed") -> ShrineKnowledgeSource:
    return ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title=f"公式-{status}",
        verification_status=status,
        verified_at=timezone.now() if status in ("source_confirmed", "reviewed") else None,
    )


def _ready() -> dict:
    return dict(
        verification_status="source_confirmed", verified_at=timezone.now(), confidence="high"
    )


def _collective(
    shrine: Shrine,
    label: str = "箱根大神",
    *,
    sort_order: int = 0,
    activate: bool = True,
    source_status: str | None = "source_confirmed",
    **overrides,
) -> ShrineDeityCollective:
    fields = dict(
        shrine=shrine,
        source_attested_label=label,
        role="primary",
        sort_order=sort_order,
        member_count=2,
        member_count_relation="exact",
        member_list_status="complete",
        **_ready(),
    )
    fields.update(overrides)
    collective = ShrineDeityCollective.objects.create(**fields)
    if source_status:
        collective.sources.add(_source(source_status))
    if activate:
        CollectiveRuntimeActivation.objects.create(collective=collective)
    return collective


def _member(
    collective: ShrineDeityCollective,
    name: str,
    sort_order: int = 0,
    source_status: str | None = "source_confirmed",
) -> ShrineDeityCollectiveMembership:
    deity = ShrineDeity.objects.create(shrine=collective.shrine, display_name=name)
    membership = ShrineDeityCollectiveMembership.objects.create(
        collective=collective, deity=deity, sort_order=sort_order, **_ready()
    )
    if source_status:
        membership.sources.add(_source(source_status))
    return membership


def _admitted(shrine: Shrine, label: str = "箱根大神", **kwargs) -> ShrineDeityCollective:
    collective = _collective(shrine, label, **kwargs)
    _member(collective, f"{label}-甲", 0)
    _member(collective, f"{label}-乙", 1)
    return collective


def _detail(shrine: Shrine) -> dict:
    return ShrineDetailSerializer(shrine).data


def _get_detail(shrine: Shrine):
    return APIClient().get(f"/api/shrines/{shrine.id}/")


def _list_items(resp) -> list[dict]:
    body = resp.json()
    return body.get("results", body) if isinstance(body, dict) else body


@pytest.fixture
def selector_spy(monkeypatch):
    calls: list[list[int]] = []
    real = collective_runtime_selector.fetch_runtime_admitted_collectives

    def spy(shrine_ids):
        ids = list(shrine_ids)
        calls.append(ids)
        return real(ids)

    monkeypatch.setattr(shrine_serializers, "fetch_runtime_admitted_collectives", spy)
    return calls


# ---------- 1-2. field presence / no activation ----------


def test_detail_serializer_declares_deity_collectives():
    assert "deity_collectives" in ShrineDetailSerializer().fields
    assert "deity_collectives" in ShrineDetailSerializer.Meta.fields


def test_no_activation_returns_empty_list():
    shrine = _shrine()
    _admitted(shrine, activate=False)
    assert _detail(shrine)["deity_collectives"] == []


def test_shrine_without_any_collective_returns_empty_list_not_null():
    data = _detail(_shrine())
    assert "deity_collectives" in data
    assert data["deity_collectives"] == []


# ---------- 3. evidence failure ----------


@pytest.mark.parametrize("source_status", [None, "draft", "unverified"])
def test_activated_but_collective_evidence_fails_returns_empty_list(source_status):
    shrine = _shrine()
    collective = _collective(shrine, source_status=source_status)
    _member(collective, "甲")
    assert _detail(shrine)["deity_collectives"] == []


def test_activated_but_collective_not_fact_ready_returns_empty_list():
    shrine = _shrine()
    collective = _admitted(shrine)
    ShrineDeityCollective.objects.filter(pk=collective.pk).update(verification_status="disputed")
    assert _detail(shrine)["deity_collectives"] == []


# ---------- 4. admitted payload ----------


def test_admitted_collective_exact_payload():
    shrine = _shrine()
    collective = _admitted(shrine, "箱根大神")
    deities = {d.display_name: d.pk for d in ShrineDeity.objects.filter(shrine=shrine)}

    assert _detail(shrine)["deity_collectives"] == [
        {
            "id": collective.pk,
            "source_attested_label": "箱根大神",
            "role": "primary",
            "sort_order": 0,
            "member_count": 2,
            "member_count_relation": "exact",
            "member_list_status": "complete",
            "verification_status": "source_confirmed",
            "confidence": "high",
            "memberships": [
                {
                    "deity": {"id": deities["箱根大神-甲"], "display_name": "箱根大神-甲"},
                    "sort_order": 0,
                    "verification_status": "source_confirmed",
                    "confidence": "high",
                },
                {
                    "deity": {"id": deities["箱根大神-乙"], "display_name": "箱根大神-乙"},
                    "sort_order": 1,
                    "verification_status": "source_confirmed",
                    "confidence": "high",
                },
            ],
        }
    ]


# ---------- 5-6. fail-safe ----------


def test_one_bad_membership_omits_whole_collective():
    shrine = _shrine()
    collective = _collective(shrine)
    _member(collective, "甲", 0)
    _member(collective, "乙", 1, source_status="draft")
    assert _detail(shrine)["deity_collectives"] == []


def test_only_admitted_collective_is_returned_among_multiple():
    shrine = _shrine()
    rejected = _collective(shrine, "却下大神", sort_order=0, member_list_status="partial")
    _member(rejected, "却下-甲")
    admitted = _admitted(shrine, "採用大神", sort_order=1)

    data = _detail(shrine)["deity_collectives"]
    assert [c["id"] for c in data] == [admitted.pk]


# ---------- 7. ordering ----------


def test_selector_ordering_is_preserved():
    shrine = _shrine()
    c2 = _admitted(shrine, "C", sort_order=2)
    c0 = _admitted(shrine, "A", sort_order=0)
    c1b = _admitted(shrine, "B2", sort_order=1)
    c1a_later = _admitted(shrine, "B1", sort_order=1)

    data = _detail(shrine)["deity_collectives"]
    assert [c["id"] for c in data] == [c0.pk, c1b.pk, c1a_later.pk, c2.pk]
    for item in data:
        assert [m["sort_order"] for m in item["memberships"]] == [0, 1]


# ---------- 8. existing deities / histories unchanged ----------


def test_existing_deities_and_histories_are_unchanged_and_not_flattened():
    shrine = _shrine()
    collective = _admitted(shrine, "箱根大神")
    source = _source()
    ready_deity = ShrineDeity.objects.create(
        shrine=shrine, display_name="個別祭神", sort_order=5, **_ready()
    )
    ready_deity.sources.add(source)
    disputed_deity = ShrineDeity.objects.create(
        shrine=shrine, display_name="係争祭神", sort_order=6, verification_status="disputed"
    )
    disputed_deity.sources.add(source)
    history = ShrineHistory.objects.create(
        shrine=shrine, history_type="official_origin", title="由緒", content="内容", **_ready()
    )
    history.sources.add(source)

    data = _detail(shrine)

    # Membership 用 ShrineDeity は source を持たないため deities には出ない（従来通り）。
    assert [d["display_name"] for d in data["deities"]] == ["個別祭神", "係争祭神"]
    assert [h["title"] for h in data["histories"]] == ["由緒"]
    assert all("memberships" not in d for d in data["deities"])
    assert [c["id"] for c in data["deity_collectives"]] == [collective.pk]


# ---------- 9. List serializer ----------


def test_list_serializer_does_not_expose_deity_collectives(selector_spy):
    shrine = _shrine()
    _admitted(shrine)

    assert "deity_collectives" not in ShrineListSerializer().fields
    data = ShrineListSerializer([shrine], many=True).data
    assert all("deity_collectives" not in item for item in data)
    assert selector_spy == []


# ---------- 10-12. HTTP ----------


def test_detail_http_get_exposes_deity_collectives(selector_spy):
    shrine = _shrine()
    collective = _admitted(shrine)

    resp = _get_detail(shrine)

    assert resp.status_code == 200
    body = resp.json()
    assert [c["id"] for c in body["deity_collectives"]] == [collective.pk]
    assert selector_spy == [[shrine.pk]]


def test_list_http_get_does_not_expose_deity_collectives(selector_spy):
    for _ in range(3):
        _admitted(_shrine())

    resp = APIClient().get("/api/shrines/")

    assert resp.status_code == 200
    items = _list_items(resp)
    assert len(items) >= 3
    assert all("deity_collectives" not in item for item in items)
    assert selector_spy == []


def test_detail_http_without_admitted_collective_returns_200_and_empty_list():
    shrine = _shrine()
    _admitted(shrine, activate=False)

    resp = _get_detail(shrine)

    assert resp.status_code == 200
    assert resp.json()["deity_collectives"] == []


# ---------- query count ----------


def _detail_query_count(shrine: Shrine) -> int:
    with CaptureQueriesContext(connection) as ctx:
        resp = _get_detail(shrine)
        assert resp.status_code == 200
    return len(ctx.captured_queries)


def test_detail_query_delta_is_bounded_by_selector_contract():
    """selector 追加分は候補0件で +1、候補ありで +5 に固定（Collective / Membership 数に依存しない）。"""
    no_candidate = _shrine()
    small = _shrine()
    _admitted(small, "単一")
    large = _shrine()
    for i in range(4):
        collective = _admitted(large, f"集合{i}", sort_order=i)
        _member(collective, f"集合{i}-丙", 2)

    base = _detail_query_count(no_candidate)
    small_count = _detail_query_count(small)
    large_count = _detail_query_count(large)

    assert small_count - base == 4
    assert large_count == small_count


# ---------- OpenAPI ----------


def _schema_components() -> dict:
    res = APIClient().get(reverse("schema"))
    assert res.status_code == 200
    schema = (
        res.json()
        if "application/json" in res["Content-Type"]
        else json.loads(res.content.decode("utf-8"))
    )
    return (schema.get("components") or {}).get("schemas") or {}


def test_openapi_detail_has_deity_collectives_and_list_does_not():
    components = _schema_components()

    detail_props = components["ShrineDetail"]["properties"]
    assert "deity_collectives" in detail_props
    items = detail_props["deity_collectives"]
    assert items.get("type") == "array"
    ref = items["items"]["$ref"].rsplit("/", 1)[-1]
    collective_props = components[ref]["properties"]
    assert set(collective_props) == {
        "id",
        "source_attested_label",
        "role",
        "sort_order",
        "member_count",
        "member_count_relation",
        "member_list_status",
        "verification_status",
        "confidence",
        "memberships",
    }

    assert "deity_collectives" not in components["ShrineList"]["properties"]
