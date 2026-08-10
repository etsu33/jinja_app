# Knowledge Batch 8 Seed Preflight — Mother Ship Report

## Executive Summary

- Execution date: 2026-08-10
- Base: `develop` / `deed42907b2f7ab55f1a83c3851944f1cf3d0d14`
- PR #2347 merge commit: present in `develop`
- Final target: five canonical, zero-Knowledge shrines
- Seed delta: Source 6, Deity 14, History 6, Knowledge shrine +5
- Local validate/import/idempotency: PASS
- Production-equivalent aggregate regression: PASS
- Production validate-only/dry-run: PASS; expected CREATE 6/14/6
- Production Knowledge writes: **0**
- Batch 8 Production import executions: **0**
- Mother Ship recommendation: **`GO_RECOMMENDED_PENDING_EXPLICIT_PRODUCTION_WRITE_APPROVAL`**

This report is a technical Go recommendation only. It does not authorize a
Production write. The Production import must remain stopped until Mother Ship
issues an explicit, separate write approval.

## 1. Phase 0 — Base and source of truth

`develop` was fast-forwarded from `origin/develop`. PR #2347 is present, HEAD
was recorded as `deed42907b2f7ab55f1a83c3851944f1cf3d0d14`, and the working tree
was clean before Batch 8 files were created. The canonical Target Selection
Contract was read fresh.

The existing local database was reused as the Production-equivalent baseline
because its read-only coverage snapshot exactly matched the canonical
Production snapshot: total 105, audit target 100, Knowledge 41, complete 39,
scoped Source 59. No destructive restore was necessary.

## 2. Phase 1 — Final target contract

| Shrine | Canonical address | Deity | History | Source |
| --- | --- | ---: | ---: | ---: |
| 富士山本宮浅間大社 | 静岡県富士宮市宮町1-1 | 3 | 2 | 1 |
| 筑波山神社 | 茨城県つくば市筑波1 | 2 | 1 | 1 |
| 氣多大社 | 石川県羽咋市寺家町ク1-1 | 1 | 1 | 1 |
| 椿大神社 | 三重県鈴鹿市山本町1871 | 5 | 1 | 1 |
| 江島神社 | 神奈川県藤沢市江の島2-3-8 | 3 | 1 | 2 |

The two partial shrines, 香取神宮 and 阿佐ヶ谷神明宮, remain excluded and
must pass their separate repair/evidence gate. Every selected identity resolves
exactly once by `name_jp` + address; ambiguous identity count is zero. Numeric
database IDs are not present in the seed.

## 3. Phases 2–4 — Evidence and canonical seed

All six Sources are classified `shrine_official`, with
`verification_status=source_confirmed`, `confidence=high`, access date,
verification timestamp, publisher, title, and URL. Traditional accounts are
expressed as traditions rather than promoted to unqualified historical fact.

| Shrine | Official evidence |
| --- | --- |
| 富士山本宮浅間大社 | `https://fuji-hongu.or.jp/sengen/history/index.html` |
| 筑波山神社 | `https://tsukubasanjinja.jp/history/` |
| 氣多大社 | `https://keta.jp/history/` |
| 椿大神社 | `https://tsubaki.or.jp/about/` |
| 江島神社 | `https://enoshimajinja.or.jp/gosaijin/`, `https://enoshimajinja.or.jp/hetsumiya/` |

Canonical seed:
`backend/temples/data/knowledge_seeds/batch_8_seed.json`

Schema validation passes. The final structure is Source 6, shrine 5, Deity 14,
History 6, Deity–Source relations 14, and History–Source relations 6. Thus every
fact has at least one Source relation and source-less fact count is zero.

## 4. Phases 5–6 — Local import and aggregate regression

Local validate-only and dry-run passed. The first local import created Source 6,
Deity 14, and History 6. A second dry-run produced only `SKIP_EXISTS`: Source 6,
Deity 14, History 6, with zero CREATE actions. This verifies same-seed
idempotency.

The post-import Production-equivalent report is:

| Metric | Baseline | Batch 8 local | Expected delta |
| --- | ---: | ---: | ---: |
| Audit target shrine | 100 | 100 | 0 |
| Knowledge coverage | 41 | 46 | +5 |
| Both Deity and History | 39 | 44 | +5 |
| Scoped Source | 59 | 65 | +6 |
| Fact-ready facts | 188 | 208 | +20 |

All five exact target identities remain single rows. No Knowledge was attached
to duplicate, QA fixture, or unresolved identities; duplicate contamination is
zero. The focused importer, GIS identity, command, and coverage regression suite
passed: **33 passed**.

## 5. Phase 7 — Production read-only preflight

Only `--validate-only` and `--dry-run` were run against Production. Validation
passed and the deterministic plan is:

- CREATE Source: 6
- CREATE Deity: 14
- CREATE History: 6
- SKIP/ERROR: 0

Neither command wrote to Production. The apply/import command was not run.

One importer limitation is recorded explicitly: existence planning identifies
natural-key collisions as `SKIP_EXISTS` but does not compare all persisted field
values for semantic drift. This Batch 8 Production plan has no collision because
all proposed records are CREATE, and same-seed local idempotency passed. Any
future plan containing unexpected `SKIP_EXISTS` must stop for a field-level
conflict audit.

## 6. Phase 8 — Runtime QA contract after an authorized import

| QA case | Shrine | Expected Detail payload |
| --- | --- | --- |
| Simple | 氣多大社 | Deity 1, History 1, Source 1 |
| Multi-deity | 椿大神社 | Deity 5, History 1, Source 1 |
| Multi-history | 富士山本宮浅間大社 | Deity 3, History 2, Source 1 |
| Multi-source | 江島神社 | Deity 3, History 1, Source 2 |

For each case, Shrine Detail must return HTTP 200, exact canonical identity,
the counts above, the expected official Source titles/URLs, and no duplicate
facts. Runtime QA is defined here but was not executed against Production,
because doing so before import cannot validate the future payload.

## 7. Phase 9 — Mother Ship Go/No-Go

**Technical decision: GO recommended, pending explicit Production write
approval.** Identity, evidence, traceability, schema, local import, idempotency,
aggregate regression, and Production read-only planning gates pass with the
expected 6/14/6 create delta. The execution boundary remains closed: no
Production Knowledge write, Batch 8 import, Score/Ranking change, Source UI, or
`PER_FACT_RENDERING` work was performed.
