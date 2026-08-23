> **Status: `SHRINE_BASE_BATCH17_SEED_ADDED_DRY_RUN_PASS_KNOWLEDGE_COMPATIBLE_PRODUCTION_IMPORT_NOT_EXECUTED`。**
>
> Batch 17 Knowledge Production Import（`docs/audit/knowledge-batch17-production-import.md`
> がNOT_EXECUTEDのまま記録した対象）の前提として、Batch 17対象3社
> （北海道神宮・建部大社・波上宮）がProduction DBに存在しない
> （read-only queryで確認済み）ことを受け、既存Production Shrine Seed
> 正本（`backend/temples/data/shrines_seed_clean.json`）へ3社のcanonical
> Shrine baseを追加した。**Production DBへは一切接続・書き込みしていない。**
> 検証はすべてscratch/isolated local PostgreSQLで行った。建部大社の座標は
> Mother Ship承認済みの外部Evidence（國學院大學デジタル・ミュージアム／
> 古典文化学事業、2ソースcross-check）を採用した。

# Shrine Base Batch 17 Production Seed Preflight

## Scope

- Batch 17 Knowledge Production Importの前提として、北海道神宮・建部大社・
  波上宮のcanonical Shrine baseを既存Production Shrine Seed契約へ追加する
- 既存100社は一切変更しない
- Production DBへは接続・書き込みしない
- Knowledge Seed・Model・Migration・Importer・Recommendation・Evidence
  Gateはいずれも変更しない
- 本タスクではProduction Importを実行しない

## 作業ブランチ / worktree（Phase 0）

| 項目 | 結果 |
|---|---|
| メインworking tree | 変更なし（`docs/shrine-geographic-expansion-rollout-plan`branch、touchしていない） |
| 既存worktree（他6件） | 変更なし。いずれもtouchしていない |
| `origin/develop`最新化 | `git fetch origin develop`実行、`origin/develop` SHA=`43c516bcf8ee4439f2d6e33a340d21b659e3a58c`を記録 |
| `data/shrine-base-batch17-production-seed`branch/worktree衝突 | なし（事前確認） |
| worktree作成 | `git worktree add ../jinja_app-shrine-base-batch17 -b data/shrine-base-batch17-production-seed origin/develop` |
| develop上の前提ファイル確認 | `batch_17_seed.json`・`knowledge-batch17-seed-preflight.md`・`shrine-expansion-batch1-data-quality-closure.md`いずれも存在確認済み |
| Compass branch/worktreeへの変更 | 0（一切touchしていない） |

## Production 0 rowsの事実

前タスク（`docs/audit/knowledge-batch17-production-import.md`）で
read-only queryにより、Production DB上に北海道神宮・建部大社・波上宮の
いずれも0 rowsであることが既に確認されている。本タスクはこの事実を
前提として引き継ぐ（本タスク内で再確認はしていない。Production DB
接続自体を行っていないため）。

## Shrine Base Seed Contract確認（Phase 1）

`backend/README.md`・`import_shrines_seed.py`・`shrines_seed_clean.json`・
`representative_shrines.yaml`・関連Auditをfresh readし、以下を確定した。

