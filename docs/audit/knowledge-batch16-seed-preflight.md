> **Status: `BATCH16_PRODUCTION_IMPORT_READY`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch16-target-selection.md`
> （`BATCH16_TARGET_SELECTION_READY`、ただしBatch17継続性への強い
> 警告付き）で選定されたRecommended 5社について、Knowledge seedを
> 構築し、Production投入直前の技術Gateまで検証した記録である。
>
> **本ドキュメント作成のセッションでは、Production Knowledge writeは
> 実行していない。** 実行したのは、Production read-only接続
> （`readonly_query.sh`）、公式サイトのfresh確認（Browser pane）、
> ローカルDBへの実際のseed投入・検証、fresh Production dumpから復元
> した isolated DBへの実際のseed投入・検証、そしてProduction DBに
> 対する`--validate-only`・`--dry-run`（いずれもDB書き込みを一切行わ
> ないモード）のみである。Production DB writeは0件。
>
> 全14 Deity・15 History Factが`confidence: high`で確定でき、限定的な
> データ完全性の制約（Batch14の玉前神社のような`confidence: medium`
> 格下げ）は生じなかったため`READY`とした。`SAFE_CANDIDATES_AFTER_BATCH16
> = 0`（`NORMAL_BATCH_CONTINUATION_EXHAUSTED`）はSection 22で再確認
> したとおりTarget Selection時点から変化していない。

develop SHA（作業開始時点）: `032e2493d274fe74603802864ecfeb2f77a12fad`
（PR #2377反映済み、`origin/develop`と同期済み、working tree clean）。

---

## 1. Base state and contracts

`docs/audit/knowledge-batch16-target-selection.md`を再読し、
Recommended 5社を対象として確定した。

freshに再読した既存contract:

- `docs/knowledge/shrine-knowledge-contract.md`
- `backend/temples/data/knowledge_seeds/batch_15_seed.json`（seed構造のテンプレート）
- `backend/temples/tests/test_batch15_knowledge_seed.py`
- `backend/temples/services/knowledge_seed.py`
- `backend/temples/management/commands/import_shrine_knowledge.py`
- `docs/audit/knowledge-batch15-seed-preflight.md`
- `docs/audit/knowledge-batch15-closure-batch16-reentry.md`

いずれも構造変更なしで再利用可能であることを確認した。

---

## 2. Target Identity Recheck（fresh実測）

Production read-only接続で、5社をfreshに再確認した。

| shrine | Production id | `place_ref_id IS NULL` | 同名重複 | deity_count | history_count |
|---|---:|---|---:|---:|---:|
| 平塚八幡宮 | 94 | true | 1 | 0 | 0 |
| 櫻木神社 | 80 | true | 1 | 0 | 0 |
| 多摩川浅間神社 | 70 | true | 1 | 0 | 0 |
| 宇都宮二荒山神社 | 84 | true | 1 | 0 | 0 |
| 白山神社 | 65 | true | 1 | 0 | 0 |

**全5社が`IDENTITY_SAFE`。** Target Selection時点の記載と完全一致
（drift 0）。numeric PKはseedへ記録しない。宇都宮二荒山神社の
`name_jp`が「宇都宮二荒山神社」で確定しており、栃木県日光市の
「日光二荒山神社」（別法人・別レコード）との混同がないことを確認済み。

---

## 3. Official Sources（Target Selection時の結果を再利用せずfresh確認）

5社すべての公式サイト（白山神社のみ東京十社会公式）をBrowser paneで
**再度**直接確認した。取得内容はTarget Selectionセッション時と完全に
一致し、drift 0件だった。

| shrine | Source URL | 確認内容 |
|---|---|---|
| 平塚八幡宮 | http://www.hachiman.org/yurai.php | 応神天皇・神功皇后・武内宿禰、仁徳天皇御代68年(380)創祀伝承、戦国期兵火、徳川家康による復興、大正12年(1923)関東大震災倒壊、昭和3年(1928)現社殿竣工 |
| 櫻木神社 | https://sakuragi.info/about/ | 伊弉諾尊・伊弉冉尊・倉稲魂命・武甕槌命、仁寿元年(851)創建伝承、永祚元年(989)宮所建立、正暦3年(992)以降の髙梨氏継承 |
| 多摩川浅間神社 | https://sengenjinja.info/about/index.html | 木花咲耶姫命（単一）、文治年間(1185-90)創祀伝承、承応元年(1652)観世音立像発掘、明治40年(1907)合祀政令による現形成立 |
| 宇都宮二荒山神社 | http://futaarayamajinja.jp/yuisyo/ | 豊城入彦命（御祭神）・大物主命・事代主命（相殿）、崇神天皇御代起源伝承、承和5年(838)臼ケ峰遷座、延長5年(927)延喜式名神大社記載 |
| 白山神社 | http://10jinja.tokyo/hakusanjinja.html（東京十社会公式） | 菊理姫命・伊弉諾命・伊弉冊命、天暦2年(948)勧請、建武4年(1337)足利尊氏祈願所、元和2年(1616)〜明暦元年(1655)の遷座歴 |

平塚八幡宮の公式サイトはHTTPS証明書がホスト名と一致しないため
Browser paneで直接コンテンツを確認した（HTTP接続自体は到達可能で、
内容の推測は行っていない）。

---

## 4. Source Semantic Conflict

Production既存104件のSourceと`normalize_source_url()`実装をそのまま
使用して照合した。

```sql
SELECT id, source_type, title, publisher, url FROM temples_shrineknowledgesource
WHERE url ILIKE '%hachiman.org%' OR url ILIKE '%sakuragi.info%'
   OR url ILIKE '%sengenjinja.info%' OR url ILIKE '%futaarayamajinja%'
   OR url ILIKE '%10jinja.tokyo%';
