> **Status: Sections 1-27 are the original PRODUCTION QUERY BLOCKED record
> — preserved unchanged as historical record, not rewritten as if access
> had never been blocked. Section 28 (new) records the valid-window
> measurement the repository owner subsequently obtained by running the
> prepared query directly.**
>
> This is a **measurement** record, not an implementation. It does not
> modify Backend production code, Frontend production code, Runtime,
> Recommendation Ranking, Concierge, Analytics instrumentation, or the DB.
> It attempts to execute the Recommendation Availability measurement
> [`compass-recommendation-availability.md`](compass-recommendation-availability.md)
> (#2515) defined, and could not — this session has no PostHog query
> capability (no MCP/API tool, no credentials), same limitation already
> established in
> [`compass-monthly-fallback-ui-analytics-boundary.md`](compass-monthly-fallback-ui-analytics-boundary.md).
> No count in Sections 1-27 is fabricated. Section 28's counts are
> **reported directly by the repository owner** from a production PostHog
> SQL query they ran themselves (Section 4's prepared Query 2, with the
> [#2517](compass-calculation-method-measurement-valid-from.md)-confirmed
> validity boundary applied) — not independently re-queried by this
> session, which still has no PostHog access.

# Compass Recommendation Availability — Production Measurement

## 1. Purpose

[`compass-recommendation-availability.md`](compass-recommendation-availability.md)
(#2515) defined Recommendation Availability, traced the code, and proved
the metric is structurally measurable — but could not compute an actual
value because this session has no production PostHog access. This record
attempts the actual measurement and documents the same blocker,
persistently, with the exact queries ready to run once access exists.

---

## 2. Canonical Metric Contract (locked, unchanged from #2515)

```
Numerator:    recommendation_success
Denominator:  recommendation_success + direction_zero_candidates + evidence_zero_candidates

Excluded from denominator:
  no_common_direction        -- no usable direction was ever resolved (Recommendation stage never reached)
  direction_filter_unavailable -- Group A invalid/unavailable runtime (Runtime Reliability, not Product Availability)
  invalid_purpose             -- request validation failure, before any direction/candidate work
  backend_error               -- frontend-only bucket, network/infra failure
```

No redefinition was made or considered. Re-confirmed against current
`develop`: `git log` shows no commits touching
`compass_recommendation_orchestrator.py`, `CompassClient.tsx`, or
`searchEvents.ts` since #2513 (Analytics Alignment) — the contract #2515
described from that same code is still exactly current. **No CONTRACT
DRIFT.**

---

## 3. Measurement Valid From

```
Status: DEPLOYMENT DATE REQUIRED (unresolved)
```

Same open item as
[`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md)
Section 9 and
[`compass-monthly-fallback-ui-analytics-boundary.md`](compass-monthly-fallback-ui-analytics-boundary.md)
Section 23-5 — neither this record nor #2515 established the exact
production deployment timestamp for `calculationMethod` on `compass_result`.
Establishing it requires the same Vercel/Render deployment-record
cross-check already used for the `no_common_direction` boundary
(`compass-posthog-query-contract.md` Section 9's existing row for that
state), which requires production deployment API access this session does
not have. **Any future COMMON/FALLBACK segmented query MUST filter
`timestamp >=` that boundary once established — not before.**

---

## 4. Production Query Method

```
Status: PRODUCTION QUERY BLOCKED
```

Checked in this session: no PostHog MCP/API tool is present (re-confirmed
by tool search immediately before this record was written — same result as
the prior two audits in this chain). No project ID, API key, or query
endpoint is available or was guessed. No production traffic was generated
to compensate (task Section 9 explicit prohibition, also this session's
own established practice throughout this audit chain).

**Exact aggregate queries required** (for the repository owner to run
manually in PostHog, or for a future session with query access):

**Query 1 — Result state population** (Section 10 of the task):

```sql
SELECT properties.result_state AS result_state, count() AS n
FROM events
WHERE event = 'compass_result'
  AND timestamp >= '<observation_window_start>'
GROUP BY result_state
ORDER BY n DESC
```

**Query 2 — COMMON / FALLBACK segmented eligible population** (Sections
14, 16 of the task; requires the Section 3 validity boundary once
established):

```sql
SELECT
  properties.calculationMethod AS calculation_method,
  properties.result_state AS result_state,
  count() AS n
FROM events
WHERE event = 'compass_result'
  AND timestamp >= '<calculationMethod_measurement_valid_from>'
  AND properties.result_state IN
      ('recommendation_success', 'direction_zero_candidates', 'evidence_zero_candidates')
GROUP BY calculation_method, result_state
ORDER BY calculation_method, result_state
```

Both queries use **only** `event`, `timestamp`, `properties.result_state`,
and `properties.calculationMethod` — no `distinct_id`, no user identity, no
raw event export. Preferred output shape for a manually-run query, per the
task's own instruction: `result_state | calculationMethod | count`.

---

## 5. Privacy Boundary

No birthdate, coordinates, raw origin, free text, `distinct_id`, email,
user ID, IP address, or credentials are requested by either query above, or
recorded anywhere in this document. Only `result_state`,
`calculationMethod`, and aggregate counts are in scope, matching
`compass-recommendation-availability.md` Section 5-7's own denominator
definition and this task's Section 8/38 privacy constraints.

---

## 6. Observation Window

```
Status: NOT ESTABLISHED — no query was run
```

No window start/end timestamp is chosen or assumed here — doing so without
being able to execute the query would just be a different form of
guessing. The placeholder `<observation_window_start>` in Section 4's
Query 1 is intentionally left for whoever actually runs it to fill in
(e.g. deployment date, or "all time" if the owner prefers a first look).

---

## 7. Production Population

```
Status: BLOCKED — not retrieved (Section 4)
```

## 8. Result State Counts

```
Status: BLOCKED
recommendation_success:        NOT RETRIEVED
direction_zero_candidates:     NOT RETRIEVED
evidence_zero_candidates:      NOT RETRIEVED
no_common_direction:           NOT RETRIEVED
direction_filter_unavailable:  NOT RETRIEVED
Unexpected/unknown states:     NOT RETRIEVED (Query 1, Section 4, would surface any)
```

## 9. Eligible Population

```
eligible_count = recommendation_success + direction_zero_candidates + evidence_zero_candidates
Status: BLOCKED — cannot be computed without Section 8's counts
```

## 10. Overall Recommendation Availability

```
Value:  NOT COMPUTED
Status: BLOCKED (not INSUFFICIENT OBSERVATION -- that classification
        would imply a query ran and returned a too-small population;
        here, no query ran at all)
```

## 11. COMMON Population

```
Status: BLOCKED — requires Query 2 (Section 4) and the Section 3
        validity boundary, neither available
```

## 12. COMMON Recommendation Availability

```
Value:  NOT COMPUTED
Status: BLOCKED
```

## 13. MONTHLY_FALLBACK Population

```
Status: BLOCKED — same as Section 11
```

## 14. MONTHLY_FALLBACK Recommendation Availability

```
Value:  NOT COMPUTED
Status: BLOCKED
```

## 15. Segment Reconciliation

```
Status: NOT APPLICABLE — no Overall or segmented counts exist to reconcile
```

Once Section 8 and Sections 11/13 are populated (by a future query), this
section must verify `COMMON eligible + MONTHLY_FALLBACK eligible` against
Overall eligible for the segmented-valid window, and if they don't
reconcile, attribute the gap to null/unknown `calculationMethod`, the
historical instrumentation boundary (Section 3), or an unexpected
`result_state` (Section 8) — not force them to match.

## 16. Zero-Candidate Breakdown

```
direction_zero_candidates: BLOCKED (production count)
evidence_zero_candidates:  BLOCKED (production count)
```

Kept separate per #2515 Section 6-2/6-3 and this task's Section 19 — not
merged even in this blocked state.

## 17. Evidence Zero Reachability

Reconfirmed against current `develop` (no drift, Section 2): the
`evidence_zero_candidates` branch
(`compass_recommendation_orchestrator.py:185-196`) is still only exercised
by a test that **mocks** `build_chat_recommendations` to force an empty
list (`TestEvidenceZeroCandidates::test_empty_recommendations_from_domain_maps_to_evidence_zero_candidates`,
`test_compass_recommendation_orchestrator.py:381-397`) — unchanged since
#2515. If Section 8's (currently blocked) production query eventually
returns `evidence_zero_candidates: 0`, that must be recorded as:

```
EXPECTED ZERO / CURRENTLY UNREACHABLE
```

— not as evidence the Evidence Gate is "working correctly," since the code
path was already known to be structurally unreachable from real data
before any query ran (#2515 Section 6-3).

## 18. Recommendation Count Distribution

```
Status: NOT MEASURABLE WITH CURRENT EVENT in this session (BLOCKED, same
        underlying cause as Section 4 -- recommendation_count IS a
        confirmed compass_result property per
        compass-posthog-query-contract.md §1, so this is an access
        blocker, not a Query Contract gap)
```

This does not block Recommendation Availability itself, which depends only
on `result_state` (per #2515 Section 5) — noted per the task's own
Section 21 instruction.

## 19. QA Traffic Boundary

The two known QA events from
[`compass-monthly-fallback-ui-analytics-boundary.md`](compass-monthly-fallback-ui-analytics-boundary.md)
Section 23 (one COMMON, one MONTHLY_FALLBACK, both
`recommendation_success`) exist in production PostHog, reported by the
repository owner. Checked: `compass_result` carries no property
distinguishing QA-originated events from organic ones (confirmed against
`SearchAnalyticsPayload` in `searchEvents.ts` — no `is_qa`/`test`-type flag
exists, and none should be added per this task's Section 24 prohibition on
new instrumentation).

```
QA TRAFFIC NOT RELIABLY SEPARABLE
```

Any future query's raw counts will include these 2 events indistinguishably
from organic traffic. No PostHog events were deleted or modified to work
around this (task Section 22 explicit prohibition).

---

## 20. Observation Sufficiency

```
Status: PRODUCTION QUERY BLOCKED (Section 4) -- distinct from
        INSUFFICIENT OBSERVATION, which would require a query to have
        actually returned a too-small population. Per this task's own
        Section 25 instruction: "If production data cannot be queried at
        all: H."
```

---

## 21. Direction Availability Relationship

```
Runtime Reliability:        not measured here
Direction Availability:     96.9% (theoretical, Option C matrix, unchanged)
Recommendation Availability: NOT COMPUTED -- BLOCKED
Product Engagement:          out of scope
```

96.9% is not multiplied by any Recommendation Availability figure here —
no such figure exists to multiply, and per #2515 Section 22/23 and this
task's Section 23, the two remain distinct metrics regardless.

---

## 22. Product Interpretation

No product conclusion is drawn. The metric contract, required queries, and
privacy-safe query shape are fully specified and ready to execute — the
only missing piece is production PostHog query access (or the repository
owner running Section 4's two queries manually and reporting the aggregate
`result_state | calculationMethod | count` rows back for this session, or
a future one, to calculate from).

---

## 23. Measurement Limitations

```
1. No PostHog query access in this session (Section 4) -- blocks every
   count in Sections 7-18.
2. calculationMethod Measurement Valid From still unresolved (Section 3)
   -- blocks segmented (COMMON/FALLBACK) analysis even once general query
   access exists, until established.
3. QA traffic is not separable from organic traffic in aggregate queries
   (Section 19) -- any future rate computed from Section 4's queries will
   include the 2 known QA events, an immaterial but non-zero contamination
   once real organic volume exists.
4. evidence_zero_candidates remains structurally unreachable under current
   code (Section 17) -- a future "0" count from this state must not be
   read as confirmation the Evidence Gate is functioning as a filter; it
   was already known to not be one.
```

---

## 24. Next Gate

```
H — PRODUCTION QUERY ACCESS BLOCKED
```

Per the task's own Section 25 rule: "If production data cannot be queried
at all: H." This is not **G** (Insufficient Observation) — G presumes a
query executed and returned a population too small to trust, which did not
happen here; no query executed at all. It is not **E** (Analytics Gap) —
#2515 and this record both confirm the analytics gap is closed
structurally (Section 2); the blocker is access, not instrumentation.

---

## 25. Non-goals

This record does not:

- Compute any Recommendation Availability percentage (overall, COMMON, or
  MONTHLY_FALLBACK).
- Establish `calculationMethod`'s Measurement Valid From timestamp.
- Redefine the Recommendation Availability metric from #2515.
- Generate any new production Compass traffic.
- Fix any shrine data, geographic filter, Evidence Gate, or Ranking
  behavior, even hypothetically.
- Begin Visit Funnel, Premium, or UX work.

---

## 26. Impact

```
Production code changed:          NO
Frontend production code changed: NO
Backend production code changed:  NO
Analytics instrumentation changed: NO
Runtime changed:                  NO
Recommendation Ranking changed:   NO
Concierge changed:                NO
DB changed:                       NONE
Migration:                        NONE
```

---

## 27. Verification

```
git status --short   -> only this document (+ known untracked
                         apps/web/AGENTS.md, apps/web/CLAUDE.md, excluded)
git diff --stat       -> only this document
git diff --check      -> clean
```

Metric re-confirmed against #2515 (Section 2, no drift). No denominator
change. No fabricated production counts anywhere in this document — every
numeric section above is explicitly `BLOCKED`/`NOT RETRIEVED`/`NOT
COMPUTED`. `calculationMethod` segmentation queries (Section 4, Query 2)
are written to require the Section 3 validity boundary once established.
Zero-candidate states kept separate throughout (Section 16). QA limitation
documented (Section 19). No PII in any query or in this document. No
production code changed.

---

## 28. Valid Window Production Measurement

> Everything in this section is **reported by the repository owner**, who
> ran Section 4's prepared Query 2 (with `timestamp >=
> 2026-08-22T01:09:00Z`, the boundary
> [#2517](compass-calculation-method-measurement-valid-from.md)
> established) directly in production PostHog. This session did not run
> the query and has no way to independently re-verify it — the same
> attribution standard already used for the COMMON/FALLBACK QA evidence in
> [`compass-monthly-fallback-ui-analytics-boundary.md`](compass-monthly-fallback-ui-analytics-boundary.md)
> Section 23.

### 28-1. Measurement Valid From

```
2026-08-22T01:09:00Z  (per #2517, unchanged, not re-derived here)
```

### 28-2. Query Used

Section 4's Query 2, unmodified in semantics (only the `timestamp >=`
literal filled in):

```sql
SELECT
  properties.result_state AS result_state,
  properties.calculationMethod AS calculationMethod,
  count() AS count
FROM events
WHERE event = 'compass_result'
  AND timestamp >= toDateTime('2026-08-22 01:09:00', 'UTC')
GROUP BY
  properties.result_state,
  properties.calculationMethod
ORDER BY count DESC
```

### 28-3. Raw Aggregate Counts (as reported)

| result_state | calculationMethod | count |
|---|---|---|
| `recommendation_success` | `monthly_kyusei_v1` | 2 |
| `recommendation_success` | `annual_monthly_kyusei_v1` | 1 |

No other rows were returned — in particular, **no**
`direction_zero_candidates`, `evidence_zero_candidates`,
`no_common_direction`, or `direction_filter_unavailable` rows appear in
the valid window. No unexpected/unknown `result_state` values were
reported either.

### 28-4. Eligible Population

```
recommendation_success:       3  (2 + 1, summed across both calculationMethod values)
direction_zero_candidates:    0
evidence_zero_candidates:     0
eligible_count:                3
```

### 28-5. Overall Recommendation Availability

```
Numerator:   3  (recommendation_success)
Denominator: 3  (eligible_count)
Rate:        100%  (3 / 3)
```

**Descriptive only** (Section 28-11) — see the caveat below before reading
this as a health signal.

### 28-6. COMMON Recommendation Availability

```
Eligible:        1
Success:         1
Zero candidates: 0
Rate:            100%  (1 / 1)
```

### 28-7. MONTHLY_FALLBACK Recommendation Availability

```
Eligible:        2
Success:         2
Zero candidates: 0
Rate:            100%  (2 / 2)
```

### 28-8. Segment Reconciliation

```
COMMON eligible (1) + MONTHLY_FALLBACK eligible (2) = 3
Overall eligible_count = 3
PASS
```

No null/unknown `calculationMethod` rows, no unaccounted `result_state`
values — the segmented and overall counts reconcile exactly.

### 28-9. Post-Valid-Window NULL Check

```
recommendation_success + calculationMethod = NULL: 0 rows
```

**Consistent with [#2517](compass-calculation-method-measurement-valid-from.md)'s
prediction** (Section 12 of that document: `recommendation_success` +
NULL is contract-invalid under current code, and both previously-observed
NULL events were independently timestamped as pre-dating this validity
boundary). This observed `0` corroborates that finding — it is not, by
itself, new evidence of anything; it is the expected outcome #2517 already
committed to in writing before this query ran.

### 28-10. QA Traffic Boundary

**All 3 eligible events are very likely known QA traffic, not organic
usage.** Cross-referencing against
[`compass-monthly-fallback-ui-analytics-boundary.md`](compass-monthly-fallback-ui-analytics-boundary.md)
Section 23 (one COMMON QA event, one MONTHLY_FALLBACK QA event,
`recommendation_success` both) and the additional MONTHLY_FALLBACK
verification referenced earlier in this audit chain (prior to the formal
Production QA write-up) plausibly accounts for the 2nd `monthly_kyusei_v1`
row. As established in Section 19 (unchanged): **`compass_result` carries
no property distinguishing QA-originated events from organic ones**, so
this cross-reference is circumstantial, not a query-level exclusion —
`QA TRAFFIC NOT RELIABLY SEPARABLE` still holds exactly as Section 19
states. No events were deleted or filtered to produce this count.

### 28-11. Observation Sufficiency

```
DESCRIPTIVE RATE ONLY
```

Reason: `eligible_count = 3`, and per Section 28-10, all 3 are plausibly
attributable to known QA activity rather than organic product usage. A
100% rate over 3 known-QA-heavy events says only "the instrumentation and
happy-path code work as designed when deliberately exercised" — it says
nothing about organic Recommendation Availability, which remains
unmeasured (zero confirmed organic eligible events observed).

### 28-12. Product Interpretation

The 100% figures in Sections 28-5/28-6/28-7 are **not** read as evidence
that Compass reliably returns recommendations in general use. Per Section
21 (unchanged) and this section's own 28-11: Direction Availability
(96.9%, theoretical) and Recommendation Availability remain distinct
metrics, and this measurement — being entirely QA-traffic-composed at
N=3 — cannot yet inform either a "healthy" or "unhealthy" product
conclusion. It confirms only that the metric is now actually queryable and
that no contract violation appears in the queried data (Section 28-9).

### 28-13. Next Gate

```
A — HEALTHY DESCRIPTIVE SIGNAL; WAIT FOR MORE ORGANIC DATA
```

Not **G** (Product-Decision-Ready) — explicitly ruled out per Section
28-11/28-12: N=3, entirely plausible QA composition. Not **B/C/D**
(a Recommendation Availability / COMMON / MONTHLY_FALLBACK problem) — no
zero-candidate event was observed at all in the valid window. Not **E**
(post-valid-window analytics defect) — Section 28-9 found zero NULL
`calculationMethod` events, consistent with #2517's contract analysis, not
contradicting it. Not **F** (no eligible observation) — 3 eligible events
exist. The correct, conservative read is: the instrumentation is verified
working end-to-end in production; the next step is accumulating organic
volume before any rate here can inform a product decision — not further
audits and not implementation.

### 28-14. Impact

```
Production code changed:          NO
Frontend production code changed: NO
Backend production code changed:  NO
Analytics instrumentation changed: NO
Runtime changed:                  NO
Recommendation Ranking changed:   NO
Concierge changed:                NO
DB changed:                       NONE
Migration:                        NONE
```

### 28-15. Verification

```
Numbers transcribed verbatim from the repository owner's report, not
re-derived or rounded. Arithmetic re-checked: 2+1=3 (Section 28-4),
1+2=3=eligible_count (Section 28-8), 3/3=100%, 1/1=100%, 2/2=100%
(Sections 28-5/28-6/28-7) -- all confirmed by this session's own
calculation from the reported raw counts, not merely copied.
```
