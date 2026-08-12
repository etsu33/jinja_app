# backend/temples/tests/test_concierge_primary_reason_unification_contract.py
"""Recommendation Primary Reason Contract Unification.

Covers docs/product/concierge-input-architecture.md Addendum: Primary
Reason Single Source of Truth. Fixes the Mismatch discovered in PR #2407
(Integrated Recommendation Intent Execution Contract): `rank_explanation
.primary_reason_source` and `_explanation_payload.primary_reason.type`
could disagree for the same recommendation, because
`_build_visit_style_primary_reason()` (concierge_explanation_payload.py)
was a second, independent primary-reason resolver bolted onto the
explanation payload, separate from `reason_facts`/`_resolve_primary_reason`
(concierge_chat_ranking.py).

Fix: `visit_style` is now a proper `reason_facts` fact type
(PRIMARY_REASON_PRIORITY), so both systems read the exact same
`rec["_reason_facts"]`/`is_primary` value -- there is exactly one primary
reason resolver.

This PR does not change ranking weights, candidate filtering, or scoring
-- reason_facts/primary_reason are purely descriptive fields computed
after `_score_total`/`score_total_ranked` are already finalized.
"""

from __future__ import annotations

import pytest

from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_ranking import PRIMARY_REASON_PRIORITY


CAREER_QUERY = "転職を考えていて、仕事の転機に向き合いたいです"
REQUESTED_GORIYAKU_ID = 501


def _shrine_match(**overrides):
    base = {
        "name": "Match",
        "distance_m": 500.0,
        "lat": 35.001,
        "lng": 139.001,
        "popular_score": 5.0,
        "astro_tags": ["career"],
        "astro_elements": ["火"],
        "goriyaku_tag_ids": [REQUESTED_GORIYAKU_ID],
        "visit_style_tags": ["quiet"],
        "goriyaku": "",
        "description": "",
        "history_theme": "",
    }
    base.update(overrides)
    return base


def _shrine_quiet_only(**overrides):
    base = {
        "name": "QuietOnly",
        "distance_m": 500.0,
        "lat": 35.002,
        "lng": 139.002,
        "popular_score": 5.0,
        "astro_tags": [],
        "astro_elements": [],
        "goriyaku_tag_ids": [],
        "visit_style_tags": ["quiet"],
        "goriyaku": "",
        "description": "",
        "history_theme": "",
    }
    base.update(overrides)
    return base


