> **Status: `TEMPLES_0091_REMEDIATION_READY`。**
>
> `temples 0091`（`0091_fill_missing_local_shrine_reason_facts`）のProduction
> 実行失敗（`docs/audit/production-migration-local-execution-runbook.md`の
> 「Execution Record — Stage 3」、`TEMPLES_0091_EXECUTION_STOP`）を受けて、
> root cause再現・duplicate shrine identity確定・安全な修正設計・
> regression test・Production相当restore DBでの実測を行った記録である。
>
> **本ドキュメント作成のセッションではProduction migrationを一切実行して
> いない。** `temples 0091`のProduction再実行・`temples 0092`/`0093`の実行は
> 一切行っていない。Production DBへのwriteは0件。Production retryの
> 可否はMother Ship判断待ち。

# temples 0091 Production Remediation

## 1. develop SHA

作業開始時点: `6e5fac58`（PR #2336 反映済み、`origin/develop`と同期済み、
working tree clean）。

---

## 2. Root Cause Reproduction

### 2.1 手法

Production実dump（`temples 0090`適用済み・`0091`未適用の状態で、Stage 3
実行直前に取得したfresh backup）を、ローカルの隔離されたPostgreSQL 18 +
PostGIS 3.6インスタンスへ復元した（`createdb`で新規作成した専用DB、
Productionへは一切接続していない）。

復元後に確認したbaseline（Stage 3 Execution Recordの事前実測と完全一致）:

| 項目 | 値 |
|---|---|
| `temples`最新migration | `0090_add_rest_healing_tag_to_silent_shrines` |
| `users`最新migration | `0006_userprofile_birth_profile_fields` |
| `shrine`件数 | 105 |
| `goriyaku_relation`件数 | 280 |
| `temples_shrine.location`列の実際の型 | `text` |
| 対象2神社の重複 | 長太稲荷神社: id=21, id=103／給田六所神社: id=22, id=101 |

### 2.2 実行結果

修正前の`0091`をこの復元DBに対して実行したところ、Production記録と
完全に同一のtraceback・同一の失敗行で`GEOSException`が再現した。

```
Applying temples.0091_fill_missing_local_shrine_reason_facts...ERROR django.contrib.gis: GEOS_ERROR:
...
File ".../temples/migrations/0091_fill_missing_local_shrine_reason_facts.py", line 24, in fill_missing_local_shrine_reason_facts
    shrine = Shrine.objects.filter(name_jp=item["name"]).first()
...
File ".../django/contrib/gis/db/backends/postgis/operations.py", line 424, in converter
    return None if value is None else GEOSGeometryBase(read(value), geom_class)
...
django.contrib.gis.geos.error.GEOSException: Error encountered checking Geometry returned from GEOS C function "GEOSWKBReader_readHEX_r".
```

`exit=1`、`django_migrations`に`0091`のレコードなし（atomic rollback）、
`shrine`/`goriyaku_relation`件数・対象4神社の`history_theme`/`goriyaku`/
`updated_at`いずれも実行前と完全一致——Production Stage 3の記録と
すべて一致した。

### 2.3 型不整合の直接確認

`MigrationLoader.project_state(("temples", "0090_..."))`から取得した
historical model stateで`Shrine._meta.get_field("location")`を確認したところ、
`django.contrib.gis.db.models.fields.PointField`（PostGIS geometry field）
であることを確認した。

一方、`Shrine.objects.filter(...)`が生成する実際のSELECT文は`location`列を
含む全カラムを取得する（`.only()`/`.defer()`未使用）:

```sql
SELECT "temples_shrine"."id", ..., "temples_shrine"."location", ...
FROM "temples_shrine" WHERE "temples_shrine"."name_jp" = 長太稲荷神社
ORDER BY "temples_shrine"."updated_at" DESC
```

Production実DBの`temples_shrine.location`列は実際には`text`型
（`migrations_nogis`由来のレガシー列。`\d temples_shrine`で実測確認）。
ORMが`location`の生値（text）をGEOS geometry objectへ変換しようとして
`GEOSException`が発生する。

### 2.4 分類

**`PRODUCTION_SCHEMA_MODEL_MISMATCH_CONFIRMED`**

---

## 3. 0091 Intent Audit

### 3.1 目的

