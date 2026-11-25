# Knowledge Batch 8 Target Selection Contract — Read-only Audit

## Executive Summary

- Audit snapshot: 2026-08-10 08:14:20 UTC
- Base: `develop` / `7fb0eb28e77b6d90102c3666cbfbeee5bfa7b049`
- Production read-only result: 105 shrines; complete 39, partial 2, none 64,
  Knowledge shrine 41
- Partial shrines: 香取神宮 and 阿佐ヶ谷神明宮; both are
  `MISSING_HISTORY`, while their existing Deity facts pass the Evidence Gate
- None 64 identity composition: 59 canonical selection-pool shrines, 3 duplicate
  rows excluded, 1 QA fixture excluded, and 1 unresolved/non-shrine identity
- Source screening: `OFFICIAL_SOURCE_READY` 9,
  `RELIABLE_PUBLIC_SOURCE_READY` 1, `ADDITIONAL_RESEARCH_REQUIRED` 48,
  `IDENTITY_UNRESOLVED` 1, `SOURCE_INSUFFICIENT` 1
- Technical recommendation: use the 5-shrine plan for the first reproducible
  Batch 8 import; treat the partial two as a separate repair gate
- Final classification: **`BATCH8_TARGET_SELECTION_READY`**. This means the
  selection contract and candidate comparison are ready, not that Production
  write is authorized. Mother Ship must choose the plan and issue a separate Go.
- Production Knowledge Data writes: **0**
- Batch 8 Data writes: **0**

## 1. Base state and source of truth

`develop` was fast-forwarded to `origin/develop`. PR #2346 is present as merge
commit `7fb0eb28`; the working tree was clean before this document was created.
The following were read fresh: `docs/knowledge/`,
`docs/audit/knowledge-batch8-scope-reentry.md`,
`docs/audit/knowledge-production-import-final-execution-gate.md`, the current
models, Evidence Gate selectors, QA fixture exclusion, seed resolver/importer,
and canonical Batch 1–7 seed.

Production was queried only through
`scripts/migration_safety/readonly_query.sh`, which validates every SQL statement
against the SELECT-only allow-list before touching the external credential.
There was no `STOP_SOURCE_OF_TRUTH_CONFLICT`: raw Production values match the
expected 105/39/2/64/41. The important refinement is that raw none=64 includes
five rows that must never enter the candidate pool (three duplicates, one QA
fixture, one unresolved city record).

## 2. Current Coverage and identity audit

| Classification | Count | Definition |
| --- | ---: | --- |
| Total Production rows | 105 | Raw `temples_shrine` count |
| Complete | 39 | At least one fact-ready, sourced Deity and History |
| Partial | 2 | Exactly one of those fact-ready layers exists |
| None | 64 | Neither fact-ready layer exists |
| Knowledge shrine | 41 | At least one fact-ready layer exists |

Fact-ready uses the current contract/implementation: `source_confirmed` or
`reviewed`, non-null `verified_at`, and at least one Source relation. The audit
did not invent a new coverage definition.

All 41 Knowledge shrines resolve to the canonical Batch 1–7 seed by exact
`name_jp` + address. None is a QA fixture/test shrine. The known duplicate pair
for 給田六所神社 remains clean: canonical row has Deity 2 / History 4; duplicate
row has zero Knowledge. No `STOP_EXISTING_KNOWLEDGE_IDENTITY_MISMATCH` occurred.

Production numeric PKs were used transiently to inspect duplicate disposition;
they are intentionally absent from candidate identity and future seed contracts.

## 3. Partial Shrine Audit

| Field | 香取神宮 | 阿佐ヶ谷神明宮 |
| --- | --- | --- |
| Canonical identity | 香取神宮 / 千葉県香取市香取1697-1 | 阿佐ヶ谷神明宮 / 東京都杉並区阿佐谷北1-25-5 |
| Current Source | 1 | 2 |
| Current Deity | 1 raw / 1 ready | 3 raw / 3 ready |
| Current History | 0 raw / 0 ready | 0 raw / 0 ready |
| Missing layer | History | History |
| Classification | `MISSING_HISTORY` | `MISSING_HISTORY` |
| Evidence Gate | PASS for all existing Deity facts | PASS for all existing Deity facts |
| Existing source sufficient | NO | NO |
| Additional source required | YES | YES |
| Reason | Existing official Source confirms Deity, but did not substantiate the claimed founding year used in earlier research | Existing sources support Deity; proposed founding accounts have inconsistent bibliography and remain deferred/disputed |
| Uncertainty | A new authoritative Source may substantiate a carefully hedged tradition; not established now | An authoritative primary/public source must resolve or safely represent the conflict; not established now |

