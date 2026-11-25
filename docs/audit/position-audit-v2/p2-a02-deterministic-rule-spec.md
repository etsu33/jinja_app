# P2-A02 Position Audit v2 Implementation Contract

## 1. Purpose

This contract defines the implementation boundary for the targeted Phase 2 update to Position Audit v2.

The implementation MUST preserve the existing Position Contract and must not perform coordinate remediation.

The implementation exists only to close the deterministic rule gaps confirmed by P2-A01 and specified by P2-A02.

---

## 2. Authoritative behavior

The implementation MUST preserve the following canonical distinction:

```text
Canonical Position status
=
PASS
HOLD_POSITION_REVIEW
```

and:

```text
Machine Audit status
=
AUTO_PASS
REVIEW
HOLD
```

Machine Audit MUST NOT create, remove, or override canonical Position decisions.

In particular:

```text
AUTO_PASS != canonical PASS
```

---

## 3. Allowed implementation scope

Primary implementation targets:

```text
scripts/audit_shrine_positions_v2.py
scripts/tests/test_audit_shrine_positions_v2.py
```

Documentation may be updated only where necessary to keep the Position Audit v2 contract synchronized.

Expected documentation target:

```text
docs/audit/shrine-position-ground-truth-v2.md
```

A separate Golden Case artifact may be added during P2-A03.

---

## 4. Explicitly prohibited changes

P2-B01 MUST NOT modify:

```text
backend/temples/data/shrines_seed_clean.json
backend/temples/data/shrine_expansion_candidate_master.json
Production DB
migrations
Shrine.latitude
Shrine.longitude
Recommendation
Compass
Ranking
scoring
goriyaku
Knowledge
canonical Position Resolution decisions
```

It MUST NOT:

```text
perform live network retrieval
write to Spreadsheet
write to Production
automatically adopt coordinates
introduce a meter-based PASS threshold
infer missing Position data
infer Anchor Semantics from free text
```

---

## 5. Existing guarantees that MUST remain intact

The implementation MUST preserve:

```text
read-only audit core
no Django ORM dependency
no DB driver dependency
no ambient Production credential dependency
no network client dependency
deterministic identical-input output
Float Comparison Contract v1
coordinate_delta_m as observation only
HOLD > REVIEW > AUTO_PASS precedence
```

The existing zero-write AST tests MUST continue to pass.

---

## 6. New machine-readable input contract

Position Audit v2 MUST gain an explicit Anchor Semantics input.

Conceptual field:

```text
anchor_semantics_status
```

Allowed values:

```text
CONFIRMED
REVIEW_REQUIRED
NOT_EVALUATED
NOT_APPLICABLE
```

Unknown values MUST fail safe to REVIEW behavior.

The implementation MUST NOT derive this field automatically from:

```text
entry_status
multi_site_status
anchor_complexity
poi_candidate_count
provider
coordinate distance
name similarity
source authority
visitor_flow_note
navigation_risk_note
```

Those fields may remain supporting evidence but MUST NOT independently determine the semantic result.

---

## 7. Anchor Semantics decision contract

AUTO_PASS eligibility is retained only when:

```text
anchor_semantics_status = CONFIRMED
```

or:

```text
anchor_semantics_status = NOT_APPLICABLE
```

The following MUST produce REVIEW:

```text
REVIEW_REQUIRED
NOT_EVALUATED
unknown semantic value
```

Anchor Semantics alone MUST NOT introduce a new HOLD path where entity identity and Position Evidence remain valid.

---

## 8. Position proof paths

The implementation MUST explicitly distinguish:

```text
PRIMARY_EVIDENCE
RESOLUTION_FALLBACK
NONE
```

Conceptual output:

```text
position_proof_path
```

Precedence:

```text
PRIMARY_EVIDENCE
>
RESOLUTION_FALLBACK
>
NONE
```

Only one proof path may be selected as the effective Position proof.

---

## 9. Primary Evidence proof path