`docs/audit/reason-facts-coverage-after-classification-policy.md`
（PR #1859より前の監査）が特定した、Recommendation Reason v4のevidenceが
不足している実運用神社2社（長太稲荷神社・給田六所神社）に対し、
`history_theme`・`goriyaku`・`goriyaku_tags`を補完するdata-only migration
（PR #1859、`c5f2b3d5`、2026-07-04）。

### 3.2 対象・更新内容

| 神社 | history_theme | goriyaku | 追加tag候補 |
|---|---|---|---|
| 長太稲荷神社 | 守り | 地域に根ざした稲荷社として、商売繁盛や五穀豊穣、日々の暮らしの安定を願う神社。 | 商売繁盛・五穀豊穣・地域安泰 |
| 給田六所神社 | 守り | 地域の氏神として、暮らしや家内安全、日々の無事を見守る神社。 | 地域安泰・家内安全 |

### 3.3 missing tag時の挙動

`GoriyakuTag.objects.filter(name__in=item["tags"])`で存在するtagのみを
取得し、`if tags: shrine.goriyaku_tags.add(*tags)`——**1件も存在しなくても
migration自体はエラーにならず、`history_theme`/`goriyaku`は無条件に
更新される。** 一部のみ存在する場合も、存在する分だけ付与される
（all-or-nothingではない）。Production実測では`地域安泰`tagが存在しない
ことを確認済み（Stage 3事前調査）。

### 3.4 `.first()`採用理由

migration作成時点（2026-07-04）では`name_jp`が実質的に一意という前提
だったと推測される（明示的なunique制約はなく、当時この2神社に重複が
存在したかは不明だが、コード上は単純な「存在すれば1件取得」という
意図のみが読み取れる）。**identity選択のための意図的なordering指定では
ない**——`Shrine.Meta.ordering = ["-updated_at"]`という既存のmodel-levelの
デフォルト順序に暗黙に依存しているだけであり、これは後述のとおり
偶然にも誤ったレコードを選択してしまう。

### 3.5 reverse function

`history_theme`/`goriyaku`を空文字へ戻し、対象tagを除去する対称的な
実装。ただし修正前は`Shrine.objects.filter(name_jp__in=names)`（`.first()`
ではなく全件ループ）で実装されており、forward側が1件のみ更新するのに
対しreverse側は**名前が一致する全レコード（重複含む）を対象にしてしまう
非対称なバグ**があった（4.4節参照）。

### 3.6 dependency

`temples.0090_add_rest_healing_tag_to_silent_shrines`のみ。cross-app
dependencyなし。

---

## 4. Duplicate Shrine Identity Audit

### 4.1 対象データの実測比較

Production復元DBで対象4行を全カラム比較した。

| id | name_jp | created_at | location格納形式 | place_ref_id | astro_elements | visit_style_tags |
|---|---|---|---|---|---|---|
| 21 | 長太稲荷神社 | 2026-06-11 14:49:02 | WKB (real geometry write) | (空) | `["火"]` | `["urban"]` |
| 22 | 給田六所神社 | 2026-06-11 14:49:02 | WKB (real geometry write) | (空) | `["土"]` | `["urban"]` |
| 101 | 給田六所神社 | 2026-06-11 16:18:01 | JSON文字列（text列への直接書き込み） | `ChIJl-MEepfxGGAR1Eo44p__GaE` | `[]` | `[]` |
| 103 | 長太稲荷神社 | 2026-06-11 17:00:18 | JSON文字列（text列への直接書き込み） | `ChIJX19mq8nxGGARsA2kP4gX90M` | `[]` | `[]` |

id=21/22は`backend/temples/seed_data/shrines_initial.json`の**21番目・22番目**
のエントリと住所・緯度経度が完全一致し、生成順（`created_at`が20ms差で
連番）から、当初の100件シード投入（`ids 1-100`）の一部であることを確認した。

id=101/103は`temples_shrinecandidate`テーブルに対応するレコードが存在し、
`raw`列に`{"via": "resolve", "shrine_id": 101}`のようなGoogle Places解決
フロー（地図クリックからshrine候補を解決・登録する機能）由来である
ことが明示されている。`temples_shrineinteractionlog`にはこれら2行の
作成直後（+4秒）に`detail_view`ログが存在し、実行者は本番の唯一の
ユーザー（`id=1`, username=`test`, superuser, `date_joined`=2026-06-11
14:58:42）——つまり実顧客トラフィックではなく、開発者/QA担当による
map機能の手動テストと判断できる。

