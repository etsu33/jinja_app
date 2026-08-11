> **Status: `BATCH12_PRODUCTION_IMPORT_READY`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch12-target-selection.md`
> （`BATCH12_TARGET_SELECTION_READY`）で選定されたRecommended 5社
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

develop SHA（作業開始時点）: `7a29c6e3a04048660a4b0cfeb2a651463915a757`
（PR #2365反映済み、`origin/develop`と同期済み、working tree clean）。

---

## 1. Base state and contracts

`docs/audit/knowledge-batch12-target-selection.md`（`BATCH12_TARGET_SELECTION_READY`）
を再読し、Recommended 5社を対象として確定した。

freshに再読した既存contract:

- `docs/knowledge/shrine-knowledge-contract.md`（deity/shrine_history/Source契約、
  Evidence Gate、verification_status/confidence enum、collective name等の扱い）
- `backend/temples/data/knowledge_seeds/batch_11_seed.json`（seed構造のテンプレート）
- `backend/temples/services/knowledge_seed.py`（`resolve_shrine`・
  `resolve_source_identity`・`parse_seed`の実装）
- `backend/temples/management/commands/import_shrine_knowledge.py`
  （`--validate-only`/`--dry-run`/適用の3モード実装）

いずれも構造変更なしで再利用可能であることを確認した。

---

## 2. Target Identity Recheck（Phase 1、fresh実測）

Production read-only接続で、5社をfreshに再確認した。

| shrine | Production id | `place_ref_id IS NULL` | 同名重複行 | deity_count | history_count |
|---|---:|---|---:|---:|---:|
| 二荒山神社 | 54 | true | 1 | 0 | 0 |
| 住吉神社（博多） | 57 | true | 1 | 0 | 0 |
| 枚岡神社 | 98 | true | 1 | 0 | 0 |
| 安房神社 | 77 | true | 1 | 0 | 0 |
| 越中一宮 高瀬神社 | 32 | true | 1 | 0 | 0 |

**全5社が`IDENTITY_SAFE`。** numeric PKはseedへ記録しない。

---

## 3. Official Sources（Phase 2、Target Selection時の調査を再利用せずfresh確認）

5社すべての公式サイトをBrowser paneで**再度**直接確認した（Target
Selection時のfetchを再利用せず、本タスクで独立して再取得）。取得内容は
Target Selection時と完全に一致し、drift 0件だった。

| shrine | Source URL | 確認内容 |
|---|---|---|
| 二荒山神社 | http://www.futarasan.jp/ | 御祭神「二荒山大神」＝大己貴命(父)・田心姫命(母)・味耜高彦根命(子)の親子3神、序列記載なし |
| 住吉神社（博多） | https://www.nihondaiichisumiyoshigu.jp/about/ | 住吉三神＋相殿2柱＝「住吉五所大神」、約1800年以上前の創建伝承 |
| 枚岡神社 | http://www.hiraoka-jinja.org/history/ | 4殿4柱（天児屋根命=主祭神、比売御神=后神、武甕槌命・経津主命=778年配祀）、神武東征以前の創祀伝承・650年遷座・「元春日」 |
| 安房神社 | http://awajinjya.org/gosaijin.htm | 主祭神天太玉命＋相殿神（天比理刀咩命＋忌部五部神5柱）、皇紀元年伝承・717年遷座 |
| 越中一宮 高瀬神社 | https://www.takase.or.jp/guide.html | 主神大国主大神＋配祀2柱、景行天皇御代伝承・1923年国幣小社昇格 |

---

## 4. Source Semantic Conflict（Phase 3）

5件のSource候補ドメインを、Production既存81件のSourceとfreshに突合した。

- exact-domain照合: 5件全てProduction既存Sourceに一致なし
- `normalize_source_url()`実装をそのまま使用した精密照合（既存80件のURL保有Sourceと突合）: 5件全て一致なし

**5候補Sourceすべてが`NO_CONFLICT`。**

---

## 5. Deity Research（Phase 4、collective name / sub-shrine除外の判断）

各社固有の注意事項に従い、以下の判断を行った。

### 二荒山神社

公式サイトは御祭神を「二荒山大神」と総称し、大己貴命（父）・田心姫命
（母）・味耜高彦根命（子）の親子3神から成ると明記している。序列の記載
（主祭神/配祀等）はないため、3柱すべて`role: unknown`とし、「二荒山大神」
という総称自体は別Fact化していない（collective nameの重複Fact化を回避）。

### 住吉神社（博多）

住吉三神（底筒男神・中筒男神・表筒男神、`role: primary`）と相殿2柱
（天照皇大神・神功皇后、`role: secondary`）を個別にFact化した。合わせて
「住吉五所大神」と総称されるが、この総称自体は別Fact化していない。

### 枚岡神社

主祭神4柱を公式表現どおり扱った。天児屋根命のみ公式サイトが「主祭神として
祀られている」と明言するため`role: primary`、比売御神（后神）・武甕槌命・
経津主命（いずれも778年に春日神社より「配祀」と明記）は`role: secondary`
とした。「元春日」はHistory側の由緒情報として扱い、Deity Factには含めて
いない。

### 安房神社

主祭神天太玉命（`role: primary`）・相殿神天比理刀咩命（`role: secondary`）
に加え、「忌部五部神」と総称される5柱（櫛明玉命・天日鷲命・彦狭知命・
手置帆負命・天目一箇命）を個別にFact化した（`role: secondary`、総称自体は
別Fact化していない）。下の宮（摂社）の天富命・天忍日命、厳島社/琴平社
（末社）の市杵島姫命・大物主神は、本宮（上の宮）とは別の摂社・末社の祭神
であるためFact化対象外とした。

### 越中一宮 高瀬神社

主神大国主大神（`role: primary`）・配祀天活玉命・五十猛命（`role: secondary`）
のみをFact化した。末社（神明宮・風宮・稲荷社・天満宮）および功霊殿
（南砺市等出身の戦没者・地方開拓功労者を祀る）の祭神は、本殿の主神・配祀
とは別区分のためFact化対象外とした。功霊殿は靖國神社と同種の「戦没者を
祀る」パターンに構造的に類似するが、本殿の主祭神とは明確に別棟の施設で
あり、そもそもFact化候補に含めていない。

**禁止事項の遵守確認**: collective nameの重複Fact化＝0件、source-less
Fact＝0件、神仏習合対象の恣意的kami化＝該当なし（5社いずれも記紀神話に
連なる古典的な神々のみ）。

---

## 6. History Research（Phase 5）

各社の由緒を、既存`history_type` enum（`founding`/`historical_event`/
`tradition`/`historical_context`等）へ適合する範囲でFact化した。神話的
創建伝承（`tradition`）と、年代の特定できる歴史的出来事（`historical_event`）
を明確に分離し、伝承文には「〜と伝えられている」等の非断定表現を用いた。

| shrine | History Fact | 分類 |
|---|---|---|
| 二荒山神社 | 霊峰二荒山（男体山）を神体山とする山岳信仰 | tradition（創建年不記載） |
| 住吉神社（博多） | 約1,800年以上前の創建伝承 | tradition |
| 住吉神社（博多） | 「住吉造」社殿と25年毎の御遷宮 | historical_event（国重要文化財） |
| 枚岡神社 | 神武東征以前の創祀伝承 | tradition |
| 枚岡神社 | 白雉元年(650)の山麓への奉遷 | historical_event |
| 枚岡神社 | 「元春日」——春日大社の元宮 | historical_event |
| 安房神社 | 神武天皇御代の創始伝承（皇紀元年） | tradition |
| 安房神社 | 養老元年(717)の遷座 | historical_event |
| 越中一宮 高瀬神社 | 景行天皇御代の創祀伝承 | tradition |
| 越中一宮 高瀬神社 | 大正12年(1923)の国幣小社昇格 | historical_event |

安房神社の「皇紀元年」（伝承上西暦紀元前660年）、高瀬神社の「景行天皇11年」
は、いずれも公式サイト自身が伝承として記述している内容であり、史実として
断定していない（`note`フィールドに明記）。高瀬神社の歴代神階奉授記録は、
公式サイトに記載された社格変遷（県社→国幣小社）の範囲に限定し、個別の
奉授年（従五位・正一位等）まではFact化していない（朝廷記録を根拠以上に
拡張しない）。長文の原文転載は行わず、要約に留めた。

---

## 7. Evidence Gate（Phase 6）

全22 Deity・10 History Factについて確認した。

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

## 8. Canonical seed integrity（Phase 7-8）

`backend/temples/data/knowledge_seeds/batch_12_seed.json`
（`schema_version: "1.0"`）。

`parse_seed()`（実装をそのまま使用したstructural検証）:

| 指標 | 値 |
|---|---:|
| errors | 0 |
| Source count | 5 |
| Shrine count | 5 |
| Deity count | 22 |
| History count | 10 |
| Deity–Source relation | 22 |
| History–Source relation | 10 |
| source-less Deity | 0 |
| source-less History | 0 |
| within-shrine重複 | 0 |
| invalid enum | 0 |
| unresolved source_key参照 | 0 |
| 数値Production PKのhardcode | 0 |

SHA-256（`batch_12_seed.json`）:
`24da852afc479c8248d57ebb7e5299c08ee5d493b3719d78ce8e4780147c57a1`

---

## 9. Regression tests（Phase 9）

新規: `backend/temples/tests/test_batch12_knowledge_seed.py`（9件）。
Batch11の`test_batch11_knowledge_seed.py`と同型の構成に加え、本Batch
固有の以下2件を追加した。

- `test_batch12_seed_excludes_collective_names_as_deity_facts`:
  「二荒山大神」「住吉五所大神」「忌部五部神」がいずれもDeity Factとして
  存在しないことを固定化
- `test_batch12_seed_excludes_sub_shrine_deities`: 安房神社の摂社/末社
  （天富命・天忍日命・市杵島姫命・大物主神）、高瀬神社の末社
  （級長戸辺命・宇迦之御魂大神等）がFact化されていないことを固定化
- `test_batch12_seed_role_assignment_matches_official_hierarchy`:
  各社のrole割当てが公式サイトの序列表現と一致することを固定化
- `test_batch12_seed_source_semantic_identity_no_conflict_with_batch11`:
  Batch11・Batch12のSource URLが互いに衝突しないことを固定化

既存の汎用テスト（`test_knowledge_seed_import.py`、24件）・Batch9/10/11
テスト（19件）を含め、合計47件すべてPASS（回帰なし）。

---

## 10. Local validation（Phase 10）

ローカル`jinja_db`（対象5社はProduction同一idで存在、import前はいずれも
deity=0/history=0を確認済み）に対して実際に実行:

| step | 結果 |
|---|---|
| `--validate-only` | `validate-only: OK, no errors` |
| `--dry-run`（1回目） | `{'source_CREATE': 5, 'deity_CREATE': 22, 'history_CREATE': 10}` |
| 適用（import） | `sources created=5, deities created=22, histories created=10` |
| 件数検証 | Source 84→89（+5）・Deity 165→187（+22）・History 113→123（+10）、対象5社の内訳は3/1・5/2・4/3・7/2・3/2件（seedと完全一致）、source-less 0件 |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 5, 'deity_SKIP_EXISTS': 22, 'history_SKIP_EXISTS': 10}`、CREATE 0件 |