`PRIMARY_EVIDENCE` may be selected only when current Primary Position Evidence independently satisfies the required Position contract, including:

```text
retrieval status usable
entity_match = SAME
coordinate traceable
position source provenance complete
no blocking Primary conflict
```

When this path is selected:

```text
PRIMARY_SOURCE_VERIFIED
```

is the positive proof reason.

A Resolution Record MUST NOT be reported as reused when Primary Evidence independently proves the current Position.

---

## 10. Resolution fallback proof path

`RESOLUTION_FALLBACK` may be selected only when Primary Evidence does not independently prove the Position and all Resolution reuse requirements are satisfied.

Required conditions include:

```text
resolution.position_status = PASS
Seed ↔ Production identity exact
Seed coordinate = adopted coordinate
Production coordinate = adopted coordinate
resolution position_source_url present
resolution position_source_type present
resolution verified_at present
no newer conflicting Primary Evidence
```

When selected:

```text
RESOLUTION_RECORD_REUSED
```

is the positive proof reason.

Resolution reuse MUST NOT bypass Anchor Semantics evaluation.

---

## 11. Canonical HOLD precedence

If an existing canonical record contains:

```text
HOLD_POSITION_REVIEW
```

Machine Audit MUST retain:

```text
audit_status = HOLD
```

The machine MUST NOT automatically override the canonical HOLD because newer evidence appears favorable.

---

## 12. Retrieval observation isolation

The following remain valid observations:

```text
SOURCE_FETCH_FAILED
SOURCE_PARSE_FAILED
POSITION_SOURCE_REDIRECTED
PRIMARY_EVIDENCE_NOT_RETRIEVED
```

They MUST NOT automatically force REVIEW when a valid `RESOLUTION_FALLBACK` proof path exists.

Example:

```text
SOURCE_FETCH_FAILED
+
valid Resolution fallback
+
anchor_semantics_status = CONFIRMED

→ position_proof_path = RESOLUTION_FALLBACK
→ AUTO_PASS eligible
```

If neither proof path succeeds, the audit must expose the lack of a usable proof path.

New candidate reason:

```text
POSITION_PROOF_UNAVAILABLE
```

---

## 13. Newer conflict precedence

A valid historical Resolution MUST NOT override newer conflicting evidence.

Blocking conflict includes at minimum:

```text
PRIMARY_COORDINATE_DIFFERS
PRIMARY_SOURCE_WRONG_ENTITY
PRIMARY_SOURCE_NON_SHRINE_ENTITY
PRIMARY_ENTITY_AMBIGUOUS
IDENTITY_EVIDENCE_MISSING
```

Anchor semantic REVIEW conditions also prevent AUTO_PASS.

`MULTIPLE_POI_CANDIDATES` alone MUST NOT block Resolution reuse once Anchor Semantics is explicitly resolved.

---

## 14. Spreadsheet responsibility

Spreadsheet MUST be treated as:

```text
OPTIONAL_EVIDENCE_INDEX
+
OPTIONAL_PROVENANCE_SUPPLEMENT
```

Spreadsheet MUST NOT be:

```text
Ground Truth
mandatory AUTO_PASS evidence
an independent Position proof path
```

The following MUST no longer independently downgrade Position status:

```text
SPREADSHEET_ROW_MISSING
SPREADSHEET_SNAPSHOT_UNAVAILABLE
SPREADSHEET_IDENTITY_REVIEW
```

These remain reportable observations.

---

## 15. Spreadsheet provenance supplementation

Spreadsheet provenance supplementation is permitted only when the Spreadsheet row is machine-verifiably tied to the same Position source.

The implementation MUST NOT manufacture Primary source provenance by combining unrelated sources.

In particular:

```text
Primary source_url missing
+
Spreadsheet position_source_url present
```

MUST NOT be treated as evidence that the Primary coordinate came from that Spreadsheet URL.

Therefore:

```text
Primary source_url
```

