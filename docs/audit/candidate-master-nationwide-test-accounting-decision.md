# Candidate Master Nationwide Test Accounting Decision

> **Status: N5 MOTHER_SHIP_DECISION = CLOSED**
>
> Recorded at: 2026-10-08
>
> Scope: Candidate Masterを全国Source Trackへ拡張した後も、
> historical Wave0のexact accountingを壊さず、global registryを増加可能にするtest policyを確定する。
>
> Candidate Master mutation: 0
> Production write: 0
> Runtime change: 0

## 1. Decision

```text
N5_TEST_ACCOUNTING_POLICY
= TRACK_SCOPED_EXACT_ACCOUNTING

GLOBAL_TOTAL_EXACT_44
= RETIRED

WAVE0_EXACT_ACCOUNTING
= PRESERVED

NATIONWIDE_ACCOUNTING
= SEPARATE_CONTRACT
```

Candidate Master testsを次の3層へ分離する。

```text
Layer A = Global Registry invariants
Layer B = Historical Wave0 exact invariants
Layer C = Nationwide Source Track invariants
```

## 2. Why the current test shape cannot remain global

Current `backend/temples/tests/test_shrine_expansion_candidate_master.py` contains assumptions such as:

```text
EXPECTED_TOTAL = 44
EXPECTED_STATUS_COUNTS = Wave0 current lifecycle counts
EXPECTED_REASON_COUNTS = Wave0 reason counts
candidate_reason default applies to every row
every row has Wave0-shaped discovery_sources[]
```

These assertions are valid historical Wave0 invariants.

They are not valid global Candidate Master invariants once `nsrc-*` rows are added.

Therefore the fix is **scope separation**, not assertion deletion.

## 3. Layer A — Global Registry invariants

Global tests apply to every Candidate Master row.

Required assertions:

1. every `candidate_id` is globally unique;
2. every Candidate belongs to an allowed namespace;
3. no Candidate silently appears in an unknown namespace;
4. Candidate Master remains one registry authority;
5. duplicate IDs across Wave0 and Nationwide are impossible;
6. lifecycle values remain within the Candidate Master lifecycle enum;
7. global registry size equals the union of recognized cohorts;
8. historical Wave0 rows and Nationwide rows are not merged by name-only logic.

Initially allowed namespaces:

```text
^wave0-[0-9]{3}$
^nsrc-[0-9]{6}$
```

Canonical cohort selectors:

```text
wave0 cohort
= candidate_id matches ^wave0-[0-9]{3}$

nationwide cohort
= candidate_id matches ^nsrc-[0-9]{6}$
```

Do not classify track membership from `candidate_name`, `prefecture`, or `candidate_reason`.

## 4. Layer B — Historical Wave0 exact accounting

Wave0 remains exact and immutable.

Canonical Wave0 accounting:

```text
WAVE0_TOTAL = 44
```

The existing exact assertions remain, but are evaluated against the Wave0 cohort only.

Current Wave0 lifecycle counts remain:

```text
BUILD_READY = 17
IMPORTED    = 5
CORE_READY  = 12
HOLD        = 9
REVIEW      = 1
TOTAL       = 44
```

Current Wave0 reason counts remain:

```text
WAVE0_CORE_READY_CANDIDATE = 34
HOLD_MAPPING               = 2
SOURCE_HOLD                = 3
UNKNOWN_EVIDENCE           = 3
MODEL_CHANGE_REQUIRED      = 1
ENTITY_GRANULARITY_REVIEW  = 1
```

Current Wave0 build-batch accounting remains:

```text
W0-DB01 ... W0-DB07
= original membership 5 each
```

Historical Wave0 tests must not be weakened to accommodate Nationwide growth.

They must instead operate on:

```text
wave0_candidates
```

rather than:

```text
all candidates
```

## 5. Wave0 admission-provenance tests remain Wave0-only

Existing tests currently assert that all Candidate rows:

- inherit `candidate_reason = historical_recovered_popularity_candidate`;
- carry Omairi-shaped `discovery_sources[]`;
- include integer `discovery_rank`.

Those are Wave0-specific historical contracts.

After the nationwide extension:

```text
Wave0 candidate_reason assertion
= wave0 cohort only

Wave0 discovery_sources assertion
= wave0 cohort only
```

Do not force Nationwide candidates to fabricate `discovery_rank`.

## 6. Layer C — Nationwide Source Track accounting

Nationwide tests apply only to `nsrc-*` rows.

Core assertions:

1. every row matches `^nsrc-[0-9]{6}$`;
2. serial IDs are unique;
3. all IDs are immutable once committed;
4. every row explicitly overrides:
   ```text
   candidate_reason
   = official_source_full_enumeration_candidate
   ```
5. every row has `admission_provenance`;
6. `admission_provenance.track = nationwide_source_candidate`;
7. top-level `prefecture` matches provenance prefecture;
8. required provenance keys are present;
9. snapshot SHA-256 is 64 lowercase hexadecimal chars;
10. Source handoff provenance is not stored in `build_batch`;
11. initial H001 rows use:
    ```text
    candidate_status = DISCOVERED
    status_reason_code = REGISTRY_ADMISSION_COMPLETE
    ```
