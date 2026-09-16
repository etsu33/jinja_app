# W0-DB02 Production Import 実測

## Status

- Status: `IMPORTED`
- Recorded at: `2026-09-16`
- Batch: `W0-DB02`
- Scope: 射水神社 / 別小江神社 / 戸隠神社 中社 / 札幌諏訪神社 / 少彦名神社
- Base Shrine Production Import: `SUCCESS`
- Position（札幌諏訪神社）: `PASS`（別 Audit で `CLOSED`）
- Knowledge Production Import: `SUCCESS`
- Knowledge idempotency: `PASS`
- Recommendation Eligibility: `PASS 5/5`
- Candidate lifecycle: `BUILD_READY -> IMPORTED`
- `knowledge_status`: `FACT_READY`
- CORE_READY: **`NOT YET DETERMINED`**
- Full canonical Base Seed Production apply: **`BLOCKED`**（別 Audit）

```text
W0_DB02_BASE_IMPORT                = SUCCESS
W0_DB02_POSITION                   = PASS
W0_DB02_KNOWLEDGE_IMPORT           = SUCCESS
W0_DB02_KNOWLEDGE_IDEMPOTENT       = PASS
W0_DB02_RECOMMENDATION_ELIGIBILITY = PASS_5_OF_5
W0_DB02_LIFECYCLE                  = IMPORTED
W0_DB02_KNOWLEDGE_STATUS           = FACT_READY
W0_DB02_CORE_READY                 = NOT_YET_DETERMINED
FULL_SEED_PRODUCTION_APPLY         = BLOCKED
```

---

## 1. Purpose

`backend/temples/data/shrine_expansion_candidate_master.json` において W0-DB02 の
5社（`wave0-007` 〜 `wave0-011`）を `candidate_status = IMPORTED` へ昇格させた
根拠となる **Production 実測値** を、repo 内の永続 Audit として固定する。

この文書が無い場合、昇格根拠は commit message と PR 本文にしか存在せず、
後から再検証できない。W0-DB03 以降で同じ判断を再現するための基準でもある。

本 Audit は Production 実測の**記録**であり、再実行・再接続の記録ではない。

先行事例は `docs/audit/shrine-expansion-wave0-db01-production-import.md`。
本書はその構成と Provenance 規約を踏襲する。

---

## 2. Provenance / 記録の限界

**本 Audit は Current Source of Truth ではない。** Production 実測の
point-in-time 記録である。Production の現在値は Production 自身が正であり、
Candidate lifecycle の canonical 定義は
`docs/knowledge/shrine-expansion-candidate-master-contract.md` が持つ。

本 Audit に記載する数値は、Mother Ship が Production に対して実行した結果として
提供されたものである。Codex 環境から Production へ接続して再測定してはいない。

```text
PRODUCTION_RECONNECT = NONE
PRODUCTION_WRITE     = NONE（本作業で追加の write は行っていない）
VALUE_COMPLETION     = NONE（実測していない値は補完していない）
```

以下は提供されておらず、**推測で補完しない**。

| 項目 | 記録 |
|---|---|
| Import 実行日時（UTC instant） | `NOT_RECORDED` |
| 実行 operator | `NOT_RECORDED` |
| Production DB identifier | `NOT_RECORDED` |
| deploy 時の application commit | `NOT_RECORDED` |

backup / isolated restore の識別時刻は、backup directory 名および restore target
名に含まれる識別 timestamp（`20260916-161205` / `20260916_161205`）として扱う。
**別の実行時刻を推測して追加していない。**

一次 log file は repo 内に保存していない。**repo 内に証跡 file が無いことと、
実測そのものが無いことは別である。**

---

## 3. Base Shrine Production Import

### 3.1 Import 結果

W0-DB02 の5社はいずれも Production に存在せず、Import は純粋な CREATE であった。

```text
5社 CREATE 済み
```

### 3.2 post-write

```text
Production Shrine = 113
GoriyakuTag       = 39
```

`GoriyakuTag = 39` は、canonical master（id 1..39）が Import で拡張されて
いないことを示す。5社の `goriyaku_tags` はすべて既存 canonical tag への link
として解決された。

### 3.3 goriyaku_tags link

```text
added_links   = 22
removed_links = 0
```

`removed_links = 0` により、既存の Shrine-GoriyakuTag 関連を1件も外していない。

### 3.4 Production identity mapping

Import で CREATE された5行の Production `id` は実測済みである。

| Production `id` | `official_name` |
|---|---|
| 114 | 射水神社 |
| 115 | 別小江神社 |
| 116 | 戸隠神社 中社 |
| 117 | 札幌諏訪神社 |
| 118 | 少彦名神社 |

```text
W0_DB02_PRODUCTION_IDS = 114, 115, 116, 117, 118
```

この Production `id` mapping は **post-write 時点で観測した値**であり、将来の
DB restore / migration / environment rebuild 後も不変であることは保証しない。
`id` は sequence 由来の provenance 値であって契約値ではない。

