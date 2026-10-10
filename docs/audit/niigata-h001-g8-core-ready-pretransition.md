# nsrc-000004 G8 CORE READY Closure

## Status

- Candidate: `nsrc-000004` 青海神社（新潟県加茂市）
- Recorded at: `2026-10-10`
- Gate: `G8 CORE READY Closure`
- Audit base: `develop@7474fe8cb556237c068e8be93ec93e17434a53da`
- Closure base: `develop@1b240598385b2079dfffb595da063f68a2a97bb1`（PR #3136 merge）
- G7 Production Import: `CLOSED / PASS`（PR #3132）
- Candidate Master G7 sync: `MERGED`（PR #3133）
- G8 GoriyakuTag current-state check: `MERGED`（PR #3134）
- CORE_READY transition: `APPLIED`（PR #3136）
- Production write in this G8 audit: `0`

```text
NSRC_000004_G8_EVIDENCE_GATE          = PASS
NSRC_000004_PRE_TRANSITION_ALIGNMENT  = PASS
NSRC_000004_POST_TRANSITION_ALIGNMENT = PASS
NSRC_000004_G8_DECISION               = APPROVED_TO_TRANSITION_TARGET_ONLY
NSRC_000004_CORE_READY                = PASS
CORE_READY_TRANSITION                 = APPLIED
G8_STATUS                             = CLOSED
```

本書はPRE_TRANSITION evidenceとMother Ship判断を保持し、PR #3136 merge後のPOST_TRANSITION verificationとG8 Closureを追記する。
Candidate MasterのCORE_READY transition自体はPR #3136で適用済みであり、本ClosureではProduction DB / Seed / lifecycle dataを変更しない。

---

## 1. Authority

G8判定のauthority:

- `docs/knowledge/shrine-expansion-gate-contract.md` §11
- `docs/audit/shrine-expansion-wave0-data-build-plan.md` CORE READY Completion Contract
- `docs/knowledge/shrine-expansion-candidate-master-contract.md` schema 1.4 Nationwide Source Track Boundary
- `docs/audit/niigata-h001-g7-production-import.md`
- `backend/temples/data/shrine_expansion_candidate_master.json`

G8は個別Gate PASSをまとめて確認する最終lifecycle Gateである。

```text
IMPORTED  != CORE_READY
FACT_READY != CORE_READY
```

---

## 2. Scope

対象は次の1件だけ。

```text
candidate_id = nsrc-000004
name_jp      = 青海神社
address      = 新潟県加茂市大字加茂字宮山229番地
```

次のH001 4候補は本G8 transition scope外とし、変更しない。

```text
nsrc-000001 相吉神社
nsrc-000002 青澤神社
nsrc-000003 蒼柴神社
nsrc-000005 青山稲荷神社
```

これら4件のupstream HOLD / review結果を本G8で解除・再解釈しない。

---

## 3. Upstream Gate lineage

| Gate | Result | Evidence |
| --- | --- | --- |
| G1 Identity / Duplicate | PASS | `docs/audit/niigata-h001-g1-identity-duplicate.md` |
| G2 Position / Navigation Anchor | PASS | adopted coordinate `37.65657387, 139.0536436` |
| G3 Source + Knowledge Model Fit | PASS / CURATION_RELEASE_CANDIDATE | `docs/audit/niigata-h001-g3-source-knowledge-fit.md` |
| G4 Knowledge Fact + Evidence | PASS | source-backed D1/D2 + H1/H2 |
| G5 Shared Recommendation Eligibility | PASS / ELIGIBLE | G5 audit |
| G6 Runtime QA | PASS | dedicated nsrc-000004 G6 runtime QA |
| G7 Production Import | CLOSED / PASS | `docs/audit/niigata-h001-g7-production-import.md` / PR #3132 |

G4 historical preflightの初期 `HOLD / BASE_SHRINE_NOT_MATERIALIZED` は履歴として保持する。
後続re-entryおよびG7が解消経路のevidenceであり、過去記録を書き換えない。

---

## 4. Completion Contract #1〜#12

