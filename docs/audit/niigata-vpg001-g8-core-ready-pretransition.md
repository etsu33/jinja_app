# NIIGATA-001-VPG001 G8 CORE READY PRE_TRANSITION

## Status（PRE_TRANSITION; Condition #8 unresolved）

- Cohort: `nsrc-000021` / `nsrc-000022` / `nsrc-000024` / `nsrc-000025`
- Excluded: `nsrc-000023` 熱串彦神社（G4以降 NOT_AUTHORIZED、本書のscope外）
- Recorded at: `2026-10-20`
- Gate: `G8 CORE READY`（PRE_TRANSITION record only）
- Audit base: `develop@c32a61799c6eb6b1db5c76522e262f9c357c4708`（PR #3283 merge）
- G7 Production Import: `CLOSED / PASS`（PR #3282, `docs/audit/niigata-vpg001-g7-production-closure.md`）
- Candidate Master G7 sync: `MERGED`（PR #3283）
- Production write in this G8 audit: `0`
- Production query executed for this record: `0`（Condition #8 は Mother Ship の実行待ち）

```text
G8_CONDITIONS_01_TO_07                     = PASS
G8_CONDITION_08                            = PENDING_MOTHER_SHIP_MEASUREMENT
G8_CONDITIONS_09_TO_11                     = PASS
G8_CONDITION_12_PRE_TRANSITION             = PASS
G8_CONDITION_12_POST_TRANSITION            = NOT_EXECUTED

COMPLETION_CONTRACT_PRE_TRANSITION         = 11/12 SATISFIED, #8 UNRESOLVED
MOTHER_SHIP_CORE_READY_TRANSITION_DECISION = NOT_RECORDED
CORE_READY_TRANSITION                      = NOT_EXECUTED
G8_STATUS                                  = OPEN
```

本書はG8 Completion Contract #1〜#12 のPRE_TRANSITION evidenceだけを記録する。
CORE_READY transitionは実行しない。Mother Ship判断は未記録であり、Candidate Master / Production DB /
Seed / lifecycle data / GoriyakuTagを変更しない。
Condition #8 は fresh Production read-only 出力が供給されるまで未解決のままとし、
`COMPLETION_CONTRACT_PRE_TRANSITION = 12/12 SATISFIED` は記録しない。

---

## 1. Authority

- `docs/knowledge/shrine-expansion-gate-contract.md` §11
- `docs/audit/shrine-expansion-wave0-data-build-plan.md` CORE READY Completion Contract
- `docs/knowledge/shrine-expansion-candidate-master-contract.md` schema 1.4 Nationwide Source Track Boundary
  （Nationwide Source Track build_batch rule, PR #3284）
- `docs/audit/niigata-vpg001-g7-production-closure.md`
- `backend/temples/data/shrine_expansion_candidate_master.json`
- Precedent: `docs/audit/niigata-h001-g8-core-ready-pretransition.md`（nsrc-000004）、
  `docs/audit/niigata-h002-nsrc-000009-g8-core-ready-pretransition.md`

```text
IMPORTED   != CORE_READY
FACT_READY != CORE_READY
```

---

## 2. Scope

| candidate_id | name_jp | address |
| --- | --- | --- |
| nsrc-000021 | 荒川神社 | 新潟県胎内市桃崎浜187番地 |
| nsrc-000022 | 五十嵐神社 | 新潟県三条市大字飯田2283番地 |
| nsrc-000024 | 秋葉神社 | 新潟県新潟市秋葉区秋葉3丁目8番19号 |
| nsrc-000025 | 天津神社 | 新潟県糸魚川市一の宮1丁目3番34号 |

`nsrc-000023` 熱串彦神社 は同じ VPG001 member だが、G4以降 NOT_AUTHORIZED のため本書の対象外であり、
連動遷移しない。cohortであることを理由に4件を一括でCORE_READYとみなさず、各Conditionは候補ごとに判定する。

---

## 3. Upstream Gate lineage

