> **Status: Active**
>
> This is an **Analytics attribution contract audit**, not an
> implementation. It does not modify Backend production code, Frontend
> production code, Runtime, Recommendation Ranking, Concierge, or Analytics
> instrumentation. It traces, precisely, whether a `route_open` event can
> be attributed back to a Compass-originated recommendation using
> properties that already exist in the current codebase. **This audit
> found a more precise result than
> [`compass-result-experience.md`](compass-result-experience.md) Section
> 20-1 assumed**: that prior audit confirmed `GoogleMapRouteLink`'s own
> prop wiring accepts `ctx`/`recommendationInstanceId`, but did not verify
> what *values* actually reach it from the page level for a
> Compass-originated visit specifically. This audit traces that exact
> value flow and finds it is broken — not the schema, the propagation.
> That correction is recorded here explicitly rather than silently
> superseding the earlier document.

# Compass Route Attribution Contract Audit

## 1. Purpose

Can a `route_open` event be reliably attributed back to a
Compass-originated recommendation, using only existing events and
properties? This is PR4 from the canonical Compass Result Experience audit
([docs/audit/compass-result-experience.md](compass-result-experience.md)
Section 26-4).

## 2. Scope

In scope: the full journey `compass_result` → `card_view` /
`shrine_detail_transition` → `shrine_detail_view` → `route_open`, and every
property that would let a query join these events back to a specific
Compass recommendation. Out of scope: any instrumentation change, any new
event, any production code fix, Visit Funnel rate calculation, Premium
work.

## 3. Canonical Sources

