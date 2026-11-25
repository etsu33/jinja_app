# P2-A03 Position Audit v2 Golden Cases

## Purpose

This document defines deterministic Golden Cases for Position Audit v2.

Each Golden Case fixes:

* input condition

* Primary Evidence state

* Resolution state

* selected Position proof path

* Anchor Semantics status

* Artifact Synchronization status

* expected reason codes

* forbidden reason codes

* expected audit status

These cases are the contract between P2-A02 deterministic rules and the later implementation / regression tests.

Case IDs preserve the numbering defined by the broader P2-A02 Decision Matrix.
Only the minimum required Golden Cases are included in this document.

---

## GC-01 — Clean Primary AUTO_PASS

```text

case_id = GC-01

purpose =

Verify that complete and valid Primary Evidence can independently prove

the current Position and retain AUTO_PASS eligibility.

primary_evidence_state = VALID

resolution_state =

NONE_OR_IRRELEVANT

position_proof_path = PRIMARY_EVIDENCE

anchor_semantics_status = CONFIRMED

artifact_sync_status = SYNCED

expected_reason_codes =

PRIMARY_SOURCE_VERIFIED

forbidden_reason_codes =

RESOLUTION_RECORD_REUSED

POSITION_PROOF_UNAVAILABLE

ANCHOR_SEMANTICS_REVIEW_REQUIRED

ANCHOR_SEMANTICS_NOT_EVALUATED

ANCHOR_SEMANTICS_UNKNOWN

expected_audit_status = AUTO_PASS

```

### Input requirements

```text

Primary Evidence.status = OK

Primary Evidence.entity_match = SAME

Primary coordinate = Production coordinate

Primary provenance = COMPLETE

Seed ↔ Production identity = exact

anchor_semantics_status = CONFIRMED

```

### Invariant

```text

Complete Primary Evidence may independently establish

the machine-verifiable Position proof path.

```

---

## GC-02 — Valid Primary isolates broken Resolution

```text

case_id = GC-02

purpose =

Verify that a valid Primary Evidence proof path is isolated

from defects in an unused Resolution fallback path.

primary_evidence_state = VALID

resolution_state =

PASS record exists but provenance is incomplete

position_proof_path = PRIMARY_EVIDENCE

anchor_semantics_status = CONFIRMED

artifact_sync_status = SYNCED

expected_reason_codes =

PRIMARY_SOURCE_VERIFIED

forbidden_reason_codes =

RESOLUTION_RECORD_REUSED

RESOLUTION_SOURCE_URL_MISSING

RESOLUTION_SOURCE_TYPE_MISSING

RESOLUTION_VERIFIED_AT_MISSING

RESOLUTION_RECORD_COORDINATE_MISMATCH

POSITION_PROOF_UNAVAILABLE

expected_audit_status = AUTO_PASS

```

### Input requirements

```text

Primary Evidence.status = OK

Primary Evidence.entity_match = SAME

Primary coordinate = Production coordinate

Primary provenance = COMPLETE

Seed ↔ Production identity = exact

anchor_semantics_status = CONFIRMED

Resolution.position_status = PASS

Resolution provenance = INCOMPLETE

```

### Invariant

```text

Unused proof path defects MUST NOT poison the selected proof path.

```

## GC-03 — FETCH_FAILED + valid Resolution fallback

```text

case_id = GC-03

purpose =

Verify that a Primary Evidence retrieval failure does not downgrade

the Position result when a valid Resolution fallback independently

proves the current Position.

primary_evidence_state =

FETCH_FAILED

resolution_state =

Reusable PASS record with complete provenance and matching adopted coordinate

position_proof_path = RESOLUTION_FALLBACK

anchor_semantics_status = CONFIRMED

artifact_sync_status = SYNCED

expected_reason_codes =

SOURCE_FETCH_FAILED

RESOLUTION_RECORD_REUSED

forbidden_reason_codes =

PRIMARY_SOURCE_VERIFIED

POSITION_PROOF_UNAVAILABLE

RESOLUTION_SOURCE_URL_MISSING

RESOLUTION_SOURCE_TYPE_MISSING

RESOLUTION_VERIFIED_AT_MISSING

RESOLUTION_RECORD_COORDINATE_MISMATCH

ANCHOR_SEMANTICS_REVIEW_REQUIRED

ANCHOR_SEMANTICS_NOT_EVALUATED

ANCHOR_SEMANTICS_UNKNOWN

expected_audit_status = AUTO_PASS

```

