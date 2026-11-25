# backend/temples/tests/test_concierge_relationship_love_separation.py
"""L1 Relationship / Love Interpretation Separation.

Fixes the Finding C bug from docs/audit/concierge-l1-freetext-readiness.md
(PR #2409): `NEED_TAG_ALIASES["relationship"] = "love"` collapsed the
domain layer's distinct `relationship` need tag (人間関係全般: 職場/
家族/友人/対人, temples/domain/need_tags.py) into `love` (恋愛/出会い/
良縁), so workplace/family/friend relationship consultations produced
romantic-love recommendation reasons.

Root cause had TWO independent copies of the same alias table:
  - temples/services/concierge_chat_need.NEED_TAG_ALIASES
  - temples/services/concierge_chat_ranking.NEED_TAG_ALIASES
Both had to drop the `"relationship": "love"` entry for the fix to take
effect end-to-end (the ranking-layer copy is what `_attach_breakdown`
actually uses for matching).

Scope: relationship/love semantic separation only. consultation_axis
taxonomy, ranking weights, candidate filtering, goriyaku hard filter,
Primary Reason priority, Level 2/3, Score v3, Frontend, DB schema are
all unchanged -- see docs/product/concierge-input-architecture.md for
the layers this PR does not touch.
"""

from __future__ import annotations

import pytest

from temples.domain.need_tags import extract_need_tags
from temples.services.concierge_chat import build_chat_recommendations
from temples.services.concierge_chat_need import (
    NEED_TAG_ALIASES as SERVICE_NEED_TAG_ALIASES,
    normalize_need_tag,
    resolve_need_payload,
)
from temples.services.concierge_chat_ranking import (
    NEED_TAG_ALIASES as RANKING_NEED_TAG_ALIASES,
    _normalize_need_tag,
)

LOVE_ONLY_PHRASES = ("恋愛", "良縁", "縁結び", "恋愛成就", "片思い", "復縁", "両思い")


# ---------------------------------------------------------------------------
# Task 3: Alias table contract (both independent copies)
# ---------------------------------------------------------------------------


def test_relationship_is_not_in_either_alias_table():
    assert "relationship" not in SERVICE_NEED_TAG_ALIASES
    assert "relationship" not in RANKING_NEED_TAG_ALIASES


@pytest.mark.parametrize(
    "normalize_fn",
    [normalize_need_tag, _normalize_need_tag],
    ids=["concierge_chat_need", "concierge_chat_ranking"],
)
def test_relationship_normalizes_to_relationship_not_love(normalize_fn):
    assert normalize_fn("relationship") == "relationship"


@pytest.mark.parametrize(
    "normalize_fn",
    [normalize_need_tag, _normalize_need_tag],
    ids=["concierge_chat_need", "concierge_chat_ranking"],
)
def test_love_normalizes_to_love(normalize_fn):
    assert normalize_fn("love") == "love"


@pytest.mark.parametrize(
    "normalize_fn",
    [normalize_need_tag, _normalize_need_tag],
    ids=["concierge_chat_need", "concierge_chat_ranking"],
)
def test_love_does_not_normalize_to_relationship(normalize_fn):
    assert normalize_fn("love") != "relationship"


@pytest.mark.parametrize(
    "normalize_fn",
    [normalize_need_tag, _normalize_need_tag],
    ids=["concierge_chat_need", "concierge_chat_ranking"],
)
def test_love_synonym_alias_is_unchanged(normalize_fn):
    """Task 4 backward compatibility: "romance" (a plain English synonym
    for "love", with no independent keyword list of its own) remains
    aliased to "love"."""
    assert normalize_fn("romance") == "love"


@pytest.mark.parametrize(
    "normalize_fn",
    [normalize_need_tag, _normalize_need_tag],
    ids=["concierge_chat_need", "concierge_chat_ranking"],
)
def test_marriage_no_longer_aliases_to_love(normalize_fn):
    """docs/audit/marriage-love-alias-boundary.md /
    marriage-need-independence-implementation.md: unlike "romance",
    "marriage" has a real, independently-defined keyword list
    (結婚/婚活/夫婦円満, temples/domain/need_tags.py KEYWORDS["marriage"]
    and temples/services/consultation_interpreter.py
    NEED_KEYWORDS["marriage"]) that the alias discarded end-to-end.
    "marriage" was removed from NEED_TAG_ALIASES and is now
    independently reachable."""
    assert normalize_fn("marriage") == "marriage"


# ---------------------------------------------------------------------------
# Task 2/5/9: Domain-level need tag lifecycle for natural-language fixtures
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query,expected_in",
    [
        ("職場の人間関係がうまくいかず悩んでいる", "relationship"),
        ("家族との関係を少し整えたい", "relationship"),
    ],
)
def test_relationship_phrasing_preserves_relationship_tag(query, expected_in):
    extracted = extract_need_tags(query)
    assert expected_in in extracted.tags
    payload = resolve_need_payload(query=query, need_tags=[], max_tags=3)
    assert expected_in in payload["tags"]


