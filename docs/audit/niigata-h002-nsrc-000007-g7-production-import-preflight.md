# NIIGATA-001-H002 — nsrc-000007 赤城社 G7 Production Import Preflight

## 0. Final classification（G7 CLOSED / PASS）

- Recorded at: `2026-10-14`
- Candidate: `nsrc-000007`
- Shrine: 赤城社（新潟県十日町市四日町2534番地）
- Gate: `G7 Production Import`
- Result: **`CLOSED / PASS`**
- G8 CORE READY: **`NOT_EXECUTED`**
- Full canonical Base Seed Production apply: **`PROHIBITED`**
- Production write after closure: **`PROHIBITED`**

```text
G7_READ_ONLY_PREFLIGHT          = PASS
G7_PRODUCTION_BACKUP_RESTORE    = PASS
G7_BASE_IMPORT                  = PASS
G7_BASE_IDEMPOTENCY             = PASS
G7_KNOWLEDGE_IMPORT             = PASS
G7_KNOWLEDGE_IDEMPOTENCY        = PASS
G7_AGGREGATE_INVARIANT          = PASS
G7_KNOWLEDGE_INTEGRITY          = PASS
G7_SOURCE_RELATION_INTEGRITY    = PASS
G7_GORIYAKU_ISOLATION           = PASS
G7_PRODUCTION_RUNTIME_QA        = PASS
G7_BLOCKERS_REMAINING           = NONE
G7_STATUS                       = CLOSED
G7_RESULT                       = PASS

Production final delta:
Shrine        +1
Source        +2
Deity         +0
History       +2
SourceFact    +0
Collective    +0
goriyaku系    +0

PRODUCTION_WRITE_AFTER_CLOSURE  = PROHIBITED
G8_CORE_READY                   = NOT_EXECUTED
```

Chronology:

1. PR #3193 prepared the artifacts with the frozen block UNSET. No Production value was available
   then; §1–§16 are that preparation record and are kept as written.
2. After #3193 merged, Mother Ship ran `nsrc_000007_g7_preflight.sql` on Production read-only and
   supplied the measurements（§17）.
3. This follow-up PR froze those values into the three guards. It performed no Production connection,
   backup, or write.
4. After #3194 merged, Mother Ship took a fresh Production backup with PostgreSQL 17.10 clients,
   restored it into an isolated PostgreSQL 17.10 environment, verified the restore fingerprint,
   and confirmed that the committed pre-Base guard passes. See §18.
5. After backup / restore readiness closed, Mother Ship explicitly authorized the scoped Production
   write. The target-only Base row and nsrc-000007 Knowledge Seed were applied with guards between
   phases, followed by idempotency checks and read-only Production Runtime QA. See §19–§25.

## 1. Status at PR #3193（preparation; historical record）

```text
candidate_id                = nsrc-000007
name_jp                     = 赤城社
address                     = 新潟県十日町市四日町2534番地

G7_PREPARATION              = PASS（artifacts + disposable-DB rehearsal only）
PRODUCTION_READ_ONLY        = NOT EXECUTED（no credential available through the Credential Bridge）
PRODUCTION_STATE_CLASS      = NOT MEASURED（Mother Ship acceptance pending）
FROZEN_PRE_STATE            = UNSET（guards fail closed）
PRODUCTION_EXPECTED_DELTA   = NOT FROZEN
BACKUP_RESTORE_READINESS    = HOLD（procedure documented; no Production backup taken）
PRODUCTION_WRITE_READY      = HOLD

PRODUCTION_WRITE_AUTHORIZED = NO
PRODUCTION_WRITE            = NONE
FORMAL_G7                   = NOT EXECUTED
G8                          = NOT EXECUTED
```

- Recorded at: 2026-10-13
- Base: `develop@6bb1c63d`（#3192 merged）
- Branch: `audit/nsrc-000007-g7-production-import-preflight`

Upstream:

```text
G0 = PASS
G1 = PASS / SAME_NAME_DIFFERENT_SHRINE
G2 = PASS
G3 = PASS / NORMAL_MODEL_FIT
G4 = PASS（docs/audit/niigata-h002-nsrc-000007-g4-knowledge-materialization-reentry.md）
G5 = PASS / ELIGIBLE（docs/audit/niigata-h002-nsrc-000007-g5-recommendation-eligibility.md）
G6 = PASS（docs/audit/niigata-h002-nsrc-000007-g6-runtime-qa.md）
```

Local simulation is not a G7 PASS. G7 can only be decided after:

- a real Production read-only preflight;
- Mother Ship acceptance of the state class;
- a fresh backup with an isolated restore and a fingerprint match;
- an explicitly authorized write.

## 2. Credential boundary

```text
check_credential_presence.sh ~/.config/kami-musubi/production-db.env DATABASE_URL -> VAR_SET=0
```

No credential is available in this environment. Nothing was requested, printed, or committed.

```text
PRODUCTION_READ_ONLY = NOT EXECUTED
```

