from __future__ import annotations

import pytest

from temples.domain.consultation_axis import (
    CONSULTATION_AXES,
    normalize_consultation_axis,
    resolve_consultation_axis,
)
from temples.llm.intent_schema import normalize_intent
from temples.llm.schemas import complete_recommendations, normalize_recs
from temples.services.concierge_chat import build_chat_recommendations


def test_consultation_axis_taxonomy_has_eight_axes_plus_other():
    """relationship_repair was added to close PR #2409 Finding A: it was
    already documented as the relationship theme_key's primary axis in
    docs/product/consultation-theme-taxonomy.md and already had real
    (non-shadow) ranking weights in concierge_chat_ranking.
    HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS, but was never wired into
    resolve_consultation_axis()."""
    assert CONSULTATION_AXES == [
        "money_growth",
        "career_change",
        "independence",
        "relationship_repair",
        "rest_healing",
        "restart_mindset",
        "nature_reset",
        "study_success",
        "other",
    ]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("money_growth", "money_growth"),
        ("money", "money_growth"),
        ("career", "career_change"),
        ("work", "career_change"),
        ("freelance", "independence"),
        ("rest", "rest_healing"),
        ("mental", "restart_mindset"),
        ("nature", "nature_reset"),
        ("study", "study_success"),
        ("relationship_repair", "relationship_repair"),
        ("relationship", "relationship_repair"),
        ("human_relationship", "relationship_repair"),
        ("love", "relationship_repair"),
        ("unknown", "other"),
    ],
)
def test_normalize_consultation_axis(raw, expected):
    assert normalize_consultation_axis(raw) == expected


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("年収を上げたい", "money_growth"),
        ("売上と収益を伸ばしたい", "money_growth"),
        ("転職と仕事の方向性を相談したい", "career_change"),
        ("今の仕事を辞めたい", "career_change"),
        ("独立して自由に働きたい", "independence"),
        ("会社を作りたい", "independence"),
        ("疲れていて静かに回復したい", "rest_healing"),
        ("最近落ち込んでいて、立て直したい", "rest_healing"),
        ("気分が沈んでいるので静かに整えたい", "rest_healing"),
        ("気持ちを切り替えて前向きになれる参拝がしたい", "restart_mindset"),
        ("自然を感じながら参拝したい", "nature_reset"),
        ("資格試験に合格したい", "study_success"),
        ("職場の人間関係がうまくいかず悩んでいる", "relationship_repair"),
        ("家族との関係を少し整えたい", "relationship_repair"),
        ("大切な人との関係を整理したい", "relationship_repair"),
        ("友人と仲直りしたい", "relationship_repair"),
    ],
)
def test_resolve_consultation_axis_from_query(query, expected):
    result = resolve_consultation_axis(query=query, need_tags=[])

    assert result.axis == expected
    assert result.source == "query"


@pytest.mark.parametrize(
    ("need_tags", "expected"),
    [
        (["relationship"], "relationship_repair"),
        (["love"], "relationship_repair"),
    ],
)
def test_resolve_consultation_axis_relationship_and_love_share_axis_via_need_tags(need_tags, expected):
    """"職場の人間関係" etc. hit a query keyword directly, but queries
    with no relationship_repair keyword (plain 恋愛/出会い/良縁 phrasing,
    tested via need_tags here to isolate the fallback branch) must still
    resolve through the need_tags fallback -- relationship and love are
    PR #2410-distinct need_tags but share this one consultation_axis
    (score-v3-consultation-axis-history-theme-mapping.md §6.2)."""
    result = resolve_consultation_axis(query="", need_tags=need_tags)

    assert result.axis == expected
    assert result.source == "need_tags"


@pytest.mark.parametrize(
    "query",
    [
        "恋愛について悩んでいる",
        "いい出会いがほしい",
        # "良縁を願いたい" now correctly resolves to need_tags=["marriage"]
        # (docs/audit/marriage-need-independence-implementation.md), not
        # "love" -- replaced with "復縁したい", an unambiguous love-only
        # keyword (temples/domain/need_tags.py KEYWORDS["love"]).
        "復縁したい",
    ],
)
def test_resolve_consultation_axis_love_phrasing_resolves_to_relationship_repair(query):
    """Love phrasing has no dedicated CONSULTATION_AXIS_KEYWORDS entry
    (intentionally not duplicating need_tags.py's love keyword list, see
    the comment on CONSULTATION_AXIS_KEYWORDS["relationship_repair"]),
    so it reaches relationship_repair via the need_tags="love" fallback."""
    from temples.services.concierge_chat_need import resolve_need_payload

    need = resolve_need_payload(query=query, need_tags=[], max_tags=3)
    result = resolve_consultation_axis(query=query, need_tags=need["tags"])

    assert result.axis == "relationship_repair"
    assert result.source == "need_tags"


