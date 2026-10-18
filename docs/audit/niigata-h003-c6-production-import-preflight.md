# NIIGATA-001-H003 — C6 Catalog Production Import Preflight（preparation）

## 1. Status

```text
write cohort                   = nsrc-000011 / nsrc-000012 / nsrc-000013 / nsrc-000015
diagnostics only               = nsrc-000014（G2 HOLD_POSITION_REVIEW）. Never in the write cohort.

C6_READ_ONLY_PREFLIGHT_SQL     = PREPARED（this PR）
PRODUCTION_PREFLIGHT           = NOT EXECUTED
PRODUCTION_STATE_CLASS         = NOT CLASSIFIED（requires the real Production output）
EXPECTED_PRODUCTION_DELTA      = NOT FROZEN
C6 write authorization         = NOT REQUESTED
C6 Production Import           = NOT EXECUTED
Production write               = NONE
```

- Recorded at: 2026-10-18
- Base: `develop@9f3a5e544d1d57014c25917c5c764deab0820c8b`（PR #3253 merge, Base Seed 125 → 129）
- Branch: `audit/niigata-h003-c6-production-preflight`

Production state is not inferred from the repository Base Seed or from any disposable DB.
Every disposable-DB result below shows that the SQL behaves as specified. None of it says
anything about Production.

## 2. Authority

- `docs/knowledge/shrine-expansion-gate-contract.md` §11A C6（Mother Ship approval, explainable
  delta, collision resolved, coordinate frozen, isolated preflight PASS. STOP on unexpected diff.）
- `docs/audit/niigata-h003-catalog-base-shrine-materialization.md`
- `docs/audit/niigata-h003-c5-catalog-runtime-qa.md`
- `docs/audit/niigata-h003-c4-catalog-evidence.md`
- `docs/audit/niigata-h003-position-hold-resolution.md`
- Precedent: `scripts/migration_safety/sql/nsrc_000006_g7_preflight.sql`,
  `scripts/migration_safety/sql/nsrc_000007_g7_preflight.sql`, `scripts/migration_safety/README.md`

| candidate_id | name_jp | address | adopted coordinate | role |
|---|---|---|---|---|
| nsrc-000011 | 赤城神社 | 新潟県新潟市江南区二本木1丁目7番16号 | 37.841794, 139.118507 | write cohort |
| nsrc-000012 | 赤城神社 | 新潟県長岡市四郎丸2丁目5番33号 | 37.440743, 138.855238 | write cohort |
| nsrc-000013 | 赤城神社 | 新潟県長岡市山屋314番地 | 37.496407, 139.008620 | write cohort |
| nsrc-000015 | 赤城神社 | 新潟県魚沼市湯之谷芋川311番地 | 37.214543, 139.036468 | write cohort |
| nsrc-000014 | 赤城神社 | 新潟県五泉市上杉川1310番地2 | NONE | diagnostics only（HOLD） |

## 3. Importer facts the contract is built on（read from code）

`backend/temples/management/commands/import_shrines_seed.py`:

```text
lookup            Shrine.objects.filter(name_jp=name, address=address).order_by("id").first()
absent            -> CREATE with payload（kind / visit_style_tags / history_theme / place_ref = model default）
present           -> compare every payload field. Any difference -> UPDATE (overwrite) that field.
payload fields    address, latitude, longitude, goriyaku, kyusei, astro_elements,
                  name_romaji, sajin, description, element
                  (+ location when USE_GIS=1, + visit_style_tags only when the seed row has the key)
coordinate equal  abs diff <= COORDINATE_ABS_TOLERANCE = 1e-12（rel_tol = 0）
other fields      strict equality（goriyaku NULL != "" -> UPDATE）
```

The four H003 seed rows carry `goriyaku: ""`, `kyusei: null`, `astro_elements: []` and no
`visit_style_tags` key. The expected payload for an existing row is therefore:

```text
goriyaku = ''  kyusei IS NULL  astro_elements = []  name_romaji IS NULL
sajin = ''     description IS NULL  element IS NULL
```

