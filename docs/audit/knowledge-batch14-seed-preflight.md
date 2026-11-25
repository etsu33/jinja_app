> **Status: `BATCH14_PRODUCTION_IMPORT_READY_WITH_LIMITATIONS`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch14-target-selection.md`
> （`BATCH14_TARGET_SELECTION_READY`）で選定されたRecommended 5社
> について、Knowledge seedを構築し、Production投入直前の技術Gateまで
> 検証した記録である。
>
> **本ドキュメント作成のセッションでは、Production Knowledge writeは
> 実行していない。** 実行したのは、Production read-only接続
> （`readonly_query.sh`）、公式サイトのfresh確認（Browser pane /
> WebFetch）、ローカルDBへの実際のseed投入・検証、fresh Production dump
> から復元した isolated DBへの実際のseed投入・検証、そしてProduction DB
> に対する`--validate-only`・`--dry-run`（いずれもDB書き込みを一切行わ
> ないモード）のみである。Production DB writeは0件。
>
> `READY_WITH_LIMITATIONS`とした理由は、玉前神社の公式サイトが
> 「ご祭神に関しての考証がなされているところ」と自ら明記しており、
> 玉依姫命単独説が確定済みとは言い切れないためである（詳細はSection 5
> 参照）。未確定の鵜茅葺不合命は推測登録せず、Evidence Gateを遵守した
> 限定的なFact化（confidence: medium）を行っている。

develop SHA（作業開始時点）: `ec0046cb6237c802fbf3679d538d3cd0d3a99d2d`
（PR #2371反映済み、`origin/develop`と同期済み、working tree clean）。

---

## 1. Base state and contracts

`docs/audit/knowledge-batch14-target-selection.md`を再読し、
Recommended 5社を対象として確定した。

freshに再読した既存contract:

- `docs/knowledge/shrine-knowledge-contract.md`
- `backend/temples/data/knowledge_seeds/batch_13_seed.json`（seed構造のテンプレート）
- `backend/temples/services/knowledge_seed.py`
- `backend/temples/management/commands/import_shrine_knowledge.py`

いずれも構造変更なしで再利用可能であることを確認した（Target
Selectionドキュメントの`BATCH13_CONTRACT_REUSED`判定どおり）。

---

## 2. Target Identity Recheck（fresh実測）

Production read-only接続で、5社をfreshに再確認した。

| shrine | Production id | address | `place_ref_id IS NULL` | 同名件数 | deity_count | history_count |
|---|---:|---|---|---:|---:|---:|
| 王子神社 | 66 | 東京都北区王子本町1-1-12 | true | 1 | 0 | 0 |
| 足利織姫神社 | 85 | 栃木県足利市西宮町3889 | true | 1 | 0 | 0 |
| 鶴嶺八幡宮 | 90 | 神奈川県茅ヶ崎市浜之郷462 | true | 1 | 0 | 0 |
| 穴守稲荷神社 | 69 | 東京都大田区羽田5-2-7 | true | 1 | 0 | 0 |
| 玉前神社 | 79 | 千葉県長生郡一宮町一宮3048 | true | 1 | 0 | 0 |

全5社が`IDENTITY_SAFE`（重複なし・canonical・Knowledge none）。
Target Selection時点の記載と完全一致（drift 0）。numeric PKはseedへ
記録しない。

---

## 3. Official Sources（fresh確認、Browser pane / WebFetchで直接確認）

| shrine | Source URL | 確認内容 |
|---|---|---|
| 王子神社 | http://ojijinja.tokyo.jp/goyuisho/index.html | 伊邪那岐命・伊邪那美命・天照大御神・速玉之男命・事解之男命の五柱（総称「王子大神」）、元亨2年(1322)熊野三社勧請、天正19年(1591)徳川家康朱印地寄進、東京十社 |
| 足利織姫神社 | https://orihimejinjya.com/entry15.html | 天御鉾命・天八千々姫命の二柱、宝永2年(1705)合祀、明治12年(1879)機神山遷宮、昭和12年(1937)現社殿完成、平成16年(2004)国登録有形文化財 |
| 鶴嶺八幡宮 | https://www.tsuruminehachimangu.com/history/ | 應神天皇・仁徳天皇・佐塚大神＋鶴嶺天満宮合祀の菅原道真、長元三年(1030)源頼義勧請伝承、康平六年(1063)「元八幡」建立、弘安四年(1281)蒙古退散祈祷、昭和9年(1934)郷社列格 |
| 穴守稲荷神社 | https://anamori.jp/yuisho.html | 豊受姫命（単一祭神）、文化文政期の創祀伝承、明治18-19年(1885-1886)公衆参拝許可・社号官許、昭和20-23年(1945-1948)強制退去・現在地遷座 |
| 玉前神社 | https://tamasaki.org/yuisho/index.htm（由緒）、https://tamasaki.org/yuisho/saisin.htm（祭神） | 延喜式内名神大社・上総国一之宮、例祭1200年余の伝承、永禄年間の戦火焼失、玉依姫命（『延喜式』以来のご祭神。ただし公式サイト自身が『古社記には鵜茅葺不合命のご神名が併記』『考証がなされているところ』と明記） |

Target Selection時点の記載内容と完全に一致し、drift 0件だった。
王子神社・足利織姫神社はWebFetchが証明書ホスト名不一致・文字化けを
起こしたため、Browser paneで直接ページを開き確認した。玉前神社の
祭神は`yuisho/index.htm`には記載がなく、サイトマップ経由で発見した
専用ページ`yuisho/saisin.htm`で直接確認した。

---

## 4. Source Semantic Conflict

6件のSource候補URL（玉前神社のみ2件）を、Production既存91件のSourceと
freshに突合した。

```sql
SELECT id, source_type, title, publisher, url, verification_status, confidence, bibliography, language
FROM temples_shrineknowledgesource
WHERE url ILIKE '%ojijinja%' OR url ILIKE '%orihimejinjya%'
   OR url ILIKE '%tsuruminehachimangu%' OR url ILIKE '%anamori.jp%'
   OR url ILIKE '%tamasaki.org%';