@pytest.fixture
def deterministic(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    import temples.domain.need_tags as need

    class FakeNeedExtract:
        def __init__(self):
            self.tags = ["career"]
            self.hits = {"career": ["転職"]}

    monkeypatch.setattr(need, "extract_need_tags", lambda q, max_tags=3: FakeNeedExtract(), raising=True)

    import temples.domain.astrology as astro

    class _Prof:
        sign = "牡羊座"
        element = "火"

    monkeypatch.setattr(astro, "sun_sign_and_element", lambda birthdate: _Prof(), raising=True)
    monkeypatch.setattr(
        astro,
        "element_priority",
        lambda user_elem, shrine_elems: 2 if "火" in (shrine_elems or []) else 0,
        raising=True,
    )
    return None


def _run(candidates, **kwargs):
    kwargs.setdefault("query", CAREER_QUERY)
    kwargs.setdefault("language", "ja")
    kwargs.setdefault("candidates", candidates)
    return build_chat_recommendations(**kwargs)


def _rec_by_name(recs, name):
    for r in recs["recommendations"]:
        if r.get("name") == name:
            return r
    raise AssertionError(f"{name!r} not found: {[r.get('name') for r in recs['recommendations']]}")


# ---------------------------------------------------------------------------
# Task 1/2/3: Inventory sanity -- visit_style is now a first-class fact type
# ---------------------------------------------------------------------------


def test_visit_style_is_a_priority_tier_below_element_above_fallback():
    assert PRIMARY_REASON_PRIORITY["element"] < PRIMARY_REASON_PRIORITY["visit_style"]
    assert PRIMARY_REASON_PRIORITY["visit_style"] < PRIMARY_REASON_PRIORITY["fallback"]
    # Consultation-Meaning-derived and Explicit-Constraint-derived types all
    # outrank visit_style (Rule: Visit Preference is a "fallback primary
    # reason candidate", Task 8).
    for stronger in ("history_theme", "culture_translation", "need_tag", "text_hint", "user_selected_tag", "goriyaku_tag"):
        assert PRIMARY_REASON_PRIORITY[stronger] < PRIMARY_REASON_PRIORITY["visit_style"]


# ---------------------------------------------------------------------------
# Task 13: PR #2407 Mismatch is fixed -- both systems agree
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_no_consultation_match_visit_style_only_becomes_unified_primary_reason(deterministic):
    """Reproduces the exact PR #2407 Mismatch scenario: a candidate with
    zero Consultation Meaning match but a visit_style match. Before this
    fix: rank_explanation.primary_reason_source == "fallback" while
    _explanation_payload.primary_reason.type == "visit_style" (disagreement).
    After this fix: both agree on "visit_style"."""
    recs = _run([_shrine_quiet_only()], visit_preferences=["quiet"])
    rec = recs["recommendations"][0]

    assert rec["_primary_reason_source"] == "visit_style"
    assert rec["rank_explanation"]["primary_reason_source"] == "visit_style"
    assert rec["_explanation_payload"]["primary_reason"]["type"] == "visit_style"

    # Single Source of Truth: all three systems reference the exact same
    # underlying fact (same evidence).
    assert (
        rec["_reason_facts"][0]["evidence"]
        == rec["_explanation_payload"]["primary_reason"]["evidence"]
    )


@pytest.mark.django_db
def test_visit_style_primary_reason_flows_into_explanation_summary(deterministic):
    recs = _run([_shrine_quiet_only()], visit_preferences=["quiet"])
    rec = recs["recommendations"][0]

    from temples.services.concierge_explanations import build_explanation_for_chat_rec

    explanation = build_explanation_for_chat_rec(
        rec, query=CAREER_QUERY, bias=None, birthdate=None, extra_condition=None,
    )
    assert "静か" in explanation["summary"] or "参拝スタイル" in explanation["summary"]


# ---------------------------------------------------------------------------
# Task 15: primary reason must exist in reason_facts (no ungrounded reason)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "candidates,visit_preferences,goriyaku_tag_ids,birthdate",
    [
        ([_shrine_match()], None, None, None),
        ([_shrine_quiet_only()], ["quiet"], None, None),
        ([_shrine_match()], None, [REQUESTED_GORIYAKU_ID], None),
        ([_shrine_match()], None, None, "1990-01-01"),
        ([{"name": "NoMatch", "distance_m": 500.0, "lat": 35.0, "lng": 139.0, "popular_score": 1.0}], None, None, None),
    ],
)
def test_primary_reason_is_always_grounded_in_reason_facts(
    deterministic, candidates, visit_preferences, goriyaku_tag_ids, birthdate,
):
    recs = _run(
        candidates,
        visit_preferences=visit_preferences,
        goriyaku_tag_ids=goriyaku_tag_ids,
        birthdate=birthdate,
    )
    rec = recs["recommendations"][0]
    primary_source = rec["_primary_reason_source"]
    primary_label = rec["_primary_reason_label"]

    fact_keys = {(f["type"], f["label"]) for f in rec["_reason_facts"]}
    assert (primary_source, primary_label) in fact_keys or primary_source == "fallback"


# ---------------------------------------------------------------------------
# Task 16: Full Integration Reason Contract Test
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_full_integration_primary_reason_is_unified_and_consultation_led(deterministic):
    recs = _run(
        [_shrine_match(distance_m=100.0)],
        visit_preferences=["quiet"],
        birthdate="1990-01-01",
        goriyaku_tag_ids=[REQUESTED_GORIYAKU_ID],
    )
    rec = recs["recommendations"][0]

    # Candidate constraint applied / consultation meaning maintained
    assert rec["breakdown"]["matched_need_tags"] == ["career"]
    assert recs["consultation_axis"] == "career_change"

    # visit preference / element / context all present as secondary signal
    visit_style = ((rec.get("breakdown_detail") or {}).get("features") or {}).get("visit_style") or {}
    assert visit_style.get("matched_tags") == ["quiet"]
    assert rec["breakdown"]["score_element"] == 2

    # Primary Reason unified across all three surfaces
    assert rec["_primary_reason_source"] in {"need_tag", "text_hint", "user_selected_tag", "history_theme", "goriyaku_tag"}
    assert rec["rank_explanation"]["primary_reason_source"] == rec["_primary_reason_source"]
    assert rec["_explanation_payload"]["primary_reason"]["type"] == rec["_primary_reason_source"]

    # reason_facts grounds the primary reason
    fact_keys = {(f["type"], f["label"]) for f in rec["_reason_facts"]}
    assert (rec["_primary_reason_source"], rec["_primary_reason_label"]) in fact_keys

    # visible reason text does not contradict (career/consultation led, not
    # a bare visit-style/element-only phrase)
    assert "仕事" in rec["reason"] or "転機" in rec["reason"]


