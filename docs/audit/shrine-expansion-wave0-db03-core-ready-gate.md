# W0-DB03 CORE READY Gate 実測（G8）

## Status

- Batch: `W0-DB03`
- Recorded at: `2026-09-26`
- Gate: `G8 CORE READY Closure`（`docs/knowledge/shrine-expansion-gate-contract.md` §11）
- Original membership: 5社（`wave0-012` / `013` / `014` / `015` / `016`）
- G8 execution subset: 4社（`wave0-012` / `013` / `015` / `016`）
- Excluded: `wave0-014 宮城縣護國神社`（G3 `MODEL_CHANGE_REQUIRED`、G4〜G8 NOT EXECUTED）
- Candidate lifecycle before transition: `IMPORTED`（4社）
- `knowledge_status`: `FACT_READY`（4社、不変）
- Candidate lifecycle after transition: `CORE_READY`（4社）
- CORE_READY transition: `APPLIED_4_OF_4`

```text
W0_DB03_G8_EVIDENCE_GATE          = PASS_4_OF_4
W0_DB03_PRE_TRANSITION_ALIGNMENT  = PASS
W0_DB03_POST_TRANSITION_ALIGNMENT = PASS
W0_DB03_COMPLETION_CONTRACT       = 12/12_PASS_4_OF_4
W0_DB03_CORE_READY                = PASS_4_OF_4
W0_DB03_WAVE0_014                 = NOT_EXECUTED
CANDIDATE_STATUS_TRANSITION       = APPLIED_4_OF_4
```

PRE_TRANSITION 記録時点では4社とも `candidate_status = IMPORTED` であり、本 transition で4社のみを
`CORE_READY` へ同期した。#1〜#11 は Evidence として確定済みであり、#12 は Candidate Master の
Governance state を同期する Synchronization Gate として遷移前後を分けて評価する
（`docs/audit/shrine-expansion-wave0-db01-core-ready-gate.md` と同じ構成）。

---

## 1. Purpose

`docs/audit/shrine-expansion-wave0-data-build-plan.md` の CORE READY Completion Contract 12条件について、
W0-DB03 execution subset 4社の Evidence と Candidate Master の Governance transition を、
repo 内の永続 Audit として固定する。

本書は次を明確に分けて記録する。

| 区分 | 節 |
| --- | --- |
| Upstream Gate evidence（G1〜G7） | §3 |
| Mother Ship による fresh Production read-only evidence（G8） | §4 |
| G7 idempotency evidence | §5 |
| Completion Contract #1〜#11 | §6 |
| #12 PRE_TRANSITION / POST_TRANSITION | §7 |
| Repository governance transition | §8 |

---

## 2. Scope と batch 分割の根拠

### 2.1 対象4社

| candidate_id | canonical identity `(name_jp, address)` | Production `id`（provenance） |
| --- | --- | ---: |
| wave0-012 | 大神神社 / 奈良県桜井市三輪1422 | 119 |
| wave0-013 | 北野天満宮 / 京都府京都市上京区馬喰町 | 120 |
| wave0-015 | 平安神宮 / 京都府京都市左京区岡崎西天王町97 | 121 |
| wave0-016 | 岡田宮 / 福岡県北九州市八幡西区岡田町1-1 | 122 |

Production `id` は `docs/audit/shrine-expansion-wave0-db03-production-import.md` §5.3 の post-write 観測値であり、
identity contract ではない。canonical identity は `(name_jp, address)` である。

### 2.2 4 / 5 で CORE_READY へ遷移する根拠

Data Build Plan は「Batch 5社すべてが Completion Contract を満たした場合のみ Candidate Master を
`CORE_READY` 相当 state へ更新する」と定める一方、同じ節で「1社だけ失敗した場合、成功4社を巻き戻すか
失敗1社を HOLD へ分離するかは Mother Ship へ判断を返す」と定めている。

W0-DB03 ではこの判断が既に下されている。

```text
docs/audit/shrine-expansion-wave0-db03-unified-gate-preflight.md
Mother Ship Decision A
  Original membership = KEEP 5
  Execution subset    = 4 CONTINUE
  Model hold          = 1（wave0-014）
  Replacement         = NONE
  Renumbering         = NONE
```