The importer does not write `kind`, `visit_style_tags`, `history_theme` or `place_ref`. A
Catalog-only row created by the importer has `kind = 'shrine'`, `visit_style_tags = []`,
`history_theme = ''` and `place_ref_id IS NULL`, plus no Knowledge, goriyaku or Source/Fact
relations.

## 4. Preflight SQL

`scripts/migration_safety/sql/niigata_h003_c6_catalog_preflight.sql`

```text
statements               15（SELECT 7 / WITH 8）
guard.py check-readonly-sql   SAFE: ok
sha256                   34b9d1e713b08346249dae774144097570cb55234b1b5367e8cd2283df13d901
```

The `-- BEGIN/END niigata_h003_c6_target_state` CTE block is byte-identical in all 8 WITH statements.
It holds the 4 frozen targets only. nsrc-000014 is never in it.

| # | Output | Purpose |
|---|---|---|
| 1 | availability flags | connection sanity（no identifier printed） |
| 2 | `server_version`, `server_version_num`, `transaction_read_only` | environment |
| 3 | `latest_temples_migration`, `fact_source_citation_migration_applied` | schema position |
| 4 | 17 `*_table_exists` flags | every table later statements read |
| 5 | Production aggregates | Shrine / Source / Deity / History / Citation / SourceFact / Collective / non-empty goriyaku / GoriyakuTag master / tag links / goriyaku assignments / history-theme assignments / canonical anchors / 赤城神社 total |
| 6 | per target: `exact_count`, `same_name_other_address_count`, `same_address_other_name_count` | identity |
| 7 | per exact row: stored kind / lat / lng / `location_present` / goriyaku / kyusei / astro / romaji / sajin / description / element / visit_style_tags / history_theme / place_ref_id + `coordinate_match` / `payload_neutral` / `catalog_neutral` | stored state |
| 8 | per target: Deity / History / SourceFact / Collective / goriyaku tag links / goriyaku assignments / history-theme assignments / canonical anchors / `source_fact_relation_count` | Knowledge & relations |
| 9 | per target: `target_state`, `target_state_reason` | classification |
| 10 | every 赤城神社 row + every row at a target address | diagnostics |
| 11 | rows within ≈220 m of an adopted coordinate that are not an exact target | diagnostics |
| 12 | 赤城-named rows in 新潟県 that are not an exact target | diagnostics |
| 13 | nsrc-000014 summary: `hold_exact_count`, `hold_same_address_other_name_count`, `hold_identity_state`, `in_write_cohort = false` | HOLD diagnostics |
| 14 | rows at the nsrc-000014 address | HOLD diagnostics |
| 15 | `h003_cohort_state_class_candidate` + counts + `create_candidate_ids` + `expected_shrine_delta_candidate` | cohort（last statement） |

`source_fact_relation_count` sums Deity-Source, History-Source, FactSourceCitation, EvidenceLink,
SourceFact-Source and Collective-Source rows reachable from the exact target row. All of these
hang off Deity / History / SourceFact / Collective, so they can only exist for a target if those
parents exist. They are counted anyway so the output shows it.

`location` is reported as presence only. Its column type is PostGIS geometry in Production but
jsonb in the nogis test DB, so a type-agnostic `IS NOT NULL` is the only portable check.

## 5. Classification contract

### 5.1 Per target

| Order | Condition | `target_state` | `target_state_reason` |
|---|---|---|---|
| 1 | `exact_count > 1` | CONFLICT | DUPLICATE_EXACT_IDENTITY |
| 2 | `same_address_other_name_count > 0`（whether or not the target exists） | CONFLICT | SAME_ADDRESS_OTHER_NAME |
| 3 | `exact_count = 0` | ABSENT | NONE |
| 4 | coordinate outside 1e-12, or NULL | CONFLICT | COORDINATE_MISMATCH |
| 5 | any payload field ≠ expected（importer would overwrite） | CONFLICT | IMPORT_WOULD_OVERWRITE_PAYLOAD |
| 6 | kind / visit_style_tags / history_theme / place_ref ≠ Catalog default | CONFLICT | UNEXPECTED_CATALOG_STATE |
| 7 | any Knowledge / goriyaku / Source-Fact relation > 0 | CONFLICT | UNEXPECTED_KNOWLEDGE_OR_RELATION |
| 8 | otherwise（exactly one fully neutral row） | EXACT_EXISTING | NONE |

