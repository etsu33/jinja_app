# NIIGATA-001-VPG001 — nsrc-000021 荒川神社 G7 Production Import Preflight

## 1. Status（preparation only）

```text
candidate_id                = nsrc-000021
name_jp                     = 荒川神社
address                     = 新潟県胎内市桃崎浜187番地
adopted coordinate（G2）     = 38.1409456, 139.4073314

G7_PREPARATION              = PASS（artifacts + disposable-DB rehearsal only）
PRODUCTION_READ_ONLY        = NOT_EXECUTED
PRODUCTION_STATE_CLASS      = NOT_MEASURED
FROZEN_PRE_STATE            = UNSET（guards fail closed）
PRODUCTION_EXPECTED_DELTA   = NOT_FROZEN
BACKUP_RESTORE_READINESS    = HOLD
PRODUCTION_WRITE_READY      = HOLD

PRODUCTION_WRITE_AUTHORIZED = NO
PRODUCTION_WRITE            = NONE
FORMAL_G7                   = NOT_EXECUTED
G8                          = NOT_EXECUTED

FULL_BASE_SEED_PRODUCTION_APPLY = PROHIBITED
```

- Recorded at: 2026-10-19
- BASE_SHA: `4892060d26bb111fbf0fbcbbb4a73942bbba7afd`（develop, PR #3278 merge, VPG001 G6）
- Branch: `audit/niigata-vpg001-g7-production-import-preflight`

Upstream（verified on develop@4892060d）:

```text
G1 = PASS / CLOSED / SAME_NAME_DIFFERENT_SHRINE（docs/audit/niigata-vpg001-g1-identity-duplicate.md）
G2 = CLOSED / PASS（docs/audit/shrine-position/niigata-vpg001-nsrc-000021-position-review.md）
G3 = NORMAL_MODEL_FIT / PRODUCT_SURFACE = RECOMMENDATION（docs/audit/niigata-vpg001-g3-source-knowledge-fit.md）
G4 = CLOSED / PASS（docs/audit/niigata-vpg001-nsrc-000021-g4-formal-pass.md）
G5 = CLOSED / PASS / ELIGIBLE（docs/audit/niigata-vpg001-nsrc-000021-g5-recommendation-eligibility.md）
G6 = CLOSED / PASS（docs/audit/niigata-vpg001-nsrc-000021-g6-runtime-qa.md）
```

Local simulation is not a G7 PASS. G7 can only be decided after a real Production read-only preflight,
Mother Ship acceptance of the state class, a separate PR that freezes the measured values, a fresh backup
with an isolated restore, and an explicit Production write authorization.

## 2. Production boundary

```text
Production connection / read / write   NONE（no Credential Bridge was used）
credentials / hostnames / DB names      none in any committed file
Production-derived values               none; every frozen value is NULL
```

## 3. Precedent and why the generator was not used

Precedent: `docs/audit/niigata-h002-nsrc-000009-g7-production-import-preflight.md`（latest G7 preparation,
PR #3237 UNSET form）. The safety model is kept; the Knowledge shape is this candidate's own.

`scripts/migration_safety/g7_sql_generator.py` cannot represent this candidate（checked on develop, reported
to Mother Ship, who chose hand-written artifacts following the nsrc-000009 precedent）:

```text
normalized_url_identity family = exactly Source 1 / Deity 0 / History 1 / SourceFact 0
url_pattern_set family         = requires SourceFact stable_key >= 1; not importer-equivalent identity
spec production_pre_state      = numeric values required; cannot express the UNSET frozen block
this candidate                 = Source 1 / Deity 1 / History 1 / SourceFact 0 / Citation 0
```

The generator contract was not changed.

## 4. Artifacts

