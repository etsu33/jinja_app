# NIIGATA-001-H002 — nsrc-000009 赤城社 G7 Production Import Preflight

## 0. Current status（Production pre-state frozen）

```text
G7_PREPARATION              = PASS（PR #3237）
PRODUCTION_READ_ONLY        = EXECUTED（Mother Ship, read-only）
G7_READ_ONLY_PREFLIGHT      = PASS
PRODUCTION_STATE_CLASS      = CLEAN_CREATE
SHARED_SOURCE_STATE         = REUSABLE
FROZEN_PRE_STATE            = SET（guards frozen; §18）
PRODUCTION_EXPECTED_DELTA   = FROZEN
BACKUP_RESTORE_READINESS    = HOLD
PRODUCTION_WRITE_READY      = HOLD

PRODUCTION_WRITE_AUTHORIZED = NO
PRODUCTION_WRITE            = NONE
FORMAL_G7                   = NOT EXECUTED
G8                          = NOT EXECUTED
```

Chronology:

1. PR #3237 prepared the artifacts with the frozen block UNSET. §1–§17 are that preparation record and
   are kept as written.
2. Mother Ship's first Production read-only preflight stopped as designed: the citation table did not
   exist（Production at `0120`）. PR #3238 created the separate temples 0121 Production Migration Gate.
3. After 0121, Mother Ship re-ran `nsrc_000009_g7_preflight.sql` on Production read-only and supplied the
   measurements（§18.1）.
4. This PR froze those values into the three guards. It performed no Production connection, backup, or
   write.

## 1. Status at PR #3237（preparation; historical record）

```text
candidate_id                = nsrc-000009
name_jp                     = 赤城社
address                     = 新潟県十日町市伊達乙48番地

G7_PREPARATION              = PASS（artifacts + disposable-DB rehearsal only）
PRODUCTION_READ_ONLY        = NOT EXECUTED
PRODUCTION_STATE_CLASS      = NOT MEASURED
FROZEN_PRE_STATE            = UNSET（guards fail closed）
PRODUCTION_EXPECTED_DELTA   = NOT FROZEN
BACKUP_RESTORE_READINESS    = HOLD
PRODUCTION_WRITE_READY      = HOLD

PRODUCTION_WRITE_AUTHORIZED = NO
PRODUCTION_WRITE            = NONE
FORMAL_G7                   = NOT EXECUTED
G8                          = NOT EXECUTED
```

- Recorded at: 2026-10-16
- Base: `develop@8a62e45`（#3236 merged）
- Branch: `audit/nsrc-000009-g7-production-import-preflight`

Upstream:

```text
G1 = PASS / SAME_NAME_DIFFERENT_SHRINE（docs/audit/niigata-h002-nsrc-000009-g1-identity-duplicate.md）
G2 = PASS
G3 = PASS / NORMAL_MODEL_FIT（docs/audit/niigata-h002-nsrc-000009-g3-source-knowledge-fit.md）
G4 = PASS（docs/audit/niigata-h002-nsrc-000009-g4-formal-pass.md）
G5 = PASS / ELIGIBLE（docs/audit/niigata-h002-nsrc-000009-g5-recommendation-eligibility.md）
G6 = PASS（docs/audit/niigata-h002-nsrc-000009-g6-runtime-qa.md）
```

Local simulation is not a G7 PASS. G7 can only be decided after:

- a real Production read-only preflight;
- Mother Ship acceptance of the state class;
- a separate PR that freezes the measured values;
- a fresh backup with an isolated restore and a fingerprint match;
- an explicitly authorized write.

## 2. Production boundary

```text
Production connection     NONE
Production credential     NOT REQUESTED / NOT READ / NOT PRINTED
Production read-only      NOT EXECUTED
Production write          NONE
```

No Production value appears anywhere in this PR. Repository, local, and test-DB counts were not
substituted for Production values. The disposable-DB numbers in §9 are labelled as such and are not
committed into any guard.

## 3. Precedent and differences from nsrc-000007

Primary precedent: `docs/audit/niigata-h002-nsrc-000007-g7-production-import-preflight.md` and its
artifacts（PR #3193 UNSET form）. The safety model is kept; the shape is not copied.

| | nsrc-000007 | nsrc-000009 |
|---|---|---|
| Sources | S2 + S3, independent | one shared municipal Source（the nsrc-000007 S2 identity） |
| Source in Production before G7 | measured ABSENT | **not assumed**; may be REUSABLE through nsrc-000007 |
| History | H1 → S2, H2 → S3 | H1 → shared, H2 → shared |
| Fact locator | `Source.bibliography`（`中魚沼郡誌上 p.398`） | `ShrineFactSourceCitation.locator_text`（`中魚沼郡誌上 p.445`） |
| Citation rows | none | 2（schema 1.3） |
| same-name 赤城社 at other address | 0 at measurement | nsrc-000007 row is expected to exist; measured, not assumed |

