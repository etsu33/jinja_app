> **Status: `MEASURED` — 2026-09-21 に sanctioned read-only 経路で Production 現況を実測した**
>
> **Classification: `AUDIT_STATUS = MEASURED_PASS`**
>
> **Reconciliation status: `PASS`**
>
> **`NO_CURRENT_NON_EXACT_SEED_POPULATION = YES`**
>
> 本書は Base Seed ↔ Production の raw exact identity 母集団を、既存の
> reconciliation contract で実測した記録である。**Production DB への write /
> transaction / migration は行っていない。raw snapshot は repository に
> commit していない。canonical Production Candidate Linkage record は
> 作成していない。**
>
> 本結果が証明するのは次の1点だけである。
>
> ```text
> 現在の Base Seed と現在の Production Shrine 母集団は、
> 既存 reconciliation contract のもとで 113/113 の exact identity match である。
> ```
>
> 座標正しさ、Visitor / Navigation Anchor、Position Audit PASS、地図正しさ、
> 経路目的地正しさ、歴史的 identity 正しさは **証明していない**。

# Non-Exact Production Identity Population Audit

## 0. 監査 metadata

```text
audit_kind               = population_measurement
audit_status             = MEASURED_PASS
audit_timestamp          = 2026-09-21
base_sha                 = 709ba4b0
base_branch              = develop
working_tree_before      = clean
reconciliation_contract  = scripts/reconcile_production_shrine_identity.py
join_function            = scripts/audit_shrine_positions_v2.py::join_seed_to_production
production_read_method   = scripts/migration_safety/readonly_query.sh
production_snapshot      = ~/production-shrine-snapshot.txt   (repo-external)
snapshot_sha256          = ff1f5c6cdcb6f3700fdda3a9fd8740f46c37a8ff8c4388300c86405012f3eef4
raw_snapshot_committed   = false
production_write         = NONE
canonical_linkage_created = false
```

### 現況の測定結果（確定）

既存 reconciliation contract の出力をそのまま記録する。

```text
BASE_SEED_TOTAL                = 113
PRODUCTION_TOTAL               = 113
MATCH                          = 113
PROD_ONLY                      = 0
SEED_ONLY                      = 0
PRODUCTION_DUPLICATE_IDENTITY  = 0
BASE_SEED_DUPLICATE_IDENTITY   = 0
REVIEW_CANDIDATES              = 0
STATUS                         = PASS
```

この `MATCH = 113` は、両側に存在する exact `(name_jp, address)` identity の
数である。`PRODUCTION_DUPLICATE_IDENTITY = 0` かつ
`BASE_SEED_DUPLICATE_IDENTITY = 0` であるため、現況は 113 identity の
1:1 対応である。

### 証明しないこと

```text
coordinate correctness
Visitor / Navigation Anchor correctness
Position Audit PASS
Map correctness
Route destination correctness
historical identity correctness
```

exact identity match を位置正しさへ読み替えていない。

---

## 1. 歴史的記録（2026-09-20: BLOCKED）

2026-09-20 の同一監査は Production 現況を読めず、
`AUDIT_STATUS = BLOCKED_BY_PRODUCTION_READ_ACCESS` で停止した。
当時の結論は次のとおりであり、**現況の測定結果ではない**。

```text
NO_CURRENT_NON_EXACT_SEED_POPULATION = NOT_DETERMINED
production_read_method               = NONE
production_rows_read                 = 0
audit_timestamp                      = 2026-09-20
base_sha                             = 0bed7fc5
```

当時 BLOCKED だった理由は、実行環境に sanctioned な Production read 経路が
無かったことである。古い監査文書・履歴の行表・W0-DB02 転記・Candidate
Master・Spreadsheet で代用することは、当時も現在も行っていない。

この歴史的 BLOCKED は文脈として残す。以降の節は **2026-09-21 の実測** を
現況とする。

---

## 2. Production 実測の経路

### 2.1 sanctioned read-only 経路

```text
production_read_method = scripts/migration_safety/readonly_query.sh
```

取得に使った SQL は既存の identity reconciliation 用である。

```text
scripts/migration_safety/sql/shrine_identity_reconciliation.sql
```

SELECT 1文のみ。`kind` による絞り込みを行わない（`temples_shrine` 全体が
母集団であり、temple kind の行も隠さず表面化させる、と SQL 自身が契約と
して明記している）。

### 2.2 snapshot

```text
path              = ~/production-shrine-snapshot.txt
location          = repo-external
committed         = false
sha256            = ff1f5c6cdcb6f3700fdda3a9fd8740f46c37a8ff8c4388300c86405012f3eef4
```

snapshot を repository に入れていない。credential 値も出力していない。

### 2.3 照合に使った既存 gate

新規 script は追加していない。既存 gate を snapshot に対して read-only で
実行した。

