# Position Audit v2 — Shrine Position Ground Truth

## Status

- Status: `ACTIVE`
- Recorded at: `2026-09-17`
- Scope: Shrine position の **machine-verifiability triage**（read-only）
- Production DB write: **なし**
- Seed / Candidate Master / Spreadsheet write: **なし**
- 座標補正: **行わない**

```text
POSITION_AUDIT_V2          = IMPLEMENTED
AUDIT_WRITE_PATH           = NONE
COORDINATE_CORRECTION      = NOT_IN_SCOPE
W0_DB02_PILOT              = EXECUTED (input-incomplete)
```

## 1. 目的と非目的

`docs/knowledge/shrine-position-contract.md` を authority として、
`Shrine.latitude` / `Shrine.longitude`（= **Visitor / Navigation Anchor**）が
どこまで機械的に検証できるかを判定する。

**本監査は座標補正タスクではない。** 判定するのは次の2点だけである。

- どの Shrine position が machine-verified と言えるか
- どれが human review を要するか

次は行わない。

- Production / Seed / Candidate Master / Spreadsheet への write
- 座標の自動補正
- 新しい primary source の自動採用
- 距離ベースの PASS 閾値の導入
- Recommendation / Compass / ranking / scoring の変更
- goriyaku / Knowledge の remediation
- 検索エンジンからの任意 URL 収集
- 欠損座標の推測
- 曖昧な identity の暗黙解決

## 2. Source 責務

| Source | 役割 | 位置づけ |
| --- | --- | --- |
| `docs/knowledge/shrine-position-contract.md` | Position の採用意味・Source 要件・Gate | **authority**。本監査はこれを再定義も弱化もしない |
| `backend/temples/data/shrines_seed_clean.json` | repository の現在の canonical 入力値 | Seed data |
| Production Shrine snapshot | Production の現在値 | read-only snapshot **file**（後述の SQL で取得） |
| Candidate Master / Position Resolution Record | candidate_id・過去の判断・採用記録・凍結 source metadata | **evidence / history**。自動的な「現在の外部真値」ではない |
| Spreadsheet snapshot | 外部 evidence の索引 | **Evidence Index**。単独では Ground Truth ではない |
| Primary Position Evidence | Position Contract に適合する一次位置資料 | 採用判断の主根拠 |
| Corroboration（OSM / Wikidata / 他 map provider 等） | 独立確認 | **単独で AUTO_PASS へ昇格させない** |

### Production snapshot の取得

取得と評価は**別ステップ**である。監査 core は ambient credential を要求しない。

```bash
scripts/migration_safety/readonly_query.sh \
  ~/.config/kami-musubi/production-db.env DATABASE_URL \
  scripts/migration_safety/sql/shrine_position_audit_snapshot.sql \
  > /path/outside/repo/production-position-snapshot.txt
```

`scripts/migration_safety/sql/shrine_position_audit_snapshot.sql` は
**SELECT 1文のみ**の専用ファイルであり、既存の
`shrine_identity_reconciliation.sql`（W0-B02 Gate の契約）とは分離している。
あちらに列を足すと Gate 側の契約が壊れるため、変更していない。

出力 field: `id` / `name_jp` / `address` / `latitude` / `longitude` / `kind` /
`place_ref_id`。

### Spreadsheet snapshot

`--spreadsheet-snapshot PATH` で明示的に受け取る（`.json` / `.csv`）。
live Google Sheets 認証は監査 core の要件にしない。

運用データを含む snapshot は、既存の repository policy が明示的に許可しない限り
**commit しない**。本 PR も snapshot を commit していない。

### Primary Position Evidence の live retrieval

本実装は evidence を**データとして受け取る**構造にしてあり、live fetch を
core に埋め込んでいない。live retrieval を実装する場合の制約:

- 取得してよいのは明示された `position_source_url` / `official_source_url` のみ
- 検索エンジンによる広域探索を行わない
- 代替 URL を発明しない
- timeout / fetch / parser 失敗は **fail closed で `REVIEW`**
- テストは fixture のみ。live network に出ない

## 3. Identity Join 契約

### Seed ↔ Production

exact `(name_jp, address)` のみで突合する。

- normalization しない
- fuzzy matching しない
- 座標による救済をしない
- Production 行はちょうど1件を要求する

失敗状態: `MISSING_SEED` / `MISSING_PRODUCTION` / `DUPLICATE_MATCH` /
`IDENTITY_REVIEW_REQUIRED`。
snapshot 自体が無い場合は `PRODUCTION_SNAPSHOT_UNAVAILABLE` とし、
`MATCH_EXACT` を騙らせない。

