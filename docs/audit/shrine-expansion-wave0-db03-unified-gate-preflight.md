# W0-DB03 Unified Gate Preflight

## Status

- Status: `W0_DB03_BLOCKED_AT_G3_MODEL_FIT`
- Recorded at: `2026-09-25`
- Branch: `audit/w0-db03-unified-gate-preflight`
- Base: `develop@a38e9ebfe9f0da7bfdb6c9ec255710b90cdfe78f`
- Batch: `W0-DB03`
- Scope: 大神神社 / 北野天満宮 / 宮城縣護國神社 / 平安神宮 / 岡田宮
- Production write: なし
- Seed change: なし
- Candidate Master write: なし
- Recommendation / Ranking change: なし
- Schema / Migration change: なし

## 目的

PR #2985 で正本化した
`docs/knowledge/shrine-expansion-gate-contract.md`
を、次のdeterministic 5社Batch `W0-DB03` に初めて実適用する。

Gateを順に実行し、1件でもblocking conditionが出た場合は、
downstream Gateへ推測で進めずSTOPする。

## 対象5社

| candidate_id | Shrine | Candidate Master state |
|---|---|---|
| wave0-012 | 大神神社 | BUILD_READY / W0-DB03 |
| wave0-013 | 北野天満宮 | BUILD_READY / W0-DB03 |
| wave0-014 | 宮城縣護國神社 | BUILD_READY / W0-DB03 |
| wave0-015 | 平安神宮 | BUILD_READY / W0-DB03 |
| wave0-016 | 岡田宮 | BUILD_READY / W0-DB03 |

---

## G0 Discovery / Registry

### Result

`PASS = 5 / 5`

5社すべてCandidate Masterへ登録済みで、
`build_batch = W0-DB03` が固定されている。

Discovery provenanceも既存Registryに保持されている。

### Boundary

G0 PASSはIdentity / Position / Knowledge / Recommendation eligibilityを意味しない。

---

## G1 Identity / Duplicate Gate

### Result

`PASS = 5 / 5`

既存Current DB Duplicate Auditでは5社とも `duplicate_status = NEW`。

現行Official / Authority Source path:

| Shrine | Identity Source | Official / Authority address |
|---|---|---|
| 大神神社 | 大神神社公式 | 奈良県桜井市三輪1422 |
| 北野天満宮 | 北野天満宮公式 | 京都市上京区馬喰町 |
| 宮城縣護國神社 | 神社公式 + 宮城県神社庁 | 宮城県仙台市青葉区川内1番地 |
| 平安神宮 | 平安神宮公式 | 京都市左京区岡崎西天王町97 |
| 岡田宮 | 岡田宮公式 | 福岡県北九州市八幡西区岡田町1-1 |

既存Audit上、同名別社との未解決collisionはない。

### Decision

```text
G1_IDENTITY = PASS
DUPLICATE_AMBIGUITY = 0
```

---

## G2 Position / Navigation Anchor Gate

### Result

`PASS = 5 / 5`

既存Position / Coordinate Auditを現行Position Contractへ接続した。

| Shrine | Existing position result | Gate result |
|---|---|---|
| 大神神社 | PASS_ANCHOR | PASS |
| 北野天満宮 | PASS | PASS |
| 宮城縣護國神社 | PASS_ANCHOR | PASS |
| 平安神宮 | PASS | PASS |
| 岡田宮 | PASS | PASS |

Anchor resolved records:

```text
大神神社
34.528817, 135.852894

宮城縣護國神社
38.252500, 140.855556
```

北野天満宮 / 平安神宮 / 岡田宮についても既存Coordinate Availability Auditで
official identityと対応するposition acquisition pathがPASSしている。

このPreflightではCandidate MasterやBase Seedへのcoordinate writeは行わない。
採用値のfreezeはdownstream Data Buildで行う。

---

## G3 Source + Knowledge Model Fit Gate

### Source Availability

5社すべてでOfficial / Authority Source pathは存在する。

```text
OFFICIAL_SOURCE_PATH = 5 / 5
```

### Model Fit

