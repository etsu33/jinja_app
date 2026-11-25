> **Status: `BATCH15_PRODUCTION_IMPORT_READY`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch15-target-selection.md`
> （`BATCH15_TARGET_SELECTION_READY`）で選定されたRecommended 5社に
> ついて、Knowledge seedを構築し、Production投入直前の技術Gateまで
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
> 全Deity/History Factが`confidence: high`で確定でき、Batch 14の玉前神社
> のような`confidence: medium`への格下げが必要な事例は生じなかったため、
> `READY_WITH_LIMITATIONS`ではなく`READY`とした。

develop SHA（作業開始時点、PR #2374 merge後）:
`c6212c4904889ed69886bffe373a049ddb7ad923`
（`origin/develop`と同期済み、working tree clean）。

**Base State注記**: 着手時点でPR #2374（Target Selection）が未mergeで
あることが判明したため、Mother Shipの明示承認を得た上でPR #2374を
merge（squash）してから本Seed Preparationに着手した
（Batch 13 Seed Preparation時のPR #2368と同型の対応）。

---

## 1. Base state and contracts

`docs/audit/knowledge-batch15-target-selection.md`を再読し、
Recommended 5社を対象として確定した。

freshに再読した既存contract:

- `docs/knowledge/shrine-knowledge-contract.md`
- `backend/temples/data/knowledge_seeds/batch_14_seed.json`（seed構造のテンプレート）
- `backend/temples/tests/test_batch14_knowledge_seed.py`
- `backend/temples/services/knowledge_seed.py`
- `backend/temples/management/commands/import_shrine_knowledge.py`
- `docs/audit/knowledge-batch14-seed-preflight.md`
- `docs/audit/knowledge-batch14-closure-batch15-reentry.md`

いずれも構造変更なしで再利用可能であることを確認した。

---

## 2. Target Identity Recheck（fresh実測）

Production read-only接続で、5社をfreshに再確認した。

| shrine | Production id | `place_ref_id IS NULL` | 同名重複 | deity_count | history_count |
|---|---:|---|---:|---:|---:|
| 湯島天満宮 | 64 | true | 1 | 0 | 0 |
| 報徳二宮神社 | 92 | true | 1 | 0 | 0 |
| 箭弓稲荷神社 | 76 | true | 1 | 0 | 0 |
| 水戸東照宮 | 53 | true | 1 | 0 | 0 |
| 葛西神社 | 68 | true | 1 | 0 | 0 |

**全5社が`IDENTITY_SAFE`。** Target Selection時点の記載と完全一致
（drift 0）。numeric PKはseedへ記録しない。

---

## 3. Official Sources（Target Selection時の結果を再利用せずfresh確認）

5社すべての公式サイトをBrowser paneで**再度**直接確認した。取得内容は
Target Selectionセッション時と完全に一致し、drift 0件だった。

| shrine | Source URL | 確認内容 |
|---|---|---|
| 湯島天満宮 | https://www.yushimatenjin.or.jp/pc/engi/engi.htm | 天之手力雄命・菅原道真公、雄略天皇2年(458)創建伝承、正平10年(1355)道真勧請、天正18-19年(1590-91)家康崇敬、明治5-18年(1872-85)社格昇格、平成7年(1995)現社殿造営 |
| 報徳二宮神社 | https://www.ninomiya.or.jp/sontoku/（祭神）、https://www.ninomiya.or.jp/info/（由緒） | 二宮尊徳翁、明治27年(1894)創建、明治42年本殿新築、平成6年(1994)創建百年記念 |
| 箭弓稲荷神社 | https://www.yakyu-inari.jp/yuisho/ | 保食神、和銅5年(712)創建伝承、源頼信の戦勝祈願伝承、末社「團十郎稲荷」（宇迦之御魂神）は別掲 |
| 水戸東照宮 | https://gongensan-mito-toshogu.jp/gosaisin.html | 徳川家康公・徳川頼房公、元和7年(1621)創建、天保14年(1843)神道祭祀改革、昭和11年(1936)配祀、昭和20年(1945)焼失、昭和37年(1962)再建 |
| 葛西神社 | https://www.kasaijinja.jp/about/saijin.html（祭神）、https://www.kasaijinja.jp/about/（由緒） | 経津主神・日本武尊・徳川家康命、元暦2年(1185)創建・香取神宮分霊、天正18-19年(1590-91)秀吉・家康より御朱印、明治14年(1881)改称 |

---

## 4. Source Semantic Conflict

7件のSource候補（湯島天満宮1・報徳二宮神社2・箭弓稲荷神社1・水戸東照宮1・
葛西神社2）を、Production既存97件のSourceとfreshに突合した。

```sql
SELECT id, source_type, title, publisher, url FROM temples_shrineknowledgesource
WHERE url ILIKE '%yushimatenjin%' OR url ILIKE '%ninomiya.or.jp%'
   OR url ILIKE '%yakyu-inari%' OR url ILIKE '%mito-toshogu%'
   OR url ILIKE '%kasaijinja%';