`scripts/migration_safety/g7_sql_generator.py` was not used for the same reason as nsrc-000007: its
`normalized_url_identity` family has no Fact citation model, and its spec requires frozen Production
values that do not exist yet. Extending the generator is out of scope.

## 4. Artifacts

| File | Role |
|---|---|
| `scripts/migration_safety/sql/nsrc_000009_g7_preflight.sql` | read-only preflight（SELECT / WITH only） |
| `scripts/migration_safety/sql/nsrc_000009_g7_backup_version_check.sql` | server major version for client compatibility |
| `scripts/migration_safety/sql/nsrc_000009_g7_pre_base_guard.sql` | fail-closed pre-Base guard（frozen UNSET） |
| `scripts/migration_safety/sql/nsrc_000009_g7_post_base_guard.sql` | fail-closed post-Base guard（frozen UNSET） |
| `scripts/migration_safety/sql/nsrc_000009_g7_post_knowledge_verification.sql` | fail-closed post-Knowledge verification（frozen UNSET） |
| `scripts/migration_safety/nsrc_000009_g7_extract_base_subset.py` | deterministic one-row target subset |
| `scripts/migration_safety/nsrc_000009_g7_runtime_qa.py` | read-only Production Runtime QA（READ ONLY transaction） |
| `backend/temples/tests/test_nsrc_000009_g7_source_identity_sql.py` | identity / guard / rehearsal regression（disposable DB） |

All five SQL files pass `guard.py check-readonly-sql`. None contains a credential, hostname, database
URL, or database name. No Production numeric PK is referenced.

## 5. Citation table and migration precondition

Confirmed from the model and migration, not guessed:

```text
model      temples.models.ShrineFactSourceCitation（no db_table override）
table      temples_shrinefactsourcecitation
migration  temples 0121_shrine_fact_source_citation（nogis: 0020_shrine_fact_source_citation）
columns    id / source_id / shrine_history_id / shrine_deity_id / locator_text / created_at
```

The regression test asserts `ShrineFactSourceCitation._meta.db_table` and that every
`to_regclass(...)` table in the preflight exists in the migrated test DB.

**Precondition (not measured):** the nsrc-000007 G7 record measured Production at
`0120_shrine_source_fact_foundation`. Whether `0121_shrine_fact_source_citation` is applied in
Production is unknown to this PR. The preflight reports it explicitly
（`fact_source_citation_migration_applied`, `fact_source_citation_table_exists`）. If the table is absent,
every later statement fails（verified on a disposable DB with the table dropped: metadata and the
table-existence row are printed, then `relation "temples_shrinefactsourcecitation" does not exist`,
exit 3）. In that case G7 is HOLD; applying 0121 to Production is a separate migration gate and is
not part of this PR.

## 6. Phase 1 — Read-only preflight SQL

`nsrc_000009_g7_preflight.sql` measures, in order:

1. availability flags; `server_version` / `server_version_num`;
2. latest `temples` migration + `fact_source_citation_migration_applied`;
3. required table existence（Shrine / Source / Deity / History / History-Source / FactSourceCitation /
   SourceFact / Collective / goriyaku tags / goriyaku assignments）;
4. aggregates: Shrine / Source / Deity / History / **Citation** / SourceFact / Collective;
5. `target_exact_count`, `same_name_akagi_count`, `same_name_other_address_count`, `same_address_count`;
6. row listing of every `赤城社` and every row at the target address, with `is_canonical_target`;
7. shared Source lookalike listing（identity / compatible flags）;
8. shared Source counts and `source_identity_state`;
9. diagnostic listing of every citation that points at a shared-Source lookalike row;
10. target Deity / History（with content）/ History-Source relations / target citations（with
    `is_expected`）/ SourceFact / Collective / goriyaku tag links / assignments;
11. `production_state_class_candidate` with the shared Source and target counts.

### 6.1 Exact target identity

```text
canonical target = name_jp = 赤城社 AND address = 新潟県十日町市伊達乙48番地
```

Same-name rows at other addresses（e.g. nsrc-000007 at 新潟県十日町市四日町2534番地）are diagnostics only.
They never identify the target, and their History / relations / Source never count as target Knowledge.
Their count is frozen so that the guards detect drift. A row at the target address with any other name
is a CONFLICT.