Unified Gate Contract §1 は Product scope / editorial HOLD の authority を Mother Ship decision record とし、
Wave0 operational flow の authority を Data Build Plan としている。本 G8 は Decision A に従い、
execution subset 4社のみを遷移し、wave0-014 は変更しない。original membership は5社のまま保持する。

---

## 3. Upstream Gate evidence（execution subset 4社）

| Gate | 結果 | 記録 |
| --- | --- | --- |
| G1 Identity | PASS | `shrine-expansion-wave0-db03-unified-gate-preflight.md` |
| G2 Position | PASS | 同上 / `shrine-expansion-wave0-db03-source-packet-freeze.md` |
| G3 Source / Model Fit | PASS（NORMAL_MODEL_FIT） | `shrine-expansion-wave0-db03-unified-gate-preflight.md` |
| G4 Knowledge / Evidence | `W0_DB03_G4_PASS_4_OF_4` | `shrine-expansion-wave0-db03-g4-evidence-preflight.md` |
| G5 Shared Eligibility | `W0_DB03_G5_PASS_4_OF_4` | `shrine-expansion-wave0-db03-g5-recommendation-eligibility.md` |
| G6 Runtime QA | `W0_DB03_G6_PASS_4_OF_4` | `shrine-expansion-wave0-db03-g6-runtime-qa.md` |
| G7 Production Import | `W0_DB03_G7 = PASS_4_OF_4` | `shrine-expansion-wave0-db03-production-import.md`（PR #2994） |

本 Audit はこれらの判定を再解釈・変更しない。

---

## 4. Fresh Production read-only evidence（G8）

Mother Ship がローカル環境から Production へ read-only で実行した結果として提供された値である。
Codex 環境から Production へは接続していない。

```text
execution date = 2026-09-26
develop used   = 25d4263ffdf1c8eaf3354aa5838a6d452a0cd717
G8_TARGETS     = 4
```

### 4.1 Production / Candidate Master reconciliation

| candidate_id | exact | candidate_status | knowledge_status | position | location | goriyaku | tags | deity | history | sources | sourceless |
| --- | ---: | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| wave0-012 大神神社 | 1 | IMPORTED | FACT_READY | True | True | True | True | 1 | 1 | 1 | 0 |
| wave0-013 北野天満宮 | 1 | IMPORTED | FACT_READY | True | True | True | True | 3 | 1 | 1 | 0 |
| wave0-015 平安神宮 | 1 | IMPORTED | FACT_READY | True | True | True | True | 2 | 2 | 1 | 0 |
| wave0-016 岡田宮 | 1 | IMPORTED | FACT_READY | True | True | True | True | 12 | 1 | 1 | 0 |

`candidate_status` / `knowledge_status` は transition 前の Candidate Master 値との突合結果である。

### 4.2 Shared eligibility / candidate path

```text
SOURCE_COUNT     = 117
ELIGIBLE_COUNT   = 103
INELIGIBLE_COUNT = 14
```

| candidate_id | candidate path |
| --- | --- |
| wave0-012 | True |
| wave0-013 | True |
| wave0-015 | True |
| wave0-016 | True |

```text
G8_TARGET_CANDIDATE_PATH = PASS
```

`103 / 117` は観測値としてのみ記録する。W0-DB03 の品質指標ではなく、ineligible 14社の原因分析は本 Audit の scope 外である。

### 4.3 Runtime

QA origin（W0-DB01 / G6 と同一の固定入力。実ユーザー位置でも推薦結果でもない）:

```text
lat = 35.681236
lng = 139.767125
```

| candidate_id | detail | candidate | distance | direction |
| --- | --- | --- | --- | --- |
| wave0-012 大神神社 | True | True | True | 西 |
| wave0-013 北野天満宮 | True | True | True | 西 |
| wave0-015 平安神宮 | True | True | True | 西 |
| wave0-016 岡田宮 | True | True | True | 西 |

---

## 5. G7 idempotency evidence

