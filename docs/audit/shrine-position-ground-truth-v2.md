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

`place_ref_id` は `PlaceRef.place_id`（`CharField(primary_key=True)`）への
FK 値であり、**Google Place ID の文字列**である。内部の連番 id ではない。
したがって Spreadsheet の `google_place_id` と直接突合でき、join rule 2
（place_id corroboration）の Production 側入力として使う。

### Spreadsheet snapshot

`--spreadsheet-snapshot PATH` で明示的に受け取る（`.json` / `.csv`）。
live Google Sheets 認証は監査 core の要件にしない。

運用データを含む snapshot は、既存の repository policy が明示的に許可しない限り
**commit しない**。本 PR も snapshot を commit していない。

### Primary Position Evidence snapshot

`--primary-evidence-snapshot PATH` で明示的に受け取る（`.json` / `.csv`）。
**live retrieval は行わない。** file 入力のみである。

各行は次の field を持つ。

```text
status                 OK / NOT_RETRIEVED / FETCH_FAILED / PARSE_FAILED / REDIRECTED
source_type
source_url
source_name
source_address
latitude
longitude
entity_match           SAME / DIFFERENT / NON_SHRINE / AMBIGUOUS
poi_candidate_count
verified_at
```

対象 Shrine は次のいずれかで指す（両方あっても良い）。

- `candidate_id`
- verified shrine identity = `official_name` + `official_address`

どちらも無い行は identity を推測せず `AuditError` にする（fail closed）。
未知の `status` も拒否する。

`build_inputs()` はこの snapshot から `primary_position_evidence` を実際に
埋める。CLI から評価まで一本で到達する経路である。

将来 live retrieval を足す場合の制約:

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
  （Resolution Record 経路も **同じ provenance 要件**を満たすこと）
- source が指す entity が **同一 Shrine であると示せる**
  （`evidence.status == "OK"` かつ `evidence.entity_match == "SAME"`）
- primary 座標が追跡可能
- **primary-source provenance が追跡可能**
  （effective な `source_type` / `source_url` / `verified_at` がすべて存在する）
- Seed と Production の座標が同値
- Production 座標が採用済み / 検証済み position と一致する
- identity / address / coordinate に説明不能な conflict が無い
- wrong-entity / non-shrine evidence が無い

### entity 同定は fail closed

`PRIMARY_SOURCE_VERIFIED` は次を**すべて**満たすときにしか出さない。

```text
evidence.status       == "OK"
evidence.entity_match == "SAME"   （大小文字・前後空白は無視）
latitude / longitude  が追跡可能
```

`entity_match` が未設定 / 空 / 未知の値のときは「同一だと示せていない」の
であって「同一である」ではない。したがって:

| `entity_match` | 扱い |
| --- | --- |
| `SAME` | `PRIMARY_SOURCE_VERIFIED`（AUTO_PASS 資格あり） |
| `DIFFERENT` | `PRIMARY_SOURCE_WRONG_ENTITY` → `HOLD` |
| `NON_SHRINE` | `PRIMARY_SOURCE_NON_SHRINE_ENTITY` → `HOLD` |
| `AMBIGUOUS` | `PRIMARY_ENTITY_AMBIGUOUS` → `REVIEW` |
| None / 空 | `IDENTITY_EVIDENCE_MISSING` → `HOLD` |
| 上記以外の未知値 | `PRIMARY_ENTITY_AMBIGUOUS` → `REVIEW` |

Position Contract §Source Adoption Rule の「primary position source が
同一Shrineの POI / place_of_worship / navigation target を示している」を
満たさないまま AUTO_PASS へ倒れることを防ぐ。

### provenance も fail closed

entity が同一だと示せても、**どの source をいつ確認したのかを示せなければ
machine-verified とは言えない**。Position Contract §Audit Record は
`position_source_type` / `position_source_url` / `verified_at` を追跡可能に
することを求めている。

したがって `PRIMARY_SOURCE_VERIFIED` は次を**すべて**満たすときにしか出さない。