| File | Role |
|---|---|
| `scripts/migration_safety/sql/nsrc_000021_g7_preflight.sql` | read-only preflight（SELECT / WITH only） |
| `scripts/migration_safety/sql/nsrc_000021_g7_backup_version_check.sql` | server major version for client compatibility |
| `scripts/migration_safety/sql/nsrc_000021_g7_pre_base_guard.sql` | fail-closed pre-Base guard（UNSET） |
| `scripts/migration_safety/sql/nsrc_000021_g7_post_base_guard.sql` | fail-closed post-Base guard（UNSET） |
| `scripts/migration_safety/sql/nsrc_000021_g7_post_knowledge_verification.sql` | report SELECTs + fail-closed post-Knowledge guard（UNSET） |
| `scripts/migration_safety/nsrc_000021_g7_extract_base_subset.py` | target-only one-row Base subset; no DB access |
| `scripts/migration_safety/nsrc_000021_g7_runtime_qa.py` | READ ONLY Production Runtime QA |
| `backend/temples/tests/test_nsrc_000021_g7_source_identity_sql.py` | disposable-DB regression（105 tests） |

## 5. Read-only preflight

Statement order（`nsrc_000021_g7_preflight.sql`）:

```text
 1 database / user / server version availability（IS NOT NULL booleans only）
 2 server_version / server_version_num
 3 latest temples migration + 0121_shrine_fact_source_citation applied flag
 4 table existence（incl. temples_shrinedeity_sources, temples_shrinefactsourcecitation）
 5 aggregates: Shrine / Source / Deity / History / Citation / SourceFact / Collective
 6 target exact / same-name / same-name other address / same-address / same-address other name
 7 diagnostic listing of same-name or same-address rows（is_canonical_target）
 8 lookalike Source listing（identity / metadata-compatible flags）
 9 Source state row（9 columns, ends with source_identity_state）
10 diagnostic: every Deity / History of any shrine related to a lookalike Source
11 target Deities  12 target Histories  13 target Fact-Source relations  14 target citations
15 target SourceFacts  16 target collectives / goriyaku tag links / assignments / goriyaku text
17 production_state_class_candidate（CLEAN_CREATE / ALREADY_MATERIALIZED / PARTIAL_EXISTING / CONFLICT）
```

### 5.1 Exact target identity

```text
target         = 荒川神社 / 新潟県胎内市桃崎浜187番地（exact name_jp + address; no numeric PK）
same-name other addresses（frozen G1 identities; diagnostics only）:
  荒川神社 / 新潟県新発田市荒川5431番地
  荒川神社 / 新潟県村上市小岩内463番地
  荒川神社 / 新潟県村上市荒川542番地
same-address other owner:
  none
```

### 5.2 Source identity（importer-equivalent）

```text
key            = NIIGATA_PREF_KITAMAEBUNE02
source_type    = government
url            = https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html
normalized_url = https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html
publisher      = 新潟県
reuse fields   = publisher / verification_status / confidence / bibliography（''）/ language（_SOURCE_REUSE_FIELDS）
lookalike      = lower(url or normalized_url) LIKE '%pref.niigata.lg.jp%' AND LIKE '%kitamaebune02%'
```

The `nsrc_000021_source_identity` block reproduces `knowledge_seed.normalize_source_url()`（the nsrc-000009 SQL
normalization, unchanged）. It is byte-identical in the four identity files. Identity is
`source_type + normalized URL` only; it is never approximated by raw URL, hostname, title or publisher.

| Source state | Meaning | Class | Pre-Base guard |
|---|---|---|---|
| ABSENT | no identity row | CLEAN_CREATE | PASS with accepted = 0 |
| REUSABLE | 1 identity row, metadata compatible | CLEAN_CREATE | PASS with accepted = 1 |
| CONFLICT_METADATA_DRIFT | 1 identity row, a reuse field differs | CONFLICT | FAIL |
| CONFLICT_IDENTITY_AMBIGUOUS | > 1 identity row | CONFLICT | FAIL |
| CONFLICT_NON_IDENTITY_LOOKALIKE | lookalike row that is not identity | CONFLICT | FAIL |
| CONFLICT_IMPORTER_UNPARSEABLE_URL | same source_type URL the importer cannot parse | CONFLICT | FAIL |

Any CONFLICT_* state: `PRODUCTION_WRITE_READY = HOLD`.

