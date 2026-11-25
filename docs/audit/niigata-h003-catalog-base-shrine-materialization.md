# NIIGATA-001-H003 — Catalog-only Base Shrine Materialization

## 1. Status

```text
targets                       = nsrc-000011 / nsrc-000012 / nsrc-000013 / nsrc-000015
excluded                      = nsrc-000014（G2 HOLD_POSITION_REVIEW / C5 NOT_AUTHORIZED）

PRODUCT_SURFACE               = CATALOG_ONLY（audit-level; not a runtime field）
BASE_SHRINE_MATERIALIZATION   = IMPLEMENTED / CI_PENDING

Base Seed row count           = 125 -> 129
existing 125-row prefix       = UNCHANGED（sha256 pinned）
target exact identity count   = 1 each
duplicate (name_jp, address)  = 0
nsrc-000014 rows              = 0

Recommendation eligibility    = INELIGIBLE x4（unchanged; fail-closed）
Knowledge Seed                = NOT CREATED
C6 Production Import          = NOT EXECUTED
C7 CATALOG_READY              = NOT EXECUTED
Production write              = NONE
```

- Recorded at: 2026-10-18
- Base: `develop@c1806db`（PR #3252 merge, C5 Catalog Runtime QA）
- Branch: `claude/tender-fermi-9ww09c`

## 2. Authority

- `docs/knowledge/shrine-expansion-gate-contract.md` §11A（C4 / C5 / C6）
- `docs/audit/niigata-h003-g1-identity-duplicate.md`
- `docs/audit/niigata-h003-position-hold-resolution.md`（adopted coordinate）
- `docs/audit/niigata-h003-c4-catalog-evidence.md`（canonical name / address FROZEN）
- `docs/audit/niigata-h003-c5-catalog-runtime-qa.md`（C5 PASS x4）

| candidate_id | canonical name | canonical address | adopted coordinate | C4 | C5 |
|---|---|---|---|---|---|
| nsrc-000011 | 赤城神社 | 新潟県新潟市江南区二本木1丁目7番16号 | 37.841794, 139.118507 | PASS | PASS |
| nsrc-000012 | 赤城神社 | 新潟県長岡市四郎丸2丁目5番33号 | 37.440743, 138.855238 | PASS | PASS |
| nsrc-000013 | 赤城神社 | 新潟県長岡市山屋314番地 | 37.496407, 139.008620 | PASS | PASS |
| nsrc-000014 | 赤城神社 | 新潟県五泉市上杉川1310番地2 | NONE | NOT_AUTHORIZED | NOT_AUTHORIZED |
| nsrc-000015 | 赤城神社 | 新潟県魚沼市湯之谷芋川311番地 | 37.214543, 139.036468 | PASS | PASS |

Name / address / coordinate values were cross-checked to be identical across the C4 evidence,
the G2 position resolution, the C5 QA constants and the G6 nationwide identity manifest tests.

## 3. Materialized Base rows

Appended to `backend/temples/data/shrines_seed_clean.json` at index 125–128, in candidate order.
Row shape follows the nsrc-000009 precedent（`docs/audit/niigata-h002-nsrc-000009-base-shrine-materialization.md`）.

```json
{
  "name_jp": "赤城神社",
  "address": "<canonical address>",
  "latitude": <adopted latitude>,
  "longitude": <adopted longitude>,
  "goriyaku": "",
  "kyusei": null,
  "astro_elements": [],
  "location": { "lat": <adopted latitude>, "lng": <adopted longitude> }
}
```

`139.008620`（nsrc-000013 longitude）is serialized as JSON number `139.00862`; the float value is
identical.

Not added:

- goriyaku_tags / visit_style_tags / history_theme
- Deity / History / Source
- Recommendation fields / derived Knowledge

The only text change inside the existing prefix is the `}` → `},` separator on row 125（JSON
append）. The 125 parsed rows are byte-for-byte identical under canonical serialization:

```text
sha256(json.dumps(rows[:125], ensure_ascii=False, sort_keys=True, separators=(",", ":")))
  before = 1e79d9f992b76ae26c2b862094d4592d3e754a2917c7b239d0e567a56740307b
  after  = 1e79d9f992b76ae26c2b862094d4592d3e754a2917c7b239d0e567a56740307b
```

