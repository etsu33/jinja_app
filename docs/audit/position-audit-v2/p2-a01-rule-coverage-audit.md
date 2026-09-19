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

P2-A01 also evaluates false AUTO_PASS risk, unnecessary REVIEW / HOLD risk, Anchor Semantics deterministic boundary, Artifact Synchronization responsibility boundary, and whether Phase 2 implementation change is required.

---

## 3. Non-Goals

P2-A01 does not modify Base Seed, Candidate Master, Production DB, migrations, Shrine coordinates, Recommendation, Compass, or Ranking.

It does not adopt replacement coordinates, redefine canonical PASS / HOLD_POSITION_REVIEW meaning, introduce a fixed meter threshold, or perform live external retrieval.

This is a read-only rule coverage audit.

---

## 4. Coverage Summary

| Phase 1 Dimension | Coverage | Summary |
| --- | --- | --- |
| Provenance reproducibility | `SUPPORTED` | Current v2 requires traceable source type, URL, verification time, coordinate, and entity identity before machine verification |
| Shrine entity identity | `SUPPORTED` | Current v2 explicitly distinguishes SAME / DIFFERENT / NON_SHRINE / AMBIGUOUS and fails closed |
| Visitor / Navigation Anchor semantics | `PARTIAL` | Current v2 detects some ambiguity such as multiple POIs, but does not directly model entry, multi-site, or visitor-anchor meaning |
| Coordinate consistency | `SUPPORTED` | Current v2 compares Seed, Production, Primary Evidence, and Resolution coordinates without using a real-world meter PASS threshold |
| Artifact synchronization | `PARTIAL` | Current v2 detects some Seed / Production / Resolution mismatches but does not expose artifact synchronization as an independent responsibility |

```text
PROVENANCE_REPRODUCIBILITY = SUPPORTED
ENTITY_IDENTITY            = SUPPORTED
ANCHOR_SEMANTICS           = PARTIAL
COORDINATE_CONSISTENCY     = SUPPORTED
ARTIFACT_SYNCHRONIZATION   = PARTIAL
```

---

## 5. Provenance Reproducibility

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

Classification:

```text
PROVENANCE_REPRODUCIBILITY = SUPPORTED
```

---

## 6. Shrine Entity Identity

Primary Position Evidence supports:

```text
SAME
DIFFERENT
NON_SHRINE
AMBIGUOUS
```

Current deterministic handling:

```text
SAME       -> AUTO_PASS eligibility may continue
DIFFERENT  -> PRIMARY_SOURCE_WRONG_ENTITY -> HOLD
NON_SHRINE -> PRIMARY_SOURCE_NON_SHRINE_ENTITY -> HOLD
AMBIGUOUS  -> PRIMARY_ENTITY_AMBIGUOUS -> REVIEW
missing identity evidence -> IDENTITY_EVIDENCE_MISSING -> HOLD
unknown entity value -> REVIEW
```

Coordinate alone, Spreadsheet id alone, and fuzzy similarity alone do not establish Shrine identity.

Classification:

```text
ENTITY_IDENTITY = SUPPORTED
```

---

## 7. Visitor / Navigation Anchor Semantics

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

Current v2 can detect limited semantic ambiguity through `MULTIPLE_POI_CANDIDATES` and some address conflicts, but Phase 1 established additional semantic observations:

```text
entry_status
anchor_complexity
multi_site_status
visitor_flow_note
navigation_risk_note
```

These fields are not currently represented as first-class machine inputs in Position Audit v2.

### 7.1 False AUTO_PASS gap

Current v2 can reach AUTO_PASS when Seed == Production, Primary == Production, entity_match = SAME, provenance is complete, Spreadsheet identity requirements are satisfied, and no current reason code requires REVIEW or HOLD.

This does not independently prove that the coordinate represents the correct Visitor / Navigation Anchor meaning.

```text
entity SAME
+ coordinate SAME
+ provenance complete
!=
Anchor Semantics confirmed
```

### 7.2 Deterministic boundary

Machine evaluation must not infer Anchor Semantics from provider type, coordinate distance, entity_match alone, name similarity, or source authority alone.

Machine-readable semantic evidence may be evaluated only when explicitly supplied.

Recommended semantic responsibility:

```text
entry_status -> machine-readable decision input
multi_site_status -> machine-readable decision input
anchor_complexity -> observation only; must not independently determine status
visitor_flow_note / navigation_risk_note -> human evidence only; machine must not interpret free text
```

Unresolved semantic conditions should produce REVIEW rather than HOLD when Shrine identity and Primary Evidence remain valid.

Examples include unconfirmed entry status, unresolved multi-site interpretation, multiple plausible visitor anchors, and unresolved entrance / parking / trailhead ambiguity.

Classification:

```text
ANCHOR_SEMANTICS = PARTIAL
```

A targeted Phase 2 specification and implementation change is required.

---

## 8. Coordinate Consistency

Current v2 compares Seed / Production, Primary Evidence / Production, Resolution adopted coordinate / Seed and Production, and corroboration coordinates.

Relevant reason codes include:

```text
PRIMARY_COORDINATE_DIFFERS
SEED_PRODUCTION_COORDINATE_DIFFERS
RESOLUTION_RECORD_COORDINATE_MISMATCH
```

`COORDINATE_ABS_TOLERANCE = 1e-12` exists only for technical float round-trip equivalence. It is not a physical Position-quality threshold.

`coordinate_delta_m` is observational.

Current tests explicitly prevent distance alone, corroboration alone, and zero-meter delta alone from producing AUTO_PASS.

Classification:

```text
COORDINATE_CONSISTENCY = SUPPORTED
```

No fixed meter threshold should be introduced in Phase 2.

---

## 9. Artifact Synchronization