### 5.3 Target facts block

`nsrc_000021_target_facts`（byte-identical in the four identity files）: `target`, `target_deity` /
`target_history` with `expected_key` set only when every frozen field matches（display_name / role
`unknown` / history_type / title / content / period_text / event_date NULL / `source_confirmed` / `high` /
verified_at `2026-10-19T14:35:38+09:00`）, `target_relation`（Deity and History Source relations, `to_source` =
metadata-compatible identity）, `target_citation`, and `foreign_relation`（other shrines' Facts related to the
Source identity）.

Frozen payload:

```text
  Deity    天鈿女命（role unknown）
  History  regional_context / 船主による船絵馬の奉納  period_text=""
excluded Deity names on the target: none
```

S2（`https://www.pref.niigata.lg.jp/uploaded/attachment/180012.pdf`）is not in the seed and is not part of
this gate. The 天保12年（1814 / 1841）chronology conflict is not a Fact; the post-Knowledge exact-field match
admits only H1（regional_context, period_text ""）.

### 5.4 State class

```text
CONFLICT              Source CONFLICT_*, target exact > 1, same-address <> target exact, or an
                      unexpected / duplicated / excluded target Fact, a relation not to the Source,
                      any citation / SourceFact / Collective, coordinate drift, goriyaku drift
CLEAN_CREATE          target exact = 0（and no Source conflict）
ALREADY_MATERIALIZED  Deity 1 / History 1 exactly as frozen, 2 relations all to the Source,
                      Source identity 1 and compatible
PARTIAL_EXISTING      anything else（e.g. Base only, a missing Fact, a source-less Fact）
```

## 6. Repository payload maximum ≠ Production measured state ≠ Production expected delta

```text
repository payload maximum（not a Production delta）:
  Shrine +1 / Source +1 max / Deity +1 / History +1 / Collective +0 / SourceFact +0 / Citation +0 / goriyaku +0
Production measured state      = NOT_MEASURED
Production expected delta      = NOT_FROZEN
```

After a Production measurement, the expected delta is
`Shrine +1 / Source +(1 - accepted_source_count) / Deity +1 / History +1 / Citation +0 / SourceFact +0 / Collective +0`.
`accepted_source_count` is 0（ABSENT）or 1（REUSABLE）as measured; CREATE is not assumed from repository state.

## 7. Fail-closed guards

### 7.1 Frozen pre-state block（UNSET）

Identical in the three guards; `frozen_values_set = false`; every value `NULL::bigint`:

```text
shrine_total, source_total, deity_total, history_total, citation_total, source_fact_total,
collective_total, same_name_other_address_total, foreign_fact_source_relation_total,
accepted_source_count
```

Each guard is `SELECT 1 / CASE WHEN (f.frozen_values_set AND …) THEN 1 ELSE 0 END`, so it raises
division by zero while the block is UNSET. Only a separate, Mother-Ship-authorized PR may replace the block
with measured Production values.

### 7.2 Pre-Base guard（CLEAN_CREATE only）

Aggregates = frozen; target exact 0; same-address 0; same-name other address = frozen; Source identity =
compatible = lookalike = accepted（0 / 1）; no unparseable URL; foreign relations = frozen; no target Fact,
relation, citation, SourceFact, Collective, goriyaku tag or assignment.

### 7.3 Post-Base guard

Shrine = frozen + 1, every other aggregate unchanged; target exact 1; same-address 1; same-name other address
unchanged; coordinate 38.1409456 / 139.4073314 within 1e-8; goriyaku ''; no target Knowledge / relation /
citation yet; no goriyaku tag / assignment; Source state and foreign relations unchanged.

### 7.4 Post-Knowledge verification

Report SELECTs（aggregates, target integrity, Fact / Source listing）, then the guard: Shrine +1 / Source
+(1 − accepted) / Deity +1 / History +1 / Citation +0 / SourceFact +0 / Collective +0; every frozen Fact
exactly once with every field equal; exactly one relation each, to the compatible Source; no other target
Fact or relation; source-less Fact 0; excluded names 0; citation / SourceFact / Collective on the target 0;
Source identity = compatible = lookalike = 1; foreign relations unchanged; goriyaku tag / assignment 0.

