# backend/temples/tests/test_models_shrine_goriyaku_assignment.py
"""Evidence Foundation PR-F3: ShrineGoriyakuAssignment model tests.

IMPORTANT SCOPE BOUNDARY: PR-F3's canonical key registry
(temples.domain.goriyaku_taxonomy_v1.GORIYAKU_V1_CANONICAL_KEYS) is
intentionally empty (Mother Ship Decision 1 = Option B). Therefore:

- Only negative-path / fail-closed tests are included here.
- Positive-path tests (valid ACTIVE assignment creation, provenance
  persistence through a *valid* row, ACTIVE/REVOKED constraint behavior
  using a real semantic key) are BLOCKED until a later DATA_REVIEW
  populates at least one approved canonical key. They are intentionally
  NOT included in this file. No placeholder/fake canonical key (e.g.
  "goriyaku:test") was added anywhere to work around this -- doing so
  would violate the explicit "do not invent canonical keys" boundary.
"""
from __future__ import annotations

from datetime import datetime, timezone as dt_timezone

import pytest
from django.core.exceptions import ValidationError

from temples.models import Shrine, ShrineGoriyakuAssignment

pytestmark = pytest.mark.django_db


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
        canonical_key="goriyaku:enmusubi",
        taxonomy_version="v1",
        lifecycle=ShrineGoriyakuAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=_assigned_at(),
    )
    defaults.update(overrides)
    return ShrineGoriyakuAssignment(**defaults)


# --- Fail-closed: the registry is empty, so no canonical_key can pass ---


@pytest.mark.parametrize(
    "canonical_key",
    [
        "goriyaku:enmusubi",
        "goriyaku:love",
        "goriyaku:money",
        "goriyaku:health",
        "goriyaku:anything_plausible_looking",
    ],
)
def test_no_canonical_key_is_accepted_while_registry_is_empty(canonical_key):
    shrine = _create_shrine()
    obj = _build(shrine, canonical_key=canonical_key)
    with pytest.raises(ValidationError):
        obj.full_clean()


# --- Negative-path: taxonomy validation ---


def test_blank_canonical_key_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, canonical_key="")
    with pytest.raises(ValidationError):
        obj.full_clean()


def test_wrong_namespace_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, canonical_key="history_theme:restart")
    with pytest.raises(ValidationError):
        obj.full_clean()


def test_unknown_goriyaku_canonical_key_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, canonical_key="goriyaku:enmusubi")
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "unknown_goriyaku_key" in str(excinfo.value)


def test_unsupported_taxonomy_version_rejected():
    # NOTE: clean() checks canonical_key before taxonomy_version and raises
    # on the first failure. Because the registry is currently empty, EVERY
    # canonical_key fails first -- so this test (like all others in this
    # file) can only prove overall rejection, not that taxonomy_version
    # specifically was the failing field. Isolating taxonomy_version's own
    # check (the way PR-F2's HistoryThemeAssignment tests could, by pairing
    # it with one of that model's already-valid canonical keys) is one of
    # the concrete things BLOCKED until DATA_REVIEW provides at least one
    # approved goriyaku canonical key.
    shrine = _create_shrine()
    obj = _build(shrine, taxonomy_version="v999")
    with pytest.raises(ValidationError):
        obj.full_clean()


# --- Negative-path: lifecycle ---


def test_invalid_lifecycle_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, lifecycle="SUPERSEDED")  # historyTheme's vocabulary, not goriyaku's
    with pytest.raises(ValidationError):
        obj.full_clean()


def test_draft_lifecycle_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, lifecycle="DRAFT")
    with pytest.raises(ValidationError):
        obj.full_clean()


# --- Negative-path: provenance ---


def test_invalid_producer_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, producer="human")  # PR-F1's rejected pre-correction value
    with pytest.raises(ValidationError):
        obj.full_clean()


def test_invalid_mechanism_rejected():
    shrine = _create_shrine()
    obj = _build(shrine, mechanism="admin_manual")  # PR-F1's rejected pre-correction value
    with pytest.raises(ValidationError):
        obj.full_clean()


@pytest.mark.parametrize(
    "producer",
    ["admin", "curator", "migration", "verified_import", "controlled_automation"],
)
def test_all_five_final_producers_pass_producer_validation_alone(producer):
    # Confirms the producer *choice* itself is accepted by the field
    # definition (PR-F1 reuse) -- the overall full_clean() still fails on
    # canonical_key (empty registry), proving these two validations are
    # independent, not silently masking each other.
    shrine = _create_shrine()
    obj = _build(shrine, producer=producer)
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "producer" not in excinfo.value.message_dict
    assert "canonical_key" in excinfo.value.message_dict


@pytest.mark.parametrize(
    "mechanism",
    ["manual_review", "source_backed_import", "verified_migration", "controlled_rule"],
)
def test_all_four_final_mechanisms_pass_mechanism_validation_alone(mechanism):
    shrine = _create_shrine()
    obj = _build(shrine, mechanism=mechanism)
    with pytest.raises(ValidationError) as excinfo:
        obj.full_clean()
    assert "mechanism" not in excinfo.value.message_dict
    assert "canonical_key" in excinfo.value.message_dict


# --- Legacy compatibility (structural, no DB dependency on real data) ---


def test_model_has_no_relation_to_legacy_goriyaku_tags_m2m():
    # ShrineGoriyakuAssignment must not read or write Shrine.goriyaku_tags.
    field_names = {f.name for f in ShrineGoriyakuAssignment._meta.get_fields()}
    assert "goriyaku_tags" not in field_names
