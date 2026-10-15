# nsrc-000006 G8 CORE READY PRE_TRANSITION

## Status

- Candidate: `nsrc-000006` 赤井神社（新潟県佐渡市加茂歌代2662番地）
- Recorded at: `2026-10-15`
- Gate: `G8 CORE READY`（PRE_TRANSITION）
- Audit base: `develop@a1245f73a874e3ff51c943b59a426681e109ec5b`（PR #3217 merge）
- G7 Production Import: `CLOSED / PASS`（PR #3216）
- Candidate Master G7 sync: `MERGED`（PR #3217）
- Production write in this G8 audit: `0`

```text
G8_CONDITIONS_01_TO_07                = PASS
G8_CONDITION_08                       = PASS_WITH_LIMITATION
G8_CONDITIONS_09_TO_11                = PASS
G8_CONDITION_12_PRE_TRANSITION        = PASS
G8_CONDITION_12_POST_TRANSITION       = PASS

COMPLETION_CONTRACT_PRE_TRANSITION    = 12/12 SATISFIED
MOTHER_SHIP_CORE_READY_TRANSITION     = APPROVED_TARGET_ONLY
CORE_READY_TRANSITION                 = APPLIED
G8_STATUS                             = CLOSED
```

本書は `nsrc-000006` の G8 PRE_TRANSITION evidence を current state で再構成する。
G7 PASS や Candidate Master の IMPORTED state を理由に CORE_READY を推論しない。
Condition #8 の fresh Production read-onlyも完了し、PRE_TRANSITION 12/12を満たした。

---

## 1. Authority

- `docs/knowledge/shrine-expansion-gate-contract.md` §11 / §18
- `docs/audit/shrine-expansion-wave0-data-build-plan.md` CORE READY Completion Contract
- `docs/knowledge/shrine-expansion-candidate-master-contract.md` schema 1.4 Nationwide Source Track Boundary
- `docs/audit/niigata-h002-nsrc-000006-g1-identity-duplicate.md`
- `docs/audit/shrine-position/niigata-h002-akai-jinja-position-resolution.md`
- `docs/audit/niigata-h002-nsrc-000006-g3-source-knowledge-fit.md`
- `docs/audit/niigata-h002-nsrc-000006-g4-knowledge-materialization.md`
- `docs/audit/niigata-h002-nsrc-000006-g5-recommendation-eligibility.md`
- `docs/audit/niigata-h002-nsrc-000006-g6-runtime-qa.md`
- `docs/audit/niigata-h002-nsrc-000006-g7-production-import-preflight.md`
- `backend/temples/data/shrine_expansion_candidate_master.json`

```text
IMPORTED   != CORE_READY
FACT_READY != CORE_READY
```

---

## 2. Scope

対象は1件だけ。

```text
candidate_id = nsrc-000006
name_jp      = 赤井神社
address      = 新潟県佐渡市加茂歌代2662番地
```

同じ H002 の他Candidateはscope外。

```text
nsrc-000007 赤城社 = CORE_READY（既存）
nsrc-000008 赤城社 = DISCOVERED
nsrc-000009 赤城社 = DISCOVERED
nsrc-000010 赤城社 = DISCOVERED
```

同名・近似住所を理由にidentityやlifecycleを連動させない。

---

## 3. Upstream Gate lineage

| Gate | Result | Evidence |
| --- | --- | --- |
| G1 Identity / Duplicate | PASS / NEW | `docs/audit/niigata-h002-nsrc-000006-g1-identity-duplicate.md` |
| G2 Position / Navigation Anchor | PASS | `docs/audit/shrine-position/niigata-h002-akai-jinja-position-resolution.md` |
| G3 Source + Knowledge Model Fit | PASS / NORMAL_MODEL_FIT | `docs/audit/niigata-h002-nsrc-000006-g3-source-knowledge-fit.md` |
| G4 Knowledge Fact + Evidence | PASS | `docs/audit/niigata-h002-nsrc-000006-g4-knowledge-materialization.md` |
| G5 Shared Recommendation Eligibility | PASS / ELIGIBLE | `docs/audit/niigata-h002-nsrc-000006-g5-recommendation-eligibility.md` |
| G6 Runtime QA | PASS | `docs/audit/niigata-h002-nsrc-000006-g6-runtime-qa.md` |
| G7 Production Import | CLOSED / PASS | `docs/audit/niigata-h002-nsrc-000006-g7-production-import-preflight.md` |

---

## 4. Completion Contract #1〜#12

### #1 Production canonical identity

G7 post-Knowledge verification:

```text
target_shrine = 1
name_jp       = 赤井神社
address       = 新潟県佐渡市加茂歌代2662番地
```

```text
G8_CONDITION_01_CANONICAL_IDENTITY = PASS
```

### #2 Adopted coordinate

G2 adopted Visitor / Navigation Anchor:

```text
latitude  = 38.085938
longitude = 138.418312
```

G7 guard / verification / Production Runtime QAが同座標を使用してPASS。

```text
G8_CONDITION_02_ADOPTED_COORDINATE = PASS
```

### #3 Source-backed ShrineKnowledgeSource

G7 Production Knowledge importで2 Sourceを確定。

```text
S2 tourism_official
   佐渡芸能アーカイブ / 加茂歌代まつりの鬼太鼓
   https://sado-geinou.com/geinou/kamoutashiro/

S3 local_history
   新潟県神職会佐渡支部 / 佐渡神社誌
   https://dl.ndl.go.jp/pid/971197
```

```text
G8_CONDITION_03_SOURCE_BACKED_KNOWLEDGE_SOURCE = PASS
```

### #4 Fact-ready Deity / History

Production target:

```text
target_deity   = 0
target_history = 3
```

採用History:

```text
H1 regional_context / 4月16日の赤井神社例祭と鬼太鼓奉納
H2 tradition        / 元日午前0時の鬼太鼓奉納
H3 regional_context / 加茂の五神社としての記録
```

current Deity は Source-backed にfreezeされていないため0件のまま維持する。

```text
G8_CONDITION_04_FACT_READY_KNOWLEDGE = PASS
```

### #5 Fact-ready Source relation / Evidence Gate

Production target integrity:

```text
history_source_relations = 3
sourceless_history       = 0
target_source_fact       = 0

H1 -> S2 only
H2 -> S2 only
H3 -> S3 only
```

G4/G5では usable History = 3 / usable Deity = 0。

```text
G8_CONDITION_05_FACT_SOURCE_RELATION = PASS
G8_CONDITION_05_EVIDENCE_USABLE      = PASS
```

### #6 Shrine.goriyaku approved-only

G7 Production verification:

```text
Shrine.goriyaku = ""
```

鬼太鼓・祭礼・地域史から未承認のご利益意味を生成していない。

```text
G8_CONDITION_06_GORIYAKU_APPROVED_ONLY = PASS
```

### #7 goriyaku_tags canonical safe subset

Production target:

```text
target_goriyaku_tag_links   = 0
target_goriyaku_assignments = 0
```

approved setは空集合。

```text
[] subset_of canonical 39
G8_CONDITION_07_GORIYAKU_TAG_SAFE_SUBSET = PASS
```

### #8 No automatic GoriyakuTag creation

G7 execution evidence:

```text
Base import:
goriyaku_tags rows=0 updated=0 added_links=0 removed_links=0

post-Knowledge:
target_goriyaku_tag_links   = 0
target_goriyaku_assignments = 0
```

Knowledge importerは本targetの GoriyakuTag / ShrineGoriyakuAssignment を作成していない。
ただし、先行G8と同じ受入基準では G8 時点の canonical GoriyakuTag master current-state を fresh Production read-only で確認する。

Required query:

```text
scripts/migration_safety/sql/nsrc_000006_g8_goriyaku_tag_master.sql
```

Expected canonical state:

```text
goriyaku_tag_total        = 39
goriyaku_tag_min_id       = 1
goriyaku_tag_max_id       = 39
goriyaku_tag_distinct_ids = 39
```

2026-10-15 Mother Ship端末からSELECT-only wrapperでfresh Production read-onlyを実行し、次を実測した。

```text
goriyaku_tag_total        = 39
goriyaku_tag_min_id       = 1
goriyaku_tag_max_id       = 39
goriyaku_tag_distinct_ids = 39
```

`readonly_query.sh` は SQL read-only check を通過し、Production write は0。

Limitation:
G7 apply直前・直後のGoriyakuTag master countを独立計測した記録はないため、
G7実行中の一時的CREATE/DELETEが絶対になかったことを時系列実測だけで証明したとは扱わない。
先行G8 precedentと同じく、このlimitationは保持する。

```text
G8_CONDITION_08_NO_NEW_GORIYAKU_TAG = PASS_WITH_LIMITATION
```

### #9 Concierge shared eligibility / candidate path

G7 Production Runtime QA:

```text
SHARED_RECOMMENDATION_ELIGIBILITY=PASS
CONCIERGE_CANDIDATE_PATH=PASS
RECOMMENDATION_REASON=PASS
G7_PRODUCTION_RUNTIME_QA=PASS
TRANSACTION_MODE=READ_ONLY
```

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

```text
G8_CONDITION_10_COMPASS_DISTANCE  = PASS
G8_CONDITION_10_COMPASS_DIRECTION = PASS
```

### #11 Re-import idempotency

Knowledge second dry-run:

```text
source_REUSE_EXISTING = 2
history_SKIP_EXISTS   = 3
CREATE                = 0
```

Base second target-only dry-run:

```text
SKIP id=129 赤井神社
done created=0 updated=0 skipped=1 total_seed=1
```

```text
G8_CONDITION_11_REIMPORT_IDEMPOTENCY = PASS
```

### #12 Candidate Master / Production PRE_TRANSITION alignment

PR #3217 merge後の current Candidate Master:

```text
candidate_id           = nsrc-000006
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

Immutable admission provenance:

```text
track                  = nationwide_source_candidate
prefecture             = 新潟県
source_batch_id        = NIIGATA-001
handoff_id             = NIIGATA-001-H002
source_position        = page001-row006
source_snapshot_sha256 = f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380
source_url             = https://niigata-jinjacho.jp/shrine_niigata/search.php
source_verified_at     = 2026-10-08
captured_at            = 2026-10-08T14:27:00+09:00
```

ProductionはG7 CLOSED / PASS、Candidate Masterは `IMPORTED / CONFIRMED / FACT_READY`。
G1 authorityどおり `duplicate_status=NEW` を保持する。
Source batch / handoffを `build_batch` へ推論しない。

```text
G8_CONDITION_12_PRE_TRANSITION_ALIGNMENT  = PASS
G8_CONDITION_12_POST_TRANSITION_ALIGNMENT = PASS
```

---

## 5. Completion Contract summary

| # | Condition | Result |
| ---: | --- | --- |
| 1 | Production canonical identity | PASS |
| 2 | adopted latitude / longitude | PASS |
| 3 | Source-backed ShrineKnowledgeSource | PASS |
| 4 | Fact-ready Deity / History（Deity 0 / History 3） | PASS |
| 5 | Fact-ready Source relation / Evidence Gate | PASS |
| 6 | Shrine.goriyaku approved-only | PASS |
| 7 | goriyaku_tags canonical safe subset | PASS |
| 8 | no automatic GoriyakuTag creation | **PASS_WITH_LIMITATION** |
| 9 | Concierge shared eligibility / candidate path | PASS |
| 10 | Compass distance / direction | PASS |
| 11 | re-import idempotency | PASS |
| 12 | Candidate Master / Production PRE_TRANSITION alignment | PASS |

```text
COMPLETION_CONTRACT_PRE_TRANSITION = 12/12 SATISFIED
G8_BLOCKER                         = NONE
```

---

## 6. Mother Ship Decision Gate

Completion Contract PRE_TRANSITIONは12/12 satisfied。CORE_READY transitionの技術入力は揃った。

```text
MOTHER_SHIP_CORE_READY_TRANSITION_DECISION = APPROVED_TARGET_ONLY
TARGET                                     = nsrc-000006
CORE_READY_TRANSITION                      = APPLIED
G8_STATUS                                  = CLOSED
```

Mother Shipが判断できるtarget-only deltaは次の2fieldだけ。

```text
candidate_status:
IMPORTED -> CORE_READY

status_reason_code:
PRODUCTION_IMPORT_COMPLETE -> CORE_READY_CONTRACT_PASS
```

不変:

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

禁止:

- Production DB write
- Base Seed / Knowledge Seed変更
- G1〜G7 audit rewrite
- Ranking / Score / Recommendation / Compass変更
- GoriyakuTag変更
- nsrc-000007 / 000008 / 000009 / 000010 のlifecycle変更
- Historical Wave0変更
- build_batch捏造
- PRE_TRANSITION監査PR内でCORE_READY transitionを実行すること

---

## 7. Required POST_TRANSITION verification

Mother Shipがtarget-only transitionを明示承認し、transition PRがmergeされた後に確認する。

1. `candidate_status == CORE_READY`
2. `status_reason_code == CORE_READY_CONTRACT_PASS`
3. `knowledge_status == FACT_READY`
4. `official_source_status == CONFIRMED`
5. `build_batch == null`
6. admission provenance完全一致
7. identity / duplicate evidence完全一致（`CONFIRMED / NEW`）
8. 他H002 4候補に差分なし
9. nsrc-000002 / nsrc-000004 / nsrc-000007 CORE_READY stateに差分なし
10. Historical Wave0 accounting不変
11. Candidate Master tests / relevant consumers PASS
12. Completion Contract #1〜#11 evidenceに後退なし

全てPASSした後だけG8 Closureを宣言する。

---

## 8. Current classification

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
G8_CONDITION_12_POST_TRANSITION       = PASS

COMPLETION_CONTRACT_PRE_TRANSITION    = 12/12 SATISFIED
MOTHER_SHIP_CORE_READY_TRANSITION     = APPROVED_TARGET_ONLY
CORE_READY_TRANSITION                 = APPLIED
G8_STATUS                             = CLOSED
STOP                                  = TRUE
```


## 9. Mother Ship decision / CORE_READY transition

Mother Ship explicitly approved the target-only transition:

```text
MOTHER_SHIP_CORE_READY_TRANSITION_DECISION = APPROVED_TARGET_ONLY
TARGET                                     = nsrc-000006
```

Applied by PR #3220.

```text
transition branch = feature/nsrc-000006-g8-core-ready-transition
merge commit      = 7ed6587bc62759ce1c8006312888b4a1cd1b5f09

candidate_status:
IMPORTED -> CORE_READY

status_reason_code:
PRODUCTION_IMPORT_COMPLETE -> CORE_READY_CONTRACT_PASS
```

The transition changed no Production DB state and did not modify Base Seed, Knowledge Seed,
Recommendation, Ranking, Compass, GoriyakuTag, Position, or G1-G7 evidence.

---

## 10. POST_TRANSITION verification / G8 Closure

### 10.1 Current target state

Current `develop` after PR #3220:

```text
candidate_id           = nsrc-000006
candidate_status       = CORE_READY
status_reason_code     = CORE_READY_CONTRACT_PASS
official_source_status = CONFIRMED
knowledge_status       = FACT_READY
identity_status        = CONFIRMED
duplicate_status       = NEW
build_batch            = null
wave_id                = null
candidate_reason       = official_source_full_enumeration_candidate
```

### 10.2 Required POST_TRANSITION verification result

| # | Verification | Result | Evidence |
| ---: | --- | --- | --- |
| 1 | `candidate_status == CORE_READY` | PASS | current develop Candidate Master |
| 2 | `status_reason_code == CORE_READY_CONTRACT_PASS` | PASS | current develop Candidate Master |
| 3 | `knowledge_status == FACT_READY` | PASS | unchanged across transition |
| 4 | `official_source_status == CONFIRMED` | PASS | unchanged across transition |
| 5 | `build_batch == null` | PASS | Nationwide Source Track boundary preserved |
| 6 | admission provenance完全一致 | PASS | before/after equality |
| 7 | identity / duplicate evidence完全一致 | PASS | `CONFIRMED / NEW` preserved |
| 8 | 他H002 4候補に差分なし | PASS | nsrc-000007 / 000008 / 000009 / 000010 unchanged |
| 9 | 既存CORE_READY候補に差分なし | PASS | nsrc-000002 / 000004 / 000007 unchanged |
| 10 | Historical Wave0 accounting不変 | PASS | Candidate Master changed IDs = `[nsrc-000006]` only |
| 11 | Candidate Master tests / relevant consumers PASS | PASS | PR #3220 backend-pr / dependency-review / CodeQL success |
| 12 | Completion Contract #1〜#11 evidenceに後退なし | PASS | transition touched lifecycle governance only; Production / Knowledge / Runtime evidence unchanged |

### 10.3 Minimal-diff result

PRE_TRANSITION base:

```text
develop@84a412458409a244bd70c69b4384bf3ed442ac90
```

POST_TRANSITION:

```text
develop@7ed6587bc62759ce1c8006312888b4a1cd1b5f09
```

Observed Candidate Master diff:

```text
changed Candidate IDs = [nsrc-000006]

candidate_status:
IMPORTED -> CORE_READY

status_reason_code:
PRODUCTION_IMPORT_COMPLETE -> CORE_READY_CONTRACT_PASS
```

No other target field changed.

```text
admission_provenance   = unchanged
official_source_status = CONFIRMED
knowledge_status       = FACT_READY
identity_status        = CONFIRMED
duplicate_status       = NEW
build_batch            = null
wave_id                = null
candidate_reason       = unchanged
```

Other tracked candidates:

```text
nsrc-000007 = CORE_READY / unchanged
nsrc-000008 = DISCOVERED / unchanged
nsrc-000009 = DISCOVERED / unchanged
nsrc-000010 = DISCOVERED / unchanged
nsrc-000002 = CORE_READY / unchanged
nsrc-000004 = CORE_READY / unchanged
```

### 10.4 Final G8 classification

Completion Contract #1〜#11 retains the PRE_TRANSITION result.
Condition #12 now has both PRE_TRANSITION and POST_TRANSITION alignment PASS.

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
G8_CONDITION_12_POST_TRANSITION       = PASS

COMPLETION_CONTRACT_PRE_TRANSITION    = 12/12 SATISFIED
MOTHER_SHIP_CORE_READY_TRANSITION     = APPROVED_TARGET_ONLY
CORE_READY_TRANSITION                 = APPLIED

NSRC_000006_POST_TRANSITION_ALIGNMENT = PASS
NSRC_000006_CORE_READY                = PASS
G8_STATUS                             = CLOSED
G8_RESULT                             = PASS
FORMAL_G8                             = PASS
```

The Condition #8 limitation remains part of the final audit record.
It does not downgrade current-state CORE_READY because the accepted G8 precedent uses the same
`PASS_WITH_LIMITATION` classification.

No further G8 transition write is authorized after closure.