```

結果: 0件。**5候補Sourceすべてが`NO_CONFLICT`。**

---

## 5. Deity Research（各社固有の判断）

### 平塚八幡宮

公式サイトから応神天皇・神功皇后・武内宿禰の三柱をfresh確認した。
序列の記載がないため三柱とも`role: unknown`とした。境内絵図に記載の
「弁財天社」（七福神の一）・「末社三社」は本社Factから除外した。

### 櫻木神社

公式サイトから伊弉諾尊・伊弉冉尊・倉稲魂命・武甕槌命の四柱を、各柱の
個別説明とともにfresh確認した。序列の記載がないため四柱とも
`role: unknown`とした。

### 多摩川浅間神社（completeness/tradition限定）

公式サイトから木花咲耶姫命の一柱をfresh確認した。創祀伝承には仏教的
要素（「正観世音像」「富士浅間大菩薩」という呼称）が登場するが、現在の
「御祭神」欄には木花咲耶姫命のみが記載されており、伝承をtradition
分類で非断定的に扱い、観世音像自体をDeity Factとして登録していない。
明治40年(1907)の合祀政令により統合された旧赤城神社・熊野神社の祭神は
現在の御祭神一覧に含まれないためFact化していない。

### 宇都宮二荒山神社（identity厳密確認）

公式サイトから豊城入彦命（`role: primary`、御祭神）・大物主命・
事代主命（`role: secondary`、相殿）の三柱をfresh確認した。当社が
栃木県宇都宮市に鎮座する「宇都宮二荒山神社」であり、栃木県日光市の
「日光二荒山神社」とは別法人であることを、Production側のaddressと
公式サイト記載の所在地の一致によって確認した。境内の十二末社は
本社Factから除外した。

### 白山神社（東京十社会公式Source）

白山神社（文京区）自体の独立公式ドメインは確認できなかったため、
当社を含む参加10社が共同運営する公式団体「東京十社会」の公式サイト
（©東京十社会）から直接fresh確認した。菊理姫命・伊弉諾命・伊弉冊命の
三柱を、序列を示さない形で確認した。白山信仰一般の解説は含まれず、
当社固有の由緒のみが記載されていることを確認済み。境内社の記載は
このページにはない。

**禁止事項の遵守確認**: unnamed deityの推測登録＝0件、collective
Fact化＝0件、摂社/末社/境内社祭神の混入＝0件（平塚八幡宮の弁財天社・
末社三社、多摩川浅間神社の旧赤城神社・熊野神社、宇都宮二荒山神社の
十二末社をいずれも除外）、仏教尊格の無理なDeity化＝0件（多摩川浅間
神社の観世音像を除外）、associated worship target混入＝0件。

---

## 6. History Research

各社の由緒を、既存`history_type` enumへ適合する範囲でFact化した。
伝承（`tradition`）と歴史的出来事（`historical_event`）を明確に分離し、
伝承文には非断定表現を用いた（fresh確認: 全4件のtradition Factで
確認済み: 平塚八幡宮の380年創祀伝承、櫻木神社の851年創建伝承、多摩川
浅間神社の1185-90年創祀伝承、宇都宮二荒山神社の起源伝承）。

BiographyとShrine Historyの混同はない（本Batchの候補にはBatch15の
報徳二宮神社のような人物伝記型の候補は含まれていない）。

---

## 7. Shrine-specific Content-model Review

| shrine | 確認事項 | 結果 |
|---|---|---|
| 平塚八幡宮 | 境内社（弁財天社・末社三社）を除外。HTTP-only sourceでも内容根拠を保持（Browser paneで直接確認） | `MODEL_FIT_SAFE` |
| 櫻木神社 | 合祀・境内社の記載なし。collective表現の過剰Fact化なし | `MODEL_FIT_SAFE` |
| 多摩川浅間神社 | 木花咲耶姫命のみFact化。富士信仰の伝承と歴史的出来事（発掘・合祀政令）を分離。富士塚等の関連信仰対象は登場せず別Fact化していない | `MODEL_FIT_SAFE`（tradition内の仏教的要素は非断定表現で処理） |
| 宇都宮二荒山神社 | 日光二荒山神社との混同なし（address一致確認）。十二末社を除外 | `MODEL_FIT_SAFE` |
| 白山神社 | 東京十社会公式Sourceのidentity/address一致確認済み。白山信仰一般論の混入なし。境内社の記載なし | `MODEL_FIT_SAFE` |

**Recommended 5全件が`MODEL_FIT_SAFE`。**

---

## 8. Evidence Gate

全14 Deity・15 History Factについて確認した。

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

全件がEvidence Gate要件を満たす。全29 Fact（Deity14+History15）が
`confidence: high`。

---

## 9. Canonical seed integrity

`backend/temples/data/knowledge_seeds/batch_16_seed.json`
（`schema_version: "1.0"`）。

`parse_seed()`（実装をそのまま使用したstructural検証）:

| 指標 | 値 |
|---|---:|
| errors | 0 |
| Source count | 5 |
| Shrine count | 5 |
| Deity count | 14 |
| History count | 15 |
| Deity–Source relation | 14 |
| History–Source relation | 15 |
| source-less Deity | 0 |
| source-less History | 0 |
| within-shrine重複 | 0 |
| invalid enum | 0 |
| unresolved source_key参照 | 0 |
| 数値Production PKのhardcode | 0 |

SHA-256（`batch_16_seed.json`）:
`41ca48e3e980da5dcb9cb0b38050d4e43e8828bc5553f8dee27c42b996fee4e9`

---

## 10. Regression tests

新規: `backend/temples/tests/test_batch16_knowledge_seed.py`（11件）。
Batch15の`test_batch15_knowledge_seed.py`と同型の構成に加え、本Batch
固有の以下を追加した。

- `test_batch16_seed_hiratsuka_hachimangu_excludes_sub_shrines`: 平塚
  八幡宮の弁財天社・末社三社が本社Factに混入していないことを固定化
- `test_batch16_seed_sengenjinja_excludes_absorbed_shrine_deities`:
  多摩川浅間神社が木花咲耶姫命の一柱のみをFact化し、合祀された旧
  赤城神社・熊野神社の祭神を含んでいないことを固定化
- `test_batch16_seed_futaarayama_excludes_sub_shrines_and_is_utsunomiya`:
  宇都宮二荒山神社の十二末社が混入していないこと、addressが日光
  二荒山神社と混同されていないことを固定化
- `test_batch16_seed_hakusan_identity_and_source`: 白山神社の
  identity・東京十社会公式Sourceの参照関係を固定化

既存の汎用テスト（24件）・Batch9〜15テスト（55件）を含め、合計90件
すべてPASS（回帰なし。`pytest -p no:dotenv`でlocal-onlyの
`pytest-dotenv`プラグイン競合を回避）。

---

## 11. Local validation

ローカル`jinja_db`（対象5社は既存Production idと一致する形で存在、
import前はいずれもdeity=0/history=0を確認済み）に対して実際に実行:

| step | 結果 |
|---|---|
| `--validate-only` | `validate-only: OK, no errors` |
| `--dry-run`（1回目） | `{'source_CREATE': 5, 'deity_CREATE': 14, 'history_CREATE': 15}` |
| 適用（import） | `sources created=5, deities created=14, histories created=15` |
| 件数検証 | 対象5社の内訳は3/3・4/3・1/3・3/3・3/3件（seedと完全一致）、source-less 0件 |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 5, 'deity_SKIP_EXISTS': 14, 'history_SKIP_EXISTS': 15}`、CREATE 0件 |

