# Knowledge Batch 9 Closure Audit / Batch 10 Re-entry Gate

## Executive Summary

- Audit date: 2026-08-10
- Base: `develop` / `00a2eea10e72c587e09176734c021ead73c10da4`
- Batch 9 Production import: PASS; executed exactly once
- Production current state: Knowledge Shrine 51 / Source 70 / Deity 130 /
  History 96 / relations 143・101
- Operational coverage (105 rows): complete 49 / partial 2 / none 54
- Batch 10 canonical candidate universe: 49
- Partial repair category: 2
- Final classification:
  **`BATCH9_CLOSED_BATCH10_REENTRY_READY_WITH_LIMITATIONS`**
- Production DB writes during this closure audit: **0**
- Batch 10 Data writes: **0**

Batch 9 is technically closed. This document is a re-entry contract and
candidate-universe audit only; it does not select Batch 10 targets, research
Sources, create a seed, or authorize a Production write.

## 1. Batch 9 Execution Record reconciliation

The merged repository contained the remediated seed and Source reuse audit, but
no post-execution Batch 9 record. The Production state and public Runtime were
therefore read fresh and reconciled with the captured execution result.

| Item | Actual result |
| --- | --- |
| Execution start / finish | `2026-08-10T10:10:57Z` / `2026-08-10T10:11:00Z` |
| develop SHA | `00a2eea10e72c587e09176734c021ead73c10da4` |
| Seed | `backend/temples/data/knowledge_seeds/batch_9_seed.json` |
| Seed SHA-256 | `8178e49da03ec4d2a1024e3708c2d16c35e549c6c70e3a6aeb439ef156f98be4` |
| Exit status | `0` |
| Transaction | importerの単一`transaction.atomic()` |
| Source | 65 → 70; CREATE 5 / REUSE_EXISTING 1 |
| Deity | 117 → 130; +13 |
| History | 91 → 96; +5 |
| Deity–Source | 130 → 143; +13 |
| History–Source | 96 → 101; +5 |
| Knowledge Shrine | 46 → 51; +5 |
| Coverage | 44/2/59 → 49/2/54 (complete/partial/none) |
| Idempotency dry-run | Source REUSE 6 / Deity SKIP 13 / History SKIP 5 / CREATE 0 |
| Runtime QA | 5/5 HTTP 200 and expected payload PASS |
| Unexpected change | 0 |
| Retry / repair / recovery / restore | NOT_EXECUTED |

The pre-write fresh backup used the remediated no-target-logging contract and
produced non-empty roles/schema/data files outside the repository. The one
approved Production import was not repeated.

## 2. Production current state and Coverage

All observations in this audit used the SELECT-only credential bridge or
public GET requests. No credential, connection string, or private hostname was
printed or recorded.

| Metric | Expected | Fresh actual | Result |
| --- | ---: | ---: | --- |
| Knowledge Shrine | 51 | 51 | PASS |
| Source | 70 | 70 | PASS |
| Deity | 130 | 130 | PASS |
| History | 96 | 96 | PASS |
| Deity–Source | 143 | 143 | PASS |
| History–Source | 101 | 101 | PASS |
| source-less Deity | 0 | 0 | PASS |
| source-less History | 0 | 0 | PASS |

The operational 105-row classification is complete 49, partial 2, none 54.
The shared Governance Coverage implementation excludes one QA fixture, giving
an audit denominator of 104, Knowledge 51, and zero-Knowledge 53. All 51
Knowledge shrines are fact-ready; all 70 scoped Sources are fact-ready.

Ambiguous name groups with no unique canonical row are zero. Facts attached to
noncanonical duplicate rows are zero, and facts attached to QA fixtures are
zero. This confirms no duplicate/QA contamination.

## 3. Batch 9 five-shrine closure

