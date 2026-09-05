"""Evidence Foundation G1: confirms the goriyaku canonical registry and the
new alias resolver have no Recommendation / Ranking / Concierge / Compass
runtime wiring.

Mirrors the PR-F4 / PR-F5 boundary checks (exact file patterns, no
whole-directory allowlist). Source text only -- no DB access needed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_TEMPLES_DIR = Path(__file__).resolve().parent.parent
_RUNTIME_PATTERNS = (
    "api/serializers/ranking.py",
    "api/views/ranking.py",
    "api_views_compass.py",
    "services/compass*.py",
    "services/concierge*.py",
    "services/recommendation*.py",
    "services/shrine_meaning_composer.py",
    "services/action_suggestions.py",
    "domain/consultation_axis.py",
    "domain/need_to_goriyaku_tag_ids.py",
    "management/commands/backfill_goriyaku_tags.py",
)
_ALIAS_IMPORT_PATTERN = re.compile(
    r"^\s*(?:from\s+temples\.domain\.goriyaku_alias_v1\b"
    r"|from\s+temples\.domain\s+import\s+[^\n]*\bgoriyaku_alias_v1\b"
    r"|import\s+temples\.domain\.goriyaku_alias_v1\b)",
    re.MULTILINE,
)
_G1_RUNTIME_MARKERS = (
    "goriyaku_alias_v1",
    "GORIYAKU_V1_ALIASES",
    "resolve_goriyaku_alias",
    "GoriyakuAliasResolutionResult",
    "goriyaku_taxonomy_v1",
    "GORIYAKU_V1_CANONICAL_KEYS",
    "validate_goriyaku_v1_canonical_key",
)


def _runtime_files():
    paths = set()
    for pattern in _RUNTIME_PATTERNS:
        paths.update(_TEMPLES_DIR.glob(pattern))
    return sorted(paths)


@pytest.mark.parametrize(
    "path",
    _runtime_files(),
    ids=lambda path: str(path.relative_to(_TEMPLES_DIR)),
)
def test_g1_has_no_recommendation_ranking_concierge_or_compass_importer(path):
    source = path.read_text(encoding="utf-8")
    offenders = tuple(marker for marker in _G1_RUNTIME_MARKERS if marker in source)
    assert offenders == (), f"{path.relative_to(_TEMPLES_DIR)} contains G1 markers: {offenders}"


def test_alias_module_is_not_imported_by_any_runtime_module():
    # The alias registry/resolver is Evidence Foundation-internal in G1: no
    # runtime module imports it yet. Docstring mentions are fine -- only real
    # import statements are checked here.
    offenders = []
    for path in _TEMPLES_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        relative = str(path.relative_to(_TEMPLES_DIR))
        if relative.startswith("tests/") or relative == "domain/goriyaku_alias_v1.py":
            continue
        if _ALIAS_IMPORT_PATTERN.search(path.read_text(encoding="utf-8")):
            offenders.append(relative)
    assert offenders == [], f"unexpected goriyaku_alias_v1 imports: {offenders}"


def test_canonical_taxonomy_module_does_not_import_the_alias_resolver():
    # resolve != validate: the canonical validator must never gain alias
    # lookup. A docstring cross-reference is allowed; an import is not.
    source = (_TEMPLES_DIR / "domain" / "goriyaku_taxonomy_v1.py").read_text(encoding="utf-8")
    assert _ALIAS_IMPORT_PATTERN.search(source) is None


def test_alias_module_does_not_import_django_or_models():
    # The resolver is pure / deterministic / DB-free.
    source = (_TEMPLES_DIR / "domain" / "goriyaku_alias_v1.py").read_text(encoding="utf-8")
    for forbidden in ("import django", "from django", "temples.models"):
        assert forbidden not in source, f"alias resolver must stay DB-free: {forbidden}"
