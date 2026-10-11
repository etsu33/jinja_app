# nsrc-000002 G8 CORE READY PRE_TRANSITION

## Status

- Candidate: `nsrc-000002` 青澤神社（新潟県糸魚川市大字青海2696番地）
- Recorded at: `2026-10-11`
- Gate: `G8 CORE READY`（PRE_TRANSITION）
- Audit base: `develop@e9d7fabe7f34c8c3a9324da5b583279939c6cdfb`（PR #3156 merge）
- G7 Production Import: `CLOSED / PASS`（PR #3155）
- Candidate Master G7 sync: `MERGED`（PR #3156）
- Production write in this G8 audit: `0`
- Structural precedent: `docs/audit/niigata-h001-g8-core-ready-pretransition.md`（nsrc-000004）。nsrc-000004 固有の Fact は使っていない

```text
COMPLETION_CONTRACT_PRE_TRANSITION         = 12/12 SATISFIED
G8_CONDITION_12_POST_TRANSITION            = NOT_EXECUTED
MOTHER_SHIP_CORE_READY_TRANSITION_DECISION = APPROVED_TARGET_ONLY
TARGET                                     = nsrc-000002
CORE_READY_TRANSITION                      = NOT_EXECUTED
G8_STATUS                                  = OPEN
```

本書は Completion Contract #1〜#12 の PRE_TRANSITION evidence と、Mother Ship の target-only CORE_READY transition 承認を記録する。
Candidate Master の `IMPORTED -> CORE_READY` transition は本 PR では実行しない（別 PR）。
本 PR は Production DB / Seed / Candidate Master / lifecycle data を変更しない。

---

## 1. Authority

- `docs/knowledge/shrine-expansion-gate-contract.md` §11
- `docs/audit/shrine-expansion-wave0-data-build-plan.md` CORE READY Completion Contract
- `docs/knowledge/shrine-expansion-candidate-master-contract.md` schema 1.4 Nationwide Source Track Boundary
- `docs/audit/niigata-h001-nsrc-000002-g7-production-import-preflight.md`
- `backend/temples/data/shrine_expansion_candidate_master.json`

```text
IMPORTED   != CORE_READY
FACT_READY != CORE_READY
```

---

## 2. Scope

対象は1件だけ。

```text
candidate_id = nsrc-000002
name_jp      = 青澤神社
address      = 新潟県糸魚川市大字青海2696番地
```

次の H001 候補は本 G8 の scope 外とし、変更しない。

```text
nsrc-000001 相吉神社
nsrc-000003 蒼柴神社
nsrc-000004 青海神社（CORE_READY 済み。nsrc-000004 G8 は CLOSED）
nsrc-000005 青山稲荷神社
```

これらの upstream HOLD / review 結果や lifecycle を本 G8 で解除・再解釈しない。

---

## 3. Upstream Gate lineage

| Gate | Result | Evidence |
| --- | --- | --- |
| G1 Identity / Duplicate | PASS / NEW | `docs/audit/niigata-h001-g1-identity-duplicate.md` |
| G2 Position / Navigation Anchor | PASS | `docs/audit/niigata-h001-g2-position-gate.md` / `docs/audit/shrine-position/niigata-h001-aosawa-jinja-position-resolution.md`。adopted coordinate `37.00763484, 137.79024297` |
| G3 Source + Knowledge Model Fit | PASS / NORMAL_MODEL_FIT | `docs/audit/niigata-h001-nsrc-000002-g3-source-knowledge-fit.md` |
| G4 Knowledge Fact + Evidence | PASS | `docs/audit/niigata-h001-nsrc-000002-g4-formal-redecision.md`（PR #3149） |
| G5 Shared Recommendation Eligibility | PASS / ELIGIBLE | `docs/audit/niigata-h001-nsrc-000002-g5-recommendation-eligibility.md`（PR #3150） |
| G6 Runtime QA | PASS | `docs/audit/niigata-h001-nsrc-000002-g6-runtime-qa.md`（PR #3151） |
| G7 Production Import | CLOSED / PASS | `docs/audit/niigata-h001-nsrc-000002-g7-production-import-preflight.md`（PR #3152〜#3155） |

