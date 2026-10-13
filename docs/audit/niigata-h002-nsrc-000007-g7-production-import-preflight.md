# NIIGATA-001-H002 — nsrc-000007 赤城社 G7 Production Import Preflight（preparation only）

## 1. Status

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

## 16. Next（requires Mother Ship）

1. Run `nsrc_000007_g7_preflight.sql` on Production through `readonly_query.sh`（Credential Bridge）.
2. Mother Ship reviews the measurements and accepts a `production_state_class`. On any CONFLICT or
   unexpected state: STOP.
3. A separate PR freezes the measured values into the three guards' frozen block.
4. Fresh backup → isolated restore → fingerprint match（§11）.
5. Only then can Mother Ship authorize the Production write and the Formal G7 decision.

```text
STOP — no Production write is authorized or performed by this PR.
```