---

## 12. Production read-only baseline

Production DBをfreshに確認した（過去値を固定せず、本セッションの実測を
正本とする）。

| 指標 | 実測値 |
|---|---:|
| Knowledge Shrine | 81 |
| Source | 104 |
| Deity | 219 |
| History | 167 |
| Deity–Source relation | 232 |
| History–Source relation | 172 |
| complete | 79 |
| partial | 2 |
| none | 24 |
| 総Shrine数 | 105 |

Application aggregates: auth_user 1・userprofile 1・shrine 105・favorite 0・
visit 2・goriyakutag 39・shrine_goriyaku_relation 283。

対象5社は全件Knowledge none、drift 0件。

---

## 13. Fresh Production Backup

PostgreSQL 17バージョン一致クライアント（`postgresql@17.10`）で新規
取得（過去のBackupを再利用していない）。

| ファイル | サイズ |
|---|---:|
| roles.sql | 5,426 bytes |
| schema.sql | 93,021 bytes |
| data.sql | 4,346,373 bytes |

repo外（`~/kami-musubi-backups/batch16-seed-preparation-<timestamp>/`）
に保存。接続情報・hostname・credentialは一切ログに出力していない。

---

## 14. Fresh Production-equivalent test

上記backupを`kami_musubi_migration_safety_b16<timestamp>`（disposable
local DB）へ復元した。復元は`exit 0`で完了。

