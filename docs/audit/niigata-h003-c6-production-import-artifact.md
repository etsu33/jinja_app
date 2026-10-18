# NIIGATA-001-H003 — C6 Catalog target-only Production Import Artifact

## Final classification（C6 CLOSED / PASS）

```text
write cohort                 = nsrc-000011 / nsrc-000012 / nsrc-000013 / nsrc-000015
excluded                     = nsrc-000014（G2 HOLD_POSITION_REVIEW / NOT_IN_WRITE_COHORT）

FRESH_PRODUCTION_BACKUP      = PASS
ISOLATED_RESTORE             = PASS（PostgreSQL 17.10）
RESTORE_FINGERPRINT          = MATCH
RESTORE_PRE_BASE_GUARD       = PASS
PRODUCTION_WRITE_AUTHORIZED  = YES（Mother Ship）
Production write             = COMPLETED（target-only 4-row subset）
import result                = created=4 updated=0 skipped=0 total_seed=4
POST_BASE_VERIFICATION       = PASS（h003_c6_post_base_verification_pass = 1）
IDEMPOTENCY                  = PASS（created=0 updated=0 skipped=4 total_seed=4）
PROCEDURE_DEVIATION          = PRE_WRITE_DRY_RUN_SKIPPED（§12）

C6                           = CLOSED / PASS
C7 CATALOG_READY             = CLOSED（docs/audit/niigata-h003-c7-catalog-ready.md）
```

§11–§16 record Mother Ship's Production execution evidence. This repository change made no
Production connection, backup, restore or write. §1–§10 below are the PR #3255 preparation record
and are kept unchanged as history.

## 1. Status at PR #3255（preparation; historical record）

```text
write cohort                 = nsrc-000011 / nsrc-000012 / nsrc-000013 / nsrc-000015
excluded                     = nsrc-000014（G2 HOLD_POSITION_REVIEW / ABSENT / NOT_IN_WRITE_COHORT）

PRODUCTION_STATE_CLASS       = CLEAN_CREATE（Mother Ship read-only measurement）
EXPECTED_PRODUCTION_DELTA    = FROZEN（§3）
C6 import artifact           = PREPARED（this PR）

BACKUP_RESTORE_READINESS     = NOT EXECUTED
PRODUCTION_WRITE_AUTHORIZED  = NOT GRANTED
Production write             = NOT EXECUTED
C6                           = NOT PASS（not executed）
C7 CATALOG_READY             = NOT EXECUTED
```

- Recorded at: 2026-10-18
- Base: `develop@91e6682a72e1eecaafb5aa7d601f7b1a14cab76b`（PR #3254 merge, C6 preflight SQL）
- Branch: `feature/niigata-h003-c6-target-only-import`

## 2. Production pre-state（Mother Ship read-only execution only）

The values below come **only** from Mother Ship's read-only execution of
`scripts/migration_safety/sql/niigata_h003_c6_catalog_preflight.sql` on Production through
`readonly_query.sh`. This repository change made no Production connection. Nothing here is
inferred from the repository Base Seed or from a disposable DB.

```text
PRODUCTION_STATE_CLASS = CLEAN_CREATE

shrine_total                    = 125
source_total                    = 145
deity_total                     = 295
history_total                   = 236
source_fact_total               = 34
collective_total                = 6
citation_total                  = 2
shrine_nonempty_goriyaku_total  = 116
goriyaku_tag_master_total       = 39
goriyaku_tag_link_total         = 366
goriyaku_assignment_total       = 0
history_theme_assignment_total  = 0
canonical_anchor_total          = 0

nsrc-000011 = ABSENT
nsrc-000012 = ABSENT
nsrc-000013 = ABSENT
nsrc-000015 = ABSENT
conflict_count = 0

nsrc-000014 = ABSENT / NOT_IN_WRITE_COHORT
```

All 13 aggregates are the full measured Production pre-state from preflight statement 5, and all 13
are frozen in `niigata_h003_c6_frozen_pre_state`（identical in both guard files）.

Correction: the first revision of this PR froze only the first six aggregates and wrongly said
the remaining seven had not been supplied. Mother Ship had measured them. They are now frozen.
Unrelated Citation / non-empty goriyaku / GoriyakuTag master / tag link / goriyaku assignment /
history-theme assignment / canonical anchor drift during the C6 window therefore **fails closed**
in both the pre-Base guard and the post-Base verification. It is no longer checked only at
target level.

