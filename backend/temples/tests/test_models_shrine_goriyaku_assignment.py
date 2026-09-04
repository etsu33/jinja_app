# backend/temples/tests/test_models_shrine_goriyaku_assignment.py
"""Evidence Foundation PR-F3b: ShrineGoriyakuAssignment model tests.

PR-F3ではcanonical key registryが意図的に空だったため、本ファイルは
negative-path / fail-closedのみで構成され、positive-path（有効な
assignment作成、制約挙動、REVOKED履歴）はDATA_REVIEW待ちのBLOCKEDと
していた。PR-F3bでProduction canonical master 39件が登録されたため、
それらのBLOCKED項目を実テストとして有効化する。

canonical keyは架空の値を使わず、registryに実在する値のみを使う。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone as dt_timezone

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from temples.models import Shrine, ShrineGoriyakuAssignment

pytestmark = pytest.mark.django_db

VALID_KEY = "goriyaku:enmusubi"
OTHER_VALID_KEY = "goriyaku:yakuyoke"


def _create_shrine(name: str = "Goriyaku監査神社") -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )


def _assigned_at() -> datetime:
    return datetime(2026, 1, 1, tzinfo=dt_timezone.utc)


def _build(shrine: Shrine, **overrides) -> ShrineGoriyakuAssignment:
    defaults = dict(
        shrine=shrine,
        canonical_key=VALID_KEY,
        taxonomy_version="v1",
        lifecycle=ShrineGoriyakuAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=_assigned_at(),
    )
    defaults.update(overrides)
    return ShrineGoriyakuAssignment(**defaults)


# --- Positive path（PR-F3bで有効化） ---


def test_valid_active_assignment_can_be_created():
    shrine = _create_shrine()
    obj = _build(shrine)
    obj.full_clean()
    obj.save()

    saved = ShrineGoriyakuAssignment.objects.get(pk=obj.pk)
    assert saved.shrine_id == shrine.id
    assert saved.canonical_key == VALID_KEY
    assert saved.taxonomy_version == "v1"
    assert saved.lifecycle == ShrineGoriyakuAssignment.Lifecycle.ACTIVE
    assert saved.producer == "admin"
    assert saved.mechanism == "manual_review"
    assert saved.assigned_at == _assigned_at()
    assert saved.created_at is not None


def test_multiple_distinct_canonical_keys_can_be_active_on_one_shrine():
    # goriyakuは1神社が複数ご利益を同時に持てる（historyThemeとは異なる）。
    shrine = _create_shrine()
    for key in (VALID_KEY, OTHER_VALID_KEY, "goriyaku:kaiun"):
        obj = _build(shrine, canonical_key=key)
        obj.full_clean()
        obj.save()

    assert shrine.goriyaku_assignments.filter(
        lifecycle=ShrineGoriyakuAssignment.Lifecycle.ACTIVE
    ).count() == 3


def test_same_canonical_key_can_be_active_on_different_shrines():
    a = _create_shrine("神社A")
    b = _create_shrine("神社B")
    for shrine in (a, b):
        obj = _build(shrine)
        obj.full_clean()
        obj.save()

    assert ShrineGoriyakuAssignment.objects.filter(canonical_key=VALID_KEY).count() == 2


@pytest.mark.parametrize(
    "producer",
    ["admin", "curator", "migration", "verified_import", "controlled_automation"],
)
def test_all_five_final_producers_are_accepted(producer):
    shrine = _create_shrine()
    obj = _build(shrine, producer=producer)
    obj.full_clean()
    obj.save()
    assert ShrineGoriyakuAssignment.objects.get(pk=obj.pk).producer == producer


@pytest.mark.parametrize(
    "mechanism",
    ["manual_review", "source_backed_import", "verified_migration", "controlled_rule"],
)
def test_all_four_final_mechanisms_are_accepted(mechanism):
    shrine = _create_shrine()
    obj = _build(shrine, mechanism=mechanism)
    obj.full_clean()
    obj.save()
    assert ShrineGoriyakuAssignment.objects.get(pk=obj.pk).mechanism == mechanism


# --- Constraint behavior（PR-F3bで有効化） ---


def test_duplicate_active_same_shrine_key_version_is_rejected():
    shrine = _create_shrine()
    first = _build(shrine)
    first.full_clean()
    first.save()

    duplicate = _build(shrine)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            duplicate.save()


def test_revoked_row_does_not_block_a_new_active_row():
    shrine = _create_shrine()
    revoked = _build(shrine, lifecycle=ShrineGoriyakuAssignment.Lifecycle.REVOKED)
    revoked.full_clean()
    revoked.save()

    active = _build(shrine)
    active.full_clean()
    active.save()

    assert shrine.goriyaku_assignments.count() == 2


def test_multiple_revoked_rows_are_retained_as_history():
    shrine = _create_shrine()
    for days in (0, 1, 2):
        obj = _build(
            shrine,
            lifecycle=ShrineGoriyakuAssignment.Lifecycle.REVOKED,
            assigned_at=_assigned_at() + timedelta(days=days),
        )
        obj.full_clean()
        obj.save()

    active = _build(shrine)
    active.full_clean()
    active.save()

    assert shrine.goriyaku_assignments.filter(
        lifecycle=ShrineGoriyakuAssignment.Lifecycle.REVOKED
    ).count() == 3
    assert shrine.goriyaku_assignments.filter(
        lifecycle=ShrineGoriyakuAssignment.Lifecycle.ACTIVE
    ).count() == 1


def test_same_key_different_taxonomy_version_is_not_a_duplicate():
    # 制約はtaxonomy_versionまで含めた3項。ただしv1以外はclean()段階で
    # rejectされるため、DB制約の粒度確認はsave()直接呼び出しで行う。
    shrine = _create_shrine()
    first = _build(shrine)
    first.full_clean()
    first.save()

    other_version = _build(shrine, taxonomy_version="v2")
    other_version.save()  # clean()を通さずDB制約のみを検証

    assert shrine.goriyaku_assignments.count() == 2


# --- Negative path（PR-F3から維持） ---


def test_blank_canonical_key_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, canonical_key="")
    with pytest.raises(ValidationError):
        obj.full_clean()


def test_wrong_namespace_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, canonical_key="history_theme:restart")
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "canonical_key" in excinfo.value.message_dict


def test_unregistered_goriyaku_canonical_key_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, canonical_key="goriyaku:love")
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "unknown_goriyaku_key" in str(excinfo.value)


def test_local_only_legacy_label_key_is_rejected():
    # local dev DBにのみ存在したlegacy概念（地域安泰）はregistry対象外。
    shrine = _create_shrine()
    obj = _build(shrine, canonical_key="goriyaku:chiiki_antai")
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "unknown_goriyaku_key" in str(excinfo.value)


def test_unsupported_taxonomy_version_rejected():
    # PR-F3bでcanonical_keyが有効になったため、taxonomy_version単独の
    # 失敗を初めて分離して確認できる（PR-F3では空registryのため
    # canonical_keyが先に失敗し、分離不能だった）。
    shrine = _create_shrine()
    obj = _build(shrine, taxonomy_version="v999")
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "taxonomy_version" in excinfo.value.message_dict
    assert "canonical_key" not in excinfo.value.message_dict


def test_invalid_lifecycle_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, lifecycle="SUPERSEDED")  # historyTheme語彙、goriyakuでは無効
    with pytest.raises(ValidationError):
        obj.full_clean()


def test_draft_lifecycle_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, lifecycle="DRAFT")
    with pytest.raises(ValidationError):
        obj.full_clean()


def test_invalid_producer_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, producer="human")  # PR-F1で却下された旧値
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "producer" in excinfo.value.message_dict


def test_invalid_mechanism_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, mechanism="admin_manual")  # PR-F1で却下された旧値
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "mechanism" in excinfo.value.message_dict


# --- Legacy compatibility（構造のみ、PR-F3から維持） ---


def test_model_has_no_relation_to_legacy_goriyaku_tags_m2m():
    # ShrineGoriyakuAssignment must not read or write Shrine.goriyaku_tags.
    field_names = {f.name for f in ShrineGoriyakuAssignment._meta.get_fields()}
    assert "goriyaku_tags" not in field_names