### #1 Production Shrine canonical identity

Mother Ship read-only確認:

```text
target_exact_count = 1
same_name_count    = 1
```

Production target:

```text
id        = 126      # provenance only
name_jp   = 青海神社
address   = 新潟県加茂市大字加茂字宮山229番地
```

```text
G8_CONDITION_01_CANONICAL_IDENTITY = PASS
```

### #2 Adopted coordinate

Production current-state:

```text
latitude  = 37.65657387
longitude = 139.0536436
```

G2 adopted coordinateと一致。

```text
G8_CONDITION_02_ADOPTED_COORDINATE = PASS
```

### #3 Source-backed ShrineKnowledgeSource

Production current-state:

```text
target_sources = 3

139 shrine_official 御祭神
140 shrine_official 由緒・年表
141 shrine_official 御祈祷種類

verification_status = source_confirmed
confidence          = high
publisher           = 青海神社
```

```text
G8_CONDITION_03_SOURCE_BACKED_KNOWLEDGE_SOURCE = PASS
```

### #4 Fact-ready Deity / History

Production current-state:

```text
target_deity   = 2
target_history = 2
```

採用Fact:

```text
Deity
- 椎根津彦命
- 大国魂命

History
- 神亀3年の創建
- 明治5年の三社本殿合殿
```

```text
G8_CONDITION_04_FACT_READY_KNOWLEDGE = PASS
```

### #5 Fact-ready Source relation / Evidence Gate

Production current-state:

```text
sourceless_deity        = 0
sourceless_history      = 0
sourceless_source_fact  = 0

deity_source_relations       = 2
history_source_relations     = 2
source_fact_source_relations = 11
```

G5 / G6 evidenceでusable Deity 2 / History 2を確認済み。

```text
G8_CONDITION_05_FACT_SOURCE_RELATION = PASS
G8_CONDITION_05_EVIDENCE_USABLE      = PASS
```

### #6 Shrine.goriyaku approved-only

Production current-state:

```text
goriyaku = ""
```

S4御祈祷11件は`ShrineSourceFact`として保持し、未承認の意味を`Shrine.goriyaku`へ変換していない。

```text
G8_CONDITION_06_GORIYAKU_APPROVED_ONLY = PASS
```

このPASSは「ご利益情報が充実している」ことを意味しない。
未承認意味をlegacy free textへ持ち込んでいないことだけを表す。

### #7 goriyaku_tags canonical safe subset

Production current-state:

```text
target_goriyaku_tag_links = 0
```

approved setも空集合であり、

```text
[] ⊆ canonical 39
```

```text
G8_CONDITION_07_GORIYAKU_TAG_SAFE_SUBSET = PASS
```

### #8 No automatic GoriyakuTag creation

G8 read-only current-state:

```text
goriyaku_tag_total        = 39
goriyaku_tag_min_id       = 1
goriyaku_tag_max_id       = 39
goriyaku_tag_distinct_ids = 39
```

専用testはKnowledge import前後のGoriyakuTag master不変を確認する。
対象Shrineへのtag linkも0件。

ただしG7実行瞬間の直前・直後でGoriyakuTag master countを独立計測した記録はない。
そのため、一時的CREATE/DELETEが絶対になかったことを時系列実測だけで証明したとは扱わない。

```text
G8_CONDITION_08_NO_NEW_GORIYAKU_TAG = PASS_WITH_LIMITATION
```

Mother Shipは、current canonical 39/39、対象Importer contract、専用regression、target delta 0を根拠にCompletion Contract上は受容する。

### #9 Concierge shared eligibility / candidate path

G7 Production Runtime QA:

```text
CONCIERGE_CANDIDATE_PATH=PASS
G7_PRODUCTION_RUNTIME_QA=PASS
TRANSACTION_MODE=READ_ONLY
```

runtimeはtargetがshared candidate pathへ1件だけ存在することを確認した。

```text
G8_CONDITION_09_CONCIERGE_SHARED_ELIGIBILITY = PASS
G8_CONDITION_09_CANDIDATE_PATH               = PASS
```

