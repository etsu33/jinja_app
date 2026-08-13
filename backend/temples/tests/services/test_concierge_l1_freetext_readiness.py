# backend/temples/tests/services/test_concierge_l1_freetext_readiness.py
"""L1 Free-text Recommendation Readiness Audit -- reproducibility tests.

See docs/audit/concierge-l1-freetext-readiness.md for the full audit
(fixture set, per-query results table, rate analysis, "仕事を辞めるか
迷っている" deep dive, semantic sanity review, Readiness Decision).

This file does two things:

1. Per-query stable contract assertions (Task 14): recommendation
   exists, need_tags contain an expected semantic tag, consultation_axis
   is in an expected family (or "other" where the audit's Finding A
   documents a structural taxonomy gap), primary reason is non-fallback
   where the audit found one. Deliberately avoids brittle assertions
   like an exact Top1 shrine name/id -- those can legitimately shift
   with unrelated ranking-adjacent changes.
2. Aggregate rate regression guards (Task 6/7/8): zero-recommendation
   rate, clear-intent / ambiguous-intent consultation_axis "other"
   rate, fallback rate -- bounded, not pinned to the exact audit-time
   percentages, so unrelated minor shifts do not break the suite while
   still catching a large regression.

No production code is changed by this PR -- this is audit fixture +
test only, per docs/audit/concierge-l1-freetext-readiness.md Task 15.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from temples.services.concierge_chat import build_chat_recommendations
from temples.tests.fixtures.concierge_l1_freetext_readiness_queries import (
    CONCIERGE_L1_FREETEXT_READINESS_QUERIES,
)

SEED_PATH = Path(__file__).resolve().parents[2] / "seed" / "representative_shrines.yaml"

# Axes that currently exist in temples.domain.consultation_axis.CONSULTATION_AXES
# for each theme. "love" and "relationship" are deliberately absent --
# Finding A (audit doc §7) documents that no love/relationship axis
# exists, so those themes structurally resolve to "other". This mapping
# pins that *documented, known* state, not an assumption.
EXPECTED_AXIS_FAMILY = {
    "career": {"career_change"},
    "rest": {"rest_healing"},
    "money": {"money_growth"},
    "courage": {"restart_mindset", "other"},  # keyword-coverage-dependent, see audit §8
    "study": {"study_success"},
    "love": {"other"},  # Finding A: no love/relationship axis exists
    "relationship": {"other", "rest_healing"},  # Finding A/C: alias + no axis
}

# Cases the audit confirmed reach a real (non-fallback) primary reason.
# The two clear-intent fallback cases documented in audit doc §8
# (l1_relationship_002, l1_courage_002) are intentionally excluded --
# their empty need_tags is itself the audited finding, not a regression
# to guard against here.
EXPECTED_NON_FALLBACK_IDS = {
    "l1_career_001", "l1_career_002", "l1_career_003",
    "l1_rest_001", "l1_rest_002", "l1_rest_003",
    "l1_relationship_001", "l1_relationship_003",
    "l1_love_001", "l1_love_002",
    "l1_money_001", "l1_money_002",
    "l1_courage_001",
    "l1_study_001",
}

# Expected semantic need_tag family per case (audit doc §5/§10). For the
# two relationship cases that Finding C documents as mis-aliased to
# "love", the expected family includes both the intended tag
# ("relationship") and the currently-observed one ("love") -- this pins
# the *current* (buggy) behavior as a known state without asserting it
# is correct, so a future fix (removing the alias) does not spuriously
# fail this test.
EXPECTED_NEED_TAG_FAMILY = {
    "l1_career_001": {"career"},
    "l1_career_002": {"career"},
    "l1_career_003": {"career"},
    "l1_rest_001": {"mental", "rest"},
    "l1_rest_002": {"rest"},
    "l1_rest_003": {"rest"},
    "l1_relationship_001": {"relationship", "love"},
    "l1_relationship_003": {"relationship", "love"},
    "l1_love_001": {"love"},
    "l1_love_002": {"love"},
    "l1_money_001": {"money", "career"},
    "l1_money_002": {"money"},
    "l1_courage_001": {"courage"},
    "l1_study_001": {"study"},
}


def _load_seed_candidates() -> list[dict]:
    with SEED_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []

    candidates: list[dict] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        lat = item.get("lat")
        lng = item.get("lng")
        address = (item.get("address") or "").strip()
        name = (item.get("name_jp") or item.get("name") or "").strip()

        if not name or lat is None or lng is None or not address:
            continue

        tags = item.get("astro_tags") or []
        if not isinstance(tags, list):
            tags = []

        candidates.append(
            {
                "id": 10000 + i,
                "shrine_id": 10000 + i,
                "name": name,
                "place_id": f"seed80_{10000 + i}",
                "address": address,
                "formatted_address": address,
                "lat": float(lat),
                "lng": float(lng),
                "distance_m": 1000,
                "goriyaku": item.get("goriyaku") or "",
                "tags": tags,
                "astro_tags": tags,
                "popular_score": 0.5,
            }
        )

    return candidates


def _run_all(candidates):
    results = {}
    for case in CONCIERGE_L1_FREETEXT_READINESS_QUERIES:
        recs = build_chat_recommendations(
            query=case["query"],
            language="ja",
            candidates=candidates,
            bias=None,
            birthdate=None,
            goriyaku_tag_ids=None,
            extra_condition=None,
            public_mode="need",
            flow="A",
        )
        results[case["id"]] = (case, recs)
    return results


@pytest.fixture(scope="module")
def readiness_results(django_db_blocker):
    with django_db_blocker.unblock():
        candidates = _load_seed_candidates()
        return _run_all(candidates)


# ---------------------------------------------------------------------------
# Task 14: per-query stable contract
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case",
    CONCIERGE_L1_FREETEXT_READINESS_QUERIES,
    ids=[c["id"] for c in CONCIERGE_L1_FREETEXT_READINESS_QUERIES],
)
def test_l1_freetext_recommendation_always_exists(case, readiness_results):
    """No L1-only query in this fixture set produced zero recommendations
    at audit time (Recommendation Zero rate = 0%, audit doc §6)."""
    _, recs = readiness_results[case["id"]]
    assert recs.get("recommendations"), f'{case["id"]}: no recommendations'


@pytest.mark.django_db
@pytest.mark.parametrize("case_id", sorted(EXPECTED_NEED_TAG_FAMILY.keys()))
def test_l1_freetext_need_tags_contain_expected_semantic_tag(case_id, readiness_results):
    _, recs = readiness_results[case_id]
    need_tags = set((recs.get("_need") or {}).get("tags") or [])
    expected = EXPECTED_NEED_TAG_FAMILY[case_id]
    assert need_tags & expected, f"{case_id}: need_tags={need_tags} does not intersect expected={expected}"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "case",
    CONCIERGE_L1_FREETEXT_READINESS_QUERIES,
    ids=[c["id"] for c in CONCIERGE_L1_FREETEXT_READINESS_QUERIES],
)
def test_l1_freetext_consultation_axis_matches_theme_family(case, readiness_results):
    theme = case["theme"]
    if theme not in EXPECTED_AXIS_FAMILY:
        pytest.skip(f"no axis family pinned for theme={theme!r} (ambiguous/study-bonus)")

    _, recs = readiness_results[case["id"]]
    axis = recs.get("consultation_axis")
    expected = EXPECTED_AXIS_FAMILY[theme]
    assert axis in expected, f'{case["id"]}: consultation_axis={axis!r} not in expected family {expected}'


@pytest.mark.django_db
@pytest.mark.parametrize("case_id", sorted(EXPECTED_NON_FALLBACK_IDS))
def test_l1_freetext_primary_reason_is_non_fallback_where_expected(case_id, readiness_results):
    _, recs = readiness_results[case_id]
    top1 = recs["recommendations"][0]
    assert top1.get("_primary_reason_source") != "fallback", (
        f"{case_id}: primary reason unexpectedly fell back "
        f"(reason_facts={top1.get('_reason_facts')})"
    )


# ---------------------------------------------------------------------------
# Task 6/7/8: aggregate rate regression guards (bounded, not exact-pinned)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_l1_freetext_zero_recommendation_rate_within_go_threshold(readiness_results):
    total = len(readiness_results)
    zero = sum(1 for _, recs in readiness_results.values() if not recs.get("recommendations"))
    rate = zero / total
    assert rate <= 0.05, f"zero_recommendation_rate={rate:.1%} exceeds GO threshold (5%)"


@pytest.mark.django_db
def test_l1_freetext_ambiguous_fallback_rate_is_expected_near_total(readiness_results):
    """Ambiguous-intent queries are *expected* to fall back near-universally
    (no thematic hook to extract) -- this is correct behavior, not a defect
    (audit doc §8)."""
    ambiguous_ids = {
        c["id"] for c in CONCIERGE_L1_FREETEXT_READINESS_QUERIES if c["intent_clarity"] == "ambiguous"
    }
    fallback = sum(
        1
        for case_id in ambiguous_ids
        if readiness_results[case_id][1]["recommendations"][0].get("_primary_reason_source") == "fallback"
    )
    assert fallback / len(ambiguous_ids) >= 0.75


@pytest.mark.django_db
def test_l1_freetext_clear_intent_fallback_rate_within_conditional_go_threshold(readiness_results):
    clear_ids = {
        c["id"] for c in CONCIERGE_L1_FREETEXT_READINESS_QUERIES if c["intent_clarity"] == "clear"
    }
    fallback = sum(
        1
        for case_id in clear_ids
        if readiness_results[case_id][1]["recommendations"][0].get("_primary_reason_source") == "fallback"
    )
    rate = fallback / len(clear_ids)
    assert rate <= 0.30, f"clear-intent fallback_rate={rate:.1%} exceeds CONDITIONAL GO threshold (30%)"
