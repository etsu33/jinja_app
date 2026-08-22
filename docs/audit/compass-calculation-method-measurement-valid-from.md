> **Status: Active**
>
> This is a **deployment-boundary audit**, not an implementation. It does
> not modify Backend production code, Frontend production code, Analytics
> instrumentation, Runtime, Recommendation Ranking, Concierge, UI, or the
> DB. It establishes when `compass_result.calculationMethod` became a valid
> analytics property, and classifies one specific user-reported
> observation (a `recommendation_success` event with a null
> `calculationMethod`, reported at approximately 3 hours before this
> audit) against that boundary. **The NULL-event timeline in Sections 8-9
> is user-reported production PostHog evidence, not independently queried
> by this session** — this session has no PostHog access (established
> across the prior three audits in this chain, re-confirmed here). What
> *is* independently verified in this document is the git commit/merge
> history (hard facts) and the current code's contract (Sections 3-7,
> 10-12), which together let the user-reported relative timestamps be
> checked against an absolute, git-verified anchor rather than accepted on
> their own.

# Compass `calculationMethod` — Measurement Valid From Audit

## 1. Purpose

[`compass-recommendation-availability-production-measurement.md`](compass-recommendation-availability-production-measurement.md)
(#2516) left `calculationMethod`'s Measurement Valid From as `DEPLOYMENT
DATE REQUIRED`. This audit resolves it as far as the available evidence
allows, and separately classifies a specific observed
`recommendation_success` + null-`calculationMethod` event reported at
approximately 3 hours before this audit as pre-deploy, post-deploy, or
ambiguous.

---

## 2. Canonical Sources

Read: [`compass-analytics-contract.md`](../analytics/compass-analytics-contract.md),
[`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md),
[`compass-monthly-fallback-ui-analytics-boundary.md`](compass-monthly-fallback-ui-analytics-boundary.md),
[`compass-recommendation-availability.md`](compass-recommendation-availability.md),
[`compass-recommendation-availability-production-measurement.md`](compass-recommendation-availability-production-measurement.md).
Current implementation re-inspected directly (`CompassClient.tsx`,
`CompassClient.analytics.test.tsx`, `searchEvents.ts`) — no reliance on
prior docs alone.

---

## 3. Instrumentation Change

`calculationMethod` was added to `SearchAnalyticsPayload` in
`apps/web/src/lib/analytics/searchEvents.ts`, and threaded through
`trackCompassResult()` in `CompassClient.tsx`, in a single commit:

```
SHA:     85649530e4fefb2b1dc51e369c81307cf08a314f
Authored: 2026-08-22 09:39:03 +0900 JST  (2026-08-22T00:39:03Z)
Message: feat: Compass月盤fallbackをAnalyticsで識別
```

An **existing event was retained** (`compass_result`) — no new event was
created. Confirmed via `git log -p -- searchEvents.ts`: the diff adds one
new optional field,

```diff
+  calculationMethod?: "annual_monthly_kyusei_v1" | "monthly_kyusei_v1" | null;
```

to the existing `SearchAnalyticsPayload` type, alongside the existing
`result_state`/`purpose`/`origin_mode`/etc. fields — a property addition,
not a schema replacement.

---

## 4. Commit Evidence

```
Instrumentation commit: 85649530e4fefb2b1dc51e369c81307cf08a314f
Files changed:           apps/web/src/lib/analytics/searchEvents.ts,
                          apps/web/src/features/compass/CompassClient.tsx,
                          apps/web/src/features/compass/__tests__/CompassClient.analytics.test.tsx
```

---

## 5. PR / Merge Evidence

Determined via `gh pr view` (GitHub API, not guessed):

```
PR:              #2513, "feat: Compass月盤fallbackをAnalyticsで識別"
Head commit:      85649530e4fefb2b1dc51e369c81307cf08a314f
Merge commit:     80c025091b04fb705b514a7186df0c7796d58901
Merge timestamp:  2026-08-22T00:45:15Z  (2026-08-22 09:45:14 JST)
```

---

## 6. Develop Integration

```
Instrumentation commit: 85649530 (feature branch head)
Merge commit:           80c02509 (first commit on develop containing it)
```