@pytest.mark.parametrize(
    "query",
    [
        "職場の人間関係がうまくいかず悩んでいる",
        "大切な人との関係を整理したい",
        "家族との関係を少し整えたい",
        "友人との関係で疲れている",
    ],
)
def test_relationship_phrasing_never_produces_love_tag(query):
    """Task 5: even in cases where "relationship" itself isn't extracted
    (e.g. "友人との関係で疲れている" doesn't literally contain a
    KEYWORDS-matched relationship word -- a pre-existing, unrelated
    Interpretation coverage gap, not touched here), the query must never
    be force-converted to "love" -- that's the specific bug this PR
    fixes."""
    payload = resolve_need_payload(query=query, need_tags=[], max_tags=3)
    assert "love" not in payload["tags"], f"{query!r} unexpectedly resolved to love: {payload}"


@pytest.mark.parametrize(
    "query",
    [
        "恋愛について悩んでいる",
        "いい出会いがほしい",
    ],
)
def test_love_phrasing_still_resolves_to_love(query):
    """Task 4 backward compatibility: real love/romance consultations are
    unaffected by removing the relationship->love alias."""
    payload = resolve_need_payload(query=query, need_tags=[], max_tags=3)
    assert "love" in payload["tags"]


def test_marriage_keyword_phrasing_now_resolves_to_marriage_not_love():
    """"良縁" is a domain-level "marriage" keyword (temples/domain/
    need_tags.py KEYWORDS["marriage"]), not "love" or "relationship".
    Following docs/audit/marriage-need-independence-implementation.md,
    the marriage->love alias was removed, so this now resolves to
    "marriage" instead of collapsing into "love" as it did before."""
    payload = resolve_need_payload(query="良縁を願いたい", need_tags=[], max_tags=3)
    assert payload["tags"] == ["marriage"]


# ---------------------------------------------------------------------------
# Task 6/11: Reason Contract -- relationship match must not produce a
# love-only Reason, end to end through the real ranking/reason pipeline
# ---------------------------------------------------------------------------


def _shrine(name, astro_tags, **overrides):
    base = {
        "name": name,
        "distance_m": 500.0,
        "lat": 35.001,
        "lng": 139.001,
        "popular_score": 5.0,
        "astro_tags": astro_tags,
        "goriyaku": "",
        "description": "",
    }
    base.update(overrides)
    return base


@pytest.mark.django_db
def test_relationship_match_produces_relationship_reason_not_love(settings, monkeypatch):
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    import temples.domain.need_tags as need

    class FakeNeedExtract:
        tags = ["relationship"]
        hits = {"relationship": ["職場", "人間関係"]}

    monkeypatch.setattr(need, "extract_need_tags", lambda q, max_tags=3: FakeNeedExtract(), raising=True)

    candidates = [_shrine("対人円満神社", ["relationship"])]
    recs = build_chat_recommendations(
        query="職場の人間関係がうまくいかず悩んでいる",
        language="ja",
        candidates=candidates,
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]

    assert top1["breakdown"]["matched_need_tags"] == ["relationship"]
    assert top1["_primary_reason_source"] == "need_tag"
    assert top1["_primary_reason_label"] == "relationship"

    for phrase in LOVE_ONLY_PHRASES:
        assert phrase not in top1["reason"], f"unexpected love phrase {phrase!r} in reason: {top1['reason']!r}"
        summary = ((top1.get("explanation") or {}).get("summary")) or ""
        assert phrase not in summary, f"unexpected love phrase {phrase!r} in summary: {summary!r}"


@pytest.mark.django_db
def test_love_match_is_unaffected_and_still_produces_love_reason(settings, monkeypatch):
    """Task 4 backward compatibility at the full pipeline level: a real
    love-need match still produces love-specific reasoning."""
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    import temples.domain.need_tags as need

    class FakeNeedExtract:
        tags = ["love"]
        hits = {"love": ["恋愛", "出会い"]}

    monkeypatch.setattr(need, "extract_need_tags", lambda q, max_tags=3: FakeNeedExtract(), raising=True)

    candidates = [_shrine("恋木神社", ["love"], goriyaku="恋愛成就")]
    recs = build_chat_recommendations(
        query="恋愛について悩んでいる",
        language="ja",
        candidates=candidates,
        public_mode="need",
        flow="A",
    )
    top1 = recs["recommendations"][0]

    assert top1["breakdown"]["matched_need_tags"] == ["love"]
    assert top1["_primary_reason_source"] == "need_tag"
    assert top1["_primary_reason_label"] == "love"
    assert "恋愛" in top1["reason"]


