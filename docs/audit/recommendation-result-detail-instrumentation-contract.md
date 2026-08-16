# Recommendation Result / Detail Instrumentation Contract Audit

> Each finding below is labeled **FACT** (verified by reading the current code/data), **INFERENCE**
> (a conclusion drawn from FACTs, stated explicitly as such), or **PROPOSAL** (a future change idea,
> not implemented, not authorized by this document).

## 1. Audit Purpose

[`recommendation-result-detail-density-change-readiness.md`](recommendation-result-detail-density-change-readiness.md)
(the prior readiness audit) found that Result Hero and Shrine Detail expose overlapping information
under shared `cardId`s (`shrine_meaning`/`action_meaning`/`consultation_summary`), but could not
determine whether the existing Analytics contract can actually measure that duplicate exposure,
because Detail-side `card_view` events lack a join key back to the Result-side exposure.

This document is the follow-up, narrowly scoped audit that answers exactly that question: **can
Result → Detail duplicate exposure be joined today, and if not, what is the minimum additive change
that would make it joinable?** It does not evaluate whether such duplication is a problem worth
fixing in the UI — that remains blocked by the Freeze (§2).

**This is a read-only audit.** No production code was changed. No UI was changed. No analytics
instrumentation was added.

## 2. Governing Policy / Freeze Status

**FACT**: [`docs/product/recommendation-result-observation-policy.md`](../product/recommendation-result-observation-policy.md)
§3 freezes Hero IA and Compact IA until `PRODUCT CHANGE READY` (§10), with an exception only for
critical bugs (crash, data corruption, unintended contract regression — not UI polish or new
features).

**FACT**: The prior readiness audit (2026-08-16) found `PRODUCT CHANGE READY` **not reached** —
state remains `WAIT FOR DATA`, unchanged from the 2026-08-14 baseline.

**INFERENCE**: This document's conclusions describe what is *technically measurable*, not what
should be built. Even a `READY FOR INSTRUMENTATION PR` decision below (§12) does not reopen the
Hero/Compact/Detail UI freeze — see the explicit statement in §13.

## 3. Current Result-Side Event Contract

All Result-side `card_view` calls for the three meaning cards are in
[`apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`](../../apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx),
inside a single `useEffect` keyed on `resultSetId`/`tid` (lines 414–523).

**FACT** — exact payload per card, current code:

| cardId | Lines | `threadId` | `resultSetId` | `shrineId` | `recommendationRank` | `recommendationInstanceId` |
|---|---|---|---|---|---|---|
| `consultation_summary` | 420–438 | ✅ (435) | ✅ (436) | ❌ (not sent) | ❌ (not sent) | ❌ |
| `shrine_meaning` | 441–462 | ✅ (458) | ✅ (459) | ✅ (453, `heroItem.shrineId`) | ✅ (454, `heroItem.rank`) | ❌ |
| `action_meaning` | 464–485 | ✅ (481) | ✅ (482) | ✅ (476) | ✅ (477) | ❌ |

**FACT**: `concierge_result_impression` (lines 396–410, `trackSearchEvent`) and
`shrine_detail_transition` (lines 949–967 for Hero, 1153–1178 for Compact) **do** include
`recommendationInstanceId` — `item.recommendationInstanceId` (405) / `heroItem.recommendationInstanceId
?? null` (963). These two events use `SearchAnalyticsPayload`
([`apps/web/src/lib/analytics/searchEvents.ts:29-80`](../../apps/web/src/lib/analytics/searchEvents.ts)),
which has an explicit `recommendationInstanceId?: string | null` field (line 53) and an open index
signature (`[key: string]: SearchAnalyticsPrimitive`, line 79).

**FACT**: The `shrine_meaning`/`action_meaning`/`consultation_summary` `card_view` calls use
`trackCardEvent()` / `CardAnalyticsPayload`
([`apps/web/src/lib/analytics/cardEvents.ts:29-49`](../../apps/web/src/lib/analytics/cardEvents.ts)),
which has **no `recommendationInstanceId` field at all** and **no index signature** (closed object
type). `heroItem.recommendationInstanceId` is available in the exact same React scope that builds
these three `trackCardEvent()` calls (it is read one function up, at line 405/963), but is not
passed into any of them.