```text
python3 scripts/reconcile_production_shrine_identity.py \
  --production-snapshot ~/production-shrine-snapshot.txt \
  --report /tmp/shrine_identity_reconciliation_2026-09-21.json
```

`--report` は repository 外へ出した。`logs/` へは書いていない。
Production DB へは、snapshot 作成時の read-only query 以外に接続していない。

identity 比較は既存契約どおり、格納値の exact `(name_jp, address)` のみ。
NFKC・trim・全角半角変換・括弧変換・住所表記変換は適用していない。
類似候補は `REVIEW_CANDIDATES` として別表示するだけで、自動 MATCH しない。

---

## 3. Base Seed（canonical・実測）

```text
BASE_SEED_PATH        = backend/temples/data/shrines_seed_clean.json
BASE_SEED_ROW_COUNT   = 113
sha256                = 3acf3ca41b1cc8d0be80db28bbc1b283f3d72eb767920f6e583d6b2048523f23
row keys              = ['address', 'latitude', 'longitude', 'name_jp']
BASE_SEED_DUPLICATE_IDENTITY = 0
```

`load_base_seed()` が読む canonical Seed である。歴史的な 103 という件数は
使っていない。Seed ファイルは本監査で変更していない。

---

## 4. 既存 join 語彙との対応（再実装していない）

本測定の一次証拠は reconciliation contract の出力である。Position Audit の
既存 join 語彙へ、件数を読み替えると次のとおりになる。

```text
JOIN_MATCH_EXACT        = MATCH_EXACT
JOIN_MISSING_PRODUCTION = MISSING_PRODUCTION
JOIN_DUPLICATE_MATCH    = DUPLICATE_MATCH
```

```text
MATCH_EXACT        = 113   （SEED_ONLY = 0 かつ MATCH = 113 かつ重複 0）
MISSING_PRODUCTION = 0     （SEED_ONLY = 0）
DUPLICATE_MATCH    = 0     （PRODUCTION_DUPLICATE_IDENTITY = 0）
RAW_PRODUCTION_ONLY = 0    （PROD_ONLY = 0）
```

意味は変更していない。

```text
MATCH_EXACT        raw exact (name_jp, address) の Production 行が ちょうど1件
MISSING_PRODUCTION raw exact (name_jp, address) の Production 行が 0件
DUPLICATE_MATCH    raw exact (name_jp, address) の Production 行が 2件以上
```

### 4.1 `MISSING_PRODUCTION` / `SEED_ONLY` の意味

```text
MISSING_PRODUCTION / SEED_ONLY
!=
Production にその神社が存在しない
```

意味するのは **raw exact (name_jp, address) が 0 件だった**ことだけである。
現況ではこの件数自体が 0 である。同一の実在神社が別表記で存在するかどうかは、
本監査の範囲では問題にならない（非 exact 行が無いため）。

### 4.2 `MISSING_SEED` を作らないこと

本監査の母集団は Base Seed 起点である。canonical join の語彙に
`MISSING_SEED` は作らない。Seed に対応の無い Production 行は
`PROD_ONLY` / `RAW_PRODUCTION_ONLY` として別枠である。現況は 0 件。

---

## 5. 逆方向観測（`PROD_ONLY`）

```text
RAW_PRODUCTION_ONLY              = 0
CANONICAL_SCOPE_PRODUCTION_ONLY  = 0
```

既存 scope 契約は除外ではなく表面化を要求する。

```text
kind による絞り込みを行わない。Shrine table 全体が
「Production Shrine母集団」である。temple kind の行が存在する場合は
PROD_ONLY として表面化させ、Gate 側で黙って隠さない。
```

現況の `PROD_ONLY = 0` は、この表面化契約のもとで 0 件だった、という意味
である。除外して 0 にしたのではない。

---

## 6. Pilot 候補分類

`MISSING_PRODUCTION` / `SEED_ONLY` が 0 件であるため、分類対象は無い。

```text
PILOT_CANDIDATE          = 0
NOT_PILOT_CANDIDATE      = 0
REQUIRES_FURTHER_AUDIT   = 0
```

1件も分類していない。linkage を発明していない。

canonical Production Candidate Linkage record は **作成しない**。
理由は、測定された現況の非 exact 母集団が 0 件だからである。空の母集団に
対して canonical record を作らない。

---

## 7. 本監査が守った境界

```text
MISSING_PRODUCTION  !=  Production 神社が存在しない
population audit    !=  identity adjudication
exact identity match !=  coordinate / Position / Map / Route 正しさ
```

本監査は exact join の miss を `SAME_SUPPORTED` / `CONFLICT` その他の
B03 結果へ変換していない。B02 / B03 / B04 の rescue 経路を実行していない。

---

## 8. 必須の結論（12項目）

