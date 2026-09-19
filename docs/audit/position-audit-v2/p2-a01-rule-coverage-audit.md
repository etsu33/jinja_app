# P2-A01 Position Audit v2 Rule Coverage Audit

## Status

```text
STATUS = COMPLETE
PHASE = PHASE_2_RULE_HARDENING
TASK = P2-A01
AUDIT_TYPE = READ_ONLY
IMPLEMENTATION_CHANGE = TARGETED_REQUIRED
WRITE_PATH = NONE
COORDINATE_REMEDIATION = NOT_IN_SCOPE
```

This document records the Phase 2 rule coverage audit for Position Audit v2.

The purpose of this audit is to determine how completely the current deterministic Position Audit v2 rules cover the findings established by the 20-Shrine Primary Position Evidence Pilot.

This audit does not modify Position data or redefine the canonical Position Contract.

---

## 1. Authority

Canonical Position meaning and adoption policy remain defined by:

```text
docs/knowledge/shrine-position-contract.md
```

Current machine-verifiability triage is defined by:

```text
docs/audit/shrine-position-ground-truth-v2.md
scripts/audit_shrine_positions_v2.py
```

Phase 1 evidence and findings are recorded in:

```text
docs/audit/shrine-position-evidence-pilot.md
```

The Real-Data Position Audit v2 Pilot is recorded in:

```text
docs/audit/position-audit-v2/w0-db02-real-data-pilot-2026-09-18.md
```

This audit must not weaken, reinterpret, or replace those authorities.

---

## 2. Scope

P2-A01 evaluates whether current Position Audit v2 deterministically covers the five dimensions identified by Phase 1:

```text
1. provenance reproducibility
2. Shrine entity identity
3. Visitor / Navigation Anchor semantics
4. coordinate consistency
5. artifact synchronization
```

Each dimension is classified as:

```text
SUPPORTED
PARTIAL
MISSING
OUT_OF_SCOPE
```

P2-A01 also evaluates:

```text
false AUTO_PASS risk
unnecessary REVIEW / HOLD risk
Anchor Semantics deterministic boundary
Artifact Synchronization responsibility boundary
whether Phase 2 implementation change is required
```

---

## 3. Non-Goals

P2-A01 does not:

```text
modify Base Seed
modify Candidate Master
modify Production DB
modify migrations
modify Shrine coordinates
adopt replacement coordinates
change Recommendation
change Compass
change Ranking
change canonical PASS / HOLD_POSITION_REVIEW meaning
introduce a fixed meter threshold
perform live external retrieval
```

This is a read-only rule coverage audit.

---

## 4. Coverage Summary

| Phase 1 Dimension                     | Coverage    | Summary                                                                                                                                         |
| ------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Provenance reproducibility            | `SUPPORTED` | Current v2 requires traceable source type, URL, verification time, coordinate, and entity identity before machine verification                  |
| Shrine entity identity                | `SUPPORTED` | Current v2 explicitly distinguishes SAME / DIFFERENT / NON_SHRINE / AMBIGUOUS and fails closed                                                  |
| Visitor / Navigation Anchor semantics | `PARTIAL`   | Current v2 detects some ambiguity such as multiple POIs, but does not directly model entry, multi-site, or visitor-anchor meaning               |
| Coordinate consistency                | `SUPPORTED` | Current v2 compares Seed, Production, Primary Evidence, and Resolution coordinates without using a real-world meter PASS threshold              |
| Artifact synchronization              | `PARTIAL`   | Current v2 detects some Seed / Production / Resolution mismatches but does not expose artifact synchronization as an independent responsibility |

Overall:

```text
PROVENANCE_REPRODUCIBILITY = SUPPORTED
ENTITY_IDENTITY            = SUPPORTED
ANCHOR_SEMANTICS           = PARTIAL
COORDINATE_CONSISTENCY     = SUPPORTED
ARTIFACT_SYNCHRONIZATION   = PARTIAL
```

---

## 5. Provenance Reproducibility

### 5.1 Current coverage

Position Audit v2 requires traceable Primary Position provenance before `PRIMARY_SOURCE_VERIFIED` is emitted.

Effective provenance requires:

```text
source_type
source_url
verified_at
latitude
longitude
entity_match = SAME
```

Relevant reason codes include:

```text
PRIMARY_SOURCE_MISSING
PRIMARY_SOURCE_TYPE_MISSING
PRIMARY_SOURCE_VERIFIED_AT_MISSING
PRIMARY_COORDINATE_UNTRACEABLE

RESOLUTION_SOURCE_URL_MISSING
RESOLUTION_SOURCE_TYPE_MISSING
RESOLUTION_VERIFIED_AT_MISSING
```

The Resolution Record reuse path does not bypass provenance requirements.

A reusable PASS Resolution Record must contain:

```text
position_source_type
position_source_url
verified_at
adopted coordinate
```

and its adopted coordinate must match the current Seed and Production coordinate.

### 5.2 Classification

```text
PROVENANCE_REPRODUCIBILITY = SUPPORTED
```

No new provenance taxonomy is required by P2-A01.

---

## 6. Shrine Entity Identity

### 6.1 Current coverage

Primary Position Evidence currently supports:

```text
SAME
DIFFERENT
NON_SHRINE
AMBIGUOUS
```

Current deterministic handling:

```text
SAME
→ AUTO_PASS eligibility may continue

DIFFERENT
→ PRIMARY_SOURCE_WRONG_ENTITY
→ HOLD

NON_SHRINE
→ PRIMARY_SOURCE_NON_SHRINE_ENTITY
→ HOLD

AMBIGUOUS
→ PRIMARY_ENTITY_AMBIGUOUS
→ REVIEW

missing identity evidence
→ IDENTITY_EVIDENCE_MISSING
→ HOLD

unknown entity value
→ REVIEW
```

The existing join contract also prevents identity from being established by:

```text
coordinate alone
spreadsheet id alone
fuzzy similarity alone
```

### 6.2 Classification

```text
ENTITY_IDENTITY = SUPPORTED
```

No new identity taxonomy is required by P2-A01.

---

## 7. Visitor / Navigation Anchor Semantics

### 7.1 Current coverage

Current `PrimaryPositionEvidence` includes:

```text
status
source_type
source_url
source_name
source_address
latitude
longitude
entity_match
poi_candidate_count
verified_at
```

Current v2 can detect limited semantic ambiguity through:

```text
MULTIPLE_POI_CANDIDATES
ADDRESS_CONFLICT_UNEXPLAINED
```

However, Phase 1 established additional semantic observations:

```text
entry_status
anchor_complexity
multi_site_status
visitor_flow_note
navigation_risk_note
```

These fields are not currently represented as first-class machine inputs in Position Audit v2.

### 7.2 False AUTO_PASS gap

Current v2 can reach `AUTO_PASS` when:

```text
Seed == Production
Primary == Production
entity_match = SAME
Primary provenance is complete
Spreadsheet identity requirement is satisfied
no current reason code requires REVIEW or HOLD
```

This does not independently prove that the coordinate represents the correct Visitor / Navigation Anchor meaning.

A Shrine may still contain unresolved distinctions such as:

```text
Shrine entity
individual worship site
main sanctuary
secondary sanctuary
entrance
parking
trailhead
mountain / precinct POI
```

Therefore:

```text
entity SAME
+
coordinate SAME
+
provenance complete
!=
Anchor Semantics confirmed
```

Phase 1 multi-site and large-precinct cases demonstrate this distinction.

### 7.3 Deterministic boundary

Machine evaluation must not infer Anchor Semantics from:

```text
provider type
coordinate distance
entity_match alone
name similarity
source authority alone
```

Machine-readable semantic evidence may be evaluated only when explicitly supplied.

Recommended semantic responsibility:

```text
entry_status
→ machine-readable decision input

multi_site_status
→ machine-readable decision input

anchor_complexity
→ observation only; must not independently determine status

visitor_flow_note
navigation_risk_note
→ human evidence only; machine must not interpret free text
```

### 7.4 Status boundary

Anchor Semantics may retain AUTO_PASS eligibility only when structured evidence explicitly establishes that there is no unresolved Visitor / Navigation Anchor ambiguity.

Unresolved semantic conditions should produce:

```text
REVIEW
```

Examples:

```text
entry status not confirmed
multi-site interpretation unresolved
multiple plausible visitor anchors
individual worship site vs Shrine representative point unresolved
entrance / parking / trailhead ambiguity unresolved
semantic evidence not collected
```

Anchor complexity alone must not produce `HOLD`.

Anchor Semantics alone should not normally create a new HOLD path where Shrine identity and Primary Evidence remain valid.

### 7.5 Classification

```text
ANCHOR_SEMANTICS = PARTIAL
```