No Production value appears anywhere in this PR. Repository or local counts were not substituted.

## 3. Why the G7 generator was not used

`scripts/migration_safety/g7_sql_generator.py` fails closed for this candidate:

- its `normalized_url_identity` SQL family accepts exactly 1 Source / 1 History（nsrc-000002 shape）;
  nsrc-000007 has 2 independent Sources and 2 Histories;
- its spec requires frozen Production values（server version, aggregates, `CLEAN_CREATE`）, which do not
  exist yet and must not be fabricated.

Extending the generator would expand scope, so the artifacts follow the hand-written nsrc-000002
machinery instead, extended to two independent Source identities. The safety model is not simplified.

## 4. Artifacts

| File | Role |
|---|---|
| `scripts/migration_safety/sql/nsrc_000007_g7_preflight.sql` | read-only preflight（SELECT / WITH only） |
| `scripts/migration_safety/sql/nsrc_000007_g7_backup_version_check.sql` | server major version for client compatibility |
| `scripts/migration_safety/sql/nsrc_000007_g7_pre_base_guard.sql` | fail-closed pre-Base guard（frozen UNSET） |
| `scripts/migration_safety/sql/nsrc_000007_g7_post_base_guard.sql` | fail-closed post-Base guard（frozen UNSET） |
| `scripts/migration_safety/sql/nsrc_000007_g7_post_knowledge_verification.sql` | fail-closed post-Knowledge verification（frozen UNSET） |
| `scripts/migration_safety/nsrc_000007_g7_extract_base_subset.py` | deterministic one-row target subset |
| `scripts/migration_safety/nsrc_000007_g7_runtime_qa.py` | read-only Production Runtime QA（READ ONLY transaction） |
| `backend/temples/tests/test_nsrc_000007_g7_source_identity_sql.py` | identity / guard / rehearsal regression（disposable DB） |

All five SQL files pass `guard.py check-readonly-sql`. None contains a credential, hostname, database
URL, or database name.

## 5. Phase 1 — Read-only preflight SQL

`nsrc_000007_g7_preflight.sql` measures:

- availability flags, `server_version` / `server_version_num`, latest `temples` migration;
- required table existence, including history-source relations, SourceFact, Collective, goriyaku tags
  and assignments;
- aggregates: Shrine / ShrineKnowledgeSource / ShrineDeity / ShrineHistory / ShrineSourceFact /
  ShrineDeityCollective;
- `target_exact_count`, `same_name_akagi_count`, `same_name_other_address_count`, `same_address_count`;
- a row listing of every `赤城社` and every row at the target address, with `is_canonical_target`;
- per S2 and per S3:
  - lookalike row listing;
  - `source_identity_count`, `source_metadata_compatible_count`, `source_url_lookalike_count`,
    `source_url_lookalike_non_identity_count`, `source_type_url_unparseable_count`;
  - `source_identity_state`;
- target Deity / History / History-Source relations / SourceFact / Collective / goriyaku tag links /
  ShrineGoriyakuAssignment;
- `production_state_class_candidate`.

### 5.1 Exact target identity

```text
canonical target = name_jp = 赤城社 AND address = 新潟県十日町市四日町2534番地
```

H002 has other distinct shrines named `赤城社`. Same-name rows at other addresses are listed as
diagnostics only. They never identify the target and are not a CONFLICT by themselves. Their count is
frozen so that the guards detect drift. A row at the target address with any other name is a CONFLICT.

### 5.2 Source identity（importer-equivalent, no approximation）

One shared block, `-- BEGIN/END nsrc_000007_source_identity`, is byte-identical in all four
preflight / guard files. It reuses the reviewed nsrc-000002 `source_url_norm` CTE verbatim, which
reproduces `knowledge_seed.normalize_source_url()`. On top of it, S2 and S3 each get independent
`*_identity`, `*_metadata_compatible`, and `*_url_lookalike` CTEs.

| | S2 | S3 |
|---|---|---|
| source_type | `government` | `museum_or_archive` |
| normalized identity URL | `https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf` | `https://www.tokamachi-museum.jp/archives/bunka023` |
| metadata（`_SOURCE_REUSE_FIELDS`） | publisher `十日町市`, bibliography `中魚沼郡誌上 p.398`, `source_confirmed` / `high` / `ja` | publisher `十日町市博物館`, bibliography `""`, `source_confirmed` / `high` / `ja` |
| lookalike diagnostic | host `city.tokamachi.lg.jp` + path `rekibun_shiryou` | host `tokamachi-museum.jp` + path `archives%bunka023` |

Per-Source state, fail closed:

```text
identity > 1                                -> CONFLICT_IDENTITY_AMBIGUOUS
identity = 1, compatible = 0                -> CONFLICT_METADATA_DRIFT
importer-unparseable URL of that type > 0   -> CONFLICT_IMPORTER_UNPARSEABLE_URL
lookalike that is not identity > 0          -> CONFLICT_NON_IDENTITY_LOOKALIKE
identity = 1, compatible = 1                -> REUSABLE
otherwise                                   -> ABSENT
```

