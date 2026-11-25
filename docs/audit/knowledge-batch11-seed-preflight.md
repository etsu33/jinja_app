> **Status: `BATCH11_PRODUCTION_IMPORT_READY`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch11-target-selection.md`
> （`BATCH11_TARGET_SELECTION_READY_WITH_LIMITATIONS`）で選定された推奨5社
> について、Knowledge seedを構築し、Production投入直前の技術Gateまで検証
> した記録である。
>
> **本ドキュメント作成のセッションでは、Production Knowledge writeは
> 実行していない。** 実行したのは、Production read-only接続
> （`readonly_query.sh`）、公式サイトのfresh確認（`WebFetch`）、ローカル
> DBへの実際のseed投入・検証、fresh Production dumpから復元したisolated
> DBへの実際のseed投入・検証、そしてProduction DBに対する
> `--validate-only`・`--dry-run`（いずれもDB書き込みを一切行わない
> モード）のみである。Production DB writeは0件。
>
> **追記（Batch 11 Deity Scope Finalization、後続セッション）**: 唯一の
> Mother Ship判断項目であった小網神社「福禄寿」の扱いについて、Mother
> Shipが「ShrineDeityへ含めない」と決定した。`batch_11_seed.json`から
> 福禄寿のFactを除外し（Deity 17→16）、ローカル・Production-equivalent・
> Production read-only（`--validate-only`/`--dry-run`）のフルサイクルを
> 再実施して結果が期待どおりであることを確認済み。詳細はSection
> 「Batch 11 Deity Scope Finalization」を参照。この追記により、本
> ドキュメントのStatusは`BATCH11_PRODUCTION_IMPORT_READY_WITH_LIMITATIONS`
> から`BATCH11_PRODUCTION_IMPORT_READY`へ更新した。

# Knowledge Batch 11 Seed Preflight — Mother Ship Report

## Executive Summary

Batch 11投入候補5社（小網神社・根津神社・赤坂氷川神社・大宮八幡宮・
寳登山神社）のKnowledge seed（`backend/temples/data/knowledge_seeds/
batch_11_seed.json`）を新規構築した。全5社はMother Ship承認済みの
`docs/audit/knowledge-batch11-target-selection.md` Recommended 5と
一致し、fresh Production read-only接続で識別安全性のdriftが0件である
ことを再確認した。候補の差替えは発生していない（Phase 7の差替えルールを
適用する必要はなかった）。

Source 5件はすべて神社公式サイトを`WebFetch`で直接確認し、Production
既存76件との意味的競合は0件（`NO_CONFLICT`）。Deity 17件・History 7件を
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

develop SHA（作業開始時点）: `fa9fbea115e83ffc5b7373fcfa21e21d052dbe15`
（PR #2361反映済み、`origin/develop`と同期済み、working tree clean）。

freshに再読した既存contract:

- `docs/audit/knowledge-batch11-target-selection.md`（Recommended 5の出典）
- `docs/knowledge/shrine-knowledge-contract.md`（deity/shrine_history/
  Source契約、Evidence Gate、verification_status/confidence enum）
- `backend/temples/data/knowledge_seeds/batch_10_seed.json`（seed構造の
  テンプレート）
- `backend/temples/services/knowledge_seed.py`（`resolve_shrine`・
  `resolve_source_identity`・`parse_seed`の実装）
- `backend/temples/management/commands/import_shrine_knowledge.py`
  （`--validate-only`/`--dry-run`/適用の3モード実装）

いずれも構造変更なしで再利用可能であることを確認した。

---

## 2. Identity recheck

Production read-only接続で、5社をfreshに再確認した
（snapshot時刻`2026-08-10 12:25:37+00`）。

| shrine | Production id | `place_ref_id IS NULL` | 同名重複行 | deity_count | history_count |
|---|---:|---|---|---:|---:|
| 小網神社 | 62 | true | 1 | 0 | 0 |
| 根津神社 | 48 | true | 1 | 0 | 0 |
| 赤坂氷川神社 | 60 | true | 1 | 0 | 0 |
| 大宮八幡宮 | 51 | true | 1 | 0 | 0 |
| 寳登山神社 | 97 | true | 1 | 0 | 0 |

Production集計ベースライン（同時刻）: Source 76・Deity 149・History 106・
Deity–Source relation 162・History–Source relation 111・Knowledge Shrine
56 —`knowledge-batch11-target-selection.md`の記録値と完全一致
（drift 0件）。

**全5社が`IDENTITY_SAFE`。** numeric PKはseedへ記録しない。候補差替えは
発生していない。

---

## 3. Official Sources and Evidence Gate

5社すべての公式サイトを`WebFetch`でfreshに直接確認した（Target
Selection時のsnippetを盲信せず、本タスクで独立して再確認）。

| shrine | Source URL | 確認内容 |
|---|---|---|
| 小網神社 | koamijinja.or.jp/history/ | 御祭神三柱（倉稲魂神・市杵島比賣神・福禄寿）・文正元年（1466）の創建伝承 |
| 根津神社 | nedujinja.or.jp/about/ | 主祭神三柱・相殿二柱・日本武尊創祀伝承・宝永三年（1706）の遷宮 |
| 赤坂氷川神社 | akasakahikawa.or.jp/about/ | 御祭神三柱・天暦五年（951）の創建伝承・享保十四〜十五年の社殿造営 |
| 大宮八幡宮 | ohmiya-hachimangu.or.jp/hachimangu/history | 御祭神三柱・康平六年（1063）の創建由緒 |
| 寳登山神社 | hodosan-jinja.or.jp/gaiyou/ | 御祭神三柱・日本武尊東征伝承に基づく創建（西暦110年頃） |

**Source semantic conflict check（Production既存76件との突合）: 0件一致。
全5候補Sourceが`NO_CONFLICT`。**

**Evidence Gateスコープ判断**: 小網神社の御祭神には「福禄寿」が含まれる。
これは七福神信仰に由来する神格であり、古典的な神話系譜を持つ他の祭神とは
性質が異なる。ただし、大國魂神社の「御霊大神」（Batch10で除外）や
愛宕神社の「将軍地蔵尊・普賢大菩薩」（Batch11代替候補、明示的な仏教
称号のため除外）とは異なり、以下の理由でFact化した:

- 個別の固有名詞を持つ（「英霊」のような抽象的集合概念ではない）
- 公式サイトが倉稲魂神・市杵島比賣神と並列に「御祭神」として明記して
  いる（仏教称号を伴わない）
- Sourceが直接存在し、source-lessではない

`note`フィールドにこの性質の違いを明記し、無自覚な「kami化」ではなく
透明性のある記録としてFact化した。この判断はMother Shipへ明示する
（Section「Remaining risks」参照）。

役割（`role`）は、公式が明示的な序列を示す場合のみ`primary`/`secondary`
を用いた（根津神社の主祭神3柱/相殿2柱、大宮八幡宮の応神天皇/仲哀天皇・
神功皇后）。赤坂氷川神社は序列記載がないため三柱とも`unknown`とした。

---

## 4. Canonical seed integrity

`backend/temples/data/knowledge_seeds/batch_11_seed.json`
（`schema_version: "1.0"`）。

`parse_seed()`（実装をそのまま使用したstructural検証）:

| 指標 | 値 |
|---|---:|
| errors | 0 |
| Source count | 5 |
| Shrine count | 5 |
| Deity count | 17 |
| History count | 7 |
| Deity–Source relation | 17 |
| History–Source relation | 7 |
| source-less Deity | 0 |
| source-less History | 0 |
| within-shrine重複 | 0 |
| invalid enum | 0 |
| unresolved source_key参照 | 0 |

全Fact（Deity 17・History 7）が`verification_status: source_confirmed`
かつ`confidence: high`かつ`verified_at`設定済みであることを確認した
（追加のpytest回帰テストで固定化）。

SHA-256（`batch_11_seed.json`）:
`236d272aa526d6763ba097d81610530f434feb7b33788c3529b832fc64089371`

---

## 5. Regression tests

新規: `backend/temples/tests/test_batch11_knowledge_seed.py`
（5件、Batch10の`test_batch10_knowledge_seed.py`と同型）。

既存の汎用テスト（`test_knowledge_seed_import.py`、24件）・Batch9専用
テスト（2件）・Batch10専用テスト（5件）を含め、合計37件すべてPASS
（回帰なし）。source-less拒否・重複検知・semantic Source reuse・
invalid enum拒否・ambiguous shrine拒否は既存の汎用テストで既に
カバーされている。

---

## 6. Local validation, import, and regression

ローカル`jinja_db`（対象5社はProduction同一idで存在、import前はいずれも
deity=0/history=0を確認済み）に対して実際に実行:

| step | 結果 |
|---|---|
| `--validate-only` | `validate-only: OK, no errors` |
| `--dry-run`（1回目） | `{'source_CREATE': 5, 'deity_CREATE': 17, 'history_CREATE': 7}` |
| 適用（import） | `sources created=5, deities created=17, histories created=7` |
| 件数検証 | Source 79→84（+5）・Deity 149→166（+17）・History 106→113（+7）、対象5社の内訳は3/5/3/3/3件（seedと完全一致）、source-less 0件 |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 5, 'deity_SKIP_EXISTS': 17, 'history_SKIP_EXISTS': 7}`、CREATE 0件 |