@pytest.mark.parametrize(
    ("query", "expected_need_tag_family"),
    [
        ("転職で迷っていて、仕事の流れを整えたい", "career_change"),
        ("最近疲れていて、静かに休みたい", "rest_healing"),
        ("お金や収入の不安があり、金運を整えたい", "money_growth"),
        ("資格試験の勉強と合格祈願について相談したい", "study_success"),
    ],
)
def test_resolve_consultation_axis_non_relationship_axes_unaffected(query, expected_need_tag_family):
    """Non-regression (Task 9): career/rest/money/study axis resolution
    must be unaffected by adding relationship_repair."""
    from temples.services.concierge_chat_need import resolve_need_payload

    need = resolve_need_payload(query=query, need_tags=[], max_tags=3)
    result = resolve_consultation_axis(query=query, need_tags=need["tags"])

    assert result.axis == expected_need_tag_family


def test_resolve_consultation_axis_prefers_valid_llm_axis():
    result = resolve_consultation_axis(
        query="仕事の相談",
        need_tags=["career"],
        llm_axis="money_growth",
    )

    assert result.axis == "money_growth"
    assert result.source == "llm"


def test_intent_schema_accepts_and_normalizes_consultation_axis():
    payload = normalize_intent(
        {
            "goriyaku": ["仕事運"],
            "tone": "soft",
            "atmosphere": [],
            "avoid": [],
            "summary": "仕事の相談",
            "consultation_axis": "work",
        }
    )

    assert payload["consultation_axis"] == "career_change"


def test_llm_recommendation_schema_carries_consultation_axis():
    normalized = normalize_recs(
        {
            "consultation_axis": "restart_mindset",
            "recommendations": [{"name": "A", "reason": "ok"}],
        }
    )
    completed = complete_recommendations(normalized)

    assert normalized["recommendations"][0]["consultation_axis"] == "restart_mindset"
    assert completed["recommendations"][0]["consultation_axis"] == "restart_mindset"


def test_build_chat_recommendations_attaches_consultation_axis_to_payload(settings):
    settings.CONCIERGE_USE_LLM = False
    recs = build_chat_recommendations(
        query="気持ちを切り替えて前向きになれる参拝がしたい",
        language="ja",
        candidates=[
            {
                "name": "再出発の神社",
                "astro_tags": ["mental"],
                "popular_score": 1.0,
            }
        ],
    )

    assert recs["consultation_axis"] == "restart_mindset"
    assert recs["_need"]["consultation_axis"] == "restart_mindset"
    assert recs["_signals"]["consultation_axis"] == "restart_mindset"
    assert recs["_signals"]["result_state"]["consultation_axis"] == "restart_mindset"
    assert recs["recommendations"][0]["consultation_axis"] == "restart_mindset"


# ---------------------------------------------------------------------------
# Task 8: Ranking Activation -- proving history_theme_candidate_boost > 0
# actually fires for relationship_repair, not just that the axis string
# changed. HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS["relationship_repair"]
# already existed in concierge_chat_ranking.py before this change (real,
# non-shadow ranking weights) but could never be reached because no query
# ever resolved to consultation_axis="relationship_repair".
# ---------------------------------------------------------------------------


def test_relationship_consultation_activates_history_theme_candidate_boost(settings):
    settings.CONCIERGE_USE_LLM = False
    recs = build_chat_recommendations(
        query="職場の人間関係がうまくいかず悩んでいる",
        language="ja",
        candidates=[
            {
                "name": "つながりの杜神社",
                "astro_tags": ["relationship"],
                "history_theme": "縁",
                "popular_score": 1.0,
            }
        ],
    )

    assert recs["consultation_axis"] == "relationship_repair"

    top1 = recs["recommendations"][0]
    boost = top1["breakdown_detail"]["features"]["history_theme_candidate_boost"]
    assert boost["consultation_axis"] == "relationship_repair"
    assert boost["history_theme"] == "縁"
    assert boost["raw"] > 0
    assert boost["raw"] == pytest.approx(1.0)