A lookalike is never treated as reusable evidence.

### 5.3 State class candidate

```text
CONFLICT              any Source CONFLICT_*; target_exact > 1; same_address <> target_exact;
                      or the target exists with unexpected Knowledge（Deity / SourceFact / Collective > 0,
                      History > 2, non-frozen History rows）, coordinate drift, or goriyaku data
CLEAN_CREATE          target_exact = 0（and no conflict）
ALREADY_MATERIALIZED  target with exactly H1 -> S2-compatible and H2 -> S3-compatible, nothing else
PARTIAL_EXISTING      anything else with the target present
```

Mother Ship confirms the class. The query authorizes nothing.

## 6. Expected delta（not frozen）

Repository payload maximum for a clean create:

```text
Shrine     +1
Source     +(2 - s2_accepted - s3_accepted)   （0..2, depending on exact compatible reuse）
Deity      +0
History    +2
SourceFact +0
Collective +0
goriyaku   +0
```

This is **not** the Production expected delta. It is frozen only after a real read-only Production
measurement and Mother Ship acceptance of the state class. If Production already contains target data,
the actual state is classified; it is not forced into CLEAN_CREATE.

## 7. Fail-closed guards

### 7.1 Frozen pre-state block（UNSET）

`-- BEGIN/END nsrc_000007_frozen_pre_state` is byte-identical in the three guard files:

```text
frozen_values_set               = false
shrine_total / source_total / deity_total / history_total
source_fact_total / collective_total                  = NULL
same_name_other_address_total                         = NULL
s2_accepted_source_count / s3_accepted_source_count   = NULL
```

Every guard asserts `f.frozen_values_set` first and compares against NULLs. In the committed state every
guard raises `division by zero`. This was verified on a disposable DB（§8.1）and by a regression test.
Replacing this block with measured Production values requires a separate, Mother-Ship-authorized change.

### 7.2 Pre-Base guard（CLEAN_CREATE only）

- aggregates = frozen;
- target exact = 0 and same-address = 0;
- `赤城社` at other addresses = frozen;
- per S2 / S3, identity = compatible = lookalike = frozen accepted count（0 or 1）, with 0 unparseable
  URLs of that type;
- target Deity / History / SourceFact / Collective / goriyaku tags / assignments = 0.

### 7.3 Post-Base guard

- Shrine = frozen + 1; every other aggregate unchanged;
- target exact = 1, same-address = 1, `赤城社` at other addresses unchanged;
- coordinate `37.14755658, 138.76887612` within 1e-8, goriyaku `""`;
- target Knowledge still absent, goriyaku tag links and assignments 0;
- S2 / S3 state unchanged.

### 7.4 Post-Knowledge verification

- Shrine +1, Source +(2 − s2_accepted − s3_accepted), Deity +0, History +2, SourceFact +0, Collective +0;
- target exact = 1, canonical coordinate, goriyaku `""`;
- target Deity 0 / SourceFact 0 / Collective 0 / History 2;
- H1 `historical_event / 安政7年正月の再建 / 安政7年正月 / event_date NULL` and H2
  `regional_context / 赤城社に伝わった越後縮幡 / "" / NULL`, both `source_confirmed / high`;
- relations exactly 2: H1 -> S2-compatible only, H2 -> S3-compatible only; source-less History 0;
- S2 and S3: identity = compatible = lookalike = 1, 0 unparseable;
- goriyaku tag links 0 and ShrineGoriyakuAssignment 0.

No Production numeric PK is referenced anywhere.

## 8. Disposable local simulation（not Production）

### 8.1 SQL execution

On a disposable local PostgreSQL/PostGIS DB（develop migrations, the 123-row Base Seed, every
repository Knowledge Seed except nsrc-000007, then the target row deleted to emulate the pre-state）:

```text
nsrc_000007_g7_preflight.sql   -> production_state_class_candidate = CLEAN_CREATE（S2 0/0, S3 0/0）
pre_base_guard（UNSET）        -> ERROR division by zero（exit 3）
post_base_guard（UNSET）       -> ERROR division by zero（exit 3）
post_knowledge_verification    -> ERROR division by zero（exit 3）
```

The DB was dropped afterwards.

### 8.2 Regression rehearsals（pytest disposable DB）

`backend/temples/tests/test_nsrc_000007_g7_source_identity_sql.py`（31 tests）. Frozen values are
substituted **in memory only**, from the disposable DB's own counts, to exercise guard semantics.
The committed SQL is never modified, and the database is never mutated to make a guard pass.

