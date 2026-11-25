# Knowledge Batch 8 Closure / Batch 9 Re-entry Audit

## Executive Summary

- Audit time: 2026-08-10 09:02 UTC
- Base: `develop` / `be4c6a62ec1e0368c9031d63c7f9144a39218780`
- PR #2349: merged as the above commit
- Batch 8 Production record and current Production state: exact match
- Current Knowledge: shrine 46 / Source 65 / Deity 117 / History 91
- Relations: Deity–Source 130 / History–Source 96
- Coverage over all 105 Production Shrine rows: complete 44 / partial 2 / none 59
- Batch 9 canonical candidate universe: 54
- Technical batch-size recommendation: continue with 5 shrines
- Final classification: **`BATCH8_CLOSED_BATCH9_REENTRY_READY`**
- Production DB writes in this audit: **0**
- Batch 9 Data writes: **0**

This classification closes Batch 8 and permits a separate Batch 9 Scope /
Candidate Selection task. It does not approve a Batch 9 target list, seed, or
Production write.

## 1. Source of truth and Batch 8 reconciliation

`develop` was fast-forwarded to `origin/develop`; the working tree was clean.
The merged execution record, Batch 8 scope/re-entry record, canonical Batch 8
seed, Knowledge Contract, Evidence Gate, selector, coverage implementation, API
route, and serializer were read fresh.

The merged record fixes execution at `2026-08-10T08:54:34Z`–`08:54:36Z`, exit
status 0, one atomic import, no retry/corrective write, and no recovery. Actual
deltas were Source +6, Deity +14, History +6, Deity–Source +14, and
History–Source +6. Current Production independently reproduces every resulting
count; there is no record/state conflict or unexpected change.

## 2. Production current state and coverage

All database observations used the existing SELECT-only credential bridge. No
credential value, connection string, or private hostname was printed or
recorded.

| Metric | Before Batch 8 | Recorded after | Fresh actual | Result |
| --- | ---: | ---: | ---: | --- |
| Knowledge shrine | 41 | 46 | 46 | PASS |
| Source | 59 | 65 | 65 | PASS |
| Deity | 103 | 117 | 117 | PASS |
| History | 85 | 91 | 91 | PASS |
| Deity–Source | 116 | 130 | 130 | PASS |
| History–Source | 90 | 96 | 96 | PASS |
| complete | 39 | 44 | 44 | PASS |
| partial | 2 | 2 | 2 | PASS |
| none | 64 | 59 | 59 | PASS |

Production shrine rows remain 105. Coverage was recomputed from the existing
contract: a Fact counts only when its own status is fact-ready, `verified_at`
is present, and at least one related Source is fact-ready. Source-less Deity and
History are both zero.

The three duplicate none rows remain Knowledge-free, the QA fixture remains
Knowledge-free, and the unresolved city record remains Knowledge-free. No
ambiguous identity or duplicate contamination affects the Batch 8 five or the
canonical Batch 9 universe.

## 3. Batch 8 five-shrine verification

Expected values were recalculated from `batch_8_seed.json`.

| Shrine / canonical address | Source | Deity | History | Fact–Source | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| 富士山本宮浅間大社 / 静岡県富士宮市宮町1-1 | 1 | 3 | 2 | 5 | PASS |
| 筑波山神社 / 茨城県つくば市筑波1 | 1 | 2 | 1 | 3 | PASS |
| 氣多大社 / 石川県羽咋市寺家町ク1-1 | 1 | 1 | 1 | 2 | PASS |
| 椿大神社 / 三重県鈴鹿市山本町1871 | 1 | 5 | 1 | 6 | PASS |
| 江島神社 / 神奈川県藤沢市江の島2-3-8 | 2 | 3 | 1 | 4 | PASS |

Each identity is a unique canonical row. All 20 Facts and six Sources are
`source_confirmed` / high confidence with populated Source relations. No Fact
is attached to a duplicate or QA fixture.

## 4. HTTP Runtime and existing-flow regression

The current repository route is `GET /api/shrines/<pk>/`; the known public
backend origin is present in repository metadata. All five GETs returned HTTP
200 with exact identity, expected Deity/History/relation counts, fact-ready
Sources, Evidence Gate output, and no duplicate facts or server exception.

The public Top page returned HTTP 200. Detail responses retained the existing
serializer fields (`id`, `kind`, `name_jp`, `address`, coordinates, `goriyaku`,
`goriyaku_tags`) alongside `deities` and `histories`. Knowledge counts remained
65/117/91 and 130/96 after all GETs, confirming no write.