Idempotency は G7 の Evidence 結果であり、本 G8 のために Production へ再接続して再実行していない。

```text
Knowledge second dry-run:
  source_REUSE_EXISTING = 4
  deity_SKIP_EXISTS     = 18
  history_SKIP_EXISTS   = 5
  CREATE                = 0

Base subset second dry-run:
  created=0 updated=0 skipped=4
  goriyaku_tags updated=0 added_links=0 removed_links=0
```

出典: `docs/audit/shrine-expansion-wave0-db03-production-import.md` §7。

---

## 6. Completion Contract #1〜#11（4社）

| # | 条件 | Evidence | 判定 |
| ---: | --- | --- | --- |
| 1 | Production Shrine が canonical `name_jp + address` で一意 | §4.1 `exact=1`（4/4）。G7 pre-state で `same_name=0` | PASS |
| 2 | 採用 `latitude / longitude` が保存されている | §4.1 `position=True` / `location=True`（4/4） | PASS |
| 3 | Source-backed `ShrineKnowledgeSource` | §4.1 `sources=1`（4/4） | PASS |
| 4 | Fact-ready Deity / History が1件以上 | §4.1 deity / history 件数（4/4）。G7 Production eligibility の usable 件数と一致 | PASS |
| 5 | Fact-ready Source relation / Evidence Gate `usable=True` | §4.1 `sourceless=0`。G7 Production verifier で4社 ELIGIBLE、§4.2 candidate path True | PASS |
| 6 | `Shrine.goriyaku` が承認済みの意味のみ | §4.1 `goriyaku=True`（4/4） | PASS |
| 7 | `goriyaku_tags` が canonical 39 の safe subset | §4.1 `tags=True`（4/4） | PASS |
| 8 | 新規 GoriyakuTag を自動生成しない | G7 post-Base: GoriyakuTag 39 / ids exactly 1..39 / removed_links 0。G7 2回目 dry-run で added_links 0 | PASS |
| 9 | Concierge の shared eligibility / candidate path で読める | §4.2 path=True（4/4） | PASS |
| 10 | Compass distance / direction 計算が可能 | §4.3 distance=True / direction=西（4/4） | PASS |
| 11 | Import 再実行で unexpected CREATE / UPDATE なし | §5（G7 evidence） | PASS |

#8 の根拠は G7 の Production 実測であり、G8 の fresh evidence には GoriyakuTag 総数が含まれていない。
本書は G8 時点での GoriyakuTag 総数の再測定を主張しない。

```text
#1〜#11 = PASS（4 / 4）
```

---

## 7. #12 Candidate Master / Production alignment

### 7.1 本条件の役割

#12 は #1〜#11 と独立した Production Evidence を追加する条件ではない。#1〜#11 で確認された
Production / Runtime readiness を、Candidate Master の Governance state が正しく表現していることを
確認する **Synchronization Gate** である。

### 7.2 PRE_TRANSITION

以下を確認済み（§4.1 と develop@25d4263 の Candidate Master）。

- 4社が `candidate_status = IMPORTED`
- `knowledge_status = FACT_READY`
- `build_batch = W0-DB03`
- `status_reason_code = WAVE0_CORE_READY_CANDIDATE`
- Production Base / Knowledge import 済み状態と整合

```text
W0_DB03_PRE_TRANSITION_ALIGNMENT = PASS
```

### 7.3 POST_TRANSITION 条件

以下をすべて満たした場合のみ PASS とする。

1. execution subset 4社だけが `candidate_status: IMPORTED -> CORE_READY` へ変更されている
2. 4社の `candidate_status` 以外の field が変更されていない
3. `knowledge_status = FACT_READY` が4社すべて保持されている
4. `build_batch = W0-DB03` が4社すべて保持されている
5. identity / official source / coordinates / goriyaku / goriyaku_tags / duplicate_status / status_reason_code /
   discovery provenance が保持されている
6. wave0-014 を含む他の candidate row が変更されていない
7. `candidate_defaults` が変更されていない
8. lifecycle 件数の delta が `IMPORTED -4 / CORE_READY +4 / TOTAL ±0` で、他 status 件数は不変
9. Candidate Master / W0-DB03 tests が PASS する（W0-DB03 original membership 5社を維持）
10. #1〜#11 の Evidence が再解釈・書き換えされていない