| Area | Cases |
|---|---|
| File contract | identity block identical in 4 files; frozen block identical, all NULL, `frozen_values_set=false`; SELECT / WITH only; no connection identifiers |
| Importer equivalence | SQL `normalized_url` == `normalize_source_url()` for S2 / S3 identity variants, lookalikes, unparseable URLs, and a general corpus |
| Identity semantics（S2, S3） | identity variants = identity; lookalikes ≠ identity but always flagged; unparseable = NULL; wrong source_type ≠ identity; S2 and S3 never match each other; drifted metadata = identity but not compatible |
| Unset guards | all three raise division by zero |
| Source-state simulations | both-absent / S2-reusable / S3-reusable / both-reusable → CLEAN_CREATE and pre-guard PASS only with the matching accepted counts（a wrong count fails）; S2 or S3 metadata-drift / identity-ambiguous / non-identity-lookalike / importer-unparseable → CONFLICT, pre-guard FAIL for every accepted-count combination |
| Drift | adding an unrelated Shrine after freezing → pre-guard FAIL |
| Same-name diagnostics | three other-address `赤城社` rows → still CLEAN_CREATE, frozen `same_name_other_address_total=3`, PASS; a different-name row at the target address → CONFLICT / FAIL |
| Base subset | extractor deterministic, exactly the frozen row; fails closed on a missing row, coordinate drift, or other-address-only data; refuses an in-repository output path |
| Base + Knowledge rehearsal（sources absent / S2 reused / both reused） | pre-guard PASS → subset dry-run（no write）→ apply `created=1` → second dry-run `created=0` → post-Base PASS（pre-Base now FAIL, post-Knowledge still FAIL）→ Knowledge dry-run plan matches the reuse state → apply → second dry-run `{'source_REUSE_EXISTING': 2, 'history_SKIP_EXISTS': 2}`, no CREATE → post-Knowledge PASS; goriyaku snapshot unchanged |
| Post-Knowledge negatives | an extra H1 -> S3 relation → FAIL（removed → PASS）; a Deity row `土田岐入彦命` on the target → FAIL |
| Runtime QA rehearsal | `nsrc_000007_g7_runtime_qa.main()` on the rehearsed state prints all PASS lines + `TRANSACTION_MODE=READ_ONLY`; aggregates unchanged |

Sources-absent rehearsal Knowledge plan: `source_CREATE: 2`, `history_CREATE: 2`.
With S2 pre-existing compatibly: `source_CREATE: 1`, `source_REUSE_EXISTING: 1`, `history_CREATE: 2`.

## 9. Target-only Base subset

```text
scripts/migration_safety/nsrc_000007_g7_extract_base_subset.py <OUTPUT_PATH outside repo>
SUBSET_ROWS=1
name_jp=赤城社
address=新潟県十日町市四日町2534番地
SUBSET_SHA256=e59cda286f1b25edab166a340244a374db7739d5bf112b967845b7b6d9225b10   （two runs, byte-identical）
```

```json
[{"name_jp": "赤城社", "address": "新潟県十日町市四日町2534番地", "latitude": 37.14755658,
  "longitude": 138.76887612, "goriyaku": "", "kyusei": null, "astro_elements": [],
  "location": {"lat": 37.14755658, "lng": 138.76887612}}]
```

The extractor:

- requires the exact (name_jp, address) row and the frozen canonical values（coordinate authority:
  `docs/audit/shrine-position/niigata-h002-akagi-sha-position-resolution.md`）;
- refuses an in-repository output path（verified: `BLOCKED ... inside the repository`, exit 1）;
- performs no DB access.

Generated subset files are not committed.

```text
FULL_BASE_SEED_PRODUCTION_APPLY = PROHIBITED
```

## 10. Production Runtime QA script

`scripts/migration_safety/nsrc_000007_g7_runtime_qa.py` runs entirely inside `transaction.atomic()` +
`SET TRANSACTION READ ONLY`. It asserts the G6 expectations:

- **Detail:** Deity 0; History 2 in order H1, H2; H1 → S2 only and H2 → S3 only（importer identity
  comparison, so a reused Source differing only in URL syntax passes）; `source_confirmed`; no
  unsupported deity names.
- **Concierge:** exact (name, address) candidate once; canonical coordinate; `distance_m=0`; History
  [H1, H2]; Deity []; goriyaku tags [].
- **Reason:** H1 selected（G6-measured）; `deity` / `fact.deity` / `fact.goriyaku` None; reason uses H1
  only; no 土田岐入彦命 / 経津主命; none of the 10 guarantee phrases.
- **Compass:** canonical coordinate; distance int > 0 and finite; bearing in [0, 360); the matching
  direction keeps the candidate, and the other seven exclude it.

Recommendation Top1 and Compass Top1 are not required.

## 11. Backup / restore readiness（procedure; not executed）

```text
LOCAL_CLIENT（this environment） = pg_dump / psql / pg_restore 16.15
PRODUCTION_SERVER_VERSION       = NOT MEASURED
BACKUP_RESTORE_READINESS        = HOLD
```

Required before any Production write. Credentials stay outside the repo in a mode-600 file and are never
printed（`scripts/migration_safety/README.md` Credential Bridge）.

