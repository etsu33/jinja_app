# backend/temples/tests/test_concierge_l3_contract.py
"""Level 3 Profile / Explicit Constraint / Recommendation Context contract
tests (pure / unit level, no HTTP).

Covers docs/product/concierge-input-architecture.md Addendum: Level 3
Profile / Explicit Constraint / Recommendation Context Contract.

    Raw L3 Input -> Canonical L3 Contract -> Compatibility Normalization
    -> Recommendation

Sections:
  A. Level 3-A Personal Profile -- profile_context birthdate precedence
  B. Level 3-C Recommendation Context -- canonical packaging
  C. radius parsing (_parse_radius, pure)
  D. Raw Input / Derived Signal boundary (Task 3)
"""

from temples.api_views_concierge import _parse_radius
from temples.services.concierge_input_contract import (
    ConciergeCanonicalInput,
    build_concierge_recommendation_context,
    resolve_profile_context_birthdate,
)


# ---------------------------------------------------------------------------
# A. Level 3-A Personal Profile: profile_context birthdate precedence
# ---------------------------------------------------------------------------


def test_resolve_profile_context_birthdate_reads_birthdate_field():
    result = resolve_profile_context_birthdate(
        {"user_profile": {"birthdate": "1990-01-01"}}
    )
    assert result == "1990-01-01"


def test_resolve_profile_context_birthdate_falls_back_to_birthday_field():
    result = resolve_profile_context_birthdate(
        {"user_profile": {"birthday": "1990-01-01"}}
    )
    assert result == "1990-01-01"


def test_resolve_profile_context_birthdate_birthdate_wins_over_birthday():
    result = resolve_profile_context_birthdate(
        {"user_profile": {"birthdate": "1990-01-01", "birthday": "1980-05-05"}}
    )
    assert result == "1990-01-01"


def test_resolve_profile_context_birthdate_none_when_no_user_profile():
    assert resolve_profile_context_birthdate({}) is None
    assert resolve_profile_context_birthdate(None) is None


def test_resolve_profile_context_birthdate_none_when_user_profile_not_dict():
    assert resolve_profile_context_birthdate({"user_profile": "not-a-dict"}) is None


def test_resolve_profile_context_birthdate_none_when_neither_field_present():
    assert resolve_profile_context_birthdate({"user_profile": {}}) is None


# ---------------------------------------------------------------------------
# B. Level 3-C Recommendation Context: canonical packaging
# ---------------------------------------------------------------------------


def test_build_concierge_recommendation_context_visit_date_alias_resolution_is_callers_job():
    # visit_date/planned_visit_date alias resolution happens at the call
    # site (`data.get("visit_date") or data.get("planned_visit_date")`,
    # api_views_concierge.py) before this packaging step -- the context
    # object itself just stores whatever canonical value it's given.
    ctx = build_concierge_recommendation_context(
        lat=35.0, lng=139.0, radius_m=8000, visit_date="2026-09-01"
    )
    assert ctx.visit_date == "2026-09-01"


# ---------------------------------------------------------------------------
# C. radius parsing (pure)
# ---------------------------------------------------------------------------


def test_parse_radius_defaults_to_8000_when_absent():
    assert _parse_radius({}) == 8000


def test_parse_radius_uses_radius_m_when_present():
    assert _parse_radius({"radius_m": 12000}) == 12000


def test_parse_radius_converts_radius_km_to_meters():
    assert _parse_radius({"radius_km": 5}) == 5000


def test_parse_radius_radius_m_wins_over_radius_km():
    assert _parse_radius({"radius_m": 3000, "radius_km": 5}) == 3000


def test_parse_radius_clips_to_minimum_1():
    assert _parse_radius({"radius_m": 0}) == 1
    assert _parse_radius({"radius_m": -100}) == 1


def test_parse_radius_clips_to_maximum_50000():
    assert _parse_radius({"radius_m": 999999}) == 50000


def test_parse_radius_invalid_value_falls_back_to_default():
    assert _parse_radius({"radius_m": "not-a-number"}) == 8000


# ---------------------------------------------------------------------------
# D. Raw Input / Derived Signal boundary (Task 3)
# ---------------------------------------------------------------------------


def test_canonical_input_does_not_include_astro_or_direction_derived_signals():
    canonical = ConciergeCanonicalInput(
        query="q",
        message="",
        language="ja",
        area=None,
        birthdate="1990-01-01",
        goriyaku_tag_ids=None,
        extra_condition=None,
        visit_preferences=[],
    )
    # astro_profile / score_element / direction_bonus are Derived Runtime
    # Signals computed downstream from birthdate (concierge_chat_ranking
    # ._attach_breakdown), never part of the canonical L3-A input itself.
    assert not hasattr(canonical, "astro_profile")
    assert not hasattr(canonical, "score_element")
    assert not hasattr(canonical, "direction_bonus")
    assert not hasattr(canonical, "element")