| Gate | 000021 | 000022 | 000024 | 000025 |
| --- | --- | --- | --- | --- |
| G1 Identity / Duplicate | PASS / SAME_NAME_DIFFERENT_SHRINE | PASS / NEW | PASS / SAME_NAME_DIFFERENT_SHRINE | PASS / SAME_NAME_DIFFERENT_SHRINE |
| G2 Position | CLOSED / PASS | CLOSED / PASS | CLOSED / PASS | CLOSED / PASS |
| G3 Model Fit | NORMAL_MODEL_FIT | NORMAL_MODEL_FIT | NORMAL_MODEL_FIT | CURATION_RELEASE_CANDIDATE |
| G4 Knowledge Fact + Evidence | CLOSED / PASS | CLOSED / PASS | CLOSED / PASS | CLOSED / PASS |
| G5 Shared Recommendation Eligibility | PASS / ELIGIBLE | PASS / ELIGIBLE | PASS / ELIGIBLE | PASS / ELIGIBLE |
| G6 Runtime QA | CLOSED / PASS | CLOSED / PASS | CLOSED / PASS | CLOSED / PASS |
| G7 Production Import | CLOSED / PASS | CLOSED / PASS | CLOSED / PASS | CLOSED / PASS |

G3 の Product Surface は4件とも `RECOMMENDATION`
（`docs/audit/niigata-vpg001-g3-source-knowledge-fit.md`）。

Evidence files:

- G1: `docs/audit/niigata-vpg001-g1-identity-duplicate.md`
- G2: `docs/audit/shrine-position/niigata-vpg001-nsrc-0000XX-position-review.md`
- G3: `docs/audit/niigata-vpg001-g3-source-knowledge-fit.md`
- G4: `docs/audit/niigata-vpg001-nsrc-0000XX-g4-formal-pass.md`
- G5: `docs/audit/niigata-vpg001-nsrc-0000XX-g5-recommendation-eligibility.md`
- G6: `docs/audit/niigata-vpg001-nsrc-0000XX-g6-runtime-qa.md`
- G7: `docs/audit/niigata-vpg001-g7-production-closure.md`

G7 の procedure deviation（`NSRC_000022_PRE_WRITE_VALIDATE_ONLY_NOT_OBSERVED_IN_SUPPLIED_LOG`）は
G7 closure で non-blocking と分類済みであり、本書でも履歴として保持する（書き換えない）。

---

## 4. Evidence source boundary

| 区分 | 内容 |
| --- | --- |
| G7 Production実測 | P1〜P5 cohort guard（5 statement 全 PASS）/ Base・Knowledge idempotency / Production Runtime QA（READ ONLY） |
| G8 fresh Production read-only | Condition #8 GoriyakuTag master current-state — **未実行**（Mother Ship が `readonly_query.sh` で実行予定） |
| repository current state | PR #3283 merge後の Candidate Master |
| G2 / G4 / G5 / G6 | 各 current audit record |

本書作成時に Production query は実行していない。

---

## 5. Completion Contract #1〜#12

### #1 Production Shrine canonical identity

G7 P5 guard（Production, 全 statement = 1）は各 target について exact `(name_jp, address)` の row が
1件、同一住所の row が1件、同名別住所 row が frozen 値（0）であることを確認した。

| candidate_id | target exact | same address | same name other address |
| --- | ---: | ---: | ---: |
| nsrc-000021 | 1 | 1 | 0 |
| nsrc-000022 | 1 | 1 | 0 |
| nsrc-000024 | 1 | 1 | 0 |
| nsrc-000025 | 1 | 1 | 0 |

G7 Production Runtime QA: `TARGET_IDENTITY=PASS`（4件）。
000025 は同一住所の別 owner `奴奈川神社` row が存在しないこと（same address = 1）も P5 で確認済み。
G7 で観測した Shrine id 135〜138 は point-in-time provenance であり、canonical identity ではない。

```text
G8_CONDITION_01_CANONICAL_IDENTITY = PASS（000021 / 000022 / 000024 / 000025）
```

### #2 Adopted coordinate

G2 adopted coordinate。G7 P1〜P5 guard が各 target について 1e-8 以内で一致を確認し、
Production Runtime QA も同座標で PASS。

| candidate_id | latitude | longitude |
| --- | --- | --- |
| nsrc-000021 | 38.1409456 | 139.4073314 |
| nsrc-000022 | 37.573979 | 139.048758 |
| nsrc-000024 | 37.7863255 | 139.1351949 |
| nsrc-000025 | 37.0397729 | 137.8644153 |

```text
G8_CONDITION_02_ADOPTED_COORDINATE = PASS（4件）
```

### #3 Source-backed ShrineKnowledgeSource

