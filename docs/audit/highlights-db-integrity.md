# Highlights PR-2: 同一神社のDB整合性・Migration安全性

> Status: Audit / Historical。PRレビュー用の記録であり、本番適用許可ではない。
> 検証日: 2026-11-22 JST
> Base: develop `4a9b821a9709745f079510e54788fde7c476b6c1`
> Branch: `feature/highlights-db-integrity`
> 判定: **PRレビューへGO / Production MigrationはHOLD**

## 前提と範囲

PR #3504はdevelopへマージ済み（merge commit `be55305e1`）。作業中断後にPR-3〜5が取り込まれたため一度STOPし、母艦から通常0125／NoGIS0024として組み直す承認を得た。最新developで通常Leaf `0124_highlight_translation_location_hint`、NoGIS Leaf `0023_highlight_translation_location_hint`、既存公開判定・API・翻訳レビュー処理を確認した。

`backend/shrine_project/settings.py`の切替条件は `IS_PYTEST and DISABLE_GIS_FOR_TESTS and not USE_SQLITE`。単にUSE_GIS=0にしてもNoGIS系列にはならない。適用対象系列を明示して検証した。

`scripts/migration_safety/README.md`は本番自動実行を禁止し、明示的な接続先・隔離DB・Backup/Restore Gateを要求する。今回の接続先は新設した専用ローカル監査DBのみ。本番・Supabase・外部環境には接続せず、実データ投入、公開判定/API/UI、推薦、Meaning、英語特徴語、削除・レビュー状態の変更は行っていない。中断時に消失した一時worktreeの変更・検証ログは完了扱いせず、リポジトリ内worktreeで復元し全件再検証した。

## 追加・変更ファイル

| パス | 内容 |
| --- | --- |
| `backend/temples/constraints_highlights.py` | Model/Stateに保持できるPostgreSQL用CompositeForeignKey |
| `backend/temples/models_highlights.py` | Highlightの複合UNIQUE、関連の複合FK2件。既存FK・列は保持 |
| `backend/temples/models.py` | ShrineHistory.Metaの複合UNIQUEのみ。既存field/on_deleteは無変更 |
| `backend/temples/migrations/0125_highlights_same_shrine_integrity.py` | 通常0124依存の新規Migration |
| `backend/temples/migrations_nogis/0024_highlights_same_shrine_integrity.py` | NoGIS0023依存の同等Migration |
| `backend/temples/tests/test_highlights_foundation.py` | PR-1のbulk迂回許容テストをDB拒否の回帰テストへ置換 |
| `backend/temples/tests/test_highlights_db_integrity.py` | 正常・異常系、実制約、Migration、ロック、失敗回復 |
| `docs/audit/highlights-db-integrity-verification.sql` | 件数・索引・制約・NOT NULL・不整合のread-only確認SQL |
| 本書 | 選択方式、安全性、結果、未保証事項 |

既存Migrationファイルは一切変更しない。既存のHighlights foundation / location_hint Migration往復テストは、既に後続Migrationを逆順に外して戻せる実装のため変更不要だった。

## 実スキーマとDjango State

3モデルのtableは `temples_shrinehighlight` / `temples_shrinehistory` / `temples_shrinehighlighthistory`。既存PKはbigintのid。関連表のhighlight_id / history_id / shrine_idは既存のNOT NULL FKのまま。既存のPK、単独FK、UNIQUE(highlight_id, history_id)、各FKのindexは削除・置換しない。

| 新規制約名 | 対象と内容 |
| --- | --- |
| `hl_id_shrine_unique` | ShrineHighlight: UNIQUE(id, shrine_id) |
| `history_id_shrine_unique` | ShrineHistory: UNIQUE(id, shrine_id) |
| `hl_history_highlight_shrine_fk` | Link(highlight_id, shrine_id) → Highlight(id, shrine_id) |
| `hl_history_history_shrine_fk` | Link(history_id, shrine_id) → History(id, shrine_id) |

全名称は63bytes以内。複合FKは `ON UPDATE NO ACTION / ON DELETE NO ACTION / NOT DEFERRABLE`、既存行も検証してからcommitする。関連先のshrine_id変更も即時拒否する。これらはORMのon_delete宣言を変更せず、DBの参照整合性を追加するもの。