Read: [`compass-result-experience.md`](compass-result-experience.md),
[`compass-analytics-contract.md`](../analytics/compass-analytics-contract.md),
[`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md).
Code re-traced directly against current `develop`:
`CompassClient.tsx`, `CompassRecommendationsSection.tsx`,
`buildShrineHref.ts`, `app/shrines/[id]/page.tsx`, `ShrineDetailViewTracker.tsx`,
`ShrineDetailShell.tsx`, `ShrineDetailArticle.tsx`, `ShrineSaveButton.tsx`,
`GoogleMapRouteLink.tsx`.

---

## 4. Current Journey

```
CompassClient.tsx (compass_result)
  -> CompassRecommendationsSection.tsx (card_view, shrine_detail_transition)
  -> buildShrineHref() -> /shrines/:id?ctx=compass&recommendation_instance_id=R&recommendation_rank=N
  -> app/shrines/[id]/page.tsx (parses ctx/recommendation_instance_id/recommendation_rank)
       |
       +-> ShrineDetailViewTracker  (gets FULL ctx + correct recommendationInstanceId) -> shrine_detail_view
       +-> ShrineDetailArticle       (gets FULL ctx override + correct recommendationInstanceId) -> visit_done, reflection_*
       +-> ShrineSaveButton          (gets FULL ctx override + correct recommendationInstanceId) -> favorite_click, shrine_decision
       +-> ShrineDetailShell         (gets NULLED ctx + WRONG recommendationInstanceId)
             -> GoogleMapRouteLink -> route_open  (source hardcoded, ctx null, recommendationInstanceId null)
```

---

## 5. Compass Result Event

```
Event:               compass_result
File:                CompassClient.tsx:87-102
Relevant properties: result_state, calculationMethod, purpose, origin_mode,
                     has_birthdate, recommendation_count, recommendationInstanceId
                     (= body.recommendation_instance_id from the API response)
```

`recommendationInstanceId` here is the same, single identifier that will
be threaded into `card_view`/`shrine_detail_transition` for every
recommendation card rendered from this one result.

---

## 6. Detail Transition

```
Impression event: card_view          CompassRecommendationsSection.tsx:36-44
                   source="compass", shrineId, recommendationRank, recommendationInstanceId
Click event:       shrine_detail_transition   CompassRecommendationsSection.tsx:71-82
                   source="compass", shrineId, recommendationRank, recommendationInstanceId,
                   position="compact" -- fires on click, before navigation
Destination:       buildShrineHref(shrineId, {ctx:"compass", recommendationInstanceId, recommendationRank})
                   -> /shrines/:id?ctx=compass&recommendation_instance_id=R&recommendation_rank=N
                   (buildShrineHref.ts:59-79)
```

**Compass attribution preserved into the URL: YES.**

---

## 7. Detail Context

`app/shrines/[id]/page.tsx` parses the URL (lines 184-189):

```ts
const ctx = normalizeCtx(sp?.ctx ?? null);                                    // "compass"
const compassRecommendationInstanceId =
  ctx === "compass" ? normalizeRecommendationInstanceId(sp.recommendation_instance_id) : null;
const parsedCompassRank = ctx === "compass" ? Number(sp.recommendation_rank) : NaN;
...
const downstreamCtx = ctx === "compass" ? null : ctx;                          // line 194 -- NULLED for compass
...
const detailRecommendationInstanceId = compassRecommendationInstanceId ?? conciergeRecommendationInstanceId; // line 457 -- correct fallback
```

**This is the crux of the audit.** `ctx` is deliberately nulled into
`downstreamCtx` before being passed to most downstream components — but
**not uniformly**. Tracing exactly which component receives which value
(page.tsx:477-536):

| Component | `ctx` prop received | `recommendationInstanceId` prop received | Compass-aware? |
|---|---|---|---|
| `ShrineDetailViewTracker` (:482) | `ctx` (full, un-nulled) | `detailRecommendationInstanceId` (:485, correct fallback) | **YES** |
| `ShrineDetailArticle` (:513, explicit override) | `ctx` (full, un-nulled — deliberately overrides `model.ctx=downstreamCtx` per the code's own PR-C comment) | `detailRecommendationInstanceId` (:518, correct) | **YES** |
| `ShrineSaveButton` (:524, inside `saveActionNode`) | `ctx` (full, un-nulled) | `detailRecommendationInstanceId` (:529, correct) | **YES** |
| `ShrineDetailShell` (:494) | `downstreamCtx` (:494 — **null** when the original ctx was `"compass"`) | `conciergeRecommendationInstanceId` (:498 — **not** `detailRecommendationInstanceId`, so also **null** for a Compass visit with no Concierge thread) | **NO** |

`ShrineDetailShell` is the component that renders `GoogleMapRouteLink`
(Section 8) — so the one path that reaches `route_open` is exactly the one
path that does **not** receive Compass-aware `ctx`/`recommendationInstanceId`.
`shrineId` does still reach it (passed independently via the URL path
segment and the `shrineId` prop, unaffected by the `ctx`/
`recommendationInstanceId` nulling).

---

## 8. `route_open` Event

```
File:      GoogleMapRouteLink.tsx:47-105
Event:     route_open
source:    hardcoded "shrine_detail" (line 67) -- never computed from ctx,
           unlike visit_done (Section 9)
ctx:       accepted as a prop (line 29), forwarded into recommendationInstanceId-
           adjacent tracking calls, but not into the route_open payload's
           own `source`/`ctx` fields directly -- passed through only as
           part of the `ctx` argument to trackSearchEvent's `route_open`
           call (line 71, `ctx,`) -- so ctx IS present as a raw property on
           route_open, it is simply *null* for a Compass-originated visit
           (Section 7)
recommendationInstanceId: accepted as a prop (line 35), included on the
           route_open payload (line 72) -- again present as a field, but
           *null* for a Compass-originated visit (Section 7)
shrineId:  present, and does survive (Section 7)
```

**`route_open`'s schema already supports the fields needed for
attribution.** The break is not a missing property — it is that the value
supplied for `ctx` and `recommendationInstanceId` at this specific
component is wrong for a Compass-originated visit.

---

## 9. `source` Semantics

```
Meaning (confirmed from code): source describes the *page/action context
immediately triggering the event*, not the journey's original entry point.
```

This is **not** a uniform hardcoded pattern across all events, however —
`visit_done` (`ShrineDetailArticle.tsx:763`) already computes it
dynamically: `source: ctx === "compass" ? "compass" : "shrine_detail"`.
`route_open` is the **one exception** that never computes this — it always
emits `"shrine_detail"` regardless of `ctx`. Even if `route_open` adopted
the same dynamic pattern, it would still fail today, because the `ctx`
value reaching `GoogleMapRouteLink` for a Compass visit is already `null`
(Section 7) — the propagation break is upstream of `source`'s own
computation.

---

## 10. `ctx` Semantics

```
Created:          app/shrines/[id]/page.tsx:185, parsed from the URL query
                   built by buildShrineHref (ctx=compass)
Possible values:   "compass" | "concierge" | other legacy values | null
Set by Compass:    YES (CompassRecommendationsSection.tsx via buildShrineHref)
Survives to Detail mount: YES, as the page-level `ctx` const
Survives to shrine_detail_view: YES (ShrineDetailViewTracker gets full ctx)
Survives to visit_done/reflection/favorite: YES (explicit overrides, Section 7 table)
Survives to route_open: NO -- nulled via downstreamCtx before reaching
                   ShrineDetailShell/GoogleMapRouteLink
Canonical or incidental: canonical for every leg except the Route leg
```

---

## 11. Recommendation Instance Semantics

```
Creation point:     backend/temples/api_views_compass.py -- uuid.uuid4().hex[:8]
                     per request, stateless, no DB write (already documented
                     in compass-posthog-query-contract.md line 55)
Relation to compass_result: one identifier per result set, embedded in the
                     response body and every recommendation item
Each result set gets one ID: YES
Shrine Detail receives it:   YES, via detailRecommendationInstanceId
                     (compassRecommendationInstanceId, correctly prioritized
                     over any stale Concierge thread value)
route_open receives it:      NO -- ShrineDetailShell receives only
                     conciergeRecommendationInstanceId (page.tsx:498), which
                     is null whenever there is no Concierge thread
                     (selectedRecommendation), true for every Compass visit
Can join funnel events without PII: YES in principle -- it is a stateless,
                     random hex string with no personal data
```

**An identifier reaching only some events in the chain is not sufficient**
for the full journey — this is exactly the gap in this specific leg.

---

## 12. Shrine ID Semantics

`shrineId` reaches every event in the chain (`card_view` through
`route_open`) because it travels via the URL path segment
(`/shrines/:id`) and an independent `shrineId` prop, not via the
`ctx`/`recommendationInstanceId` propagation path that breaks. However,
per this task's own instruction and this audit's confirmation: **`shrineId`
alone cannot prove journey origin** — the same shrine could be reached via
Concierge, direct navigation, or search, and `shrineId` alone does not
distinguish these. It is a necessary join key, never a sufficient
attribution key by itself.

---

## 13. Event Inventory

| Event | Meaning | Compass-origin property | Shrine ID | Recommendation instance | Context/source | Sufficient for funnel? |
|---|---|---|---|---|---|---|
| `compass_result` | Compass request resolved | `calculationMethod`, `result_state` | N/A | generates R | N/A | Origin point |
| `card_view` | Recommendation card shown | `source="compass"` | YES | YES (R) | `source="compass"` | YES |
| `shrine_detail_transition` | Card tapped | `source="compass"` | YES | YES (R) | `source="compass"` | YES |
| `shrine_detail_view` | Detail page mounted | `source="compass"` when `ctx=compass` | YES | YES (R) | correct | YES |
| `visit_done` | Visit marked | `source` dynamically `"compass"` when `ctx=compass` | YES | YES (R) | correct | YES |
| `favorite_click` / `shrine_decision` | Save toggled | `source="compass"` when `ctx=compass` | YES | YES (R) | correct | YES |
| `route_open` | Route link clicked | **NO** — hardcoded `"shrine_detail"`, `ctx`/`recommendationInstanceId` both null for Compass visits | YES | **NO** (null) | **broken for Compass** | **NO** |

No `card_click`/`detail_transition`/`route_click` events exist beyond
those already named above — no event name was invented or assumed.

---

## 14. Compass → Detail Attribution

```
Classification: MEASURABLE
```

Join rule: `card_view{source="compass"}` → `shrine_detail_transition{source="compass"}`
→ `shrine_detail_view{source="compass"}`, matched on `(recommendationInstanceId, shrineId)`.
This is exactly what `compass-posthog-query-contract.md` Section 3
("Canonical Compass Funnel") already documents, and this audit confirms it
against current code without finding any discrepancy.

---

## 15. Detail → Route Attribution

```
Classification: NOT MEASURABLE (currently)
```

No join rule currently exists. `route_open`'s `ctx` and
`recommendationInstanceId` are both `null` for a Compass-originated visit
(Section 7-8). Only `shrineId` survives, and per Section 12, `shrineId`
alone cannot establish Compass origin (a Concierge-originated visit to the
same shrine would look identical on this one property).

---

## 16. Full Compass → Route Attribution

```
D — NOT RELIABLY MEASURABLE
```

Reasoning: not **A** (fully measurable) or **B** (measurable via a
documented multi-event join) — the second leg has no working join key at
all today. Not **C** (one existing event property must be added) — this
would imply the `route_open` *schema* lacks a field; it does not (Section
8: `ctx` and `recommendationInstanceId` are already accepted parameters
and already appear in the event payload shape). The actual defect is that
`app/shrines/[id]/page.tsx` passes the wrong (nulled) *values* into an
already-adequate schema for one specific component
(`ShrineDetailShell`/`GoogleMapRouteLink`) while correctly passing the
right values into three sibling components (`ShrineDetailViewTracker`,
`ShrineDetailArticle`, `ShrineSaveButton`) that all sit at the exact same
point in the component tree. This is a **frontend propagation break**, not
an instrumentation/schema gap — hence **D**.

---

## 17. Attribution Candidate Comparison

```
Candidate A (route_open.source = "compass"):
  Currently INVALID -- hardcoded "shrine_detail" always, and even if made
  dynamic (mirroring visit_done's pattern), the ctx it would read from is
  already null at this component (Section 7).

Candidate B (route_open.ctx = "compass"):
  Currently INVALID -- ctx is null at this event for Compass visits.

Candidate C (recommendationInstanceId join):
  Currently INVALID -- also null at this event for Compass visits.

Candidate D (ctx + recommendationInstanceId + shrineId combination):
  Currently INVALID (both of the first two components are null); this is
  the TARGET state once the propagation break (Section 16) is fixed --
  mirrors the already-working Compass -> Detail join exactly.

Candidate E (event-sequence/session proximity):
  NOT recommended. A deterministic property path already exists in the
  codebase's own pattern (three sibling components already do this
  correctly) -- the fix is restoring that pattern, not inventing a fuzzy
  timestamp-based join.
```

**Canonical Attribution Key (target, once fixed): `ctx="compass"` AND
`recommendationInstanceId`, with `shrineId` as an additional join/scoping
key** — identical in shape to the already-working Compass → Detail join
(Section 14).

---

## 18. Canonical Query Contract

**Not executable today** (Section 16: D). Documented here as the target
query, to be enabled only if/when the propagation break is fixed (out of
this audit's scope to implement):

```
Step 1: Identify Compass recommendation events.
  card_view{source="compass"} -> (recommendationInstanceId, shrineId) pairs

Step 2: Identify the corresponding detail events.
  shrine_detail_view{source="compass"}
    WHERE (recommendationInstanceId, shrineId) matches Step 1

Step 3 (TARGET, not currently valid): Identify route_open events
  associated with those same recommendation journeys.
  route_open{ctx="compass"}
    WHERE (recommendationInstanceId, shrineId) matches Step 1/2
```

---

## 19. HogQL / Query Recipe

Not run (this task is contract/readiness only, Section 21 of the task).
Prepared as a recipe only, for future use **once** Section 16's propagation
break is fixed — currently, running this against production would return
zero or unreliable rows for the `route_open` leg specifically, because
`ctx`/`recommendationInstanceId` are absent on that event for Compass
journeys:

```sql
-- Step 1+2 (already valid today):
SELECT count(DISTINCT (properties.recommendationInstanceId, properties.shrineId)) AS detail_reached
FROM events
WHERE event = 'shrine_detail_view'
  AND properties.source = 'compass'

-- Step 3 (NOT valid today -- included only as the target shape):
SELECT count(DISTINCT (properties.recommendationInstanceId, properties.shrineId)) AS route_reached
FROM events
WHERE event = 'route_open'
  AND properties.ctx = 'compass'
```

No `distinct_id`, coordinates, birthdate, or free text in either query —
aggregate counts of non-PII product properties only.

---

## 20. Privacy Boundary

```
PII required: NO
```

Every property referenced in this audit (`recommendationInstanceId`,
`ctx`, `source`, `shrineId`, event names) is non-PII, stateless, product
context. No `distinct_id`, person ID, email, birthdate, coordinates, raw
origin, free text, IP, or credentials were queried, retrieved, or are
required by the proposed query contract.

---

## 21. Current Docs Assessment

```
compass-posthog-query-contract.md: MISSING (route_open is not mentioned
  anywhere in this document -- confirmed via direct search, zero matches)
compass-analytics-contract.md:     MISSING (same -- zero matches)
```

Not **MISLEADING** — neither document makes an incorrect claim about
`route_open`'s Compass attribution, because neither document discusses
`route_open` at all. It is simply absent from the Compass-scoped funnel
documentation, which is accurate given `route_open` is not currently
attributable to Compass (Section 16). No doc correction is made in this PR
beyond noting this absence — adding a row prematurely (before the
propagation break is fixed) would risk implying a working join that does
not exist.

---

## 22. Instrumentation Gap

```
Required (new event property / schema change): NO
```

`route_open` already accepts and already carries `ctx` and
`recommendationInstanceId` as properties (Section 8) — the schema is
already sufficient. What *is* required, but is explicitly **not**
instrumentation and **not implemented by this audit**, is a narrow
frontend propagation correction:

```
Minimal identified gap (frontend, NOT analytics instrumentation):
  app/shrines/[id]/page.tsx passes `ctx={downstreamCtx}` and
  `recommendationInstanceId={conciergeRecommendationInstanceId}` to
  <ShrineDetailShell> (lines 494, 498).
  Three sibling components at the same point in the tree
  (ShrineDetailViewTracker, ShrineDetailArticle, ShrineSaveButton)
  already receive `ctx={ctx}` (full) and
  `recommendationInstanceId={detailRecommendationInstanceId}` (correct
  fallback) instead. Mirroring that same, already-established pattern for
  <ShrineDetailShell> would close this gap -- no new prop, no new event,
  no new instrumentation call; only two prop *values* passed at one
  existing call site would change.
```

This is recorded as a candidate future fix, not performed here.

---

## 23. Analytics Contract Decision

```
D — EXISTING PROPAGATION IS BROKEN; FRONTEND FIX REQUIRED
```

Not implemented in this task (per this task's own explicit instruction not
to implement C/D/E).

---

## 24. Visit Funnel Readiness

```
READY WITH QUERY CAVEAT
```

Reasoning: the **Visit** action itself (`visit_done`, fired from
`ShrineDetailArticle`) already correctly receives Compass attribution —
confirmed at `ShrineDetailArticle.tsx:763`,
`source: ctx === "compass" ? "compass" : "shrine_detail"`, with the correct
`recommendationInstanceId` (Section 7 table). A future "Compass → Visit
Funnel" task is **not blocked** by this audit's finding. The caveat: (1)
the existing, already-documented same-page-render-only attribution rule
for Favorite/Visit/Reflection still applies (`compass-posthog-query-contract.md`),
and (2) **Route specifically** (a different action from Visit) remains
not attributable to Compass and must be excluded from, or explicitly
flagged within, any such funnel work until Section 22's propagation gap is
addressed separately.

---

## 25. Non-goals

This audit does not:

- Modify `app/shrines/[id]/page.tsx`, `GoogleMapRouteLink.tsx`,
  `ShrineDetailShell.tsx`, or any other production file.
- Add any new Analytics event or property.
- Calculate any production funnel rate.
- Begin Visit Funnel measurement, Premium work, or Concierge work.
- Edit [`compass-result-experience.md`](compass-result-experience.md) —
  that document's Section 20-1 is now superseded in accuracy by this
  audit's Section 7-8 finding, but this audit corrects the record here
  rather than silently editing a prior, separately-merged audit's text.

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

Every property/event/file citation in Sections 5-13 was re-read directly
from current `develop` in this session — not assumed from prior audits.
No timestamp-proximity join was proposed anywhere in this document, since
a deterministic property path already exists structurally (three sibling
components already implement it correctly) — the gap is a propagation
value bug, not an absence of a deterministic mechanism. No PII was
required or referenced. Visit Funnel readiness classification is explicit
(Section 24). No production code was changed.