`git log --oneline develop` places `80c02509` immediately as an ancestor of
current `develop` HEAD with no other `searchEvents.ts`/`CompassClient.tsx`
changes since — re-confirmed no drift (also stated in #2516 Section 2).

---

## 7. Production Deployment Evidence

```
Classification: B — DEPLOY WINDOW CONFIRMED (narrowed, not exact)
```

No Vercel/Render deployment API access exists in this session (no linked
project, re-confirmed) — an **exact** deploy timestamp (Classification A)
is not obtainable here, consistent with every prior audit in this chain.
However, combining the hard merge timestamp (Section 5) with the
user-reported first valid event (Section 8) narrows the window
considerably:

```
Lower bound: 2026-08-22T00:45:15Z  (merge to develop — deploy cannot
             precede this, and in practice a Vercel build+deploy adds a
             few minutes on top)
Upper bound: 2026-08-22T01:09:18Z  (approx.) -- the first user-reported
             valid calculationMethod event ("~2 hours" before this
             audit's write-up time, 2026-08-22T03:09:18Z)
Window:      approximately 24 minutes
```

This is a **narrower, evidence-based** window than the prior audits in
this chain achieved, precisely because it combines a hard git fact with a
user-reported relative timestamp, rather than relying on either alone.

---

## 8. First Valid Production Event

Per the user-reported production PostHog evidence provided for this audit
(not independently queried by this session):

```
recommendation_success + calculationMethod=monthly_kyusei_v1     ~2 hours before this audit
recommendation_success + calculationMethod=annual_monthly_kyusei_v1 ~1 hour before this audit
```

Converted to absolute time using this audit's write-up timestamp
(2026-08-22T03:09:18Z, `date -u` at the time this section was written) as
the "now" reference point for the reported relative offsets:

```
~2 hours before "now"  ≈ 2026-08-22T01:09Z   (monthly_kyusei_v1, first confirmed valid event)
~1 hour before "now"   ≈ 2026-08-22T02:09Z   (annual_monthly_kyusei_v1)
```

Both fall **after** the PR #2513 merge timestamp (00:45:15Z, Section 5) —
consistent with genuine post-deploy instrumentation, not a coincidence.
These two events match the COMMON/MONTHLY_FALLBACK Production QA already
recorded in
[`compass-monthly-fallback-ui-analytics-boundary.md`](compass-monthly-fallback-ui-analytics-boundary.md)
Section 23.

---

## 9. Observed NULL Timeline

Per the user-reported production PostHog evidence provided for this audit:

```
recommendation_success + calculationMethod=NULL   ~2 days before this audit
recommendation_success + calculationMethod=NULL   ~3 hours before this audit
```

Converted to absolute time the same way (reference "now" =
2026-08-22T03:09:18Z):

```
~2 days before "now"   ≈ 2026-08-20T~03:09Z
~3 hours before "now"  ≈ 2026-08-22T00:09Z
```

**Classification of the ~2-days-ago NULL event: PRE-DEPLOY.** Trivially —
it predates the instrumentation commit's own authoring time
(2026-08-22T00:39:03Z, Section 3) by roughly two days. The
`calculationMethod` concept did not exist in the codebase at all at that
point.

**Classification of the ~3-hours-ago NULL event: PRE-DEPLOY** (not
ambiguous). This is the more interesting case, and it is resolved by
comparing absolute timestamps, not by "inferring solely from relative
ordering" (which this task explicitly prohibits without deployment
evidence):

```
~3-hours-ago NULL event (implied):  2026-08-22T00:09:18Z
Instrumentation commit authored:    2026-08-22T00:39:03Z
PR #2513 merged to develop:         2026-08-22T00:45:15Z
```

The implied event timestamp (00:09:18Z) is **~30 minutes before the
instrumentation commit was even authored**, and ~36 minutes before it
merged to `develop`. The code that adds `calculationMethod` to the
`compass_result` payload did not exist in the repository — let alone in a
deployed build — at 00:09:18Z. This is deployment evidence (a hard git
timestamp), not mere ordering, supporting a definitive **PRE-DEPLOY**
classification for this specific event.

---

## 10. Current Code Path

Re-traced directly against current `develop` (Section 6, no drift):

```
CompassRecommendationsView.post()          api_views_compass.py:44-88
  -> build_compass_direction_runtime()      compass_runtime.py:70-127
  -> get_compass_recommendations()          compass_recommendation_orchestrator.py:86-203
  -> API response body.direction_context
  -> CompassClient.tsx:153 (body = await res.json())
  -> CompassClient.tsx:171 (directionContext = result?.direction_context ?? null)
  -> CompassClient.tsx:158-163 (trackCompassResult(body.state, ...,
       body.direction_context?.calculationMethod ?? null))
  -> searchEvents.ts trackSearchEvent("compass_result", {..., calculationMethod})
  -> providers.ts posthog.capture(eventName, serializedPayload)
```

