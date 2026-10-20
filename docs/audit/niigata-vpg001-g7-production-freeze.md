# NIIGATA-001-VPG001 — G7 cohort Production pre-state freeze

## 1. Status（freeze / guard only）

```text
cohort                         = nsrc-000021 / nsrc-000022 / nsrc-000024 / nsrc-000025
                                 (nsrc-000023 is not in the cohort; G7 NOT_AUTHORIZED)

G7_READ_ONLY_PREFLIGHT         = PASS（executed read-only by Mother Ship after PR #3279）
PRODUCTION_STATE_CLASS         = CLEAN_CREATE ×4（accepted by Mother Ship）
FROZEN_PRE_STATE               = SET（cohort guards; single measured P0）
PRODUCTION_EXPECTED_DELTA      = FROZEN

EXECUTION_MODE                 = VPG001_4_CANDIDATE_BATCH
BASELINE_MODE                  = SINGLE_FROZEN_PRESTATE + CUMULATIVE_STAGE_CHECKPOINTS

PRODUCTION_WRITE_READY         = HOLD
BACKUP_RESTORE_READINESS       = HOLD
PRODUCTION_WRITE_AUTHORIZED    = NO
PRODUCTION_WRITE               = NONE
FORMAL_G7                      = NOT_EXECUTED
G8                             = NOT_EXECUTED

FULL_BASE_SEED_PRODUCTION_APPLY = PROHIBITED
```

- Recorded at: 2026-10-20
- BASE_SHA: `5f8d2209f74d90eab56d106d1345c8f36fd808ff`（develop, PR #3279 merge, VPG001 G7 preflight）
- Branch: `audit/niigata-vpg001-g7-production-freeze`
- This PR made no Production connection, no Production write, and took no Production backup.
  No import and no G8 step was executed.

## 2. MEASURED vs DERIVED

| label | stage | source |
|---|---|---|
| **MEASURED** | P0 | Mother Ship read-only Production measurement after PR #3279 merged |
| **DERIVED / EXPECTED** | P1–P5 | P0 + reviewed repository payload, given `accepted_source_count = 0` for every target |

P1–P5 are **not** Production measurements and must not be recorded as such until each one has
actually been observed on Production by its guard.

Only one Production pre-state exists: the one before any of the four candidates exists. The four
candidates are therefore **not** modelled as four independently measured pre-states. The
candidate-specific guards from #3279 (`nsrc_0000XX_g7_{pre_base_guard,post_base_guard,
post_knowledge_verification}.sql`) keep their frozen block **UNSET** and still fail closed. They were
not converted into fake baselines. They remain the authority for Source identity semantics, exact
target Fact validation, target Runtime QA and the one-row extractors.

## 3. MEASURED Production pre-state（P0）

```text
server_version                   = 17.6
server_version_num               = 170006
latest temples migration         = 0121_shrine_fact_source_citation