## 8. Disposable local simulation（not Production）

### 8.1 SQL execution through psql

Disposable local PostgreSQL 16.15 DB（nogis migrations, 133-row Base Seed with the target row deleted, the
other three VPG001 Knowledge Seeds imported）, executed with `psql --set ON_ERROR_STOP=1`. Local values only:

```text
nsrc_000021_g7_preflight.sql             exit 0
  aggregates                         132 / 3 / 7 / 7 / 0 / 0 / 0（local, not Production）
  target / same-name / other / same-address / same-address other name = 0 / 0 / 0 / 0 / 0
  Source                             0 / 0 / 0 / 0 / 0 -> ABSENT
  production_state_class_candidate   CLEAN_CREATE
nsrc_000021_g7_backup_version_check.sql  exit 0
pre_base_guard（UNSET）              ERROR division by zero（exit 3）
post_base_guard（UNSET）             ERROR division by zero（exit 3）
post_knowledge_verification（UNSET） ERROR division by zero（exit 3）

after subset import + Knowledge import:
  import_shrines_seed（subset）      created=1 updated=0 skipped=0 total_seed=1
  import_shrine_knowledge           sources created=1, deities created=1, histories created=1, collectives created=0,
                                    memberships created=0, source_facts created=0
  preflight state class row         ALREADY_MATERIALIZED|1|1|1|1|1|2|0
  nsrc_000021_g7_runtime_qa.py          every surface PASS, AGGREGATES_UNCHANGED=PASS, TRANSACTION_MODE=READ_ONLY
```

The databases were dropped afterwards.

### 8.2 Regression rehearsals（pytest disposable DB）

`backend/temples/tests/test_nsrc_000021_g7_source_identity_sql.py`（105 tests）. Frozen values are substituted
**in memory only**, from the disposable DB's own pre-state, to exercise guard semantics. The committed SQL is
never modified.

| Area | Cases |
|---|---|
| File contract | `guard.is_readonly_sql` on all 5 files; SELECT / WITH only; no write verb; no connection identifiers; identity / target blocks identical; frozen block identical, UNSET, 10 NULLs |
| Schema | every `to_regclass` table exists; Deity / History relation tables are the model tables; preflight / backup check inside `SET TRANSACTION READ ONLY`, aggregates unchanged |
| Importer equivalence | SQL `normalized_url` == `normalize_source_url()` for identity variants, lookalikes, unparseable URLs, a general corpus |
| Identity semantics | identity variants = identity; lookalikes flagged, not identity; unparseable = NULL; wrong source_type ≠ identity; publisher / bibliography drift = identity but not compatible |
| Unset guards | all three raise division by zero in the pre-state, after Base, and after Knowledge |
| Source states | ABSENT / REUSABLE / REUSABLE（URL variant）→ CLEAN_CREATE, guard PASS only with the matching accepted count; metadata drift, bibliography drift, identity ambiguous, lookalike, reusable + lookalike, unparseable → CONFLICT, guard FAIL |
| Pre-state drift | Shrine / Source / Deity / History / Citation / SourceFact / Collective +1, existing target row, same-address different name, Source metadata drift, identity ambiguity, lookalike, unparseable, foreign relation to the Source, same-name other address +1 → FAIL |
| Exact identity | frozen same-name identities never the target; same-address other owner → CONFLICT |
| State lifecycle | CLEAN_CREATE → Base only = PARTIAL_EXISTING → Knowledge = ALREADY_MATERIALIZED |
| CONFLICT / PARTIAL matrix | unexpected / excluded Deity, Deity name drift, unexpected History, History content / type drift（if History）, extra relation, relation moved, citation, SourceFact, Collective, goriyaku text / tag / assignment, coordinate drift, Source metadata drift → CONFLICT; missing Deity / History, source-less Fact, wrong Fact owner → PARTIAL_EXISTING |
| Sequential rehearsal（3 lineages） | Base only（ABSENT）, VPG001 siblings（ABSENT）, REUSABLE: pre-Base PASS → subset dry-run → apply `created=1` → second dry-run / apply `skipped=1` → post-Base PASS → validate-only → dry-run → apply → second dry-run / apply（no CREATE, ids unchanged）→ post-Knowledge PASS → ALREADY_MATERIALIZED; goriyaku snapshot unchanged; reused Source byte-unchanged |
| Post-Knowledge negatives | every CONFLICT / PARTIAL mutation, Shrine +1, Citation +1, foreign relation, same-address row → FAIL |
| Post-Base negatives | Shrine +1, coordinate, goriyaku text / tag / assignment, premature Deity, same-address row → FAIL |
| Base subset | deterministic one row, SHA pinned; full Base Seed never the payload; missing / duplicated / drifted（lat / lng / location / goriyaku / kyusei / astro）/ other-address row → BLOCKED; in-repository output refused |
| Runtime QA | AST: `main()` starts with `transaction.atomic()` + `SET TRANSACTION READ ONLY`, the only `execute`, no write call; READ ONLY transaction rejects a write; `main()` prints every PASS line, aggregates unchanged; Deity drift / excluded Deity / Source drift / goriyaku / coordinate / same-address row → fail closed |