`calculationMethod`'s only source is `body.direction_context?.calculationMethod`
— read directly off the parsed API response, never defaulted to a
non-null placeholder, never computed client-side.

---

## 11. NULL Emission Possibility (under current code)

**Question: can current code emit `result_state = recommendation_success`
with `calculationMethod = null`? Answer: NO.**

Traced precisely: `compass_recommendation_orchestrator.py:121-126` returns
`STATE_DIRECTION_FILTER_UNAVAILABLE` immediately if `direction_context` is
not a `Mapping` (i.e. is `None` or `NoCommonDirectionResult`) — **before**
candidate pool construction, direction filtering, or
`build_chat_recommendations()` are ever reached. `STATE_RECOMMENDATION_SUCCESS`
(`:198-203`) can therefore only be reached when `direction_context` is
already confirmed to be a `Mapping`. And every `Mapping` `compass_runtime.py`
can return always includes `calculationMethod` as a required key — both the
COMMON branch (`:99-108`) and the MONTHLY FALLBACK branch (`:116-124`)
construct their return dict with `"calculationMethod": result["calculationMethod"]`
/ `monthly["calculationMethod"]` respectively; there is no code path that
returns a dict without it.

**Conclusion: whenever `result_state === "recommendation_success"`, the
underlying `direction_context.calculationMethod` is guaranteed non-null by
current code.** No fallback/default null is ever substituted for a real
value — the `?? null` in `CompassClient.tsx:162` only fires when
`direction_context` itself is absent, which (per the trace above) cannot
co-occur with `recommendation_success`.

Classification: **HISTORICAL_PRE_INSTRUMENTATION** applies to both
observed NULL events (Section 9) — under current code, a
`CURRENT_UNEXPECTED_NULL` (contract-invalid post-deploy occurrence) is not
what either observation represents, and no evidence of one exists in the
data provided for this audit.

---

## 12. Contract Expectation

Reconfirmed, unchanged from #2513/#2515/#2516:

```
COMMON:                     calculationMethod = annual_monthly_kyusei_v1  (required)
MONTHLY_FALLBACK:            calculationMethod = monthly_kyusei_v1         (required)
no_common_direction:         calculationMethod = null / absent             (acceptable — no direction_context)
direction_filter_unavailable: calculationMethod = null / absent            (acceptable — no direction_context)
recommendation_success:      calculationMethod = null / absent            (CONTRACT-INVALID -- Section 11)
```

`recommendation_success` + NULL is **CONTRACT-INVALID** under current
code — it should never occur for any event recorded after the
instrumentation was actually live in production.

---

## 13. Measurement Valid From

Per this task's own hierarchy (exact timestamp → deploy window lower bound
→ first valid event → UNKNOWN):

```
Value:      2026-08-22T01:09Z (approx.) -- the first user-reported
            valid calculationMethod event (Section 8), used as the
            conservative lower bound per hierarchy item 3, since an exact
            production deploy timestamp (item 1) is not independently
            obtainable in this session, and the derived deploy window
            (item 2, Section 7: 00:45Z-01:09Z) is itself bounded above by
            this same first valid event.
Confidence: MODERATE -- anchored to a hard git merge timestamp (Section 5)
            plus a narrow (~24 minute) inferred deploy window (Section 7),
            not merely a guess; but the underlying event timestamps
            themselves are user-reported relative offsets, not
            independently queried absolute PostHog timestamps.
```

