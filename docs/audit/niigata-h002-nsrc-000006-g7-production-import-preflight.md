# NIIGATA-001-H002 — nsrc-000006 赤井神社 G7 Production Import Preflight（preparation only）

## 0. Current status — Production read-only measured and frozen

Mother Ship executed `nsrc_000006_g7_preflight.sql` against Production through the Credential Bridge after PR #3210 and accepted the measured state as `CLEAN_CREATE`.

```text
G7_READ_ONLY_PREFLIGHT      = PASS
PRODUCTION_STATE_CLASS      = CLEAN_CREATE
FROZEN_PRE_STATE            = SET
PRODUCTION_EXPECTED_DELTA   = FROZEN

PRODUCTION_SERVER_VERSION   = 17.6
LATEST_TEMPLES_MIGRATION    = 0120_shrine_source_fact_foundation

PRODUCTION_WRITE_READY      = HOLD
PRODUCTION_WRITE_AUTHORIZED = NO
PRODUCTION_WRITE            = NONE
FORMAL_G7                   = NOT_EXECUTED
G8                          = NOT_EXECUTED
```

Frozen Production pre-state:

```text
Shrine      123
Source      143
Deity       295
History     231
SourceFact   34
Collective    6

same_name_other_address_total = 0
S2 source_identity_state      = ABSENT
S3 source_identity_state      = ABSENT
s2_accepted_source_count      = 0
s3_accepted_source_count      = 0
```

Frozen expected delta:

```text
Shrine      +1
Source      +2
Deity       +0
History     +3
SourceFact  +0
Collective  +0
goriyaku    +0
```

Expected aggregate checkpoints:

| Aggregate | Pre | Post-Base | Post-Knowledge |
|---|---:|---:|---:|
| Shrine | 123 | 124 | 124 |
| Source | 143 | 143 | 145 |
| Deity | 295 | 295 | 295 |
| History | 231 | 231 | 234 |
| SourceFact | 34 | 34 | 34 |
| Collective | 6 | 6 | 6 |

No Production write was performed by the read-only measurement or by this freeze change.


## 1. Status

```text
candidate_id                = nsrc-000006
name_jp                     = 赤井神社
address                     = 新潟県佐渡市加茂歌代2662番地

G7_PREPARATION              = PASS（artifacts + disposable-DB rehearsal only）
PRODUCTION_READ_ONLY        = NOT_EXECUTED（Credential Bridge: VAR_SET=0）
PRODUCTION_STATE_CLASS      = NOT MEASURED
FROZEN_PRE_STATE            = UNSET（guards fail closed）
PRODUCTION_EXPECTED_DELTA   = NOT_FROZEN
BACKUP_CLIENT_COMPATIBILITY = HOLD（Production server version not measured; local client 16.15）
BACKUP_RESTORE_READINESS    = HOLD
PRODUCTION_WRITE_READY      = HOLD

PRODUCTION_WRITE_AUTHORIZED = NO
PRODUCTION_WRITE            = NONE
FORMAL_G7                   = NOT_EXECUTED
G8                          = NOT_EXECUTED
STOP                        = TRUE
```

- Recorded at: 2026-10-14
- Base: `develop@7ded481f`（#3209 merged）
- Branch: `audit/nsrc-000006-g7-production-import-preflight`
- Structural precedent: nsrc-000007 G7 preparation（PR #3193,
  `docs/audit/niigata-h002-nsrc-000007-g7-production-import-preflight.md` §1–§16）

Upstream authorities:

- `docs/knowledge/shrine-expansion-gate-contract.md`
- `docs/audit/niigata-h002-nsrc-000006-g4-knowledge-materialization.md`（G4 PASS）
- `docs/audit/niigata-h002-nsrc-000006-g5-recommendation-eligibility.md`（G5 PASS / ELIGIBLE）
- `docs/audit/niigata-h002-nsrc-000006-g6-runtime-qa.md`（G6 PASS）
- `backend/temples/data/knowledge_seeds/nsrc_000006_seed.json`

