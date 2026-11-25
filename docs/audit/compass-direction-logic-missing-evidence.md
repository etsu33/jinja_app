> **Status: `PROPOSED — MOTHER SHIP DECISION REQUIRED` (evidence-gap audit,
> not a Product Decision)**
>
> This document closes as much of [#2503](compass-direction-logic-product-decision.md)'s
> evidence gap as is safely possible without modifying production code, and
> records precisely what remains closed off and why. **Option D's 97.5%
> Direction Availability figure is independently reproduced** with a second,
> differently-sampled synthetic birthdate set (§7–§8) and its remaining 2.5%
> unavailability is now explained by manual trace against the actual
> production output, not guessed (§9). **Option C (Monthly Fallback) remains
> NOT SAFELY QUANTIFIABLE** — this audit's deeper inventory of `kyusei.py`
> confirms the blocking reason is more specific than "no public function
> exists": no function, public *or* private, exposes the monthly-only
> lucky-direction computation in isolation; the formula is inlined only
> inside `planned_visit_lucky_directions()` (§5–§6). **Option E remains
> `REQUIRES SCORE CONTRACT BEFORE QUANTIFICATION`** — no weights, thresholds,
> or availability numbers are invented (§10–§11).
>
> No production code, Product Contract, Runtime Contract, Recommendation
> Ranking, Concierge behavior, or Analytics instrumentation is changed.
> docs-only.

---

## 1. Executive Summary

[compass-direction-logic-product-decision.md](compass-direction-logic-product-decision.md)
(#2503, merged) compared five Direction Logic options on the ten axes fixed
by [compass-product-logic-evaluation-framework.md](../product/compass-product-logic-evaluation-framework.md)
(#2502) and recommended keeping Option B, with Option C as a conditional
Alternative — but left three evidence gaps open: Option C's Direction
Availability was NOT QUANTIFIABLE, Option D's 97.5% figure came from a
single measurement run, and Option E's missing contract fields were not
itemized. This audit closes what can honestly be closed:

1. **Option C**: still not safely quantifiable, but now with a precise,
   actionable technical reason (§5) instead of a general "not exposed"
   statement — and a concrete description of the minimal, additive,
   read-only helper that would unblock it (§6).
2. **Option D**: **REPRODUCED** — 948/972 = 97.5%, using an independently
   chosen synthetic birthdate set (different years, different day-of-month)
   against the same unmodified `annual_lucky_directions()` function and the
   same 9×12×9 grid. The by-honmei breakdown (12/108 empty for stars 1 and
   9, 0/108 for the other seven) matches #2503's original run exactly (§8).
   The remaining 2.5% is now explained by a hand-traced, code-verified
   mechanism, not asserted (§9).
3. **Option E**: fifteen contract fields a future Score Contract would need
   to define are itemized (§10), none are chosen, and the existing
   Ranking-layer `direction_signal` term (`recommendation-score-v2-current-design.md`)
   is confirmed to be a **separate, already-existing, Layer D mechanism**
   unrelated to the Layer B direction-confidence concept Option E describes
   (§10, §20 boundary note).

No prior #2503 axis conclusion is overturned by this new evidence — the one
NEW EVIDENCE IMPACT is a refinement of Option C's evidence classification
(from a general "not exposed" to a specific "no importable unit exists,
here is what one would need to look like") and additional depth on Option
D's Axis 2/5 (Semantic Consistency, User Comprehensibility) via the
root-cause mechanism (§19).

**Decision readiness: D — MULTIPLE MATERIAL EVIDENCE GAPS REMAIN** (§20) —
Option C's availability and Option E's contract are both still open, and
neither can be resolved by further analysis alone; both require a
follow-on decision or contract PR.

---

## 2. Audit Questions

This audit answers exactly four narrow questions, per task instruction —
nothing broader:

1. Can Option C Monthly Fallback be quantified reproducibly without
   modifying production code?
2. Does Option D Annual Fallback's previously observed 97.5% Direction
   Availability reproduce under the same methodology?
3. What exactly is still undefined for Option E Weighted Score Model?
4. How do Product Promise A/B/C affect which Option is logically
   preferable?

---

## 3. Canonical Sources

Read in full for this audit (no path assumed, all confirmed against
current `develop`):

| Document | Role |
|---|---|
| [compass-product-logic-evaluation-framework.md](../product/compass-product-logic-evaluation-framework.md) (#2502) | Immutable — vocabulary, ten axes, evaluation methods. Not changed by this audit. |
| [compass-direction-logic-product-decision.md](compass-direction-logic-product-decision.md) (#2503) | Immutable — prior comparison, PROPOSED recommendation (B), Alternative (C). Not changed by this audit. |
| [compass-direction-availability-product-decision.md](compass-direction-availability-product-decision.md) (#2497) | Source of the 972-case 9×12×9 methodology and the 53.5%/46.5% baseline, re-cited only. |
| [compass-direction-filter-unavailable-root-cause.md](compass-direction-filter-unavailable-root-cause.md) (#2496) | Source of the EXPECTED FAIL-SAFE classification precedent this audit's Option D root-cause finding (§9) follows. |
| `docs/product/compass-product-contract.md` | Confirmed unchanged; Section 2.1-5 Shrine Recommendation boundary still OPEN (relevant to §16). |
| `docs/product/compass-mvp-runtime-contract.md` | Confirmed unchanged; Section 5's annual-only prohibition still governs Option D (unchanged from #2503's finding). |
| `docs/analytics/compass-posthog-query-contract.md` | Confirmed unchanged; no new query executed against it (§21 boundary). |
| `docs/analytics/recommendation-score-v2-current-design.md` | Inspected to confirm the existing `direction_signal` Ranking term is unrelated to Option E's proposed Direction-confidence concept (§10, §20). |
| `backend/temples/domain/kyusei.py` (current `develop`) | Full function/constant inventory taken (§5) to determine Option C's exact blocking condition. |

---

## 4. Prior Evidence State (from #2503)

| Option | #2503 Direction Availability | #2503 evidence status |
|---|---|---|
| A | 53.5% (520/972) | MEASURED (#2497, re-cited) |
| B | 53.5% (520/972), identical to A | MEASURED (#2497, re-cited) |
| C | — | **NOT QUANTIFIABLE** (general reason: no public function exposes monthly-only directions) |
| D | 97.5% (948/972) | MEASURED — **single run only**, not independently reproduced |
| E | — | NOT QUANTIFIABLE UNTIL SCORE CONTRACT EXISTS (no fields itemized) |

---

## 5. Option C Quantification Method

**Full inventory of `backend/temples/domain/kyusei.py`** (284 lines, every
top-level `def`/`class`/constant, verified for this audit):

```
parse_birthdate()               public
_ki_year()                      private helper — importable, pure
_star_num_from_year()           private helper — importable, pure
_build_result()                 private helper — importable, pure
honmei_star()                   public
year_star()                     public
kyusei_signals()                public
DIRECTION_PALACES               public constant
OPPOSITE_DIRECTION              public constant
STAR_ELEMENTS                   public constant
GENERATES                       public constant
TAISAI_DIRECTIONS               public constant
SOLAR_MONTH_DIRECTIONS          public constant
annual_lucky_directions()       public — used for Option D (§7-§9)
_solar_month_index()            private helper — importable, pure
planned_visit_lucky_directions() public — the ONLY function containing the monthly-only calculation
```

**Finding, more precise than #2503's**: this is not merely "no *public*
function exposes monthly-only directions" — **no function or helper of any
visibility, public or private, contains the monthly-lucky-direction
computation in isolation.** The entire calculation —

```python
month_index = _solar_month_index(planned)
ki_year = year_star(today=planned).ki_year
branch = (ki_year - 4) % 12
start_star = 8 if branch in {0, 3, 6, 9} else 5 if branch in {1, 4, 7, 10} else 2
month_center = ((start_star - month_index - 1) % 9) + 1
stars = {direction: ((month_center + palace - 5 - 1 + 18) % 9) + 1 for direction, palace in DIRECTION_PALACES.items()}
# ... exclusion + element-compatibility filter ...
monthly_lucky = [...]
```

— is written inline inside `planned_visit_lucky_directions()`
(`kyusei.py:239-278`), with no factoring-out at all. The pieces that *are*
importable and reusable read-only (`_solar_month_index()`, `year_star()`,
`DIRECTION_PALACES`, `STAR_ELEMENTS`, `GENERATES`, `SOLAR_MONTH_DIRECTIONS`)
do not, by themselves, constitute the calculation — the specific formula
mapping `(ki_year, month_index)` to `start_star`/`month_center` (the
"which star governs this solar month" derivation) exists nowhere as an
importable unit.

**Compared with Option D**: `annual_lucky_directions()` is fully public and
self-contained — calling it directly (as §7–§9 does) requires zero
reimplementation. `planned_visit_lucky_directions()` returns only the
*intersection* (`combined`) of annual and monthly, never `monthly_lucky`
alone — so even calling this public function repeatedly cannot recover the
monthly-only set (annual ⊇ combined is not invertible; monthly_lucky may
contain directions not in `combined` whenever annual excludes them).

**Conclusion, per the task's explicit branching instruction (§5 of the
task)**: this cannot be done without either (a) `kyusei.py` exposing a new,
additive, read-only helper — a production code change, out of scope for
this audit — or (b) transcribing the `month_center`/`start_star` formula
into an audit-only script, which would constitute reimplementing business
logic outside the call-the-unmodified-function-directly methodology #2497
established and #2502/#2503 inherited. **Neither is done here.**

---

## 6. Option C Results

```
NOT SAFELY QUANTIFIABLE WITHOUT A PRODUCTION CONTRACT / HELPER
```

No shadow business logic was created for this audit. If the Mother Ship
later authorizes closing this gap, the minimal, lowest-risk unblocking
change (described here for reference only — **not implemented, not
proposed for adoption, not scoped as part of this docs-only audit**) would
be an **additive** function in `kyusei.py`, e.g.:

```
def monthly_lucky_directions(birthdate: Optional[str], visit_date: Optional[str]) -> Optional[Dict[str, Any]]:
    """Returns the monthly-chart-only lucky directions, independent of the
    annual chart. Read-only refactor: factors the existing inline monthly
    calculation out of planned_visit_lucky_directions() without changing
    that function's own signature, return shape, or behavior."""
```

This would be additive (new function, zero changes to any existing
function's signature or return contract), so it would not, by itself,
carry Concierge risk (`api_views_concierge.py:563` calls
`annual_lucky_directions`/`planned_visit_lucky_directions` only, and
neither would change). It is still a **production code change**, and
therefore explicitly out of scope for both this audit and #2503. It is
recorded here only so a future, narrowly-scoped PR (§26 Recommended Next
Task) has a concrete starting point instead of an open-ended question.

**Semantic limit, recorded regardless of whether Option C is ever
quantified** (per task §7): even if a future measurement showed Option C's
availability approaching 100%, that would not make it the better *product*
option by itself. Recorded explicitly:

```
MEASURED AVAILABILITY:           [not available — §5, §6]
PRODUCT SEMANTIC IMPLICATION:    Under Option C, a fallback result is no
                                  longer "the direction annual AND monthly
                                  both support" — it becomes "the direction
                                  this month's chart alone supports, when
                                  the year's chart does not corroborate it."
                                  This is a real change in what the shown
                                  direction *means*, not merely a
                                  presentation change (contrast with
                                  Option B, #2503 §7). No claim about
                                  astrological/spiritual correctness is
                                  made or implied by this document.
```

---

## 7. Option D Reproduction Method

Per task §8, this audit does **not** copy #2503's number — a second,
independent measurement was executed against current `develop`.

**Independence from #2503's original run**:

| | #2503 original run | This audit's reproduction |
|---|---|---|
| Synthetic birth years | 1975–1983 (one per honmei num) | 2000–2008 (one per honmei num) |
| Synthetic birth day | June 15 | September 10 |
| Function called | `annual_lucky_directions()`, unmodified | Same function, re-imported fresh this session |
| Grid | 9 honmei × 12 solar-month-bucket representative dates × 9 years (2022–2030) = 972 | Identical grid shape |
| Solar-month bucket boundaries/representative dates | `_solar_month_index()`'s actual boundaries, mid-bucket representative dates | Identical (re-read from source, not reused verbatim from the prior script) |
| Script location | Session scratchpad, not committed | New script, session scratchpad, not committed |
| Django/DB setup | `settings.configure(USE_TZ=True, TIME_ZONE="Asia/Tokyo")`, no DB access | Identical |

`git log -1 --oneline` at the time of this run: `5f560e3e` (the #2503
merge commit) — confirmed identical to `develop` HEAD, no code drift since
#2503's original measurement.

---

## 8. Option D Results

```
TOTAL CASES: 972
AVAILABLE (annual-only, non-empty): 948
EMPTY (annual-only, empty):          24
AVAILABLE %: 97.5%
EMPTY %:      2.5%
```

**Classification: `REPRODUCED`.**

By-honmei breakdown, compared directly against #2503's original figures:

| Honmei | #2503 original (empty/108) | This audit (empty/108) | Match |
|---|---|---|---|
| 1 | 12 | 12 | ✅ |
| 2 | 0 | 0 | ✅ |
| 3 | 0 | 0 | ✅ |
| 4 | 0 | 0 | ✅ |
| 5 | 0 | 0 | ✅ |
| 6 | 0 | 0 | ✅ |
| 7 | 0 | 0 | ✅ |
| 8 | 0 | 0 | ✅ |
| 9 | 12 | 12 | ✅ |

Exact match on every row, using a **completely disjoint synthetic
birthdate set** (different years, different day-of-month) — this rules out
the original 97.5% figure being an artifact of the specific birthdates
#2503 happened to choose. The per-honmei pattern is expected to be
birthdate-choice-invariant, since `annual_lucky_directions()`'s exclusion
logic depends only on `honmei.num` (not the exact birthdate) and the
target date's own `year_star()` — this reproduction confirms that
invariance holds in practice, not just in theory.

By-solar-month-bucket breakdown (this audit, new — not computed by #2503):

```
Every one of the 12 solar-month buckets: 2/81 empty (2.5%), uniformly.
```

The empty rate is **flat across all twelve solar-month buckets** — further
confirming the unavailability is driven entirely by `(honmei star, target
year)`, not by which month within the year is chosen (annual-only
calculation, by construction, does not depend on solar-month bucket at
all — see §9's mechanism).

By-year breakdown (this audit, new): non-uniform across the 9 sampled
years (concentrated in 2 of the 9 years for this run's birthdate set) —
this is expected and not a discrepancy from #2503, since #2503 did not
publish a by-year table to compare against; the total and by-honmei
figures (the only two breakdowns #2503 did publish) match exactly.

---

## 9. Option D Remaining Unavailability Cause

**Not guessed — traced by hand against the actual documented formula,
cross-validated against the real function's actual output for one
concrete empty case.**

Sample case: honmei star 1 (birthdate `2008-09-10` in this audit's table),
target date `2023-02-20`.

**Step 1 — confirm via the real function call (already executed, §8)**:

```
annual_lucky_directions("2008-09-10", today=date(2023,2,20))
  -> excludedDirections: ["北東","南東","南西","西","北西"]  (5 of 8 directions)
  -> luckyDirections: []
```

**Step 2 — manual trace of `kyusei.py:191-223`'s documented formula**
(quoted directly from source, not reimplemented as a separate executable
artifact) to explain *why*:

```
annual.num = year_star(today=2023-02-20).num = 4   (target-year-only, birthdate-independent)
stars = {direction: ((4 + palace - 5 - 1 + 18) % 9) + 1 for direction, palace in DIRECTION_PALACES.items()}
      = {北:9, 北東:7, 東:2, 南東:3, 南:8, 南西:1, 西:6, 北西:5}

five_yellow (star==5)          -> 北西  -> excluded: {北西, opposite(北西)=南東}
honmei_direction (star==1)     -> 南西  -> excluded: {南西, opposite(南西)=北東}
taisai (ki_year=2023 -> index3 -> "東") -> excluded: {opposite(東)=西}

excluded = {北西, 南東, 南西, 北東, 西}   <- matches the real function's actual output exactly
remaining (non-excluded) = {北, 東, 南}   -> stars 9, 2, 8   -> elements 火, 土, 土

honmei_element = STAR_ELEMENTS[1] = 水
compatible elements for 水 = {水 (same), 木 (水 generates 木), 金 (金 generates 水)}

remaining directions' elements {火, 土, 土} ∩ compatible {水, 木, 金} = ∅
  -> luckyDirections = []   <- matches the real function's actual output exactly
```

Both intermediate facts this hand trace predicts (`excludedDirections` set,
and the empty `luckyDirections` result) match the real, unmodified
function's actual output exactly — this is a verification of the
already-obtained measurement's mechanism, not a parallel or shadow
calculation used to produce a new metric.

**Root cause, stated generally**: `annual_lucky_directions()` applies two
sequential, independent filters — (1) **identity-based exclusion**
(five-yellow direction + its opposite, the honmei-star's own direction +
its opposite, and the taisai direction's opposite — up to 5 of 8
directions), then (2) **element-compatibility filtering** (same element as
honmei, or a generates-relationship) over whatever directions survive
filter 1. For honmei stars 1 (水) and 9 (火) specifically, in the years
where filter 1 happens to leave exactly the directions whose elements are
disjoint from the honmei star's compatible-element set, **filter 2 has
nothing left to pass**, and the result is empty — independent of month,
and independent of which specific birthdate maps to that honmei number.

This is the same **structural, deterministic, EXPECTED** pattern class
[#2496](compass-direction-filter-unavailable-root-cause.md) already
classified for the intersection case (`A — EXPECTED FAIL-SAFE`) — not a
code defect, and not evidence that annual-only calculation is "broken."
**This matters for Product Promise B/C** (§13, §14): even under Option D,
a small but real and structurally-recurring residual unavailability (2.5%,
concentrated in exactly 2 of 9 honmei stars) would remain — "annual
fallback" does not mean literally-always-available.

---

## 10. Option E Missing Score Contract

Per task §10, fields itemized, **none chosen or valued**:

| Contract field | Currently defined anywhere? | Note |
|---|---|---|
| Annual signal representation | NO | Would need to define what "annual supports direction X" contributes as a scoreable unit |
| Monthly signal representation | NO | Same, for monthly — and blocked by the same Option C exposure gap (§5) if the monthly signal must be isolated first |
| Weighting semantics | NO | No document proposes relative weights between annual/monthly/agreement |
| Score range | NO | Not defined as continuous, discrete tiers, or otherwise |
| Eligibility threshold | NO | At what score a direction becomes "shown" is undefined |
| Tie handling | NO | Two directions with equal score — undefined |
| Multiple-direction handling | NO | Whether more than one direction can be shown at different confidence levels is undefined |
| Zero-score / no-direction possibility | NO | Whether a score model can still produce "no direction at all," and under what condition, is undefined |
| `calculationMethod` vocabulary | NO | `compass-mvp-runtime-contract.md` Section 5 defines only `"annual_monthly_kyusei_v1"`; no score-model value exists |
| Explainability requirements | PARTIALLY, indirectly | `compass-product-contract.md` Section 8 (Signal-to-Explanation Rule) and Section 9 (non-deterministic-claim prohibition) would constrain any future explanation copy, but neither defines confidence-specific explainability rules |
| Deterministic ordering | NO | Not defined for a tie or near-tie scenario |
| Interaction with candidate filtering (Layer C) | NO | Whether Layer C receives a single winning direction or a ranked/weighted set is undefined |
| Isolation from Recommendation Ranking (Layer D) | **Boundary condition exists, not a full contract** | #2502 §19/§14 Axis 8 and #2503 §18 already establish that Layer D must remain untouched — but this is a boundary constraint, not a specification of how Layer B's score interacts with Layer C's population handoff |
| Concierge isolation | **Boundary condition exists, not a full contract** | #2502 §18 already establishes the Layer-B-confinement discipline generally; Option E's specific SHARED FUNCTION RISK (#2503 §17, highest of the five options) is flagged but not mitigated by any contract text |
| Test matrix | NO | No test plan or coverage target exists for a score model |
| Analytics state semantics | NO | `compass-posthog-query-contract.md` §1.1's six-state vocabulary has no confidence-tier concept; how a score model's output would map to `result_state` (new states? a new property?) is undefined |

**Boundary clarification (per task §20, explicitly checked for this
audit)**: `docs/analytics/recommendation-score-v2-current-design.md` already
defines a `direction_signal` term inside
`score_total_ranked = score_total_ranked_base + capped_behavior_contribution + profile_signal + direction_signal`
— **this is a pre-existing Layer D (Recommendation Ranking) term**,
already live, already outside this document's and #2502/#2503's scope
(Ranking is out of bounds for all Direction Logic options, #2502 §19).
**Option E's proposed "weighted score model" concerns Layer B — a
direction-confidence concept computed before any shrine candidate is even
considered — and is a distinct concept from this existing `direction_signal`
Ranking term.** No document confuses the two, and this audit confirms they
remain confirmed-separate mechanisms.

---

## 11. Option E Quantification Boundary

```
Without a Score Contract, Direction Availability for Option E is
NOT QUANTIFIABLE.
```

No weight, threshold, score formula, or availability percentage is
invented here (task §11). Status, restated exactly as #2503 left it,
**not penalized for the contract remaining incomplete**:

```
REQUIRES SCORE CONTRACT BEFORE QUANTIFICATION
```

No canonical document (Product Contract, Runtime Contract, PostHog Query
Contract, or `recommendation-score-v2-current-design.md`) already defines
such a contract for Direction confidence (§10) — the status is unchanged
from #2503.

---

## 12. Product Promise A Dependency

**Promise A — Strict Common Direction**: "I get a direction, or an honest
no-direction result"; annual/monthly agreement is the entire point.

- **Compatible Options**: **B** (implements this Promise faithfully and
  accurately, #2503 §23) and, as a pure-calculation baseline, **A** (same
  calculation, worse framing).
- **Conditionally Compatible Options**: none — C, D, and E all redefine
  what "the direction" means whenever the strict intersection is empty,
  which directly contradicts Promise A's premise that agreement itself is
  the deliverable.
- **Poorly Aligned Options**: **C, D, E** — each introduces a case where a
  direction is shown *without* annual/monthly agreement, which Promise A
  does not admit.
- **Missing Evidence**: none for this Promise — A/B's availability is fully
  measured (#2497), and C/D/E's incompatibility with Promise A is a
  structural/definitional fact, not an evidence gap.

---

## 13. Product Promise B Dependency

**Promise B — Actionable Monthly Direction**: "I get something actionable
to do this month"; the calculation method is not fixed by the Promise
itself (#2502 §12).

- **Compatible Options**: **C** (monthly fallback directly targets "this
  month," if it raises availability — magnitude unmeasured, §5–§6).
- **Conditionally Compatible Options**: **D** — technically raises
  availability further than C plausibly would (97.5% for annual-only,
  §8), but "actionable this month" is stretched by an annual-only signal
  more than by a monthly-only one, since D's signal is explicitly *not*
  month-specific. **E** — theoretically the best fit (could surface
  whichever signal, at whatever confidence, is actually available this
  month), conditional on the Score Contract (§10–§11) being defined first.
- **Poorly Aligned Options**: **A** — under Promise B, A's 46.5%
  no-direction rate directly fails "actionable," with no fallback offered.
  **B** — same underlying calculation as A; framing improvement alone does
  not make a no-direction result "actionable."
- **Missing Evidence**: **C's actual availability improvement is
  unmeasured** (§5–§6) — Promise B's best-supported option cannot be
  confirmed as *actually* better than A/B under this Promise until that
  gap closes.

---

## 14. Product Promise C Dependency

**Promise C — Direction-to-Shrine Guidance**: direction as an entry point,
guiding the user all the way to a selectable shrine candidate.

- **Compatible Options**: none, for any of A–E, in isolation — Promise C's
  core requirement (reaching an actual shrine candidate) is gated by the
  **Shrine Recommendation boundary**, which remains explicitly **OPEN**
  (`compass-product-contract.md` Section 2.1-5) regardless of which
  Direction Logic option governs (#2503 §12, unchanged by this audit).
- **Conditionally Compatible Options**: **C, D, E** — each *could*
  contribute to Promise C by raising the population of results that reach
  Layer C's candidate filtering, but none of them, by itself, resolves
  whether a no-direction (or now-fallback) result should surface
  purpose-only recommendations at all.
- **Poorly Aligned Options**: **A, B** — both, by construction, produce
  zero candidates whenever no direction resolves (46.5% of cases), and
  neither changes that.
- **Missing Evidence**: the Shrine Recommendation boundary decision itself
  (not a Direction Logic question) — this audit does not resolve it, and
  no amount of Direction Availability measurement can substitute for that
  separate Product decision.

---

## 15. Conditional Preferred Options

**Status: `PROPOSED — MOTHER SHIP DECISION REQUIRED`.** Analytical
dependencies only — not a final authorization (task §13).

```
IF Promise A is adopted:
    Preferred direction logic candidate = B
    (already implements Promise A faithfully; §12)

IF Promise B is adopted:
    Preferred direction logic candidate = C, CONDITIONAL on closing the
    Option C availability-measurement gap first (§5-§6, §13) — D is a
    weaker fit despite higher measured availability, because it stretches
    "this month" further than C would (§13). E is the strongest
    theoretical fit but requires a Score Contract phase before it can even
    be compared (§10-§11).

IF Promise C is adopted:
    No Direction Logic option alone is sufficient (§14) — the Shrine
    Recommendation boundary (compass-product-contract.md Section 2.1-5)
    must be resolved first, independent of which Direction Logic option
    is chosen alongside it.
```

This matches and is unchanged from #2503 §25's Decision Dependencies —
this audit adds no new conditional branch, only tightens the evidentiary
basis for the Promise B branch (§13).

---

## 16. Recommendation Availability Limitation

Restated and held unchanged from #2503 §12, per task §14's explicit
instruction not to expand into a new Recommendation audit:

```
Direction Availability:        algorithmically measurable (A/B/D measured
                                in this audit chain; C/E not measurable —
                                §5-§6, §10-§11)
Recommendation Availability:   NOT automatically derivable from Direction
                                Availability alone, for ANY option
```

Even where a direction is available (any option), reaching
`recommendation_success` additionally depends on shrine geography,
coordinate availability, direction-sector candidate filtering (Layer C),
and Evidence Gate outcomes (Layer C/D boundary, #2502 §5.1) — none of
which any Direction Logic option changes. No existing deterministic test
data was found, during this audit's scope, that could estimate
Recommendation Availability without a production DB query or a new test
fixture — both out of scope here (task §14: "do not expand scope unless
the evidence is already available"). This remains an open item, not
resolved by this audit, and not claimed to be.

---

## 17. Evidence Gap Table

| Item | Prior status (#2503) | This audit result | Remaining gap |
|---|---|---|---|
| Option C Direction Availability | NOT QUANTIFIABLE (general) | NOT SAFELY QUANTIFIABLE WITHOUT A PRODUCTION CONTRACT / HELPER (specific: no importable unit exists at any visibility) | Requires either a new additive `kyusei.py` helper (production code change) or accepted reimplementation risk — neither resolved here (§5-§6) |
| Option D Direction Availability | 97.5% (single run) | 97.5% (**independently reproduced**, second birthdate set, exact by-honmei match) | Root cause of residual 2.5% now explained (§9) — no further gap on this item |
| Option E Direction Availability | NOT QUANTIFIABLE UNTIL SCORE CONTRACT EXISTS | Same status, now with 15 itemized missing contract fields (§10) | Score Contract definition PR still required — not started here |
| Option E Contract Completeness | Not itemized | 15 fields itemized, 0 defined, 2 partially bounded by existing Layer-isolation principles (§10) | Full Score Contract PR is the closing action (§26) |
| Promise A dependency | Established (#2503 §25) | Confirmed unchanged; Compatible = A/B, Poorly Aligned = C/D/E (§12) | None — fully resolved for this Promise |
| Promise B dependency | Established (#2503 §25) | Refined — C is the best-supported candidate but its own availability gap (§5-§6) blocks confirming it | Same as Option C's own gap (§5-§6) |
| Promise C dependency | Established (#2503 §25) | Confirmed unchanged; blocked on the separate, non-Direction-Logic Shrine Recommendation boundary (§14) | Not a Direction Logic gap — a distinct, still-OPEN Product decision |

---

## 18. Current Option Snapshot

```
Option A — Strict Intersection
  Direction Availability: 53.5% (520/972)
  Evidence status: MEASURED (#2497, re-cited, unchanged)

Option B — First-Class No-Direction (current develop)
  Direction Availability: 53.5% (520/972), identical to A
  Evidence status: MEASURED (#2497, re-cited) + production-verified (#2501)

Option C — Monthly Fallback
  Direction Availability: NOT AVAILABLE
  Evidence status: NOT SAFELY QUANTIFIABLE WITHOUT A PRODUCTION CONTRACT / HELPER (§5-§6)

Option D — Annual Fallback
  Direction Availability: 97.5% (948/972)
  Evidence status: REPRODUCED (independent second measurement, §7-§9),
                    residual 2.5% mechanism explained

Option E — Weighted Score Model
  Direction Availability: NOT AVAILABLE
  Evidence status: REQUIRES SCORE CONTRACT BEFORE QUANTIFICATION (§10-§11),
                    15 missing contract fields itemized
```

This is not a re-run of #2503's full ten-axis matrix (task §17/§18 — this
document fills evidence gaps only).

---

## 19. New Evidence Impact on #2503

Per task §18, only where new evidence materially changes a specific
#2503 axis conclusion:

- **Axis 3 (Direction Availability), Option D cell**: **NO CHANGE** — the
  97.5% figure is confirmed, not revised, by independent reproduction
  (§7-§8). #2503's cell stands as originally written.
- **Axis 2 (Semantic Consistency) / Axis 5 (User Comprehensibility),
  Option D cells**: **NEW EVIDENCE IMPACT** — #2503 characterized D's
  semantic consistency as "weakest of the four... contradicts Compass's
  own MONTH-centric self-description" without a concrete mechanism. This
  audit's §9 root-cause trace adds a specific, code-verified fact: even
  under D, a structural ~2.5% residual unavailability remains,
  concentrated in exactly 2 of 9 honmei stars, for reasons unrelated to
  the month at all. This strengthens (does not reverse) #2503's existing
  WEAK rating on these two axes for Option D — an "annual fallback" is not
  quite "always available," and the reason why is now documented rather
  than asserted.
- **Axis 3, Option C cell**: **NEW EVIDENCE IMPACT (classification
  refinement, not a reversal)** — #2503 recorded "NOT QUANTIFIABLE"
  because "monthly-only directions are not exposed by a public production
  function." This audit's §5 inventory confirms the stronger, more precise
  fact: no function of *any* visibility exposes it, and identifies exactly
  where the boundary is (`kyusei.py:239-278`'s inline formula) and what a
  minimal fix would require. The evidence classification itself (NOT
  QUANTIFIABLE) is unchanged; its supporting detail is now actionable.
- **No other axis, for any option, is affected.** #2503's ten-axis matrix
  (its §22) is not rewritten by this document.

---

## 20. Product Decision Readiness

```
D — MULTIPLE MATERIAL EVIDENCE GAPS REMAIN
```

Reasoning: Option D's evidence gap (single-run measurement) is now fully
closed by this audit (§7-§9) — that alone would have supported a "B —
READY EXCEPT SCORE MODEL CONTRACT" classification. However, **Option C's
availability remains genuinely unresolved** (§5-§6), and it is not a minor
detail: §13 shows Promise B's best-supported candidate is precisely the
option this audit could not quantify. Two independent, materially
significant gaps — Option C's availability and Option E's Score Contract —
both remain open, neither resolvable without a follow-on PR. This is not
"A — READY" (two option's worth of evidence is genuinely missing), and it
is not narrowly "C — MONTHLY FALLBACK EVIDENCE STILL MISSING" alone,
because Option E's contract gap is equally unresolved and independent of
Option C's.

---

## 21. Mother Ship Decision Gate

Exact remaining choices left for the Mother Ship, per task §25 minimum:

```
1. Select final Product Promise A, B, or C (#2502 §12) — this audit
   sharpens the dependency mapping (§12-§15) but does not select one.
2. Decide whether Option E deserves a separate Score Contract phase before
   any further comparison is possible — 15 specific fields are itemized
   (§10) as exactly what such a phase would need to define; none are
   pre-decided here.
3. Decide whether to authorize a narrowly-scoped follow-on PR to close
   Option C's evidence gap (either via an additive kyusei.py helper, or by
   accepting a documented reimplementation-risk script) — §5-§6, §26.
4. Select a Direction Logic option after reviewing the conditional mapping
   in §15, once (2) and/or (3) above are resolved as far as the Mother
   Ship judges necessary.
```

This audit performs none of these four decisions.

---

## 22. Non-goals

This audit does **not**:

- Select a final Product Promise (A, B, or C)
- Adopt or finalize a Direction Logic option
- Implement Option C, D, or E
- Add a new function to `kyusei.py` (the additive helper described in §6
  is a reference design, not an implementation)
- Change the Product Contract, Runtime Contract, PostHog Query Contract,
  or Analytics Contract
- Change Recommendation Ranking (`concierge_chat_ranking.py`,
  `concierge_chat_candidates.py`, `build_chat_recommendations`, or the
  existing `direction_signal` Ranking term in
  `recommendation-score-v2-current-design.md`)
- Change Concierge behavior or `api_views_concierge.py`
- Execute any new production PostHog query
- Change PostHog configuration, add dashboards, or add analytics
  events/properties
- Resolve the OPEN Shrine Recommendation boundary
  (`compass-product-contract.md` Section 2.1-5)
- Re-run or rewrite #2503's ten-axis comparison matrix wholesale
- Touch Premium or Personal Continuity

---

## 23. Verification

```
$ git -C /Users/morietsu/Developer/jinja_app diff --check
(no output = no whitespace errors)
```

- **#2502 unchanged**: confirmed — `git diff` against `develop` shows zero
  changes under `docs/product/`.
- **#2503 unchanged**: confirmed — `git diff` against `develop` shows zero
  changes to `docs/audit/compass-direction-logic-product-decision.md`.
- **No production files changed**: confirmed — diff scope is exactly one
  new file under `docs/audit/` (§28).
- **Option C methodology uses existing logic only**: confirmed — §5's
  inventory used only `grep`/read access to already-existing source; no
  new logic was written or executed to attempt a monthly-only measurement.
- **Option D value independently reproduced**: confirmed — §7-§8, a second
  synthetic birthdate set, exact match on total/available/empty and the
  full by-honmei breakdown.
- **Option E has no invented score**: confirmed — §10-§11, fifteen fields
  itemized, zero values chosen.
- **Promise A/B/C definitions unchanged**: confirmed — this audit quotes
  #2502 §12's candidates verbatim, does not redefine them (§12-§15).
- **git diff --check clean**: confirmed above.

```
$ git status --short
?? docs/audit/compass-direction-logic-missing-evidence.md

$ git diff --stat
(untracked, 1 file)

$ git diff --name-only
(none — untracked, not yet staged)
```

---

## Diff Scope Gate

Exactly one new file, `docs/audit/compass-direction-logic-missing-evidence.md`,
matching the expected diff (task §28). No existing file is modified. Two
analysis scripts were used for this audit (§7's reproduction script and
§9's cross-validation, which reused §7's already-executed output) — both
live only in this session's scratchpad directory
(`/private/tmp/claude-501/.../scratchpad/`), never staged, never committed,
confirmed absent from `git status`.