1. Run `sql/nsrc_000007_g7_backup_version_check.sql` read-only and record the server major version.
2. Use `pg_dump` / `pg_dumpall` / `pg_restore` / `psql` of the same or newer major
   （`PG_DUMP_BIN` / `PG_DUMPALL_BIN`）.
3. Take a **fresh** Production backup with `dump_readonly.sh`（roles / schema / data）, stored outside
   the repository.
4. Create a disposable local DB whose name contains `restore_test` / `audit` / `migration_safety`.
5. Restore it with `restore_isolated.sh`, including the extensions（PostGIS / pg_trgm）.
6. Run `nsrc_000007_g7_preflight.sql` on the restored DB. Its output must equal the Production read-only
   preflight output exactly（fingerprint match）.
7. Run `nsrc_000007_g7_pre_base_guard.sql`, with the Mother-Ship-frozen values, on the restored DB. It
   must PASS.
8. If any step fails: `PRODUCTION_WRITE_READY = HOLD`. Do not proceed.

A backup that merely exists somewhere is not sufficient. A fresh backup, a successful isolated restore,
and a fingerprint match are all required.

## 12. verified_at representation（documented risk; not changed）

```text
seed value  2026-10-13T00:00:00+09:00  =  stored instant 2026-10-12T15:00:00Z
```

A UTC calendar-date rendering would show `2026-10-12`. The Knowledge Seed is unchanged, and G7 does not
"fix" this.

## 13. Validation

```text
guard.py check-readonly-sql（5 nsrc-000007 SQL files）         READONLY_OK × 5
test_nsrc_000007_g7_source_identity_sql.py                     31 passed
  （mutation sanity: changing the S2 identity URL in the block -> 3 failed; file restored）
nsrc-000007 tests（base / knowledge / G5 / G6 / G7）             75 passed
test_nsrc_000002_g7_source_identity_sql.py（precedent）          4 passed
backend full suite（-n auto）                                    5440 passed, 12 skipped
scripts/tests                                                    685 passed
scripts/migration_safety/tests                                   320 passed
makemigrations --check                                           No changes detected
ruff check / format --check（new Python files）                   clean
git diff --check                                                 clean
```

## 14. Impact boundary

```text
Production connection / write             NONE
Base Seed / Knowledge Seed / Candidate Master  NONE
G1–G6 audit outcomes                      UNCHANGED
Ranking / Score / Recommendation / Evidence Gate  NONE
Concierge / Compass runtime / models / migrations NONE
g7_sql_generator / existing G7 artifacts  NONE
G8                                        NOT EXECUTED
```

## 15. Rollback

Revert the commit. It adds scripts, SQL, a test, and this audit only. Nothing was written to Production.
The disposable databases were dropped.

## 16. Next at PR #3193（requires Mother Ship; historical record）

Steps 1–3 below were completed by the follow-up recorded in §17.

1. Run `nsrc_000007_g7_preflight.sql` on Production through `readonly_query.sh`（Credential Bridge）.
2. Mother Ship reviews the measurements and accepts a `production_state_class`. On any CONFLICT or
   unexpected state: STOP.
3. A separate PR freezes the measured values into the three guards' frozen block.
4. Fresh backup → isolated restore → fingerprint match（§11）.
5. Only then can Mother Ship authorize the Production write and the Formal G7 decision.

```text
STOP — no Production write is authorized or performed by this PR.
```

## 17. Production read-only measurement and freeze（follow-up PR, after #3193）

- Recorded at: 2026-10-13
- Base: `develop@d99e60ba`（#3193 merged）
- Branch: `audit/nsrc-000007-g7-freeze-production-prestate`

### 17.1 Measurement（supplied by Mother Ship）

Mother Ship executed:

```text
scripts/migration_safety/readonly_query.sh \
  ~/.config/kami-musubi/production-db.env DATABASE_URL \
  scripts/migration_safety/sql/nsrc_000007_g7_preflight.sql
```

The query completed successfully. This environment did not connect to Production. The values below are
Mother Ship's measurement, used verbatim.

```text
PostgreSQL version        = 17.6
latest temples migration  = 0120_shrine_source_fact_foundation

Shrine      = 122
Source      = 141
Deity       = 295
History     = 229
SourceFact  = 34
Collective  = 6

target exact             = 0
same-name 赤城社          = 0
same-name other-address  = 0
same-address             = 0
```

| | S2 | S3 |
|---|---|---|
| source_identity_count | 0 | 0 |
| source_metadata_compatible_count | 0 | 0 |
| source_url_lookalike_count | 0 | 0 |
| source_url_lookalike_non_identity_count | 0 | 0 |
| source_type_url_unparseable_count | 0 | 0 |
| source_identity_state | ABSENT | ABSENT |