```

結果: 0件（既存Sourceに一致なし）。**6候補Sourceすべてが`NO_CONFLICT`。**

---

## 5. Deity Research（各社固有の判断）

### 王子神社

公式サイトは伊邪那岐命・伊邪那美命・天照大御神・速玉之男命・事解之男命
の五柱を序列なく列挙し、総称して「王子大神」と呼ぶと記載している。
5柱それぞれを個別Fact化し、「王子大神」という総称自体は別Factとして
作成していない（role: unknown、序列の記載がないため）。境内末社
「関神社」（御祭神：蝉丸公）は本社とは別の社であり、Fact化対象から
除外した。

### 足利織姫神社

公式サイトから天御鉾命（織師）・天八千々姫命（織女）の二柱をfresh
確認し、対となる二柱として序列なく（role: unknown）Fact化した。

### 鶴嶺八幡宮

公式サイトの「御由緒」表に、本社御祭神として應神天皇・仁徳天皇・
佐塚大神の三柱（序列なし、role: unknown）、および同一表内に
「鶴嶺天満宮 合祀 菅原道真」の記載を直接確認した。菅原道真はこの
合祀情報に基づき`role: secondary`としてFact化した。ページ下部に
別途列挙されている「兼務社」11社（神明神社・厳島神社・山王社・
松尾大神・三島大神等、いずれも別住所・別法人の神社）は、本社の
御由緒表とは明確に区別されるセクションであり、いずれもFact化して
いない。

### 穴守稲荷神社

公式サイトから豊受姫命（役割: primary、公式サイトが明記する唯一の
祭神）をfresh確認した。境内社「羽田航空神社」「空港分社」は別途
祀られる社でありFact化していない。

### 玉前神社（completeness limitation）

公式サイト専用ページ（`yuisho/saisin.htm`）は「『延喜式』をはじめと
して当社のご祭神は玉依姫命のみとされてきました」と記載する一方、
同ページ内で「古社記には鵜茅葺不合命のご神名が併記されています」
「ご祭神に関しての考証がなされているところです」とも明記しており、
玉依姫命単独説が確定済みとは言い切れない状態であることを公式サイト
自身が認めている。以下のルールを厳守した。

- 玉依姫命のみをFact化（`role: primary`）。ただし上記の事情を反映し
  `confidence: medium`とした（他4社の全Deityは`confidence: high`）
- 未確定の鵜茅葺不合命を第二の祭神として確定Fact化しない
- トップページに登場する「その一族の神々」（上総十二社まつりの説明
  文脈）は個別名が示されていないため、collective Factとして作成
  していない。History Fact本文でもこの語をそのまま再掲せず、
  文言を変更して言及を避けた

**禁止事項の遵守確認**: 王子大神の重複Fact化＝0件、関神社（蝉丸公）
Fact混入＝0件、鶴嶺八幡宮の兼務社Fact混入＝0件、「その一族の神々」
のcollective Fact化＝0件、鵜茅葺不合命の確定Fact化＝0件、
associated worship target混入＝0件。

---

## 6. History Research

各社の由緒を、既存`history_type` enumへ適合する範囲でFact化した。
神話的伝承（`tradition`）と、年代が特定できる歴史的出来事
（`historical_event`）を明確に分離し、伝承文には非断定表現を用いた
（fresh確認: 全4件のtradition Factで確認済み: 王子神社の源義家伝承、
鶴嶺八幡宮の1030年源頼義勧請伝承、穴守稲荷神社の文化文政期創祀伝承、
玉前神社の例祭1200年余の伝承）。

| shrine | History Fact | 分類 |
|---|---|---|
| 王子神社 | 源義家にまつわる社頭祈願の伝承 | tradition |
| 王子神社 | 元亨2年(1322)の熊野三社勧請と「若一王子宮」への改称 | founding |
| 王子神社 | 徳川将軍家の庇護と東京十社への選定 | historical_event |
| 足利織姫神社 | 宝永2年(1705)の合祀と当地における祭祀の起源 | founding |
| 足利織姫神社 | 機神山への遷宮と現社殿の造営 | historical_event |
| 足利織姫神社 | 国登録有形文化財への指定 | historical_event |
| 鶴嶺八幡宮 | 長元三年(1030)の石清水八幡宮勧請伝承 | tradition |
| 鶴嶺八幡宮 | 康平六年(1063)の「元八幡」建立と「本社八幡宮」の呼称 | historical_event |
| 鶴嶺八幡宮 | 弘安四年(1281)の蒙古退散祈祷と「晦日祭」の成立 | historical_event |
| 鶴嶺八幡宮 | 江戸幕府の朱印地寄進と昭和9年(1934)の郷社列格 | historical_event |
| 穴守稲荷神社 | 文化文政期の創祀伝承 | tradition |
| 穴守稲荷神社 | 公衆参拝の許可と社号の官許 | historical_event |
| 穴守稲荷神社 | 戦後の強制退去と現在地への遷座 | historical_event |
| 玉前神社 | 延喜式内名神大社・上総国一之宮としての社格 | historical_event |
| 玉前神社 | 例祭に伝わる千二百年余の歴史 | tradition |
| 玉前神社 | 永禄年間の戦火による焼失 | historical_event |

長文の原文転載は行わず、要約に留めた。

---

## 7. Evidence Gate

全13 Deity・16 History Factについて確認した。

| 指標 | 値 |
|---|---:|
| source-less Deity | 0 |
| source-less History | 0 |
| `verification_status`が`source_confirmed`以外 | 0 |
| `confidence`が`high`/`medium`以外 | 0 |
| `verified_at`未設定 | 0 |
| invalid enum | 0 |
| identity unsafe | 0 |
| semantic conflict unsafe | 0 |

全件がEvidence Gate要件を満たす。玉前神社の玉依姫命のみ
`confidence: medium`（理由はSection 5参照）、他12 Deity・16 Historyは
`confidence: high`。

---

## 8. Canonical seed integrity

`backend/temples/data/knowledge_seeds/batch_14_seed.json`
（`schema_version: "1.0"`）。

`parse_seed()`（実装をそのまま使用したstructural検証）:

| 指標 | 値 |
|---|---:|
| errors | 0 |
| Source count | 6 |
| Shrine count | 5 |
| Deity count | 13 |
| History count | 16 |
| Deity–Source relation | 13 |
| History–Source relation | 16 |
| source-less Deity | 0 |
| source-less History | 0 |
| within-shrine重複 | 0 |
| invalid enum | 0 |
| unresolved source_key参照 | 0 |
| 数値Production PKのhardcode | 0 |

SHA-256（`batch_14_seed.json`）:
`c6fec20e888afb31b31f289855c96fca87c4e07a297dd9161f1897c2e9f866bb`

---

## 9. Regression tests

新規: `backend/temples/tests/test_batch14_knowledge_seed.py`（12件）。
Batch13の`test_batch13_knowledge_seed.py`と同型の構成に加え、本Batch
固有の以下を追加した。

- `test_batch14_seed_oji_jinja_does_not_duplicate_collective_name`:
  王子神社の「王子大神」（5柱の総称）が別Factとして作成されておらず、
  末社「関神社」（蝉丸公）も混入していないことを固定化
- `test_batch14_seed_tsurumine_excludes_kenmusha_and_only_includes_main_shrine_merger`:
  鶴嶺八幡宮の兼務社（天照大神・市杵島姫命・大山咋命・大山祗命等）が
  混入せず、御由緒表内の「鶴嶺天満宮合祀」菅原道真のみ`role: secondary`
  で含まれることを固定化
- `test_batch14_seed_tamasaki_excludes_unnamed_family_gods_and_unresolved_second_deity`:
  玉前神社が玉依姫命のみをFact化し、「その一族の神々」「鵜茅葺不合命」
  のいずれもFact化していないことを固定化
- `test_batch14_seed_no_excluded_names_anywhere`: 全8種の除外名が
  seed全体のどこにも出現しないことを固定化
- `test_batch14_seed_tamasaki_deity_confidence_is_medium_with_documented_reason`:
  玉前神社のみ`confidence: medium`で他4社は`high`であることを固定化
- `test_batch14_seed_source_semantic_identity_no_conflict_with_prior_batches`:
  Batch12/13・Batch14のSource URLが互いに衝突しないことを固定化

既存の汎用テスト（24件）・Batch9/10/11/12/13テスト（33件）を含め、
合計69件すべてPASS（回帰なし。`pytest -p no:dotenv`でlocal-onlyの
`pytest-dotenv`プラグイン競合を回避、後述Section 17参照）。

---

## 10. Local validation

ローカル`jinja_db`（対象5社は既存Production idと一致する形で存在、
import前はいずれもdeity=0/history=0を確認済み）に対して実際に実行:

| step | 結果 |
|---|---|
| `--validate-only` | `validate-only: OK, no errors` |
| `--dry-run`（1回目） | `{'source_CREATE': 6, 'deity_CREATE': 13, 'history_CREATE': 16}` |
| 適用（import） | `sources created=6, deities created=13, histories created=16` |
| 件数検証 | 対象5社の内訳は5/3・2/3・4/4・1/3・1/3件（seedと完全一致）、source-less 0件 |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 6, 'deity_SKIP_EXISTS': 13, 'history_SKIP_EXISTS': 16}`、CREATE 0件 |