G4 preflight 時点の `FORMAL_G4 = HOLD`（reason_code `BASE_SHRINE_NOT_MATERIALIZED`）と、G7 準備段階の HOLD / NO / NOT EXECUTED は履歴として保持する。
後続の re-decision と G7 実行記録が解消経路の evidence であり、過去記録を書き換えない。

---

## 4. Evidence の出所

| 区分 | 内容 |
| --- | --- |
| G7 Production 実測（Mother Ship 実行、PR #3155 で記録） | post-Base guard / post-Knowledge verification / aggregate / target integrity / idempotency dry-run / Production Runtime QA |
| G8 fresh Production read-only（Mother Ship 実行） | Condition #8 の GoriyakuTag master current-state だけ |
| repository current state | Candidate Master（PR #3156 merge 後の `develop`） |

本 PR を作成した実行環境は Production に接続していない。#8 以外の Production 値は G7 実行時点の point-in-time 実測である。

---

## 5. Completion Contract #1〜#12

### #1 Production Shrine canonical identity

G7 Production post-Knowledge verification:

```text
target_shrine = 1    (name_jp = 青澤神社 AND address = 新潟県糸魚川市大字青海2696番地)
```

G7 post-Base guard（`g7_post_base_guard_pass = 1`）は同時に次を条件としている:

```text
same-name 青澤神社 = 1
same-name 青沢神社 = 0
same-address       = 1
```

Production Shrine id `127` は point-in-time provenance であり、canonical identity ではない。

```text
G8_CONDITION_01_CANONICAL_IDENTITY = PASS
```

### #2 Adopted coordinate

G2 adopted coordinate:

```text
latitude  = 37.00763484
longitude = 137.79024297
```

G7 post-Base guard と post-Knowledge verification（`pass = 1`）は、target の座標が上記と `1e-8` 未満で一致することを条件に含む。
G7 Production Runtime QA の candidate も同じ座標を返した（`candidate.lat / lng` 一致、`distance_m = 0`）。

```text
G8_CONDITION_02_ADOPTED_COORDINATE = PASS
```

### #3 Source-backed ShrineKnowledgeSource

G7 Production post-Knowledge verification:

```text
source_type         = government
publisher           = 糸魚川市 / 糸魚川ジオパーク協議会
url                 = https://matsuri.geo-itoigawa.com/calendar/m04/
verification_status = source_confirmed
confidence          = high
language            = ja
```

target History に結び付く Source は importer semantic identity（`source_type + normalize_source_url()`）で1件、metadata compatible。

```text
G8_CONDITION_03_SOURCE_BACKED_KNOWLEDGE_SOURCE = PASS
```

### #4 Fact-ready Deity / History

G7 Production target integrity:

```text
target_deity   = 0
target_history = 1
```

採用 Fact:

```text
History
- 青沢神社の春季祭礼
  history_type        = regional_context
  period_text         = 毎年4月第3日曜日
  event_date          = null
  verification_status = source_confirmed
  confidence          = high

Deity
- なし
```

nsrc-000002 は History-only Knowledge である。凍結 Source packet に Source-backed な祭神名が無いため Deity は 0 件で、
沼河比賣命 / 沼河比売命を含む未裏付けの祭神名は追加していない。
G5 authority では usable History が1件あれば ELIGIBLE であり、Deity 0 は CORE READY の欠格理由ではない。

```text
G8_CONDITION_04_FACT_READY_KNOWLEDGE = PASS
```

### #5 Fact-ready Source relation / Evidence Gate

G7 Production target integrity:

```text
history_source_relations = 1
sourceless_history       = 0
target_source_fact       = 0
```

