# W0-DB03 Production Import 実測（G7）

## Status

- Status: `IMPORTED`（execution subset 4社）
- Recorded at: `2026-09-26`
- Batch: `W0-DB03`
- Gate: `G7 Production Import`（`docs/knowledge/shrine-expansion-gate-contract.md` §10）
- Execution subset: 大神神社 / 北野天満宮 / 平安神宮 / 岡田宮（`wave0-012` / `013` / `015` / `016`）
- Excluded: 宮城縣護國神社（`wave0-014`、G3 `MODEL_CHANGE_REQUIRED`、G7 NOT EXECUTED）
- Base Shrine Production Import: `SUCCESS`（CREATE 4）
- Knowledge Production Import: `SUCCESS`（Source 4 / Deity 18 / History 5）
- Base / Knowledge idempotency: `PASS`
- Production Recommendation Eligibility: `PASS 4/4`
- Candidate lifecycle: `BUILD_READY -> IMPORTED`（4社のみ）
- `knowledge_status`: `ACQUISITION_PATH_CONFIRMED -> FACT_READY`（4社のみ）
- CORE_READY: **`NOT YET DETERMINED`**（G8 未実行）
- Full canonical Base Seed Production apply: **`BLOCKED`**（変更なし。4行 subset のみ適用）

```text
W0_DB03_G7_BASE_IMPORT           = PASS_4_OF_4
W0_DB03_G7_KNOWLEDGE_IMPORT      = PASS_4_OF_4
W0_DB03_G7_BASE_IDEMPOTENCY      = PASS
W0_DB03_G7_KNOWLEDGE_IDEMPOTENCY = PASS
W0_DB03_G7_ELIGIBILITY           = PASS_4_OF_4
W0_DB03_G7_WAVE0_014             = NOT_EXECUTED
W0_DB03_G7                       = PASS_4_OF_4
W0_DB03_G8                       = NOT_EXECUTED
```

---

## 1. Purpose

`backend/temples/data/shrine_expansion_candidate_master.json` の W0-DB03 execution subset 4社を
`candidate_status = IMPORTED` / `knowledge_status = FACT_READY` へ遷移させる根拠となる
**Production 実測値**を、repo 内の永続 Audit として固定する。

構成と Provenance 規約は `docs/audit/shrine-expansion-wave0-db02-production-import.md` を踏襲する。

Upstream Gate:

| Gate | 記録 | 結果 |
| --- | --- | --- |
| G4 | `docs/audit/shrine-expansion-wave0-db03-g4-evidence-preflight.md` | `W0_DB03_G4_PASS_4_OF_4` |
| G5 | `docs/audit/shrine-expansion-wave0-db03-g5-recommendation-eligibility.md` | `W0_DB03_G5_PASS_4_OF_4` |
| G6 | `docs/audit/shrine-expansion-wave0-db03-g6-runtime-qa.md` | `W0_DB03_G6_PASS_4_OF_4` |

---

## 2. Provenance / 記録の限界

**本 Audit は Current Source of Truth ではない。** Production 実測の point-in-time 記録である。

| 種別 | 正本 |
| --- | --- |
| Production の現在値 | Production 自身 |
| Candidate lifecycle の canonical 定義 | `docs/knowledge/shrine-expansion-candidate-master-contract.md` |
| Gate の定義 | `docs/knowledge/shrine-expansion-gate-contract.md` |
| Eligibility の定義 | `docs/knowledge/recommendation-eligibility-contract.md` |
| 採用座標・Fact の値 | `docs/audit/shrine-expansion-wave0-db03-source-packet-freeze.md` と repo の Seed |

本 Audit に記載する数値は、Mother Ship が Production に対して実行した結果として提供されたものである。
Codex 環境から Production へ接続・再測定はしていない。

```text
PRODUCTION_RECONNECT = NONE
PRODUCTION_WRITE     = NONE（本 PR では追加の write を行っていない）
VALUE_COMPLETION     = NONE（実測していない値は補完していない）
CREDENTIAL_RECORDED  = NONE
```

