> **Status: Active**
>
> Production-facing Funnel Measurement Audit. Docs-only — no production
> code, Analytics instrumentation, Runtime, Ranking, Concierge, or DB
> change is made here. This audit assembles, for the first time, the full
> Compass → Visit journey now that PR5 ([#2525](https://github.com/etsu33/jinja_app/pull/2525))
> has fixed the one remaining gap
> ([`compass-route-attribution-contract.md`](compass-route-attribution-contract.md))
> in Route attribution. It draws heavily on
> [`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md),
> which already defines every stage through Reflection in detail — this
> document does not re-derive what that contract already establishes, it
> re-verifies it against current code, adds the now-fixed Route stage, and
> assembles the specific Result→Detail→Route→Visit **Primary Funnel**
> question the task asks.

# Compass → Visit Funnel Measurement Audit

## 1. Purpose

After a user receives a Compass result, how far do they progress toward
an actual shrine visit? Determine which stages are measurable, whether
Compass origin survives attribution through the journey, what production
data currently exists, whether it is Product-decision-ready, and what (if
anything) must be fixed before a Premium Value evaluation.

## 2. Scope

Docs-only. No production code, Analytics instrumentation, Runtime,
Ranking, Concierge, or DB change. No Premium decision. No UX fix. No
Analytics instrumentation fix — if a gap is found, it is named and gated,
not implemented here.

## 3. Canonical Sources

Read and re-verified against current `develop`:
[`compass-result-experience.md`](compass-result-experience.md),
[`compass-route-attribution-contract.md`](compass-route-attribution-contract.md),
[`compass-recommendation-availability.md`](compass-recommendation-availability.md),
[`compass-recommendation-availability-production-measurement.md`](compass-recommendation-availability-production-measurement.md),
[`compass-analytics-contract.md`](../analytics/compass-analytics-contract.md),
[`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md).

---

## 4. Current Journey Architecture

```
CompassClient.tsx (compass_result)
  -> CompassRecommendationsSection.tsx (card_view, shrine_detail_transition)
  -> buildShrineHref() -> /shrines/:id?ctx=compass&recommendation_instance_id=R&recommendation_rank=N
  -> app/shrines/[id]/page.tsx
       +-> ShrineDetailViewTracker  (ctx, detailRecommendationInstanceId)      -> shrine_detail_view
       +-> ShrineDetailArticle       (ctx override, detailRecommendationInstanceId) -> visit_done, reflection_*
       +-> ShrineSaveButton          (ctx override, detailRecommendationInstanceId) -> favorite_click, shrine_decision
       +-> ShrineDetailShell         (ctx, detailRecommendationInstanceId -- FIXED by PR5)
             -> GoogleMapRouteLink -> route_open
```

**Re-traced against current `develop` (post-PR5), not assumed from the merge alone**:

```
apps/web/src/app/shrines/[id]/page.tsx:494-499
  ctx={ctx}                                    (full, un-nulled)
  recommendationInstanceId={detailRecommendationInstanceId}
```

confirmed identical to what PR5 committed, no drift since merge
(`git log -1` on `page.tsx`'s history shows no commit after PR5 touching
this file). `GoogleMapRouteLink.tsx:65-73` still emits
`source: "shrine_detail"` (hardcoded, unchanged, per PR5's explicit
instruction not to alter `source` semantics), `ctx`, `recommendationInstanceId`.
Direct shrine-detail access and Concierge (`ctx="concierge"`) were
re-confirmed distinct: for any `ctx !== "compass"`, `downstreamCtx === ctx`
and `detailRecommendationInstanceId === conciergeRecommendationInstanceId`
already held before PR5, so those paths are provably unaffected (PR5's
own test suite, `apps/web/src/app/shrines/[id]/__tests__/page.test.tsx`,
asserts this directly and was sanity-checked against the pre-fix code to
confirm it actually fails without the fix).

---

## 5. Production QA Gate for PR5

**PR5 production deployment: CONFIRMED.**

```
Vercel project:     jinja-app-web (prj_odAjGXc6alMlAGSx46q4RQ9EBrjp)
Deployment id:      dpl_C6n7UgYNj28RkQREXdULfER57QJZ
target:             production
state:              READY
githubCommitSha:    33b02419edfb74663fd058d5f40056ac86c4eae0
githubCommitRef:    develop
githubCommitMessage: "fix: Compass起点のルート計測コンテキストを引き継ぐ (#2525)"
created:            1787397232524 (epoch ms) = 2026-08-22T11:13:52Z
```

This commit SHA is identical to the current `develop` HEAD
(`git log -1 --oneline` = `33b02419 fix: Compass起点のルート計測コンテキストを引き継ぐ (#2525)`),
confirmed via the Vercel deployments API for this session (same class of
evidence already established as sufficient precedent by
[`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md)
§9's `no_common_direction` boundary, which cross-checked Vercel + Render).
PR5 is frontend-only (no backend file touched), so Vercel confirmation
alone is sufficient here — no Render cross-check is needed for this
specific fix.

**Has one production Compass→Detail→Route event been observed since this
deployment?** **NO — none has been reported or queried in this session.**
This session has no PostHog query capability (re-confirmed, §24). No user
report of a post-11:13:52Z `route_open{ctx="compass"}` event exists in
this conversation.

**Classification: ROUTE ATTRIBUTION PRODUCTION QA REQUIRED.**

Events before `2026-08-22T11:13:52Z` must **not** be treated as valid
Compass→Route attribution, even if they carry `ctx="compass"` by
coincidence of query construction — before this deployment, the code
path that populates `route_open`'s `ctx`/`recommendationInstanceId` for a
Compass-originated visit did not exist in production; any such event
would in fact have been recorded with `ctx: null`.

---

## 6. Measurement Valid From

Per-stage boundaries (existing instrumentation, re-affirmed from
[`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md)
§9, not re-derived here except where noted):

| Stage | Introduced in | Valid From | Confidence |
|---|---|---|---|
| `compass_result` (no `recommendationInstanceId`) | PR-A (#2488) | OPEN — merge `2026-08-19T04:24:55Z` is earliest possible bound only | LOW |
| `compass_result.recommendationInstanceId`, `card_view`/`shrine_detail_transition`/`shrine_detail_view` (source=compass) | PR-B (#2489) | OPEN — merge `2026-08-19T08:25:22Z` is earliest possible bound only | LOW |
| `favorite_click`/`shrine_decision`/`visit_done`/`reflection_*` (source=compass) | PR-C (#2490) | OPEN — merge timestamp known, deploy not independently verified in this audit | LOW |
| `compass_result.calculationMethod` | Analytics Alignment PR (#2513) | `2026-08-22T00:45:15Z`–`2026-08-22T01:09:00Z` window (per [#2517](compass-calculation-method-measurement-valid-from.md)) | MEDIUM (narrowed window, not exact) |
| `route_open.ctx`/`recommendationInstanceId` correctly populated for Compass | **PR5 (#2525)** | **`2026-08-22T11:13:52Z`** (Vercel-confirmed, this audit, §5) | **HIGH** |

**Funnel Measurement Valid From, per stage combination:**

```
Result -> Detail (Recommendation CTR):              PR-B boundary (OPEN, low confidence)
Result -> Detail -> Favorite/Visit/Reflection:       PR-C boundary (OPEN, low confidence)
Result -> Detail -> Route (full Primary Funnel):      max(PR-B, PR5) = 2026-08-22T11:13:52Z (HIGH confidence)
Result -> Detail -> Route -> Visit (full Primary Funnel + Visit): same, 2026-08-22T11:13:52Z
```

The **full Primary Funnel** (§14 below) that includes Route is valid only
from **`2026-08-22T11:13:52Z`** onward — the latest of all required
stage boundaries, per the task's own "max of all boundaries" rule. Given
this is extremely recent relative to this audit, essentially **zero
observation window has elapsed** for the Route-inclusive funnel.

---

## 7. Funnel Unit

**Primary funnel unit: unique `recommendationInstanceId`** (journey-level
— "did this Compass result lead to at least one Detail / Route / Visit"),
per the task's explicit preference for result/journey-level conversion
over card-level CTR. A single Compass result can recommend multiple
shrines; the primary funnel asks whether the result led to progress at
all, not what fraction of individual cards were opened.

**Secondary/shrine-level unit: `(recommendationInstanceId, shrineId)`
pair** — used for the Recommendation CTR (card-level "was this specific
row opened") and for any Route/Visit metric that needs to confirm the
*same* shrine progressed through each stage, not just *any* shrine from
the same result.

---

## 8. Event Inventory

Re-verified directly against current `develop` (not assumed from prior
docs):

| Stage | Event | Required properties | Compass attribution property | Recommendation instance | Shrine ID | Measurement readiness |
|---|---|---|---|---|---|---|
| Result | `compass_result` | `result_state`, `calculationMethod`, `recommendationInstanceId` | N/A (origin point) | generates R | N/A | MEASURABLE |
| Detail (impression) | `card_view` | `source="compass"`, `shrineId`, `recommendationInstanceId`, `recommendationRank` | `source` | YES | YES | MEASURABLE |
| Detail (click) | `shrine_detail_transition` | same as above | `source` | YES | YES | MEASURABLE |
| Detail (view) | `shrine_detail_view` | `source`, `shrineId`, `recommendationInstanceId`, `recommendationRank` | `source` | YES | YES | MEASURABLE |
| Route | `route_open` | `source` (hardcoded `"shrine_detail"`, not Compass-aware), `ctx`, `recommendationInstanceId`, `shrineId` | `ctx` (**not** `source` — PR5) | YES (post-PR5) | YES | MEASURABLE post-PR5, **zero confirmed production events yet** |
| Favorite | `favorite_click`, `shrine_decision` | `source`, `shrineId`, `recommendationInstanceId`, `nextFav`, `accessLevel` | `source` | YES (same-page-render) | YES | MEASURABLE (secondary) |
| Visit | `visit_done` | `source`, `shrineId`, `recommendationInstanceId`, `accessLevel` | `source` | YES (same-page-render) | YES | MEASURABLE, **self-reported action, not a verified physical visit (§12)** |
| Reflection | `reflection_prompt_view`, `reflection_saved` | `source`, `shrineId`, `recommendationInstanceId` | `source` | YES (same-page-render, gated on same-render Visit) | YES | PARTIAL — same-session only, expected near-zero volume |

No event name was assumed — every row above traces to a concrete file
already cited in
[`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md)
§1, re-confirmed for `route_open` in
[`compass-route-attribution-contract.md`](compass-route-attribution-contract.md)
and this audit's own §4/§5.

**Critical asymmetry, confirmed for this audit**: every stage from Detail
through Reflection uses `source="compass"` as its Compass-attribution
property — **except `route_open`**, whose `source` remains
`"shrine_detail"` even for a Compass-originated open (by design, per
PR5's explicit instruction not to conflate `source` with journey origin).
**`route_open`'s Compass attribution property is `ctx="compass"`, not
`source`.** Any query built by copy-pasting the `source="compass"`
pattern from other stages onto `route_open` will silently return zero
rows.

---

## 9. Compass Result Stage

**Canonical funnel start**: `compass_result` **WHERE**
`result_state = "recommendation_success"` — not all `compass_result`
events. The behavioral funnel question is "after receiving usable
recommendations, what do users do," which by construction excludes
`no_common_direction`, `direction_zero_candidates`,
`evidence_zero_candidates`, `invalid_purpose`,
`direction_filter_unavailable`, and `backend_error` — none of these ever
produce a recommendation card, so none can enter a Detail/Route/Visit
funnel denominator (confirmed structurally, not just by convention, in
[`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md)
§8's Recommendation CTR section — `card_view` cannot fire without
`recommendation_success`). This mirrors, and does not duplicate, the
separately-defined **Recommendation Availability** metric
([`compass-recommendation-availability.md`](compass-recommendation-availability.md)),
which asks a different question (is `recommendation_success` itself
healthy) — the Visit Funnel takes `recommendation_success` as its given
starting population, it does not re-litigate whether that population
should be larger.

**Recorded**: `recommendationInstanceId`, `calculationMethod`,
`result_state`.

---

## 10. Detail Stage

**Canonical single funnel-stage event: `shrine_detail_view{source="compass"}`.**
`card_view` and `shrine_detail_transition` are earlier, real, and already
individually defined (Recommendation CTR uses `card_view` as its
denominator, per the existing contract) — but for the *Primary* Visit
Funnel, only one Detail-stage event is used, to avoid double-counting the
same transition three times. `shrine_detail_view` is chosen because it is
the event that actually confirms the destination page mounted (not merely
that a click was recorded before navigation, which `shrine_detail_transition`
only proves intent).

**Deduplication**: an `(recommendationInstanceId, shrineId)` pair counts
as "reached Detail" if **at least one** `shrine_detail_view` exists for
it — multiple opens (refresh, back-and-forth) count once, per the
existing Deduplication Contract (`compass-analytics-contract.md`/
`compass-posthog-query-contract.md` §5).

**Join keys**: `recommendationInstanceId` + `shrineId`, both required.

---

## 11. Route Stage

**Post-PR5, the corrected concept**: for a Compass-originated open,

```
event = route_open
source = "shrine_detail"   (unchanged, per PR5 -- not Compass-aware, by design)
ctx = "compass"
recommendationInstanceId = R
shrineId = S
```

**Do not filter on `source="compass"` for this event — it will never
match.** The Compass-origin filter for `route_open` is `ctx="compass"`
(§8's asymmetry note). This is the single most important correction this
audit contributes to the existing Query Contract, since every other
stage's filter pattern (`source="compass"`) would silently produce zero
rows if copy-pasted onto Route.

**Attribution mechanism, re-verified (not assumed from the PR5 merge)**:
`page.tsx` passes `ctx` (full, un-nulled) and `detailRecommendationInstanceId`
to `<ShrineDetailShell>`, which forwards them unchanged into
`<GoogleMapRouteLink>`, which includes both directly in the `route_open`
payload (§4). No `source`-based join is defined or should be attempted
for this stage.

---

## 12. Favorite / Save

**Event**: `favorite_click`, `shrine_decision`. **`source="compass"`**
when `ctx==="compass"` at the same page render; `nextFav=true` isolates
the save action from unsave. **Classification: MEASURABLE** (secondary),
same-page-render attribution window only (established, unchanged by this
audit — `compass-analytics-contract.md` "Action source propagation").
Requires authentication (`ShrineSaveButton`'s guest path redirects to
login) — anonymous users are excluded by construction, not a measurement
gap.

Favorite is **not** a required step before Route or Visit — a user can
open the route link, mark a visit, and never favorite the shrine, or
favorite it without ever opening the route link. This audit does not
place Favorite in the Primary Funnel's linear sequence (§14/§15).

---

## 13. Visit Stage

**Event**: `visit_done`, fired from `ShrineDetailArticle.tsx:762-771`, on
a manual **"参拝しました" (I visited) button press**, confirmed by direct
code read (§4's re-trace) to be a **self-reported user action**, gated
only on `!hasVisitHistory` (i.e., "not already marked") — it is **not**
gated behind, triggered by, or in any way dependent on `route_open` having
fired. A user can press this button having never clicked the route link
at all (they may know the way, have visited before recommendations
existed, or be recording a past visit). **This event proves "the user
told the app they visited," not "GPS/location-verified the user was
physically present," and this document does not call it an "actual
physical visit"** per the task's explicit instruction (§13).

**Compass attribution**: `source="compass"` when `ctx==="compass"` at
the same render, `recommendationInstanceId` carried, same-page-render
window only (identical mechanism and limitation to Favorite, §12).
**Classification: MEASURABLE**, with the same-page-render coverage
caveat already established in
[`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md):
a true Compass-driven visit is, by the nature of a physical-world action,
more likely to happen in a *later* browsing session than the Compass
discovery itself — so this metric's coverage of true Compass-driven
visiting behavior is expected to be a **minority**, not a majority, of
what actually happens. This is a coverage limitation, not a defect.

---

## 14. Reflection Stage

**Events**: `reflection_prompt_view`, `reflection_saved`. Only rendered
when `hasVisitHistory` is true **in the current page render** — if that
becomes true via the *current* render's own Visit action, `source`
correctly carries `"compass"`; if `hasVisitHistory` is true from a
**prior**, separate visit (fresh page load, no `ctx=compass` in the URL),
`source` correctly falls back to `"shrine_detail"` — no false attribution,
but also no long-horizon signal. **Classification: PARTIAL** — mechanism
is correct and non-fabricating, but by construction requires Visit
**and** Reflection to both occur before the user navigates away, within
one Shrine Detail render — this is expected to be a **near-zero-volume**
diagnostic, not a usable rate, per the existing contract's own
expectation.

**The long-horizon question the product actually cares about ("does a
Compass-driven visit eventually get reflected on, even days later") is a
MEASUREMENT GAP**, unchanged by this audit, not solvable without new
persistence (explicitly out of scope, per PR-C and the Persistence
Boundary in `compass-analytics-contract.md`).

---

## 15. Primary Funnel Contract

```
Stage 0: Compass Recommendation Result
  compass_result WHERE result_state = "recommendation_success"
  unit: recommendationInstanceId

Stage 1: Compass-origin Shrine Detail
  shrine_detail_view WHERE source = "compass"
  unit: recommendationInstanceId (>=1 matching shrineId)

Stage 2: Compass-origin Route Open
  route_open WHERE ctx = "compass"          <-- NOT source="compass" (see Section 11)
  unit: recommendationInstanceId (>=1 matching shrineId)

Stage 3: Compass-origin Visit
  visit_done WHERE source = "compass"
  unit: recommendationInstanceId (>=1 matching shrineId)
```

**Important, honest caveat on Stage 2 -> Stage 3 sequencing**: this is a
funnel in the PostHog sense (a progression of increasingly-engaged
behavior), **not** a claim that Route causes or gates Visit. §13
confirmed `visit_done` has no dependency on `route_open` having fired. A
low Stage 2 -> Stage 3 rate can mean "many users visit without ever
needing the in-app route link" just as plausibly as "users drop off
after seeing the route" — this document does not resolve that ambiguity
from event data alone (§30).

Favorite and Reflection are **not** included as Primary Funnel stages
(§16).

---

## 16. Secondary Actions

**Secondary, not sequential-prerequisite, behaviors**:

- **Favorite/Save** (`favorite_click`, `shrine_decision`) — MEASURABLE,
  same-page-render window, requires authentication. Not required before
  Route or Visit.
- **Reflection** (`reflection_prompt_view`, `reflection_saved`) —
  PARTIAL, same-session diagnostic only, expected near-zero volume.

This document explicitly does **not** construct a false mandatory
sequence such as `Result -> Detail -> Favorite -> Route -> Visit` — no
product or code semantics require Favorite before Route/Visit, and
forcing it into the linear Primary Funnel would misrepresent users who
skip it entirely (the majority, expected, since Favorite requires
authentication and Visit does not).

---

## 17. Attribution Keys

**Primary**: `recommendationInstanceId` — the only journey-level, non-PII
key. Verified present (when applicable) on every stage:

```
Result:      generates it (backend, uuid.uuid4().hex[:8], stateless, no DB write)
Detail:      present (card_view, shrine_detail_transition, shrine_detail_view)
Route:       present, post-PR5 (ctx/recommendationInstanceId both populated correctly)
Favorite:    present, same-page-render only
Visit:       present, same-page-render only
Reflection:  present, same-page-render only, gated on same-render Visit
```

It does **not** survive farther than same-page-render for
Favorite/Visit/Reflection — this document does not assume it does.

**Secondary**: `shrineId` — scopes an action to a specific shrine, used
together with `recommendationInstanceId` for shrine-level joins (CTR,
Route-Detail-Visit-for-the-same-shrine). **`shrineId` alone never
establishes Compass origin** (recurs across unrelated result instances,
users, and months) — used only as a consistency/secondary check, never
as a standalone attribution key, consistent with
[`compass-route-attribution-contract.md`](compass-route-attribution-contract.md)
§12.

---

## 18. Deduplication Contract

| Metric | Counting unit | Rule |
|---|---|---|
| Result -> Detail | `recommendationInstanceId` | Counts once if **>=1** matching `shrine_detail_view{source=compass}` exists, regardless of how many shrines or how many opens of the same shrine. |
| Detail -> Route | `recommendationInstanceId` | Counts once if **>=1** matching `route_open{ctx=compass}` exists for **any** shrine from that result (result-level primary question), or `(recommendationInstanceId, shrineId)` if the shrine-level variant is needed. |
| Route -> Visit | `recommendationInstanceId` | Counts once if **>=1** matching `visit_done{source=compass}` exists — **not required to be the same shrine that had the Route open**, for the result-level Primary Funnel (§22); a shrine-level variant requires the `shrineId` match too. |
| Recommendation CTR (secondary, card-level) | `(recommendationInstanceId, shrineId)` | Unchanged from the existing contract — counts a row "opened" if >=1 matching detail view exists for that exact pair. |

**Never use raw `route_open` event counts as a conversion signal** — a
single user can click the route link multiple times for the same shrine;
only distinct-journey (or distinct-journey+shrine) counts are valid
numerators, per the task's explicit instruction.

---

## 19. Multiple Shrine Semantics

A single Compass result can recommend several shrines. The **Primary
Funnel asks the journey-level question**: "did this Compass result lead
to at least one Detail / Route / Visit," not "what fraction of individual
cards were opened" (that is the separate, already-defined Recommendation
CTR, a card-level metric). This audit does not introduce a new CTR
definition — it reuses the existing one for Detail
([`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md)
§8) and defines the analogous **result-level** "at least one" semantics
newly for Route and Visit, since neither existed as a defined KPI before
PR5 made Route measurable at all.

---

## 20. Query Contract

Privacy-safe, aggregate-only, non-executed pseudocode (this session has
no PostHog access, §24) — prepared for manual execution, following the
existing contract's own established pattern
([`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md)
§8's `-- conceptual, not executed` queries):

```sql
-- Primary Funnel, result-level (recommendationInstanceId only), from
-- the LATEST valid boundary (Section 6): 2026-08-22T11:13:52Z onward.

WITH results AS (
  SELECT DISTINCT properties.recommendationInstanceId AS rid
  FROM events
  WHERE event = 'compass_result'
    AND properties.result_state = 'recommendation_success'
    AND timestamp >= toDateTime('2026-08-22 11:13:52', 'UTC')
),
detail AS (
  SELECT DISTINCT properties.recommendationInstanceId AS rid
  FROM events
  WHERE event = 'shrine_detail_view'
    AND properties.source = 'compass'
    AND timestamp >= toDateTime('2026-08-22 11:13:52', 'UTC')
),
route AS (
  SELECT DISTINCT properties.recommendationInstanceId AS rid
  FROM events
  WHERE event = 'route_open'
    AND properties.ctx = 'compass'                 -- NOT source (Section 11)
    AND timestamp >= toDateTime('2026-08-22 11:13:52', 'UTC')
),
visit AS (
  SELECT DISTINCT properties.recommendationInstanceId AS rid
  FROM events
  WHERE event = 'visit_done'
    AND properties.source = 'compass'
    AND timestamp >= toDateTime('2026-08-22 11:13:52', 'UTC')
)
SELECT
  (SELECT count() FROM results)                         AS result_n,
  (SELECT count() FROM results r WHERE r.rid IN (SELECT rid FROM detail)) AS detail_n,
  (SELECT count() FROM results r WHERE r.rid IN (SELECT rid FROM route))  AS route_n,
  (SELECT count() FROM results r WHERE r.rid IN (SELECT rid FROM visit))  AS visit_n
```

**COMMON/FALLBACK segmentation (Section 25)**: `calculationMethod` exists
only on `compass_result`, never repeated on downstream events. The
downstream journey inherits the segment **analytically**, by joining back
to `results` via `recommendationInstanceId` — no new propagation is
needed or added:

```sql
-- Segment the same funnel by calculationMethod, joined back to compass_result
WITH results AS (
  SELECT properties.recommendationInstanceId AS rid,
         properties.calculationMethod AS calculationMethod
  FROM events
  WHERE event = 'compass_result'
    AND properties.result_state = 'recommendation_success'
    AND timestamp >= toDateTime('2026-08-22 11:13:52', 'UTC')
)
-- then LEFT JOIN detail/route/visit's rid sets onto results.rid,
-- GROUP BY results.calculationMethod
```

No `distinct_id`, person id, email, birthdate, coordinates, raw origin,
or free text appears in any query above.

---

## 21. Result → Detail Metric

Already defined (unchanged): Result Instance → Detail Engagement Rate
([`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md)
§8). This audit does not redefine it.

---

## 22. Detail → Route Metric

**New, defined by this audit** (did not exist before PR5):

```
Numerator:   count of recommendationInstanceId values present in both
             `detail` and `route` (Section 20 CTEs).
Denominator: count of recommendationInstanceId values in `detail`.
```

**Not yet computed** — zero observation window has elapsed since the
valid boundary (Section 6).

---

## 23. Result → Route Metric

```
Numerator:   count of recommendationInstanceId values present in both
             `results` and `route`.
Denominator: count of recommendationInstanceId values in `results`.
```

**Not yet computed** — same reason as Section 22.

---

## 24. Route → Visit Metric

```
Numerator:   count of recommendationInstanceId values present in both
             `route` and `visit`.
Denominator: count of recommendationInstanceId values in `route`.
```

Per Section 15's caveat, a low value here is **not** automatically a
"drop-off problem" — Visit does not require Route to have fired.
**Not yet computed.**

---

## 25. Result → Visit Metric

```
Numerator:   count of recommendationInstanceId values present in both
             `results` and `visit`.
Denominator: count of recommendationInstanceId values in `results`.
```

Expected to be small by nature (§13's same-page-render coverage
limitation, pre-existing and unchanged by PR5). **Not yet computed.**

---

## 26. Production Observation

**Result stage (pre-Route, pre-existing data)**: per
[`compass-recommendation-availability-production-measurement.md`](compass-recommendation-availability-production-measurement.md)
§28, a valid-window query since `2026-08-22T01:09:00Z` returned **3
eligible `recommendation_success` events** (1 `annual_monthly_kyusei_v1`,
2 `monthly_kyusei_v1`), all plausibly known QA traffic. **This data
predates PR5's deploy by ~10 hours and therefore cannot be used as the
denominator for any Route-inclusive metric** — those 3 result instances
occurred before `route_open`'s `ctx`/`recommendationInstanceId` were
correctly populated in production, so even if one of those sessions
happened to click a route link, that specific `route_open` event would
have recorded `ctx: null` and must be excluded, not retroactively
credited.

**Detail/Route/Favorite/Visit/Reflection stage counts since the
Route-valid boundary (`2026-08-22T11:13:52Z`): NOT OBTAINED.** No query
has been run or reported for these stages in this session. This is not
estimated, backfilled, or approximated from the Result-stage numbers
above.

---

## 27. QA Traffic Boundary

**Reliably separable: NO.** Unchanged from the existing finding
(`compass-recommendation-availability-production-measurement.md` §19,
`compass-posthog-query-contract.md` §11B): no Compass event carries an
`is_test`/`is_internal` property, and no app-level QA flag exists on any
event in this funnel. Given the observed population so far (§26, 3
events, plausibly all QA) is small and plausibly entirely non-organic,
any rate computed from it must be labeled **descriptive**, never
**organic conversion**.

---

## 28. Observation Sufficiency

**QA ONLY / no observation yet for the Route-inclusive funnel.** The only
existing observed population (§26, N=3, pre-Route-boundary) was already
classified `DESCRIPTIVE RATE ONLY` by the prior audit and is not
reusable here. No observation at all exists yet for Detail→Route,
Result→Route, Route→Visit, or Result→Visit under the corrected
instrumentation. This is not "too small to interpret" — it is **zero**,
which is a distinct and more conservative state than "small."

---

## 29. Drop-off Analysis

**Not performed.** Per the task's own instruction, drop-off analysis
requires production counts to support it — none exist yet for any stage
downstream of Result under the Route-valid boundary. No stage is named as
a "UX problem" from the absence of data; absence of data is not evidence
of a drop-off, per the task's explicit caution against inferring a UX
problem from QA-only or zero data.

---

## 30. Product Interpretation

Kept explicitly separate, per the task's instruction, none substituting
for another:

```
Direction Availability:        docs/audit/compass-direction-availability-product-decision.md
                                (theoretical, ~46.5% no-common-direction rate, algorithmic)
Recommendation Availability:   docs/audit/compass-recommendation-availability.md +
                                -production-measurement.md (N=3, descriptive, QA-heavy)
Result Experience readiness:   docs/audit/compass-result-experience.md
                                (UX Change Decision F, resolved via PR1-3, #2521-2523)
Visit Funnel conversion:       THIS document -- zero observation yet for the
                                Route-inclusive funnel, mechanism now correct
                                as of PR5
Premium Value:                 NOT addressed here (Section 32/38 boundary)
```

None of the above stands in for another. A healthy Recommendation
Availability does not imply a healthy Visit Funnel, and the absence of
Visit Funnel data says nothing about Direction or Recommendation
Availability, which are separately and already measured.

---

## 31. Funnel Readiness Decision

```
D — ROUTE PRODUCTION QA REQUIRED BEFORE MEASUREMENT
```

Not **A/B** (fully measurable, data sufficient or organic-data-pending)
— the mechanism is now correct end-to-end (verified by code trace and
PR5's own test suite, §4), but **zero** production observation exists for
the Route-inclusive funnel (§26/§28), so no rate can yet be computed, let
alone judged sufficient. Not **E** (attribution gap still exists) — PR5
closed the specific gap [`compass-route-attribution-contract.md`](compass-route-attribution-contract.md)
identified; re-tracing current code in this audit's own §4 found no
drift or regression. Not **F** (analytics event gap) — no new event or
property is needed; every required field already exists on `route_open`
(§8, §11). **G** (QA-only/too-small) does not apply either — G presumes
*some* data exists that is QA-composed; here, no post-boundary data
exists at all yet, which is the more conservative "not yet observed"
state this audit's §5 already named as **ROUTE ATTRIBUTION PRODUCTION QA
REQUIRED**. D is the most precise fit: the correct next step is a
deliberate QA confirmation click-through (same category of evidence
already used successfully for the COMMON/FALLBACK production check,
`compass-monthly-fallback-ui-analytics-boundary.md` §23), not a passive
wait and not further code changes.

---

## 32. Next Product Gate

```
1 — WAIT FOR ORGANIC DATA
```

**Reason**: the immediate, concrete next action is a single deliberate
production QA click-through (Compass result → Shrine Detail → Route
click) to produce and confirm at least one valid post-PR5
`route_open{ctx="compass"}` event — the same kind of manual verification
step already used for the COMMON/FALLBACK segmentation check. This is a
narrow verification action, not a new audit or an implementation task, so
it is folded into "1" rather than treated as its own category; once that
one event is confirmed, the correct posture is exactly "1 — wait for
organic volume to accumulate" across the whole Result→Detail→Route→Visit
funnel before any rate in this document is read as product-decision-grade.
Not **2** (no drop-off evidence exists to act on, §29). Not **3** (no
analytics/code fix is needed, §31). Not **4** (Premium Value evaluation
requires exactly the funnel data this document found absent — beginning
it now would mean deciding Premium Value on zero Visit-stage observation,
directly contradicting Section 32/38's boundary). Not **5** (unrelated to
this audit's findings).

---

## 33. Non-goals

This audit does not:

- Modify any production, frontend, backend, Runtime, Ranking, Concierge,
  Analytics instrumentation, or DB/migration code.
- Compute or report any Route-inclusive funnel rate (none exists yet,
  §26/§28/§29).
- Decide Compass Premium pricing or value (§30/§32 boundary).
- Reopen Personal Continuity (unaffected, unchanged from
  `compass-posthog-query-contract.md` §12).
- Fabricate a production count, retroactively credit pre-PR5 `route_open`
  events, or extrapolate Detail/Route/Visit counts from the pre-Route-boundary
  Result-stage numbers (§26).
- Begin UX fixes, Analytics instrumentation fixes, Premium implementation,
  or Concierge Input v2.

---

## 34. Impact

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
New analytics events:             NONE
New analytics properties:         NONE
```

---

## 35. Verification

```
git status --short / git diff --stat: limited to this document only
(verified before staging, Section 41 of the task).
PR5's fix re-traced directly against current develop (Section 4), not
assumed from the merge record alone -- confirmed no drift since #2525.
PR5's production deployment independently confirmed via the Vercel
deployments API (Section 5) -- commit SHA matches current develop HEAD
exactly, target=production, state=READY.
No production count in this document was fabricated, backfilled, or
extrapolated across the PR5 deployment boundary -- Section 26 explicitly
states what is NOT obtained rather than estimating it.
No PII, distinct_id, or raw session data appears in any query (Section 20).
