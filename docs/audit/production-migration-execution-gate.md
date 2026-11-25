> **Status: Active — Backup Gate PASS反映済み、Production live read-only監査完了、
> 重要な新発見（temples migration lineageの歴史的分岐）を確認した上で
> `READY_WITH_LIMITATIONS`と判定。Production migrationはまだ実行しない。**
>
> **Classification: `READY_WITH_LIMITATIONS`**
>
> 本ドキュメントはProduction Migration Execution Gateの正本であり、
> 過去のSTOP版（`EXECUTION_BLOCKED_BACKUP_GATE`）を置き換える。
> 本セッションでは、read-only credential bridge
> （`docs/audit/production-readonly-credential-bridge.md`）を通じて
> **実際にProduction DBへSELECT-only接続し**、migration state・schema
> を直接確認した。**Production migrate/restore/DB write/Environment変更は
> 一切行っていない。許可されたのはSELECT-only確認のみ。**

# Production Migration Execution Gate — Final Preflight Audit

## Phase 0 — Base State

| 項目 | 結果 |
|---|---|
| develop checkout | 完了 |
| `git fetch` + `git merge --ff-only origin/develop` | 完了（実行時点で既にup to date） |
| working tree | clean |
| develop HEAD SHA | `b1b86a6d...`（PR #2329、credential bridge追加のsquash merge commit） |
| PR #2329以降のtooling存在確認 | `scripts/migration_safety/`一式（`check_credential_presence.sh`・`readonly_query.sh`含む）を確認済み |
| 参照した既存文書 | `production-migration-execution-gate.md`（本ドキュメント旧版）・`real-production-backup-restore-gate.md`・`production-readonly-credential-bridge.md`・`migration-safety-tooling.md`をすべて再読した |

---

## Phase 1 — Backup Gate Re-entry

Mother Shipより、以下がBackup Gate実測結果として提供された（本セッションでは
独自に再実施せず、提供事実として記録する）:

| 項目 | 結果 |
|---|---|
| Production manual dump | 成功 |
| Production PostgreSQL version | `17.6` |
| dump使用client | PostgreSQL 17 client（version一致） |
| `roles.sql`/`schema.sql`/`data.sql` | いずれも size > 0 |
| dump保存先 | repo外 |
| isolated localhost PostgreSQLへのrestore | 成功、guard = `SAFE` |
| restored `users`最新 | `0005` |
| restored `temples`最新 | `0089` |
| Production/restored aggregate counts | 一致 |

Production baseline（Mother Ship提供値、本セッションでもPhase 2で再確認済み）:

| table | count |
|---|---|
| `auth_user` | 1 |
| `users_userprofile` | 1 |
| `temples_shrine` | 105 |
| `favorites_favorite` | 0 |
| `temples_visit` | 2 |
| `temples_shrine_goriyaku_tags` | 280 |

Schema baseline（Mother Ship提供値）:
- `users 0006` = unapplied
- `temples 0093` = unapplied
- `users 0006`追加4カラム = 不存在
- Knowledge tables = 不存在

**制約事項（Mother Ship報告のまま記録）**: `roles.sql`のrestore時、Supabase
固有role/GRANTでlocal restore時にpermission errorが発生した。ただし
Django migration state・public schema・application data・aggregate
countsはrestore後に一致した。**これはSupabase platform全体の完全DRでは
なく、KAMI MUSUBI Django application DBのmanual recovery routeとして
評価する**（Mother Ship方針をそのまま踏襲）。

### 判定

**`MANUAL_BACKUP_RESTORE_PASS` / `BACKUP_READY_WITH_MANUAL_RESTORE`として
Backup GateをPASS相当で受け入れ、Execution Gateを再開する。**

理由: Django application層（migration state・public schema・aggregate
data）の観点では完全一致が確認されており、今回のExecution Gateが
必要とする「migration直前に戻せる」という要件を満たす。role/GRANT
周りの制約はSupabase管理領域の話であり、KAMI MUSUBIアプリケーション
データの復旧可否には影響しない、というMother Shipの評価に同意する。

---

## Phase 2 — Production State Re-verification（実測・SELECT-only）

`docs/audit/production-readonly-credential-bridge.md`で構築した
credential bridge（`~/.config/kami-musubi/production-db.env` +
`scripts/migration_safety/readonly_query.sh`）を使用し、**実際に
ProductionへSELECT-only接続した。** credential値は一切表示・出力して
いない（`readonly_query.sh`は接続前にSQLがread-only allow-listを
通過することを強制し、接続はPG*環境変数経由でargvに一切現れない）。