Partial status is not caused by hidden/unready History facts: Production has zero
raw History rows for both shrines. Existing facts and Source relations are not
changed in this audit.

## 4. None Shrine Inventory

Source availability is a gate-level screen, not a completed fact sheet. `A`
means a directly attributable official page exposing a Deity/History research
entry was found; `B` means a reliable public body exposes both layers; `C` means
the shrine remains canonical but a complete Source package was not verified in
this audit; `D` and excluded rows cannot be candidates; `E` records a prior
documented insufficient-evidence outcome.

| # | Canonical identity (`name_jp` / address) | Identity | Duplicate | Knowledge | Source / research |
| ---: | --- | --- | --- | --- | --- |
| 1 | 宇佐神宮 / 大分県宇佐市南宇佐2859 | CANONICAL_CONFIRMED | NO | NONE | C / prior official endpoint unreachable; re-research |
| 2 | 氷川神社（大宮） / 埼玉県さいたま市大宮区高鼻町1-407 | CANONICAL_CONFIRMED | NO | NONE | A / official Deity-History entry confirmed |
| 3 | 箱根神社 / 神奈川県足柄下郡箱根町元箱根80-1 | CANONICAL_CONFIRMED | NO | NONE | A / official identity and history entry confirmed |
| 4 | 富士山本宮浅間大社 / 静岡県富士宮市宮町1-1 | CANONICAL_CONFIRMED | NO | NONE | A / official history entry confirmed |
| 5 | 長太稲荷神社 / 東京都世田谷区上祖師谷1丁目3-10 | CANONICAL_CONFIRMED | canonical row; duplicate excluded separately | NONE | E / prior authoritative search insufficient |
| 6 | 浅草神社 / 東京都台東区浅草2-3-1 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 7 | 大國魂神社 / 東京都府中市宮町3-1 | CANONICAL_CONFIRMED | NO | NONE | C / official page not unambiguously verified in this search |
| 8 | 寒川神社 / 神奈川県高座郡寒川町宮山3916 | CANONICAL_CONFIRMED | NO | NONE | A / official Deity and history pages confirmed |
| 9 | 榛名神社 / 群馬県高崎市榛名山町849 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 10 | 筑波山神社 / 茨城県つくば市筑波1 | CANONICAL_CONFIRMED | NO | NONE | A / official history plus municipal corroboration confirmed |
| 11 | 氣多大社 / 石川県羽咋市寺家町ク1-1 | CANONICAL_CONFIRMED | NO | NONE | A / official Deity-History entry confirmed |
| 12 | 越中一宮 高瀬神社 / 富山県南砺市高瀬291 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 13 | 椿大神社 / 三重県鈴鹿市山本町1871 | CANONICAL_CONFIRMED | NO | NONE | A / official Deity-History entry confirmed |
| 14 | 川越氷川神社 / 埼玉県川越市宮下町2-11-3 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 15 | 高千穂神社 / 宮崎県西臼杵郡高千穂町三田井1037 | CANONICAL_CONFIRMED | NO | NONE | B / MLIT public source confirmed; full fact sheet required |
| 16 | 芝大神宮 / 東京都港区芝大門1-12-7 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 17 | 愛宕神社 / 東京都港区愛宕1-5-3 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 18 | 根津神社 / 東京都文京区根津1-28-9 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 19 | 富岡八幡宮 / 東京都江東区富岡1-20-3 | CANONICAL_CONFIRMED | canonical row; formatted-address duplicate excluded separately | NONE | C / prior official endpoint issue; re-research |
| 20 | 大宮八幡宮 / 東京都杉並区大宮2-3-1 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 21 | 江島神社 / 神奈川県藤沢市江の島2-3-8 | CANONICAL_CONFIRMED | NO | NONE | A / official Deity page and prefectural history confirmed |
| 22 | 水戸東照宮 / 茨城県水戸市宮町2-5-13 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 23 | 二荒山神社 / 栃木県日光市山内2307 | CANONICAL_CONFIRMED | NO | NONE | C / identity must remain distinct from 宇都宮二荒山神社 |
| 24 | 貴船神社 / 京都府京都市左京区鞍馬貴船町180 | CANONICAL_CONFIRMED | NO | NONE | C / public identity confirmed; complete official Deity-History package pending |
| 25 | 住吉神社（博多） / 福岡県福岡市博多区住吉3-1-51 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 26 | 靖國神社 / 東京都千代田区九段北3-1-1 | CANONICAL_CONFIRMED | NO | NONE | C / separate collective-deity contract review required |
| 27 | 赤坂氷川神社 / 東京都港区赤坂6-10-12 | CANONICAL_CONFIRMED | NO | NONE | C / official Source observed, full package not screened |
| 28 | 花園神社 / 東京都新宿区新宿5-17-3 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 29 | 小網神社 / 東京都中央区日本橋小網町16-23 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 30 | 鳥越神社 / 東京都台東区鳥越2-4-1 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 31 | 湯島天満宮 / 東京都文京区湯島3-30-1 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 32 | 白山神社 / 東京都文京区白山5-31-26 | CANONICAL_CONFIRMED | NO | NONE | C / identity/source TO_BE_RESEARCHED |
| 33 | 王子神社 / 東京都北区王子本町1-1-12 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 34 | 千住神社 / 東京都足立区千住宮元町24-1 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 35 | 葛西神社 / 東京都葛飾区東金町6-10-5 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 36 | 穴守稲荷神社 / 東京都大田区羽田5-2-7 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 37 | 多摩川浅間神社 / 東京都大田区田園調布1-55-12 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 38 | 武蔵一宮 氷川女體神社 / 埼玉県さいたま市緑区宮本2-17-1 | CANONICAL_CONFIRMED | NO | NONE | C / distinguish from 大宮氷川神社 |
| 39 | 調神社 / 埼玉県さいたま市浦和区岸町3-17-25 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 40 | 鷲宮神社 / 埼玉県久喜市鷲宮1-6-1 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 41 | 箭弓稲荷神社 / 埼玉県東松山市箭弓町2-5-14 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 42 | 安房神社 / 千葉県館山市大神宮589 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 43 | 千葉神社 / 千葉県千葉市中央区院内1-16-1 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 44 | 玉前神社 / 千葉県長生郡一宮町一宮3048 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 45 | 櫻木神社 / 千葉県野田市桜台210 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 46 | 大洗磯前神社 / 茨城県東茨城郡大洗町磯浜町6890 | CANONICAL_CONFIRMED | NO | NONE | A / official entry plus prefectural Source confirmed |
| 47 | 笠間稲荷神社 / 茨城県笠間市笠間1 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 48 | 宇都宮二荒山神社 / 栃木県宇都宮市馬場通り1-1-1 | CANONICAL_CONFIRMED | NO | NONE | C / distinguish from 日光二荒山神社 |
| 49 | 足利織姫神社 / 栃木県足利市西宮町3889 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 50 | 古峯神社 / 栃木県鹿沼市草久3027 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 51 | 冠稲荷神社 / 群馬県太田市細谷町1 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 52 | 赤城神社 / 群馬県前橋市富士見町赤城山4-2 | CANONICAL_CONFIRMED | NO | NONE | C / same-name identity care required |
| 53 | 鶴嶺八幡宮 / 神奈川県茅ヶ崎市浜之郷462 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 54 | 報徳二宮神社 / 神奈川県小田原市城内8-10 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 55 | 平塚八幡宮 / 神奈川県平塚市浅間町1-6 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 56 | 忌宮神社 / 山口県下関市長府宮の内町1-18 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 57 | 高良大社 / 福岡県久留米市御井町1 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 58 | 寳登山神社 / 埼玉県秩父郡長瀞町長瀞1828 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 59 | 枚岡神社 / 大阪府東大阪市出雲井町7-16 | CANONICAL_CONFIRMED | NO | NONE | C / TO_BE_RESEARCHED |
| 60 | 給田六所神社 / same canonical address | DUPLICATE_EXCLUDED | YES | NONE | excluded; canonical row already complete |
| 61 | 長太稲荷神社 / same canonical address | DUPLICATE_EXCLUDED | YES | NONE | excluded; canonical row is item 5 |
| 62 | 富岡八幡宮 / postal-format variant of canonical address | DUPLICATE_EXCLUDED | YES | NONE | excluded; normalized identity duplicates item 19 |
| 63 | テスト確認神社 20260611 / 東京テスト | QA_FIXTURE_EXCLUDED | N/A | NONE | excluded by shared QA fixture contract |
| 64 | 広島市 / 広島県広島市 | UNRESOLVED | N/A | NONE | D / city record, not a canonical shrine identity |

