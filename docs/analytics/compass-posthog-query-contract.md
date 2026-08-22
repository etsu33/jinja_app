# Compass PostHog Query Contract

> Status: Active — revised to align with the `no_common_direction` runtime
> state ([PR #2499](../audit/compass-direction-filter-unavailable-root-cause.md)-family
> work: [#2496](../audit/compass-direction-filter-unavailable-root-cause.md),
> [#2497](../audit/compass-direction-availability-product-decision.md),
> [#2498](../product/compass-product-contract.md) Section 2.1, #2499 implementation,
> all merged). See §1.1, §8, §9, §13, §15 for the changes.

This document defines how the already-implemented Compass analytics (PR-A #2488,
PR-B #2489, PR-C #2490 — all merged) should be **queried** in PostHog. It is a
companion to `docs/analytics/compass-analytics-contract.md` (the event/payload
contract) and `docs/audit/compass-analytics-contract-readiness.md` (the
pre-implementation proposal). This document defines measurement only. It draws
no product conclusions, executes no production queries, and adds no
instrumentation.

Every claim below is verified against current `develop` code (post PR-A/B/C,
and post-#2499 for the `no_common_direction` state), re-read directly for
this revision — not assumed from prior audit docs.

---

## 1. Pre-Contract Inventory

All rows verified directly against current `develop` source.

| Stage | Event | Required properties | Identifier | Source (file) | Notes |
|---|---|---|---|---|---|
| Home → Compass discovery | `home_compass_entry_click` | `source="home"` | PostHog `distinct_id` only | `HomeCompassSection.tsx:34` | Click-only. No impression event exists for the Home section. |
| Compass entry | `compass_entry` | `referrer_source: "home"\|"direct"` | PostHog `distinct_id` only | `CompassClient.tsx:58-65` | Fires once per mount (`entryTrackedRef` guard). No `recommendationInstanceId` yet — not generated until submit. |
| Compass result | `compass_result` | `result_state`, `purpose`, `origin_mode`, `has_birthdate`, `recommendation_count`, `recommendationInstanceId`, `calculationMethod` (new, optional — §1.2) | PostHog `distinct_id`; `recommendationInstanceId` present for every state **except** `backend_error`; `calculationMethod` present only when the result carries a `direction_context` | `CompassClient.tsx:67-80,127-144` | `result_state` uses the real backend vocabulary + one frontend-only bucket (§1.1). Now 6 backend values (post-#2499, includes `no_common_direction`) + 1 frontend-only. |
| Recommendation exposure (impression) | `card_view` | `cardId="shrine_compact"`, `source="compass"`, `visibility="visible"`, `shrineId`, `recommendationRank`, `recommendationInstanceId` | `recommendationInstanceId` + `shrineId` | `CompassRecommendationsSection.tsx:36-44` | Deduped client-side via a `Set` keyed `${instanceId}:${shrineId}:${rank}`. Only fires when `result_state==="recommendation_success"` (nothing to show otherwise — this now also explicitly excludes `no_common_direction`, which likewise renders no recommendation cards, §12). |
| Recommendation → Shrine Detail (click) | `shrine_detail_transition` | `source="compass"`, `shrineId`, `recommendationRank`, `recommendationInstanceId`, `position="compact"` | `recommendationInstanceId` + `shrineId` | `CompassRecommendationsSection.tsx:71-82` | Fires on the card's `onDetailClick`, before navigation. |
| Shrine Detail view | `shrine_detail_view` | `source` (`"compass"` when `ctx=compass`), `shrineId`, `recommendationInstanceId`, `recommendationRank`, `threadId` | `recommendationInstanceId` + `shrineId` | `ShrineDetailViewTracker.tsx:30-58` | Fires once per mount (`trackedRef` guard). `ctx`/`recommendationInstanceId`/`recommendationRank` arrive via the URL (`/shrines/:id?ctx=compass&recommendation_instance_id=…&recommendation_rank=…`), built by `buildShrineHref` in `CompassRecommendationsSection.tsx`. |
| Favorite | `favorite_click`, `shrine_decision` | `source` (`"compass"` when `ctx==="compass"` at render time, else unchanged `"shrine_detail"`), `shrineId`, `recommendationInstanceId`, `analyticsSessionId`/`sessionId` (auto, via `track()`) | `recommendationInstanceId` + `shrineId`, when `source="compass"` | `ShrineSaveButton.tsx:62-90` | PR-C. `ctx`/`recommendationInstanceId` only reach this component within the **same Shrine Detail page render** (`page.tsx` overrides them explicitly on this component only). |
| Visit | `visit_done` | `source` (same rule as Favorite), `shrineId`, `recommendationInstanceId`, `accessLevel`, `historyTheme` | `recommendationInstanceId` + `shrineId`, when `source="compass"` | `ShrineDetailArticle.tsx:759-768` | PR-C. Same same-page-render scope as Favorite. |
| Reflection prompt | `reflection_prompt_view` | `source` (same rule), `shrineId`, `recommendationInstanceId`, `accessLevel` | `recommendationInstanceId` + `shrineId`, when `source="compass"` | `ShrineReflectionPrompt.tsx:54-67` | PR-C. Only rendered when `hasVisitHistory` is true in the **current** page render. |
| Reflection saved | `reflection_saved` | same as prompt + `answerLength`, `moodBefore`, `moodAfter` | same | `ShrineReflectionPrompt.tsx:87-100` | Never carries the reflection body itself (`answer` text is never sent — only its length). |

**Property presence confirmed / absent, per §3 of the task:**

| Property | Present on |
|---|---|
| `source` | `card_view`, `shrine_detail_transition`, `shrine_detail_view`, `favorite_click`, `shrine_decision`, `visit_done`, `reflection_prompt_view`, `reflection_saved` |
| `recommendationInstanceId` | All of the above **except** `home_compass_entry_click` and `compass_entry` (not yet generated at that point) |
| `shrineId` | `card_view` onward — every event from Recommendation exposure through Reflection |
| `recommendationRank` | `card_view`, `shrine_detail_transition`, `shrine_detail_view` only. **Not propagated to Favorite/Visit/Reflection** (PR-C deliberately did not add new rank plumbing where Concierge itself has none — see `docs/analytics/compass-analytics-contract.md` "Action source propagation") |
| `result_state` | `compass_result` only |
| `purpose` | `compass_result` only |
| `origin_mode` | `compass_result` only |
| `accessLevel` (Free/Premium/anonymous plan context) | `favorite_click` (as `accessLevel`, computed from guest/login state), `visit_done`, `reflection_prompt_view`, `reflection_saved`. **Absent from the entire Compass discovery→entry→result→impression→click→detail-view chain.** This is a material limitation for §20 (Free/Premium boundary) below. |
| PostHog-native anonymous/session identifier | Every event carries PostHog's own auto-generated `distinct_id` (via the SDK itself — no app code needed). The app's own custom `analyticsSessionId`/`sessionId` property is **only** explicitly attached to events dispatched through `track()` (`track.ts`) — i.e. `favorite_click`/`shrine_decision`. Every other Compass event (all `trackSearchEvent`/`trackCardEvent` calls) does **not** carry this custom property; they rely solely on PostHog's native identity. |

**Backend `recommendation_instance_id` generation** (`backend/temples/api_views_compass.py:50,76-86`): `uuid.uuid4().hex[:8]`, generated once per request, stateless (no DB write), embedded in the top-level response body **and** every recommendation item. Present in the response for every state that reaches `body = {...}` — i.e. `invalid_purpose`, `direction_filter_unavailable`, `no_common_direction`, `direction_zero_candidates`, `evidence_zero_candidates`, `recommendation_success`. **Absent** for the HTTP 500 `{"state": "error"}` path (returns before `body` is built) — this is the case the frontend labels `result_state: "backend_error"`, and `trackCompassResult` correctly passes `recommendationInstanceId: null` for it.

### 1.1 Result state vocabulary (verified against `backend/temples/services/compass_recommendation_orchestrator.py:49-54`, current `develop`, post-#2499)

```
STATE_INVALID_PURPOSE               = "invalid_purpose"
STATE_DIRECTION_FILTER_UNAVAILABLE  = "direction_filter_unavailable"
STATE_NO_COMMON_DIRECTION           = "no_common_direction"          # new, PR #2499
STATE_DIRECTION_ZERO_CANDIDATES     = "direction_zero_candidates"
STATE_EVIDENCE_ZERO_CANDIDATES      = "evidence_zero_candidates"
STATE_RECOMMENDATION_SUCCESS        = "recommendation_success"
```

Plus the frontend-only `backend_error` bucket (`CompassClient.tsx`), covering both network exceptions and any non-2xx/non-400 HTTP response. These **seven** values (six backend + one frontend-only) are never renamed or collapsed anywhere in the analytics layer — `compass_result.result_state` uses exactly these strings. `no_common_direction` is never collapsed into `direction_filter_unavailable`, and the reverse — the two are semantically distinct (Group B "valid, no common direction" vs. Group A "genuinely invalid/unavailable runtime", `docs/product/compass-mvp-runtime-contract.md` Section 8).

**Instrumentation change required to emit `no_common_direction`: NONE.** `trackCompassResult()` (`CompassClient.tsx`) forwards whatever `body.state` string the backend returns, unconditionally — it does not branch on the value. `apps/web/src/lib/analytics/searchEvents.ts`'s `result_state` TypeScript union was widened to include `"no_common_direction"` as part of #2499 (a type-only change, required only to keep compilation valid — no new event, no dispatch logic change). This document's job is purely to define how the already-flowing value should be **queried and interpreted**.

### 1.2 `calculationMethod` segmentation dimension (Monthly Fallback, new)

Added to `compass_result` per
[`compass-monthly-fallback-ui-analytics-boundary.md`](../audit/compass-monthly-fallback-ui-analytics-boundary.md)
Section 13 (Classification B: existing-event extension, no new event) and
[`compass-product-contract.md`](../product/compass-product-contract.md)
Section 2.2 / [`compass-mvp-runtime-contract.md`](../product/compass-mvp-runtime-contract.md)
Section 5-1 (#2508 Option C).

```
"annual_monthly_kyusei_v1"  -- COMMON DIRECTION (annual ∩ monthly non-empty)
"monthly_kyusei_v1"         -- MONTHLY FALLBACK DIRECTION (annual ∩ monthly empty, monthly-only used)
null                        -- no direction_context on this result (no_common_direction,
                               direction_filter_unavailable, invalid_purpose, backend_error)
```

**Query use**:

```
COMMON population:           compass_result WHERE calculationMethod = "annual_monthly_kyusei_v1"
MONTHLY_FALLBACK population: compass_result WHERE calculationMethod = "monthly_kyusei_v1"
```

**This is a diagnostic/segmentation dimension only.** It:

- does **not** alter Recommendation CTR identity (§4's join keys are
  unchanged — `recommendationInstanceId`/`shrineId`, never `calculationMethod`);
- does **not** redefine Compass Runtime Reliability Rate or Compass
  Recommendation Delivery Rate (§8) — a MONTHLY FALLBACK result is exactly
  as "reliable" and exactly as eligible for Recommendation Delivery as a
  COMMON result; only its calculation source differs;
- must **not** be read as "Fallback is an error" — a MONTHLY FALLBACK
  `calculationMethod` value co-occurs with `result_state` values including
  `recommendation_success`, `direction_zero_candidates`, and
  `evidence_zero_candidates`, exactly like a COMMON value would (§1.1's
  state vocabulary is unaffected by this dimension);
- must **not** be read as changing `no_common_direction`'s classification —
  it remains `VALID_NO_DIRECTION` (restated from §1.1 above);
  `calculationMethod` is simply absent (`null`) on that state, never
  fabricated as `"monthly_kyusei_v1"` or any other value merely because a
  fallback mechanism exists elsewhere in the system;
- must **not** be presented as evidence that Monthly Fallback "improves
  engagement" — its existence changes which direction is shown, not
  whether a user engages with the result; any such claim requires an
  actual engagement-KPI comparison, not an existence argument.

Instrumentation: `trackCompassResult()` (`CompassClient.tsx`) now threads
`body.direction_context?.calculationMethod ?? null` through as a fourth,
optional argument — no new tracking call, no new event.

---

## 2. Privacy Inventory

Re-confirmed against current code (not re-derived from the prior readiness audit):

```
Birthdate required:     NO  (only a boolean has_birthdate, always true given client-side submit gating)
Coordinates required:   NO  (only categorical origin_mode: "device"|"station"|"address"|"prefecture")
Raw origin required:    NO
Free text required:     NO  (purpose is a canonical 15-value slug, never free text)
Reflection body required: NO  (reflection_saved carries answerLength only, never the answer text)
```

No Compass-related event anywhere sends `birthdate`, `latitude`, `longitude`, raw address/station text, consultation text, or Reflection body content. The PostHog Query Contract below depends on none of these.

---

## 3. Canonical Compass Funnel

Per the task's explicit instruction not to force every stage into one giant funnel, this is split into four semantically distinct groups:

**A. Lifecycle funnel** (discovery → activation → result):
```
home_compass_entry_click → compass_entry → compass_result
```

**B. Recommendation funnel** (exposure → click → detail view):
```
card_view (source=compass) → shrine_detail_transition (source=compass) → shrine_detail_view (source=compass)
```

**C. Downstream action funnel** (detail view → action, same-page-render scope only):
```
shrine_detail_view (source=compass) → favorite_click / visit_done / reflection_prompt_view → reflection_saved
```

**D. Engagement/Retention metrics** (not funnels — time-bucketed aggregates over `compass_result`):
```
Same-Month Repeat Usage, Month-over-Month Return
```

**Why split, not one funnel:** (A) and (B) are bridged only by the frontend's own render (a `compass_result` success renders `CompassRecommendationsSection`, which then fires `card_view`) — there is no shared event connecting them other than co-occurrence in the same page state, so they compose cleanly as two PostHog Funnels joined conceptually, not as literal funnel steps. (B) and (C) are bridged by navigation (`shrine_detail_view` occurs on a different route than the click), which PostHog Funnels handle natively via distinct_id sequencing — but (C)'s later steps are governed by a **different attribution rule** (same-page-render only, §7 below) that a naive multi-step Funnel spanning A→B→C would silently misrepresent as "reachable in any session," so (C) is kept as its own funnel with its own explicit attribution caveat rather than merged into (B).

---

## 4. Recommendation Join Contract

**Required join keys**: `recommendationInstanceId` **AND** `shrineId`, together.

**Reasoning**: `recommendationInstanceId` alone identifies a single Compass request/result set (which can contain multiple shrines); `shrineId` alone can recur across many unrelated result instances (the same shrine recommended to different users, or to the same user across different months). Only the pair uniquely identifies "this specific shrine, as recommended by this specific Compass result."

**Is `recommendationRank` identity or metadata?** **Metadata (analytical dimension), not identity.** Verified: each `recommendation_instance_id` is generated once per request and its ranking is computed once, server-side, in a single ordered pass (`backend/temples/api_views_compass.py:76-79` enumerates `result.recommendations` once) — a given `shrineId` cannot appear at two different ranks within the same instance. Rank is therefore redundant with `(recommendationInstanceId, shrineId)` for identity purposes in the current architecture, but is still carried as a validation/diagnostic field (§10 rank analysis) and should be used to sanity-check joins, not to define them.

**Missing-key behavior**: if `recommendationInstanceId` is `null` (e.g. any event downstream of a `backend_error` result, which never reaches the recommendation stage at all — moot in practice, since no `card_view`/`shrine_detail_transition` can fire without a successful result), the corresponding row must be **excluded** from any recommendation-level join, never coerced to a synthetic key.

**Duplicate view behavior**: `shrine_detail_view` is deduplicated per mount via `trackedRef` (§5 below) — a single page load cannot emit two `shrine_detail_view` events for the same visit. A user re-loading the same URL (e.g. refresh) produces a **new**, legitimate `shrine_detail_view` with the same `(recommendationInstanceId, shrineId)` pair — this is correct, not a bug; it should count as a separate detail-view event for impression-level CTR (§9 below counts *distinct instance+shrine pairs opened*, so a refresh does not inflate the CTR numerator beyond 1, but does not need to be filtered out of raw event counts either).

**Multiple opens of the same shrine** (user clicks, goes back, clicks again within the same result): produces multiple `shrine_detail_transition`/`shrine_detail_view` event pairs with the identical `(recommendationInstanceId, shrineId, rank)` triple. For CTR purposes (§9), this must be deduplicated to "was this recommendation row opened at least once" — see §5.

**Multiple recommendations of the same shrine across different result instances** (same user, different Compass submissions — e.g. changed purpose): each submission generates a **new** `recommendationInstanceId` (stateless UUID, §1.1), so the same `shrineId` recommended twice across two submissions produces two independent, correctly-distinguishable rows. No special handling needed — the join key pair already disambiguates them.

---

## 5. Deduplication Contract

| Metric | Semantic counting unit | Deduplication rule |
|---|---|---|
| Compass Entry count | `compass_entry` event | Already deduplicated client-side (`entryTrackedRef`) — one event per actual mount. React re-render does not produce duplicates. |
| Compass Runtime Reliability Rate / Recommendation Delivery Rate (§8, split post-#2499) | `compass_result` event (one per submit attempt) | No client-side submit-dedup exists — a user double-clicking submit while `isLoading` is `false`... actually the button is `disabled={isLoading}` during the request, so a genuine double-submit before the first request resolves is prevented by the UI. Retries (a resubmission after seeing an error, or after a legitimate `no_common_direction` result) are **new, legitimate** `compass_result` events — not deduplicated, since each is a real distinct attempt. |
| Recommendation exposure | Recommendation row = `(recommendationInstanceId, shrineId, rank)` triple | Already deduplicated client-side (`trackedImpressionsRef`, `CompassRecommendationsSection.tsx:25-34`) — one `card_view` per unique triple even across re-renders. |
| Recommendation → Shrine Detail CTR (numerator) | Recommendation row, **not** raw event count | A recommendation row counts as "opened" if **at least one** `shrine_detail_view{source=compass}` exists with the matching `(recommendationInstanceId, shrineId)` pair — multiple opens of the same row count once for CTR, not N times. |
| Compass Result → Detail Engagement (§9B) | Compass result instance = `recommendationInstanceId` | A result instance counts as "engaged" if **at least one** of its recommended shrines was opened — multiple shrines opened from the same instance still count once. |
| Compass-attributed Favorite/Visit/Reflection rate | Shrine Detail view instance (one page render) | A Favorite toggled on then off then on again within the same page render still counts as **one** qualifying detail-view-to-action transition for the rate's numerator (the question is "did this compass-attributed detail view lead to an action," not "how many times was the button pressed"). Toggle-off (`nextFav: false`) events are excluded from the *positive-action* numerator entirely, per §12 below. |
| Same-Month Repeat Usage | distinct calendar-day-independent `compass_result` events per identity per month | See §16 — counts *instances*, not raw event volume; a user resubmitting after an error within seconds is still a second instance by this definition, since the metric is "did Compass get used more than once," not "was it used flawlessly once." |
| Month-over-Month Return | one qualifying `compass_result` per identity per month (any `result_state`, see §17) | Presence/absence per month, not a count — a person is either "present in month M" or not, regardless of how many times. |

**General rule**: never deduplicate a metric down to "per distinct person" unless the metric is explicitly person-level (Same-Month Repeat, Month-over-Month Return). Funnel/CTR metrics use the smallest correct unit — the recommendation row or the result instance — not the person, since one person can legitimately generate several independent, equally-valid recommendation rows.

---

## 6. Same-Session vs Cross-Session Attribution Boundary

**SAME-SESSION / SAME-NAVIGATION ATTRIBUTION**: the current implementation's only supported attribution mechanism. `ctx=compass`, `recommendation_instance_id`, and `recommendation_rank` travel exclusively as URL query parameters on the `/shrines/:id` navigation built by `buildShrineHref` (`CompassRecommendationsSection.tsx:62-69`). `page.tsx` reads them server-side per-request (`normalizeCtx`, `normalizeRecommendationInstanceId`) and explicitly overrides them onto `ShrineDetailArticle`/`ShrineSaveButton` for that render only (`page.tsx:500-524`, PR-C). Nothing is written to a database, cookie, or any storage that would survive past this one page load.

**CROSS-SESSION ATTRIBUTION**: **not supported, and not attempted.** A user who discovers a shrine via Compass, closes the tab, and returns to that Shrine Detail page on a different day (no `ctx=compass` in that later URL) will correctly see `source: "shrine_detail"` on any Favorite/Visit/Reflection action taken then — this is the honest, correct behavior, not a bug to fix.

**This document does not, and must not, invent a cross-session join using:**
- `shrineId` alone (recurs across unrelated users/sessions/months)
- `userId + shrineId` alone (would fabricate a causal link the data doesn't support — a user could independently rediscover the same shrine via Search or Concierge)
- nearest-timestamp heuristics
- Favorite/Visit/Reflection history correlated after the fact

**Correlation is not provenance.** Any future query that reconstructs "this Favorite probably came from that earlier Compass session" via timestamp proximity or shared `shrineId` would be fabricating attribution beyond what this instrumentation actually proves, directly contradicting the design principle established across the Compass audit chain (`docs/audit/compass-runtime-personal-continuity-boundary.md`).

---

## 7. Time Model

**Canonical reporting period: calendar month.** Not Compass's own solar-month (`solarMonthIndex`, used only for the in-product "this month's direction" display, `CompassDirectionRuntime.solarMonthIndex`). This re-affirms the recommendation already made in `docs/audit/compass-analytics-contract-readiness.md` §17: calendar month for analytics/KPI reporting, solar month reserved for in-product display logic. The two serve different consumers and conflating them risks off-by-a-few-days boundary errors in retention counts for a distinction that only matters to the product's own kyusei calculation, not to aggregate measurement.

**Timezone: `Asia/Tokyo` (JST, UTC+9, no DST)** — confirmed as the backend's own canonical timezone (`backend/shrine_project/settings.py:425`, `TIME_ZONE = "Asia/Tokyo"`). Any PostHog query bucketing by calendar month **must** use this timezone explicitly; PostHog's project-level default timezone should be verified to match before any month-boundary query is trusted (this document does not change PostHog project configuration — that verification is an operational prerequisite, flagged as an open item in §14).

**Qualifying event for a "monthly usage instance": `compass_result` with any `result_state`** (not `compass_entry`, and not restricted to `recommendation_success`) — see §16/§17 for the reasoning (an attempted-but-failed Compass usage is still evidence the person engaged with the product that month, and restricting to success-only would understate genuine repeat engagement while also conflating an engagement metric with the separate reliability metric in §8).

---

## 8. KPI Definitions

### KPI — Home Compass Entry Click Count

**Purpose**: measure how many users actively choose Compass from Home.

**Product Question**: are users discovering Compass from Home? (#1)

**Event(s)**: `home_compass_entry_click`

**Numerator**: N/A — this is a raw count metric, not a rate.

**Denominator**: **MEASUREMENT GAP.** No Home page-view or Home-section impression event exists anywhere in the codebase (`HomeMainClient.tsx`, `HomePage.tsx` — no `track`/`trackSearchEvent`/`trackCardEvent` call found). A CTR (clicks ÷ impressions) **cannot be honestly calculated today.** Do not estimate one from Home page-load analytics belonging to an unrelated event family — no such family exists either.

**Counting Unit**: event count, deduplicated by PostHog's standard event de-duplication only (no client-side impression-style dedup exists on this click, since a click is inherently a one-shot user action, not a mount-based tracker).

**Required Properties**: `source="home"` (constant — always this value, since this is the only event of this name).

**Join Keys**: none required — this is a leaf metric, though it can optionally be sequenced into a Funnel with `compass_entry` (§8's "Compass Activation" KPI below) to estimate what fraction of Home clicks result in an actual Compass page load, which is a *different*, answerable question from "how many people who saw Home chose Compass."

**Filters**: none.

**Exclusions**: none currently defined; see §27B for the general non-organic-traffic caveat.

**Deduplication**: standard PostHog event-level only.

**Attribution Window**: N/A (single event).

**Supported Cohorts**: anonymous, authenticated Free, authenticated Premium — all safely includable (event carries no plan-gating logic and Compass is plan-neutral by contract).

**Known Measurement Gaps**: no impression denominator exists; **Home Compass Discovery Rate (CTR) is not currently measurable** and must not be estimated.

**Minimum Observation Requirement**: see §27B (session diversity gate) before treating any count as representative of organic usage.

**Decision Use**: raw volume trend only — "is anyone clicking this at all," not a conversion rate.

**PostHog Representation**: Trends (event count over time), optionally broken down by `referrer` if PostHog captures it natively (not an app-level property here).

---

### KPI — Compass Activation

**Purpose**: distinguish "opened Compass" from "attempted to submit Compass" from "received a usable result."

**Product Question**: are users entering Compass, and are they completing enough input to execute it? (#2, #3)

**Event(s)**: `compass_entry` (entered), `compass_result` (submitted + resolved — see below for why these two are not split further)

**Numerator / Denominator, defined as three distinct measurements, not collapsed:**

1. **Entered Compass** = count of `compass_entry`.
2. **Submitted Compass** = count of `compass_result` (any `result_state`) — because the current architecture has **no separate "submit attempted" event distinct from "result received"** (`CompassClient.tsx`'s `handleSubmit` fires `trackCompassResult` only after the fetch resolves or throws, §1 of the readiness audit already made this exact design call: Compass's request is synchronous enough that a separate pre-flight "activation" event was judged unnecessary). Submitted and Resolved are therefore the same instant in this architecture — do not invent a distinction the event model does not support.
3. **Received a usable result** = count of `compass_result{result_state="recommendation_success"}`.

**Counting Unit**: `compass_entry`/`compass_result` event, already deduplicated at entry (§5) and not deduplicated at result (retries are legitimate distinct attempts, §5).

**Required Properties**: `referrer_source` (entry); `result_state` (result).

**Join Keys**: sequencing `compass_entry → compass_result` by `distinct_id` within a bounded window (recommend the same session; PostHog's native session concept can be used here since no custom session property exists on these two events, per §1).

**Filters**: none.

**Exclusions**: none.

**Deduplication**: see §5.

**Attribution Window**: same PostHog session (native), since no custom session id is attached to either event.

**Supported Cohorts**: anonymous, Free, Premium — all safely includable (no `accessLevel` property exists on these events at all, so no gating logic could differ by plan even if desired).

**Known Measurement Gaps**: cannot distinguish "user is still filling the form" from "user abandoned" — there is no client-side pre-submit-attempt event (deliberate, per the readiness audit's event-minimization decision), so a `compass_entry` with no following `compass_result` in a session is ambiguous between "still deciding" and "gave up."

**Minimum Observation Requirement**: §27B.

**Decision Use**: `compass_result` ÷ `compass_entry` (a "did they at least try" rate) is the only honestly derivable ratio here; do not present it as an "activation funnel" implying finer-grained steps that don't exist.

**PostHog Representation**: Funnel (`compass_entry` → `compass_result`), 2-step.

---

### Two distinct operational questions (revised post-#2499)

Before #2499, every non-`recommendation_success` outcome collapsed toward
either an explicit error state or an implicit "not success" bucket, so a
single "Compass Result Success Rate" metric could stand in for both "is the
runtime working" and "did we produce recommendations" without much cost to
clarity. Now that `no_common_direction` exists as an explicitly **valid,
non-error, no-recommendation** outcome (`docs/product/compass-product-contract.md`
Section 2.1), those two questions must be answered by two separate metrics —
collapsing them back into one would either wrongly penalize
`no_common_direction` as unreliable, or wrongly credit it as a
recommendation success. Neither KPI below changes any existing query
mechanism; both are computable from the same `compass_result.result_state`
property already in production.

### KPI — Compass Runtime Reliability Rate (OPERATIONAL)

**Purpose**: answer "did the Compass runtime complete normally, without a
technical or fail-safe failure?" — a purely computational-health question,
independent of whether a direction or recommendations resulted.

**Product Question**: what percentage of executions completed as a valid
product outcome, of any kind? (#5, reliability framing, revised)

**Event(s)**: `compass_result`

**Numerator**: `compass_result` count where `result_state` is one of
`recommendation_success`, `no_common_direction`, `direction_zero_candidates`,
`evidence_zero_candidates` — i.e. every outcome that represents a **valid,
completed calculation**, regardless of whether it produced a direction or
recommendations.

**Denominator**: all `compass_result` events, **including** `backend_error`,
`invalid_purpose`, and `direction_filter_unavailable` — the three genuinely
non-valid/error outcomes.

**Counting Unit**: `compass_result` event (submit attempt, per §5/§8 above —
retries are separate, legitimate attempts and each belongs in the
denominator).

**Required Properties**: `result_state`.

**Join Keys**: none.

**Filters**: none.

**Exclusions**: none — deliberate, reasoning per state:
- `backend_error` — **must be excluded from the numerator (counted only in the denominator).** This is exactly the failure mode this metric exists to surface.
- `invalid_purpose` — **must be excluded from the numerator.** The API contract allows it, and any occurrence (malformed request, future UI bug) should count against reliability, not be silently dropped.
- `direction_filter_unavailable` — **must be excluded from the numerator**, and per §10/§8 of `compass-analytics-contract-readiness.md`, this state specifically represents "the system could not safely complete a computation" — a genuine fail-safe/error signal (Runtime Contract Group A).
- `no_common_direction` — **must be counted in the numerator, not excluded.** This is a valid, completed calculation (Runtime Contract Group B, `docs/product/compass-mvp-runtime-contract.md` Section 8) — the runtime did not fail, it correctly found no common direction. Excluding it from the numerator would misreport a legitimate, frequent product outcome (empirically ~46.5% of algorithmic cases, `docs/audit/compass-direction-availability-product-decision.md`) as unreliability.
- `direction_zero_candidates` / `evidence_zero_candidates` — **must be counted in the numerator.** A valid, well-formed request that legitimately found a direction but no matching shrines (or no evidence-usable shrines) is a real, completed outcome, not a runtime failure.

**Deduplication**: none beyond §5's retry handling (each retry is counted).

**Attribution Window**: N/A (single event).

**Supported Cohorts**: anonymous, Free, Premium — all includable (no plan property on this event).

**Known Measurement Gaps**: none for this specific metric; the states are exhaustive and already verified against current backend code (§1.1).

**Minimum Observation Requirement**: §27B — do not compare reliability across small segments (e.g. by purpose, §22) with a trivial sample.

**Decision Use**: operational health monitoring. A sustained drop signals a backend/data/environment problem, not a product-value problem — do not conflate with the Recommendation Delivery Rate below or with engagement metrics further down this document.

**PostHog Representation**: a formula insight — count of `compass_result{result_state IN ("recommendation_success","no_common_direction","direction_zero_candidates","evidence_zero_candidates")}` ÷ total `compass_result` count — over a rolling window.

---

### KPI — Compass Recommendation Delivery Rate (OPERATIONAL)

**Purpose**: answer "what percentage of executions actually produced shrine
recommendations?" — this is the metric previously named "Compass Result
Success Rate"; its numerator and denominator are **unchanged** by this
revision, only its name and framing are corrected to avoid being read as a
reliability metric (see the split rationale above).

**Product Question**: what percentage of executions successfully produce
recommendations? (#5, delivery framing)

**Event(s)**: `compass_result`

**Numerator**: `compass_result{result_state="recommendation_success"}` count.

**Denominator**: all `compass_result` events, **including** `backend_error`,
`invalid_purpose`, `direction_filter_unavailable`, `no_common_direction`,
`direction_zero_candidates`, and `evidence_zero_candidates` — every attempt,
regardless of outcome, per the same denominator logic as before #2499.
`no_common_direction` belongs here for the same reason
`direction_zero_candidates` always did: it is a real attempt that did not
result in recommendations, so it correctly depresses this delivery-focused
rate without implying anything about reliability (that question belongs to
the KPI above, not this one).

**Counting Unit**: `compass_result` event (submit attempt, per §5/§8 above —
retries are separate, legitimate attempts and each belongs in the
denominator).

**Required Properties**: `result_state`.

**Join Keys**: none.

**Filters**: none.

**Exclusions**: none.

**Deduplication**: none beyond §5's retry handling (each retry is counted).

**Attribution Window**: N/A (single event).

**Supported Cohorts**: anonymous, Free, Premium — all includable (no plan property on this event).

**Known Measurement Gaps**: none for this specific metric; the states are exhaustive and already verified against current backend code (§1.1). Note that a low value here can now mean either "runtime is unreliable" (see Reliability Rate above) or "runtime is reliable but frequently finds no common direction / no candidates" — this KPI alone cannot distinguish the two; read it together with the Reliability Rate.

**Minimum Observation Requirement**: §27B — do not compare delivery rate across small segments (e.g. by purpose, §22) with a trivial sample.

**Decision Use**: operational/product-mix monitoring — "how often does using Compass end with something to look at." Do not read a drop here as a reliability regression without also checking the Reliability Rate above; do not conflate with engagement/value metrics below.

**Sub-breakdown (for the "operational-quality query" the task requests in §21, revised to give `no_common_direction` its own bucket rather than folding it into EMPTY/NO CANDIDATE, which is specifically about zero *shrine candidates*, not zero *direction*):**

| Bucket | `result_state` values included | Runtime validity (Reliability Rate numerator?) |
|---|---|---|
| SUCCESS | `recommendation_success` | Valid |
| VALID_NO_DIRECTION | `no_common_direction` | Valid |
| EMPTY / NO CANDIDATE | `direction_zero_candidates`, `evidence_zero_candidates` | Valid |
| ERROR | `backend_error`, `direction_filter_unavailable` | Invalid |
| OTHER | `invalid_purpose` | Invalid |

**PostHog Representation**: Trends (event count, breakdown by `result_state`), or a single formula insight (`recommendation_success` count ÷ total `compass_result` count) over a rolling window.

---

### KPI — Recommendation → Shrine Detail CTR (PRIMARY, recommendation-level — the primary Recommendation CTR)

**Purpose**: the headline metric PR-B was built to support — of the shrines Compass recommended, which were actually opened.

**Product Question**: which displayed recommendations are actually opened? (#4)

**Event(s)**: `card_view` (numerator base / denominator), `shrine_detail_view` (numerator qualifier)

**Numerator**: count of distinct `(recommendationInstanceId, shrineId)` pairs from `card_view{source="compass"}` for which **at least one** matching `shrine_detail_view{source="compass", recommendationInstanceId, shrineId}` exists (§5 dedup rule — multiple opens of the same row count once).

**Denominator**: count of distinct `(recommendationInstanceId, shrineId)` pairs from `card_view{source="compass"}`.

**Counting Unit**: recommendation row (`recommendationInstanceId` + `shrineId` pair) — **not** raw event count, **not** person, **not** result instance.

**Required Properties**: `recommendationInstanceId`, `shrineId`, `source="compass"` on both events; `recommendationRank` present but not required for the join (§4).

**Join Keys**: `recommendationInstanceId` AND `shrineId` (§4, required, exact match, both must be present).

**Filters**: `source="compass"` on both sides (excludes Concierge/map-originated impressions and detail views from this Compass-specific metric — Concierge has its own separate, pre-existing CTR measurement, unaffected by this document).

**Exclusions**: rows where `recommendationInstanceId` is null (cannot occur for `card_view`, since it only fires after a successful result, §1) or where `shrineId` is null (cannot occur — `CompassRecommendationsSection.tsx:30` explicitly guards `if (shrineId == null) return`).

**`no_common_direction` and `direction_zero_candidates` in this denominator (confirmed, revised post-#2499)**: **neither enters the denominator**, and this requires no query-level exclusion — both are structurally absent from `card_view` by construction. `card_view` only fires when `CompassRecommendationsSection` renders, which only happens when `result_state==="recommendation_success"` (§1 row above); `no_common_direction` and `direction_zero_candidates` both return `recommendations: []` (`compass_recommendation_orchestrator.py`), so no recommendation cards — and therefore no `card_view` impressions — are ever produced for either state. Do not fabricate a recommendation impression for a valid-but-empty result state to "complete" this denominator.

**Deduplication**: §5 — impression-side already deduplicated client-side; detail-view-side collapses to "opened at least once" for this metric.

**Attribution Window**: unbounded within the life of the browser tab/session that generated the impression — since both events fire from the same `recommendationInstanceId`-scoped result and the click happens via an in-app navigation from the same recommendation list, there is no realistic scenario where a legitimate open happens outside the immediate session. (This is a same-session metric by construction, not because of an explicit time cutoff.)

**Supported Cohorts**: anonymous, Free, Premium — all includable (no `accessLevel` on Recommendation-stage events).

**Known Measurement Gaps**: none for this specific metric — this is the one KPI the instrumentation is most directly and completely built to support.

**Minimum Observation Requirement**: §27A/B — a handful of impressions is not a reliable CTR.

**Decision Use**: primary signal for "does Compass's recommendation list itself create real interest," independent of what happens after the detail view.

**PostHog Representation**: Funnel (`card_view` → `shrine_detail_view`, both filtered `source=compass`, matched on `recommendationInstanceId` + `shrineId` as the funnel's per-actor grouping key if PostHog's funnel engine is configured to group by a custom property rather than `distinct_id`) — otherwise, a HogQL query directly joining the two event tables on the two required keys is the more precise conceptual approach; provided as pseudocode only, not an executed query:

```
-- conceptual, not executed
SELECT
  card_view.recommendationInstanceId,
  card_view.shrineId,
  count(DISTINCT card_view.recommendationInstanceId || ':' || card_view.shrineId) AS impressions,
  count(DISTINCT CASE WHEN detail.shrineId IS NOT NULL
        THEN card_view.recommendationInstanceId || ':' || card_view.shrineId END) AS opened
FROM events card_view
LEFT JOIN events detail
  ON detail.event = 'shrine_detail_view'
  AND detail.properties.source = 'compass'
  AND detail.properties.recommendationInstanceId = card_view.properties.recommendationInstanceId
  AND detail.properties.shrineId = card_view.properties.shrineId
WHERE card_view.event = 'card_view'
  AND card_view.properties.source = 'compass'
```

---

### KPI — Result Instance → Detail Engagement Rate (SECONDARY, result-session-level)

**Purpose**: a coarser, complementary view of the same underlying behavior — "did this Compass result create *any* interest," independent of which or how many specific rows were opened.

**Product Question**: do users inspect the recommended shrines, at the level of a whole Compass result? (#3, coarse framing)

**Event(s)**: `compass_result`, `shrine_detail_view`

**Numerator**: count of distinct `recommendationInstanceId` values (from `compass_result{result_state="recommendation_success"}`) for which **at least one** `shrine_detail_view{source="compass", recommendationInstanceId}` exists.

**Denominator**: count of distinct `recommendationInstanceId` values from `compass_result{result_state="recommendation_success", recommendation_count>0}`.

**Denominator meaning (clarified post-#2499)**: this denominator means **result instances that actually contained at least one recommendation**, not **all Compass result attempts**. The `result_state="recommendation_success"` filter already excludes `no_common_direction`, `direction_zero_candidates`, `evidence_zero_candidates`, `invalid_purpose`, `direction_filter_unavailable`, and `backend_error` — none of these ever reach this denominator, and none should: an attempt that produced zero recommendations has nothing for a Shrine Detail view to "engage" with. Before `no_common_direction` existed as a distinct state, this exclusion was less visible (it was one of several outcomes folded under an implicit "not success" umbrella); now that it is a named, expected outcome, this document states explicitly that this KPI answers "of the Compass results that had something to show, how many got at least one look" — not "of all Compass attempts."

**Counting Unit**: Compass result instance (`recommendationInstanceId`) — coarser than the recommendation-row unit above.

**Required Properties**: `recommendationInstanceId`, `recommendation_count` (to exclude instances with zero recommendations from the denominator, though `recommendation_count>0` should already be implied by `result_state="recommendation_success"` — kept as an explicit filter for defensive correctness).

**Join Keys**: `recommendationInstanceId` only (rank/shrineId not needed at this coarser grain).

**Filters**: `result_state="recommendation_success"` on the denominator side.

**Exclusions**: same null-key exclusions as the recommendation-level KPI above.

**Deduplication**: §5 — one qualifying instance counts once regardless of how many of its shrines were opened.

**Attribution Window**: same as the recommendation-level KPI (same-session, by construction).

**Supported Cohorts**: anonymous, Free, Premium.

**Known Measurement Gaps**: none.

**Minimum Observation Requirement**: §27A/B.

**Decision Use**: **this is the metric nominated as the answer to product question #3 ("do users inspect the recommended shrines") at the aggregate level**; the recommendation-level CTR above remains the **primary** Recommendation CTR (nominated per the task's explicit instruction to nominate one). This metric is a useful secondary cross-check — a low recommendation-level CTR with a high result-level engagement rate would indicate users open exactly one shrine and stop (satisfied quickly), while the reverse pattern would be harder to interpret and worth a follow-up look.

**PostHog Representation**: Funnel (`compass_result` filtered `result_state=recommendation_success` → `shrine_detail_view` filtered `source=compass`, matched by `recommendationInstanceId`).

---

**`no_common_direction` and downstream Favorite/Visit/Reflection KPIs (confirmed, revised post-#2499)**: none of the three KPIs below (Favorite, Visit, Reflection) require any change on account of `no_common_direction`. Each is keyed off `shrine_detail_view{source="compass"}` as its base event (directly or via `recommendationInstanceId`+`shrineId`), and — per the CTR reasoning above — `shrine_detail_view{source="compass"}` cannot exist without a prior `card_view`, which cannot exist without `result_state="recommendation_success"`. A `no_common_direction` result never produces a Shrine Detail view under the current implementation (`docs/product/compass-product-contract.md` Section 2.1-5 records the Shrine-Recommendation boundary as an explicit **OPEN PRODUCT DECISION** — current behavior is "no direction → no recommendation candidate flow," unchanged by #2499). Therefore `no_common_direction` cannot enter any Favorite/Visit/Reflection conversion denominator today, and this document does not fabricate one. If that OPEN PRODUCT DECISION is ever resolved in favor of showing purpose-only recommendations without a direction, these KPI definitions will need to be revisited at that time — not before.

### KPI — Compass-attributed Favorite Rate (PRIMARY)

**Purpose**: the strongest honestly measurable Favorite metric now that PR-C propagates `source=compass` into `favorite_click`.

**Product Question**: do Compass-originated detail views lead to Favorite? (#5)

**Event(s)**: `shrine_detail_view`, `favorite_click`

**Numerator**: count of distinct `shrine_detail_view{source="compass"}` instances (identified by `recommendationInstanceId` + `shrineId`, or failing that, session + shrineId — see below) for which a matching `favorite_click{source="compass", nextFav=true}` exists in the same page render.

**Denominator**: count of `shrine_detail_view{source="compass"}` events.

**Counting Unit**: Shrine Detail view instance (one page render reached via Compass).

**Required Properties**: `source`, `shrineId`, `recommendationInstanceId` (on both events, when present); `nextFav` (on `favorite_click`, to isolate the save action from the unsave action).

**Join Keys**: `recommendationInstanceId` + `shrineId`, **verified available** — PR-C threads the same `detailRecommendationInstanceId` (`compassRecommendationInstanceId ?? conciergeRecommendationInstanceId`) into `ShrineSaveButton` that `ShrineDetailViewTracker` already receives (`page.tsx`), so a **recommendation-level** join is genuinely possible here, not merely a coarser same-session approximation. This is a stronger result than the pre-implementation audit anticipated (`compass-analytics-contract-readiness.md` §13 had flagged Favorite attribution as an open question pending exactly this wiring, which PR-C completed).

**Filters**: `source="compass"` on both sides; `nextFav=true` on `favorite_click` (excludes the toggle-off action from the positive numerator, per §5/§11).

**Exclusions**: `favorite_click{nextFav=false}` (unsave) is excluded from this rate's numerator entirely — it answers a different question (retention-of-save, not conversion-to-save) not defined as a KPI here.

**Deduplication**: §5 — multiple toggles within the same page render still count as one qualifying instance.

**Attribution Window**: **same Shrine Detail page render only** (§6). `ShrineSaveButton.tsx`'s `ctx`/`recommendationInstanceId` props are populated exclusively from `page.tsx`'s per-request override — there is no mechanism for a Favorite click on a *later*, separate page load to carry `source=compass`.

**Supported Cohorts**: anonymous is **excluded by construction** — `Favorite` requires authentication (`ShrineSaveButton`'s guest-mode path redirects to login rather than saving, `useFavorite.ts`). This metric is therefore Free + Premium only, not anonymous. `accessLevel` is present on `favorite_click`, so a Free/Premium breakdown is technically possible (§20 caveat: exploratory only, not a Premium-quality claim).

**Known Measurement Gaps**: **cross-session Compass → Favorite is not measurable** and must not be estimated (§6). A user who returns on a different day and favorites a shrine they first saw via Compass will not be attributed to Compass — this is the honest, by-design limitation, not a bug.

**Minimum Observation Requirement**: §27A/B — Favorite is a rarer action than a detail view; expect a smaller sample than the CTR above.

**Decision Use**: primary signal for "does Compass surface shrines worth intentionally saving," bounded strictly to the same-visit window. Never report this as "X% of Compass users favorite a shrine" without the same-session caveat attached.

**PostHog Representation**: Funnel (`shrine_detail_view` filtered `source=compass` → `favorite_click` filtered `source=compass, nextFav=true`, matched on `recommendationInstanceId` + `shrineId`).

---

### KPI — Compass-attributed Visit Rate (PRIMARY, carefully named)

**Purpose**: the strongest honestly measurable Visit metric, named to avoid implying causality the architecture cannot prove.

**Product Question**: do Compass-originated detail views lead to Visit? (#6)

**Event(s)**: `shrine_detail_view`, `visit_done`

**Numerator**: count of distinct `shrine_detail_view{source="compass"}` instances for which a matching `visit_done{source="compass"}` exists in the same page render.

**Denominator**: count of `shrine_detail_view{source="compass"}` events.

**Counting Unit**: Shrine Detail view instance.

**Required Properties**: `source`, `shrineId`, `recommendationInstanceId` (both events).

**Join Keys**: `recommendationInstanceId` + `shrineId`, same availability as Favorite above (PR-C wiring).

**Filters**: `source="compass"` on both sides.

**Exclusions**: none additional.

**Deduplication**: §5.

**Attribution Window**: **same Shrine Detail page render only**, identical constraint to Favorite (§6).

**Naming discipline — explicit, per the task's instruction**: this metric must be read as **"a Visit was recorded while Compass context remained available (same page render),"** never as **"Compass caused this Visit."** A physical shrine visit is, by nature, far more likely than a Favorite to happen in a *later* browsing session than the initial Compass discovery (the task's own example: discover → leave → return later → visit later) — meaning this metric's *coverage* (what fraction of true Compass-driven visits it can even see) is expected to be **lower** than Favorite's, even though the *mechanism* for computing it is identical. This is a coverage limitation, not a measurement error.

**Supported Cohorts**: anonymous, Free, Premium all included — `Visit` does not require authentication in the current architecture (unlike Favorite; confirmed no guest-mode redirect exists in `ShrineDetailArticle.tsx`'s visit button handler, only Favorite has one).

**Known Measurement Gaps**: cross-session Compass → Visit is not measurable (§6) — and, per the naming discussion above, is expected to be the *majority* of true Compass-driven visits, meaning this metric likely represents a **small, non-representative subset** of actual Compass-driven visiting behavior. Do not extrapolate this rate to estimate "true" Compass-driven visit volume.

**Minimum Observation Requirement**: §27A/B — expect a low sample size by nature; do not draw conclusions from a handful of events.

**Decision Use**: a lower-bound signal only — "at least this many Compass-driven visits happened in the same sitting." Never the numerator for a claimed overall Compass→Visit conversion rate.

**PostHog Representation**: Funnel (`shrine_detail_view` filtered `source=compass` → `visit_done` filtered `source=compass`, matched on `recommendationInstanceId` + `shrineId`).

---

### KPI — Compass-attributed Reflection (SECONDARY / DIAGNOSTIC, same-session only)

**Purpose**: audit what Reflection can actually prove about Compass provenance, per the task's explicit caution against inventing cross-session causality here (#7).

**Product Question**: what downstream Reflection attribution is honestly measurable? (#7)

**Event(s)**: `shrine_detail_view`, `visit_done`, `reflection_prompt_view`, `reflection_saved`

**Attribution classification, per event:**

| Event | Classification | Reasoning |
|---|---|---|
| `reflection_prompt_view` | **SESSION/NAVIGATION** (only when it appears within the same page render as a Compass-attributed `visit_done`) | `ShrineReflectionPrompt` only renders when `hasVisitHistory` is true; if that becomes true via the *current* render's own Visit action, `source="compass"` correctly propagates. If `hasVisitHistory` is true from a **prior**, separate visit (page loaded fresh, no `ctx=compass` in this URL), `source` correctly falls back to `"shrine_detail"` — no false attribution. |
| `reflection_saved` | **SESSION/NAVIGATION** (same rule) | Same mechanism as prompt. |
| Reflection occurring in a genuinely later, separate session (different day, different page load, no `ctx=compass`) | **NOT AVAILABLE** | Classified as a **MEASUREMENT GAP** below, not a KPI. |

**Numerator (if computed)**: count of `shrine_detail_view{source="compass"}` instances for which a matching `reflection_saved{source="compass"}` exists in the same page render.

**Denominator (if computed)**: count of `shrine_detail_view{source="compass"}` events, or more precisely the subset that also produced a `visit_done{source="compass"}` (since Reflection is gated on Visit).

**Counting Unit**: Shrine Detail view instance.

**Required Properties**: `source`, `shrineId`, `recommendationInstanceId`.

**Join Keys**: `recommendationInstanceId` + `shrineId`.

**Filters**: `source="compass"`.

**Exclusions**: none additional beyond the null-key rule.

**Deduplication**: §5.

**Attribution Window**: same page render only — realistically the narrowest window of any KPI in this document, since it requires Visit **and** Reflection both to occur before the user navigates away.

**Supported Cohorts**: anonymous, Free, Premium (Reflection does not require authentication in current code, `accessLevel` can be `"anonymous"`).

**Known Measurement Gaps**: **the long-term "Compass → Reflection" relationship the product cares about most (does a Compass-driven visit eventually get reflected on, even days later) is explicitly a MEASUREMENT GAP.** Per the task's instruction, no KPI in this document implies that longer-horizon causality. If this same-session variant's volume proves too low to be useful (likely, given how rarely Visit-then-Reflection both happen in one sitting for a physical-world action), do not manufacture a substitute — report it as near-zero-volume and leave the long-horizon question explicitly unanswered pending future instrumentation (out of scope here, §31).

**Minimum Observation Requirement**: §27A/B, with the expectation that this metric may never reach a usable sample size under the current architecture.

**Decision Use**: diagnostic only — not a headline KPI. Useful primarily to confirm the mechanism works at all (non-zero), not to estimate a rate.

**PostHog Representation**: Funnel (4-step: `shrine_detail_view` → `visit_done` → `reflection_prompt_view` → `reflection_saved`, all filtered `source=compass`, matched on `recommendationInstanceId` + `shrineId`) — expect very low counts by construction.

---

### KPI — Same-Month Compass Repeat Usage (SECONDARY — Engagement, explicitly not Retention)

**Purpose**: measure within-month re-use, classified strictly as an engagement diagnostic per the task's explicit instruction (§16), never as a retention signal.

**Product Question**: do users use Compass repeatedly within the same month? (#8)

**Event(s)**: `compass_result`

**Numerator**: count of identities (see cohort note below) with **2 or more** distinct `compass_result` events (any `result_state`) within the same calendar month M.

**Denominator**: count of identities with **at least 1** `compass_result` event within calendar month M.

**Counting Unit**: identity × calendar month (see Identity below).

**Required Properties**: none beyond the event's existence; `result_state` optionally for a "repeat that changed purpose/origin vs. repeat with identical inputs" secondary breakdown (`purpose`, `origin_mode` are available on the event for this — no new property needed).

**Join Keys**: none (single-event aggregate).

**Filters**: calendar month boundary (§7, `Asia/Tokyo`).

**Exclusions**: §27B (non-organic traffic).

**Deduplication**: counts distinct **instances** (events), not deduplicated further — a second `compass_result` seconds after the first (e.g. a quick purpose change) legitimately counts as usage instance #2, per the reasoning in §5.

**Attribution Window**: one calendar month.

**Supported Cohorts — critical limitation, per the task's explicit instruction not to silently treat anonymous `distinct_id` as account identity**: PostHog's `distinct_id` is the only available identity for this metric, for **both** anonymous and logged-in users, **because `posthog.identify()` is never called anywhere in this codebase** (verified: no occurrence in `apps/web/src` or `backend/`, re-confirmed for this audit). Consequently:
- An anonymous `distinct_id` is a browser/device-local, `localStorage`/cookie-backed identifier via posthog-js's own default behavior — it survives across page loads **on the same browser, same device**, but is lost on cache clear, private browsing, or a different device.
- A **logged-in** user gets **no stronger identity signal in PostHog than an anonymous one** — logging in does not currently call `identify()`, so a logged-in user on two different devices appears as two unrelated `distinct_id`s in PostHog, indistinguishable from two different anonymous people.
- This metric is therefore an **undercount** of true repeat usage by real people, not an overcount — the failure mode is losing the identifier (device change, cache clear), never double-counting a single person as two.

**Known Measurement Gaps**: repeated `compass_entry` events without an intervening `compass_result` are **not** counted as "usage instances" for this metric (a `compass_entry` alone, per §8's Activation KPI, only proves the page loaded, not that Compass was used) — this is a deliberate scoping choice, not an oversight.

**Minimum Observation Requirement**: §27A/B/D.

**Decision Use**: engagement diagnostic. **Must never be presented as a retention or Premium-continuity signal** — the task is explicit that repeat same-month use may reflect purpose exploration, origin exploration, retry-after-empty-result, curiosity, or accidental repeat, none of which are retention evidence on their own.

**PostHog Representation**: Trends with a "unique users doing event 2+ times" style aggregation, or a cohort-based breakdown; alternatively Retention with a same-period (day-granularity-within-month) window if PostHog's native Retention insight is repurposed for an intra-month view rather than its default cross-period use (documented here as a conceptual option, not a built query).

---

### KPI — Month-over-Month Compass Return (PRIMARY — the primary Retention concept)

**Purpose**: the primary retention hypothesis for Compass, per the task's explicit framing and consistent with the entire prior Compass audit chain.

**Product Question**: do users return to Compass in a later month? (#9)

**Event(s)**: `compass_result`

**Numerator**: count of identities with a qualifying `compass_result` in calendar month M **and** a qualifying `compass_result` in calendar month M+1 (or, for a looser "eventual return" variant, any month after M).

**Denominator**: count of identities with a qualifying `compass_result` in calendar month M.

**Counting Unit**: identity, presence/absence per month (not a count within the month — see §5).

**Required Properties**: none beyond event existence.

**Join Keys**: none (single-event-type, self-joined across two time windows by identity).

**Filters**: calendar month boundaries, `Asia/Tokyo` (§7).

**Exclusions**: §27B/C.

**Deduplication**: presence-based, not count-based — multiple `compass_result` events within month M+1 still count as one "returned" instance.

**Attribution Window**: exactly two adjacent calendar months for the strict definition; open-ended for the "eventual return" variant.

**Supported Cohorts**: same identity limitation as Same-Month Repeat above — anonymous `distinct_id` only, no `identify()` anywhere, so this metric **structurally undercounts** true person-level return behavior, more severely than the within-month metric since the cross-month window gives more opportunity for the identifier to be lost (device change, cache clear, time elapsed).

**Known Measurement Gaps**: identical identity limitation as above, compounded by elapsed time; and the **mandatory Time Gate below**.

**Minimum Observation Requirement — MANDATORY HARD RULE (§28 of the task, non-negotiable):**

> **MONTH-OVER-MONTH RETURN MUST NOT BE JUDGED WITH LESS THAN TWO ELIGIBLE CALENDAR MONTHS OF REAL USAGE.**

If fewer than two full eligible calendar months of `compass_result` data exist since Measurement Valid From (§9 below), this metric's status is:

```
Status: INSUFFICIENT OBSERVATION WINDOW
```

**never** `Status: LOW RETENTION` or a computed `0%`. A zero or near-zero value computed before two eligible months exist is not evidence of low retention — it is definitionally impossible to have observed a return yet, and reporting it as a rate would be actively misleading.

**Decision Use**: this is the metric this document nominates as the **primary Retention signal for Compass**, and — per §29 below — one of the key inputs to any future decision about reopening Personal Continuity. It must not be computed or reported until the Time Gate above is satisfied.

**PostHog Representation**: PostHog's native Retention insight (event-based, `compass_result` as both the "first event" and "returning event," monthly granularity, `Asia/Tokyo` project timezone) is the natural fit — conceptually described here, not configured or executed in this audit.

---

### Diagnostic dimensions (SECONDARY / not standalone KPIs)

**Rank breakdown** (§22 of the task): what fraction of Shrine Detail opens come from rank 1 / 2 / 3 / etc. **Classification: SECONDARY DIAGNOSTIC**, per the task's own steer to prefer this classification absent contrary evidence. `recommendationRank` is available on `card_view`, `shrine_detail_transition`, and `shrine_detail_view` (§1), so this is a straightforward breakdown of the primary Recommendation CTR KPI by the `recommendationRank` property — not a new query mechanism, just a `breakdown` dimension on the existing Funnel/Trends insight. Rank is metadata, not identity (§4) — never used to define "the same recommendation," only to segment an already-defined metric.

**Purpose segmentation** (§23): `purpose` is a coarse, canonical 15-value slug present on `compass_result` — safe as a non-PII breakdown dimension on any of the above KPIs computed from or downstream of `compass_result`. **Do not interpret a CTR/rate difference between purposes as proof one purpose is "better."** This document also preserves, without re-litigating, the previously-documented product caveat that some purpose-taxonomy mappings may currently produce equivalent Recommendation behavior — any purpose-level comparison should be read with that caveat in mind, not treated as clean independent variables. Taxonomy correctness is out of scope for this audit.

**Origin mode segmentation** (§24): `origin_mode` (`"device"|"station"|"address"|"prefecture"`) is present on `compass_result` — safe as a coarse, non-PII breakdown dimension. **Never** use `latitude`/`longitude`/raw address/station text for PostHog segmentation — these are never sent (§2) and must never be added for this purpose.

**`calculationMethod` segmentation** (Monthly Fallback, §1.2): `calculationMethod` (`"annual_monthly_kyusei_v1"|"monthly_kyusei_v1"|null`) is present on `compass_result` — safe as a coarse, non-PII breakdown dimension, same category as `purpose`/`origin_mode` above. **Classification: SECONDARY DIAGNOSTIC**, not a standalone KPI and not a redefinition of any KPI in §8 (see §1.2 for the full boundary). Do not interpret a CTR/engagement difference between COMMON and MONTHLY_FALLBACK populations as proof one calculation source is "better" — the same non-comparison caveat given for Purpose segmentation above applies here.

---

## 9. Existing Data Limitations — Measurement Valid From

Every event in this contract was introduced across three merged PRs. Data recorded **before** each PR's production deployment cannot be joined with data recorded after it, and pre-instrumentation traffic must never be mixed into any of the KPIs above.

| Event(s) | Introduced in | Measurement Valid From |
|---|---|---|
| `home_compass_entry_click`, `compass_entry`, `compass_result` (without `recommendationInstanceId`) | PR-A (#2488, merged) | OPEN / DEPLOYMENT DATE REQUIRED — exact production deploy timestamp not available to this audit; merge timestamp (`2026-08-19T04:24:55Z`, PR merge record) is the earliest possible bound, not necessarily the production rollout time. |
| `compass_result.recommendationInstanceId`, `card_view{source=compass}`, `shrine_detail_transition{source=compass}`, `shrine_detail_view{source=compass}` | PR-B (#2489, merged) | OPEN / DEPLOYMENT DATE REQUIRED — merge timestamp `2026-08-19T08:25:22Z` is the earliest possible bound. |
| `favorite_click`/`shrine_decision`/`visit_done`/`reflection_prompt_view`/`reflection_saved` carrying `source=compass` | PR-C (#2490, merged) | OPEN / DEPLOYMENT DATE REQUIRED — merge timestamp available in git history, exact production deploy timestamp not verified by this audit. |
| `compass_result{result_state="no_common_direction"}` | PR #2499 (merged) | **`2026-08-20T10:54:25Z`** — confirmed via Vercel production deployment record (`target=production`, `state=READY`, `githubCommitSha` matches PR #2499's merge commit `41cba8d6` exactly) and cross-checked against Render backend `healthz` release (`41cba8d6`, identical commit) — both frontend and backend serving this logic in production from this timestamp, not merely inferred from git merge time. |
| `compass_result.calculationMethod` (Monthly Fallback segmentation, §1.2) | This PR (Analytics Alignment) | OPEN / DEPLOYMENT DATE REQUIRED — not established here; this is an implementation-only PR (task §31 explicit instruction not to run Production PostHog queries or establish the deploy boundary). The actual production deploy timestamp is to be recorded during the later, separate Production Verification task, following the same evidence standard as the `no_common_direction` row above (Vercel/Render deployment records cross-checked against the merge commit, not the git merge timestamp alone). |

Any KPI in this document that spans the PR-A/PR-B boundary (e.g. the Compass Activation funnel, which needs both `compass_entry` and `compass_result`) is valid from PR-A's deployment. Any KPI depending on `recommendationInstanceId`-based joins (Recommendation CTR, Favorite/Visit/Reflection attribution) is valid only from PR-B's deployment onward, **not** from PR-A's. Do not backfill or approximate pre-PR-B data for these. Any query that filters or breaks down by `result_state="no_common_direction"` specifically is valid only from **2026-08-20T10:54:25Z** onward — see the Historical Classification Break note immediately below for why this boundary is unusually important for this particular state.

**HISTORICAL CLASSIFICATION BREAK**: before PR #2499's deployment (`2026-08-20T10:54:25Z`), the `no_common_direction` state **did not exist in the implementation** — a valid, completed calculation with an empty annual/monthly intersection was indistinguishable, at the code level, from a genuinely invalid/unavailable runtime, and both were emitted as `result_state="direction_filter_unavailable"` (`docs/audit/compass-direction-filter-unavailable-root-cause.md`). Consequently:

- **Historical `direction_filter_unavailable` counts recorded before this timestamp are not directly comparable to `direction_filter_unavailable` counts recorded after it.** Pre-#2499, that bucket contains an unknown mixture of true errors (Group A) and what would now be classified `no_common_direction` (Group B) — post-#2499, it contains Group A only. A pre/post trend line on `direction_filter_unavailable` alone would read as a reliability *improvement* that is actually a classification split, not a behavior change.
- **Do not retroactively reclassify individual historical `direction_filter_unavailable` events as `no_common_direction`** (or vice versa) after the fact. No property recorded on those historical events distinguishes which Group they belonged to (see #2496's audit of the collapse point); any retroactive relabeling would be a fabricated inference, not a query.
- Any Reliability Rate or Recommendation Delivery Rate trend that spans this boundary must state the boundary explicitly and should not be presented as a single continuous series without that caveat.
- This is the same category of limitation §14 (Open Items) already names for PR-A/B/C's own undetermined exact deployment timestamps — this row is simply the one boundary in this document precise enough to state exactly, and consequential enough (a real behavior-vs-classification distinction, not just an unknown start date) to call out on its own.

**HISTORICAL BOUNDARY (calculationMethod, §1.2)**: before this Analytics Alignment PR's production deployment, `compass_result` never carried a `calculationMethod` property at all — the Monthly Fallback Runtime (#2510) and UI/Copy Alignment (#2512) changes were already live in production by that point, but PostHog had no way to observe which of a request's results were COMMON vs. MONTHLY_FALLBACK. Consequently:

- **Do not retroactively infer `calculationMethod` for historical `compass_result` events recorded before this property's deployment** from timestamps, shrine IDs, recommendation results, or historical `result_state` distributions. Correlation is not provenance (task §29) — no historical event carries the information needed to determine which branch produced it.
- Any query segmenting by `calculationMethod` is valid only from this PR's own, separately-established production deploy timestamp onward (row above) — not from #2510's or #2512's deploy dates, which predate PostHog's ability to observe this dimension at all.

---

## 10. Anonymous vs Authenticated Users, and the Free/Premium Boundary

**Compass usage itself is Free/Premium neutral by contract, confirmed unaffected**: no Compass lifecycle, Recommendation, or Shrine-Detail-view event (`home_compass_entry_click` through `shrine_detail_view`) carries an `accessLevel`/plan property at all (§1) — there is structurally no way for a query against this stage of the funnel to differ by plan, which is the correct, contract-preserving state.

**`accessLevel` first appears at the action boundary**: `favorite_click`, `visit_done`, `reflection_prompt_view`, `reflection_saved` do carry `accessLevel` (`"anonymous"|"free"|"premium"`). This means:
- Metrics through Shrine Detail view: safely includable across anonymous/Free/Premium, no segmentation even possible.
- Favorite/Visit/Reflection-stage metrics: **exploratory** Free-vs-Premium breakdown is technically possible using the existing `accessLevel` property, without adding instrumentation — per the task's explicit allowance (§20) that this may be exploratory only, given current analytics already provides the needed non-PII plan context at this specific stage.

**Do not define Premium success as better Recommendation quality** — there is no mechanism for that claim to even be constructed from this data (Recommendation-stage events carry no plan property, and the underlying Recommendation logic itself is untouched by any of PR-A/B/C, confirmed by all three PRs' own explicit non-goals).

**Identity requirement by metric type**:
- Funnel/CTR/rate metrics (Recommendation CTR, Favorite/Visit/Reflection rate): do **not** require stable person-level identity — they operate on event-level joins (`recommendationInstanceId`+`shrineId`) or session-scoped attribution, safe for anonymous users.
- Retention metrics (Same-Month Repeat, Month-over-Month Return): **do** require identity continuity across time, and — per §8 above — this is currently only PostHog's own `distinct_id`, unlinked to real account identity for anyone, authenticated or not.

---

## 11. Observation Gates

**A. Sample Size Gate**: no statistically authoritative numeric threshold is invented here — consistent with this repository's established, repeated pattern (`docs/audit/posthog-recommendation-quality-observation-cadence.md`, `docs/audit/recommendation-quality-observation-operations.md`, `docs/audit/knowledge-recommendation-analytics-baseline-readiness.md`, all explicitly refuse to fabricate a sample-size number). **Classified as: PRODUCT/ANALYTICS DECISION REQUIRED** if a specific threshold is ever needed; until then, treat any KPI computed from a single-digit or low-double-digit event count as non-decision-grade, qualitatively.

**B. Session Diversity Gate**: do not treat Mother Ship QA/developer traffic as organic usage. This document does not define a technical bot/QA-filtering mechanism (none currently exists in the Compass event properties — no `is_test`/`is_internal` flag is sent by any Compass event) — flagged as an **open operational gap**: any future query execution against these KPIs should first confirm whether PostHog project-level internal-traffic filtering (e.g. IP-based) is configured, since app-level filtering is not available.

**C. Time Gate**: §8's Month-over-Month Return hard rule — never judged with fewer than two eligible calendar months.

**D. Identity Gate**: never claim user-level retention when only unstable anonymous `distinct_id` is available (§8, §10) — always state this limitation alongside any Same-Month Repeat or Month-over-Month Return figure.

**E. Attribution Gate**: never claim Compass → Visit/Reflection causal conversion beyond the same-page-render attribution boundary (§6) — the Favorite/Visit/Reflection KPIs above are named and scoped specifically to avoid this.

---

## 12. Personal Continuity Decision Gate

Personal Continuity remains deferred (`docs/audit/compass-runtime-personal-continuity-boundary.md`, `docs/audit/compass-premium-personal-continuity.md`). This document does not reopen that decision. It defines, without asserting any threshold has been met, what evidence a future review would need to draw on:

- A meaningfully non-zero **Month-over-Month Compass Return** (§8), observed only after the mandatory two-month Time Gate has passed.
- Non-trivial **Recommendation → Shrine Detail CTR** and **Result Instance → Detail Engagement Rate** sustained across enough session diversity to rule out a small-sample artifact.
- Non-trivial **Compass-attributed Favorite Rate** and (to the extent its low expected coverage allows) **Visit Rate**, specifically the same-session-attributable subset — understanding these almost certainly undercount true Compass-driven action volume (§6).
- Any qualitative signal (user feedback, support requests) indicating desire for saved/continuous shrine journey — outside this document's data scope entirely.

No specific numeric threshold is set for any of the above — consistent with §27A, this is recorded as a **future Product Decision Gate**, not a rule this audit can pre-resolve. Personal Continuity is **not implemented** by this document, and this document does not recommend implementing it.

---

## 13. Primary KPI Set

Per the task's instruction to target ~4–6 primary metrics, not a 25-number dashboard:

| Metric | Classification |
|---|---|
| Compass Runtime Reliability Rate (revised, was part of "Compass Result Success Rate") | OPERATIONAL |
| Compass Recommendation Delivery Rate (revised, was "Compass Result Success Rate") | OPERATIONAL |
| No-Common-Direction Frequency (`no_common_direction` share of `compass_result`) | SECONDARY / OPERATIONAL DIAGNOSTIC |
| Recommendation → Shrine Detail CTR | **PRIMARY** |
| Result Instance → Detail Engagement Rate | SECONDARY |
| Compass-attributed Favorite Rate | **PRIMARY** |
| Compass-attributed Visit Rate | **PRIMARY** |
| Month-over-Month Compass Return | **PRIMARY** |
| Home Compass Entry Click Count | SECONDARY (denominator for a true CTR is a MEASUREMENT GAP) |
| Compass Activation (`compass_result` ÷ `compass_entry`) | SECONDARY |
| Same-Month Compass Repeat Usage | SECONDARY (Engagement, explicitly not Retention) |
| Compass-attributed Reflection (same-session) | SECONDARY / DIAGNOSTIC |
| Rank breakdown | SECONDARY DIAGNOSTIC |
| Purpose segmentation | SECONDARY DIAGNOSTIC |
| Origin mode segmentation | SECONDARY DIAGNOSTIC |

**Four PRIMARY metrics, unchanged**: Recommendation → Shrine Detail CTR, Compass-attributed Favorite Rate, Compass-attributed Visit Rate, Month-over-Month Compass Return — none of these required semantic revision for `no_common_direction` (each already, structurally, excludes it — see the notes on the CTR/Favorite/Visit/Reflection KPIs above). Compass Runtime Reliability Rate and Compass Recommendation Delivery Rate (the split of the former "Compass Result Success Rate") remain OPERATIONAL rather than PRIMARY, per the task's explicit instruction not to mix reliability and engagement/value KPIs (§21) — they answer "is Compass working" and "does Compass deliver recommendations," not "is Compass valuable." **No-Common-Direction Frequency is not elevated to PRIMARY** — it is a diagnostic breakdown of the Recommendation Delivery Rate's denominator (already computable from the sub-breakdown table above via the `VALID_NO_DIRECTION` bucket), not a new independent metric requiring its own KPI machinery.

---

## 14. Open Items (not resolved by this audit)

1. Exact production deployment timestamps for PR-A/B/C (§9) — merge timestamps are known, rollout timestamps are not verified here.
2. Whether PostHog's project-level timezone is actually configured to `Asia/Tokyo` — must be confirmed before any calendar-month query is trusted (§7).
3. Whether PostHog project-level internal/QA-traffic filtering exists (§11B) — no app-level flag currently distinguishes Mother Ship QA traffic from organic usage.
4. Numeric sample-size thresholds for any of the gates in §11 — explicitly left as PRODUCT/ANALYTICS DECISION REQUIRED, not fabricated here.
5. Whether/how to eventually attach real account identity to PostHog (`identify()`) — a pre-existing, cross-cutting gap this document surfaces (§8, §10) but cannot resolve; doing so is out of this audit's authorization (would be new instrumentation).

---

## 15. Final Report

```
Canonical Compass funnel:
  A. Lifecycle: home_compass_entry_click → compass_entry → compass_result
  B. Recommendation: card_view(compass) → shrine_detail_transition(compass) → shrine_detail_view(compass)
  C. Downstream action (same-page-render only): shrine_detail_view(compass) → favorite_click/visit_done/reflection_prompt_view → reflection_saved
  D. Engagement/Retention: time-bucketed aggregates over compass_result (not a funnel)

Primary KPIs:
  Recommendation → Shrine Detail CTR
  Compass-attributed Favorite Rate
  Compass-attributed Visit Rate
  Month-over-Month Compass Return

Secondary KPIs:
  Result Instance → Detail Engagement Rate, Home Compass Entry Click Count,
  Compass Activation, Same-Month Compass Repeat Usage,
  Compass-attributed Reflection (same-session), Rank/Purpose/Origin-mode diagnostics

Operational KPIs:
  Compass Runtime Reliability Rate, Compass Recommendation Delivery Rate
  (split post-#2499 from the former single "Compass Result Success Rate";
  + SUCCESS/VALID_NO_DIRECTION/EMPTY/ERROR/OTHER state breakdown)

Recommendation CTR definition:
  Numerator = distinct (recommendationInstanceId, shrineId) card_view rows with >=1 matching
  shrine_detail_view(source=compass); Denominator = distinct (recommendationInstanceId, shrineId)
  card_view(source=compass) rows. Join keys: recommendationInstanceId + shrineId (required, exact).
  recommendationRank = validation/diagnostic dimension, not identity.

Favorite attribution definition:
  shrine_detail_view(compass) -> favorite_click(compass, nextFav=true), joined on
  recommendationInstanceId + shrineId, same-page-render window only (SESSION/NAVIGATION
  ATTRIBUTION). Cross-session: MEASUREMENT GAP, not estimated.

Visit attribution definition:
  Same mechanism as Favorite, same-page-render window only. Explicitly named to avoid causal
  claims -- "Visit recorded while Compass context available," not "Compass caused this Visit."
  Expected coverage is lower than Favorite's (physical visits more likely to be cross-session).

Reflection attribution:
  SESSION/NAVIGATION only, and only when prompt/saved occur in the same page render as the
  Compass-attributed Visit. Long-horizon Compass -> Reflection: NOT AVAILABLE / MEASUREMENT GAP,
  not a KPI.

Same-Month Repeat definition:
  Identities (PostHog distinct_id) with >=2 compass_result events (any result_state) within one
  calendar month (Asia/Tokyo). Classified ENGAGEMENT, not Retention. distinct_id only -- no
  identify() exists anywhere in the codebase, so this cannot distinguish authenticated identity
  from anonymous device identity.

Month-over-Month Return definition:
  Identities with a qualifying compass_result in calendar month M and again in M+1 (Asia/Tokyo).
  PRIMARY Retention metric. MUST NOT be judged with fewer than two eligible calendar months --
  report INSUFFICIENT OBSERVATION WINDOW, never a computed 0%, until that gate is satisfied.

Anonymous-user limitation:
  No posthog.identify() call exists anywhere in the codebase (frontend or backend, re-verified).
  Anonymous and logged-in users are equally unlinked in PostHog's own identity graph. Retention
  metrics structurally undercount true person-level return (failure mode: losing the identifier,
  never double-counting).

Cross-session limitation:
  Compass runtime is fully ephemeral (no persistence exists at any stage, PR-A through PR-C).
  ctx/recommendationInstanceId/recommendationRank travel only as URL query parameters on the
  single Compass -> Shrine Detail navigation. No cross-session join is defined or permitted using
  shrineId alone, userId+shrineId alone, timestamp proximity, or post-hoc Favorite/Visit/
  Reflection history correlation. Correlation is not provenance.

Measurement valid from:
  PR-A (#2488), PR-B (#2489), PR-C (#2490) merge timestamps are known; exact production
  deployment timestamps are OPEN / DEPLOYMENT DATE REQUIRED. recommendationInstanceId-based
  joins are valid only from PR-B onward, not from PR-A. result_state="no_common_direction"
  is valid only from 2026-08-20T10:54:25Z (PR #2499, confirmed via Vercel + Render).

Historical classification break (no_common_direction):
  Before PR #2499, a valid empty-intersection outcome and a genuinely invalid/unavailable
  runtime were both emitted as result_state="direction_filter_unavailable" -- they were
  indistinguishable at the code level. direction_filter_unavailable counts before
  2026-08-20T10:54:25Z are therefore NOT directly comparable to counts after it, and no
  individual historical event may be retroactively reclassified. Any Reliability/Delivery
  Rate trend spanning this boundary must state it explicitly.

Minimum observation gates:
  A. Sample Size -- no threshold invented, PRODUCT/ANALYTICS DECISION REQUIRED if one is needed.
  B. Session Diversity -- no app-level QA/internal-traffic flag exists; PostHog-level filtering
     status is an open item.
  C. Time -- Month-over-Month Return requires >=2 eligible calendar months (hard rule).
  D. Identity -- never claim retention from unstable anonymous distinct_id without this caveat.
  E. Attribution -- never claim causal Compass -> Visit/Reflection beyond same-page-render.

Personal Continuity decision gate:
  Deferred, not reopened. Future evidence inputs (non-zero Month-over-Month Return post-Time-Gate,
  sustained CTR/engagement/Favorite-Visit rates across real session diversity, qualitative signal)
  are named without any numeric threshold. Personal Continuity is NOT implemented here and this
  document does not recommend implementing it.

Production code changed:
NO

DB change:
NONE

Migration:
NONE

New analytics events:
NONE

New analytics properties:
NONE

Final Classification:
B — QUERY CONTRACT READY WITH MEASUREMENT GAPS
```

**Why B, not A**: several KPIs (Home discovery CTR, cross-session Favorite/Visit/Reflection, long-horizon Compass → Reflection) are honestly and explicitly unmeasurable with the current architecture — not because the contract is unclear, but because the underlying instrumentation was deliberately scoped (PR-A/B/C) not to solve them yet. Every one of these gaps is precisely named, bounded, and distinguished from what *is* measurable, per the task's own instruction not to downgrade merely because a clearly-specified limitation exists. **Why not C**: no part of this contract is ambiguous or contested — every event, property, join key, and exclusion traces to a concrete, re-verified line of current code. **Why not D**: no architecture conflict exists; every KPI that *can* be computed is fully specified and ready to query as-is, with zero new instrumentation required.