Local simulation is not a G7 PASS. No Production value appears in this PR, and no nsrc-000007 Production
count was reused. Repository, local DB, test DB, and Seed counts were not substituted for Production counts.

## 2. Credential boundary

```text
check_credential_presence.sh ~/.config/kami-musubi/production-db.env DATABASE_URL -> VAR_SET=0
PRODUCTION_READ_ONLY = NOT_EXECUTED
```

Nothing was requested, printed, or committed. This task did not connect to Production.

## 3. Artifacts

| File | Role |
|---|---|
| `scripts/migration_safety/sql/nsrc_000006_g7_preflight.sql` | read-only preflight（SELECT / WITH only） |
| `scripts/migration_safety/sql/nsrc_000006_g7_backup_version_check.sql` | server major version for backup client compatibility |
| `scripts/migration_safety/sql/nsrc_000006_g7_pre_base_guard.sql` | fail-closed pre-Base guard（frozen UNSET） |
| `scripts/migration_safety/sql/nsrc_000006_g7_post_base_guard.sql` | fail-closed post-Base guard（frozen UNSET） |
| `scripts/migration_safety/sql/nsrc_000006_g7_post_knowledge_verification.sql` | fail-closed post-Knowledge verification（frozen UNSET） |
| `scripts/migration_safety/nsrc_000006_g7_extract_base_subset.py` | deterministic one-row target subset |
| `scripts/migration_safety/nsrc_000006_g7_runtime_qa.py` | read-only Production Runtime QA（READ ONLY transaction） |
| `backend/temples/tests/test_nsrc_000006_g7_source_identity_sql.py` | identity / guard / rehearsal / negative regression（64 tests） |

All five SQL files pass `guard.py check-readonly-sql`. None contains a connection string, password, host,
username, SSL setting, database name, or credential.

## 4. Exact identity

```text
canonical target = name_jp = 赤井神社 AND address = 新潟県佐渡市加茂歌代2662番地
```

- Same-name rows at other addresses, including the noncanonical forms `新潟県佐渡市加茂歌代2622番地` and
  `新潟県佐渡市加茂歌代1164-7`, are diagnostics only and never identify the target. Their count is frozen,
  so any appearance after freezing fails closed.
- A row at the target address with a different name is `CONFLICT`.
- The preflight lists every `赤井神社` row and every row at the target address, with `is_canonical_target`.

## 5. Source identity（importer-equivalent, no approximation）

One shared block, `-- BEGIN/END nsrc_000006_source_identity`, is byte-identical in the preflight and the
three guards. It reuses the reviewed `source_url_norm` CTE verbatim（nsrc-000002 / nsrc-000007）, which
reproduces `knowledge_seed.normalize_source_url()`. S2 and S3 each get independent `*_identity`,
`*_metadata_compatible`, and `*_url_lookalike` CTEs.

| | S2 | S3 |
|---|---|---|
| source_type | `tourism_official` | `local_history` |
| seed URL | `https://sado-geinou.com/geinou/kamoutashiro/` | `https://dl.ndl.go.jp/pid/971197` |
| normalized identity | `https://sado-geinou.com/geinou/kamoutashiro` | `https://dl.ndl.go.jp/pid/971197` |
| metadata（`_SOURCE_REUSE_FIELDS`） | publisher `佐渡芸能アーカイブ`, bibliography `""`, `source_confirmed` / `high` / `ja` | publisher `新潟県神職会佐渡支部`, bibliography `新潟県神職会佐渡支部 編, 1926（大正15）, NDL書誌ID 000000585602`, `source_confirmed` / `high` / `ja` |
| lookalike diagnostic | host `sado-geinou.com` + path `geinou%kamoutashiro` | host `dl.ndl.go.jp` + path `pid%971197` |

Per-Source state, classified independently and failing closed:

```text
identity > 1                                -> CONFLICT_IDENTITY_AMBIGUOUS
identity = 1, compatible = 0                -> CONFLICT_METADATA_DRIFT
importer-unparseable URL of that type > 0   -> CONFLICT_IMPORTER_UNPARSEABLE_URL
lookalike that is not identity > 0          -> CONFLICT_NON_IDENTITY_LOOKALIKE
identity = 1, compatible = 1                -> REUSABLE
otherwise                                   -> ABSENT
```

The state class candidate is `CLEAN_CREATE` / `ALREADY_MATERIALIZED` / `PARTIAL_EXISTING` / `CONFLICT`,
with the same rules as the precedent, generalized to 3 Histories. Mother Ship confirms it; the query
authorizes nothing.

## 6. Knowledge shape and expected delta（not frozen）

```text
Deity = 0 / History = 3 / Collective = 0 / SourceFact = 0

H1 regional_context / 4月16日の赤井神社例祭と鬼太鼓奉納  -> S2 only
H2 tradition        / 元日午前0時の鬼太鼓奉納           -> S2 only
H3 regional_context / 加茂の五神社としての記録           -> S3 only
```

Repository payload maximum for a clean create:

```text
Shrine     +1
Source     +(2 - s2_accepted - s3_accepted)   （0..2）
Deity      +0
History    +3   （unchanged by Source reuse）
SourceFact +0
Collective +0
goriyaku   +0
```

This is not the Production expected delta. It is frozen only after a real read-only Production measurement
and Mother Ship acceptance of the state class.

```text
PRODUCTION_EXPECTED_DELTA = NOT_FROZEN
```

## 7. Fail-closed guards

### 7.1 Frozen pre-state block（UNSET）

`-- BEGIN/END nsrc_000006_frozen_pre_state` is byte-identical in the three guards:

```text
frozen_values_set = false
shrine_total / source_total / deity_total / history_total / source_fact_total / collective_total = NULL
same_name_other_address_total = NULL
s2_accepted_source_count / s3_accepted_source_count = NULL
```

Every guard asserts `f.frozen_values_set` first, so each committed guard raises `division by zero`.
This was verified on a disposable DB（§8.1）and by regression tests, including on a correctly materialized
state.

### 7.2 Guard semantics（once frozen）

- **Pre-Base（CLEAN_CREATE only）:**
  - aggregates = frozen;
  - target 0 and same-address 0;
  - same-name other-address = frozen;
  - per S2 / S3: identity = compatible = lookalike = frozen accepted count（0 or 1）, with 0 unparseable;
  - target Knowledge and goriyaku = 0.
- **Post-Base:**
  - Shrine +1, every other aggregate unchanged;
  - target 1, same-address 1, same-name other-address unchanged;
  - coordinate `38.085938, 138.418312` within 1e-8, goriyaku `""`;
  - target Knowledge still absent, goriyaku tag links and assignments 0;
  - S2 / S3 state unchanged.
- **Post-Knowledge:**
  - Shrine +1, Source +(2 − s2_accepted − s3_accepted), Deity +0, History +3, SourceFact +0, Collective +0;
  - target exact 1 with the canonical coordinate and goriyaku `""`;
  - Deity / SourceFact / Collective 0, History 3, each History with the frozen type / title / period /
    `event_date NULL` / `source_confirmed` / `high`;
  - relations exactly 3: H1 → S2-compatible only, H2 → S2-compatible only, H3 → S3-compatible only;
  - source-less History 0;
  - S2 and S3: identity = compatible = lookalike = 1, with 0 unparseable;
  - goriyaku tag links 0 and ShrineGoriyakuAssignment 0.

No Production numeric PK is referenced.

## 8. Disposable local simulation（not Production）

### 8.1 Raw SQL execution

On a disposable local PostgreSQL/PostGIS DB:

- develop migrations;
- the 124-row Base Seed;
- every repository Knowledge Seed except nsrc-000006;
- the target row then deleted.

```text
nsrc_000006_g7_preflight.sql  -> production_state_class_candidate = CLEAN_CREATE（S2 0/0, S3 0/0）
pre_base_guard（UNSET）       -> ERROR division by zero（exit 3）
post_base_guard（UNSET）      -> ERROR division by zero（exit 3）
post_knowledge_verification   -> ERROR division by zero（exit 3）
```