### Input requirements

```text

Primary Evidence.status = FETCH_FAILED

Resolution.position_status = PASS

Resolution adopted coordinate = Seed coordinate

Resolution adopted coordinate = Production coordinate

Resolution.position_source_url = present

Resolution.position_source_type = present

Resolution.verified_at = present

Seed ↔ Production identity = exact

newer Primary conflict = NONE

anchor_semantics_status = CONFIRMED

```

### Invariant

```text

Retrieval failure is an observation, not an automatic Position failure,

when an independent valid Resolution fallback exists.

```

### Important boundary

```text

SOURCE_FETCH_FAILED

!=

POSITION_PROOF_UNAVAILABLE

```

`SOURCE_FETCH_FAILED` remains reportable as an observation.

`POSITION_PROOF_UNAVAILABLE` MUST NOT be emitted because the Resolution Record supplies a valid proof path.

Resolution fallback also MUST NOT bypass Anchor Semantics. If the same case used:

```text

anchor_semantics_status = NOT_EVALUATED

```

the expected audit status would be `REVIEW`, not `AUTO_PASS`.

## GC-06 — Newer coordinate conflict blocks fallback

```text
case_id = GC-06

purpose =
Verify that a newer Primary coordinate conflict blocks reuse
of an otherwise valid historical Resolution fallback.

primary_evidence_state =
VALID SOURCE WITH COORDINATE CONFLICT

resolution_state =
Reusable-looking PASS record with complete provenance

position_proof_path = NONE

anchor_semantics_status = CONFIRMED

artifact_sync_status = SYNCED

expected_reason_codes =
PRIMARY_COORDINATE_DIFFERS

forbidden_reason_codes =
RESOLUTION_RECORD_REUSED
PRIMARY_SOURCE_VERIFIED
POSITION_PROOF_UNAVAILABLE

expected_audit_status = REVIEW
```

### Input requirements

```text
Primary Evidence.status = OK
Primary Evidence.entity_match = SAME
Primary Evidence.latitude / longitude = present
Primary provenance = COMPLETE

Primary coordinate != current Production coordinate

Resolution.position_status = PASS
Resolution adopted coordinate = current Seed coordinate
Resolution adopted coordinate = current Production coordinate
Resolution.position_source_url = present
Resolution.position_source_type = present
Resolution.verified_at = present

Seed ↔ Production identity = exact
anchor_semantics_status = CONFIRMED

Current repository-controlled artifacts = synchronized
```

### Invariant

```text
Newer conflicting Primary Evidence MUST block historical Resolution reuse.
```

### Important boundary

```text
FETCH_FAILED
!=
COORDINATE_CONFLICT
```

`FETCH_FAILED` means current retrieval could not prove or disprove the historical Resolution.

`PRIMARY_COORDINATE_DIFFERS` means newer Primary Evidence actively disagrees with the current adopted Position.

Therefore:

```text
FETCH_FAILED
+ valid Resolution
→ Resolution fallback may be used
```

but:

```text
PRIMARY_COORDINATE_DIFFERS
+ valid Resolution
→ Resolution fallback MUST NOT be used
```

### Why `position_proof_path = NONE`

The Primary path cannot prove the current Position because its coordinate conflicts with Production.

The Resolution path is blocked because newer contradictory evidence exists.

Therefore:

```text
position_proof_path = NONE
audit_status = REVIEW
```

### Artifact synchronization note

GC-06 tests proof-path conflict precedence, not artifact drift.

For this Golden Case, current repository-controlled artifacts are aligned:

```text
artifact_sync_status = SYNCED
```

The Position REVIEW is driven by:

```text
PRIMARY_COORDINATE_DIFFERS
```

---

## GC-10 — Valid Primary + semantic NOT_EVALUATED → REVIEW