Any future COMMON/FALLBACK segmented query (per #2516 Section 4's Query 2)
should filter `timestamp >= '2026-08-22T01:09:00Z'` (approximate,
conservative) once independent PostHog query access exists to actually run
it.

---

## 14. Overall Availability Impact

```
Affected by calculationMethod gap: NO
```

Overall Recommendation Availability (`recommendation_success` /
[`recommendation_success` + `direction_zero_candidates` +
`evidence_zero_candidates`]) depends only on `result_state`, which has been
present on `compass_result` since PR-A (#2488) — long before
`calculationMethod` existed. The `calculationMethod` validity boundary
established here does not restrict or narrow the Overall Recommendation
Availability observation window at all.

---

## 15. COMMON/FALLBACK Segmentation Impact

```
Affected: YES
```

COMMON and MONTHLY_FALLBACK segmented Recommendation Availability
(#2515 Sections 12-13, #2516 Sections 11-14) require valid, non-null
`calculationMethod` coverage — any future segmented query must exclude
events before the Section 13 boundary (`2026-08-22T01:09Z`, approximate).
Events before that point (including both NULL events in Section 9) must
not be counted toward either the COMMON or MONTHLY_FALLBACK eligible
population, nor toward an "unknown/null calculationMethod" bucket implying
a current defect — they are simply pre-instrumentation, not
mis-instrumented.

---

## 16. Method Coverage Diagnostic

Per the (user-reported, not independently queried) production evidence
available to this audit — 5 `recommendation_success` events total, 3 with
a known `calculationMethod`, 2 with NULL:

```
3 / 5 = 60% (raw, unfiltered coverage across the full observed window)
```

**This 60% figure must not be read as current production instrumentation
coverage.** Applying the Section 13 validity boundary, both NULL events
(Section 9) fall before it, and both non-null events (Section 8) fall
after it — meaning **coverage among events at-or-after the Measurement
Valid From boundary is 2/2 = 100%**, not 60%. The 60% figure mixes
pre-instrumentation and post-instrumentation events indiscriminately,
exactly the mistake Section 13/15 exist to prevent.

---

## 17. Historical Data Boundary

Consistent with the same treatment already given to the
`no_common_direction` pre/post-#2499 boundary in
`compass-posthog-query-contract.md` Section 9's "HISTORICAL CLASSIFICATION
BREAK": events recorded before `2026-08-22T01:09Z` (approximate) simply
predate `calculationMethod`'s existence as a concept — they are not
"missing data" or "broken instrumentation," they are outside this
property's applicable range entirely, the same way pre-#2499
`no_common_direction` observations were outside that state's applicable
range. Do not retroactively infer a `calculationMethod` value for any
event before this boundary from timestamps, shrine IDs, or any other
correlated signal (same non-inference principle as
`compass-posthog-query-contract.md`'s existing historical-boundary
guidance).

---

## 18. Defect Classification

```
A — NULL EVENTS ARE PRE-DEPLOY ONLY; NO DEFECT
```

Both observed NULL events (Section 9) are independently, absolutely
timestamped (via the reported relative offset applied to this audit's
write-up time) as preceding the instrumentation commit's own existence in
the repository (Section 3) — not merely preceding it in relative order.
Current code, traced directly (Section 10-11), cannot produce
`recommendation_success` + NULL under any path once the instrumentation is
live. No post-deploy occurrence of this combination was reported or found.
This is not classification **D** (ambiguous) — the ~3-hour event's timing
was resolved definitively by comparing it against the hard merge
timestamp, not left uncertain. It is not **C** (contract-invalid
post-deploy occurrence needing investigation) or **E** (propagation gap)
— no such occurrence exists in the evidence available to this audit.

---

## 19. Recommended Query Window

For a future session with PostHog access (or the repository owner running
manually), per #2516 Section 4's Query 2 shape:

```sql
SELECT
  properties.calculationMethod AS calculation_method,
  properties.result_state AS result_state,
  count() AS n
FROM events
WHERE event = 'compass_result'
  AND timestamp >= '2026-08-22T01:09:00Z'   -- approximate Measurement Valid From (Section 13)
  AND properties.result_state IN
      ('recommendation_success', 'direction_zero_candidates', 'evidence_zero_candidates')
GROUP BY calculation_method, result_state
ORDER BY calculation_method, result_state
```

No PII fields (`distinct_id`, coordinates, birthdate, free text) are
included, consistent with #2515/#2516's privacy boundary.

---

## 20. Non-goals

This audit does not:

- Establish an exact (to-the-second) production deployment timestamp —
  only a narrowed window (Section 7) and a conservative first-valid-event
  lower bound (Section 13).
- Independently verify the user-reported NULL/valid event timeline via
  PostHog — this session has no query access (Sections 0, 9 explicit
  attribution).
- Compute any Recommendation Availability percentage.
- Fix, modify, or re-instrument anything.
- Begin UX, Premium, or Visit Funnel work.

---

## 21. Impact

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

## 22. Verification

```
git status --short   -> only this document (+ known untracked
                         apps/web/AGENTS.md, apps/web/CLAUDE.md, excluded)
git diff --stat       -> only this document
git diff --check      -> clean
```

Commit SHA, merge SHA, and merge timestamp (Sections 3-5) were retrieved
via `git log`/`gh pr view` directly against this session's clone — not
copied from a prior document. The code contract (Sections 10-11) was
re-traced directly from current `develop` source, not assumed. The
NULL/valid event timeline (Sections 8-9) is explicitly and consistently
labeled throughout as user-reported, not independently queried. No PII
recorded anywhere in this document.
