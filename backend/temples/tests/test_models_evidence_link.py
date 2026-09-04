from __future__ import annotations

from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models import NOT_PROVIDED
from django.db.models.deletion import CASCADE, PROTECT, ProtectedError
from django.utils import timezone

from temples.models import (
    EvidenceLink,
    HistoryThemeAssignment,
    Shrine,
    ShrineDeity,
    ShrineHistory,
    ShrineKnowledgeSource,
)

pytestmark = pytest.mark.django_db


def _shrine(name: str = "Evidence Link神社") -> Shrine:
    return Shrine.objects.create(
        name_jp=name,
        address="東京都千代田区1-2-3",
        latitude=35.6812,
        longitude=139.7671,
    )


def _assignment(shrine: Shrine, **overrides) -> HistoryThemeAssignment:
    values = dict(
        shrine=shrine,
        canonical_key="history_theme:restart",
        taxonomy_version="v1",
        lifecycle=HistoryThemeAssignment.Lifecycle.ACTIVE,
        producer="admin",
        mechanism="manual_review",
        assigned_at=datetime(2026, 1, 1, tzinfo=dt_timezone.utc),
    )
    values.update(overrides)
    assignment = HistoryThemeAssignment(**values)
    assignment.full_clean()
    assignment.save()
    return assignment


def _history(shrine: Shrine, title: str = "由緒") -> ShrineHistory:
    return ShrineHistory.objects.create(
        shrine=shrine,
        history_type="official_origin",
        title=title,
        content="根拠となる由緒です。",
    )


def _deity(shrine: Shrine) -> ShrineDeity:
    return ShrineDeity.objects.create(shrine=shrine, display_name="天照大神")


def test_schema_contains_only_f4_fields_with_required_delete_semantics():
    concrete_field_names = {field.name for field in EvidenceLink._meta.concrete_fields}
    assert concrete_field_names == {
        "id",
        "history_theme_assignment",
        "goriyaku_assignment",
        "shrine_history",
        "shrine_deity",
        "rationale",
        "created_at",
    }
    assert (
        EvidenceLink._meta.get_field("history_theme_assignment").remote_field.on_delete is CASCADE
    )
    assert EvidenceLink._meta.get_field("goriyaku_assignment").remote_field.on_delete is CASCADE
    assert EvidenceLink._meta.get_field("shrine_history").remote_field.on_delete is PROTECT
    assert EvidenceLink._meta.get_field("shrine_deity").remote_field.on_delete is PROTECT

    rationale = EvidenceLink._meta.get_field("rationale")
    assert rationale.null is False
    assert rationale.blank is False
    assert rationale.default is NOT_PROVIDED
    assert rationale.max_length is None
    assert EvidenceLink._meta.get_field("created_at").default is timezone.now


def test_valid_history_theme_to_history_link_persists_with_stable_id_and_reverse_relations():
    shrine = _shrine()
    assignment = _assignment(shrine)
    history = _history(shrine)

    link = EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_history=history,
        rationale="この由緒が再出発のthemeを直接裏付けるため。",
    )
    original_id = link.id
    link.refresh_from_db()

    assert link.id == original_id
    assert link.rationale == "この由緒が再出発のthemeを直接裏付けるため。"
    assert link.created_at is not None
    assert assignment.evidence_links.get() == link
    assert history.evidence_links.get() == link


def test_valid_history_theme_to_deity_link_persists():
    shrine = _shrine()
    assignment = _assignment(shrine)
    deity = _deity(shrine)

    link = EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_deity=deity,
        rationale="祭神との関係がthemeの根拠になるため。",
    )

    assert link.id is not None
    assert link.shrine_deity_id == deity.id


@pytest.mark.parametrize(
    "overrides",
    [
        {},
        {"goriyaku_assignment_id": 999999},
    ],
)
def test_assignment_must_be_exactly_one(overrides):
    shrine = _shrine()
    assignment = _assignment(shrine)
    link = EvidenceLink(
        history_theme_assignment=assignment if overrides else None,
        shrine_history=_history(shrine),
        rationale="明示的な根拠。",
        **overrides,
    )
    with pytest.raises(ValidationError):
        link.save()


@pytest.mark.parametrize(
    "include_history,include_deity",
    [(False, False), (True, True)],
)
def test_fact_must_be_exactly_one(include_history, include_deity):
    shrine = _shrine()
    link = EvidenceLink(
        history_theme_assignment=_assignment(shrine),
        shrine_history=_history(shrine) if include_history else None,
        shrine_deity=_deity(shrine) if include_deity else None,
        rationale="明示的な根拠。",
    )
    with pytest.raises(ValidationError):
        link.save()


@pytest.mark.parametrize("rationale", ["", " ", "\n\t"])
def test_rationale_must_be_nonblank_even_on_direct_save(rationale):
    shrine = _shrine()
    link = EvidenceLink(
        history_theme_assignment=_assignment(shrine),
        shrine_history=_history(shrine),
        rationale=rationale,
    )
    with pytest.raises(ValidationError):
        link.save()