| # | 問い | 回答 |
| --- | --- | --- |
| 1 | 現在の Base Seed 行数 | **113**（実測。`sha256 3acf3ca4…`） |
| 2 | 現在の Production Shrine 行数 | **113**（2026-09-21 snapshot `ff1f5c6c…`） |
| 3 | exact match 件数と比率 | **MATCH = 113 / 113**（100%） |
| 4 | Seed-only / `MISSING_PRODUCTION` | **SEED_ONLY = 0**（0%） |
| 5 | Production 側 identity 重複 | **PRODUCTION_DUPLICATE_IDENTITY = 0**。Seed 側も **BASE_SEED_DUPLICATE_IDENTITY = 0** |
| 6 | `MISSING_PRODUCTION` Seed identity の全件列挙 | **該当なし（0件）** |
| 7 | `DUPLICATE_MATCH` identity と Production id の全件列挙 | **該当なし（0件）** |
| 8 | `RAW_PRODUCTION_ONLY` / `PROD_ONLY` 件数 | **0** |
| 9 | canonical scope 適用後の Production-only 件数 | **0**（既定の scope 契約は除外ではなく表面化。表面化しても 0） |
| 10 | 実在する非 exact pilot 母集団があるか | **無い。** `NO_CURRENT_NON_EXACT_SEED_POPULATION = YES` |
| 11 | linkage pilot に使える候補が1件以上あるか | **無い。** 非 exact 行が 0 件のため、canonical linkage record も作らない |
| 12 | identity / linkage 判定なしに残る未知 | §9 |

### 8.1 `NO_CURRENT_NON_EXACT_SEED_POPULATION`

2026-09-20 の歴史的結論:

```text
NO_CURRENT_NON_EXACT_SEED_POPULATION = NOT_DETERMINED
```

2026-09-21 の現況（本測定の結論）:

```text
NO_CURRENT_NON_EXACT_SEED_POPULATION = YES
```

根拠は `SEED_ONLY = 0` かつ `PROD_ONLY = 0` かつ
`PRODUCTION_DUPLICATE_IDENTITY = 0` かつ `MATCH = 113` である。
未測定を 0 件と書いたのではない。

### 8.2 rescue 実装について

B04 を動かすためだけの rescue 実装は作っていない。現況の非 exact 母集団が
0 件であるため、作る根拠も無い。

### 8.3 canonical linkage を作らないこと

```text
canonical Production Candidate Linkage records created = 0
reason = measured current non-exact population is zero
```

---

## 9. identity / linkage 判定なしに残る未知

人口照合は閉じた。残る未知は identity の欠落ではなく、**位置・経路・歴史**
の別問題である。

```text
A. 座標
   - exact (name_jp, address) match は latitude / longitude の正しさを
     証明しない

B. Visitor / Navigation Anchor
   - 本監査は触っていない

C. Position Audit
   - 本監査は Position Audit を実行していない
   - MATCH=113 を Position Audit PASS と読まない

D. Map / Route destination
   - 本監査は触っていない

E. historical identity
   - 現況 113/113 は、過去時点の identity 正しさを証明しない
   - 2026-09-20 の BLOCKED 記録は歴史的文脈であり、現況ではない
```

---

## 10. 本監査が実施していないこと

```text
Production write / transaction / migration  なし
raw Production snapshot の commit           なし（raw_snapshot_committed = false）
credential 値の要求・出力                   なし
B02 / B03 / B04 rescue 経路の実行           なし
fuzzy matching / 正規化 discovery           なし
座標近接による候補選択                      なし
linkage の実装・canonical artifact 作成     なし
identity adjudication                       なし
Seed / Candidate Master / Spreadsheet 変更  なし
canonical identity / Position decision 変更 なし
新規 script の追加                          なし（commit は本文書のみ）
Position Audit の実行                       なし
```

## 11. 検証

```text
working tree before        clean
canonical gate 再利用      reconcile_production_shrine_identity.py をそのまま使用
snapshot sha256            ff1f5c6cdcb6f3700fdda3a9fd8740f46c37a8ff8c4388300c86405012f3eef4
reconciliation             PASS（113/113）
SEED_ONLY                  0
PROD_ONLY                  0
duplicate identities       0 / 0
REVIEW_CANDIDATES          0
canonical linkage created  false
scripts/tests              本監査では実行していない（code 変更なし）
working tree after         本監査文書 1 件のみ
```

## 12. 参照

- `scripts/reconcile_production_shrine_identity.py`
- `scripts/audit_shrine_positions_v2.py`（`load_base_seed` / `load_production_snapshot` / `join_seed_to_production`）
- `scripts/migration_safety/README.md`（Credential Bridge）
- `scripts/migration_safety/readonly_query.sh`
- `scripts/migration_safety/sql/shrine_identity_reconciliation.sql`
- `docs/audit/shrine-expansion-wave0-b02-production-shrine-reconciliation-gate.md`
- `docs/audit/position-audit-v2/production-candidate-linkage-contract-audit.md`
- `docs/knowledge/production-candidate-linkage-contract.md`