### Production ↔ Spreadsheet

fallback 順:

1. normalized `official_name` + `official_address` の unique match → `JOIN_EXACT`
2. name または address の一致を `google_place_id` が corroborate → `JOIN_CORROBORATED`
3. name または address の一致を coordinate evidence が corroborate → `JOIN_CORROBORATED`
4. 同一 id かつ corroborating identity field が1つ以上 → `JOIN_CORROBORATED`

**Spreadsheet の id 単独では identity を成立させない。**
**座標単独でも identity を成立させない。**
fuzzy 類似は `JOIN_REVIEW_CANDIDATE` を作るだけで、自動 match にしない。

## 4. 比較正規化

正規化は**比較専用**であり、永続値を書き換えない。

| 対象 | 行うこと |
| --- | --- |
| 名称 | Unicode NFKC / 前後空白 / 連続空白 |
| 住所 | Unicode NFKC / `日本、` prefix / 郵便番号 prefix / 全角 ASCII 数字（NFKC）/ dash 異体字 / 空白 |

**丁目・番・番地・号 の意味的な書き換えは行わない。** その変換を所有する
テスト済みの既存 utility が repository に無いため、過剰正規化して別地番を
同一視するより fail closed（差分として表面化）を選ぶ。

## 5. Triage 契約

Position Contract の canonical status（`PASS` / `HOLD_POSITION_REVIEW`）は
変更しない。本監査はその上に **audit status** を重ねるだけである。

```text
AUTO_PASS  必要な evidence がすべて machine-verifiable
REVIEW     evidence は存在しうるが human interpretation が必要
HOLD       必要な evidence または identity certainty が欠けている
```

判定は `HOLD > REVIEW > AUTO_PASS` の優先順で決まる。

### AUTO_PASS の必要条件（すべて）

- Seed ↔ Production が exact 1:1
- Spreadsheet identity が `JOIN_EXACT` または `JOIN_CORROBORATED`
- 有効な primary position source が存在する
- primary source が取得可能、または有効な現行 Resolution Record で代替されている
- source が指す entity が同一 Shrine であると示せる
- primary 座標が追跡可能
- Seed と Production の座標が同値
- Production 座標が採用済み / 検証済み position と一致する
- identity / address / coordinate に説明不能な conflict が無い
- wrong-entity / non-shrine evidence が無い

### 既存 PASS Resolution Record の再利用

次を**すべて**満たすときだけ、外部 position の判断を代替できる。

```text
current Seed == current Production == recorded adopted coordinate
```

かつ、より新しい evidence が record と矛盾していないこと。
矛盾する場合は `PRIMARY_COORDINATE_DIFFERS` として `REVIEW` に倒れ、
自動再利用しない。

### REVIEW と HOLD の区別

```text
REVIEW = evidence は存在しそうだが、人間の解釈が要る
HOLD   = 必要な evidence または identity の確からしさ自体が無い
```

### Reason codes

| status | reason_code |
| --- | --- |
| AUTO_PASS 根拠 | `SEED_PRODUCTION_EXACT` / `PRIMARY_SOURCE_VERIFIED` / `RESOLUTION_RECORD_REUSED` |
| HOLD | `MISSING_SEED` / `MISSING_PRODUCTION` / `DUPLICATE_PRODUCTION_IDENTITY` / `IDENTITY_NOT_EXACT` / `PRODUCTION_SNAPSHOT_UNAVAILABLE` / `PRIMARY_SOURCE_MISSING` / `PRIMARY_SOURCE_WRONG_ENTITY` / `PRIMARY_SOURCE_NON_SHRINE_ENTITY` / `PRIMARY_COORDINATE_UNTRACEABLE` / `AMBIGUOUS_SAME_NAME_SHRINE` / `IDENTITY_EVIDENCE_MISSING` / `POSITION_CONTRACT_HOLD_RECORD` |
| REVIEW | `PRIMARY_COORDINATE_DIFFERS` / `SOURCE_PARSE_FAILED` / `SOURCE_FETCH_FAILED` / `PRIMARY_EVIDENCE_NOT_RETRIEVED` / `ADDRESS_CONFLICT_UNEXPLAINED` / `CORROBORATION_CONFLICT` / `MULTIPLE_POI_CANDIDATES` / `PRIMARY_ENTITY_AMBIGUOUS` / `SPREADSHEET_ROW_MISSING` / `SPREADSHEET_SNAPSHOT_UNAVAILABLE` / `SPREADSHEET_IDENTITY_REVIEW` / `IDENTITY_NORMALIZATION_REQUIRED` / `POSITION_SOURCE_REDIRECTED` / `SEED_PRODUCTION_COORDINATE_DIFFERS` / `RESOLUTION_RECORD_COORDINATE_MISMATCH` |