同じセッション内（`id`連番101〜105）に、名前が明らかにテスト目的である
`id=102 "テスト確認神社 20260611"`・`id=105 "広島市"`が挟まっており、
101/103がこの手動テストセッションの副産物であることを補強する。

さらに、同一パターンの重複が**他に1件存在する**ことも確認した
（`富岡八幡宮`: id=49（seed, place_ref_id空）／id=104（resolve由来,
place_ref_idあり、created_at=翌日10:31））——0091の対象外だが、
「resolve機能が既存shrineと名寄せせずに重複行を作成する」という
根本原因が0091固有ではなくsystem-wideの既知パターンであることを裏付ける。

### 4.2 Engagement/FK参照の確認

`temples_favorite`/`temples_visit`/`temples_goshuin`/`temples_shrine_deities`/
`temples_actionevent`/`temples_conciergethread.main_shrine_id`のいずれにも
id=21/22/101/103への参照は0件。`temples_shrineinteractionlog`のみ
id=101/103に1件ずつ（上記の手動テストクリック由来）。実質的な
ユーザーengagementはいずれの行にも存在しない。

### 4.3 判断

- **canonical**: id=21（長太稲荷神社）, id=22（給田六所神社）
  — 元々の100件シードデータの一部、`shrines_initial.json`の該当位置と
  完全一致、`astro_elements`/`visit_style_tags`がseed時点で正しく設定済み
- **duplicate**: id=101, id=103
  — 単一のtest/superuserアカウントによる地図resolve機能の手動テストで
  偶発的に作成された重複行。`place_ref_id`あり、seed由来の付随データ
  （`astro_elements`/`visit_style_tags`）が欠落

複数の独立した証拠（seed fileの位置一致、id範囲の生成波、
`place_ref_id`の有無、`astro_elements`/`visit_style_tags`の有無、
同一セッション内の明示的テストshrine名との時系列近接、
他の重複ペア`富岡八幡宮`での同一パターン再現）が収束しており、
推測ではなく実測に基づく判断である。

### 4.4 `.first()`は意図的な選択だったか

**偶然である。** `Shrine.Meta.ordering = ["-updated_at"]`により、`.first()`
は「最も最近更新された行」を選ぶ。対象2ペアではid=101/103が
duplicateでありながら`updated_at`がより新しいため、**もし
GEOSExceptionが発生していなければ、0091は誤ってduplicate行
（id=101/103）を更新し、本来enrichすべきcanonical行（id=21/22）は
未着手のまま残っていたはずである。** これはGEOS crashとは独立した、
より深刻な潜在的正しさのバグであり、スキーマ不整合による偶発的な
「クラッシュによる回避」がなければ気づかれずにProductionへ誤データを
書き込んでいた可能性が高い。

同様に、修正前のreverse関数は`name_jp__in=names`で全件（duplicateも
含む）を対象にしており、forward/reverseの非対称性というバグも
併存していた。

### 4.5 分類

**`CANONICAL_IDENTITY_CONFIRMED`**

---

## 5. Remediation Candidate Comparison

| 候補 | GEOS回避 | migration意図維持 | duplicate解決 | 備考 |
|---|---|---|---|---|
| A: `.only()` + 明示的`order_by` | ○ | ○ | ○ | 最小の変更、model instance/M2M managerをそのまま使える |
| B: `.values()` | ○ | △ | ○ | dictを返すため`.save()`/`goriyaku_tags.add()`が使えず、`update()`とM2M throughテーブル操作を別途実装する必要があり複雑化 |
| C: raw SQL | ○ | △ | ○ | M2M through tableのschemaをmigration外で決め打ちする必要があり、ORMのhistorical model stateが持つ正しい情報を捨てることになる。portability/保守性で劣る |
| D: 過去migrationの再構成（新migration追加等） | — | — | — | Phase 7で不要と判断（5節参照）。fake migration/手動`django_migrations`更新/Production ALTER/UPDATEは候補から除外（絶対禁止事項） |

**選定: Candidate A。** 最小の差分で、GEOS回避とduplicate解決の両方を
同時に満たし、ORM/M2M managerの既存セマンティクスをそのまま維持できる。

---

## 6. Historical Migration Edit Risk