### 6.2 Shared Source identity（importer-equivalent）

One block, `-- BEGIN/END nsrc_000009_source_identity`, is byte-identical wherever it appears in the
four preflight / guard files. `source_url_norm` is the reviewed nsrc-000002 / nsrc-000007 CTE verbatim
（reproduces `knowledge_seed.normalize_source_url()`）.

```text
source_type          government
normalized identity  https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf
reuse metadata       publisher 十日町市 / bibliography 中魚沼郡誌上 p.398 /
                     source_confirmed / high / ja（_SOURCE_REUSE_FIELDS, after strip）
lookalike diagnostic host city.tokamachi.lg.jp + path rekibun_shiryou, any source_type
```

The `SOURCE_REUSE_CONFLICT` contract is unchanged. A shared Source whose bibliography was rewritten to
`p.445` is metadata drift, not reusable. The Fact locator is never a Source reuse condition.

```text
identity > 1                                -> CONFLICT_IDENTITY_AMBIGUOUS
identity = 1, compatible = 0                -> CONFLICT_METADATA_DRIFT
importer-unparseable government URL > 0     -> CONFLICT_IMPORTER_UNPARSEABLE_URL
lookalike that is not identity > 0          -> CONFLICT_NON_IDENTITY_LOOKALIKE
identity = 1, compatible = 1                -> REUSABLE
otherwise                                   -> ABSENT
```

A lookalike is never reusable evidence.

### 6.3 Target facts block

`-- BEGIN/END nsrc_000009_target_facts` is byte-identical in the preflight state-class statement and
the three guards. It defines `target`, `target_deity`, `target_history`（`is_h1` / `is_h2` = every
frozen field equal: history_type, title, content, period_text, `event_date IS NULL`,
`source_confirmed`, `high`）, `target_relation`（`to_shared` = shared compatible Source）, and
`target_citation`. A citation is `is_expected` only when it is on a History, its locator is exactly
`中魚沼郡誌上 p.445`, its Source is the shared compatible Source, **and** that Source is one of the
History's own M2M sources.

### 6.4 State class candidate

```text
CONFLICT              shared Source CONFLICT_*; target_exact > 1; same_address <> target_exact;
                      or the target exists with: Deity / SourceFact / Collective > 0; History > 2;
                      a non-H1/H2 History row; H1 or H2 duplicated; a relation to anything but the
                      shared compatible Source; any non-expected citation（wrong locator, wrong Source,
                      Source not related to the History, extra citation, Deity citation）;
                      coordinate drift; goriyaku text / tag links / assignments
CLEAN_CREATE          target_exact = 0（and no conflict）
ALREADY_MATERIALIZED  target = 1; History = exactly H1 + H2; relations = 2, H1 → shared, H2 → shared;
                      citations = 2, H1 and H2 each one expected citation; shared identity = compatible = 1;
                      Deity / SourceFact / Collective / goriyaku additions = 0
PARTIAL_EXISTING      target present, nothing contradictory, but incomplete（e.g. Base only, H2 missing,
                      a citation missing）
```

Mother Ship confirms the class. The query authorizes nothing. A real Production state is not forced
into CLEAN_CREATE. The pre-Base guard is written for CLEAN_CREATE only; any other accepted class needs
its own reviewed guard.

## 7. Expected delta（not frozen）

Repository payload maximum for a clean create:

```text
Shrine     +1
Source     +(1 - accepted_shared_source_count)   （0 if REUSABLE, 1 if ABSENT）
Deity      +0
History    +2
Citation   +2
SourceFact +0
Collective +0
goriyaku   +0
```

This is **not** the Production expected delta.

```text
PRODUCTION_EXPECTED_DELTA = NOT FROZEN
```

Hypothesis only（not a measurement）: because nsrc-000007 G7 created the S2 Source in Production
（§17.4 / §22 of its audit）, Production may report the shared Source as REUSABLE and
`same_name_other_address_count = 1`. Neither is assumed. Both are frozen only from the real read-only
measurement after Mother Ship acceptance.

## 8. Fail-closed guards

### 8.1 Frozen pre-state block（UNSET）

`-- BEGIN/END nsrc_000009_frozen_pre_state` is byte-identical in the three guard files:

```text
frozen_values_set               = false
shrine_total / source_total / deity_total / history_total / citation_total
source_fact_total / collective_total                  = NULL
same_name_other_address_total                         = NULL
accepted_shared_source_count                          = NULL
```