| 確認項目 | 結果 |
|---|---|
| Production Shrine Seed正本 | `backend/temples/data/shrines_seed_clean.json`（`import_shrines_seed`の`--source`デフォルト値、`backend/README.md`「神社seedデータ投入」節で確認） |
| import_shrines_seedのdefault source | `temples/data/shrines_seed_clean.json`（コード`add_arguments`で確認） |
| identity判定方法 | `Shrine.objects.filter(name_jp=name, address=address).order_by("id").first()`——`name_jp`+`address`の完全一致 |
| update/create条件 | 一致行が無ければCREATE。一致行があり値に差分があればUPDATE（`payload`の各fieldを比較、`changed_fields`のみ`update_fields`で保存）。差分が無ければSKIP |
| 必須field | `name_jp`・`address`（いずれかが空文字なら該当行をSKIPし例外は投げない） |
| optional field | `latitude`・`longitude`・`goriyaku`・`kyusei`・`astro_elements`・`visit_style_tags`・`name_romaji`・`sajin`・`description`・`element`（すべて`row.get(...)`、未指定なら空文字/None/空配列にfallback） |
| transaction境界 | 全行を単一`transaction.atomic()`で包む。`--dry-run`時は全行を実際に評価した後`transaction.set_rollback(True)`で明示的にrollbackする（Knowledge Importerの「plan計算のみで書き込みコードパス自体に到達しない」設計とは異なり、こちらは一度書き込みを評価してから確定的にrollbackする設計） |
| dry-run契約 | 上記のとおり、DB上は書き込まれない（rollback）が、`created`/`updated`/`skipped`件数はPRINTされる |
| representative_shrines.yamlの責務 | **Production Shrine Seedではない。** `backend/scripts/generate_shrines_fixture.py`のDEFAULT_SEEDおよびConcierge eval/readinessテスト（`test_concierge_eval_queries_seed80.py`等）専用のtest/eval fixture pool。Production Shrine Seedとしては一切使用されていないことをコード検索で確認した |

既存契約は変更していない。

## 3社Candidate確定（Phase 2）

既存repo内tracked evidenceのみから確定した。新規Web調査（本Phase時点）・
AI座標推測はいずれも行っていない。

| 項目 | 北海道神宮 | 建部大社 | 波上宮 |
|---|---|---|---|
| name_jp | 北海道神宮 | 建部大社 | 波上宮 |
| address | 北海道札幌市中央区宮ヶ丘474 | 滋賀県大津市神領1-16-1 | 沖縄県那覇市若狭1-25-11 |
| address evidence | Discovery Automation Readiness Audit・`representative_shrines.yaml`・Batch17 Knowledge Seed`shrine_ref`の3ソース一致 | Discovery Automation Readiness Audit・Batch17 Knowledge Seed`shrine_ref`の2ソース一致（`representative_shrines.yaml`に該当エントリなし） | Discovery Automation Readiness Audit・`representative_shrines.yaml`・Batch17 Knowledge Seed`shrine_ref`の3ソース一致 |
| latitude（第一次確認時点） | 43.0553（`representative_shrines.yaml`） | **未確定（tracked evidenceなし）** | 26.2144（`representative_shrines.yaml`） |
| longitude（第一次確認時点） | 141.3126（`representative_shrines.yaml`） | **未確定（tracked evidenceなし）** | 127.6672（`representative_shrines.yaml`） |

第一次確認の結果、建部大社の緯度経度がリポジトリ内のいずれのtracked
sourceにも存在しないことが判明し、本タスクを一度HOLDとしてMother Shipへ
差し戻した（新規Web調査・AI推測はいずれも禁止されていたため）。

### Mother Ship Decision による建部大社座標の確定

Mother Shipが新規Web調査を明示的に許可し、以下の外部Evidenceを採用した。

| Source | 緯度（DMS） | 経度（DMS） |
|---|---|---|
| 國學院大學デジタル・ミュージアム | 34°58′24.174″N | 135°54′48.740″E |
| 國學院大學 古典文化学事業（cross-check） | 34°58′24.6″N | 135°54′48.6″E |

両資料は「建部大社／滋賀県大津市神領1-16-1」とidentity一致することが
Mother Shipにより確認されている。

DMS→10進変換を本タスクで再計算し検証した。

```
Source1: 34 + 58/60 + 24.174/3600 = 34.973382
         135 + 54/60 + 48.740/3600 = 135.913539
Source2: 34 + 58/60 + 24.6/3600   = 34.973500
         135 + 54/60 + 48.6/3600  = 135.913500
diff latitude:  0.000118°（約13m相当）
diff longitude: 0.000039°（約4m相当）
```

2ソースの差は建物規模内の測定誤差範囲であり、競合ではなく相互補強と
判断した（AIによる追加推測は行わず、Mother Ship提示の候補小数度
`latitude ≈ 34.9735 / longitude ≈ 135.9135`をそのまま採用）。