**`id` を Shrine identity として扱ってはならない。** identity は引き続き
`(name_jp, address)` である。W0-DB01 が `id = 109..113` を占めており、本 Batch が
`114..118` を連続で得ていることは、W0-DB01 以降に他の Shrine 行が
挿入されていないことと整合する。

### 3.5 repo 内での cross-check

Production 実測値を、repo 内 canonical source から独立に再計算して照合した。

`added_links = 22` は Candidate Master 側の `goriyaku_tags` 件数合計と一致する。

| Candidate | `goriyaku_tags` 件数 |
|---|---|
| 射水神社 | 4 |
| 別小江神社 | 8 |
| 戸隠神社 中社 | 5 |
| 札幌諏訪神社 | 4 |
| 少彦名神社 | 1 |
| **合計** | **22** |

```text
Base Seed 行数 113        = post-write Production Shrine 113   ... 一致
Candidate Master 合計 22  = added_links 22                     ... 一致
```

Production 値と repo 内 canonical source が独立に一致しており、`added_links` が
意図した exact-set であることを支持する。

### 3.6 Full canonical Base Seed Production apply は BLOCKED のまま

本 Import は W0-DB02 の5社を対象とした scope 限定の Import である。
Base Seed 全件を Production へ apply する操作は**実施していない**。

```text
FULL_SEED_PRODUCTION_APPLY = BLOCKED
```

---

## 4. 札幌諏訪神社 Position

札幌諏訪神社（`wave0-010` / Production `id=117`）の Position correction は
**別 Audit で完了済み**である。

```text
W0_DB02_POSITION = PASS
```

正本:
`docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md`
（`STATUS = CLOSED` / `POSITION_GATE = PASS` /
`PRODUCTION_POSITION_CORRECTION = PASS`）

**本 Audit では Position を再判断しない。** 採用 Position・Position Source・
`position_source_type` のいずれも本書では変更・再評価せず、上記 Record を
参照するにとどめる。Position 採用の意味・Source 要件・Gate の Contract は
`docs/knowledge/shrine-position-contract.md` が持つ。

他4社（`wave0-007` / `008` / `009` / `011`）の Position は Source Packet Freeze
（`docs/audit/shrine-expansion-wave0-db02-source-packet-freeze.md`）の値から
変更していない。

---

## 5. Knowledge Production Import

### 5.1 validate-only

```text
validate-only = PASS
```

### 5.2 Production initial dry-run

```text
source_CREATE  = 7
deity_CREATE   = 12
history_CREATE = 7
```

### 5.3 fresh Production backup

Knowledge Import の前に、Production の fresh backup を取得した。

```text
backup_path = /Users/morietsu/kami-musubi-backups/w0-db02-knowledge-20260916-161205
backup_identifier_timestamp = 20260916-161205（backup directory 名の識別 timestamp）
```

| 構成物 | サイズ |
|---|---|
| `roles.sql` | 5,426 bytes |
| `schema.sql` | 106,945 bytes |
| `data.sql` | 7,245,182 bytes |

### 5.4 isolated restore

取得した backup が実際に復元可能であることを、Production とは別の隔離 DB へ
restore して確認した。

```text
restore_target = w0_db02_knowledge_restore_test_20260916_161205
restore        = PASS
```

復元後の確認値:

```text
Shrine      = 113
GoriyakuTag = 39
```

Base Import 後の post-write 値（§3.2）と一致しており、backup が Base Import 済み
かつ Knowledge Import 前の状態を正しく保持していることを示す。

### 5.5 restore 後 dry-run

隔離 restore DB に対する dry-run:

```text
source_CREATE  = 7
deity_CREATE   = 12
history_CREATE = 7
```

初回 dry-run（§5.2）と完全一致。

### 5.6 Production final pre-write dry-run

write 直前に Production に対して再度 dry-run を実行した。

```text
source_CREATE  = 7
deity_CREATE   = 12
history_CREATE = 7
```

初回 dry-run・restore 後 dry-run と3回とも完全一致しており、write 直前まで
予測が動いていないことを示す。

### 5.7 Knowledge Production apply

```text
sources created   = 7
deities created   = 12
histories created = 7
```

dry-run の CREATE 件数と apply の created 件数が完全一致している。
dry-run が実際の write を正しく予測していた、という意味である。

### 5.8 post-import idempotency dry-run

```text
source_REUSE_EXISTING = 7
deity_SKIP_EXISTS     = 12
history_SKIP_EXISTS   = 7
CREATE                = 0
errors                = 0
```

`CREATE = 0` により idempotency が成立している。Knowledge Import を再実行しても
重複 Fact を作らない。

```text
W0_DB02_KNOWLEDGE_IMPORT     = SUCCESS
W0_DB02_KNOWLEDGE_IDEMPOTENT = PASS
```

### 5.9 repo 内での cross-check

Knowledge Seed（`backend/temples/data/knowledge_seeds/wave0_batch_02_seed.json`）
から独立に再計算した値と一致する。

```text
Seed sources   7 = source_CREATE  7   ... 一致
Seed deities  12 = deity_CREATE  12   ... 一致
Seed histories 7 = history_CREATE 7   ... 一致
```

