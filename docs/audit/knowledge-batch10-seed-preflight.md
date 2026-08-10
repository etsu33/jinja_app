> **Status: `BATCH10_PRODUCTION_IMPORT_READY_WITH_LIMITATIONS`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch10-target-selection.md`
> （`BATCH10_TARGET_SELECTION_READY_WITH_LIMITATIONS`）で選定された推奨5社
> について、Knowledge seedを構築し、Production投入直前の技術Gateまで検証
> した記録である。
>
> **本ドキュメント作成のセッションでは、Production Knowledge writeは
> 実行していない。** 実行したのは、Production read-only接続（既存
> `readonly_query.sh`、`docs/audit/readonly-query-hostname-redaction.md`で
> hostname漏出を修復済みのもの経由）、公式サイトのfresh確認
> （`WebFetch`）、ローカルDBへの実際のseed投入・検証、fresh Production
> dumpから復元したisolated DBへの実際のseed投入・検証、そして
> Production DBに対する`--validate-only`・`--dry-run`（いずれも
> DB書き込みを一切行わないモード）のみである。Production DB writeは0件。
>
> **追記（後続セッション）**: Mother Ship承認後、
> `docs/audit/knowledge-batch10-production-import-execution.md`
> （`BATCH10_PRODUCTION_IMPORT_EXECUTED`）でProduction Knowledge Data
> importを実際に実行済み。本ドキュメントの内容自体は実行前時点の
> As-Isとして書き換えていない。

# Knowledge Batch 10 Seed Preflight — Mother Ship Report

## Executive Summary

Batch 10投入候補5社（大國魂神社・寒川神社・浅草神社・川越氷川神社・
芝大神宮）のKnowledge seed（`backend/temples/data/knowledge_seeds/
batch_10_seed.json`）を新規構築した。全5社は`docs/audit/
knowledge-batch10-target-selection.md`のRecommended 5と一致し、fresh
Production read-only接続で識別安全性のdriftが0件であることを再確認した。

Source 6件はすべて神社公式サイトを`WebFetch`で直接確認し、Production
既存70件との意味的競合は0件（`NO_CONFLICT`）。Deity 19件・History 10件を
構造化し、全件`source_confirmed`/`high`・Source relation必須の
Evidence Gate要件を満たす。

ローカルDB・fresh Production dump復元isolated DBの両方で`--validate-only`
→`--dry-run`→実import→件数検証→再`--dry-run`（冪等性確認）を実施し、
すべて期待どおりの結果を得た。最後にProduction DBへ`--validate-only`・
`--dry-run`（いずれも読み取り専用）を実行し、isolated DB結果と完全に
一致するplanを確認した。

**Production Knowledge writeは本ドキュメントでは実行していない。**
Mother Shipの明示的な承認後、別セッションでProduction importの実行
Gateへ進む必要がある。

---

## 1. Base state and contracts

develop SHA（作業開始時点）: `6180538d18c6246065276e4a540eaadbc5b866ac`
（PR #2357反映済み、`origin/develop`と同期済み、working tree clean）。

freshに再読した既存contract:

- `docs/audit/knowledge-batch10-target-selection.md`（Recommended 5の出典）
- `docs/knowledge/shrine-knowledge-contract.md`（deity/shrine_history/
  Source契約、Evidence Gate、verification_status/confidence enum）
- `backend/temples/data/knowledge_seeds/batch_9_seed.json`（seed構造の
  テンプレート）
- `backend/temples/services/knowledge_seed.py`（`resolve_shrine`・
  `resolve_source_identity`・`parse_seed`の実装）
- `backend/temples/management/commands/import_shrine_knowledge.py`
  （`--validate-only`/`--dry-run`/適用の3モード実装）

いずれも構造変更なしで再利用可能であることを確認した。

---

## 2. Identity recheck

Production read-only接続（`scripts/migration_safety/readonly_query.sh`、
`docs/audit/readonly-query-hostname-redaction.md`で修復済みのもの）で、
5社をfreshに再確認した（snapshot時刻`2026-08-10 11:05:49+00`）。

| shrine | Production id | `place_ref_id IS NULL` | 同名重複行 | deity_count | history_count |
|---|---:|---|---|---:|---:|
| 大國魂神社 | 25 | true | 1 | 0 | 0 |
| 寒川神社 | 26 | true | 1 | 0 | 0 |
| 浅草神社 | 24 | true | 1 | 0 | 0 |
| 川越氷川神社 | 40 | true | 1 | 0 | 0 |
| 芝大神宮 | 45 | true | 1 | 0 | 0 |

Production集計ベースライン（同時刻）: Source 70・Deity 130・History 96・
Deity–Source relation 143・History–Source relation 101・Knowledge Shrine
51 —`knowledge-batch10-target-selection.md`のPhase 1記録値と完全一致
（drift 0件）。

**全5社が`IDENTITY_SAFE`。** numeric PKはseedへ記録しない（`name_jp`+
`address`のnatural keyのみ使用）。

---

## 3. Official Sources and Evidence Gate

5社すべての公式サイトを`WebFetch`でfreshに直接確認した。

| shrine | Source URL | 確認内容 |
|---|---|---|
| 大國魂神社 | ookunitamajinja.or.jp/yuisho/ | 主祭神・配祀六所・創建（景行天皇41年）・武蔵国府設置 |
| 寒川神社 | samukawajinjya.jp/about/main-deities.html | 御祭神二柱（寒川比古命・寒川比女命） |
| 寒川神社 | samukawajinjya.jp/about/history.html | 創建伝承・承和十三年（846）『続日本後紀』記録 |
| 浅草神社 | asakusajinja.jp/asakusajinja/about/ | 御祭神三柱（檜前浜成・檜前武成・土師真中知）・628年由緒・明治6年改称 |
| 川越氷川神社 | kawagoehikawa.jp/shoukai/ | 御祭神5柱（家族神構成）・541年創建・昭和23年祭具発掘 |
| 芝大神宮 | shibadaijingu.com/goyuisyo/ | 御祭神二柱（天照皇大御神・豊受大御神）・1005年創建・源頼朝公の信仰 |

浅草神社の3柱の固有名詞は、初回`WebFetch`の要約では抽出されなかった
ため、対象ページに対して固有名詞抽出に特化した再`WebFetch`を実施し、
「檜前浜成」「檜前武成」「土師真中知」を直接確認した。

**Source semantic conflict check（Production既存70件との突合、
`url ILIKE`による全ドメイン一致検索）: 0件一致。全6候補Sourceが
`NO_CONFLICT`。**

**Evidence Gateスコープ判断**: 大國魂神社の公式由緒には「御霊大神」
「国内諸神」という記載もあるが、個別神格として特定困難な集合的表記
のため、本seedでは主祭神＋配祀六所の7柱に限定し、これらはFact化して
いない（スコープ判断はseed内の`note`フィールドに明記）。

役割（`role`）は、公式が明示的な序列を示す場合のみ`primary`/
`secondary`を用い、序列不明の場合は`unknown`とした（寒川神社の二柱・
浅草神社の三柱）。川越氷川神社は公式が「主祭神」と明記する素盞嗚尊の
みを`primary`とし、他4柱は`enshrined`とした。

---

## 4. Canonical seed integrity

`backend/temples/data/knowledge_seeds/batch_10_seed.json`
（`schema_version: "1.0"`）。

`parse_seed()`（実装をそのまま使用したstructural検証）:

| 指標 | 値 |
|---|---:|
| errors | 0 |
| Source count | 6 |
| Shrine count | 5 |
| Deity count | 19 |
| History count | 10 |
| Deity–Source relation | 19 |
| History–Source relation | 10 |
| source-less Deity | 0 |
| source-less History | 0 |
| within-shrine重複（同一display_nameまたは同一history_type+title） | 0 |
| invalid enum | 0 |
| unresolved source_key参照 | 0 |

全Fact（Deity 19・History 10）が`verification_status: source_confirmed`
かつ`confidence: high`かつ`verified_at`設定済みであることを確認した
（追加のpytest回帰テストで固定化）。

SHA-256（`batch_10_seed.json`）:
`e44484431af89274c3ba7258e49dac7cd2b186f8d0bfebb62b60137d0b7255d9`

---

## 5. Local validation, import, and regression

新規テスト: `backend/temples/tests/test_batch10_knowledge_seed.py`
（5件、Batch9の`test_batch9_knowledge_seed.py`と同型）。

- スキーマ・件数・relation検証
- shrine内重複ゼロ検証
- 全Fact `source_confirmed`/`high`検証
- import冪等性・既存無関係Knowledge非破壊検証（第2の無関係神社・
  Source・Deity・Historyを作成し、import前後で内容が変化しないことを確認）
- 対象shrineが1社欠けている場合の`--validate-only`失敗検証

既存の汎用テスト（`test_knowledge_seed_import.py`、24件）・Batch9専用
テスト（`test_batch9_knowledge_seed.py`、2件）を含め、合計32件すべて
PASS（回帰なし）。source-less拒否・重複検知・semantic Source reuse
（REUSE/AMBIGUOUS/CONFLICT）・invalid enum拒否・ambiguous shrine拒否は
既存の汎用テストで既にカバーされており、Batch10固有の重複は作らなかった。

ローカル`jinja_db`（Production構造を反映した開発DB、対象5社は
Production同一idで存在、import前はいずれもdeity=0/history=0を確認
済み）に対して実際に実行:

| step | 結果 |
|---|---|
| `--validate-only` | `validate-only: OK, no errors` |
| `--dry-run`（1回目） | `{'source_CREATE': 6, 'deity_CREATE': 19, 'history_CREATE': 10}` |
| 適用（import） | `sources created=6, deities created=19, histories created=10` |
| 件数検証 | Source 73→79（+6）・Deity 130→149（+19）・History 96→106（+10）、対象5社の内訳は7/2/3/5/2件（seedと完全一致）、source-less 0件 |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 6, 'deity_SKIP_EXISTS': 19, 'history_SKIP_EXISTS': 10}`、CREATE 0件 |