EXACT_EXISTING requires every per-row count to be exactly 1 and every relation count to be 0, so
a duplicate falls to CONFLICT even without rule 1. Rule 1 names the reason.

### 5.2 Cohort

```text
any target CONFLICT                  -> CONFLICT              expected_shrine_delta_candidate = NULL
all 4 ABSENT                         -> CLEAN_CREATE          expected_shrine_delta_candidate = 4
all 4 EXACT_EXISTING                 -> ALREADY_MATERIALIZED  expected_shrine_delta_candidate = 0
mix of ABSENT and EXACT_EXISTING     -> PARTIAL_EXISTING      expected_shrine_delta_candidate = absent_count
```

The cohort statement does not reference nsrc-000014.

### 5.3 Diagnostics that do not change the class but must be reviewed before C6 authorization

These are reported read-only. The SQL cannot decide them, so Mother Ship decides from the
listed rows:

| Output | STOP / review rule |
|---|---|
| #11 nearby non-target row | If it is the same real-world shrine under another name or address, treat as CONFLICT（import would create a duplicate）. |
| #12 赤城-named 新潟県 row | Known H002 `赤城社` rows are expected. Any other row needs an explanation. |
| #13 `hold_identity_state = PRESENT` | nsrc-000014 was written without authorization. STOP and investigate. It is never added to the cohort. |
| #7 `location_present = false` on an EXACT_EXISTING row | With USE_GIS=1 the importer would set `location`（overwrite）. Review before treating as ALREADY_MATERIALIZED. |
| #3 / #4 missing table or migration | Later statements fail（ON_ERROR_STOP）. HOLD. Schema change is a separate gate. |

## 6. Repository clean-create maximum delta（NOT the frozen Production delta）

```text
Shrine       +4
Source       +0
Deity        +0
History      +0
Citation     +0
SourceFact   +0
Collective   +0
goriyaku     +0（shrine_nonempty_goriyaku_total unchanged）
goriyaku_tags +0（GoriyakuTag master and tag links unchanged）
```

This is the upper bound when Production is CLEAN_CREATE. It is frozen only after the real
Production preflight output is recorded in this document.

## 7. Finding: the C6 write path must be a target-subset import

Fact（`backend/start.sh`, Visit Style sync section comment）: "Production carries non-Visit-Style
drift (goriyaku / latitude / longitude) that the importer would rewrite in the same transaction."

Consequence: running `import_shrines_seed` with the full 129-row Base Seed against Production
would UPDATE unrelated drifted rows as well as create the four targets. In that case the
"Shrine +4, everything else +0" delta would not hold. The C6 write must import only the four
target rows（the G7 precedent extracts a subset with `*_g7_extract_base_subset.py`）. This PR does
not create that subset tool or any import SQL. That belongs to the C6 write preparation after
the Production preflight.

Also checked: `bootstrap_production_data` and the `start.sh` bootstrap path are opt-in
（`RUN_BOOTSTRAP_ON_START`）, and their step versions are unchanged, so merging #3253 alone does
not import the new rows. Whether anyone ran an import manually is not known. The preflight
measures it（ALREADY_MATERIALIZED / PARTIAL_EXISTING）.

## 8. How to run（Mother Ship, read-only）

```bash
scripts/migration_safety/readonly_query.sh \
  ~/.config/kami-musubi/production-db.env DATABASE_URL \
  scripts/migration_safety/sql/niigata_h003_c6_catalog_preflight.sql
```

Never paste the credential into chat. Record the full output of statements 1–15 in §11.