# ---------------------------------------------------------------------------
# Task 10: PR #2409 regression (l1_relationship_001/002/003), before/after
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_pr2409_l1_relationship_001_no_longer_gets_love_primary_reason(settings, monkeypatch):
    """Before this fix: need_tags=['mental','love','rest'], primary_reason
    = need_tag/love, Top1 reason mentioned "恋愛や良縁" (縁結びのご利益で
    知られる高千穂神社は、恋愛や良縁を願う参拝先として適しています。).
    After this fix: need_tags=['mental','relationship','rest'] (relationship
    preserved), and since this fixture's shrine has no relationship-tagged
    match, "mental" wins instead -- primary_reason_source stays a real
    need_tag match, just no longer a wrong love-themed one."""
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    candidates = [
        _shrine("高千穂神社", ["love"], goriyaku="縁結び"),
        _shrine("鎮守の森神社", ["mental", "rest"], goriyaku="厄除け・開運"),
    ]
    recs = build_chat_recommendations(
        query="人間関係で少し疲れている",
        language="ja",
        candidates=candidates,
        public_mode="need",
        flow="A",
    )

    need_tags = recs["_need"]["tags"]
    assert "relationship" in need_tags
    assert "love" not in need_tags

    top1 = recs["recommendations"][0]
    assert top1["_primary_reason_label"] != "love"
    for phrase in LOVE_ONLY_PHRASES:
        assert phrase not in top1["reason"]


@pytest.mark.django_db
def test_pr2409_l1_relationship_002_interpretation_gap_unchanged(settings, monkeypatch):
    """l1_relationship_002 ("大切な人との関係を整理したい") was, and
    remains, an Interpretation Gap (empty need_tags) -- unaffected by
    this fix, confirmed as a non-regression."""
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    candidates = [_shrine("三光稲荷神社", [], goriyaku="金運")]
    recs = build_chat_recommendations(
        query="大切な人との関係を整理したい",
        language="ja",
        candidates=candidates,
        public_mode="need",
        flow="A",
    )

    assert recs["_need"]["tags"] == []
    top1 = recs["recommendations"][0]
    assert top1["_primary_reason_source"] == "fallback"
    for phrase in LOVE_ONLY_PHRASES:
        assert phrase not in top1["reason"]


@pytest.mark.django_db
def test_pr2409_l1_relationship_003_no_longer_gets_love_primary_reason(settings, monkeypatch):
    """Before this fix: need_tags=['love'], primary_reason = need_tag/love,
    Top1 reason: "恋愛成就のご利益で知られる恋木神社は、恋愛や良縁を願う
    参拝先として適しています。" -- a workplace-relationship complaint
    recommended with a romantic-love justification.
    After this fix: need_tags=['relationship'] (correctly preserved, not
    converted). Whether it then matches a candidate or falls back
    depends on candidate coverage (Task 8, a separate concern) -- either
    outcome is acceptable here, the only forbidden outcome is a
    love-labeled primary reason for this workplace-relationship query.

    The candidate's static `goriyaku` text is deliberately neutral here
    (unlike the real 恋木神社/"恋愛成就" fixture in the 82-shrine
    readiness pool): the fallback reason template quotes a candidate's
    own static goriyaku text verbatim regardless of matched need tags,
    so a real "恋愛成就"-goriyaku shrine would legitimately mention 恋愛
    in fallback mode purely as its own real-world description, not as a
    love-biased *primary reason* -- that's a Candidate Coverage Gap
    (Task 8), not the Interpretation bug this test targets."""
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    candidates = [_shrine("恋木神社", ["love"], goriyaku="心願成就")]
    recs = build_chat_recommendations(
        query="職場の人間関係がうまくいかず悩んでいる",
        language="ja",
        candidates=candidates,
        public_mode="need",
        flow="A",
    )

    need_tags = recs["_need"]["tags"]
    assert need_tags == ["relationship"]
    assert "love" not in need_tags

    top1 = recs["recommendations"][0]
    assert top1["_primary_reason_label"] != "love"
    for phrase in LOVE_ONLY_PHRASES:
        assert phrase not in top1["reason"]


# ---------------------------------------------------------------------------
# Task 11: Semantic assertion -- relationship consultation != love
# recommendation meaning, as an explicit, reusable Contract
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query",
    [
        "職場の人間関係がうまくいかず悩んでいる",
        "大切な人との関係を整理したい",
        "家族との関係を少し整えたい",
        "友人との関係で疲れている",
    ],
)
def test_relationship_consultation_never_produces_love_only_reason(query, settings, monkeypatch):
    """A candidate astro-tagged "love" stays in the pool (proving it is
    not spuriously matched via a relationship->love need-tag conversion)
    but uses neutral static goriyaku text -- unlike a real 恋愛成就-type
    shrine, whose own descriptive text would legitimately mention 恋愛
    regardless of the query's need tags if it were ranked to the top by
    distance/popularity alone (a Candidate Coverage Gap concern, Task 8,
    not the Interpretation contract this test targets)."""
    settings.CONCIERGE_USE_LLM = False
    monkeypatch.setenv("CHAT_MAX_ADDRESS_LOOKUPS", "0")

    candidates = [
        _shrine("恋木神社", ["love"], goriyaku="心願成就"),
        _shrine("近隣神社", [], goriyaku=""),
    ]
    recs = build_chat_recommendations(
        query=query,
        language="ja",
        candidates=candidates,
        public_mode="need",
        flow="A",
    )

    assert "love" not in recs["_need"]["tags"]
    top1 = recs["recommendations"][0]
    assert top1["_primary_reason_label"] != "love"
    for phrase in LOVE_ONLY_PHRASES:
        assert phrase not in top1["reason"]