```text
target Deity / History / History-Source / SourceFact / Collective = 0 / 0 / 0 / 0 / 0
target goriyaku tag links / ShrineGoriyakuAssignment            = 0 / 0

production_state_class_candidate = CLEAN_CREATE
```

```text
G7_READ_ONLY_PREFLIGHT = PASS
PRODUCTION_STATE_CLASS = CLEAN_CREATE
```

### 17.2 Frozen block（SET）

`-- BEGIN/END nsrc_000007_frozen_pre_state` is byte-identical in:

- `nsrc_000007_g7_pre_base_guard.sql`
- `nsrc_000007_g7_post_base_guard.sql`
- `nsrc_000007_g7_post_knowledge_verification.sql`

```text
frozen_values_set              = true
shrine_total                   = 122
source_total                   = 141
deity_total                    = 295
history_total                  = 229
source_fact_total              = 34
collective_total               = 6
same_name_other_address_total  = 0
s2_accepted_source_count       = 0
s3_accepted_source_count       = 0
```

Only the frozen block and the three guards' stale "UNSET" header line changed. The Source identity
block and normalization are byte-unchanged. `nsrc_000007_g7_preflight.sql` is unchanged.

### 17.3 Observation（non-blocking）

Production `Source = 141`. A disposable DB loaded with every repository Knowledge Seed except
nsrc-000007（§8.1 environment）has 139 Sources, so Production holds 2 Sources that the repository seeds
do not reproduce. This does not affect the classification: S2 / S3 are ABSENT with 0 lookalikes.
The guards use the Production value 141, never a repository count.

### 17.4 Expected Production delta（FROZEN）

```text
EXPECTED_PRODUCTION_DELTA
Shrine     +1
Source     +2
Deity      +0
History    +2
SourceFact +0
Collective +0
goriyaku   +0
```

| Aggregate | Pre-state | Post-Base | Post-Knowledge |
|---|---:|---:|---:|
| Shrine | 122 | 123 | 123 |
| Source | 141 | 141 | 143 |
| Deity | 295 | 295 | 295 |
| History | 229 | 229 | 231 |
| SourceFact | 34 | 34 | 34 |
| Collective | 6 | 6 | 6 |

```text
PRODUCTION_EXPECTED_DELTA = FROZEN
```

### 17.5 Disposable sequential rehearsal with the committed frozen blocks

Run in a pytest disposable DB. The committed guard files run unchanged; frozen values were not altered.

The simulated pre-state:

- Base Seed with the target row removed;
- Shrine count set to 122;
- unrelated, non-lookalike filler rows bringing Source / Deity / History / SourceFact / Collective to
  exactly 141 / 295 / 229 / 34 / 6;
- preflight result `CLEAN_CREATE` with S2 / S3 `ABSENT`.

```text
exact Production pre-state          -> pre-Base PASS（post-Base FAIL, post-Knowledge FAIL）
target subset dry-run               -> no write
target subset apply                 -> created=1; aggregates = 123 / 141 / 295 / 229 / 34 / 6
second subset dry-run               -> created=0
post-Base                           -> PASS（pre-Base FAIL, post-Knowledge FAIL）
Knowledge dry-run                   -> {'source_CREATE': 2, 'history_CREATE': 2}
Knowledge apply                     -> sources created=2, deities created=0, histories created=2
                                       aggregates = 123 / 143 / 295 / 231 / 34 / 6
post-Knowledge                      -> PASS（post-Base FAIL）
second Knowledge dry-run / apply    -> {'source_REUSE_EXISTING': 2, 'history_SKIP_EXISTS': 2}, no CREATE;
                                       aggregates unchanged; post-Knowledge PASS
relations                           -> 安政7年正月の再建 -> S2 only; 赤城社に伝わった越後縮幡 -> S3 only
goriyaku snapshot                   -> unchanged
```

Committed pre-Base guard drift（each starts from the exact pre-state, then fails）:

- aggregates: Shrine +1, Source +1, Source −1, Deity +1, History +1, SourceFact +1, Collective +1;
- target identity: target row exists; a different-name row at the target address（Shrine total kept 122）;
- same-name other-address: one `赤城社` at another address（total kept）;
- accepted count: S2 compatible present; S3 compatible present（Source total kept 141）;
- Source conflicts: S2 / S3 metadata drift, S2 / S3 non-identity lookalike, S2 importer-unparseable,
  S3 identity ambiguous.

Also:

- the committed post-Base guard fails when an extra unrelated Shrine is added after the target Base row;
- the committed post-Knowledge verification fails on an extra relation H1 → S3, H1 swapped to S3, a
  created Deity（`土田岐入彦命`）, a goriyaku text mutation, a goriyaku tag link, and coordinate drift;
- the committed guards fail on a non-Production state（Base Seed only）.

The earlier in-memory conflict matrix（§8.2）is kept unchanged.

### 17.6 Backup boundary

```text
Production PostgreSQL       = 17.6
observed local client       = 16.15
BACKUP_CLIENT_COMPATIBILITY = HOLD（until a PostgreSQL 17-compatible client is used）
BACKUP_RESTORE_READINESS    = HOLD
```