## 4. Same-name isolation

After this change the Base Seed contains five `赤城神社` rows, all distinct exact identities:

```text
群馬県前橋市富士見町赤城山4-2           != H003（pre-existing, separate shrine）
新潟県新潟市江南区二本木1丁目7番16号    =  nsrc-000011
新潟県長岡市四郎丸2丁目5番33号          =  nsrc-000012
新潟県長岡市山屋314番地                 =  nsrc-000013
新潟県魚沼市湯之谷芋川311番地           =  nsrc-000015
新潟県五泉市上杉川1310番地2             -> NOT_FOUND（nsrc-000014, not materialized）
```

All resolution uses exact `(name_jp, address)`（`knowledge_seed.resolve_shrine`）.

## 5. Changed files

| File | Change |
|---|---|
| `backend/temples/data/shrines_seed_clean.json` | +4 rows（125 → 129） |
| `backend/temples/tests/test_niigata_h003_catalog_base_shrine_seed.py` | new regression（23 tests） |
| `backend/temples/tests/test_niigata_h003_c5_catalog_runtime_qa.py` | targets are now resolved from the imported Base Seed by exact identity（and coordinate-asserted）instead of `Shrine.objects.create()`, which would collide with the seeded rows |
| `backend/temples/tests/test_import_shrines_seed_command.py` | visit-style repair test counts managed rows by exact `(name_jp, address)` instead of `name_jp__in`（see §7） |
| this audit | — |

### 5.1 New regression coverage

```text
exact identity once                      x4
exact frozen row values                  x4
neutral goriyaku / kyusei / astro_elements, no inferred keys  x4
rows[125:129] == expected（candidate order）
rows[:125] sha256 unchanged
later appends keep targets once
nsrc-000014 absent
no duplicate (name_jp, address)
赤城神社 addresses == {群馬 + 4 targets}, distinct
import: created=129 → dry-run skipped=129 → re-apply skipped=129, rows unchanged
imported targets: no Deity / History / goriyaku / goriyaku_tags / history_theme / visit_style_tags
resolve_shrine: each target → own row; 群馬 → not a target; nsrc-000014 → NOT_FOUND
verify_recommendation_eligibility: INELIGIBLE x4 + UNRESOLVED（nsrc-000014）, usable_fact_count=0
partition_recommendation_eligible_shrines(targets): eligible=[], ineligible=4
```

### 5.2 Fail-closed sanity（temporary seed mutation, restored afterwards）

| Mutation | New regression result |
|---|---|
| rows[0] address altered（prefix drift） | 1 failed |
| nsrc-000013 latitude drift | 4 failed |
| nsrc-000012 row duplicated | 6 failed |
| nsrc-000014 row appended | 5 failed |
| nsrc-000011 goriyaku set to `開運` | 5 failed |

## 6. Isolated import rehearsal

Scratch PostgreSQL 16 database `h003_rehearsal`（local, disposable; nogis migrations）. Not
Production, not the pytest test DB. Real management commands:

```text
pre  Shrine total = 0, 赤城神社 = 0

import_shrines_seed --skip-goriyaku-tags            done created=129 updated=0 skipped=0 total_seed=129
import_shrines_seed --skip-goriyaku-tags --dry-run  done created=0 updated=0 skipped=129 total_seed=129
import_shrines_seed --skip-goriyaku-tags            done created=0 updated=0 skipped=129 total_seed=129

post Shrine total = 129
```

Imported `赤城神社` rows（address / lat / lng / goriyaku / goriyaku_tags / visit_style_tags /
history_theme / Deity / History）:

```text
群馬県前橋市富士見町赤城山4-2          36.5601   139.1936   '縁結び・開運・心願成就' 0 ['nature','classic'] '' 0 0
新潟県新潟市江南区二本木1丁目7番16号   37.841794 139.118507 ''                       0 []                  '' 0 0
新潟県長岡市四郎丸2丁目5番33号         37.440743 138.855238 ''                       0 []                  '' 0 0
新潟県長岡市山屋314番地                37.496407 139.00862  ''                       0 []                  '' 0 0
新潟県魚沼市湯之谷芋川311番地          37.214543 139.036468 ''                       0 []                  '' 0 0
```