G4 Evidence Gate（`decide_fact_usability`）は H1 を `usable=True / display_mode=full / reason_strength=assertive /
reason=fact_ready_with_source` と判定した。G5 verifier の usable History = 1。

```text
usable History = 1
usable Deity   = 0
```

```text
G8_CONDITION_05_FACT_SOURCE_RELATION = PASS
G8_CONDITION_05_EVIDENCE_USABLE      = PASS
```

### #6 Shrine.goriyaku approved-only

G7 Production post-Knowledge verification の条件:

```text
Shrine.goriyaku = ""
```

Knowledge Seed は goriyaku を持たず、History / Source から未承認のご利益意味を `Shrine.goriyaku` へ変換していない。

```text
G8_CONDITION_06_GORIYAKU_APPROVED_ONLY = PASS
```

この PASS は「ご利益情報がある」ことを意味しない。未承認の意味を legacy free text へ持ち込んでいないことだけを表す。

### #7 goriyaku_tags canonical safe subset

G7 Production target integrity:

```text
target_goriyaku_tag_links   = 0
target_goriyaku_assignments = 0
```

approved set は空集合。

```text
[] ⊆ canonical 39
```

```text
G8_CONDITION_07_GORIYAKU_TAG_SAFE_SUBSET = PASS
```

### #8 No automatic GoriyakuTag creation

G8 fresh Production read-only:

```text
goriyaku_tag_total        = 39
goriyaku_tag_min_id       = 1
goriyaku_tag_max_id       = 39
goriyaku_tag_distinct_ids = 39
```

G7 監査記録では、Production Base dry-run / apply の goriyaku 変更は `goriyaku delta = 0` と記録されている。
Knowledge importer は GoriyakuTag / ShrineGoriyakuAssignment を操作対象に持たず、
既存 regression（`test_nsrc_000002_knowledge_seed.py` の goriyaku isolation）で GoriyakuTag master と target goriyaku state の before / after 完全一致を確認している。
Production post-Knowledge verification でも `Shrine.goriyaku = ""`、`target_goriyaku_tag_links = 0`、`target_goriyaku_assignments = 0` を確認した。

Limitation:

G7 apply の直前・直後に GoriyakuTag master count を独立測定した記録はない。
そのため、G7 実行中に一時的な CREATE / DELETE が絶対になかったことを時系列実測だけで証明したとは扱わない。

```text
G8_CONDITION_08_NO_NEW_GORIYAKU_TAG = PASS_WITH_LIMITATION
```

Mother Ship は、current canonical 39/39、Importer contract、target goriyaku delta 0、既存 regression を根拠に
Completion Contract 上は受容する。この limitation は後続記録でも消さない。

### #9 Concierge shared eligibility / candidate path

G5（isolated）: verifier `ELIGIBLE`、shared partition 通過、runtime candidate filter 保持。

G7 Production Runtime QA:

```text
CONCIERGE_CANDIDATE_PATH=PASS
G7_PRODUCTION_RUNTIME_QA=PASS
TRANSACTION_MODE=READ_ONLY
```

runtime log:

```text
trace=nsrc-000002-g7-production-runtime
count=108
eligible=108
ineligible=14
with_place_id=2
miss_latlng=0
dist_none=0
```

target は shared candidate path に1件だけ存在し、`knowledge_deities = []`、`knowledge_histories` 1件、`goriyaku_tag_ids = []`。

```text
G8_CONDITION_09_CONCIERGE_SHARED_ELIGIBILITY = PASS
G8_CONDITION_09_CANDIDATE_PATH               = PASS
```

Recommendation Reason（G7 Production Runtime QA `RECOMMENDATION_REASON=PASS`）は deity None / shrine_history = H1 / goriyaku None で、
保証表現を含まない。Recommendation Top1 は要求していない。

### #10 Compass distance / direction

G7 Production Runtime QA:

```text
COMPASS_DISTANCE=PASS
COMPASS_DIRECTION=PASS
```

