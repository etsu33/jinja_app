# backend/temples/tests/test_concierge_visit_preference_contract.py
"""Level 2 Visit Preference Signal Redesign contract tests.

Covers docs/product/concierge-input-architecture.md Addendum: Level 2
Visit Preference Signal Redesign.

    UI selection -> Canonical Visit Preference -> Compatibility Layer
    -> Recommendation

Sections:
  A. Canonical tag vocabulary (temples/domain/visit_preference)
  B. Compatibility Layer (Structured + Legacy merge, no double-counting)
  C. Canonical Input Contract (ConciergeCanonicalInput.visit_preferences)
  D. Ranking integration (build_chat_recommendations)
  E. No Behavior Regression (old client path unaffected)

These tests do not change Recommendation behavior for existing clients --
`visit_preferences` is purely additive (new optional field / kwarg,
default None / []).
"""

import pytest

from temples.domain.visit_preference import (
    MAX_VISIT_PREFERENCES,
    VISIT_PREFERENCE_TAGS,
    normalize_visit_preferences,
)
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_extra_condition import (
    resolve_visit_preference_tags,
)
from temples.services.concierge_input_contract import normalize_concierge_request


# ---------------------------------------------------------------------------
# A. Canonical tag vocabulary
# ---------------------------------------------------------------------------


def test_canonical_tag_set_is_the_documented_six():
    assert VISIT_PREFERENCE_TAGS == {
        "quiet",
        "nature",
        "reset",
        "less_crowded",
        "nearby",
        "classic",
    }


@pytest.mark.parametrize("tag", sorted(VISIT_PREFERENCE_TAGS))
def test_normalize_visit_preferences_accepts_each_canonical_tag(tag):
    assert normalize_visit_preferences([tag]) == [tag]


def test_normalize_visit_preferences_multiple_preferences():
    assert normalize_visit_preferences(["quiet", "nature", "classic"]) == [
        "quiet",
        "nature",
        "classic",
    ]


def test_normalize_visit_preferences_dedupes_duplicates_preserving_first_position():
    assert normalize_visit_preferences(["quiet", "nature", "quiet"]) == [
        "quiet",
        "nature",
    ]


def test_normalize_visit_preferences_drops_unknown_tag():
    assert normalize_visit_preferences(["quiet", "made_up_tag"]) == ["quiet"]


def test_normalize_visit_preferences_drops_legacy_visit_style_tags_not_in_canonical_set():
    # `business`/`study` are valid EXTRA_TAG_META visit_style tags but are
    # NOT part of the Level 2 canonical structured vocabulary (Task 3/7).
    assert normalize_visit_preferences(["business", "study", "quiet"]) == ["quiet"]


def test_normalize_visit_preferences_empty_input():
    assert normalize_visit_preferences(None) == []
    assert normalize_visit_preferences([]) == []


def test_normalize_visit_preferences_caps_at_max():
    all_six_twice = list(VISIT_PREFERENCE_TAGS) * 2 + ["another_unknown"]
    result = normalize_visit_preferences(all_six_twice)
    assert len(result) <= MAX_VISIT_PREFERENCES
    assert len(result) == len(VISIT_PREFERENCE_TAGS)


# ---------------------------------------------------------------------------
# B. Compatibility Layer
# ---------------------------------------------------------------------------


def test_resolve_visit_preference_tags_structured_only():
    result = resolve_visit_preference_tags(structured=["quiet"], legacy_visit_style_tags=set())
    assert result == {"quiet"}


def test_resolve_visit_preference_tags_legacy_only():
    result = resolve_visit_preference_tags(structured=None, legacy_visit_style_tags={"nature"})
    assert result == {"nature"}


def test_resolve_visit_preference_tags_same_meaning_dedupes():
    result = resolve_visit_preference_tags(
        structured=["quiet"],
        legacy_visit_style_tags={"quiet"},
    )
    assert result == {"quiet"}


def test_resolve_visit_preference_tags_different_meaning_both_kept():
    result = resolve_visit_preference_tags(
        structured=["quiet"],
        legacy_visit_style_tags={"less_crowded"},
    )
    assert result == {"quiet", "less_crowded"}


def test_resolve_visit_preference_tags_ignores_unknown_structured_tag():
    result = resolve_visit_preference_tags(
        structured=["not_a_real_tag"],
        legacy_visit_style_tags={"classic"},
    )
    assert result == {"classic"}


# ---------------------------------------------------------------------------
# C. Canonical Input Contract
# ---------------------------------------------------------------------------


def test_canonical_input_visit_preferences_from_top_level():
    canonical = normalize_concierge_request(
        {"query": "q", "visit_preferences": ["quiet", "nature"]}
    )
    assert canonical.visit_preferences == ["quiet", "nature"]


