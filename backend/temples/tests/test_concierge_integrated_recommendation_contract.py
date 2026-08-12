# backend/temples/tests/test_concierge_integrated_recommendation_contract.py
"""Integrated Recommendation Intent Execution Contract.

Covers docs/product/concierge-input-architecture.md Addendum: Integrated
Recommendation Flow. Ties together L1 Consultation, L2 Visit Preference,
L3-A Personal Profile, L3-B Explicit Constraint, and L3-C Recommendation
Context (PR #2397/#2398/#2399/#2405/#2406) into one tested Contract:

    Raw Consultation -> Interpretation -> Candidate Constraint -> Ranking
    -> Recommendation Reason

Core Principle under test: Consultation Meaning is the primary
recommendation axis. Lower-level Signals (L2/L3) adjust ranking but never
replace L1 meaning (need_tags / consultation_axis).

This PR does not change any ranking weight, candidate filtering semantics,
or Recommendation Reason text-generation logic -- it is a test + audit PR
building on existing, unchanged behavior.
"""

from __future__ import annotations

import pytest

from temples.services.concierge_chat import build_chat_recommendations


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

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


def _shrine_other(**overrides):
    base = {
        "name": "Other",
        "distance_m": 500.0,
        "lat": 35.002,
        "lng": 139.002,
        "popular_score": 5.0,
        "astro_tags": [],
        "astro_elements": [],
        "goriyaku_tag_ids": [],
        "visit_style_tags": [],
        "goriyaku": "",
        "description": "",
        "history_theme": "",
    }
    base.update(overrides)
    return base


@pytest.fixture
def deterministic(monkeypatch, settings):
    """Deterministic path: LLM off, real need_tags mocked to a single
    stable tag ('career'), real (unmocked) consultation_axis/astro/goriyaku/
    visit_style resolution -- same fixture pattern as
    test_concierge_need_contract.py / test_concierge_visit_preference_contract.py."""
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
    raise AssertionError(f"{name!r} not found in recommendations: {[r.get('name') for r in recs['recommendations']]}")


# ---------------------------------------------------------------------------
# Task 12: Integrated Contract Tests -- combination matrix
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_l1_only(deterministic):
    recs = _run([_shrine_match(), _shrine_other()])
    top = recs["recommendations"][0]
    assert top["name"] == "Match"
    assert top["breakdown"]["matched_need_tags"] == ["career"]
    assert recs["consultation_axis"] == "career_change"


@pytest.mark.django_db
def test_l1_plus_l2(deterministic):
    recs = _run([_shrine_match(), _shrine_other()], visit_preferences=["quiet"])
    top = recs["recommendations"][0]
    assert top["name"] == "Match"
    assert top["breakdown"]["matched_need_tags"] == ["career"]
    visit_style = ((top.get("breakdown_detail") or {}).get("features") or {}).get("visit_style") or {}
    assert visit_style.get("matched_tags") == ["quiet"]


@pytest.mark.django_db
def test_l1_plus_l3a_personal_profile(deterministic):
    recs = _run([_shrine_match(), _shrine_other()], birthdate="1990-01-01")
    top = recs["recommendations"][0]
    assert top["name"] == "Match"
    assert top["breakdown"]["matched_need_tags"] == ["career"]
    assert top["breakdown"]["score_element"] == 2


@pytest.mark.django_db
def test_l1_plus_l3b_explicit_constraint(deterministic):
    recs = _run(
        [_shrine_match(), _shrine_other()],
        goriyaku_tag_ids=[REQUESTED_GORIYAKU_ID],
    )
    top = recs["recommendations"][0]
    assert top["name"] == "Match"
    assert top["breakdown"]["matched_need_tags"] == ["career"]
    signals = (top.get("score_v2") or {}).get("signals") or {}
    assert signals.get("matched_user_selected_goriyaku_tag_ids") == [REQUESTED_GORIYAKU_ID]


@pytest.mark.django_db
def test_l1_plus_l3c_context(deterministic):
    recs = _run(
        [_shrine_match(distance_m=100.0), _shrine_other(distance_m=100000.0)],
    )
    top = recs["recommendations"][0]
    assert top["name"] == "Match"
    assert top["breakdown"]["matched_need_tags"] == ["career"]
    context_profile = ((top.get("score_v2") or {}).get("signals") or {}).get("context_profile") or {}
    assert context_profile.get("distance_m") == 100.0


@pytest.mark.django_db
def test_l1_plus_l2_plus_l3a(deterministic):
    recs = _run(
        [_shrine_match(), _shrine_other()],
        visit_preferences=["quiet"],
        birthdate="1990-01-01",
    )
    top = recs["recommendations"][0]
    assert top["name"] == "Match"
    assert top["breakdown"]["matched_need_tags"] == ["career"]
    assert top["breakdown"]["score_element"] == 2
    visit_style = ((top.get("breakdown_detail") or {}).get("features") or {}).get("visit_style") or {}
    assert visit_style.get("matched_tags") == ["quiet"]