### 既存Seed座標精度の確認と最終値

`shrines_seed_clean.json`の既存100社の小数桁数を実測した。

| 小数桁数 | 件数 |
|---|---:|
| 4桁 | 85 |
| 3桁 | 11（JSON上末尾0が省略された4桁値である可能性が高い） |
| 6桁 | 2 |
| 7桁 | 2 |

**4桁が支配的（85%）であり、既存の主たる精度規約と判断した。** 北海道神宮・
波上宮の`representative_shrines.yaml`由来座標も4桁（例: 43.0553）であり
整合する。Mother Ship提示の建部大社候補値（34.9735 / 135.9135）は既に
4桁精度で提示されており、精度変換は不要だった。AIによる追加の丸め判断・
再計算は行わず、提示値をそのまま採用した。

### 最終Candidate値（確定）

| 項目 | 北海道神宮 | 建部大社 | 波上宮 |
|---|---|---|---|
| name_jp | 北海道神宮 | 建部大社 | 波上宮 |
| address | 北海道札幌市中央区宮ヶ丘474 | 滋賀県大津市神領1-16-1 | 沖縄県那覇市若狭1-25-11 |
| latitude | 43.0553 | **34.9735** | 26.2144 |
| longitude | 141.3126 | **135.9135** | 127.6672 |

## Duplicate / Identity Gate（Phase 3）

Production DBへは接続していない（前タスクで0 rows確認済みの事実を
引き継ぐのみ）。

| チェック | 結果 |
|---|---|
| 既存100社Seed内の完全name一致 | 0件（3社とも） |
| 既存100社Seed内の完全name+address一致 | 0件（3社とも） |
| 既存100社Seed内の近似名候補 | 0件（3社とも、部分文字列一致で確認） |
| address衝突 | 0件 |
| coordinate衝突 | 未実施（既存Seedに衝突判定ロジックなし、必要性も確認されなかった） |
| `find_duplicate_candidates`（scratch DB、read-only） | 3社とも自分自身（scratch DB内、本セッション過去タスクで作成済みのid133/134/135）とのみ一致。これは本セッションのscratch DB特有の既存pilotデータへの自己一致であり、Production/既存100社Seedに対する実質的な重複ではない |

identityは3社とも一意に確定した。曖昧な点はない。

## Seed方針確定（Phase 4）

Production正本が`shrines_seed_clean.json`であることをfresh確認した上で
編集した。

- 既存100社の値は一切変更していない（`git diff origin/develop -- <path>`
  で確認、後述）
- 追加3社は既存schema（`name_jp`/`address`/`latitude`/`longitude`/
  `goriyaku`/`kyusei`/`astro_elements`/`location`）にそのまま従う
- `goriyaku`/`kyusei`/`astro_elements`/`visit_style_tags`は、Phase 2で
  確認対象とした`name_jp`/`address`/`latitude`/`longitude`の範囲外であり
  tracked evidenceが無いため、既存importerが未指定行に対して行う
  デフォルト処理と同じ値（`goriyaku=""`、`kyusei=null`、
  `astro_elements=[]`）をそのまま採用した。`representative_shrines.yaml`
  の`goriyaku`/`description`/`astro_tags`は、同ファイルがtest/eval
  fixtureでありProduction Shrine Seedの正本ではないと確認済みのため
  （Phase 1参照）、これらのfield値としては転用していない
- `visit_style_tags`は既存100社の一部エントリでもキー自体が省略されて
  いる前例（例: 伏見稲荷大社）があり、同様に省略した
- 既存ordering（挿入順）を維持し、3社は既存100社の末尾へ追加した
  （既存100社に挿入順以外の明示的なsort規約は確認されなかった）
- Knowledge Seed・Model・Migration・Importer・Recommendation・Evidence
  Gate・`representative_shrines.yaml`のいずれも変更していない
- Production DBへは接続・書き込みしていない

## Structural Validation（Phase 5）

追加後のSeedを`python3`で直接検証した。