## 3. Frozen expected Production delta

```text
Shrine                     +4   (125 -> 129)
Source                     +0   (145)
Deity                      +0   (295)
History                    +0   (236)
SourceFact                 +0   (34)
Collective                 +0   (6)
Citation                   +0   (2)
goriyaku (non-empty rows)  +0   (116, the four rows carry goriyaku = '')
GoriyakuTag master         +0   (39)
goriyaku tag links         +0   (366, 0 tag links on the four rows)
goriyaku assignments       +0   (0)
history-theme assignments  +0   (0)
canonical anchors          +0   (0)
```

## 4. Target-only import requirement

```text
full 129-row Base Seed Production import = PROHIBITED
target-only 4-row subset import          = the only permitted C6 write path
```

Reason（fact, `backend/start.sh` Visit Style sync comment, recorded in the C6 preflight audit §7）:
Production carries goriyaku / latitude / longitude drift that `import_shrines_seed` would rewrite.
A full-seed run would UPDATE unrelated Production rows. The frozen delta (§3) only holds for
the four-row subset.

The generated subset file must remain **outside the repository** and is never committed. The
extractor refuses any path inside the repository.

## 5. Artifacts

| File | Role |
|---|---|
| `scripts/migration_safety/niigata_h003_c6_extract_base_subset.py` | deterministic 4-row target subset（no DB, no credential, no network） |
| `scripts/migration_safety/sql/niigata_h003_c6_pre_base_guard.sql` | fail-closed pre-write guard（frozen CLEAN_CREATE pre-state） |
| `scripts/migration_safety/sql/niigata_h003_c6_post_base_verification.sql` | fail-closed post-write verification（exact +4） |
| `backend/temples/tests/test_niigata_h003_c6_target_only_import.py` | disposable-DB regression（76 tests） |

No Production import SQL is created. The write is the existing importer on the subset file.

### 5.1 Extractor

```text
targets            exact (name_jp, address), candidate order nsrc-000011 / 012 / 013 / 015
whole-row equality each row == frozen Base Seed row（name, address, lat, lng, goriyaku '',
                   kyusei null, astro_elements [], location {lat, lng}）
BLOCKED            0 or >1 exact matches / any field differs / target set ≠ the frozen four
                   (extra, missing, reordered, empty) / nsrc-000014 requested / nsrc-000014 row
                   in rendered output / output path inside the repository / existing output
                   without --overwrite / non-regular output file
output             4 rows, json.dumps(ensure_ascii=False, indent=2) + "\n"
prints             SUBSET_ROWS=4, candidate_ids=..., SUBSET_SHA256=...
```

Local run（output under the session scratchpad, outside the repository）:

```text
SUBSET_ROWS=4
candidate_ids=nsrc-000011,nsrc-000012,nsrc-000013,nsrc-000015
SUBSET_SHA256=f216eb15f12ce5b5a831a47874a6eb66d66bdb6ed49b2e9c766ae3bc164c5bbd
```

Second run to the same path is `BLOCKED: ... exists`, and a repository path is `BLOCKED: ... inside the
repository`. The SHA256 is a function of the committed Base Seed only. Mother Ship's run must
print the same value.

### 5.2 Pre-Base guard

Single SELECT result `h003_c6_pre_base_guard_pass = 1`, or a division-by-zero error（= FAIL）.
PASS only when:

```text
all 13 aggregates = frozen exactly（§2）
every target target_state = ABSENT（exact count 0, hence no target Knowledge / relations）
no row at any exact target identity
same_address_other_name_count = 0 for every target
nsrc-000014 exact count = 0 and no row at its address
cohort = CLEAN_CREATE（all 4 ABSENT）
```

### 5.3 Post-Base verification

Statement 1 lists the four target states and `location_present`（diagnostics）. The last statement
is `h003_c6_post_base_verification_pass = 1`, or a division-by-zero error（= FAIL）. PASS only when:

```text
Shrine = 125 + 4 = 129
every other frozen aggregate unchanged: Source 145, Deity 295, History 236, SourceFact 34,
  Collective 6, Citation 2, non-empty goriyaku 116, GoriyakuTag master 39, tag links 366,
  goriyaku assignments 0, history-theme assignments 0, canonical anchors 0
every target target_state = EXACT_EXISTING with exact_count = 1:
  coordinate within importer tolerance 1e-12 of the adopted coordinate
  payload: goriyaku '' (not NULL), kyusei NULL, astro_elements [], name_romaji NULL, sajin '',
           description NULL, element NULL
  catalog: kind 'shrine', visit_style_tags [], history_theme '', place_ref_id NULL
  0 Deity / History / SourceFact / Collective / goriyaku tag links / goriyaku assignments /
    history-theme assignments / canonical anchors / Source-Fact relations
same_address_other_name_count = 0 for every target
nsrc-000014 exact count = 0 and no row at its address
```

Any unrelated Shrine +1 makes Shrine ≠ 129 and fails. Any unrelated change to the other 12 frozen
aggregates fails too.

Both guard files reuse the preflight's `niigata_h003_c6_target_state` block **byte-identically**,
and share one `niigata_h003_c6_frozen_pre_state` block. The test checks both. Classification logic
is therefore not re-implemented. It is the same code that produced the CLEAN_CREATE measurement.

## 6. Verification（disposable / local only, not Production）

`backend/temples/tests/test_niigata_h003_c6_target_only_import.py`, 76 tests. Committed SQL is
run unchanged against a disposable DB whose 13 aggregates are made exactly equal to the frozen
Production pre-state. Base Seed minus the four targets, trimmed to 125 Shrine. Knowledge,
Citation and filler goriyaku are attached only to non-target Shrines. The 39 filler GoriyakuTags
and 366 links sit on 10 non-target Shrines:

```text
extractor   exact 4 rows in candidate order == Base Seed == frozen. Deterministic bytes + SHA.
            Full seed never the payload. 群馬 赤城神社 never extracted.
            nsrc-000014 appended / substituted / alone -> BLOCKED. Extra / missing / reordered /
            empty target set -> BLOCKED.
            Missing / duplicated / 8 field mutations -> BLOCKED.
            Repo output path -> BLOCKED. Existing output kept unless --overwrite.
            No DB / credential access in source.
static      guard SQL read-only（guard.py + SELECT/WITH + no write verb + no identifier）.
            Target block == preflight block. Frozen block identical and == measurement.
            nsrc-000014 never a guard target.
pre-Base    exact frozen state PASS（post FAIL, preflight CLEAN_CREATE）.
            Aggregate drift ×15 -> FAIL: Shrine ±1, Source, Deity, History, SourceFact, Collective,
            Citation, non-empty goriyaku ±1, GoriyakuTag master, tag link, goriyaku assignment,
            history-theme assignment, canonical anchor（each +1 on non-target rows only）.
            Unexpected row with unchanged counts: target present / same-address other name /
            nsrc-000014 identity / other name at nsrc-000014 address -> FAIL.
rehearsal   pre PASS -> subset dry-run created=4（no write） -> apply created=4 updated=0 skipped=0
            -> aggregates exactly +4 Shrine -> post PASS, pre FAIL
            -> second import dry-run and apply: created=0 updated=0 skipped=4 -> post still PASS
            -> preflight ALREADY_MATERIALIZED
post-Base   26 drifts -> FAIL: coordinate +1e-9 / NULL, goriyaku set / NULL, kyusei, astro, sajin,
            visit_style_tags, history_theme, kind, goriyaku tag link on the target, target History
            Fact, target Deity（the last three with all 13 aggregates unchanged）, unrelated
            Shrine +1, target missing, nsrc-000014 added, same-address other name, Deity +1
            elsewhere, and the 8 extended aggregate drifts above on non-target rows.
            Coordinate +1e-13（importer round-trip） -> still PASS.
```

Guard mutation sanity（temporary edits, restored and byte-compared）:

| Removed condition | Result |
|---|---|
| pre: History aggregate | 1 failed |
| pre / post: each of Citation, GoriyakuTag master, tag link, goriyaku assignment, history-theme assignment, canonical anchor（12 removals, one at a time） | 1 failed each |
| pre / post: non-empty goriyaku（2 removals） | 2 failed each |
| post: EXACT_EXISTING = 4 | 13 failed |
| post: Shrine delta | 17 failed |
| pre: both hold checks | 2 failed |
| pre: ABSENT = 4 and "no exact row" | 1 failed |
| post: both hold checks | 1 failed |
| post: same-address and EXACT_EXISTING | 14 failed |

Single removals of `hold_exact_count`, pre `ABSENT = 4`, post hold or post same-address survive,
because each is covered by a second condition（defense-in-depth）. Each pair is load-bearing.

Local disposable PostgreSQL 16（nogis）, Python 3.11:

```text
backend full suite                      6087 passed, 8 skipped（base 6011 + 76 new）
scripts/migration_safety/tests/test_guard.py   passed
guard.py check-readonly-sql             SAFE: ok（pre-Base guard, post-Base verification）
ruff check / format（new Python files）  clean
```

## 7. Production procedure（reference only, not authorization）

Mirrors nsrc-000009 G7 §19–§21. Every step requires Mother Ship, and step 3 onward requires
explicit `PRODUCTION_WRITE_AUTHORIZED`.

1. Backup / restore readiness: fresh Production backup with `dump_readonly.sh`（outside the
   repository, client major ≥ Production 17）, isolated restore with `restore_isolated.sh`, then the
   committed pre-Base guard on the restored DB must PASS.
2. Mother Ship grants or withholds `PRODUCTION_WRITE_AUTHORIZED` for exactly the four targets.
3. Generate the subset outside the repository and confirm `SUBSET_SHA256` equals §5.1:
   ```bash
   scripts/migration_safety/niigata_h003_c6_extract_base_subset.py --output <PATH_OUTSIDE_REPO>
   ```
4. Re-run `niigata_h003_c6_pre_base_guard.sql`（read-only）immediately before the write. FAIL = STOP.
5. Dry-run, then apply, the subset only:
   ```bash
   python manage.py import_shrines_seed --source <PATH_OUTSIDE_REPO> --skip-goriyaku-tags --dry-run
   python manage.py import_shrines_seed --source <PATH_OUTSIDE_REPO> --skip-goriyaku-tags
   ```
   Expected both times: `done created=4 updated=0 skipped=0 total_seed=4`. Anything else = STOP.
6. Run `niigata_h003_c6_post_base_verification.sql`（read-only）. FAIL = STOP. Gate contract C6:
   no ad-hoc repair writes.
7. A second dry-run must report `created=0 updated=0 skipped=4`（idempotency, C7 input）.

Never: the full Base Seed as `--source`, nsrc-000014 in any write, Knowledge import, goriyaku tag
sync without `--skip-goriyaku-tags`.

## 8. Limitations

- `location` is not value-checked（PostGIS geometry in Production, jsonb in the nogis test DB）.
  The post-verification's first statement reports `location_present`. With USE_GIS=1 the importer
  sets it on CREATE.
- `shrine_nonempty_goriyaku_total` is a count. An unrelated row whose non-empty goriyaku text
  changes to another non-empty value keeps the count and is not detected. The four target rows
  are checked for exactly `goriyaku = ''`.
- The rehearsal runs on PostgreSQL 16（nogis）. Production is PostgreSQL 17.6（nsrc-000009 §19.1）.

## 9. Not changed

```text
Production DB                      NONE（no connection, no write）
Full Base Seed                     NONE
Knowledge Seed / Knowledge         NONE
Recommendation Eligibility         NONE
Candidate Master                   NONE
Product Surface fields             NONE（not created, not inferred）
nsrc-000014                        NONE（excluded, diagnostics only）
```

## 10. STOP at PR #3255（historical record）

```text
C6 import artifact          = PREPARED
BACKUP_RESTORE_READINESS    = NOT EXECUTED
PRODUCTION_WRITE_AUTHORIZED = NOT GRANTED
Production write            = NOT EXECUTED
C6                          = NOT PASS
C7                          = NOT STARTED
STOP                        = TRUE
```

## 11. Backup / restore readiness（Mother Ship）

Executed by Mother Ship after PR #3255 merged. The values are as supplied; this repository change
did not run them.