Recommendation runtime was not invoked. The current concierge Recommendation
route is POST and its implementation saves thread/recommendation-observability
records. Classification: **`RECOMMENDATION_RUNTIME_WRITE_REQUIRED`**.

## 5. Batch 9 candidate universe

The fresh none set has 59 Production rows. Applying the established exclusions
produces 54 canonical candidates:

- 3 duplicate rows excluded: 給田六所神社、長太稲荷神社、富岡八幡宮
- 1 QA fixture excluded: テスト確認神社 20260611
- 1 unresolved/non-shrine identity excluded: 広島市
- 2 partial shrines remain a separate repair category: 香取神宮、阿佐ヶ谷神明宮
- all 44 complete shrines and the two partial shrines are outside the none pool

| # | Canonical candidate identity | Status / duplicate note |
| ---: | --- | --- |
| 1 | 宇佐神宮 / 大分県宇佐市南宇佐2859 | NONE / unique |
| 2 | 氷川神社（大宮） / 埼玉県さいたま市大宮区高鼻町1-407 | NONE / unique |
| 3 | 箱根神社 / 神奈川県足柄下郡箱根町元箱根80-1 | NONE / unique |
| 4 | 長太稲荷神社 / 東京都世田谷区上祖師谷1丁目3-10 | NONE / canonical; duplicate excluded |
| 5 | 浅草神社 / 東京都台東区浅草2-3-1 | NONE / unique |
| 6 | 大國魂神社 / 東京都府中市宮町3-1 | NONE / unique |
| 7 | 寒川神社 / 神奈川県高座郡寒川町宮山3916 | NONE / unique |
| 8 | 榛名神社 / 群馬県高崎市榛名山町849 | NONE / unique |
| 9 | 越中一宮 高瀬神社 / 富山県南砺市高瀬291 | NONE / unique |
| 10 | 川越氷川神社 / 埼玉県川越市宮下町2-11-3 | NONE / unique |
| 11 | 高千穂神社 / 宮崎県西臼杵郡高千穂町三田井1037 | NONE / unique |
| 12 | 芝大神宮 / 東京都港区芝大門1-12-7 | NONE / unique |
| 13 | 愛宕神社 / 東京都港区愛宕1-5-3 | NONE / unique |
| 14 | 根津神社 / 東京都文京区根津1-28-9 | NONE / unique |
| 15 | 富岡八幡宮 / 東京都江東区富岡1-20-3 | NONE / canonical; duplicate excluded |
| 16 | 大宮八幡宮 / 東京都杉並区大宮2-3-1 | NONE / unique |
| 17 | 水戸東照宮 / 茨城県水戸市宮町2-5-13 | NONE / unique |
| 18 | 二荒山神社 / 栃木県日光市山内2307 | NONE / unique-name contract |
| 19 | 貴船神社 / 京都府京都市左京区鞍馬貴船町180 | NONE / unique |
| 20 | 住吉神社（博多） / 福岡県福岡市博多区住吉3-1-51 | NONE / unique-name contract |
| 21 | 靖國神社 / 東京都千代田区九段北3-1-1 | NONE / unique |
| 22 | 赤坂氷川神社 / 東京都港区赤坂6-10-12 | NONE / unique |
| 23 | 花園神社 / 東京都新宿区新宿5-17-3 | NONE / unique |
| 24 | 小網神社 / 東京都中央区日本橋小網町16-23 | NONE / unique |
| 25 | 鳥越神社 / 東京都台東区鳥越2-4-1 | NONE / unique |
| 26 | 湯島天満宮 / 東京都文京区湯島3-30-1 | NONE / unique |
| 27 | 白山神社 / 東京都文京区白山5-31-26 | NONE / same-name care required |
| 28 | 王子神社 / 東京都北区王子本町1-1-12 | NONE / unique |
| 29 | 千住神社 / 東京都足立区千住宮元町24-1 | NONE / unique |
| 30 | 葛西神社 / 東京都葛飾区東金町6-10-5 | NONE / unique |
| 31 | 穴守稲荷神社 / 東京都大田区羽田5-2-7 | NONE / unique |
| 32 | 多摩川浅間神社 / 東京都大田区田園調布1-55-12 | NONE / unique |
| 33 | 武蔵一宮 氷川女體神社 / 埼玉県さいたま市緑区宮本2-17-1 | NONE / unique-name contract |
| 34 | 調神社 / 埼玉県さいたま市浦和区岸町3-17-25 | NONE / unique |
| 35 | 鷲宮神社 / 埼玉県久喜市鷲宮1-6-1 | NONE / unique |
| 36 | 箭弓稲荷神社 / 埼玉県東松山市箭弓町2-5-14 | NONE / unique |
| 37 | 安房神社 / 千葉県館山市大神宮589 | NONE / unique |
| 38 | 千葉神社 / 千葉県千葉市中央区院内1-16-1 | NONE / unique |
| 39 | 玉前神社 / 千葉県長生郡一宮町一宮3048 | NONE / unique |
| 40 | 櫻木神社 / 千葉県野田市桜台210 | NONE / unique |
| 41 | 大洗磯前神社 / 茨城県東茨城郡大洗町磯浜町6890 | NONE / unique |
| 42 | 笠間稲荷神社 / 茨城県笠間市笠間1 | NONE / unique |
| 43 | 宇都宮二荒山神社 / 栃木県宇都宮市馬場通り1-1-1 | NONE / unique-name contract |
| 44 | 足利織姫神社 / 栃木県足利市西宮町3889 | NONE / unique |
| 45 | 古峯神社 / 栃木県鹿沼市草久3027 | NONE / unique |
| 46 | 冠稲荷神社 / 群馬県太田市細谷町1 | NONE / unique |
| 47 | 赤城神社 / 群馬県前橋市富士見町赤城山4-2 | NONE / same-name care required |
| 48 | 鶴嶺八幡宮 / 神奈川県茅ヶ崎市浜之郷462 | NONE / unique |
| 49 | 報徳二宮神社 / 神奈川県小田原市城内8-10 | NONE / unique |
| 50 | 平塚八幡宮 / 神奈川県平塚市浅間町1-6 | NONE / unique |
| 51 | 忌宮神社 / 山口県下関市長府宮の内町1-18 | NONE / unique |
| 52 | 高良大社 / 福岡県久留米市御井町1 | NONE / unique |
| 53 | 寳登山神社 / 埼玉県秩父郡長瀞町長瀞1828 | NONE / unique |
| 54 | 枚岡神社 / 大阪府東大阪市出雲井町7-16 | NONE / unique |