Summary arithmetic: A 9 + B 1 + C 48 + D 1 + E 1 + duplicate excluded 3 +
QA fixture excluded 1 = 64.

## 5. Source Availability Classification and candidate evidence

The ten screened candidates have the following authoritative research entry
points. Finding a page does not authorize a fact; every proposed Fact still
requires line-level review and a fact sheet.

| Shrine | Class | Confirmed entry point |
| --- | --- | --- |
| 氷川神社（大宮） | A | `https://musashiichinomiya-hikawa.or.jp/about/index.html` |
| 箱根神社 | A | `https://hakonejinja.or.jp/hakone/` |
| 富士山本宮浅間大社 | A | `https://fuji-hongu.or.jp/sengen/history/index.html` |
| 寒川神社 | A | `https://samukawajinjya.jp/about/history.html` and official Deity page |
| 筑波山神社 | A | `https://tsukubasanjinja.jp/history/` |
| 氣多大社 | A | `https://keta.jp/history/` |
| 椿大神社 | A | `https://tsubaki.or.jp/about/` |
| 江島神社 | A | `https://enoshimajinja.or.jp/gosaijin/` plus Kanagawa Jinja Agency |
| 大洗磯前神社 | A | `https://www.oarai-isosakijinja.net/` plus Ibaraki Jinja Agency |
| 高千穂神社 | B | MLIT multilingual public cultural description; exact Fact package pending |

