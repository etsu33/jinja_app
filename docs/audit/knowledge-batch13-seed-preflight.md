> **Status: `BATCH13_PRODUCTION_IMPORT_READY_WITH_LIMITATIONS`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch13-target-selection.md`
> （`BATCH13_TARGET_SELECTION_READY`）で選定されたRecommended 5社
> について、Knowledge seedを構築し、Production投入直前の技術Gateまで
> 検証した記録である。
>
> **本ドキュメント作成のセッションでは、Production Knowledge writeは
> 実行していない。** 実行したのは、Production read-only接続
> （`readonly_query.sh`）、公式サイトのfresh確認（Browser pane）、
> ローカルDBへの実際のseed投入・検証、fresh Production dumpから復元した
> isolated DBへの実際のseed投入・検証、そしてProduction DBに対する
> `--validate-only`・`--dry-run`（いずれもDB書き込みを一切行わない
> モード）のみである。Production DB writeは0件。
>
> `READY_WITH_LIMITATIONS`とした理由は、富岡八幡宮の公式サイトが
> 「御祭神 応神天皇（誉田別命）外８柱」とのみ記載し、他8柱の個別名を
> 明かしていないためである（詳細はSection 5参照）。未確認の8柱は
> 推測登録せず、Evidence Gateを遵守した限定的なFact化を行っている。

develop SHA（作業開始時点）: `42b21690a50b6f8808727344edcacbf6b90ed163`
（PR #2368反映済み、`origin/develop`と同期済み、working tree clean）。

---

## 1. Base state and contracts

`docs/audit/knowledge-batch13-target-selection.md`を再読し、
Recommended 5社を対象として確定した。

freshに再読した既存contract:

- `docs/knowledge/shrine-knowledge-contract.md`
- `backend/temples/data/knowledge_seeds/batch_12_seed.json`（seed構造のテンプレート）
- `backend/temples/services/knowledge_seed.py`
- `backend/temples/management/commands/import_shrine_knowledge.py`

いずれも構造変更なしで再利用可能であることを確認した。

**注記**: 本タスク着手時、`docs/audit/knowledge-batch13-target-selection.md`
を追加するPR #2368がまだmergeされていないことが判明した。Mother Shipの
明示承認を得た上でPR #2368をmerge（squash、`42b21690`）してから本
Seed Preparationに着手した。

---

## 2. Target Identity Recheck（fresh実測）

Production read-only接続で、5社をfreshに再確認した。

| shrine | Production id | `place_ref_id IS NULL` | 同名重複行 | deity_count | history_count |
|---|---:|---|---:|---:|---:|
| 富岡八幡宮 | 49（canonical）／104（非canonical重複） | true／false | 2 | 0 | 0 |
| 忌宮神社 | 95 | true | 1 | 0 | 0 |
| 高良大社 | 96 | true | 1 | 0 | 0 |
| 笠間稲荷神社 | 82 | true | 1 | 0 | 0 |
| 鷲宮神社 | 75 | true | 1 | 0 | 0 |

富岡八幡宮は既知の非canonical重複行（id=104）が存在するが、
`resolve_shrine`の`place_ref_id IS NULL`優先ロジックによりid=49が
一意に解決される（`OK_CANONICAL_PREFERRED`）。**全5社が`IDENTITY_SAFE`。**
numeric PKはseedへ記録しない。

---

## 3. Official Sources（Target Selection時の結果を再利用せずfresh確認）

5社すべての公式サイトをBrowser paneで**再度**直接確認した。取得内容は
Target Selectionセッション時と完全に一致し、drift 0件だった。

| shrine | Source URL | 確認内容 |
|---|---|---|
| 富岡八幡宮 | http://www.tomiokahachimangu.or.jp/annai/goyuisho/goyuisho.html | 「御祭神 応神天皇（誉田別命）外８柱」、寛永4年(1627)創建、准勅祭社 |
| 忌宮神社 | https://iminomiya-jinjya.com/about/ | 仲哀天皇・神功皇后・応神天皇、延喜式内社・長門二宮・旧国幣社 |
| 高良大社 | http://www.kourataisya.or.jp/kourataisya/saiji | 八幡大神・高良玉垂命・住吉大神、仁徳天皇55年(367)/78年(390)伝、旧国幣大社 |
| 笠間稲荷神社 | http://www.kasama.or.jp/about/index.html | 宇迦之御魂神、白雉2年(651)創建伝承、国指定重要文化財本殿 |
| 鷲宮神社 | http://www.washinomiyajinja.or.jp/history/history.html | 天穂日命（本殿）・武夷鳥命（相殿）、関東最古の大社 |

---

## 4. Source Semantic Conflict

5件のSource候補ドメインを、Production既存86件のSourceとfreshに突合した。

- exact-domain照合: 5件全てProduction既存Sourceに一致なし
- `normalize_source_url()`実装をそのまま使用した精密照合（既存85件の
  URL保有Sourceと突合）: 5件全て一致なし

**5候補Sourceすべてが`NO_CONFLICT`。**

---

## 5. Deity Research（各社固有の判断）

### 富岡八幡宮（completeness limitation）

公式サイトは「御祭神 応神天皇（誉田別命）外８柱」とのみ記載し、他8柱の
個別名を明かしていない。以下のルールを厳守した。

- 応神天皇（誉田別命）のみFact化（`role: primary`）
- 未確認の他8柱を外部一般知識・推測で補完しない
- 「他8柱」「外8柱」をcollective deity Factとして作成しない
- Source `note`に、公式サイトの記載範囲の制約を明示

この結果、富岡八幡宮のDeity Factは1件のみとなる。History（創建
寛永4年・准勅祭社宣下）は公式記載どおりHIGH Evidenceで2件Fact化した。

### 忌宮神社

公式サイトから仲哀天皇（`role: primary`、当社の起源となった祭神）・
神功皇后（`role: secondary`）・応神天皇（`role: secondary`）をfresh
確認し、3柱ともFact化した。

### 高良大社

公式サイトから八幡大神（`role: secondary`、本殿向かって右）・
高良玉垂命（`role: primary`、本殿中央）・住吉大神（`role: secondary`、
本殿向かって左）をfresh確認し、3柱ともFact化した。

### 笠間稲荷神社

公式サイトから宇迦之御魂神（`role: primary`、唯一の御祭神）をfresh
確認し、Fact化した。

### 鷲宮神社

公式サイトから天穂日命（`role: primary`、現本殿の祭神）・武夷鳥命
（`role: secondary`、景行天皇御世に相殿へ奉祀）をfresh確認した。由緒
冒頭に登場する「神崎神社（大己貴命）」は、天穂日命父子が鷲宮神社創建
以前に別途建立した**別の神社**の祭神であり、鷲宮神社自体の祭神ではない
ため、Fact化対象から明確に除外した。

**禁止事項の遵守確認**: 富岡八幡宮の未確認8柱の推測登録＝0件、collective
deity placeholder＝0件、war memorial/collective spirit混入＝0件
（高良大社の「武内宿禰像」は博多人形の作品名であり祭神ではないため
Fact化していない）、神仏習合対象の恣意的kami化＝該当なし、摂社/末社
Fact混入＝0件。

---

## 6. History Research

各社の由緒を、既存`history_type` enumへ適合する範囲でFact化した。神話的
創建伝承（`tradition`）と、年代が特定できる歴史的出来事（`historical_event`）
を明確に分離し、伝承文には「〜と伝えられている」等の非断定表現を用いた
（fresh確認: 全4件のtradition Factで確認済み）。

| shrine | History Fact | 分類 |
|---|---|---|
| 富岡八幡宮 | 寛永4年(1627)の創建 | founding |
| 富岡八幡宮 | 明治維新の准勅祭社宣下と徳川将軍家の崇敬 | historical_event |
| 忌宮神社 | 仲哀天皇御神霊の鎮祭伝承 | tradition |
| 忌宮神社 | 延喜式内社・長門二宮としての社格 | historical_event |
| 高良大社 | 仁徳天皇御代の御鎮座伝承 | tradition |
| 高良大社 | 蒙古襲来時の勅使参向と綸旨 | historical_event |
| 笠間稲荷神社 | 白雉2年(651)の創建伝承 | tradition |
| 笠間稲荷神社 | 御本殿の国重要文化財指定 | historical_event |
| 鷲宮神社 | 出雲族草創の伝承と関東最古の大社 | tradition |
| 鷲宮神社 | 明治天皇御世の准勅祭社宣下 | historical_event |

高良大社の歴代神階等の詳細な朝廷記録は、公式サイトに記載された蒙古襲来
時の綸旨の範囲に限定し、根拠以上の年代断定を行っていない。長文の原文
転載は行わず、要約に留めた。

---

## 7. Evidence Gate

全10 Deity・10 History Factについて確認した。

| 指標 | 値 |
|---|---:|
| source-less Deity | 0 |
| source-less History | 0 |
| `verification_status`が`source_confirmed`以外 | 0 |
| `confidence`が`high`以外 | 0 |
| `verified_at`未設定 | 0 |
| invalid enum | 0 |
| identity unsafe | 0 |
| semantic conflict unsafe | 0 |

全件がEvidence Gate要件を満たす。

---

## 8. Canonical seed integrity

`backend/temples/data/knowledge_seeds/batch_13_seed.json`
（`schema_version: "1.0"`）。

`parse_seed()`（実装をそのまま使用したstructural検証）:

| 指標 | 値 |
|---|---:|
| errors | 0 |
| Source count | 5 |
| Shrine count | 5 |
| Deity count | 10 |
| History count | 10 |
| Deity–Source relation | 10 |
| History–Source relation | 10 |
| source-less Deity | 0 |
| source-less History | 0 |
| within-shrine重複 | 0 |
| invalid enum | 0 |
| unresolved source_key参照 | 0 |
| 数値Production PKのhardcode | 0 |

SHA-256（`batch_13_seed.json`）:
`512225777c5509a8c75d142a276473495717e6a947d3d60699e02b156b20b9b2`

---

## 9. Regression tests

新規: `backend/temples/tests/test_batch13_knowledge_seed.py`（9件）。
Batch12の`test_batch12_knowledge_seed.py`と同型の構成に加え、本Batch
固有の以下を追加した。

- `test_batch13_seed_tomioka_hachimangu_has_only_named_deity`: 富岡
  八幡宮のDeityが応神天皇1柱のみであり、「他8柱」「外8柱」が
  Fact化されていないことを固定化
- `test_batch13_seed_washinomiya_excludes_referenced_shrine_deity`:
  鷲宮神社の由緒に登場する「大己貴命」（神崎神社の祭神、別の神社）が
  鷲宮神社のFactとして混入していないことを固定化
- `test_batch13_seed_role_assignment_matches_official_hierarchy`:
  高良大社・忌宮神社のrole割当てが公式サイトの序列・空間配置と一致
  することを固定化
- `test_batch13_seed_source_semantic_identity_no_conflict_with_prior_batches`:
  Batch11/12・Batch13のSource URLが互いに衝突しないことを固定化

既存の汎用テスト（24件）・Batch9/10/11/12テスト（28件）を含め、合計
56件すべてPASS（回帰なし）。

---

## 10. Local validation

ローカル`jinja_db`（対象5社は既存Production idと一致する形で存在、
import前はいずれもdeity=0/history=0を確認済み）に対して実際に実行:

| step | 結果 |
|---|---|
| `--validate-only` | `validate-only: OK, no errors` |
| `--dry-run`（1回目） | `{'source_CREATE': 5, 'deity_CREATE': 10, 'history_CREATE': 10}` |
| 適用（import） | `sources created=5, deities created=10, histories created=10` |
| 件数検証 | 対象5社の内訳は1/2・3/2・1/2・3/2・2/2件（seedと完全一致）、source-less 0件 |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 5, 'deity_SKIP_EXISTS': 10, 'history_SKIP_EXISTS': 10}`、CREATE 0件 |