def test_canonical_input_visit_preferences_absent_defaults_to_empty_list():
    canonical = normalize_concierge_request({"query": "q"})
    assert canonical.visit_preferences == []


def test_canonical_input_visit_preferences_drops_unknown_tag():
    canonical = normalize_concierge_request(
        {"query": "q", "visit_preferences": ["quiet", "unknown_tag"]}
    )
    assert canonical.visit_preferences == ["quiet"]


def test_canonical_input_visit_preferences_dedupes():
    canonical = normalize_concierge_request(
        {"query": "q", "visit_preferences": ["quiet", "quiet"]}
    )
    assert canonical.visit_preferences == ["quiet"]


def test_canonical_input_visit_preferences_ignores_filters_duplicate():
    # Unlike birthdate/goriyaku_tag_ids/extra_condition, visit_preferences is
    # a new field with no top-level/filters duplication (Gap C is not
    # inherited here) -- filters.visit_preferences is not read.
    canonical = normalize_concierge_request(
        {"query": "q", "filters": {"visit_preferences": ["quiet"]}}
    )
    assert canonical.visit_preferences == []


def test_canonical_input_does_not_include_derived_signals_alongside_visit_preferences():
    canonical = normalize_concierge_request(
        {"query": "q", "visit_preferences": ["quiet"]}
    )
    assert not hasattr(canonical, "need_tags")
    assert not hasattr(canonical, "consultation_axis")


# ---------------------------------------------------------------------------
# D. Ranking integration
# ---------------------------------------------------------------------------


def _visit_style_raw(rec: dict) -> int:
    """score_visit_style is not in the public `breakdown` dict (it never
    contributes to the public `score_total` -- only to the internal ranking
    score `_score_total`, see concierge_chat_ranking._attach_breakdown).
    Tests read it from breakdown_detail.features.visit_style.raw instead."""
    detail = ((rec.get("breakdown_detail") or {}).get("features") or {}).get("visit_style") or {}
    return int(detail.get("raw") or 0)


