> **Status: Active**
>
> This is a **measurement / contract / root-cause audit**, not an
> implementation. It does not modify Backend production code, Frontend
> production code, Runtime, Recommendation Ranking, Concierge, Analytics
> instrumentation, shrine data, or the DB. It defines Recommendation
> Availability, traces the code that determines it, and reports what could
> and could not be measured in this session's execution environment.
> **Production PostHog access and production DB access were both
> unavailable in this session** (no MCP/API tool, no credentials, no linked
> project) — the production-measurement portions are explicitly classified
> as blocked below, per this task's own instruction not to invent results.

# Compass Recommendation Availability Audit

## 1. Purpose

[`compass-product-direction-decision.md`](../product/compass-product-direction-decision.md)
(#2508) and every subsequent Compass document in this audit chain have
repeatedly deferred the same question: **Direction Availability (96.9%
under Option C) is not Recommendation Availability.** This audit defines
Recommendation Availability precisely, traces the current code that
determines it, classifies why zero-candidate results occur, and reports
what is and is not currently measurable — without implementing anything.

---

## 2. Canonical Boundaries

- [`compass-product-contract.md`](../product/compass-product-contract.md)
  Section 2.1-5: Shrine Recommendation boundary remains an explicit
  **OPEN PRODUCT DECISION**, untouched by this audit.
- [`compass-product-direction-decision.md`](../product/compass-product-direction-decision.md)
  Section 12/16: Recommendation Availability evidence does not exist for
  any Direction Logic option — this is the first audit to attempt it.
- [`compass-monthly-fallback-ui-analytics-boundary.md`](compass-monthly-fallback-ui-analytics-boundary.md)
  Section 14 (KPI Boundary): restates the same boundary yet again and is
  the direct predecessor of this audit's Section 22.
- This audit does not resolve the OPEN PRODUCT DECISION above — it only
  measures the availability dimension needed to eventually inform it.

---

## 3. Current Recommendation Flow (traced against current `develop`)

```
CompassRecommendationsView.post()                    api_views_compass.py:44-88
  |
  v
build_compass_direction_runtime(birthdate, target_date)   compass_runtime.py:70-127
  -> dict (COMMON, calculationMethod=annual_monthly_kyusei_v1)
  -> dict (MONTHLY_FALLBACK, calculationMethod=monthly_kyusei_v1)
  -> NoCommonDirectionResult()  (narrowed, #2508)
  -> None  (Group A invalid/unavailable runtime)
  |
  v
get_compass_recommendations(purpose, origin, direction_context)  compass_recommendation_orchestrator.py:86-203
  1. purpose not in NEED_TAGS?              -> STATE_INVALID_PURPOSE          (:106-112)
  2. isinstance(direction_context,
     NoCommonDirectionResult)?              -> STATE_NO_COMMON_DIRECTION      (:114-119)
  3. not isinstance(direction_context,
     Mapping)? (i.e. was None)              -> STATE_DIRECTION_FILTER_UNAVAILABLE (:121-126)
  4. build_chat_candidates(...)              concierge_chat_candidates.py:54-189
     (candidate pool: lat/lng+address required, QA fixtures excluded,
     pool_limit = max(candidate_pool_limit*5, 50) = 300 for Compass's
     candidate_pool_limit=60)
  5. filter_candidates_by_direction(pool, origin, referenceDirections)  compass_direction_filter.py:29-92
     -> None (origin/reference_directions invalid)  -> STATE_DIRECTION_FILTER_UNAVAILABLE (:152-157)
     -> []   (no shrine in the authorized 8-direction sector(s)) -> STATE_DIRECTION_ZERO_CANDIDATES (:159-164)
  6. build_chat_recommendations(candidates=filtered, ...)  concierge_chat.py:636-...
     (shared Concierge Ranking domain, reused unmodified)
     -> recommendations == []  -> STATE_EVIDENCE_ZERO_CANDIDATES (:185-196)
     -> recommendations != []  -> STATE_RECOMMENDATION_SUCCESS   (:198-203)
  |
  v
CompassRecommendationsView response body               api_views_compass.py:70-88
  |
  v
CompassClient.tsx (handleSubmit)                        CompassClient.tsx:136-165
  |
  v
trackCompassResult() -> trackSearchEvent("compass_result", {..., calculationMethod})
```

---

## 4. Result State Inventory

| State | Runtime meaning | Direction available? | Recommendation available? | Technical error? | Denominator? | Numerator? |
|---|---|---|---|---|---|---|
| `recommendation_success` | ≥1 shrine returned by Ranking | YES | YES | NO | **YES** | **YES** |
| `direction_zero_candidates` | usable direction, but no shrine survived geographic sector filter | YES | NO | NO | **YES** | NO |
| `evidence_zero_candidates` | usable direction + non-empty candidate pool, but Ranking returned zero (defensive branch — see Section 8) | YES | NO | NO | **YES** | NO |
| `no_common_direction` | valid, completed calculation; no usable direction after Monthly Fallback (narrowed, #2508) | NO | N/A (never attempted) | NO | **NO** (excluded) | N/A |
| `direction_filter_unavailable` | invalid/unavailable runtime (missing birthdate/origin, invalid `reference_directions`, exception) | NO | N/A (never attempted) | YES | **NO** (excluded) | N/A |
| `invalid_purpose` | request-level validation failure, before any direction/candidate work | N/A (not reached) | N/A | NO (client error) | **NO** (excluded) | N/A |
| `backend_error` (frontend-only) | network exception or non-2xx/non-400 HTTP response | N/A (not reached) | N/A | YES | **NO** (excluded) | N/A |

Verified directly against `backend/temples/services/compass_recommendation_orchestrator.py:49-54`
(current `develop`, unchanged since the prior UI/Analytics Boundary audit —
no drift) and `CompassClient.tsx:34-41`'s mirrored frontend union (also
unchanged).

---

## 5. Recommendation Availability Definition

**Recommendation Availability** answers: *of the Compass attempts where a
usable reference direction was resolved and the Recommendation stage was
eligible to run, how many actually returned at least one shrine?*

```
Recommendation Availability =
    count(result_state = recommendation_success)
    -----------------------------------------------------------------
    count(result_state ∈ {recommendation_success,
                           direction_zero_candidates,
                           evidence_zero_candidates})
```

This matches the task's candidate definition (Section 11) exactly —
confirmed against code, not assumed: all three denominator states are
reached only *after* a usable `direction_context` (COMMON or
MONTHLY_FALLBACK dict) already produced a non-null `referenceDirections`
(Section 3 steps 4-6). No other state satisfies "direction resolved,
Recommendation stage eligible."

---

## 6. Numerator / Denominator

```
Numerator:    recommendation_success
Denominator:  recommendation_success + direction_zero_candidates + evidence_zero_candidates
```

## 6-1. `recommendation_success` contract (verified)

- At least one shrine **is** required: the orchestrator explicitly branches
  on `if not recommendations:` before returning
  `STATE_RECOMMENDATION_SUCCESS` (`compass_recommendation_orchestrator.py:185-203`)
  — the empty case is diverted to `evidence_zero_candidates` first. There is
  **no code path** that returns `recommendation_success` with
  `recommendation_count == 0`.
- It is **after** candidate pool construction, geographic direction
  filtering, and the full `build_chat_recommendations()` Ranking call — not
  a pre-Ranking check.
- `recommendation_count` sent to Analytics is `body.recommendations?.length
  ?? 0` (`CompassClient.tsx:158`), computed from the same array the state
  decision is based on — guaranteed >0 whenever `result_state ===
  "recommendation_success"`.
- Recommendation objects are already ranked: `build_chat_recommendations()`
  is the same, unmodified Concierge Ranking entry point
  (`concierge_chat.py:636`) Compass reuses without custom weights —
  confirmed by `TestRankingAndReasonAuthorityUnchanged::test_orchestrator_does_not_pass_custom_weights`
  in `test_compass_recommendation_orchestrator.py`.

## 6-2. `direction_zero_candidates` contract (verified)

Exact path: `referenceDirections` (from a valid `direction_context`) is
passed to `filter_candidates_by_direction()`
(`compass_direction_filter.py:29-92`), which returns an **empty list**
(not `None`) when the candidate pool contains shrines but none of them
resolve to a bearing inside any of the authorized 8-direction sectors from
`origin`. This is distinct from `None` (returned only when `origin` or
`reference_directions` themselves are invalid/missing —
`compass_direction_filter.py:53-64` — which instead produces
`direction_filter_unavailable`, Section 3 step 5). Confirmed: **usable
direction exists, but no shrine survived geographic candidate selection.**

## 6-3. `evidence_zero_candidates` contract (verified — and important caveat)

Meaning per the orchestrator's own module: candidate pool was non-empty
*and* passed geographic direction filtering, but
`build_chat_recommendations()` returned zero recommendations anyway.

**This state is currently a defensive branch, not an empirically observed
one.** The orchestrator's own docstring at
`compass_recommendation_orchestrator.py:186-191` states this explicitly:
*"Not reachable under the traced Evidence Gate / pool-fill behavior today
... kept as an explicit branch so a future change to
build_chat_recommendations that does start dropping candidates surfaces as
this distinct state rather than silently looking like
direction_zero_candidates."* The only test exercising this state
(`TestEvidenceZeroCandidates::test_empty_recommendations_from_domain_maps_to_evidence_zero_candidates`,
`test_compass_recommendation_orchestrator.py:381-397`) does so by
**mocking** `build_chat_recommendations` to force `{"recommendations":
[]}` — it is not reproduced from real shrine/Evidence data. This is a real
distinction from `direction_zero_candidates` (Section 8 below), but under
current code it is **not** a live root cause of zero Recommendation
Availability in practice — it exists to catch a *future* regression, not a
*current* one.

---

## 7. Exclusions

| State | Why excluded from Recommendation Availability |
|---|---|
| `no_common_direction` | No usable direction was ever resolved (Section 2.2-4, #2508 narrowed semantics) — the Recommendation stage is never reached at all (`compass_recommendation_orchestrator.py:114-119` returns before candidate pool construction). Asking "did Recommendation succeed" is meaningless when it was never attempted. |
| `direction_filter_unavailable` | Group A: genuinely invalid/unavailable runtime (missing birthdate/origin, invalid `reference_directions`, or an exception) — `docs/product/compass-mvp-runtime-contract.md` Section 8. This belongs to **Runtime Reliability**, a separate metric (Section 22), not Product Availability. |
| `invalid_purpose` | Client-side request validation failure, before any direction/candidate/Recommendation work begins. Not a Compass runtime or Recommendation question at all. |
| `backend_error` | Network exception or unexpected HTTP status — infrastructure-level failure, same category as `direction_filter_unavailable` for this purpose. |

No exclusion is asserted merely because it is a `compass_result` — each is
justified by what the orchestrator's own code did (or didn't) attempt.

---

## 8. Analytics Measurement Readiness

Traced against `CompassClient.tsx` and `compass_recommendation_orchestrator.py`
(current `develop`, includes #2513's `calculationMethod` property):

`calculationMethod` is present on `direction_context` for **every** state
that reaches the denominator. The orchestrator passes
`direction_context=direction_context` (the same dict, untouched) into
`CompassRecommendationResult` for `direction_zero_candidates`
(`:159-164`), `evidence_zero_candidates` (`:192-196`), and
`recommendation_success` (`:198-203`) alike — `calculationMethod` is never
stripped between a valid direction resolving and any of these three
states. `CompassClient.tsx:159` forwards
`body.direction_context?.calculationMethod ?? null` regardless of
`body.state`.

**Classification: MEASURABLE (structurally)** for all three:

```
A. Overall Recommendation Availability:      MEASURABLE (structurally)
B. COMMON Recommendation Availability:       MEASURABLE (structurally)
C. MONTHLY_FALLBACK Recommendation Availability: MEASURABLE (structurally)
```

"Structurally" qualifies this: the *code* guarantees the property is
present and correct wherever needed. Whether it is *actually queryable
right now* depends on production PostHog access, which this session does
not have (Section 10/17).

---

## 9. Measurement Valid From

Per [`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md)
Section 9, `calculationMethod`'s Measurement Valid From remains
**`DEPLOYMENT DATE REQUIRED`** — not established even by the subsequent
Production QA audit
([`compass-monthly-fallback-ui-analytics-boundary.md`](compass-monthly-fallback-ui-analytics-boundary.md)
Section 23-5 explicitly left this open). This audit does not derive it
either — doing so requires the same Vercel/Render deployment-record
cross-check method already used for the `no_common_direction` boundary,
which requires production deployment API access this session does not
have. Any Recommendation Availability figure segmented by `calculationMethod`
is valid only from that (still unestablished) timestamp onward.

---

## 10. Observation Gate — BLOCKED

**Production PostHog access: unavailable in this session** (no MCP/API
tool exposed, no credentials, confirmed by tool search before the prior
Production QA audit and re-confirmed here — nothing has changed). Per this
task's own Section 18 instruction ("If no approved PostHog access exists...
STOP the production-query portion and classify it as blocked. Do not
invent results."), the following are **not reported** because they cannot
be honestly reported:

```
Eligible compass_result count:            BLOCKED — no production query access
recommendation_success count:             BLOCKED
direction_zero_candidates count:          BLOCKED
evidence_zero_candidates count:           BLOCKED
Distinct session/thread diversity:        BLOCKED
```

The only production evidence available to this audit is the **two known
QA events** already recorded in
[`compass-monthly-fallback-ui-analytics-boundary.md`](compass-monthly-fallback-ui-analytics-boundary.md)
Section 23 (one COMMON, one MONTHLY_FALLBACK, both reported by the
repository owner as `result_state = recommendation_success`). Two data
points is not an observable population — no rate, ratio, or percentage is
computed from them here.

**Classification: INSUFFICIENT OBSERVATION** (for a rate); **BLOCKED** (for
raw production counts, since this session cannot query PostHog itself).

---

## 11. Overall Recommendation Availability

```
Value:  NOT COMPUTED — blocked (Section 10)
Status: INSUFFICIENT OBSERVATION / BLOCKED
```

## 12. COMMON Recommendation Availability

```
Value:  NOT COMPUTED — blocked (Section 10)
Status: INSUFFICIENT OBSERVATION / BLOCKED
```

## 13. MONTHLY_FALLBACK Recommendation Availability

```
Value:  NOT COMPUTED — blocked (Section 10)
Status: INSUFFICIENT OBSERVATION / BLOCKED
```

No percentage is fabricated for any of the three above. This audit's
contribution is the **definition** (Section 5-7) and the **structural
measurability proof** (Section 8) — not a number, because the number
requires access this session doesn't have.

---

## 14. Recommendation Count Distribution

Not computed, for the same reason as Section 11-13 — `recommendation_count`
is a `compass_result` property (confirmed present,
`compass-posthog-query-contract.md` §1), but its distribution requires the
same blocked production query access.

---

## 15. Zero-Candidate State Breakdown (production)

```
direction_zero_candidates: BLOCKED (Section 10)
evidence_zero_candidates:  BLOCKED (Section 10)
```

See Section 16-20 for the **structural** (code-level, not production-
volume) root-cause analysis this audit *could* perform.

---

## 16. DB Coverage Dependency

`build_chat_candidates()` (`concierge_chat_candidates.py:64-93`) applies,
before any direction filtering:

```python
qs = exclude_qa_fixture_shrines(qs)
qs = qs.select_related("place_ref")
qs = qs.prefetch_related("goriyaku_tags")
qs = qs.filter(latitude__isnull=False, longitude__isnull=False)
qs = qs.exclude(address="")
```

`Shrine.latitude`/`longitude` are nullable `FloatField`s and `address` is a
blank-allowed `CharField` (`backend/temples/models.py:220-236`) — a shrine
missing either is **structurally invisible to Compass** (and to Concierge)
regardless of direction, before geographic filtering even runs.

**This session's local development database** (not confirmed to mirror
production — no read-only production DB access method was established;
labeled explicitly as local-only):

```
Total shrines:              105
Missing lat/lng:            0
Missing/empty address:      0
Candidate-pool-eligible:    105 (100%)
```

This local figure cannot be extrapolated to production shrine coverage —
it only confirms the *filter exists* and demonstrates it is
*currently satisfiable* in this dataset. **Production DB coverage is
BLOCKED**, same as Section 10.

Knowledge (Evidence Gate) coverage, via the repository's own existing
read-only `knowledge_coverage_report` management command
(`backend/temples/management/commands/knowledge_coverage_report.py`), run
against this same local dataset (100 audit-target shrines, 5 QA fixtures
excluded):

```
Fact-ready Coverage (Any):        86.0%
Zero Knowledge (no usable Fact):  14.0%
```

This is a **diagnostic** figure about Reason richness, not about
Recommendation Availability directly — Section 6-3 already established
that Evidence Gate coverage does not currently exclude a shrine from
`recommendation_success` (the candidate still gets recommended; only its
Reason's evidentiary strength would be affected, per `evidence_gate.py`'s
`decide_fact_usability()`, which controls Reason `display_mode`/
`reason_strength`, not candidate inclusion).

---

## 17. Geographic Sector Dependency

`compass_direction_filter.py:29-92` (unchanged since the last audit):

```
Sectors:            8 (北/北東/東/南東/南/南西/西/北西, 45° each)
Boundaries:         reused from direction_reference.py's existing
                    _direction_label() — no separate Compass-specific
                    geometry
Boundary tolerance: none beyond the existing 45°-sector midpoint rounding
Edge-case handling: a bearing exactly on a sector boundary resolves to
                    whichever sector _direction_label()'s existing
                    (unchanged) rounding assigns it to -- not modified or
                    re-verified by this audit (out of scope: Section 32,
                    "do not change geometry")
Multiple directions: reference_directions can hold >1 label (e.g. COMMON's
                    intersection); filter_candidates_by_direction() unions
                    them -- a candidate matching ANY authorized sector
                    passes (compass_direction_filter.py:58-64,89)
```

**Structural demonstration** (local dev data, Tokyo-Station-area origin,
35.6762/139.6503 — illustrative only, not a production measurement):

```
西 (West):      32 shrines
東 (East):      24 shrines
北西 (NW):      11 shrines
北 (North):     11 shrines
北東 (NE):      11 shrines
南西 (SW):       8 shrines
南 (South):      5 shrines
南東 (SE):       3 shrines
```

Even in this small local dataset, sector density is highly uneven (32 vs.
3, roughly a 10x spread). This demonstrates the *mechanism* by which
`direction_zero_candidates` can occur — a resolved direction landing in a
sparsely-populated sector for a given origin — without claiming this
distribution holds in production.

---

## 18. Distance Dependency

`compass_direction_filter.py` itself has **no explicit radius/distance
cutoff** — it only tests bearing-to-sector membership
(`_bearing()`/`_direction_label()`, reused from `direction_reference.py`).
The only distance-related constraint in the flow is **upstream**, in
`build_chat_candidates()` (`concierge_chat_candidates.py:92-93,148-164`):

```python
pool_limit = max(limit * 5, 50)   # Compass passes limit=60 -> pool_limit=300
...
candidates.sort(key=lambda c: (float(c.get("distance_m") or 1e12), ...))
...
candidates = candidates[:pool_limit]
```

Candidates are sorted **nearest-first** and truncated to `pool_limit`
(300 for Compass) *before* direction filtering ever sees them. If the 300
geographically-nearest shrines to `origin` happen to contain none in the
resolved sector, `direction_zero_candidates` results — **even if a
matching shrine exists further away, outside the pre-filter pool.** This
is a soft, pool-size-driven distance dependency, not a hard radius, and it
was not changed by this audit (Section 32/33 prohibit ranking/candidate
logic changes) — it is documented here as a structural cause, to be
weighed against actual production pool-truncation frequency once
Observation Gate access exists (Section 10).

---

## 19. Origin Dependency

Structural dependency identified (not measured — Section 27 explicitly
defers segmented-rate calculation without data volume):

- `device`/`prefecture`/`manual`(`station`,`address`) origin modes all
  resolve to a single `{lat, lng}` pair before reaching
  `get_compass_recommendations()` — the direction filter and candidate
  query treat all origin modes identically once resolved to coordinates.
- `prefecture` mode uses a single representative point per prefecture
  (`packages/shared/userOrigin.ts`'s `PREFECTURE_ORIGINS`) — meaningfully
  coarser than `device`'s precise GPS coordinate, which structurally
  changes which shrines are "nearest" and could shift which shrines fall
  inside `pool_limit` (Section 18) differently by origin mode.
- No code path excludes or specially handles any origin mode differently
  for direction filtering or candidate pool construction — the dependency
  is entirely a byproduct of coordinate precision affecting distance
  sorting, not an explicit branch.

---

## 20. Evidence Gate Dependency

Re-confirmed from Section 6-3/16: `evidence_gate.py`'s `decide_fact_usability()`
governs **Fact display strength within a Recommendation Reason**
(`display_mode`, `reason_strength`) — it is not consulted by
`build_chat_candidates()` to exclude a shrine from the candidate pool, and
the orchestrator's own `evidence_zero_candidates` branch is untested
against real Evidence Gate behavior (only against a mock, Section 6-3).
**Current classification: this is an intentional Product quality
constraint on Reason richness, not a data-coverage gate on Recommendation
Availability** — 14% "zero knowledge" shrines (Section 16, local data)
still appear as `recommendation_success` candidates today, per the traced
code.

---

## 21. Root-Cause Taxonomy

| Cause | Structurally possible? | Observed in production? | Basis |
|---|---|---|---|
| `GEOGRAPHIC_COVERAGE` (sparse shrine density in resolved sector) | YES | BLOCKED (no production query access) | Section 17 |
| `DISTANCE_CONSTRAINT` (pool-size truncation before direction filter) | YES | BLOCKED | Section 18 |
| `MISSING_COORDINATES` (shrine lacks lat/lng or address) | YES (structurally excludable) | BLOCKED (local dataset shows 0% missing, not extrapolable) | Section 16 |
| `QUERY_FILTER` (QA fixture exclusion, `goriyaku_tag_ids` filter when present) | YES | BLOCKED | Section 16 |
| `EVIDENCE_GATE` | **NO** (does not currently exclude candidates, Section 20) | N/A — structurally not a cause under current code | Section 6-3, 20 |
| `ORIGIN_RESOLUTION` (coarse prefecture point vs. precise device GPS) | YES (indirect, via distance sort) | BLOCKED | Section 19 |
| `UNKNOWN` | — | Cannot be ruled in or out without production data | Section 10 |

Only structural possibility is assessed here — no percentage attribution
is made without production evidence, per this task's explicit instruction.

---

## 22. Direction Availability Relationship

| Metric | Question answered | Current value/status |
|---|---|---|
| Runtime Reliability | Did the calculation complete without error? | Not measured by this audit (see `compass-posthog-query-contract.md` §8 OPERATIONAL KPIs) |
| Direction Availability | Did Compass resolve a usable reference direction? | **96.9%** (theoretical, Option C matrix, `compass-monthly-fallback-availability.md`) |
| Recommendation Availability | Given a resolved direction, did ≥1 shrine come back? | **NOT COMPUTED — BLOCKED** (Section 11) |
| Product engagement | Did the user do anything with the result? | Out of scope (deferred to a future Visit Funnel task per prior conversation) |

**96.9% Direction Availability does not imply 96.9% Recommendation
Availability** — restated explicitly, per this task's Section 31
instruction, because every metric above answers a genuinely different
question and none may be substituted for another.

---

## 23. KPI Boundary

`calculationMethod` (COMMON/MONTHLY_FALLBACK) and the Recommendation
Availability metric defined here remain **diagnostic/measurement
dimensions**. This audit does not redefine, and this document does not
claim any change to:

```
Runtime Reliability Rate
Direction Availability Rate
Recommendation Delivery Rate (compass-posthog-query-contract.md §8 —
  this audit's "Recommendation Availability" is conceptually the same
  metric that document already named OPERATIONAL; this audit adds the
  code-level contract and structural analysis, not a redefinition)
Recommendation CTR
```

No claim is made that Monthly Fallback increases or decreases
Recommendation Availability relative to COMMON — no data exists in this
session to support either direction (Section 10).

---

## 24. Recommendation Ranking Boundary

```
Recommendation Ranking changed: NO
```

Inspected only to locate the boundary (Section 6-1, 6-3): `build_chat_recommendations()`
(`concierge_chat.py:636`) is called by Compass with no custom weights,
confirmed by the existing, unmodified
`TestRankingAndReasonAuthorityUnchanged` test class. No weight, score,
ordering, or Reason-generation logic was read in more depth than needed to
confirm this boundary, and none was changed.

---

## 25. Concierge Boundary

```
Concierge changed: NO
```

`api_views_concierge.py` was not touched. `build_chat_candidates()` and
`build_chat_recommendations()` are shared, unmodified Concierge domain
functions Compass already reused before this audit (`compass-product-contract.md`
Section 1's "Signal Reuse, not Authority Reuse" boundary, unaffected). No
Compass-specific Availability policy was proposed for, or imported into,
Concierge.

---

## 26. Measurement Gaps

```
1. Production PostHog query access: BLOCKED (no MCP/API tool, no
   credentials) -- blocks Sections 11-15, 21's production-observed column.
2. Production DB read-only access: BLOCKED (no established method) --
   blocks extrapolating Section 16's local-only DB coverage figures to
   production.
3. calculationMethod Measurement Valid From: still DEPLOYMENT DATE
   REQUIRED (Section 9) -- unresolved by two prior audits already, not
   resolved by this one either.
4. evidence_zero_candidates: untested against real Evidence Gate data
   (Section 6-3) -- if this ever becomes reachable in practice (a future
   change to build_chat_recommendations), this audit's Section 21
   classification of EVIDENCE_GATE as "not currently a cause" would need
   re-verification.
```

---

## 27. Product Interpretation

Recommendation Availability is now **fully defined and structurally
measurable** — every state in the denominator carries `calculationMethod`
without loss (Section 8), and the metric's numerator/denominator boundary
is grounded in code, not assumption (Section 5-7). What remains is purely
an **access problem**, not a design or instrumentation problem: this
session cannot query production PostHog or production Postgres to compute
an actual value. No product conclusion (whether Recommendation
Availability is "good enough," whether COMMON differs from
MONTHLY_FALLBACK, whether shrine data coverage is a bottleneck) can be
drawn without that access.

---

## 28. Next Implementation Gate

```
G — INSUFFICIENT OBSERVATION; WAIT FOR DATA
```

Reasoning: this is not classification **E** (Analytics Gap) — Section 8
already proved the analytics gap from the prior audit chain is closed
(`calculationMethod` is present everywhere needed). It is not **F**
(Implementation Defect) — nothing traced in Sections 3-8 indicates a
defect; `evidence_zero_candidates` being untested against real data
(Section 6-3) is a coverage gap in test *and* production evidence, not a
known-wrong behavior. It is not **B/C/D** (data/filter/evidence work
needed) — Section 21 shows these are all *structurally possible* causes,
but none is confirmed as an *actual* production bottleneck, because no
production data was accessible. The only honest classification is **G**:
the definition and instrumentation are ready; what's needed next is actual
production observation access (PostHog query capability, and/or a
read-only production DB reporting method), not another docs-only audit
and not an implementation PR.

---

## 29. Non-goals

This audit does not:

- Fix any shrine data, geographic filter, Evidence Gate, or Ranking
  behavior.
- Establish `calculationMethod`'s Measurement Valid From timestamp.
- Compute any actual Recommendation Availability percentage (overall,
  COMMON, or MONTHLY_FALLBACK).
- Compare COMMON vs. MONTHLY_FALLBACK Recommendation Availability, CTR, or
  any other rate.
- Begin Visit Funnel, Premium, or UX redesign work.
- Resolve the Shrine Recommendation boundary (`compass-product-contract.md`
  Section 2.1-5) — still OPEN.

---

## 30. Impact

```
Production code changed:          NO
Frontend production code changed: NO
Backend production code changed:  NO
Analytics instrumentation changed: NO
Recommendation Ranking changed:   NO
Concierge changed:                NO
UI changed:                       NO
DB changed:                       NONE
Migration:                        NONE
```

---

## 31. Verification

```
git status --short   -> only this document (+ known untracked
                         apps/web/AGENTS.md, apps/web/CLAUDE.md, excluded)
git diff --stat       -> only this document
git diff --check      -> clean
```

All code citations in Sections 3-8, 16-20 were re-read directly from
current `develop` in this session (`compass_runtime.py`,
`compass_recommendation_orchestrator.py`, `concierge_chat_candidates.py`,
`compass_direction_filter.py`, `evidence_gate.py`, `models.py`,
`concierge_chat.py`), not assumed from prior audit docs. The local DB/
Knowledge Coverage figures (Section 16) were produced via the repository's
existing read-only `knowledge_coverage_report` management command and a
read-only aggregate SQL query against this session's local development
database — no data was written or modified.