def test_cross_shrine_link_is_rejected_without_repair():
    assignment_shrine = _shrine("Assignment神社")
    fact_shrine = _shrine("Fact神社")
    history = _history(fact_shrine)
    link = EvidenceLink(
        history_theme_assignment=_assignment(assignment_shrine),
        shrine_history=history,
        rationale="別神社なので無効。",
    )

    with pytest.raises(ValidationError):
        link.save()
    assert link.shrine_history is history


def test_database_check_constraints_reject_missing_selectors_and_empty_rationale():
    shrine = _shrine()
    assignment = _assignment(shrine)
    history = _history(shrine)
    invalid_rows = [
        dict(shrine_history=history, rationale="根拠"),
        dict(history_theme_assignment=assignment, rationale="根拠"),
        dict(history_theme_assignment=assignment, shrine_history=history, rationale=""),
    ]

    with patch.object(EvidenceLink, "full_clean"):
        for values in invalid_rows:
            with pytest.raises(IntegrityError):
                with transaction.atomic():
                    EvidenceLink.objects.create(**values)


@pytest.mark.parametrize("fact_kind", ["history", "deity"])
def test_database_rejects_duplicate_history_theme_edges_even_with_different_rationale(fact_kind):
    shrine = _shrine()
    assignment = _assignment(shrine)
    fact_field = (
        {"shrine_history": _history(shrine)}
        if fact_kind == "history"
        else {"shrine_deity": _deity(shrine)}
    )
    EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        rationale="最初の根拠。",
        **fact_field,
    )

    with patch.object(EvidenceLink, "full_clean"):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                EvidenceLink.objects.create(
                    history_theme_assignment=assignment,
                    rationale="異なる文でも同一edge。",
                    **fact_field,
                )


def test_all_constraint_names_include_goriyaku_duplicate_guards():
    names = {constraint.name for constraint in EvidenceLink._meta.constraints}
    assert names == {
        "chk_evlink_one_assignment",
        "chk_evlink_one_fact",
        "chk_evlink_rationale_nonempty",
        "uniq_evlink_ht_history",
        "uniq_evlink_ht_deity",
        "uniq_evlink_gori_history",
        "uniq_evlink_gori_deity",
    }


def test_database_introspection_has_both_goriyaku_duplicate_constraints():
    with connection.cursor() as cursor:
        constraints = connection.introspection.get_constraints(cursor, EvidenceLink._meta.db_table)

    assert constraints["uniq_evlink_gori_history"]["unique"] is True
    assert set(constraints["uniq_evlink_gori_history"]["columns"]) == {
        "goriyaku_assignment_id",
        "shrine_history_id",
    }
    assert constraints["uniq_evlink_gori_deity"]["unique"] is True
    assert set(constraints["uniq_evlink_gori_deity"]["columns"]) == {
        "goriyaku_assignment_id",
        "shrine_deity_id",
    }


def test_deleting_link_keeps_assignment_and_fact():
    shrine = _shrine()
    assignment = _assignment(shrine)
    history = _history(shrine)
    source = ShrineKnowledgeSource.objects.create(
        source_type="shrine_official",
        title="保持対象の出典",
    )
    history.sources.add(source)
    link = EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_history=history,
        rationale="削除契約の根拠。",
    )

    link.delete()

    assert HistoryThemeAssignment.objects.filter(pk=assignment.pk).exists()
    assert ShrineHistory.objects.filter(pk=history.pk).exists()
    assert ShrineKnowledgeSource.objects.filter(pk=source.pk).exists()


def test_deleting_assignment_cascades_link_but_keeps_fact():
    shrine = _shrine()
    assignment = _assignment(shrine)
    history = _history(shrine)
    link = EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_history=history,
        rationale="CASCADE契約の根拠。",
    )

    assignment.delete()

    assert not EvidenceLink.objects.filter(pk=link.pk).exists()
    assert ShrineHistory.objects.filter(pk=history.pk).exists()


def test_fact_delete_is_protected_until_link_is_explicitly_deleted():
    shrine = _shrine()
    assignment = _assignment(shrine)
    history = _history(shrine)
    link = EvidenceLink.objects.create(
        history_theme_assignment=assignment,
        shrine_history=history,
        rationale="PROTECT契約の根拠。",
    )

    with pytest.raises(ProtectedError):
        history.delete()
    link.delete()
    history.delete()

    assert not ShrineHistory.objects.filter(pk=history.pk).exists()


def test_superseding_assignment_retains_link_and_does_not_copy_it():
    shrine = _shrine()
    old_assignment = _assignment(shrine)
    history = _history(shrine)
    link = EvidenceLink.objects.create(
        history_theme_assignment=old_assignment,
        shrine_history=history,
        rationale="履歴として保持する根拠。",
    )
    old_assignment.lifecycle = HistoryThemeAssignment.Lifecycle.SUPERSEDED
    old_assignment.save(update_fields=["lifecycle"])
    new_assignment = _assignment(shrine, canonical_key="history_theme:stillness")

    assert EvidenceLink.objects.filter(pk=link.pk).exists()
    assert old_assignment.evidence_links.get() == link
    assert not new_assignment.evidence_links.exists()