Wikipedia/SEO-only evidence was not used to promote any candidate.

## 6. Selection Criteria

Apply gates in order; later signals cannot rescue an earlier failure.

1. **Identity Safety**: exact `name_jp` + address resolves through the current
   natural identity resolver to one canonical shrine. Ambiguous/not-found,
   duplicate, QA, and non-shrine rows stop.
2. **Evidence Quality**: directly inspected official Source is preferred, then
   Jinja Agency/public/cultural authority, then reliable local history. A Source
   must plausibly support both Deity and History. Evidence Quality outranks all
   recommendation value.
3. **Knowledge Completeness**: target both Deity and History plus Source
   relations. A documented `DO_NOT_ENTER` remains valid when evidence fails.
4. **Reproducibility**: preserve URL/title/publisher/access date, exact identity,
   inclusion/exclusion result, and deterministic gate order in a fact sheet.
5. **Duplicate Safety**: normalized name/address neighbors are reviewed before
   selection; numeric PK is never seed identity.
6. **Secondary value**: among equal A/B candidates, reduce severe regional and
   fact-structure concentration. Popularity/fame alone is not a criterion.

## 7. Recommendation Value and regional distribution

Production read-only results for the none candidates show Favorite=0 and Visit=0
for every candidate, so those fields cannot rank Batch 8. Recommendation
exposure, Detail view, consultation-axis coverage, and trustworthy per-shrine
exposure analytics were not available through the approved read-only contract:
**`NOT_AVAILABLE`**. No proxy or invented value is used.

Current 41 Knowledge shrines are concentrated in Tokyo (10), Kyoto (6), and
Kanagawa (5). The remaining distribution is Saitama/Fukuoka/Ibaraki (2 each),
and one each across Osaka, Okayama, Hiroshima, Hyogo, Tochigi, Kumamoto,
Shimane, Niigata, Aichi, Nara, Chiba, Mie, Nagano, and Gunma. This supports using
region as a tie-breaker, but never at the cost of Source quality.

## 8. Partial handling comparison

