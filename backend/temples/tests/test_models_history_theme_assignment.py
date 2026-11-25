# backend/temples/tests/test_models_history_theme_assignment.py
from __future__ import annotations

from datetime import datetime, timezone as dt_timezone

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from temples.domain.history_theme_taxonomy_v1 import HISTORY_THEME_V1_CANONICAL_KEYS
from temples.models import HistoryThemeAssignment, Shrine

pytestmark = pytest.mark.django_db


def _create_shrine(name: str = "History Theme監査神社") -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )


def _assigned_at() -> datetime:
    return datetime(2026, 1, 1, tzinfo=dt_timezone.utc)


def _create_assignment(shrine: Shrine, **kwargs) -> HistoryThemeAssignment:
    defaults = dict(
        shrine=shrine,
        canonical_key="history_theme:restart",
        taxonomy_version="v1",
        lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=_assigned_at(),
    )
    defaults.update(kwargs)
    obj = HistoryThemeAssignment(**defaults)
    obj.full_clean()
    obj.save()
    return obj


# --- Model creation ---


def test_valid_active_assignment_can_be_created():
    shrine = _create_shrine()
    assignment = _create_assignment(shrine)
    assert assignment.id is not None
    assert assignment.shrine_id == shrine.id


def test_provenance_fields_persist():
    shrine = _create_shrine()
    assignment = _create_assignment(shrine, producer="migration", mechanism="verified_migration")
    assignment.refresh_from_db()
    assert assignment.producer == "migration"
    assert assignment.mechanism == "verified_migration"


def test_assigned_at_persists():
    shrine = _create_shrine()
    at = _assigned_at()
    assignment = _create_assignment(shrine, assigned_at=at)
    assignment.refresh_from_db()
    assert assignment.assigned_at == at


def test_created_at_exists_and_differs_in_purpose_from_assigned_at():
    shrine = _create_shrine()
    assignment = _create_assignment(shrine, assigned_at=_assigned_at())
    assert assignment.created_at is not None
    # created_at is auto-populated at row-creation time and is not forced to
    # equal the caller-supplied assigned_at value.
    assert assignment.created_at != assignment.assigned_at


def test_canonical_key_persists():
    shrine = _create_shrine()
    assignment = _create_assignment(shrine, canonical_key="history_theme:stillness")
    assignment.refresh_from_db()
    assert assignment.canonical_key == "history_theme:stillness"


def test_taxonomy_version_persists():
    shrine = _create_shrine()
    assignment = _create_assignment(shrine, taxonomy_version="v1")
    assignment.refresh_from_db()
    assert assignment.taxonomy_version == "v1"


def test_taxonomy_version_is_string_not_integer():
    # Mother Ship FINAL contract: taxonomyVersion is a string end-to-end.
    # No integer representation was ever persisted for this model.
    shrine = _create_shrine()
    assignment = _create_assignment(shrine)
    assert isinstance(assignment.taxonomy_version, str)


# --- Taxonomy validation ---


@pytest.mark.parametrize("local_key", sorted(HISTORY_THEME_V1_CANONICAL_KEYS))
def test_all_seven_v1_canonical_keys_accepted(local_key):
    shrine = _create_shrine()
    assignment = _create_assignment(shrine, canonical_key=f"history_theme:{local_key}")
    assert assignment.canonical_key == f"history_theme:{local_key}"


def test_unsupported_namespace_rejected():
    shrine = _create_shrine()
    obj = HistoryThemeAssignment(
        shrine=shrine,
        canonical_key="bogus:restart",
        taxonomy_version="v1",
        lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=_assigned_at(),
    )
    with pytest.raises(ValidationError):
        obj.full_clean()


def test_goriyaku_namespace_rejected():
    shrine = _create_shrine()
    obj = HistoryThemeAssignment(
        shrine=shrine,
        canonical_key="goriyaku:love",
        taxonomy_version="v1",
        lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=_assigned_at(),
    )
    with pytest.raises(ValidationError):
        obj.full_clean()


def test_unknown_history_theme_key_rejected():
    shrine = _create_shrine()
    obj = HistoryThemeAssignment(
        shrine=shrine,
        canonical_key="history_theme:unknown_theme",
        taxonomy_version="v1",
        lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=_assigned_at(),
    )
    with pytest.raises(ValidationError):
        obj.full_clean()


def test_unknown_taxonomy_version_rejected():
    shrine = _create_shrine()
    obj = HistoryThemeAssignment(
        shrine=shrine,
        canonical_key="history_theme:restart",
        taxonomy_version="v999",
        lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=_assigned_at(),
    )
    with pytest.raises(ValidationError):
        obj.full_clean()


def test_blank_semantic_identity_rejected():
    shrine = _create_shrine()
    obj = HistoryThemeAssignment(
        shrine=shrine,
        canonical_key="",
        taxonomy_version="v1",
        lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=_assigned_at(),
    )
    with pytest.raises(ValidationError):
        obj.full_clean()


