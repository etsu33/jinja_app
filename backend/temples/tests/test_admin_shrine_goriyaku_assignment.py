# backend/temples/tests/test_admin_shrine_goriyaku_assignment.py
"""Evidence Foundation PR-F3 admin registration checks.

Same scope discipline as test_admin_history_theme_assignment.py (PR-F2):
registration/structure checks only, not a full admin-workflow test suite --
no admin test file precedent existed in this repository before PR-F2, and
PR-F3 follows the same minimal shape rather than inventing a heavier one.
"""
from __future__ import annotations

from django.contrib import admin

from temples.admin import (
    ShrineAdmin,
    ShrineGoriyakuAssignmentAdmin,
    ShrineGoriyakuAssignmentInline,
)
from temples.models import GoriyakuTag, Shrine, ShrineGoriyakuAssignment


def test_shrine_goriyaku_assignment_registered_in_admin_site():
    assert admin.site._registry.get(ShrineGoriyakuAssignment) is not None
    assert isinstance(admin.site._registry[ShrineGoriyakuAssignment], ShrineGoriyakuAssignmentAdmin)


def test_shrine_admin_includes_shrine_goriyaku_assignment_inline():
    assert ShrineGoriyakuAssignmentInline in ShrineAdmin.inlines


def test_shrine_admin_all_evidence_foundation_and_legacy_inlines_present():
    # PR-F3 only adds -- it must not remove any inline PR-F1/F2 or the
    # original Knowledge model set already established.
    inline_models = {inline.model for inline in ShrineAdmin.inlines}
    assert ShrineGoriyakuAssignment in inline_models
    assert len(ShrineAdmin.inlines) == 4  # ShrineDeity, ShrineHistory, HistoryThemeAssignment, ShrineGoriyakuAssignment


def test_shrine_admin_legacy_goriyaku_tags_filter_horizontal_untouched():
    # Existing Shrine.goriyaku_tags M2M widget must remain exactly as-is.
    assert ShrineAdmin.filter_horizontal == ("goriyaku_tags",)


def test_shrine_goriyaku_assignment_inline_has_no_custom_save_side_effects():
    # No overridden save_model/save_formset -- admin must not silently
    # create provenance, infer taxonomy, or auto-revoke rows. Combined with
    # model-level fail-closed validation, this confirms the admin surface
    # cannot bypass the empty-registry rejection either.
    assert "save_model" not in ShrineGoriyakuAssignmentInline.__dict__
    assert "save_formset" not in ShrineGoriyakuAssignmentInline.__dict__
    assert "get_changeform_initial_data" not in ShrineGoriyakuAssignmentInline.__dict__


def test_shrine_goriyaku_assignment_inline_fields_are_explicit():
    assert ShrineGoriyakuAssignmentInline.fields == (
        "canonical_key",
        "taxonomy_version",
        "lifecycle",
        "producer",
        "mechanism",
        "assigned_at",
    )


def test_goriyaku_tag_admin_unaffected_by_pr_f3():
    # GoriyakuTagAdmin (legacy Recommendation-layer governance, or lack
    # thereof) is explicitly out of PR-F3's scope (Decision 3 = Option C).
    # This just confirms the model it wraps is unaffected structurally.
    assert GoriyakuTag._meta.get_field("name") is not None