Every guard asserts `f.frozen_values_set` first. In the committed state every guard raises
`division by zero`（disposable DB via `psql --set ON_ERROR_STOP=1`: exit 3 for all three）. Even if
`frozen_values_set` alone were flipped, NULL comparisons keep the guard failing; the regression test also
rejects any non-UNSET block. Replacing this block with measured Production values requires a separate,
Mother-Ship-authorized change.

### 8.2 Pre-Base guard（CLEAN_CREATE only）

- aggregates（incl. Citation）= frozen;
- target exact = 0, same-address = 0, `赤城社` at other addresses = frozen;
- shared Source identity = compatible = lookalike = frozen accepted count（0 or 1）, 0 unparseable
  government URLs;
- target Deity / History / relations / citations / SourceFact / Collective / goriyaku tags /
  assignments = 0.

### 8.3 Post-Base guard

- Shrine = frozen + 1; Source / Deity / History / Citation / SourceFact / Collective unchanged;
- target exact = 1, same-address = 1, `赤城社` at other addresses unchanged;
- coordinate `37.089683, 138.748108` within 1e-8, goriyaku `""`;
- target Knowledge / relations / citations absent, goriyaku tag links and assignments 0;
- shared Source state unchanged.

### 8.4 Post-Knowledge verification

- Shrine +1, Source +(1 − accepted), Deity +0, History +2, Citation +2, SourceFact +0, Collective +0;
- target exact = 1, same-address = 1, same-name other address unchanged, canonical coordinate,
  goriyaku `""`;
- target Deity 0 / SourceFact 0 / Collective 0 / History 2, H1 exactly once and H2 exactly once（all
  fields incl. content）;
- relations exactly 2, none to a non-shared Source; H1 and H2 each exactly one relation, to the
  shared compatible Source; source-less History 0;
- citations exactly 2, none non-expected; H1 and H2 each exactly one citation, expected（shared Source,
  `中魚沼郡誌上 p.445`, Source related to that History）;
- shared Source identity = compatible = lookalike = 1, 0 unparseable → bibliography is still
  `中魚沼郡誌上 p.398`;
- goriyaku tag links 0 and ShrineGoriyakuAssignment 0.

## 9. Disposable local simulation（not Production）

### 9.1 SQL execution through psql

Disposable local PostgreSQL 16.15 DB（nogis migrations, 125-row Base Seed, the nsrc-000009 target row
deleted, nsrc-000007 Knowledge imported to reproduce the lineage）, executed with
`psql --set ON_ERROR_STOP=1`. Local values only:

```text
nsrc_000009_g7_preflight.sql            exit 0
  aggregates                            124 / 2 / 0 / 2 / 0 / 0 / 0（local, not Production）
  target / same-name / other-addr / same-address = 0 / 1 / 1 / 0
  shared Source                         1 / 1 / 1 / 0 / 0 -> REUSABLE
  production_state_class_candidate      CLEAN_CREATE
nsrc_000009_g7_backup_version_check.sql exit 0
pre_base_guard（UNSET）                 ERROR division by zero（exit 3）
post_base_guard（UNSET）                ERROR division by zero（exit 3）
post_knowledge_verification（UNSET）    ERROR division by zero（exit 3）
citation table dropped                  preflight exit 3 after the table-existence row
```

The DB was dropped afterwards.

### 9.2 Regression rehearsals（pytest disposable DB）

`backend/temples/tests/test_nsrc_000009_g7_source_identity_sql.py`（83 tests）. Frozen values are
substituted **in memory only**, from the disposable DB's own pre-state counts, to exercise guard
semantics. The committed SQL is never modified.