| 確認項目 | 結果 |
|---|---|
| users latest migration | `0005_userprofile_current_period_end_and_more` |
| temples latest migration | `0089_actionevent` |
| `users 0006` applied | `false` |
| `temples 0093` applied | `false` |
| Knowledge tables存在 | `false`（3テーブルすべて未存在を直接確認） |
| `users_userprofile`追加4カラム存在 | `false`（`birthday`/`worship_style`で代表確認） |
| aggregate counts | Phase 1のbaselineと完全一致（`auth_user=1`/`userprofile=1`/`shrine=105`/`favorite=0`/`visit=2`/`goriyaku_relation=280`） |

**期待値と完全一致。`PRODUCTION_STATE_CHANGED`には該当しない。**

---

## Phase 3 — Target Migration Drift Audit

### develop最新版のmigration file再読（正本として確認、過去監査を盲信しない）

`users/migrations/0006_userprofile_birth_profile_fields.py`・
`temples/migrations/0090_*.py`〜`0093_*.py`を今回**改めて全文読み直した**。
内容は`docs/audit/production-all-app-migration-state-audit.md`・
`docs/audit/production-migration-0090-0093-safety.md`で確認済みの内容と
**完全に一致しており、変更は検出されなかった**（dependency・
RunPython/RunSQL・AddField/CreateModel・destructive operationの
有無いずれも既存監査の記述通り）。

| migration | dependency | 内容 | destructive操作 |
|---|---|---|---|
| `users 0006` | `users.0005` | `AddField`×4（`birthday`/`birth_time`/`birth_place`/`worship_style`） | なし |
| `temples 0090` | `temples.0089` | `RunPython`（`GoriyakuTag id=43`をself-guardingで付与、対象なければno-op） | なし |
| `temples 0091` | `temples.0090` | `RunPython`（2神社の`history_theme`/`goriyaku`/tags更新、`.filter().first()`で存在しなければno-op） | なし |
| `temples 0092` | `temples.0091` | `AddField`×2（`ShrineReflection`/`Visit`へ`thread`FK、`SET_NULL`、target=`temples.conciergethread`） | なし |
| `temples 0093` | `temples.0092` | `CreateModel`×3（`ShrineKnowledgeSource`/`ShrineHistory`/`ShrineDeity`）+ M2M | なし |

`TARGET_MIGRATION_CHANGED`には該当しない。

### ⚠️ 重要な新発見: temples migration lineageの歴史的分岐

Phase 2のライブ接続を活用し、`django_migrations`の`temples` app全件を
確認したところ、**想定していなかった事実**が判明した。

`temples`appのmigration履歴には、**2つの異なる命名lineageが混在して
いる**:

1. **2026-06-07 01:35台に適用された、`temples/migrations_nogis/`
   （`USE_GIS=False`時専用、"テスト/CIで使う"とコメントされた
   ディレクトリ）と完全一致する名前のmigration群**:
   `0001_initial`・`0002_goshuin_shrine`・`0003_backfill_missing_tables`・
   `0004_conciergethread_anonymous_id_and_user_nullable`・
   `0005_goshuin_and_goshuinimage`・`0006_goshuin_columns_repair`・
   `0007_shrine_history_theme_shrine_idx_shrine_history_theme`
2. **2026-06-11 08:49台に適用された、`temples/migrations/`
   （production運用中と想定していた標準ディレクトリ）の命名と一致する
   migration群**: `0002_initial`〜`0089_actionevent`（`0001_initial`は
   1で既に記録済みのため、この回では改めて記録されていない）

**`(temples, 0001_initial)`という同一名の行は1件のみ存在する
（重複行はSQLで確認済み、`COUNT(*) > 1`の行は0件）。** つまり
`django_migrations`は「`0001_initial`は適用済み」という**名前だけ**を
記録しており、それが`migrations/0001_initial.py`（ConciergeHistory・
Favorite・GoriyakuTag・Goshuin・RankingLog・Shrine[緯度経度のみ]・
ViewLike・Visitを作成）由来なのか、`migrations_nogis/0001_initial.py`
（PlaceRef・Shrine[kind/location(text)/place_ref/owner/astro_elements等]・
GoriyakuTag・Deity・ShrineDeities・Visitを作成、テーブル名を明示指定）
由来なのかを、テーブル自体は区別できない。

