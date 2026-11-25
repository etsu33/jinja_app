# backend/temples/tests/services/test_signal_authority_explanation_alignment_contract.py
"""Recommendation Explanation Alignment Hardening.

Audit follow-up to docs/product/recommendation-signal-authority.md (#2416),
its Contract Tests (#2417), and the Context Override Guard (#2418). This
module fixes the one live Authority Mismatch found while auditing whether
"the Authority that actually drove Recommendation" and "the reason shown
to the user" agree across all Explanation surfaces (reason_facts,
_primary_reason_source, rank_explanation, _explanation_payload.primary_reason,
_explanation_payload.history_context/action_suggestions).

Finding: `history_theme` is classified in the Decision Doc §6 as "Primary
（条件付き）" -- it only has Rank Authority when `consultation_axis`
corresponds to the candidate's `history_theme`
(`history_theme_candidate_boost > 0`). But both `_build_reason_facts()`
(concierge_chat_ranking.py) and `_build_history_context()`
(concierge_explanation_payload.py) independently read
`rec.get("history_theme")` truthiness alone, with no check on whether the
boost actually fired. That let a candidate whose history_theme had ZERO
ranking contribution (axis genuinely does not correspond, boost == 0.0)
be presented as if history_theme were its Primary Reason -- via
reason_facts (the field the main concierge chat card's narrative reads),
_primary_reason_source, rank_explanation, _explanation_payload.primary_reason,
and _explanation_payload.history_context/action_suggestions all at once,
since they all ultimately derive from the same reason_facts SSOT (or, for
history_context, independently duplicated the same unguarded check).

Fix: both call sites now gate on the same already-computed
`history_theme_candidate_boost` value (no new resolver, no ranking
change, no candidate filtering change, no Signal Authority classification
change -- history_theme's Authority remains exactly "Primary（条件付き）"
as already defined; this only makes the implementation match that
existing, already-adopted classification faithfully).

This module does not change production code beyond that single gate
(applied in two closely related places), and does not touch ranking
weight, candidate filtering, or the Primary Reason priority ordering.
"""

from __future__ import annotations

import pytest

from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_ranking import resolve_history_theme_candidate_boost


def _shrine(id_, name, **overrides):
    base = {
        "id": id_,
        "shrine_id": id_,
        "name": name,
        "address": f"テスト所在地{id_}",
        "lat": 35.0,
        "lng": 139.0,
        "distance_m": 1000,
        "goriyaku": "",
        "description": "",
        "goriyaku_tag_ids": [],
        "astro_tags": [],
        "astro_elements": [],
        "astro_priority": 0,
        "visit_style_tags": [],
        "history_theme": "",
        "popular_score": 0.5,
    }
    base.update(overrides)
    return base


@pytest.fixture
def deterministic(settings):
    settings.CONCIERGE_USE_LLM = False


@pytest.mark.django_db
def test_history_theme_reason_is_suppressed_when_axis_does_not_correspond(deterministic):
    """§6: history_theme only has Rank Authority when consultation_axis
    corresponds (boost > 0). When it genuinely does not (boost == 0.0,
    e.g. axis=nature_reset vs theme=勝負, per
    HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS), the candidate's actual driving
    signal (need_tag) must be the one shown across every Explanation
    surface -- not history_theme."""
    assert resolve_history_theme_candidate_boost(consultation_axis="nature_reset", history_theme="勝負") == 0.0

    candidate = _shrine(1, "A", astro_tags=["career"], history_theme="勝負")
    recs = build_chat_recommendations(
        query="", language="ja", candidates=[candidate],
        need_tags=["career"], consultation_axis="nature_reset",
    )
    rec = recs["recommendations"][0]

    assert rec["_primary_reason_source"] == "need_tag"
    fact_types = {f["type"] for f in rec["_reason_facts"]}
    assert "history_theme" not in fact_types

    assert rec["rank_explanation"]["primary_reason_source"] == "need_tag"
    assert rec["_explanation_payload"]["primary_reason"]["type"] == "need_tag"
    assert rec["_explanation_payload"]["history_context"] is None
    # action_suggestions falls back to the theme-less default set, not the
    # (unrelated) 勝負 theme's suggestions.
    action_theme = rec["_explanation_payload"]["action_suggestions"][0].get("history_theme")
    assert action_theme != "勝負"


@pytest.mark.django_db
def test_history_theme_reason_still_surfaces_when_axis_does_correspond(deterministic):
    """Non-regression: when consultation_axis genuinely corresponds to the
    candidate's history_theme (boost > 0), history_theme legitimately has
    Rank Authority and must still be presented as Primary -- this is the
    same scenario PR #2417's Primary Contract test covers, re-asserted
    here for the Explanation-surface consistency angle."""
    assert resolve_history_theme_candidate_boost(consultation_axis="relationship_repair", history_theme="縁") > 0.0

    candidate = _shrine(1, "A", astro_tags=["relationship"], history_theme="縁")
    recs = build_chat_recommendations(
        query="", language="ja", candidates=[candidate],
        need_tags=["relationship"], consultation_axis="relationship_repair",
    )
    rec = recs["recommendations"][0]

    assert rec["_primary_reason_source"] == "history_theme"
    assert rec["rank_explanation"]["primary_reason_source"] == "history_theme"
    assert rec["_explanation_payload"]["primary_reason"]["type"] == "history_theme"
    assert rec["_explanation_payload"]["history_context"] == {
        "theme": "縁", "label": "縁", "tone": "人や機会とのつながりを見直す文脈",
    }


@pytest.mark.django_db
def test_explanation_surfaces_agree_even_when_history_theme_is_present_but_ungrounded(deterministic):
    """All Explanation surfaces (reason_facts / _primary_reason_source /
    rank_explanation / _explanation_payload.primary_reason) must agree
    with each other and with the actual ranking driver, even when a
    candidate happens to carry a history_theme value that had zero
    influence on its ranking."""
    candidate = _shrine(1, "A", astro_tags=["career"], history_theme="勝負")
    recs = build_chat_recommendations(
        query="", language="ja", candidates=[candidate],
        need_tags=["career"], consultation_axis="nature_reset",
    )
    rec = recs["recommendations"][0]

    primary_type_from_facts = next(
        (f["type"] for f in rec["_reason_facts"] if f.get("is_primary")), None,
    )
    assert primary_type_from_facts == "need_tag"
    assert rec["_primary_reason_source"] == primary_type_from_facts
    assert rec["rank_explanation"]["primary_reason_source"] == primary_type_from_facts
    assert rec["_explanation_payload"]["primary_reason"]["type"] == primary_type_from_facts