Knowledge plans observed:

```text
Source ABSENT : first {'source_CREATE': 1, ...}; second {'source_REUSE_EXISTING': 1, '*_SKIP_EXISTS'}
Source REUSABLE: first {'source_REUSE_EXISTING': 1, ...}; second same as above, CREATE = 0
```

Mutation sanity（nsrc-000021, temporary, restored byte-identical）: changing the first Deity name in the
committed target block made 30 of 105 tests fail.

## 9. Target-only Base subset

```text
scripts/migration_safety/nsrc_000021_g7_extract_base_subset.py <OUTPUT_PATH outside repo>
SUBSET_ROWS=1
name_jp=荒川神社
address=新潟県胎内市桃崎浜187番地
SUBSET_SHA256=9a608bc049ff4e6c4bfa2ca851c38df7f7d22f839eef49b3fb31f0cdcf5564b2   （byte-identical across runs）
```

```json
[{"name_jp": "荒川神社", "address": "新潟県胎内市桃崎浜187番地", "latitude": 38.1409456,
  "longitude": 139.4073314, "goriyaku": "", "kyusei": null, "astro_elements": [],
  "location": {"lat": 38.1409456, "lng": 139.4073314}}]
```

Exactly one row, exact name + address, frozen G2 coordinate, neutral goriyaku / kyusei / astro state from
the Base Seed. In-repository output is refused（`BLOCKED ... inside the repository`, exit 1）. No DB access.
Generated subset files are not committed.

```text
FULL_BASE_SEED_PRODUCTION_APPLY = PROHIBITED
```

## 10. Production Runtime QA script

`scripts/migration_safety/nsrc_000021_g7_runtime_qa.py` runs inside `transaction.atomic()` + `SET TRANSACTION READ ONLY`:

```text
TARGET_IDENTITY            exact (name, address); adopted G2 coordinate
DETAIL_RUNTIME             Deity 1 / History 1 exactly; each Fact source_confirmed with one Source
                           of the importer identity; only the target's own rows; excluded text absent
SOURCE_RELATION_INTEGRITY  one Source for every Fact, metadata as frozen; no citation / SourceFact / Collective
SHARED_ELIGIBILITY         verify_recommendation_eligibility = ELIGIBLE（1 / 1）
CONCIERGE_CANDIDATE_PATH   exact candidate once, coordinate, distance 0, Knowledge as frozen, tags []
RECOMMENDATION_REASON      G6-measured Deity sentence; no goriyaku / history_theme; no excluded text;
                           none of the 10 guarantee phrases
COMPASS_DISTANCE           275370 m from the QA origin（G6 value）
COMPASS_DIRECTION          北; matching label keeps it, the other 7 exclude it
GORIYAKU_ISOLATION         goriyaku '', no tag link, no assignment
FACT_OWNERSHIP_ISOLATION   only the target at the address; no foreign owner row
AGGREGATES_UNCHANGED       8 table counts + goriyaku tag links before = after
```