- **Production**: `0091`は一度も成功appliedになっていない
  （`django_migrations`にレコードなし、atomic rollback）。既存の
  committed効果はゼロであり、in-place編集による「他環境で既に適用済み
  との乖離」リスクはProductionに関しては存在しない。
- **CI**: `.github/workflows/backend-tests.yml`の`unit`/`integration`
  jobはいずれもephemeralな`postgres`serviceコンテナを毎回新規作成し、
  そこへ全migrationを新規適用する。永続DBが存在しないため、CI側にも
  乖離リスクはない。
- **local dev**: `backend/db.sqlite3`は既に`0091`（旧コード）を適用済み
  （`django_migrations`で確認）。migrationファイルを編集しても、
  Djangoはfile checksumをDBへ保存しないため**このsqliteに対して0091が
  再実行されることはない**——つまりこの開発者ローカルの状態は編集の
  影響を受けず、単に「ローカルの適用履歴が現在のファイル内容と
  食い違う」という静的な事実が残るのみ（新規`migrate`実行時に
  影響はない）。

**結論: `0091`のin-place編集は安全。** データ変更のみのmigrationであり
schema変更を伴わないため、リスクは限定的。

---

## 7. Safe Patch Design

`backend/temples/migrations/0091_fill_missing_local_shrine_reason_facts.py`
を以下の方針で修正した（要件はすべて満たす）:

- **`location`列を読み込まない**: `.only("id", "name_jp", "history_theme",
  "goriyaku", "place_ref_id", "updated_at")`で明示的に列を絞り込み
- **migration本来の更新内容は不変**: `updates`リスト（対象名・
  history_theme・goriyaku・tags候補）は一切変更していない
- **canonical shrineを安定して選択**: `order_by(F("place_ref_id")
  .asc(nulls_first=True), "id")` — `place_ref_id`が`NULL`（=resolve機能を
  経由していない、元のカタログ行）を優先し、次点で`id`昇順。重複が
  存在しない環境では単純に唯一の一致行を返す（no-op的に安全）
- **`.first()`の暗黙orderingに非依存**: 上記の明示的`order_by`により、
  `Shrine.Meta.ordering`（`-updated_at`）に依存しなくなった
- **missing tagの既存guardを保持**: `if tags: shrine.goriyaku_tags.add(*tags)`
  はそのまま維持
- **id hardcodeなし**: production固有のid値（21/22/101/103等）は
  コード中に一切登場しない。`place_ref_id`の有無という一般的な
  識別ルールのみを使用
- **reverse behaviorを維持**: reverse関数も同じ`_resolve_target_shrine`
  helperを使うよう修正し、forward/reverseの対称性を回復
  （旧実装の「reverseは重複行も含めて全件処理してしまう」という
  非対称バグも同時に修正）

差分: [0091_fill_missing_local_shrine_reason_facts.py](../../backend/temples/migrations/0091_fill_missing_local_shrine_reason_facts.py)

---

## 8. Regression Tests

`backend/temples/tests/test_gis_migration_0091_shrine_reason_facts.py`
（新規、`USE_GIS=1`時のみ実行——GISが無効な環境では`temples`アプリが
`temples.migrations_nogis`という別の squashed migration setを使うため、
このmigration自体が独立したstepとして存在せず、テストの前提が
成立しない）。

| Test | 内容 | 修正前migrationでの結果 |
|---|---|---|
| A | `location`列が実際に`text`型（GiST indexを一時的に外して型変更し、非WKB値を挿入）でも`GEOSException`が起きないこと | **FAIL**（実際に同一の`GEOSException`を再現） |
| B | duplicate（`place_ref_id`あり・`updated_at`がより新しい）が存在してもcanonical行のみ更新される | **FAIL**（誤った行を更新） |
| C | 対象外のduplicate行が完全に無変更のまま（tag付与も含め）であること | **FAIL** |
| D | `地域安泰`tagが存在しない状態でもmigrationがエラーにならず、存在するtagのみ付与されること | PASS（元々このケースは重複と無関係のため旧実装でも成立） |
| E | reverse migrationがcanonical行のみを対象に正しく取り消すこと | **FAIL**（旧reverseは重複行も対象にしてしまう） |
| F | shrineデータが存在しないfresh DBで`0090`→`0091`のchainが例外なく成立すること | PASS |