| Shrine | Deity path | History path | Model Fit |
|---|---|---|---|
| 大神神社 | PASS_DEITY | PASS_HISTORY | `NORMAL_MODEL_FIT` |
| 北野天満宮 | PASS_DEITY | PASS_HISTORY | `NORMAL_MODEL_FIT` |
| 宮城縣護國神社 | `HOLD_DEITY_STRUCTURE` | PASS_HISTORY | `MODEL_CHANGE_REQUIRED` |
| 平安神宮 | PASS_DEITY | PASS_HISTORY | `NORMAL_MODEL_FIT` |
| 岡田宮 | PASS_DEITY | PASS_HISTORY | `NORMAL_MODEL_FIT` |

### Blocking Candidate: 宮城縣護國神社

既存Deity Fact Availability Auditは、この神社のcurrent principal enshrinementを
未記名collective deityとして明示し、`HOLD_DEITY_STRUCTURE`としている。

Repositoryで記録済みのSource表現:

```text
明治維新以降戦歿者の御霊 56,091柱
```

これはSource不足ではない。

問題は現行 `ShrineDeity` が
「1 row = individually attributable named deity」
を前提としており、未記名collectiveを意味損失なく表現する型を持たないことである。

PR #2984 のModel Risk Release Contractおよび
PR #2985 のUnified Gate Contractにより、次の旧経路は現在は禁止される。

```text
Deity structure unresolved
+
usable History Fact exists
->
Recommendation eligibilityへ進む
```

History Factがusableになり得ることは、
Collective Deity Model Riskの解除を意味しない。

したがって:

```text
宮城縣護國神社
G3 = MODEL_CHANGE_REQUIRED
```

と判定する。

本監査はProduct scopeの判断を追加しない。
Repository上の根拠だけから `PRODUCT_DECISION_REQUIRED` へ昇格させない。

---

## Gate Summary

| Gate | 大神 | 北野天満宮 | 宮城縣護國 | 平安神宮 | 岡田宮 |
|---|---|---|---|---|---|
| G0 Registry | PASS | PASS | PASS | PASS | PASS |
| G1 Identity | PASS | PASS | PASS | PASS | PASS |
| G2 Position | PASS | PASS | PASS | PASS | PASS |
| G3 Source | PASS | PASS | PASS | PASS | PASS |
| G3 Model Fit | PASS | PASS | **STOP** | PASS | PASS |
| G4 Evidence | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED |
| G5 Eligibility | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED |
| G6 Runtime QA | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED |
| G7 Production Import | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED |
| G8 CORE READY | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED | NOT EXECUTED |

---

## Why G4-G8 Were Not Executed

Unified Gate Contractでは、upstream blocking causeを下流Gateで迂回しない。

W0-DB03は5社固定Batchとして開始したが、
G3で1社に`MODEL_CHANGE_REQUIRED`が発生した。

この状態で:

- 宮城縣護國神社をHistory-only Seedで通す
- 5社Batchを見た目上維持するため別Candidateを自動補充する
- 4社だけを自動的にProductionへ進める
- Candidate Master status / build_batchを推測で書き換える

ことは本Preflightでは行わない。

Batch handlingはMother Shipの明示判断へ返す。

---

## Mother Ship Decision Boundary

本Auditが確定した事実:

```text
W0-DB03 original members = 5
G0-G2 PASS = 5
G3 Source PASS = 5
G3 Model Fit PASS = 4
G3 MODEL_CHANGE_REQUIRED = 1
blocking candidate = 宮城縣護國神社
```

Mother Shipが決める必要があるのは、
このG3 split後のBatch lifecycleだけである。

本Auditでは:

- 4社Batchへ縮小する
- 別Candidateを補充して5社を維持する
- W0-DB03全体を保留する

のいずれも選択しない。

既存deterministic member setを変更する場合は、
Data Build Plan / Candidate Master / testsへの影響を別PRで記録する。

---

## Files / Data Changed

```text
Production DB                       NONE
backend/temples/data/shrines_seed_clean.json NONE
Knowledge Seed                      NONE
Candidate Master JSON               NONE
Recommendation / Ranking            NONE
Schema / Migration                  NONE
```

変更は本Audit文書のみ。

---

## Final Classification

```text
W0_DB03_BLOCKED_AT_G3_MODEL_FIT
```

Unified Gateは意図どおり、
History FactによるModel Risk bypassを防止した。

W0-DB03はG3 split処理のMother Ship判断が確定するまで、
G4〜G8へ進めない。