### #10 Compass distance / direction

G7 Production Runtime QA:

```text
COMPASS_DISTANCE=PASS
COMPASS_DIRECTION=PASS
```

採用座標を使用してdistance / bearing / 8方位label / direction filterを実行し、
一致方向ではtargetを保持し、不一致方向では除外することを確認済み。

```text
G8_CONDITION_10_COMPASS_DISTANCE  = PASS
G8_CONDITION_10_COMPASS_DIRECTION = PASS
```

### #11 Re-import idempotency

G7 Production post-stateへのBase dry-run:

```text
SKIP id=126 青海神社
goriyaku_tags rows=0 updated=0 added_links=0 removed_links=0
done created=0 updated=0 skipped=1 total_seed=1
```

Knowledge dry-run:

```text
source_REUSE_EXISTING   = 3
deity_SKIP_EXISTS       = 2
history_SKIP_EXISTS     = 2
source_fact_SKIP_EXISTS = 11

CREATE    = 0
CONFLICT  = 0
AMBIGUOUS = 0
NOT_FOUND = 0
```

```text
G8_CONDITION_11_REIMPORT_IDEMPOTENCY = PASS
```

### #12 Candidate Master / Production PRE_TRANSITION alignment

PR #3133でG7 Production stateへ同期済み。

Current Candidate Master:

```text
candidate_id           = nsrc-000004
candidate_status       = IMPORTED
status_reason_code     = PRODUCTION_IMPORT_COMPLETE
build_batch            = null
duplicate_status       = SAME_NAME_DIFFERENT_SHRINE
wave_id                = null
identity_status        = CONFIRMED
official_source_status = CONFIRMED
knowledge_status       = FACT_READY
candidate_reason       = official_source_full_enumeration_candidate
```

保持されたimmutable admission provenance:

```text
track                  = nationwide_source_candidate
source_batch_id        = NIIGATA-001
handoff_id             = NIIGATA-001-H001
source_position        = page001-row004
source_snapshot_sha256 = f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380
```

Nationwide Source TrackではSource batch / handoffを`build_batch`へ推論しない。

禁止:

```text
build_batch = NIIGATA-001
build_batch = NIIGATA-001-H001
```

またHistorical Wave0の`W0-DBxx`を捏造しない。
本targetはdownstream Data Build batch assignmentを持たないため`build_batch=null`を維持する。

PR #3133 validation:

```text
Candidate Master tests = 74 passed
Candidate Master consumers = 182 passed
backend full suite = 4918 passed, 12 skipped
makemigrations --check = No changes detected
git diff --check = clean
ruff = 0 findings
```

```text
G8_CONDITION_12_PRE_TRANSITION_ALIGNMENT = PASS
G8_CONDITION_12_POST_TRANSITION_ALIGNMENT = NOT_EXECUTED
```

---

## 5. Completion Contract summary（PRE_TRANSITION時点）

| # | Condition | Result |
| ---: | --- | --- |
| 1 | Production canonical identity | PASS |
| 2 | adopted latitude / longitude | PASS |
| 3 | Source-backed ShrineKnowledgeSource | PASS |
| 4 | Fact-ready Deity / History | PASS |
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
POST_TRANSITION                    = NOT_EXECUTED
```

---

## 6. Mother Ship Decision Record

Recorded at: `2026-10-10`

### Decision

```text
MOTHER_SHIP_CORE_READY_TRANSITION_DECISION = APPROVED_TARGET_ONLY
TARGET                                    = nsrc-000004
```

理由:

- G1〜G7が対象CandidateについてPASS / CLOSEDしている
- Completion Contract #1〜#11が満たされている
- #12 PRE_TRANSITIONがPR #3133 merge後のCandidate MasterでPASS
- Product HOLD / unresolved Model Risk / Position HOLDがtargetに残っていない
- G7 re-import idempotencyがPASS
- Production runtimeでDetail / Concierge / Recommendation / CompassがPASS
- transitionはProduction writeを必要としない

### Approved transition delta

別PRで次だけを変更してよい。

```text
candidate_id = nsrc-000004