adopted coordinate で distance / bearing / 8方位 label / direction filter を実行し、
一致方向では target を保持し、不一致の7方向では除外することを確認した。Compass Top1 は要求していない。

```text
G8_CONDITION_10_COMPASS_DISTANCE  = PASS
G8_CONDITION_10_COMPASS_DIRECTION = PASS
```

### #11 Re-import idempotency

G7 Production post-state への Base dry-run:

```text
created=0 updated=0 skipped=1 total_seed=1
```

Knowledge dry-run:

```text
source_REUSE_EXISTING = 1
history_SKIP_EXISTS   = 1
CREATE                = 0
```

```text
G8_CONDITION_11_REIMPORT_IDEMPOTENCY = PASS
```

### #12 Candidate Master / Production PRE_TRANSITION alignment

PR #3156 で G7 Production state へ同期済み。

Current Candidate Master（`develop@e9d7fabe`）:

```text
candidate_id           = nsrc-000002
candidate_status       = IMPORTED
status_reason_code     = PRODUCTION_IMPORT_COMPLETE
official_source_status = CONFIRMED
knowledge_status       = FACT_READY
identity_status        = CONFIRMED
duplicate_status       = NEW
build_batch            = null
wave_id                = null
candidate_reason       = official_source_full_enumeration_candidate
```

保持された immutable admission provenance:

```text
track                  = nationwide_source_candidate
prefecture             = 新潟県
source_batch_id        = NIIGATA-001
handoff_id             = NIIGATA-001-H001
source_position        = page001-row002
source_snapshot_sha256 = f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380
source_url             = https://niigata-jinjacho.jp/shrine_niigata/search.php
source_verified_at     = 2026-10-08
captured_at            = 2026-10-08T14:27:00+09:00
```

Production（G7 CLOSED / PASS: Shrine / Source / History 作成済み、Deity / SourceFact 0）と Candidate Master
（IMPORTED / CONFIRMED / FACT_READY）は一致している。

Nationwide Source Track では Source batch / handoff を `build_batch` へ推論しない（`NIIGATA-001` / `NIIGATA-001-H001` 禁止）。
Historical Wave0 の `W0-DBxx` も捏造しない。target は downstream Data Build batch assignment を持たないため `build_batch = null` を維持する。

PR #3156 validation:

```text
Candidate Master tests      = 91 passed
Candidate Master consumers  = 119 passed
scripts/tests               = 685 passed
backend full suite          = 4959 passed, 12 skipped
makemigrations --check      = No changes detected
ruff                        = PASS
git diff --check            = clean
```

```text
G8_CONDITION_12_PRE_TRANSITION_ALIGNMENT  = PASS
G8_CONDITION_12_POST_TRANSITION_ALIGNMENT = NOT_EXECUTED
```

---

## 6. Completion Contract summary（PRE_TRANSITION 時点）

| # | Condition | Result |
| ---: | --- | --- |
| 1 | Production canonical identity | PASS |
| 2 | adopted latitude / longitude | PASS |
| 3 | Source-backed ShrineKnowledgeSource | PASS |
| 4 | Fact-ready Deity / History（Deity 0 / History 1） | PASS |
| 5 | Fact-ready Source relation / Evidence Gate | PASS |
| 6 | Shrine.goriyaku approved-only | PASS |
| 7 | goriyaku_tags canonical safe subset | PASS |
| 8 | no automatic GoriyakuTag creation | PASS_WITH_LIMITATION |
| 9 | Concierge shared eligibility / candidate path | PASS |
| 10 | Compass distance / direction | PASS |
| 11 | re-import idempotency | PASS |
| 12 | Candidate Master / Production alignment | PRE_TRANSITION PASS / POST_TRANSITION NOT_EXECUTED |

```text
COMPLETION_CONTRACT_PRE_TRANSITION = 12/12 SATISFIED
G8_CONDITION_12_POST_TRANSITION    = NOT_EXECUTED
```

---

## 7. Mother Ship Decision Record

Recorded at: `2026-10-11`