The DB was dropped afterwards.

### 8.2 Regression rehearsals（pytest disposable DB）

The test now carries the Mother-Ship-accepted `PRODUCTION_PRESTATE` and validates the committed frozen
guards unchanged against a disposable DB shaped to the exact Production aggregates. Existing in-memory
Source-state matrix / rehearsal / negative coverage remains in place so accepted-count variants and conflict
states continue to exercise guard semantics without weakening the fail-closed checks. Production is never
contacted by pytest.

| Area | Result |
|---|---|
| File contract | identity block identical in 4 files; frozen block byte-identical in all 3 guards and equal to the accepted Production measurement; no NULLs; `frozen_values_set=true`; SELECT / WITH only; no connection identifiers |
| Importer equivalence | SQL `normalized_url` == `normalize_source_url()` for S2 / S3 identity variants, lookalikes, unparseable URLs, and a general corpus |
| Identity semantics（S2, S3） | variants = identity; lookalikes ≠ identity but flagged; unparseable = NULL; wrong source_type ≠ identity; S2 / S3 never match each other; drifted metadata = identity but not compatible |
| Committed frozen guards | reject ordinary local/Base states; exact simulated Production pre-state passes pre-Base only; committed sequential rehearsal and drift/negative checks cover the frozen guards unchanged |
| Source-state matrix（12 cases） | ABSENT / REUSABLE combinations → CLEAN_CREATE, pass only with the matching accepted counts（wrong S2 or S3 count fails）; METADATA_DRIFT / IDENTITY_AMBIGUOUS / NON_IDENTITY_LOOKALIKE / IMPORTER_UNPARSEABLE_URL for S2 and S3 → CONFLICT, pre-Base fails for every accepted-count combination |
| Exact identity | both noncanonical-address `赤井神社` rows → still CLEAN_CREATE, frozen `same_name_other_address_total=2`, pre-Base PASS; a different-name row at the target address → CONFLICT / FAIL |
| Base subset | deterministic; exactly the canonical row; fails closed on a missing row, coordinate drift, or noncanonical-address-only data; refuses in-repository output |
| Sequential rehearsal（sources absent / S2 reused / S3 reused / both reused） | pre-Base PASS → subset dry-run（no write）→ apply `created=1` → second dry-run `created=0` → post-Base PASS（pre-Base / post-Knowledge FAIL）→ Knowledge dry-run plan matches reuse（absent: `source_CREATE 2`, `history_CREATE 3`）→ apply → post-Knowledge PASS → second import `{'source_REUSE_EXISTING': 2, 'history_SKIP_EXISTS': 3}`, no CREATE, aggregates unchanged; goriyaku unchanged; Deity 0; relations H1 / H2 → S2, H3 → S3 |
| Pre-Base negatives（16） | aggregate drift（Shrine / Source / Deity / History / Collective）, target already exists, different-name same-address, noncanonical address 2622番地 / 1164-7, S2 / S3 accepted-count drift, S2 metadata drift, S3 identity ambiguity, S2 / S3 lookalike, S3 importer-unparseable → all FAIL |
| Post-Base negatives（5） | extra unrelated Shrine, coordinate drift, goriyaku text, goriyaku tag, Knowledge created early → all FAIL |
| Post-Knowledge negatives（12） | extra Deity, extra relation H1 → S3 / H3 → S2, swapped H1 → S3 / H2 → S3 / H3 → S2, source-less History, goriyaku text, goriyaku tag, coordinate drift, extra unrelated Shrine, SourceFact → all FAIL |
| Runtime QA rehearsal | `main()` on the rehearsed state（noncanonical rows present）prints every PASS line + `TRANSACTION_MODE=READ_ONLY`; aggregates unchanged |

Mutation sanity:

- S3 identity URL changed in the preflight block → 3 failed;
- the H2 → S2 relation check changed to S3 in post-Knowledge → 16 failed.

