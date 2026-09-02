# backend/temples/tests/test_history_theme_assignment_recommendation_boundary.py
"""Evidence Foundation PR-F2: confirms HistoryThemeAssignment has no runtime
Recommendation/Ranking/Concierge importer. This does not require DB access --
it only inspects source text, matching the same boundary check performed
manually during PR-F1/PR-F2 development."""
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
]


@pytest.mark.parametrize("relative_path", _RECOMMENDATION_RELATED_FILES)
def test_recommendation_file_does_not_import_history_theme_assignment(relative_path):
    path = _TEMPLES_DIR / relative_path
    assert path.exists(), f"expected file not found: {path}"
    text = path.read_text(encoding="utf-8")
    assert "HistoryThemeAssignment" not in text, (
        f"{relative_path} references HistoryThemeAssignment -- PR-F2 must not "
        f"connect the new model to Recommendation/Ranking/Concierge"
    )


def test_no_file_under_temples_imports_history_theme_assignment_outside_its_own_module_and_tests():
    # migrations/0102_... and migrations_nogis/0009_... are the two
    # independent, legitimate PR-F2 migration artifacts (see
    # docs/audit/production-migration-modules-nogis-root-cause.md for why
    # this repository has two parallel, independently-maintained `temples`
    # migration lineages). A migration file defining the model's schema is
    # an expected structural reference, not a runtime Recommendation/
    # Ranking/Concierge integration -- so both, and only these two exact
    # files, are allowed here. This intentionally does not allowlist all of
    # migrations/ or migrations_nogis/, to keep the check scoped.
    allowed_prefixes = (
        "models.py",
        "admin.py",
        "tests/",
        "migrations/0102_history_theme_assignment_foundation.py",
        "migrations_nogis/0009_historythemeassignment.py",
    )
    offenders = []
    for path in _TEMPLES_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        relative = str(path.relative_to(_TEMPLES_DIR))
        if relative.startswith(allowed_prefixes):
            continue
        text = path.read_text(encoding="utf-8")
        if "HistoryThemeAssignment" in text:
            offenders.append(relative)
    assert offenders == [], f"unexpected HistoryThemeAssignment references: {offenders}"