```

結果: 0件。**7候補Sourceすべてが`NO_CONFLICT`。**

---

## 5. Deity Research（各社固有の判断）

### 湯島天満宮

公式サイトから天之手力雄命（雄略天皇2年/458年の創建時に奉斎）・
菅原道真公（正平10年/1355年に勧請合祀）の二柱をfresh確認した。序列の
記載がないため両柱`role: unknown`とした。

### 報徳二宮神社（biography / shrine historyの分離）

公式サイトの「御祭神」専用ページ（`sontoku/`）から二宮尊徳翁
（1787-1856）をfresh確認し、`role: primary`でFact化した。同ページは
尊徳翁個人の伝記的記述（財政再建の功績、五常講、内村鑑三による紹介等）
が大半を占めるが、これは**Deity Factの根拠としてのみ使用**し、Shrine
History Factは別ページ（`info/`、神社自体の創建・社殿整備の由緒）
のみを根拠とした。伝記内容をShrine Historyへ混入させていないことを
テストで固定化した。

### 箭弓稲荷神社

公式サイトから保食神（本社唯一の御祭神）をfresh確認した。末社
「團十郎稲荷」（御祭神：宇迦之御魂神、通称「穴宮」、七代目市川團十郎
ゆかりの由緒を持つ）は本社ページとは明確に区別されて紹介されており、
Fact化対象から除外した。

### 水戸東照宮

公式サイトから徳川家康公（東照公、`role: primary`）・徳川頼房公
（威公、`role: secondary`、昭和11年配祀）の二柱をfresh確認した。公式
サイト自身が「当初は神仏習合で仏祭だったが、天保14年(1843)に神道による
祭祀にあらためられた」と明記しており、現在は神仏習合状態ではないことが
公式Source自体から確認できる。

### 葛西神社

公式サイトから経津主神・日本武尊・徳川家康命（東照権現さま）の三柱を、
各柱の個別説明とともにfresh確認した。序列の記載はないため三柱とも
`role: unknown`とした。境内社（招魂社・弁天・富士）は「ご祭神」ページ
には含まれず、年中行事名（招魂社祭・弁天祭・富士祭）としてのみ言及
されているため、Fact化対象から明確に除外した。

**禁止事項の遵守確認**: unnamed deityの推測登録＝0件（冠稲荷神社の
「ほか15柱以上」はTarget Selection段階で既にRecommended 5から除外
済み）、collective name重複登録＝0件、摂社/末社祭神の混入＝0件
（箭弓稲荷神社の團十郎稲荷）、境内社祭神の混入＝0件（葛西神社の
招魂社・弁天・富士）、associated worship targetの混入＝0件、仏教尊格の
無理なDeity化＝0件、根拠のない読み仮名＝0件（`canonical_name`は
公式表記の範囲内のみ）。

---

## 6. History Research

各社の由緒を、既存`history_type` enumへ適合する範囲でFact化した。
伝承（`tradition`）と歴史的出来事（`historical_event`）を明確に分離し、
伝承文には非断定表現を用いた（fresh確認: 全4件のtradition Factで
確認済み: 湯島天満宮の458年創建伝承、箭弓稲荷神社の712年創建伝承と
源頼信の戦勝祈願伝承）。

| shrine | History Fact | 分類 |
|---|---|---|
| 湯島天満宮 | 雄略天皇2年(458)の創建伝承と天之手力雄命の奉斎 | tradition |
| 湯島天満宮 | 正平10年(1355)の菅原道真公勧請合祀 | historical_event |
| 湯島天満宮 | 戦国期の再興と徳川家康公の崇敬 | historical_event |
| 湯島天満宮 | 社格の変遷と平成の社殿造営 | historical_event |
| 報徳二宮神社 | 明治27年(1894)の創建 | founding |
| 報徳二宮神社 | 明治42年の社殿整備 | historical_event |
| 報徳二宮神社 | 拝殿礎石にまつわる由来 | historical_event |
| 報徳二宮神社 | 平成6年(1994)の創建百年記念 | historical_event |
| 箭弓稲荷神社 | 和銅5年(712)の創建伝承 | tradition |
| 箭弓稲荷神社 | 源頼信の戦勝祈願と社名改称の伝承 | tradition |
| 箭弓稲荷神社 | 江戸期以降の隆盛と文化財指定 | historical_event |
| 水戸東照宮 | 元和7年(1621)の創建 | founding |
| 水戸東照宮 | 神仏習合の仏祭から神道祭祀への改革 | historical_event |
| 水戸東照宮 | 配祀・戦災焼失と戦後の再建 | historical_event |
| 水戸東照宮 | 東日本大震災の被災と大鳥居再建 | historical_event |
| 葛西神社 | 元暦2年(1185)の創建と香取神宮分霊 | founding |
| 葛西神社 | 豊臣秀吉・徳川家康による御朱印拝進 | historical_event |
| 葛西神社 | 社名の変遷と社格 | historical_event |

長文の原文転載は行わず、要約に留めた。

---

## 7. Shrine-specific Content-model Review

| shrine | 確認事項 | 結果 |
|---|---|---|
| 湯島天満宮 | 境内社祭神の混入なし。天之手力雄命と菅原道真公の合祀構造は既存precedent（鶴嶺八幡宮の鶴嶺天満宮合祀パターン）と整合 | `MODEL_FIT_SAFE` |
| 報徳二宮神社 | 人物神格化（乃木神社に前例あり）。biographyとShrine Historyを明確に分離（Section 5参照） | `MODEL_FIT_SAFE` |
| 箭弓稲荷神社 | 稲荷信仰の個別祭神（保食神）を明確化。境内社（團十郎稲荷）を除外 | `MODEL_FIT_SAFE` |
| 水戸東照宮 | 人物神格化（東照宮型）。神仏習合から神道祭祀への改革を公式Source自身が明記しており、一般論としての東照宮説明と当該神社固有のHistoryを混同していない（本文はすべて水戸東照宮固有の記述） | `MODEL_FIT_SAFE` |
| 葛西神社 | 主祭神と境内社（招魂社・弁天・富士）を分離。三柱に合祀・配祀の記載はなく、いずれも創建当初からの祭神として扱った | `MODEL_FIT_SAFE` |

**Recommended 5全件が`MODEL_FIT_SAFE`。**

---

## 8. Evidence Gate

全9 Deity・18 History Factについて確認した。

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

全件がEvidence Gate要件を満たす。全27 Fact（Deity9+History18）が
`confidence: high`であり、Batch 14の玉前神社のような`medium`への
格下げは本Batchでは生じなかった。

---

## 9. Canonical seed integrity

`backend/temples/data/knowledge_seeds/batch_15_seed.json`
（`schema_version: "1.0"`）。

`parse_seed()`（実装をそのまま使用したstructural検証）:

| 指標 | 値 |
|---|---:|
| errors | 0 |
| Source count | 7 |
| Shrine count | 5 |
| Deity count | 9 |
| History count | 18 |
| Deity–Source relation | 9 |
| History–Source relation | 18 |
| source-less Deity | 0 |
| source-less History | 0 |
| within-shrine重複 | 0 |
| invalid enum | 0 |
| unresolved source_key参照 | 0 |
| 数値Production PKのhardcode | 0 |

SHA-256（`batch_15_seed.json`）:
`ad8fcb6d25f5b85982207cc4305602c0b2b49577b441e9d111b7d1e92593b1d2`

---

## 10. Regression tests

新規: `backend/temples/tests/test_batch15_knowledge_seed.py`（9件）。
Batch14の`test_batch14_knowledge_seed.py`と同型の構成に加え、本Batch
固有の以下を追加した。

- `test_batch15_seed_yakyu_inari_excludes_sub_shrine_deity`: 箭弓稲荷
  神社の末社「團十郎稲荷」（宇迦之御魂神）が本社Factに混入していない
  ことを固定化
- `test_batch15_seed_kasai_excludes_grounds_sub_shrines`: 葛西神社の
  境内社（招魂社・弁天・富士）が三柱の祭神一覧に混入していないことを
  固定化
- `test_batch15_seed_ninomiya_history_excludes_biography_content`:
  報徳二宮神社のHistory Factが由緒ページのみを根拠とし、二宮尊徳翁
  個人の伝記的内容（「五常講」「内村鑑三」等）を含んでいないことを
  固定化
- `test_batch15_seed_role_assignment_matches_official_hierarchy`:
  報徳二宮神社・箭弓稲荷神社・水戸東照宮のrole割当てが公式サイトの
  記載と一致することを固定化

既存の汎用テスト（24件）・Batch9〜14テスト（46件）を含め、合計79件
すべてPASS（回帰なし。`pytest -p no:dotenv`でlocal-onlyの
`pytest-dotenv`プラグイン競合を回避）。

---

## 11. Local validation

ローカル`jinja_db`（対象5社は既存Production idと一致する形で存在、
import前はいずれもdeity=0/history=0を確認済み）に対して実際に実行:

| step | 結果 |
|---|---|
| `--validate-only` | `validate-only: OK, no errors` |
| `--dry-run`（1回目） | `{'source_CREATE': 7, 'deity_CREATE': 9, 'history_CREATE': 18}` |
| 適用（import） | `sources created=7, deities created=9, histories created=18` |
| 件数検証 | 対象5社の内訳は2/4・1/4・1/3・2/4・3/3件（seedと完全一致）、source-less 0件 |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 7, 'deity_SKIP_EXISTS': 9, 'history_SKIP_EXISTS': 18}`、CREATE 0件 |