**INFERENCE**: On the Result side, `resultSetId` + `threadId` are already present for all three
meaning cards except `consultation_summary`'s missing `shrineId`/`recommendationRank`.
`recommendationInstanceId` is present in scope but not wired into any of the three calls — this is
a Result-side gap symmetric to the Detail-side gap in §4.

## 4. Current Detail-Side Event Contract

All three meaning cards on Shrine Detail funnel through one helper,
[`apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx`](../../apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx)
`trackShrineDetailCardView()` (lines 130–150):

```ts
function trackShrineDetailCardView(args: {
  cardId: ShrineDetailTrackedCardId;
  accessLevel: "anonymous" | "free" | "premium";
  visibility: CardVisibilityState;
  payloadSource?: "v2" | "fallback";
  shrineId?: number | string;
  historyTheme?: string | null;
}) {
  ...
  trackCardEvent({
    event: ...,
    cardId: args.cardId,
    source: "shrine_detail",
    accessLevel: args.accessLevel,
    visibility: args.visibility,
    shrineId: args.shrineId,
    historyTheme: args.historyTheme,
    payloadSource: args.payloadSource,
  });
}
```

**FACT**: This function's parameter type does not accept `threadId`, `resultSetId`, or
`recommendationInstanceId` at all — not just "not populated," the field literally isn't in the
function signature. Call sites for the three meaning cards are lines 533–542
(`freeMeaningBlockCardIds.forEach`, covers `shrine_meaning`/`action_meaning`/`consultation_summary`
via `collectMeaningBlockCardIds()`, lines 152–166) and 555–564
(`premiumMeaningBlockCardIds.forEach`, same cardIds for the premium variant).

**FACT**: `ShrineDetailArticle` itself **does** receive both values as props: `tid` (line 392, typed
at line 425) and `recommendationInstanceId` (line 395, default `null`, typed at line 428). Both are
already used elsewhere in the same file — `recommendationInstanceId`/`analyticsProvenance` are
forwarded to a child at lines 727–728, and used directly in the `visit_done` analytics call at
lines 756–757. They are simply **not** threaded into `trackShrineDetailCardView()`.

**FACT**: `recommendationInstanceId` is not synthesized on the Detail page — it is read from the
Backend-persisted thread snapshot. In
[`apps/web/src/app/shrines/[id]/page.tsx`](../../apps/web/src/app/shrines/[id]/page.tsx):
- line 314: `getConciergeThreadServer(String(tid))` re-fetches the thread.
- line 321–322: finds the matching recommendation item by `shrineId` within that thread's
  recommendation list.
- line 432–434: `normalizeRecommendationInstanceId(selectedRecommendation?.recommendation_instance_id)`
  — comment at 428–431 states this is "Backend rid persisted on the thread snapshot," never
  synthesized; direct access without `ctx=concierge && tid` yields `null`.
- line 488: passed to `<ShrineDetailArticle recommendationInstanceId={recommendationInstanceId} ...>`.

**FACT**: `resultSetId` is **not** available anywhere on the Detail page — neither as a URL query
param (confirmed in §5) nor recoverable server-side, because (per §5) it is a pure frontend hash
of the specific Result rendering's ordered shrineId list, which the Backend thread snapshot does
not store.

**FACT**: A working precedent for propagating `threadId` + `recommendationInstanceId` on the Detail
page already exists in the same codebase:
[`apps/web/src/components/shrine/ShrineDetailViewTracker.tsx`](../../apps/web/src/components/shrine/ShrineDetailViewTracker.tsx)
(lines 34–40) sends `shrine_detail_view` with `threadId: tid ?? undefined` and
`recommendationInstanceId` (both accepted because this event uses `SearchAnalyticsPayload`, not
`CardAnalyticsPayload`). This is a page-level "arrived at detail" event, not a per-card one.