```text id="gc10-case"

case_id = GC-10

purpose =

Verify that a valid Primary Evidence proof path does not produce

AUTO_PASS when Anchor Semantics has not yet been evaluated.

primary_evidence_state = VALID

resolution_state =

NONE_OR_IRRELEVANT

position_proof_path = PRIMARY_EVIDENCE

anchor_semantics_status = NOT_EVALUATED

artifact_sync_status = SYNCED

expected_reason_codes =

PRIMARY_SOURCE_VERIFIED

ANCHOR_SEMANTICS_NOT_EVALUATED

forbidden_reason_codes =

RESOLUTION_RECORD_REUSED

POSITION_PROOF_UNAVAILABLE

ANCHOR_SEMANTICS_REVIEW_REQUIRED

ANCHOR_SEMANTICS_UNKNOWN

expected_audit_status = REVIEW

```

### Input requirements

```text id="gc10-input"

Primary Evidence.status = OK

Primary Evidence.entity_match = SAME

Primary coordinate = Production coordinate

Primary provenance = COMPLETE

Seed ↔ Production identity = exact

anchor_semantics_status = NOT_EVALUATED

Resolution = NONE or irrelevant

```

### Invariant

```text id="gc10-invariant"

A valid Position proof path MUST NOT bypass the Anchor Semantics gate.

```

### Important boundary

The Primary Evidence proves that the current coordinate is traceable and belongs to the same Shrine.

It does not independently prove that the coordinate satisfies the required:

```text id="gc10-semantic"

Visitor / Navigation Anchor

```

meaning.

Therefore:

```text id="gc10-result"

position_proof_path = PRIMARY_EVIDENCE

PRIMARY_SOURCE_VERIFIED = present

but

anchor_semantics_status = NOT_EVALUATED

→ ANCHOR_SEMANTICS_NOT_EVALUATED

→ audit_status = REVIEW

```

### Artifact synchronization note

This case does not test Artifact Synchronization.

Current-state artifacts may all match, so the expected value is:

```text id="gc10-sync"

artifact_sync_status = SYNCED

```

A synchronized coordinate set MUST NOT convert unevaluated Anchor Semantics into AUTO_PASS.

## GC-12 — Multi-site + semantic CONFIRMED → AUTO_PASS eligible

```text

case_id = GC-12

purpose =

Verify that multi-site or structurally complex Shrine evidence does not

downgrade a valid Position when Anchor Semantics has already been

explicitly confirmed.

primary_evidence_state = VALID

resolution_state =

NONE_OR_IRRELEVANT

position_proof_path = PRIMARY_EVIDENCE

anchor_semantics_status = CONFIRMED

artifact_sync_status = SYNCED

expected_reason_codes =

PRIMARY_SOURCE_VERIFIED

forbidden_reason_codes =

ANCHOR_SEMANTICS_REVIEW_REQUIRED

ANCHOR_SEMANTICS_NOT_EVALUATED

ANCHOR_SEMANTICS_UNKNOWN

POSITION_PROOF_UNAVAILABLE

RESOLUTION_RECORD_REUSED

expected_audit_status = AUTO_PASS

```

### Input requirements

```text

Primary Evidence.status = OK

Primary Evidence.entity_match = SAME

Primary coordinate = Production coordinate

Primary provenance = COMPLETE

Seed ↔ Production identity = exact

multi_site_status = MULTI_SITE

anchor_complexity = HIGH or equivalent supporting evidence

anchor_semantics_status = CONFIRMED

Resolution = NONE or irrelevant

```

### Invariant

```text

Multi-site complexity MUST NOT independently cause REVIEW

when Anchor Semantics has already been explicitly confirmed.

```

### Important boundary

Supporting evidence such as:

```text

multi_site_status = MULTI_SITE

anchor_complexity = HIGH

poi_candidate_count > 1

```

may describe a complex Shrine structure.

They MUST NOT independently override:

```text

anchor_semantics_status = CONFIRMED

```

Therefore:

```text

valid Primary Evidence

+

multi-site complexity

+

anchor_semantics_status = CONFIRMED

→ position_proof_path = PRIMARY_EVIDENCE

→ AUTO_PASS eligible

```

### Reason Code boundary

If:

```text

MULTIPLE_POI_CANDIDATES

```

is emitted for backward-compatible observation, it MUST NOT independently drive `REVIEW`.

The status-driving semantic field remains:

```text

anchor_semantics_status

```

Because this case is explicitly `CONFIRMED`, the audit MUST NOT emit:

```text

ANCHOR_SEMANTICS_REVIEW_REQUIRED

ANCHOR_SEMANTICS_NOT_EVALUATED

ANCHOR_SEMANTICS_UNKNOWN

```

### Artifact synchronization note

GC-12 does not test Artifact Synchronization.

With all current-state artifacts aligned:

```text

artifact_sync_status = SYNCED

```

The important distinction is:

```text

complex navigation structure

!=

artifact drift

!=

unresolved Anchor Semantics

```

## GC-15 — Spreadsheet row missing does not downgrade

```text

case_id = GC-15

purpose =

Verify that a missing Spreadsheet row does not downgrade

a complete and valid Primary Evidence proof path.

primary_evidence_state = VALID

resolution_state =

NONE_OR_IRRELEVANT

position_proof_path = PRIMARY_EVIDENCE

anchor_semantics_status = CONFIRMED

artifact_sync_status = SYNCED

spreadsheet_state =

ROW_MISSING

expected_reason_codes =

PRIMARY_SOURCE_VERIFIED

SPREADSHEET_ROW_MISSING

forbidden_reason_codes =

POSITION_PROOF_UNAVAILABLE

RESOLUTION_RECORD_REUSED

ANCHOR_SEMANTICS_REVIEW_REQUIRED

ANCHOR_SEMANTICS_NOT_EVALUATED

ANCHOR_SEMANTICS_UNKNOWN

expected_audit_status = AUTO_PASS

```

### Input requirements

```text

Primary Evidence.status = OK

Primary Evidence.entity_match = SAME

Primary coordinate = Production coordinate

Primary source_url = present

Primary source_type = present

Primary verified_at = present

Seed ↔ Production identity = exact

Spreadsheet snapshot = available

Spreadsheet matching row = missing

anchor_semantics_status = CONFIRMED

Resolution = NONE or irrelevant

```

### Invariant

```text

Spreadsheet availability MUST NOT be required for AUTO_PASS

when the selected Position proof path is independently complete.

```

### Important boundary

`SPREADSHEET_ROW_MISSING` remains a useful observation:

```text

SPREADSHEET_ROW_MISSING

```

but it MUST NOT independently participate in final Position classification.

Therefore:

```text

valid Primary Evidence

+

Spreadsheet row missing

+

anchor_semantics_status = CONFIRMED

→ position_proof_path = PRIMARY_EVIDENCE

→ audit_status = AUTO_PASS

```

### Provenance boundary

This Golden Case requires Primary provenance to be independently complete.

The Spreadsheet is not needed to supply:

```text

source_url

source_type

verified_at

```

Therefore the missing Spreadsheet row has no effect on the selected proof path.

This case MUST NOT be generalized to a Primary Evidence record whose provenance is incomplete.

That separate boundary is covered by GC-18.

### Spreadsheet responsibility

GC-15 fixes the following contract:

```text

Spreadsheet =

OPTIONAL_EVIDENCE_INDEX

+

OPTIONAL_PROVENANCE_SUPPLEMENT

```

and explicitly rejects:

```text

Spreadsheet =

mandatory AUTO_PASS evidence

```

### Artifact synchronization note

Spreadsheet is not a current canonical Position artifact for the purpose of Artifact Synchronization.

Therefore a missing Spreadsheet row alone MUST NOT produce:

```text

artifact_sync_status = DRIFT

```

With repository-controlled current artifacts aligned:

```text

artifact_sync_status = SYNCED

```

## GC-18 — Missing Primary source_url cannot be supplemented

```text

case_id = GC-18

purpose =

Verify that a missing Primary source_url cannot be supplied

from Spreadsheet provenance when same-source identity

cannot be machine-verified.

primary_evidence_state =

INCOMPLETE_PROVENANCE

resolution_state =

NONE_OR_IRRELEVANT

position_proof_path = NONE

anchor_semantics_status = CONFIRMED

artifact_sync_status = SYNCED

spreadsheet_state =

MATCHING ROW EXISTS WITH position_source_url

expected_reason_codes =

PRIMARY_SOURCE_MISSING

forbidden_reason_codes =

PRIMARY_SOURCE_VERIFIED

RESOLUTION_RECORD_REUSED

SPREADSHEET_POSITION_SOURCE_MISMATCH

expected_audit_status = HOLD

```