---

## 11. Production read-only baseline（Phase 11）

Production DBをfreshに確認した（過去値を固定せず、本セッションの実測を
正本とする）。

| 指標 | 実測値 |
|---|---:|
| Knowledge Shrine | 61 |
| Source | 81 |
| Deity | 165 |
| History | 113 |
| Deity–Source relation | 178 |
| History–Source relation | 118 |
| complete | 59 |
| partial | 2 |
| none | 44 |
| 総Shrine数 | 105 |

Application aggregates: auth_user 1・userprofile 1・shrine 105・favorite 0・
visit 2・goriyakutag 39・shrine_goriyaku_relation 283。

対象5社は全件Knowledge none、drift 0件。

---

## 12. Fresh Production Backup（Phase 12）

PostgreSQL 17バージョン一致クライアント（`postgresql@17.10`）で新規取得
（過去のBackupを再利用していない）。

| ファイル | サイズ |
|---|---:|
| roles.sql | 5,426 bytes |
| schema.sql | 93,021 bytes |
| data.sql | 4,286,688 bytes |

repo外（`~/kami-musubi-backups/`）に保存。接続情報・hostname・credentialは
一切ログに出力していない。

---

## 13. Fresh Production-equivalent test（Phase 13）

上記backupを`kami_musubi_migration_safety_b12<timestamp>`（disposable
local DB）へ復元した。復元は`exit 0`で完了。