**実際にProductionの`temples_shrine`テーブルを直接確認したところ、
現在の実カラム構成は`migrations_nogis/0001_initial.py`の設計と一致した**
（`kind`/`location`(text型、PostGIS geometryではない)/`place_ref_id`/
`owner_id`/`astro_elements`/`views_30d`/`favorites_30d`/`popular_score`/
`last_popular_calc_at`/`kyusei`が存在。`migrations/0001_initial.py`が
定義する`name_jp`のみのシンプルな初期形とは明確に異なる）。**加えて、
`history_theme`（`migrations/0084`由来）・`visit_style_tags`
（`migrations/0080`由来）も存在しており、これらは`migrations/`
lineageの「後半」migrationが実際に実行されたことを示す。**

つまり、production の`temples_shrine`実体は、**`migrations_nogis`ベースで
初期構築され、その後`migrations/`lineageの後続migration（少なくとも
0080・0084、および`postgis` extension自体を作成した0021/0025/0027
相当）が実際に適用されて現在の形になった**、と直接確認できるデータから
判断するのが最も整合的な解釈である。（`pg_extension`テーブルで
`postgis 3.3.7`のインストールを確認したが、これは`migrations_nogis`
には存在しない`CreateExtension("postgis")`操作を含む`migrations/`
lineageの一部が実行された証拠。一方`pg_trgm`は未インストールであり、
これを作成するはずの`migrations/0027`・`0036`の該当部分は実行されて
いない可能性がある——ただしこの詳細は本Gateの対象範囲外のため深追いは
していない。）

**したがって、`docs/audit/production-migration-0090-0093-safety.md`
（PR #2320）が確立した`SAFE_SEQUENTIAL_MIGRATION`の evidentiary basisは、
実際にはProductionの実schemaを反映していなかったことが判明した。**
あの監査はローカルで`migrations/0001→0089`を素直に再現したDB上で
検証したものであり、それは実Productionの実際の来歴
（`migrations_nogis`起点）とは異なる。

### この発見への対応（本Gateでの追加検証）

上記発見を受け、`SAFE_SEQUENTIAL_MIGRATION`の結論を鵜呑みにせず、
**Productionの実schemaに対して`users 0006`・`temples 0090-0093`が
実際に必要とする個別の対象（column/table）が、現時点で本当に不在で
あるか**をPhase 2で直接SELECT-onlyにより再確認済みである（上表参照）。
加えて、以下も直接確認した:

| 確認項目 | 結果 |
|---|---|
| `temples_visit.thread_id`存在 | `false`（0092が追加する対象、衝突なし） |
| `temples_shrinereflection.thread_id`存在 | `false`（同上） |
| `temples_conciergethread`テーブル存在・`id`型 | 存在、`bigint`（0092のFK先として型互換） |
| `temples_shrine.id`型 | `bigint`（0093の`ShrineHistory.shrine`FK先として型互換） |
| `temples_goriyakutag`・`temples_shrine_goriyaku_tags`存在 | 存在（0090/0091のRunPythonが操作する対象） |
| `temples_shrine.history_theme`存在 | 存在（0091が更新する対象列） |

**結論**: `users 0006`・`temples 0090-0093`の4件のtemples migrationが
実際に発行するDDL/ORM操作は、いずれも「対象table/columnの存在」
「FK先の型互換性」という狭い前提にのみ依存する**加算的（additive）**
操作であり、これらの前提はすべて満たされていることを直接確認した。
**したがって、歴史的なlineage分岐の発見にもかかわらず、この4件の
migrationを現在のProductionへ適用すること自体の技術的リスクは
低いと評価する。** ただし、これは「事前のローカル再現テストで
証明された安全性」ではなく「**Production実DBへの直接確認によって
裏付けられた安全性**」であり、根拠の性質が変わったことをMother Ship
は認識すべきである。

### 分類

**`SCHEMA_DRIFT_CONFIRMED_BUT_TARGET_OPERATIONS_VERIFIED_SAFE`**

（Phase 4の定型分類リストには存在しない状態のため、本監査独自の
中間ラベルとして付記する。Phase 12の最終classificationでは
`READY_WITH_LIMITATIONS`に反映する。）

---

## Phase 4 — Cross-App Dependency Audit