### 7.4 POST_TRANSITION 実測（machine-checkable diff verification）

`origin/develop`（`25d4263`）の Candidate Master と本 PR の Candidate Master を JSON として比較した。

```text
CHANGED_IDS = ['wave0-012', 'wave0-013', 'wave0-015', 'wave0-016']
ADDED_IDS = [] REMOVED_IDS = []
  wave0-012 changed_fields=['candidate_status'] IMPORTED->CORE_READY knowledge_status=FACT_READY build_batch=W0-DB03 reason=WAVE0_CORE_READY_CANDIDATE
  wave0-013 changed_fields=['candidate_status'] IMPORTED->CORE_READY knowledge_status=FACT_READY build_batch=W0-DB03 reason=WAVE0_CORE_READY_CANDIDATE
  wave0-015 changed_fields=['candidate_status'] IMPORTED->CORE_READY knowledge_status=FACT_READY build_batch=W0-DB03 reason=WAVE0_CORE_READY_CANDIDATE
  wave0-016 changed_fields=['candidate_status'] IMPORTED->CORE_READY knowledge_status=FACT_READY build_batch=W0-DB03 reason=WAVE0_CORE_READY_CANDIDATE
WAVE0_014_ZERO_DIFF = True
NON_CANDIDATE_TOP_LEVEL_ZERO_DIFF = True
CANDIDATE_DEFAULTS_ZERO_DIFF = True
LIFECYCLE_BEFORE = {'BUILD_READY': 21, 'CORE_READY': 5, 'HOLD': 8, 'IMPORTED': 9, 'REVIEW': 1} TOTAL 44
LIFECYCLE_AFTER  = {'BUILD_READY': 21, 'CORE_READY': 9, 'HOLD': 8, 'IMPORTED': 5, 'REVIEW': 1} TOTAL 44
LIFECYCLE_DELTA  = {'CORE_READY': 4, 'IMPORTED': -4}
BASE_SEED_ZERO_DIFF = True
KNOWLEDGE_SEED_ZERO_DIFF = True
RUNTIME_OR_PRODUCTION_CODE_ZERO_DIFF = True
```

Tests:

```text
Candidate Master / W0-DB01〜03 / eligibility verifier : 94 passed
backend full suite（CI unit job と同じ NoGIS 設定）   : 4012 passed, 12 skipped, 0 failed
makemigrations --check                              : No changes detected
git diff --check                                    : clean
```

POST_TRANSITION 10条件をすべて満たした。

```text
W0_DB03_POST_TRANSITION_ALIGNMENT = PASS
```

**#12 判定: `PRE_TRANSITION PASS / POST_TRANSITION PASS`**

---

## 8. Repository governance transition

`backend/temples/data/shrine_expansion_candidate_master.json` の4行のみ:

| candidate_id | candidate_status | knowledge_status | build_batch | status_reason_code |
| --- | --- | --- | --- | --- |
| wave0-012 | IMPORTED → **CORE_READY** | FACT_READY（不変） | W0-DB03（不変） | WAVE0_CORE_READY_CANDIDATE（不変） |
| wave0-013 | IMPORTED → **CORE_READY** | FACT_READY（不変） | W0-DB03（不変） | WAVE0_CORE_READY_CANDIDATE（不変） |
| wave0-015 | IMPORTED → **CORE_READY** | FACT_READY（不変） | W0-DB03（不変） | WAVE0_CORE_READY_CANDIDATE（不変） |
| wave0-016 | IMPORTED → **CORE_READY** | FACT_READY（不変） | W0-DB03（不変） | WAVE0_CORE_READY_CANDIDATE（不変） |

`build_batch` は lifecycle state ではなく Data Build provenance であるため、`CORE_READY` 遷移でも保持する
（`docs/knowledge/shrine-expansion-candidate-master-contract.md`）。

### wave0-014