## 6. 座標比較

Seed ↔ Production の同値判定は **Float Comparison Contract v1** を再利用する。

```text
rel_tol = 0
abs_tol = 1e-12
```

これは PostgreSQL の `extra_float_digits=0` による float8 text round-trip
差分を吸収するためのものであり、**実世界の空間的品質の閾値ではない**。

外部 source との差は `coordinate_delta_m` として**報告専用**に計算する。

> **「N m 以内なら PASS」は実装していない。**
> Position Contract はそのような固定閾値を定義していない
>（「本Contractは『何m以内なら自動PASS』という固定閾値を定義しない」）。

## 7. Zero-write guarantee

監査経路に write は存在しない。

- Django / ORM を import しない（`save` / `create` / `update` / `delete` なし）
- DB driver（psycopg 等）を import しない。DB へ接続しない
- network client（requests / httpx / urllib 等）を import しない
- Spreadsheet への書き戻し経路を持たない
- file への書き込みは `--output-json` / `--output-md` で指定された report のみ

これは文字列一致ではなく **AST** で固定している
（`scripts/tests/test_audit_shrine_positions_v2.py`）。

- `test_audit_module_has_no_write_path` — 禁止 import root と禁止呼び出し attr を構文木で検査
- `test_audit_module_writes_only_the_requested_report_files` — `write_text` の対象が `args.output_json` / `args.output_md` だけであることを固定

Production snapshot SQL も既存 guard で read-only を確認している。

```bash
python3 scripts/migration_safety/guard.py check-readonly-sql \
  scripts/migration_safety/sql/shrine_position_audit_snapshot.sql
# SAFE: ok
```

## 8. CLI

```bash
python scripts/audit_shrine_positions_v2.py \
  --production-snapshot PATH \
  --spreadsheet-snapshot PATH \
  --output-json PATH \
  --output-md PATH \
  [--candidate-ids wave0-007 wave0-008 ...] \
  [--batch W0-DB02]
```

監査は Gate ではないため、`HOLD` / `REVIEW` があっても exit code は 0 を返す。
判定は report を読んで人間が行う。

## 9. 出力

JSON は `sort_keys=True` / `indent=2` で決定性を持たせ、同一入力からは
**byte 単位で同一**の出力になる。

```text
schema_version
totals { total, auto_pass, review, hold }
reason_code_counts
unresolved_input_dependencies
results[] {
  candidate_id, production_id, name_jp,
  join_status, spreadsheet_join_status, audit_status, reason_codes[],
  stored_address, official_address,
  stored_latitude, stored_longitude,
  seed_latitude, seed_longitude,
  primary_latitude, primary_longitude,
  coordinate_delta_m,
  primary_source_type, primary_source_url,
  corroboration_sources[],
  existing_resolution_record, verified_at
}
```

Markdown summary は集計 / `AUTO_PASS` 行 / `REVIEW` 行 / `HOLD` 行 /
未解決の入力依存を含む。

## 10. W0-DB02 pilot

対象: 射水神社 / 別小江神社 / 戸隠神社 中社 / 札幌諏訪神社 / 少彦名神社

pilot は**この5社が正しいと仮定しない**。目的は、Position Audit v2 が
human map QA で既に見えている差異を再現・表面化できるかを確かめることである。

### 実行条件（重要）

本 PR の pilot は **input-incomplete モード**で実行した。

```text
production snapshot  = 未取得（本実行環境に Production credential が存在しない）
spreadsheet snapshot = 未取得（運用データを commit しない方針）
```

Production snapshot の取得は sanctioned な read-only credential bridge を
必要とし、監査の設計上**取得と評価は別ステップ**である。したがって本 PR で
実行できたのは「入力が欠けたときに pipeline が fail closed するか」の確認である。

### 結果

```text
total     = 5
AUTO_PASS = 0
REVIEW    = 0
HOLD      = 5
```