A targeted Phase 2 specification and implementation change is required.

---

## 8. Coordinate Consistency

### 8.1 Current coverage

Current v2 compares:

```text
Seed ↔ Production
Primary Evidence ↔ Production
Resolution adopted coordinate ↔ Seed
Resolution adopted coordinate ↔ Production
Corroboration coordinates
```

Relevant reason codes include:

```text
PRIMARY_COORDINATE_DIFFERS
SEED_PRODUCTION_COORDINATE_DIFFERS
RESOLUTION_RECORD_COORDINATE_MISMATCH
```

The current float comparison tolerance:

```text
COORDINATE_ABS_TOLERANCE = 1e-12
```

exists only for technical float round-trip equivalence.

It is not a physical Position-quality threshold.

`coordinate_delta_m` is observational.

Current tests explicitly prevent:

```text
distance alone
corroboration alone
zero-meter delta alone
```

from producing AUTO_PASS.

### 8.2 Phase 1 consistency

Phase 1 showed that:

```text
small distance != automatically valid
large distance != automatically invalid
```

The current implementation is consistent with this finding.

### 8.3 Classification

```text
COORDINATE_CONSISTENCY = SUPPORTED
```

No fixed meter threshold should be introduced in Phase 2.

---

## 9. Artifact Synchronization

### 9.1 Current coverage

Current v2 can detect some repository inconsistencies through reason codes such as:

```text
SEED_PRODUCTION_COORDINATE_DIFFERS
RESOLUTION_RECORD_COORDINATE_MISMATCH
```

However these reason codes currently participate directly in Position Audit triage.

Phase 1 established that:

```text
Position correctness
!=
Artifact synchronization
```

Pilot 16 富岡八幡宮 demonstrated that a corrected Position can exist while another repository-controlled artifact remains stale.

### 9.2 Responsibility boundary

Artifact Synchronization must be conceptually independent from Position correctness.

The model must allow states such as:

```text
Position Result = AUTO_PASS
Artifact Synchronization = DRIFT
```

and:

```text
Position Result = REVIEW
Artifact Synchronization = SYNCED
```

A fully synchronized set of artifacts does not prove that the synchronized coordinate is the correct Visitor / Navigation Anchor.

Likewise, one stale artifact does not independently prove that the currently validated Position is wrong.

### 9.3 Synchronization candidates

Current-state synchronization candidates include:

```text
Base Seed
Production Shrine
Candidate Master
current adopted Position Resolution Record
```

Historical artifacts must not be classified as stale merely because they preserve older values.

Examples:

```text
closed historical audit
historical Source Packet
superseded Resolution Record
```

must remain historical evidence rather than synchronization failures.

### 9.4 Classification

```text
ARTIFACT_SYNCHRONIZATION = PARTIAL
```

A separate Phase 2 synchronization responsibility is required.

The final status vocabulary is deferred to P2-A02.

---

## 10. Reason Code Mapping

### 10.1 Provenance

```text
PRIMARY_SOURCE_MISSING
PRIMARY_SOURCE_TYPE_MISSING
PRIMARY_SOURCE_VERIFIED_AT_MISSING
PRIMARY_COORDINATE_UNTRACEABLE
RESOLUTION_SOURCE_URL_MISSING
RESOLUTION_SOURCE_TYPE_MISSING
RESOLUTION_VERIFIED_AT_MISSING
PRIMARY_EVIDENCE_NOT_RETRIEVED
SOURCE_FETCH_FAILED
SOURCE_PARSE_FAILED
POSITION_SOURCE_REDIRECTED
```

### 10.2 Entity Identity

```text
PRIMARY_SOURCE_WRONG_ENTITY
PRIMARY_SOURCE_NON_SHRINE_ENTITY
PRIMARY_ENTITY_AMBIGUOUS
IDENTITY_EVIDENCE_MISSING
IDENTITY_NOT_EXACT
AMBIGUOUS_SAME_NAME_SHRINE
SPREADSHEET_IDENTITY_REVIEW
IDENTITY_NORMALIZATION_REQUIRED
```

### 10.3 Anchor Semantics

Partial current coverage:

```text
MULTIPLE_POI_CANDIDATES
ADDRESS_CONFLICT_UNEXPLAINED
```

These codes do not fully cover Phase 1 Anchor Semantics.

### 10.4 Coordinate Consistency