提供された実行条件:

```text
execution date = 2026-09-26
develop used   = 2387f680fb3ef5963a4e3afe0163df894ddac251
```

以下は提供されておらず、**推測で補完しない**。

| 項目 | 記録 |
| --- | --- |
| Import 実行時刻（UTC instant） | `NOT_RECORDED` |
| Base write 承認時刻 | `NOT_RECORDED`（明示承認があったことのみ記録） |
| Knowledge write 承認時刻 | `NOT_RECORDED`（明示承認があったことのみ記録） |
| 実行 operator | `NOT_RECORDED` |
| Production DB identifier | `NOT_RECORDED` |
| deploy 時の application commit | `NOT_RECORDED` |

backup の識別時刻は backup identifier に含まれる timestamp（`20260926-102820`）として扱う。
一次 log file は repo 内に保存していない。**repo 内に証跡 file が無いことと、実測が無いことは別である。**

### Identity と Production id

canonical identity は引き続き `(name_jp, address)` である。本書に記載する Production `id` は
post-write 時点で観測した **provenance 値**であり、契約値ではない。restore / migration /
環境再構築後に不変であることは保証しない。**`id` を Shrine identity として扱ってはならない。**

---

## 3. Production pre-state（write 前の新規実測）

```text
Shrine total                     = 113
GoriyakuTag total                = 39
GoriyakuTag ids exactly 1..39    = true
ShrineKnowledgeSource total      = 127
ShrineDeity total                = 269
ShrineHistory total              = 209
W0_DB03_SOURCE_URL_PREEXISTING   = 0
```

| canonical identity | `exact` | `same_name` |
| --- | ---: | ---: |
| 大神神社 / 奈良県桜井市三輪1422 | 0 | 0 |
| 北野天満宮 / 京都府京都市上京区馬喰町 | 0 | 0 |
| 平安神宮 / 京都府京都市左京区岡崎西天王町97 | 0 | 0 |
| 岡田宮 / 福岡県北九州市八幡西区岡田町1-1 | 0 | 0 |

4社とも Production に存在せず、同名の別住所行も無かった（identity ambiguity なし）。
wave0-014 は execution subset に含まれておらず、G7 対象として Production へ照会していない。

---

## 4. Backup / isolated restore

```text
backup_identifier = w0-db03-g7-20260926-102820
```

### 4.1 1回目の dump（失敗）

```text
result       = FAILED_AT_ROLES_DUMP
PATH client  = PostgreSQL 16.10
Production write = 0
```

roles dump の段階で失敗した。dump は read-only 操作であり、Production への write は発生していない。
`scripts/migration_safety/dump_readonly.sh` は client の major version が server より古い場合に
`PG_DUMP_BIN` / `PG_DUMPALL_BIN` の指定を求める設計であり、2回目は client を切り替えて再実行した。
失敗原因の詳細（エラー本文）は提供されておらず、本書では推測しない。

### 4.2 2回目の dump（成功）

```text
client = PostgreSQL 17.10
```

| 構成物 | サイズ |
| --- | ---: |
| `roles.sql` | 5,426 bytes |
| `schema.sql` | 106,945 bytes |
| `data.sql` | 8,270,684 bytes |

### 4.3 isolated restore

```text
isolated restore = PASS
restored DB fingerprint == Production pre-write fingerprint（完全一致）
```

backup が write 前の Production 状態を正しく保持し、復元可能であることを確認してから write へ進んだ。

---

## 5. Base Shrine Production Import

scope は `/tmp/w0_db03_base_seed.json`（canonical Base Seed から4社を機械的に抽出した subset）のみ。
Base Seed 全件の Production apply は行っていない。

### 5.1 dry-run

```text
created=4 updated=0 skipped=0
goriyaku_tags rows=4 updated=4 added_links=24 removed_links=0
```

Mother Ship が Base write を明示承認した（時刻は `NOT_RECORDED`）。

### 5.2 apply