```text
evidence.status       == "OK"
evidence.entity_match == "SAME"
latitude / longitude          が存在する
effective source_type         が存在する
effective source_url          が存在する
effective verified_at         が存在する
```

#### effective provenance の解決順

`PrimaryPositionEvidence` を優先し、**欠けている field だけ** joined
Spreadsheet 行で補う。

```text
source_type   = evidence.source_type   or spreadsheet.position_source_type
                                       or spreadsheet.official_source_type
source_url    = evidence.source_url    or spreadsheet.position_source_url
                                       or spreadsheet.official_source_url
verified_at   = evidence.verified_at   or spreadsheet.verified_at
```

evidence snapshot 側に source metadata を**重複させることは要求しない**。
joined Spreadsheet が同じ traceable source を持つならそれで足りる。

出力の `verified_at` もこの解決順に従う（evidence が優先）。

#### 欠落時の扱い

| 欠落 | reason_code | status |
| --- | --- | --- |
| effective `source_url` | `PRIMARY_SOURCE_MISSING` | `HOLD` |
| effective `source_type` | `PRIMARY_SOURCE_TYPE_MISSING` | `REVIEW` |
| effective `verified_at` | `PRIMARY_SOURCE_VERIFIED_AT_MISSING` | `REVIEW` |

provenance が不完全なまま黙って `AUTO_PASS` にはしない。
`PRIMARY_COORDINATE_DIFFERS` の観測は provenance の充足とは独立に行い、
差があれば併せて表面化する。

### 既存 PASS Resolution Record の再利用

> **Resolution Record 再利用は provenance bypass ではない。**
> 他の AUTO_PASS 経路とまったく同じ traceability を満たす必要がある。

次を**すべて**満たすときだけ、外部 position の判断を代替できる。

```text
resolution.position_status      == "PASS"
Seed ↔ Production identity      が exact
current Seed        == recorded adopted coordinate
current Production  == recorded adopted coordinate
resolution.position_source_type が存在する
resolution.position_source_url  が存在する
resolution.verified_at          が存在する
```

record の provenance は Position Resolution Record の次の field から読む。
**fallback 値を発明しない。**

```text
new_position_source_type  ->  resolution.position_source_type
new_position_source_url   ->  resolution.position_source_url
verified_at               ->  resolution.verified_at
```

#### candidate と reusable を分ける（path isolation）

Resolution Record の provenance 欠落は **Resolution 再利用経路だけ**を塞ぐ。
有効な `PrimaryPositionEvidence` 経路を巻き添えにしてはならない。

そのため2つの概念を分離している。

```text
resolution_candidate            PASS + identity exact + Seed/Production 座標一致
resolution_provenance_complete  record 自身の provenance が揃っている
resolution_reusable             上記を満たし、かつ実際に再利用してよい
```

`RESOLUTION_*_MISSING` は「どちらの経路が実際に使われるか」を決めた**後**に
しか出さない。

#### positive な AUTO_PASS 根拠は排他的

`RESOLUTION_RECORD_REUSED` の意味を次に限定する。

> **Resolution Record を fallback proof path として実際に使った。**

したがって `PRIMARY_SOURCE_VERIFIED` が立っているときは
`RESOLUTION_RECORD_REUSED` を**出さない**。evidence 経路が現在の position を
独立に検証できている以上、record は使っていないからである。

Resolution 再利用を使うのは次を**すべて**満たすときだけ。

```text
PrimaryPositionEvidence が現在の position を独立に検証していない
resolution が有効な candidate である
resolution の provenance が完備している
より新しい矛盾 evidence が存在しない
```

履歴としての追跡可能性は出力の `existing_resolution_record` が担う。
これは経路に関係なく常に populate される。

#### 経路ごとの挙動

