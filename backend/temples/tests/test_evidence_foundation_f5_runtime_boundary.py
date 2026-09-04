"""Evidence Foundation PR-F5: confirms the F5 transport / final qualification
runtime has no Recommendation / Ranking / Concierge / Compass importer.

This mirrors the PR-F4 boundary check（exact file patterns、directory丸ごとの
allowlistはしない）。source textだけを検査するためDB accessを必要としない。
"""

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
_F5_RUNTIME_MARKERS = (
    "normalized_evidence",
    "NormalizedEvidenceV1",
    "transport_traceable",
    "qualify_evidence",
    "evaluate_evidence_qualification",
    "temples.domain.evidence_transport",
    "temples.services.evidence_transport",
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
def test_f5_has_no_recommendation_ranking_concierge_or_compass_importer(path):
    source = path.read_text(encoding="utf-8")
    offenders = tuple(marker for marker in _F5_RUNTIME_MARKERS if marker in source)
    assert offenders == (), f"{path.relative_to(_TEMPLES_DIR)} contains F5 markers: {offenders}"