復元直後のisolated DB確認: Production同時刻の値（Source81・Deity165・
History113・relation178/118・Knowledge Shrine61・総Shrine105）と完全一致。
対象5社は全件Knowledge none。

isolated DBに対して、ローカルと同一の5ステップ＋追加確認を実施:

| step | 結果 |
|---|---|
| `--validate-only` | OK, no errors |
| `--dry-run`（1回目） | `{'source_CREATE': 5, 'deity_CREATE': 22, 'history_CREATE': 10}` |
| 適用 | `sources created=5, deities created=22, histories created=10` |
| 件数検証 | Source 81→86・Deity 165→187・History 113→123・Deity–Source rel 178→200・History–Source rel 118→128・Knowledge Shrine 61→66（いずれもseed件数と完全一致） |
| 対象5社のdeity/history内訳 | 二荒山神社3/1・住吉神社（博多）5/2・安房神社7/2・枚岡神社4/3・高瀬神社3/2（seedと完全一致、混入なし） |
| Coverage | complete 59→64・partial 2（不変）・none 44→39 |
| source-less（DB全体） | Deity 0・History 0 |
| collective name混入チェック | 「二荒山大神」「住吉五所大神」「忌部五部神」のDeityはDB全体で0件 |
| 無関係データ回帰チェック | 大國魂神社7/2・小網神社2/1・根津神社5/2（いずれも既存seedの値のまま、変化なし） |
| Application aggregate | auth_user1・userprofile1・shrine105・favorite0・visit2・goriyakutag39・shrine_goriyaku_rel283（完全不変） |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 5, 'deity_SKIP_EXISTS': 22, 'history_SKIP_EXISTS': 10}`、CREATE 0件 |

isolated DBは検証完了後に`dropdb`で削除済み。dumpファイルはrepo外に残置
（コミットしない）。

---

## 14. Coverage projection

isolated DB（Production-equivalent）の実測値から算出（推測値は使用して
いない）。

| 区分 | Batch12投入前（実測） | Batch12投入後（実測） |
|---|---:|---:|
| complete | 59 | 64 |
| partial | 2 | 2（不変） |
| none | 44 | 39 |
| Knowledge Shrine合計 | 61 | 66 |
| 全Shrine数 | 105 | 105（不変） |

対象5社はいずれも投入前`none`→投入後`complete`へ移行する。

---

## 15. Production read-only preflight

Production DBに対して以下を実行した（いずれもコマンド自身の設計上、
DB書き込みを一切行わないモード）。

**`--validate-only`**: `validate-only: OK, no errors`

**`--dry-run`**:
```
plan summary: {'source_CREATE': 5, 'deity_CREATE': 22, 'history_CREATE': 10}
dry-run: OK, no DB writes performed
```

全項目、isolated DBの1回目`--dry-run`結果と完全一致。`SKIP_EXISTS`・
`REUSE_EXISTING`・`SOURCE_REUSE_CONFLICT`・`SOURCE_REUSE_AMBIGUOUS`・
`IMPORT_IDENTITY_AMBIGUOUS`・`NOT_FOUND`はいずれも0件。

実行後、`readonly_query.sh`で再度Production状態を確認し、対象5社の
deity/history、および集計値（Source81・Deity165・History113・
relation178/118・Knowledge Shrine61）が実行前と完全に不変であることを
確認した。

---

## 16. Runtime expected payload

seedから算出（Production import実行後に期待される値、実行はしていない）。

| shrine | Deity | History | Unique Source |
|---|---:|---:|---:|
| 二荒山神社 | 3 | 1 | 1 |
| 住吉神社（博多） | 5 | 2 | 1 |
| 枚岡神社 | 4 | 3 | 1 |
| 安房神社 | 7 | 2 | 1 |
| 越中一宮 高瀬神社 | 3 | 2 | 1 |
| **合計** | **22** | **10** | **5** |

Fact–Source relation count: 32（Deity 22 + History 10）。

---

## 17. Risk Audit（Phase 18）

- **collective deity表現**: 「二荒山大神」「住吉五所大神」「忌部五部神」の
  3件を特定し、いずれも総称自体をFact化せず個別祭神のみをFact化した
  （テストで固定化済み）。
- **神話/歴史の区別**: 全ての伝承的記述（`tradition`）は非断定表現を用い、
  公式サイト自身が伝承として記述している旨を`note`に明記した。歴史的
  出来事（`historical_event`）は年代が特定できるもののみとした。
- **Source page instability**: 他Batchと同様の一般的リスク。
- **`SKIP_EXISTS`のsemantic-diff limitation**: 既知の設計上の制約であり、
  本Batchに固有の問題ではない。
- **Source semantic conflict**: 5件全て`NO_CONFLICT`。
- **identity/address exactness**: 5社全件、Production記載住所と完全一致
  することをfreshに確認済み。
- **regional distribution**: 栃木・福岡・大阪・千葉・富山の5県に分散
  （Target Selection時のtie-breaker選定結果どおり）。
- **高瀬神社の功霊殿**: 戦没者・地方開拓功労者を祀る別棟施設であり、
  靖國神社と構造的に類似するパターンだが、本殿の主神・配祀とは明確に
  別区分のため、そもそもFact化候補に含めていない（新規リスクとしての
  対応は不要）。
- **新規のcontent-model問題**: 発生していない。Mother Ship判断が必要な
  項目（Batch11の福禄寿のような）は本Batchには存在しない。全てのrole・
  Fact化可否判断は、公式サイトの明示的な表現（「主祭神」「配祀」「后神」
  「摂社」「末社」等）に直接基づいている。

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
- Mother Ship判断が必要な新規項目は発生していない

**`BATCH12_PRODUCTION_IMPORT_READY`**

残存する非blocking事項（Productionへの実書き込み判断とは独立）:

- partial 2社（阿佐ヶ谷神明宮・香取神宮）のHistory repairは別タスクのまま
- `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`（Batch11由来、将来のModel設計課題）は未着手のまま
- `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`（pytest-dotenvのlocal-onlyのdrift）は継続、本ドキュメントでもpackage変更は行っていない
- Production importそのもの（Fact実書き込み・Runtime QA）は本ドキュメントでは未実施。Mother Shipの明示的な承認後、別セッション（Human Execution Boundary Gate相当）で実施する必要がある

Production DB writes = 0
Batch 12 Production import = NOT_EXECUTED
Batch 13 = NOT_STARTED
