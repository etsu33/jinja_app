"""A6-01 Collective Runtime selector / admission の test。"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from django.core.management import call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from temples.models import (
    CollectiveRuntimeActivation,
    Shrine,
    ShrineDeity,
    ShrineDeityCollective,
    ShrineDeityCollectiveMembership,
    ShrineKnowledgeSource,
)
from temples.services.collective_runtime_selector import (
    AdmittedCollective,
    fetch_runtime_admitted_collectives,
)

pytestmark = pytest.mark.django_db


# ---------- helpers ----------

_shrine_seq = {"n": 0}


def _shrine(name: str = "選定神社") -> Shrine:
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
    source: ShrineKnowledgeSource | None | bool = True,
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
    if source is True:
        collective.sources.add(_source())
    elif source:
        collective.sources.add(source)
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


def _admitted_ids(shrine: Shrine) -> list[int]:
    return [
        c.collective_id for c in fetch_runtime_admitted_collectives([shrine.pk]).get(shrine.pk, [])
    ]


# ---------- 1. activation ----------


def test_no_activation_row_is_excluded():
    shrine = _shrine()
    _valid_collective(shrine, activate=False)
    assert fetch_runtime_admitted_collectives([shrine.pk]) == {}


# ---------- 2. admitted ----------


def test_activated_usable_complete_collective_is_admitted_with_structure():
    shrine = _shrine()
    collective = _valid_collective(shrine, label="箱根大神", role="primary", member_count=2)

    result = fetch_runtime_admitted_collectives([shrine.pk])

    assert list(result) == [shrine.pk]
    [admitted] = result[shrine.pk]
    assert isinstance(admitted, AdmittedCollective)
    assert admitted.collective_id == collective.pk
    assert admitted.shrine_id == shrine.pk
    assert admitted.source_attested_label == "箱根大神"
    assert admitted.role == "primary"
    assert admitted.sort_order == 0
    assert admitted.member_count == 2
    assert admitted.member_count_relation == "exact"
    assert admitted.member_list_status == "complete"
    assert admitted.verification_status == "source_confirmed"
    assert admitted.confidence == "high"
    assert [m.deity_display_name for m in admitted.memberships] == ["箱根大神-甲", "箱根大神-乙"]
    first = admitted.memberships[0]
    membership = ShrineDeityCollectiveMembership.objects.get(pk=first.membership_id)
    assert first.deity_id == membership.deity_id
    assert first.sort_order == 0
    assert first.verification_status == "source_confirmed"
    assert first.confidence == "high"


def test_reviewed_status_is_admitted_like_existing_evidence_gate():
    shrine = _shrine()
    collective = _collective(shrine, verification_status="reviewed")
    _member(collective, "甲", verification_status="reviewed", source=_source("reviewed"))
    assert _admitted_ids(shrine) == [collective.pk]


# ---------- 3-4. Collective evidence ----------


@pytest.mark.parametrize("status", ["draft", "unverified", "disputed", "outdated", "rejected"])
def test_collective_evidence_not_ready_is_excluded(status):
    shrine = _shrine()
    collective = _valid_collective(shrine)
    ShrineDeityCollective.objects.filter(pk=collective.pk).update(verification_status=status)
    assert fetch_runtime_admitted_collectives([shrine.pk]) == {}


def test_collective_without_any_source_is_excluded():
    shrine = _shrine()
    collective = _collective(shrine, source=False)
    _member(collective, "甲")
    assert fetch_runtime_admitted_collectives([shrine.pk]) == {}


@pytest.mark.parametrize("status", ["draft", "unverified", "disputed", "outdated", "rejected"])
def test_collective_without_fact_ready_source_is_excluded(status):
    shrine = _shrine()
    collective = _collective(shrine, source=_source(status))
    _member(collective, "甲")
    assert fetch_runtime_admitted_collectives([shrine.pk]) == {}


def test_high_confidence_does_not_substitute_for_evidence():
    shrine = _shrine()
    collective = _collective(shrine, source=False, confidence="high")
    _member(collective, "甲")
    assert fetch_runtime_admitted_collectives([shrine.pk]) == {}


# ---------- 5-6. structure ----------


@pytest.mark.parametrize("status", ["partial", "not_enumerated", "not_determined"])
def test_member_list_status_not_complete_is_excluded(status):
    shrine = _shrine()
    _valid_collective(shrine, member_list_status=status)
    assert fetch_runtime_admitted_collectives([shrine.pk]) == {}


def test_zero_memberships_is_excluded():
    shrine = _shrine()
    _collective(shrine)
    assert fetch_runtime_admitted_collectives([shrine.pk]) == {}


# ---------- 7-9. Membership evidence (independent, fail-safe at Collective boundary) ----------


@pytest.mark.parametrize("status", ["draft", "unverified", "disputed", "outdated", "rejected"])
def test_one_membership_evidence_failing_excludes_whole_collective(status):
    shrine = _shrine()
    collective = _valid_collective(shrine)
    bad = collective.memberships.order_by("id").last()
    ShrineDeityCollectiveMembership.objects.filter(pk=bad.pk).update(verification_status=status)
    assert fetch_runtime_admitted_collectives([shrine.pk]) == {}


def test_membership_without_any_source_excludes_whole_collective():
    shrine = _shrine()
    collective = _collective(shrine)
    _member(collective, "甲")
    _member(collective, "乙", sort_order=1, source=False)
    assert fetch_runtime_admitted_collectives([shrine.pk]) == {}


def test_membership_without_fact_ready_source_excludes_whole_collective():
    shrine = _shrine()
    collective = _collective(shrine)
    _member(collective, "甲")
    _member(collective, "乙", sort_order=1, source=_source("draft"))
    assert fetch_runtime_admitted_collectives([shrine.pk]) == {}


def test_collective_source_is_not_inherited_by_membership():
    shrine = _shrine()
    shared = _source()
    collective = _collective(shrine, source=shared)
    _member(collective, "甲", source=False)
    assert collective.sources.filter(pk=shared.pk).exists()
    assert fetch_runtime_admitted_collectives([shrine.pk]) == {}


def test_collective_source_usable_but_membership_source_not_usable_is_excluded():
    shrine = _shrine()
    collective = _collective(shrine, source=_source("reviewed"))
    _member(collective, "甲", source=_source("unverified"))
    assert fetch_runtime_admitted_collectives([shrine.pk]) == {}


def test_membership_sharing_the_same_ready_source_is_admitted():
    shrine = _shrine()
    shared = _source()
    collective = _collective(shrine, source=shared)
    _member(collective, "甲", source=shared)
    assert _admitted_ids(shrine) == [collective.pk]


# ---------- 6. unresolved deity / 10. same-Shrine ----------


def test_unresolved_membership_deity_excludes_whole_collective():
    # Django の PostgreSQL FK は DEFERRABLE INITIALLY DEFERRED。test transaction は commit
    # されないため、存在しない deity_id を持つ Membership を再現できる。
    shrine = _shrine()
    collective = _valid_collective(shrine)
    target = collective.memberships.order_by("id").last()
    missing_id = (
        ShrineDeity.objects.order_by("-id").values_list("id", flat=True).first() or 0
    ) + 1000
    ShrineDeityCollectiveMembership.objects.filter(pk=target.pk).update(deity_id=missing_id)
    try:
        assert fetch_runtime_admitted_collectives([shrine.pk]) == {}
    finally:
        # teardown 時の deferred FK check を通すため元の参照へ戻す。
        ShrineDeityCollectiveMembership.objects.filter(pk=target.pk).update(
            deity_id=target.deity_id
        )


def test_cross_shrine_membership_excludes_whole_collective():
    # save() の same-Shrine 検証を通らない QuerySet.update() 経路で不整合を作る。
    shrine = _shrine()
    other = _shrine("別神社")
    collective = _valid_collective(shrine)
    foreign = ShrineDeity.objects.create(shrine=other, display_name="他社の神")
    target = collective.memberships.order_by("id").last()
    ShrineDeityCollectiveMembership.objects.filter(pk=target.pk).update(deity=foreign)

    assert fetch_runtime_admitted_collectives([shrine.pk, other.pk]) == {}


# ---------- 11. independence ----------


def test_invalid_collective_does_not_suppress_valid_collective_on_same_shrine():
    shrine = _shrine()
    valid = _valid_collective(shrine, label="有効大神", sort_order=1)
    invalid = _valid_collective(shrine, label="無効大神", sort_order=0)
    bad = invalid.memberships.order_by("id").first()
    ShrineDeityCollectiveMembership.objects.filter(pk=bad.pk).update(verification_status="draft")
    _valid_collective(shrine, label="未承認大神", activate=False)

    assert _admitted_ids(shrine) == [valid.pk]


def test_multiple_shrines_are_grouped_and_evaluated_independently():
    shrine_a, shrine_b, shrine_c = _shrine(), _shrine(), _shrine()
    a = _valid_collective(shrine_a)
    b = _valid_collective(shrine_b)
    _valid_collective(shrine_c, member_list_status="partial")

    result = fetch_runtime_admitted_collectives([shrine_a.pk, shrine_b.pk, shrine_c.pk])

    assert set(result) == {shrine_a.pk, shrine_b.pk}
    assert [c.collective_id for c in result[shrine_a.pk]] == [a.pk]
    assert [c.collective_id for c in result[shrine_b.pk]] == [b.pk]


def test_other_shrines_collectives_are_not_returned():
    shrine, other = _shrine(), _shrine()
    _valid_collective(other)
    assert fetch_runtime_admitted_collectives([shrine.pk]) == {}


# ---------- 12-13. ordering ----------


def test_collective_ordering_is_sort_order_then_id():
    shrine = _shrine()
    c2 = _valid_collective(shrine, label="C", sort_order=2)
    b1 = _valid_collective(shrine, label="A", sort_order=1)
    a0 = _valid_collective(shrine, label="Z", sort_order=0)
    b1_later = _valid_collective(shrine, label="B", sort_order=1)

    assert _admitted_ids(shrine) == [a0.pk, b1.pk, b1_later.pk, c2.pk]


def test_membership_ordering_is_sort_order_then_id():
    shrine = _shrine()
    collective = _collective(shrine)
    m_late = _member(collective, "ん", sort_order=2)
    m_first_1 = _member(collective, "わ", sort_order=1)
    m_zero = _member(collective, "を", sort_order=0)
    m_second_1 = _member(collective, "あ", sort_order=1)

    [admitted] = fetch_runtime_admitted_collectives([shrine.pk])[shrine.pk]
    assert [m.membership_id for m in admitted.memberships] == [
        m_zero.pk,
        m_first_1.pk,
        m_second_1.pk,
        m_late.pk,
    ]


# ---------- 14. empty input ----------


@pytest.mark.parametrize("shrine_ids", [[], (), set()])
def test_empty_shrine_ids_returns_empty_without_queries(shrine_ids):
    with CaptureQueriesContext(connection) as ctx:
        assert fetch_runtime_admitted_collectives(shrine_ids) == {}
    assert len(ctx.captured_queries) == 0


def test_no_candidates_uses_single_query():
    shrine = _shrine()
    _valid_collective(shrine, activate=False)
    with CaptureQueriesContext(connection) as ctx:
        assert fetch_runtime_admitted_collectives([shrine.pk]) == {}
    assert len(ctx.captured_queries) == 1


# ---------- 15. query count ----------


def _count_queries(shrine_ids: list[int]) -> tuple[int, dict]:
    with CaptureQueriesContext(connection) as ctx:
        result = fetch_runtime_admitted_collectives(shrine_ids)
    return len(ctx.captured_queries), result


def test_query_count_does_not_grow_with_shrines_collectives_or_memberships():
    small = _shrine()
    _valid_collective(small)
    small_count, small_result = _count_queries([small.pk])

    shrines = [_shrine() for _ in range(4)]
    for shrine in shrines:
        for i in range(3):
            collective = _valid_collective(shrine, label=f"集合{i}", sort_order=i)
            _member(collective, f"集合{i}-丙", sort_order=2)
    large_count, large_result = _count_queries([s.pk for s in shrines] + [small.pk])

    assert len(small_result[small.pk]) == 1
    assert sum(len(v) for v in large_result.values()) == 13
    assert small_count == large_count == 5


# ---------- read-only ----------


def test_selector_performs_no_writes():
    shrine = _shrine()
    _valid_collective(shrine)
    with CaptureQueriesContext(connection) as ctx:
        fetch_runtime_admitted_collectives([shrine.pk])
    assert all(q["sql"].lstrip().upper().startswith("SELECT") for q in ctx.captured_queries)


# ---------- production-equivalent (A-5b seed + A6 activation seed) ----------


def test_production_equivalent_a5b_activation_admits_six_collectives():
    """repository 正本 seed を既存 command で適用した状態で、6 Collective / 23 Membership が admit される。"""
    data_dir = Path(__file__).resolve().parents[1] / "data"
    a5b_path = data_dir / "knowledge_seeds" / "a5b_collective_pattern_b_seed.json"
    activation_path = data_dir / "runtime_rollout" / "a6_collective_runtime_activation_v1.json"
    shrine_ids = []
    for block in json.loads(a5b_path.read_text(encoding="utf-8"))["shrines"]:
        shrine = Shrine.objects.create(
            name_jp=block["shrine_ref"]["name_jp"],
            address=block["shrine_ref"]["address"],
            latitude=35.0,
            longitude=139.0,
        )
        shrine_ids.append(shrine.pk)
        for collective in block["collectives"]:
            for membership in collective["memberships"]:
                ShrineDeity.objects.create(
                    shrine=shrine, display_name=membership["deity_ref"]["display_name"]
                )
    quiet = dict(stdout=io.StringIO(), stderr=io.StringIO())
    call_command("import_shrine_knowledge", str(a5b_path), **quiet)

    assert fetch_runtime_admitted_collectives(shrine_ids) == {}

    call_command("activate_collective_runtime", str(activation_path), **quiet)
    result = fetch_runtime_admitted_collectives(shrine_ids)

    admitted = [c for shrine_id in shrine_ids for c in result.get(shrine_id, [])]
    assert len(admitted) == 6
    assert sum(len(c.memberships) for c in admitted) == 23
    assert {c.source_attested_label for c in admitted} == {
        "箱根大神",
        "寒川大明神",
        "二荒山大神",
        "住吉五所大神",
        "忌部五部神",
        "王子大神",
    }
