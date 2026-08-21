> **Status: `PROPOSED — MOTHER SHIP DECISION REQUIRED`**
>
> Using the evaluation vocabulary, ten axes, and evaluation methods fixed by
> [compass-product-logic-evaluation-framework.md](../product/compass-product-logic-evaluation-framework.md)
> (PR [#2502](https://github.com/etsu33/jinja_app/pull/2502), merged, unchanged
> by this document), this audit compares five Direction Logic options —
> **A** strict annual∩monthly (pre-first-class framing), **B** the same
> calculation with `no_common_direction` as a first-class result (**this is
> the current `develop` implementation**, live since #2499), **C** monthly
> fallback, **D** annual fallback, and **E** a weighted score model — on the
> same evidence, without selecting one as final.
>
> **Recommended (Mother Ship decision required): B — keep the current
> implementation as-is.** It is already live, already resolves the
> MISLEADING-copy problem #2497 identified, and scores at or near the best on
> 9 of the 10 fixed axes with zero incremental engineering cost. **Alternative:
> C — Monthly Fallback**, conditional on the Mother Ship deciding the 46.5%
> no-common-direction rate is unacceptable under whichever Product Promise is
> adopted; C's own Direction Availability is **not quantifiable today**
> without a follow-on measurement PR (§11, §29).
>
> This audit implements nothing, adopts no Product Promise, and changes no
> production code, Contract, Recommendation Ranking, Concierge behavior, or
> Analytics instrumentation. docs-only.

---

## 1. Executive Summary

[compass-product-logic-evaluation-framework.md](../product/compass-product-logic-evaluation-framework.md)
(#2502, merged) fixed the vocabulary, ten evaluation axes, evaluation
methods, and quantitative metric definitions that this audit is required to
use, without itself comparing any Direction Logic option. This document
performs that comparison for the first time, across five options:

```
A — Strict annual ∩ monthly, pre-first-class framing (historical/legacy comparison point)
B — Same calculation + no_common_direction as first-class result (CURRENT develop, live since #2499)
C — Monthly fallback (not implemented)
D — Annual fallback (not implemented)
E — Weighted annual/monthly score model (not implemented)
```

**Key findings**:

- **A and B share identical Direction Availability** (53.5% available / 46.5%
  no-common-direction, [#2497](compass-direction-availability-product-decision.md)'s
  972-case matrix) — they differ *only* in product interpretation (error vs.
  first-class result), not in the underlying calculation. B is what
  `develop` actually runs today; A is retained here purely as the comparison
  baseline B superseded.
- **A new synthetic measurement performed for this audit** (§11.3) found
  Option D's Direction Availability, if annual lucky directions were used
  alone, is **97.5% (948/972)** — far higher than the strict intersection.
  This number is reported honestly per the Framework's Axis 3 evidence
  method, but high availability alone does not make D a good option (§9,
  §21): D directly reverses an existing, explicit Runtime Contract
  prohibition (`compass-mvp-runtime-contract.md` Section 5: "Compassは年盤
  単独結果を出力として採用しない") and weakens the MONTH time model that is
  Compass's defining feature (`compass-product-contract.md` Section 4).
- **Option C's Direction Availability is NOT quantifiable within this
  audit's constraints.** Unlike annual-only (a public function,
  `annual_lucky_directions()`), monthly-only lucky directions exist only as
  an unexposed internal variable inside `planned_visit_lucky_directions()`
  (`backend/temples/domain/kyusei.py:239-278`). Measuring it honestly would
  require either modifying `kyusei.py`'s public interface (prohibited by
  this task) or reimplementing its internal logic outside the
  call-the-unmodified-function-directly methodology #2497 established and
  this Framework's Axis 3 evidence source requires. This is recorded as an
  open item, not silently worked around (§11.2, §27).
- **Option E remains `NOT QUANTIFIABLE UNTIL SCORE CONTRACT EXISTS`**, per
  the Framework's own instruction (§9 of the task, §29 Option E limitation)
  — no weights or thresholds are invented here.
- All five options score **Ranking Isolation: NONE** (no option touches
  Layer D) and **Concierge Isolation: NO CONCIERGE IMPACT is achievable for
  every option**, provided the Layer-B-only implementation discipline
  #2499 already established is followed (§17).

No production code, Contract, Runtime Contract, Recommendation Ranking,
Concierge behavior, or Analytics instrumentation is changed by this
document. The one net-new artifact is a single freshly-computed number
(Option D's 97.5%, §11.3), produced the same way #2496/#2497 produced their
numbers — a scratchpad-only script calling unmodified production `kyusei.py`
functions, never committed to the repository.

---

## 2. Decision Question

> Of the five Direction Logic options fixed by the Framework's Next Product
> Decision Gate (#2502 §22), which — if any — should the Mother Ship adopt
> as Compass's Direction Logic, and under which Product Promise (A/B/C,
> #2502 §12)?

This document answers with a **PROPOSED** recommendation and an
**Alternative**, both explicitly conditional where the evidence requires it
(§23–§25). It does not itself decide.

---

## 3. Framework Authority (#2502)

[compass-product-logic-evaluation-framework.md](../product/compass-product-logic-evaluation-framework.md)
(merged into `develop` as commit `336932e6`, PR
[#2502](https://github.com/etsu33/jinja_app/pull/2502)) is the sole source
of vocabulary, axes, evaluation methods, and metric definitions used below.
Nothing in that document is changed, added to, or reinterpreted by this
audit:

| Framework element | Used as-is from #2502 |
|---|---|
| Runtime Reliability / Direction Availability / Recommendation Availability / Product Value (four distinct concepts) | §7–§10 |
| `no_common_direction` Technical State vs. Product Result | §11 |
| Product Promise Candidates A/B/C | §12 |
| Ten Evaluation Axes | §14 |
| Evaluation Method per axis | §15 |
| Quantitative Metric definitions (Reliability Rate, Direction Availability Rate, Recommendation Availability Rate, Recommendation CTR) | §16 |
| Known Availability Characteristic (46.5%) | §17 |
| Concierge Boundary | §18 |
| Recommendation Ranking Boundary | §19 |
| Analytics Boundary | §20 |

No **FRAMEWORK DEFECT** was found while performing this comparison — the
Framework's axes and methods were sufficient to evaluate all five options
without needing to be extended, narrowed, or reinterpreted per-option. Where
the Framework leaves a question genuinely open (e.g. it does not itself
prescribe how to measure a not-yet-implemented option's availability), this
document says so explicitly rather than inventing a method (§11.2).

---

## 4. Current Baseline

**Current `develop` implementation is Option B** (§7), not Option A.
Verified against current code with no drift since #2502
(`git diff 41cba8d6 develop -- backend/ apps/web/` empty, `git log -1
--oneline` = `336932e6`):

```
backend/temples/services/compass_recommendation_orchestrator.py:49-54
  STATE_INVALID_PURPOSE               = "invalid_purpose"
  STATE_DIRECTION_FILTER_UNAVAILABLE  = "direction_filter_unavailable"
  STATE_NO_COMMON_DIRECTION           = "no_common_direction"
  STATE_DIRECTION_ZERO_CANDIDATES     = "direction_zero_candidates"
  STATE_EVIDENCE_ZERO_CANDIDATES      = "evidence_zero_candidates"
  STATE_RECOMMENDATION_SUCCESS        = "recommendation_success"
```

**Known Algorithmic Availability** (re-cited, not recomputed, per #2502
§17 and this Framework's own instruction not to treat it as a verdict):

```
TOTAL CASES: 972 (9 honmei stars × 12 solar-month buckets × 9 years, 2022-2030)
Direction available:    520 / 972 = 53.5%
No common direction:    452 / 972 = 46.5%
```

Source: [compass-direction-availability-product-decision.md](compass-direction-availability-product-decision.md)
(#2497) §6, run against unmodified production `kyusei.py`. This baseline
applies identically to Option A and Option B (§11.1) — they share the exact
same calculation; only the product interpretation of the empty-intersection
case differs.

**KNOWN AVAILABILITY CHARACTERISTIC, restated per the Framework's own
constraint (#2502 §17, and this task's §6):** 46.5% is not evaluated here as
"good" or "bad." It is one input to the Product Promise Alignment axis
(§13), whose verdict depends on which Promise (A/B/C) governs — a decision
this document does not make.

---

## 5. Product Promise Dependencies

Per #2502 §12, three Product Promise candidates remain comparable, not
ranked:

- **Promise A — Strict Common Direction**: a direction is shown only when
  annual and monthly both support it; no-common-direction is itself valid
  information.
- **Promise B — Actionable Monthly Direction**: the user gets something
  actionable this month; the calculation method is not fixed by the Promise
  itself.
- **Promise C — Direction-to-Shrine Guidance**: the month's direction is an
  entry point that guides the user all the way to a selectable shrine
  candidate.

This audit does not select one. However, per §28 of the task, the
Recommended/Alternative options below are **not Promise-independent**, and
this document does not hide that dependency (§25).

---

## 6. Option A — Strict Intersection

```
annual lucky directions ∩ monthly lucky directions
intersection empty -> "no common direction" (framed as an unavailable/error result)
```

This is the current calculation logic **combined with the pre-#2498
product framing** — i.e., what `develop` looked like before #2499 shipped.
It is **not** the current implementation (that is Option B, §7); it is
retained here as Option B's direct comparison baseline, per the task's own
instruction (§7 of the task) to keep A and B distinguishable.

- **Direction Availability**: 53.5% (520/972), identical to B (§4, §11.1) —
  the calculation is unchanged.
- **Recommendation Availability**: identical to B for the same structural
  reason (§12) — Layer C/D are untouched by the interpretation change.
- **Semantic Consistency**: low. The pre-#2498 framing described a
  structurally frequent, valid outcome (46.5% of algorithmic cases) using
  language that implied technical failure or user input error
  ("計算できませんでした" / "生年月日または出発地点をご確認のうえ") — #2497
  §12 classified this **MISLEADING**.
- **User Comprehensibility**: low, for the same reason — users are told to
  retry or check their input, when neither would change a deterministic
  result (#2497 §12 point 3).
- **Determinism**: high — same input, same output, always (unchanged from
  B).
- **Concierge Isolation**: NO CONCIERGE IMPACT — no code change involved at
  all (this option requires zero changes, since it describes the
  pre-existing state).
- **Ranking Isolation**: NONE — untouched.
- **Runtime Contract Impact**: NONE (as a comparison baseline; reverting to
  it from current `develop` would itself be a Contract change, since #2498
  already canonicalized the first-class treatment — see §19).
- **Implementation Complexity**: N/A as a forward option (it is a
  hypothetical rollback of already-shipped, already-verified work, not a
  net-new build).

**GAINS**: none beyond what already exists; zero engineering cost to
"choose" since it requires no work.

**LOSES**: the MISLEADING-copy problem #2497 already identified would
persist (or be reintroduced, if read as a proposal to revert B). Loses the
already-verified production correctness of B (#2501).

**RISKS**: presenting A as a live option risks the Mother Ship believing a
genuine choice remains between A and B's *underlying availability* — it
does not; only the *framing* differs (§11.1). The only real risk A carries
is regression: reverting B back toward A would undo #2498–#2501 without new
justification.

Product Value framing preserved unchanged: A does not itself "sacrifice"
anything technical relative to B, since B *is* A's calculation with better
product interpretation, not a different calculation.

---

## 7. Option B — First-Class No-Direction (current `develop`)

```
Calculation: identical to A (annual ∩ monthly, kyusei.py unmodified)
Interpretation: intersection empty -> STATE_NO_COMMON_DIRECTION,
  a legitimate, non-error, first-class Compass result
  (compass-product-contract.md Section 2.1, #2498/#2499/#2500/#2501)
```

**This is the current, live, production-verified implementation.** Traced
directly against current `develop` (§4):

```
kyusei.py: unmodified since before #2499 (Layer A)
compass_runtime.py: NoCommonDirectionResult() marker (Layer B)
compass_recommendation_orchestrator.py: STATE_NO_COMMON_DIRECTION = "no_common_direction" (Layer B)
CompassClient.tsx: neutral copy, "今月は年盤と月盤で重なる方位がありません" (Layer E)
compass-posthog-query-contract.md: VALID_NO_DIRECTION bucket, distinct from ERROR (Layer F)
```

Production-verified: [compass-no-direction-production-verification.md](compass-no-direction-production-verification.md)
(#2501) confirmed 4 known-QA `compass_result` events all classified as
`no_common_direction`, zero collapse into `direction_filter_unavailable`.

- **Direction Availability**: 53.5% (520/972) — **identical to A**, stated
  honestly per the task's own instruction (§7 of the task) not to invent a
  different number.
- **Recommendation Availability**: identical to A — `no_common_direction`
  still produces `recommendations: []` (Product Contract Section 2.1-5,
  Shrine Recommendation boundary remains explicitly OPEN, unresolved by
  this audit).
- **Semantic Consistency**: high — the copy now matches the technical
  reality ("年盤と月盤がともに支持する方位が今月はなかった、という結果
  です"), not an implied failure.
- **User Comprehensibility**: high relative to A — no retry-suggestion, no
  input-blame; #2497's MISLEADING finding is resolved for the framing
  layer (the underlying 46.5% frequency itself is unchanged — comprehension
  of *why it happens so often* is a separate, still-open question, §21).
- **Determinism**: high, identical to A.
- **Concierge Isolation**: **NO CONCIERGE IMPACT**, confirmed directly —
  `kyusei.py` (`annual_lucky_directions`/`planned_visit_lucky_directions`)
  is unmodified; `backend/temples/api_views_concierge.py:30,563-565` still
  calls these same functions directly and is unaffected.
- **Ranking Isolation**: NONE — Layer D untouched.
- **Runtime Contract Impact**: already absorbed — `CompassDirectionRuntime`'s
  Schema (`compass-mvp-runtime-contract.md` Section 5) was not changed to
  ship this; only the *interpretation* of one already-existing return path
  (`None`) needed a distinct state name downstream, in Layer B.
- **Implementation Complexity**: already paid, zero incremental cost to
  "select" this option going forward.

**GAINS**: resolves #2497's MISLEADING classification without touching
`kyusei.py`, Recommendation Ranking, or Concierge. Lowest-risk of all five
options because it requires no new work.

**LOSES**: does not raise the underlying 46.5% no-common-direction
frequency — a user who wants *a direction, any direction* still gets none
in roughly the same share of cases as before. Framing improved; the
frequency itself did not change.

**RISKS**: none specific to adopting B, since it is already adopted and
already verified in production (#2501). The residual risk is entirely
external to this option: the OPEN Shrine Recommendation boundary
(§4.3/§9 of the Framework) remains unresolved regardless of which Direction
Logic option governs.

---

## 8. Option C — Monthly Fallback

```
annual ∩ monthly non-empty: use intersection
annual ∩ monthly empty:    use monthly lucky directions alone (fallback)
```

**DO NOT IMPLEMENT. Concept evaluation only**, per the task's explicit
instruction.

- **Direction Availability**: **NOT QUANTIFIABLE within this audit.**
  Monthly-only lucky directions (`monthly_lucky`, `kyusei.py:264-273`) are
  computed as an internal local variable inside
  `planned_visit_lucky_directions()` and are never returned by any public
  function — only their *intersection* with annual (`combined`) is exposed.
  Recovering `monthly_lucky` alone would require either (a) modifying
  `kyusei.py`'s public interface to expose it (prohibited by this task), or
  (b) reimplementing the internal calculation independently of the
  production function (which would violate the same methodology principle
  #2497 §5 established and this Framework's Axis 3 evidence source
  requires: call the unmodified production function directly, do not
  re-derive the algorithm). This is recorded as an open item for a future,
  narrowly-scoped measurement PR (§27), not worked around here.
- **Recommendation Availability**: not quantifiable for the same reason
  (depends on Direction Availability as an upstream input).
- **Semantic Consistency**: medium. "This month's direction, standing
  alone, without annual agreement" is an explainable concept, but it
  changes what "the direction" *means* — from "the direction both signals
  agree on" to "the direction this month's signal alone supports." This is
  a real redefinition of the underlying claim, not merely a presentation
  change (contrast with B, §7).
- **User Comprehensibility**: medium — requires disclosing that a fallback
  occurred (or not disclosing it, which risks misrepresenting signal
  strength, per #2497 §24 point 2) — a new UX decision this document does
  not make.
- **Determinism**: high — still a pure function of birthdate + target_date,
  no randomness introduced.
- **Concierge Isolation**: **NO CONCIERGE IMPACT is achievable**, provided
  the fallback branching is implemented entirely inside
  `compass_runtime.py` (Layer B) without changing `kyusei.py`'s public
  signatures or return contracts — the same discipline #2499 already
  established. If a future implementation instead changed
  `planned_visit_lucky_directions()`'s own return contract, it would
  become **SHARED FUNCTION RISK** (`api_views_concierge.py:563` depends on
  this exact function).
- **Ranking Isolation**: NONE — Layer D untouched; C only changes which
  direction(s) reach Layer C's candidate-filtering step.
- **Runtime Contract Impact**: **YES** — `CompassDirectionRuntime.
  calculationMethod` (`compass-mvp-runtime-contract.md` Section 5, currently
  the single fixed value `"annual_monthly_kyusei_v1"`) would need a new
  value (e.g. `"monthly_only_fallback_v1"`) or an ambiguity the Contract
  would need to explicitly accept. Product Contract Section 2's Promise
  wording would also need revision to describe the fallback behavior
  honestly.
- **Implementation Complexity**: LOW–MEDIUM. Confined to
  `compass_runtime.py` if the Concierge-isolation discipline above is
  followed; `kyusei.py` unchanged. New UI branch for fallback-disclosure
  decision; new Contract language; likely 1-2 new backend tests plus
  Frontend copy/state tests.

**GAINS**: aligns with Compass's own MONTH time model
(`compass-product-contract.md` Section 4) more directly than D does, since
it keeps the month-specific signal as the fallback rather than discarding
it. Plausibly raises Direction Availability relative to A/B (direction —
not magnitude — inferred; magnitude is the open item above).

**LOSES**: the annual signal's corroboration is dropped in fallback cases —
the resulting direction carries less agreement-based confidence than the
intersection did, and this document does not know how much more available
it becomes to say whether that trade is favorable.

**RISKS**: shipping C without first resolving the availability-measurement
gap above would mean adopting a Runtime Contract change and new UX surface
area to solve a problem (46.5% no-direction) whose actual improvement is
unverified until measured.

---

## 9. Option D — Annual Fallback

```
annual ∩ monthly non-empty: use intersection
annual ∩ monthly empty:    use annual lucky directions alone (fallback)
```

**DO NOT IMPLEMENT. Concept evaluation only.**

- **Direction Availability**: **MEASURED for this audit** (§11.3), because
  unlike monthly-only, `annual_lucky_directions()` is already a public,
  standalone production function (`kyusei.py:191-223`) that can be called
  directly without reimplementing anything:

  ```
  TOTAL CASES: 972 (same 9×12×9 grid as the Option A/B baseline)
  Annual-only available:  948 / 972 = 97.5%
  Annual-only empty:        24 / 972 = 2.5%
  ```

  Concentrated almost entirely in honmei stars 1 and 9 (12/108 each; all
  other seven stars: 0/108 empty). See §11.3 for the full breakdown and
  methodology.

- **Recommendation Availability**: not empirically measured (same
  structural gap as every other option, §12) — but the Direction
  Availability finding above at minimum establishes that *if* annual-only
  were adopted, the population reaching Layer C would be far larger than
  under A/B/C.
- **Semantic Consistency**: **weakest of the four fallback/current options**.
  Using the year-level signal alone as "this month's direction" directly
  contradicts the month-specificity claim in Compass's own Product Promise
  (#2502 §12 Candidate B: "actionable this month") and in the current
  documented Promise's structure. It also means the fallback triggers
  *more* than 10x as often as C's fallback would need to justify (2.5%
  empty vs. presumably higher for monthly, unmeasured) — meaning under D,
  the "fallback" is close to becoming the primary path whenever the strict
  intersection is empty, which is 46.5% of the time.
- **User Comprehensibility**: medium-low — explaining "this direction is
  based on the whole year, not this month" when the product's entire time
  model is MONTH (`compass-product-contract.md` Section 4) is a harder
  explanation to keep consistent with the product's own stated identity
  than C's monthly-fallback framing.
- **Determinism**: high, same as all options.
- **Concierge Isolation**: **NO CONCIERGE IMPACT achievable**, same
  Layer-B-confinement condition as C.
- **Ranking Isolation**: NONE.
- **Runtime Contract Impact**: **YES, and heavier than C.**
  `compass-mvp-runtime-contract.md` Section 5 does not merely need a new
  `calculationMethod` value — it explicitly, currently **prohibits** using
  an annual-only result as Compass output: *"既存
  `direction_reference.py:59` `build_direction_reference()`が
  `calculationMethod == "annual_monthly_kyusei_v1"`のみを受理する
  （年盤単独の`"annual_kyusei_v1"`を拒否する）という既存の「grounded
  inputsのみ」契約と整合させるため、Compassも年盤単独結果を出力として
  採用しない"* (Section 5, verified verbatim against current `develop`).
  Adopting D means **reversing this explicit prior decision**, not merely
  extending it.
- **Implementation Complexity**: LOW–MEDIUM at the code level (similar
  scope to C — `compass_runtime.py`-confined, `kyusei.py` unchanged), but
  **carries the largest documentation/contract-reversal burden** of any
  fallback option, since it requires explicitly retracting Section 5's
  prohibition rather than extending an open area.

**GAINS**: by far the highest measured Direction Availability of any option
in this document (97.5%) — nearly eliminates the no-common-direction
outcome.

**LOSES**: the month-specificity that is Compass's defining product
identity (§4 of the Product Contract). Per the task's explicit instruction
(§10 of the task) not to credit an option solely for raising availability —
**this document does not conclude D is favorable because of the 97.5%
figure alone.** What is lost — an explicit, already-made product decision
(no annual-only output) and the MONTH time model's centrality — is
material and must be weighed by the Mother Ship, not resolved by the
availability number.

**RISKS**: the largest Contract-reversal burden of the four non-A options;
highest risk that "we found a number that looks good" substitutes for a
genuine Product Promise decision, which is exactly the failure mode this
Framework was built to prevent (#2502 §1).

---

## 10. Option E — Weighted Score Model

```
Conceptual only, not implemented, no weights proposed:
  annual ∩ monthly agreement -> strongest signal
  monthly only               -> medium signal
  annual only                -> weaker signal
```

**DO NOT IMPLEMENT. Architecture-level comparison only. No score formula,
weights, or thresholds are proposed.** This concerns direction-confidence
scoring only — not Recommendation Ranking, a distinct concern
(`compass-product-contract.md` Section 6 Authority boundary; §18 below).

- **Direction Availability**: **QUALITATIVE ONLY / NOT QUANTIFIABLE UNTIL
  SCORE CONTRACT EXISTS**, per the task's explicit instruction (§29 of the
  task) and the Framework's own prohibition on fabricated metrics (#2502
  §16 Product Value, §21). Qualitatively, a score model's availability
  would be the union of A/B/C/D's underlying signal availability (annual
  ∩ monthly, monthly alone, annual alone), so it would exceed all of them
  — but assigning a number without a defined confidence threshold would be
  inventing precision this document does not have.
- **Recommendation Availability**: same qualitative-only status.
- **Semantic Consistency**: **highest of the five options, if implemented
  well** — moving from a binary "direction exists / does not" to an
  explicit confidence gradient can make the *reason* for a weaker or
  stronger recommendation more legible, provided the UI never overstates
  the confidence gradient as personalized certainty (Product Contract
  Section 9's prohibition on deterministic future-outcome claims applies
  equally to confidence language).
- **User Comprehensibility**: **most demanding of the five** — requires a
  wholly new Presentation Authority decision (how to render confidence
  without implying precision the calculation doesn't have) with no existing
  precedent in the current UI.
- **Determinism**: high — a score model over deterministic inputs remains
  deterministic; no randomness is introduced.
- **Concierge Isolation**: **SHARED FUNCTION RISK is highest for this
  option among the five**, exactly as #2497 §21 already found for its
  structurally identical Option D: the temptation to change `kyusei.py`'s
  own output shape (to carry confidence data) is strongest here, and doing
  so would directly risk `api_views_concierge.py:563`'s consumers
  (`direction_reference.py`'s current dict-shape assumptions).
- **Ranking Isolation**: NONE, by design constraint (§18) — but this is the
  option where **RANKING ISOLATION FAILURE is easiest to accidentally
  trigger**, because a "confidence score" is conceptually adjacent to a
  "ranking weight." Any future implementation PR must explicitly keep
  Compass Runtime Authority's confidence scoring (Layer B) separate from
  Recommendation Authority's candidate scoring (Layer D) — this document
  flags the boundary, does not implement either side of it.
- **Runtime Contract Impact**: **largest of all five options.**
  `CompassDirectionRuntime`'s Schema (`referenceDirections: string[]`,
  `compass-mvp-runtime-contract.md` Section 5) would need a structural
  rewrite (e.g. `{direction: string, confidence: "high"|"medium"|"low"}[]`),
  not merely a new enum value.
- **Implementation Complexity**: **highest of all five** — Schema
  redesign, `compass_direction_filter.py` extension (currently accepts a
  flat `Sequence[str]`), new Presentation Authority logic, and the
  Concierge-isolation risk above all compound.

**GAINS**: theoretically the most information-rich and semantically
flexible design; could subsume C and D as special cases of a single model.

**LOSES**: simplicity, determin-appearing UX (a confidence gradient is
harder to present without implying false precision, contradicting Product
Contract Section 9's non-deterministic-claim principle), and the low-risk
Concierge isolation every other option can achieve more easily.

**RISKS**: highest engineering cost, highest Concierge shared-function
risk, highest chance of the Ranking-boundary being blurred by a future
implementer, and a Runtime Contract rewrite whose blast radius is larger
than any other option's. Per the task's explicit instruction (§29), this
document does not manufacture a number to make E look more or less
attractive than this qualitative picture supports.

---

## 11. Direction Availability Comparison

### 11.1 A vs. B (identical, by construction)

```
A: 520/972 = 53.5% available, 452/972 = 46.5% empty
B: 520/972 = 53.5% available, 452/972 = 46.5% empty  (same calculation, different interpretation)
```

### 11.2 C (monthly fallback) — NOT QUANTIFIABLE

`monthly_lucky` (`kyusei.py:264-273`) is a local variable inside
`planned_visit_lucky_directions()`, never returned. No public function
exposes "monthly lucky directions alone." Quantifying it honestly, without
violating either the "don't modify `kyusei.py`" constraint (task §31) or
the "call the unmodified function directly, don't re-derive the algorithm"
methodology (#2497 §5, inherited by this Framework's Axis 3 evidence
source, #2502 §15), is **not possible within this audit**. This is recorded
as an explicit open item for §27's Future PR Plan, not silently
approximated.

### 11.3 D (annual fallback) — MEASURED (new for this audit)

**Methodology** (same discipline as #2496/#2497 — no algorithm
reimplementation, unmodified production function called directly, no real
user data, synthetic birthdates only, script never committed to the
repository):

```
Function called: backend/temples/domain/kyusei.py::annual_lucky_directions(birthdate, today=target_date)
Grid: 9 honmei stars (synthetic birthdates, one representative per num, June 15 births 1975-1983)
      × 12 solar-month-bucket representative dates (same boundaries as _solar_month_index())
      × 9 years (2022-2030)
      = 972 cases (same grid shape as the #2497 baseline, for direct comparability)
Environment: django.conf.settings.configure(USE_TZ=True, TIME_ZONE="Asia/Tokyo"), no DB access
Script location: scratchpad only (/private/tmp/...), not committed to this repository
```

**Result**:

```
TOTAL CASES: 972
AVAILABLE (annual-only, non-empty): 948 (97.5%)
EMPTY (annual-only, empty):          24 (2.5%)
```

**By honmei star** (108 cases each):

| Honmei | Empty | Available rate |
|---|---|---|
| 1 | 12/108 | 88.9% |
| 2 | 0/108 | 100.0% |
| 3 | 0/108 | 100.0% |
| 4 | 0/108 | 100.0% |
| 5 | 0/108 | 100.0% |
| 6 | 0/108 | 100.0% |
| 7 | 0/108 | 100.0% |
| 8 | 0/108 | 100.0% |
| 9 | 12/108 | 88.9% |

The empty cases concentrate entirely in honmei stars 1 and 9 (24/24) — a
purely algorithmic/structural pattern (five-yellow and honmei-star exclusion
overlapping with the taisai-direction exclusion for those two stars in
specific years), not a claim about astrological validity, consistent with
the Framework's and #2497's shared Interpretation Boundary (#2497 §11): this
measures algorithmic availability only, not real user distribution,
satisfaction, or accuracy.

**Interpretation boundary (restated)**: like #2497's 46.5% figure, this
97.5% is a deterministic-grid characteristic of the algorithm, not a
production/user-population statistic, and per §9 above it is **not**, by
itself, evidence that D is the better option.

### 11.4 E — NOT QUANTIFIABLE UNTIL SCORE CONTRACT EXISTS

No fabricated number is produced (§10, task §29).

### Summary table

| Option | Direction Availability | Basis |
|---|---|---|
| A | 53.5% (520/972) | #2497, re-cited |
| B | 53.5% (520/972), identical to A | #2497, re-cited |
| C | NOT QUANTIFIABLE | §11.2 — no public function exposes the needed value |
| D | 97.5% (948/972) | §11.3 — newly measured for this audit |
| E | NOT QUANTIFIABLE UNTIL SCORE CONTRACT EXISTS | §10, task §29 |

---

## 12. Recommendation Availability Comparison

No option's Recommendation Availability Rate has been empirically measured
against production traffic — this would require a new PostHog query, out
of scope for a docs-only audit (#2502 §16, task §30 Analytics Boundary).

**Structural finding, common to all five options**: Recommendation
Availability is strictly narrower than Direction Availability for every
option (#2502 §9) — having *a* direction (of any confidence) is necessary
but not sufficient for `recommendation_success`; Layer C (candidate
filtering) and Layer D (Ranking, unaffected by any option here) still
determine whether any shrine candidate survives. None of A/B/C/D/E changes
Layer C's or Layer D's logic; each only changes *how many, or which,*
direction(s) reach Layer C's filtering step. This document does not
estimate a Recommendation Availability number for any option, since doing
so for A/B (the only options with a measured Direction Availability
denominator that maps to real production behavior) would require the same
out-of-scope PostHog query, and for C/D/E it would additionally require
Direction Availability data this document does not have (C, E) or has only
as a synthetic algorithmic figure disconnected from candidate-pool data (D).

**Shrine Recommendation boundary remains OPEN for every option**
(`compass-product-contract.md` Section 2.1-5): whether a no-direction (or
low-confidence-direction) result should ever surface purpose-only shrine
recommendations is not resolved by this document, for any option A–E.

---

## 13. Promise A/B/C Alignment

| Option | Promise A (Strict Common Direction) | Promise B (Actionable Monthly) | Promise C (Direction-to-Shrine Guidance) |
|---|---|---|---|
| **A** | Full alignment (this candidate *is* what A implements), but framing (§6) undermines it | Weak — "actionable" is not guaranteed 46.5% of the time, and A's copy misrepresents that | Weak — no mechanism guarantees reaching a shrine |
| **B** | Full alignment, and framing now matches (§7) — this is the strongest current fit | Weak, same structural reason as A (calculation unchanged) | Weak, same reason as A |
| **C** | Contradicts A's core premise (no longer *requires* agreement) | Improves alignment — monthly-first fallback directly serves "actionable this month," *if* availability actually rises (unmeasured, §11.2) | Partial — direction more often present, but shrine-reachability still gated by the OPEN boundary (§12) |
| **D** | Contradicts A more severely than C (drops month-specificity, not just agreement) | Weak-to-contradictory — an annual-only "monthly" direction stretches what "actionable this month" honestly means | Partial, same caveat as C |
| **E** | Ambiguous — A assumes a binary, E assumes a gradient; would require Promise A to be reworded to admit confidence levels | Best theoretical fit, if implemented well — could surface the strongest actionable signal available at any confidence | Partial, same shrine-reachability caveat as C/D |

No option is scored as an overall winner in this table — it exists so the
Mother Ship can read the row for whichever Promise it leans toward (task
§16).

---

## 14. Semantic Consistency

Summarized from §6–§10's per-option analysis, ranked qualitatively (no
numeric score, per the Framework's method, #2502 §15):

```
B  ≈ A(calculation) > C > D > E(if implemented carelessly)
```

- **A/B**: what changes between them is exactly framing, not meaning — the
  calculation's semantics (agreement between two independent signals) is
  identical and easy to state consistently. B states it accurately; A's
  legacy copy did not (§6).
- **C**: "this month's own signal, standing alone" is a coherent, statable
  concept, but it is a *different* claim than "signals in agreement" — the
  redefinition must be disclosed, not silently substituted (§8).
- **D**: "the year's signal, standing in for this month" is the least
  internally consistent claim of the four calculation-based options,
  because it contradicts Compass's own MONTH-centric self-description
  (§9).
- **E**: potentially the *most* semantically rich (a confidence gradient
  can be more honest than a binary), but only if implemented with
  discipline — poorly implemented, it risks conflating direction-confidence
  language with recommendation-confidence language, which Product Contract
  Section 7 explicitly requires to stay separate ("方位の根拠は神社の根拠を
  代替できない").

---

## 15. User Comprehensibility

| Option | Comprehensibility summary |
|---|---|
| A | Low — misleading retry/input-blame language (#2497 §12) |
| B | High — neutral, accurate, already user-tested in production (#2501) |
| C | Medium — requires a new explanation for *why* a weaker signal is being shown, and a decision on whether to disclose the fallback at all |
| D | Medium-low — same disclosure burden as C, plus the harder task of explaining an annual signal inside a product whose whole framing is monthly |
| E | Lowest — requires the user to understand a confidence gradient with no existing UI precedent in this product |

No final copy is proposed for any option (task §18).

---

## 16. Determinism

All five options are deterministic: same birthdate + same target_date
(same honmei star, same solar-month bucket, same year) produces the same
output on every call, for every option, since none introduces randomness,
external state, or time-of-request dependence beyond the already-existing
`target_date`/`today` inputs. This holds for A/B (verified, #2497 §10),
and would continue to hold for C/D/E as architectural proposals, since each
is still a pure function of the same two inputs.

---

## 17. Concierge Isolation

Confirmed directly against current code (re-verified for this audit, no
change since #2497 §21 / #2502 §18):

```
$ grep -rln "from temples.domain.kyusei" backend --include="*.py" | grep -v test
backend/temples/api_views_concierge.py
backend/temples/services/compass_runtime.py
```

`backend/temples/api_views_concierge.py:30,563-565` calls
`annual_lucky_directions()` and `planned_visit_lucky_directions()` directly,
unchanged. Any Direction Logic option that requires changing either
function's public signature or return-value contract carries Concierge
risk.

| Option | Classification |
|---|---|
| A | NO CONCIERGE IMPACT (no change involved) |
| B | NO CONCIERGE IMPACT (confirmed in production, #2501; `kyusei.py` unmodified) |
| C | NO CONCIERGE IMPACT **achievable**, if confined to `compass_runtime.py` (Layer B); SHARED FUNCTION RISK if `kyusei.py`'s own contract is changed instead |
| D | Same conditional as C |
| E | **SHARED FUNCTION RISK is highest** among the five — a confidence-carrying Schema creates the strongest incentive to change `kyusei.py`'s own output shape, which would directly threaten `api_views_concierge.py:563`'s consumers |

**Evaluation condition, restated from the Framework (#2502 §18)**: "Compass
Product Logic change must not alter Concierge behavior." All five options
can satisfy this if Compass-specific policy stays confined to Layer B
(`compass_runtime.py`/`compass_recommendation_orchestrator.py`) — the
precedent #2499 already established and #2501 already verified in
production.

---

## 18. Recommendation Ranking Isolation

```
Recommendation Ranking change: NONE, for all five options (target condition met)
```

None of A/B/C/D/E touches `concierge_chat_ranking.py`, candidate scoring
weights, or reason-authority logic (Layer D). Each option only changes
*which* direction(s), if any, are handed to Layer C's candidate filtering —
which population of shrines Layer D ever sees — not how Layer D scores or
ranks that population.

**No RANKING ISOLATION FAILURE is found for any option**, but E carries the
highest *risk* of one being introduced by a careless future implementation
(§10, §18) — flagged explicitly as a boundary condition for any future PR,
not as a failure of this audit's five options as conceptually described.

---

## 19. Runtime Contract Impact

| Option | Product Contract change | Runtime Contract change | API schema change | Frontend state change | Analytics Contract change |
|---|---|---|---|---|---|
| A | N/A (pre-existing state; adopting it now = reverting #2498) | N/A (reverting #2498/#2499) | NO | NO | NO |
| B | NO (already current) | NO (already current) | NO | NO | NO |
| C | POSSIBLE (Promise wording re: fallback) | YES (`calculationMethod` new value, Section 5 extension) | YES | YES | POSSIBLE (`result_state` vocabulary, if a new state is introduced) |
| D | YES (Promise wording) | **YES — reverses an existing explicit prohibition** (Section 5) | YES | YES | POSSIBLE |
| E | YES (Promise itself, binary → gradient) | **YES — Schema-level rewrite** (`CompassDirectionRuntime`) | YES | YES | POSSIBLE (new properties) |

No actual Contract is changed by this document (task §31); the table
above is a comparison of *how much* future work each option would require.

---

## 20. Implementation Complexity

| Option | Backend scope | Frontend scope | Tests | Shared-code risk | DB / Migration | Analytics follow-up |
|---|---|---|---|---|---|---|
| A | N/A (revert) | N/A (revert) | N/A | NONE | NONE | NONE |
| B | Already shipped | Already shipped | Already covered | NONE (confirmed) | NONE | Already aligned (#2500/#2501) |
| C | LOW–MEDIUM (`compass_runtime.py` only, if isolated) | MEDIUM (fallback-disclosure UI decision) | New backend + frontend cases | LOW, conditional on isolation discipline | NONE | POSSIBLE new state value follow-up |
| D | LOW–MEDIUM (code) / **HIGH (contract-reversal documentation)** | MEDIUM, same as C | New backend + frontend cases | LOW, conditional on isolation discipline | NONE | POSSIBLE |
| E | HIGH (Schema rewrite, `compass_direction_filter.py` extension) | HIGH (new confidence-presentation UI) | Most new test surface of any option | **HIGHEST** | NONE | POSSIBLE new properties |

```
Complexity ranking (qualitative, no pseudo-precise scoring): B < A(as a no-op) < C ≈ D(code) < D(contract burden) < E
```

---

## 21. Gains / Losses / Risks

Consolidated from §6–§10 (required per task §23):

| Option | GAINS | LOSES | RISKS |
|---|---|---|---|
| **A** | Zero cost (already exists as a concept) | Resolved MISLEADING framing (if read as "revert to A") | Regression risk if mistaken for a live proposal |
| **B** | Resolves MISLEADING copy; zero incremental cost; production-verified | Does not raise the 46.5% no-direction frequency itself | None specific — lowest-risk option |
| **C** | Plausibly raises availability while preserving MONTH-centricity | Annual corroboration dropped on fallback; magnitude of gain unmeasured | Contract change committed before its own benefit is quantified |
| **D** | Highest measured availability (97.5%) | Month-specificity, an explicit prior Contract decision | Largest contract-reversal burden; availability number could be misread as sufficient justification alone |
| **E** | Richest semantic model; could subsume C/D | Simplicity; low-risk Concierge isolation other options get more easily | Highest engineering cost; highest Concierge shared-function risk; highest Ranking-boundary blur risk |

---

## 22. 10-Axis Comparison Matrix

Per task §33, one consolidated table, `STRONG`/`MODERATE`/`WEAK`/`HIGH RISK`
with a short rationale per cell (detailed rationale in §6–§20 above; no
numeric total is computed, per task §13's prohibition on pseudo-precision).

| Axis | A | B | C | D | E |
|---|---|---|---|---|---|
| 1. Product Promise Alignment | MODERATE (matches Promise A logic, undermined by framing) | STRONG (matches Promise A, framing now accurate) | MODERATE (better fit for Promise B, unmeasured gain) | WEAK (stretches "monthly" claim) | MODERATE (best *theoretical* fit for Promise B, unproven) |
| 2. Semantic Consistency | WEAK (MISLEADING per #2497) | STRONG | MODERATE (redefinition disclosed = consistent; undisclosed = not) | WEAK (contradicts MONTH model) | MODERATE-STRONG (if disciplined), HIGH RISK (if not) |
| 3. Direction Availability | 53.5% (measured) | 53.5% (measured, same as A) | NOT QUANTIFIABLE | 97.5% (measured, §11.3) | NOT QUANTIFIABLE |
| 4. Recommendation Availability | NOT EMPIRICALLY MEASURED | NOT EMPIRICALLY MEASURED | NOT QUANTIFIABLE | NOT EMPIRICALLY MEASURED (only a synthetic Direction proxy exists) | NOT QUANTIFIABLE |
| 5. User Comprehensibility | WEAK | STRONG (production-verified) | MODERATE | MODERATE-WEAK | WEAK (no UI precedent) |
| 6. Determinism / Reproducibility | STRONG | STRONG | STRONG | STRONG | STRONG |
| 7. Concierge Isolation | STRONG (no change) | STRONG (confirmed in production) | STRONG, conditional on Layer-B confinement | STRONG, same condition | HIGH RISK (strongest temptation to touch shared `kyusei.py` shape) |
| 8. Recommendation Ranking Isolation | STRONG (NONE) | STRONG (NONE) | STRONG (NONE) | STRONG (NONE) | MODERATE (NONE by design, but easiest to blur in a careless implementation) |
| 9. Runtime Contract Impact | NONE (as-is) | NONE (already absorbed) | MODERATE (`calculationMethod` extension) | HIGH (reverses an explicit prohibition) | HIGH (Schema rewrite) |
| 10. Implementation Complexity | N/A / LOW (revert) | NONE (already shipped) | LOW–MEDIUM | LOW–MEDIUM (code) / HIGH (contract burden) | HIGH |

---

## 23. Recommended Option

**Status: `PROPOSED — MOTHER SHIP DECISION REQUIRED`**

### RECOMMENDED OPTION: **B — Keep the current implementation (strict intersection + first-class no-direction result)**

Grounded in the Framework's own axes (#2502 §14), not preference:

- **Axis 1/2/5** (Promise Alignment, Semantic Consistency, User
  Comprehensibility): B scores STRONG on all three (§22) — it is the only
  option with zero open UX-disclosure design questions and a
  production-verified, non-misleading result (#2501).
- **Axis 7/8** (Concierge/Ranking Isolation): B is STRONG and already
  confirmed in production, not merely designed to be (§17, §18).
- **Axis 9/10** (Runtime Contract Impact, Implementation Complexity): B is
  the only option with **zero** incremental cost or Contract change,
  because it is already shipped.
- **Axis 3** (Direction Availability): B does not improve on A's 53.5%
  (§11.1) — this is the one axis where B is not the strongest performer.
  This is not concealed: adopting B as Recommended is a statement that,
  under the current evidence, resolving the *framing* problem (already
  done) outweighs the unresolved *frequency* problem (still 46.5%), absent
  a Mother Ship decision that the frequency itself must fall.

This mirrors [#2497](compass-direction-availability-product-decision.md)'s
own PROPOSED recommendation (its "Option E," this document's "Option B"),
which the Mother Ship has already, in effect, approved by way of #2498's
Decision Record and #2499's implementation — this audit's independent
axis-by-axis comparison reaches the same conclusion using the now-fixed
Framework, not by assuming the prior recommendation was correct.

---

## 24. Alternative Option

### ALTERNATIVE OPTION: **C — Monthly Fallback**

Conditions under which the Mother Ship should prefer C over B:

```
IF the Mother Ship judges the 46.5% no-common-direction rate (§4) itself
   -- not merely its framing -- to be product-unacceptable under whichever
   Promise (A/B/C) is eventually adopted,
AND the Mother Ship wants to preserve Compass's MONTH-centric identity
   (Product Contract Section 4) rather than trade it away (which D would
   require),
AND the Mother Ship accepts that C's actual availability improvement is
   currently unmeasured and unmeasurable without either a `kyusei.py`
   public-interface change or a dedicated follow-on measurement PR (§11.2,
   §27),
THEN C is the next option to formally scope.
```

D is explicitly **not** nominated as the Alternative despite its higher
measured availability (97.5%, §11.3), because it requires reversing an
existing, explicit Runtime Contract prohibition (§9, §19) and weakens
Compass's own MONTH time model more severely than C does — exactly the
kind of "availability went up, therefore it's better" reasoning the task
instructs this document not to perform (task §10, §21).

---

## 25. Decision Dependencies

Per task §28, made explicit rather than hidden:

```
IF Promise A (Strict Common Direction) is adopted:
    B is preferred — it already implements Promise A faithfully and
    accurately (§13).

IF Promise B (Actionable Monthly Direction) is adopted:
    C becomes more attractive than under Promise A, but C's own
    availability gain must be measured (§11.2, §27) before it can be
    responsibly adopted — D is a weaker fit even under Promise B, since
    "actionable this month" is stretched further by an annual-only signal
    than by a monthly-only one.

IF Promise C (Direction-to-Shrine Guidance) is adopted:
    Neither C nor D alone is sufficient — Promise C additionally requires
    resolving the OPEN Shrine Recommendation boundary
    (compass-product-contract.md Section 2.1-5), which no Direction Logic
    option in this document resolves. E's richer confidence model is the
    closest conceptual fit for guiding a user "all the way to a shrine,"
    but requires the most additional definition work (§10) before any
    quantification is possible.
```

**Overall proposed recommendation, restated**: B (§23), with C as the
conditional Alternative (§24) — this holds regardless of which Promise is
adopted, since B is the only option with zero open dependencies.

---

## 26. Mother Ship Decision Gate

Per task §34, the following remain for Mother Ship decision — this
document decides none of them:

```
1. Final Product Promise: A, B, C, or another candidate
2. Adopted Direction Logic: A (revert), B (keep, recommended here),
   C, D, or E
3. Whether no-direction remains a legitimate, permanent product state
   (independent of which Direction Logic option governs)
4. Whether a fallback (C or D) is authorized, and if so, only after
   the availability-measurement gap (§11.2 for C; §11.3's number for D,
   already available) is filled
5. Whether a score model (E) warrants a separate, dedicated Score
   Contract definition phase before any further evaluation is possible
```

---

## 27. Future PR Plan

Per task §35, derived from this audit's actual findings, not a generic
template. **Nothing below is started by this document.**

**If B is confirmed (no further Direction Logic change)**:

```
No PR required — already shipped and verified (#2498-#2501).
```

**If the Mother Ship wants to evaluate C (Monthly Fallback) further**:

```
PR-1: Measurement-only audit (docs + scratchpad script, no production
      code change) to quantify monthly-only Direction Availability.
      Requires deciding, as a preliminary sub-question, whether to:
        (a) expose monthly_lucky via a new, additive, read-only public
            function in kyusei.py (a Concierge-safe, backward-compatible
            addition — but still a production code change, requiring its
            own review), or
        (b) accept a documented reimplementation risk and reproduce the
            internal calculation in an audit-only script, explicitly
            flagged as divergence-risk-bearing.
      This audit does not choose between (a) and (b) — that choice itself
      requires a decision this document does not make.

PR-2: Runtime Contract update (docs-only) — calculationMethod vocabulary
      extension, Product Promise wording revision.

PR-3: Backend implementation, compass_runtime.py-confined per §17's
      isolation condition, kyusei.py unmodified.

PR-4: Frontend UI/copy for the fallback-disclosure decision (§8).

PR-5: Analytics Contract alignment (only if a new result_state value is
      introduced) + production verification, following the #2499→#2501
      precedent.
```

**If the Mother Ship wants to evaluate D (Annual Fallback) further**:

```
PR-1: Product/Runtime Contract audit dedicated to reversing
      compass-mvp-runtime-contract.md Section 5's existing annual-only
      prohibition -- this must be its own reviewed decision, not folded
      into an implementation PR, given the magnitude of reversing an
      explicit prior Decision Record.
PR-2 onward: same shape as C's PR-3/4/5 above, once PR-1 is resolved.
```

**If the Mother Ship wants to evaluate E (Score Model) further**:

```
PR-1: A dedicated Score Contract definition PR (docs-only) -- weights,
      confidence-tier boundaries, and Presentation Authority rules for
      displaying confidence without overstating precision (Product
      Contract Section 9). No quantification of Direction Availability is
      possible before this exists (§10, §29 of the task).
PR-2 onward: Schema redesign, compass_direction_filter.py extension,
      Concierge shared-function-risk mitigation plan (§17) reviewed
      explicitly before implementation, given E's HIGH RISK classification
      on Axis 7.
```

This split is derived from this audit's own findings and is not a
confirmed implementation plan; the Mother Ship's actual decision (§26)
determines which branch, if any, is pursued.

---

## 28. Non-goals

This audit does **not**:

- Select a final Product Promise (A, B, or C)
- Adopt a Direction Logic option as final (the Recommended/Alternative in
  §23/§24 are PROPOSED, not decided)
- Implement any fallback or score model
- Change `kyusei.py`, `compass_runtime.py`,
  `compass_recommendation_orchestrator.py`, or any other production file
- Change the Product Contract, Runtime Contract, or Analytics Contract
- Change Recommendation Ranking (`concierge_chat_ranking.py`,
  `concierge_chat_candidates.py`, `build_chat_recommendations`)
- Change Concierge behavior or `api_views_concierge.py`
- Execute any new production PostHog query (the one new artifact in this
  document, §11.3, is a synthetic algorithmic measurement against
  unmodified `kyusei.py`, not a production data query)
- Change PostHog configuration, add dashboards, or add analytics events/
  properties
- Resolve the OPEN Shrine Recommendation boundary
  (`compass-product-contract.md` Section 2.1-5)
- Touch Premium or Personal Continuity in any way

---

## 29. Verification

```
$ git -C /Users/morietsu/Developer/jinja_app diff --check
(no output = no whitespace errors)
```

- **#2502 Framework unchanged**: confirmed — this document only reads
  `compass-product-logic-evaluation-framework.md`; `git diff` against
  `develop` shows zero changes to any file under `docs/product/`.
- **All five options evaluated on the same ten axes**: confirmed, §22.
- **Option A/B known availability matches #2497**: confirmed verbatim,
  520/972 = 53.5% / 452/972 = 46.5% (§4, §11.1).
- **Option D's newly-measured availability uses the same 9×12×9
  methodology as #2497**, calling the unmodified production
  `annual_lucky_directions()` function directly, no DB access, script not
  committed (§11.3) — reproducibility script summary included above;
  actual script lives only in the session scratchpad, per the same
  practice #2496/#2497 followed.
- **Option C has no fabricated metric**: confirmed — explicitly recorded
  as NOT QUANTIFIABLE with a stated structural reason (§11.2), not silently
  skipped or estimated.
- **Option E has no fabricated metric**: confirmed — QUALITATIVE ONLY /
  NOT QUANTIFIABLE UNTIL SCORE CONTRACT EXISTS (§10, §11.4).
- **Concierge boundary re-confirmed against current code**: `grep`
  re-executed for this audit (§17), same two call sites as #2497/#2502,
  no drift.
- **Ranking isolation re-confirmed**: no option's description touches
  `concierge_chat_ranking.py`/`concierge_chat_candidates.py` (§18).
- **No production code diff**: this branch contains exactly one new file
  (§30 below).
- **No PII used**: the one new measurement (§11.3) uses only synthetic,
  non-real birthdates (June 15, years 1975-1983), the same practice
  #2496/#2497 established; no real user data, coordinates, or free text
  was read or referenced anywhere in this audit.

**pytest**: not executed — this is a docs-only change with no production
code modification; no new production test coverage is required (task §36).
No pre-push hook output to report, since no push has occurred as of
writing this section (see §26/final step of the task for the actual
push/PR sequence).

---

## Diff Scope Gate

```
$ git status --short
?? docs/audit/compass-direction-logic-product-decision.md

$ git diff --stat
(untracked, 1 file)

$ git diff --name-only
(none — untracked, not yet staged)
```

Exactly one new file, under `docs/audit/`, matching repo convention (see
`docs/product/README.md`'s existing pattern of pairing `docs/product/`
canonical contracts with `docs/audit/` decision records). No existing file
is modified. The synthetic measurement script used for §11.3 lives only in
this session's scratchpad directory and is never staged or committed, per
the same practice #2496/#2497 followed.