Recommendation Top1 and Compass Top1 are not required.

## 11. Backup / restore readiness（procedure; not executed）

```text
LOCAL_CLIENT（this environment） = psql 16.15
PRODUCTION_SERVER_VERSION       = NOT MEASURED
BACKUP_RESTORE_READINESS        = HOLD
```

1. Run `sql/nsrc_000021_g7_backup_version_check.sql` read-only and record the server major / minor version.
2. Use `pg_dump` / `pg_restore` / `psql` clients of the same or newer major.
3. Take a **fresh** Production backup with `dump_readonly.sh`, stored outside the repository.
4. Restore it with `restore_isolated.sh` into a disposable DB.
5. Run `nsrc_000021_g7_preflight.sql` on the restored DB; the fingerprint（latest temples migration, tables,
   aggregates incl. Citation, identity, same-name / same-address, Source state, target Knowledge, goriyaku,
   state class）must match the Production read-only measurement.
6. Run the committed pre-Base guard, with the Mother-Ship-frozen values, on the restored DB. It must PASS.
7. If any step fails: `PRODUCTION_WRITE_READY = HOLD`.

## 12. Future Production execution plan（not executed; requires authorization）

```text
pre-Base guard PASS（frozen values）
-> subset dry-run（no write）-> subset apply（created=1）-> second dry-run / apply（created=0）
-> post-Base guard PASS
-> Knowledge validate-only -> dry-run -> apply -> second import（CREATE = 0, aggregates unchanged）
-> post-Knowledge verification PASS
-> Production Runtime QA（READ ONLY）
```

## 13. Notes

- **btrim vs strip（inherited, fail-closed direction）:** the SQL compares reuse metadata with `btrim()`
  （spaces only）, the importer with `str.strip()`. The SQL is stricter, never looser.
- **verified_at:** stored as `2026-10-19T05:35:38+00:00`, the same instant as `14:35:38+09:00`. The guards
  compare the instant.
- **Citation table:** the seed（schema 1.0）has no citation. The table is counted only for aggregate
  invariance; the preflight requires `temples_shrinefactsourcecitation` to exist.

## 14. Validation

```text
guard.py check-readonly-sql（5 nsrc_000021 SQL files）                    SAFE × 5
test_nsrc_000021_g7_source_identity_sql.py                                 105 passed
```

Combined validation for the four candidates is recorded in the PR body.

## 15. Impact boundary

```text
Production connection / read / write                NONE
Base Seed / Knowledge Seeds / Candidate Master       NONE
Position values / G1–G6 audits                      NONE
Evidence Gate / Eligibility / Recommendation logic   NONE
Ranking / Score / Concierge / Compass                NONE
models / migrations / frontend                       NONE
g7_sql_generator / existing G7 artifacts             NONE
nsrc-000023                                         NONE（G7 NOT_AUTHORIZED）
```

## 16. Rollback

Revert the commit. It adds scripts, SQL, a test and this audit only. Nothing was written to Production. The
disposable databases were dropped.

## 17. Remaining HOLD items（require Mother Ship）

1. Run `nsrc_000021_g7_preflight.sql` on Production through `readonly_query.sh`（explicitly authorized read-only).
2. Mother Ship reviews the measurements and accepts a `production_state_class`. On CONFLICT,
   PARTIAL_EXISTING, ALREADY_MATERIALIZED or any unexpected state: STOP and decide separately.
3. A separate PR freezes the measured values into the three guards' frozen block.
4. Fresh backup → isolated restore → fingerprint match（§11）.
5. Only then can Mother Ship authorize the Production write and the Formal G7 decision.

```text
STOP — no Production read, backup, or write is authorized or performed by this PR.
```