```text
wave0-014 宮城縣護國神社
G3 = MODEL_CHANGE_REQUIRED
G4 / G5 / G6 / G7 / G8 = NOT EXECUTED
Candidate Master row = diff 0
```

status / reason code / knowledge_status / hydration field のいずれも付与・変更していない。
W0-DB03 は「4社 CORE_READY / 1社 BUILD_READY」の混在状態となり、original membership は5社のまま保持する。

### Tests で固定した状態

- `test_shrine_expansion_candidate_master.py`: lifecycle 件数（BUILD_READY 21 / IMPORTED 5 / CORE_READY 9 / HOLD 8 / REVIEW 1 / TOTAL 44）と、W0-DB03 の 4社 CORE_READY / wave0-014 BUILD_READY
- `test_wave0_db03_shrine_seed.py`: original membership 5社と discovery provenance、4社の CORE_READY / FACT_READY と Source Packet 由来値の一致、wave0-014 の行全体の不変

---

## 9. Provenance / 限界

```text
PRODUCTION_RECONNECT = NONE（Codex 環境から Production へ接続していない）
PRODUCTION_WRITE     = NONE
G7_RERUN             = NONE
VALUE_COMPLETION     = NONE
```

### 9.1 NOT_RECORDED

| 項目 | 記録 |
| --- | --- |
| G8 read-only 各 command の実行 UTC instant | `NOT_RECORDED` |
| 実行 operator | `NOT_RECORDED` |
| Production DB identifier | `NOT_RECORDED` |

いずれも推測で補完しない。一次 log file は repo 内に保存していない。

### 9.2 Production `id`

`119`〜`122` は G7 post-write 時点の provenance 値であり、identity ではない。identity は `(name_jp, address)`。

---

## 10. Known separate issues（CORE READY を block しない）

- **Full canonical Base Seed Production apply は BLOCKED のまま。** #11 は W0-DB03 subset 4行の idempotency のみを主張する。
- **ineligible 14社**（§4.2）の原因分析は scope 外。
- **Recommendation Reason の tradition 二重 hedge** は PR #2993 で修正済みであり、本 G8 の判定には影響しない。
- **visit_style_tags** は現行 Completion Contract の条件ではなく、W0-DB03 4社について推測・補完していない。

---

## 11. 本 PR が変更していないもの

```text
Production DB                          接続なし / write なし
Base Seed / Knowledge Seed / Knowledge Fact  変更なし
Schema / Migration / Model             変更なし
Ranking / Score / Recommendation mapping / Evidence Gate / Eligibility  変更なし
Compass / Concierge                    変更なし
goriyaku / GoriyakuTag                 変更なし
candidate_defaults / 新規 lifecycle field / 新規 status_reason_code  なし
wave0-014                              変更なし
W0-DB04 以降                            変更なし
```

---

## 12. Final

```text
W0_DB03_G8_EVIDENCE_GATE          = PASS_4_OF_4
W0_DB03_PRE_TRANSITION_ALIGNMENT  = PASS
W0_DB03_POST_TRANSITION_ALIGNMENT = PASS
W0_DB03_COMPLETION_CONTRACT       = 12/12_PASS_4_OF_4
W0_DB03_CORE_READY                = PASS_4_OF_4
W0_DB03_WAVE0_014                 = NOT_EXECUTED
CANDIDATE_STATUS_TRANSITION       = APPLIED_4_OF_4
```

| # | 条件 | 判定（4社） |
| ---: | --- | --- |
| 1 | Production Shrine canonical identity | PASS |
| 2 | latitude / longitude | PASS |
| 3 | Source-backed ShrineKnowledgeSource | PASS |
| 4 | Fact-ready Deity / History | PASS |
| 5 | Fact-ready Source relation / Evidence Gate | PASS |
| 6 | `Shrine.goriyaku` | PASS |
| 7 | `goriyaku_tags` canonical safe subset | PASS |
| 8 | 新規 GoriyakuTag 自動生成なし | PASS |
| 9 | Shared Recommendation Eligibility / candidate path | PASS |
| 10 | Compass distance / direction | PASS |
| 11 | Import idempotency | PASS |
| 12 | Candidate Master / Production alignment | PASS |
