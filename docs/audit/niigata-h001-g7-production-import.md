# NIIGATA-H001 nsrc-000004 青海神社（加茂市） G7 Production Import

## Status

- Recorded at: `2026-10-10`
- Candidate: `nsrc-000004`
- Shrine: 青海神社（加茂市）
- Gate: `G7 Production Import`
- Result: **`CLOSED / PASS`**
- G8 CORE READY: **`NOT EXECUTED`**
- Full canonical Base Seed Production apply: **`PROHIBITED`**
- Production write after closure: **`PROHIBITED`**

```text
G7_READ_ONLY_PREFLIGHT          = PASS
G7_PRODUCTION_BACKUP_RESTORE    = PASS
G7_BASE_IMPORT                  = PASS
G7_BASE_IDEMPOTENCY             = PASS
G7_KNOWLEDGE_IMPORT             = PASS
G7_KNOWLEDGE_IDEMPOTENCY        = PASS
G7_AGGREGATE_INVARIANT          = PASS
G7_KNOWLEDGE_INTEGRITY          = PASS
G7_SOURCE_RELATION_INTEGRITY    = PASS
G7_GORIYAKU_ISOLATION           = PASS
G7_PRODUCTION_RUNTIME_QA        = PASS
G7_RESULT                       = PASS
G8                              = NOT_EXECUTED
```

---

## 1. Purpose

`docs/knowledge/shrine-expansion-gate-contract.md` の G7 に従い、G1〜G6 を通過した
`nsrc-000004 青海神社（加茂市）` について、Production への限定 import と
post-write verification / idempotency / Runtime QA を実測し、point-in-time の証跡を固定する。

Upstream:

| Gate | Evidence |
| --- | --- |
| G4 | `docs/audit/niigata-h001-g4-source-packet-freeze.md` / `docs/audit/niigata-h001-g4-data-materialization-reentry.md` |
| G5 | dedicated PostgreSQL eligibility test / PR #3130 |
| G6 | `docs/audit/niigata-h001-g6-runtime-qa.md` / PR #3131 |

本 Audit は Production の現在値を永久に保証するものではない。Production の current state は Production 自身が正本である。

---

## 2. Approved scope

Mother Ship は以下を明示承認した。

```text
candidate = nsrc-000004 青海神社（加茂市）
Base      = canonical Base Seed から機械抽出した当該1社のみ
Knowledge = backend/temples/data/knowledge_seeds/nsrc_000004_seed.json のみ

expected delta:
Shrine        +1
Source        +3
Deity         +2
History       +2
SourceFact    +11
goriyaku系    +0

unexpected delta => STOP
Full Base Seed apply => PROHIBITED
```

承認外の候補・HOLD 4社・Ranking / Score / Recommendation logic・goriyaku mapping は変更していない。

---

## 3. Production pre-state / read-only preflight

Production read-only preflight の実測:

```text
latest temples migration = 0120_shrine_source_fact_foundation

Shrine                  = 120
ShrineKnowledgeSource   = 137
ShrineDeity             = 293
ShrineHistory           = 226
ShrineSourceFact         = 23

target exact count       = 0
same-name count          = 0
S1 / S2 / S4 source     = 0
target Deity             = 0
target History           = 0
11 stable_key collision  = 0
target goriyaku links    = 0
```

したがって expected Production delta は exact と判定した。

---

## 4. Backup / isolated restore

### 4.1 Dump client mismatch

1回目は local client `16.10`、Production server `17.6` の major mismatch により
roles dump で停止した。Production write は 0。

```text
BACKUP_FAILURE_ROOT_CAUSE = CLIENT_SERVER_MAJOR_VERSION_MISMATCH
```

PostgreSQL 17 client `17.10` を明示し、再取得した。

| artifact | bytes |
| --- | ---: |
| `roles.sql` | 5,792 |
| `schema.sql` | 134,714 |
| `data.sql` | 11,757,025 |

backup identifier:

```text
nsrc-000004-g7-20261010-prewrite-pg17
```

credential / hostname / database identifier は repo に記録していない。

### 4.2 Isolated restore