develop最新のmigration fileを確認した結果:

- `users 0006`の`dependencies`は`[("users", "0005_...")]`のみ
- `temples 0090`〜`0093`の`dependencies`はいずれも直前のtemples
  migrationのみ（線形、分岐なし）
- **どちらのappも、相手appへのdependencyを一切宣言していない**

### 分類

**`INDEPENDENT`**

Django migration graph上、`users 0006`と`temples 0090-0093`は互いに
独立しており、どちらを先に適用しても技術的な支障はない。ただし
`python manage.py migrate`（app指定なし）を使うと、この独立性とは
無関係に**両方を同時に巻き込む**ため、Phase 5では引き続きapp単位の
明示実行を第一候補とする。

---

## Phase 5 — Execution Order Design

### 推奨execution order

1. `users 0006`
2. verification（Phase 8）
3. `temples 0090`
4. `temples 0091`
5. `temples 0092`
6. `temples 0093`
7. verification（Phase 9）

### 技術的理由

- Phase 4で`INDEPENDENT`と確定したため、`users`→`temples`の順序自体に
  技術的な強制力はない。`users 0006`を先に置くのは、**変更が単純
  （`AddField`×4のみ）で影響範囲が最小のものから着手し、1件ごとの
  成功を確認してから次に進む**という設計判断による（指示のPhase 5に
  合わせた順序）
- `temples`側は0090→0091→0092→0093の順序が**Django migration graph上
  strictly必須**（各migrationが直前のみに依存する線形チェーン）
- 裸の`python manage.py migrate`は、Phase 3で確認した通り`users 0006`と
  `temples 0090-0093`を同時に巻き込むため、**第一候補にしない**
  （`docs/audit/migration-execution-method-reality-audit.md`・
  `docs/audit/production-all-app-migration-state-audit.md`で既に
  確立した結論を踏襲）

### migration間verification point

- `users 0006`適用直後 → Phase 8
- `temples 0090`適用直後 → 簡易確認（`django_migrations`の`temples`
  latestが`0090`になっていること、error無し）
- `temples 0091`適用直後 → 同上（`0091`）
- `temples 0092`適用直後 → 同上（`0092`）
- `temples 0093`適用直後 → Phase 9（詳細）

---

## Phase 6 — Exact Command Design（設計のみ、未実行）

### 前提確認（推測でパスを作らない）

- `backend/start.sh`は`RUN_MIGRATIONS_ON_START=1`の場合`cd`せず
  `python manage.py migrate --noinput`をリポジトリのbuild時
  working directoryから実行する構造（`docs/audit/
  migration-execution-method-reality-audit.md`Phase 4で確認済み）
- Render上のbuild/start commandそのもの（root directory設定・
  build command）は本セッションから未確認のまま
  （`docs/audit/render-reality-gate-phase2-stop.md`でDashboardアクセス
  不可と既に結論済み。今回のcredential bridgeはDB接続専用であり、
  Render Dashboard情報を提供するものではない）

### Exact command（案、実行しない）

```bash
# working directory: Renderのbuild root（backend/相当。Render Dashboard側の
# root directory設定と一致させる必要があるが、本セッションからは未確認）
python manage.py migrate users 0006 --noinput
python manage.py migrate temples 0090 --noinput
python manage.py migrate temples 0091 --noinput
python manage.py migrate temples 0092 --noinput
python manage.py migrate temples 0093 --noinput
```

- [x] users exact command確定（上記）
- [x] temples exact command確定（上記、4件個別指定）
- [ ] working directory確定 — **未確定**。Render側のroot directory設定が
  未確認のため（Dashboard未確認）
- [ ] environment前提確定 — **未確定**。`DATABASE_URL`がRender環境変数
  として自動的にどの値になっているか（Supabase接続文字列がRender側で
  正しく設定されているか）は前提とするが、本セッションからは
  Render環境変数を直接見ていない
- [ ] command execution location確定 — **未確定**。候補（Render Shell /
  One-Off Job / `RUN_MIGRATIONS_ON_START`）はいずれも
  `docs/audit/migration-execution-method-reality-audit.md`で比較済みだが、
  実際にどれが使えるか（現在のRender planでShell/Job機能が有効か）は
  未確認のまま
- [x] `--noinput`要否: 必要（対話プロンプトを避けるため、既存運用と同じ）
- [x] app scoped migrationであること確認: 上記コマンドはすべて`<app> <migration_name>`形式であり、app指定なしの`migrate`は使わない