---

## 11. Production read-only baseline

Production DBをfreshに確認した（過去値を固定せず、本セッションの実測を
正本とする）。

| 指標 | 実測値 |
|---|---:|
| Knowledge Shrine | 66 |
| Source | 86 |
| Deity | 187 |
| History | 123 |
| Deity–Source relation | 200 |
| History–Source relation | 128 |
| complete | 64 |
| partial | 2 |
| none | 39 |
| 総Shrine数 | 105 |

Application aggregates: auth_user 1・userprofile 1・shrine 105・favorite 0・
visit 2・goriyakutag 39・shrine_goriyaku_relation 283。

対象5社は全件Knowledge none、drift 0件。

---

## 12. Fresh Production Backup

PostgreSQL 17バージョン一致クライアント（`postgresql@17.10`）で新規取得
（過去のBackupを再利用していない）。

| ファイル | サイズ |
|---|---:|
| roles.sql | 5,426 bytes |
| schema.sql | 93,021 bytes |
| data.sql | 4,302,635 bytes |

repo外（`~/kami-musubi-backups/`）に保存。接続情報・hostname・credentialは
一切ログに出力していない。

---

## 13. Fresh Production-equivalent test

上記backupを`kami_musubi_migration_safety_b13<timestamp>`（disposable
local DB）へ復元した。復元は`exit 0`で完了。