Both files were restored byte-identical.

## 9. Target-only Base subset

```text
scripts/migration_safety/nsrc_000006_g7_extract_base_subset.py <OUTPUT_PATH outside repo>
SUBSET_ROWS=1
name_jp=赤井神社
address=新潟県佐渡市加茂歌代2662番地
SUBSET_SHA256=1d0fe560f9caa2a49638f6963ed27ef768117c867a714f38f8cab6b04df99c32   （two runs, byte-identical）
```

```json
[{"name_jp": "赤井神社", "address": "新潟県佐渡市加茂歌代2662番地", "latitude": 38.085938,
  "longitude": 138.418312, "goriyaku": "", "kyusei": null, "astro_elements": [],
  "location": {"lat": 38.085938, "lng": 138.418312}}]
```

The extractor:

- requires the exact (name_jp, address) row and the frozen canonical values（exact G2 coordinate）;
- refuses an in-repository output path（verified: `BLOCKED`, exit 1）;
- performs no DB access.

Generated subset files are not committed.

```text
FULL_BASE_SEED_PRODUCTION_APPLY = PROHIBITED
```

## 10. Production Runtime QA script

`scripts/migration_safety/nsrc_000006_g7_runtime_qa.py` runs entirely inside `transaction.atomic()` +
`SET TRANSACTION READ ONLY` and verifies:

- **Exact target:**
  - `resolve_shrine` returns `OK` to the exact row;
  - the noncanonical addresses never resolve to it;
  - the adopted coordinate `38.085938, 138.418312` is retained.
- **Detail:**
  - Deity 0; History 3 in order H1, H2, H3;
  - H1 / H2 → S2 only, H3 → S3 only, compared by importer identity;
  - `source_confirmed`; none of the unsupported current Deity names（素盞嗚尊 / 別雷尊 / 倉稲魂命 / 菅原道真公）.
- **Shared Recommendation eligibility:** verifier `(1, 0, 0)`, `ELIGIBLE`, Deity 0 / History 3; partition 1 / 1.
- **Concierge candidate path:**
  - exact candidate once; canonical coordinate; `distance_m=0`;
  - History [H1, H2, H3]; Deity []; goriyaku tags [];
  - the shared filter preserves the candidate.
- **Reason:**
  - H1 is selected（G6-measured）; deity / goriyaku None;
  - neither H2 nor H3 is substituted;
  - no unsupported Deity name and none of the 10 guarantee phrases.
- **Compass:**
  - distance int > 0 and finite; bearing in [0, 360);
  - the matching direction keeps the candidate, and the other seven exclude it.
- **Aggregates:** Shrine / Source / Deity / History / SourceFact / Collective unchanged by the QA.

Recommendation Top1 and Compass Top1 are not required.

## 11. Backup / restore readiness（procedure; not executed）

```text
PRODUCTION_SERVER_VERSION   = 17.6
LOCAL_CLIENT                = pg_dump / psql / pg_restore 16.15 (previously observed; re-check before backup)
BACKUP_CLIENT_COMPATIBILITY = HOLD
BACKUP_RESTORE_READINESS    = HOLD
```

Required before any Production write（`scripts/migration_safety/README.md` Credential Bridge; credential
outside the repository, mode 600, never printed）:

1. Run `sql/nsrc_000006_g7_backup_version_check.sql` read-only and record the server major version.
2. Use `pg_dump` / `pg_dumpall` / `pg_restore` / `psql` of the same or newer major
   （`PG_DUMP_BIN` / `PG_DUMPALL_BIN`）.
3. Take a fresh Production backup with `dump_readonly.sh`, stored outside the repository.
4. Restore it to a disposable DB（name contains `restore_test` / `audit` / `migration_safety`）with
   `restore_isolated.sh`, including the extensions.
5. The `nsrc_000006_g7_preflight.sql` output on the restored DB must equal the Production read-only
   output exactly.