# ---------------------------------------------------------------------------
# Task 17: Conflict Reason Tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_conflict_consultation_plus_visit_preference_meaning_wins_primary(deterministic):
    recs = _run([_shrine_match()], visit_preferences=["quiet"])
    rec = recs["recommendations"][0]
    assert rec["_primary_reason_source"] in {"need_tag", "text_hint", "history_theme", "goriyaku_tag"}
    secondary_types = {f["type"] for f in rec["_reason_facts"] if not f.get("is_primary")}
    assert "visit_style" in secondary_types


@pytest.mark.django_db
def test_conflict_consultation_plus_profile_meaning_wins_primary(deterministic):
    # element only becomes a reason_fact candidate at all in compat mode
    # (astro_bonus_enabled = public_mode == "compat", Task 9) -- need mode
    # never produces an "element" fact, matching existing behavior.
    recs = _run([_shrine_match()], birthdate="1990-01-01", public_mode="compat")
    rec = recs["recommendations"][0]
    assert rec["_primary_reason_source"] in {"need_tag", "text_hint", "history_theme", "goriyaku_tag"}
    secondary_types = {f["type"] for f in rec["_reason_facts"] if not f.get("is_primary")}
    assert "element" in secondary_types


@pytest.mark.django_db
def test_conflict_consultation_plus_constraint_meaning_wins_when_present(deterministic):
    recs = _run([_shrine_match()], goriyaku_tag_ids=[REQUESTED_GORIYAKU_ID])
    rec = recs["recommendations"][0]
    # Consultation Meaning (need_tag/text_hint/history_theme) outranks pure
    # Explicit Constraint (user_selected_tag) per PRIMARY_REASON_PRIORITY.
    assert rec["_primary_reason_source"] in {"need_tag", "text_hint", "history_theme", "goriyaku_tag"}


@pytest.mark.django_db
def test_context_only_never_becomes_primary_meaning_reason(deterministic):
    """Context (distance/location) has no reason_facts type at all -- it
    can never become the primary reason, regardless of how close the
    candidate is."""
    near = {"name": "Near", "distance_m": 10.0, "lat": 35.0, "lng": 139.0, "popular_score": 1.0}
    recs = _run([near])
    rec = recs["recommendations"][0]
    assert rec["_primary_reason_source"] == "fallback"
    for fact in rec["_reason_facts"]:
        assert fact["type"] not in {"distance", "context", "location"}


# ---------------------------------------------------------------------------
# Task 18: No Ranking Change
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_ranking_scores_unaffected_by_primary_reason_unification(deterministic):
    """score_total / _score_total / score_need / score_element /
    score_visit_style(raw) / distance contribution are computed before
    reason_facts and are unaffected by this PR (reason_facts is
    purely descriptive metadata attached afterward)."""
    candidates = [_shrine_match(distance_m=250.0), _shrine_quiet_only(distance_m=250.0)]

    recs = _run(candidates, visit_preferences=["quiet"], birthdate="1990-01-01")
    names = [r["name"] for r in recs["recommendations"]]
    assert names == ["Match", "QuietOnly"]

    match = _rec_by_name(recs, "Match")
    assert match["breakdown"]["score_need"] == 1
    assert match["breakdown"]["score_element"] == 2
    visit_style = ((match.get("breakdown_detail") or {}).get("features") or {}).get("visit_style") or {}
    assert visit_style.get("raw") == 1
    assert match["_score_total"] > 0