```text
created=4 updated=0 skipped=0
added_links=24 removed_links=0
```

dry-run と apply が完全一致した。`updated=0` / `removed_links=0` により、既存 Shrine 行・既存 tag link を変更していない。

### 5.3 post-Base

```text
Shrine total                  = 117
GoriyakuTag total             = 39
GoriyakuTag ids exactly 1..39 = true
target tag links total        = 24
```

| canonical identity | Production `id`（provenance） | `exact` | lat/lng | location | tags |
| --- | ---: | ---: | --- | --- | --- |
| 大神神社 / 奈良県桜井市三輪1422 | 119 | 1 | match | match | match |
| 北野天満宮 / 京都府京都市上京区馬喰町 | 120 | 1 | match | match | match |
| 平安神宮 / 京都府京都市左京区岡崎西天王町97 | 121 | 1 | match | match | match |
| 岡田宮 / 福岡県北九州市八幡西区岡田町1-1 | 122 | 1 | match | match | match |

```text
W0_DB03_PRODUCTION_IDS = 119, 120, 121, 122   （provenance only）
```

GoriyakuTag は新規作成されず、canonical master（id 1..39）は不変。

### 5.4 repo 内での cross-check

| 観点 | repo 側 | Production 実測 | 判定 |
| --- | --- | --- | --- |
| Shrine 増分 | subset 4行 | 113 → 117（+4） | 一致 |
| tag link | Candidate Master の goriyaku_tags 合計 6 + 6 + 8 + 4 = 24 | added_links 24 | 一致 |
| 座標 | Source Packet / Base Seed / Candidate Master | lat_lng_match / location_match = True（4/4） | 一致 |

---

## 6. Knowledge Production Import

対象: `backend/temples/data/knowledge_seeds/wave0_batch_03_seed.json`

### 6.1 validate-only

```text
validate-only = PASS
```

### 6.2 pre-write dry-run

```text
source_CREATE  = 4
deity_CREATE   = 18
history_CREATE = 5
```

Mother Ship が Knowledge write を明示承認した（時刻は `NOT_RECORDED`）。

### 6.3 apply

```text
sources created   = 4
deities created   = 18
histories created = 5
```

### 6.4 post-write

```text
ShrineKnowledgeSource total = 131   （127 + 4）
ShrineDeity total           = 287   （269 + 18）
ShrineHistory total         = 214   （209 + 5）
```

| Shrine | deity | history | sourceless |
| --- | ---: | ---: | ---: |
| 大神神社 | 1 | 1 | 0 |
| 北野天満宮 | 3 | 1 | 0 |
| 平安神宮 | 2 | 2 | 0 |
| 岡田宮 | 12 | 1 | 0 |

### 6.5 repo 内での cross-check

```text
Seed sources    4 = source_CREATE   4 = 増分 +4    ... 一致
Seed deities   18 = deity_CREATE   18 = 増分 +18   ... 一致
Seed histories  5 = history_CREATE  5 = 増分 +5    ... 一致
```

per-shrine 件数は `backend/temples/tests/test_wave0_db03_shrine_seed.py::EXPECTED_FACT_COUNTS` と一致する。

---

## 7. Idempotency

### 7.1 Knowledge（2回目 dry-run）

```text
source_REUSE_EXISTING = 4
deity_SKIP_EXISTS     = 18
history_SKIP_EXISTS   = 5
CREATE                = 0
```

### 7.2 Base subset（2回目 dry-run）

```text
created=0 updated=0 skipped=4
goriyaku_tags updated=0 added_links=0 removed_links=0
```

```text
W0_DB03_G7_KNOWLEDGE_IDEMPOTENCY = PASS
W0_DB03_G7_BASE_IDEMPOTENCY      = PASS
```

---

## 8. Production Recommendation Eligibility

read-only verifier（`temples.services.recommendation_eligibility_verifier.verify_recommendation_eligibility()`）へ
4社の canonical identity のみを渡した。`--batch W0-DB03` は使用していない（original membership 5 と
canonical identity 4 が一致しないため fail closed するのが正しい挙動であり、wave0-014 を hydrate しない）。