**FACT (from the prior readiness audit, still accurate)**: `context_reason`/`personal_meaning`/
`saved_record`/`recommendation_meta`/`previous_comparison` — the remaining `ShrineDetailTrackedCardId`
values — have the identical gap (same `trackShrineDetailCardView()` / same direct `trackCardEvent()`
calls at lines 578–591 and 594–607). This audit's join-key findings apply to all of them, not only
the three cardIds shared with Result.

## 5. Available Identifiers at Each Boundary

**FACT**: The Detail page URL only ever carries `ctx` and `tid` from the Result → Detail transition.
[`apps/web/src/features/concierge/detailHref.ts`](../../apps/web/src/features/concierge/detailHref.ts)
(`detailHrefFromRecommendation`, lines 32–50) calls
[`apps/web/src/lib/nav/buildShrineHref.ts`](../../apps/web/src/lib/nav/buildShrineHref.ts)
with only `ctx`/`tid` (plus `place_id`/`toast`, irrelevant here). `buildShrineHref`'s allow-list
(`SHRINE_HREF_ALLOWED_QUERY_KEYS`, line 5) is `["place_id", "toast"]` — `resultSetId` and
`recommendationRank` are not in the allow-list and are never appended to the Detail URL by
`ConciergeSectionsRenderer.tsx`'s `shrine_detail_transition` click handlers (lines 949–969,
1153–1178) either; those handlers build `href` via `withDirectionRouteContext(heroItem.detailHref, ...)`,
which does not add `resultSetId`.

**FACT (design-doc corroboration)**:
[`docs/audit/recommendation-instance-identity-propagation.md`](recommendation-instance-identity-propagation.md)
§6 "Detail Identity" independently documents the same finding for `ShrineDetailViewTracker.tsx`:
"`resultSetId`/rankは無い" (no resultSetId/rank).

Summary table (both sides, as actually emitted for the 3 shared meaning cards today):

| Identifier | Result `card_view` (shrine_meaning/action_meaning) | Result `card_view` (consultation_summary) | Detail `card_view` (all 3) |
|---|---|---|---|
| `threadId` | ✅ | ✅ | ❌ (available in component scope, not sent) |
| `resultSetId` | ✅ | ✅ | ❌ (not available anywhere on Detail, §5) |
| `shrineId` | ✅ | ❌ | ✅ |
| `recommendationRank` | ✅ | ❌ | ❌ (not in `trackShrineDetailCardView` signature) |
| `recommendationInstanceId` | ❌ (in scope, not sent, §3) | ❌ | ❌ (in scope, not sent, §4) |

## 6. Missing Join Keys

**FACT**: No property exists today on any `card_view` event, on either side, that is both (a)
present in every relevant call and (b) sufficient by itself to identify "this specific recommended
shrine, from this specific Result generation."

**FACT**: `resultSetId` cannot be added to the Detail side without either (a) adding it to the
Detail URL allow-list and to every `shrine_detail_transition`/click-through construction site
(a Result-side + navigation change), or (b) some other propagation mechanism (e.g. `sessionStorage`)
not currently present. It cannot be *recovered* server-side from `tid` alone, unlike
`recommendationInstanceId` (§4).