@pytest.mark.django_db
def test_l1_plus_l2_plus_l3b(deterministic):
    recs = _run(
        [_shrine_match(), _shrine_other()],
        visit_preferences=["quiet"],
        goriyaku_tag_ids=[REQUESTED_GORIYAKU_ID],
    )
    top = recs["recommendations"][0]
    assert top["name"] == "Match"
    assert top["breakdown"]["matched_need_tags"] == ["career"]
    signals = (top.get("score_v2") or {}).get("signals") or {}
    assert signals.get("matched_user_selected_goriyaku_tag_ids") == [REQUESTED_GORIYAKU_ID]
    visit_style = ((top.get("breakdown_detail") or {}).get("features") or {}).get("visit_style") or {}
    assert visit_style.get("matched_tags") == ["quiet"]


@pytest.mark.django_db
def test_l1_plus_l3b_plus_l3c(deterministic):
    recs = _run(
        [_shrine_match(distance_m=100.0), _shrine_other(distance_m=100000.0)],
        goriyaku_tag_ids=[REQUESTED_GORIYAKU_ID],
    )
    top = recs["recommendations"][0]
    assert top["name"] == "Match"
    assert top["breakdown"]["matched_need_tags"] == ["career"]
    signals = (top.get("score_v2") or {}).get("signals") or {}
    assert signals.get("matched_user_selected_goriyaku_tag_ids") == [REQUESTED_GORIYAKU_ID]
    context_profile = signals.get("context_profile") or {}
    assert context_profile.get("distance_m") == 100.0


# ---------------------------------------------------------------------------
# Task 12/13: Full Integration
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_full_integration_all_levels_together(deterministic):
    recs = _run(
        [_shrine_match(distance_m=100.0), _shrine_other(distance_m=100000.0)],
        visit_preferences=["quiet"],
        birthdate="1990-01-01",
        goriyaku_tag_ids=[REQUESTED_GORIYAKU_ID],
    )
    top = recs["recommendations"][0]

    # Candidate filter applied correctly / need score remains
    assert top["name"] == "Match"
    assert top["breakdown"]["score_need"] >= 1
    assert top["breakdown"]["matched_need_tags"] == ["career"]

    # consultation_axis maintained
    assert recs["consultation_axis"] == "career_change"

    # Visit preference score reflected
    visit_style = ((top.get("breakdown_detail") or {}).get("features") or {}).get("visit_style") or {}
    assert visit_style.get("matched_tags") == ["quiet"]

    # birthdate (element) score reflected
    assert top["breakdown"]["score_element"] == 2

    # context distance reflected
    signals = (top.get("score_v2") or {}).get("signals") or {}
    context_profile = signals.get("context_profile") or {}
    assert context_profile.get("distance_m") == 100.0

    # explicit constraint (goriyaku) reflected
    assert signals.get("matched_user_selected_goriyaku_tag_ids") == [REQUESTED_GORIYAKU_ID]

    # primary reason is not hijacked by a lower-priority auxiliary Signal:
    # need_tag / user_selected_tag facts exist (Consultation + Constraint),
    # so the primary reason must not fall back to bare "element"/"fallback".
    assert top["_primary_reason_source"] in {"need_tag", "user_selected_tag", "text_hint", "history_theme"}

    # reason_facts is consistent with the actual matched signals
    reason_fact_types = {f["type"] for f in top["_reason_facts"]}
    assert "need_tag" in reason_fact_types
    assert "user_selected_tag" in reason_fact_types


@pytest.mark.django_db
def test_full_integration_visible_reason_text_reflects_consultation_not_lower_level_signal(deterministic):
    """The user-visible `reason` string (build_recommendation_reason) must
    stay driven by Consultation Meaning (need_tags/_primary_reason_label),
    even when Visit Preference / Personal Profile / Explicit Constraint are
    all present simultaneously."""
    recs = _run(
        [_shrine_match(distance_m=100.0), _shrine_other(distance_m=100000.0)],
        visit_preferences=["quiet"],
        birthdate="1990-01-01",
        goriyaku_tag_ids=[REQUESTED_GORIYAKU_ID],
    )
    top = recs["recommendations"][0]
    # career-need reason text, not a visit-style/element-only phrase.
    assert "仕事" in top["reason"] or "転機" in top["reason"]


# ---------------------------------------------------------------------------
# Section 7: Conflict Scenarios -- L2/L3 must not override Consultation Meaning
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_conflict_consultation_vs_visit_preference_does_not_flip_ranking(deterministic):
    """相談: 仕事の転機 / Preference: 静か.
    Expected: 相談に一致する候補（Match）が引き続き優先される。
    'quiet' な候補というだけの理由で誤って上位が入れ替わらない。"""
    matched = _shrine_match(distance_m=500.0)  # career + goriyaku match, no visit_style
    matched["visit_style_tags"] = []
    quiet_only = _shrine_other(distance_m=500.0)
    quiet_only["visit_style_tags"] = ["quiet"]  # visit_style match only, no consultation match

    recs = _run([matched, quiet_only], visit_preferences=["quiet"])
    top = recs["recommendations"][0]
    assert top["name"] == "Match"
    assert top["breakdown"]["matched_need_tags"] == ["career"]