複合FKをDBだけのRunSQLとして隠さず、`CompositeForeignKey(BaseConstraint)`をModel.MetaとAddConstraintに保持する。constraint_sql/create_sql/remove_sql/validate、deconstruct/clone互換を実装し、makemigrationsで比較可能にした。親参照はhistorical appsから解決する。helperのimport pathは今後もMigration互換のため維持する。PostgreSQL以外のDDLでは明示的に拒否する。[Django 5.2 BaseConstraint](https://docs.djangoproject.com/en/5.2/ref/models/constraints/#baseconstraint)

child側は既存highlight_id / history_id index、およびUNIQUE(highlight_id, history_id)の先頭列で参照先からの検査を支える。今回追加する親側2つのUNIQUE index以外に、既存indexと重複するchild indexは増やさない。実負荷に対する性能保証はしない。

## DDL方式・ロック・失敗時の扱い

採用は**atomic=Trueの直接検証方式**。順序はtimeout設定→Highlight UNIQUE→History UNIQUE→Highlight複合FK→History複合FK。reverseはtimeout設定→両FK削除→両UNIQUE削除。CASCADE削除や既存行の修正・削除は含まない。

両方向で `SET LOCAL lock_timeout='5s'`、`statement_timeout='60s'`を設定する。これはSQLごとの上限であり、Migration全体が60秒以内という保証ではない。transaction終了後に接続設定を残さない。

| 操作 | 根拠・観測 |
| --- | --- |
| UNIQUE追加 | parent表のACCESS EXCLUSIVE。索引作成・検査が終わるまで読取・更新を妨げ得る |
| FK追加と既存行検査 | child・参照先にSHARE ROW EXCLUSIVE。今回のatomic transactionでは先のparent排他ロックもcommitまで保持 |
| reverse | FKを先に外すため参照されるUNIQUEを先にDROPしない。DROPは強いロックを必要とする |
| 競合 | 別接続でHistoryをROW EXCLUSIVEロックすると5秒で失敗。4制約が部分的に残らず、競合解消後に再試行成功 |

ロック種別は[PostgreSQL 17 ALTER TABLE](https://www.postgresql.org/docs/17/sql-altertable.html)を参照し、テスト中のpg_locksでもparent2表のAccessExclusiveLockとchildのShareRowExclusiveLockを確認した。

採用しなかった方式:

- `CREATE UNIQUE INDEX CONCURRENTLY` + UNIQUE USING INDEX: 既存History表が大きい／稼働中なら検討すべき方式。ただしtransaction外の複数段階となり、失敗時の無効index・中間状態・復旧契約が別途必要。今回の小規模隔離検証では全DDL rollbackできる方式を採用した。本番負荷不明のままこの選択を本番向けの最適解と断定しない。
- `ADD ... NOT VALID` → `VALIDATE CONSTRAINT`: 別transactionへ分ければ検証時のロックを軽減できるが、同一atomic transactionでは先行するparent排他ロックを解放できない。今回は完全検証済みの4制約を一括commitする。大規模本番で段階適用が必要なら別設計・母艦承認を要する。
- `IF NOT EXISTS`等による無条件スキップ: 同名で異なる制約・indexのdriftを正常扱いしないため不採用。重複適用はtransactionを失敗させ、元の制約を保持する。ledgerが適用済みなら通常のmigrate再実行はno-op。

失敗時はtransaction全体をrollbackする。既存不整合行がある場合も修復せず失敗し、新UNIQUE/FKを部分的に残さない。Migration ledger、pg_constraint、pg_indexを確認し、ロック・既存不整合・同名objectの原因を特定する。自動データ修復・--fake・制約の強制DROPで先へ進まない。対応方針承認後に再試行する。

## 検証結果と観測範囲

隔離PostgreSQL **17.10** / Django **5.2.17**。通常はPostGIS、NoGISもPostgreSQLを使用。SQLiteで代替しない。

- NoGIS関連回帰: **890 passed**（23.76s）。
- 通常PostGIS関連回帰: **890 passed**（25.87s）。
- 新規DB整合性テストは21ケース（最後のテスト用driver型補足後もNoGIS 21 passed / 通常PostGIS 21 passedを再確認）。複数神社・複数Historyの正常関連、bulk_create / QuerySet.update / SQL INSERT / SQL UPDATE、parent更新、NULL、重複拒否を含む。
- 新規Migrationは両系列とも適用→逆適用→再適用、実制約とStateの照合、失敗時savepoint回復を検証した。既存のcategory6値、review3状態、削除保護、Knowledge、推薦、Action、Meaning、既存Highlights公開判定・APIも回帰対象。
- 別接続のロック競合によるtimeout→全DDL rollback→再試行と、不整合行によるFK検証失敗→全DDL rollbackを検証した。失敗行の除去は隔離テストfixtureのcleanupであり、Migrationにはデータ修復処理を入れていない。
- 通常CLIでもtemples0124→0125→0124→0125を確認し、最後のmigrate0125再実行はNo migrations to apply。
- 専用の空DBでShrine / History / Source / Highlight / Linkは前後とも各0件、不整合0件。非空のfixtureを使う往復試験でも既存Shrine / History / Source件数を比較して不変を確認した。空DBの観測を本番件数やDDL所要時間の推定には使わない。
- 前後SELECTで既存PK・FK index・History(shrine_id, sort_order)を保持し、親の複合UNIQUE index2件がvalidで追加された。新4制約はvalidated=true、deferrable=false。関連3列はNOT NULL。
- 両系列 `makemigrations temples --check --dry-run` はNo changes detected。Django checkは問題なし。Ruff / Black / git diff --check、変更Python7ファイルのAST検査は成功。確認SQLは既存guard.pyのcheck-readonly-sqlでSAFE: ok。

### 型検査の既存指摘

既存backend/mypy.iniを使い、helperとテスト3ファイルは`--check-untyped-defs`を加えて **4 files成功**。変更したmodels_highlights.pyを含む5ファイルも `--disable-error-code=unreachable` を指定して成功した。

標準設定で全5ファイルを検査すると、PR-3から存在する `_invalidate_approval_if_content_changed()` の `if self.pk is None: return` がunreachableと判定される。`git show HEAD:backend/temples/models_highlights.py`をmypyのshadow-fileへ渡した**未変更develop側でも同じ指摘が再現**した。PKを非NULLと扱う型情報と、未保存instanceの実行時状態に関する既存指摘であり、今回の制約追加が導入したものではない。全5ファイルに--check-untyped-defsを加えると、既存pre_deleteのProtectedErrorへ渡すlistに対するstubのset型指摘も出るため、未変更コードの型補修は今回へ混ぜていない。新helper・テスト本体はcheck-untyped-defs付きで検査する。レビュー処理・削除処理や共通設定は変更していない。標準設定で全5ファイルが無警告だったとは報告しない。

### 再現コマンド

以下は専用ローカルDBに限る。通常ユーザーの既存DB・本番資格情報を環境から拾わない。

```sh
export DATABASE_URL=postgres://morietsu@127.0.0.1:55471/highlights_integrity_audit
export DB_NAME=highlights_integrity_audit DJANGO_SECRET_KEY=integrity-test-only PYTHONDONTWRITEBYTECODE=1 USE_SQLITE=0
export GEOS_LIBRARY_PATH=/opt/homebrew/opt/geos/lib/libgeos_c.dylib GDAL_LIBRARY_PATH=/opt/homebrew/opt/gdal/lib/libgdal.dylib

# 同じtest listを両モードで実行。通常: USE_GIS=1 DISABLE_GIS_FOR_TESTS=0
USE_GIS=0 DISABLE_GIS_FOR_TESTS=1 /Users/morietsu/Desktop/jinja_app/.venv/bin/python -m pytest -c backend/pytest.ini -p no:cacheprovider -p no:rerunfailures --override-ini=addopts='' --maxfail=1 --tb=short backend/temples/tests/test_highlights_foundation.py backend/temples/tests/test_highlights_migrations.py backend/temples/tests/test_highlights_db_integrity.py backend/temples/tests/test_highlights_publication_gate.py backend/temples/tests/api/test_shrine_detail_highlights_api.py backend/temples/tests/test_models_shrine_knowledge.py backend/temples/tests/serializers/test_shrine_knowledge_serializers.py backend/temples/tests/api/test_shrine_detail_knowledge_api.py backend/temples/tests/services/test_evidence_gate.py backend/temples/tests/services/test_evidence_gate_detail_display_state.py backend/temples/tests/services/test_shared_recommendation_eligibility.py backend/temples/tests/services/test_culture_translation_primary_attribution_guard.py backend/temples/tests/services/test_action_suggestion_grounding_alignment.py backend/temples/tests/test_shrine_meaning_composer.py backend/temples/tests/api/test_shrine_feature_words_en.py

USE_GIS=1 DISABLE_GIS_FOR_TESTS=0 /Users/morietsu/Desktop/jinja_app/.venv/bin/python backend/manage.py check
USE_GIS=1 DISABLE_GIS_FOR_TESTS=0 /Users/morietsu/Desktop/jinja_app/.venv/bin/python backend/manage.py makemigrations temples --check --dry-run
USE_GIS=0 DISABLE_GIS_FOR_TESTS=1 IS_PYTEST=1 /Users/morietsu/Desktop/jinja_app/.venv/bin/python backend/manage.py makemigrations temples --check --dry-run

# 通常系列の隔離DBのみ。0124で前のsnapshot、0125で後のsnapshotを採取。
USE_GIS=1 DISABLE_GIS_FOR_TESTS=0 /Users/morietsu/Desktop/jinja_app/.venv/bin/python backend/manage.py migrate temples 0124 --noinput
USE_GIS=1 DISABLE_GIS_FOR_TESTS=0 /Users/morietsu/Desktop/jinja_app/.venv/bin/python backend/manage.py migrate temples 0125 --noinput
/opt/homebrew/opt/postgresql@17/bin/psql -X -v ON_ERROR_STOP=1 -h 127.0.0.1 -p 55471 -d highlights_integrity_audit -f docs/audit/highlights-db-integrity-verification.sql

/Users/morietsu/Desktop/jinja_app/.venv/bin/ruff check --config backend/pyproject.toml backend/temples/constraints_highlights.py backend/temples/models_highlights.py backend/temples/tests/test_highlights_db_integrity.py backend/temples/tests/test_highlights_foundation.py
/Users/morietsu/Desktop/jinja_app/.venv/bin/black --check backend/temples/constraints_highlights.py backend/temples/models_highlights.py backend/temples/tests/test_highlights_db_integrity.py backend/temples/tests/test_highlights_foundation.py backend/temples/migrations/0125_highlights_same_shrine_integrity.py backend/temples/migrations_nogis/0024_highlights_same_shrine_integrity.py
git diff --check
/Users/morietsu/Desktop/jinja_app/.venv/bin/python scripts/migration_safety/guard.py check-readonly-sql docs/audit/highlights-db-integrity-verification.sql
```

backendで上記のlocal環境変数を明示して実行する型検査:

```sh
/Users/morietsu/Desktop/jinja_app/backend/.venv/bin/python -m mypy --config-file mypy.ini --check-untyped-defs temples/constraints_highlights.py temples/tests/test_highlights_db_integrity.py temples/tests/test_highlights_foundation.py temples/tests/test_highlights_migrations.py
/Users/morietsu/Desktop/jinja_app/backend/.venv/bin/python -m mypy --config-file mypy.ini --disable-error-code=unreachable temples/constraints_highlights.py temples/models_highlights.py temples/tests/test_highlights_db_integrity.py temples/tests/test_highlights_foundation.py temples/tests/test_highlights_migrations.py
```

## 本番Gate・未保証事項

本番の件数・indexサイズ・負荷・lock待ち・所要時間・Migration ledgerは**未確認**。空DBおよび小規模fixtureの成功だけで本番DDLを承認しない。Fresh Backup、Isolated Restore、実データ規模のcloneでの時間・ロック検証、read-only前後snapshot、対象Migration限定の母艦承認が揃うまでHOLDする。既存runbookの過去Migration用SQLを今回用として流用しない。

前検証で不整合が1件でもある、想定外の同名制約・index、通常／NoGIS lineage混在、検証時間・lock budget超過があればSTOP。大規模運用でCIC・段階VALIDATEが必要なら、今回のatomic方式を無断で本番適用せず別途設計を判断する。

直接SQLによるpublished/archivedの状態依存DELETE保護は別課題のまま。子relationがないpublished行のSQL DELETEを阻止するtriggerは今回も追加していない。新FKの参照整合性を削除保護全般の完成とは宣言しない。

PR-3〜5の既存コードは変更していない。後続のデータ作成・更新経路も同一神社条件を満たす必要があり、迂回時にはDBで拒否される。公開・UIの新仕様追加、マージ、デプロイ、本番Migrationは対象外。
