"""Evidence Foundation G1: ShrineGoriyakuAssignment model tests.

SCOPE UPDATE (G1): PR-F3 wrote this file under the premise that
`temples.domain.goriyaku_taxonomy_v1.GORIYAKU_V1_CANONICAL_KEYS` was
intentionally empty, so every positive path was BLOCKED and only
fail-closed negative tests existed. G1's DATA_REVIEW activated the registry
with 18 approved canonical keys, so the positive paths are now exercised
using the official key `goriyaku:misfortune_warding`.

No fake/test canonical key is used anywhere in this file -- every canonical
key here is either one of the 18 approved identities or a deliberately
unapproved value used to prove the fail-closed behaviour.
"""
from __future__ import annotations

from datetime import datetime, timezone as dt_timezone

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from temples.domain.goriyaku_taxonomy_v1 import GORIYAKU_V1_CANONICAL_KEYS
from temples.models import Shrine, ShrineGoriyakuAssignment

pytestmark = pytest.mark.django_db

# Mother Ship approved positive reference key (G1).
POSITIVE_REFERENCE_CANONICAL_KEY = "goriyaku:misfortune_warding"
# A second approved key, used where two distinct valid identities are needed.
SECOND_APPROVED_CANONICAL_KEY = "goriyaku:relationship_bonding"


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
        canonical_key=POSITIVE_REFERENCE_CANONICAL_KEY,
        taxonomy_version="v1",
        lifecycle=ShrineGoriyakuAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=_assigned_at(),
    )
    defaults.update(overrides)
    return ShrineGoriyakuAssignment(**defaults)


def _create(shrine: Shrine, **overrides) -> ShrineGoriyakuAssignment:
    obj = _build(shrine, **overrides)
    obj.full_clean()
    obj.save()
    return obj


# --- Positive path (unblocked by the G1 canonical registry activation) ---


def test_valid_active_assignment_passes_full_clean():
    shrine = _create_shrine()
    obj = _build(shrine)
    obj.full_clean()  # must not raise


def test_valid_active_assignment_can_be_created():
    shrine = _create_shrine()
    assignment = _create(shrine)
    assert assignment.id is not None
    assert assignment.shrine_id == shrine.id
    assert assignment.canonical_key == POSITIVE_REFERENCE_CANONICAL_KEY
    assert assignment.lifecycle == "ACTIVE"


@pytest.mark.parametrize("local_key", sorted(GORIYAKU_V1_CANONICAL_KEYS))
def test_all_eighteen_approved_canonical_keys_are_accepted(local_key):
    shrine = _create_shrine()
    assignment = _create(shrine, canonical_key=f"goriyaku:{local_key}")
    assignment.refresh_from_db()
    assert assignment.canonical_key == f"goriyaku:{local_key}"


def test_valid_provenance_path_persists():
    shrine = _create_shrine()
    assignment = _create(shrine, producer="migration", mechanism="verified_migration")
    assignment.refresh_from_db()
    assert assignment.producer == "migration"
    assert assignment.mechanism == "verified_migration"


@pytest.mark.parametrize(
    "producer",
    ["admin", "curator", "migration", "verified_import", "controlled_automation"],
)
def test_all_five_final_producers_are_accepted_on_a_valid_row(producer):
    shrine = _create_shrine()
    assignment = _create(shrine, producer=producer)
    assert assignment.producer == producer


@pytest.mark.parametrize(
    "mechanism",
    ["manual_review", "source_backed_import", "verified_migration", "controlled_rule"],
)
def test_all_four_final_mechanisms_are_accepted_on_a_valid_row(mechanism):
    shrine = _create_shrine()
    assignment = _create(shrine, mechanism=mechanism)
    assert assignment.mechanism == mechanism


def test_assigned_at_and_created_at_have_different_responsibilities():
    shrine = _create_shrine()
    assignment = _create(shrine, assigned_at=_assigned_at())
    assignment.refresh_from_db()
    assert assignment.assigned_at == _assigned_at()
    assert assignment.created_at is not None
    assert assignment.created_at != assignment.assigned_at


def test_taxonomy_version_is_string_not_integer():
    shrine = _create_shrine()
    assignment = _create(shrine)
    assert assignment.taxonomy_version == "v1"
    assert isinstance(assignment.taxonomy_version, str)


def test_revoked_lifecycle_is_accepted():
    shrine = _create_shrine()
    assignment = _create(shrine, lifecycle=ShrineGoriyakuAssignment.Lifecycle.REVOKED)
    assert assignment.lifecycle == "REVOKED"