4件とも G7 で Source を1件ずつ新規作成した（`source_CREATE = 1`、accepted_source_count = 0）。
P5 guard は各 Source について importer semantic identity（source_type + normalized URL）= 1、
metadata compatible = 1、lookalike = 1、importer-unparseable URL = 0、他 Shrine からの relation = 0 を確認した。

| candidate_id | source_type | publisher | title | url |
| --- | --- | --- | --- | --- |
| nsrc-000021 | government | 新潟県 | 北前船の魅力を訪ねて | `https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html` |
| nsrc-000022 | government | 三条市 | 五十嵐神社 | `https://www.city.sanjo.niigata.jp/sanjonavi/see_do/history_culture/jinja_jisha_joshi/2289.html` |
| nsrc-000024 | government | 新潟市 | 文化資源ガイド（秋葉区） | `https://www.city.niigata.lg.jp/kanko/bunka/shinko/bunkashigen/bunkaisannintei2.files/akihaku.pdf` |
| nsrc-000025 | shrine_official | 天津神社・奴奈川神社 | 御由緒・御祭神 | `https://amatsujinja.com/story/`（normalized `https://amatsujinja.com/story`） |

bibliography は4件とも空。G7 で観測した Source id 147〜150 は canonical identity として扱わない。

```text
G8_CONDITION_03_SOURCE_BACKED_KNOWLEDGE_SOURCE = PASS（4件）
```

### #4 Fact-ready Deity / History

P5 guard は各 target の Deity / History が frozen Fact に全 field 一致で各1回だけ存在し
（verification_status = source_confirmed、confidence = high、verified_at = 2026-10-19T14:35:38+09:00）、
想定外の Fact が0件であることを確認した。

| candidate_id | Deity | History |
| --- | --- | --- |
| nsrc-000021 | 天鈿女命 | regional_context / 船主による船絵馬の奉納 |
| nsrc-000022 | 五十日帯日子命 | （0件） |
| nsrc-000024 | 大己貴神 / 大物主命 / 菅原道真公 | historical_event / 桂家の守り神から秋葉町内への移譲（昭和39年（1964））; historical_event / 創建250年（平成25年（2013）） |
| nsrc-000025 | 天津彦々火瓊々杵尊 / 天児屋根命 / 天太玉命 | tradition / 景行天皇御代の創設（公式由緒）; tradition / 孝徳天皇の勅願所（公式由緒）; historical_event / 本殿の建立（寛政9年（1797））; historical_event / 拝殿の改築（寛文2年（1662））; historical_event / 幣殿の増築（天明2年（1782）） |

除外 Fact が存在しないことも P5 で確認済み: 000022 `五十日帯彦命`、000025 `奴奈川媛命` / `八千矛命`。
000022 は Deity-only Knowledge（History 0）であり、G5 contract（usable Deity ≥ 1 OR usable History ≥ 1）上許容される。

```text
G8_CONDITION_04_FACT_READY_KNOWLEDGE = PASS（4件）
```

### #5 Fact-ready Source relation / Evidence Gate

P5 guard: 各 Fact が自候補の metadata-compatible Source へちょうど1件の relation を持ち、
他 Source への relation = 0、source-less Fact = 0、target citation = 0、target SourceFact = 0、
target Collective = 0。Production Runtime QA: `SOURCE_RELATION_INTEGRITY=PASS` / `FACT_OWNERSHIP_ISOLATION=PASS`。

| candidate_id | Fact-Source relations | G5 usable Deity | G5 usable History | G5 usable total |
| --- | ---: | ---: | ---: | ---: |
| nsrc-000021 | 2 | 1 | 1 | 2 |
| nsrc-000022 | 1 | 1 | 0 | 1 |
| nsrc-000024 | 5 | 3 | 2 | 5 |
| nsrc-000025 | 8 | 3 | 5 | 8 |

```text
G8_CONDITION_05_FACT_SOURCE_RELATION = PASS（4件）
G8_CONDITION_05_EVIDENCE_USABLE      = PASS（4件）
```

### #6 Shrine.goriyaku approved-only

P1〜P5 guard: 各 target の `Shrine.goriyaku = ''`。Production Runtime QA: `GORIYAKU_ISOLATION=PASS`。
Source / Fact から未承認のご利益意味を生成していない。

```text
G8_CONDITION_06_GORIYAKU_APPROVED_ONLY = PASS（4件）
```