**Production実行はしない。**

---

## Phase 7 — Pre-Migration Procedure（設計のみ）

- [x] Production release SHA確認手順 — `/healthz/`のread-only GETで
  `release`フィールドを確認する方式を既存監査（`docs/audit/
  production-db-readonly-audit-access-gate.md`）で確立済み。今回は
  DB側のcredential bridgeとは別に、Renderの`/healthz/`への読み取り
  専用GETも実行前に再確認することを推奨する
- [x] Production migration state確認手順 — `sql/migration_state.sql`を
  `readonly_query.sh`経由で実行（本Gateで既に実演済み）
- [x] `users = 0005`確認 — Phase 2で確認済み
- [x] `temples = 0089`確認 — Phase 2で確認済み
- [ ] Production runtime重大障害なし確認 — **未実施**。`/healthz/`
  または`/api/schema/`への読み取り専用GETを migration直前に行う
  ことを手順として明記するが、本セッションでは今回実施していない
- [x] fresh pre-migration snapshot取得手順 — `sql/pre_migration_snapshot.sql`
  （既存）
- [x] fresh manual dump取得手順 — `scripts/migration_safety/dump_readonly.sh`
  （既存、Backup Gateで実証済み）
- [x] dump size > 0確認手順 — script自体が自動報告（既存実装）
- [x] dump repo外保存 — `guard.py`が強制（既存実装）
- [x] backup timestamp記録手順 — 手動記録（Runbook既定）
- [x] credential非露出確認 — `readonly_query.sh`/`check_credential_presence.sh`が構造的に保証（既存実装、本Gateでも実演し漏洩なしを確認）

**重要**: 今回Phase 1で反映したdumpはBackup Routeの実証用であり、
**実際にProduction migrationを実行する場合は、migration直前に
fresh dumpを再取得する**ことを原則とする（Backup Gate実証時点の
dumpをそのまま「直前backup」として使い回さない）。

---

## Phase 8 — `users 0006` Verification Design

DB（`sql/post_migration_verification.sql`の該当部分を使用）:

- [ ] `django_migrations` users latest = `0006`
- [ ] `birthday`/`birth_time`/`birth_place`/`worship_style`列存在
- [ ] `auth_user`件数維持（baseline: `1`）
- [ ] `users_userprofile`件数維持（baseline: `1`）

Runtime（未実施、Mother Ship側での確認を想定）:

- [ ] Production Web起動確認
- [ ] login確認
- [ ] MyPage確認
- [ ] UserProfile参照500なし確認
- [ ] Render logで`UndefinedColumn`なし確認
  （`docs/audit/production-all-app-migration-state-audit.md`で発見した
  `users/apps.py`の`ensure_profile`signalとschema不整合の問題が、
  `users 0006`適用によって解消していることの確認でもある）

新規signupは、migration成功とruntime確認後、実施可否をMother Shipへ
返す。**本Gateでは新規signupを実行しない。**

---

## Phase 9 — `temples 0090-0093` Verification Design

Migration:
- [ ] `django_migrations` temples latest = `0093`

Knowledge schema:
- [ ] `temples_shrineknowledgesource`存在
- [ ] `temples_shrinedeity`存在
- [ ] `temples_shrinehistory`存在
- [ ] `temples_shrinedeity_sources`存在（M2M）
- [ ] `temples_shrinehistory_sources`存在（M2M）

Existing data（baseline、Phase 1/2で確認済みの値と比較）:
- [ ] `temples_shrine`件数 = `105`維持
- [ ] `temples_shrine_goriyaku_tags`件数 ≥ `280`
      （`0090`/`0091`が対象神社にtagを追加する可能性があるため、
      「維持」ではなく「減少していないこと」を確認基準とする。
      対象神社が存在しない場合はno-opのため`280`のまま変化しない
      ケースもある）
- [ ] `temples_visit`件数 = `2`維持
- [ ] `favorites_favorite`件数 = `0`維持

`0090`/`0091`のRunPython個別確認（期待される更新がある場合）:
- [ ] `0090`: 対象4神社（筑波山神社等）のうち`history_theme='静寂'`かつ
      `name_jp`一致するものに`GoriyakuTag id=43`が付与されているか
      （対象が存在しなければno-opのままで正常）