最初の restore attempt は target disposable DB が未作成だったため停止した。
`createdb kami_musubi_g7_restore_test_20261010` 後に再実行し、
PostGIS / pg_trgm、schema、data まで完走した。

```text
ISOLATED_DB_CREATED = PASS
ISOLATED_RESTORE    = PASS
```

restore 後に Production pre-state と同じ preflight SQL を実行し、以下を完全一致で確認した。

```text
Shrine        120
Source        137
Deity         293
History       226
SourceFact     23

target exact / same-name = 0 / 0
target S1/S2/S4          = 0
target Deity / History   = 0 / 0
stable_key collision     = 0
goriyaku links           = 0
```

```text
RESTORED_DB_FINGERPRINT  = PASS
BACKUP_RESTORE_READINESS = PASS
```

---

## 5. Pre-write fail-closed guards

Production write の直前状態を固定するため、以下を追加した。

- `scripts/migration_safety/sql/nsrc_000004_g7_pre_base_guard.sql`
- `scripts/migration_safety/sql/nsrc_000004_g7_post_base_guard.sql`

初版の pre-Base Guard は定数 `1/0` を fail-closed に利用していたため、
PostgreSQL planner による早期評価の可能性があり、read-only query が失敗した。
その修正過程で条件式の括弧不足も検出した。

いずれも **Production write 前** に検出・修正し、Production data への影響は 0。
最終版を isolated restore DB と Production の両方へ実行し、各 `PASS=1` を確認した。

```text
ISOLATED_PRE_BASE_GUARD = PASS
PRODUCTION_PRE_BASE_GUARD = PASS
POST_BASE_PRODUCTION_GUARD = PASS
```

---

## 6. Base Shrine Production import

canonical Base Seed から target identity 1行だけを `/tmp/nsrc_000004_base_seed.json` へ機械抽出した。

```text
SUBSET_ROWS = 1
name_jp     = 青海神社
address     = 新潟県加茂市大字加茂字宮山229番地
```

### 6.1 Dry-run

```text
CREATE 青海神社
goriyaku_tags rows=0 updated=0 added_links=0 removed_links=0
done created=1 updated=0 skipped=0 total_seed=1
```

### 6.2 Apply

pre-Base Guard を再実行後、同 subset のみ apply した。

```text
CREATE 青海神社
goriyaku_tags rows=0 updated=0 added_links=0 removed_links=0
done created=1 updated=0 skipped=0 total_seed=1
```

dry-run と apply は完全一致した。

Production id `126` はこの時点の provenance 値であり、canonical identity ではない。

### 6.3 Post-Base

post-Base Guard が `1` を返した。

```text
Shrine        120 -> 121
Source        137 -> 137
Deity         293 -> 293
History       226 -> 226
SourceFact     23 -> 23
goriyaku系         -> delta 0
```

---

## 7. Knowledge Production import

対象:

`backend/temples/data/knowledge_seeds/nsrc_000004_seed.json`

### 7.1 Dry-run

```text
source_CREATE      = 3
deity_CREATE       = 2
history_CREATE     = 2
source_fact_CREATE = 11
```

unexpected `REUSE_EXISTING` / `SKIP_EXISTS` / `CONFLICT` / `AMBIGUOUS` /
`NOT_FOUND` は 0。

### 7.2 Apply

post-Base Guard を再実行後に apply した。

```text
plan summary:
  source_CREATE      = 3
  deity_CREATE       = 2
  history_CREATE     = 2
  source_fact_CREATE = 11

import complete:
  sources created      = 3
  deities created      = 2
  histories created    = 2
  collectives created  = 0
  memberships created  = 0
  source_facts created = 11
```

dry-run と apply は完全一致した。

Observed provenance ids:

```text
Source      = 139, 140, 141
Deity       = 294, 295
History     = 227, 228
SourceFact  = 24..34
```

これら numeric id は identity contract ではない。

---

## 8. Post-Knowledge verification

`scripts/migration_safety/sql/nsrc_000004_g7_post_knowledge_verification.sql`
を Production へ read-only 実行した。

### 8.1 Aggregate

