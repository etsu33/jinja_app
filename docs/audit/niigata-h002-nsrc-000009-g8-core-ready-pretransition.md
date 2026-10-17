# nsrc-000009 G8 CORE READY PRE_TRANSITION

## Status

- Candidate: `nsrc-000009` 赤城社（新潟県十日町市伊達乙48番地）
- Recorded at: `2026-10-17`
- Gate: `G8 CORE READY`（PRE_TRANSITION record only）
- Audit base: `develop@16917e4d64adc6c14d122bd25c38793a877a6ea0`（PR #3241 merge）
- G7 Production Import: `CLOSED / PASS`（PR #3240）
- Candidate Master G7 sync: `MERGED`（PR #3241）
- Production write in this G8 audit: `0`

```text
COMPLETION_CONTRACT_PRE_TRANSITION         = 12/12 SATISFIED
G8_CONDITION_08                            = PASS_WITH_LIMITATION
G8_CONDITION_12_POST_TRANSITION            = NOT_EXECUTED
MOTHER_SHIP_CORE_READY_TRANSITION_DECISION = NOT_RECORDED
CORE_READY_TRANSITION                      = NOT_EXECUTED
G8_STATUS                                  = OPEN
```

本書はG8 Completion Contract #1〜#12 のPRE_TRANSITION evidenceだけを記録する。
CORE_READY transitionは実行しない。Mother Ship判断は未記録であり、Candidate Master / Production DB / Seed / lifecycle dataを変更しない。

---

## 1. Authority

- `docs/knowledge/shrine-expansion-gate-contract.md` §11
- `docs/audit/shrine-expansion-wave0-data-build-plan.md` CORE READY Completion Contract
- `docs/knowledge/shrine-expansion-candidate-master-contract.md` schema 1.4 Nationwide Source Track Boundary
- `docs/audit/niigata-h002-nsrc-000009-g7-production-import-preflight.md`
- `backend/temples/data/shrine_expansion_candidate_master.json`

```text
IMPORTED   != CORE_READY
FACT_READY != CORE_READY
```

---

## 2. Scope

対象は1件だけ。

```text
candidate_id = nsrc-000009
name_jp      = 赤城社
address      = 新潟県十日町市伊達乙48番地
```

同じ H002 の他Candidateはscope外。

```text
nsrc-000006 赤井神社
nsrc-000007 赤城社 / 十日町市四日町2534番地
nsrc-000008 赤城社 / 十日町市上組2059番地子
nsrc-000010 赤城社 / 南魚沼市芹田79番地
```

同名を理由に統合・連動遷移しない。

---

## 3. Upstream Gate lineage

| Gate | Result | Evidence |
| --- | --- | --- |
| G1 Identity / Duplicate | PASS / SAME_NAME_DIFFERENT_SHRINE | `docs/audit/niigata-h002-nsrc-000009-g1-identity-duplicate.md` |
| G2 Position / Navigation Anchor | PASS | `docs/audit/shrine-position/niigata-h002-nsrc-000009-akagi-sha-position-review.md` |
| G3 Source + Knowledge Model Fit | PASS / NORMAL_MODEL_FIT | `docs/audit/niigata-h002-nsrc-000009-g3-source-knowledge-fit.md` |
| G4 Knowledge Fact + Evidence | PASS | `docs/audit/niigata-h002-nsrc-000009-g4-formal-pass.md` |
| G5 Shared Recommendation Eligibility | PASS / ELIGIBLE | `docs/audit/niigata-h002-nsrc-000009-g5-recommendation-eligibility.md` |
| G6 Runtime QA | PASS | `docs/audit/niigata-h002-nsrc-000009-g6-runtime-qa.md` |
| G7 Production Import | CLOSED / PASS | `docs/audit/niigata-h002-nsrc-000009-g7-production-import-preflight.md` |

G7途中の historical HOLD / NOT_EXECUTED は履歴として保持する。
後続の正式PASS / Closureがcurrent stateであり、過去記録を書き換えない。

---

## 4. Evidence source boundary

| 区分 | 内容 |
| --- | --- |
| G7 Production実測 | post-Base guard / post-Knowledge verification / aggregate / target integrity / citation / idempotency / Production Runtime QA |
| G8 fresh Production read-only | Condition #8 GoriyakuTag master current-state（2026-10-17） |
| repository current state | PR #3241 merge後の Candidate Master |
| G2/G3/G4/G5/G6 | 各current audit / test record |

G8 fresh read-onlyはSELECT-only wrapper（`readonly_query.sh`）で実行され、Production writeは0。
本書作成時に追加のProduction queryは実行していない。

---

## 5. Completion Contract #1〜#12

### #1 Production Shrine canonical identity

G7 post-Knowledge verification:

```text
target_shrine = 1
name_jp       = 赤城社
address       = 新潟県十日町市伊達乙48番地
```