| 確認項目 | 結果 |
|---|---|
| JSON parse | PASS |
| 総件数 | 103（既存100 + Batch17 3社） |
| name_jp non-empty | 3社とも非空 |
| address non-empty | 3社とも非空 |
| latitude valid | 3社ともfloat型・非null |
| longitude valid | 3社ともfloat型・非null |
| exact duplicate | 0件（name完全一致・name+address完全一致とも） |
| 既存100社 drift | **0**（`git show origin/develop:<path>`とdata[:100]を比較し完全一致を確認） |
| Batch17 3社が各1件 | 確認済み（北海道神宮1・建部大社1・波上宮1） |

期待値と完全一致。`git diff --stat`は39行追加のみ（既存100社への
変更行は0）。

## import_shrines_seed Dry-run（Phase 6）

Production DBではなく、専用の使い捨てisolated local PostgreSQL
（`jinja_batch17_shrinebase_test`、このタスク専用に新規作成・検証後
`dropdb`で削除済み）を使用した。**このセッションの永続scratch DB
（`jinja_db`）には、以前のタスクで作成済みの北海道神宮/建部大社/波上宮
（id 133/134/135）が既に存在しており、そのままdry-runするとCREATEでは
なくUPDATE/SKIPになってしまうため、Production相当のクリーンな状態を
再現する目的で専用DBを新規作成した。**

```
$ python manage.py import_shrines_seed --dry-run
（103件中、北海道神宮・建部大社・波上宮を含む全件が）
CREATE 北海道神宮
CREATE 建部大社
CREATE 波上宮
（他100社もCREATE。isolated DBが完全に空のため）
done created=103 updated=0 skipped=0 total_seed=103
```

**結果: PASS。** SKIP・identity ambiguity・validation errorはいずれも
0件。Production credentialは使用していない。Production DBへは接続して
いない。

## Knowledge Compatibility Gate（Phase 7）

Shrine base投入後の状態を再現するため、同一isolated DBに対して実際に
`import_shrines_seed`（flagなし）を適用し、103社を作成した（このDB自体
はProductionではない使い捨てのisolated DB）。続けて`--dry-run`で冪等性
（0 create/0 update/103 skip）を確認した。

その上で、Batch 17 Knowledge Seed（`batch_17_seed.json`、無変更）に
対して以下を実施した。

```python
resolve_shrine("北海道神宮", "北海道札幌市中央区宮ヶ丘474") -> status=OK, id=101
resolve_shrine("建部大社",   "滋賀県大津市神領1-16-1")       -> status=OK, id=102
resolve_shrine("波上宮",     "沖縄県那覇市若狭1-25-11")       -> status=OK, id=103
```

3社とも一意にresolve（`AMBIGUOUS`/`NOT_FOUND`は0件）。

```
$ python manage.py import_shrine_knowledge batch_17_seed.json --validate-only
validate-only: OK, no errors

$ python manage.py import_shrine_knowledge batch_17_seed.json --dry-run
plan summary: {'source_CREATE': 5, 'deity_CREATE': 12, 'history_CREATE': 13}
dry-run: OK, no DB writes performed
```

**結果: PASS。** Deity 12・History 13・Total 25を維持することを確認した。
Knowledge Seed自体は一切変更していない。使い捨てisolated DBは検証完了後
`dropdb`で削除した。

## Tests（Phase 8）

既存`shrines_seed_clean.json`の内容そのものを検証する専用testは
develop上に存在しなかった（`import_shrines_seed`のorchestration自体を
扱う`test_bootstrap_production_data_command.py`は合成fixtureを使用して
おり、実Seed内容は検証していない）。既存パターンを壊さない範囲で、
必要最小限の新規test（6件）を追加した。

新規: `backend/temples/tests/test_shrine_base_batch17_seed.py`

- `test_shrine_base_seed_has_103_entries_existing_100_plus_batch17_3`
- `test_shrine_base_seed_batch17_shrines_present_exactly_once`
- `test_shrine_base_seed_batch17_identity_matches_knowledge_seed`
  （Batch17 Knowledge Seedの`shrine_ref`とShrine base Seedのaddressが
  一致することを固定化——不一致ならKnowledge Importが`NOT_FOUND`になる）