復元直後のisolated DB確認: Production同時刻の値（Source86・Deity187・
History123・relation200/128・Knowledge Shrine66・総Shrine105）と完全一致。
対象5社（富岡八幡宮の非canonical重複行id=104を含む）は全件Knowledge none。

isolated DBに対して、ローカルと同一の5ステップ＋追加確認を実施:

| step | 結果 |
|---|---|
| `--validate-only` | OK, no errors |
| `--dry-run`（1回目） | `{'source_CREATE': 5, 'deity_CREATE': 10, 'history_CREATE': 10}` |
| 適用 | `sources created=5, deities created=10, histories created=10` |
| 件数検証 | Source 86→91・Deity 187→197・History 123→133・Deity–Source rel 200→210・History–Source rel 128→138・Knowledge Shrine 66→71（いずれもseed件数と完全一致） |
| 対象5社のdeity/history内訳 | 富岡八幡宮1/2・忌宮神社3/2・笠間稲荷神社1/2・高良大社3/2・鷲宮神社2/2（seedと完全一致、混入なし） |
| Coverage | complete 64→69・partial 2（不変）・none 39→34 |
| source-less（DB全体） | Deity 0・History 0 |
| 除外名混入チェック（対象5社スコープ） | 「他8柱」「外8柱」「大己貴命」いずれも対象5社では0件（DB全体では既存Batchの正当な祭神として7件存在するが、いずれも神田神社・武蔵御嶽神社・氷川神社（大宮）・大洗磯前神社・川越氷川神社・赤坂氷川神社・二荒山神社の既存祭神であり無関係） |
| 富岡八幡宮の非canonical重複行（id=104）へのKnowledge混入 | 0件（canonical行id=49のみにFact付与されたことを確認） |
| 無関係データ回帰チェック | 二荒山神社3/1・小網神社2/1・根津神社5/2（いずれも既存値のまま不変） |
| Application aggregate | auth_user1・userprofile1・shrine105・favorite0・visit2・goriyakutag39・shrine_goriyaku_rel283（完全不変） |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 5, 'deity_SKIP_EXISTS': 10, 'history_SKIP_EXISTS': 10}`、CREATE 0件 |

isolated DBは検証完了後に`dropdb`で削除済み。

---

## 14. Coverage projection

isolated DB（Production-equivalent）の実測値から算出（推測値は使用して
いない）。5社すべてが投入前`none`のため、5社ともDeity/History両方を
獲得しcompleteへ移行する（先に決め打ちせず、実測で確認）。

| 区分 | Batch13投入前（実測） | Batch13投入後（実測） |
|---|---:|---:|
| complete | 64 | 69 |
| partial | 2 | 2（不変） |
| none | 39 | 34 |
| Knowledge Shrine合計 | 66 | 71 |
| 全Shrine数 | 105 | 105（不変） |

---

## 15. Production read-only preflight

Production DBに対して以下を実行した（いずれもコマンド自身の設計上、
DB書き込みを一切行わないモード）。

**`--validate-only`**: `validate-only: OK, no errors`

**`--dry-run`**:
```
plan summary: {'source_CREATE': 5, 'deity_CREATE': 10, 'history_CREATE': 10}
dry-run: OK, no DB writes performed
```

全項目、isolated DBの1回目`--dry-run`結果と完全一致。`SKIP_EXISTS`・
`REUSE_EXISTING`・`SOURCE_REUSE_CONFLICT`・`SOURCE_REUSE_AMBIGUOUS`・
`IMPORT_IDENTITY_AMBIGUOUS`・`NOT_FOUND`はいずれも0件。富岡八幡宮は
canonical行（id=49相当）1件のみへCREATEされ、非canonical重複行は
影響を受けない。

実行後、`readonly_query.sh`で再度Production状態を確認し、対象5社の
deity/history、および集計値（Source86・Deity187・History123・
relation200/128・Knowledge Shrine66）が実行前と完全に不変であることを
確認した。

---

## 16. Runtime expected payload

seedから算出（Production import実行後に期待される値、実行はしていない）。

| shrine | Deity | History | Unique Source |
|---|---:|---:|---:|
| 富岡八幡宮 | 1 | 2 | 1 |
| 忌宮神社 | 3 | 2 | 1 |
| 高良大社 | 3 | 2 | 1 |
| 笠間稲荷神社 | 1 | 2 | 1 |
| 鷲宮神社 | 2 | 2 | 1 |
| **合計** | **10** | **10** | **5** |

Fact–Source relation count: 20（Deity 10 + History 10）。

富岡八幡宮のDeity=1は、公式サイトの記載範囲の限界を反映した値であり、
Seed PreparationおよびProduction-equivalent双方で一貫している。

---

## 17. Risk Audit

- **富岡八幡宮 deity completeness limitation**: 公式サイトが「外8柱」の
  個別名を明かしていないため、Deity Factは応神天皇1柱のみ。未確認の
  8柱を推測登録していない（テストで固定化済み）。
- **Source page instability**: 他Batchと同様の一般的リスク。
- **`SKIP_EXISTS`のsemantic-diff limitation**: 既知の設計上の制約であり、
  本Batchに固有の問題ではない。
- **historical tradition / history distinction**: 全4件のtradition Fact
  で非断定表現を確認済み（fresh検証）。
- **identity/address exactness**: 5社全件、Production記載住所と完全一致
  することをfreshに確認済み。富岡八幡宮の非canonical重複行への誤混入も
  0件を確認。
- **regional distribution**: 東京・山口・福岡・茨城・埼玉の5都県に分散
  （Target Selection時のtie-breaker選定結果どおり）。
- **新規のcontent-model問題**: 発生していない。鷲宮神社の由緒に登場する
  「神崎神社（大己貴命）」を誤って自社祭神としてFact化するリスクを
  特定し、正しく除外した（テストで固定化済み）。

---

## 18. Final Classification

- 5社全件が`IDENTITY_SAFE`・`NO_CONFLICT`・Evidence Gate要件を満たす
- ローカル・Production-equivalent（fresh dump復元）の両方で
  `--validate-only`→`--dry-run`→適用→件数検証→再`--dry-run`の
  フルサイクルが期待どおりの結果
- Production DBに対する`--validate-only`・`--dry-run`がProduction-equivalent
  の結果と完全一致し、unexpected SKIP/UPDATE/conflictが0件
- Production状態がこれらの読み取り専用操作の前後で完全に不変であることを
  実測で確認
- 候補の差替えは発生していない
- **軽微な制限あり**: 富岡八幡宮のDeity Evidenceが1柱のみ（公式サイトの
  記載範囲の限界、Evidence Gateは遵守）

**`BATCH13_PRODUCTION_IMPORT_READY_WITH_LIMITATIONS`**

残存する非blocking事項（Productionへの実書き込み判断とは独立）:

- 富岡八幡宮の未確認8柱は、将来的に公式サイトの更新や追加Source
  （例: 現地案内板・刊行物）が見つかった場合に追加Fact化を検討できる
- partial 2社（阿佐ヶ谷神明宮・香取神宮）のHistory repairは別タスクの
  まま
- `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`（Batch11由来）は未着手のまま
- 靖國神社・千葉神社・愛宕神社のcontent-model判断は引き続き保留
- `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`（pytest-dotenvのlocal-only
  のdrift）は継続、本ドキュメントでもpackage変更は行っていない
- Production importそのもの（Fact実書き込み・Runtime QA）は本ドキュメント
  では未実施。Mother Shipの明示的な承認後、別セッション（Human
  Execution Boundary Gate相当）で実施する必要がある

Production DB writes = 0
Batch 13 Production import = NOT_EXECUTED
Batch 14 = NOT_STARTED