candidate_status:
IMPORTED -> CORE_READY

status_reason_code:
PRODUCTION_IMPORT_COMPLETE -> CORE_READY_CONTRACT_PASS
```

以下は不変。

```text
knowledge_status       = FACT_READY
official_source_status = CONFIRMED
identity_status        = CONFIRMED
duplicate_status       = SAME_NAME_DIFFERENT_SHRINE
build_batch            = null
wave_id                = null
candidate_reason       = official_source_full_enumeration_candidate
admission_provenance   = unchanged
```

### Explicit prohibitions

- Production DB write禁止
- Base Seed / Knowledge Seed変更禁止
- G1〜G7 audit rewrite禁止
- Ranking / Score / Recommendation contract変更禁止
- GoriyakuTag変更禁止
- `nsrc-000001 / 000002 / 000003 / 000005`変更禁止
- Historical Wave0変更禁止
- `build_batch`捏造禁止
- transition PR内でG8をCLOSEDと断定しない

---

## 7. Required POST_TRANSITION verification

CORE_READY transition PR merge後、次を確認する。

1. `nsrc-000004.candidate_status == CORE_READY`
2. `status_reason_code == CORE_READY_CONTRACT_PASS`
3. `knowledge_status == FACT_READY`
4. `official_source_status == CONFIRMED`
5. `build_batch == null`
6. admission provenance完全一致
7. identity / duplicate evidence完全一致
8. 他4 H001候補に差分なし
9. Historical Wave0 accounting不変
10. Candidate Master tests PASS
11. Completion Contract #1〜#11 evidenceに後退なし

すべてPASSした後だけ:

```text
NSRC_000004_POST_TRANSITION_ALIGNMENT = PASS
NSRC_000004_CORE_READY                = PASS
G8_STATUS                             = CLOSED
```

としてClosure recordを更新する。

---

## 8. Final PRE_TRANSITION classification

```text
G1                                    = PASS
G2                                    = PASS
G3                                    = PASS
G4                                    = PASS
G5                                    = PASS
G6                                    = PASS
G7                                    = CLOSED / PASS

G8_CONDITIONS_01_TO_07                = PASS
G8_CONDITION_08                       = PASS_WITH_LIMITATION
G8_CONDITIONS_09_TO_11                = PASS
G8_CONDITION_12_PRE_TRANSITION        = PASS
G8_CONDITION_12_POST_TRANSITION       = NOT_EXECUTED

MOTHER_SHIP_CORE_READY_TRANSITION     = APPROVED_TARGET_ONLY
CORE_READY_TRANSITION                 = NOT_EXECUTED
G8_STATUS                             = OPEN
```

次工程は、対象1件だけのCandidate Master `IMPORTED -> CORE_READY` transition PRである。

---

## 9. POST_TRANSITION verification / G8 Closure

### 9.1 Transition merge

CORE_READY transitionはPR #3136で`develop`へmerge済み。

```text
PR                              = #3136
merge_commit                    = 1b240598385b2079dfffb595da063f68a2a97bb1
candidate_id                    = nsrc-000004
candidate_status                = CORE_READY
status_reason_code              = CORE_READY_CONTRACT_PASS
knowledge_status                = FACT_READY
official_source_status          = CONFIRMED
build_batch                     = null
```

PR #3136の変更対象はCandidate Masterとそのcontract testの2ファイルのみ。
Production DB / Base Seed / Knowledge Seed / Recommendation / Ranking / Compass / GoriyakuTagへのwriteはない。

### 9.2 Required POST_TRANSITION verification result

| # | Verification | Result | Evidence |
| ---: | --- | --- | --- |
| 1 | `candidate_status == CORE_READY` | PASS | current `develop` Candidate Master |
| 2 | `status_reason_code == CORE_READY_CONTRACT_PASS` | PASS | current `develop` Candidate Master |
| 3 | `knowledge_status == FACT_READY` | PASS | transition前後で不変 |
| 4 | `official_source_status == CONFIRMED` | PASS | transition前後で不変 |
| 5 | `build_batch == null` | PASS | schema 1.4 Nationwide責務境界およびMother Ship decisionどおり |
| 6 | admission provenance完全一致 | PASS | `track / prefecture / source_batch_id / handoff_id / source_position / source_snapshot_sha256 / source_url / source_verified_at / captured_at` に差分なし |
| 7 | identity / duplicate evidence完全一致 | PASS | `identity_status=CONFIRMED` / `duplicate_status=SAME_NAME_DIFFERENT_SHRINE` を保持 |
| 8 | 他4 H001候補に差分なし | PASS | `nsrc-000001 / 000002 / 000003 / 000005` のbefore/after diff = 0 |
| 9 | Historical Wave0 accounting不変 | PASS | Wave0 44件 -> 44件、changed IDs = 0 |
| 10 | Candidate Master tests PASS | PASS | PR #3136: 74 passed。PR headとmerge commitの対象2ファイルはbyte-for-byte一致、backend-pr CI = success |
| 11 | Completion Contract #1〜#11 evidenceに後退なし | PASS | merge commitはCandidate lifecycle 2 field +対応testのみ。Production / Runtime evidenceへの変更なし |

### 9.3 Minimal-diff result

Transition前の`develop@99473954f7e2ff26f500d8f547402c46dedc383f`とPOST_TRANSITION current stateを比較した結果:

```text
changed H001 candidate = nsrc-000004 only