```text
Shrine        = 121   (+1)
Source        = 140   (+3)
Deity         = 295   (+2)
History       = 228   (+2)
SourceFact    = 34    (+11)
```

### 8.2 Target integrity

```text
target Shrine              = 1
target Sources             = 3
target Deity               = 2
target History             = 2
target SourceFact          = 11

source-less Deity          = 0
source-less History        = 0
source-less SourceFact     = 0

Deity-Source relations     = 2
History-Source relations   = 2
SourceFact-Source relations= 11

stable_key                 = 11 / 11 unique
goriyaku tag links         = 0
```

```text
G7_AGGREGATE_INVARIANT       = PASS
G7_KNOWLEDGE_INTEGRITY       = PASS
G7_SOURCE_RELATION_INTEGRITY = PASS
G7_GORIYAKU_ISOLATION        = PASS
```

---

## 9. Idempotency

### 9.1 Base

post-state 再確認後、target Base subset を `--dry-run` した。

```text
SKIP id=126 青海神社
goriyaku_tags rows=0 updated=0 added_links=0 removed_links=0
done created=0 updated=0 skipped=1 total_seed=1
```

```text
G7_BASE_IDEMPOTENCY = PASS
```

### 9.2 Knowledge

同じ Production state に対して Knowledge seed を `--dry-run` した。

```text
source_REUSE_EXISTING   = 3
deity_SKIP_EXISTS       = 2
history_SKIP_EXISTS     = 2
source_fact_SKIP_EXISTS = 11

CREATE     = 0
CONFLICT   = 0
AMBIGUOUS  = 0
NOT_FOUND  = 0
```

```text
G7_KNOWLEDGE_IDEMPOTENCY = PASS
```

---

## 10. Production Runtime QA

G6 と同じ4 surface を Production data で再確認する専用 read-only script を追加した。

`scripts/migration_safety/nsrc_000004_g7_runtime_qa.py`

script は transaction 開始直後に `SET TRANSACTION READ ONLY` を実行し、
意図しない write を DB 側で fail closed にする。

実測:

```text
DETAIL_RUNTIME=PASS
CONCIERGE_CANDIDATE_PATH=PASS
RECOMMENDATION_REASON=PASS
COMPASS_DISTANCE=PASS
COMPASS_DIRECTION=PASS
G7_PRODUCTION_RUNTIME_QA=PASS
TRANSACTION_MODE=READ_ONLY
```

runtime log:

```text
trace=nsrc-000004-g7-production-runtime
count=107
eligible=107
ineligible=14
with_place_id=2
miss_latlng=0
dist_none=0
```

Runtime QA は以下を確認した。

- Shrine Detail が D1/D2 と H1/H2 を source-backed data として返す
- Kamo/Mio 系の除外祭神を混入させない
- Concierge shared candidate path に target が1件だけ存在する
- `goriyaku_tag_ids == []` を維持する
- Recommendation reason が D1/D2 と H1 を authority として利用する
- 保証・断定表現を生成しない
- adopted coordinate を距離 / 方角計算へ利用する
- direction filter が一致方向のみ target を保持する

---

## 11. No-scope-change invariants

本 G7 で変更していないもの:

```text
Full Base Seed
HOLD candidates nsrc-000001 / 000002 / 000003 / 000005
GoriyakuTag
ShrineGoriyakuAssignment
Ranking / Score
Recommendation contract
Coordinate decision
G1-G6 historical audit result
G8 CORE READY state
```

G4 historical `HOLD / BASE_SHRINE_NOT_MATERIALIZED` は書き換えず、
後続 re-entry と本 G7 が解消経路の evidence である。

---

## 12. Final classification

```text
G7_BLOCKERS_REMAINING = NONE
G7_STATUS             = CLOSED
G7_RESULT             = PASS

Production final delta:
Shrine        +1
Source        +3
Deity         +2
History       +2
SourceFact    +11
goriyaku系    +0

PRODUCTION_WRITE_AFTER_CLOSURE = PROHIBITED
G8_CORE_READY                  = NOT_EXECUTED
```

G7 PASS は G8 CORE READY を意味しない。次工程で G8 Completion Contract を別途判定する。
