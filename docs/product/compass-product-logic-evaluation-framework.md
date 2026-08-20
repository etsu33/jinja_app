> **Status: Active — Evaluation Framework only. Does not select a Direction
> Logic option. Does not finalize a Product Promise.**
>
> This document fixes the vocabulary, evaluation axes, evaluation method,
> and quantitative metric definitions that the next PR (**Compass Direction
> Logic Product Decision Audit**) must use to compare Direction Logic
> options (current annual∩monthly, monthly fallback, annual fallback, score
> model, no-direction-as-first-class). It intentionally does **not** compare
> those options, does **not** recommend one, and does **not** change
> production code, the Runtime Contract, Recommendation Ranking, or
> Concierge. docs-only.

---

## 1. Purpose

Prior audits ([#2496](../audit/compass-direction-filter-unavailable-root-cause.md),
[#2497](../audit/compass-direction-availability-product-decision.md)) and the
resulting contract/implementation work ([#2498](compass-product-contract.md)
Section 2.1, #2499
implementation, [#2500](../analytics/compass-posthog-query-contract.md),
[#2501](../audit/compass-no-direction-production-verification.md)) established
*that* `no_common_direction` is a legitimate, first-class Compass result and
verified it in production. They did **not** establish *how* to compare
`no_common_direction` (current strict intersection) against alternative
Direction Logic designs (monthly fallback, annual fallback, score model) in
a way that is not silently biased toward whichever option is described
first, most vividly, or most recently.

This document exists to fix that evaluation apparatus **before** any such
comparison is attempted, so the comparison itself is not built to justify a
predetermined answer.

---

## 2. Scope

### In scope

- Extracting the current, documented Product Promise (not inventing a new one)
- Tracing current Direction Logic responsibility across the actual code
- Defining Runtime Reliability, Direction Availability, Recommendation
  Availability, and Product Value as four distinct, non-interchangeable concepts
- Defining `no_common_direction` as a Technical State and, separately, as an
  unresolved Product Result
- Defining three comparable (not ranked) Product Promise candidates (A/B/C)
- Fixing ten evaluation axes and, for each, what evidence would answer it
- Fixing quantitative metric definitions (Reliability Rate, Direction
  Availability Rate, Recommendation Availability Rate) without computing new
  numbers beyond what [#2497](../audit/compass-direction-availability-product-decision.md)
  already measured
- Recording contract/documentation drift discovered while doing this (see
  §3.3) — reporting it, not silently fixing it

### Out of scope (see §21 for the explicit list)

- Selecting a Direction Logic option
- Selecting a final Product Promise
- Implementing anything (fallback, score model, UI copy, Runtime Contract change)
- Changing Recommendation Ranking or Concierge
- Computing any new PostHog query or production number beyond what is
  already recorded in merged audits

---

## 3. Source of Truth

### 3.1 Audits (chronological, all merged into `develop` as of this document)

| PR | Title | What it established |
|---|---|---|
| [#2496](../audit/compass-direction-filter-unavailable-root-cause.md) | Compass Direction Filter Root Cause Audit | `direction_filter_unavailable` root cause = year-chart ∩ month-chart intersection empty; Classification `A — EXPECTED FAIL-SAFE` |
| [#2497](../audit/compass-direction-availability-product-decision.md) | Compass Direction Availability Product Decision Audit | 972-case deterministic matrix (9 honmei stars × 12 solar-month buckets × 9 years) against unmodified `kyusei.py`: 520/972 (53.5%) available, 452/972 (46.5%) empty intersection; 5 product options compared (not yet decided) |
| [#2498](compass-product-contract.md) Section 2.1 | No-Direction First-Class Contract | Canonical Decision: model no-common-direction as a first-class result, not an error; introduced `NO_COMMON_DIRECTION` as a **concept** (marked CONTRACT TARGET, not yet an implemented state name at the time) |
| #2499 (no dedicated audit doc — implementation PR, `git log` only) | Runtime / UI State Implementation | Implemented `NoCommonDirectionResult` marker in `compass_runtime.py` and `STATE_NO_COMMON_DIRECTION = "no_common_direction"` in `compass_recommendation_orchestrator.py`; `kyusei.py` left unmodified |
| [#2500](../analytics/compass-posthog-query-contract.md) | No-Direction Analytics Contract Alignment | Query Contract updated: `no_common_direction` → `VALID_NO_DIRECTION` bucket, distinct from `ERROR`; split former "Compass Result Success Rate" into Reliability Rate and Recommendation Delivery Rate |
| [#2501](../audit/compass-no-direction-production-verification.md) | No-Direction Production Analytics Verification | Confirmed in production PostHog: known QA traffic on 2026-08-20 classified correctly as `no_common_direction`, no collapse into `direction_filter_unavailable` |

### 3.2 Canonical Contracts (paths confirmed directly against current `develop`, not assumed)

| Document | Path |
|---|---|
| Compass Product Contract | `docs/product/compass-product-contract.md` |
| Compass MVP Runtime Contract | `docs/product/compass-mvp-runtime-contract.md` |
| Compass PostHog Query Contract | `docs/analytics/compass-posthog-query-contract.md` |
| Compass Analytics Contract | `docs/analytics/compass-analytics-contract.md` |

### 3.3 Source Precedence and Recorded Drift

Precedence used throughout this document, per task instruction:

```
1. current develop production code
2. current canonical Product / Runtime Contract
3. latest merged audit
4. historical audit
```

**DOCUMENTATION DRIFT found while assembling this Framework** (recorded, not
silently corrected — fixing these is out of this PR's scope):

1. `docs/product/compass-product-contract.md` Section 2.1-1 states: *"`NO_COMMON_DIRECTION`という名称は概念上の識別子であり、CONTRACT TARGETとして記載する（現時点で実装されたstate名・API値ではない）"* — i.e. "not yet an implemented state name." This was true when written (#2498) but is now stale: current `develop` (post-#2499) implements exactly this as `STATE_NO_COMMON_DIRECTION = "no_common_direction"` in `backend/temples/services/compass_recommendation_orchestrator.py:51`. **Current code takes precedence** over this sentence for this Framework's purposes.
2. The same document's Section 2.1-3, titled "現行実装とのギャップ（IMPLEMENTATION GAP）", describes both Group A (invalid runtime) and Group B (no-common-direction) as collapsing into the same `None` / `STATE_DIRECTION_FILTER_UNAVAILABLE`. This gap was **closed by #2499** — current code returns a distinct `NoCommonDirectionResult` marker (see §5 below) that the orchestrator maps to a distinct state. The gap this section describes no longer exists in `develop`.
3. The same document's Section 2.1-6 classifies the required Analytics Contract change as "DOC CLARIFICATION REQUIRED" pending a future state split. That split was **completed by #2500** (`compass-posthog-query-contract.md`'s `VALID_NO_DIRECTION` bucket).
4. `docs/product/compass-mvp-runtime-contract.md` Section 8-1 contains the identical stale "IMPLEMENTATION GAP" claim, for the same reason as (2).

None of these are **CONTRACT DRIFT** (the current Product/Runtime Contract's *decisions* — first-class treatment, retry semantics, Concierge isolation, the open Shrine Recommendation question — remain valid and unchanged by #2499/#2500/#2501). They are narrower: three sentences describing an implementation gap that has since been closed, and one classification note whose triggering condition has since occurred. This Framework treats current `develop` code as authoritative for "is `no_common_direction` implemented" and treats the Product/Runtime Contract's *Decision*, *Reason*, and open items (Shrine Recommendation boundary, §2.1-5) as still governing.

---

## 4. Current Product Promise

Extracted from `docs/product/compass-product-contract.md` Section 2/2.1 and
`apps/web/src/features/compass/CompassClient.tsx`, current `develop`. No new
Promise is proposed here.

### 4.1 CURRENT DOCUMENTED PROMISE (Product Contract Section 2, as revised by #2498)

> 時間・方位runtime signalと目的から、今月の方向を解釈し、年盤と月盤が共通して支持する参考方位がある月はそれを示す。ない月は、その結果自体を今月の参考情報として示した上で、目的から参拝候補を示す。

Explicitly states: **"Compass does not promise to always return a direction"**
(Product Contract Section 2, line: "「Compassは常に方向を返す」とは約束しない。").

### 4.2 CURRENT UI PROMISE (as rendered by `CompassClient.tsx`, current `develop`)

| Surface | Copy |
|---|---|
| Page intro | 「今月の流れと目的から、向かう方向と参拝候補を見つけます。方向が重ならない月は、その結果もそのままお伝えします。」— visible header text: 「今月の流れと目的から、向かう方向と参拝候補を見つけます。」（`CompassClient.tsx:161`） |
| Submit CTA | 「今月の方向を確認する」 |
| `no_common_direction` result | Title: 「今月は年盤と月盤で重なる方位がありません」／Body: 「生年月日・出発地点はどちらも問題ありません。年盤と月盤がともに支持する方位が今月はなかった、という結果です。」（`CompassClient.tsx:234-240`） |
| `direction_filter_unavailable` result | Title: 「方向の参考情報を計算できませんでした」／Body: 「生年月日または出発地点をご確認のうえ、もう一度お試しください。」（`CompassClient.tsx:226-232`） |

### 4.3 UNRESOLVED PROMISE

The following are **not** answered by the current documented Promise or the
current UI copy, and this Framework does not answer them either:

- Whether Compass **must** show at least one shrine recommendation whenever
  a direction is available (implicitly yes today, but never stated as a
  requirement — see the Recommendation Availability discussion, §9).
- Whether Compass **must** show shrine recommendations when no direction is
  available (`docs/product/compass-product-contract.md` Section 2.1-5,
  **explicitly recorded as OPEN PRODUCT DECISION**, unresolved by #2498 or
  #2499 — this Framework does not resolve it either).
- What fraction of Compass sessions ending in `no_common_direction` is
  acceptable (the empirical rate is recorded in §17 as a *characteristic*,
  not evaluated against a threshold).

### 4.4 Guarantee Confirmation

- **"Compass always returns a direction"**: NO such guarantee exists,
  documented or implemented (Product Contract Section 2, explicit denial;
  matches implementation — `no_common_direction` is a real, reachable state).
- **"Compass always recommends a shrine"**: NO such guarantee exists. No
  document asserts it. Current implementation returns zero recommendations
  for `no_common_direction`, `direction_zero_candidates`,
  `evidence_zero_candidates`, `direction_filter_unavailable`, and
  `invalid_purpose` — five of six backend result states produce zero
  recommendations; only `recommendation_success` produces any.

---

## 5. Current Direction Logic Responsibility

Traced directly against current `develop` (verified — no code changed since
#2499; `git diff 41cba8d6 develop -- backend/ apps/web/` is empty).

```
birthdate, target_date
        │
        ▼
backend/temples/domain/kyusei.py
  honmei_star(birthdate)
  annual_lucky_directions(birthdate, today)        -- annual (year-chart) lucky directions
  planned_visit_lucky_directions(birthdate, visit_date)
    = annual ∩ monthly (month-chart) lucky directions
        │
        ▼  (result dict, or None if birthdate/date invalid)
backend/temples/services/compass_runtime.py
  build_compass_direction_runtime(birthdate, target_date)
    -> CompassDirectionRuntime dict            (intersection non-empty)
    -> NoCommonDirectionResult()               (intersection == [], valid calculation)
    -> None                                    (invalid/unavailable input)
        │
        ▼  direction_context
backend/temples/services/compass_recommendation_orchestrator.py
  get_compass_recommendations(purpose, origin, direction_context)
    - isinstance(direction_context, NoCommonDirectionResult)
        -> STATE_NO_COMMON_DIRECTION, recommendations=[]
    - not isinstance(direction_context, Mapping)
        -> STATE_DIRECTION_FILTER_UNAVAILABLE, recommendations=[]
    - else: calls compass_direction_filter.filter_candidates_by_direction()
        to narrow the DB candidate pool to shrines whose bearing falls in
        an authorized sector, then hands the filtered pool to
        build_chat_recommendations() (the Recommendation domain)
        │
        ▼
backend/temples/services/compass_direction_filter.py
  filter_candidates_by_direction(candidates, origin, reference_directions)
    -- geographic filter only: which shrines fall within the authorized
       bearing sectors. Does not score, rank, or generate reasons.
        │
        ▼  filtered candidate list
Recommendation domain (build_chat_recommendations, concierge_chat_candidates,
concierge_chat_ranking -- NOT modified or traced further by this Framework;
see §18 Ranking Boundary)
        │
        ▼
apps/web/src/features/compass/CompassClient.tsx, CompassRecommendationsSection.tsx
  UI presentation of state + recommendations
        │
        ▼
apps/web/src/lib/analytics/searchEvents.ts, trackCompassResult()
  compass_result{result_state=...} forwarded generically, no branching logic
```

### 5.1 Layer Separation (A–F)

| Layer | Owns | Files | Does NOT own |
|---|---|---|---|
| **A. 九星/方位計算 (Kyusei Calculation)** | Pure honmei-star and annual/monthly lucky-direction math | `backend/temples/domain/kyusei.py` | Product interpretation of an empty result; Concierge-specific behavior (shared, Signal Reuse only per `compass-product-contract.md` Section 1) |
| **B. Compass Runtime (Direction Runtime Authority)** | Deciding whether a `CompassDirectionRuntime`, a `NoCommonDirectionResult`, or `None` results from Layer A's output; Compass-specific interpretation policy | `backend/temples/services/compass_runtime.py` | Any change to Layer A's calculation itself |
| **C. Shrine Candidate Filtering** | Geographic narrowing of the DB candidate pool by authorized bearing sector | `backend/temples/services/compass_direction_filter.py` | Scoring, ranking, reason generation |
| **D. Recommendation Ranking** | Scoring, ranking, reason authority for the already-filtered candidate pool | `concierge_chat_ranking.py`, `concierge_chat_candidates.py`, `build_chat_recommendations` (not modified by any Compass work to date) | Deciding *which* candidates enter the pool (that's Layer C) |
| **E. UI Presentation** | Rendering the returned state as copy/visuals | `CompassClient.tsx`, `CompassRecommendationsSection.tsx`, `CompassDirectionVisual.tsx` | Any calculation or filtering |
| **F. Analytics** | Observing state distributions | `searchEvents.ts`, PostHog Query Contract | Deciding whether an observed distribution is product-acceptable (see §19) |

---

## 6. Responsibility Boundaries

These boundaries are the constraints any future Direction Logic option must
satisfy to remain **comparable** under this Framework:

1. **Layer A must not be silently redefined to serve a single Compass
   preference.** `kyusei.py` is Signal Reuse shared with Concierge (§18). A
   Direction Logic option that requires changing `annual_lucky_directions()`
   or `planned_visit_lucky_directions()`'s own contract carries **higher**
   Concierge risk than one that doesn't (Axis 7), and must say so explicitly
   when compared.
2. **Layer B is where Compass-specific interpretation policy belongs.**
   `#2499`'s architectural principle — implement Compass-specific policy in
   `compass_runtime.py`/`compass_recommendation_orchestrator.py`, not in
   `kyusei.py` — is the reference precedent for keeping future Direction
   Logic changes isolated from Concierge.
3. **Layer C (candidate filtering) and Layer D (Ranking) are separate
   concerns and must be evaluated separately.** A Direction Logic option may
   change *which* candidate population reaches Layer D (e.g. a wider
   authorized-sector set under a fallback design), but must not be described
   as "changing Ranking" if it does not touch Layer D's scoring/reason logic.
   See §18.
4. **Layer F cannot certify Layer B's correctness.** Analytics observes; it
   does not decide. See §19.

---

## 7. Runtime Reliability

**Question**: did calculation processing complete normally for a valid input?

**Definition**: a `compass_result` is Reliability-valid if it reached one of
the states that represents "the runtime completed a real computation and
returned a determinate outcome" — regardless of whether that outcome
included a direction or a recommendation. Per the current Query Contract
(#2500), this is `recommendation_success`, `no_common_direction`,
`direction_zero_candidates`, or `evidence_zero_candidates`. It excludes
`backend_error`, `invalid_purpose`, and `direction_filter_unavailable` (the
three states representing invalid input or genuine runtime failure).

**Scope**: this concept says nothing about whether a direction or a
recommendation resulted — only whether the *computation itself* behaved as
designed for the input it received.

---

## 8. Direction Availability

**Question**: could Compass present the user with a usable direction?

**Definition**: of the Compass results where Runtime Reliability held (§7),
what fraction actually produced a non-empty `CompassDirectionRuntime` (i.e.
`recommendation_success`, `direction_zero_candidates`, or
`evidence_zero_candidates` — all three require a resolved direction before
candidate filtering can even run) versus produced `no_common_direction`
(reliable, but no direction).

**Scope**: this concept is **downstream of** Reliability and **independent
of** Recommendation Availability — a result can have a direction and still
produce zero shrine candidates (`direction_zero_candidates`).

---

## 9. Recommendation Availability

**Question**: could Compass present the user with at least one shrine candidate?

**Definition**: of the Compass results where Runtime Reliability held (§7),
what fraction reached `recommendation_success` (the only state that carries
a non-empty `recommendations` array in the current implementation).

**Scope**: strictly narrower than Direction Availability — every
`recommendation_success` result had a direction, but not every result with a
direction reaches `recommendation_success` (`direction_zero_candidates` and
`evidence_zero_candidates` both had a direction and zero recommendations).

---

## 10. Product Value

**Question**: did Compass provide something the user could use for their
next decision or action?

**Definition**: **deliberately undefined by this Framework.** Product Value
cannot be derived automatically from Runtime Reliability, Direction
Availability, or Recommendation Availability — it depends on which Product
Promise (§12) is adopted. A `no_common_direction` result might have zero
Product Value under Promise A (which treats the direction itself as the
deliverable) or non-zero Product Value under a Promise that treats "an
honest, timely answer" as valuable regardless of content. **This Framework
does not resolve which is correct.** Any future PR that reports a single
"Product Value rate" without first resolving the Product Promise is
fabricating a metric this Framework explicitly declines to define — see §16
Explicit Non-Decisions.

---

## 11. no_common_direction Dual Definition

### 11.1 Technical State (Runtime Contract Section 8 Group B, current `develop`)

```
- valid birthdate
- valid target_date
- annual lucky-direction calculation completed (honmei_star resolved)
- monthly lucky-direction calculation completed
- annual ∩ monthly == empty set
- NOT an error (Runtime Contract Group A is a different, disjoint set of causes)
- deterministic: same birthdate + same target_date (same honmei star, same
  solar-month bucket) -> same result, every time (per #2497 §10's
  demonstrated star×month combinations that stay empty across multiple years)
```

Implemented as `NoCommonDirectionResult` (`compass_runtime.py`) →
`STATE_NO_COMMON_DIRECTION = "no_common_direction"`
(`compass_recommendation_orchestrator.py`), verified reaching production
PostHog correctly classified in [#2501](../audit/compass-no-direction-production-verification.md).

### 11.2 Product Result (deliberately incomplete — Promise-dependent)

```
- no direction is shown to the user
- no shrine recommendation is shown to the user (current implementation;
  Shrine Recommendation boundary remains OPEN, Product Contract Section 2.1-5)
- Product Value is NOT automatically zero -- whether this is a
  satisfactory, neutral, or unsatisfactory outcome depends entirely on
  which Product Promise candidate (§12) is eventually adopted
```

**This Framework does not infer Product Value from the Technical State.**
The Technical State is a fact about the runtime; the Product Result's value
is a judgment that requires a Product Promise decision this document does
not make.

---

## 12. Product Promise Candidates

Presented as **comparable candidates only** — none is recommended, adopted,
or ranked here.

### Candidate A — Strict Common Direction

**Concept**: if annual and monthly charts both support a direction, present
that common direction as the reference for the visit. If no common direction
exists, return "no common direction" itself as the information.

**This is the current implementation and current documented Promise**
(Product Contract Section 2, as revised by #2498/#2499).

### Candidate B — Actionable Monthly Direction

**Concept**: provide a direction the user can act on this month. The exact
annual/monthly calculation method that produces it is **not decided by this
Framework** — that is precisely the comparison the next PR performs.

### Candidate C — Direction-to-Shrine Guidance

**Concept**: use the month's direction information as an entry point, and
guide the user all the way to a state where they can actually select a
visit candidate.

---

## 13. Promise Comparison Model

No verdict, no PASS/FAIL. This table exists so the next PR can compare
Direction Logic options against a fixed row set, not an ad hoc one.

| Dimension | Candidate A | Candidate B | Candidate C |
|---|---|---|---|
| User expectation | "I get a direction, or an honest no-direction result" | "I get something actionable to do this month" | "I get guided all the way to a shrine to visit" |
| Direction required? | No (explicit no-direction is a valid outcome) | Yes (by definition of "actionable direction") | Yes, as an entry point |
| Shrine recommendation required? | No (current: never required; OPEN per §4.3) | Unspecified — depends on the calculation method chosen | Yes (explicit end-state of the Promise) |
| Consistency with `no_common_direction` | Fully consistent — this candidate *is* what #2498 already adopted | Requires resolving what "actionable" means when the strict intersection is empty (this is exactly what a monthly/annual-fallback or score-model Direction Logic option would need to answer) | Same tension as B, plus a stronger requirement that *something* shrine-shaped always results |
| Distance from current implementation | None — already implemented (#2499) | Undetermined — depends on which Direction Logic option is chosen next | Undetermined, and additionally requires resolving the OPEN Shrine Recommendation boundary (§4.3) |
| Distance from current Product Contract | None | Would require revising Product Contract Section 2's one-line Promise | Would require revising Product Contract Section 2 **and** resolving Section 2.1-5 |
| Measurability | Fully measurable today with existing Query Contract (#2500) — Direction Availability Rate, Reliability Rate | Direction Availability Rate would need to be recomputed once a specific calculation method is chosen (numbers would differ from #2497's) | Would additionally require defining and measuring a Recommendation Availability Rate under the new logic |
| User misunderstanding risk | Low, if the no-direction copy stays as restrained as #2499's (already verified non-error framing in production, #2501) | Medium — "actionable" is a promise that must be kept precisely, or the same MISLEADING-copy problem #2497 found in the old `direction_filter_unavailable` text could recur under a new name | Medium-high — promising a shrine "always" reintroduces exactly the "does Compass always return X" question #2497/#2498 moved away from for direction |

---

## 14. Product Logic Evaluation Axes

Fixed for use by the next PR. Ten axes, none weighted or ranked here.

1. **Product Promise Alignment** — does the Direction Logic satisfy whichever Promise (§12) is adopted?
2. **Semantic Consistency** — does it explain annual/monthly/direction consistently, without redefining their meaning merely because a redefinition would let something be displayed?
3. **Direction Availability** — for valid input, how often is a direction produced (§8)?
4. **Recommendation Availability** — for valid input, how often does the flow reach a shrine candidate (§9)?
5. **User Comprehensibility** — can the user understand why this direction, why no direction, why this shrine?
6. **Determinism / Reproducibility** — does the same input always produce the same result?
7. **Concierge Isolation** — does the change avoid altering Concierge behavior (§18)?
8. **Recommendation Ranking Isolation** — does the change avoid altering Ranking algorithm itself (§18/§6.3)?
9. **Runtime Contract Impact** — how much of the existing Runtime Contract (Schema, state taxonomy, Fail-safe table) must change?
10. **Implementation Complexity** — scope of production change, test surface, maintainability.

---

## 15. Evaluation Method

For each axis, what evidence answers it — fixed now so the comparison PR
cannot invent ad hoc evidence per option.

| Axis | Evidence source |
|---|---|
| 1. Product Promise Alignment | Manual review: does the option's behavior match the adopted Promise's stated User expectation row (§13)? |
| 2. Semantic Consistency | Review against `docs/product/compass-product-contract.md` Section 7 ("なぜこの方向か"/"なぜこの神社か" separation) and Section 8 (Signal-to-Explanation Rule) — does the option's explanation trace to a signal actually used? |
| 3. Direction Availability | Representative matrix (same method as #2497: 9 honmei stars × 12 solar-month buckets × N years, run against the option's actual calculation logic) — measure available/valid ratio |
| 4. Recommendation Availability | Same matrix, extended to count results reaching `recommendation_success` / results with Runtime Reliability |
| 5. User Comprehensibility | Copy review against §14's three questions, plus the MISLEADING/PARTIALLY ALIGNED/ALIGNED rubric #2497 §12 already established |
| 6. Determinism | Code review: same birthdate + same target_date must produce the same output on repeated calls, no randomness, no external state |
| 7. Concierge Isolation | Call-graph / `grep` review: does the option require changing `kyusei.py`'s public function signatures or return contracts (which `api_views_concierge.py:563` depends on directly)? Classify per #2497 §21's own taxonomy: NO CONCIERGE IMPACT / SHARED FUNCTION RISK / CONCIERGE CONTRACT CHANGE REQUIRED |
| 8. Recommendation Ranking Isolation | Diff review: does the option touch `concierge_chat_ranking.py`, weights, or reason-authority logic (Layer D, §5.1), versus only changing what reaches Layer C? |
| 9. Runtime Contract Impact | Schema/state/`calculationMethod` diff against `docs/product/compass-mvp-runtime-contract.md` Section 5/8 — YES/NO per field |
| 10. Implementation Complexity | File-count and layer-count of the required change (§5.1), test files requiring new/updated coverage, whether a new PR sequence (contract → runtime → UI → analytics, per #2499/#2500's own precedent) is needed |

This PR does **not** run any of these evaluations against a specific
Direction Logic option.

---

## 16. Quantitative Metric Definitions

### Runtime Reliability Rate

```
(count of compass_result with Runtime-Reliability-valid state, §7)
÷
(count of compass_result with a valid — i.e. not itself malformed — attempt)
```

Already implemented in the Query Contract as **Compass Runtime Reliability
Rate** (`docs/analytics/compass-posthog-query-contract.md`, #2500). This
Framework does not redefine it, only restates it for cross-reference.

### Direction Availability Rate

```
(count of Runtime-Reliability-valid results with a non-empty CompassDirectionRuntime)
÷
(count of Runtime-Reliability-valid compass_result)
```

Algorithmically measured for the **current** implementation by #2497
(972-case matrix: 520/972 = 53.5%). Any future Direction Logic option would
need this same ratio recomputed against its own logic — not assumed to
transfer from #2497's number.

### Recommendation Availability Rate

```
(count of compass_result{result_state="recommendation_success"})
÷
(count of Runtime-Reliability-valid compass_result)
```

Not yet computed for current production traffic (would require a
production PostHog query outside this docs-only Framework's scope) — this
document only fixes the definition.

### Recommendation CTR

**Unchanged.** Per `docs/analytics/compass-posthog-query-contract.md` §KPI
"Recommendation → Shrine Detail CTR", the denominator remains `card_view`
impressions actually shown — i.e. the population where
`result_state="recommendation_success"` (confirmed structurally excludes
`no_common_direction`/`direction_zero_candidates` in
[#2500](../analytics/compass-posthog-query-contract.md) and re-verified
empirically in [#2501](../audit/compass-no-direction-production-verification.md)
Target E). This Framework does not modify the CTR definition.

### Product Value

**Not reduced to a single rate.** Per §10, Product Value depends on which
Product Promise (§12) is adopted. Fabricating a single "Product Value KPI"
before that decision would smuggle a Promise decision into a measurement
document — explicitly disallowed (§21).

---

## 17. Known Availability Characteristic

```
Overall direction available:   520 / 972 (53.5%)
Overall no-common-direction:   452 / 972 (46.5%)
```

Source: [#2497](../audit/compass-direction-availability-product-decision.md)
§6, a deterministic 9-honmei-star × 12-solar-month-bucket × 9-year matrix
run against unmodified production `kyusei.py`. Re-cited here, not
recomputed.

**This is recorded strictly as a KNOWN AVAILABILITY CHARACTERISTIC of the
current (Candidate A / strict intersection) Direction Logic — not as a
verdict.** Whether 46.5% is acceptable, concerning, or irrelevant depends on
which Product Promise (§12) governs, and that decision is explicitly out of
scope for this document (§21). This Framework's only claim about the number
is that it exists, is reproducible, and belongs in the Direction Availability
axis (§14 Axis 3) evidence set for the current option when the next PR
performs its comparison.

---

## 18. Concierge Boundary

Confirmed directly against current code:
`backend/temples/api_views_concierge.py:30,563-565` imports and calls
`annual_lucky_directions()` and `planned_visit_lucky_directions()` from
`backend/temples/domain/kyusei.py` directly (Compat Mode direction-calc
path), unchanged by any Compass work through #2501.

**Evaluation condition fixed by this Framework**: *"Compass Product Logic
change must not alter Concierge behavior."* Operationally, this means any
Direction Logic option that requires changing `kyusei.py`'s public function
signatures, return-value contract, or calculation semantics carries
Concierge risk and must be classified under Axis 7 (§14/§15) as at minimum
SHARED FUNCTION RISK. An option confined to `compass_runtime.py`/
`compass_recommendation_orchestrator.py` (Layer B, §5.1) — the precedent
#2499 already established — qualifies as NO CONCIERGE IMPACT.

No shared code is modified by this document.

---

## 19. Recommendation Ranking Boundary

Recommendation Ranking (Layer D, §5.1 — `concierge_chat_ranking.py`,
`build_chat_recommendations`, candidate scoring, reason authority) is
**not** a change target of this Framework or of any Direction Logic
comparison it enables.

Direction Logic **may** influence *which population* of candidates reaches
Layer D (e.g. a wider or narrower authorized-sector set under a different
Direction Logic option changes Layer C's output, which changes Layer D's
input population) — that influence is expected and in scope for comparison.
The Ranking **algorithm itself** — weights, scoring formula, reason
generation — is not. Any future PR proposing a Direction Logic option that
also touches Layer D must be flagged as out-of-boundary for that PR, not
folded into it silently.

---

## 20. Analytics Boundary

Analytics (Layer F, §5.1) observes Reliability, Direction Availability,
Recommendation Availability, and downstream engagement (CTR,
Favorite/Visit/Reflection attribution, per the existing Query Contract). It
does **not** decide whether a Direction Logic option is product-correct.
"This is measurable" is not evidence that "this is good" — the two
questions are answered by different axes (§14 Axis 3/4 vs. Axis 1/5)
requiring different evidence (§15).

No PostHog instrumentation, event, property, or configuration is changed by
this document.

---

## 21. Explicit Non-Decisions

This Framework does **not** decide, and any reviewer citing this document to
justify one of the following should be corrected:

- Whether to keep current annual ∩ monthly (Candidate A / current
  implementation) as final
- Whether to adopt a monthly fallback
- Whether to adopt an annual fallback
- Whether to adopt a score model
- Fallback priority (if any fallback is later adopted)
- Any change to `calculationMethod` or `CompassDirectionRuntime` Schema
- Any change to Recommendation behavior (including the OPEN Shrine
  Recommendation boundary, Product Contract Section 2.1-5)
- Premium value or subscription pricing implications
- A final Product Promise (Candidate A, B, C, or another)
- Whether the 46.5% no-common-direction rate (§17) is product-acceptable

---

## 22. Next Product Decision Gate

The next PR — **Compass Direction Logic Product Decision Audit** — may
proceed only after this Framework is merged, and must:

1. Adopt (or explicitly re-derive, with justification, if this Framework is
   found insufficient) the same vocabulary from §7–§11.
2. Compare Direction Logic options (current strict intersection, monthly
   fallback, annual fallback, score model, and any others) using the same
   ten axes from §14, evaluated by the methods fixed in §15.
3. Compute Direction Availability Rate and Recommendation Availability Rate
   (§16) **per option**, using the same 9×12×9 matrix methodology #2497
   established for the current option — not reuse #2497's number for a
   different option's logic.
4. Select (or explicitly decline to select) a Product Promise candidate from
   §12, or propose a new one only with the same comparison rigor.
5. Classify each option's Concierge Isolation (§18) and Ranking Isolation
   (§19) using the fixed evaluation method, before any implementation is proposed.

This document does not perform any of steps 1–5. That is the next PR's job.

---

## Non-Goals (restated)

```
Production code changed: NO
Frontend code changed: NO
Backend code changed: NO
kyusei.py changed: NO
compass_runtime.py changed: NO
Orchestrator changed: NO
API changed: NO
Runtime Contract changed: NO
Product Contract's final Promise changed: NO
Recommendation Ranking changed: NO
Concierge changed: NO
DB change: NONE
Migration: NONE
Analytics instrumentation changed: NO
PostHog configuration changed: NONE
Dashboards created: NONE
New analytics events: NONE
Fallback implemented: NO
Score model implemented: NO
Premium: NOT STARTED
Personal Continuity: NOT STARTED
```