candidate_status:
IMPORTED -> CORE_READY

status_reason_code:
PRODUCTION_IMPORT_COMPLETE -> CORE_READY_CONTRACT_PASS

nsrc-000001 = unchanged
nsrc-000002 = unchanged
nsrc-000003 = unchanged
nsrc-000005 = unchanged

Historical Wave0 count = 44 -> 44
Historical Wave0 changed IDs = 0
```

対象のimmutable / evidence fieldsは保持されている。

```text
knowledge_status       = FACT_READY
official_source_status = CONFIRMED
identity_status        = CONFIRMED
duplicate_status       = SAME_NAME_DIFFERENT_SHRINE
build_batch            = null
wave_id                = null
candidate_reason       = official_source_full_enumeration_candidate
admission_provenance   = unchanged
```

### 9.4 Validation carried by transition PR

PR #3136 validation:

```text
Candidate Master tests = 74 passed
Candidate Master consumers = 182 passed
scripts/tests = PASS
backend full suite = 4918 passed, 12 skipped
makemigrations --check = No changes detected
ruff = 0 findings
git diff --check = clean

dependency-review = success
codeql = success
backend-pr = success
```

### 9.5 Final G8 classification

Completion Contract #1〜#11はPRE_TRANSITION evidenceから判定変更なし。
#12はtransition後のGovernance Synchronizationを確認し、POST_TRANSITION PASSとする。

```text
G1                                    = PASS
G2                                    = PASS
G3                                    = PASS
G4                                    = PASS
G5                                    = PASS
G6                                    = PASS
G7                                    = CLOSED / PASS

G8_CONDITIONS_01_TO_07                = PASS
G8_CONDITION_08                       = PASS_WITH_LIMITATION
G8_CONDITIONS_09_TO_11                = PASS
G8_CONDITION_12_PRE_TRANSITION        = PASS
G8_CONDITION_12_POST_TRANSITION       = PASS

MOTHER_SHIP_CORE_READY_TRANSITION     = APPROVED_TARGET_ONLY
CORE_READY_TRANSITION                 = APPLIED
NSRC_000004_POST_TRANSITION_ALIGNMENT = PASS
NSRC_000004_CORE_READY                = PASS
COMPLETION_CONTRACT                   = 12/12 SATISFIED
G8_STATUS                             = CLOSED
```

`PASS_WITH_LIMITATION`である#8の既存limitationは本Closureでも保持する。
G8 Closureによって過去のG1〜G7 evidence、historical HOLD、またはMother Ship decisionを再解釈しない。

### 9.6 Closure

```text
NSRC_000004_G8_CLOSURE = PASS
NEXT_GATE              = NONE
STOP                   = TRUE
```