# --- Constraint: one ACTIVE per (shrine, canonical_key, taxonomy_version) ---


def test_second_active_row_for_same_shrine_key_version_rejected():
    shrine = _create_shrine()
    _create(shrine, lifecycle=ShrineGoriyakuAssignment.Lifecycle.ACTIVE)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ShrineGoriyakuAssignment.objects.create(
                shrine=shrine,
                canonical_key=POSITIVE_REFERENCE_CANONICAL_KEY,
                taxonomy_version="v1",
                lifecycle=ShrineGoriyakuAssignment.Lifecycle.ACTIVE,
                producer="admin",
                mechanism="manual_review",
                assigned_at=_assigned_at(),
            )


def test_one_shrine_may_hold_several_distinct_active_goriyaku_assignments():
    shrine = _create_shrine()
    _create(shrine, canonical_key=POSITIVE_REFERENCE_CANONICAL_KEY)
    _create(shrine, canonical_key=SECOND_APPROVED_CANONICAL_KEY)
    assert (
        ShrineGoriyakuAssignment.objects.filter(
            shrine=shrine, lifecycle=ShrineGoriyakuAssignment.Lifecycle.ACTIVE
        ).count()
        == 2
    )


def test_multiple_revoked_rows_for_the_same_identity_are_allowed():
    shrine = _create_shrine()
    _create(shrine, lifecycle=ShrineGoriyakuAssignment.Lifecycle.REVOKED)
    _create(shrine, lifecycle=ShrineGoriyakuAssignment.Lifecycle.REVOKED)
    _create(shrine, lifecycle=ShrineGoriyakuAssignment.Lifecycle.ACTIVE)
    assert ShrineGoriyakuAssignment.objects.filter(shrine=shrine).count() == 3


# --- Negative-path: taxonomy validation ---


@pytest.mark.parametrize(
    "canonical_key",
    [
        "goriyaku:enmusubi",
        "goriyaku:love",
        "goriyaku:money",
        "goriyaku:health",
        "goriyaku:anything_plausible_looking",
        "goriyaku:misfortune_ward",
    ],
)
def test_unapproved_canonical_key_is_still_rejected(canonical_key):
    shrine = _create_shrine()
    obj = _build(shrine, canonical_key=canonical_key)
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "unknown_goriyaku_key" in str(excinfo.value)


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
    assert "wrong_namespace" in str(excinfo.value)


def test_japanese_display_label_is_not_a_canonical_key():
    # 厄除け is the display label of goriyaku:misfortune_warding, never an
    # identity the model accepts.
    shrine = _create_shrine()
    obj = _build(shrine, canonical_key="goriyaku:厄除け")
    with pytest.raises(ValidationError):
        obj.full_clean()


def test_unsupported_taxonomy_version_rejected_for_the_version_reason():
    # With an approved canonical key in place, clean() gets past the
    # canonical_key check, so this now proves that taxonomy_version itself
    # is the failing field (PR-F3 could only prove overall rejection).
    shrine = _create_shrine()
    obj = _build(shrine, taxonomy_version="v999")
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "taxonomy_version" in excinfo.value.message_dict
    assert "canonical_key" not in excinfo.value.message_dict


# --- Negative-path: lifecycle ---


def test_invalid_lifecycle_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, lifecycle="SUPERSEDED")  # historyTheme's vocabulary, not goriyaku's
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "lifecycle" in excinfo.value.message_dict


def test_draft_lifecycle_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, lifecycle="DRAFT")
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "lifecycle" in excinfo.value.message_dict


# --- Negative-path: provenance ---


def test_invalid_producer_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, producer="human")  # PR-F1's rejected pre-correction value
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "producer" in excinfo.value.message_dict


def test_invalid_mechanism_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, mechanism="admin_manual")  # PR-F1's rejected pre-correction value
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "mechanism" in excinfo.value.message_dict


# --- Legacy compatibility: no connection to Shrine.goriyaku_tags M2M ---


def test_model_has_no_relation_to_legacy_goriyaku_tags_m2m():
    # ShrineGoriyakuAssignment must not read or write Shrine.goriyaku_tags.
    field_names = {f.name for f in ShrineGoriyakuAssignment._meta.get_fields()}
    assert "goriyaku_tags" not in field_names


def test_creating_an_assignment_does_not_touch_the_legacy_goriyaku_tags_m2m():
    shrine = _create_shrine()
    assert shrine.goriyaku_tags.count() == 0
    _create(shrine)
    shrine.refresh_from_db()
    assert shrine.goriyaku_tags.count() == 0