def test_love_consultation_activates_same_history_theme_candidate_boost(settings):
    """love shares the relationship_repair axis (Task 5 Option A), so a
    love query against the same 縁-themed candidate must activate the
    identical boost -- proving the axis sharing actually reaches ranking,
    not just need_tags."""
    settings.CONCIERGE_USE_LLM = False
    recs = build_chat_recommendations(
        query="良い出会いがほしい",
        language="ja",
        candidates=[
            {
                "name": "つながりの杜神社",
                "astro_tags": ["love"],
                "history_theme": "縁",
                "popular_score": 1.0,
            }
        ],
    )

    assert recs["consultation_axis"] == "relationship_repair"

    top1 = recs["recommendations"][0]
    boost = top1["breakdown_detail"]["features"]["history_theme_candidate_boost"]
    assert boost["consultation_axis"] == "relationship_repair"
    assert boost["raw"] == pytest.approx(1.0)


def test_relationship_consultation_axis_history_theme_boost_is_zero_without_relationship_axis(settings):
    """Regression guard for the bug this whole PR fixes: before wiring
    relationship_repair into resolve_consultation_axis, a relationship
    query's consultation_axis was always "other", under which
    HISTORY_THEME_CANDIDATE_BOOST_BY_AXIS has no entry -- so the boost
    was silently always 0 even for a perfectly-matched 縁-themed
    candidate. Simulate the pre-fix axis explicitly via llm_axis to
    prove the boost really is axis-gated, not just history_theme-gated."""
    from temples.services.concierge_chat_ranking import _attach_breakdown

    rec = {
        "id": 1,
        "name": "縁結び神社",
        "astro_tags": ["relationship"],
        "astro_elements": [],
        "history_theme": "縁",
        "goriyaku": "",
        "description": "",
        "goriyaku_tag_ids": [],
        "popular_score": 0,
    }

    _attach_breakdown(
        rec,
        birthdate=None,
        need_tags=["relationship"],
        weights={"element": 0.0, "need": 1.0, "popular": 0.0, "distance": 0.0},
        astro_bonus_enabled=False,
        visit_style_tags=set(),
        query="職場の人間関係がうまくいかず悩んでいる",
        requested_goriyaku_tag_ids=None,
        goriyaku_tag_label_by_id={},
        user=None,
        consultation_axis="other",
    )

    assert rec["breakdown_detail"]["features"]["history_theme_candidate_boost"]["raw"] == 0.0


# ---------------------------------------------------------------------------
# Task 13: Reason Sanity -- a shared consultation_axis must not resurrect
# a love-only primary reason for a relationship consultation.
# ---------------------------------------------------------------------------


def test_relationship_consultation_axis_sharing_does_not_reintroduce_love_reason(settings):
    """With the relationship_repair axis wired up, this candidate now
    also earns a history_theme="縁" match, which legitimately outranks
    the plain need_tag match under the existing (untouched) Primary
    Reason priority -- so primary_reason_label becomes "縁", not
    "relationship". That's a correct, thematically-appropriate upgrade
    (Ranking behavior change: relationship queries only), not a
    regression. The contract this test guards is narrower and must hold
    regardless of which label wins: it must never be "love", and the
    visible reason text must never contain love-only phrasing."""
    settings.CONCIERGE_USE_LLM = False
    recs = build_chat_recommendations(
        query="職場の人間関係がうまくいかず悩んでいる",
        language="ja",
        candidates=[
            {
                "name": "つながりの杜神社",
                "astro_tags": ["relationship"],
                "history_theme": "縁",
                "goriyaku": "心願成就",
                "popular_score": 1.0,
            }
        ],
    )

    assert recs["consultation_axis"] == "relationship_repair"
    assert "love" not in recs["_need"]["tags"]

    top1 = recs["recommendations"][0]
    assert top1["breakdown"]["matched_need_tags"] == ["relationship"]
    assert top1["_primary_reason_label"] != "love"
    assert top1["_primary_reason_source"] != "fallback"
    for phrase in ("恋愛", "良縁", "縁結び", "恋愛成就", "片思い", "復縁", "両思い"):
        assert phrase not in top1["reason"]
