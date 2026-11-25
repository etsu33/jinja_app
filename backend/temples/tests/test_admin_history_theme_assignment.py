# backend/temples/tests/test_admin_history_theme_assignment.py
"""Evidence Foundation PR-F2 admin registration checks.

No existing admin test file precedent exists in this repository (confirmed by
inspection before writing this file), so this stays intentionally small:
registration/structure checks only, not a full admin-workflow test suite.
"""
from __future__ import annotations

from django.contrib import admin

from temples.admin import HistoryThemeAssignmentAdmin, HistoryThemeAssignmentInline, ShrineAdmin
from temples.models import HistoryThemeAssignment, Shrine, ShrineDeity, ShrineHistory


def test_history_theme_assignment_registered_in_admin_site():
    assert admin.site._registry.get(HistoryThemeAssignment) is not None
    assert isinstance(admin.site._registry[HistoryThemeAssignment], HistoryThemeAssignmentAdmin)


def test_shrine_admin_includes_history_theme_assignment_inline():
    assert HistoryThemeAssignmentInline in ShrineAdmin.inlines


def test_shrine_admin_legacy_inlines_still_present():
    # Legacy Shrine admin structure (ShrineDeityInline / ShrineHistoryInline)
    # must remain intact -- PR-F2 only adds, never removes.
    inline_models = {inline.model for inline in ShrineAdmin.inlines}
    assert ShrineDeity in inline_models
    assert ShrineHistory in inline_models
    assert HistoryThemeAssignment in inline_models


def test_shrine_admin_legacy_history_theme_field_still_visible():
    # Existing Shrine.history_theme compatibility field must remain visible
    # in the admin list/filter exactly as before this PR.
    assert "history_theme" in ShrineAdmin.list_display
    assert "history_theme" in ShrineAdmin.list_filter


def test_history_theme_assignment_inline_has_no_custom_save_side_effects():
    # No overridden save_model/save_formset -- admin must not silently
    # create provenance, infer taxonomy, or auto-supersede.
    assert "save_model" not in HistoryThemeAssignmentInline.__dict__
    assert "save_formset" not in HistoryThemeAssignmentInline.__dict__
    assert "get_changeform_initial_data" not in HistoryThemeAssignmentInline.__dict__


def test_history_theme_assignment_inline_fields_are_explicit():
    assert HistoryThemeAssignmentInline.fields == (
        "canonical_key",
        "taxonomy_version",
        "lifecycle",
        "producer",
        "mechanism",
        "assigned_at",
    )