- `test_shrine_base_seed_batch17_coordinates_and_address`
- `test_shrine_base_seed_no_duplicate_name_or_address`
- `test_shrine_base_seed_existing_100_entries_unchanged`

既存test（`test_bootstrap_production_data_command.py`・
`test_batch17_knowledge_seed.py`・`test_batch16_knowledge_seed.py`）と
合わせて実行し、**合計32件すべてPASS（回帰なし）**。

```
$ python -m pytest temples/tests/test_shrine_base_batch17_seed.py \
    temples/tests/test_bootstrap_production_data_command.py \
    temples/tests/test_batch17_knowledge_seed.py \
    temples/tests/test_batch16_knowledge_seed.py -p no:dotenv -q
32 passed in 4.50s
```

## Production変更0

| 項目 | 結果 |
|---|---|
| Production DB接続 | 0 |
| Production DB write | 0 |
| Model / Migration変更 | 0 |
| Importer変更 | 0（`import_shrines_seed`・`import_shrine_knowledge`いずれも無変更） |
| Recommendation変更 | 0 |
| Evidence Gate変更 | 0 |
| Knowledge Seed変更 | 0（`batch_17_seed.json`は一切touchしていない） |
| `representative_shrines.yaml`変更 | 0 |
| Production credential露出 | 0 |

**Production Importは実行していない（NOT_EXECUTED）。**

## Remaining STOP/HOLD

**0件。** 建部大社座標の当初HOLDはMother Ship Decisionにより解消済み
（本ドキュメント「Mother Ship Decisionによる建部大社座標の確定」節）。

参考記録（新規STOP事項ではない）:

- 建部大社の座標はMother Ship承認の外部Evidence（國學院大學2ソース）に
  基づく。今後、より高精度なgeocoding手段（PlaceRef経由等）が利用可能
  になった場合、既存の位置情報取得経路での再検証を妨げない
- Batch 17 Knowledge Production Import自体（`knowledge-batch17-production-import.md`
  が記録したNOT_EXECUTED状態）は、本タスクの範囲外のまま継続する。
  本タスクはあくまでその前提となるShrine base追加のみを扱った

## 次工程

- Shrine base（3社）・Batch 17 Knowledge Seed（25 Fact）とも
  Production投入前の技術検証はすべてPASS済み
- 実際のProduction投入順序は、既存契約上（`import_shrine_knowledge`が
  Shrine identityの事前存在を要求するため）**Shrine base Seed投入 →
  Knowledge Seed投入**の順で行う必要がある
- 実Production Import（Shrine base・Knowledge Seedとも）は、
  `docs/audit/knowledge-batch17-production-import.md`が既に記録した
  とおり、本セッション（cloud sandbox）からは実行できない
  （Production credentialが存在しない）。ユーザー自身のローカルMacでの
  実行、または別途安全な実行経路の構築のいずれかがMother Ship判断として
  必要
- Production Import実行可否そのものは本タスクでは判断しない

## Repository Diff Gate（Phase 10）

```
$ git diff --check
（無出力 = 問題なし）
$ git status --short
 M backend/temples/data/shrines_seed_clean.json
?? backend/temples/tests/test_shrine_base_batch17_seed.py
?? docs/audit/shrine-base-batch17-production-seed-preflight.md
$ git diff --stat
 backend/temples/data/shrines_seed_clean.json | 39 +++++++++++++++++++++++++++
 1 file changed, 39 insertions(+)
$ git diff origin/develop -- backend/temples/data/shrines_seed_clean.json
（39行の追加のみ、既存100社への変更行は0であることを確認）
```

変更ファイルは許可された3件（`shrines_seed_clean.json`・新規test・
新規Audit）のみ。Model・Migration・Importer・Evidence Gate・
Recommendation・unrelated docs/codeへの変更は0件。main working tree・
他worktree（Compass含む）はいずれも未変更。