---

## 7. Fresh Production-equivalent test

Fresh Production dump（`postgresql@17`バージョン一致クライアント）を
取得し、`kami_musubi_migration_safety_b11s_<timestamp>`（disposable
local DB）へ復元した。復元は`exit 0`で完了。

復元直後のisolated DB確認: Production同時刻の値（Source76・Deity149・
History106・relation162/111）と完全一致。対象5社は全件Knowledge none。

isolated DBに対して、ローカルと同一の5ステップを実施:

| step | 結果 |
|---|---|
| `--validate-only` | OK, no errors |
| `--dry-run`（1回目） | `{'source_CREATE': 5, 'deity_CREATE': 17, 'history_CREATE': 7}` |
| 適用 | `sources created=5, deities created=17, histories created=7` |
| 件数検証 | Source 76→81・Deity 149→166・History 106→113・Deity–Source rel 162→179・History–Source rel 111→118（いずれもseed件数と完全一致） |
| 対象5社のdeity内訳 | 小網神社3・根津神社5・赤坂氷川神社3・大宮八幡宮3・寳登山神社3（seedと完全一致、混入なし） |
| source-less（対象5社） | Deity 0・History 0 |
| 無関係データ回帰チェック | 大國魂神社7/2・宇佐神宮3/1・箱根神社3/1・芝大神宮2/2（いずれも既存seedの値のまま、変化なし） |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 5, 'deity_SKIP_EXISTS': 17, 'history_SKIP_EXISTS': 7}`、CREATE 0件 |

isolated DBは検証完了後に`dropdb`で削除済み。dumpファイルはrepo外に
残置（コミットしない）。

---

## 8. Coverage projection

isolated DB（Production-equivalent）の実測値から算出（推測値は使用
していない）。

| 区分 | Batch11投入前（実測） | Batch11投入後（実測） |
|---|---:|---:|
| complete | 54 | 59 |
| partial | 2 | 2（不変） |
| none | 49 | 44 |
| Knowledge Shrine合計 | 56 | 61 |
| 全Shrine数 | 105 | 105（不変） |

partial 2件（阿佐ヶ谷神明宮・香取神宮）は本Batchの対象外のため不変。
対象5社はいずれも投入前`none`→投入後`complete`へ移行する。

---

## 9. Production read-only preflight

Production DBに対して以下を実行した（いずれもコマンド自身の設計上、
DB書き込みを一切行わないモード）。

**`--validate-only`**: `validate-only: OK, no errors`

**`--dry-run`**:
```
plan summary: {'source_CREATE': 5, 'deity_CREATE': 17, 'history_CREATE': 7}
dry-run: OK, no DB writes performed
```

全項目、isolated DBの1回目`--dry-run`結果と完全一致。`SKIP_EXISTS`・
`REUSE_EXISTING`・`SOURCE_REUSE_CONFLICT`・`SOURCE_REUSE_AMBIGUOUS`・
`IMPORT_IDENTITY_AMBIGUOUS`・`NOT_FOUND`はいずれも0件。

実行後、`readonly_query.sh`で再度Production状態を確認し、対象5社の
deity/history、および集計値（Source 76・Deity 149・History 106・
relation 162/111・Knowledge Shrine 56）が実行前と完全に不変であること
を確認した。

---

## 10. Runtime expected payload

seedから算出（Production import実行後に期待される値、実行はしていない）。

| shrine | Deity | History | Unique Source |
|---|---:|---:|---:|
| 小網神社 | 3 | 1 | 1 |
| 根津神社 | 5 | 2 | 1 |
| 赤坂氷川神社 | 3 | 2 | 1 |
| 大宮八幡宮 | 3 | 1 | 1 |
| 寳登山神社 | 3 | 1 | 1 |
| **合計** | **17** | **7** | **5** |

Fact–Source relation count: 24（Deity 17 + History 7）。

---

## 11. Remaining risks and Mother Ship decision

- **小網神社の「福禄寿」**: 七福神信仰由来の神格で、古典的な神話系譜を
  持つ祭神とは性質が異なる。公式サイトが明示的に「御祭神」として掲載
  しているためFact化したが、この判断（除外ではなく、noteによる透明な
  記録での採用）についてMother Shipの確認を推奨する。
- Source page instability（公式サイトの将来的な変更リスク）は他Batch
  と同様の一般的リスク。
- `SKIP_EXISTS`のsemantic-diff limitation（既存Factと同名でも内容差分を
  検知しない）は既知の設計上の制約であり、本Batchに固有の問題ではない。
- 地域偏り: Recommended 5は東京都4・埼玉県1。Batch11 Top10候補自体が
  東京都に偏っていたことに起因する構造的な結果であり、記録のみ
  （tie-breakerとして地域分散よりSource品質を優先した既定方針どおり）。
- 靖國神社・千葉神社・愛宕神社等のcontent設計判断は引き続き未解決の
  まま、本Batchの対象外。
- partial 2社（阿佐ヶ谷神明宮・香取神宮）のHistory repairは別タスクの
  まま。

## 12. Batch 11 Deity Scope Finalization（追記）

Mother Ship方針: 小網神社の「福禄寿」をShrineDeityへ含めない
（七福神信仰由来の神格であり、通常の「神社の御祭神」と同一contractへ
無条件に入れると意味モデルが揺れるため。将来のKnowledge Model設計課題
として分離する。分類: `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`）。

### 変更内容

- `batch_11_seed.json`から小網神社の福禄寿`ShrineDeity` Factのみを除外
- 福禄寿が参照していたSource（`batch11-koami-official`）は倉稲魂神・
  市杵島比賣神・史実Factから引き続き参照されており、orphan化していない
- Sourceの`note`を、公式ページには福禄寿の記載があるがFact化対象外と
  した旨がわかるよう更新

### Seed hash

| | 値 |
|---|---|
| 旧SHA-256（福禄寿含む、履歴として記録） | `236d272aa526d6763ba097d81610530f434feb7b33788c3529b832fc64089371` |
| 新SHA-256（福禄寿除外後） | `4cf202506823da322fad710843c2a7aa600e35d7606890ce8f3d9a1c76446b2c` |

### Count recalculation（fresh実測）

| 指標 | 旧値 | 新値 |
|---|---:|---:|
| Shrine | 5 | 5（不変） |
| Source | 5 | 5（不変） |
| Deity | 17 | 16 |
| History | 7 | 7（不変） |
| Deity–Source relation | 17 | 16 |
| History–Source relation | 7 | 7（不変） |
| source-less | 0 | 0 |
| orphan Source | — | 0 |

小網神社の内訳: 修正前は3 Deity（倉稲魂神・市杵島比賣神・福禄寿）、
修正後は2 Deity（倉稲魂神・市杵島比賣神）のみ。他4社のDeity/Historyは
無変更。

### Regression tests

`test_batch11_knowledge_seed.py`を更新（Deity件数17→16、
`--dry-run`期待出力の`deity_SKIP_EXISTS`件数を修正）。新規テスト
`test_batch11_seed_excludes_fukurokuju_from_koami_deities`を追加し、
小網神社のDeityが`["倉稲魂神", "市杵島比賣神"]`のみであること、
Sourceがorphan化していないことを固定化。既存の汎用テスト（24件）・
Batch9/10テスト（7件）を含め、合計38件すべてPASS（回帰なし）。

### Local validation（修正版seed、クリーンな状態からの再実施）

ローカル`jinja_db`の対象5社Knowledge（前セッションで投入済みだった
福禄寿含む旧データ）を削除し、クリーンな状態（対象5社deity=0/
history=0、Source79・Deity149・History106）から再実施した。

| step | 結果 |
|---|---|
| `--validate-only` | OK, no errors |
| `--dry-run`（1回目） | `{'source_CREATE': 5, 'deity_CREATE': 16, 'history_CREATE': 7}` |
| 適用 | `sources created=5, deities created=16, histories created=7` |
| 件数検証 | Source 79→84・Deity 149→165・History 106→113、小網神社=2 Deity（福禄寿なし）、`display_name='福禄寿'`のDeityはDB全体で0件 |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 5, 'deity_SKIP_EXISTS': 16, 'history_SKIP_EXISTS': 7}`、CREATE 0件 |