# --- Lifecycle ---


def test_lifecycle_active_accepted():
    shrine = _create_shrine()
    assignment = _create_assignment(shrine, lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE)
    assert assignment.lifecycle == "ACTIVE"


def test_lifecycle_superseded_accepted():
    shrine = _create_shrine()
    assignment = _create_assignment(shrine, lifecycle=HistoryThemeAssignment.Lifecycle.SUPERSEDED)
    assert assignment.lifecycle == "SUPERSEDED"


def test_invalid_lifecycle_rejected():
    shrine = _create_shrine()
    obj = HistoryThemeAssignment(
        shrine=shrine,
        canonical_key="history_theme:restart",
        taxonomy_version="v1",
        lifecycle="DRAFT",
        producer="admin",
        mechanism="manual_review",
        assigned_at=_assigned_at(),
    )
    with pytest.raises(ValidationError):
        obj.full_clean()


# --- Constraint: one ACTIVE per shrine ---


def test_first_active_for_shrine_allowed():
    shrine = _create_shrine()
    assignment = _create_assignment(shrine, lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE)
    assert assignment.lifecycle == "ACTIVE"


def test_second_active_for_same_shrine_rejected():
    shrine = _create_shrine()
    _create_assignment(
        shrine, canonical_key="history_theme:restart", lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            HistoryThemeAssignment.objects.create(
                shrine=shrine,
                canonical_key="history_theme:stillness",
                taxonomy_version="v1",
                lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE,
                producer="admin",
                mechanism="manual_review",
                assigned_at=_assigned_at(),
            )


def test_multiple_superseded_for_same_shrine_allowed():
    shrine = _create_shrine()
    _create_assignment(
        shrine, canonical_key="history_theme:restart", lifecycle=HistoryThemeAssignment.Lifecycle.SUPERSEDED
    )
    _create_assignment(
        shrine, canonical_key="history_theme:stillness", lifecycle=HistoryThemeAssignment.Lifecycle.SUPERSEDED
    )
    assert (
        HistoryThemeAssignment.objects.filter(
            shrine=shrine, lifecycle=HistoryThemeAssignment.Lifecycle.SUPERSEDED
        ).count()
        == 2
    )


def test_one_active_plus_multiple_superseded_allowed():
    shrine = _create_shrine()
    _create_assignment(
        shrine, canonical_key="history_theme:restart", lifecycle=HistoryThemeAssignment.Lifecycle.SUPERSEDED
    )
    _create_assignment(
        shrine, canonical_key="history_theme:stillness", lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE
    )
    assert HistoryThemeAssignment.objects.filter(shrine=shrine).count() == 2
    assert (
        HistoryThemeAssignment.objects.filter(
            shrine=shrine, lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE
        ).count()
        == 1
    )


def test_different_shrines_may_each_have_an_active_assignment():
    shrine_a = _create_shrine("神社A")
    shrine_b = _create_shrine("神社B")
    _create_assignment(shrine_a, lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE)
    _create_assignment(shrine_b, lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE)
    assert (
        HistoryThemeAssignment.objects.filter(lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE).count() == 2
    )


# --- Identity ---


def test_separate_assignment_rows_get_separate_stable_ids():
    shrine = _create_shrine()
    first = _create_assignment(
        shrine, canonical_key="history_theme:restart", lifecycle=HistoryThemeAssignment.Lifecycle.SUPERSEDED
    )
    second = _create_assignment(
        shrine, canonical_key="history_theme:stillness", lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE
    )
    assert first.id != second.id


def test_superseded_and_later_new_assignment_remain_distinct_records():
    shrine = _create_shrine()
    original = _create_assignment(
        shrine, canonical_key="history_theme:restart", lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE
    )
    original.lifecycle = HistoryThemeAssignment.Lifecycle.SUPERSEDED
    original.full_clean()
    original.save()

    recreated = _create_assignment(
        shrine, canonical_key="history_theme:restart", lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE
    )

    assert original.id != recreated.id
    assert HistoryThemeAssignment.objects.filter(shrine=shrine, canonical_key="history_theme:restart").count() == 2


# --- Legacy compatibility ---


def test_existing_shrine_history_theme_field_remains_unchanged_by_assignment_creation():
    shrine = _create_shrine()
    shrine.history_theme = "再出発"
    shrine.save(update_fields=["history_theme"])

    _create_assignment(shrine, canonical_key="history_theme:stillness")

    shrine.refresh_from_db()
    assert shrine.history_theme == "再出発"


def test_changing_shrine_history_theme_does_not_create_assignment():
    shrine = _create_shrine()
    assert HistoryThemeAssignment.objects.filter(shrine=shrine).count() == 0

    shrine.history_theme = "守り"
    shrine.save(update_fields=["history_theme"])

    assert HistoryThemeAssignment.objects.filter(shrine=shrine).count() == 0