### #7 goriyaku_tags canonical safe subset

P1〜P5 guard: 各 target の goriyaku tag link = 0、ShrineGoriyakuAssignment = 0。
Base import は `--skip-goriyaku-tags`（`goriyaku_tags rows=0 updated=0 added_links=0 removed_links=0`）。

```text
[] subset_of canonical 39（4件とも approved set は空集合）
G8_CONDITION_07_GORIYAKU_TAG_SAFE_SUBSET = PASS（4件）
```

### #8 No automatic GoriyakuTag creation（UNRESOLVED）

Query（本 PR で追加、SELECT-only）:
`scripts/migration_safety/sql/niigata_vpg001_g8_goriyaku_tag_master.sql`

```text
reports:
goriyaku_tag_total
goriyaku_tag_min_id
goriyaku_tag_max_id
goriyaku_tag_distinct_ids

expected canonical state = 39 / 1 / 39 / 39
```

実行方法（Mother Ship、local、read-only）:

```text
scripts/migration_safety/readonly_query.sh <credential file outside repo> DATABASE_URL \
  scripts/migration_safety/sql/niigata_vpg001_g8_goriyaku_tag_master.sql
```

現時点の evidence:

- G7 closure は goriyaku 系 delta 0 を記録している。
- Knowledge importer は GoriyakuTag / ShrineGoriyakuAssignment を作成対象に持たず、Base import は
  `--skip-goriyaku-tags` で実行された。
- ただし G7 cohort guard（P0〜P5）は `temples_goriyakutag` master count を含まないため、
  G7 apply の直前・直後に GoriyakuTag master を独立計測した記録はない。

fresh Production 出力が供給されるまで、本 Condition は判定しない。分類（PASS / PASS_WITH_LIMITATION / FAIL）は
供給された出力と上記 limitation を見て Mother Ship が決める。

```text
G8_CONDITION_08_NO_NEW_GORIYAKU_TAG = PENDING_MOTHER_SHIP_MEASUREMENT
```

### #9 Concierge shared eligibility / candidate path

G7 Production Runtime QA（4件とも、READ ONLY transaction）:

```text
SHARED_ELIGIBILITY=PASS
CONCIERGE_CANDIDATE_PATH=PASS
RECOMMENDATION_REASON=PASS
G7_PRODUCTION_RUNTIME_QA=PASS
TRANSACTION_MODE=READ_ONLY
```

shared runtime trace（各候補）: `count=115 eligible=115 ineligible=18 with_place_id=2 miss_latlng=0 dist_none=0`。
Top1 は Acceptance Criteria ではない。

```text
G8_CONDITION_09_CONCIERGE_SHARED_ELIGIBILITY = PASS（4件）
G8_CONDITION_09_CANDIDATE_PATH               = PASS（4件）
```

### #10 Compass distance / direction

G7 Production Runtime QA（4件とも）: `COMPASS_DISTANCE=PASS` / `COMPASS_DIRECTION=PASS`。G2 adopted coordinate を使用。

```text
G8_CONDITION_10_COMPASS_DISTANCE  = PASS（4件）
G8_CONDITION_10_COMPASS_DIRECTION = PASS（4件）
```

### #11 Re-import idempotency

Base second dry-run（4-row target-only subset）:

```text
done created=0 updated=0 skipped=4 total_seed=4
```

Knowledge second dry-run（G7 §8）:

| candidate_id | plan | CREATE |
| --- | --- | ---: |
| nsrc-000021 | source_REUSE_EXISTING 1 / deity_SKIP_EXISTS 1 / history_SKIP_EXISTS 1 | 0 |
| nsrc-000022 | source_REUSE_EXISTING 1 / deity_SKIP_EXISTS 1 | 0 |
| nsrc-000024 | source_REUSE_EXISTING 1 / deity_SKIP_EXISTS 3 / history_SKIP_EXISTS 2 | 0 |
| nsrc-000025 | source_REUSE_EXISTING 1 / deity_SKIP_EXISTS 3 / history_SKIP_EXISTS 5 | 0 |

idempotency 後に P5 guard を再実行し、5 statement すべて PASS（`P5_FINAL_RECHECK = PASS`）。

```text
G8_CONDITION_11_REIMPORT_IDEMPOTENCY = PASS（4件）
```