---

## 12. Production read-only baseline

Production DBをfreshに確認した（過去値を固定せず、本セッションの実測を
正本とする）。

| 指標 | 実測値 |
|---|---:|
| Knowledge Shrine | 76 |
| Source | 97 |
| Deity | 210 |
| History | 149 |
| Deity–Source relation | 223 |
| History–Source relation | 154 |
| complete | 74 |
| partial | 2 |
| none | 29 |
| 総Shrine数 | 105 |

Application aggregates: auth_user 1・userprofile 1・shrine 105・favorite 0・
visit 2・goriyakutag 39・shrine_goriyaku_relation 283。

対象5社は全件Knowledge none、drift 0件。

---

## 13. Fresh Production Backup

PostgreSQL 17バージョン一致クライアント（`postgresql@17.10`、
Production側`PostgreSQL 17.6`）で新規取得（過去のBackupを再利用して
いない）。

| ファイル | サイズ |
|---|---:|
| roles.sql | 5,426 bytes |
| schema.sql | 93,021 bytes |
| data.sql | 4,330,471 bytes |

repo外（`~/kami-musubi-backups/batch15-seed-preparation-<timestamp>/`）
に保存。接続情報・hostname・credentialは一切ログに出力していない。

---

## 14. Fresh Production-equivalent test