| Area | Cases |
|---|---|
| File contract | `guard.is_readonly_sql` on all 5 files; SELECT / WITH only; no connection identifiers; identity and target-facts blocks identical; frozen block identical, UNSET, 9 NULLs, `frozen_values_set=false` |
| Schema | citation table = `ShrineFactSourceCitation._meta.db_table`; every `to_regclass` table exists; preflight / backup check run inside `SET TRANSACTION READ ONLY` with aggregates unchanged |
| Importer equivalence | SQL `normalized_url` == `normalize_source_url()` for identity variants, lookalikes, unparseable URLs, and a general corpus |
| Identity semantics | identity variants = identity; lookalikes ≠ identity but flagged; unparseable = NULL; wrong source_type ≠ identity; publisher drift and bibliography rewritten to p.445 = identity but not compatible |
| Unset guards | all three raise division by zero in the pre-state and in the materialized state |
| Source states | ABSENT → CLEAN_CREATE（accepted 0）; REUSABLE via nsrc-000007 lineage and via URL variant → CLEAN_CREATE（accepted 1）; pre-guard PASS only with the matching accepted count. Metadata drift, bibliography p.445, identity ambiguous, non-identity lookalike, lineage + lookalike, importer-unparseable → CONFLICT, pre-guard FAIL for accepted 0 and 1 |
| Pre-state drift（lineage） | Shrine / Source / Deity / History / Citation / SourceFact / Collective +1, same-name other address +1, shared Source publisher drift, bibliography → p.445, new lookalike → pre-guard FAIL |
| Exact identity | nsrc-000007 + two other `赤城社` rows → CLEAN_CREATE, `is_canonical_target=false`, target counts 0, frozen same-name = 3 PASS; different-name row at the target address → CONFLICT / FAIL |
| State lifecycle | CLEAN_CREATE → Base only = PARTIAL_EXISTING → Knowledge = ALREADY_MATERIALIZED |
| CONFLICT matrix（materialized target） | wrong locator, extra citation, citation to unrelated Source（clean() bypassed）, relation + citation to wrong Source, extra relation, current Deity `大山祇命`, extra History, H1 content drift, SourceFact, Collective, goriyaku text, goriyaku tag, coordinate drift, shared bibliography → p.445 |
| PARTIAL matrix | missing citation, citation moved to nsrc-000007 History, H2 missing |
| Base subset | deterministic one row; full Base Seed never the payload; fails on missing / duplicated target, latitude / longitude / location / goriyaku drift, same-name-other-address only; refuses in-repository output |
| Sequential rehearsal（both lineages） | pre-Base PASS → subset dry-run（no write）→ apply `created=1` → second dry-run `skipped=1` → post-Base PASS（pre-Base / post-Knowledge FAIL）→ Knowledge dry-run → apply → second dry-run / apply（no CREATE, `citations created=0`）→ post-Knowledge PASS（pre / post-Base FAIL）→ ALREADY_MATERIALIZED; goriyaku snapshot unchanged; reused Source row byte-unchanged |
| Post-Knowledge negatives | every CONFLICT and PARTIAL mutation above → FAIL（PASS immediately before） |
| Post-Base negatives | extra Shrine, coordinate drift, goriyaku text, goriyaku tag, extra citation elsewhere → FAIL |
| Runtime QA | `main()` prints all PASS lines + `TRANSACTION_MODE=READ_ONLY`, aggregates unchanged; wrong locator / bibliography p.445 / current Deity → AssertionError |

Knowledge plans observed:

```text
nsrc-000007 lineage（shared Source REUSABLE）
  first : {'source_REUSE_EXISTING': 1, 'history_CREATE': 2, 'citation_CREATE': 2}
          sources created=0, histories created=2, citations created=2
  second: {'source_REUSE_EXISTING': 1, 'history_SKIP_EXISTS': 2, 'citation_SKIP_EXISTS': 2}
          CREATE = 0, citations created=0

shared Source ABSENT
  first : {'source_CREATE': 1, 'history_CREATE': 2, 'citation_CREATE': 2}
  second: {'source_REUSE_EXISTING': 1, 'history_SKIP_EXISTS': 2, 'citation_SKIP_EXISTS': 2}
```

Mutation sanity（temporary, restored byte-identical）:

```text
post-Knowledge target block locator p.445 -> p.398   20 failed
pre-Base frozen_values_set false -> true               1 failed（block contract; guards still fail on NULLs）
```

## 10. Target-only Base subset

```text
scripts/migration_safety/nsrc_000009_g7_extract_base_subset.py <OUTPUT_PATH outside repo>
SUBSET_ROWS=1
name_jp=赤城社
address=新潟県十日町市伊達乙48番地
SUBSET_SHA256=e054685f13bd6375ff918c7a2d92f094d9e9ae56d40720f0de77f5a3aa0a95e7   （two runs, byte-identical）
```

```json
[{"name_jp": "赤城社", "address": "新潟県十日町市伊達乙48番地", "latitude": 37.089683,
  "longitude": 138.748108, "goriyaku": "", "kyusei": null, "astro_elements": [],
  "location": {"lat": 37.089683, "lng": 138.748108}}]
```

The extractor requires the exact (name_jp, address) row and the frozen canonical values（coordinate
authority: `docs/audit/shrine-position/niigata-h002-nsrc-000009-akagi-sha-position-review.md`）,
refuses an in-repository output path（`BLOCKED ... inside the repository`, exit 1）, and performs no DB
access. Generated subset files are not committed.