Shrine / Source / Deity / History / Citation / SourceFact / Collective
= 129 / 145 / 295 / 236 / 2 / 34 / 6
```

| candidate | target_exact | same_name_other_address | same_address | source_identity | source_metadata_compatible | state |
|---|---|---|---|---|---|---|
| nsrc-000021 荒川神社 | 0 | 0 | 0 | 0 | 0 | CLEAN_CREATE |
| nsrc-000022 五十嵐神社 | 0 | 0 | 0 | 0 | 0 | CLEAN_CREATE |
| nsrc-000024 秋葉神社 | 0 | 0 | 0 | 0 | 0 | CLEAN_CREATE |
| nsrc-000025 天津神社 | 0 | 0 | 0 | 0 | 0 | CLEAN_CREATE |

Accepted Source count: 000021 = 0, 000022 = 0, 000024 = 0, 000025 = 0.

`foreign_fact_source_relation_total = 0` per candidate is **implied** rather than separately reported:
no Source identity row exists, so no other shrine's Fact can relate to one.

## 4. Frozen expected Production delta

All four targets are absent, all four accepted Sources are absent, all four classes are
CLEAN_CREATE, and no Source reuse was observed. The repository payload maximum therefore becomes the
frozen expected delta.

```text
Shrine +4 / Source +4 / Deity +8 / History +8 / Citation +0 / SourceFact +0 / Collective +0 / goriyaku +0
final = 133 / 149 / 303 / 244 / 2 / 34 / 6
```

## 5. Cumulative stage checkpoints（P1–P5 = DERIVED / EXPECTED）

Candidate order is fixed: 000021 → 000022 → 000024 → 000025.

| stage | after | Shrine | Source | Deity | History | Citation | SourceFact | Collective | 000021 | 000022 | 000024 | 000025 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P0 **MEASURED** | — | 129 | 145 | 295 | 236 | 2 | 34 | 6 | ABSENT | ABSENT | ABSENT | ABSENT |
| P1 | 4-row Base | 133 | 145 | 295 | 236 | 2 | 34 | 6 | BASE | BASE | BASE | BASE |
| P2 | 000021 Knowledge | 133 | 146 | 296 | 237 | 2 | 34 | 6 | K（S1 D1 H1 rel 2） | BASE | BASE | BASE |
| P3 | 000022 Knowledge | 133 | 147 | 297 | 237 | 2 | 34 | 6 | K | K（S1 D1 H0 rel 1） | BASE | BASE |
| P4 | 000024 Knowledge | 133 | 148 | 300 | 239 | 2 | 34 | 6 | K | K | K（S1 D3 H2 rel 5） | BASE |
| P5 | 000025 Knowledge | 133 | 149 | 303 | 244 | 2 | 34 | 6 | K | K | K | K（S1 D3 H5 rel 8） |

- BASE = the exact Base row at the frozen G2 coordinate, goriyaku neutral, Knowledge 0, Source ABSENT.
- K = Knowledge complete: every frozen Fact exactly once, one relation each to the compatible Source.
- P5 is the expected final G7 data state before Production Runtime QA.

## 6. Artifacts

| file | role |
|---|---|
| `scripts/migration_safety/sql/niigata_vpg001_g7_frozen_pre_base_guard.sql` | P0 guard（run immediately before the Base import） |
| `scripts/migration_safety/sql/niigata_vpg001_g7_post_base_guard.sql` | P1 guard |
| `scripts/migration_safety/sql/niigata_vpg001_g7_post_000021_knowledge_guard.sql` | P2 guard |
| `scripts/migration_safety/sql/niigata_vpg001_g7_post_000022_knowledge_guard.sql` | P3 guard |
| `scripts/migration_safety/sql/niigata_vpg001_g7_post_000024_knowledge_guard.sql` | P4 guard |
| `scripts/migration_safety/sql/niigata_vpg001_g7_post_000025_knowledge_guard.sql` | P5 guard |
| `scripts/migration_safety/niigata_vpg001_g7_extract_base_subset.py` | 4-row cohort Base subset |
| `backend/temples/tests/test_niigata_vpg001_g7_cohort_guard.py` | contract + disposable rehearsal + negatives |

No #3279 artifact, seed, Candidate Master, G1–G6 record, generator, Recommendation / Ranking code
or nsrc-000023 file was modified.

## 7. Guard design

### 7.1 Explicit files, no parameters

There is one explicit file per stage, with no psql variables or other runtime parameters. Each file
holds five SELECT / WITH statements, and each statement is a `1 / CASE WHEN … THEN 1 ELSE 0 END`
assertion over one row. A statement whose assertion fails raises division by zero. Under
`readonly_query.sh`（`ON_ERROR_STOP=1`）the first failure stops the run. **FAIL = STOP.**

1. **Cohort checkpoint.** This statement checks:
   - the frozen P0 block (`frozen_values_set = true`, measured values);
   - the stage checkpoint block, where `expected = frozen + cumulative delta` is asserted inside the
     SQL itself;
   - the existence of the 11 tables the G7 contract reads (`to_regclass`);
   - the 7 live aggregates against the checkpoint exactly.
2. **Statements 2–5, one per candidate in cohort order.** Each one contains:
   - the frozen P0 block;
   - that candidate's `nsrc_0000XX_source_identity` and `nsrc_0000XX_target_facts` blocks,
     **byte-identical** to #3279;
   - the #3279 assertion for the candidate's state at this stage:
     - ABSENT uses the pre-Base assertion;
     - BASE_ONLY uses the post-Base assertion;
     - KNOWLEDGE uses the post-Knowledge assertion.

How each assertion is taken from #3279 (re-derived and checked by the test):

- **Kept unchanged:** every target, Fact, relation, Source, coordinate, goriyaku and exclusion line.
- **Removed:** only the per-candidate aggregate lines. The cohort checkpoint owns the aggregates.
- **Prefixed:** the frozen names (`f.nsrc_0000XX_*`).
- **Tightened:** `accepted_source_count IN (0, 1)` becomes `= 0` (the measured value).

The frozen P0 block is byte-identical in all 30 statements.

### 7.2 What each stage enforces

- **P0（pre-Base）:**
  - aggregates are exactly 129 / 145 / 295 / 236 / 2 / 34 / 6;
  - for all four candidates, exact = 0, same-address = 0 and same-name-other-address = 0;
  - for all four Source identities, identity = compatible = lookalike = 0 and there is no
    importer-unparseable URL;
  - there are no target Facts, relations, citations, SourceFacts, Collectives, goriyaku tag links or
    assignments.
- **P1（post-Base）:**
  - aggregates are exactly 133 / 145 / 295 / 236 / 2 / 34 / 6;
  - all four exact targets = 1, and the same-address count = 1;
  - each target sits at its exact frozen G2 coordinate within 1e-8:
    - 000021 = 38.1409456 / 139.4073314
    - 000022 = 37.573979 / 139.048758
    - 000024 = 37.7863255 / 139.1351949
    - 000025 = 37.0397729 / 137.8644153
  - goriyaku `''`, with no goriyaku tag relation and no goriyaku assignment;
  - no Knowledge yet, and all four Source identities are still absent.
- **P2–P5（post-Knowledge）:**
  - the aggregate checkpoint;
  - for every completed candidate:
    - exact Fact counts and exact Fact fields (including verified_at);
    - exactly one relation per Fact, to the metadata-compatible Source;
    - source-less Facts = 0;
    - Citation, SourceFact and Collective = 0 for the target;
    - foreign relations to the Source = 0 and goriyaku isolation;
    - excluded Facts absent: 000022 五十日帯彦命, and 000025 奴奈川媛命 / 八千矛命;
  - for every not-yet-imported candidate, the Base row exists and its Knowledge and Source are 0.
  - Previously imported candidates are re-verified field by field at every later stage.

## 8. Execution plan（not executed; requires authorization）

Every step below runs only after BACKUP_RESTORE_READINESS = PASS and explicit Mother Ship write
authorization.

```text
P0 guard（frozen_pre_base）PASS
→ niigata_vpg001_g7_extract_base_subset.py --output <outside repo>
   SUBSET_ROWS=4  SUBSET_SHA256=7dafa5e1243c50b0c46a5a4f02762e533326b0fac956acc7dfe979b182691c03
