# Knowledge Batch 9 Target Selection

## Executive Summary

- Audit date: 2026-08-10 (Asia/Tokyo)
- Base: `develop` / `cb15538ab88a9a8cd072776817e3d5589c5af062`
- PR #2350: merged at the base commit
- Canonical `none` candidate universe: 54
- Source screening: A 9 / B 1 / C 43 / D 1
- Recommended Batch 9 size: 5 shrines
- Recommended targets: 宇佐神宮、氷川神社（大宮）、貴船神社、大洗磯前神社、箱根神社
- Alternatives: 寒川神社、大國魂神社、川越氷川神社、赤坂氷川神社、高千穂神社
- Partial repair track: 香取神宮、阿佐ヶ谷神明宮（Batch 9 selection外）
- Final classification: **`BATCH9_TARGET_SELECTION_READY`**
- Production DB writes: **0**
- Batch 9 Data writes: **0**

This document approves only a reproducible target selection. It does not create
or approve a seed, an import, or any Production write.

## 1. Base state and source of truth

`develop` was fast-forwarded to `origin/develop` before this audit. PR #2350 is
present as commit `cb15538a`; the working tree was clean. The merged Batch 8
closure / Batch 9 re-entry audit, the current Knowledge Contract, and the seed
import identity/evidence implementation were read fresh.

The merged audit fixes the current state at complete 44 / partial 2 / none 59
over 105 Production Shrine rows. Excluding three duplicate rows, one QA fixture,
and one unresolved/non-shrine identity leaves exactly 54 canonical `none`
candidates. The two partial shrines are a separate repair category and are not
mixed into this target selection.

## 2. Reproducible selection rule

The following order is mandatory and was applied without numeric-PK selection:

1. Start from the 54 canonical identities in the merged Batch 9 universe.
2. Reject duplicate, QA, unresolved, and ambiguous identities.
3. Require Source class A or B and high evidence feasibility for the top ten.
4. Rank official primary Source coverage above fame or presumed popularity.
5. Prefer candidates where both Deity and History facts can be traced directly
   to inspected Source text and every planned fact can have a Source relation.
6. Use region, thematic breadth, and five-case Runtime QA cost only as
   tie-breakers after evidence and identity safety.
7. If an official/public page cannot be inspected or the identity is uncertain,
   keep the candidate in C/D; do not infer facts and do not silently promote it.

Source classes:

- **A — official**: the shrine's official site directly exposes deity and
  history/lineage material sufficient for fact research.
- **B — reliable public**: a government, cultural-property, tourism-language,
  or prefectural shrine-body source supports the required research, but the
  official shrine package is incomplete or unavailable in this pass.
- **C — further research**: no complete A/B evidence package was directly
  inspected in this bounded screening. C is not a claim that no source exists.
- **D — insufficient**: prior authoritative screening found identity/source
  insufficiency requiring resolution before selection.

## 3. Source screening for all 54 candidates

### A — official (9)

