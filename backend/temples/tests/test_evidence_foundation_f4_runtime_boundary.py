from __future__ import annotations

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
)
_F4_RUNTIME_MARKERS = (
    "EvidenceLink",
    "prepare_f4_qualification",
    "temples.domain.evidence_link",
    "temples.services.evidence_foundation",
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
def test_f4_has_no_recommendation_ranking_concierge_or_compass_importer(path):
    source = path.read_text(encoding="utf-8")
    offenders = tuple(marker for marker in _F4_RUNTIME_MARKERS if marker in source)
    assert offenders == (), f"{path.relative_to(_TEMPLES_DIR)} contains F4 markers: {offenders}"