`verify_recommendation_eligibility --handoff NIIGATA-001-H003`:

```text
赤城神社 / 新潟県新潟市江南区二本木1丁目7番16号  INELIGIBLE  usable_deity=0 usable_history=0
赤城神社 / 新潟県長岡市四郎丸2丁目5番33号        INELIGIBLE  usable_deity=0 usable_history=0
赤城神社 / 新潟県長岡市山屋314番地               INELIGIBLE  usable_deity=0 usable_history=0
赤城神社 / 新潟県五泉市上杉川1310番地2           UNRESOLVED
赤城神社 / 新潟県魚沼市湯之谷芋川311番地         INELIGIBLE  usable_deity=0 usable_history=0
ELIGIBLE = 0 / INELIGIBLE = 4 / UNRESOLVED = 1
```

（The verifier's UNRESOLVED note says "not found in Production Shrine table"; that is its fixed
wording. The database queried was the scratch rehearsal DB.）

`scripts/migration_safety/niigata_h003_c5_catalog_runtime_qa.py` against the same DB（READ ONLY）:

```text
nsrc-000011 / 000012 / 000013 / 000015  C5_STATUS=PASS
H003_C5_CATALOG_RUNTIME_QA=PASS
TRANSACTION_MODE=READ_ONLY
post Shrine total = 129（no write）
```

## 7. Finding: name-based count in the visit-style repair test

`test_repair_only_visit_style_backfill_is_idempotent_against_canonical_seed` counted
`Shrine.objects.filter(name_jp__in=managed_names)` after `backfill_goriyaku_tags --with-visit-style`.
The four new rows share the name `赤城神社` with the pre-existing managed 群馬 row, so the count
became 107 vs expected 103.

Cause（fact, from code）: `infer_visit_style_tags()` is a keyword heuristic over
name / goriyaku / sajin / description / address, applied to **every** Shrine whose
`visit_style_tags` is empty. It does not copy tags by name. The extra 4 were the new rows being
inferred from their own text, which the name filter mistook for managed rows.

Fix: count by exact `(name_jp, address)` identity. Assertion strength is unchanged（the set of
managed identities with tags must equal the managed set）.

Production relevance: `bootstrap_production_data` runs `backfill_goriyaku_tags --force` **without**
`--with-visit-style`（repair-only, see the step comment）. On that path the four rows keep
`visit_style_tags = []`. If the repair-only flag were ever run manually, these rows（like the
already-materialized nsrc-000006 / 000007 / 000009 rows）would receive heuristic visit-style tags.
`visit_style_tags` is not an input to Shared Recommendation Eligibility, so this would not make
them Recommendation-eligible, but it would be non-evidence-backed metadata on Catalog-only rows.
Not changed in this PR.

## 8. Execution results

Local disposable PostgreSQL 16（nogis）, Python 3.11.

```text
baseline develop@c1806db   full suite  5952 passed, 8 skipped
this branch                full suite  5975 passed, 8 skipped（+23 new）
ruff check（changed tests）            clean
```

## 9. Not changed

```text
nsrc-000014                            NONE（G2 HOLD_POSITION_REVIEW preserved）
Knowledge Seed                         NONE
ShrineDeity / ShrineHistory            NONE
goriyaku_tags / history_theme          NONE
Recommendation mappings                NONE
Ranking / scoring                      NONE
Recommendation Eligibility rule        NONE
Candidate Master / schema              NONE
Production DB                          NONE
```

## 10. Limitations

- The rehearsal DB contains no Knowledge for any Shrine, so its INELIGIBLE result is not by itself
  proof that the Recommendation paths are live. The positive control（an eligible non-H003 Shrine
  that does participate）remains in the C5 pytest suite, which now runs on the seeded rows.
- Production pre-state（row count, possible pre-existing same-address rows）was not inspected.
  The C6 expected delta must be derived from a Production read-only preflight, not from this
  rehearsal.

## 11. STOP

```text
H003 Catalog Base Seed materialization  = IMPLEMENTED（PR）
C6 Catalog Production Import            = NOT EXECUTED（requires Mother Ship authorization）
C7 CATALOG_READY                        = NOT EXECUTED
STOP                                    = TRUE
```