**修正前のコードに対して意図的に再実行し、A/B/C/Eが実際に失敗する
（D/Fはduplicateやexisting dataと無関係なため元々成立する）ことを
確認した——テストが実際にこの2つのバグ（GEOS crash・誤ったidentity
selection）を検出できることを検証済み。** 修正後は6件すべてPASS。

---

## 9. Production-Equivalent Restore Test

2節で復元したProduction実dump相当の隔離DB（`temples 0090`適用済み・
`0091`未適用）に対し、**修正後**の`0091`を適用した。

| 項目 | 結果 |
|---|---|
| exit status | `0` |
| `GEOSException` | 発生せず |
| id=21（長太稲荷神社） | `history_theme="守り"`、`goriyaku`=想定文言、tag: `商売繁盛`・`五穀豊穣`（`地域安泰`はProductionに存在しないため付与されず、既存guard通り） |
| id=22（給田六所神社） | `history_theme="守り"`、`goriyaku`=想定文言、tag: `家内安全`のみ（同上） |
| id=101, id=103（duplicate） | `history_theme`/`goriyaku`とも空のまま、`updated_at`も無変更——**完全に無変更** |
| aggregate: `shrine` | 105 → 105（不変） |
| aggregate: `goriyaku_relation` | 280 → 283（Stage 3事前予測どおり+3） |
| aggregate: `auth_user`/`userprofile`/`visit` | 不変 |
| その他shrine（id=21/22以外）の`history_theme` | 変化なし（0件） |
| `users`側migration state | `0006`のまま不変（regressionなし） |
| `django_migrations`記録 | `temples 0091`が正しくapplied記録される |
| `0092`/`0093` | **実行していない**（絶対禁止事項として厳守） |

Stage 3記録に残っていた事前予測（「id=103/101がduplicateの`.first()`で
誤って選ばれ、`goriyaku_relation`が280→283になるはず」という**旧実装
前提の予測**）とは対象行が入れ替わったが、件数（283）自体は一致した
——正しい行（canonical）に対して同じ内容が適用された結果であり、
migration本来の意図（実運用2神社のreason facts補完）がようやく
正しく実現されたことを意味する。

---

## 10. Limitations

- Production baseline（`favorite`件数）について、
  `production-migration-local-execution-runbook.md`のStage 0〜3記録では
  `favorite=0`と記載されているが、今回参照した4つのProduction dump
  （Stage 0〜Stage 3直前のいずれも）を直接確認したところ実際には
  一貫して`favorite=3`だった。これは既存ドキュメントの記載誤り
  （おそらく初期の誤記がそのままコピーされ続けた）と考えられ、
  今回のPhase 8検証は同一dump内でのpre/post比較（3→3、不変）に
  基づいているため本修正の正しさには影響しない。念のため記録する。
- 同一パターンの重複（`富岡八幡宮` id=49/104等）が他にも存在する
  可能性があり、resolve機能自体の名寄せロジック改善は本Gateの
  scope外（Stage 3記録が既に指摘済みの別途点検事項）。
- `pytest`/`pytest-dotenv`のCLIオプション競合（`--envfile`の二重登録、
  `pytest-env`と`pytest-dotenv`の間の既知衝突）は本修正の対象外。
  ローカル実行では`-p no:dotenv`で回避し、実行可能なテスト経路
  （`temples`アプリ全体、1026 passed / 9 skipped、うちskipはGDAL/PostGIS
  ローカル環境起因で本修正と無関係）を最大限使用した。

---

## 11. Final Classification

**`TEMPLES_0091_REMEDIATION_READY`**

根拠:
- root cause再現済み（`PRODUCTION_SCHEMA_MODEL_MISMATCH_CONFIRMED`）
- canonical identity確定済み（`CANONICAL_IDENTITY_CONFIRMED`）
- safe patch実装済み（Candidate A、id hardcodeなし、意図維持）
- regression test 6件すべてPASS（修正前は該当4件が実際に失敗することも確認済み）
- Production相当restore DBで`0091`単体がexit 0、期待効果と完全一致、
  意図しない変更ゼロ
- `makemigrations --check --dry-run` / `manage.py check` / ruff lint
  すべてPASS
- `temples`アプリ全体のtest suite: 1026 passed, 9 skipped（既存環境起因、
  本修正と無関係）

**Production retryはMother Ship判断待ち。** 本セッションではProduction
migrationを一切実行していない。