---

## 11. Production read-only baseline

Production DBをfreshに確認した（過去値を固定せず、本セッションの実測を
正本とする）。

| 指標 | 実測値 |
|---|---:|
| Knowledge Shrine | 71 |
| Source | 91 |
| Deity | 197 |
| History | 133 |
| Deity–Source relation | 210 |
| History–Source relation | 138 |
| complete | 69 |
| partial | 2 |
| none | 34 |
| 総Shrine数 | 105 |

Application aggregates: auth_user 1・userprofile 1・shrine 105・favorite 0・
visit 2・goriyakutag 39・shrine_goriyaku_relation 283。

対象5社は全件Knowledge none、drift 0件（Target Selection時点・本
セッションのPhase 2再確認いずれとも一致）。

---

## 12. Fresh Production Backup

PostgreSQL 17バージョン一致クライアント（`postgresql@17.10`、
Production側`PostgreSQL 17.6`と確認）で新規取得（過去のBackupを
再利用していない）。

| ファイル | サイズ |
|---|---:|
| roles.sql | 5,426 bytes |
| schema.sql | 93,021 bytes |
| data.sql | 4,313,741 bytes |

repo外（`~/kami-musubi-backups/batch14-seed-preparation-<timestamp>/`）
に保存。接続情報・hostname・credentialは一切ログに出力していない。