**FACT**: `recommendationInstanceId` is per-**generation** (per `/api/concierge/chat/` POST), not
per-shrine. Per
[`docs/audit/recommendation-instance-identity-propagation.md`](recommendation-instance-identity-propagation.md)
§3.2 and §12 (Option C, "the recommended minimal contract" that shipped as PR #2429–#2432):
`rid = uuid.uuid4().hex[:8]` is generated once per chat request, then copied onto **every**
recommendation item in that response (`rec["recommendation_instance_id"] = rid`). All shrines
returned by one Result render therefore share the **same** `recommendationInstanceId`.

**INFERENCE**: `recommendationInstanceId` alone cannot disambiguate *which* shrine within a
generation — it only disambiguates *which generation* (solves "did the thread get re-queried
between Result and Detail," not "which of the 3 recommended shrines is this"). `shrineId` must
always accompany it.

## 7. Minimum Stable Join Contract

**PROPOSAL** (not implemented): the minimum key that would let a query join "this cardId was seen
on Result" to "this same cardId was seen again on Detail, for the same recommendation" is the pair:

```
(recommendationInstanceId, shrineId)
```

with `cardId` as the dimension being compared (not part of the join key itself — `shrine_meaning`
on Result joins to `shrine_meaning` on Detail, `action_meaning` to `action_meaning`, etc., since §4
confirmed both sides already use the identical cardId strings for these three cards).

**Rationale for this specific pair over the alternatives, stated as INFERENCE from §3–§6 above**:

- `threadId` alone is insufficient: a single thread can be re-queried (new filter, new message),
  producing a new generation with a new `recommendationInstanceId` but the same `threadId`. Using
  `threadId` alone would silently merge distinct generations' exposures.
- `resultSetId` alone (or `resultSetId + shrineId`) would work in principle but is **not
  recoverable on Detail today** without a new propagation path (§6) — it is a pure frontend value,
  never persisted server-side, so `tid`-based re-fetch (the mechanism that already recovers
  `recommendationInstanceId`, §4) cannot reconstruct it.
- `recommendationInstanceId` alone is insufficient (§6 — shared across all shrines in one
  generation).
- `recommendationInstanceId + shrineId` is sufficient to identify one specific recommended item
  from one specific generation, and — critically — **both values are already available on the
  Detail page without any new propagation mechanism**: `shrineId` is the page's own path param,
  and `recommendationInstanceId` is already re-derived server-side from `tid` in `page.tsx` (§4)
  and already flows as a prop into the exact component (`ShrineDetailArticle`) that fires the
  `card_view` calls in question.

**PROPOSAL**: `recommendationRank` is not required for correctness of the join itself (`shrineId`
is already unique per generation), but including it would keep the payload consistent with how
`shrine_meaning`/`action_meaning` are already sent on the Result side (§3) and would let a future
query segment by Hero-vs-Compact position without an extra join — an ergonomic nice-to-have, not a
join-key necessity.

## 8. Duplicate Exposure KPI Feasibility

Evaluating the candidate metric from the task:

> Numerator: transitions where the same `cardId` was viewed in both surfaces.
> Denominator: users/result sets that transitioned from Result to Detail.

**FACT**: The denominator is already fully computable today — `shrine_detail_transition` already
carries `resultSetId`, `shrineId`, `recommendationRank`, and `recommendationInstanceId` (§3), and is
the established Primary/Secondary KPI event per
[`recommendation-result-observation-policy.md`](../product/recommendation-result-observation-policy.md) §4/§5.

**FACT**: The numerator is **not** computable today. It requires joining a Result-side `card_view`
(`cardId=shrine_meaning`, `source=concierge_result`) to a Detail-side `card_view`
(`cardId=shrine_meaning`, `source=shrine_detail`) for the same recommendation exposure, and neither
side currently emits a key that both (a) identifies the specific recommendation and (b) is present
on both sides (§6).

**INFERENCE**: If the §7 join contract (`recommendationInstanceId` + `shrineId`, added to both
sides' `card_view` calls for the three meaning cards) were implemented, the numerator would become:

```
count(DISTINCT (recommendationInstanceId, shrineId, cardId))
  WHERE card_view exists with source='concierge_result'
    AND card_view exists with source='shrine_detail'
    for the same (recommendationInstanceId, shrineId, cardId)
```

segmented by `cardId ∈ {shrine_meaning, action_meaning, consultation_summary}`, divided by the
`shrine_detail_transition` count for the matching `(recommendationInstanceId, shrineId)` pairs.

**Ambiguity to flag (INFERENCE, not resolved by this audit)**: this KPI does not by itself prove
"the user re-read information they'd already seen" — `card_view` fires on render/visibility, not on
active reading (no dwell-time or scroll-depth signal exists for these cards on either surface, per
this repo's `CardAnalyticsEvent` type, §3/§4). A high "duplicate exposure rate" would show the same
content rendered twice, not that the user was bothered by it or skipped it. Any future KPI decision
should treat this as an exposure-overlap metric, not an engagement/annoyance metric, unless
additional instrumentation (dwell/scroll) is separately proposed and evaluated — out of scope here.

## 9. Risks / Ambiguity

- **FACT**: `rid` (`recommendationInstanceId`'s source) is documented as **not cryptographically
  unique** — 8 hex chars / 32 bits
  ([`recommendation-instance-identity-propagation.md`](recommendation-instance-identity-propagation.md)
  §3.2). At this app's current traffic volume this is stated there as sufficient for join purposes,
  but any future instrumentation PR should carry that caveat forward rather than treat
  `recommendationInstanceId` as a guaranteed-unique key at unbounded scale.
- **FACT**: `recommendationInstanceId` is `null` for direct Detail access without
  `ctx=concierge && tid` (§4, page.tsx comment lines 428–431) and for pre-PR #2429 threads. Any
  future join query must exclude nulls rather than treat them as a valid "no duplicate" join match.
- **INFERENCE**: Mobile is out of scope for this specific gap — `ShrineDetailArticle.tsx` and
  `ConciergeSectionsRenderer.tsx` are Web-only. This audit makes no claim about Mobile's equivalent
  screens; a separate audit would be needed there (the prior readiness audit's §12 Measurement Gaps,
  inherited from the 2026-08-14 baseline, already flags Mobile as a distinct, unresolved gap).
- **INFERENCE**: Extending `CardAnalyticsPayload` (cardEvents.ts) with `recommendationInstanceId` is
  additive (new optional field) and does not change any existing field's meaning or any existing
  caller's behavior — no existing dashboard/query reading `card_view` would break, since PostHog
  events are schemaless per-property and unset properties on older events simply remain absent. This
  is stated as INFERENCE (not verified against a live dashboard) because this audit did not enumerate
  every existing PostHog saved query/dashboard that reads `card_view`.

## 10. Candidate Future Instrumentation Change (PROPOSAL — not implemented)

Scoped narrowly to close exactly the gap in §6/§7, nothing else:

1. Add `recommendationInstanceId?: string | null` to `CardAnalyticsPayload`
   ([`cardEvents.ts:29-49`](../../apps/web/src/lib/analytics/cardEvents.ts)) — additive field.
2. Result side
   ([`ConciergeSectionsRenderer.tsx`](../../apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx)):
   pass `recommendationInstanceId: heroItem.recommendationInstanceId ?? null` into the three
   `trackCardEvent()` calls at lines 426–437, 447–460, 470–483 (value already in scope, same pattern
   already used at line 963 for `shrine_detail_transition`). Also add `shrineId`/`recommendationRank`
   to the `consultation_summary` call (420–438) for consistency with the other two.
3. Detail side
   ([`ShrineDetailArticle.tsx`](../../apps/web/src/components/shrine/detail/ShrineDetailArticle.tsx)):
   add `recommendationInstanceId?: string | null` (and optionally `threadId`) to
   `trackShrineDetailCardView()`'s parameter type (130–137) and its `trackCardEvent()` call
   (140–149), then pass `recommendationInstanceId` (already destructured at line 395) through at each
   of the call sites (523–531, 533–542, 544–553, 555–564, and optionally the remaining cardIds at
   566–607 for consistency).
4. No Backend change, no Ranking change, no Recommendation Authority change, no Reason V4 change, no
   Action Suggestion change, no new PostHog writer beyond new properties on existing events, no
   migration.

This candidate is deliberately **not implemented** in this PR. It would need its own scoped PR, its
own review, and explicit Mother Ship approval — this audit only establishes that it is technically
minimal and additive.

## 11. Tests That Would Be Required (if the §10 proposal is approved and implemented)

**FACT** — existing tests that would need extension (not new files, extending assertions in place):

- [`apps/web/src/components/shrine/detail/__tests__/ShrineDetailArticle.test.tsx`](../../apps/web/src/components/shrine/detail/__tests__/ShrineDetailArticle.test.tsx),
  the `"推薦理由と前回比較の view イベントを送信する"` test (lines 347–421) already asserts
  `trackCardEvent` payload shape via `expect.objectContaining({...})` for `recommendation_meta`/
  `previous_comparison` (402–420) — this is the direct precedent to extend for `shrine_meaning`/
  `action_meaning`/`consultation_summary`/`context_reason`/`personal_meaning`, asserting
  `recommendationInstanceId` is present once a `recommendationInstanceId` prop is passed to the
  component under test.
- [`apps/web/src/features/concierge/components/__tests__/ConciergeSectionsRenderer.recommendationInstanceId.test.tsx`](../../apps/web/src/features/concierge/components/__tests__/ConciergeSectionsRenderer.recommendationInstanceId.test.tsx)
  already tests `concierge_result_impression`/`shrine_detail_transition` `recommendationInstanceId`
  propagation (lines 52–94+) — the direct precedent to extend to also assert it on the
  `shrine_meaning`/`action_meaning`/`consultation_summary` `card_view` calls.
- `apps/web/src/lib/analytics/__tests__/cardEvents.test.ts` (if it exists — not read in this audit)
  or a new unit test for the `CardAnalyticsPayload` type/`trackCardEvent` serialization, to cover the
  new optional field passing through `serializeCardAnalyticsPayload()` (cardEvents.ts lines 53–55)
  correctly (undefined values are filtered out there already).

**PROPOSAL**: a new test asserting the join is possible end-to-end (e.g. rendering
`ConciergeSectionsRenderer` then `ShrineDetailArticle` with the same fixture `recommendationInstanceId`
+ `shrineId` and asserting both emitted `card_view` payloads match on that pair) would be valuable
but does not exist today and is not required to ship §10 — it would be a regression-guard for the
join contract itself, addable in the same future PR.

## 12. Explicit Decision

# READY FOR INSTRUMENTATION PR

**Basis**: §3–§7 establish, with file:line evidence, that:

- the exact gap is known precisely (§6),
- the minimum join contract is fully specified and requires no new data source — both values
  (`recommendationInstanceId`, `shrineId`) are already computed and already in scope at every call
  site that would need them (§4, §7),
- the change is additive-only at the type level (§9),
- a working precedent for the same propagation pattern already ships in this codebase
  (`ShrineDetailViewTracker.tsx`, §4),
- the required test extensions are identified against existing, already-passing tests (§11).

This is **not** `NOT READY` (the technical unknowns are resolved) and **not** `BLOCKED` (no
Backend/Ranking/migration dependency exists).

## 13. This Decision Does Not Authorize a Product/UI Change

**§12's `READY FOR INSTRUMENTATION PR` verdict applies only to the Analytics contract addition
described in §10.** It does not:

- authorize starting the Result/Detail Information Responsibility UI redesign,
- change the `WAIT FOR DATA` state recorded in
  [`recommendation-result-detail-density-change-readiness.md`](recommendation-result-detail-density-change-readiness.md),
- reopen the Hero IA / Compact IA freeze in
  [`recommendation-result-observation-policy.md`](../product/recommendation-result-observation-policy.md) §3,
- declare `PRODUCT CHANGE READY` under that policy's §10 criteria (which require organic traffic
  and observed behavioral difference, neither of which this audit touches).

Any instrumentation PR scoped from §10 would itself need Mother Ship approval as a standalone,
narrowly-scoped Analytics-contract-only change — not as a step toward the frozen UI work.

---

Production code changes = 0
UI changes = 0
Information architecture changes = 0
Ranking changes = 0
Recommendation Authority changes = 0
Analytics instrumentation added = 0
Analytics schema changes = 0
Migrations = 0