@pytest.mark.django_db
def test_conflict_consultation_vs_personal_profile_does_not_flip_ranking(deterministic):
    """相談: 仕事の転機 / birthdate: 特定element.
    Expected: 相談一致がProfile一致より優先して上位を占める。"""
    matched = _shrine_match(distance_m=500.0)
    matched["astro_elements"] = []  # no element match, only consultation match
    element_only = _shrine_other(distance_m=500.0)
    element_only["astro_elements"] = ["火"]  # element match only, no consultation match

    recs = _run([matched, element_only], birthdate="1990-01-01")
    top = recs["recommendations"][0]
    assert top["name"] == "Match"
    assert top["breakdown"]["matched_need_tags"] == ["career"]


@pytest.mark.django_db
def test_conflict_consultation_vs_explicit_constraint_evaluates_meaning_within_filtered_set(deterministic):
    """相談: 転職 / goriyaku: 厄除け等.
    Expected: goriyaku Candidate集合内で、相談との意味一致がranking軸になる
    （Constraintは候補集合を絞るだけで、意味一致の評価自体は差し替えない）。"""
    both_match = _shrine_match(distance_m=500.0)  # career + requested goriyaku
    constraint_only = _shrine_other(distance_m=500.0)
    constraint_only["goriyaku_tag_ids"] = [REQUESTED_GORIYAKU_ID]  # constraint match only, no need match

    recs = _run(
        [both_match, constraint_only],
        goriyaku_tag_ids=[REQUESTED_GORIYAKU_ID],
    )
    top = recs["recommendations"][0]
    # Both candidates satisfy the constraint (both remain eligible); the one
    # that ALSO matches Consultation Meaning ranks first.
    assert top["name"] == "Match"
    assert top["breakdown"]["matched_need_tags"] == ["career"]


@pytest.mark.django_db
def test_conflict_consultation_vs_context_does_not_relabel_reason_as_distance_only(deterministic):
    """相談: 心を整えたい / location: 近距離Candidate.
    Expected: 近いだけの神社を「あなたの悩みに最も合う」と誤説明しない --
    近い候補（Otherのみ）でも、reasonはneed一致ではなくfallback/distance
    相当の文言になる（need一致していないものをneed一致だと言わない）。"""
    far_match = _shrine_match(distance_m=50000.0)  # consultation match, far away
    near_no_match = _shrine_other(distance_m=100.0)  # very close, no consultation match

    recs = _run([far_match, near_no_match])
    near = _rec_by_name(recs, "Other")
    # The near-but-unmatched candidate must not claim a need_tag match it
    # doesn't have.
    assert near["breakdown"]["matched_need_tags"] == []
    assert near["_primary_reason_source"] != "need_tag"


# ---------------------------------------------------------------------------
# Task 8/14: Explainability -- candidate_eligibility / meaning_fit /
# visit_preference_fit / profile_fit / context_fit are each independently
# inspectable (reusing existing breakdown_detail.features -- no new schema)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_breakdown_detail_separates_meaning_visit_profile_context_features(deterministic):
    recs = _run(
        [_shrine_match(distance_m=250.0), _shrine_other(distance_m=250.0)],
        visit_preferences=["quiet"],
        birthdate="1990-01-01",
        goriyaku_tag_ids=[REQUESTED_GORIYAKU_ID],
    )
    top = recs["recommendations"][0]
    features = ((top.get("breakdown_detail") or {}).get("features") or {})

    # meaning_fit (Consultation)
    assert features["need"]["matched_by_gid_count"] >= 1 or features["need"]["raw"] >= 1
    # visit_preference_fit (L2)
    assert features["visit_style"]["matched_tags"] == ["quiet"]
    # profile_fit (L3-A)
    assert features["element"]["raw"] == 2
    # context_fit (L3-C)
    assert features["distance"]["raw"] > 0


# ---------------------------------------------------------------------------
# Task 15: No Behavior Drift -- weights unchanged
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_weights_unchanged_from_documented_contract(deterministic):
    recs = _run([_shrine_match(), _shrine_other()])
    top = recs["recommendations"][0]
    weights = top["breakdown"]["weights"]
    # need mode defaults (see _resolve_mode_weights) -- pinned as a
    # regression guard, not re-tuned by this PR.
    assert weights["element"] == pytest.approx(0.6)
    assert weights["need"] == pytest.approx(0.3)
    visit_style_weight = ((top.get("breakdown_detail") or {}).get("features") or {}).get("visit_style", {}).get("weight")
    assert visit_style_weight == pytest.approx(0.35)
