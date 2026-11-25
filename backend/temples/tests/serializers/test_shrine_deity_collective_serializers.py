"""A6-02 Step 1: admitted Collective の Read 専用 Serializer の test。

入力は selector の AdmittedCollective / AdmittedCollectiveMembership（frozen dataclass）。
Serializer は写像のみで、DB アクセス・Evidence Gate 再判定・admission 再計算をしない。
"""

from __future__ import annotations

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from temples.api.serializers import shrine as shrine_serializers
from temples.api.serializers.shrine import (
    ShrineDeityCollectiveMembershipSerializer,
    ShrineDeityCollectiveSerializer,
    ShrineDeitySerializer,
    ShrineDetailSerializer,
    ShrineHistorySerializer,
)
from temples.models import Shrine, ShrineDeity, ShrineHistory, ShrineKnowledgeSource
from temples.services.collective_runtime_selector import (
    AdmittedCollective,
    AdmittedCollectiveMembership,
)


def _membership(
    membership_id: int, deity_id: int, name: str, sort_order: int = 0
) -> AdmittedCollectiveMembership:
    return AdmittedCollectiveMembership(
        membership_id=membership_id,
        deity_id=deity_id,
        deity_display_name=name,
        sort_order=sort_order,
        verification_status="source_confirmed",
        confidence="high",
    )


def _collective(**overrides) -> AdmittedCollective:
    fields = dict(
        collective_id=10,
        shrine_id=1,
        source_attested_label="箱根大神",
        role="primary",
        sort_order=0,
        member_count=3,
        member_count_relation="exact",
        member_list_status="complete",
        verification_status="source_confirmed",
        confidence="high",
        memberships=(
            _membership(100, 201, "瓊瓊杵尊", 0),
            _membership(101, 202, "木花咲耶姫命", 1),
            _membership(102, 203, "彦火火出見尊", 2),
        ),
    )
    fields.update(overrides)
    return AdmittedCollective(**fields)


# ---------- 1. payload ----------


def test_admitted_collective_serializes_to_expected_payload():
    assert ShrineDeityCollectiveSerializer(_collective()).data == {
        "id": 10,
        "source_attested_label": "箱根大神",
        "role": "primary",
        "sort_order": 0,
        "member_count": 3,
        "member_count_relation": "exact",
        "member_list_status": "complete",
        "verification_status": "source_confirmed",
        "confidence": "high",
        "memberships": [
            {
                "deity": {"id": 201, "display_name": "瓊瓊杵尊"},
                "sort_order": 0,
                "verification_status": "source_confirmed",
                "confidence": "high",
            },
            {
                "deity": {"id": 202, "display_name": "木花咲耶姫命"},
                "sort_order": 1,
                "verification_status": "source_confirmed",
                "confidence": "high",
            },
            {
                "deity": {"id": 203, "display_name": "彦火火出見尊"},
                "sort_order": 2,
                "verification_status": "source_confirmed",
                "confidence": "high",
            },
        ],
    }


def test_internal_fields_and_sources_are_not_exposed():
    data = ShrineDeityCollectiveSerializer(_collective()).data
    assert "collective_id" not in data
    assert "shrine_id" not in data
    assert "sources" not in data
    for membership in data["memberships"]:
        assert set(membership) == {"deity", "sort_order", "verification_status", "confidence"}


# ---------- 2. nested deity ----------


def test_membership_deity_is_nested_as_id_and_display_name():
    data = ShrineDeityCollectiveMembershipSerializer(_membership(100, 201, "瓊瓊杵尊", 4)).data
    assert data == {
        "deity": {"id": 201, "display_name": "瓊瓊杵尊"},
        "sort_order": 4,
        "verification_status": "source_confirmed",
        "confidence": "high",
    }
    assert "membership_id" not in data
    assert "deity_id" not in data


# ---------- 3. ordering ----------


def test_membership_order_is_preserved_from_input():
    memberships = (
        _membership(3, 303, "丙", 5),
        _membership(1, 301, "甲", 0),
        _membership(2, 302, "乙", 2),
    )
    data = ShrineDeityCollectiveSerializer(_collective(memberships=memberships)).data
    assert [m["deity"]["display_name"] for m in data["memberships"]] == ["丙", "甲", "乙"]


