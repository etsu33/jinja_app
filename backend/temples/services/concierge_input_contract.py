# backend/temples/services/concierge_input_contract.py
"""Concierge Chat request -> canonical input contract (Foundation).

Per docs/product/concierge-input-architecture.md (Architecture Decision)
and docs/audit/concierge-input-level-signal-inventory.md (PR #2397 audit),
this module makes the

    Raw User Input -> Canonical Request -> Compatibility Normalization
    -> Derived Signal -> Recommendation

boundary explicit in code, without changing any Recommendation behavior.
`normalize_birthdate()` and `_resolve_request_inputs_basic()` are moved
here verbatim from `api_views_concierge.py` (no logic change) so that the
phase-1 (request-parse-time) resolution has one canonical home.

Level tagging (Architecture Decision Signal Attribute Model, §6/§8):

    query            -> Level 1 Consultation (raw input; `message` is a
                         legacy alias folded into `query` at resolution
                         time, not a separate signal)
    birthdate        -> Level 3-A Personal Profile
    goriyaku_tag_ids -> Level 3-B Explicit Constraint. NOT Personal Profile
                         data -- PR #2397 confirmed this is a DB-level hard
                         candidate filter, not user identity data.
    extra_condition  -> Level 2 Visit Preference (Legacy/Transitional
                         compatibility field, free-text keyword parsing).
    visit_preferences -> Level 2 Visit Preference (Structured, canonical
                         tags -- see temples/domain/visit_preference.py and
                         docs/product/concierge-input-architecture.md
                         Addendum: Level 2 Visit Preference Signal Redesign).
                         Session/Request-scoped, never persisted as Personal
                         Profile data.
    lat/lng/radius_m/visit_date -> Level 3-C Context (see
                         ConciergeRecommendationContext below for why this
                         is a separate type, resolved separately).

Derived Signals (`need_tags`, `consultation_axis`, `interpretation_profile`,
`intent`) are intentionally NOT part of this contract -- they are Runtime
Derived Signals computed downstream from `query`, never raw request input
(Architecture Decision §4, Core Principle 5). Nothing in this module
computes or references them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

from temples.domain.visit_preference import normalize_visit_preferences

# ---------------------------------------------------------------------------
# Compatibility normalization (moved from api_views_concierge.py, unchanged)
# ---------------------------------------------------------------------------

BIRTHDATE_PATTERNS = (
    re.compile(r"^(\d{4})-(\d{2})-(\d{2})$"),
    re.compile(r"^(\d{4})/(\d{2})/(\d{2})$"),
    re.compile(r"^(\d{4})(\d{2})(\d{2})$"),
)


def normalize_birthdate(value: Any) -> str | None:
    """Compatibility normalization: accepts YYYY-MM-DD / YYYY/MM/DD / YYYYMMDD.

    Invalid input is discarded (returns None), never raises -- see
    docs/core/concierge-spec.md §0.2 for the accepted format contract.
    """
    s = str(value or "").strip()
    if not s:
        return None

    for pattern in BIRTHDATE_PATTERNS:
        m = pattern.match(s)
        if not m:
            continue

        yyyy, mm, dd = m.groups()

        try:
            normalized = date(int(yyyy), int(mm), int(dd))
        except ValueError:
            return None

        return normalized.isoformat()

    return None


def _resolve_request_inputs_basic(data: Dict[str, Any]):
    """Compatibility normalization: top-level/filters merge, message/query
    coalesce, query -> birthdate rescue.

    Mutates `data` in place -- this is existing behavior, not new. Later,
    independent `request.data.get(...)` reads elsewhere in the view (e.g.
    `_build_chat_candidates_pipeline`'s own `data.get("goriyaku_tag_ids")`)
    rely on this mutation having already happened on the same `data`
    object (see docs/audit/concierge-input-level-signal-inventory.md).

    Moved verbatim from api_views_concierge.py -- no logic change.
    """
    filters = data.get("filters") if isinstance(data.get("filters"), dict) else {}
    for k in ("birthdate", "goriyaku_tag_ids", "extra_condition"):
        if data.get(k) in (None, "", []) and filters.get(k) not in (None, "", []):
            data[k] = filters.get(k)

    filters = data.get("filters") or {}
    if isinstance(filters, dict):
        if not data.get("birthdate") and filters.get("birthdate"):
            data["birthdate"] = filters.get("birthdate")

    if not data.get("goriyaku_tag_ids") and filters.get("goriyaku_tag_ids"):
        data["goriyaku_tag_ids"] = filters.get("goriyaku_tag_ids")
    if not data.get("extra_condition") and filters.get("extra_condition"):
        data["extra_condition"] = filters.get("extra_condition")

    message = (data.get("message") or "").strip()
    query = (data.get("query") or "").strip()
    query = message or query

    # backend救済: query が日付文字列なら birthdate に寄せる
    birthdate_raw = normalize_birthdate(data.get("birthdate"))

    if not birthdate_raw and isinstance(filters, dict):
        birthdate_raw = normalize_birthdate(filters.get("birthdate"))
        if birthdate_raw:
            data["birthdate"] = birthdate_raw

    if not birthdate_raw:
        rescued_birthdate = normalize_birthdate(query)
        if rescued_birthdate:
            data["birthdate"] = rescued_birthdate
            birthdate_raw = rescued_birthdate
            query = ""

    language = (data.get("language") or "ja").strip()
    area = data.get("area") or data.get("where") or data.get("location_text")

    birthdate = data.get("birthdate")
    goriyaku_tag_ids = data.get("goriyaku_tag_ids")
    extra_condition = data.get("extra_condition")

    return (
        query,
        message,
        language,
        area,
        birthdate,
        goriyaku_tag_ids,
        extra_condition,
    )


# ---------------------------------------------------------------------------
# Canonical Concierge Input Contract (Level 1 / Level 2 / Level 3-A / 3-B)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConciergeCanonicalInput:
    """Canonical, Level-tagged view of the phase-1 (request-parse-time)
    Concierge Chat input. Built by `normalize_concierge_request()`.

    Field -> Level mapping (see module docstring and
    docs/product/concierge-input-architecture.md):

        query            -> Level 1 Consultation (raw input)
        birthdate        -> Level 3-A Personal Profile
        goriyaku_tag_ids -> Level 3-B Explicit Constraint (NOT Profile data)
        extra_condition  -> Level 2 Visit Preference (Legacy/Transitional)
        visit_preferences -> Level 2 Visit Preference (Structured, canonical
                            tags -- see temples/domain/visit_preference.py)
        language, area   -> neutral request metadata (`area` also feeds
                            Level 3-C Context resolution downstream, see
                            ConciergeRecommendationContext)
        message          -> legacy alias, folded into `query`; kept on the
                            struct only for callers that still need to
                            distinguish which raw field was sent (e.g.
                            `mode_label` telemetry)
    """

    query: str
    message: str
    language: str
    area: Any
    birthdate: Optional[str]
    goriyaku_tag_ids: Any
    extra_condition: Any
    visit_preferences: List[str]


def normalize_concierge_request(data: Dict[str, Any]) -> ConciergeCanonicalInput:
    """Raw Request -> Canonical Concierge Input (phase 1).

    Wraps the existing, unchanged `_resolve_request_inputs_basic()`
    compatibility normalization. This is the phase-1 resolution entry
    point Recommendation Service callers should use going forward; the
    underlying compatibility mechanics (top-level/filters duplication,
    query->birthdate rescue) are unchanged in this PR -- see
    docs/audit/concierge-input-level-signal-inventory.md Gap C and
    Follow-up PR1 in the Architecture Decision.

    `visit_preferences` is a new field (Level 2 Visit Preference Signal
    Redesign) with no legacy top-level/filters duplication to carry
    forward -- it is read from top-level `visit_preferences` only, and
    validated against the canonical tag vocabulary
    (temples/domain/visit_preference.normalize_visit_preferences()).
    Unlike `birthdate`/`goriyaku_tag_ids`/`extra_condition`, it does not
    inherit Gap C (Duplicate Signals).
    """
    (
        query,
        message,
        language,
        area,
        birthdate,
        goriyaku_tag_ids,
        extra_condition,
    ) = _resolve_request_inputs_basic(data)

    visit_preferences = normalize_visit_preferences(data.get("visit_preferences"))

    return ConciergeCanonicalInput(
        query=query,
        message=message,
        language=language,
        area=area,
        birthdate=birthdate,
        goriyaku_tag_ids=goriyaku_tag_ids,
        extra_condition=extra_condition,
        visit_preferences=visit_preferences,
    )


# ---------------------------------------------------------------------------
# Level 3-C Recommendation Context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConciergeRecommendationContext:
    """Canonical, Level-tagged shape of Level 3-C Context input
    (`lat`/`lng`/`radius_m`/`visit_date`).

    Deliberately NOT resolved by `normalize_concierge_request()` and
    deliberately not yet constructed at the view's call site in this PR:
    `lat`/`lng` resolution (`_resolve_request_location_inputs`, still in
    `api_views_concierge.py`) can trigger an external geocode call, and
    the existing view intentionally resolves it only *after* the quota
    gate passes, to avoid a wasted geocode call for a request that will
    be rejected anyway. Moving that resolution earlier -- or duplicating
    it here -- would be a behavior change (extra external calls for
    blocked/invalid requests), which this Foundation PR explicitly does
    not make. See docs/product/concierge-input-architecture.md §6 (Level
    3-C Context) and Follow-up PR4.

    `build_concierge_recommendation_context()` below is provided as a
    pure, tested packaging helper for callers (including Follow-up PRs)
    that already have `lat`/`lng`/`radius_m`/`visit_date` resolved and
    want the canonical, Level-tagged shape.
    """

    lat: Optional[float]
    lng: Optional[float]
    radius_m: int
    visit_date: Any


def build_concierge_recommendation_context(
    *,
    lat: Optional[float],
    lng: Optional[float],
    radius_m: int,
    visit_date: Any,
) -> ConciergeRecommendationContext:
    """Package already-resolved Level 3-C values into the canonical shape.

    Pure packaging only -- does not resolve, geocode, or default anything
    itself. Callers must resolve `lat`/`lng`/`radius_m`/`visit_date`
    exactly as the existing view does before calling this.
    """
    return ConciergeRecommendationContext(
        lat=lat,
        lng=lng,
        radius_m=radius_m,
        visit_date=visit_date,
    )


# ---------------------------------------------------------------------------
# Level 3-A Personal Profile: profile_context birthdate precedence
# ---------------------------------------------------------------------------


def resolve_profile_context_birthdate(
    profile_context: Optional[Dict[str, Any]],
) -> Optional[str]:
    """Level 3-A Personal Profile: `profile_context.user_profile.{birthdate,birthday}`.

    Moved verbatim from api_views_concierge.py -- no logic change.

    IMPORTANT: this is a SEPARATE precedence chain from
    `ConciergeCanonicalInput.birthdate` (the one used for astrology/element
    scoring in `_attach_breakdown`). This one is consulted ONLY for
    direction-calc (`planned_visit_lucky_directions`/`annual_lucky_directions`),
    where the call site uses `resolve_profile_context_birthdate(...) or
    canonical_input.birthdate` -- i.e. profile_context wins over the
    canonical scoring birthdate for direction-calc specifically.

    This two-precedence-chain split is a documented Current Gap (see
    docs/product/concierge-input-architecture.md Addendum: Level 3 Profile
    / Explicit Constraint / Recommendation Context Contract), not unified
    in this PR -- unifying them would change existing direction-calc
    results for requests where profile_context and canonical birthdate
    disagree, which is out of scope here.
    """
    profile_user = profile_context.get("user_profile") if isinstance(profile_context, dict) else None
    if not isinstance(profile_user, dict):
        return None
    return profile_user.get("birthdate") or profile_user.get("birthday")