12. lifecycle-specific status reason mapping follows N4.

## 7. H001 exact regression accounting

The first Nationwide registration is pinned as its own exact cohort.

Canonical H001 membership:

```text
nsrc-000001 相吉神社
nsrc-000002 青澤神社
nsrc-000003 蒼柴神社
nsrc-000004 青海神社
nsrc-000005 青山稲荷神社
```

H001 exact test requirements:

```text
H001_TOTAL = 5
handoff_id = NIIGATA-001-H001
source_batch_id = NIIGATA-001
snapshot_sha256 = f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380

candidate_status count:
DISCOVERED = 5

status_reason_code count:
REGISTRY_ADMISSION_COMPLETE = 5
```

Future H002 / H003 registration must add their own exact handoff tests.

Do not rewrite H001 expectations when future handoffs are appended.

## 8. Global total policy

Do not retain:

```text
len(all_candidates) == 44
```

Do not replace it with a manually updated forever-growing magic number such as:

```text
49
54
59
...
```

Instead validate:

```text
all_candidates
= wave0_candidates UNION nationwide_candidates

intersection
= empty

candidate_id uniqueness
= global
```

At the first H001 implementation the observed total will be:

```text
44 Wave0 + 5 Nationwide = 49
```

but `49` is an implementation-point observation, not a permanent global contract constant.

## 9. Current tests that require scope correction

At minimum the implementation PR must review / update these current assumptions:

### `test_wave0_candidate_master_registry_accounting`

Current problem:

```text
len(candidates) == EXPECTED_TOTAL
Counter(all candidate_status) == Wave0 counts
Counter(all status_reason_code) == Wave0 counts
```

Required:

```text
filter wave0 cohort first
then retain exact Wave0 assertions
```

### `test_candidate_reason_is_registry_admission_reason_and_not_overridden`

Current problem:

```text
all rows have no candidate_reason override
```

Required:

```text
wave0 rows retain no override
nsrc rows require explicit nationwide override
```

### `test_wave0_discovery_provenance_has_required_fields`

Current problem:

```text
loops over all Candidate rows
requires Omairi / discovery_rank shape
```

Required:

```text
loop over wave0 cohort only
add separate nationwide admission_provenance tests
```

### build_batch / lifecycle Wave0 tests

Where a test intends to freeze Wave0 history, it must explicitly select the Wave0 cohort or exact W0 batch values.

Future `nsrc-*` lifecycle advancement must not alter historical Wave0 count assertions.

## 10. Test helper policy

Implementation should introduce explicit helper selectors rather than repeated ad-hoc filtering.

Recommended semantic helpers:

```text
_wave0_candidates(master)
_nationwide_candidates(master)
```

Exact function names are implementation detail, but selection semantics are contractual.

Fail closed:

- malformed `wave0-` IDs must not silently become Nationwide;
- malformed `nsrc-` IDs must not silently become Wave0;
- unknown prefixes fail the global namespace test.

## 11. Historical tests are not deleted

The nationwide extension must not solve failing tests by:

- deleting Wave0 count assertions;
- changing Wave0 total from 44 to 49;
- broadening Wave0 expected reason counts;
- giving Nationwide rows fake Omairi provenance;
- forcing Nationwide rows into W0-DB batches;
- changing existing Wave0 IDs.

Instead:

```text
historical exactness
+ additive track-specific tests
```

is the required pattern.

## 12. Schema / implementation consequence

N5 closes the accounting design needed for the additive Candidate Master extension.

The implementation PR may now:

- update Candidate Master Contract for multi-track semantics;
- introduce the Nationwide `admission_provenance` field contract;
- update tests to track-scoped accounting;
- add H001 rows;
- bump schema version if required by the concrete contract change.

The exact schema version number is implementation/contract work and is not assigned by this N5 decision alone.

## 13. N1-N5 closure

```text
N1 candidate_id namespace
= nsrc-000001 / NSRC_GLOBAL_SERIAL

N2 candidate_reason
= official_source_full_enumeration_candidate

N3 provenance
= admission_provenance object

N4 status_reason_code
= lifecycle-state-specific

N5 test accounting
= TRACK_SCOPED_EXACT_ACCOUNTING
```

All pre-registration design decisions are now closed.

## 14. Current H001 state

```text
CANDIDATE_MASTER_EXTENSION_DESIGN
= COMPLETE

G0_DATA_REGISTRATION
= NOT_EXECUTED

G1
= NOT_EXECUTED

G2
= NOT_EXECUTED
```

## 15. Next Gate

Next work is no longer another Mother Ship namespace decision.

Next work is an implementation task:

```text
Candidate Master Contract additive extension
+ Candidate Master tests
+ H001 5-row G0 registration
```

This is a multi-file contract + data + test change and should be implemented as one Codex PR.

## 16. STOP

Do not execute G1 or G2 until the implementation PR registers H001 under the closed N1-N5 contract and tests pass.