| Shrine / canonical address | Source | Deity | History | Fact–Source | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| 宇佐神宮 / 大分県宇佐市南宇佐2859 | 1 | 3 | 1 | 4 | PASS |
| 氷川神社（大宮） / 埼玉県さいたま市大宮区高鼻町1-407 | 1 | 3 | 1 | 4 | PASS |
| 貴船神社 / 京都府京都市左京区鞍馬貴船町180 | 2 | 2 | 1 | 3 | PASS |
| 大洗磯前神社 / 茨城県東茨城郡大洗町磯浜町6890 | 1 | 2 | 1 | 3 | PASS |
| 箱根神社 / 神奈川県足柄下郡箱根町元箱根80-1 | 1 | 3 | 1 | 4 | PASS |

Each identity is the unique canonical-preferred row. All Facts are
`source_confirmed` / high confidence and have at least one fact-ready Source.

The Hakone official page remains exactly one normalized-URL Source. It now has
four Deity and two History relations across the existing and Batch 9 facts.
The pre-existing 九頭龍神社 新宮 Deity/History relations remain 1/1. No Source
row was duplicated or overwritten.

## 4. Runtime Closure and existing-flow regression

The current public Detail contract is `GET /api/shrines/<pk>/data/`.

| Shrine | HTTP | Deity | History | Unique Source | Fact–Source |
| --- | ---: | ---: | ---: | ---: | ---: |
| 宇佐神宮 | 200 | 3 | 1 | 1 | 4 |
| 氷川神社（大宮） | 200 | 3 | 1 | 1 | 4 |
| 貴船神社 | 200 | 2 | 1 | 2 | 3 |
| 大洗磯前神社 | 200 | 2 | 1 | 1 | 3 |
| 箱根神社 | 200 | 3 | 1 | 1 | 4 |

Every response matched canonical name/address and retained the existing fields
`id`, `kind`, `name_jp`, `address`, coordinates, `goriyaku`, and
`goriyaku_tags` alongside `deities` and `histories`. Source evidence,
verification status, and confidence were populated; source-less payload and
HTTP 500 were zero. The Top page returned HTTP 200. Knowledge counts remained
70/130/96 and 143/101 after all GETs.

Recommendation Runtime was not called. The current flow is POST-based and
creates thread/message/recommendation-observability records. Classification:
**`RECOMMENDATION_RUNTIME_WRITE_REQUIRED`**.

## 5. Batch 10 candidate universe

Production has 54 raw none rows. Applying the established identity and fixture
exclusions removes five rows: three noncanonical duplicate rows, one QA
fixture, and one unresolved/non-shrine record. There are no additional
ambiguous groups. The resulting Batch 10 candidate universe is **49 canonical
identities**. Complete and partial shrines are not candidates.