---

## 6. Recommendation Eligibility 実測

Recommendation eligibility は `candidate_status` が表すものではなく、**別 Gate**
である。本 Batch では Import 後に独立して実測した。

判定 Contract: `docs/knowledge/recommendation-eligibility-contract.md`

### 6.1 Batch 集計

```text
requested    = 5
ELIGIBLE     = 5
INELIGIBLE   = 0
UNRESOLVED   = 0
ALL_ELIGIBLE = PASS
```

`UNRESOLVED = 0` は、5社すべてが `(official_name, official_address)` で
Production 上の行として解決できたことを意味する。

### 6.2 per-shrine

| 神社 | `usable_deity` | `usable_history` |
|---|---|---|
| 射水神社 | 1 | 2 |
| 別小江神社 | 6 | 1 |
| 戸隠神社 中社 | 1 | 1 |
| 札幌諏訪神社 | 2 | 1 |
| 少彦名神社 | 2 | 2 |

5社とも usable Deity Fact >= 1 かつ usable History Fact >= 1 を満たす。

### 6.3 repo 内での cross-check

per-shrine の usable 件数は、Knowledge Seed の per-shrine fact 件数と完全一致する
（`backend/temples/tests/test_wave0_db02_shrine_seed.py::EXPECTED_FACT_COUNTS`
が同じ値を凍結している）。

すべての Fact が `source_confirmed` / `high` であり Evidence Gate を通過するため、
seed 上の fact 件数がそのまま usable 件数になる。Production 側で Fact が
欠落・降格していないことを示す。

```text
W0_DB02_RECOMMENDATION_ELIGIBILITY = PASS_5_OF_5
```

---

## 7. Candidate lifecycle 遷移

### 7.1 遷移内容

`backend/temples/data/shrine_expansion_candidate_master.json` の W0-DB02 5件のみ:

```text
candidate_status: BUILD_READY -> IMPORTED
```

| `candidate_id` | `official_name` | Production `id` |
|---|---|---|
| `wave0-007` | 射水神社 | 114 |
| `wave0-008` | 別小江神社 | 115 |
| `wave0-009` | 戸隠神社 中社 | 116 |
| `wave0-010` | 札幌諏訪神社 | 117 |
| `wave0-011` | 少彦名神社 | 118 |

### 7.2 維持した値

```text
build_batch        = W0-DB02   （不変）
knowledge_status   = FACT_READY（不変）
status_reason_code = WAVE0_CORE_READY_CANDIDATE（不変）
```

`build_batch` は lifecycle state ではなく Data Build provenance であるため、
`BUILD_READY -> IMPORTED` の遷移で消さない
（`docs/knowledge/shrine-expansion-candidate-master-contract.md`）。

identity / official source / factual fields / coordinates / goriyaku /
goriyaku_tags / discovery provenance / `candidate_defaults` はいずれも
**変更していない**。

### 7.3 lifecycle 会計

実ファイルから再計算した値。

```text
BUILD_READY = 25   W0-DB03〜W0-DB07
IMPORTED    =  5   W0-DB02
CORE_READY  =  5   W0-DB01
HOLD        =  8
REVIEW      =  1
TOTAL       = 44
```

総数 44 と HOLD / REVIEW の内訳は不変である。W0-DB02 以外の Candidate に
差分は無い。

---

## 8. 意味境界

`IMPORTED` が主張する範囲を取り違えないために、本 Batch で成立した命題と
成立していない命題を明示する。

### 8.1 `IMPORTED` が意味しないもの

- **`IMPORTED` は `CORE_READY` を意味しない。**
- **`IMPORTED` は Recommendation eligibility を意味しない。**
- **`FACT_READY` も `CORE_READY` を意味しない。**

`IMPORTED` が主張するのは Production への write 完了だけである。

### 8.2 Recommendation eligibility は別 Gate として実測した

本 Batch では Recommendation eligibility を `candidate_status` から推論せず、
**独立した Gate として 5/5 PASS を実測した**（§6）。

これは「`IMPORTED` だから eligible」ではなく、「別 Gate を通した結果 eligible
だった」という意味である。この順序を逆にしてはならない。

### 8.3 CORE_READY は次フェーズ

```text
W0_DB02_CORE_READY = NOT_YET_DETERMINED
```

`CORE_READY` は次フェーズの **Completion Contract 12/12** でのみ判定する。
本 Audit は `CORE_READY` を宣言しない。

---

## 9. 参照

- `docs/audit/shrine-expansion-wave0-db01-production-import.md`（W0-DB01 先行事例 / Provenance 規約）
- `docs/knowledge/shrine-expansion-candidate-master-contract.md`（Candidate lifecycle の Contract）
- `docs/audit/shrine-expansion-wave0-db02-source-packet-freeze.md`（2026-09-15 凍結記録）
- `docs/audit/shrine-expansion-wave0-db02-isolated-preflight.md`（Phase 6 実測記録）
- `docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md`（札幌諏訪神社 Position 正本）
- `docs/knowledge/recommendation-eligibility-contract.md`（Recommendation eligibility の Contract）
