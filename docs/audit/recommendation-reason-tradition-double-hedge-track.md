# Recommendation Reason Tradition Double-Hedge Track

## Status

- Status: `TRACKED_SEPARATE_NON_BLOCKING`
- Recorded at: `2026-09-25`
- Origin: `W0-DB03 G6 Runtime QA`
- Origin audit: `docs/audit/shrine-expansion-wave0-db03-g6-runtime-qa.md`
- Owning module: `backend/temples/services/recommendation_reason_v4.py::_build_fact_text`
- Contract authority: `docs/core/recommendation-reason-contract.md`
- Safety contract: `TRADITION_ALWAYS_HEDGED`
- Production write: `NONE`
- Runtime code change: `NONE`
- G7 blocker: `NO`

This document keeps the Recommendation Reason tradition double-hedge wording issue on a dedicated track.

It does not change Recommendation Reason runtime behavior and does not reopen W0-DB03 G6.

---

## 1. Finding

When a `ShrineHistory` fact with:

```text
history_type = tradition
reason_strength.shrine_history = weakened
```

already ends with wording equivalent to:

```text
...と伝えられている
```

and the history-only branch of `_build_fact_text()` wraps the full fact content with:

```text
...と伝えられています。
```

the final copy can become redundant.

Observed shape:

```text
...と伝えられていると伝えられています。
```

This is a copy-quality defect.

It is not a factual-certainty defect.

---

## 2. Current runtime cause

Current authority:

```text
backend/temples/services/recommendation_reason_v4.py
  -> _build_fact_text()
```

Current history-only weakened branch:

```python
history_text = fact_shrine_history.rstrip("。")
fact_text = f"{subject}には、{history_text}と伝えられています。"
```

The builder treats the history content as opaque text and appends the hedge mechanically.

The current contract intentionally does not depend on whether the stored Fact text already contains a hedge.

That independence is important for safety, but it also permits duplicate hedge wording.

---

## 3. Why this is not a TRADITION_ALWAYS_HEDGED failure

The current contract requires:

```text
history_type = tradition
-> assertive output prohibited
-> hedged wording required
```

The observed double hedge still satisfies this safety requirement.

It does not:

- convert tradition into confirmed historical fact
- remove the hedge
- increase confidence
- alter Evidence Gate usability
- change Recommendation Eligibility
- change Ranking / Score
- create a new Knowledge Fact

Therefore:

```text
TRADITION_ALWAYS_HEDGED = PASS
COPY_QUALITY            = DEFECT
```

These are separate responsibilities.

---

## 4. Scope

### In scope for this track

- duplicated hedge wording in Recommendation Reason v4
- history-only branch of `_build_fact_text()`
- deterministic copy cleanup
- regression tests for already-hedged tradition content
- preserving the existing tradition safety floor

### Out of scope

- Knowledge Fact rewriting
- changing `history_type`
- changing Fact `confidence`
- changing Evidence Gate
- changing Shared Recommendation Eligibility
- changing Ranking / Score
- changing Concierge candidate selection
- changing Compass
- changing Shrine Detail display
- Production data cleanup
- W0-DB03 G6 reclassification

---

## 5. Known reachability

The issue is reachable only when Recommendation Reason selects the history sentence branch.

Current `_build_fact_text()` priority is:

```text
deity
-> shrine_history
-> goriyaku
-> history_theme
-> fallback
```

Therefore, when a candidate has an available deity Fact, the deity branch wins and the double-hedge history sentence is not used as the main Fact sentence.

W0-DB03 岡田宮 currently has named deity Facts, so the observed redundant history sentence is not the current main Reason sentence for that shrine.

The G6 audit nevertheless reproduced the history-only branch directly and confirmed the issue is systemic rather than W0-DB03-specific.

---

## 6. Existing contract/test gap

Current regression authority:

```text
backend/temples/tests/services/test_tradition_output_contract.py
```

The tests correctly verify:

- tradition + high confidence is hedged
- tradition + medium confidence is hedged
- tradition is not assertive
- low-confidence tradition stays suppressed
- non-tradition history types are not forced into the tradition floor

The tests do not currently verify:

```text
already-hedged tradition content
-> must not receive a semantically duplicate hedge
```

Therefore the safety contract is covered, while this copy-quality case is not.

---

## 7. Remediation boundary

A future implementation PR may address this only if it preserves the following invariant:

```text
history_type = tradition
-> output remains hedged
```

The fix must not depend on changing stored Source-backed Fact content merely to satisfy presentation formatting.

Preferred responsibility boundary:

```text
Stored Fact
  remains Source-backed content

Recommendation Reason presentation
  avoids duplicate hedge phrasing
```

Do not solve this by mutating Knowledge Seed text across existing shrines.

---

## 8. Future implementation acceptance criteria

A dedicated implementation PR should prove at minimum:

```text
1. already-hedged tradition content does not produce a duplicate hedge
2. unhedged tradition content still receives a hedge
3. tradition + high confidence remains non-assertive
4. tradition + medium confidence remains non-assertive
5. tradition + low confidence remains suppressed
6. historical_event / founding current behavior does not regress
7. deity-first sentence priority does not regress
8. Ranking / Score output does not change
9. Evidence Gate / Eligibility output does not change
10. existing Recommendation Reason tests remain green
```

The implementation should be deterministic and local to Recommendation Reason presentation logic unless fresh evidence shows a broader ownership problem.

---

## 9. Suggested implementation test cases

Future tests should include at least these content shapes:

```text
A. "この地に祀られたと伝えられている。"
B. "この地に祀られたとされています。"
C. "この地に祀られたという伝承がある。"
D. "この地に祀られた。"
```

For all tradition cases:

- output must remain visibly hedged
- no assertive historical claim may be introduced
- duplicate hedge tails should not appear

The exact copy transformation is intentionally not selected in this tracking audit.

That choice belongs to the future implementation task after code/test review.

---

## 10. W0-DB03 boundary

W0-DB03 G6 remains:

```text
W0_DB03_G6_PASS_4_OF_4
```

This track does not change:

- 大神神社 G6 result
- 北野天満宮 G6 result
- 平安神宮 G6 result
- 岡田宮 G6 result
- wave0-014 upstream Model HOLD

The double-hedge observation is non-blocking for W0-DB03 G7.

---

## 11. Next-state classification

```text
TRACK_ID                = REASON_V4_TRADITION_DOUBLE_HEDGE
STATUS                  = TRACKED_SEPARATE_NON_BLOCKING
OWNER                   = recommendation_reason_v4._build_fact_text
SAFETY_CONTRACT         = PASS
COPY_QUALITY            = NEEDS_FOLLOWUP
W0_DB03_G6              = UNCHANGED
W0_DB03_G7_BLOCKER      = NO
IMPLEMENTATION          = NOT_STARTED
```

---

## 12. STOP

This tracking PR must not include:

- runtime code fixes
- test behavior changes
- Knowledge data edits
- contract semantic changes
- Production writes
- W0-DB03 lifecycle changes

Implementation, if approved later, belongs in a dedicated PR.