上記backupを`kami_musubi_migration_safety_b15<timestamp>`（disposable
local DB）へ復元した。復元は`exit 0`で完了。

復元直後のisolated DB確認: Production同時刻の値（Source97・Deity210・
History149・relation223/154・Knowledge Shrine76・総Shrine105）と完全
一致。対象5社は全件Knowledge none。

isolated DBに対して、ローカルと同一の5ステップ＋追加確認を実施:

| step | 結果 |
|---|---|
| `--validate-only` | OK, no errors |
| `--dry-run`（1回目） | `{'source_CREATE': 7, 'deity_CREATE': 9, 'history_CREATE': 18}` |
| 適用 | `sources created=7, deities created=9, histories created=18` |
| 件数検証 | Source 97→104・Deity 210→219・History 149→167・Deity–Source rel 223→232・History–Source rel 154→172・Knowledge Shrine 76→81（いずれもseed件数と完全一致） |
| 対象5社のdeity/history内訳 | 湯島天満宮2/4・報徳二宮神社1/4・箭弓稲荷神社1/3・水戸東照宮2/4・葛西神社3/3（seedと完全一致、混入なし） |
| Coverage | complete 74→79・partial 2（不変）・none 29→24 |
| source-less（DB全体） | Deity 0・History 0 |
| 除外名混入チェック（対象5社スコープ） | 「宇迦之御魂神」（箭弓稲荷神社末社の祭神）が対象5社では0件 |
| 無関係データ回帰チェック | 王子神社5/3・足利織姫神社2/3・鶴嶺八幡宮4/4・穴守稲荷神社1/3・玉前神社1/3・富岡八幡宮1/2（非canonical重複行0/0も不変）（いずれもBatch14投入値のまま不変） |
| Application aggregate | auth_user1・userprofile1・shrine105・favorite0・visit2・goriyakutag39・shrine_goriyaku_rel283（完全不変） |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 7, 'deity_SKIP_EXISTS': 9, 'history_SKIP_EXISTS': 18}`、CREATE 0件 |

isolated DBは検証完了後に`dropdb`で削除済み（削除後の存在確認も実施
済み）。

---

## 15. Production read-only preflight

Production DBに対して以下を実行した（いずれもコマンド自身の設計上、
DB書き込みを一切行わないモード）。

**`--validate-only`**: `validate-only: OK, no errors`

**`--dry-run`**:
```
plan summary: {'source_CREATE': 7, 'deity_CREATE': 9, 'history_CREATE': 18}
dry-run: OK, no DB writes performed
```

全項目、isolated DBの1回目`--dry-run`結果と完全一致。`SKIP_EXISTS`・
`REUSE_EXISTING`・`SOURCE_REUSE_CONFLICT`・`SOURCE_REUSE_AMBIGUOUS`・
`IMPORT_IDENTITY_AMBIGUOUS`・`NOT_FOUND`はいずれも0件。

実行後、`readonly_query.sh`で再度Production状態を確認し、対象5社の
deity/history、および集計値（Source97・Deity210・History149・
relation223/154・Knowledge Shrine76・総Shrine105）が実行前と完全に
不変であることを確認した。

---

## 16. Runtime Expected Payload

seedから算出（Production import実行後に期待される値、実行はしていない）。

| shrine | Deity | History | Unique Source |
|---|---:|---:|---:|
| 湯島天満宮 | 2 | 4 | 1 |
| 報徳二宮神社 | 1 | 4 | 2 |
| 箭弓稲荷神社 | 1 | 3 | 1 |
| 水戸東照宮 | 2 | 4 | 1 |
| 葛西神社 | 3 | 3 | 2 |
| **合計** | **9** | **18** | **7** |

Fact–Source relation count: 27（Deity 9 + History 18）。

---

## 17. Runtime Exposure Compatibility

コード変更は一切行っていない。`docs/audit/knowledge-batch14-closure-batch15-reentry.md`
で確認済みの経路（`ShrineDetailSerializer`→BFF `/api/shrines/<id>/data/`
→Web `buildShrineFactSection`/`ShrineFactSection`→
`concierge_chat_candidates.py`経由のRecommendation）を、本Batch15
seedのfresh再確認としてもfreshに再確認した。

```
GET https://jinja-backend.onrender.com/api/shrines/66/data/
→ HTTP 200, name_jp=王子神社, deities=5, histories=3
```

Batch14で投入したFactが変わらずRuntime公開されていることを確認した
（本Batch15 seedはBatch14と同一の`schema_version: "1.0"`・同一field
構成であり、`ShrineDeitySerializer`/`ShrineHistorySerializer`の
`fields`と完全に互換）。

**分類: `KNOWLEDGE_RUNTIME_COMPATIBLE`。**

---

## 18. Risk Audit

- **historical human deification**: 報徳二宮神社（二宮尊徳翁）・
  水戸東照宮（徳川家康公・徳川頼房公）・葛西神社（徳川家康命）の
  3社5柱が該当する。いずれも乃木神社・東照宮全国の前例に基づく
  確立したパターンであり、新規のcontent-model判断を要しない
  （既存contractで処理可能）
- **collective deity / unnamed deity**: 0件（冠稲荷神社はTarget
  Selection段階で除外済み）
- **associated worship target**: 0件
- **七福神**: 0件
- **Buddhist deity**: 0件（水戸東照宮の歴史的神仏習合は公式Source
  自身が「天保14年(1843)に神道による祭祀にあらためられた」と明記して
  おり、現在の祭祀構造には影響しない）
- **摂社/末社**: 箭弓稲荷神社の團十郎稲荷を除外
- **境内社**: 葛西神社の招魂社・弁天・富士を除外
- **merged shrine history**: 湯島天満宮の天之手力雄命/菅原道真公の
  合祀構造は、role=unknownとして対等に扱い、序列を推測していない
- **tradition assertion**: tradition分類の4件すべてで非断定表現
  （「伝えられ」「社記によると」）を維持
- **ambiguous Source reuse**: 0件（全7件`NO_CONFLICT`）

新規のcontent-model判断が必要な事項は発生しなかったため、
`MOTHER_SHIP_REVIEW_REQUIRED`には該当しない。**続行可能。**

---

## 19. Coverage Projection

isolated DB（Production-equivalent）の実測値から算出した
**projection**（Production実測ではない）。5社すべてが投入前`none`の
ため、5社ともDeity/History両方を獲得しcompleteへ移行する見込みである。

| 区分 | Batch15投入前（実測） | Batch15投入後（projection） |
|---|---:|---:|
| complete | 74 | 79 |
| partial | 2 | 2（不変） |
| none | 29 | 24 |
| Knowledge Shrine合計 | 76 | 81 |
| 全Shrine数 | 105 | 105（不変） |

---

## 20. Final Classification

- 5社全件が`IDENTITY_SAFE`・`NO_CONFLICT`・Evidence Gate要件を満たす
- ローカル・Production-equivalent（fresh dump復元）の両方で
  `--validate-only`→`--dry-run`→適用→件数検証→再`--dry-run`の
  フルサイクルが期待どおりの結果
- Production DBに対する`--validate-only`・`--dry-run`がProduction-equivalent
  の結果と完全一致し、unexpected SKIP/UPDATE/conflictが0件
- Production状態がこれらの読み取り専用操作の前後で完全に不変であることを
  実測で確認
- 候補の差替えは発生していない
- 全27 Fact（Deity9+History18）が`confidence: high`（`medium`への
  格下げなし）
- `KNOWLEDGE_RUNTIME_COMPATIBLE`確認済み
- Risk Auditで新規content-model判断は不要と判定

**`BATCH15_PRODUCTION_IMPORT_READY`**

残存する非blocking事項（Productionへの実書き込み判断とは独立）:

- partial 2社（阿佐ヶ谷神明宮・香取神宮）のHistory repairは別タスクの
  まま
- model-risk 5件（靖國神社・千葉神社・愛宕神社・赤城神社・千住神社）の
  content-model判断は引き続き保留
- 冠稲荷神社の特別設計（本殿の確認できる数柱のみに限定する等）は
  未着手
- `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`（pytest-dotenvのlocal-only
  のdrift）は継続
- Production importそのもの（Fact実書き込み・Runtime QA）は本ドキュメント
  では未実施。Mother Shipの明示的な承認後、別セッション（Human
  Execution Boundary Gate相当）で実施する必要がある

Production DB writes = 0
Batch 15 Production import = NOT_EXECUTED
Batch 16 = NOT_STARTED

---

## 最終報告サマリ

1. develop SHA: `c6212c4904889ed69886bffe373a049ddb7ad923`
2. target 5: 湯島天満宮・報徳二宮神社・箭弓稲荷神社・水戸東照宮・葛西神社
3. identity result: 全5社`IDENTITY_SAFE`
4. official Source result: 全5社公式Source直接確認、drift 0
5. Source conflict: 7件全て`NO_CONFLICT`
6. seed hash: `ad8fcb6d25f5b85982207cc4305602c0b2b49577b441e9d111b7d1e92593b1d2`
7. seed counts: Shrine5・Source7・Deity9・History18・relation27
8. Deity counts: 9（全件confidence: high）
9. History counts: 18（全件confidence: high）
10. Evidence Gate: 全件PASS、source-less 0
11. content-model exclusions: 團十郎稲荷（箭弓稲荷神社末社）・招魂社/弁天/富士（葛西神社境内社）・二宮尊徳翁の伝記内容（報徳二宮神社History除外）
12. tests: 新規9件＋既存70件＝合計79件PASS
13. local validation: フルサイクル完了、件数一致
14. Production baseline: Knowledge Shrine76・Source97・Deity210・History149・rel223/154
15. backup: roles 5,426B・schema 93,021B・data 4,330,471B（repo外保存）
16. Production-equivalent: フルサイクル完了、件数一致、コンタミネーション0
17. Production validate-only: OK, no errors
18. Production dry-run: `{'source_CREATE': 7, 'deity_CREATE': 9, 'history_CREATE': 18}`、Production状態不変
19. Runtime Expected Payload: 合計Deity9・History18・Unique Source7
20. Runtime compatibility: `KNOWLEDGE_RUNTIME_COMPATIBLE`
21. coverage projection: complete74→79・partial2（不変）・none29→24
22. remaining risks: Section 18参照（historical human deification 3社、新規content-model判断は不要）
23. audit doc: 本ドキュメント
    （`docs/audit/knowledge-batch15-seed-preflight.md`）
24. PR: 別途作成（本ドキュメントのcommit時に作成）
25. CI: PR作成後に確認
26. final classification: `BATCH15_PRODUCTION_IMPORT_READY`

Production DB writes = 0
Batch 15 Production import = NOT_EXECUTED
Batch 16 = NOT_STARTED
