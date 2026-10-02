"""A6-02 Step 2: Shrine Detail API の deity_collectives（A6-01 admitted のみ）の test。

admission は temples.services.collective_runtime_selector.fetch_runtime_admitted_collectives が
唯一の authority。View（ShrineViewSet.retrieve）が request ごとに 1 回だけ呼び、結果を
serializer context で ShrineDetailSerializer に渡す。Serializer は表示のみ。
"""

from __future__ import annotations

from unittest import mock

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient
from temples.api.serializers.shrine import ShrineDeityCollectiveSerializer
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


# ---------- helpers ----------

_shrine_seq = {"n": 0}


def _shrine(name: str = "集合詳細神社") -> Shrine:
    _shrine_seq["n"] += 1
    return Shrine.objects.create(
        name_jp=f"{name}{_shrine_seq['n']}",
        address="東京都千代田区1-2-3",
        latitude=35.0 + _shrine_seq["n"] * 0.001,
        longitude=139.0,
    )


def _source(status: str = "source_confirmed") -> ShrineKnowledgeSource:
    return ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="公式由緒書",
        verification_status=status,
        verified_at=timezone.now() if status in ("source_confirmed", "reviewed") else None,
    )


def _ready() -> dict:
    return dict(
        verification_status="source_confirmed", verified_at=timezone.now(), confidence="high"
    )


def _collective(
    shrine: Shrine,
    *,
    label: str = "集合大神",
    sort_order: int = 0,
    activate: bool = True,
    source: bool = True,
    **overrides,
) -> ShrineDeityCollective:
    fields = dict(
        shrine=shrine,
        source_attested_label=label,
        sort_order=sort_order,
        member_count=2,
        member_count_relation="exact",
        member_list_status="complete",
        **_ready(),
    )
    fields.update(overrides)
    collective = ShrineDeityCollective.objects.create(**fields)
    if source:
        collective.sources.add(_source())
    if activate:
        CollectiveRuntimeActivation.objects.create(collective=collective)
    return collective


def _member(
    collective: ShrineDeityCollective,
    name: str,
    *,
    sort_order: int = 0,
    source: ShrineKnowledgeSource | None | bool = True,
    **overrides,
) -> ShrineDeityCollectiveMembership:
    deity = ShrineDeity.objects.create(shrine=collective.shrine, display_name=name)
    fields = dict(collective=collective, deity=deity, sort_order=sort_order, **_ready())
    fields.update(overrides)
    membership = ShrineDeityCollectiveMembership.objects.create(**fields)
    if source is True:
        membership.sources.add(_source())
    elif source:
        membership.sources.add(source)
    return membership


def _valid_collective(shrine: Shrine, **kwargs) -> ShrineDeityCollective:
    collective = _collective(shrine, **kwargs)
    _member(collective, f"{collective.source_attested_label}-甲", sort_order=0)
    _member(collective, f"{collective.source_attested_label}-乙", sort_order=1)
    return collective


def _detail(shrine: Shrine) -> dict:
    resp = APIClient().get(f"/api/shrines/{shrine.id}/")
    assert resp.status_code == 200
    return resp.json()


def _collective_ids(shrine: Shrine) -> list[int]:
    return [c["id"] for c in _detail(shrine)["deity_collectives"]]


# ---------- A. field present ----------


def test_detail_includes_deity_collectives_field():
    shrine = _shrine()
    assert "deity_collectives" in _detail(shrine)


# ---------- B / M. no admitted collective / no knowledge ----------


def test_no_admitted_collective_returns_empty_list():
    shrine = _shrine()
    _valid_collective(shrine, activate=False)
    assert _detail(shrine)["deity_collectives"] == []


def test_detail_without_knowledge_or_collective_is_safe_and_empty():
    body = _detail(_shrine())
    assert body["deity_collectives"] == []
    assert body["deities"] == []
    assert body["histories"] == []


# ---------- C. admitted collective appears exactly once with the selector payload ----------


