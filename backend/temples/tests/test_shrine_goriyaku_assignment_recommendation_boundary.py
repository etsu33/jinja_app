# backend/temples/tests/test_shrine_goriyaku_assignment_recommendation_boundary.py
"""Evidence Foundation PR-F3: confirms ShrineGoriyakuAssignment has no
runtime Recommendation/Ranking/Concierge importer. This does not require DB
access -- it only inspects source text, matching the same boundary check
performed for HistoryThemeAssignment in PR-F2 (including that PR's
allowlist-scope correction: migration filenames are allowlisted by exact
name, not by directory prefix)."""
from __future__ import annotations

from pathlib import Path

import pytest

_TEMPLES_DIR = Path(__file__).resolve().parent.parent

_RECOMMENDATION_RELATED_FILES = [
    "services/concierge_chat.py",
    "services/concierge_chat_ranking.py",
    "services/concierge_chat_candidates.py",
    "services/concierge_chat_extra_condition.py",
    "services/recommendation_reason_v4.py",
    "services/recommendation_score_components.py",
    "services/recommendation_quality_measurement.py",
    "services/shrine_meaning_composer.py",
    "services/concierge_explanation_payload.py",
    "services/action_suggestions.py",
    "domain/consultation_axis.py",
    "domain/need_to_goriyaku_tag_ids.py",
    "management/commands/backfill_goriyaku_tags.py",
]


@pytest.mark.parametrize("relative_path", _RECOMMENDATION_RELATED_FILES)
def test_recommendation_file_does_not_import_shrine_goriyaku_assignment(relative_path):
    path = _TEMPLES_DIR / relative_path
    assert path.exists(), f"expected file not found: {path}"
    text = path.read_text(encoding="utf-8")
    assert "ShrineGoriyakuAssignment" not in text, (
        f"{relative_path} references ShrineGoriyakuAssignment -- PR-F3 must not "
        f"connect the new model to Recommendation/Ranking/Concierge"
    )


def test_no_file_under_temples_imports_shrine_goriyaku_assignment_outside_its_own_module_and_tests():
    # migrations/0103_... and migrations_nogis/0010_... are the two
    # independent, legitimate PR-F3 migration artifacts (dual migration
    # tree, see docs/audit/production-migration-modules-nogis-root-cause.md
    # and the PR-F2 boundary-test correction that established this exact
    # allowlist shape). A migration file defining the model's schema is an
    # expected structural reference, not a runtime Recommendation/Ranking/
    # Concierge integration -- so both, and only these two exact files, are
    # allowed here. This intentionally does not allowlist all of
    # migrations/ or migrations_nogis/, to keep the check scoped.
    allowed_prefixes = (
        "models.py",
        "admin.py",
        "tests/",
        "migrations/0103_goriyaku_evidence_foundation.py",
        "migrations_nogis/0010_shrinegoriyakuassignment.py",
    )
    offenders = []
    for path in _TEMPLES_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        relative = str(path.relative_to(_TEMPLES_DIR))
        if relative.startswith(allowed_prefixes):
            continue
        text = path.read_text(encoding="utf-8")
        if "ShrineGoriyakuAssignment" in text:
            offenders.append(relative)
    assert offenders == [], f"unexpected ShrineGoriyakuAssignment references: {offenders}"