### #12 Candidate Master / Production PRE_TRANSITION alignment

PR #3283 で G7 Production state へ同期済み。current Candidate Master（`develop@c32a617`）:

| field | nsrc-000021 | nsrc-000022 | nsrc-000024 | nsrc-000025 |
| --- | --- | --- | --- | --- |
| candidate_status | IMPORTED | IMPORTED | IMPORTED | IMPORTED |
| status_reason_code | PRODUCTION_IMPORT_COMPLETE | PRODUCTION_IMPORT_COMPLETE | PRODUCTION_IMPORT_COMPLETE | PRODUCTION_IMPORT_COMPLETE |
| official_source_status | CONFIRMED | CONFIRMED | CONFIRMED | CONFIRMED |
| knowledge_status | FACT_READY | FACT_READY | FACT_READY | FACT_READY |
| identity_status | CONFIRMED | CONFIRMED | CONFIRMED | CONFIRMED |
| duplicate_status | SAME_NAME_DIFFERENT_SHRINE | NEW | SAME_NAME_DIFFERENT_SHRINE | SAME_NAME_DIFFERENT_SHRINE |
| build_batch | null | null | null | null |
| wave_id | null | null | null | null |
| candidate_reason | official_source_full_enumeration_candidate | 同左 | 同左 | 同左 |

immutable admission provenance（4件共通部分）:

```text
track                  = nationwide_source_candidate
prefecture             = 新潟県
source_batch_id        = NIIGATA-001
source_snapshot_sha256 = f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380
source_url             = https://niigata-jinjacho.jp/shrine_niigata/search.php
source_verified_at     = 2026-10-08
captured_at            = 2026-10-08T14:27:00+09:00
```

| candidate_id | handoff_id | source_position |
| --- | --- | --- |
| nsrc-000021 | NIIGATA-001-H015 | page008-row003 |
| nsrc-000022 | NIIGATA-001-H019 | page010-row004 |
| nsrc-000024 | NIIGATA-001-H006 | page003-row007 |
| nsrc-000025 | NIIGATA-001-H014 | page007-row006 |

Production は G7 CLOSED / PASS、Candidate Master は `IMPORTED / CONFIRMED / FACT_READY`。
Source batch / handoff / VPG id を `build_batch` へ推論せず null を維持する
（Nationwide Source Track build_batch rule）。

Excluded `nsrc-000023`（unchanged）:

```text
candidate_status       = DISCOVERED
status_reason_code     = REGISTRY_ADMISSION_COMPLETE
official_source_status = AVAILABLE
knowledge_status       = UNREVIEWED
identity_status        = CONFIRMED
duplicate_status       = NEW
build_batch            = null
wave_id                = null
```

```text
G8_CONDITION_12_PRE_TRANSITION_ALIGNMENT  = PASS（4件）
G8_CONDITION_12_POST_TRANSITION_ALIGNMENT = NOT_EXECUTED
```

---

## 6. Completion Contract summary

| # | Condition | 000021 | 000022 | 000024 | 000025 |
| ---: | --- | --- | --- | --- | --- |
| 1 | Production canonical identity | PASS | PASS | PASS | PASS |
| 2 | adopted latitude / longitude | PASS | PASS | PASS | PASS |
| 3 | Source-backed ShrineKnowledgeSource | PASS | PASS | PASS | PASS |
| 4 | Fact-ready Deity / History | PASS（D1 / H1） | PASS（D1 / H0） | PASS（D3 / H2） | PASS（D3 / H5） |
| 5 | Fact-ready Source relation / Evidence Gate | PASS | PASS | PASS | PASS |
| 6 | Shrine.goriyaku approved-only | PASS | PASS | PASS | PASS |
| 7 | goriyaku_tags canonical safe subset | PASS | PASS | PASS | PASS |
| 8 | no automatic GoriyakuTag creation | PENDING | PENDING | PENDING | PENDING |
| 9 | Concierge shared eligibility / candidate path | PASS | PASS | PASS | PASS |
| 10 | Compass distance / direction | PASS | PASS | PASS | PASS |
| 11 | re-import idempotency | PASS | PASS | PASS | PASS |
| 12 | Candidate Master / Production alignment | PRE PASS / POST NOT_EXECUTED | 同左 | 同左 | 同左 |