def test_admitted_collective_appears_exactly_once_with_serializer_payload():
    shrine = _shrine()
    collective = _valid_collective(shrine, label="箱根大神", role="primary")

    body = _detail(shrine)

    [admitted] = collective_runtime_selector.fetch_runtime_admitted_collectives([shrine.pk])[
        shrine.pk
    ]
    assert body["deity_collectives"] == [ShrineDeityCollectiveSerializer(admitted).data]
    assert [c["id"] for c in body["deity_collectives"]] == [collective.pk]
    [payload] = body["deity_collectives"]
    assert list(payload) == [
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
    ]
    assert list(payload["memberships"][0]) == [
        "deity",
        "sort_order",
        "verification_status",
        "confidence",
    ]
    assert list(payload["memberships"][0]["deity"]) == ["id", "display_name"]
    # Source payload は A6-02 Step 2 では出さない。
    assert "sources" not in payload
    assert all("sources" not in m for m in payload["memberships"])


# ---------- D–I. non-admitted collectives never appear ----------


def test_collective_without_activation_does_not_appear():
    shrine = _shrine()
    _valid_collective(shrine, activate=False)
    assert _collective_ids(shrine) == []


@pytest.mark.parametrize("status", ["draft", "unverified", "disputed"])
def test_activated_collective_with_invalid_evidence_does_not_appear(status):
    shrine = _shrine()
    _valid_collective(shrine, verification_status=status, verified_at=None)
    assert _collective_ids(shrine) == []


def test_activated_collective_without_fact_ready_source_does_not_appear():
    shrine = _shrine()
    collective = _valid_collective(shrine, source=False)
    collective.sources.add(_source("unverified"))
    assert _collective_ids(shrine) == []


@pytest.mark.parametrize("status", ["partial", "not_enumerated", "not_determined"])
def test_activated_collective_with_incomplete_member_list_does_not_appear(status):
    shrine = _shrine()
    _valid_collective(shrine, member_list_status=status)
    assert _collective_ids(shrine) == []


def test_activated_collective_without_membership_does_not_appear():
    shrine = _shrine()
    _collective(shrine)
    assert _collective_ids(shrine) == []


def test_membership_without_own_fact_ready_source_hides_collective():
    shrine = _shrine()
    collective = _collective(shrine)
    _member(collective, "甲", sort_order=0)
    _member(collective, "乙", sort_order=1, source=_source("unverified"))
    assert _collective_ids(shrine) == []


def test_membership_without_any_source_hides_collective_even_if_collective_source_ready():
    shrine = _shrine()
    collective = _collective(shrine)
    _member(collective, "甲", sort_order=0)
    _member(collective, "乙", sort_order=1, source=False)
    assert _collective_ids(shrine) == []


def test_membership_resolving_to_other_shrine_deity_hides_collective():
    # save() の same-Shrine 検証を通らない QuerySet.update() 経路で不整合を作る
    # （A6-01 selector test と同じ再現方法）。
    shrine = _shrine()
    other = _shrine("他社")
    collective = _valid_collective(shrine)
    foreign = ShrineDeity.objects.create(shrine=other, display_name="他社の神")
    target = collective.memberships.order_by("id").last()
    ShrineDeityCollectiveMembership.objects.filter(pk=target.pk).update(deity=foreign)

    assert _collective_ids(shrine) == []
    assert _collective_ids(other) == []


def test_invalid_collective_is_hidden_while_valid_sibling_is_shown():
    shrine = _shrine()
    valid = _valid_collective(shrine, label="有効", sort_order=0)
    _valid_collective(shrine, label="無効", sort_order=1, member_list_status="partial")
    assert _collective_ids(shrine) == [valid.pk]


def test_other_shrines_admitted_collectives_are_not_shown():
    shrine = _shrine()
    other = _shrine("他社")
    _valid_collective(other)
    assert _collective_ids(shrine) == []


# ---------- J. ordering is selector-owned ----------


def test_collective_and_membership_ordering_follow_selector():
    shrine = _shrine()
    second = _collective(shrine, label="後", sort_order=2)
    first = _collective(shrine, label="先", sort_order=1)
    for collective in (second, first):
        _member(collective, f"{collective.source_attested_label}-c", sort_order=3)
        _member(collective, f"{collective.source_attested_label}-a", sort_order=1)
        _member(collective, f"{collective.source_attested_label}-b", sort_order=2)

    body = _detail(shrine)

    selected = collective_runtime_selector.fetch_runtime_admitted_collectives([shrine.pk])[
        shrine.pk
    ]
    assert [c["id"] for c in body["deity_collectives"]] == [c.collective_id for c in selected]
    assert [c["id"] for c in body["deity_collectives"]] == [first.pk, second.pk]
    for payload, admitted in zip(body["deity_collectives"], selected):
        assert [m["deity"]["id"] for m in payload["memberships"]] == [
            m.deity_id for m in admitted.memberships
        ]
        assert [m["deity"]["display_name"] for m in payload["memberships"]] == [
            f"{payload['source_attested_label']}-a",
            f"{payload['source_attested_label']}-b",
            f"{payload['source_attested_label']}-c",
        ]