- [ ] `0091`: `長太稲荷神社`・`給田六所神社`の`history_theme`が`'守り'`に
      更新されているか（対象が存在すれば）

Knowledge Dataはまだ投入しない（`Phase 3 — Knowledge Data Foundation`
は別Gateのまま、本監査の対象外）。

---

## Phase 10 — Failure Stop Conditions

以下のいずれかに該当した場合、即STOPし次のmigrationへ進まない:

- migration commandがnon-zero exitで終了した
- `django_migrations`に想定外のmigrationが記録された（例: 他appの
  migrationが巻き込まれた）
- `users 0006`後、`UserProfile`schemaがPhase 8の期待値と不一致
- `temples`migration後、Knowledge tableが不足
- 既存aggregate countが予期せず減少した
- Runtimeで500が発生した
- `UndefinedColumn`が発生した
- `IntegrityError`が発生した
- migration stateが想定外の値になった
- 実行直前の再確認でProduction release SHAが変化していた
- 直前backup取得に失敗した
- credential漏洩の疑いが生じた
- schema driftが新たに発見された（今回のPhase 3の発見を踏まえ、
  今後も同様の「`django_migrations`上の名前と実schemaの不一致」が
  他appでも起きていないか、実行前に改めて注意を払う）

---

## Phase 11 — Recovery Decision Tree

**migration失敗時に自動rollbackはしない。** まず状態を観測する:

1. どのmigrationで失敗したか（`users 0006`か、`temples 0090-0093`の
   どれか）
2. `django_migrations`へ記録されたか（Djangoは通常、失敗した
   migrationは記録しない設計だが、`RunPython`の一部が実行された後に
   例外が出た場合、PostgreSQLのトランザクション境界内であれば
   ロールバックされる——各migrationは既定でtransactional）
3. schema変更が途中まで入ったか
4. existing dataが維持されているか
5. runtimeが利用可能か（他migrationは無事適用済みなら、部分適用でも
   runtime自体は動き続けている可能性が高い）

分類:

| 状況 | 分類 |
|---|---|
| 原因不明、影響範囲が読めない | `STOP_AND_INVESTIGATE` |
| 特定のmigrationが安全にreverseできると判断できる（例: `users 0006`は
  `AddField`のみで、実データ書き込みが起きる前に失敗した） | `DJANGO_MIGRATION_ROLLBACK_CANDIDATE`（`python manage.py migrate <app> <前のmigration>`） |
| schemaとmigration stateの記録が食い違っている（Phase 3で発見した
  ような不一致が新たに生じた） | `MANUAL_SCHEMA_RECONCILIATION_REQUIRED` |
| データ破損・aggregate count減少等、Django migration機構では
  対処できない事故 | `MANUAL_BACKUP_RESTORE_CANDIDATE`（最終手段） |

`MANUAL_BACKUP_RESTORE_CANDIDATE`を選ぶ場合の実行手順は
`scripts/migration_safety/README.md`のRestore Verification Routeに
準じるが、**Production restoreそのものは本タスクでは実行しない**、
かつ実行判断はMother Ship専権とする。

---

## Phase 12 — Execution Method Final Classification

**`READY_WITH_LIMITATIONS`**

根拠（Backup Gate PASSのみを理由にせず、Phase 2〜11全体を根拠とする）:

**READYと判断する理由**:
- Phase 1: Backup GateがPASS相当（アプリケーション層の観点で完全一致）
- Phase 2: Production live read-only接続で、想定通りの migration
  state・schema・aggregate countsを直接確認できた
- Phase 3: migration file自体に変更なし。**歴史的なschema lineage分岐を
  発見したが、対象migrationが必要とする個別の column/table 前提は
  Production実DBに対して直接確認済みであり、加算的操作のみで
  構成されているため技術的リスクは低いと判断できる**
- Phase 4: `INDEPENDENT`（cross-app dependencyなし）
- Phase 5〜11: execution order・exact command（一部未確定）・
  verification・failure条件・recovery decision treeを設計済み

**LIMITATIONSとして残る理由（`READY_FOR_SCOPED_SEQUENTIAL_MIGRATION`と
断定しない理由）**:
1. Phase 3の発見（temples migration lineageの歴史的分岐）は、**今回
   検証した4件のmigration以外の箇所にも同様の分岐が潜んでいる
   可能性を完全には排除できない**。今回は対象migrationが触れる
   column/tableのみを個別確認したのであり、temples app全体の
   schemaを`migrations/`lineageと1:1で突き合わせる網羅的な検証は
   行っていない
