> **Status: `DECIDED — MOTHER SHIP PRODUCT DIRECTION`**
>
> This document is the Product Decision Record for Compass's Direction
> Logic and Product Promise, closing the evaluation chain
> ([#2496](../audit/compass-direction-filter-unavailable-root-cause.md),
> [#2497](../audit/compass-direction-availability-product-decision.md),
> [#2498](compass-product-contract.md) Section 2.1,
> [#2502](compass-product-logic-evaluation-framework.md),
> [#2503](../audit/compass-direction-logic-product-decision.md),
> [#2504](../audit/compass-direction-logic-missing-evidence.md),
> [#2505](../audit/compass-monthly-direction-calculation-contract.md),
> #2506,
> [#2507](../audit/compass-monthly-fallback-availability.md)).
>
> **Final Product Promise: B — Actionable Monthly Direction.**
> **Final Direction Logic: Option C — Monthly Fallback.**
> **Fallback: ADOPTED, type MONTHLY (not annual).**
> **Option E (Weighted Score Model): deferred as OPTIONAL FUTURE EVOLUTION,
> not required for this decision.**
>
> This document is a **decision record**, not an implementation. It
> selects the Promise and Direction Logic and inventories the Contract/UI/
> Analytics changes a future implementation sequence would need — it does
> not perform any of them. No production code, Product Contract, Runtime
> Contract, Recommendation Ranking, Concierge behavior, or Analytics
> instrumentation is changed by this document. docs-only.

---

## 1. Decision Status

```
DECIDED — MOTHER SHIP PRODUCT DIRECTION
```

Not PROPOSED. This document is the decision gate the entire audit chain
(#2496→#2507) was built toward, per
[#2502](compass-product-logic-evaluation-framework.md) §22's own Next
Product Decision Gate and [#2507](../audit/compass-monthly-fallback-availability.md)
§29's `A — READY FOR MOTHER SHIP PRODUCT DECISION` readiness
classification.

---

## 2. Decision Summary

| Decision item | Result |
|---|---|
| Final Product Promise | **B — Actionable Monthly Direction** |
| Final Direction Logic | **C — Monthly Fallback** |
| Fallback adopted | **YES, type MONTHLY** |
| Option E | **Deferred — OPTIONAL FUTURE EVOLUTION, not required** |
| Direction Availability (selected logic) | **96.9% (942/972)** |
| `no_common_direction` future role | Retained, narrowed to the 3.1% residual (§20) |
| Implementation | **NOT performed by this document** (§27) |

---

## 3. Evidence Base

All figures below are re-cited, not recomputed, from the merged audit
chain — no contradiction was found between any two documents' figures
during this review.

| Source | What it established |
|---|---|
| [#2496](../audit/compass-direction-filter-unavailable-root-cause.md) | `direction_filter_unavailable` root cause = empty annual∩monthly intersection; `A — EXPECTED FAIL-SAFE`, not a defect |
| [#2497](../audit/compass-direction-availability-product-decision.md) | 972-case deterministic matrix (9 honmei × 12 solar-month buckets × 9 years, 2022–2030): 520/972 (53.5%) available, 452/972 (46.5%) no-common-direction |
| [#2498](compass-product-contract.md) Section 2.1 | `no_common_direction` canonical Decision: first-class, non-error result |
| [#2502](compass-product-logic-evaluation-framework.md) | Vocabulary, ten evaluation axes, evaluation methods, Product Promise candidates A/B/C — used as-is below, unchanged |
| [#2503](../audit/compass-direction-logic-product-decision.md) | First five-option comparison (A/B/C/D/E under this decision's naming); recommended keeping B, C as conditional Alternative pending its own availability gap |
| [#2504](../audit/compass-direction-logic-missing-evidence.md) | Reproduced Option D at 97.5% (948/972); found Option C not quantifiable without a helper; itemized Option E's 15 missing contract fields |
| [#2505](../audit/compass-monthly-direction-calculation-contract.md) | Defined the safe extraction boundary (public domain helper) for the monthly-only calculation |
| #2506 | Implemented `monthly_lucky_directions()` in `kyusei.py` (behavior-preserving refactor, merged) |
| [#2507](../audit/compass-monthly-fallback-availability.md) | Quantified Option C: 942/972 (96.9%) available; 520 strict + 422 fallback-recovered (93.4% of the 452 strict-empty cases) + 30 still unavailable (3.1%) |

No prior audit's figures are redefined here. This document uses:

```
Option B Direction Availability: 53.5%
Option C Direction Availability: 96.9%  (520 strict + 422 fallback-recovered)
Option D Direction Availability: 97.5%
Option E Direction Availability: N/A (score contract not defined)

Option C fallback recovery rate:  93.4%  (422 / 452)
Option C residual unavailable:     3.1%  ( 30 / 972)
```

---

## 4. Product Promise Candidates

Per [#2502](compass-product-logic-evaluation-framework.md) §12, used
as-is, not redefined:

- **Promise A — Strict Common Direction**: a direction is shown only when
  annual and monthly charts agree; no-common-direction is itself valid
  information.
- **Promise B — Actionable Monthly Direction**: the user receives
  something actionable this month; the exact calculation method is not
  fixed by the Promise's own definition.
- **Promise C — Direction-to-Shrine Guidance**: the month's direction is
  an entry point that guides the user all the way to a selectable shrine
  candidate.

---

## 5. Direction Logic Candidates

Per [#2503](../audit/compass-direction-logic-product-decision.md)/[#2507](../audit/compass-monthly-fallback-availability.md),
used as-is:

- **Option B — Strict Intersection + First-Class No-Direction**: current
  `develop` implementation. annual∩monthly; empty intersection is a
  legitimate, non-error result.
- **Option C — Monthly Fallback**: annual∩monthly when non-empty;
  otherwise, monthly-only lucky directions.
- **Option D — Annual Fallback**: annual∩monthly when non-empty;
  otherwise, annual-only lucky directions.
- **Option E — Weighted Score Model**: a confidence-gradient model over
  annual/monthly signals; no score contract exists (§14).

---

## 6. Fixed Evaluation Criteria

Per [#2502](compass-product-logic-evaluation-framework.md) §14, the ten
axes are used unchanged, mapped to this task's own decision-principle list
(§4 of the authorizing task, a re-statement of the same ten concerns, not
a new axis set):

```
1. Product Promise Alignment      (= Product Value or Promise fit)
2. Semantic Consistency
3. Direction Availability
4. Recommendation Availability
5. User Comprehensibility
6. Determinism / Reproducibility
7. Concierge Isolation
8. Recommendation Ranking Isolation
9. Runtime Contract Impact
10. Implementation Complexity     (= Future extensibility)
```

No axis is added, removed, or reweighted for this decision. Availability
(axis 3) is one input among ten, not the deciding factor (§13).

---

## 7. Promise × Option Matrix

**Mandatory matrix (task §12)**:

| Product Promise | Option B | Option C | Option D |
|---|---|---|---|
| **Promise A** | **STRONG FIT** — Option B *is* Promise A's exact implementation; every shown direction carries dual-signal agreement | **CONFLICT** — 43.4% of Option C's results are monthly-only, violating the agreement requirement | **CONFLICT** — same violation, plus the fallback signal isn't even month-specific |
| **Promise B** | **WEAK FIT** — 46.5% of attempts deliver nothing actionable for the month | **STRONG FIT** — 96.9% available, fallback content remains month-specific (§9) | **CONDITIONAL** — 97.5% available, but fallback content is year-level, straining the word "monthly" in the Promise's own name (§10) |
| **Promise C** | **WEAK FIT** — the direction entry-point itself is missing 46.5% of the time, before the unresolved Recommendation-layer gap (§17) is even considered | **CONDITIONAL** — best direction-entry availability among month-preserving options (96.9%), but Recommendation Availability remains unestablished for every option, so shrine-guidance itself cannot be confirmed | **CONDITIONAL** — marginally higher entry availability (97.5%), same unresolved Recommendation-layer gap, plus a semantic mismatch (year-level signal) with a month-centric guidance narrative |

---

## 8. Availability Evidence

Re-cited only (task §13 — no rerun performed, no contradiction found):

```
Option B: 53.5%  (520/972)
Option C: 96.9%  (942/972 = 520 strict + 422 fallback-recovered)
Option D: 97.5%  (948/972)
Option E: N/A    (score contract not defined, #2504 §10-§11)
```

Availability is treated as one of ten evaluation inputs (§6), not the
sole criterion — see §9–§11 for the axes that ultimately separate C from
D despite D's marginally higher number.

---

## 9. Semantic Consistency

Per task §14, the three candidate meanings, compared explicitly:

```
B: "annual and monthly agree" (the only claim ever made)

C: "annual and monthly agree, when available;
    otherwise, monthly-only guidance for this month"

D: "annual and monthly agree, when available;
    otherwise, annual-only guidance for this month"
```

**C's fallback meaning stays anchored to the same time grain the product
promises ("this month") even when it cannot corroborate with the annual
chart. D's fallback meaning silently substitutes a different time grain
(the year) for a promise stated in terms of the month.** This is the
central semantic distinction between C and D, and it is not visible from
the availability numbers alone (97.5% vs 96.9%) — it only appears when
the *meaning* of the fallback result is examined, exactly as
[#2503](../audit/compass-direction-logic-product-decision.md) §14 and
[#2507](../audit/compass-monthly-fallback-availability.md) §18 already
established. Under Promise B, C's semantic consistency is judged
**stronger** than D's, because C never substitutes a different time grain
than the one the Promise itself names.

Semantic accuracy is not sacrificed under this decision merely to remove
no-direction: Option C's fallback cases are not described, anywhere in
this document or in the implied future implementation, as "annual and
monthly agreement" — they remain a distinct, honestly-labeled case (§16,
§24).

---

## 10. User Comprehensibility

Per task §15, compared as concept counts, not final copy:

```
B: 2 concepts  — common direction / no common direction
C: 3 concepts  — common direction / monthly-only direction / no direction available (even monthly)
D: 3 concepts  — common direction / annual-only direction / no direction available (even annual)
```

C and D carry the same *number* of concepts, but C's third concept
("monthly-only direction") is a smaller conceptual leap from the user's
existing mental model ("my direction for this month") than D's
("annual-only direction," which requires explaining that "this month's"
answer is actually derived from the whole year) — **C requires
introducing one new idea (a weaker-corroborated version of the same kind
of information); D requires introducing a new idea AND explaining a
change in time-grain.** This is a comprehensibility, not an availability,
distinction, and it favors C over D at equivalent concept count. No final
UI copy is written or designed by this document.

---

## 11. Monthly Product Value

Per task §16, this is Product Value reasoning, not measured retention —
no retention claim is made here.

**Question**: if Compass is meant to give users a reason to return
monthly, which Direction Logic best supports that behavior, distinct from
raw technical availability?

- **Option B**: 46.5% of monthly visits return nothing actionable — a
  structural headwind against habit formation specifically because the
  failure is frequent and (per #2497's own honmei/month breakdown)
  concentrated for some users in nearly every month they might check.
- **Option D**: even where a direction is *available* (97.5% of cases),
  43.4%+3.1%=46.5% of those results are year-level in the fallback case —
  meaning a user who checks Compass in two different months during a
  strict-intersection-empty stretch could see the **same annual-derived
  answer twice**, which weakens (though it does not eliminate — the
  strict-intersection months would still differ) the incentive to check
  back specifically *because it's a new month*.
- **Option C**: fallback content is itself solar-month-dependent (its
  formula's `month_center` derivation, `kyusei.py:250-252`, changes with
  `_solar_month_index()`), so even in fallback cases, a genuinely
  different signal is being computed each month — preserving a
  month-over-month reason to check back that D's fallback path does not.

This reasoning is a Product Value argument grounded in what each option's
fallback signal actually depends on (already-established, unmodified
production code, §5's Evidence Base), not a behavioral/retention
measurement — no such measurement exists or is claimed here.

---

## 12. Recommendation Availability Boundary

Per task §17, kept completely separate, stated explicitly:

```
96.9% Direction Availability (Option C) does NOT mean
96.9% shrine recommendation delivery.
```

Recommendation Availability remains **not established** for any option
(A/B/C/D/E alike) — confirmed unchanged across
[#2503](../audit/compass-direction-logic-product-decision.md) §12,
[#2504](../audit/compass-direction-logic-missing-evidence.md) §16, and
[#2507](../audit/compass-monthly-fallback-availability.md) §22-§21, none
of which executed a production Recommendation or PostHog query to
estimate it, and neither does this document. **This is precisely why
Promise C is not selected as the Final Product Promise** (§16, §19) —
Promise C's core requirement (reaching an actual shrine candidate) cannot
be confirmed by any Direction Logic decision alone.

---

## 13. Reliability Boundary

Per task §18, the three layers are kept explicit and distinct throughout
this document:

```
Runtime Reliability:      did the calculation complete normally?
                           (a legitimate no-direction result is NOT a
                           runtime failure — #2502 §7, unchanged)

Product Result Availability: did a direction (and/or recommendation)
                           result? (§8's 96.9%/53.5%/97.5% figures)

Product Value:             is the result useful to the user's next
                           decision? (#2502 §10 — deliberately not
                           reduced to a single rate; §11's Monthly
                           Product Value reasoning is qualitative, not a
                           Product Value measurement)
```

A monthly fallback result being *available* (§8) is not, by itself, proof
of higher *Product Value* (§11) — the Monthly Product Value argument in
§11 is offered as reasoning under the fixed framework, not as a
measurement that collapses these three layers into one number.

---

## 14. Option E Decision

**Classification: `B — OPTIONAL FUTURE EVOLUTION`**, not required before
this Product Decision.

Reasoning: [#2504](../audit/compass-direction-logic-missing-evidence.md)
§10-§11 itemized fifteen contract fields (weighting semantics, score
range, eligibility threshold, tie handling, `calculationMethod`
vocabulary, analytics state semantics, and nine others) that a Score
Contract would need to define before Option E could even be quantified —
none of which exist today, and none of which this document defines (task
§0 explicit prohibition: "Do not create the Score Contract"). Existing B/C/D
evidence (§8-§11) is sufficient to select a Direction Logic strategy
without E: C already satisfies Promise B's requirement at 96.9%
availability while preserving month-specificity, and no plausible Option
E outcome would change *which Promise* is selected (§16) — only, at most,
whether a future, more elaborate confidence-gradient model might someday
supersede C's simpler binary-fallback mechanism. That is deferred as a
distinct, optional future task (§27), not a blocker to deciding now.

---

## 15. Fallback Decision

```
Fallback adopted: YES
Fallback type:    MONTHLY
```

Conceptual authorization only (task §19) — not implemented by this
document. Reasoning: §9 (semantic consistency favors month-preserving
fallback over annual fallback), §10 (comprehensibility favors the smaller
conceptual leap), §11 (monthly product value favors a fallback signal
that itself varies by month). Annual fallback (Option D) is explicitly
**not** adopted, despite its marginally higher raw availability (§8, §10
of the task's own explicit question, answered NO in §16 below).

---

## 16. Final Product Promise

```
SELECTED: Promise B — Actionable Monthly Direction
```

**WHY SELECTED**: across the ten fixed axes (§6), Promise B is the only
candidate a currently-evaluable Direction Logic option (C) can fully
satisfy today. Promise A is fully satisfiable (by Option B) but leaves
46.5% of monthly attempts with nothing actionable — a direct conflict
with sustaining a *monthly* product's recurring value (§11). Promise C
cannot be responsibly selected yet: its core requirement (reaching a
shrine candidate) depends on Recommendation Availability evidence that
does not exist for any option (§12), and on the still-OPEN Shrine
Recommendation boundary (`compass-product-contract.md` Section 2.1-5),
neither of which this Direction-Logic-focused decision chain resolves.

**WHAT IT PROMISES**: an actionable direction for the target month in the
large majority of cases (96.9% under the selected Direction Logic, §17),
using the strongest available signal — annual+monthly agreement when
present, monthly-only guidance otherwise — while remaining honest that a
small residual (3.1%) may still yield no direction at all (§20).

**WHAT IT DOES NOT PROMISE**:

- It does **not** promise annual/monthly agreement in every case — 43.4
  percentage points of the 96.9% figure are monthly-only guidance, and
  this document requires that distinction remain visible in any future
  implementation (§9, §24, §25), never presented as if it were agreement.
- It does **not** promise a shrine recommendation will always follow —
  that is Promise C's unresolved territory (§12).
- It does **not** promise a direction will always be present — the 3.1%
  residual no-direction case remains a valid, expected outcome (§20).

**WHAT IS LOST BY NOT SELECTING THE OTHERS**:

- **Not selecting Promise A** loses the absolute semantic purity of "every
  shown direction is dual-signal corroborated" — a smaller, higher-confidence
  claim, traded for far wider monthly coverage (53.5%→96.9%).
- **Not selecting Promise C** loses the fuller product vision of
  guaranteed direction-to-shrine guidance for now — **deferred, not
  abandoned**: Promise C is a strict superset of Promise B's requirements
  (everything Promise B requires, plus guaranteed shrine reachability), so
  adopting Promise B today does not foreclose Promise C later, once
  Recommendation Availability evidence and the Shrine Recommendation
  boundary decision are separately resolved (§27's implementation
  sequence does not include either).

---

## 17. Final Direction Logic

```
SELECTED: Option C — Monthly Fallback
Direction Availability: 96.9% (942/972)
```

**WHY**: Option C is the only Direction Logic option that fully satisfies
the selected Promise (B) by construction (§7's matrix: STRONG FIT). It
achieves availability within 0.6 percentage points of the highest
measured option (D, 97.5%) without D's costs: D requires **reversing** an
existing, explicit Runtime Contract prohibition on annual-only output
(`compass-mvp-runtime-contract.md` Section 5, confirmed unchanged and
still in force, [#2503](../audit/compass-direction-logic-product-decision.md)
§9/§19) and weakens Compass's own MONTH time model
(`compass-product-contract.md` Section 4) more severely than C does (§9,
§11). C's calculation boundary already exists cleanly and
behavior-preservingly (`monthly_lucky_directions()`, #2506, verified via
a 972-case equivalence proof with zero drift), reducing the risk profile
of a future implementation relative to either inventing D's contract
reversal or E's score model from an undefined starting point (§14).

**TRADE-OFF ACCEPTED**: in 43.4% of cases (422/972), the shown direction
will **not** carry annual-chart corroboration — a real, disclosed semantic
weakening relative to today's Option B guarantee. This trade is accepted
in exchange for converting what is today Option B's single most common
negative outcome (no direction at all, 46.5% of cases) into a rare
outcome (3.1%, §20) while preserving month-specific meaning throughout
(§9, §11) — an explicit, evidence-grounded trade, not treated as costless.

---

## 18. Answering §10's Explicit Question (Option D)

> Does the additional ~0.6 percentage-point availability (D's 97.5% vs
> C's 96.9%) justify replacing monthly specificity with annual-only
> guidance in fallback cases?

**Answer: NO.**

0.6 percentage points is not sufficient justification to: (a) reverse an
existing, deliberate Runtime Contract decision
(`compass-mvp-runtime-contract.md` Section 5's annual-only prohibition,
made in a prior, separate audit chain and never revisited by this one);
(b) discard the "this month" specificity that differentiates Compass's
fallback cases from a generic, static yearly forecast (§9, §11); (c)
undermine the recurring-monthly-engagement rationale in exactly the
population (46.5% of cases) where a differentiated monthly hook matters
most (§11). This conclusion is not assumed merely because 97.5 > 96.9 —
it follows from weighing Semantic Consistency (§9), User Comprehensibility
(§10), and Monthly Product Value (§11) against a 0.6-point availability
difference, per the fixed ten-axis framework (§6), exactly as the task
instructed.

---

## 19. Accepted Trade-offs

```
1. 43.4% of Option C's available directions lack annual corroboration
   (§17) -- accepted, disclosed, never to be presented as agreement.
2. A residual 3.1% no-direction rate remains, down from 46.5% but not
   zero (§20) -- accepted as a legitimate, expected outcome, not
   eliminated artificially.
3. User Comprehensibility burden rises from 2 concepts to 3 (§10) --
   accepted as the necessary cost of Promise B's month-specific fallback
   design.
4. A future Runtime Contract change is required (calculationMethod
   vocabulary, referenceDirections semantics, fallback indication, §22) --
   accepted as necessary implementation cost, not performed here.
5. Promise C is deferred, not selected (§16) -- accepted because
   Recommendation Availability evidence does not yet exist for any
   option.
```

---

## 20. Rejected Alternatives

**Option B (kept as current implementation until superseded)**: rejected
as the *final* Direction Logic because its 46.5% no-direction rate
directly undermines Promise B's "actionable monthly" requirement (§7
matrix: WEAK FIT for Promise B). Not rejected as ever having been wrong —
[#2503](../audit/compass-direction-logic-product-decision.md)'s original
recommendation of B remains a correct, evidence-grounded decision *for
the evidence available at that time* (before Option C was quantifiable);
this document supersedes that recommendation now that Option C's
evidence gap is closed (#2507).

**Option D (Annual Fallback)**: rejected per §18's explicit analysis — its
marginal availability edge (97.5% vs 96.9%) does not justify discarding
month-specificity or reversing an existing Runtime Contract prohibition.

**Option E (Weighted Score Model)**: deferred, not rejected outright
(§14) — remains available as a future, optional evolution once (and only
if) a dedicated Score Contract phase (#2504 §10-§11) is separately
authorized. This document does not create that contract.

**Promise A**: not selected as final, for the reasons in §16 — its
semantic purity is real but its 46.5% no-direction rate is judged, under
the fixed framework's Monthly Product Value reasoning (§11), too costly
for a product whose core mechanic depends on giving users a reason to
return each month.

**Promise C**: not selected as final (yet) — deferred per §16's
superset reasoning, pending Recommendation Availability evidence and the
Shrine Recommendation boundary decision, neither resolved by this
document.

---

## 21. `no_common_direction` Future Role

Per task §23, **not eliminated artificially**. If Option C is
implemented in a future PR (§27), `no_common_direction` (or its
equivalent future state name) remains a valid, expected, first-class
result — its **trigger condition narrows**, from "annual∩monthly is
empty" (46.5% of cases today) to "annual∩monthly is empty **and**
monthly-only guidance is also empty" (3.1% of cases, measured at §8/§17).

```
Measured residual: 30 / 972 = 3.1%
```

This state continues to represent a genuine, deterministic, structural
outcome (per [#2496](../audit/compass-direction-filter-unavailable-root-cause.md)'s
`EXPECTED FAIL-SAFE` classification, which this decision does not
revisit or weaken) — not an error, and not something a future
implementation should attempt to eliminate entirely, since §9's own
manual root-cause trace ([#2503](../audit/compass-direction-logic-product-decision.md)
via [#2504](../audit/compass-direction-logic-missing-evidence.md) §9's
Option D analogue) already showed this class of outcome is a genuine,
reproducible property of the underlying kyusei calculation, not a defect.
No implementation of this narrowed role is performed by this document.

---

## 22. Product Contract Changes Required

Not performed by this document (task §31 explicit prohibition). Inventory
only:

| Change | Classification | Reason |
|---|---|---|
| Section 2 Promise wording (revise from Promise A's language to Promise B's) | **REQUIRED** | Current wording (`compass-product-contract.md` Section 2, as revised by #2498) describes Promise A's exact behavior; a Promise B implementation would need this rewritten to honestly describe the fallback mechanism, not merely re-interpreted |
| Fallback semantics (new Decision Record subsection, e.g. Section 2.2) | **REQUIRED** | No existing Product Contract section describes a fallback concept at all; this decision introduces one |
| `no_common_direction` semantics (Section 2.1 narrowing) | **REQUIRED** | Section 2.1's current text frames `no_common_direction` around the 46.5% frequency; the narrowed 3.1% trigger condition (§21) needs its own documented update |
| Shrine Recommendation boundary (Section 2.1-5) | **NOT REQUIRED by this decision** | Remains explicitly OPEN, untouched by this Promise/Direction Logic decision — Promise C's deferral (§16) does not require resolving this boundary now |

---

## 23. Runtime Contract Changes Required

Not performed by this document. Inventory only:

| Change | Classification | Reason |
|---|---|---|
| `calculationMethod` vocabulary | **REQUIRED** | `monthly_lucky_directions()` already returns `"monthly_kyusei_v1"` (#2506) when used standalone; `compass-mvp-runtime-contract.md` Section 5 would need to formally accept this value (or a composite one) as a legitimate `CompassDirectionRuntime.calculationMethod` |
| `referenceDirections` semantics | **REQUIRED** | Currently documented as "the annual∩monthly intersection" (Section 5); under Option C it would sometimes hold a strict-intersection result and sometimes a monthly-only result — the field's meaning becomes conditional |
| Fallback indication (explicit flag or reliance on `calculationMethod` alone) | **REQUIRED** | Some machine-readable signal is necessary so downstream consumers (UI, Analytics) can honestly distinguish Category 1 from Category 2 results (§9, §19 item 1) — this decision does not choose which mechanism |
| `no_common_direction` trigger condition (Section 8 Fail-safe table) | **REQUIRED** | The condition narrows from "intersection empty" to "intersection empty AND monthly also empty" (§21) — the Fail-safe table's Group B row needs updating to reflect this |
| `CompassDirectionRuntime` Schema itself (field-level structural change) | **NOT REQUIRED** | Unlike Option E (#2503 §19), Option C needs no new fields beyond what `calculationMethod`/fallback-indication already cover — no confidence-tier structure is introduced |

---

## 24. Analytics Changes Required

Not performed by this document. Inventory only:

```
Analytics Contract change:    REQUIRED
Instrumentation change:       REQUIRED
```

**Analytics Contract (documentation)**: `docs/analytics/compass-posthog-query-contract.md`'s
`VALID_NO_DIRECTION` bucket definition and the Reliability Rate /
Recommendation Delivery Rate KPI definitions ([#2507](../audit/compass-monthly-fallback-availability.md)
§27) would need updating to explain the narrowed `no_common_direction`
frequency (46.5%→3.1%) and to define how a Category-2 (fallback) result
should be classified for Reliability purposes — this is Runtime-Reliability-valid
by the existing definition (§13, a legitimate completed calculation),
but the KPI documentation should say so explicitly rather than leaving it
implicit.

**Instrumentation (code)**: a future implementation would need to
actually emit a distinguishable signal for fallback-vs-strict results
(most likely reusing the `calculationMethod` value the helper already
produces, §23, rather than inventing a new event) — some code change is
therefore required to make this observable in production PostHog, even
if minimal. Neither the contract text nor the instrumentation code is
changed by this document.

---

## 25. UI Impact

Not implemented, no final copy written (task §25). Three states a future
UI must distinguish:

```
1. Common direction   (annual + monthly agree)
2. Fallback direction (monthly-only guidance, no annual corroboration)
3. No direction       (neither signal available, 3.1% residual)
```

**The UI must distinguish states 1 and 2**, per
`compass-product-contract.md` Section 8's Signal-to-Explanation Rule,
which is an existing, unmodified absolute constraint: "影響していない信号
が影響したかのように暗示する表現をしてはならない" ("must not imply a
signal influenced the result when it did not"). Presenting a fallback
(state 2) result as if it carried annual agreement would violate this
rule directly. Whether states 2 and 3 (or 1 and 2) share similar visual
*tone* (both are legitimate, non-error outcomes, per §21's
non-elimination stance) is an implementation-PR decision, not resolved
here — only the requirement that the underlying explanation stay honest
per-case is fixed by this decision.

---

## 26. Concierge Boundary

```
Concierge changed: NO
```

Unaffected by this decision, and must remain unaffected by any future
implementation of it. Per
[#2505](../audit/compass-monthly-direction-calculation-contract.md) §6's
already-established ownership finding: Option C's fallback policy, if
implemented, belongs to Compass Layer B (`compass_runtime.py`), never to
`kyusei.py`'s shared calculation layer. `monthly_lucky_directions()` may
be called by Compass; **Concierge must not inherit the fallback policy
automatically** — `api_views_concierge.py`'s existing two call sites
(`annual_lucky_directions()`, `planned_visit_lucky_directions()`) are
unaffected by this decision and must remain so in any future
implementation PR.

---

## 27. Implementation Sequence

Not executed by this document (task §30 explicit instruction). Proposed
future PR order, adjusted from the task's default template only where
this audit chain's own evidence supports a safer split (per #2503/#2504/#2505's
own precedent of separating contract-first from code-second):

```
PR-1: Product / Runtime Contract alignment (docs-only)
  - compass-product-contract.md Section 2 Promise rewrite (Promise B)
  - Fallback semantics subsection (new)
  - no_common_direction narrowed trigger condition (Section 2.1 update)
  - compass-mvp-runtime-contract.md Section 5 calculationMethod
    vocabulary, referenceDirections conditional semantics
  - compass-mvp-runtime-contract.md Section 8 Fail-safe table update
  - No code change

PR-2: Compass Runtime implementation
  - compass_runtime.py gains the fallback decision logic (call
    monthly_lucky_directions() when the strict intersection is empty),
    confined to Layer B per #2505's ownership finding
  - kyusei.py unchanged (monthly_lucky_directions() already exists, #2506)
  - api_views_concierge.py unchanged (§26)
  - New/updated backend tests (behavior-preservation-style, following
    #2506's own equivalence-test precedent)

PR-3: Frontend state / copy
  - Distinguish the three states (§25) honestly, per the
    Signal-to-Explanation Rule
  - No final copy pre-written by this decision record

PR-4: Analytics Contract / instrumentation (§24)
  - Fallback observability (state/property, reusing calculationMethod
    where possible)
  - VALID_NO_DIRECTION bucket and Reliability/Delivery KPI documentation
    updated for the narrowed frequency

PR-5: Production verification
  - Mirrors the #2499 -> #2501 precedent: confirm in production PostHog
    that fallback cases classify correctly, with no collapse into other
    states, before declaring the rollout complete
```

**Recommendation Ranking remains entirely outside this sequence** (§28) —
no PR in this list touches `concierge_chat_ranking.py`,
`concierge_chat_candidates.py`, or `build_chat_recommendations`, and none
should, absent a separate, distinct future decision explicitly authorizing
it.

---

## 28. Ranking Boundary

```
Ranking changed: NO
```

This Direction Logic decision does not alter, and must not be read as
authorizing any future alteration of, candidate scoring, ranking weights,
candidate ordering, or Recommendation Reason logic
(`concierge_chat_ranking.py`, `concierge_chat_candidates.py`,
`build_chat_recommendations`) — unchanged from
[#2502](compass-product-logic-evaluation-framework.md) §19/[#2503](../audit/compass-direction-logic-product-decision.md)
§18's Ranking Boundary, re-confirmed here as still in force.

---

## 29. Non-goals

This document does **not**:

- Implement Monthly Fallback (Option C) in production
- Modify `kyusei.py`, `compass_runtime.py`, or any other production file
- Modify the Product Contract, Runtime Contract, or Analytics Contract
  (§22-§24 are inventories, not edits)
- Modify the frontend or write final UI copy
- Modify Analytics instrumentation
- Modify Recommendation Ranking
- Modify Concierge behavior
- Resolve Recommendation Availability for any option
- Implement Promise C
- Create an Option E Score Contract or implement Option E
- Modify the DB or create migrations

---

## 30. Decision Record

```
Product Promise:      B — Actionable Monthly Direction   (DECIDED)
Direction Logic:      C — Monthly Fallback                (DECIDED)
Fallback:             ADOPTED, type MONTHLY               (DECIDED)
Option E:             DEFERRED — optional future evolution (DECIDED)
Promise C:            DEFERRED — pending Recommendation Availability
                       evidence and the Shrine Recommendation boundary
                       decision                            (DECIDED to defer)
Implementation:       NOT STARTED — §27 sequence proposed, not executed
```

This record supersedes [#2503](../audit/compass-direction-logic-product-decision.md)'s
PROPOSED recommendation (Option B) now that Option C's evidence gap is
closed ([#2507](../audit/compass-monthly-fallback-availability.md)), per
§20's Rejected Alternatives note. It does not supersede any Concierge,
Ranking, or Recommendation-layer decision, all of which remain governed
by their existing, unchanged contracts.

---

## Verification

```
$ git -C /Users/morietsu/Developer/jinja_app diff --check
(no output = no whitespace errors)
```

- **#2502 evidence used correctly**: confirmed — vocabulary, axes, and
  Promise candidates A/B/C quoted/used as-is (§4, §6), not redefined.
- **#2503 comparison used correctly**: confirmed — Option lettering (B/C/D/E)
  and its original Recommended/Alternative framing (§20) are consistent
  with the source document.
- **#2504 missing-evidence conclusions reflected**: confirmed — Option E's
  15-field contract gap (§14) and Option D's independent reproduction
  (§3, §8) are both re-cited accurately.
- **#2505 helper-boundary conclusion reflected**: confirmed — the
  Concierge-isolation ownership finding (§26) matches #2505 §6 exactly.
- **#2507 Option C figures reproduced accurately**: confirmed —
  96.9%/942/972, 520 strict, 422 fallback-recovered, 30 residual, 93.4%
  recovery rate, all match #2507 verbatim (§3, §8, §17, §21).
- **B = 53.5%, C = 96.9%, D = 97.5%**: confirmed (§8).
- **C fallback recovery = 93.4%, C residual unavailable = 3.1%**:
  confirmed (§3, §21).
- **Direction Availability != Recommendation Availability**: confirmed,
  kept explicitly separate throughout (§12).
- **`no_common_direction` != runtime error**: confirmed, unchanged from
  #2496/#2498 (§21).
- **Product Value != Reliability**: confirmed, kept as three distinct
  layers (§13).
- **Concierge boundary preserved**: confirmed (§26).
- **Ranking boundary preserved**: confirmed (§28).
- **No production code modified**: confirmed (§32 below).
- **git diff --check clean**: confirmed above.

```
$ git status --short
?? docs/product/compass-product-direction-decision.md

$ git diff --stat
(untracked, 1 file)

$ git diff --name-only
(none — untracked, not yet staged)
```

---

## Diff Scope Gate

Exactly one new file, matching the expected diff (task §32). No existing
canonical contract (`compass-product-contract.md`,
`compass-mvp-runtime-contract.md`, or any prior audit document) is
modified — this document is additive only, and the Contract-change
inventories in §22-§24 are explicitly future work, not edits performed
here.