```text
FULL_BASE_SEED_PRODUCTION_APPLY = PROHIBITED
```

## 11. Production Runtime QA script

`scripts/migration_safety/nsrc_000009_g7_runtime_qa.py` runs entirely inside `transaction.atomic()` +
`SET TRANSACTION READ ONLY`:

- **Detail:** no ShrineDeity row on the target; serialized deities []; History 2 in order H1, H2, both
  `historical_event` / `source_confirmed`; each exactly one Source（importer identity comparison）, the
  same Source for both; only the target's own History rows; no `大山祇命`.
- **Fact citation integrity:** H1 and H2 each relate only to the shared Source and have exactly one
  citation, on that Source, `locator_text = 中魚沼郡誌上 p.445`; no target Deity citation; shared Source
  bibliography still `中魚沼郡誌上 p.398`.
- **Concierge:** exact (name, address) candidate once; coordinate `37.089683 / 138.748108`;
  `distance_m=0`; History [H1, H2]; Deity []; goriyaku tags [].
- **Reason:** H1 selected（G6-measured）; `deity` / `fact.deity` / `fact.goriyaku` None; reason uses H1
  only; no `大山祇命`; none of the 10 guarantee phrases.
- **Compass:** finite positive int distance; bearing in [0, 360); canonical direction label; the
  matching direction keeps the candidate, and the other seven exclude it.

Recommendation Top1 and Compass Top1 are not required.

## 12. Backup / restore readiness（procedure; not executed）

```text
LOCAL_CLIENT（this environment） = psql 16.15
PRODUCTION_SERVER_VERSION       = NOT MEASURED（PostgreSQL 17.6 at the nsrc-000007 measurement; not reused）
BACKUP_RESTORE_READINESS        = HOLD
```

Same procedure as nsrc-000007 §11 / §18.4（active fingerprint contract）, with the citation table added:

1. Run `sql/nsrc_000009_g7_backup_version_check.sql` read-only and record the server major version.
2. Use `pg_dump` / `pg_dumpall` / `pg_restore` / `psql` of the same or newer major.
3. Take a **fresh** Production backup with `dump_readonly.sh`, stored outside the repository.
4. Restore it with `restore_isolated.sh` into a disposable DB whose name contains `restore_test` /
   `audit` / `migration_safety`.
5. Run `nsrc_000009_g7_preflight.sql` on the restored DB. The fingerprint（latest temples migration,
   table existence incl. `temples_shrinefactsourcecitation`, aggregates incl. Citation, identity,
   same-name / same-address, shared Source state, target Knowledge / relations / citations,
   goriyaku, state class）must match the Production read-only measurement.
6. Run the committed `nsrc_000009_g7_pre_base_guard.sql`, with the Mother-Ship-frozen values, on the
   restored DB. It must PASS.
7. If any step fails: `PRODUCTION_WRITE_READY = HOLD`.

## 13. Notes

- **btrim vs strip（inherited, fail-closed direction）:** the SQL compares reuse metadata with
  `btrim()`（spaces only）, the importer with Python `str.strip()`（all whitespace）. A Production value
  with a trailing tab / full-width space would be CONFLICT_METADATA_DRIFT in SQL while the importer
  would reuse it. The SQL is stricter, never looser. Same as nsrc-000002 / nsrc-000007.
- **verified_at representation（not changed）:** History `verified_at = 2026-10-16T00:00:00+09:00` is
  stored as `2026-10-15T15:00:00Z`. G7 does not "fix" this.
- **Python 3.13 local observation（pre-existing, not this PR）:** under Python 3.13.16,
  `test_nsrc_000002_g7_source_identity_sql.py::test_sql_normalized_url_equals_importer_normalize_source_url`
  fails for `https:example.com/p/`（`urlunsplit` behaviour changed）. Under Python 3.11（CI version）
  the whole suite passes. nsrc-000009 identity URLs are not affected; the corpus here passes on both.

## 14. Validation

```text
guard.py check-readonly-sql（5 nsrc-000009 SQL files）           SAFE × 5
test_nsrc_000009_g7_source_identity_sql.py                       83 passed
nsrc-000009 G4 / base / G5 / G6 + G7, nsrc-000007 G7,
  test_fact_source_citation.py                                   225 passed
backend full suite, Python 3.11.17（-n auto）                     5785 passed, 8 skipped
scripts/migration_safety/tests                                   320 passed
scripts/tests                                                    685 passed
makemigrations --check                                           No changes detected
ruff check / format --check（new Python files）                   clean
git diff --check                                                 clean
```

## 15. Impact boundary