```text
COMPLETION_CONTRACT_PRE_TRANSITION = 11/12 SATISFIED, #8 UNRESOLVED
G8_BLOCKER                         = CONDITION_08_FRESH_PRODUCTION_MEASUREMENT_NOT_SUPPLIED
G8_CONDITION_12_POST_TRANSITION    = NOT_EXECUTED
```

---

## 7. Mother Ship Decision Gate（unresolved）

```text
MOTHER_SHIP_CORE_READY_TRANSITION_DECISION = NOT_RECORDED
```

本書は transition を承認しない。Condition #8 が測定・分類されるまで、transition decision の前提
（Completion Contract PRE_TRANSITION 12/12）は満たされていない。

将来検討され得る delta は各 target の次の2 field だけ（本書では適用しない）。

```text
candidate_status:
IMPORTED -> CORE_READY

status_reason_code:
PRODUCTION_IMPORT_COMPLETE -> CORE_READY_CONTRACT_PASS
```

不変であるべき field（各 target）:

```text
official_source_status = CONFIRMED
knowledge_status       = FACT_READY
identity_status        = CONFIRMED
duplicate_status       = 候補ごとの現在値（000022 = NEW、他3件 = SAME_NAME_DIFFERENT_SHRINE）
build_batch            = null
wave_id                = null
candidate_reason       = official_source_full_enumeration_candidate
admission_provenance   = unchanged
```

いかなる場合も禁止:

- Production DB write
- Base Seed / Knowledge Seed 変更
- G1〜G7 audit rewrite
- Ranking / Score / Recommendation / Concierge / Compass / Position 変更
- GoriyakuTag 変更
- nsrc-000023 の lifecycle 変更
- Historical Wave0 変更
- build_batch 捏造
- transition 前に G8 CLOSED を宣言

---

## 8. Next steps

1. Mother Ship が `niigata_vpg001_g8_goriyaku_tag_master.sql` を `readonly_query.sh` で Production に read-only 実行し、
   4値（total / min_id / max_id / distinct_ids）を供給する。
2. 出力と §5 #8 の limitation を元に Condition #8 を分類し、本書へ追記する。
   12/12 SATISFIED を記録できるのはこの時点以降だけである。
3. その後、Mother Ship が CORE_READY transition decision を行う。

transition PR が merge された後にだけ、次の POST_TRANSITION verification を行う。

1. 各 target の `candidate_status == CORE_READY`
2. 各 target の `status_reason_code == CORE_READY_CONTRACT_PASS`
3. `knowledge_status == FACT_READY` / `official_source_status == CONFIRMED` 不変
4. `build_batch == null` / `wave_id == null`
5. admission provenance 完全一致
6. identity / duplicate evidence 完全一致
7. nsrc-000023 に差分なし
8. 既存 CORE_READY Candidate に差分なし
9. Historical Wave0 accounting 不変
10. Candidate Master tests / relevant consumers PASS
11. Completion Contract #1〜#11 evidence に後退なし

---

## 9. Final PRE_TRANSITION classification

```text
G1                                    = PASS（000022 NEW / 他3件 SAME_NAME_DIFFERENT_SHRINE）
G2                                    = CLOSED / PASS
G3                                    = NORMAL_MODEL_FIT（000021 / 000022 / 000024）
                                        CURATION_RELEASE_CANDIDATE（000025）
G4                                    = CLOSED / PASS
G5                                    = PASS / ELIGIBLE
G6                                    = CLOSED / PASS
G7                                    = CLOSED / PASS

G8_CONDITIONS_01_TO_07                = PASS
G8_CONDITION_08                       = PENDING_MOTHER_SHIP_MEASUREMENT
G8_CONDITIONS_09_TO_11                = PASS
G8_CONDITION_12_PRE_TRANSITION        = PASS
G8_CONDITION_12_POST_TRANSITION       = NOT_EXECUTED

COMPLETION_CONTRACT_PRE_TRANSITION    = 11/12 SATISFIED, #8 UNRESOLVED
G8_BLOCKER                            = CONDITION_08_FRESH_PRODUCTION_MEASUREMENT_NOT_SUPPLIED

MOTHER_SHIP_CORE_READY_TRANSITION_DECISION = NOT_RECORDED
CORE_READY_TRANSITION                      = NOT_EXECUTED
G8_STATUS                                  = OPEN
```

```text
IMPORTED   != CORE_READY
FACT_READY != CORE_READY
```