| # | Canonical candidate identity | Status / duplicate note |
| ---: | --- | --- |
| 1 | 二荒山神社 / 栃木県日光市山内2307 | NONE / unique |
| 2 | 住吉神社（博多） / 福岡県福岡市博多区住吉3-1-51 | NONE / unique |
| 3 | 冠稲荷神社 / 群馬県太田市細谷町1 | NONE / unique |
| 4 | 千住神社 / 東京都足立区千住宮元町24-1 | NONE / unique |
| 5 | 千葉神社 / 千葉県千葉市中央区院内1-16-1 | NONE / unique |
| 6 | 古峯神社 / 栃木県鹿沼市草久3027 | NONE / unique |
| 7 | 報徳二宮神社 / 神奈川県小田原市城内8-10 | NONE / unique |
| 8 | 多摩川浅間神社 / 東京都大田区田園調布1-55-12 | NONE / unique |
| 9 | 大國魂神社 / 東京都府中市宮町3-1 | NONE / unique |
| 10 | 大宮八幡宮 / 東京都杉並区大宮2-3-1 | NONE / unique |
| 11 | 宇都宮二荒山神社 / 栃木県宇都宮市馬場通り1-1-1 | NONE / unique |
| 12 | 安房神社 / 千葉県館山市大神宮589 | NONE / unique |
| 13 | 富岡八幡宮 / 東京都江東区富岡1-20-3 | NONE / canonical; duplicate row excluded |
| 14 | 寒川神社 / 神奈川県高座郡寒川町宮山3916 | NONE / unique |
| 15 | 寳登山神社 / 埼玉県秩父郡長瀞町長瀞1828 | NONE / unique |
| 16 | 小網神社 / 東京都中央区日本橋小網町16-23 | NONE / unique |
| 17 | 川越氷川神社 / 埼玉県川越市宮下町2-11-3 | NONE / unique |
| 18 | 平塚八幡宮 / 神奈川県平塚市浅間町1-6 | NONE / unique |
| 19 | 忌宮神社 / 山口県下関市長府宮の内町1-18 | NONE / unique |
| 20 | 愛宕神社 / 東京都港区愛宕1-5-3 | NONE / unique |
| 21 | 枚岡神社 / 大阪府東大阪市出雲井町7-16 | NONE / unique |
| 22 | 根津神社 / 東京都文京区根津1-28-9 | NONE / unique |
| 23 | 榛名神社 / 群馬県高崎市榛名山町849 | NONE / unique |
| 24 | 櫻木神社 / 千葉県野田市桜台210 | NONE / unique |
| 25 | 武蔵一宮 氷川女體神社 / 埼玉県さいたま市緑区宮本2-17-1 | NONE / unique |
| 26 | 水戸東照宮 / 茨城県水戸市宮町2-5-13 | NONE / unique |
| 27 | 浅草神社 / 東京都台東区浅草2-3-1 | NONE / unique |
| 28 | 湯島天満宮 / 東京都文京区湯島3-30-1 | NONE / unique |
| 29 | 玉前神社 / 千葉県長生郡一宮町一宮3048 | NONE / unique |
| 30 | 王子神社 / 東京都北区王子本町1-1-12 | NONE / unique |
| 31 | 白山神社 / 東京都文京区白山5-31-26 | NONE / same-name care required |
| 32 | 穴守稲荷神社 / 東京都大田区羽田5-2-7 | NONE / unique |
| 33 | 笠間稲荷神社 / 茨城県笠間市笠間1 | NONE / unique |
| 34 | 箭弓稲荷神社 / 埼玉県東松山市箭弓町2-5-14 | NONE / unique |
| 35 | 芝大神宮 / 東京都港区芝大門1-12-7 | NONE / unique |
| 36 | 花園神社 / 東京都新宿区新宿5-17-3 | NONE / unique |
| 37 | 葛西神社 / 東京都葛飾区東金町6-10-5 | NONE / unique |
| 38 | 調神社 / 埼玉県さいたま市浦和区岸町3-17-25 | NONE / unique |
| 39 | 赤坂氷川神社 / 東京都港区赤坂6-10-12 | NONE / unique |
| 40 | 赤城神社 / 群馬県前橋市富士見町赤城山4-2 | NONE / unique |
| 41 | 越中一宮 高瀬神社 / 富山県南砺市高瀬291 | NONE / unique |
| 42 | 足利織姫神社 / 栃木県足利市西宮町3889 | NONE / unique |
| 43 | 長太稲荷神社 / 日本、〒157-0065 東京都世田谷区上祖師谷１丁目３−１０ | NONE / canonical; duplicate row excluded |
| 44 | 靖國神社 / 東京都千代田区九段北3-1-1 | NONE / unique |
| 45 | 高千穂神社 / 宮崎県西臼杵郡高千穂町三田井1037 | NONE / unique |
| 46 | 高良大社 / 福岡県久留米市御井町1 | NONE / unique |
| 47 | 鳥越神社 / 東京都台東区鳥越2-4-1 | NONE / unique |
| 48 | 鶴嶺八幡宮 / 神奈川県茅ヶ崎市浜之郷462 | NONE / unique |
| 49 | 鷲宮神社 / 埼玉県久喜市鷲宮1-6-1 | NONE / unique |

Excluded none rows:

