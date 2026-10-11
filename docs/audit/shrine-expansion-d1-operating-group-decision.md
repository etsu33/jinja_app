# Shrine Expansion D-1 Operating Group Decision

> **Status: D-1 MOTHER_SHIP_DECISION = CLOSED**
>
> Recorded at: 2026-10-11
>
> Base: `develop@9828f29ca37c0bbf8d796dbeecb9e24cbd9a09c3`（PR #3165 merge）
>
> Scope: 10社単位の運用グルーピング（Operating Group）の扱いを確定する。
>
> Candidate Master mutation: 0
> Seed mutation: 0
> Production write: 0
> Runtime change: 0
> Contract text change: 0

## 1. Decision

```text
D-1 = OPTION_A_ACCEPTED
```

10社の **Operating Group** は運用上のグルーピングだけである。
新しい Data Build Batch ではなく、既存の凍結済み handoff contract を置き換えも変更もしない。

Canonical values:

```text
D1_STATUS                         = CLOSED
OPERATING_GROUP_POLICY            = OPTION_A
OPERATING_GROUP_TARGET_SIZE       = 10
OPERATING_GROUP_COMPOSITION       = 2_EXISTING_FROZEN_HANDOFFS
READY_HANDOFF_MAX                 = 5
DATA_BUILD_BATCH_MAX              = 5
M4_CONTRACT_CHANGE                = NONE
CANDIDATE_MASTER_SCHEMA_CHANGE    = NONE
PRODUCTION_CHANGE                 = NONE
```

## 2. Upstream

本決定は次の監査の D-1（Batch size decision）を閉じる。

```text
docs/audit/shrine-expansion-10-shrine-batch-pipeline-readiness.md（PR #3165）
```

同監査は、10社単位が既存の決定済み契約（Data Build 5社 / Batch、M4 handoff max 5）と衝突することを示し、
Option A（凍結済み 5社 handoff × 2 の運用グループ）と Option B（契約を10社へ改定）を比較した。
Mother Ship は Option A を採用した。Option B は採用しない。

## 3. Authority（変更しない）

```text
docs/audit/shrine-expansion-10-shrine-batch-pipeline-readiness.md
docs/audit/shrine-expansion-wave0-data-build-plan.md
docs/audit/shrine-source-candidate-extraction-contract.md
docs/audit/niigata-batch001-ready-set-freeze.md
docs/knowledge/shrine-expansion-gate-contract.md
```

既存の 5社 Data Build / handoff contract が引き続き authoritative である。
本書はこれらの文書の記述を編集しない。

```text
Data Build Plan        : Data Build 標準単位 = 5社 / Batch、最大5社
Extraction Contract §32: M4_READY_CANDIDATE_HANDOFF_SIZE = MAX 5（DECIDED）
Implementation         : READY_HANDOFF_MAX = 5
```

## 4. Invariants

1. 既存の handoff max は 5 のまま。
2. 凍結済み handoff の membership は immutable のまま。
3. 凍結済み handoff の順序は immutable のまま。
4. Extraction snapshot の境界は変わらない。
5. Operating Group は Candidate Master に新しい lifecycle state も field も作らない。
6. G0〜G8 の Gate semantics は変わらない。
7. Gate の結果は candidate / handoff 単位のまま。
8. ある handoff の PASS は、同じ Operating Group の sibling handoff の PASS を意味しない。
9. ある candidate / handoff の HOLD は、その Gate を迂回してよいという許可にならない。
10. ある handoff の HOLD は、それだけで sibling handoff を無効にしない。
11. Production apply を Operating Group 単位で atomic にしない。
12. Rollback semantics は本決定で変わらない。
13. 既存の 5社 Data Build / handoff contract が authoritative のまま。
14. canonical documentation では Operating Group を「新しい 10社 Batch」と呼ばない。

## 5. Terminology

| 用語 | 意味 | 契約上の位置づけ |
| --- | --- | --- |
| Handoff | Extraction snapshot ごとに凍結された最大5社の READY 集合（例: `NIIGATA-001-H002`） | 既存 M4 contract |
| Data Build Batch | 最大5社の Data Build 単位 | 既存 Data Build Plan |
| Operating Group | 2つの凍結済み handoff をまとめて計画・進行管理するための運用ラベル（目標10社） | 本決定。Gate・apply・rollback の単位ではない |