Current v2 can detect some repository inconsistencies through reason codes such as `SEED_PRODUCTION_COORDINATE_DIFFERS` and `RESOLUTION_RECORD_COORDINATE_MISMATCH`.

However these reason codes currently participate directly in Position Audit triage.

Phase 1 established:

```text
Position correctness
!=
Artifact synchronization
```

Pilot 16 富岡八幡宮 demonstrated that a corrected Position can exist while another repository-controlled artifact remains stale.

### 9.1 Responsibility boundary

Artifact Synchronization must be conceptually independent from Position correctness.

The model must allow:

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

Current-state synchronization candidates include Base Seed, Production Shrine, Candidate Master, and current adopted Position Resolution Record.

Historical audits, historical Source Packets, and superseded Resolution Records must remain historical evidence rather than synchronization failures.

Classification:

```text
ARTIFACT_SYNCHRONIZATION = PARTIAL
```

A separate Phase 2 synchronization responsibility is required. Final status vocabulary is deferred to P2-A02.

---

## 10. Representative Phase 1 Cases

### Pilot 10 — 金刀比羅宮

Current v2 can surface coordinate disagreement as REVIEW, but the REVIEW is produced by coordinate difference rather than deterministic understanding of mountain / navigation semantics.

Result:

```text
safe outcome
semantic coverage incomplete
```

### Pilot 11 — 貴船神社

Current v2 can surface coordinate disagreement as REVIEW, but does not independently understand multi-site meaning.

Result:

```text
safe outcome
semantic coverage incomplete
```

### Pilot 13 — 江島神社

Current coordinate disagreement can produce REVIEW. The semantic risk itself is not directly modeled.

Result:

```text
safe outcome
semantic coverage incomplete
```

### Pilot 16 — 富岡八幡宮

Current v2 can detect Seed / Production drift where present. Artifact drift is not modeled independently from Position triage.

Result:

```text
artifact drift detectable
responsibility boundary incomplete
```

### Pilot 18 — 射水神社

Canonical state remains `HOLD_POSITION_REVIEW`. Current v2 respects an existing canonical HOLD record and surfaces current Primary coordinate conflict.

The HOLD is not based on the approximately 33.75 m coordinate delta.

Result:

```text
expected fail-closed behavior
```

### Pilot 19 — 札幌諏訪神社

Stored coordinate reproduces the authority access-map anchor and traceable provenance exists. Current v2 can support AUTO_PASS when all current evidence requirements are satisfied.

Result:

```text
expected behavior
```

---

## 11. Unnecessary REVIEW / HOLD Audit

### 11.1 HOLD

No clearly unnecessary HOLD path was confirmed during P2-A01.

Existing HOLD paths remain appropriate fail-closed behavior for missing required identity, wrong Shrine entity, non-Shrine entity, missing required Primary source URL, untraceable Primary coordinate, and canonical HOLD_POSITION_REVIEW records.

```text
UNNECESSARY_HOLD = NONE_CONFIRMED
```

### 11.2 Spreadsheet coupling

W0-DB02 Real-Data Pilot produced 5/5 REVIEW. All five records contained `PRIMARY_SOURCE_VERIFIED`, `SEED_PRODUCTION_EXACT`, and `SPREADSHEET_ROW_MISSING`.

Human Position adjudication later produced PASS 4 / HOLD_POSITION_REVIEW 1.

The Real-Data Pilot explicitly records that `SPREADSHEET_ROW_MISSING` was the common factor keeping all five machine results in REVIEW.

The Spreadsheet is defined as an Evidence Index rather than Ground Truth.

Therefore independently verified Primary Position Evidence plus verified identity and traceable provenance should not necessarily be downgraded solely because the Spreadsheet row is missing.

```text
UNNECESSARY_REVIEW_GAP = SPREADSHEET_COUPLING
```

### 11.3 Resolution fallback and retrieval failure

Current v2 formally allows a reusable PASS Resolution Record to substitute for current Primary Evidence when the Resolution is PASS, Seed / Production identity is exact, current coordinates match the adopted coordinate, Resolution provenance is complete, and no newer conflicting evidence exists.

However `FETCH_FAILED`, `PARSE_FAILED`, and `REDIRECTED` currently produce REVIEW reason codes before Resolution fallback is finalized.

This can leave a record in REVIEW even when a valid Resolution Record supplies the accepted fallback proof path.

```text
temporary retrieval failure
must not automatically poison
a complete reusable Resolution proof path
```

```text
UNNECESSARY_REVIEW_GAP = RESOLUTION_FALLBACK_PATH_POISONING
```

---

## 12. False AUTO_PASS Audit

```text
PROVENANCE_FALSE_AUTO_PASS = NONE_CONFIRMED
ENTITY_FALSE_AUTO_PASS = NONE_CONFIRMED
COORDINATE_ONLY_FALSE_AUTO_PASS = NONE_CONFIRMED
ANCHOR_SEMANTICS_FALSE_AUTO_PASS = FOUND
```

Current v2 can reach AUTO_PASS without explicit machine-readable evidence that the selected coordinate has no unresolved Visitor / Navigation Anchor ambiguity.

---

## 13. Implementation Decision

P2-A01 does not support a full rewrite of Position Audit v2.

The current implementation already provides strong deterministic coverage for provenance, entity identity, coordinate consistency, fail-closed source handling, Resolution Record provenance, and distance-threshold avoidance.

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

## 14. P2-A02 Inputs

P2-A02 must define deterministic rules for Anchor Semantics, Artifact Synchronization, Spreadsheet dependency, and Resolution fallback isolation.

P2-A02 must not weaken provenance requirements, entity identity requirements, Primary coordinate traceability, the canonical Position Contract, or fail-closed behavior for true evidence absence.

---

## 15. Final Finding

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

## 16. STOP

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
