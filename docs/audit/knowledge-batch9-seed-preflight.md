# Knowledge Batch 9 Seed Preflight — Mother Ship Report

## Executive Summary

- Execution date: 2026-08-10
- Base: `develop` / `41d37e61511a0cc3cde373e8fbf326fa87de0f0d`
- PR #2351: merged at the base commit
- Targets: 宇佐神宮、氷川神社（大宮）、貴船神社、大洗磯前神社、箱根神社
- Seed: Source 6 / Deity 13 / History 5
- Relations: Deity–Source 13 / History–Source 5
- Local validate/import/idempotency: PASS
- Fresh Production-equivalent restore/import/idempotency: PASS
- Production validate-only/dry-run: PASS; CREATE 6/13/5, SKIP/UPDATE/error 0
- Final classification: **`BATCH9_PRODUCTION_IMPORT_READY`**
- Production DB writes: **0**
- Batch 9 Production import: **NOT_EXECUTED**

This classification is a technical preflight result only. It does not authorize
the Production import. A separate explicit human confirmation remains required.

## 1. Base state and contracts

`develop` was synchronized with `origin/develop`. PR #2351 is present as merge
commit `41d37e61`; the working tree was clean before this task. The merged Batch
9 Target Selection, Batch 8 seed and preflight, importer/exporter implementation,
Knowledge Contract, and Evidence Gate were read fresh.

The canonical natural key remains exact `name_jp` + address. Numeric Shrine PKs
are absent from the seed. The importer resolves every target exactly once and
plans the full import before its single atomic write transaction.

## 2. Identity recheck

Fresh Production read-only inspection returned one exact canonical row for each
target. All have `place_ref_id IS NULL`, zero Deity, and zero History; none is a
QA fixture. `validate-only` resolved every target without `AMBIGUOUS` or
`NOT_FOUND`.

| Shrine | Canonical address | Current Knowledge | Identity |
| --- | --- | --- | --- |
| 宇佐神宮 | 大分県宇佐市南宇佐2859 | none | PASS |
| 氷川神社（大宮） | 埼玉県さいたま市大宮区高鼻町1-407 | none | PASS |
| 貴船神社 | 京都府京都市左京区鞍馬貴船町180 | none | PASS |
| 大洗磯前神社 | 茨城県東茨城郡大洗町磯浜町6890 | none | PASS |
| 箱根神社 | 神奈川県足柄下郡箱根町元箱根80-1 | none | PASS |

## 3. Official Sources and Evidence Gate

All six Sources are `shrine_official`, `source_confirmed`, high confidence,
Japanese, and carry access/verification dates. Facts summarize the official
text rather than copying long passages.