Operating Group ID の例: `NIIGATA-001-OG001`。
Operating Group ID は Candidate Master / Seed / Production に書かない。

## 6. First Operating Group example

これは運用計画の例であり、Gate の完了や承認を意味しない。

```text
operating_group_id = NIIGATA-001-OG001
member_handoffs    = NIIGATA-001-H002, NIIGATA-001-H003
target_size        = 10
```

H002 frozen Source membership（`docs/audit/niigata-batch001-ready-set-freeze.md` §NIIGATA-001-H002）:

| source_position | raw_name | raw_address |
| --- | --- | --- |
| page001-row006 | 赤井神社 | 佐渡市加茂歌代2662番地 |
| page001-row007 | 赤城社 | 十日町市四日町2534番地 |
| page001-row008 | 赤城社 | 十日町市上組2059番地子 |
| page001-row009 | 赤城社 | 十日町市伊達乙48番地 |
| page001-row010 | 赤城社 | 南魚沼市芹田79番地 |

H003 frozen Source membership（同 §NIIGATA-001-H003）:

| source_position | raw_name | raw_address |
| --- | --- | --- |
| page002-row001 | 赤城神社 | 新潟市江南区二本木1丁目7番16号 |
| page002-row002 | 赤城神社 | 長岡市四郎丸2丁目5番33号 |
| page002-row003 | 赤城神社 | 長岡市山屋314番地 |
| page002-row004 | 赤城神社 | 五泉市上杉川1310番地2 |
| page002-row005 | 赤城神社 | 魚沼市湯之谷芋川311番地 |

H002 と H003 を同じ Operating Group にまとめても、どちらの handoff も Gate 完了を意味しない。

### 6.1 Current H002 state（本書では変更しない）

Candidate Master（`develop@9828f29c`）と既存 audit 記録の現状:

| candidate_id | Source position | G1 | G2（repository 上の記録） |
| --- | --- | --- | --- |
| nsrc-000006 | page001-row006 | PASS / NEW | HOLD_POSITION_REVIEW |
| nsrc-000007 | page001-row007 | PASS / SAME_NAME_DIFFERENT_SHRINE | 記録なし |
| nsrc-000008 | page001-row008 | unresolved（UNREVIEWED） | 記録なし |
| nsrc-000009 | page001-row009 | PASS / SAME_NAME_DIFFERENT_SHRINE | 記録なし |
| nsrc-000010 | page001-row010 | unresolved（UNREVIEWED） | 記録なし |

5件とも `candidate_status = DISCOVERED`。G2 の Position Resolution Record は repository 上 nsrc-000006 の1件だけ（`docs/audit/shrine-position/niigata-h002-akai-jinja-position-resolution.md`）。

### 6.2 Current H003 state（本書では変更しない）

H003 の Source membership は凍結済みだが、Candidate Master には未登録である。
本書は H003 の candidate_id を推論も割り当てもしない。
H003 の Candidate Master 登録（G0）は別の後続 operation として扱う。

## 7. Explicit non-goals

本決定は次を行わない。

- M4 / Data Build Plan / Extraction Contract / Gate Contract の記述変更
- handoff membership・順序・snapshot 境界の変更
- Candidate Master の schema / lifecycle / field の追加
- H003 の candidate_id 割り当て・G0 登録
- H002 の G1 / G2 状態の変更
- Seed / Knowledge / Position / Recommendation / Production の変更
- Operating Group 単位の atomic apply や rollback の導入

## 8. Final classification

```text
D-1                              = OPTION_A_ACCEPTED
D1_STATUS                        = CLOSED
OPERATING_GROUP_POLICY           = OPTION_A
OPERATING_GROUP_TARGET_SIZE      = 10
OPERATING_GROUP_COMPOSITION      = 2_EXISTING_FROZEN_HANDOFFS
READY_HANDOFF_MAX                = 5
DATA_BUILD_BATCH_MAX             = 5
M4_CONTRACT_CHANGE               = NONE
CANDIDATE_MASTER_SCHEMA_CHANGE   = NONE
PRODUCTION_CHANGE                = NONE

FIRST_OPERATING_GROUP_EXAMPLE    = NIIGATA-001-OG001 (H002 + H003)
H003_CANDIDATE_MASTER_REGISTRATION = NOT_EXECUTED
```