No Production backup is part of this PR. The §11 procedure is still required before any write.

### 17.7 Validation

```text
guard.py check-readonly-sql（5 nsrc-000007 SQL files）     READONLY_OK × 5
test_nsrc_000007_g7_source_identity_sql.py                 58 passed
  （mutation sanity: pre-Base source_total 141 -> 140 -> 21 failed; file restored byte-identical）
nsrc-000007 tests（base / knowledge / G5 / G6 / G7）         102 passed
test_nsrc_000002_g7_source_identity_sql.py（precedent）      4 passed
backend full suite（-n auto）                                5467 passed, 12 skipped
scripts/tests                                                685 passed
scripts/migration_safety/tests                               320 passed
makemigrations --check                                       No changes detected
ruff check / format --check（test）                           clean
git diff --check                                             clean
```

### 17.8 Changed files

```text
scripts/migration_safety/sql/nsrc_000007_g7_pre_base_guard.sql              frozen block SET + header line
scripts/migration_safety/sql/nsrc_000007_g7_post_base_guard.sql             frozen block SET + header line
scripts/migration_safety/sql/nsrc_000007_g7_post_knowledge_verification.sql frozen block SET + header line
backend/temples/tests/test_nsrc_000007_g7_source_identity_sql.py            SET assertions + committed-guard rehearsal
docs/audit/niigata-h002-nsrc-000007-g7-production-import-preflight.md       this section, §0, labels
```

### 17.9 Next at PR #3194（historical record）

1. Use a PostgreSQL 17-compatible client and take a **fresh** Production backup outside the repository.
2. Restore it to a disposable DB. The `nsrc_000007_g7_preflight.sql` output must equal §17.1, and the
   committed `nsrc_000007_g7_pre_base_guard.sql` must PASS on the restored DB.
3. Only then can Mother Ship authorize the Production write and the Formal G7 decision.

```text
STOP — no Production backup or write is performed by this PR.
```
## 18. Backup / Restore Readiness Closure

### 18.1 Fresh Production backup

Production PostgreSQL = 17.6
Backup client          = PostgreSQL 17.10

roles.sql  = 5,792 bytes
schema.sql = 134,714 bytes
data.sql   = 11,762,122 bytes

FRESH_PRODUCTION_BACKUP = PASS

### 18.2 Isolated restore

Restore PostgreSQL = 17.10

ISOLATED_RESTORE = PASS

### 18.3 Restore fingerprint

latest_temples_migration = 0120_shrine_source_fact_foundation

Shrine      = 122
Source      = 141
Deity       = 295
History     = 229
SourceFact  = 34
Collective  = 6

target exact            = 0
same-name other-address = 0
same-address            = 0

S2 = ABSENT
S3 = ABSENT

production_state_class_candidate = CLEAN_CREATE

### 18.4 Active restore fingerprint contract

The historical §11 wording required the restored preflight output to equal the Production
preflight output exactly.

For the active G7 restore-readiness decision, the restore fingerprint consists of:

- latest temples migration
- required table existence
- aggregate counts
- target identity state
- same-name / same-address state
- S2 Source identity state
- S3 Source identity state
- target Knowledge counts and relations
- goriyaku links / assignments
- production_state_class_candidate

Server version is compatibility metadata and is not part of the restored application-data fingerprint.

Required server compatibility:

Production PostgreSQL major = 17
Restore PostgreSQL major    = 17
Backup / restore client     = 17

Patch-version equality is not required.

### 18.5 Frozen guard verification

RESTORE_PRE_BASE_GUARD = PASS

g7_pre_base_guard_pass = 1

### 18.6 Readiness decision

BACKUP_CLIENT_COMPATIBILITY = PASS
ISOLATED_RESTORE            = PASS
DATA_FINGERPRINT            = MATCH
MIGRATION_FINGERPRINT       = MATCH
IDENTITY_FINGERPRINT        = MATCH
SOURCE_STATE_FINGERPRINT    = MATCH
SERVER_MAJOR_COMPATIBILITY  = PASS
RESTORE_PRE_BASE_GUARD      = PASS

BACKUP_RESTORE_READINESS    = PASS

PRODUCTION_WRITE_READY      = HOLD
PRODUCTION_WRITE_AUTHORIZED = NO
PRODUCTION_WRITE            = NONE
FORMAL_G7                   = NOT EXECUTED
G8                          = NOT EXECUTED


## 19. Production write authorization

```text
PRODUCTION_WRITE_AUTHORIZED = YES   (Mother Ship)
authorized target           = nsrc-000007 赤城社 / 新潟県十日町市四日町2534番地

scope =
  target-only Base import
  nsrc-000007 Knowledge import
  G7 verification / runtime QA

full Base Seed apply        = PROHIBITED
G8                          = NOT AUTHORIZED
```

