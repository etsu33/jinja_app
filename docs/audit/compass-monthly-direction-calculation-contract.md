> **Status: `PROPOSED — MOTHER SHIP / IMPLEMENTATION REVIEW REQUIRED`**
>
> [compass-direction-logic-missing-evidence.md](compass-direction-logic-missing-evidence.md)
> (#2504, merged) found Option C (Monthly Fallback) not safely quantifiable
> because the monthly-only lucky-direction calculation exists only as
> inline code inside `planned_visit_lucky_directions()`
> (`backend/temples/domain/kyusei.py:248-271`), reachable through no
> function of any visibility. This audit traces that calculation
> line-by-line, confirms no current production path can reuse it without
> either code change or reimplementation, and compares four possible
> calculation boundaries. **Recommended boundary: a new, additive public
> domain function in `kyusei.py`** — `monthly_lucky_directions(birthdate,
> visit_date)` — a pure extract-method refactor mirroring the calculation's
> existing sibling, `annual_lucky_directions()`, with zero behavior change
> to `planned_visit_lucky_directions()` or any existing caller.
>
> **Final Classification: `B — MONTHLY DOMAIN HELPER REQUIRED`.**
>
> No helper is implemented here. This document defines its contract only,
> as a **FUTURE IMPLEMENTATION TASK**. No production code, Product
> Contract, Runtime Contract, Recommendation Ranking, Concierge behavior,
> or Analytics instrumentation is changed. docs-only.

---

## 1. Executive Summary

Three prior audits established, in order: the evaluation framework
([#2502](../product/compass-product-logic-evaluation-framework.md)), a
five-option comparison recommending the current implementation
([#2503](compass-direction-logic-product-decision.md)), and an evidence-gap
closure pass that reproduced Option D's availability but left Option C's
own availability unmeasurable
([#2504](compass-direction-logic-missing-evidence.md)). This document
answers the narrower question #2504 could not: **what is the safest way to
make the monthly-only calculation a reusable, canonical boundary, without
touching current behavior?**

**Findings**:

- The monthly-only computation is a single, contiguous, 24-line block
  (`kyusei.py:248-271`) inlined inside `planned_visit_lucky_directions()`
  — not factored into any function, public or private.
- Some of its building blocks (`_solar_month_index()`, `year_star()`,
  five module-level constants) are already independently importable and
  reusable; the specific `start_star`/`month_center` derivation formula
  (`kyusei.py:250-252`) is not — it exists nowhere outside this one
  function body.
- Exactly two production call sites reuse `kyusei.py`'s direction
  functions today: `backend/temples/api_views_concierge.py:563-565`
  (Concierge Compat Mode) and `backend/temples/services/compass_runtime.py:77`
  (Compass). Neither would be affected by an additive helper.
- The safest boundary is a **public domain helper**, not a private one and
  not a Compass-runtime-local reimplementation — because
  `annual_lucky_directions()` already establishes exactly this pattern as
  a public, standalone, sibling calculation in the same module, and the
  existing test suite (`test_kyusei_direction.py`) only ever exercises
  `kyusei.py`'s functions through their public names, never an
  underscore-prefixed one.
- A Compass-runtime-local reimplementation (Option 4) is classified
  **high risk**: it would require transcribing `kyusei.py`'s proprietary
  formula into a second location, creating exactly the shadow-business-logic
  condition this task's hard rule (§7) forbids.

No helper is implemented. The contract for one is defined (§17) as a
**FUTURE IMPLEMENTATION TASK**, scoped to extraction and tests only — no
fallback logic, no Compass runtime change, no Product Promise decision.

---

## 2. Background

[#2504](compass-direction-logic-missing-evidence.md) §5 found:

> "no function or helper of any visibility, public or private, contains
> the monthly-lucky-direction computation in isolation... Neither is done
> here" — i.e. #2504 correctly declined to either modify `kyusei.py` or
> reimplement its formula, and recorded Option C's Direction Availability
> as `NOT SAFELY QUANTIFIABLE WITHOUT A PRODUCTION CONTRACT / HELPER`.

This audit picks up exactly where #2504 stopped: not to quantify Option C,
and not to decide whether Option C should ever be adopted, but to
determine — as a pure architecture/contract question — what a safe,
canonical calculation boundary for the monthly-only signal would look
like, so that a future, separate implementation PR (§21) has a concrete,
reviewed contract to build against instead of an open question.

---

## 3. Audit Question

> Given that the monthly-only lucky-direction calculation is currently
> inlined and unreusable, what is the smallest, safest, behavior-preserving
> calculation boundary that would expose it — and where should that
> boundary live?

This audit does not decide whether to implement that boundary, and does
not decide whether Option C should be adopted once it exists.

---

## 4. Current Calculation Trace

Traced against current `develop` (confirmed no drift since #2504's
baseline commit `5f560e3e`: `git diff 5f560e3e develop -- backend/
apps/web/` is empty).

| Stage | Function / constant | File : lines | Input | Output | Reusable outside parent? | Visibility |
|---|---|---|---|---|---|---|
| 1. Parse birthdate | `parse_birthdate()` | `kyusei.py:62-90` | raw birthdate string | `date` or `None` | YES | public |
| 2. Resolve honmei star | `honmei_star()` | `kyusei.py:130-140` | birthdate string | `KyuseiResult` (`num`, `ki_year`, ...) or `None` | YES | public |
| 3. Parse target/visit date | `parse_birthdate()` (reused) | `kyusei.py:62-90`, called at `kyusei.py:241` | visit_date string | `date` or `None` | YES | public |
| 4. Annual lucky directions | `annual_lucky_directions()` | `kyusei.py:191-223`, called at `kyusei.py:245` | birthdate, `today=planned` | dict incl. `luckyDirections`, `excludedDirections`, `targetYear` | YES | public |
| 5. Solar-month index | `_solar_month_index()` | `kyusei.py:229-236`, called at `kyusei.py:248` | target `date` | int (0-11) | YES (importable; underscore-prefixed) | private |
| 6. Target-year ki_year | `year_star()` | `kyusei.py:142-155`, called at `kyusei.py:249` | `today=planned` | `KyuseiResult` incl. `ki_year` | YES | public |
| 7. Month-governing star derivation | inline arithmetic | `kyusei.py:250-252` (`branch`, `start_star`, `month_center`) | `ki_year`, `month_index` | int (1-9), the "month center star" | **NO — not factored into any function** | not exposed at all |
| 8. Per-direction star mapping | inline dict comprehension | `kyusei.py:253-256` | `month_center`, `DIRECTION_PALACES` (public constant) | `{direction: star}` dict | **NO — not factored into any function** (though `DIRECTION_PALACES` itself is reusable) | not exposed at all |
| 9. Identity-based exclusion | inline loop | `kyusei.py:257-263` | `stars` dict, `honmei.num`, `month_index`, `SOLAR_MONTH_DIRECTIONS`/`OPPOSITE_DIRECTION` (public constants) | `excluded: set[str]` | **NO — not factored into any function** | not exposed at all |
| 10. Element-compatibility filter | inline loop | `kyusei.py:264-271` | `stars`, `excluded`, `honmei_element`, `STAR_ELEMENTS`/`GENERATES` (public constants) | `monthly_lucky: list[str]` | **NO — not factored into any function** | not exposed at all — **this is the monthly-only result itself, and it is discarded immediately after this line** |
| 11. Intersection with annual | inline list comprehension | `kyusei.py:272` | `annual["luckyDirections"]`, `monthly_lucky` | `combined: list[str]` (the function's actual return value) | YES (this is `planned_visit_lucky_directions()`'s own public return, but only the *intersection*, never `monthly_lucky` itself) | public |

**Stages 7-10 are the exact, contiguous, unreusable block** (`kyusei.py:248-271`,
24 lines). Every constant and helper it touches (`DIRECTION_PALACES`,
`OPPOSITE_DIRECTION`, `STAR_ELEMENTS`, `GENERATES`, `SOLAR_MONTH_DIRECTIONS`,
`_solar_month_index()`, `year_star()`) is independently reusable — but the
formula that combines them (`start_star`/`month_center`, and the two
filtering passes) exists nowhere as a callable unit. `monthly_lucky`
(stage 10's output) is computed, then immediately reduced to `combined`
(stage 11) and discarded — the caller (`compass_runtime.py`, §5) never
sees it.

---

## 5. Current Responsibility Boundary

Re-confirmed against current code (unchanged from #2502/#2503's own
findings):

```
Layer A (九星/方位計算, kyusei.py):
  owns: honmei-star resolution, annual lucky directions, the full
  annual∩monthly intersection (as a single opaque calculation)
  does NOT currently own: an independently reusable monthly-only result

Layer B (Compass Runtime, compass_runtime.py):
  owns: interpreting Layer A's output (dict / NoCommonDirectionResult / None)
  does NOT own: any direction calculation itself — compass_runtime.py's own
  module docstring states it "Reuses kyusei.py's planned_visit_lucky_directions()
  as the sole calculation source" (kyusei.py:12-14) and performs no
  arithmetic of its own beyond emptiness checks (compass_runtime.py:77-90)
```

`compass_runtime.py:77-90` receives only the already-intersected `result`
dict — `targetDate`, `targetYear`, `solarMonthIndex`, `referenceDirections`
(= the intersection), `calculationMethod`, and (via `result.get("luckyDirections")`)
the emptiness check that decides `NoCommonDirectionResult` vs. a full
payload. It has no access to, and makes no use of, `monthly_lucky` or
`annual`'s own `luckyDirections` as separate values.

---

## 6. Monthly Calculation Ownership

Per the task's explicit instruction not to collapse domain calculation
with product policy:

```
"Given a valid birthdate and target date, return monthly lucky directions"
  -> belongs to A. Domain astrology calculation layer (kyusei.py)

"When to use monthly lucky directions as a fallback, if annual∩monthly is empty"
  -> belongs to B. Compass Product Runtime layer (compass_runtime.py)
```

This mirrors the split `kyusei.py`/`compass_runtime.py` already
implements for the intersection case today: `kyusei.py` computes *what*
the directions are (a pure, product-context-free calculation —
`compass-product-contract.md` Section 1's "Signal Reuse" framing);
`compass_runtime.py` decides *what it means* for Compass specifically
(`NoCommonDirectionResult` vs. a payload). A monthly-only helper should
extend the same split, not blur it: `kyusei.py` would gain a new pure
calculation output; **no fallback decision logic belongs in `kyusei.py`**,
and this audit does not propose adding any.

**C. Recommendation layer**: not a candidate owner for this calculation at
all — it operates only after a direction (of any kind) has already been
resolved and handed to Layer C/D (`compass_direction_filter.py`,
`concierge_chat_ranking.py`), which is unaffected by where or how the
direction itself was computed.

---

## 7. Existing Reuse Possibility

**NO** — confirmed, not assumed. §4's trace shows the specific blocking
reason precisely: stages 7-10 (`kyusei.py:248-271`) have no existing
callable form. Calling `planned_visit_lucky_directions()` itself only
returns `combined` (the intersection); calling `annual_lucky_directions()`
only returns the annual side. Neither call, alone or combined, can recover
`monthly_lucky`, because `combined ⊆ monthly_lucky` is not invertible —
`monthly_lucky` may contain directions absent from `combined` whenever
`annual["luckyDirections"]` excludes them, and the API surface gives no
way to observe those extra directions.

---

## 8. Option 1 — Current Reuse (No Code Change)

**Not viable.** Confirmed by §4, §7 — no combination of existing public or
private `kyusei.py` calls can reconstruct `monthly_lucky` without either
adding code or reimplementing the formula.

- Exactness: N/A (not achievable)
- Reproducibility: N/A
- Shadow-logic risk: N/A (the option itself does not exist; attempting it
  would collapse into Option 4's reimplementation risk)
- Testability: N/A
- Concierge risk: N/A (moot — nothing to call)

---

## 9. Option 2 — Private Helper in `kyusei.py`

Concept only, **not implemented**: extract stages 7-10 into a
private helper, e.g. `_monthly_lucky_directions(birthdate: Optional[str],
visit_date: Optional[str]) -> Optional[Dict[str, Any]]`, called internally
by `planned_visit_lucky_directions()` in place of the current inline block.

- **Behavior preservation**: HIGH — a pure extract-method refactor;
  `planned_visit_lucky_directions()`'s own inputs/outputs are unaffected
  if the extracted function reproduces the exact same 24 lines verbatim.
- **Shared-function risk**: NONE beyond what already exists — Concierge
  never imports underscore-prefixed names from `kyusei.py` today (§10),
  and a private helper by definition signals "not for external reuse,"
  so it would not create a new expectation of stability for Concierge or
  any other caller.
- **Testability**: technically possible (Python does not block importing
  `_foo`), but **breaks the repo's own established convention** — every
  existing test in `test_kyusei_direction.py` imports and exercises only
  the two current public functions (`annual_lucky_directions`,
  `planned_visit_lucky_directions`); no existing kyusei test imports an
  underscore-prefixed helper directly (confirmed by inspection, §16
  below).
- **Visibility**: signals internal-only, which is honest about current
  reality (only `kyusei.py` itself would call it) but forecloses the
  future Compass reuse this whole audit exists to unblock (§21, §24
  Outcome B) without a second migration later.
- **Future Compass reuse**: possible, but `compass_runtime.py` importing
  a `_`-prefixed name from another module would itself be an
  unconventional pattern not currently used anywhere in this codebase
  (`compass_runtime.py`'s own imports are all public names, §4).

---

## 10. Option 3 — Public Domain Helper in `kyusei.py`

Concept only, **not implemented**: expose the same extracted logic as a
public function, e.g. `monthly_lucky_directions(birthdate: Optional[str],
visit_date: Optional[str]) -> Optional[Dict[str, Any]]`, as a direct
sibling to the already-public `annual_lucky_directions()`.

- **Domain clarity**: HIGH — `kyusei.py` already treats "annual lucky
  directions, standing alone" as a first-class public concept
  (`annual_lucky_directions()`, `kyusei.py:191-223`). "Monthly lucky
  directions, standing alone" is symmetrically the same kind of concept —
  the module's own existing design already implies this symmetry; it is
  simply incomplete today.
- **Public API responsibility**: matches `compass-product-contract.md`
  Section 1's existing framing of `kyusei.py` as a "product-context-free
  pure calculation module" available for Signal Reuse — a new pure,
  deterministic, side-effect-free function is consistent with that
  charter, not an expansion of it.
- **Concierge impact**: NONE by default — additive, and Concierge's two
  existing call sites (`api_views_concierge.py:563,565`) would remain
  byte-for-byte unchanged unless a future, separate PR deliberately wires
  Concierge to the new function (not proposed here or by any prior audit).
- **Compatibility**: a new function cannot break any existing caller —
  there is nothing to be incompatible with.
- **Testability**: HIGH — fits the existing convention exactly (§9's
  finding): a new public function tested the same way its sibling
  `annual_lucky_directions()` already is.
- **Future reuse**: this is the *only* option that cleanly unblocks a
  future Option C quantification (§16) using the same
  call-the-unmodified-function-directly methodology #2497/#2503/#2504 all
  established, without asking a future auditor to import a private name
  (Option 2) or duplicate logic (Option 4).

---

## 11. Option 4 — Compass Runtime-local Logic

Concept only, **not implemented, and not recommended**: reconstruct or
approximate monthly-only behavior inside `compass_runtime.py`, without
touching `kyusei.py` at all.

**Classified HIGH RISK**, per the task's own instruction (§8 of the task):

- **Duplicated business logic**: to reproduce `monthly_lucky` correctly,
  `compass_runtime.py` would need its own copy of the `start_star`/
  `month_center` formula (`kyusei.py:250-252`) — this is precisely the
  shadow-business-logic condition §7 of the task (and #2497's own
  methodology principle, inherited by #2502/#2503/#2504) forbids. It
  would create a **second source of truth** for the same astrological
  calculation, in direct violation of this audit's own "No Shadow
  Business Logic Rule" (§7 above).
- **Semantic drift**: if `kyusei.py`'s formula is ever revised (bugfix,
  algorithm change), a duplicated copy in `compass_runtime.py` would
  silently diverge unless someone remembers to update both — with no
  compiler or test-suite mechanism forcing that synchronization, since
  the two would be textually independent.
- **Divergence from Concierge**: `api_views_concierge.py:563` calls
  `kyusei.py`'s own `planned_visit_lucky_directions()` directly. If
  Compass's monthly-only signal were computed by a *different* code path
  than Concierge's intersection, the two products' outputs could
  silently diverge for the same birthdate/date even though both claim to
  derive from "the same" kyusei calculation — undermining the
  Signal-Reuse-not-Authority-Reuse principle
  (`compass-product-contract.md` Section 1) this whole audit chain has
  consistently protected.
- **Ownership mismatch**: `compass_runtime.py`'s own module docstring
  (§4, stage list) already states its architectural commitment: "Reuses
  kyusei.py's `planned_visit_lucky_directions()` as the **sole**
  calculation source." Option 4 would directly contradict this
  self-documented boundary.

---

## 12. Comparison Matrix

| Approach | Single Source of Truth | Behavior Preservation | Testability | Concierge Safety | Option C Quantifiable | Risk |
|---|---|---|---|---|---|---|
| **Existing reuse (Option 1)** | N/A — not achievable | N/A | N/A | N/A (moot) | NO | N/A (blocked, not merely risky) |
| **Private kyusei helper (Option 2)** | YES | HIGH | MODERATE (breaks repo's public-only test convention) | NO CONCIERGE BEHAVIOR CHANGE | YES, once extracted | LOW |
| **Public kyusei helper (Option 3)** | YES | HIGH | HIGH (matches existing convention) | NO CONCIERGE BEHAVIOR CHANGE | YES, once extracted | LOW |
| **Compass runtime-local (Option 4)** | **NO — creates a second implementation** | UNVERIFIABLE / AT RISK OF DRIFT | LOW (would need its own parallel test suite) | Technically NO CONCIERGE BEHAVIOR CHANGE, but undermines Signal-Reuse principle | Technically yes, but the number would describe a **different, shadow algorithm** — not trustworthy as Option C evidence | **HIGH** |

---

## 13. Concierge Impact

Confirmed callers, re-verified this session (`grep -rn
"planned_visit_lucky_directions\|annual_lucky_directions" --include="*.py"`,
excluding test files and one docstring-only mention in
`concierge_input_contract.py:306`):

```
backend/temples/api_views_concierge.py:563  planned_visit_lucky_directions(...)
backend/temples/api_views_concierge.py:565  annual_lucky_directions(...)
```

Exactly these two call sites, unchanged since #2497/#2503/#2504.

| Option | Classification |
|---|---|
| 1 (existing reuse) | N/A — not achievable |
| 2 (private helper) | **NO CONCIERGE BEHAVIOR CHANGE** — additive, Concierge does not import it |
| 3 (public helper) | **NO CONCIERGE BEHAVIOR CHANGE** — additive, Concierge does not import it unless a separate future PR deliberately wires it in (not proposed) |
| 4 (runtime-local) | Narrowly NO CONCIERGE BEHAVIOR CHANGE (Concierge's own code path is untouched), but this is the one option where **SHARED FUNCTION RISK re-emerges in a different form** — not because Concierge's code changes, but because a second, textually-independent formula could silently produce different results than Concierge's `kyusei.py`-derived ones for what should be "the same" monthly signal |

**Preferred future design, confirmed achievable**: existing Concierge
behavior remains unchanged under Option 2 or Option 3 — both are purely
additive.

---

## 14. Behavior Preservation Contract

If a future extraction PR (§21) is authorized, it must guarantee: for
every input currently accepted by `planned_visit_lucky_directions()`, the
refactored implementation produces **exactly** the same:

```
- luckyDirection / luckyDirections (the intersection, "combined")
- targetYear
- targetMonth
- solarMonthIndex
- visitDate
- calculationMethod ("annual_monthly_kyusei_v1", unchanged)
- excludedDirections (the union of annual + monthly exclusions, "all_excluded")
- source ("calculated")
- failure behavior: None whenever visit_date or birthdate is invalid,
  identical to current kyusei.py:243/246
```

The new function (`monthly_lucky_directions()` or
`_monthly_lucky_directions()`) would be additive and would not itself need
a preservation contract against prior behavior (it has no prior behavior
to preserve — it is new). Its correctness contract instead is:
**its output, restricted to the annual-agreeing subset, must equal exactly
what `planned_visit_lucky_directions()`'s `combined` value already is** —
i.e. `[d for d in annual_lucky_directions(...)["luckyDirections"] if d in
monthly_lucky_directions(...)["luckyDirections"]]` must equal
`planned_visit_lucky_directions(...)["luckyDirections"]` for every input,
by construction (both would share the identical extracted code for stages
7-10). This is the primary future test requirement (§18, test 2).

No calculation semantic change is authorized by this document, for either
the existing function or the new one.

---

## 15. API / Schema Impact

```
API response change:        NO   (no endpoint calls the proposed helper)
Frontend change:             NO   (Compass frontend is unaffected; no
                                   Compass code path calls the proposed
                                   helper in this document's scope)
Runtime Contract change:     NO   (CompassDirectionRuntime's Schema,
                                   compass-mvp-runtime-contract.md Section
                                   5, is untouched — compass_runtime.py
                                   does not call the new function)
Product Contract change:     NO   (the Product Promise remains undecided
                                   between A/B/C; a calculation helper's
                                   existence does not authorize adopting
                                   Monthly Fallback)
Analytics change:            NO   (no new event, property, or query)
```

Exposing a pure internal-to-`kyusei.py` domain helper, called by nothing
outside `kyusei.py` itself at the moment of its introduction, has no
observable effect on any API, frontend, Contract, or Analytics surface.
This holds for both Option 2 and Option 3 identically — the
public-vs-private choice affects import ergonomics and repo convention
alignment (§9, §10), not any of the five rows above.

---

## 16. Option C Quantification Method (Post-Helper)

**Not executed in this audit** — this section defines the method only, for
after a helper (§17) exists, per the task's explicit instruction not to
calculate a rate through duplicated logic.

```
Target methodology (unchanged from #2497/#2503/#2504):
  9 honmei outcomes × 12 solar-month buckets × 9 representative years
  = 972 deterministic cases

Option C policy (concept only, still not implemented):
  if annual_lucky_directions(...)["luckyDirections"] ∩
     monthly_lucky_directions(...)["luckyDirections"] is non-empty:
       use the intersection
  else:
       use monthly_lucky_directions(...)["luckyDirections"] alone

Direction Available   = the chosen Option C direction set is non-empty
Direction Unavailable = the chosen Option C direction set is empty
```

Once `monthly_lucky_directions()` (or its private equivalent) exists and
is verified against the Behavior Preservation Contract (§14), a future
audit would call it directly — exactly as this audit chain already called
`annual_lucky_directions()` for Option D (#2504 §7-§8) — against the same
9×12×9 grid, with **zero duplicated logic**, since the call would exercise
the actual production formula, not a transcription of it.

**Confirmed NOT calculated in this document** (per task §13's explicit
instruction, since no such helper exists yet — doing so now would require
exactly the reimplementation §7's hard rule forbids).

---

## 17. Helper Contract (If Required)

**FUTURE IMPLEMENTATION TASK — not implemented here.**

```
Suggested function responsibility:
  Given a valid birthdate and visit_date, return the monthly-chart-only
  lucky directions (kyusei.py stages 7-10, §4), independent of the annual
  chart's own luckyDirections — i.e. the "monthly_lucky" value that
  planned_visit_lucky_directions() already computes internally today,
  exposed as its own return value.

Suggested location:
  backend/temples/domain/kyusei.py, adjacent to annual_lucky_directions()
  and planned_visit_lucky_directions(), per §10's ownership/pattern finding.

Suggested name (not binding, subject to implementation-PR review):
  monthly_lucky_directions(birthdate, visit_date)   [public, Option 3, §16]

Inputs:
  birthdate: Optional[str]   (same parsing/shape as existing functions)
  visit_date: Optional[str]  (same parsing/shape as existing visit_date arg)

Outputs (proposed, mirroring annual_lucky_directions()'s own shape):
  {
    "luckyDirection": str | None,
    "luckyDirections": list[str],
    "targetYear": int,
    "solarMonthIndex": int,
    "calculationMethod": <new value, e.g. "monthly_kyusei_v1" -- exact
      naming is an implementation-PR decision, not fixed here>,
    "excludedDirections": list[str],   (the monthly-only exclusion set,
      distinct from planned_visit_lucky_directions()'s combined
      all_excluded value)
    "source": "calculated",
  }
  Exact field list is an implementation-PR decision; the constraint this
  document fixes is only that it must be derived from the identical
  extracted code that currently powers stages 7-10, not a re-derivation.

Failure semantics:
  None whenever birthdate or visit_date is invalid/unparseable — identical
  failure contract to annual_lucky_directions() and
  planned_visit_lucky_directions().

Determinism:
  Same birthdate + same visit_date -> same output, always (inherited
  automatically from the extracted code being byte-identical to the
  current inline implementation).

Privacy:
  No new privacy surface -- same two plain-string inputs
  (birthdate/visit_date) as every existing kyusei.py function; no PII is
  newly logged, stored, or exposed.

Caller compatibility:
  Purely additive. planned_visit_lucky_directions()'s own signature,
  return shape, and behavior for all existing inputs must be unchanged
  (Behavior Preservation Contract, §14) -- verified by keeping its
  existing test suite (test_kyusei_direction.py) green with zero
  modifications required to those tests' assertions.

Existing function integration:
  planned_visit_lucky_directions() would call the new function internally
  in place of its current inline stages 7-10, then compute `combined`
  exactly as it does today (kyusei.py:272) using the new function's
  luckyDirections field as the old monthly_lucky local variable's
  replacement.

Required tests:
  See §18.
```

---

## 18. Future Test Contract

Per task §22, required for the future implementation PR — **not written in
this docs-only audit**:

```
1. Current planned_visit_lucky_directions() behavior unchanged for every
   existing test case in test_kyusei_direction.py (zero test modifications
   needed, only possibly new tests added alongside).
2. New helper's luckyDirections, intersected with annual_lucky_directions()'s
   luckyDirections for the same input, equals exactly
   planned_visit_lucky_directions()'s own luckyDirections for that input
   (the Behavior Preservation Contract's core equivalence, §14).
3. Solar-month boundary tests (dates immediately before/after each of the
   11 fixed boundaries kyusei.py:230 defines).
4. All 9 honmei outcomes produce a well-formed result (empty or non-empty,
   never an exception) for the new helper.
5. Representative multiple-year coverage (matching the existing 9-year
   convention #2497/#2503/#2504 established).
6. At least one empty-monthly-direction case.
7. At least one non-empty-monthly-direction case.
8. Invalid visit_date behavior (None returned, no exception).
9. Invalid birthdate behavior (None returned, no exception).
10. Concierge regression: existing api_views_concierge.py tests
    (unmodified) remain green, confirming the new function's introduction
    does not alter Concierge's own call path in any way.
11. All existing kyusei.py tests (test_kyusei_direction.py's current 7
    tests) remain green without modification.
```

---

## 19. Recommended Boundary

**Public Domain Helper in `kyusei.py`** (Option 3, §10), not private
(Option 2), and explicitly not Compass-runtime-local (Option 4, §11).

Grounded in §16's own decision criteria:

- **Is monthly direction a meaningful standalone domain concept?** YES —
  `kyusei.py` already treats the annual equivalent this way
  (`annual_lucky_directions()`); the module's own existing design implies
  the same treatment for monthly.
- **Will Compass need it directly?** Plausibly, if Option C is ever
  authorized (§24 Outcome B) — a public function avoids a second migration
  later.
- **Could another product safely reuse it?** At minimum, symmetrically as
  safe as `annual_lucky_directions()` already is — Concierge's own code
  already demonstrates a comfortable precedent for calling either the
  annual-only or the intersection function depending on whether
  `visit_date` is present; a monthly-only option is not a larger
  conceptual leap.
- **Is exposing it likely to encourage misuse?** LOW — it is a pure,
  deterministic, side-effect-free calculation, identical in risk profile
  to its already-public sibling.
- **Does it belong in the stable domain API?** YES, per
  `compass-product-contract.md` Section 1's existing charter for
  `kyusei.py` as reusable, product-context-free calculation.
- **Can tests exercise it sufficiently if private?** Technically yes, but
  doing so would be the first instance in this codebase of a test
  importing an underscore-prefixed `kyusei.py` name — confirmed by
  inspection of `test_kyusei_direction.py`'s current imports (§9).

**Status: `PROPOSED — MOTHER SHIP / IMPLEMENTATION REVIEW REQUIRED`.**

---

## 20. Final Classification

```
B — MONTHLY DOMAIN HELPER REQUIRED
```

Evidence: §4/§7 confirm Option C cannot be quantified with current code
(rules out A). §9-§12 confirm extraction (private or public) is a
low-risk, behavior-preserving, well-precedented refactor (rules out C —
extraction is not architecturally unsafe). §5-§6 confirm the Domain vs.
Product-Policy responsibility split is already clear and consistent with
existing architecture (rules out D — responsibility is not unclear, only
currently unimplemented).

---

## 21. Next Task

**Recommend exactly ONE, per task §26**:

```
PR: Extract canonical monthly lucky-direction helper

Scope:
  - kyusei.py extraction only (stages 7-10, kyusei.py:248-271, moved
    verbatim into a new public function per §17's contract)
  - New tests per §18
  - Zero behavior change to planned_visit_lucky_directions() or any
    existing caller

Explicitly NOT in this future PR's scope:
  - Monthly Fallback implementation (Option C policy itself)
  - Compass runtime behavior change
  - Product Promise decision
  - UI / frontend change
  - Analytics change
  - Re-running the Option C 972-case matrix (a separate, subsequent audit,
    once the helper exists and its equivalence tests are green)
```

This separation (extraction PR, then a later, separate Option C
measurement audit) mirrors how #2503/#2504 already separated "measure the
existing options" from "adopt an option" — the same discipline applies
here to "expose the calculation" versus "use it for a policy decision."

---

## 22. Non-goals

This audit does **not**:

- Implement the proposed helper (public or private)
- Modify `kyusei.py`, `compass_runtime.py`, or any other production file
- Implement Monthly Fallback (Option C) or quantify its availability
- Change the Product Contract or finalize a Product Promise
- Change the Runtime Contract
- Change Recommendation Ranking
- Change Concierge behavior or `api_views_concierge.py`
- Change Analytics instrumentation, execute a new PostHog query, or touch
  PostHog configuration
- Touch Option E / the Score Contract question (#2504 §10-§11, unchanged)
- Touch Premium or Personal Continuity

---

## 23. Verification

```
$ git -C /Users/morietsu/Developer/jinja_app diff --check
(no output = no whitespace errors)
```

- **#2502 unchanged**: confirmed — `git diff` against `develop` shows zero
  changes under `docs/product/`.
- **#2503 unchanged**: confirmed — zero changes to
  `docs/audit/compass-direction-logic-product-decision.md`.
- **#2504 unchanged**: confirmed — zero changes to
  `docs/audit/compass-direction-logic-missing-evidence.md`.
- **Current `kyusei.py` accurately traced**: confirmed — every line
  citation in §4 re-read directly from current `develop`
  (`backend/temples/domain/kyusei.py`, HEAD `5f560e3e`, no drift).
- **All `planned_visit_lucky_directions()` callers inventoried**:
  confirmed — `grep -rn` re-executed this session across the full
  repository (not `backend/` alone), excluding test files; exactly two
  production call sites found (`api_views_concierge.py`,
  `compass_runtime.py`), matching #2497/#2503/#2504's prior findings, plus
  one docstring-only mention (`concierge_input_contract.py:306`, not a
  call) confirmed by direct inspection.
- **No shadow business logic introduced**: confirmed — no formula from
  `kyusei.py:248-271` was transcribed into any script, test, or document
  as executable logic; §16 explicitly declines to run any quantification
  that would require doing so.
- **No production files modified**: confirmed, §28 below.
- **git diff --check clean**: confirmed above.

```
$ git status --short
?? docs/audit/compass-monthly-direction-calculation-contract.md

$ git diff --stat
(untracked, 1 file)

$ git diff --name-only
(none — untracked, not yet staged)
```

---

## Diff Scope Gate

Exactly one new file, matching the expected diff (task §30). No existing
file is modified.