```text
PRIMARY_COORDINATE_DIFFERS
SEED_PRODUCTION_COORDINATE_DIFFERS
RESOLUTION_RECORD_COORDINATE_MISMATCH
CORROBORATION_CONFLICT
```

### 10.5 Artifact Synchronization

Partial current signals:

```text
SEED_PRODUCTION_COORDINATE_DIFFERS
RESOLUTION_RECORD_COORDINATE_MISMATCH
```

These are not currently exposed as an independent synchronization result.

---

## 11. Representative Phase 1 Cases

### Pilot 10 — 金刀比羅宮

Phase 1 risk:

```text
mountain / navigation semantics
```

Current v2 can surface coordinate disagreement as REVIEW.

However the REVIEW is produced by coordinate difference, not by deterministic understanding of the navigation-anchor semantics.

Result:

```text
safe outcome
semantic coverage incomplete
```

---

### Pilot 11 — 貴船神社

Phase 1 risk:

```text
multi-site Shrine
main sanctuary / intermediate sanctuary / rear sanctuary distinctions
```

Current v2 can surface coordinate disagreement as REVIEW.

It does not independently understand multi-site meaning.

Result:

```text
safe outcome
semantic coverage incomplete
```

---

### Pilot 13 — 江島神社

Phase 1 risk:

```text
island multi-site structure
multiple worship locations
representative Shrine Position ambiguity
```

Current coordinate disagreement can produce REVIEW.

The semantic risk itself is not directly modeled.

Result:

```text
safe outcome
semantic coverage incomplete
```

---

### Pilot 16 — 富岡八幡宮

Phase 1 risk:

```text
corrected Position exists
Base Seed contains legacy coordinate
```

Current v2 can detect Seed / Production drift where present.

However artifact drift is not modeled independently from Position triage.

Result:

```text
artifact drift detectable
responsibility boundary incomplete
```

---

### Pilot 18 — 射水神社

Phase 1 risk:

```text
stored coordinate adopted provenance cannot be deterministically reproduced
```

Canonical state remains:

```text
HOLD_POSITION_REVIEW
```

Current v2 respects an existing canonical HOLD record and surfaces current Primary coordinate conflict.

Result:

```text
expected fail-closed behavior
```

The HOLD is not based on the approximately 33.75 m coordinate delta.

---

### Pilot 19 — 札幌諏訪神社

Phase 1 state:

```text
authority access-map Visitor / Navigation Anchor
stored coordinate reproduces adopted Primary
traceable provenance exists
```

Current v2 can support AUTO_PASS when all current evidence requirements are satisfied.

Result:

```text
expected behavior
```

---

## 12. Unnecessary REVIEW / HOLD Audit

### 12.1 HOLD

No clearly unnecessary HOLD path was confirmed during P2-A01.

Existing HOLD cases remain appropriate fail-closed behavior for conditions such as:

```text
missing required identity
wrong Shrine entity
non-Shrine entity
missing required Primary source URL
untraceable Primary coordinate
canonical HOLD_POSITION_REVIEW record
```

Result:

```text
UNNECESSARY_HOLD = NONE_CONFIRMED
```

### 12.2 Spreadsheet coupling

W0-DB02 Real-Data Pilot produced:

```text
AUTO_PASS = 0
REVIEW    = 5
HOLD      = 0
```

All five records contained:

```text
PRIMARY_SOURCE_VERIFIED
SEED_PRODUCTION_EXACT
SPREADSHEET_ROW_MISSING
```

Human Position adjudication later produced:

```text
PASS = 4
HOLD_POSITION_REVIEW = 1
```

The Real-Data Pilot explicitly records that `SPREADSHEET_ROW_MISSING` was the common factor keeping all five machine results in REVIEW.

The Spreadsheet is defined as an Evidence Index rather than Ground Truth.

Therefore:

```text
independently verified Primary Position Evidence
+
verified identity
+
traceable provenance
```

should not necessarily be downgraded solely because the Spreadsheet row is missing.

Result:

```text
UNNECESSARY_REVIEW_GAP = SPREADSHEET_COUPLING
```

---

### 12.3 Resolution fallback and retrieval failure

Current v2 formally allows a reusable PASS Resolution Record to substitute for current Primary Evidence when:

```text
position_status = PASS
Seed identity is exact
Production identity is exact
Seed coordinate == adopted coordinate
Production coordinate == adopted coordinate
Resolution provenance is complete
no newer conflicting evidence exists
```

However retrieval statuses such as:

```text
FETCH_FAILED
PARSE_FAILED
REDIRECTED
```

currently produce REVIEW reason codes before Resolution fallback is finalized.

This can leave a record in REVIEW even when a valid Resolution Record supplies the accepted fallback proof path.

P2-A01 therefore identifies a path-isolation inconsistency:

```text
temporary retrieval failure
must not automatically poison
a complete reusable Resolution proof path
```

This does not mean retrieval failure should be discarded.

It means Position status and retrieval observation must remain distinguishable when the Resolution fallback contract is satisfied.

Result:

```text
UNNECESSARY_REVIEW_GAP = RESOLUTION_FALLBACK_PATH_POISONING
```

---

## 13. False AUTO_PASS Audit

### Provenance

```text
FALSE_AUTO_PASS_GAP = NONE_CONFIRMED
```

### Entity Identity

```text
FALSE_AUTO_PASS_GAP = NONE_CONFIRMED
```

### Coordinate-only verification

Existing tests confirm:

```text
zero-meter delta alone != AUTO_PASS
corroboration alone != AUTO_PASS
distance alone != AUTO_PASS
```

Result:

```text
FALSE_AUTO_PASS_GAP = NONE_CONFIRMED
```

### Anchor Semantics

Current v2 can reach AUTO_PASS without explicit machine-readable evidence that the selected coordinate has no unresolved Visitor / Navigation Anchor ambiguity.

Result:

```text
FALSE_AUTO_PASS_GAP = FOUND
DIMENSION = ANCHOR_SEMANTICS
```

---

## 14. Implementation Decision

P2-A01 does not support a full rewrite of Position Audit v2.

The current implementation already provides strong deterministic coverage for:

```text
provenance
entity identity
coordinate consistency
fail-closed source handling
Resolution Record provenance
distance-threshold avoidance
```

Required Phase 2 work is targeted.

```text
POSITION_AUDIT_V2_REWRITE = NO
TARGETED_PHASE_2_CHANGE   = REQUIRED
```

Required target areas:

```text
1. Anchor Semantics machine-readable gate
2. Artifact Synchronization responsibility separation
3. Spreadsheet coupling review
4. Resolution fallback path-isolation review
```

---

## 15. P2-A02 Inputs

P2-A02 must define deterministic rules for:

### Anchor Semantics

```text
which structured fields are required
which values preserve AUTO_PASS eligibility
which conditions produce REVIEW
which fields are observation-only
how missing semantic evidence is handled
```

### Artifact Synchronization

```text
which artifacts are current-state synchronization authorities
which artifacts are historical-only
how SYNC / DRIFT / UNKNOWN-like states are represented
whether synchronization status is emitted inside Position Audit v2 or by a separate result structure
```

### Excess REVIEW reduction

```text
when Spreadsheet evidence is required for Position triage
when independently complete Primary Evidence is sufficient
how Resolution fallback isolates temporary retrieval failures
```

P2-A02 must not weaken:

```text
provenance requirements
entity identity requirements
Primary coordinate traceability
canonical Position Contract
fail-closed behavior for true evidence absence
```

---

## 16. Final Finding

P2-A01 concludes:

```text
PROVENANCE_REPRODUCIBILITY = SUPPORTED
ENTITY_IDENTITY            = SUPPORTED
ANCHOR_SEMANTICS           = PARTIAL
COORDINATE_CONSISTENCY     = SUPPORTED
ARTIFACT_SYNCHRONIZATION   = PARTIAL

FALSE_AUTO_PASS_ANCHOR_SEMANTICS = FOUND

UNNECESSARY_REVIEW_SPREADSHEET_COUPLING = FOUND
UNNECESSARY_REVIEW_RESOLUTION_FALLBACK  = FOUND

UNNECESSARY_HOLD = NONE_CONFIRMED

IMPLEMENTATION_CHANGE = TARGETED_REQUIRED
```

The next task is:

```text
P2-A02 Deterministic Rule Specification
```

P2-A02 must define the missing deterministic boundaries before implementation changes are authorized.

---

## 17. STOP

P2-A01 is a rule coverage audit only.

Do not modify:

```text
scripts/audit_shrine_positions_v2.py
Base Seed
Candidate Master
Production DB
migrations
Shrine coordinates
Recommendation
Compass
Ranking
```

during this task.

No coordinate remediation is authorized.

No Position Audit v2 implementation change is authorized until P2-A02 defines the deterministic rule specification.
