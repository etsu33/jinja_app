> **Status: Completed — Classification: `SAFE_SEQUENTIAL_MIGRATION`**
>
> 本ドキュメントはtemples migration 0090〜0093の安全性をローカルのみで検証した
> 記録である。**production migrateは一切実行していない。** 検証はローカルの
> 一時PostgreSQLデータベース（テスト終了後に削除済み）上でのみ行った。

# Production Migration 0090-0093 Safety Audit

## Phase 0 — Local Audit Base

| 項目 | 結果 |
|---|---|
| develop最新化 | 完了（`git pull --ff-only`） |
| working tree | clean |
| develop HEAD | `4146140d7e52663e70a8322a29a243a972255156` |
| Production latest migration | `0089_actionevent`（Mother Ship提供値として記録） |
| Production 0093 | `false`（Mother Ship提供値として記録） |
| Knowledge table | production不存在（Mother Ship提供値として記録） |

上記3項目はMother Ship側がRender Dashboard経由で実行したSQL結果として
提供されたものであり、本監査ではこれを検証済みの前提として扱う。

---

## Phase 1 — Migration Inventory（ローカルrepo）

`backend/temples/migrations/0090*.py` 〜 `0093*.py` を直接読んだ。

| Migration | 種別 | 内容 | dependencies |
|---|---|---|---|
| `0090_add_rest_healing_tag_to_silent_shrines` | `RunPython`（reversible） | 4神社（筑波山神社等）へGoriyakuTag id=43を追加。`GoriyakuTag.DoesNotExist`をtry/exceptで捕捉し、tag未存在ならno-op | `0089_actionevent` |
| `0091_fill_missing_local_shrine_reason_facts` | `RunPython`（reversible） | 2神社（長太稲荷神社・給田六所神社）の`history_theme`/`goriyaku`/tagsを設定。`.filter().first()`で対象神社が存在しない場合はno-op | `0090_add_rest_healing_tag_to_silent_shrines` |
| `0092_add_thread_to_visit_and_reflection` | `AddField`（nullable, `blank=True, null=True`） | `ShrineReflection`/`Visit`に`thread`FK（`SET_NULL`）を追加 | `0091_fill_missing_local_shrine_reason_facts` |
| `0093_shrine_knowledge_model_foundation` | `CreateModel` × 3 | `ShrineKnowledgeSource`/`ShrineHistory`/`ShrineDeity`の新規テーブル作成（Knowledge Schema Foundation） | `0092_add_thread_to_visit_and_reflection` |

### dependency chain

`0089 → 0090 → 0091 → 0092 → 0093`（完全に線形、分岐なし）。

### 危険操作の有無

- **RunSQL**: なし
- **RemoveField**: なし
- **DeleteModel**: なし
- **destructive SQL**: なし（`sqlmigrate`実測でも`ALTER TABLE ... ADD COLUMN`と
  `CREATE TABLE`のみ。`DROP`/`ALTER COLUMN TYPE`/`DELETE`は一切含まれない）

この4件の範囲には、develop全体のmigration gap監査（`docs/audit/
backend-release-strategy-audit.md`）で発見した危険migration（`0072`
RemoveField、`0081`/`0082`/`0085`/`0086`のforce recreate/repair系）は
**一件も含まれない**。それらは全て`0072`〜`0086`の範囲、つまりproductionの
現在地`0089`より前に位置しており、productionが`0089`まで到達できている
以上、既に解消済みと判断できる。

### 補足確認: USE_GIS migration経路の分岐リスク

`shrine_project/settings.py`には、`USE_GIS=False`時に`temples`アプリの
migrationを`temples.migrations_nogis`へ切り替えるロジックが存在する
（`MIGRATION_MODULES["temples"] = "temples.migrations_nogis"`、
「テスト/CIで使う」とコメントあり）。`migrations_nogis/`は`0008`までしか
存在しない古いディレクトリであり、production運用中のディレクトリとは
考えにくいが、念のため`.env.render.example`・`backend/.env.prod`・
`backend/.env.example`を確認したところ、`USE_GIS`を明示的に`0`/`False`へ
上書きする記述はどこにもなかった（`backend/.env.example`は`USE_GIS=1`）。
したがって、production は`USE_GIS`のデフォルト値`True`のまま動作しており、
標準の`temples/migrations/`（本監査で読んだディレクトリ）が実際に使われて
いると判断した（推測ではなく設定ファイルの直接確認による）。

---

## Phase 2 — Production Compatibility（ローカル分析）

- **0089から順次適用可能か**: Phase 4の実測で確認済み（後述）
- **0090→0091→0092→0093の依存関係**: 完全線形、分岐なし（Phase 1で確認済み）
- **repair migrationとの競合**: 該当範囲に repair/force-recreate 系migrationは
  存在しないため競合なし
- **IF NOT EXISTS系との競合**: 該当範囲に raw SQL 自体が存在しないため競合なし
- **existing production data影響**: `0090`/`0091`はRunPythonで既存の`Shrine`/
  `GoriyakuTag`データを読み書きするが、対象が存在しない場合は自己防御的に
  no-opする設計（Phase 1のコード確認、Phase 4の実測両方で確認）。`0092`/
  `0093`は既存データに一切触れない（新規カラム追加・新規テーブル作成のみ）
- **schema driftリスク分類**: 低（後述Phase 5で確定）

---

## Phase 3 — Dry-run（ローカルのみ、production未実行）