復元直後のisolated DB確認: Production同時刻の値（Source104・Deity219・
History167・relation232/172・Knowledge Shrine81・総Shrine105）と完全
一致。対象5社は全件Knowledge none。

isolated DBに対して、ローカルと同一の5ステップ＋追加確認を実施:

| step | 結果 |
|---|---|
| `--validate-only` | OK, no errors |
| `--dry-run`（1回目） | `{'source_CREATE': 5, 'deity_CREATE': 14, 'history_CREATE': 15}` |
| 適用 | `sources created=5, deities created=14, histories created=15` |
| 件数検証 | Source 104→109・Deity 219→233・History 167→182・Deity–Source rel 232→246・History–Source rel 172→187・Knowledge Shrine 81→86（いずれもseed件数と完全一致） |
| 対象5社のdeity/history内訳 | 平塚八幡宮3/3・櫻木神社4/3・多摩川浅間神社1/3・宇都宮二荒山神社3/3・白山神社3/3（seedと完全一致、混入なし） |
| Coverage | complete 79→84・partial 2（不変）・none 24→19 |
| source-less（DB全体） | Deity 0・History 0 |
| 無関係データ回帰チェック | Batch14・Batch15投入分（王子神社・足利織姫神社・鶴嶺八幡宮・穴守稲荷神社・玉前神社・湯島天満宮・報徳二宮神社・箭弓稲荷神社・水戸東照宮・葛西神社）すべて既存値のまま不変 |
| Application aggregate | auth_user1・userprofile1・shrine105・favorite0・visit2・goriyakutag39・shrine_goriyaku_rel283（完全不変） |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 5, 'deity_SKIP_EXISTS': 14, 'history_SKIP_EXISTS': 15}`、CREATE 0件 |

isolated DBは検証完了後に`dropdb`で削除済み（削除後の存在確認も実施
済み）。

---

## 15. Coverage Projection

isolated DB（Production-equivalent）の実測値から算出（推測値は使用して
いない）。

| 区分 | Batch16投入前（実測） | Batch16投入後（projection） |
|---|---:|---:|
| complete | 79 | 84 |
| partial | 2 | 2（不変） |
| none | 24 | 19 |
| Knowledge Shrine合計 | 81 | 86 |
| 全Shrine数 | 105 | 105（不変） |

---

## 16. Production read-only preflight

Production DBに対して以下を実行した（いずれもコマンド自身の設計上、
DB書き込みを一切行わないモード）。

**`--validate-only`**: `validate-only: OK, no errors`

**`--dry-run`**:
```
plan summary: {'source_CREATE': 5, 'deity_CREATE': 14, 'history_CREATE': 15}
dry-run: OK, no DB writes performed
```

全項目、isolated DBの1回目`--dry-run`結果と完全一致。`SKIP_EXISTS`・
`REUSE_EXISTING`・`SOURCE_REUSE_CONFLICT`・`SOURCE_REUSE_AMBIGUOUS`・
`IMPORT_IDENTITY_AMBIGUOUS`・`NOT_FOUND`はいずれも0件。

実行後、`readonly_query.sh`で再度Production状態を確認し、対象5社の
deity/history、および集計値（Source104・Deity219・History167・
relation232/172・Knowledge Shrine81・総Shrine105）が実行前と完全に
不変であることを確認した。

---

## 17. Runtime Expected Payload

seedから算出（Production import実行後に期待される値、実行はしていない）。

| shrine | Deity | History | Unique Source |
|---|---:|---:|---:|
| 平塚八幡宮 | 3 | 3 | 1 |
| 櫻木神社 | 4 | 3 | 1 |
| 多摩川浅間神社 | 1 | 3 | 1 |
| 宇都宮二荒山神社 | 3 | 3 | 1 |
| 白山神社 | 3 | 3 | 1 |
| **合計** | **14** | **15** | **5** |

Fact–Source relation count: 29（Deity 14 + History 15）。

---

## 18. Runtime Compatibility

コード変更は一切行っていない。`GET https://jinja-backend.onrender.com/api/shrines/64/data/`
を実行し、Batch15投入分（湯島天満宮、deities=2, histories=4）が変わらず
Runtime公開されていることをfresh再確認した。本Batch16 seedはBatch14/15
と同一の`schema_version: "1.0"`・同一field構成であり、
`ShrineDeitySerializer`/`ShrineHistorySerializer`の`fields`と完全に
互換である。