| Criterion | Option A: partial 2 + none | Option B: separate repair batch; Batch 8 none-only |
| --- | --- | --- |
| Implementation cost | MEDIUM; two different outcome types | LOW for Batch 8 |
| Source research cost | HIGH; both known difficult/disputed | MEDIUM |
| Coverage improvement | 3–5 new complete plus 0–2 repaired | 5 or 10 new complete targets |
| Verification ease | MEDIUM/LOW | HIGH; uniform zero-to-complete flow |
| Recovery complexity | MEDIUM | LOW |
| Reproducibility | MEDIUM | HIGH |

**Technical recommendation: Option B.** Keep 香取/阿佐ヶ谷 in a separately
bounded repair research gate. Their known difficult evidence should not block or
change a uniform Batch 8 seed acceptance delta. Mother Ship decides.

## 9. Batch-size comparison

| Criterion | Plan A: 5 shrines | Plan B: 10 shrines |
| --- | --- | --- |
| Research cost | MEDIUM | HIGH |
| Verification cost | MEDIUM | HIGH |
| Evidence Gate risk | LOW/MEDIUM | MEDIUM |
| Identity risk | LOW after exact gate | MEDIUM due to more variants |
| Expected Knowledge-shrine delta | up to +5, exact value fixed by fact sheets | up to +10, exact value fixed by fact sheets |
| Operational complexity | LOW | MEDIUM/HIGH |
| Rollback blast radius | LOW | MEDIUM |

Plan A is recommended for the first canonical Batch 8 because it revalidates the
new reproducible import workflow with the smaller review surface.

## 10. Candidate Lists

### Plan A — 5 shrines

| Shrine / address | Source | Expected Source / Deity / History | Reason | Gate confidence | Duplicate risk / uncertainty |
| --- | --- | --- | --- | --- | --- |
| 富士山本宮浅間大社 / 静岡県富士宮市宮町1-1 | A | TO_BE_RESEARCHED / TO_BE_RESEARCHED / TO_BE_RESEARCHED | official history; adds Shizuoka coverage | HIGH | LOW; tradition wording review |
| 筑波山神社 / 茨城県つくば市筑波1 | A | TO_BE_RESEARCHED / TO_BE_RESEARCHED / TO_BE_RESEARCHED | official + municipal evidence | HIGH | LOW; two-peak/deity structure review |
| 氣多大社 / 石川県羽咋市寺家町ク1-1 | A | TO_BE_RESEARCHED / TO_BE_RESEARCHED / TO_BE_RESEARCHED | official entry; strengthens Hokuriku | HIGH | LOW; same-name shrines must not cross-contaminate |
| 椿大神社 / 三重県鈴鹿市山本町1871 | A | TO_BE_RESEARCHED / TO_BE_RESEARCHED / TO_BE_RESEARCHED | official multi-deity entry | HIGH | LOW; claims require tradition handling |
| 江島神社 / 神奈川県藤沢市江の島2-3-8 | A | TO_BE_RESEARCHED / TO_BE_RESEARCHED / TO_BE_RESEARCHED | official Deity + agency history; multi-deity variance | HIGH | LOW; three-miya mapping review |

### Plan B — 10 shrines

Plan B contains all Plan A candidates plus:

| Shrine / address | Source | Expected Source / Deity / History | Reason | Gate confidence | Duplicate risk / uncertainty |
| --- | --- | --- | --- | --- | --- |
| 氷川神社（大宮） / 埼玉県さいたま市大宮区高鼻町1-407 | A | TO_BE_RESEARCHED / TO_BE_RESEARCHED / TO_BE_RESEARCHED | official history; canonical exact label | HIGH | MEDIUM; many 氷川 names |
| 箱根神社 / 神奈川県足柄下郡箱根町元箱根80-1 | A | TO_BE_RESEARCHED / TO_BE_RESEARCHED / TO_BE_RESEARCHED | official history and existing 九頭龍 neighbor stress | HIGH | MEDIUM; shared address with 九頭龍新宮 |
| 寒川神社 / 神奈川県高座郡寒川町宮山3916 | A | TO_BE_RESEARCHED / TO_BE_RESEARCHED / TO_BE_RESEARCHED | separate official Deity/history pages | HIGH | LOW; avoid Chiba same-name result |
| 大洗磯前神社 / 茨城県東茨城郡大洗町磯浜町6890 | A | TO_BE_RESEARCHED / TO_BE_RESEARCHED / TO_BE_RESEARCHED | official + prefectural evidence; pairs safely with existing 酒列 | HIGH | LOW; paired-origin claims need careful separation |
| 高千穂神社 / 宮崎県西臼杵郡高千穂町三田井1037 | B | TO_BE_RESEARCHED / TO_BE_RESEARCHED / TO_BE_RESEARCHED | reliable public cultural source; geographic breadth | MEDIUM | MEDIUM; similarly named shrines and collective deity structure |