```
$ python manage.py sqlmigrate temples 0090
BEGIN; -- Raw Python operation（SQL化不可） COMMIT;

$ python manage.py sqlmigrate temples 0091
BEGIN; -- Raw Python operation（SQL化不可） COMMIT;

$ python manage.py sqlmigrate temples 0092
ALTER TABLE "temples_shrinereflection" ADD COLUMN "thread_id" bigint NULL ...
ALTER TABLE "temples_visit" ADD COLUMN "thread_id" bigint NULL ...
CREATE INDEX ...

$ python manage.py sqlmigrate temples 0093
CREATE TABLE "temples_shrineknowledgesource" (...);
CREATE TABLE "temples_shrinehistory" (...);
CREATE TABLE "temples_shrinehistory_sources" (...);
CREATE TABLE "temples_shrinedeity" (...);
CREATE TABLE "temples_shrinedeity_sources" (...);
-- ALTER TABLE ... ADD CONSTRAINT（FK）、CREATE INDEX のみ
```

全SQLをレビューした。`DROP`/`ALTER COLUMN ... TYPE`/`DELETE`/`TRUNCATE`は
一切含まれない。**Productionでは実行していない**（ローカルの`sqlmigrate`は
DB接続なしで静的にSQLを生成するコマンドであり、それ自体が安全である）。

---

## Phase 4 — 0089相当DB再現（ローカル一時DB）

1. **一時PostgreSQL用意**: `jinja_migration_audit_temp`をローカルで新規作成
   （既存のlocal dev DB `jinja_db`とは完全に別のデータベース。テスト後に削除済み）
2. **0089までmigration**: `DATABASE_URL=...jinja_migration_audit_temp
   python manage.py migrate temples 0089 --noinput` → **全件`OK`、エラーなし**
3. **schema状態確認**: Knowledge関連テーブル（`temples_shrineknowledgesource`
   等）が存在しないことを確認（production報告と一致）
4. **realisticなbaseline data投入**: `import_shrines_seed`（100神社作成）+
   `backfill_goriyaku_tags --with-visit-style --force`（39 tag作成、280 links）
   を実行し、空DBではなくデータが入った状態で0090/0091のRunPythonを本番同様に
   検証できるようにした
   - この時点で `GoriyakuTag id=43` は存在しなかった（fresh seedのtag ID採番は
     productionの実IDと一致しない）→ **`0090`が意図通りno-opするケースを
     実地で検証できた**
   - `長太稲荷神社`・`給田六所神社`はseedに含まれていた → **`0091`が実際に
     データを更新するケースを実地で検証できた**
5. **0090〜0093を順次適用**: `migrate temples 0093 --noinput` →
   **全4件`OK`、エラーなし**
6. **エラー有無確認**: エラーなし
7. **既存データ保持確認**: 適用前後でShrine件数`100`→`100`、変化なし
   （データ削除・破損なし）。`給田六所神社`の`history_theme`が`0091`の
   意図通り`'守り'`へ更新されたことを確認
8. **Knowledge table作成確認**: `temples_shrineknowledgesource` /
   `temples_shrinehistory` / `temples_shrinehistory_sources` /
   `temples_shrinedeity` / `temples_shrinedeity_sources` の**5テーブル全て
   作成を確認**
9. **rollback可否確認**: `migrate temples 0089 --noinput` →
   **`0093`→`0090`まで全件`Unapplying ... OK`、エラーなくrollback成功**

一時DBはテスト完了後、`DROP DATABASE jinja_migration_audit_temp`で削除済み。

---

## Phase 5 — Classification

**`SAFE_SEQUENTIAL_MIGRATION`**

根拠:
- dependency chainが完全線形（分岐なし）
- destructive operation（RemoveField/DeleteModel/RunSQL/DROP）が対象範囲に
  一件も存在しない
- `0089`相当のローカル再現DBに対して0090〜0093が実データ付きでエラーなく
  適用できた（実測）
- 既存データの損失・破損が発生しないことを実測で確認した
- rollback（0093→0089）もエラーなく成功することを実測で確認した
- 対象範囲に過去のschema drift repair migration（`0081`/`0082`/`0085`/
  `0086`等）は含まれない（それらは既にproductionの現在地より前に位置する）

---

## Stop Conditions（遵守確認）

- [x] Production migrateしない（実行せず、ローカル一時DBのみ使用）
- [x] makemigrationsしない（実行していない）
- [x] Environment変更しない（Render環境変数は一切変更していない）
- [x] production DB writeしない（production DBへは一切接続していない）
- [x] Batch 8開始しない（着手していない）

---

## Repository Changes

- `docs/audit/production-migration-0090-0093-safety.md`: 本ドキュメント（新規）
- 上記以外の変更なし。一時DB `jinja_migration_audit_temp` はローカルのみに
  作成・削除しており、リポジトリやproductionには一切影響しない

## 次のGate

Migration安全性は`SAFE_SEQUENTIAL_MIGRATION`と確定した。これは
`docs/audit/backend-release-strategy-audit.md`のRelease Strategy候補比較
（Phase 5、Candidate A〜D）における「migration complexity」軸の判断材料と
なる。ただし、これはtemples app・0090-0093範囲**のみ**の結論であり、
他アプリのmigration state・Release Strategy自体の最終決定・Knowledge Data
投入方法（Importer Contract）は本監査の対象外のままである。
