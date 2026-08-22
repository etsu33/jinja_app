> **Status: Active**
>
> This is an **audit-only** document. It does not modify Backend production
> code, Frontend production code, UI copy, PostHog instrumentation, the
> Runtime Contract, the Product Contract, Recommendation Ranking, Concierge
> behavior, or `kyusei.py`. It traces whether the COMMON DIRECTION / MONTHLY
> FALLBACK DIRECTION distinction established by
> [`compass-product-direction-decision.md`](../product/compass-product-direction-decision.md)
> (#2508), formalized in
> [`compass-product-contract.md`](../product/compass-product-contract.md) Section 2.2 and
> [`compass-mvp-runtime-contract.md`](../product/compass-mvp-runtime-contract.md) Section 5-1
> (#2509), and implemented in `backend/temples/services/compass_runtime.py`
> (#2510), actually reaches the user and PostHog. Findings only; no
> implementation.

# Compass Monthly Fallback — UI / Analytics Boundary Audit

## 1. Purpose

#2510 made `build_compass_direction_runtime()` return a Monthly Fallback
result (`calculationMethod: "monthly_kyusei_v1"`) instead of always falling
through to `NoCommonDirectionResult` when the annual∩monthly intersection is
empty. This audit answers five questions, end to end:

1. Does `calculationMethod` actually reach the Frontend from Backend?
2. Can the Frontend technically distinguish COMMON from MONTHLY_FALLBACK?
3. Does the current UI distinguish them *semantically* (not just technically)?
4. Can PostHog distinguish them today?
5. What (if anything) needs to change in a future UI PR and a future
   Analytics PR?

No code is changed by this document. Where a gap is found, it is recorded
as a **Required Follow-up** (Section 17/18), not fixed here.

---

## 2. Canonical Product Semantics (fixed for this audit)

Per [#2508](../product/compass-product-direction-decision.md) and
[#2509](../product/compass-product-contract.md) Section 2.2 /
[Runtime Contract Section 5-1](../product/compass-mvp-runtime-contract.md):

```
A. COMMON DIRECTION
   annual ∩ monthly non-empty
   calculationMethod = "annual_monthly_kyusei_v1"
   referenceDirections = annual ∩ monthly

B. MONTHLY FALLBACK DIRECTION
   annual ∩ monthly empty, monthly-only non-empty
   calculationMethod = "monthly_kyusei_v1"
   referenceDirections = monthly-only directions
   NOT "annual and monthly agreed" -- annual contributed nothing to this result

C. NO_COMMON_DIRECTION (narrowed, #2508)
   annual ∩ monthly empty AND monthly-only empty
   Theoretical residual: 3.1% (was 46.5% under the pre-#2508 Option B semantics)
```

These three are never collapsed into each other in this document.

---

## 3. Current Production UI Evidence

User-observed, current production Compass (as reported for this audit):

- A direction is shown.
- Shrine candidates are shown.
- Below the direction card, a note reading to the effect of *"年盤と月盤に
  よる参考情報です。日盤は使用していません。（参考情報です）"* ("This is
  reference information based on the annual and monthly charts. The day
  chart is not used.") is shown.

This observation is recorded as **evidence of copy content**, not as
evidence of which classification (COMMON vs. MONTHLY_FALLBACK) produced
that specific screenshot — a screenshot alone cannot establish that, and
this audit does not infer it. Section 6 below establishes, by tracing the
actual code (not the screenshot), that **this exact note text is emitted
identically for both COMMON and MONTHLY_FALLBACK results** — which is what
makes it possible to reach a definite classification (Section 9) without
needing to know which case the screenshot came from.

---

## 4. Runtime → API Trace

Traced against current `develop` (post-#2510):

```
build_compass_direction_runtime()                 (backend/temples/services/compass_runtime.py)
  COMMON:   returns {targetDate, targetYear, solarMonthIndex,
                     referenceDirections, calculationMethod="annual_monthly_kyusei_v1", note}
  FALLBACK: returns {targetDate, targetYear, solarMonthIndex,
                     referenceDirections, calculationMethod="monthly_kyusei_v1", note}
  NO_COMMON_DIRECTION: returns NoCommonDirectionResult() (no fields at all)
        |
        v
get_compass_recommendations()                     (compass_recommendation_orchestrator.py)
  Reads only direction_context.get("referenceDirections") (line 128).
  Never reads, branches on, or strips calculationMethod.
  Returns CompassRecommendationResult(direction_context=direction_context)
  UNMODIFIED for both COMMON and FALLBACK (dict passed through as-is);
  direction_context=None specifically for NoCommonDirectionResult (line 118).
        |
        v
CompassRecommendationsView.post()                 (backend/temples/api_views_compass.py)
  body = {"state": ..., "direction_context": result.direction_context, ...}
  Serializes direction_context verbatim via DRF's Response() -- no field
  allowlist/denylist is applied to it beyond it already being a plain dict.
```

**Conclusion**: `calculationMethod` is generated at the Runtime layer and is
never read, stripped, or overwritten by any layer between Runtime and the
HTTP response body. It reaches the wire as `direction_context.calculationMethod`
for every state that carries a `direction_context` (i.e. COMMON and
FALLBACK; not `no_common_direction`, which carries `direction_context: null`
by design, Section 11).

---

## 5. API → Frontend Trace

```
fetch("/api/compass/recommendations")             (CompassClient.tsx:118-126)
        |
        v
body = await res.json() as CompassRecommendationsResponse   (CompassClient.tsx:134)
        |
        v
setResult(body)                                    (CompassClient.tsx:135)
        |
        v
directionContext = result?.direction_context ?? null   (CompassClient.tsx:149)
        |
        v
<CompassDirectionVisual referenceDirections={directionContext.referenceDirections} />  (CompassClient.tsx:220)
<p>{directionContext.note}（参考情報です）</p>                                          (CompassClient.tsx:221)
```

`directionContext.calculationMethod` is present on the parsed object (the
TypeScript type guarantees the field exists, Section 6), but **no line in
`CompassClient.tsx` or `CompassDirectionVisual.tsx` reads
`directionContext.calculationMethod`** — confirmed by grep across both
files. Only `.referenceDirections` and `.note` are read from
`directionContext`.

---

## 6. `calculationMethod` Preservation (table)

| Layer | Field present? | COMMON value | MONTHLY_FALLBACK value | Preserved? |
|---|---|---|---|---|
| Runtime (`compass_runtime.py`) | Yes | `annual_monthly_kyusei_v1` | `monthly_kyusei_v1` | Source of truth |
| Orchestrator (`compass_recommendation_orchestrator.py`) | Yes (passthrough) | unchanged | unchanged | YES — dict never touched, only `.get("referenceDirections")` is read |
| API response body (`api_views_compass.py`) | Yes | unchanged | unchanged | YES — `direction_context` serialized verbatim |
| Frontend type (`compass/types.ts:41`) | Yes | `"annual_monthly_kyusei_v1"` | `"monthly_kyusei_v1"` | YES — union type since #2510, was a single literal before (would have been a type-only compile error, not a data-loss issue, if left unwidened) |
| `CompassClient.tsx` state (`result`, `directionContext`) | Yes | unchanged | unchanged | YES — stored on `result` as parsed, untouched |
| `CompassClient.tsx` rendering | **Field exists in memory but is never read** | n/a | n/a | **NOT USED** (not "lost" — present but inert) |
| Analytics payload (`trackCompassResult`, `CompassClient.tsx:68-81`) | **No** | — | — | **NOT SENT** — `calculationMethod` is not one of the properties passed to `trackSearchEvent("compass_result", …)` |

**Conclusion**: `calculationMethod` survives, unmodified, all the way to
the Frontend's in-memory `result` object. It is lost only in the sense that
nothing downstream of that point (UI render, Analytics dispatch) reads it.
This is a **usage** gap, not a **propagation** gap.

---

## 7. Current UI Behavior

`CompassClient.tsx` renders the direction card (lines 217-224) whenever
`directionContext` is non-null — which is true for **both** COMMON and
MONTHLY_FALLBACK (both return a non-null `CompassDirectionRuntime` dict,
Section 4). The card's contents:

```tsx
<CompassDirectionVisual referenceDirections={directionContext.referenceDirections} />
<p>{directionContext.note}（参考情報です）</p>
```

`directionContext.note` is not a per-request computed string — it is the
fixed constant `DIRECTION_REFERENCE_NOTE` from
`backend/temples/services/direction_reference.py`, returned identically by
both the COMMON branch and the MONTHLY_FALLBACK branch of
`build_compass_direction_runtime()` (Section 4). There is no conditional
copy logic anywhere in this render path — `calculationMethod` is not
inspected, so no branch could exist.

---

## 8. COMMON vs. MONTHLY_FALLBACK UI Distinction — Frontend Distinction Audit

Checked: TypeScript union (yes, widened #2510), response parsing (field
survives `res.json()` cast, Section 5), state storage (survives on
`result`/`directionContext`, Section 6), component props
(`CompassDirectionVisual` accepts only `referenceDirections`, never
`calculationMethod`, confirmed by its prop type at
`CompassDirectionVisual.tsx:47`), rendering condition (none present that
reads `calculationMethod`).

**Classification: B — reaches the Frontend, but the UI does not use it.**

(Not A: the UI does not distinguish them. Not C: nothing is lost in
transit — Section 6 traces it intact all the way into `directionContext`.
Not D: it does originate from and arrive from Backend/API.)

---

## 9. Copy Semantic Audit

The direction-card note (`directionContext.note`, rendered at
`CompassClient.tsx:221`) reads to the effect of *"年盤と月盤による参考情報
です"* ("reference information based on the annual and monthly charts") for
**every** non-null `directionContext`, including a MONTHLY_FALLBACK result
where, by definition (Section 2), the annual chart contributed **nothing**
to `referenceDirections` — only the monthly chart did.

**Classification: SEMANTICALLY MISLEADING** for the MONTHLY_FALLBACK case.

**Reason**: the copy asserts joint annual+monthly grounding
("年盤と月盤による") for a result that Section 2's own definition
establishes is monthly-only. This is not a hypothetical concern — it
directly violates the Signal-to-Explanation Rule that
[`compass-product-contract.md`](../product/compass-product-contract.md)
Section 8 already establishes as an absolute constraint ("影響していない信
号が影響したかのように暗示する表現をしてはならない" — "must not imply a
signal influenced the result when it did not"), and that Section 2.2-7
(added in #2509) explicitly anticipates: *"Monthly Fallback Directionを
年盤・月盤の合意であるかのように表示してはならない"*. The current
production copy does exactly what Section 2.2-7 says must not happen — not
because anyone violated the rule when writing it, but because the note
text predates the Monthly Fallback concept (it was written when
`calculationMethod` had only one possible value) and has not yet been
revisited now that a second value exists.

This audit does **not** propose introducing any religious/fortune-telling
certainty language, any claim of a "correct direction," or any auspicious/
inauspicious judgment — the note is a **provenance** disclosure (which
chart(s) the number came from), not a claim about the direction's meaning
or accuracy, and the fix (Section 10) stays within that same provenance
scope.

---

## 10. Minimum UI Requirement (not implemented here)

Given Section 9's finding, the minimum viable distinction is a **copy-only**
change, evaluated against four questions:

1. **Does a copy change alone suffice?** Yes for the note text. The
   direction card's structure (visual + note) does not need to change;
   only the note's wording needs to vary by `calculationMethod`.
2. **Is a badge/label needed?** Not required to satisfy the
   Signal-to-Explanation Rule — a corrected note string already
   communicates provenance in prose, matching the existing pattern (a
   trailing "（参考情報です）" qualifier, not a separate UI element). A
   badge is a legitimate *stronger* option for a future design pass but is
   not the minimum.
3. **Should `calculationMethod` be shown to the user directly?** No — it is
   an internal machine-readable string (`"monthly_kyusei_v1"`), not
   user-facing vocabulary; Product Contract Section 8 already establishes
   that raw internal identifiers are not exposed as UI copy.
4. **Does the recommendation card need to change?** No —
   `CompassRecommendationsSection.tsx` never reads `direction_context` or
   `calculationMethod` at all (confirmed by grep, Section 6); the
   distinction is scoped entirely to the direction card, not the
   recommendation list.

**Illustrative candidate copy** (evaluation only, per this task's own
instruction — not a final implementation decision, and not to be shipped
without a dedicated Frontend PR):

```
COMMON:           「年盤と月盤の両方で重なる、今月の参考方位です」
MONTHLY_FALLBACK: 「年盤と月盤で重なる方位がないため、今月の月盤を参考にした方位です」
```

Both avoid auspicious/inauspicious claims, avoid asserting a "correct"
direction, and stay within the existing "参考情報" (reference information)
framing already used today.

---

## 11. `no_common_direction` Residual UX Audit

Current copy (`CompassClient.tsx:234-239`):

```
Title: 「今月は年盤と月盤で重なる方位がありません」
Body:  「生年月日・出発地点はどちらも問題ありません。年盤と月盤がともに支持
        する方位が今月はなかった、という結果です。」
```

**Old meaning this copy was written for**: `no_common_direction` fires
whenever annual∩monthly is empty (46.5% of algorithmic cases, pre-#2508).

**New meaning** (#2508, narrowed): `no_common_direction` now fires only
when annual∩monthly **and** monthly-only are *both* empty (3.1% residual,
Section 2).

**Classification: PARTIALLY STALE.**

The copy's literal claim — "a direction jointly supported by annual and
monthly charts did not exist this month" — remains **true** under the new
semantics (it is still a necessary condition for reaching this state), so
it is not false or misleading in the way Section 9's finding is. It is
*incomplete*: it does not communicate that a monthly-only fallback was
also attempted and also came up empty, which is now part of why this state
is reached at all, and it gives no signal that this state is now a rare
edge case (~3.1% of algorithmic cases) rather than the common outcome
(~46.5%) it was written to explain. Nothing in the copy needs correcting
for *accuracy*; it would benefit from being brought up to date with what
actually had to fail to reach it, in a future UI PR — not required by this
audit to be classified as misleading.

**No change made in this document.**

---

## 12. Analytics Instrumentation Trace

`compass_result` event (`trackCompassResult`, `CompassClient.tsx:68-81`,
documented in
[`compass-posthog-query-contract.md`](../analytics/compass-posthog-query-contract.md)
line 32) currently carries exactly:

```
result_state, purpose, origin_mode, has_birthdate,
recommendation_count, recommendationInstanceId
```

`calculationMethod` is **not** one of these properties. Confirmed against
`apps/web/src/lib/analytics/searchEvents.ts`'s `SearchAnalyticsPayload`
type: no `calculationMethod` field is declared, and `trackCompassResult`
does not pass one (an ad-hoc property could technically be added without a
type change, since the payload type carries a `[key: string]:
SearchAnalyticsPrimitive` index signature, but none is sent today).

`referenceDirections` (the array of direction labels) is also not sent to
Analytics — only the coarse `result_state` bucket is. This is unaffected by
Monthly Fallback specifically; it was already true before #2508.

**Runtime-level distinguishability vs. PostHog-level distinguishability
(kept separate per this task's instruction)**:

1. **Runtime**: COMMON and MONTHLY_FALLBACK are fully distinguishable
   (`calculationMethod` differs, Section 4).
2. **PostHog**: COMMON and MONTHLY_FALLBACK are **not** distinguishable —
   both produce identical `compass_result` events with
   `result_state="recommendation_success"` (or any of the other five
   backend states), because the orchestrator never threads
   `calculationMethod` into anything `result_state`-shaped (Section 4), and
   the frontend event payload doesn't carry the field either.

---

## 13. COMMON / FALLBACK Analytics Distinguishability — Classification

**Classification: B — adding `calculationMethod` to the existing
`compass_result` event would make COMMON/FALLBACK distinguishable.**

No new event is required. `compass_result` already fires exactly once per
resolved Compass attempt (Section 12), already carries `result_state`, and
already has `direction_context.calculationMethod` sitting unused one level
up the call stack in `CompassClient.tsx` at the exact point
`trackCompassResult` is invoked (`body.state` is read from the same
`body` object that also has `body.direction_context.calculationMethod`,
`CompassClient.tsx:134-141`) — adding the property is a same-event
extension, not a new-event problem. (This audit does not implement the
addition; it only establishes that Classification B, not C or D, is the
right shape for a future PR.)

**Relationship to the existing `VALID_NO_DIRECTION` bucket**
(`compass-posthog-query-contract.md` line 382): that bucket maps 1:1 to
`result_state="no_common_direction"` and its *definition* is unaffected by
Monthly Fallback — it still means "a completed, valid calculation that
found no usable direction." What changes is only its **expected empirical
rate**, from ~46.5% (pre-#2508 Option B semantics) to a theoretical ~3.1%
residual (Section 2) once Monthly Fallback is actually implemented in
production traffic (it already is, per #2510, merged to `develop`). Any
dashboard trending `VALID_NO_DIRECTION` frequency across the #2510 deploy
boundary needs to treat this the same way
`compass-posthog-query-contract.md` already treats the pre/post-#2499
classification break (line ~727 of that document) — as a **classification-
boundary discontinuity**, not a reliability regression or improvement in
the underlying calculation.

---

## 14. KPI Boundary

Kept explicitly separate, per this task's instruction and consistent with
[#2508](../product/compass-product-direction-decision.md) Section 19/§13:

```
Runtime Reliability:        did the calculation complete without error?
Direction Availability:     did Compass produce a usable reference direction
                             (COMMON or MONTHLY_FALLBACK)? -- 96.9% theoretical
                             under Option C (docs/audit/compass-monthly-fallback-availability.md)
Recommendation Availability: did Compass produce at least one shrine candidate?
Product Value:               did the experience provide useful decision/action value?
```

**Direction Availability rising to 96.9% (theoretical, under #2507's
matrix) does not mean Recommendation Availability is 96.9%.** Whether a
shrine actually exists inside the resolved direction's geographic sector,
from a given origin, is governed entirely by
`compass_direction_filter.filter_candidates_by_direction()` and the shrine
data set — neither of which Monthly Fallback touches (Section 15). A
MONTHLY_FALLBACK direction can just as easily resolve to
`direction_zero_candidates` as a COMMON one can; #2510's own test suite
(`TestMonthlyFallbackDirectionContext` in
`test_compass_recommendation_orchestrator.py`) explicitly covers and
asserts this — a fallback-shaped `direction_context` reaching
`direction_zero_candidates`, not `recommendation_success`, when no shrine
matches the resolved sector. No Recommendation Availability figure is
claimed or measured by this audit or by #2508/#2509/#2510.

---

## 15. Recommendation Boundary

Confirmed against `backend/temples/services/compass_recommendation_orchestrator.py`
and its test suite:

- MONTHLY_FALLBACK's `direction_context` is consumed by
  `filter_candidates_by_direction()` through the exact same call path as a
  COMMON `direction_context` (`compass_recommendation_orchestrator.py:146-150`)
  — no separate fallback-specific filter path exists.
- `build_chat_recommendations()` (the Ranking domain call,
  `compass_recommendation_orchestrator.py:172-181`) receives no
  fallback-related argument; its call signature is unchanged by #2510
  (confirmed via `git diff` against develop pre-#2510: the orchestrator
  file has zero diff).
- No ranking bonus, weight change, or candidate-pool-size change is applied
  conditionally on `calculationMethod` — the orchestrator does not branch
  on it at all (Section 4), so it structurally cannot apply one.
- No artificial candidate inflation exists for fallback results — the same
  `DEFAULT_CANDIDATE_POOL_LIMIT = 60` pre-filter applies unconditionally.

**Recommendation Ranking changed: NO.**

---

## 16. Concierge Boundary

Confirmed:

- `git diff develop... -- backend/temples/api_views_concierge.py` across
  #2508/#2509/#2510: **no diff**.
- `git diff develop... -- backend/temples/domain/kyusei.py` across
  #2508/#2509/#2510: **no diff** — `monthly_lucky_directions()` (added by
  #2506, prior to this decision chain) is reused as a pure calculation
  function by Compass; Concierge's own two call sites
  (`annual_lucky_directions()`, `planned_visit_lucky_directions()` in
  `api_views_concierge.py`) are unaffected and do not call
  `monthly_lucky_directions()` or any fallback-precedence logic.
- Monthly Fallback's precedence policy (COMMON → FALLBACK → NO_COMMON)
  lives entirely in `compass_runtime.py` (Compass Layer B), never in
  `kyusei.py`'s shared domain layer — confirmed by Section 4's trace.

**Concierge changed: NO.**

---

## 17. Required UI Follow-up

```
1. Direction-card note text: distinguish COMMON from MONTHLY_FALLBACK
   (Section 9/10) -- copy-only, no new component structurally required.
2. no_common_direction copy: optionally refresh to reflect that a monthly
   fallback attempt already failed too (Section 11) -- not required for
   accuracy, worth doing for completeness in the same Frontend PR as (1).
3. Do not surface calculationMethod as raw text anywhere (Section 10).
4. Recommendation card / CompassRecommendationsSection: no change required
   (Section 10, item 4).
```

Not implemented by this document.

---

## 18. Required Analytics Follow-up

```
1. Add calculationMethod (or an equivalent derived boolean/enum) to the
   compass_result event payload (Section 13, Classification B) -- a
   same-event property addition, not a new event.
2. Document, in a future compass-posthog-query-contract.md revision, that
   VALID_NO_DIRECTION's empirical rate is expected to drop sharply
   post-#2510 deployment, and that this is a classification-boundary
   effect (Section 13), not a reliability change -- same treatment already
   given to the pre/post-#2499 boundary in that document.
3. No new PostHog event is required (Section 13 explicitly rejects
   Classification C/D).
```

Not implemented by this document.

---

## 19. Explicit Non-Decisions

This audit does not decide, and this PR does not implement:

- Final UI copy for either the direction card or the no_common_direction
  state (Section 10/11 give evaluation only).
- Whether a badge/label component should eventually be introduced (Section
  10 concludes it is not the *minimum*, not that it is prohibited).
- The exact analytics property name or type for `calculationMethod` in
  `SearchAnalyticsPayload` (Section 18 states *that* it's needed, not its
  final shape).
- Any change to `compass-posthog-query-contract.md`, the Product Contract,
  or the Runtime Contract.
- Recommendation Availability measurement (Section 14) — remains a
  separate, unresolved boundary per #2508 Section 12/16.

---

## 20. Impact

```
Production code changed:            NO
Frontend production code changed:   NO
Backend production code changed:    NO
UI copy changed:                    NO
PostHog instrumentation changed:    NO
Runtime Contract changed:           NO
Product Contract changed:           NO
Recommendation Ranking changed:     NO
Concierge changed:                  NO
kyusei.py changed:                  NO
DB change:                          NONE
Migration:                          NONE
```

---

## 21. Verification

```
git status --short            -> only this document
git diff --stat                -> only this document
git diff --name-only           -> docs/audit/compass-monthly-fallback-ui-analytics-boundary.md
git diff --check               -> clean
```

All findings in Sections 3-16 were verified by reading the actual
`develop`-branch source (post-#2510) named in each section, not inferred
from documentation alone; documentation (Product/Runtime Contract, PostHog
Query Contract) was cross-checked against, and found consistent with, the
code it describes, except where explicitly flagged (Section 9's copy
staleness, Section 11's partial staleness, Section 13's missing property).

---

## 22. Next Implementation Gate

```
D: UI + Analytics both required.
```

Reasoning: Section 9 establishes the direction-card copy is semantically
misleading for MONTHLY_FALLBACK today (a UI-required finding), and Section
13 establishes PostHog cannot distinguish COMMON from MONTHLY_FALLBACK
today (an Analytics-required finding). Neither finding depends on the
other — a future implementation could sequence them as two independent,
narrowly-scoped PRs (one Frontend-copy PR per Section 17, one
Analytics-property PR per Section 18) rather than a single combined PR,
consistent with #2508's Section 27 implementation-sequence philosophy of
small, single-concern PRs. No implementation is performed by this document.
