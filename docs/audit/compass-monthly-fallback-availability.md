> **Status: `PROPOSED — MOTHER SHIP DECISION REQUIRED` (evidence-completion
> audit, not a Product Decision)**
>
> Using the canonical, production `monthly_lucky_directions()` helper
> ([#2506](https://github.com/etsu33/jinja_app/pull/2506), merged) together
> with the unmodified `annual_lucky_directions()`, this audit quantifies
> Option C (Monthly Fallback) Direction Availability for the first time,
> closing the evidence gap [#2504](compass-direction-logic-missing-evidence.md)
> and [#2505](compass-monthly-direction-calculation-contract.md) left open.
>
> **Result: Option C Direction Availability = 96.9% (942/972)**, a
> +43.4-percentage-point improvement over the current strict-intersection
> baseline (53.5%). Of the 452 cases where the strict intersection is
> empty, monthly-only guidance recovers a direction in 422 (**93.4%
> fallback recovery rate**); 30 cases (3.1% of the full population) remain
> unavailable even after fallback.
>
> This number is reported honestly, per the Framework's and prior audits'
> explicit constraint: **high availability alone does not make Option C the
> better product option.** Option C still changes what a shown direction
> *means* whenever fallback activates (§18), and Promise A's semantic
> requirement (annual/monthly agreement) is still not preserved by it
> (§19).
>
> No production code, Product Contract, Runtime Contract, Recommendation
> Ranking, Concierge behavior, or Analytics instrumentation is changed.
> docs-only.

---

## 1. Executive Summary

[#2506](https://github.com/etsu33/jinja_app/pull/2506) (merged) introduced
`monthly_lucky_directions()` as a canonical, standalone public function in
`backend/temples/domain/kyusei.py`, purpose-built (per
[#2505](compass-monthly-direction-calculation-contract.md)) to unblock
exactly the measurement this audit performs. This document runs the same
9×12×9 = 972-case deterministic methodology
[#2497](compass-direction-availability-product-decision.md)/[#2503](compass-direction-logic-product-decision.md)/[#2504](compass-direction-logic-missing-evidence.md)
established, calling `annual_lucky_directions()` and
`monthly_lucky_directions()` directly (unmodified, zero reimplementation)
and applying a **hypothetical, audit-only** Option C policy: use the
annual∩monthly intersection when non-empty; otherwise use monthly-only
lucky directions.

**Key results**:

```
Option C Direction Available:    942 / 972 = 96.9%
Option C Direction Unavailable:   30 / 972 =  3.1%

Strict intersection available:            520 / 972 = 53.5%
Strict empty -> monthly fallback recovered: 422 / 972 = 43.4%
Strict empty -> monthly also empty:          30 / 972 =  3.1%
                                            -----
                                            972 / 972 = 100%

Fallback activation rate:  452 / 972 = 46.5%  (== the known no-common-direction rate)
Fallback recovery rate:    422 / 452 = 93.4%
```

The strict-intersection subtotal (520/972 = 53.5%) reproduces
[#2497](compass-direction-availability-product-decision.md)'s own figure
exactly, using an entirely independent synthetic birthdate set (1991–1999,
disjoint from every prior audit's set) — this is strong internal
cross-validation, not a coincidence: it confirms `monthly_lucky_directions()`
and `annual_lucky_directions()`, called independently and intersected by
this audit's own script, reproduce precisely what
`planned_visit_lucky_directions()` itself computes internally — the exact
equivalence [#2506](https://github.com/etsu33/jinja_app/pull/2506)'s own
test suite already proved for all 972 cases.

**Decision readiness: `A — READY FOR MOTHER SHIP PRODUCT DECISION`** (§29)
— every option the Mother Ship might choose among (A, B, C, D) now has
measured Direction Availability; Option E remains a distinct, optional
future path, not a blocker.

---

## 2. Audit Question

> Using the now-canonical `monthly_lucky_directions()` helper, what is
> Option C's actual Direction Availability — both overall, and broken down
> by exactly how much of any improvement comes from fallback recovery
> versus the pre-existing strict intersection — and does this new evidence
> change any #2503 conclusion?

This audit does not decide whether to adopt Option C, and does not
implement it.

---

## 3. Canonical Sources

| Document | Role |
|---|---|
| [compass-product-logic-evaluation-framework.md](../product/compass-product-logic-evaluation-framework.md) (#2502) | Immutable — vocabulary, axes, Direction/Recommendation Availability definitions, Product Promise candidates A/B/C. Not changed. |
| [compass-direction-logic-product-decision.md](compass-direction-logic-product-decision.md) (#2503) | Immutable — prior five-option comparison. Not changed; §28 below records evidence impact only. |
| [compass-direction-logic-missing-evidence.md](compass-direction-logic-missing-evidence.md) (#2504) | Immutable — established Option C was then unquantifiable, and independently reproduced Option D's 97.5%. |
| [compass-monthly-direction-calculation-contract.md](compass-monthly-direction-calculation-contract.md) (#2505) | Immutable — the contract this audit's helper usage complies with. |
| `backend/temples/domain/kyusei.py` (current `develop`) | Implementation authority — `annual_lucky_directions()`, `monthly_lucky_directions()` (new, #2506), `planned_visit_lucky_directions()` all confirmed present and called unmodified. |
| [compass-direction-availability-product-decision.md](compass-direction-availability-product-decision.md) (#2497) | Source of the 9×12×9 methodology and the 53.5%/46.5% baseline this audit's own strict-intersection subtotal reproduces exactly. |

Confirmed before proceeding (`git log -1 --oneline` = `763abe71`, the #2506
merge commit): `annual_lucky_directions()` (`kyusei.py:191`),
`monthly_lucky_directions()` (`kyusei.py:239`, new),
`planned_visit_lucky_directions()` (`kyusei.py:286`) all present.

---

## 4. Option C Definition

**Hypothetical, audit-only policy — not implemented in production**:

```
annual = annual_lucky_directions(birthdate, today=target_date)
monthly = monthly_lucky_directions(birthdate, visit_date=target_date)
intersection = [d for d in annual["luckyDirections"] if d in monthly["luckyDirections"]]

if intersection is non-empty:
    Option C selected directions = intersection
else:
    Option C selected directions = monthly["luckyDirections"]  (may itself be empty)
```

Both `annual_lucky_directions()` and `monthly_lucky_directions()` are
called directly, unmodified, exactly as
[#2504](compass-direction-logic-missing-evidence.md) did for Option D and
[#2506](https://github.com/etsu33/jinja_app/pull/2506)'s own tests do for
their equivalence proof. No formula, exclusion rule, or compatibility
check from either function is reimplemented anywhere in this audit's
script.

---

## 5. Methodology

Same deterministic grid [#2497](compass-direction-availability-product-decision.md)
established, reused by [#2503](compass-direction-logic-product-decision.md)/[#2504](compass-direction-logic-missing-evidence.md):

```
9 honmei outcomes × 12 solar-month buckets × 9 representative years = 972 cases
```

Environment: `django.conf.settings.configure(USE_TZ=True,
TIME_ZONE="Asia/Tokyo")`, no DB access, no migrations, no real settings
module. Script location: session scratchpad only
(`/private/tmp/claude-501/.../scratchpad/compass_option_c_matrix.py`),
never committed (§36, §37).

For every one of the 972 cases, both `annual_lucky_directions()` and
`monthly_lucky_directions()` returned a non-`None` result — zero anomalies
(no case fell outside the synthetic valid-input matrix; the "STOP and
investigate" condition in the task's methodology was never triggered).

---

## 6. Synthetic Population

**9 synthetic birthdates, one per honmei star (1–9), independent of every
prior audit's set**: constructed by scanning birth years 1991–1999
(June 15 each year) through `honmei_star()` until all nine `num` values
1–9 were each represented exactly once. No real user birthdate is used
anywhere in this audit. Only the resulting honmei-star classification is
meaningful to the results — the specific synthetic year/day chosen is not
independently significant (per the task's instruction not to publish
unnecessary personal-looking detail, the exact birth-year-to-honmei
mapping is recorded here only for reproducibility, not as a claim about
any real person):

```
honmei 1 <- 1999-06-15   honmei 4 <- 1996-06-15   honmei 7 <- 1993-06-15
honmei 2 <- 1998-06-15   honmei 5 <- 1995-06-15   honmei 8 <- 1992-06-15
honmei 3 <- 1997-06-15   honmei 6 <- 1994-06-15   honmei 9 <- 1991-06-15
```

---

## 7. Solar-month Sampling

Twelve representative target dates, one per solar-month bucket, each
chosen safely inside its bucket (mid-bucket, per the task's instruction to
avoid boundary dates except when specifically testing a boundary — boundary
behavior itself was already separately verified in
[#2506](https://github.com/etsu33/jinja_app/pull/2506)'s own boundary
test, not repeated here):

```
Bucket 0  (2/4–3/5):   2/20      Bucket 6  (8/8–9/7):   8/20
Bucket 1  (3/6–4/4):   3/20      Bucket 7  (9/8–10/7):  9/20
Bucket 2  (4/5–5/5):   4/20      Bucket 8  (10/8–11/6): 10/20
Bucket 3  (5/6–6/5):   5/20      Bucket 9  (11/7–12/6): 11/20
Bucket 4  (6/6–7/6):   6/20      Bucket 10 (12/7–1/5):  12/20
Bucket 5  (7/7–8/7):   7/20      Bucket 11 (1/6–2/3):   1/20
```

Boundaries themselves are read directly from current production
`_solar_month_index()` (`kyusei.py:229-236`, unchanged), not re-derived.
**9 representative years: 2022–2030**, the same span
[#2497](compass-direction-availability-product-decision.md)/[#2503](compass-direction-logic-product-decision.md)/[#2504](compass-direction-logic-missing-evidence.md)
established, preserved here for direct comparability.

---

## 8. Overall Direction Availability

```
Option C Direction Available:  942 / 972 = 96.9%
```

---

## 9. Overall Direction Unavailability

```
Option C Direction Unavailable:  30 / 972 = 3.1%
```

These 30 cases are exactly the cases where **both** the strict
intersection **and** the monthly-only signal are empty — see §10.

---

## 10. Strict vs Fallback Breakdown

**Mandatory table (task §34)**:

| Category | Count | Rate |
|---|---:|---:|
| Strict intersection available | 520 | 53.5% |
| Strict empty → monthly recovered | 422 | 43.4% |
| Strict empty → monthly also empty | 30 | 3.1% |
| **Total** | **972** | **100%** |

The three categories sum to exactly 972, confirming the classification is
exhaustive and non-overlapping (task §14).

---

## 11. Fallback Activation Rate

```
(cases where strict intersection is empty, i.e. fallback is invoked)
= 422 + 30 = 452 / 972 = 46.5%
```

This equals, to the decimal, [#2497](compass-direction-availability-product-decision.md)'s
already-established "no common direction" rate (452/972 = 46.5%) — not a
coincidence: fallback is defined to activate in exactly the same cases
where the strict intersection is empty, which is the same population
#2497 already measured. **Fallback activation is not itself evidence of
anything new** — it is the same known 46.5% characteristic, now viewed
from the "what happens next" side rather than the "what happened" side.

---

## 12. Fallback Recovery Rate

```
(cases where fallback was invoked AND produced >=1 direction)
= 422 / 452 = 93.4%
```

**This is the number that matters, and it is kept explicitly distinct
from Fallback Activation Rate**, per the task's own instruction (§13 of
the task: "Do not confuse fallback activated with fallback successfully
recovered availability"). Of the 452 cases where annual and monthly
disagreed, monthly-only guidance was itself non-empty in 422 of them
(93.4%) — only 30 cases (6.6% of the fallback-invoked population, 3.1% of
the full population) had a monthly signal that was *also* empty.

---

## 13. Honmei Breakdown

| Honmei | Total | Strict available (cat1) | Fallback recovered (cat2) | Fallback also empty (cat3) |
|---|---:|---:|---:|---:|
| 1 | 108 | 51 | 54 | 3 |
| 2 | 108 | 62 | 46 | 0 |
| 3 | 108 | 39 | 66 | 3 |
| 4 | 108 | 36 | 66 | 6 |
| 5 | 108 | 94 | 14 | 0 |
| 6 | 108 | 61 | 41 | 6 |
| 7 | 108 | 61 | 44 | 3 |
| 8 | 108 | 63 | 42 | 3 |
| 9 | 108 | 53 | 49 | 6 |

The "cat1" column (51, 62, 39, 36, 94, 61, 61, 63, 53) reproduces
[#2497](compass-direction-availability-product-decision.md) §7's Honmei
Breakdown table exactly — a second independent cross-validation of the
strict-intersection subtotal, at the per-honmei level, using this audit's
own disjoint birthdate set. Honmei stars 4 and 6 show the highest
`cat3` (fully unavailable even after fallback) rate (6/108 ≈ 5.6% each);
honmei stars 2 and 5 show zero `cat3` cases in this sample.

---

## 14. Month Breakdown

| Bucket | Approx. period | Total | Strict available | Fallback recovered | Fallback also empty |
|---|---|---:|---:|---:|---:|
| 0 | 2/4–3/5 | 81 | 50 | 31 | 0 |
| 1 | 3/6–4/4 | 81 | 44 | 34 | 3 |
| 2 | 4/5–5/5 | 81 | 46 | 32 | 3 |
| 3 | 5/6–6/5 | 81 | 46 | 32 | 3 |
| 4 | 6/6–7/6 | 81 | 43 | 35 | 3 |
| 5 | 7/7–8/7 | 81 | 45 | 36 | 0 |
| 6 | 8/8–9/7 | 81 | 42 | 39 | 0 |
| 7 | 9/8–10/7 | 81 | 35 | 43 | 3 |
| 8 | 10/8–11/6 | 81 | 40 | 41 | 0 |
| 9 | 11/7–12/6 | 81 | 44 | 28 | 9 |
| 10 | 12/7–1/5 | 81 | 42 | 36 | 3 |
| 11 | 1/6–2/3 | 81 | 43 | 35 | 3 |

Bucket 9 (11/7–12/6) shows the highest `cat3` rate (9/81 ≈ 11.1%) of any
month bucket; several buckets (0, 5, 6, 8) show zero `cat3` cases in this
sample. No month bucket is catastrophically worse than the others —
consistent with [#2497](compass-direction-availability-product-decision.md)
§8's finding that month-to-month variation is smaller than honmei-to-honmei
variation.

---

## 15. Year Breakdown

| Year | Total | Strict available | Fallback recovered | Fallback also empty |
|---|---:|---:|---:|---:|
| 2022 | 108 | 65 | 37 | 6 |
| 2023 | 108 | 52 | 54 | 2 |
| 2024 | 108 | 66 | 40 | 2 |
| 2025 | 108 | 53 | 49 | 6 |
| 2026 | 108 | 55 | 51 | 2 |
| 2027 | 108 | 55 | 51 | 2 |
| 2028 | 108 | 54 | 48 | 6 |
| 2029 | 108 | 59 | 47 | 2 |
| 2030 | 108 | 61 | 45 | 2 |

`cat3` (fully unavailable) stays low and fairly flat across years (2–6 of
108, roughly 1.9%–5.6%) — no single year is an outlier.

---

## 16. Direction-count Distribution

| Direction count | Cases | Share |
|---|---:|---:|
| 0 | 30 | 3.1% |
| 1 | 447 | 46.0% |
| 2 | 316 | 32.5% |
| 3+ | 179 | 18.4% |

Sum: 30+447+316+179 = 972. Compared with Option A/B's own distribution
([#2497](compass-direction-availability-product-decision.md) §10: 0→46.5%,
1→35.7%, 2→12.6%, 3+→5.2%), Option C not only reduces the 0-direction
share (46.5%→3.1%) but also shifts real mass into the 2-and-3+-direction
buckets (12.6%→32.5%, 5.2%→18.4%) — because whenever the strict
intersection is empty, the fallback substitutes the *entire* monthly-only
set (which, unfiltered by annual agreement, is often larger than a
one-direction intersection would have been).

---

## 17. Comparison with Options A/B/D/E

**Mandatory summary table (task §33)**:

| Option | Direction Availability | Evidence status |
|---|---:|---|
| A Strict Intersection | 53.5% | established (#2497, re-cited) |
| B First-Class No-Direction | 53.5% | established (#2497, re-cited) |
| C Monthly Fallback | **96.9%** | **this audit** |
| D Annual Fallback | 97.5% | independently reproduced (#2504) |
| E Weighted Score | N/A | score contract missing (#2504) |

No discrepancy found between this audit's re-cited A/B/D/E figures and
current canonical docs (#2503 §4, #2504 §8) — all match exactly.

**C vs. D, read carefully**: D's 97.5% is still nominally higher than C's
96.9%, but the two are not interchangeable substitutes — D fully discards
month-specificity (its fallback is the *year's* signal), while C's
fallback preserves month-specificity (its fallback is *this month's*
signal alone) at a marginal availability cost (0.6 percentage points).
Per [#2503](compass-direction-logic-product-decision.md) §9, D also
carries the heavier Runtime Contract burden (reversing an existing
explicit prohibition). This audit does not re-rank C against D — that is
a Mother Ship decision, not an evidence question.

---

## 18. Semantic Interpretation

Restated plainly, per the task's explicit instruction not to hide the
shift:

```
Category 1 (520/972, 53.5%):
  "annual and monthly agree" -- the shown direction has both signals'
  support, exactly as under Option A/B today.

Category 2 (422/972, 43.4%):
  "annual and monthly do NOT agree, so monthly-only guidance is used
  instead" -- the shown direction carries only this month's support, not
  the year's. This is not annual/monthly agreement, and must not be
  presented as if it were.

Category 3 (30/972, 3.1%):
  no direction at all -- both signals failed to produce anything,
  identical in kind to Option A/B's no_common_direction outcome, just at
  a much lower frequency (3.1% vs 46.5%).
```

Category 2's directions are **not** described anywhere in this document
as "annual and monthly agreeing" — they are a different, weaker claim
(monthly signal alone), and any future implementation must keep this
distinction visible in whatever Presentation Authority logic renders it
(`compass-product-contract.md` Section 8's Signal-to-Explanation Rule
already requires this: explanations must trace to the signal actually
used).

---

## 19. Promise A Impact

**Not reinterpreted.** Promise A (Strict Common Direction, #2502 §12)
still means annual/monthly agreement, full stop. Option C's 96.9% overall
availability does **not** change this: 43.4 percentage points of that
number (Category 2) come from monthly-only guidance, which by definition
does not satisfy Promise A's semantic requirement. **The availability gain
does not remove the Promise A semantic mismatch** — Option C remains
Poorly Aligned with Promise A, exactly as [#2503](compass-direction-logic-product-decision.md)
§13 already found, unchanged by this audit's numbers.

---

## 20. Promise B Impact

**Question**: does the measured Option C availability materially
strengthen it as a candidate for Promise B (Actionable Monthly Direction)?

**Classification: `STRONGLY SUPPORTS`.**

Reasoning, grounded in the fixed #2502 framework: Promise B's own
definition (#2502 §12) does not require annual/monthly agreement — only
that the user receives something actionable "this month." Option C's
fallback mechanism is a close structural match to that requirement: when
agreement exists, the strongest possible signal is used (Category 1);
when it does not, the *month-specific* signal alone is used (Category 2)
rather than falling back to a year-level signal (contrast Option D) or
returning nothing (contrast A/B). The magnitude of the improvement —
53.5%→96.9% overall, with a 93.4% recovery rate specifically in the cases
where the strict version would have failed — is large enough to be a
material factor, not a marginal one. This classification does **not**
resolve whether Promise B should be adopted, and does not by itself
authorize implementing Option C (§19's semantic caveat and §22's
Recommendation Availability boundary both still apply in full).

---

## 21. Promise C Impact

Per the task's explicit instruction: **Direction Availability alone does
not prove Direction-to-Shrine Guidance** (Promise C, #2502 §12).

```
Option C Direction Availability:     QUANTIFIED (96.9%, this audit)
Option C Recommendation Availability: STILL NOT ESTABLISHED
```

Reaching a shrine candidate additionally depends on Layer C (candidate
filtering by bearing sector) and Layer D (Ranking), neither of which any
Direction Logic option changes (#2502 §19, unchanged). A higher Direction
Availability *may* widen the population of results that reach Layer C,
but does not itself guarantee any resulting candidate count — this is not
inferred here, in either direction.

---

## 22. Recommendation Availability Boundary

Per the task's explicit instruction (§21 of the task), **no production
Recommendation query or PostHog query was executed for this audit.** This
document answers only "can Option C provide a direction?" (§8-§17), never
"can Option C always provide a shrine?" The latter question remains
exactly as open as it was after [#2503](compass-direction-logic-product-decision.md)/[#2504](compass-direction-logic-missing-evidence.md)
left it, for every option, not only C.

---

## 23. User Comprehensibility Impact

Per the fixed #2502 framework (Axis 5), the explanatory burden **increases**
under Option C relative to Option A/B, and the measured category sizes
make this concrete: Option A/B's binary explanation space ("direction
shown" / "no common direction, ~46.5% of the time") becomes a three-way
space under Option C:

```
"annual and monthly agree"                (53.5% of cases)
"no agreement -- monthly-only guidance"    (43.4% of cases, NEW explanatory case)
"no direction at all, even monthly failed" (3.1% of cases, rarer than
                                             Option A/B's no-direction case,
                                             but still needs its own copy)
```

Notably, the *new* explanatory case (Category 2, "monthly-only guidance")
applies to a larger population (43.4%) than the case it most resembles in
spirit — Option A/B's current `no_common_direction` copy (46.5%) — meaning
a future implementation would need new, carefully-worded copy for a case
that is nearly as frequent as today's no-direction case is, not a rare
edge case. No UI copy is written or designed here (task §22 explicit
instruction).

---

## 24. Concierge Boundary

```
Concierge behavior changed: NO
```

The audit script only called `annual_lucky_directions()` and
`monthly_lucky_directions()` read-only, from a session scratchpad script
outside the repository. `kyusei.py` and `api_views_concierge.py` were not
modified (confirmed, §36). Option C's hypothetical fallback policy, if
ever adopted, would belong to Compass Layer B
(`compass_runtime.py`/`compass_recommendation_orchestrator.py`), per
[#2505](compass-monthly-direction-calculation-contract.md) §6's ownership
finding — not to `kyusei.py`, and not to Concierge.

---

## 25. Ranking Boundary

```
Recommendation Ranking changed: NO
```

No candidate scoring, ranking weight, ranking order, or recommendation
reason logic was touched, read, or reasoned about beyond what
[#2502](../product/compass-product-logic-evaluation-framework.md)/[#2503](compass-direction-logic-product-decision.md)
already established: Direction Logic options may influence which
population reaches Layer C, never Layer D's scoring itself.

---

## 26. Runtime Contract Impact

```
Runtime Contract change: YES, if Option C is ever adopted (not performed here)
```

Reasons, restated and now more specific than [#2503](compass-direction-logic-product-decision.md)
§9's general finding, using this audit's actual category data:

- **`calculationMethod` vocabulary**: `monthly_lucky_directions()` already
  returns a distinct value (`"monthly_kyusei_v1"`, #2506) whenever it is
  used standalone. A future Option C implementation would need
  `compass-mvp-runtime-contract.md` Section 5 to explicitly accept this
  value (or a new composite one) as a legitimate `CompassDirectionRuntime.
  calculationMethod`, alongside the existing `"annual_monthly_kyusei_v1"`.
- **Fallback indication**: whether `CompassDirectionRuntime` should carry
  an explicit "this is a fallback result" flag, or rely solely on
  `calculationMethod` to signal it, is undecided — but *some* signal is
  necessary, since §18/§23 established that Category 1 and Category 2
  results are semantically different and must not be presented
  identically.
- **`referenceDirections` semantics**: currently documented (Runtime
  Contract Section 5) as "the annual∩monthly intersection." Under Option
  C, this field would sometimes hold a strict-intersection result and
  sometimes a monthly-only result — the field's own meaning would need to
  become conditional on `calculationMethod`, a real semantic widening.
- **`no_common_direction` frequency/role**: under Option A/B today, this
  state occurs in 46.5% of algorithmic cases (#2497). Under Option C, an
  equivalent "direction unavailable" state would occur in only 3.1% of
  cases (§9) — the state does not disappear, but its frequency and,
  arguably, its product significance would change substantially, which
  the Runtime Contract's Section 8 Fail-safe table would need to reflect.

No Runtime Contract change is performed by this document.

---

## 27. Analytics Impact

**No instrumentation is invented or modified.** Recorded as likely future
implications only, per the task's explicit instruction:

- If Option C is adopted, distinguishing "strict success" (Category 1)
  from "fallback success" (Category 2) in analytics would likely require
  either a new `result_state` value or a new boolean/categorical property
  (e.g., a `fallback_used` flag) — not designed here.
- `no_common_direction`'s product-result classification
  (`compass-posthog-query-contract.md` §4's `VALID_NO_DIRECTION` bucket)
  would need to be re-examined: under Option C, the state that would map
  to "truly no direction" (Category 3) occurs far less often (3.1% vs
  46.5%), which could shift how that bucket is interpreted operationally,
  even without any instrumentation code change.
- The comparison boundary between Direction Availability Rate and
  Recommendation Availability Rate (#2502 §16) would remain unchanged in
  *definition*, but its *numerator composition* would change if Category
  2 results are treated as Direction-Availability-valid (which, per this
  audit's own definition, they are — §4, §8).

No PostHog query, dashboard, event, or property was created or modified.

---

## 28. New Evidence Impact on #2503

Per task §28, **not a rewrite of #2503** — only which specific #2503
claims are affected:

| #2503 claim | Status after this audit |
|---|---|
| §22 Axis 3 cell, Option C: "NOT QUANTIFIABLE" | **CONFIRMED SUPERSEDED WITH DATA** — now measured at 96.9% (§8). The axis conclusion itself ("Option C's availability was unknown") is resolved, not contradicted. |
| §21 GAINS for Option C: "plausibly raises availability... magnitude unmeasured" | **STRENGTHENED** — magnitude is now known precisely: +43.4pp overall, 93.4% recovery rate specifically among previously-empty cases (§10-§12). |
| §21 LOSES for Option C: "annual corroboration dropped on fallback" | **UNCHANGED, and now quantified** — this loss applies to exactly 422/972 (43.4%) of cases, not an unspecified fraction. |
| §22 Axis 2 (Semantic Consistency), Option C: "MODERATE... redefinition disclosed = consistent" | **UNCHANGED** — this audit's high availability number does not improve this rating; §18/§19 explicitly preserve the semantic caveat #2503 already recorded. |
| §22 Axis 9 (Runtime Contract Impact), Option C: "MODERATE (`calculationMethod` extension)" | **STRENGTHENED WITH SPECIFICS** — §26 above itemizes exactly what would need to change; the qualitative MODERATE rating is not contradicted, only detailed further. |
| §23 Recommended Option: B | **UNCHANGED** — this audit does not re-rank B against C; B's own axis strengths (§2503 §23) are untouched by Option C's new number. |
| §24 Alternative Option: C, "conditional on closing the Option C availability-measurement gap first" | **CONDITION NOW SATISFIED** — the gap #2503 flagged as blocking C's status as a credible Alternative is closed by this audit. C remains the Alternative, now with evidence behind it rather than an open question. |
| §25 Decision Dependencies, Promise B branch: "C... pending its own gap" | **GAP CLOSED** — see §20 above (STRONGLY SUPPORTS classification). |

No #2503 axis rating for Option A, B, D, or E is affected by this audit.

---

## 29. Product Decision Readiness

```
A — READY FOR MOTHER SHIP PRODUCT DECISION
```

Reasoning: every option among A, B, C, and D — the four concrete
Direction Logic designs the Mother Ship could plausibly choose among
today — now has a measured Direction Availability (53.5%, 53.5%, 96.9%,
97.5% respectively). Option E remains genuinely unquantified (§17, #2504
§10-§11), but per the task's explicit instruction, **Option E's absence
does not automatically block readiness** — E was always scoped as
requiring its own, separate Score Contract phase before it could even be
compared (#2504 §21), and the Mother Ship can choose among A/B/C/D (or
decline to adopt any of them) without resolving E first. Recommendation
Availability remains unmeasured for every option (§22), but this has
consistently been treated, since #2503, as a separate, still-OPEN Product
question (the Shrine Recommendation boundary,
`compass-product-contract.md` Section 2.1-5) rather than a Direction Logic
evidence gap — it does not differentiate among A/B/C/D and therefore does
not block a Direction Logic decision specifically.

---

## 30. Recommended Next Task

**Recommend exactly ONE, per task §30**:

```
Mother Ship Product Promise / Direction Logic Decision
```

With Direction Availability now measured for A, B, C, and D, and Promise
A/B/C's dependency mapping already established (#2503 §25, #2504 §12-§15,
sharpened by §19-§21 above), the single remaining blocker to adopting any
concrete option is a Product Promise and Direction Logic selection — a
Mother Ship decision, not an evidence question this audit chain can
resolve further. Option E's Score Contract audit remains available as a
*separate*, optional future path if the Mother Ship later wants to
compare a score-model design specifically — not a prerequisite for
deciding among A/B/C/D now.

---

## 31. Non-goals

This audit does **not**:

- Implement Option C (Monthly Fallback) in production
- Adopt or finalize a Product Promise
- Select a final Direction Logic option
- Change `kyusei.py`, `compass_runtime.py`,
  `compass_recommendation_orchestrator.py`, or any other production file
- Change the Product Contract, Runtime Contract, or Analytics Contract
- Change Recommendation Ranking
- Change Concierge behavior
- Execute any new production PostHog query
- Change PostHog configuration, add dashboards, or add analytics
  events/properties
- Measure or estimate Recommendation Availability for any option
- Resolve the OPEN Shrine Recommendation boundary
- Pursue Option E's Score Contract
- Touch Premium or Personal Continuity

---

## 32. Verification

```
$ git -C /Users/morietsu/Developer/jinja_app diff --check
(no output = no whitespace errors)
```

- **#2502 unchanged**: confirmed — zero changes under `docs/product/`.
- **#2503 unchanged**: confirmed — zero changes to
  `docs/audit/compass-direction-logic-product-decision.md`.
- **#2504 unchanged**: confirmed — zero changes to
  `docs/audit/compass-direction-logic-missing-evidence.md`.
- **#2505 unchanged**: confirmed — zero changes to
  `docs/audit/compass-monthly-direction-calculation-contract.md`.
- **#2506 production code untouched**: confirmed — zero changes to
  `backend/temples/domain/kyusei.py` or any other production file in this
  branch's diff.
- **Option C uses the canonical monthly helper**: confirmed — the audit
  script imports and calls `monthly_lucky_directions()` and
  `annual_lucky_directions()` directly from `temples.domain.kyusei`, with
  no reimplementation of either function's internal logic.
- **No shadow calculation logic**: confirmed — the script's only
  domain-specific logic is the Option C selection policy itself
  (intersection, then fallback), which the task explicitly permits as the
  hypothesis under evaluation; no formula, exclusion rule, or
  compatibility rule from either `kyusei.py` function is duplicated.
- **Matrix total = 972**: confirmed (§5, §10).
- **Option C category counts sum to 972**: confirmed (§10: 520+422+30=972).
- **Percentages reconcile**: confirmed — 53.5%+43.4%+3.1%=100.0% (§10);
  96.9%+3.1%=100.0% (§8-§9); 422/452=93.4% (§12); by-honmei/by-bucket/
  by-year subtotals each sum to their expected totals (§13-§15).
- **Synthetic data only**: confirmed — nine synthetic June-15 birthdates
  (1991–1999), no real user data (§6).
- **Temporary script absent from diff**: confirmed, §37 below.
- **git diff --check clean**: confirmed above.

```
$ git status --short
?? docs/audit/compass-monthly-fallback-availability.md

$ git diff --stat
(untracked, 1 file)

$ git diff --name-only
(none — untracked, not yet staged)
```

---

## Diff Scope Gate

Exactly one new file, matching the expected diff (task §37). No existing
file is modified. The analysis script
(`compass_option_c_matrix.py`) lives only in this session's scratchpad
directory (`/private/tmp/claude-501/.../scratchpad/`), never staged, never
committed.