→ import_shrines_seed --source <subset> --skip-goriyaku-tags --dry-run   (created=4)
→ import_shrines_seed --source <subset> --skip-goriyaku-tags             (created=4)
→ P1 guard PASS
→ Base idempotency: second dry-run / apply = created=0 updated=0 skipped=4
→ for cid in 000021, 000022, 000024, 000025:
     import_shrine_knowledge nsrc_<cid>_seed.json --validate-only / --dry-run / apply
     → P(n) guard PASS
     → second import: no CREATE（SKIP_EXISTS / REUSE_EXISTING only）, P(n) guard PASS
→ rerun all four Knowledge imports: no CREATE; 133 / 149 / 303 / 244 / 2 / 34 / 6 preserved
→ P5 guard PASS
→ nsrc_0000XX_g7_runtime_qa.py ×4（READ ONLY transaction）
```

Any FAIL means STOP: do not continue and do not import. Four separate full-seed imports are
prohibited, and so is a full Base Seed apply.

## 9. 4-row cohort Base subset

`niigata_vpg001_g7_extract_base_subset.py` composes the four `EXPECTED_ROW`s of the existing
#3279 one-row extractors. Those extractors are kept in place.

- The output is exactly 4 rows in candidate order. Each row is the exact Base Seed row: the frozen G2
  coordinate (cross-checked independently) and a neutral goriyaku / kyusei / astro_elements state.
- Output is deterministic: `SUBSET_SHA256=7dafa5e1243c50b0c46a5a4f02762e533326b0fac956acc7dfe979b182691c03`.
- The script never accesses a DB or the network.
- The extractor is BLOCKED when:
  - a target row is missing, duplicated or drifted (coordinate, location, goriyaku, kyusei or astro);
  - the requested set or order is wrong, or nsrc-000023 is requested;
  - a render has the wrong row count or order;
  - the output path is inside the repository;
  - the output file already exists and `--overwrite` was not given.

## 10. Disposable rehearsal（local PostgreSQL 16.15; not Production）

The simulated P0 is built as follows:

1. The Base Seed is imported.
2. The four target rows are removed, so 129 rows remain.
3. One unrelated row is swapped for a filler owner.
4. Unrelated filler rows are added until every aggregate equals the measured P0.

The committed guard files then run **unchanged**.

Sequential rehearsal（`test_sequential_cohort_rehearsal`）:

- At every step, exactly one stage guard passes: the expected one.
  - P0 passes before the Base import.
  - P1 passes after the Base import: 4 rows created, and the second dry-run / apply skipped all 4.
  - P2–P5 pass after each Knowledge import. Each first plan is `source_CREATE: 1`, plus the
    payload's `deity_CREATE` / `history_CREATE`. Each second import has no CREATE and leaves Fact /
    relation / Source rows unchanged.
- At each stage, the rows of earlier candidates are a byte-equal prefix.
- Rerunning all four Knowledge imports gives no CREATE, an identical snapshot and the P5 aggregates
  133 / 149 / 303 / 244 / 2 / 34 / 6.
- The goriyaku tag, assignment and link snapshot is unchanged, and the targets' goriyaku stays `''`.

Final Runtime QA rehearsal（`test_final_runtime_qa_rehearsal_on_p5`）: the four #3279 runtime QA
scripts all report PASS on P5 with `TRANSACTION_MODE=READ_ONLY`, and the P5 guard still passes
afterwards.

A plain repository lineage (not equal to P0) makes every stage guard fail.

## 11. Fail-closed proof（131 stage × mutation cases）

Each case builds the stage and confirms that only that stage's guard passes. It then mutates the
state and checks two things:

- **Aggregate drift:** the cohort checkpoint statement fails, and only that statement fails.
- **Count-preserving mutations:** filler rows rebalance the aggregates back to the checkpoint. The
  cohort statement then still passes, and at least one candidate statement fails. This proves that
  the per-candidate checks bite independently of the aggregates.

| mutation | stages |
|---|---|
| aggregate drift（Shrine / Source / Deity / History / Citation / SourceFact / Collective +1） | P0–P5 |
| candidate imported too early（Base at P0; next Knowledge at P1–P4） | P0–P4 |
| expected candidate missing（Base row at P1; last Knowledge at P2–P5） | P1–P5 |
| extra Fact | P1–P5 |
| missing Fact | P2–P5 |
| wrong Source relation / extra Source relation | P2–P5 |
| Source metadata drift（imported Source） / Source identity appearing early（next candidate） | P2–P5 / P0–P4 |
| coordinate drift | P1–P5 |
| goriyaku text / tag / assignment | P1–P5 |
| cross-candidate Fact owner | P2–P5 |
| cross-candidate Source relation | P3–P5 |
| same-name other-address row / same-address other-name row | P0–P5 |
| 000025 奴奈川 contamination: 奴奈川神社 at the shared address | P0–P5 |
| 000025 奴奈川 contamination: 奴奈川媛命 Deity on 000025 | P1–P5 |
| 000025 奴奈川 contamination: 天太玉命 renamed 八千矛命 / 奴奈川 Fact related to the 000025 Source | P5 |

Committed-file mutation sanity is recorded in the PR body.

## 12. Server / schema assumptions

- Measured on Production: PostgreSQL 17.6 / 170006, latest temples migration
  `0121_shrine_fact_source_citation`. These values are recorded in the frozen block comment.
- Enforced by every stage guard: the 11 tables the G7 contract reads exist (`to_regclass`), and the
  guard's queries reference them. A missing table or column is an SQL error, so the guard fails
  closed.
- Not enforced inside the guards: `server_version_num = 170006` and the `django_migrations` ledger.
  The disposable rehearsal runs PostgreSQL 16 with the `temples.migrations_nogis` ledger, so a guard
  that checked these could never pass in rehearsal. The #3279 per-candidate guards do not check them
  either.
  - Both values are re-confirmed before a write by
    `nsrc_0000XX_g7_preflight.sql`（statements 2–3）and `nsrc_0000XX_g7_backup_version_check.sql`.
  - These checks are part of BACKUP_RESTORE_READINESS. Mother Ship may decide to add them to the
    P0 guard instead.

## 13. Remaining HOLD items（require Mother Ship）

1. **Backup / restore readiness = HOLD.** Required:
   - compatible PostgreSQL 17 clients;
   - a fresh Production backup;
   - an isolated restore;
   - a fingerprint match;
   - **the P0 guard passing on the restore**.
2. **Production write authorization = NO.** Only after item 1 can Mother Ship authorize the
   VPG001_4_CANDIDATE_BATCH write.
3. **Formal G7 = NOT_EXECUTED.** It requires P0 → P5 guards PASS on Production plus Production
   Runtime QA PASS. Only then may P1–P5 be recorded as observed Production values.
4. **G8 = NOT_EXECUTED.**