---

## 6. Fresh Production-equivalent test

Production PostgreSQLバージョンをread-only確認（`SELECT version();`）
した結果`PostgreSQL 17.6`であったため、バージョン一致するHomebrew
`postgresql@17`クライアント（`pg_dump`/`pg_dumpall` 17.10）で
`dump_readonly.sh`を実行した。

```
[dump_readonly] roles.sql: 5426 bytes
[dump_readonly] schema.sql: 93021 bytes
[dump_readonly] data.sql: 4105505 bytes
[dump_readonly] done.
```

接続情報（hostname/user/password/port/database名）はログに一切出力
されなかった。ダンプ先はrepo外（`~/kami-musubi-backups/<timestamp>/`）。

ローカルPostgreSQLサーバーが18.0であることを確認し、バージョン一致する
`postgresql@18`クライアントで`restore_isolated.sh`を実行し、
`kami_musubi_migration_safety_b10s_<timestamp>`（`migration_safety`
markerを含む、guard.pyのallow-listで許可される disposable local DB）へ
復元した。復元は`exit 0`で完了。

復元直後のisolated DB確認:

| 指標 | isolated DB（復元直後） | Production（同時刻read-only） |
|---|---:|---:|
| Source | 70 | 70 |
| Deity | 130 | 130 |
| History | 96 | 96 |
| Deity–Source relation | 143 | 143 |
| History–Source relation | 101 | 101 |
| 対象5社 deity/history | 全件0 | 全件0 |