- noncanonical duplicates: 富岡八幡宮、給田六所神社、長太稲荷神社
- QA fixture: テスト確認神社 20260611
- unresolved/non-shrine identity: 広島市

## 6. Partial repair category

| Shrine | Current layer | Missing layer | Evidence | Repair feasibility |
| --- | --- | --- | --- | --- |
| 阿佐ヶ谷神明宮 | Deity 3 / Sources 2 | History | current Deity evidence-ready | History Source research not performed; UNASSESSED |
| 香取神宮 | Deity 1 / Source 1 | History | current Deity evidence-ready | History Source research not performed; UNASSESSED |

Both remain outside the Batch 10 none universe. A later Mother Ship decision may
open a separate repair track; this audit does not mix repair and breadth work.

## 7. Batch 10 re-entry and Source reuse contracts

The Batch 8/9 contract remains reusable without structural change:

1. five-target batch and canonical `name_jp + address` identity;
2. Identity Safety before Source research;
3. official/reliable primary Sources over fame;
4. every Fact must pass Evidence Gate and have a Source relation;
5. canonical versioned seed with no numeric Production PK;
6. schema validation, validate-only, exact Production dry-run;
7. fresh backup and Production-equivalent import/idempotency test;
8. Human Execution Boundary before one atomic Production import;
9. five-target Runtime QA and hard stop.

Source semantic reuse is now a standard preflight contract. URL-backed Sources
use `source_type + normalized URL`; scheme/host case, default port, fragment,
and non-root trailing slash normalization follow the implementation. A unique
compatible row is reused, metadata conflict stops, and multiple matches stop as
ambiguous. Existing relations must be measured before and after. Batch 10
Selection must scan every proposed URL against current Production before seed
approval; a same-URL conflict may not be deferred to the execution gate.

## 8. Batch size analysis

| Dimension | A: 5 shrines | B: 10 shrines |
| --- | --- | --- |
| Research cost | One proven review unit | Approximately double, with more cross-target coordination |
| Evidence review | 5 identity/source bundles | 10 bundles; reviewer fatigue and inconsistency risk increase |
| Source conflict risk | Bounded; Batch 9 conflict was isolated and remediated | More URLs and higher chance of semantic collision in one atomic plan |
| Runtime QA | Five exact payload checks, already operationalized | Ten checks and a larger failure triage surface |
| Production blast radius | +5 complete targets | Up to +10 targets and larger relation delta |
| Recovery decision | Smaller all-or-nothing decision | More facts/sources implicated by one failure |
| Evidence from Batch 8/9 | Two consecutive five-shrine batches passed | No Production execution evidence for ten-shrine batches |

Technical recommendation: **continue with five shrines for Batch 10**. Batch 9
showed that even a five-target batch can surface a cross-batch Source semantic
conflict. The remediation reduces recurrence but does not create a database
uniqueness constraint. A ten-target batch offers faster nominal breadth at the
cost of an unproven review and blast-radius step change. Mother Ship retains the
final size decision.

## 9. Remaining limitations and Mother Ship Decision

- Source availability, official-primary evidence quality, regional balance,
  and same-URL collisions have not yet been researched for the 49 candidates.
- 白山神社 and other broad/common naming patterns require exact address-based
  identity care during selection even though current rows are unique.
- Source semantic URL identity has no database uniqueness constraint; the
  importer detects ambiguity at planning time but cannot prevent external
  concurrent creation.
- Existing Fact `SKIP_EXISTS` does not compare every semantic field.
- Partial History repair feasibility remains unassessed because Source research
  is outside this closure task.

Mother Ship decisions required before Batch 10 Selection:

1. approve five targets (technical recommendation) or expand to ten;
2. keep partial repair as a separate track or prioritize it later;
3. authorize Source research against the 49-candidate universe.

**Final classification:
`BATCH9_CLOSED_BATCH10_REENTRY_READY_WITH_LIMITATIONS`.**

- Production DB writes during closure: **0**
- Batch 10 seed/import/Data writes: **0 / NOT_STARTED**