```text
FRESH_PRODUCTION_BACKUP  = PASS（stored outside the repository）
ISOLATED_RESTORE         = PASS
restore server           = PostgreSQL 17.10
RESTORE_FINGERPRINT      = MATCH
RESTORE_PRE_BASE_GUARD   = PASS（committed niigata_h003_c6_pre_base_guard.sql on the restored DB）

BACKUP_RESTORE_READINESS = PASS
```

## 12. Production write authorization and procedure deviation

```text
PRODUCTION_WRITE_AUTHORIZED = YES（Mother Ship）

authorized target =
  nsrc-000011  赤城神社  新潟県新潟市江南区二本木1丁目7番16号
  nsrc-000012  赤城神社  新潟県長岡市四郎丸2丁目5番33号
  nsrc-000013  赤城神社  新潟県長岡市山屋314番地
  nsrc-000015  赤城神社  新潟県魚沼市湯之谷芋川311番地

scope           = target-only 4-row Base import + post-Base verification + idempotency dry-run
full Base Seed  = PROHIBITED（not used）
nsrc-000014     = NOT_IN_WRITE_COHORT（not imported）
Knowledge       = NOT AUTHORIZED（not imported）
```

**Procedure deviation（recorded, not hidden）:**

```text
PROCEDURE_DEVIATION = PRE_WRITE_DRY_RUN_SKIPPED
```

§7 step 5 required `import_shrines_seed --dry-run` on the subset before the apply. That pre-write
dry-run was **not executed**. The apply ran directly.

What still held, as supplied by Mother Ship: the actual apply result, the post-Base verification
and the idempotency dry-run all passed（§13–§15）. Because the post-Base verification freezes all
13 aggregates and the exact target state, any unexpected create, update or skip in the apply would
have made it fail. The skipped dry-run therefore left no undetected effect on the verified Production
state. It does mean the expected-output check happened **after** the write instead of before it,
so the apply was not previewed.

Whether the pre-Base guard itself was re-run on Production immediately before the write（§7
step 4）is not stated in the supplied evidence. This record does not claim it.

## 13. Base Shrine Production import

```text
input   = niigata_h003_c6_extract_base_subset.py output（4 rows, outside the repository）
command = import_shrines_seed --source <subset> --skip-goriyaku-tags

done created=4 updated=0 skipped=0 total_seed=4
```

`created=4 updated=0 skipped=0` equals the frozen expectation（§3, §7 step 5）. No existing
Production row was updated.

## 14. Post-Base verification

`niigata_h003_c6_post_base_verification.sql`（read-only）:

```text
nsrc-000011  EXACT_EXISTING  location_present = true
nsrc-000012  EXACT_EXISTING  location_present = true
nsrc-000013  EXACT_EXISTING  location_present = true
nsrc-000015  EXACT_EXISTING  location_present = true

h003_c6_post_base_verification_pass = 1

POST_BASE_VERIFICATION = PASS
```

PASS proves, on Production（§5.3）:

```text
Shrine = 129, the other 12 frozen aggregates unchanged
each target exactly once at its exact (name_jp, address)
adopted coordinate within 1e-12
neutral payload and Catalog defaults
no Deity / History / SourceFact / Collective / goriyaku tag / assignment / anchor / relation
no same-address different-name row
nsrc-000014 absent
```

`location_present = true` for all four closes the §8 `location` limitation for presence. The value
of `location` is still not compared（type differs between PostGIS and nogis）.

## 15. Idempotency

```text
import_shrines_seed --source <subset> --skip-goriyaku-tags --dry-run

done created=0 updated=0 skipped=4 total_seed=4

IDEMPOTENCY = PASS
```

## 16. C6 closure

```text
BACKUP_RESTORE_READINESS     = PASS
PRODUCTION_WRITE_AUTHORIZED  = YES
Production write             = COMPLETED
import result                = created=4 updated=0 skipped=0 total_seed=4
POST_BASE_VERIFICATION       = PASS
IDEMPOTENCY                  = PASS
PROCEDURE_DEVIATION          = PRE_WRITE_DRY_RUN_SKIPPED
C6_BLOCKERS_REMAINING        = NONE

C6 = CLOSED / PASS
```

Next: C7 CATALOG_READY closure — `docs/audit/niigata-h003-c7-catalog-ready.md`.
