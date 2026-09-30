"""CollectiveRuntimeActivation（A6-00 Collective Runtime Activation Foundation）の model test。

row の有無だけが rollout state であり、Activation は Runtime admission の十分条件ではない。
本 PR は Foundation のみで、Collective / Membership の意味・Runtime 経路を変えない。
"""

from __future__ import annotations

import importlib

import pytest
from django.db import IntegrityError, migrations, transaction
from django.utils import timezone
from temples.models import (
    CollectiveRuntimeActivation,
    Shrine,
    ShrineDeity,
    ShrineDeityCollective,
    ShrineDeityCollectiveMembership,
    ShrineKnowledgeSource,
)

pytestmark = pytest.mark.django_db


def _create_shrine(name: str = "Activation監査神社") -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )


def _create_collective(shrine: Shrine | None = None, **kwargs) -> ShrineDeityCollective:
    defaults = dict(
        shrine=shrine or _create_shrine(),
        source_attested_label="箱根大神",
        member_count=3,
        member_count_relation="exact",
        member_list_status="complete",
    )
    defaults.update(kwargs)
    return ShrineDeityCollective.objects.create(**defaults)


# --- 1. 作成 / 6. created_at ---


def test_activation_can_be_created_for_collective():
    collective = _create_collective()
    activation = CollectiveRuntimeActivation.objects.create(collective=collective)
    activation.refresh_from_db()

    assert activation.collective_id == collective.id
    assert collective.runtime_activation == activation
    assert str(activation) == f"runtime_activation:{collective.id}"


def test_activation_created_at_is_populated():
    before = timezone.now()
    activation = CollectiveRuntimeActivation.objects.create(collective=_create_collective())
    after = timezone.now()
    activation.refresh_from_db()

    assert activation.created_at is not None
    assert before <= activation.created_at <= after


# --- 2. OneToOne ---


def test_second_activation_for_same_collective_is_rejected():
    collective = _create_collective()
    CollectiveRuntimeActivation.objects.create(collective=collective)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            CollectiveRuntimeActivation.objects.create(collective=collective)

    assert CollectiveRuntimeActivation.objects.filter(collective=collective).count() == 1


# --- 3. 別 Collective ---


def test_different_collectives_each_have_own_activation():
    shrine = _create_shrine()
    first = _create_collective(shrine, source_attested_label="甲大神")
    second = _create_collective(shrine, source_attested_label="乙大神")
    other_shrine_collective = _create_collective(_create_shrine("別神社"))

    for collective in (first, second, other_shrine_collective):
        CollectiveRuntimeActivation.objects.create(collective=collective)

    assert CollectiveRuntimeActivation.objects.count() == 3
    assert {a.collective_id for a in CollectiveRuntimeActivation.objects.all()} == {
        first.id,
        second.id,
        other_shrine_collective.id,
    }


# --- 4. Activation 削除 / 5. Collective 削除 ---


def test_deleting_activation_leaves_collective_intact():
    collective = _create_collective()
    activation = CollectiveRuntimeActivation.objects.create(collective=collective)

    activation.delete()

    collective.refresh_from_db()
    assert ShrineDeityCollective.objects.filter(pk=collective.pk).exists()
    assert collective.source_attested_label == "箱根大神"
    assert not CollectiveRuntimeActivation.objects.filter(collective_id=collective.id).exists()
    assert not hasattr(ShrineDeityCollective.objects.get(pk=collective.pk), "runtime_activation")


def test_deleting_collective_cascades_to_activation():
    collective = _create_collective()
    activation = CollectiveRuntimeActivation.objects.create(collective=collective)

    collective.delete()

    assert not CollectiveRuntimeActivation.objects.filter(pk=activation.pk).exists()


# --- row 不在 = not activated（fixture が作らない限り 0 件） ---


def test_collective_without_activation_row_is_not_activated():
    collective = _create_collective()

    assert CollectiveRuntimeActivation.objects.count() == 0
    assert not hasattr(ShrineDeityCollective.objects.get(pk=collective.pk), "runtime_activation")


def test_activation_model_has_only_contract_fields():
    field_names = {f.name for f in CollectiveRuntimeActivation._meta.get_fields()}
    assert field_names == {"id", "collective", "created_at"}

    collective_field_names = {f.name for f in ShrineDeityCollective._meta.get_fields()}
    for forbidden in ("runtime_active", "is_public", "status", "activated_by", "deactivated_at"):
        assert forbidden not in collective_field_names


# --- 7. 既存 Collective の挙動不変 / 8. 既存 Membership の挙動不変 ---


def test_activation_does_not_mutate_collective_fields_or_validation():
    source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="公式由緒書",
        verification_status="source_confirmed",
        verified_at=timezone.now(),
    )
    collective = _create_collective(
        verification_status="source_confirmed", verified_at=timezone.now(), confidence="high"
    )
    collective.sources.add(source)
    before = ShrineDeityCollective.objects.filter(pk=collective.pk).values().get()

    CollectiveRuntimeActivation.objects.create(collective=collective)

    after = ShrineDeityCollective.objects.filter(pk=collective.pk).values().get()
    assert after == before
    assert list(collective.sources.all()) == [source]
    collective.full_clean()


def test_activation_does_not_mutate_memberships():
    shrine = _create_shrine()
    collective = _create_collective(shrine)
    deity = ShrineDeity.objects.create(shrine=shrine, display_name="瓊瓊杵尊")
    membership = ShrineDeityCollectiveMembership.objects.create(collective=collective, deity=deity)
    before = ShrineDeityCollectiveMembership.objects.filter(pk=membership.pk).values().get()

    CollectiveRuntimeActivation.objects.create(collective=collective)

    after = ShrineDeityCollectiveMembership.objects.filter(pk=membership.pk).values().get()
    assert after == before
    assert list(collective.memberships.all()) == [membership]
    assert membership.sources.count() == 0


# --- Migration は schema-only（RunPython / data 操作なし） ---


@pytest.mark.parametrize(
    "module_path, expected_dependency",
    [
        (
            "temples.migrations.0119_collective_runtime_activation_foundation",
            "0118_shrine_deity_collective_count_relation_constraint",
        ),
        (
            "temples.migrations_nogis.0018_collective_runtime_activation_foundation",
            "0017_shrine_deity_collective_count_relation_constraint",
        ),
    ],
)
def test_migration_is_schema_only(module_path, expected_dependency):
    migration = importlib.import_module(module_path).Migration

    assert migration.dependencies == [("temples", expected_dependency)]
    assert len(migration.operations) == 1
    operation = migration.operations[0]
    assert isinstance(operation, migrations.CreateModel)
    assert operation.name == "CollectiveRuntimeActivation"
    assert {name for name, _ in operation.fields} == {"id", "created_at", "collective"}
    assert not any(
        isinstance(op, (migrations.RunPython, migrations.RunSQL)) for op in migration.operations
    )