同名別住所の赤城社（nsrc-000007 / nsrc-000008 / nsrc-000010）は別identityとして扱う。
Production numeric Shrine id はpoint-in-time provenanceであり、canonical identityは exact (name_jp, address)。

```text
G8_CONDITION_01_CANONICAL_IDENTITY = PASS
```

### #2 Adopted coordinate

G2 adopted Visitor / Navigation Anchor:

```text
latitude  = 37.089683
longitude = 138.748108
```

G7 guard / verificationおよびProduction Runtime QAが同座標を使用してPASS。

```text
G8_CONDITION_02_ADOPTED_COORDINATE = PASS
```

### #3 Source-backed ShrineKnowledgeSource

Production Knowledge importでは既存Sourceをimporter semantic identity（source_type + normalized URL）で再利用した（source_REUSE_EXISTING = 1、sources created = 0）。

Shared accepted Source:

```text
source_type  = government
publisher    = 十日町市
title        = 歴史文化基本構想 資料集
url          = https://www.city.tokamachi.lg.jp/material/files/group/31/rekibun_shiryou.pdf
bibliography = 中魚沼郡誌上 p.398
```

`bibliography = 中魚沼郡誌上 p.398` はnsrc-000007由来のlegacy Source metadataであり、書き換えていない。
Production Source idはcanonical identityとして扱わない。

```text
G8_CONDITION_03_SOURCE_BACKED_KNOWLEDGE_SOURCE = PASS
```

### #4 Fact-ready Deity / History

Production target:

```text
target_deity   = 0
target_history = 2
```

採用History:

```text
H1 historical_event / 天明3年8月の創立記録 / period_text=天明3年8月
H2 historical_event / 大正2年の改築記録     / period_text=大正2年
```

`大山祇命` はhistorical deity evidenceのままであり、current ShrineDeityへ昇格させない。
History-only KnowledgeはG5 contract上許容される。

```text
G8_CONDITION_04_FACT_READY_KNOWLEDGE = PASS
```

### #5 Fact-ready Source relation / Evidence Gate

Production target integrity:

```text
history_source_relations = 2
sourceless_history       = 0
target_source_fact       = 0

H1 -> shared government Source only
H2 -> shared government Source only
```

Fact locator（ShrineFactSourceCitation）:

```text
H1 citation locator = 中魚沼郡誌上 p.445
H2 citation locator = 中魚沼郡誌上 p.445
```

G5では usable History = 2 / usable Deity = 0。

```text
G8_CONDITION_05_FACT_SOURCE_RELATION = PASS
G8_CONDITION_05_EVIDENCE_USABLE      = PASS
```

### #6 Shrine.goriyaku approved-only

G7 Production verification:

```text
Shrine.goriyaku = ""
```

History / Sourceから未承認のご利益意味を生成していない。

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

2026-10-17 G8 fresh Production read-only（Mother Ship）:

Query: `scripts/migration_safety/sql/nsrc_000009_g8_goriyaku_tag_master.sql`

```text
goriyaku_tag_total        = 39
goriyaku_tag_min_id       = 1
goriyaku_tag_max_id       = 39
goriyaku_tag_distinct_ids = 39
```

Queryはrepository read-only safety guardをPASSし、`readonly_query.sh` 経由で実行された。Production write = 0。

G7ではtarget goriyaku delta = 0、Knowledge importerはGoriyakuTag / ShrineGoriyakuAssignmentを作成対象に持たず、
post-Knowledge verificationでもtarget link / assignment = 0。

Limitation:
G7 applyの直前・直後にGoriyakuTag master countを独立計測した記録はないため、
G7実行中の一時的CREATE/DELETEが絶対になかったことを時系列実測だけで証明したとは扱わない。
このlimitationはnsrc-000006 / nsrc-000007 G8 precedentと同様に保持する。

```text
G8_CONDITION_08_NO_NEW_GORIYAKU_TAG = PASS_WITH_LIMITATION
```

### #9 Concierge shared eligibility / candidate path

G7 Production Runtime QA:

```text
CONCIERGE_CANDIDATE_PATH=PASS
RECOMMENDATION_REASON=PASS
G7_PRODUCTION_RUNTIME_QA=PASS
TRANSACTION_MODE=READ_ONLY
```

targetはshared candidate pathに参加でき、History 2 / Deity 0 / goriyaku tags 0。
Top1はAcceptance Criteriaではない。

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

G2 adopted coordinateを使用。

```text
G8_CONDITION_10_COMPASS_DISTANCE  = PASS
G8_CONDITION_10_COMPASS_DIRECTION = PASS
```

### #11 Re-import idempotency

Knowledge second dry-run:

```text
source_REUSE_EXISTING = 1
history_SKIP_EXISTS   = 2
citation_SKIP_EXISTS  = 2
CREATE                = 0
```

Base second target-only dry-run:

```text
done created=0 updated=0 skipped=1 total_seed=1
```