6. The pre-Base guard, with the Mother-Ship-frozen values, must PASS on the restored DB.
7. If any step fails: `PRODUCTION_WRITE_READY = HOLD`.

## 12. Deviations from the nsrc-000007 precedent

1. **Same-name wording.** The nsrc-000007 header stated that H002 has other distinct shrines with the same
   name. That is not established for `赤井神社`, so it was replaced with neutral wording: same-name rows at
   other addresses, including the two named noncanonical forms, are diagnostics only.
2. **Knowledge shape.** There are 3 Histories, and two of them（H1, H2）share S2. The relation checks were
   generalized: per-History relation count = 1 and the relation is to the right compatible Source;
   total relations = 3; History delta +3.
3. **Runtime QA scope.** It adds `EXACT_TARGET`, `SHARED_RECOMMENDATION_ELIGIBILITY`, and
   `AGGREGATES_UNCHANGED`, as requested. The nsrc-000007 script covered Detail / Concierge / Reason /
   Compass only.
4. **Negative tests across preparation and freeze.** The preparation PR already carried the full in-memory
   negative list. This freeze change keeps that coverage and adds committed-guard validation against an exact
   simulated Production pre-state plus committed drift / post-Knowledge negative checks. Rehearsal still covers
   the `s3-reused` case.
5. **Lookalike breadth.** The S3 path token `pid%971197` also flags other NDL IDs that start with
   `971197`（e.g. `pid/9711970`）, as well as page sub-paths. Such rows classify as
   `CONFLICT_NON_IDENTITY_LOOKALIKE`. This is conservative and fails closed; Mother Ship reviews any such
   Production row.

The Source normalization（`source_url_norm`）is unchanged from the precedent.

## 13. verified_at representation（documented risk; not changed）

```text
seed value  2026-10-14T00:00:00+09:00  =  stored instant 2026-10-13T15:00:00Z
```

A UTC calendar-date rendering would show `2026-10-13`. The Knowledge Seed is unchanged.

## 14. Validation

Freeze-change validation is intentionally recorded in two phases.

### 14.1 Completed before this freeze change

```text
Production readonly_query / nsrc_000006_g7_preflight.sql       PASS
Production state candidate                                     CLEAN_CREATE
Mother Ship acceptance                                         CLEAN_CREATE
3 guard frozen blocks                                           byte-identical
Frozen values vs Production measurement                         MATCH
```

### 14.2 Required on the freeze branch before PR

```text
committed guard rehearsal                                      PENDING
committed drift / negative tests                               PENDING
test_nsrc_000006_g7_source_identity_sql.py                     PENDING
nsrc-000006 regression set                                     PENDING
guard.py check-readonly-sql                                    PENDING
git diff --check                                               PENDING
```

No PASS count is copied forward from the preparation PR. The freeze branch must record fresh results.

## 15. Impact boundary

```text
Production connection / write                         NONE
Candidate Master / Base Seed / Knowledge Seed         NONE
G1–G6 decisions                                       UNCHANGED
Ranking / Score / Recommendation / Evidence Gate      NONE
Concierge / Compass runtime / models / migrations     NONE
existing G7 artifacts（nsrc-000002 / 000004 / 000007） NONE
G8                                                    NOT_EXECUTED
```

## 16. Rollback

Revert the commit. It adds scripts, SQL, a test, and this audit only.

## 17. Next

1. Run the freeze-branch committed guard rehearsal and drift / negative tests.
2. Run the full nsrc-000006 G7 regression set and read-only SQL checks; record fresh counts in §14.
3. Open the freeze PR only after those checks are green.
4. After merge, take a fresh Production backup with a PostgreSQL 17-compatible client.
5. Restore to an isolated DB; require Production-preflight fingerprint equivalence and committed pre-Base guard PASS.
6. Only then can Mother Ship separately authorize the Production write and Formal G7.

```text
PRODUCTION_WRITE_READY      = HOLD
PRODUCTION_WRITE_AUTHORIZED = NO
PRODUCTION_WRITE            = NONE
STOP                        = TRUE
```