No expected count is asserted before a reviewed fact sheet. Candidate order is
deterministic: A before B, then identity risk, regional gap, and structure value.

## 11. Knowledge Write Contract

Future write may create only:

- `ShrineKnowledgeSource`
- `ShrineDeity`
- `ShrineHistory`
- Deity–Source and History–Source M2M relations

It may not change `Shrine`, Favorite, Visit, User, Score, Ranking, existing Fact,
or existing Source. Seed identity is the importer’s current natural identity:
exact `name_jp` and address resolved by `resolve_shrine()` with canonical
preference. Numeric Production PK is prohibited.

Stop before write on ambiguous/not-found identity, duplicate contamination,
unknown Source key, Source-less Fact, invalid enum, missing fact-ready
verification date, Evidence Gate failure, or conflict with an existing natural
key. No silent overwrite/update is permitted.

## 12. Verification Contract

Every approved candidate seed must mechanically expose exact:

- `expected_source_delta`
- `expected_deity_delta`
- `expected_history_delta`
- `expected_deity_source_delta`
- `expected_history_source_delta`
- `expected_knowledge_shrine_delta`

Pre-import capture current Source, Deity, History, both relation counts, and
Knowledge-shrine count. Run validate-only, dry-run, isolated atomic import, a
second dry-run/import, Production-equivalent clean import, and only then a
Production read-only dry-run. Acceptance: source-less facts 0, ambiguous identity
0, duplicate contamination 0, unexpected overwrite 0, exact baseline + approved
deltas, and existing 59/103/85/116/90 baseline preserved.

## 13. Idempotency Contract

The current importer resolves Source by its content natural key, Deity by
`(shrine, display_name)`, and History by `(shrine, history_type, title)`. First run plans
`CREATE`; the same seed on the resulting state plans/skips existing records and
creates zero rows. If an existing natural-key record differs from seed content,
the planner reports an error and blocks the whole atomic apply. It does not
auto-update. That conflict is a mandatory STOP and must return to Mother Ship.

## 14. Runtime QA Contract

After an separately authorized Production import, use public GET Shrine Detail
only. Require HTTP 200, exact canonical shrine, expected Deities, Histories and
Sources, Evidence Gate display behavior, zero source-less leakage, and zero
duplicate-neighbor contamination. Sample 2–5 Batch targets covering:

- simple case
- multi-deity case
- multi-history case
- multi-source case

The exact sample is fixed after fact sheets reveal those structures. Also test
one unchanged Batch 1–7 shrine. Recommendation POST remains
`RECOMMENDATION_RUNTIME_WRITE_REQUIRED`, is a separate Gate, and is not executed
by this audit.

## 15. Risks, limitations, and Mother Ship decision

- A/B screening is not a fact sheet; precise fact counts and relation deltas are
  still unknown.
- Analytics cannot distinguish candidates today; Recommendation exposure and
  Detail view are `NOT_AVAILABLE`, while Favorite/Visit are all zero.
- Three duplicate rows demonstrate that raw none=64 must never be used directly
  as the seed candidate pool.
- Plan B raises identity/evidence review surface and operational blast radius.
- Partial repair may yield zero data even after valid research; that is a safe
  evidence outcome.

Mother Ship must decide: Plan A or B; whether to accept Option B partial handling;
the exact frozen target order; whether B-class 高千穂 belongs in the first batch;
and the later exact deltas/Production Go after fact sheets. Until then, STOP
before seed authoring or any Production write.

Final classification: **`BATCH8_TARGET_SELECTION_READY`**.