### Decision

```text
MOTHER_SHIP_CORE_READY_TRANSITION_DECISION = APPROVED_TARGET_ONLY
TARGET                                    = nsrc-000002
```

根拠（本書 §3〜§6）:

- G1〜G7 が対象 Candidate について PASS / CLOSED
- Completion Contract #1〜#11 を満たす（#8 は PASS_WITH_LIMITATION）
- #12 PRE_TRANSITION が PR #3156 merge 後の Candidate Master で PASS
- G7 re-import idempotency が PASS
- Production runtime で Detail / Concierge / Recommendation / Compass が PASS
- transition は Production write を必要としない

### Approved transition delta（別 PR でのみ許可）

```text
candidate_id = nsrc-000002

candidate_status:
IMPORTED -> CORE_READY

status_reason_code:
PRODUCTION_IMPORT_COMPLETE -> CORE_READY_CONTRACT_PASS
```

以下は不変。

```text
official_source_status = CONFIRMED
knowledge_status       = FACT_READY
identity_status        = CONFIRMED
duplicate_status       = NEW
build_batch            = null
wave_id                = null
candidate_reason       = official_source_full_enumeration_candidate
admission_provenance   = unchanged
```

### Explicit prohibitions

- Candidate Master 変更（本 PR）
- Production DB write
- Base Seed / Knowledge Seed 変更
- G1〜G7 historical audit の書き換え
- Ranking / Score / Recommendation 変更
- Compass 変更
- GoriyakuTag 変更
- models / migrations 変更
- `nsrc-000001 / 000003 / 000004 / 000005` 変更
- Historical Wave0 変更
- `build_batch` 捏造
- CORE_READY transition の実行（本 PR）
- G8 CLOSED の宣言（本 PR / transition PR）

---

## 8. Required POST_TRANSITION verification

CORE_READY transition PR merge 後に次を確認する。

1. `nsrc-000002.candidate_status == CORE_READY`
2. `status_reason_code == CORE_READY_CONTRACT_PASS`
3. `knowledge_status == FACT_READY`
4. `official_source_status == CONFIRMED`
5. `build_batch == null` / `wave_id == null`
6. admission provenance 完全一致
7. identity / duplicate evidence 完全一致（`CONFIRMED` / `NEW`）
8. 他 H001 4候補（`nsrc-000001 / 000003 / 000004 / 000005`）に差分なし
9. Historical Wave0 accounting 不変
10. Candidate Master tests PASS
11. Completion Contract #1〜#11 evidence に後退なし

すべて PASS した後だけ、Closure record で次を記録する。

```text
NSRC_000002_POST_TRANSITION_ALIGNMENT = PASS
NSRC_000002_CORE_READY                = PASS
G8_STATUS                             = CLOSED
```

#8 の PASS_WITH_LIMITATION と limitation の記述は Closure でも保持する。

---

## 9. Final PRE_TRANSITION classification

```text
G1                                    = PASS / NEW
G2                                    = PASS
G3                                    = PASS / NORMAL_MODEL_FIT
G4                                    = PASS
G5                                    = PASS / ELIGIBLE
G6                                    = PASS
G7                                    = CLOSED / PASS

G8_CONDITIONS_01_TO_07                = PASS
G8_CONDITION_08                       = PASS_WITH_LIMITATION
G8_CONDITIONS_09_TO_11                = PASS
G8_CONDITION_12_PRE_TRANSITION        = PASS
G8_CONDITION_12_POST_TRANSITION       = NOT_EXECUTED

COMPLETION_CONTRACT_PRE_TRANSITION    = 12/12 SATISFIED
MOTHER_SHIP_CORE_READY_TRANSITION     = APPROVED_TARGET_ONLY
CORE_READY_TRANSITION                 = NOT_EXECUTED
G8_STATUS                             = OPEN
```

次工程は、対象1件だけの Candidate Master `IMPORTED -> CORE_READY` transition PR である。