**分類: `KNOWLEDGE_RUNTIME_COMPATIBLE`。**

---

## 19. Remaining-normal-batch Audit（fresh再確認、重要KPI）

Target Selection時点の判定（`SAFE_CANDIDATES_AFTER_BATCH16 = 0`）を
盲信せず、本セッションでもfreshにDBを再照会した。

raw `none`（Batch16投入前の現状値、24件）から、Batch16の5社が離脱した
後を projectionとして算出:

| 区分 | 件数（Batch16後projection） |
|---|---:|
| raw none | 19（24-5） |
| canonical candidate | 14（19-5の除外＝変化なし） |
| model-risk（既存6件＋Batch16 Target Selection時点で新規判明3件） | 9 |
| `ADDITIONAL_RESEARCH_REQUIRED` | 4 |
| `SOURCE_INSUFFICIENT` | 1 |
| **通常Batchで即座に安全な候補** | **0** |

**`SAFE_CANDIDATES_AFTER_BATCH16 = 0`（fresh再確認、drift 0）。**

**分類: `NORMAL_BATCH_CONTINUATION_EXHAUSTED`。**

Target Selection以降、model-risk・研究要求候補の状態に変化はない
（Mother Shipによる新たな設計判断が行われていないため）。

---

## 20. Risk Audit

- **identity ambiguity**: 0件。宇都宮二荒山神社は日光二荒山神社との
  混同がないことをaddress照合で確認済み
- **Source instability**: 平塚八幡宮はHTTPS証明書がホスト名と一致しない
  ためHTTP接続で確認した（一般的なリスクとして記録、内容の推測は
  行っていない）
- **unnamed deities**: 0件
- **collective deity**: 0件
- **shinbutsu-shugo**: 多摩川浅間神社の創祀伝承に仏教的要素（観世音像）
  が含まれるが、現在の御祭神は木花咲耶姫命のみであり、伝承を
  非断定的なtradition Factとして扱い、観世音像自体をDeity Fact化して
  いない。榛名神社・古峯神社のような現役の仏教組織支配の歴史とは
  性質が異なると判断した
- **sub-shrine contamination**: 0件（平塚八幡宮・多摩川浅間神社・
  宇都宮二荒山神社いずれも境内社/合祀吸収元を除外）
- **`SKIP_EXISTS`のsemantic-diff limitation**: 既知の設計上の制約であり、
  本Batchに固有の問題ではない

新規にMother Ship判断が必要なcontent-model問題は生じなかった。
`MOTHER_SHIP_REVIEW_REQUIRED`には該当しない。

---

## 21. Final Classification

- 5社全件が`IDENTITY_SAFE`・`NO_CONFLICT`・Evidence Gate要件を満たす
- ローカル・Production-equivalent（fresh dump復元）の両方で
  `--validate-only`→`--dry-run`→適用→件数検証→再`--dry-run`の
  フルサイクルが期待どおりの結果
