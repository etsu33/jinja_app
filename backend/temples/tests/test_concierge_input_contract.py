# backend/temples/tests/test_concierge_input_contract.py
"""Contract tests for temples.services.concierge_input_contract.

This is a pure Contract refactor -- normalize_concierge_request() wraps
the exact same compatibility logic that previously lived inline in
api_views_concierge.py (top-level/filters merge, message/query coalesce,
query->birthdate rescue). These tests pin that behavior down so a future
change cannot silently alter what reaches the Recommendation Service.

See docs/product/concierge-input-architecture.md (Architecture Decision)
and docs/audit/concierge-input-level-signal-inventory.md (PR #2397 audit)
for the Level tagging these fields correspond to.
"""

from temples.services.concierge_input_contract import (
    ConciergeCanonicalInput,
    build_concierge_recommendation_context,
    normalize_birthdate,
    normalize_concierge_request,
)


# -----------------------------------------------------------------------
# query / message (Level 1 Consultation)
# -----------------------------------------------------------------------


def test_query_only():
    canonical = normalize_concierge_request({"query": "縁結びの神社を知りたい"})
    assert canonical.query == "縁結びの神社を知りたい"
    assert canonical.message == ""


def test_message_only():
    canonical = normalize_concierge_request({"message": "転職で悩んでいます"})
    assert canonical.query == "転職で悩んでいます"
    assert canonical.message == "転職で悩んでいます"


def test_message_and_query_both_present_message_wins():
    canonical = normalize_concierge_request({"message": "message版", "query": "query版"})
    assert canonical.query == "message版"


def test_query_and_message_both_empty():
    canonical = normalize_concierge_request({"query": "", "message": ""})
    assert canonical.query == ""
    assert canonical.message == ""


def test_query_and_message_absent():
    canonical = normalize_concierge_request({})
    assert canonical.query == ""
    assert canonical.message == ""


def test_query_is_trimmed():
    canonical = normalize_concierge_request({"query": "  余白あり  "})
    assert canonical.query == "余白あり"


# -----------------------------------------------------------------------
# birthdate (Level 3-A Personal Profile)
# -----------------------------------------------------------------------


def test_birthdate_top_level():
    canonical = normalize_concierge_request({"query": "q", "birthdate": "1990-01-01"})
    assert canonical.birthdate == "1990-01-01"


def test_birthdate_from_filters_when_top_level_absent():
    canonical = normalize_concierge_request(
        {"query": "q", "filters": {"birthdate": "1990-01-01"}}
    )
    assert canonical.birthdate == "1990-01-01"


def test_birthdate_top_level_wins_over_filters():
    canonical = normalize_concierge_request(
        {
            "query": "q",
            "birthdate": "1990-01-01",
            "filters": {"birthdate": "1985-05-05"},
        }
    )
    assert canonical.birthdate == "1990-01-01"


def test_birthdate_compat_rescue_from_query():
    # No explicit birthdate anywhere, but query itself is a birthdate string.
    canonical = normalize_concierge_request({"query": "1990-01-01"})
    assert canonical.birthdate == "1990-01-01"
    # Rescue empties the query (existing behavior).
    assert canonical.query == ""


def test_birthdate_compat_rescue_does_not_apply_when_birthdate_already_set():
    canonical = normalize_concierge_request(
        {"query": "1990-01-01", "birthdate": "2000-12-31"}
    )
    assert canonical.birthdate == "2000-12-31"
    # Query is untouched because rescue only triggers when birthdate is absent.
    assert canonical.query == "1990-01-01"


def test_birthdate_empty():
    canonical = normalize_concierge_request({"query": "q"})
    assert canonical.birthdate is None


def test_birthdate_invalid_format_passes_through_unvalidated():
    """Pinning existing behavior: normalize_birthdate() is only consulted
    internally to decide whether a *rescue* from `query` should happen; it
    is not applied to a birthdate that was already explicitly provided.
    An invalid top-level `birthdate` string therefore passes through
    verbatim on the canonical struct -- format validation for an
    already-present birthdate happens downstream (e.g. astrology
    calculation), not in this normalization step. This is not new
    behavior introduced by this refactor; see
    test_concierge_astrology.py::test_chat_astrology_ignored_when_birthdate_invalid
    for the downstream guard.
    """
    canonical = normalize_concierge_request({"query": "q", "birthdate": "not-a-date"})
    assert canonical.birthdate == "not-a-date"


def test_normalize_birthdate_accepts_all_documented_formats():
    assert normalize_birthdate("1990-01-01") == "1990-01-01"
    assert normalize_birthdate("1990/01/01") == "1990-01-01"
    assert normalize_birthdate("19900101") == "1990-01-01"
    assert normalize_birthdate("garbage") is None
    assert normalize_birthdate(None) is None
    assert normalize_birthdate("") is None


# -----------------------------------------------------------------------
# goriyaku_tag_ids (Level 3-B Explicit Constraint -- NOT Profile data)
# -----------------------------------------------------------------------


def test_goriyaku_tag_ids_top_level():
    canonical = normalize_concierge_request({"query": "q", "goriyaku_tag_ids": [1, 2]})
    assert canonical.goriyaku_tag_ids == [1, 2]


def test_goriyaku_tag_ids_from_filters_when_top_level_absent():
    canonical = normalize_concierge_request(
        {"query": "q", "filters": {"goriyaku_tag_ids": [3]}}
    )
    assert canonical.goriyaku_tag_ids == [3]


def test_goriyaku_tag_ids_top_level_wins_over_filters():
    canonical = normalize_concierge_request(
        {"query": "q", "goriyaku_tag_ids": [1], "filters": {"goriyaku_tag_ids": [2]}}
    )
    assert canonical.goriyaku_tag_ids == [1]