```text
G8_CONDITION_11_REIMPORT_IDEMPOTENCY = PASS
```

### #12 Candidate Master / Production PRE_TRANSITION alignment

PR #3241でG7 Production stateへ同期済み。

Current Candidate Master:

```text
candidate_id           = nsrc-000009
candidate_status       = IMPORTED
status_reason_code     = PRODUCTION_IMPORT_COMPLETE
official_source_status = CONFIRMED
knowledge_status       = FACT_READY
identity_status        = CONFIRMED
duplicate_status       = SAME_NAME_DIFFERENT_SHRINE
build_batch            = null
wave_id                = null
candidate_reason       = official_source_full_enumeration_candidate
```

immutable admission provenance:

```text
track                  = nationwide_source_candidate
prefecture             = 新潟県
source_batch_id        = NIIGATA-001
handoff_id             = NIIGATA-001-H002
source_position        = page001-row009
source_snapshot_sha256 = f54022303700821672ee4ee65e9967a7e8f343715a66ad987cc0b43530850380
source_url             = https://niigata-jinjacho.jp/shrine_niigata/search.php
source_verified_at     = 2026-10-08
captured_at            = 2026-10-08T14:27:00+09:00
```

ProductionはG7 CLOSED / PASS、Candidate Masterは `IMPORTED / CONFIRMED / FACT_READY`。
Source batch / handoffを `build_batch` へ推論せずnullを維持する。

```text
G8_CONDITION_12_PRE_TRANSITION_ALIGNMENT  = PASS
G8_CONDITION_12_POST_TRANSITION_ALIGNMENT = NOT_EXECUTED
```

---

## 6. Completion Contract summary

| # | Condition | Result |
| ---: | --- | --- |
| 1 | Production canonical identity | PASS |
| 2 | adopted latitude / longitude | PASS |
| 3 | Source-backed ShrineKnowledgeSource | PASS |
| 4 | Fact-ready Deity / History（Deity 0 / History 2） | PASS |
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

## 7. Mother Ship Decision Gate（unresolved）

```text
MOTHER_SHIP_CORE_READY_TRANSITION_DECISION = NOT_RECORDED
TARGET                                     = nsrc-000009
```

Mother Ship判断はまだ記録されていない。本書はtransitionを承認しない。

将来検討され得るtarget-only deltaは次の2fieldだけ（本書では適用しない）。

```text
candidate_status:
IMPORTED -> CORE_READY

status_reason_code:
PRODUCTION_IMPORT_COMPLETE -> CORE_READY_CONTRACT_PASS
```

不変であるべきfield:

```text
official_source_status = CONFIRMED
knowledge_status       = FACT_READY
identity_status        = CONFIRMED
duplicate_status       = SAME_NAME_DIFFERENT_SHRINE
build_batch            = null
wave_id                = null
candidate_reason       = official_source_full_enumeration_candidate
admission_provenance   = unchanged
```

いかなる場合も禁止:

- Production DB write
- Base Seed / Knowledge Seed変更
- G1〜G7 audit rewrite
- Ranking / Score / Recommendation / Concierge / Compass / Position変更
- GoriyakuTag変更
- nsrc-000006 / 000007 / 000008 / 000010 のlifecycle変更
- Historical Wave0変更
- build_batch捏造
- transition前にG8 CLOSEDを宣言

---

## 8. Required POST_TRANSITION verification

Mother Shipがtarget-only transitionを承認し、transition PRがmergeされた後にだけ次を確認する。

1. `candidate_status == CORE_READY`
2. `status_reason_code == CORE_READY_CONTRACT_PASS`
3. `knowledge_status == FACT_READY`
4. `official_source_status == CONFIRMED`
5. `build_batch == null`
6. admission provenance完全一致
7. identity / duplicate evidence完全一致
8. 他H002 4候補に差分なし
9. 既存CORE_READY Candidateに差分なし
10. Historical Wave0 accounting不変
11. Candidate Master tests / relevant consumers PASS
12. Completion Contract #1〜#11 evidenceに後退なし

全てPASSした後だけ:

```text
NSRC_000009_POST_TRANSITION_ALIGNMENT = PASS
NSRC_000009_CORE_READY                = PASS
G8_STATUS                             = CLOSED
```

---

## 9. Final PRE_TRANSITION classification

```text
G1                                    = PASS / SAME_NAME_DIFFERENT_SHRINE
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
G8_BLOCKER                            = NONE

MOTHER_SHIP_CORE_READY_TRANSITION_DECISION = NOT_RECORDED
CORE_READY_TRANSITION                      = NOT_EXECUTED
G8_STATUS                                  = OPEN
```

```text
IMPORTED   != CORE_READY
FACT_READY != CORE_READY
```

Next action is the Mother Ship CORE_READY transition decision. G8 remains OPEN until a target-only transition is approved, applied, and POST_TRANSITION verification passes.