### Production-equivalent recheck

fresh Production dump（`postgresql@17`バージョン一致クライアント）を
新規取得し、isolated DBへ復元。復元直後の値はProduction同時刻の値
（Source76・Deity149・History106・relation162/111）と完全一致。

| step | 結果 |
|---|---|
| `--validate-only` | OK, no errors |
| `--dry-run`（1回目） | `{'source_CREATE': 5, 'deity_CREATE': 16, 'history_CREATE': 7}` |
| 適用 | `sources created=5, deities created=16, histories created=7` |
| 件数検証 | Source 76→81・Deity 149→165・History 106→113・Deity–Source rel 162→178・History–Source rel 111→118（seedと完全一致） |
| Coverage | complete 54→59・partial 2（不変）・none 49→44 |
| source-less（対象5社） | Deity 0・History 0 |
| 福禄寿混入チェック | DB全体で`display_name='福禄寿'`のDeity 0件 |
| 無関係データ回帰チェック | 大國魂神社7/2・宇佐神宮3/1・芝大神宮2/2（いずれも既存値のまま不変） |
| `--dry-run`（2回目、冪等性） | `{'source_REUSE_EXISTING': 5, 'deity_SKIP_EXISTS': 16, 'history_SKIP_EXISTS': 7}`、CREATE 0件 |