def test_goriyaku_tag_ids_empty():
    canonical = normalize_concierge_request({"query": "q"})
    assert canonical.goriyaku_tag_ids is None


def test_goriyaku_tag_ids_empty_list_falls_back_to_filters():
    # An empty top-level list is treated as "absent" (matches existing
    # `data.get(k) in (None, "", [])` compatibility check).
    canonical = normalize_concierge_request(
        {"query": "q", "goriyaku_tag_ids": [], "filters": {"goriyaku_tag_ids": [5]}}
    )
    assert canonical.goriyaku_tag_ids == [5]


# -----------------------------------------------------------------------
# extra_condition (Level 2 Visit Preference, Legacy/Transitional)
# -----------------------------------------------------------------------


def test_extra_condition_top_level():
    canonical = normalize_concierge_request({"query": "q", "extra_condition": "駅近"})
    assert canonical.extra_condition == "駅近"


def test_extra_condition_from_filters_when_top_level_absent():
    canonical = normalize_concierge_request(
        {"query": "q", "filters": {"extra_condition": "静か"}}
    )
    assert canonical.extra_condition == "静か"


def test_extra_condition_top_level_wins_over_filters():
    canonical = normalize_concierge_request(
        {"query": "q", "extra_condition": "駅近", "filters": {"extra_condition": "静か"}}
    )
    assert canonical.extra_condition == "駅近"


def test_extra_condition_empty():
    canonical = normalize_concierge_request({"query": "q"})
    assert canonical.extra_condition is None


def test_free_text_and_crowd_are_not_backend_contract_fields():
    """free_text -> extra_condition and crowd -> extra_condition merging is
    performed entirely client-side (apps/web/src/features/concierge/hooks.ts).
    The backend contract never reads `filters.free_text` / `filters.crowd`
    -- by the time a request reaches normalize_concierge_request(), any
    such compatibility text has already been folded into extra_condition
    by the frontend. This test pins that boundary: sending free_text/crowd
    without extra_condition must NOT populate extra_condition server-side.
    """
    canonical = normalize_concierge_request(
        {
            "query": "q",
            "filters": {"free_text": "静かな場所", "crowd": ["quiet"]},
        }
    )
    assert canonical.extra_condition is None


# -----------------------------------------------------------------------
# language / area (neutral request metadata)
# -----------------------------------------------------------------------


def test_language_defaults_to_ja():
    canonical = normalize_concierge_request({"query": "q"})
    assert canonical.language == "ja"


def test_language_explicit():
    canonical = normalize_concierge_request({"query": "q", "language": "en"})
    assert canonical.language == "en"


def test_area_from_area_field():
    canonical = normalize_concierge_request({"query": "q", "area": "東京都"})
    assert canonical.area == "東京都"


def test_area_from_where_field_when_area_absent():
    canonical = normalize_concierge_request({"query": "q", "where": "大阪府"})
    assert canonical.area == "大阪府"


def test_area_from_location_text_field_when_others_absent():
    canonical = normalize_concierge_request({"query": "q", "location_text": "京都府"})
    assert canonical.area == "京都府"


def test_area_priority_area_over_where_over_location_text():
    canonical = normalize_concierge_request(
        {"query": "q", "area": "東京都", "where": "大阪府", "location_text": "京都府"}
    )
    assert canonical.area == "東京都"


# -----------------------------------------------------------------------
# Canonical struct shape
# -----------------------------------------------------------------------


def test_normalize_concierge_request_returns_frozen_dataclass():
    canonical = normalize_concierge_request({"query": "q"})
    assert isinstance(canonical, ConciergeCanonicalInput)


def test_canonical_input_does_not_include_derived_signals():
    """Raw Input / Derived Signal separation (Architecture Decision §4,
    Core Principle 5): need_tags, consultation_axis, interpretation_profile,
    and intent must never appear on the canonical struct -- they are
    Runtime Derived Signals computed downstream from `query`.
    """
    canonical = normalize_concierge_request({"query": "q"})
    field_names = set(canonical.__dataclass_fields__.keys())
    assert "need_tags" not in field_names
    assert "consultation_axis" not in field_names
    assert "interpretation_profile" not in field_names
    assert "intent" not in field_names


# -----------------------------------------------------------------------
# Compatibility mutation side effect (existing behavior, pinned)
# -----------------------------------------------------------------------


def test_normalize_concierge_request_mutates_data_in_place_for_downstream_reads():
    """_build_chat_candidates_pipeline (api_views_concierge.py) re-reads
    request.data.get("goriyaku_tag_ids") independently after phase-1
    resolution. This only works because _resolve_request_inputs_basic
    mutates `data` in place. This test pins that side effect explicitly
    so a future refactor does not silently break it.
    """
    data = {"query": "q", "filters": {"goriyaku_tag_ids": [7, 8]}}
    normalize_concierge_request(data)
    assert data["goriyaku_tag_ids"] == [7, 8]


# -----------------------------------------------------------------------
# Level 3-C Recommendation Context (packaging only)
# -----------------------------------------------------------------------


def test_build_concierge_recommendation_context_packages_values_verbatim():
    context = build_concierge_recommendation_context(
        lat=35.6, lng=139.7, radius_m=8000, visit_date="2026-09-01"
    )
    assert context.lat == 35.6
    assert context.lng == 139.7
    assert context.radius_m == 8000
    assert context.visit_date == "2026-09-01"


def test_build_concierge_recommendation_context_allows_none_lat_lng():
    context = build_concierge_recommendation_context(
        lat=None, lng=None, radius_m=8000, visit_date=None
    )
    assert context.lat is None
    assert context.lng is None
    assert context.visit_date is None