MUST NOT be filled from Spreadsheet when it is absent.

When Primary `source_url` is already present and exactly matches:

```text
Spreadsheet.position_source_url
```

the Spreadsheet may supplement compatible metadata such as:

```text
position_source_type
verified_at
```

The implementation MUST NOT use:

```text
official_source_url
official_source_type
```

as substitutes for Position provenance.

Identity-source provenance and Position-source provenance MUST remain separate responsibilities.

---

## 16. Spreadsheet source mismatch

New candidate observation:

```text
SPREADSHEET_POSITION_SOURCE_MISMATCH
```

This indicates that Primary and Spreadsheet Position source identities do not satisfy the same-source supplementation contract.

It MUST NOT independently downgrade a complete Primary proof path.

---

## 17. Reason Code responsibility classes

Reason Codes MUST be conceptually divided into:

```text
POSITION_STATUS_REASON
OBSERVATION_REASON
ARTIFACT_SYNC_REASON
```

Existing string values MUST NOT be renamed or deleted solely to implement this Phase.

Historical report compatibility takes precedence over cosmetic taxonomy cleanup.

---

## 18. Observation-only Reason Codes

The following MUST no longer automatically drive Position REVIEW:

```text
SOURCE_FETCH_FAILED
SOURCE_PARSE_FAILED
POSITION_SOURCE_REDIRECTED
PRIMARY_EVIDENCE_NOT_RETRIEVED

SPREADSHEET_ROW_MISSING
SPREADSHEET_SNAPSHOT_UNAVAILABLE
SPREADSHEET_IDENTITY_REVIEW
IDENTITY_NORMALIZATION_REQUIRED

MULTIPLE_POI_CANDIDATES
SEED_PRODUCTION_EXACT
```

Whether some existing codes continue to appear in `reason_codes` is separate from whether they participate in `_classify()`.

---

## 19. Anchor Semantics Reason Codes

New candidate status-driving reasons:

```text
ANCHOR_SEMANTICS_REVIEW_REQUIRED
ANCHOR_SEMANTICS_NOT_EVALUATED
ANCHOR_SEMANTICS_UNKNOWN
```

They map to:

```text
REVIEW
```

No positive `ANCHOR_SEMANTICS_CONFIRMED` reason code is required because the structured field itself expresses that state.

---

## 20. Artifact Synchronization

Artifact synchronization MUST be independent from Position audit classification.

Conceptual output:

```text
artifact_sync_status
```

Allowed values:

```text
SYNCED
DRIFT
UNKNOWN
```

The model MUST permit:

```text
audit_status = AUTO_PASS
artifact_sync_status = DRIFT
```

and:

```text
audit_status = REVIEW
artifact_sync_status = SYNCED
```

---

## 21. Artifact synchronization inputs

Current-state synchronization candidates:

```text
Base Seed
Production Shrine
Candidate Master
current adopted Position Resolution Record
```

Historical artifacts MUST NOT be classified as drift merely because they preserve old values.

Excluded historical evidence includes:

```text
closed audits
historical Source Packets
superseded Resolution Records
historical snapshots
```

---

## 22. Artifact synchronization reasons

Candidate dedicated reasons:

```text
ARTIFACT_BASE_SEED_DRIFT
ARTIFACT_PRODUCTION_DRIFT
ARTIFACT_CANDIDATE_MASTER_DRIFT
ARTIFACT_RESOLUTION_DRIFT
ARTIFACT_SYNC_INPUT_UNAVAILABLE
```

These MUST NOT belong to:

```text
HOLD_REASON_CODES
REVIEW_REASON_CODES
```

They drive only:

```text
artifact_sync_status
```

`SEED_PRODUCTION_COORDINATE_DIFFERS` may remain for backward-compatible reporting but MUST NOT independently define Position correctness.

---

## 23. Resolution Reason Code isolation

The following Resolution reasons may affect Position status only when the Resolution path is actually required:

```text
RESOLUTION_SOURCE_URL_MISSING
RESOLUTION_SOURCE_TYPE_MISSING
RESOLUTION_VERIFIED_AT_MISSING
RESOLUTION_RECORD_COORDINATE_MISMATCH
```

When `PRIMARY_EVIDENCE` is the selected proof path, historical Resolution defects MUST NOT downgrade the Position result.

---

## 24. Output provenance

Output provenance MUST come from the selected proof path only.

For:

```text
position_proof_path = PRIMARY_EVIDENCE
```

output provenance comes from Primary Evidence.

For:

```text
position_proof_path = RESOLUTION_FALLBACK
```

output provenance comes from the reused Resolution Record.

The implementation MUST NOT create hybrid provenance by mixing metadata from unrelated proof paths.

---

## 25. Deterministic evaluation order

The implementation MUST follow this conceptual order:

```text
1. canonical HOLD check
2. identity validation
3. Primary Evidence evaluation
4. newer conflict evaluation
5. proof path selection
6. Anchor Semantics gate
7. Position status-driving reason evaluation
8. Artifact Synchronization evaluation
9. final audit status generation
10. report serialization
```

Implementation details may use helpers, but observable behavior MUST match this order.

---

## 26. Required Golden Case tests

P2-B01/B02 MUST preserve or introduce tests equivalent to at least:

```text
GC-01 clean Primary AUTO_PASS
GC-02 valid Primary isolates broken Resolution
GC-03 FETCH_FAILED + valid Resolution fallback
GC-06 newer coordinate conflict blocks fallback
GC-10 valid Primary + semantic NOT_EVALUATED → REVIEW
GC-12 multi-site + semantic CONFIRMED → AUTO_PASS eligible
GC-15 Spreadsheet row missing does not downgrade
GC-18 missing Primary source_url cannot be supplemented
GC-20 Position AUTO_PASS + artifact DRIFT
GC-21 artifact SYNCED + Position REVIEW
GC-23 canonical HOLD wins
GC-24 no proof path → REVIEW
```

Tests MUST validate both:

```text
expected_reason_codes
```

and:

```text
forbidden_reason_codes
```

where relevant.

Final status alone is insufficient test coverage.

---

## 27. Backward compatibility contract

P2-B01 MUST preserve:

```text
existing Reason Code string values
existing read-only CLI behavior unless explicitly extended
existing Position canonical statuses
Float Comparison Contract v1
report determinism
historical report readability
```

Schema additions are allowed where required for:

```text
position_proof_path
anchor_semantics_status
artifact_sync_status
```

If report schema changes, the schema version MUST be intentionally reviewed rather than silently changed.

P2-B01 MUST NOT silently reinterpret existing serialized fields.

---

## 28. Schema version gate

Current implementation declares:

```text
SCHEMA_VERSION = position-audit-v2/1.0
```

Because P2-B01 may introduce new output semantics and fields, implementation MUST explicitly decide whether the report contract remains backward-compatible.

If serialized output gains contract-significant fields:

```text
position_proof_path
anchor_semantics_status
artifact_sync_status
```

the implementation MUST update the schema version deliberately and add tests covering it.

No silent schema drift is allowed.

---

## 29. No hidden fallback contract

The implementation MUST NOT invent fallback values for:

```text
source_url
source_type
verified_at
anchor semantics
identity
coordinates
```

Absence must remain explicit.

Fail-safe behavior is preferred over inferred completion.

---

## 30. Definition of Done

P2-B01 is complete only when:

```text
implementation matches P2-A02 deterministic rules
required Golden Cases pass
existing Position Audit v2 tests pass
zero-write tests pass
deterministic JSON test passes
Float Comparison Contract test passes
no Production / Seed / Candidate Master data changed
no coordinate remediation occurred
no unrelated application behavior changed
documentation matches implementation
git diff contains only approved scope
PR is created
```

P2-B01 MUST STOP after the implementation PR is created.

No Production rollout or Position adoption is authorized by this contract.