isolated DBは検証完了後に`dropdb`で削除済み。

### Production read-only recheck

Production DBに対して`--validate-only`・`--dry-run`を再実行した
（DB書き込みを一切行わないモード）。

```
validate-only: OK, no errors
```

```
plan summary: {'source_CREATE': 5, 'deity_CREATE': 16, 'history_CREATE': 7}
dry-run: OK, no DB writes performed
```

Production-equivalentの結果と完全一致。小網神社は`[deity] CREATE
小網神社: 倉稲魂神`・`[deity] CREATE 小網神社: 市杵島比賣神`の2件のみで、
福禄寿のCREATE行は出力されていない。unexpected SKIP/UPDATE/conflictは
0件。

実行後、`readonly_query.sh`でProduction状態（Source 76・Deity 149・
History 106・relation 162/111・Knowledge Shrine 56）が実行前と完全に
不変であることを確認した。

### Remaining design issue（将来課題）

`ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`: 七福神・神仏習合等、古典的な
神話系譜を持たない「祀られている対象」をKnowledge Modelでどう扱うかは
未確定のまま。今回は保守的に除外したが、将来的に別のFact分類・別Model
（`ShrineDeity`とは別の「合祀・併祀対象」概念）を設計する余地がある。
本Batchでは新設せず、既存`ShrineDeity`契約を変更しない方針を維持した。