def test_many_collectives_preserve_input_order():
    items = [
        _collective(collective_id=3),
        _collective(collective_id=1),
        _collective(collective_id=2),
    ]
    data = ShrineDeityCollectiveSerializer(items, many=True).data
    assert [c["id"] for c in data] == [3, 1, 2]


# ---------- 4. nullable member_count ----------


def test_member_count_may_be_null():
    data = ShrineDeityCollectiveSerializer(
        _collective(member_count=None, member_count_relation="unspecified")
    ).data
    assert data["member_count"] is None
    assert data["member_count_relation"] == "unspecified"


# ---------- 5. no DB query ----------


@pytest.mark.django_db
def test_serialization_performs_no_db_query():
    items = [_collective(collective_id=i) for i in range(3)]
    with CaptureQueriesContext(connection) as ctx:
        data = ShrineDeityCollectiveSerializer(items, many=True).data
        assert len(data) == 3
    assert ctx.captured_queries == []


# ---------- read-only ----------


def test_serializers_are_read_only():
    for serializer in (
        ShrineDeityCollectiveSerializer(),
        ShrineDeityCollectiveMembershipSerializer(),
    ):
        assert all(field.read_only for field in serializer.fields.values())


def test_new_serializers_are_exported():
    assert "ShrineDeityCollectiveSerializer" in shrine_serializers.__all__
    assert "ShrineDeityCollectiveMembershipSerializer" in shrine_serializers.__all__


# ---------- 6. existing serializers unchanged / A6-02 Step 2 detail connection ----------


def test_shrine_detail_serializer_exposes_deity_collectives_field():
    # A6-02 Step 2: Shrine Detail は deity_collectives を持つ（表示は context 経由の admitted のみ）。
    assert "deity_collectives" in ShrineDetailSerializer().fields


@pytest.mark.django_db
def test_shrine_detail_serializer_renders_only_context_admitted_collectives():
    shrine = Shrine.objects.create(
        name_jp="文脈神社", address="東京都2", latitude=35.0, longitude=139.0
    )
    admitted = _collective(shrine_id=shrine.pk)
    other_shrine_admitted = _collective(collective_id=99, shrine_id=shrine.pk + 1000)
    context = {
        shrine_serializers.ADMITTED_DEITY_COLLECTIVES_CONTEXT_KEY: {
            shrine.pk: [admitted],
            shrine.pk + 1000: [other_shrine_admitted],
        }
    }

    with CaptureQueriesContext(connection) as ctx:
        data = ShrineDetailSerializer(shrine, context=context).data["deity_collectives"]

    assert data == [ShrineDeityCollectiveSerializer(admitted).data]
    # deity_collectives の表示は context 写像のみ（Collective / Membership の追加 query なし）。
    assert not any("deitycollective" in q["sql"].lower() for q in ctx.captured_queries)


@pytest.mark.django_db
def test_shrine_detail_serializer_without_context_returns_empty_collectives():
    # context が無い呼び出しは fail closed で []（model relation へ fallback しない）。
    shrine = Shrine.objects.create(
        name_jp="無文脈神社", address="東京都3", latitude=35.0, longitude=139.0
    )
    assert ShrineDetailSerializer(shrine).data["deity_collectives"] == []


@pytest.mark.django_db
def test_existing_deity_and_history_serializers_are_unchanged():
    shrine = Shrine.objects.create(
        name_jp="既存互換神社", address="東京都1", latitude=35.0, longitude=139.0
    )
    source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="公式",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    deity = ShrineDeity.objects.create(
        shrine=shrine,
        display_name="祭神",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    deity.sources.add(source)
    history = ShrineHistory.objects.create(
        shrine=shrine,
        history_type="official_origin",
        title="由緒",
        content="内容",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    history.sources.add(source)

    deity_data = ShrineDeitySerializer(deity).data
    history_data = ShrineHistorySerializer(history).data

    assert list(deity_data) == [
        "id",
        "display_name",
        "canonical_name",
        "role",
        "sort_order",
        "verification_status",
        "confidence",
        "sources",
    ]
    assert list(history_data) == [
        "id",
        "history_type",
        "title",
        "content",
        "period_text",
        "event_date",
        "sort_order",
        "verification_status",
        "confidence",
        "sources",
    ]
    assert [s["id"] for s in deity_data["sources"]] == [source.pk]
    assert [s["id"] for s in history_data["sources"]] == [source.pk]