| 状況 | 結果 |
| --- | --- |
| 有効な evidence なし + record 完備・一致 | `RESOLUTION_RECORD_REUSED` → `AUTO_PASS` |
| 有効な evidence なし + record 不完全 | `RESOLUTION_*_MISSING` で fail closed |
| 有効な evidence なし + record 座標食い違い | `RESOLUTION_RECORD_COORDINATE_MISMATCH` → `REVIEW` |
| **有効な evidence あり + record 完備・一致** | **`PRIMARY_SOURCE_VERIFIED` のみ。`RESOLUTION_RECORD_REUSED` は出さない** |
| **有効な evidence あり + record 不完全** | **evidence 経路を独立に評価。`RESOLUTION_*_MISSING` を出さず降格もしない** |
| **有効な evidence あり + record 座標食い違い** | **`RESOLUTION_RECORD_COORDINATE_MISMATCH` を status に効かせない** |
| evidence が record と矛盾 | `RESOLUTION_RECORD_REUSED` を出さない |

**歴史的 record の座標食い違いで、検証済み evidence 経路を引き下げない。**
`RESOLUTION_RECORD_COORDINATE_MISMATCH` は Resolution 経路に依存している
ときにのみ status を駆動する。

#### provenance 欠落時（Resolution 経路に依存している場合のみ）

| 欠落 | reason_code | status |
| --- | --- | --- |
| `position_source_url` | `RESOLUTION_SOURCE_URL_MISSING` | `HOLD` |
| `position_source_type` | `RESOLUTION_SOURCE_TYPE_MISSING` | `REVIEW` |
| `verified_at` | `RESOLUTION_VERIFIED_AT_MISSING` | `REVIEW` |

provenance が不完全なら `RESOLUTION_RECORD_REUSED` を**出さない**。

#### conflict precedence

より新しい `PrimaryPositionEvidence` が record と矛盾する場合は、provenance が
完備していても `RESOLUTION_RECORD_REUSED` を出さない。**より新しい evidence が
現に矛盾しているのに「record を再利用した」と主張しない。**

矛盾とみなす code:

```text
PRIMARY_COORDINATE_DIFFERS
PRIMARY_SOURCE_WRONG_ENTITY
PRIMARY_SOURCE_NON_SHRINE_ENTITY
PRIMARY_ENTITY_AMBIGUOUS
IDENTITY_EVIDENCE_MISSING
MULTIPLE_POI_CANDIDATES
```

これらは既に `HOLD` / `REVIEW` を生んでいるため、矛盾時に
`RESOLUTION_*_MISSING` を重ねて出すことはしない。

なお **座標不一致**（`RESOLUTION_RECORD_COORDINATE_MISMATCH`）も、
Resolution 経路に依存している場合にのみ出す。evidence 経路が独立に
検証できているなら、過去の record の食い違いは status を駆動しない。

> **freshness threshold は導入しない。**
> 「verified_at が N 日より古ければ stale」という判定は行わない。
> Position Contract は現時点でそのような閾値を定義していない。

#### 出力 provenance

Resolution Record が evidence source であり、かつ新しい
`PrimaryPositionEvidence` が adopted source を供給していない場合、出力は
record 自身の provenance を引き継ぐ。

```text
primary_source_type = resolution.position_source_type
primary_source_url  = resolution.position_source_url
verified_at         = resolution.verified_at
```

これにより、`RESOLUTION_RECORD_REUSED` による AUTO_PASS も出力レベルで
追跡可能なまま保たれる。

### REVIEW と HOLD の区別

```text
REVIEW = evidence は存在しそうだが、人間の解釈が要る
HOLD   = 必要な evidence または identity の確からしさ自体が無い
```

### Reason codes