# ---------- K. existing deities / histories unchanged ----------


def test_existing_deities_and_histories_are_unchanged_by_collectives():
    shrine = _shrine()
    source = _source()
    deity = ShrineDeity.objects.create(shrine=shrine, display_name="既存祭神", **_ready())
    deity.sources.add(source)
    history = ShrineHistory.objects.create(
        shrine=shrine, history_type="official_origin", title="由緒", content="内容", **_ready()
    )
    history.sources.add(source)

    before = _detail(shrine)
    collective = _valid_collective(shrine)
    after = _detail(shrine)

    assert [c["id"] for c in after["deity_collectives"]] == [collective.pk]
    # Membership 用の ShrineDeity（source なし）は deities に出ない既存挙動のまま。
    assert after["deities"] == before["deities"]
    assert after["histories"] == before["histories"]
    assert {k: v for k, v in after.items() if k != "deity_collectives"} == {
        k: v for k, v in before.items() if k != "deity_collectives"
    }


# ---------- L. list / nearest do not expose ----------


def test_shrine_list_api_does_not_expose_deity_collectives():
    shrine = _shrine()
    _valid_collective(shrine)

    resp = APIClient().get("/api/shrines/")

    assert resp.status_code == 200
    body = resp.json()
    items = body.get("results", body) if isinstance(body, dict) else body
    assert len(items) >= 1
    for item in items:
        assert "deity_collectives" not in item


def test_list_and_nearest_serializer_have_no_deity_collectives_field():
    from temples.api.serializers.shrine import ShrineListSerializer
    from temples.api.views.shrine import ShrineViewSet

    for action in ("list", "nearest"):
        view = ShrineViewSet()
        view.action = action
        assert view.get_serializer_class() is ShrineListSerializer
    assert "deity_collectives" not in ShrineListSerializer().fields


# ---------- selector is the single admission source, called once per request ----------


def test_detail_calls_selector_exactly_once_with_the_shrine_id():
    shrine = _shrine()
    _valid_collective(shrine)
    real = collective_runtime_selector.fetch_runtime_admitted_collectives

    with mock.patch(
        "temples.api.views.shrine.fetch_runtime_admitted_collectives", side_effect=real
    ) as spy:
        body = _detail(shrine)

    assert spy.call_count == 1
    assert list(spy.call_args.args[0]) == [shrine.pk]
    assert len(body["deity_collectives"]) == 1


def test_detail_output_is_exactly_what_selector_returns():
    # Serializer は selector の結果を写像するだけ: selector が空を返せば DB 上の有効な
    # Collective も出ない（serializer 側で admission を再計算しない）。
    shrine = _shrine()
    _valid_collective(shrine)
    with mock.patch(
        "temples.api.views.shrine.fetch_runtime_admitted_collectives", return_value={}
    ):
        assert _detail(shrine)["deity_collectives"] == []


# ---------- query count ----------


def _detail_query_count(shrine: Shrine) -> int:
    with CaptureQueriesContext(connection) as ctx:
        resp = APIClient().get(f"/api/shrines/{shrine.id}/")
    assert resp.status_code == 200
    return len(ctx.captured_queries)


def test_detail_query_count_does_not_grow_with_collectives_or_memberships():
    small = _shrine()
    _valid_collective(small, label="小")

    large = _shrine()
    for i in range(4):
        collective = _collective(large, label=f"大{i}", sort_order=i)
        for m in range(5):
            _member(collective, f"大{i}-{m}", sort_order=m)

    small_count = _detail_query_count(small)
    large_count = _detail_query_count(large)

    assert len(_detail(large)["deity_collectives"]) == 4
    # selector は候補がある場合 5 クエリの定数（A6-01 契約）。Collective / Membership 数に依らない。
    assert small_count == large_count