| canonical identity | status | usable_deity | usable_history |
| --- | --- | ---: | ---: |
| 大神神社 / 奈良県桜井市三輪1422 | ELIGIBLE | 1 | 1 |
| 北野天満宮 / 京都府京都市上京区馬喰町 | ELIGIBLE | 3 | 1 |
| 平安神宮 / 京都府京都市左京区岡崎西天王町97 | ELIGIBLE | 2 | 2 |
| 岡田宮 / 福岡県北九州市八幡西区岡田町1-1 | ELIGIBLE | 12 | 1 |

```text
requested    = 4
ELIGIBLE     = 4
INELIGIBLE   = 0
UNRESOLVED   = 0
ALL_ELIGIBLE = PASS
```

usable 件数は G5（隔離 DB）実測と完全一致した。

---

## 9. Candidate lifecycle 遷移

`backend/temples/data/shrine_expansion_candidate_master.json` の4行のみ:

| `candidate_id` | `official_name` | `candidate_status` | `knowledge_status` | Production `id`（provenance） |
| --- | --- | --- | --- | ---: |
| `wave0-012` | 大神神社 | BUILD_READY → IMPORTED | ACQUISITION_PATH_CONFIRMED → FACT_READY | 119 |
| `wave0-013` | 北野天満宮 | BUILD_READY → IMPORTED | ACQUISITION_PATH_CONFIRMED → FACT_READY | 120 |
| `wave0-015` | 平安神宮 | BUILD_READY → IMPORTED | ACQUISITION_PATH_CONFIRMED → FACT_READY | 121 |
| `wave0-016` | 岡田宮 | BUILD_READY → IMPORTED | ACQUISITION_PATH_CONFIRMED → FACT_READY | 122 |

`knowledge_status` は行レベルの override として付与した（`candidate_defaults` は
`ACQUISITION_PATH_CONFIRMED` のまま）。`FACT_READY` の要件である「Production 上で usable Knowledge が
確認された」ことは §6 / §8 の実測が根拠である。

維持した値:

```text
build_batch        = W0-DB03（不変）
status_reason_code = WAVE0_CORE_READY_CANDIDATE（不変）
identity_status / official_source_status / official_* / verified_at /
latitude / longitude / goriyaku / goriyaku_tags / discovery_sources（不変）
```

### wave0-014

```text
wave0-014 宮城縣護國神社
G3 = MODEL_CHANGE_REQUIRED
G4 / G5 / G6 / G7 = NOT EXECUTED
Candidate Master row = 無変更（diff 0）
```

W0-DB03 の original membership は5社のままであり、Batch は「4社 IMPORTED / 1社 BUILD_READY」の
混在状態となる。wave0-014 に新しい status / status_reason_code は付与していない。

### CORE_READY

どの W0-DB03 Candidate も `CORE_READY` にしていない。CORE READY Completion Contract は G8 が判定する。

---

## 10. 本 PR が変更していないもの

```text
Production DB（追加の接続・write なし）
Base Seed / Knowledge Seed / Knowledge Fact
Schema / Migration
Ranking / Score / Evidence Gate / Recommendation Eligibility / Compass
GoriyakuTag master
wave0-014
G8
```

---

## 11. Final

```text
W0_DB03_G7_BASE_IMPORT           = PASS_4_OF_4
W0_DB03_G7_KNOWLEDGE_IMPORT      = PASS_4_OF_4
W0_DB03_G7_BASE_IDEMPOTENCY      = PASS
W0_DB03_G7_KNOWLEDGE_IDEMPOTENCY = PASS
W0_DB03_G7_ELIGIBILITY           = PASS_4_OF_4
W0_DB03_G7_WAVE0_014             = NOT_EXECUTED
W0_DB03_G7                       = PASS_4_OF_4
W0_DB03_G8                       = NOT_EXECUTED
NEXT                             = G8 CORE READY Closure（別 PR / 別指示）
```