def _candidates_for(tag: str):
    return [
        {
            "name": "Match",
            "distance_m": 500.0,
            "lat": 35.001,
            "lng": 139.001,
            "popular_score": 5.0,
            "visit_style_tags": [tag],
        },
        {
            "name": "NoMatch",
            "distance_m": 500.0,
            "lat": 35.002,
            "lng": 139.002,
            "popular_score": 5.0,
            "visit_style_tags": [],
        },
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("tag", sorted(VISIT_PREFERENCE_TAGS))
def test_structured_preference_ranks_matching_shrine_first(monkeypatch, settings, tag):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    recs = build_chat_recommendations(
        query="",
        language="ja",
        candidates=_candidates_for(tag),
        visit_preferences=[tag],
    )

    items = recs["recommendations"]
    assert items[0]["name"] == "Match"
    visit_style_detail = ((items[0].get("breakdown_detail") or {}).get("features") or {}).get("visit_style") or {}
    assert tag in (visit_style_detail.get("matched_tags") or [])


@pytest.mark.django_db
def test_structured_multiple_preferences_all_match(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    candidates = [
        {
            "name": "Both",
            "distance_m": 500.0,
            "lat": 35.001,
            "lng": 139.001,
            "popular_score": 5.0,
            "visit_style_tags": ["quiet", "nature"],
        },
        {
            "name": "One",
            "distance_m": 500.0,
            "lat": 35.002,
            "lng": 139.002,
            "popular_score": 5.0,
            "visit_style_tags": ["quiet"],
        },
    ]

    recs = build_chat_recommendations(
        query="",
        language="ja",
        candidates=candidates,
        visit_preferences=["quiet", "nature"],
    )

    items = recs["recommendations"]
    assert items[0]["name"] == "Both"
    assert _visit_style_raw(items[0]) == 2
    assert _visit_style_raw(items[1]) == 1


@pytest.mark.django_db
def test_structured_duplicate_preferences_no_double_count(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    candidates = _candidates_for("quiet")

    recs_dup = build_chat_recommendations(
        query="",
        language="ja",
        candidates=candidates,
        visit_preferences=["quiet", "quiet"],
    )
    recs_single = build_chat_recommendations(
        query="",
        language="ja",
        candidates=candidates,
        visit_preferences=["quiet"],
    )

    score_dup = _visit_style_raw(recs_dup["recommendations"][0])
    score_single = _visit_style_raw(recs_single["recommendations"][0])
    assert score_dup == score_single == 1


@pytest.mark.django_db
def test_structured_unknown_preference_ignored_no_crash(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    recs = build_chat_recommendations(
        query="",
        language="ja",
        candidates=_candidates_for("quiet"),
        visit_preferences=["not_a_real_tag"],
    )

    items = recs["recommendations"]
    assert all(_visit_style_raw(r) == 0 for r in items)


@pytest.mark.django_db
def test_compatibility_legacy_extra_condition_only_still_effective(monkeypatch, settings):
    """Regression guard: the pre-existing free-text -> keyword -> visit_style
    path (real, unmocked extract_extra_tags) must keep working exactly as
    before once visit_preferences exists."""
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    recs = build_chat_recommendations(
        query="",
        language="ja",
        candidates=_candidates_for("quiet"),
        extra_condition="静かな雰囲気で、気持ちを落ち着けて過ごしたい",
    )

    items = recs["recommendations"]
    assert items[0]["name"] == "Match"
    assert _visit_style_raw(items[0]) == 1


@pytest.mark.django_db
def test_compatibility_crowd_derived_text_still_produces_less_crowded(monkeypatch, settings):
    """crowd -> extra_condition round-trip (apps/web hooks.ts) injects
    '空いている ひとり向け' -- confirms this still resolves to
    less_crowded via the real (unmocked) keyword parser."""
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    recs = build_chat_recommendations(
        query="",
        language="ja",
        candidates=_candidates_for("less_crowded"),
        extra_condition="空いている ひとり向け",
    )

    items = recs["recommendations"]
    assert items[0]["name"] == "Match"
    assert _visit_style_raw(items[0]) == 1


@pytest.mark.django_db
def test_compatibility_structured_and_legacy_same_meaning_no_double_score(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    recs = build_chat_recommendations(
        query="",
        language="ja",
        candidates=_candidates_for("quiet"),
        extra_condition="静かな雰囲気で、気持ちを落ち着けて過ごしたい",
        visit_preferences=["quiet"],
    )

    items = recs["recommendations"]
    assert _visit_style_raw(items[0]) == 1


@pytest.mark.django_db
def test_compatibility_structured_and_legacy_different_meaning_both_applied(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    candidates = [
        {
            "name": "Both",
            "distance_m": 500.0,
            "lat": 35.001,
            "lng": 139.001,
            "popular_score": 5.0,
            "visit_style_tags": ["quiet", "less_crowded"],
        },
    ]

    recs = build_chat_recommendations(
        query="",
        language="ja",
        candidates=candidates,
        extra_condition="人混みを避けたい、混雑しにくい場所がいい",
        visit_preferences=["quiet"],
    )

    items = recs["recommendations"]
    assert _visit_style_raw(items[0]) == 2


@pytest.mark.django_db
def test_visit_style_score_parity_structured_vs_legacy_same_contribution(monkeypatch, settings):
    """Task 10 Ranking Contract: same preference / same shrine / same score
    contribution regardless of whether the tag arrived Structured or via
    the Legacy free-text parser (both feed the same score_visit_style x
    0.35 computation)."""
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    candidates = _candidates_for("nature")

    recs_structured = build_chat_recommendations(
        query="",
        language="ja",
        candidates=candidates,
        visit_preferences=["nature"],
    )
    recs_legacy = build_chat_recommendations(
        query="",
        language="ja",
        candidates=candidates,
        extra_condition="自然を感じながら、ゆっくり参拝できる場所がいい",
    )

    top_structured = recs_structured["recommendations"][0]
    top_legacy = recs_legacy["recommendations"][0]

    assert top_structured["name"] == top_legacy["name"] == "Match"
    assert (
        _visit_style_raw(top_structured)
        == _visit_style_raw(top_legacy)
        == 1
    )
    # score_visit_style only contributes to the internal ranking score
    # (_score_total), not the public breakdown.score_total -- see
    # _visit_style_raw() docstring above.
    assert top_structured["_score_total"] == top_legacy["_score_total"]


@pytest.mark.django_db
def test_sort_distance_unaffected_by_visit_preferences(monkeypatch, settings):
    """Task 11 Sort Contract: `nearby` is a Preference (Ranking Bonus),
    `sort_distance` is a separate Sort Override. Sending visit_preferences
    (including `nearby`) must not itself trigger the distance sort
    override -- only the legacy `sort_distance` extra_condition tag does."""
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    # Same candidate shape as test_concierge_sort_distance_override_sorts_by_
    # distance (test_concierge_need_contract.py) -- under a real
    # sort_distance override this set sorts strictly by distance:
    # A(100m) -> B(200m) -> C(300m).
    candidates = [
        {"name": "B", "distance_m": 200.0, "lat": 35.002, "lng": 139.002, "popular_score": 9.0, "visit_style_tags": []},
        {"name": "C", "distance_m": 300.0, "lat": 35.003, "lng": 139.003, "popular_score": 10.0, "visit_style_tags": []},
        {"name": "A", "distance_m": 100.0, "lat": 35.001, "lng": 139.001, "popular_score": 1.0, "visit_style_tags": []},
    ]

    recs = build_chat_recommendations(
        query="",
        language="ja",
        candidates=candidates,
        visit_preferences=["nearby"],
    )

    items = recs["recommendations"]
    # `nearby` is a Preference (Ranking Bonus, none of these candidates has
    # it in visit_style_tags so it contributes 0 either way) -- it must NOT
    # itself flip the sort into the strict-distance order that only the
    # Legacy `sort_distance` extra_condition tag triggers.
    assert [x["name"] for x in items] != ["A", "B", "C"]


@pytest.mark.django_db
def test_need_score_unaffected_by_visit_preferences(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    import temples.domain.need_tags as need

    class FakeNeedExtract:
        def __init__(self):
            self.tags = ["rest"]
            self.hits = {"rest": ["疲れ"]}

    monkeypatch.setattr(need, "extract_need_tags", lambda q, max_tags=3: FakeNeedExtract(), raising=True)

    candidates = [
        {
            "name": "A",
            "distance_m": 500.0,
            "lat": 35.001,
            "lng": 139.001,
            "popular_score": 5.0,
            "astro_tags": ["rest"],
            "visit_style_tags": [],
        },
    ]

    recs_without = build_chat_recommendations(
        query="疲れが取れない", language="ja", candidates=candidates,
    )
    recs_with = build_chat_recommendations(
        query="疲れが取れない", language="ja", candidates=candidates, visit_preferences=["quiet"],
    )

    assert (
        recs_without["recommendations"][0]["breakdown"]["score_need"]
        == recs_with["recommendations"][0]["breakdown"]["score_need"]
    )


@pytest.mark.django_db
def test_goriyaku_match_unaffected_by_visit_preferences(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    candidates = [
        {
            "name": "A",
            "distance_m": 500.0,
            "lat": 35.001,
            "lng": 139.001,
            "popular_score": 5.0,
            "goriyaku_tag_ids": [1],
            "visit_style_tags": [],
        },
    ]

    recs_without = build_chat_recommendations(
        query="", language="ja", candidates=candidates, goriyaku_tag_ids=[1],
    )
    recs_with = build_chat_recommendations(
        query="", language="ja", candidates=candidates, goriyaku_tag_ids=[1], visit_preferences=["classic"],
    )

    matched_without = (recs_without["recommendations"][0].get("breakdown") or {}).get("matched_need_tags")
    matched_with = (recs_with["recommendations"][0].get("breakdown") or {}).get("matched_need_tags")
    assert matched_without == matched_with


@pytest.mark.django_db
def test_birthdate_score_unaffected_by_visit_preferences(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    import temples.domain.astrology as astro

    class _Prof:
        sign = "牡牛座"
        element = "土"

    monkeypatch.setattr(astro, "sun_sign_and_element", lambda birthdate: _Prof(), raising=True)
    monkeypatch.setattr(astro, "element_priority", lambda user_elem, shrine_elems: 2, raising=True)

    candidates = [
        {
            "name": "A",
            "distance_m": 500.0,
            "lat": 35.001,
            "lng": 139.001,
            "popular_score": 5.0,
            "astro_elements": ["土"],
            "visit_style_tags": [],
        },
    ]

    recs_without = build_chat_recommendations(
        query="", language="ja", candidates=candidates, birthdate="1990-01-01",
    )
    recs_with = build_chat_recommendations(
        query="", language="ja", candidates=candidates, birthdate="1990-01-01", visit_preferences=["nature"],
    )

    assert (
        recs_without["recommendations"][0]["breakdown"]["score_element"]
        == recs_with["recommendations"][0]["breakdown"]["score_element"]
    )


# ---------------------------------------------------------------------------
# E. No Behavior Regression
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_omitting_visit_preferences_kwarg_matches_explicit_empty_list(monkeypatch, settings):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    candidates = _candidates_for("quiet")

    recs_omitted = build_chat_recommendations(query="", language="ja", candidates=candidates)
    recs_explicit_empty = build_chat_recommendations(
        query="", language="ja", candidates=candidates, visit_preferences=[]
    )

    assert (
        _visit_style_raw(recs_omitted["recommendations"][0])
        == _visit_style_raw(recs_explicit_empty["recommendations"][0])
        == 0
    )