---

## 13. Fresh Production-equivalent test

上記backupを`kami_musubi_migration_safety_b14<timestamp>`（disposable
local DB）へ復元した。復元は`exit 0`で完了。

復元直後のisolated DB確認: Production同時刻の値（Source91・Deity197・
History133・relation210/138・Knowledge Shrine71・総Shrine105）と完全
一致。対象5社は全件Knowledge none。

isolated DBに対して、ローカルと同一の5ステップ＋追加確認を実施:

| step | 結果 |
|---|---|
| `--validate-only` | OK, no errors |
| `--dry-run`（1回目） | `{'source_CREATE': 6, 'deity_CREATE': 13, 'history_CREATE': 16}` |
| 適用 | `sources created=6, deities created=13, histories created=16` |
| 件数検証 | Source 91→97・Deity 197→210・History 133→149・Deity–Source rel 210→223・History–Source rel 138→154・Knowledge Shrine 71→76（いずれもseed件数と完全一致） |
| 対象5社のdeity/history内訳 | 王子神社5/3・足利織姫神社2/3・鶴嶺八幡宮4/4・穴守稲荷神社1/3・玉前神社1/3（seedと完全一致、混入なし） |
| Coverage | complete 69→74・partial 2（不変）・none 34→29 |
| source-less（DB全体） | Deity 0・History 0 |
| 除外名混入チェック（対象5社スコープ） | 「王子大神」「蝉丸公」「その一族の神々」「鵜茅葺不合命」「天照大神」「市杵島姫命」「大山咋命」「大山祗命」いずれも対象5社では0件 |
| 無関係データ回帰チェック | 富岡八幡宮1/2（非canonical重複行0/0も不変）・忌宮神社3/2・鷲宮神社2/2（いずれも既存値のまま不変） |
| Application aggregate | auth_user1・userprofile1・shrine105・favorite0・visit2・goriyakutag39・shrine_goriyaku_rel283（完全不変） |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 6, 'deity_SKIP_EXISTS': 13, 'history_SKIP_EXISTS': 16}`、CREATE 0件 |

isolated DBは検証完了後に`dropdb`で削除済み（削除後の存在確認も実施
済み）。

---

## 14. Coverage projection

isolated DB（Production-equivalent）の実測値から算出（推測値は使用して
いない）。5社すべてが投入前`none`のため、5社ともDeity/History両方を
獲得しcompleteへ移行する（先に決め打ちせず、実測で確認）。

| 区分 | Batch14投入前（実測） | Batch14投入後（実測） |
|---|---:|---:|
| complete | 69 | 74 |
| partial | 2 | 2（不変） |
| none | 34 | 29 |
| Knowledge Shrine合計 | 71 | 76 |
| 全Shrine数 | 105 | 105（不変） |

---

## 15. Production read-only preflight

Production DBに対して以下を実行した（いずれもコマンド自身の設計上、
DB書き込みを一切行わないモード）。

**`--validate-only`**: `validate-only: OK, no errors`

**`--dry-run`**:
```
plan summary: {'source_CREATE': 6, 'deity_CREATE': 13, 'history_CREATE': 16}
dry-run: OK, no DB writes performed
```

全項目、isolated DBの1回目`--dry-run`結果と完全一致。`SKIP_EXISTS`・
`REUSE_EXISTING`・`SOURCE_REUSE_CONFLICT`・`SOURCE_REUSE_AMBIGUOUS`・
`IMPORT_IDENTITY_AMBIGUOUS`・`NOT_FOUND`はいずれも0件。

実行後、`readonly_query.sh`で再度Production状態を確認し、対象5社の
deity/history、および集計値（Source91・Deity197・History133・
relation210/138・Knowledge Shrine71・総Shrine105）が実行前と完全に
不変であることを確認した。

---

## 16. Runtime expected payload

seedから算出（Production import実行後に期待される値、実行はしていない）。

| shrine | Deity | History | Unique Source |
|---|---:|---:|---:|
| 王子神社 | 5 | 3 | 1 |
| 足利織姫神社 | 2 | 3 | 1 |
| 鶴嶺八幡宮 | 4 | 4 | 1 |
| 穴守稲荷神社 | 1 | 3 | 1 |
| 玉前神社 | 1 | 3 | 2 |
| **合計** | **13** | **16** | **6** |

Fact–Source relation count: 29（Deity 13 + History 16）。

玉前神社のみUnique Source 2件（由緒ページ・祭神ページが別URL）。

---

## 17. Risk Audit

- **玉前神社 unnamed-family-gods limitation**: 公式サイトが「その一族の
  神々」の個別名を明かしておらず、また「古社記には鵜茅葺不合命の
  ご神名が併記」「考証がなされているところ」と自ら未確定を認めている
  ため、Deity Factは玉依姫命1柱のみ（`confidence: medium`）。未確認の
  鵜茅葺不合命・家族神を推測登録していない（テストで固定化済み）。
- **王子大神 collective-name treatment**: 「王子大神」は5柱の総称に
  過ぎず、別Factとして作成していない（テストで固定化済み）。
- **鶴嶺八幡宮兼務社 separation**: 御由緒表内の「鶴嶺天満宮合祀」
  菅原道真のみをFact化し、ページ下部の兼務社11社（別住所・別法人）は
  明確に区別して除外した（テストで固定化済み）。
- **Source page instability**: 他Batchと同様の一般的リスク。
- **`SKIP_EXISTS`のsemantic-diff limitation**: 既知の設計上の制約であり、
  本Batchに固有の問題ではない。
- **historical tradition / history distinction**: 全4件のtradition Fact
  で非断定表現を確認済み（fresh検証）。
- **identity/address exactness**: 5社全件、Production記載住所と完全
  一致することをfreshに確認済み。
- **新規のcontent-model問題**: 発生していない。赤城神社
  （`MODEL_REVIEW_REQUIRED`）・千住神社（associated worship target）は
  Target Selection段階で既にRecommended 5から除外されており、本
  Seed Preparationでは対象としていない。

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
- **軽微な制限あり**: 玉前神社のDeity Evidenceが1柱のみ、かつ
  `confidence: medium`（公式サイト自身が祭神を考証中と明記している
  ことの反映であり、Evidence Gateは遵守）

**`BATCH14_PRODUCTION_IMPORT_READY_WITH_LIMITATIONS`**

残存する非blocking事項（Productionへの実書き込み判断とは独立）:

- 玉前神社の鵜茅葺不合命は、公式サイトの考証が確定した場合に追加
  Fact化を検討できる
- partial 2社（阿佐ヶ谷神明宮・香取神宮）のHistory repairは別タスクの
  まま
- `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`（千住神社等）は未着手のまま
- 靖國神社・千葉神社・愛宕神社・赤城神社のcontent-model判断は引き続き
  保留
- `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`（pytest-dotenvのlocal-only
  のdrift）は継続、本ドキュメントでもpackage変更は行っていない
- Production importそのもの（Fact実書き込み・Runtime QA）は本ドキュメント
  では未実施。Mother Shipの明示的な承認後、別セッション（Human
  Execution Boundary Gate相当）で実施する必要がある

Production DB writes = 0
Batch 14 Production import = NOT_EXECUTED
Batch 15 = NOT_STARTED

---

## 最終報告サマリ

1. develop SHA: `ec0046cb6237c802fbf3679d538d3cd0d3a99d2d`
2. targets: 王子神社・足利織姫神社・鶴嶺八幡宮・穴守稲荷神社・玉前神社
3. official Sources: Section 3参照（全6件、Browser pane / WebFetchで直接fresh確認）
4. Source conflict/reuse: 6件全て`NO_CONFLICT`
5. content-model handling: Section 5・17参照
6. seed hash: `c6fec20e888afb31b31f289855c96fca87c4e07a297dd9161f1897c2e9f866bb`
7. Shrine count: 5
8. Source count: 6
9. Deity count: 13
10. History count: 16
11. relations: Deity–Source 13・History–Source 16
12. source-less: 0
13. ambiguous: 0
14. tests: 新規12件＋既存57件＝合計69件PASS
15. local validation: フルサイクル完了、件数一致
16. idempotency: PASS（ローカル・isolated DB・Production dry-run全て）
17. Production baseline: Knowledge Shrine71・Source91・Deity197・History133・rel210/138
18. fresh backup: roles 5,426B・schema 93,021B・data 4,313,741B（repo外保存）
19. Production-equivalent: フルサイクル完了、件数一致、コンタミネーション0
20. Coverage projection: complete69→74・partial2（不変）・none34→29
21. Production validate-only: OK, no errors
22. Production dry-run: `{'source_CREATE': 6, 'deity_CREATE': 13, 'history_CREATE': 16}`、Production状態不変を確認
23. Runtime expected payload: Section 16参照（合計Deity13・History16・Unique Source6）
24. risks: Section 17参照
25. final classification: `BATCH14_PRODUCTION_IMPORT_READY_WITH_LIMITATIONS`
26. audit doc: 本ドキュメント
    （`docs/audit/knowledge-batch14-seed-preflight.md`）
27. PR: 別途作成（本ドキュメントのcommit時に作成）
28. CI: PR作成後に確認

Production DB writes = 0
Batch 14 Production import = NOT_EXECUTED
Batch 15 = NOT_STARTED