- Production DBに対する`--validate-only`・`--dry-run`がProduction-equivalent
  の結果と完全一致し、unexpected SKIP/UPDATE/conflictが0件
- Production状態がこれらの読み取り専用操作の前後で完全に不変であることを
  実測で確認
- 候補の差替えは発生していない
- 全29 Fact（Deity14+History15）が`confidence: high`
- `KNOWLEDGE_RUNTIME_COMPATIBLE`確認済み
- Risk Auditで新規content-model判断は不要と判定
- `SAFE_CANDIDATES_AFTER_BATCH16 = 0`（`NORMAL_BATCH_CONTINUATION_EXHAUSTED`）
  をfresh再確認

**`BATCH16_PRODUCTION_IMPORT_READY`**

残存する非blocking事項（Productionへの実書き込み判断とは独立）:

- partial 2社（阿佐ヶ谷神明宮・香取神宮）のHistory repairは別タスクの
  まま
- model-risk 9件（うち3件はBatch16 Target Selectionで新規判明）の
  content-model判断は引き続き保留
- `ADDITIONAL_RESEARCH_REQUIRED`4件（花園神社・武蔵一宮氷川女體神社・
  調神社・鳥越神社）への追加調査は未着手
- **Batch 16の実施をもって、通常のBatch継続（Option A）は事実上停止
  する。Batch 17を開始する場合は、Mother Shipによる次工程（Option
  A-F、`knowledge-batch16-target-selection.md` Section 21参照）の
  明示判断が必須である**
- Production importそのもの（Fact実書き込み・Runtime QA）は本ドキュメント
  では未実施。Mother Shipの明示的な承認後、別セッション（Human
  Execution Boundary Gate相当）で実施する必要がある

Production DB writes = 0
Batch 16 Production import = NOT_EXECUTED
Batch 17 = NOT_STARTED

---

## 最終報告サマリ

1. develop SHA: `032e2493d274fe74603802864ecfeb2f77a12fad`
2. target5: 平塚八幡宮・櫻木神社・多摩川浅間神社・宇都宮二荒山神社・白山神社
3. identity: 全5社`IDENTITY_SAFE`
4. official Sources: 全5社公式/準公式Source直接確認、drift 0
5. Source conflict: 5件全て`NO_CONFLICT`
6. seed hash: `41ca48e3e980da5dcb9cb0b38050d4e43e8828bc5553f8dee27c42b996fee4e9`
7. seed counts: Shrine5・Source5・Deity14・History15・relation29
8. Deity: 14（全件confidence: high）
9. History: 15（全件confidence: high）
10. Evidence Gate: 全件PASS、source-less 0
11. content-model exclusions: 弁財天社/末社三社（平塚八幡宮）・旧赤城
    神社/熊野神社（多摩川浅間神社）・十二末社（宇都宮二荒山神社）
12. tests: 新規11件＋既存79件＝合計90件PASS
13. local validation: フルサイクル完了、件数一致
14. Production baseline: Knowledge Shrine81・Source104・Deity219・
    History167・rel232/172
15. backup: roles 5,426B・schema 93,021B・data 4,346,373B（repo外保存）
16. Production-equivalent: フルサイクル完了、件数一致、コンタミネーション0
17. Coverage projection: complete79→84・partial2（不変）・none24→19
18. Production validate-only: OK, no errors
19. Production dry-run: `{'source_CREATE': 5, 'deity_CREATE': 14, 'history_CREATE': 15}`、Production状態不変
20. Runtime Expected Payload: 合計Deity14・History15・Unique Source5
21. Runtime compatibility: `KNOWLEDGE_RUNTIME_COMPATIBLE`
22. SAFE_CANDIDATES_AFTER_BATCH16: **0**（fresh再確認、drift 0）
23. normal-batch viability: **`NORMAL_BATCH_CONTINUATION_EXHAUSTED`**
24. remaining risks: Section 20参照（新規Mother Ship判断は不要と判定）
25. audit doc: 本ドキュメント
    （`docs/audit/knowledge-batch16-seed-preflight.md`）
26. PR: 別途作成（本ドキュメントのcommit時に作成）
27. CI: PR作成後に確認
28. final classification: `BATCH16_PRODUCTION_IMPORT_READY`

Production DB writes = 0
Batch16 Production import = NOT_EXECUTED
Batch17 = NOT_STARTED