### Final Classification

**`BATCH11_PRODUCTION_IMPORT_READY`**

READYと判断する根拠:

- 5社全件が`IDENTITY_SAFE`・`NO_CONFLICT`・Evidence Gate要件を満たす
- ローカル・Production-equivalent（fresh dump復元）の両方で
  `--validate-only`→`--dry-run`→適用→件数検証→再`--dry-run`の
  フルサイクルが（修正版seedで再実施の上）期待どおりの結果
- Production DBに対する`--validate-only`・`--dry-run`が
  Production-equivalentの結果と完全一致し、unexpected SKIP/UPDATE/
  conflictが0件
- Production状態がこれらの読み取り専用操作の前後で完全に不変であることを
  実測で確認
- 候補の差替えは発生していない
- 唯一のMother Ship判断項目（福禄寿の扱い）が解決済み

残存する非blocking事項（Productionへの実書き込み判断とは独立）:

- `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`（上記、将来のModel設計課題）
- Production importそのもの（Fact実書き込み・Runtime QA）は本
  ドキュメントでは未実施。Mother Shipの明示的な承認後、別セッション
  （Human Execution Boundary Gate相当）で実施する必要がある

Production DB writes = 0
Batch 11 Production import = NOT_EXECUTED
Batch 12 = NOT_STARTED