## 20. Base Shrine Production import
### 20.1 Pre-Base guard

g7_pre_base_guard_pass = 1

### 20.2 Target-only subset

SUBSET_ROWS   = 1
name_jp       = 赤城社
address       = 新潟県十日町市四日町2534番地
SUBSET_SHA256 = e59cda286f1b25edab166a340244a374db7739d5bf112b967845b7b6d9225b10

### 20.3 Dry-run

CREATE 赤城社
goriyaku_tags rows=0 updated=0 added_links=0 removed_links=0
done created=1 updated=0 skipped=0 total_seed=1

### 20.4 Apply

The committed pre-Base guard was re-run immediately before the write and passed.
g7_pre_base_guard_pass = 1

CREATE 赤城社
goriyaku_tags rows=0 updated=0 added_links=0 removed_links=0
done created=1 updated=0 skipped=0 total_seed=1

### 20.5 Post-Base guard

g7_post_base_guard_pass = 1

G7_BASE_IMPORT = PASS

### 21. Knowledge Production import

Target:
backend/temples/data/knowledge_seeds/nsrc_000007_seed.json

### 21.1 Dry-run

source_CREATE  = 2
history_CREATE = 2

plan summary:
{'source_CREATE': 2, 'history_CREATE': 2}

### 21.2 Apply

The post-Base guard was re-run immediately before the write and passed.
g7_post_base_guard_pass = 1

plan summary:
{'source_CREATE': 2, 'history_CREATE': 2}

import complete:
sources created=2
deities created=0
histories created=2
collectives created=0
memberships created=0
source_facts created=0

G7_KNOWLEDGE_IMPORT = PASS

### 22. Post-Knowledge verification

Production aggregates:
Shrine      = 123
Source      = 143
Deity       = 295
History     = 231
SourceFact  = 34
Collective  = 6

Target state:
target Shrine                = 1
target Deity                 = 0
target History               = 2
target SourceFact            = 0
target Collective            = 0
History-Source relations     = 2
source-less History          = 0
target goriyaku tag links    = 0
target goriyaku assignments  = 0

Persisted relations:
安政7年正月の再建
  -> government / 歴史文化基本構想 資料集

赤城社に伝わった越後縮幡
  -> museum_or_archive / 越後縮幡

Committed verification result:
g7_post_knowledge_verification_pass = 1

G7_AGGREGATE_INVARIANT       = PASS
G7_KNOWLEDGE_INTEGRITY       = PASS
G7_SOURCE_RELATION_INTEGRITY = PASS
G7_GORIYAKU_ISOLATION        = PASS

## 23. Production idempotency
### 23.1 Knowledge

Second Knowledge dry-run:
source_REUSE_EXISTING = 2
history_SKIP_EXISTS   = 2

plan summary:
{'source_REUSE_EXISTING': 2, 'history_SKIP_EXISTS': 2}

CREATE = 0

G7_KNOWLEDGE_IDEMPOTENCY = PASS

### 23.2 Base

Second target-only Base dry-run:
SKIP id=128 赤城社
goriyaku_tags rows=0 updated=0 added_links=0 removed_links=0
done created=0 updated=0 skipped=1 total_seed=1

Production numeric id 128 is point-in-time provenance only.
Canonical identity remains exact (name_jp, address).
G7_BASE_IDEMPOTENCY = PASS

## 24. Production Runtime QA

The committed Production Runtime QA ran inside a PostgreSQL READ ONLY transaction.
DETAIL_RUNTIME=PASS
CONCIERGE_CANDIDATE_PATH=PASS
RECOMMENDATION_REASON=PASS
COMPASS_DISTANCE=PASS
COMPASS_DIRECTION=PASS
G7_PRODUCTION_RUNTIME_QA=PASS
TRANSACTION_MODE=READ_ON

Recommendation Top1 and Compass Top1 were not required.

## 25. Formal G7 closure

No-scope-change invariants:
Full Base Seed                         NOT APPLIED
other H002 candidates                  UNCHANGED
Deity                                  +0
Collective                             +0
SourceFact                             +0
goriyaku / goriyaku tags               +0
Ranking / Score                         UNCHANGED
Recommendation contracts               UNCHANGED
Position decision                       UNCHANGED
models / migrations                     UNCHANGED
Candidate Master                        UNCHANGED
G1-G6 historical results                UNCHANGED
G8                                      NOT EXECUTED

Final Production delta:
Shrine      +1
Source      +2
Deity       +0
History     +2
SourceFact  +0
Collective  +0
goriyaku    +0

G7_BLOCKERS_REMAINING          = NONE
G7_STATUS                      = CLOSED
G7_RESULT                      = PASS
FORMAL_G7                      = PASS

PRODUCTION_WRITE_AFTER_CLOSURE = PROHIBITED
G8_CORE_READY                  = NOT_EXECUTED

G7 PASS does not imply G8 CORE READY.
Candidate Master alignment and G8 closure remain a separate gate.
```