### Input requirements

```text

Primary Evidence.status = OK

Primary Evidence.entity_match = SAME

Primary coordinate = Production coordinate

Primary source_url = missing

Primary source_type = present or missing

Primary verified_at = present or missing

Spreadsheet matching row = present

Spreadsheet.position_source_url = present

Spreadsheet.position_source_type = present

Spreadsheet.verified_at = present

Seed ↔ Production identity = exact

anchor_semantics_status = CONFIRMED

Resolution = NONE or not reusable

```

### Invariant

```text

Primary source_url MUST NOT be invented or supplied

from Spreadsheet when the Primary source identity

cannot already be machine-verified.

```

### Important boundary

Spreadsheet supplementation is allowed only after

the Primary Position source has already been identified.

Valid supplementation requires:

```text

Primary source_url = X

Spreadsheet.position_source_url = X

```

Only then may Spreadsheet metadata supplement fields such as:

```text

position_source_type

verified_at

```

But this case is:

```text

Primary source_url = missing

Spreadsheet.position_source_url = X

```

Therefore the system cannot prove that the Primary coordinate

originated from source X.

The Spreadsheet URL MUST NOT be copied into Primary provenance.

### Expected proof result

Because Primary provenance is incomplete:

```text

position_proof_path != PRIMARY_EVIDENCE

```

and because no reusable Resolution fallback exists:

```text

position_proof_path = NONE

```

The missing required Position source URL produces:

```text

PRIMARY_SOURCE_MISSING

→ HOLD

```

### Spreadsheet note

The presence of a Spreadsheet row is not itself an error.

This case does not require:

```text

SPREADSHEET_POSITION_SOURCE_MISMATCH

```

because there is no Primary source URL to compare against.

The problem is not a mismatch.

The problem is:

```text

Primary source identity is unknown.

```

### Artifact synchronization note

This Golden Case tests provenance, not repository artifact drift.

If current repository-controlled artifacts are aligned:

```text

artifact_sync_status = SYNCED

```

The Position HOLD is independent from Artifact Synchronization.

## GC-20 — Position AUTO_PASS + artifact DRIFT

```text

case_id = GC-20

purpose =

Verify that a valid Position proof path can remain AUTO_PASS

even when one or more current repository-controlled artifacts

are out of synchronization with the adopted Position.

primary_evidence_state = VALID

resolution_state =

NONE_OR_IRRELEVANT

position_proof_path = PRIMARY_EVIDENCE

anchor_semantics_status = CONFIRMED

artifact_sync_status = DRIFT

expected_reason_codes =

PRIMARY_SOURCE_VERIFIED

ARTIFACT_BASE_SEED_DRIFT

forbidden_reason_codes =

POSITION_PROOF_UNAVAILABLE

RESOLUTION_RECORD_REUSED

ANCHOR_SEMANTICS_REVIEW_REQUIRED

ANCHOR_SEMANTICS_NOT_EVALUATED

ANCHOR_SEMANTICS_UNKNOWN

expected_audit_status = AUTO_PASS

```

### Input requirements

```text

Primary Evidence.status = OK

Primary Evidence.entity_match = SAME

Primary coordinate = Production coordinate

Primary provenance = COMPLETE

anchor_semantics_status = CONFIRMED

Production coordinate = adopted Position

Base Seed coordinate != adopted Position

Candidate Master / Resolution state =

either synchronized or irrelevant to this minimal case

```

### Invariant

```text

Artifact drift MUST NOT independently downgrade

a valid Position proof path.

```

### Important boundary

The audit must independently produce:

```text

position_proof_path = PRIMARY_EVIDENCE

audit_status = AUTO_PASS

```

and:

```text

artifact_sync_status = DRIFT

```

at the same time.

These results are not contradictory.

They answer different questions:

```text

audit_status

→ Is the current Position machine-verifiable?

artifact_sync_status

→ Are repository-controlled current artifacts synchronized

   with that Position?

```

### Artifact reason

For this Golden Case, the minimal drift is:

```text

ARTIFACT_BASE_SEED_DRIFT

```

This reason MUST affect only:

```text

artifact_sync_status

```

It MUST NOT belong to:

```text

HOLD_REASON_CODES

REVIEW_REASON_CODES

```