| Shrine | Official Source | Seed decision |
| --- | --- | --- |
| 宇佐神宮 | [由緒](https://www.usajinguu.com/lineage/) | Keep the official three-seat祭祀 units; do not duplicate 比売大神 into additional Facts |
| 氷川神社（大宮） | [由緒・歴史](https://musashiichinomiya-hikawa.or.jp/about/index.html) | Three祭神; use the documented 766 record instead of treating the founding tradition as dated fact |
| 貴船神社 | [御祭神](https://kifunejinja.jp/shrine/) / [由緒](https://kifunejinja.jp/sp/history.html) | Include 本宮 and 結社 confirmed祭神; exclude the 奥宮「一説」「伝わる」variants |
| 大洗磯前神社 | [御祭神・由緒](https://www.oarai-isosakijinja.net/yuisyo/) | Two祭神; classify the divine-descent founding account as `tradition` |
| 箱根神社 | [御祭神・由緒](https://hakonejinja.or.jp/hakone/) | Preserve the three deities collectively奉称 as 箱根大神; use the 757社殿建立 event |

Every Deity and History has one directly related fact-ready Source. All enums
are accepted by schema 1.0. Source-less facts, invalid enums, duplicate seed
identities, and ambiguous identities are zero.

## 4. Canonical seed integrity

Canonical seed:
`backend/temples/data/knowledge_seeds/batch_9_seed.json`

- SHA-256: `a4acc276839e8b25937f6a5d7e830365783c7fb787ff5b5d01f29e20dc5116e4`
- Shrine: 5
- Source: 6
- Deity: 13
- History: 5
- Deity–Source relations: 13
- History–Source relations: 5
- Duplicate seed entries: 0
- Source-less facts: 0
- Invalid enum: 0
- Numeric Production PK: 0

Per-target expected payload:

| Shrine | Deity | History | Unique Source | Fact–Source relation |
| --- | ---: | ---: | ---: | ---: |
| 宇佐神宮 | 3 | 1 | 1 | 4 |
| 氷川神社（大宮） | 3 | 1 | 1 | 4 |
| 貴船神社 | 2 | 1 | 2 | 3 |
| 大洗磯前神社 | 2 | 1 | 1 | 3 |
| 箱根神社 | 3 | 1 | 1 | 4 |

## 5. Local validation, import, and regression

The active environment was Python 3.11.13, Django 5.2.16, and psycopg 3.3.4.

1. `--validate-only`: exit 0, no errors.
2. First `--dry-run`: Source CREATE 6 / Deity CREATE 13 / History CREATE 5.
3. One local import: exit 0 with the exact 6/13/5 creates.
4. Relations after import: 13/5; source-less count 0/0.
5. Second `--dry-run`: Source 6 / Deity 13 / History 5 all `SKIP_EXISTS`;
   CREATE/UPDATE/error 0.

Focused schema, importer, duplicate/ambiguity, source-less, Evidence Gate,
coverage, idempotency, and unrelated-Knowledge preservation tests passed:
**51 passed**. The Batch 9-specific regression creates unrelated existing
Knowledge before import and verifies it remains byte-for-byte logically
unchanged after import and idempotency planning.

The first test invocation exposed an environment-only pytest plugin duplication
(`--envfile` registered twice). Tests were rerun with plugin autoload disabled
and the repository-declared Django/env plugins explicitly loaded; no repository
or package change was made for that runner issue.

## 6. Fresh Production-equivalent test

Credential Gate passed without printing a credential, connection string, or
hostname. A fresh read-only Production dump was stored outside the repository:

- roles.sql: 5,426 bytes
- schema.sql: 93,021 bytes
- data.sql: 3,943,166 bytes

It was restored only into the guard-approved disposable local database
`batch9_audit_restore_2351`. Expected pre-existing role/grant warnings were
best-effort and non-fatal; schema and data restore completed successfully.

| Metric | Fresh baseline | After isolated import | Delta | Result |
| --- | ---: | ---: | ---: | --- |
| Shrine | 105 | 105 | 0 | PASS |
| Source | 65 | 71 | +6 | PASS |
| Deity | 117 | 130 | +13 | PASS |
| History | 91 | 96 | +5 | PASS |
| Deity–Source | 130 | 143 | +13 | PASS |
| History–Source | 96 | 101 | +5 | PASS |
| auth user | 1 | 1 | 0 | PASS |
| user profile | 1 | 1 | 0 | PASS |
| favorite | 0 | 0 | 0 | PASS |
| visit | 2 | 2 | 0 | PASS |

All target identities were Knowledge-none before import. Isolated
`validate-only`, first dry-run, one import, aggregate verification, and second
dry-run passed. Source-less Deity/History remained 0/0. The second dry-run was
entirely `SKIP_EXISTS`; no second write was executed.

## 7. Coverage projection

Coverage is computed from the fresh Production-equivalent database, not assumed.
The command excludes the single QA fixture from its 104-row audit denominator.

| Metric | Before | Projected after | Delta |
| --- | ---: | ---: | ---: |
| Knowledge shrine (audit target) | 46 | 51 | +5 |
| Complete / both Deity and History | 44 | 49 | +5 |
| Partial | 2 | 2 | 0 |
| Zero Knowledge (audit target) | 58 | 53 | -5 |

Including the excluded QA fixture in the operational 105-row classification,
the projection is complete 49 / partial 2 / none 54. The five targets each move
from none to complete.

## 8. Production read-only preflight

Fresh Production baseline was Shrine 105 / Source 65 / Deity 117 / History 91.
All five target rows remained Knowledge-none immediately before planning.

- Production `--validate-only`: PASS; errors 0, ambiguous 0, not found 0.
- Production `--dry-run`: Source CREATE 6 / Deity CREATE 13 / History CREATE 5.
- SKIP: 0
- UPDATE: 0 (the importer has no update plan for this seed)
- Errors: 0
- Production write: 0

The apply/import command was not run against Production.

## 9. Runtime expected payload

The repository route remains `GET /api/shrines/<pk>/` through the current
Shrine Detail view/serializer. After a separately authorized import, each case
must return HTTP 200, the exact canonical identity and counts in section 4,
fact-ready Source evidence, and no duplicate or source-less fact. Runtime QA was
not executed now because the payload does not yet exist in Production.

## 10. Remaining risks and Mother Ship decision

- The importer treats an existing natural key as `SKIP_EXISTS` and does not
  compare every persisted field for semantic drift. Any unexpected Production
  skip at execution time is a hard stop.
- 宇佐神宮's 比売大神 is intentionally represented as the official collective
 祭祀 unit. A future product decision to expose its component deities requires a
  separate collective-deity review, not an in-place silent rewrite.
- 貴船神社 contains official text describing alternate 奥宮祭神 traditions.
  Those uncertain variants are intentionally absent from this seed.
- Official web pages are mutable; Sources must be rechecked if the seed hash or
  execution date changes materially before Production approval.

Mother Ship may consider a separate Production Execution Gate using only seed
hash `a4acc276...5116e4`, expected atomic creates 6/13/5 and relation deltas
13/5. Any hash drift, identity drift, SKIP, UPDATE, count mismatch, relation
mismatch, or source-less fact must stop execution without automatic repair.

**Final classification: `BATCH9_PRODUCTION_IMPORT_READY`.**

- Production DB writes: **0**
- Batch 9 Production import: **NOT_EXECUTED**
- Batch 10 / Score/Ranking / Source UI / PER_FACT_RENDERING: **NOT_STARTED**