**完全一致。** isolated DBに対して、ローカルと同一の5ステップ
（`--validate-only`→`--dry-run`→適用→件数検証→`--dry-run`再実行）を実施:

| step | 結果 |
|---|---|
| `--validate-only` | OK, no errors |
| `--dry-run`（1回目） | `{'source_CREATE': 6, 'deity_CREATE': 19, 'history_CREATE': 10}` |
| 適用 | `sources created=6, deities created=19, histories created=10` |
| 件数検証 | Source 70→76・Deity 130→149・History 96→106・Deity–Source rel 143→162・History–Source rel 101→111（いずれもseed件数と完全一致） |
| 対象5社のdeity内訳 | 大國魂神社7・寒川神社2・浅草神社3・川越氷川神社5・芝大神宮2（seedと完全一致、混入なし） |
| source-less（対象5社） | Deity 0・History 0 |
| 無関係データ回帰チェック | 宇佐神宮3/1・箱根神社3/1・貴船神社2/1（いずれもBatch9 seedの値のまま、変化なし） |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 6, 'deity_SKIP_EXISTS': 19, 'history_SKIP_EXISTS': 10}`、CREATE 0件 |

isolated DBは検証完了後に`dropdb`で削除済み。dumpファイル自体は
repo外に残置（コミットしない）。

---

## 7. Coverage projection

isolated DB（Production-equivalent）の実測値から算出（推測値は使用
していない）。

| 区分 | Batch10投入前（実測） | Batch10投入後（実測） |
|---|---:|---:|
| complete（Deity>0 かつ History>0） | 49 | 54 |
| partial（Deity>0 または History>0のいずれか） | 2 | 2（不変） |
| none | 54 | 49 |
| Knowledge Shrine合計（complete+partial） | 51 | 56 |
| 全Shrine数 | 105 | 105（不変） |

partial 2件（阿佐ヶ谷神明宮・香取神宮、`knowledge-batch9-closure-
batch10-reentry.md`記載）は本Batchの対象外のため不変。対象5社は
いずれも投入前`none`→投入後`complete`へ移行する。

---

## 8. Production read-only preflight

Production DBに対して以下を実行した（いずれもコマンド自身の設計上、
DB書き込みを一切行わないモード。`_apply()`は呼び出されない）。

**`--validate-only`**:

```
validate-only: OK, no errors
```

**`--dry-run`**:

```
plan summary: {'source_CREATE': 6, 'deity_CREATE': 19, 'history_CREATE': 10}
dry-run: OK, no DB writes performed
```

全項目、isolated DB（Section 6）の1回目`--dry-run`結果と完全一致。
`SKIP_EXISTS`・`REUSE_EXISTING`・`SOURCE_REUSE_CONFLICT`・
`SOURCE_REUSE_AMBIGUOUS`・`IMPORT_IDENTITY_AMBIGUOUS`・`NOT_FOUND`は
いずれも0件。unexpected SKIP/UPDATE/conflictは検出されなかった。

実行後、`readonly_query.sh`で再度Production状態を確認し、対象5社の
deity/history、および集計値（Source 70・Deity 130・History 96・
relation 143/101・Knowledge Shrine 51）が実行前と完全に不変であること
を確認した（`--validate-only`/`--dry-run`はDB書き込みを行わないという
コマンド自身の設計を実測でも再確認）。

---

## 9. Runtime expected payload

seedから算出（Production import実行後に期待される値、実行はしていない）。

| 指標 | 値 |
|---|---:|
| Deity count | 19 |
| History count | 10 |
| Unique Source count | 6 |
| Fact–Source relation count | 29（Deity 19 + History 10） |

---

## 10. Remaining risks and Mother Ship decision

- 大國魂神社の「御霊大神」「国内諸神」はスコープ外とした（個別神格の
  特定困難）。将来的にこれらを構造化する場合は別途Sourceでの追加確認
  が必要。
- 靖國神社は本Batchに含めていない（`knowledge-batch10-target-
  selection.md`で明示した祭神content設計判断が引き続き未解決のため）。
- 本ドキュメントの検証はすべてProduction-equivalentまたは
  Production read-only（`--validate-only`/`--dry-run`）の範囲であり、
  実際のProduction Fact表示・Runtime QA（Batch8/9で実施したHTTPレベル
  QA相当）は、Production importが実行された後でなければ実施できない。

### Final Classification

**`BATCH10_PRODUCTION_IMPORT_READY_WITH_LIMITATIONS`**

READYと判断する根拠:

- 5社全件が`IDENTITY_SAFE`・`NO_CONFLICT`・Evidence Gate要件を満たす
- ローカル・Production-equivalent（fresh dump復元）の両方で
  `--validate-only`→`--dry-run`→適用→件数検証→再`--dry-run`の
  フルサイクルが期待どおりの結果
- Production DBに対する`--validate-only`・`--dry-run`が
  Production-equivalentの結果と完全一致し、unexpected SKIP/UPDATE/
  conflictが0件
- Production状態がこれらの読み取り専用操作の前後で完全に不変であることを
  実測で確認

`WITH_LIMITATIONS`とする理由:

- 靖國神社の祭神content設計判断が未解決のまま
- Production importそのもの（Fact実書き込み・Runtime QA）は本
  ドキュメントでは未実施。Mother Shipの明示的な承認後、別セッション
  （Human Execution Boundary Gate相当）で実施する必要がある

Production DB writes = 0
Batch 10 Production import = NOT_EXECUTED
Batch 11 = NOT_STARTED