| Candidate | Inspected source | Evidence feasibility |
| --- | --- | --- |
| 宇佐神宮 | [公式・由緒](https://www.usajinguu.com/lineage/) | High;祭神と沿革を同一公式ページで追跡可能 |
| 氷川神社（大宮） | [公式・御由緒](https://musashiichinomiya-hikawa.or.jp/about/index.html) | High; canonical address/name is unique |
| 箱根神社 | [公式・箱根神社](https://hakonejinja.or.jp/hakone/) | High;祭神・創建伝承を公式本文で追跡可能 |
| 大國魂神社 | [公式・由緒と歴史](https://www.ookunitamajinja.or.jp/yuisho/) | High;主祭神と沿革を同一ページで追跡可能 |
| 寒川神社 | [公式・御祭神](https://samukawajinjya.jp/about/main-deities.html) / [御由緒](https://samukawajinjya.jp/about/history.html) | High; fact typeごとの公式ページあり |
| 川越氷川神社 | [公式・神社紹介](https://www.kawagoehikawa.jp/shoukai/) | High;大宮・赤坂とのidentity分離必須だが住所で一意 |
| 貴船神社 | [公式・由緒](https://kifunejinja.jp/sp/history.html) | High;京都市左京区の総本宮として一意 |
| 赤坂氷川神社 | [公式・神社について](https://www.akasakahikawa.or.jp/about/) | High;祭神と沿革を同一ページで追跡可能 |
| 大洗磯前神社 | [公式・御祭神／由緒](https://www.oarai-isosakijinja.net/yuisyo/) | High;祭神と史料由来の創建記事を追跡可能 |

### B — reliable public (1)

| Candidate | Inspected source | Evidence feasibility |
| --- | --- | --- |
| 高千穂神社 | [国土交通省・多言語解説](https://www.mlit.go.jp/tagengo-db/common/001554055.pdf) / [国指定文化財等DB](https://kunishitei.bunka.go.jp/heritage/detail/102/00003883) | High;住所identityと由緒は強いが、祭神粒度はseed前に追加照合する |

### C — further research (43)

浅草神社、榛名神社、越中一宮 高瀬神社、芝大神宮、愛宕神社、根津神社、
富岡八幡宮、大宮八幡宮、水戸東照宮、二荒山神社、住吉神社（博多）、靖國神社、
花園神社、小網神社、鳥越神社、湯島天満宮、白山神社、王子神社、
千住神社、葛西神社、穴守稲荷神社、多摩川浅間神社、
武蔵一宮 氷川女體神社、調神社、鷲宮神社、箭弓稲荷神社、安房神社、
千葉神社、玉前神社、櫻木神社、笠間稲荷神社、宇都宮二荒山神社、
足利織姫神社、古峯神社、冠稲荷神社、赤城神社、鶴嶺八幡宮、
報徳二宮神社、平塚八幡宮、忌宮神社、高良大社、寳登山神社、
枚岡神社。

These candidates remain eligible for a later pass, but are not promoted based
on search snippets, name recognition, or uninspected pages. Same-name and
unique-name-contract rows require address-level reconfirmation at promotion.

### D — insufficient (1)

| Candidate | Reason |
| --- | --- |
| 長太稲荷神社 / 東京都世田谷区上祖師谷1丁目3-10 | The prior authoritative selection audit classified the canonical row as source/identity insufficient. It remains excluded until independent resolution. |

## 4. Top-ten ranking and final five

Scores are ordinal screening aids, not Product Score/Ranking changes. Evidence
and identity are gates; region/product value only break ties. Runtime popularity,
detail-view counts, recommendation exposure, favorites, and visits were not
available as safe read-only candidate metrics and are recorded as
`NOT_AVAILABLE`, not estimated.

| Rank | Candidate | Source | Evidence | Identity | Region / product value | Decision |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | 宇佐神宮 | A | High | Safe | Kyushu; major Hachiman lineage | Final 5 |
| 2 | 氷川神社（大宮） | A | High | Safe by exact name+address | Saitama; distinguishes Hikawa family | Final 5 |
| 3 | 貴船神社 | A | High | Safe by Kyoto address | Kansai; improves regional breadth | Final 5 |
| 4 | 大洗磯前神社 | A | High | Safe | Ibaraki; official historical citation | Final 5 |
| 5 | 箱根神社 | A | High | Safe | Kanagawa; strong official package | Final 5 |
| 6 | 寒川神社 | A | High | Safe | Kanagawa; clean two-page package | Alternate 1 |
| 7 | 大國魂神社 | A | High | Safe | Tokyo; ancient provincial context | Alternate 2 |
| 8 | 川越氷川神社 | A | High | Safe by exact address | Saitama; Hikawa identity QA value | Alternate 3 |
| 9 | 赤坂氷川神社 | A | High | Safe by exact address | Tokyo; Hikawa identity QA value | Alternate 4 |
| 10 | 高千穂神社 | B | High | Safe by exact address | Kyushu; public-source breadth | Alternate 5 |

The final five are all A, high-evidence, canonical identities. They span Oita,
Saitama, Kyoto, Ibaraki, and Kanagawa. This is more regionally balanced than
selecting the first five Kanto-heavy A candidates while preserving evidence as
the primary gate. Alternatives remain ordered and can replace a target only if
the later fact-level review stops that target; replacement is not automatic.

## 5. Evidence and implementation contract for the next phase

For each selected shrine, the seed-authoring phase must freshly inspect the
linked Source and define exact proposed facts. This selection does not authorize
copying snippets into a seed. Each future Deity/History must have:

- a unique natural identity using exact shrine name + canonical address;
- a fact-ready verification status, confidence, and `verified_at`;
- at least one direct, fact-ready Source relation;
- no numeric PK, source-less fact, silent overwrite, or unresolved tradition;
- validate-only, exact dry-run delta, Production-equivalent import/idempotency,
  and Runtime expected-payload review before any Production execution request.

Batch size remains five. Expanding to ten would double Source review, expected
fact/relation review, Runtime QA cases, and discrepancy search space without
additional evidence benefit in this pass.

## 6. Separate partial-repair track

香取神宮 and 阿佐ヶ谷神明宮 remain `partial`. They are not `none`, not members
of the 54-candidate universe, and not selectable in Batch 9 without a distinct
repair contract that examines existing facts and prevents silent overwrite.

## 7. Validation and hard stops

- Candidate count: A 9 + B 1 + C 43 + D 1 = **54**
- Top ten: **10**, all A/B, high evidence, identity-safe
- Final targets: **5**, all A, high evidence, identity-safe
- Alternatives: **5**
- Partial category: **2**, separate
- Existing Knowledge changes: **0**
- Production DB writes: **0**
- Batch 9 Data writes / seed creation / import: **0 / NOT_EXECUTED**
- Score/Ranking, Source UI, PER_FACT_RENDERING changes: **0**
- Recommendation Runtime QA: **NOT_EXECUTED** (write-required flow)

Any later failure in identity, direct evidence, source relation coverage, seed
validation, expected delta, or idempotency must stop the batch without automatic
repair or substitution.

**Final classification: `BATCH9_TARGET_SELECTION_READY`.**