### Legacy reason boundary

If backward-compatible reporting also emits:

```text

SEED_PRODUCTION_COORDINATE_DIFFERS

```

that code MUST NOT independently downgrade the Position result.

The expected result remains:

```text

audit_status = AUTO_PASS

artifact_sync_status = DRIFT

```

### Why this case matters

A stale artifact means:

```text

repository synchronization problem

```

not necessarily:

```text

Position correctness problem

```

This case prevents the audit from conflating those two defect classes.

## GC-21 — Artifact SYNCED + Position REVIEW

```text id="gc21-case"

case_id = GC-21

purpose =

Verify that synchronized current-state artifacts do not produce

AUTO_PASS when the Position itself still requires human review.

primary_evidence_state = VALID

resolution_state =

NONE_OR_IRRELEVANT

position_proof_path = PRIMARY_EVIDENCE

anchor_semantics_status = NOT_EVALUATED

artifact_sync_status = SYNCED

expected_reason_codes =

PRIMARY_SOURCE_VERIFIED

ANCHOR_SEMANTICS_NOT_EVALUATED

forbidden_reason_codes =

POSITION_PROOF_UNAVAILABLE

RESOLUTION_RECORD_REUSED

ARTIFACT_BASE_SEED_DRIFT

ARTIFACT_PRODUCTION_DRIFT

ARTIFACT_CANDIDATE_MASTER_DRIFT

ARTIFACT_RESOLUTION_DRIFT

expected_audit_status = REVIEW

```

### Input requirements

```text id="gc21-input"

Primary Evidence.status = OK

Primary Evidence.entity_match = SAME

Primary coordinate = Production coordinate

Primary provenance = COMPLETE

Seed coordinate = Production coordinate

Candidate Master coordinate = current adopted Position

current Resolution adopted coordinate = current adopted Position

anchor_semantics_status = NOT_EVALUATED

```

### Invariant

```text id="gc21-invariant"

Artifact synchronization MUST NOT be treated as proof

of Position correctness or Anchor Semantics.

```

### Important boundary

The audit must independently produce:

```text id="gc21-position"

position_proof_path = PRIMARY_EVIDENCE

audit_status = REVIEW

```

and:

```text id="gc21-sync"

artifact_sync_status = SYNCED

```

at the same time.

This is valid because the two outputs answer different questions.

```text id="gc21-questions"

artifact_sync_status

→ Are current repository-controlled artifacts aligned?

audit_status

→ Is the Position fully machine-verifiable under the Position Contract?

```

### Why REVIEW still applies

All repository artifacts may agree on the same coordinate.

But agreement alone does not prove:

```text id="gc21-semantic"

that the coordinate is the intended Visitor / Navigation Anchor

```

With:

```text id="gc21-not-evaluated"

anchor_semantics_status = NOT_EVALUATED

```

the audit MUST emit:

```text id="gc21-reason"

ANCHOR_SEMANTICS_NOT_EVALUATED

```

and final:

```text id="gc21-result"

audit_status = REVIEW

```

### Critical distinction

```text id="gc21-distinction"

synchronized wrong-or-unverified data

is still synchronized data

```

Therefore:

```text id="gc21-final-boundary"

artifact_sync_status = SYNCED

```

MUST NOT imply:

```text id="gc21-no-auto"

audit_status = AUTO_PASS

```

## GC-23 — Canonical HOLD wins

```text

case_id = GC-23

purpose =

Verify that an existing canonical HOLD_POSITION_REVIEW decision

cannot be overridden by Machine Audit, even when current machine-readable

evidence would otherwise qualify for AUTO_PASS.

primary_evidence_state = VALID

resolution_state =

HOLD_POSITION_REVIEW

position_proof_path = NONE

anchor_semantics_status = CONFIRMED

artifact_sync_status = SYNCED

expected_reason_codes =

POSITION_CONTRACT_HOLD_RECORD

forbidden_reason_codes =

RESOLUTION_RECORD_REUSED

POSITION_PROOF_UNAVAILABLE

expected_audit_status = HOLD

```

### Input requirements