This is an identity/status universe, not an approved target ranking. Tokyo and
the broader Kanto region remain heavily represented, so region is a valid
tie-breaker after evidence quality, never a substitute for evidence.

## 6. Batch 9 re-entry contract

Batch 8's contracts are reusable without a schema or importer change:

1. Source quality and directly inspected official primary Sources outrank fame,
   usage proxies, or geographic balancing.
2. Every Deity/History must pass the existing Evidence Gate and have at least
   one fact-ready Source relation; source-less facts are forbidden.
3. Natural identity is exact name + address. Numeric PKs are forbidden in the
   seed; ambiguity stops the batch.
4. Duplicate/QA/unresolved rows are excluded before Source research.
5. Existing natural-key records must never be silently overwritten. Any
   unexpected `SKIP_EXISTS` requires field-level conflict review.
6. Production write requires validate-only, exact dry-run, fresh backup,
   Production-equivalent import/idempotency, and a separate Human Execution
   Boundary.

## 7. Batch-size decision input

| Axis | Five shrines | Ten shrines |
| --- | --- | --- |
| Source research | Bounded; five complete packages | Approximately double, with more weak-source tails |
| Evidence verification | Reviewable in one focused pass | Larger cross-source and tradition review burden |
| Seed review | Small deterministic delta | More facts/relations and identity variants |
| Production blast radius | Same proven Batch 8 shape | Roughly double object/relation exposure |
| Runtime QA | Five exact Detail cases | Ten exact Detail cases |
| Recovery reasoning | Simple, matches rehearsed procedure | Larger discrepancy search space |
| Reproducibility | Directly demonstrated by Batch 8 | Feasible but not yet demonstrated at that size |
| Breadth benefit | +5 complete candidates per cycle | Faster nominal coverage gain |

**Technical recommendation: five shrines.** Batch 8 proved that size end to end,
while 54 candidates leave ample room for evidence-first selection. Ten shrines
may be chosen by Mother Ship only if faster breadth justifies approximately
double research, review, runtime QA, and blast radius.

## 8. Remaining limitations and Mother Ship decision

- This task did not perform Web Source research, rank candidates, or create a
  Batch 9 seed.
- Recommendation Runtime QA remains write-required and was not run.
- Importer `SKIP_EXISTS` detects natural-key existence but does not compare all
  persisted fields; unexpected skips remain a mandatory conflict gate.
- Same-name candidates require exact identity review even when current rows are
  individually canonical-preferred.

Mother Ship must decide: (1) five or ten shrines, (2) whether the two partial
shrines remain a separate repair track, and (3) which evidence-ready candidates
enter Source research. No popularity-only selection is authorized.

**Final classification: `BATCH8_CLOSED_BATCH9_REENTRY_READY`.**

- Production DB writes: **0**
- Batch 9 Data writes: **0**