Known gap（pre-existing, `scripts/migration_safety/README.md` "Known gaps"）: on a GNU coreutils
host, `readonly_query.sh`'s `stat -f` permission check reports a false `BLOCKED` before
connecting. Reproduced here with a local test credential. It fails closed and does not affect
macOS/BSD. Not changed in this PR.

## 9. Verification performed（disposable / local only）

### 9.1 Regression

`backend/temples/tests/test_niigata_h003_c6_catalog_preflight_sql.py`（36 tests, committed SQL
unchanged）:

```text
static    guard is_readonly_sql = True. Every statement SELECT/WITH. No write verb outside comments.
          No connection identifier.
          target block byte-identical ×8, values == C4 frozen == Base Seed rows
          nsrc-000014 absent from the block and from every classification statement
          coordinate tolerance == importer COORDINATE_ABS_TOLERANCE
          payload_neutral covers exactly the importer payload fields（parsed from importer source）
states    empty DB / Base without targets          -> CLEAN_CREATE, delta 4
          Base Seed imported                       -> ALREADY_MATERIALIZED, delta 0
          2 of 4 removed                           -> PARTIAL_EXISTING, create ids 000012,000015, delta 2
          coordinate +1e-13                        -> still ALREADY_MATERIALIZED
conflict  coordinate +1e-9 / NULL, goriyaku set / NULL, kyusei, astro, sajin, description, romaji,
          element, visit_style_tags, history_theme, kind, goriyaku tag link, History Fact, Deity,
          duplicate exact identity, same-address other name（target present / absent）
          -> CONFLICT with the expected reason, delta NULL
importer  for every column mutation, "importer would UPDATE" (subset dry-run) is True exactly
          for COORDINATE_MISMATCH / IMPORT_WOULD_OVERWRITE_PAYLOAD
diag      nsrc-000014 present -> hold PRESENT, cohort unchanged, never a create id
          same-name variant / nearby row -> listed in #11 / #12, cohort unchanged
read-only full file runs inside SET TRANSACTION READ ONLY, row count unchanged
```

SQL mutation sanity（temporary edits, restored, sha256 re-checked）:

| Mutation | Result |
|---|---|
| tolerance 1e-12 → 1e-8 | 2 failed |
| drop `sajin = ''` | 2 failed |
| drop same-address rule | 2 failed |
| drop `visit_style_tags = []` | 1 failed |
| drop Deity/History = 0 | 1 failed |
| drop duplicate state + reason rules | 1 failed（state alone is defense-in-depth, §5.1） |

### 9.2 psql execution（local scratch DB, not Production）

`psql --set ON_ERROR_STOP=1` with `default_transaction_read_only=on` against the local
`h003_rehearsal` DB（Base Seed 129 rows imported in the previous PR's rehearsal）: exit 0, all 15
statements printed, `h003_cohort_state_class_candidate = ALREADY_MATERIALIZED`, hold `ABSENT`,
nearby rows 0. This only shows that the SQL runs under psql and a read-only transaction.
It is not a Production measurement.

### 9.3 Full suite

Local disposable PostgreSQL 16（nogis）, Python 3.11:

```text
backend full suite   6011 passed, 8 skipped（base 5975 + 36 new）
ruff check / format  clean（new test file）
```

## 10. Not changed

```text
Production DB                          NONE
Production import SQL / subset tool    NONE
Candidate Master                       NONE
Recommendation eligibility             NONE
nsrc-000014                            NONE（diagnostics only）
Base Seed / Knowledge Seed             NONE
readonly_query.sh / guard.py           NONE
```

## 11. Production preflight result

```text
NOT EXECUTED
```

To be filled from Mother Ship's real read-only output（statements 1–15）. Only then:
production state class, frozen pre-state aggregates and the frozen expected delta.

## 12. STOP

```text
C6_READ_ONLY_PREFLIGHT_SQL  = PREPARED
PRODUCTION_PREFLIGHT        = NOT EXECUTED
C6 write authorization      = NOT REQUESTED
STOP                        = TRUE
```