| candidate_id | name_jp | audit_status | reason_codes |
| --- | --- | --- | --- |
| `wave0-007` | 射水神社 | `HOLD` | `PRIMARY_SOURCE_MISSING`, `PRODUCTION_SNAPSHOT_UNAVAILABLE`, `SPREADSHEET_SNAPSHOT_UNAVAILABLE` |
| `wave0-008` | 別小江神社 | `HOLD` | 同上 |
| `wave0-009` | 戸隠神社 中社 | `HOLD` | 同上 |
| `wave0-010` | 札幌諏訪神社 | `HOLD` | 同上 |
| `wave0-011` | 少彦名神社 | `HOLD` | 同上 |

全5社が status と reason_codes を受け取り、入力欠落が
`unresolved_input_dependencies` として明示された。
**座標は1件も変更していない。**

生成物:

- `docs/audit/position-audit-v2/w0-db02-pilot.json`
- `docs/audit/position-audit-v2/w0-db02-pilot.md`

同一入力で2回実行し、JSON / Markdown とも byte 単位で一致することを
`cmp` と `sha256sum` で実測した。

### 注意: この pilot は triage の実質を示していない

`HOLD` × 5 は「5社の position が悪い」という意味では**ない**。
「Production / Spreadsheet の入力が無いので判定できない」という意味である。
この区別を取り違えてはならない。

実質的な pilot は、Mother Ship 側で snapshot を取得してから再実行する。

```bash
scripts/migration_safety/readonly_query.sh \
  ~/.config/kami-musubi/production-db.env DATABASE_URL \
  scripts/migration_safety/sql/shrine_position_audit_snapshot.sql \
  > /path/outside/repo/production-position-snapshot.txt

python scripts/audit_shrine_positions_v2.py \
  --batch W0-DB02 \
  --production-snapshot /path/outside/repo/production-position-snapshot.txt \
  --spreadsheet-snapshot /path/outside/repo/spreadsheet-snapshot.json \
  --output-json /path/outside/repo/w0-db02-pilot.json \
  --output-md   /path/outside/repo/w0-db02-pilot.md
```

なお `wave0-010`（札幌諏訪神社）は Position Resolution Record
（`position_status = PASS`、adopted `43.07603505258046 / 141.3540979693115`）を
repository から正しく読めており、Production snapshot が入れば
Resolution Record 再利用経路が評価される。
`scripts/tests/test_audit_shrine_positions_v2.py::test_repository_resolution_records_are_loadable`
が実ファイルに対してこれを固定している。

## 11. 既知の限界

1. **Primary evidence の live retrieval は未実装。**
   evidence はデータとして受け取る構造のみを提供している。取得器を足すまで、
   Resolution Record で代替できない行は `PRIMARY_EVIDENCE_NOT_RETRIEVED`
   （`REVIEW`）または `PRIMARY_SOURCE_MISSING`（`HOLD`）に倒れる。

2. **本 PR の pilot は入力不足のため triage の実質を示していない。**（§10）

3. **住所の意味的正規化を持たない。**
   丁目 / 番 / 番地 / 号 の表記揺れは同一視されず、差分として表面化する。
   過剰正規化より fail closed を選んだ結果であり、`REVIEW` が増える方向に効く。

4. **`google_place_id` による corroboration は Production 側 place_id を要求する。**
   現行 snapshot は `place_ref_id`（内部 FK）までしか持たず、外部 place_id を
   持たない。したがって join rule 2 は Spreadsheet 側に place_id があっても
   Production 側の値が供給されるまで発火しない。`--production-place-id` 相当の
   入力経路は未実装。

5. **`AMBIGUOUS_SAME_NAME_SHRINE` / `IDENTITY_EVIDENCE_MISSING` /
   `CORROBORATION_CONFLICT` / `IDENTITY_NORMALIZATION_REQUIRED` は
   reason code として定義済みだが、現時点で発火させる判定器を持たない。**
   evidence retrieval と同名神社の解決器を足す段階で接続する。

6. **`coordinate_delta_m` は報告値であり、判定には使われない。**
   距離を閾値化したくなったら、まず Position Contract 側の変更が必要である。
   本監査を理由に閾値を導入してはならない。

## 12. 参照

- `docs/knowledge/shrine-position-contract.md`（Position 採用ルールの authority）
- `docs/audit/shrine-position/sapporo-suwa-jinja-position-resolution.md`（`wave0-010` の Position Resolution Record / 採用判断履歴）
- `docs/knowledge/shrine-expansion-candidate-master-contract.md`（Candidate lifecycle の Contract）
- `scripts/migration_safety/README.md`（read-only credential bridge）