```text
Production connection / read / write          NONE
Base Seed / Knowledge Seed / Candidate Master NONE
Source reuse semantics / SOURCE_REUSE_CONFLICT UNCHANGED
Ranking / Score / Recommendation / Evidence Gate NONE
Position / Knowledge payload                  NONE
models / migrations / runtime implementation  NONE
g7_sql_generator / existing G7 artifacts      NONE
G1–G6 audit outcomes                          UNCHANGED
G8                                            NOT EXECUTED
```

## 16. Rollback

Revert the commits. They add scripts, SQL, a test, and this audit only. Nothing was written to
Production. The disposable databases were dropped.

## 17. Next（requires Mother Ship）

1. Run `nsrc_000009_g7_preflight.sql` on Production through `readonly_query.sh`（Credential Bridge）.
   If `fact_source_citation_table_exists = false`: STOP（§5）.
2. Mother Ship reviews the measurements and accepts a `production_state_class`. On CONFLICT,
   PARTIAL_EXISTING, ALREADY_MATERIALIZED, or any unexpected state: STOP and decide separately.
3. A separate PR freezes the measured values（including `citation_total` and
   `accepted_shared_source_count`）into the three guards' frozen block.
4. Fresh backup → isolated restore → fingerprint match（§12）.
5. Only then can Mother Ship authorize the Production write and the Formal G7 decision.

```text
STOP — no Production read, backup, or write is authorized or performed by this PR.
```

## 18. Production read-only measurement and freeze（follow-up PR, after #3237 / #3238）

- Recorded at: 2026-10-17
- Base: `develop@e1d953c`（#3238 merged）
- Branch: `audit/nsrc-000009-g7-freeze-production-prestate`

### 18.1 Measurement（supplied by Mother Ship）

Mother Ship executed `scripts/migration_safety/sql/nsrc_000009_g7_preflight.sql` on Production through
`readonly_query.sh`. This environment did not connect to Production. The values below are Mother Ship's
measurement and approval, used verbatim.

```text
latest temples migration           = 0121_shrine_fact_source_citation
temples_shrinefactsourcecitation   = exists
citation_total                     = 0

Shrine      = 124
Source      = 145
Deity       = 295
History     = 234
Citation    = 0
SourceFact  = 34
Collective  = 6

same_name_other_address_total      = 1
shared Source source_identity_state = REUSABLE
accepted_shared_source_count       = 1

production_state_class             = CLEAN_CREATE
```

Not supplied to this PR and therefore not recorded here: the server version string and the per-row
diagnostic listings. `docs/audit/production-temples-0121-migration-gate.md` in the repository still
shows its pre-execution status（HOLD）; this PR does not update that document. The 0121 application is
taken from Mother Ship's measurement（latest temples migration = 0121, citation table exists）.

```text
G7_READ_ONLY_PREFLIGHT = PASS
PRODUCTION_STATE_CLASS = CLEAN_CREATE
```

### 18.2 Frozen block（SET）

`-- BEGIN/END nsrc_000009_frozen_pre_state` is byte-identical in:

- `scripts/migration_safety/sql/nsrc_000009_g7_pre_base_guard.sql`
- `scripts/migration_safety/sql/nsrc_000009_g7_post_base_guard.sql`
- `scripts/migration_safety/sql/nsrc_000009_g7_post_knowledge_verification.sql`

```text
frozen_values_set              = true
shrine_total                   = 124
source_total                   = 145
deity_total                    = 295
history_total                  = 234
citation_total                 = 0
source_fact_total              = 34
collective_total               = 6
same_name_other_address_total  = 1
accepted_shared_source_count   = 1
```

Only the frozen block and each guard's stale "UNSET" header line changed. The Source identity block,
URL normalization, target facts block, coordinates, citation locator, and delta logic are
byte-unchanged. `nsrc_000009_g7_preflight.sql` is unchanged.

### 18.3 Expected Production delta（FROZEN）

```text
EXPECTED_PRODUCTION_DELTA
Shrine     +1
Source     +0   （shared Source REUSABLE: 1 - accepted_shared_source_count = 0）
Deity      +0
History    +2
Citation   +2
SourceFact +0
Collective +0
goriyaku   +0
```

| Aggregate | Pre-state | Post-Base | Post-Knowledge |
|---|---:|---:|---:|
| Shrine | 124 | 125 | 125 |
| Source | 145 | 145 | 145 |
| Deity | 295 | 295 | 295 |
| History | 234 | 234 | 236 |
| Citation | 0 | 0 | 2 |
| SourceFact | 34 | 34 | 34 |
| Collective | 6 | 6 | 6 |