```text

Existing canonical Position Resolution record =

HOLD_POSITION_REVIEW

Primary Evidence.status = OK

Primary Evidence.entity_match = SAME

Primary coordinate = Production coordinate

Primary provenance = COMPLETE

Seed ↔ Production identity = exact

anchor_semantics_status = CONFIRMED

current repository-controlled artifacts = synchronized

```

### Invariant

```text

Canonical HOLD MUST NOT be automatically cleared

by Machine Audit.

```

### Important boundary

Without the canonical HOLD, this input may otherwise satisfy:

```text

position_proof_path = PRIMARY_EVIDENCE

audit_status = AUTO_PASS

```

But because the existing authoritative record is:

```text

HOLD_POSITION_REVIEW

```

the machine result MUST remain:

```text

audit_status = HOLD

```

with:

```text

POSITION_CONTRACT_HOLD_RECORD

```

as the status-driving reason.

### Why no automatic override

Machine Audit is a triage layer.

It may report that newer evidence appears complete, but it does not own the authority to convert:

```text

HOLD_POSITION_REVIEW

→ PASS

```

That remains a separate human / Mother Ship adjudication step.

### Proof-path note

The implementation MUST NOT emit:

```text

RESOLUTION_RECORD_REUSED

```

because a canonical HOLD record is not a reusable PASS Resolution fallback.

Likewise, this is not a missing-proof case, so:

```text

POSITION_PROOF_UNAVAILABLE

```

MUST NOT be used as the reason for HOLD.

The HOLD is caused specifically by:

```text

POSITION_CONTRACT_HOLD_RECORD

```

### Artifact synchronization note

GC-23 does not test Artifact Synchronization.

The repository artifacts may all be synchronized:

```text

artifact_sync_status = SYNCED

```

and the final Position result still remains:

```text

audit_status = HOLD

```

because canonical status and artifact synchronization are separate responsibilities.

## GC-24 — No proof path → REVIEW

```text
case_id = GC-24

purpose =
Verify that the audit returns REVIEW when neither Primary Evidence
nor Resolution fallback can establish a usable Position proof path.

primary_evidence_state =
FETCH_FAILED

resolution_state =
NONE_OR_NOT_REUSABLE

position_proof_path = NONE

anchor_semantics_status = CONFIRMED

artifact_sync_status = SYNCED

expected_reason_codes =
SOURCE_FETCH_FAILED
POSITION_PROOF_UNAVAILABLE

forbidden_reason_codes =
PRIMARY_SOURCE_VERIFIED
RESOLUTION_RECORD_REUSED
ANCHOR_SEMANTICS_REVIEW_REQUIRED
ANCHOR_SEMANTICS_NOT_EVALUATED
ANCHOR_SEMANTICS_UNKNOWN

expected_audit_status = REVIEW
```

### Input requirements

```text
Primary Evidence.status = FETCH_FAILED

Resolution =
NONE
or
not reusable under the Resolution fallback contract

Seed ↔ Production identity = exact
anchor_semantics_status = CONFIRMED

Current repository-controlled artifacts = synchronized
```

### Invariant

```text
When no valid Position proof path exists,
the audit MUST expose proof unavailability explicitly
and MUST NOT claim AUTO_PASS.
```

### Important boundary

The retrieval failure remains an observation:

```text
SOURCE_FETCH_FAILED
```

But the status-driving reason is:

```text
POSITION_PROOF_UNAVAILABLE
```

Therefore:

```text
SOURCE_FETCH_FAILED
+
no valid Primary proof
+
no valid Resolution fallback

→ position_proof_path = NONE
→ POSITION_PROOF_UNAVAILABLE
→ audit_status = REVIEW
```

### Contrast with GC-03

GC-03:

```text
FETCH_FAILED
+
valid Resolution fallback

→ position_proof_path = RESOLUTION_FALLBACK
→ AUTO_PASS eligible
```

GC-24:

```text
FETCH_FAILED
+
no valid Resolution fallback

→ position_proof_path = NONE
→ REVIEW
```

This pair fixes the boundary between:

```text
retrieval failure
```

and:

```text
proof-path failure
```

### Artifact synchronization note

GC-24 does not test Artifact Synchronization.

For this Golden Case, current repository-controlled artifacts are aligned:

```text
artifact_sync_status = SYNCED
```

Artifact synchronization MUST NOT change the expected Position result:

```text
audit_status = REVIEW
```