2. Phase 6: Render側のexecution method（working directory・
   実行手段そのもの）が未確定のまま
3. Phase 7: Production runtime健全性の実行直前確認、fresh dumpの
   実行直前取得は、設計のみで今回実施していない
4. Backup Gate自体に、Supabase role/GRANT復元の制約が残っている
   （Mother Ship報告のまま）

---

## Phase 13 — Mother Ship Go / No-Go Package

**最終判断は行わない。以下をMother Shipへ返す。**

1. **develop SHA**: `b1b86a6d`
2. **Production release SHA**: 未確認（`/healthz/`再確認は今回未実施、Phase 7参照）
3. **Production users migration state**: `0005`（Phase 2で実測確認）
4. **Production temples migration state**: `0089`（Phase 2で実測確認）
5. **Backup Gate classification**: `MANUAL_BACKUP_RESTORE_PASS` / `BACKUP_READY_WITH_MANUAL_RESTORE`（Mother Ship実測、role/GRANT制約付き）
6. **target migration drift有無**: migration file自体の変更は**なし**。ただし**Production側のtemples app migration lineageに歴史的分岐を新規発見**（Phase 3、詳細は上記）
7. **cross-app dependency classification**: `INDEPENDENT`
8. **推奨execution order**: `users 0006` → verify → `temples 0090` → `0091` → `0092` → `0093` → verify
9. **exact Production commands**: Phase 6記載の5コマンド（app scoped、`--noinput`）。ただしworking directory/実行手段は未確定
10. **pre-migration procedure**: Phase 7記載（fresh dump再取得を原則とする）
11. **`users 0006` verification**: Phase 8記載
12. **`temples 0090-0093` verification**: Phase 9記載
13. **Runtime QA**: Phase 8/9に記載、いずれも未実施（設計のみ）
14. **failure STOP conditions**: Phase 10記載
15. **recovery decision tree**: Phase 11記載
16. **Execution Gate classification**: **`READY_WITH_LIMITATIONS`**
17. **remaining risks**:
    - **最重要**: temples app migration lineageの歴史的分岐（Phase 3）。
      今回対象の4 migrationについては個別に安全性を直接確認したが、
      temples app全体としての「`django_migrations`の記録」と「実schema」の
      整合性は、今回のGateのscopeを超えて網羅検証されていない
    - Render側の実行手段（working directory含む）が未確定
    - Production runtime健全性・release SHAの実行直前再確認が未実施
    - Backup GateのSupabase role/GRANT制約が残っている
18. **Go/No-Go判断に必要な未確定事項**:
    - Render Dashboardでのroot directory/実行手段確認（Mother Ship側作業）
    - 実行直前の`/healthz/`確認・fresh dump取得（実行フェーズの一部として、Go判断後に行う）
    - temples app全体のschema lineage分岐について、今回のscope外の
      箇所にも同様の問題がないか、追加監査を行うかどうかの判断
      （Mother Ship判断。**今回の4 migrationの適用可否自体は
      ブロックしないという評価だが、根本原因調査は別途の検討事項として
      切り出すことを提案する**）

**Production migrationはMother Ship判断まで実行しない。**

---

## Stop Conditions（遵守確認）

- [x] Production migrate禁止（遵守）
- [x] Production restore禁止（遵守）
- [x] Production DBへのINSERT/UPDATE/DELETE禁止（遵守、SELECT-onlyのみ実施）
- [x] Production schema変更禁止（遵守）
- [x] Environment変更禁止（遵守）
- [x] `RUN_MIGRATIONS_ON_START`変更禁止（遵守）
- [x] Render設定変更禁止（遵守）
- [x] Supabase設定変更禁止（遵守）
- [x] Knowledge Data投入禁止（遵守）
- [x] Batch 8開始禁止（遵守）
- [x] 新規signup禁止（遵守）
- [x] credential value表示禁止（遵守。本ドキュメントに接続情報は一切含まれない）
- [x] dumpのGit追加禁止（遵守。dumpファイル自体は本セッションで生成していない）

## Repository Changes

- `docs/audit/production-migration-execution-gate.md`: 本ドキュメント（更新。旧`EXECUTION_BLOCKED_BACKUP_GATE`版を置き換え）
- 上記以外の変更なし