```text
PRODUCTION_EXPECTED_DELTA = FROZEN
```

### 18.4 Disposable rehearsal with the committed frozen blocks

pytest disposable DB only. The committed guard files run unchanged.

Simulated pre-state: Base Seed without the target, nsrc-000007 Knowledge imported（shared Source
REUSABLE, the 四日町 `赤城社` as the one same-name row）, then unrelated non-lookalike filler rows bringing
the aggregates to exactly 124 / 145 / 295 / 234 / 0 / 34 / 6; preflight `CLEAN_CREATE`.

```text
exact Production pre-state      -> pre-Base PASS（post-Base FAIL, post-Knowledge FAIL）
target subset dry-run           -> no write
target subset apply             -> created=1; aggregates = 125 / 145 / 295 / 234 / 0 / 34 / 6
second subset dry-run           -> skipped=1
post-Base                       -> PASS（pre-Base FAIL, post-Knowledge FAIL）
Knowledge dry-run               -> {'source_REUSE_EXISTING': 1, 'history_CREATE': 2, 'citation_CREATE': 2}
Knowledge apply                 -> sources created=0, histories created=2, citations created=2
                                   aggregates = 125 / 145 / 295 / 236 / 2 / 34 / 6
post-Knowledge                  -> PASS（post-Base FAIL）
second Knowledge dry-run/apply  -> {'source_REUSE_EXISTING': 1, 'history_SKIP_EXISTS': 2,
                                   'citation_SKIP_EXISTS': 2}, no CREATE, citations created=0;
                                   post-Knowledge PASS; ALREADY_MATERIALIZED
shared Source row               -> byte-unchanged（bibliography 中魚沼郡誌上 p.398）
goriyaku snapshot               -> unchanged
```

Committed pre-Base guard drift（each starts from the exact pre-state, then fails）: Shrine / Source /
Deity / History / Citation / SourceFact / Collective +1, Source −1, same-name other address +1 and
swapped, target exists, different-name row at the target address, shared Source metadata drift /
bibliography → p.445 / identity ambiguous / non-identity lookalike（added and swapped）/
importer-unparseable / absent.

Committed post-Base guard fails on coordinate drift, goriyaku text, goriyaku tag, an extra citation
elsewhere, and an extra Shrine. Committed post-Knowledge verification fails on every CONFLICT and
PARTIAL mutation of §9.2. The committed guards also fail on a non-Production state（disposable lineage
aggregates）. The in-memory Source-state / state-class matrix（§9.2）is kept unchanged.

Mutation sanity（temporary, restored byte-identical）: pre-Base `source_total` 145 → 144 → 22 failed.

### 18.5 Validation

```text
guard.py check-readonly-sql（5 nsrc-000009 SQL files）        SAFE × 5
frozen block identical in 3 guard files                       1 distinct block
test_nsrc_000009_g7_source_identity_sql.py                    126 passed
nsrc-000009 base / knowledge / G5 / G6 / G7, nsrc-000007 G7,
  test_fact_source_citation.py                                268 passed
scripts/migration_safety/tests                                320 passed
ruff check / format --check（test）                            clean
git diff --check                                              clean
```

### 18.6 Changed files

```text
scripts/migration_safety/sql/nsrc_000009_g7_pre_base_guard.sql              frozen block SET + header line
scripts/migration_safety/sql/nsrc_000009_g7_post_base_guard.sql             frozen block SET + header line
scripts/migration_safety/sql/nsrc_000009_g7_post_knowledge_verification.sql frozen block SET + header line
backend/temples/tests/test_nsrc_000009_g7_source_identity_sql.py            SET assertions + committed-guard rehearsal
docs/audit/niigata-h002-nsrc-000009-g7-production-import-preflight.md       §0, §1 label, this section
```

### 18.7 Next（requires Mother Ship）

1. Use a PostgreSQL client of the Production major version and take a **fresh** Production backup outside
   the repository.
2. Restore it to a disposable DB. The `nsrc_000009_g7_preflight.sql` fingerprint must equal §18.1, and
   the committed `nsrc_000009_g7_pre_base_guard.sql` must PASS on the restored DB.
3. Only then can Mother Ship authorize the Production write and the Formal G7 decision.

```text
PRODUCTION_WRITE_READY      = HOLD
PRODUCTION_WRITE_AUTHORIZED = NO
PRODUCTION_WRITE            = NONE
FORMAL_G7                   = NOT EXECUTED

STOP — no Production backup or write is performed by this PR.
```