| status | reason_code |
| --- | --- |
| AUTO_PASS 根拠 | `SEED_PRODUCTION_EXACT` / `PRIMARY_SOURCE_VERIFIED` / `RESOLUTION_RECORD_REUSED` |
| HOLD | `MISSING_SEED` / `MISSING_PRODUCTION` / `DUPLICATE_PRODUCTION_IDENTITY` / `IDENTITY_NOT_EXACT` / `PRODUCTION_SNAPSHOT_UNAVAILABLE` / `PRIMARY_SOURCE_MISSING` / `PRIMARY_SOURCE_WRONG_ENTITY` / `PRIMARY_SOURCE_NON_SHRINE_ENTITY` / `PRIMARY_COORDINATE_UNTRACEABLE` / `AMBIGUOUS_SAME_NAME_SHRINE` / `IDENTITY_EVIDENCE_MISSING` / `POSITION_CONTRACT_HOLD_RECORD` / `RESOLUTION_SOURCE_URL_MISSING` |
| REVIEW | `PRIMARY_COORDINATE_DIFFERS` / `SOURCE_PARSE_FAILED` / `SOURCE_FETCH_FAILED` / `PRIMARY_EVIDENCE_NOT_RETRIEVED` / `ADDRESS_CONFLICT_UNEXPLAINED` / `CORROBORATION_CONFLICT` / `MULTIPLE_POI_CANDIDATES` / `PRIMARY_ENTITY_AMBIGUOUS` / `SPREADSHEET_ROW_MISSING` / `SPREADSHEET_SNAPSHOT_UNAVAILABLE` / `SPREADSHEET_IDENTITY_REVIEW` / `IDENTITY_NORMALIZATION_REQUIRED` / `POSITION_SOURCE_REDIRECTED` / `SEED_PRODUCTION_COORDINATE_DIFFERS` / `RESOLUTION_RECORD_COORDINATE_MISMATCH` / `PRIMARY_SOURCE_TYPE_MISSING` / `PRIMARY_SOURCE_VERIFIED_AT_MISSING` / `RESOLUTION_SOURCE_TYPE_MISSING` / `RESOLUTION_VERIFIED_AT_MISSING` |

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
  --primary-evidence-snapshot PATH \
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
production snapshot       = 未取得（本実行環境に Production credential が存在しない）
spreadsheet snapshot      = 未取得（運用データを commit しない方針）
primary evidence snapshot = 未取得（一次位置資料の検証済み export が未供給）
```

CLI は3つとも消費できる（`--production-snapshot` / `--spreadsheet-snapshot` /
`--primary-evidence-snapshot`）。欠けているのは入力であって経路ではない。

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
「Production / Spreadsheet / Primary evidence の入力が無いので判定できない」
という意味である。この区別を取り違えてはならない。

**実世界の discrepancy pilot は完了していない。** 3つの snapshot が供給される
までは、human map QA で見えている差異を再現できるかは未検証である。

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
  --primary-evidence-snapshot /path/outside/repo/primary-evidence-snapshot.json \
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

1. **Primary evidence の live retrieval は未実装（意図的）。**
   evidence は `--primary-evidence-snapshot` の file 入力としてのみ受け取る。
   snapshot が供給されない行は、Resolution Record で代替できない限り
   `PRIMARY_EVIDENCE_NOT_RETRIEVED`（`REVIEW`）または
   `PRIMARY_SOURCE_MISSING`（`HOLD`）に倒れる。
   evidence の収集そのもの（誰がどう検証して `entity_match` を決めるか）は
   本監査の外側にある運用手順である。

2. **本 PR の pilot は入力不足のため triage の実質を示していない。**（§10）

3. **住所の意味的正規化を持たない。**
   丁目 / 番 / 番地 / 号 の表記揺れは同一視されず、差分として表面化する。
   過剰正規化より fail closed を選んだ結果であり、`REVIEW` が増える方向に効く。

4. **`google_place_id` corroboration は Production 行に `place_ref_id` がある場合のみ効く。**
   `place_ref_id` は `PlaceRef.place_id`（Google Place ID 文字列）であり、
   snapshot から join rule 2 へ配線済みである。ただし `place_ref` が未設定の
   Shrine 行では `None` になるため、その行では rule 2 は発火せず rule 3 / 4 へ
   落ちる。Production 上でどれだけの行が `place_ref` を持つかは未計測。

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
