# W0-DB03 Unified Gate Preflight

## Status

- Status: `W0_DB03_SPLIT_DECISION_A_4_CONTINUE_1_MODEL_HOLD`
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

## Why G4-G8 Were Not Executed Yet

Unified Gate Contractでは、upstream blocking causeを下流Gateで迂回しない。

W0-DB03は5社固定Batchとして開始し、
G3で宮城縣護國神社のみ `MODEL_CHANGE_REQUIRED` となった。

Mother Shipは後述のDecision Aを確定したため、
次工程では4社だけをexecution subsetとしてG4へ進める。

ただし本PRはG0〜G3 PreflightとMother Ship Decision記録までをscopeとし、
G4〜G8の実処理自体はまだ実行しない。

禁止事項は維持する。

- 宮城縣護國神社をHistory-only Seedで通さない
- 別Candidateを補充して5社へ戻さない
- W0-DB04以降をrenumberしない
- Candidate Master status / build_batchを推測で書き換えない

---

## Mother Ship Decision

Mother Ship Decision:

```text
Decision = A

Original membership = KEEP 5
Execution subset    = 4 CONTINUE
Model hold          = 1
Replacement         = NONE
Renumbering         = NONE
```

### Continue to G4

```text
大神神社
北野天満宮
平安神宮
岡田宮
```

### Isolate at G3

```text
宮城縣護國神社
MODEL_CHANGE_REQUIRED
```

W0-DB03のoriginal deterministic membershipは5社のまま監査履歴として保持する。

一方、downstream executionでは問題の所有者だけを隔離し、
PASS済み4社を止めない。

このDecisionではCandidate Masterの`build_batch`やstatusをこのPRで変更しない。
Gate-level HOLDは本Auditで追跡し、Candidate Master contractへ新しいfieldやreason codeを
推測追加しない。

別Candidateの補充およびW0-DB04以降のrenumberは行わない。

これにより:

```text
deterministic history = KEEP
gate independence     = KEEP
blast radius          = 1 shrine
```

を同時に維持する。

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
W0_DB03_SPLIT_DECISION_A_4_CONTINUE_1_MODEL_HOLD
```

Unified Gateは意図どおり、
History FactによるModel Risk bypassを防止した。

次工程では:

```text
4 shrines -> G4 Knowledge Fact + Evidence
1 shrine  -> dedicated Model Risk track
```

として進める。
