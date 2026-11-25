# Highlights Model Foundation（PR-1）

> Status: Audit / Historical — PR-1実装・検証記録。公開許可・本番適用許可ではない。
> 日付: 2026-11-21 JST
> Base: develop `eabea1da312bc254cdf49bc2d388f5ec0a0cc2e1`
> Branch: `feature/highlights-model-foundation`

## 対象と変更

母艦承認済みのC案とPR-1再開条件に従い、4モデルと通常制約、管理画面、テストを追加した。PR-2以降の複合外部キー・Publication Gate・API・表示接続は含まない。最新developをfetchして確認し、既存変更のある元workspaceとは別のworktreeで実装した。

| ファイル | 責務 |
| --- | --- |
| `backend/temples/models_highlights.py` | ShrineHighlight / ShrineHighlightTranslation / ShrineHighlightSource / ShrineHighlightHistory、検証・通常DB制約・ORM削除保護 |
| `backend/temples/models.py` | 末尾で新4モデルを登録。既存モデル定義は変更しない |
| `backend/temples/admin_highlights.py` | 4モデルのAdmin登録、非draftの個別削除権限を拒否 |
| `backend/temples/admin.py` | 新Adminモジュールの読み込みのみ |
| `backend/temples/migrations/0123_highlights_model_foundation.py` | 通常系列の新規schema migration |
| `backend/temples/migrations_nogis/0022_highlights_model_foundation.py` | NoGIS系列の同等schema migration |
| `backend/temples/tests/test_highlights_foundation.py` | 保存・通常DB制約・Adminを含む削除経路・PR-1の保証限界 |
| `backend/temples/tests/test_highlights_migrations.py` | 両系列のoperation一致、State一致、適用・逆適用・再適用、既存テーブル件数不変 |
| 本書 | 仕様対応・検証・残る境界 |

### Fieldと通常制約

- `ShrineHighlight`: Shrine FK、全神社を通じ一意のstable_key、固定カテゴリーcategory、非負sort_order、verification_status、confidence、verified_at、publication_status、created_at / updated_at。
- `ShrineHighlightTranslation`: Highlight FK、ja/en限定language_code、name、description、historical_connection、review_status、reviewed_at、created_at / updated_at。UNIQUE(highlight, language_code)。説明2項目は下書き段階で空を許可する。公開要件としての説明の非空確認はPR-3の責務。
- `ShrineHighlightSource`: Highlight FKとShrineKnowledgeSource FK。UNIQUE(highlight, source)。Source側はPROTECT。
- `ShrineHighlightHistory`: Highlight FKとShrineHistory FK、NOT NULLのShrine FK。UNIQUE(highlight, history)。History側はPROTECT。clean/saveでHighlight・History・指定Shrineの同一性を確認。

categoryは母艦決定により**固定カテゴリー・最大50文字**。Highlights専用のTextChoicesを持ち、`GoriyakuTag`のchoices・意味とは共通化しない。長さ50は当初実装の上限を維持する。stable_keyと翻訳nameは既存Knowledgeのstable_key / title / display_nameに合わせ最大255文字。statusは既存のverification_status（32文字）とconfidence（8文字）を再利用し、publication / translation reviewは必要な値が収まる16文字とした。

### 母艦決定：category仕様整合修正

当初の自由文字列方式は、今回の母艦決定によって固定カテゴリーへ置き換えた。許可値を指定された6種類に限定するための修正であり、自由文字列方式は現行仕様として採用しない。新たなカテゴリーの推測追加やGoriyakuTagとの共通化は行わない。

許可値は `architecture` / `cultural_heritage` / `nature` / `ritual_festival` / `historical_site` / `experience` の6種類のみ。

Djangoでは `ShrineHighlight.Category`（TextChoices）をcategory.choicesに指定し、DBでは `hl_category_valid` CHECKで同じ6値に限定する。max_length=50と既存 `hl_category_not_blank` CHECKは維持。両MigrationのCreateModel状態・追加CHECKを一致させる。6値の保存成功6ケース、未定義値のDjango validation・bulk_create・QuerySet.update拒否12ケースを追加し、既存の空白・一意性・日時整合・削除保護テストを維持した。

公開状態は `draft / published / archived`（default draft）、翻訳reviewは `draft / approved / rejected`（default draft）。確認状態source_confirmed/reviewedにはverified_at、翻訳approvedにはreviewed_atを要求する。言語・状態語彙・confidence・非空白・日時整合・一意性はDB制約でも確認する。通常saveはHighlight / Translation / History linkでfull_cleanする。

空白検査はPythonのstripとPostgreSQLの照合順序による差を避けるため、Unicode空白を明示的に除外した正規表現をDB CHECKに使用。全角空白・NBSPもPostgreSQLの直接更新テストで拒否を確認する。既存モデルのvalidatorや制約は変更していない。

## 削除の保証範囲

`ShrineHighlight`のpre_delete receiverは、Django Collectorの削除transaction内で行をselect_for_updateし、**現在DBに保存されている状態**がdraft以外ならProtectedErrorを返す。古いmodel instanceがdraftを保持していても、保存済み状態がpublished/archivedなら削除しない。

| 経路 | 保証・テスト |
| --- | --- |
| model.delete | published/archivedを拒否。draftを削除可能 |
| QuerySet.delete / Admin.delete_queryset | 非draftを拒否。混在batchはdraftも含め全体rollback |
| Admin個別画面 / delete_selected | 個別削除権限と一括削除actionで拒否。HTTP POSTも403を検証 |
| ShrineからのORM cascade | 非draft Highlightを含む削除を拒否。既存モデルのFK/on_delete宣言は変更していない |
| Source / History削除 | 新しい関連がある場合PROTECT。関連がない既存Source/Historyは従来どおり削除可能 |
| draft Highlight削除 | 翻訳・Source link・History linkはCASCADE。参照先Source / Historyそのものを削除する指定ではない |

新しいPROTECT relationのため、同時に削除しようとする神社配下に関連Historyがある場合も、そのHistoryの削除は保護され得る。これは既存モデルの削除宣言を書き換えた結果ではなく、新たな参照関係による保護である。

**DBだけでは保証しない範囲:** 状態依存DELETE triggerは追加していない。子を持たないpublished行の直接SQL DELETEは成功し得ることを明示的にテストする。signalを通らないprivate ORM経路・historical model・raw SQLでも同じ保証はない。状態遷移自体を固定するworkflowは本PRに含まれず、削除判定は削除直前の永続状態に対するもの。運用上の公開・アーカイブ手順の代替ではない。

関連Historyの同一神社性はアプリ検証であり、bulk_create / QuerySet.update / 親Shrineの変更 / raw SQLまでDBで強制しない。bulk_createがcleanを迂回できることもテストして、PR-2の複合FK保証を実装済みと誤認しないようにした。通常のFKとUNIQUEだけでPR-2完了とはしない。

## Migrationの安全境界

実装前に依存関係を確認したHeadは通常 `0122_shrine_feature_word_en`、NoGIS `0021_shrine_feature_word_en`。それぞれを親として新規Migrationを1件ずつ追加した。今回のcategory整合修正では、この未マージのPR-1追加Migration 2件だけを更新した。developに存在するMigrationは編集していない。

category修正前の安全確認（2026-11-21 JST）:

- GitHub PR #3504はopen・未マージ、headは `1a5f6e4508e9e68f3ce9e21addb460701897d095`。fetch後もリモートとの追加差分は0。
- GitHub Deployments APIには当該headのVercel Preview（deployment `7960515564`）が存在したため調査した。Vercel deployment `dpl_FJjWaoAWP9tZ9phsXhSh1r2qMy8f` は `jinja-app-web` / Next.jsであり、buildログは `/vercel/path0/apps/web` の `pnpm run build` → `next build`。確認したログにDjango migrateはない。Preview公開とDB Migration適用を同一視していない。
- 前回のローカル適用は破棄されるpytestテストDBのみ。専用クラスタを再起動し、`highlights_local` の `to_regclass('public.django_migrations')` がNULL、DB一覧がhighlights_local/postgresのみで、残存テストDBがないことを確認した。
- `.github/workflows/backend-tests.yml` は一時的なPostgreSQL service上のpytest。リポジトリのdeploy workflowは無効ファイル。確認可能な範囲で、永続DBへ本2件を適用した証拠はない。本番DBには接続していない。記録外の手動適用まで不存在と断定しない。
- 他環境の永続DBに適用済み・その可能性を示す追加証拠が判明した場合は、この2件の書き換え方式を継続せずSTOPする。

確認した読み取りコマンド: `git fetch origin develop feature/highlights-model-foundation`、`git rev-list --left-right --count HEAD...origin/feature/highlights-model-foundation`、`gh api 'repos/etsu33/jinja_app/deployments?sha=1a5f6e4508e9e68f3ce9e21addb460701897d095'`、`gh api repos/etsu33/jinja_app/deployments/7960515564/statuses`。Vercel metadata / build eventsも接続ツールで読み取り確認した。

両Migrationは同じCreateModel / AddConstraint operationを持ち、既存テーブルのAlterField・data migration・RunSQLは含まない。新4テーブルの期待初期件数は0。FKにはDjango既定のindexが生成される。UNIQUE(id, shrine_id)・複合FK・そのSQLはPR-2まで追加しない。

テストは**専用ローカルPostgreSQL 17.10、127.0.0.1:55471**のみ。クラスタは `/private/tmp/jinja-highlights-pg17` に新規作成し、他のDB設定・既存神社データには触れていない。通常系列はPostGISを使用。テストDB生成時に既存系列も適用したうえで、新Migrationの適用・逆適用・再適用を検証した。逆適用は新4テーブルを破棄するため、本番データ投入後の安全なrollback許可を意味しない。

## 検証コマンド

実装worktree `/private/tmp/jinja-highlights-foundation` で実行。以下のsecretはテスト専用の固定値で、本番認証情報ではない。

```sh
export DATABASE_URL=postgres://morietsu@127.0.0.1:55471/highlights_local
export DB_NAME=highlights_local DJANGO_SECRET_KEY=highlights-local-test-only PYTHONDONTWRITEBYTECODE=1 USE_SQLITE=0
export GEOS_LIBRARY_PATH=/opt/homebrew/opt/geos/lib/libgeos_c.dylib GDAL_LIBRARY_PATH=/opt/homebrew/opt/gdal/lib/libgdal.dylib

USE_GIS=0 DISABLE_GIS_FOR_TESTS=1 /Users/morietsu/Desktop/jinja_app/.venv/bin/python -m pytest -c backend/pytest.ini -p no:cacheprovider -p no:rerunfailures --override-ini=addopts='' --maxfail=1 --tb=short backend/temples/tests/test_highlights_foundation.py backend/temples/tests/test_highlights_migrations.py backend/temples/tests/test_models_shrine_knowledge.py backend/temples/tests/serializers/test_shrine_knowledge_serializers.py backend/temples/tests/api/test_shrine_detail_knowledge_api.py backend/temples/tests/services/test_evidence_gate.py backend/temples/tests/services/test_evidence_gate_detail_display_state.py backend/temples/tests/services/test_shared_recommendation_eligibility.py backend/temples/tests/services/test_culture_translation_primary_attribution_guard.py backend/temples/tests/services/test_action_suggestion_grounding_alignment.py backend/temples/tests/test_shrine_meaning_composer.py backend/temples/tests/api/test_shrine_feature_words_en.py

USE_GIS=1 DISABLE_GIS_FOR_TESTS=0 /Users/morietsu/Desktop/jinja_app/.venv/bin/python -m pytest -c backend/pytest.ini -p no:cacheprovider -p no:rerunfailures --override-ini=addopts='' --maxfail=1 --tb=short backend/temples/tests/test_highlights_foundation.py backend/temples/tests/test_highlights_migrations.py backend/temples/tests/test_models_shrine_knowledge.py backend/temples/tests/serializers/test_shrine_knowledge_serializers.py backend/temples/tests/api/test_shrine_detail_knowledge_api.py backend/temples/tests/services/test_evidence_gate.py backend/temples/tests/services/test_evidence_gate_detail_display_state.py backend/temples/tests/services/test_shared_recommendation_eligibility.py backend/temples/tests/services/test_culture_translation_primary_attribution_guard.py backend/temples/tests/services/test_action_suggestion_grounding_alignment.py backend/temples/tests/test_shrine_meaning_composer.py backend/temples/tests/api/test_shrine_feature_words_en.py

USE_GIS=1 DISABLE_GIS_FOR_TESTS=0 /Users/morietsu/Desktop/jinja_app/.venv/bin/python backend/manage.py check
USE_GIS=1 DISABLE_GIS_FOR_TESTS=0 /Users/morietsu/Desktop/jinja_app/.venv/bin/python backend/manage.py makemigrations temples --check --dry-run
USE_GIS=0 DISABLE_GIS_FOR_TESTS=1 IS_PYTEST=1 /Users/morietsu/Desktop/jinja_app/.venv/bin/python backend/manage.py makemigrations temples --check --dry-run

/Users/morietsu/Desktop/jinja_app/.venv/bin/ruff check --config backend/pyproject.toml backend/temples/models_highlights.py backend/temples/admin_highlights.py backend/temples/tests/test_highlights*.py
/Users/morietsu/Desktop/jinja_app/.venv/bin/black --check backend/temples/models_highlights.py backend/temples/admin_highlights.py backend/temples/tests/test_highlights*.py backend/temples/migrations/0123_highlights_model_foundation.py backend/temples/migrations_nogis/0022_highlights_model_foundation.py
git diff --check
```

型検査は `backend/` で実行:

```sh
DATABASE_URL=postgres://morietsu@127.0.0.1:55471/highlights_local DB_NAME=highlights_local DJANGO_SECRET_KEY=highlights-local-test-only USE_GIS=0 DISABLE_GIS_FOR_TESTS=0 PYTHONDONTWRITEBYTECODE=1 /Users/morietsu/Desktop/jinja_app/backend/.venv/bin/python -m mypy --config-file mypy.ini temples/models_highlights.py temples/admin_highlights.py temples/tests/test_highlights_foundation.py temples/tests/test_highlights_migrations.py
```

### 結果

- NoGIS PostgreSQL回帰: **824 passed**（14.60s）。Knowledge、Detail API、Evidence Gate、Shared Eligibility、culture translation、Action、Meaning Composer、英語特徴語を含む。
- 通常PostGIS: 関連回帰 **824 passed**（新規105ケースを含む）。両系列のoperations往復、空テーブル生成、既存Shrine / History / Source件数不変を含む。
- 両系列makemigrations: No changes detected。Django system check、Ruff、Black、git diff --check成功。
- mypy: Django pluginを使う既存backend/mypy.iniで新規4ファイルを検査し成功。最初のroot .venvでの直接検査はdjango-stubs 1.9.0の古い型定義でエラーとなったため、既存backend .venv（mypy 2.3.0 / django-stubs 6.0.9）と既存設定で再検証した。依存ファイルは変更していない。
- 初回の単体テストではProtectedError後のtransactionをテスト側でsavepointに分離できておらず失敗した。テストを修正し、最終回帰で再検証した。

## 非干渉と残るSTOP条件

本番DBのDDL/DML/migrate、Supabase接続、既存神社データ・Google Sheets・本番環境変数の変更は行っていない。seed・架空の見どころ・自動生成文章も追加していない。既存モデルの列、既存serializer / API / URL、travel_ranking、Evidence Gate、Meaning Composer、英語特徴語は変更していない。新モデルを既存の推薦入力へ接続しない。

PR-1の未解決の仕様判断はない。公開可能性、翻訳変更時のreview無効化、複合FK、API、UI、本番Migration Gateは未実装であり、PR-1の成功から後続PRの開始・マージ・デプロイ・本番適用を承認しない。直接SQL等の削除保護や同一神社DB強制までPR-1の完了条件に追加する場合は、現在の承認範囲と異なるためSTOPして仕様を再確認する。

コミットメッセージ: `feat: 神社Highlightsのモデル基盤と削除保護を追加`

category修正の追加コミットメッセージ: `fix: Highlightsカテゴリーを母艦承認の6種類に限定`

## 母艦決定：翻訳レビュー状態（3状態）

母艦は `ShrineHighlightTranslation.review_status` に **B案（`draft` / `approved` / `rejected`）** を正式採用することを決定した。従前の4状態案（`draft` / `in_review` / `approved` / `needs_revision`）は採用しない。

| 状態 | 意味 | 一般公開判定 |
| --- | --- | --- |
| `draft` | 新規作成中・レビュー待ち・修正中 | 不可 |
| `approved` | 翻訳内容のレビュー完了 | 候補（Highlight本体のPublication GateとEvidence Gateの通過が別途必要） |
| `rejected` | 公開対象として不採用 | 不可 |

- `draft` を既定値とし、単なる修正依頼を `rejected` と同義にしない。
- `approved` には `reviewed_at` を必須とする。Django Choices・DB CHECK `hl_review_valid` / `hl_reviewed_at_required` は現行実装を維持する。
- 承認済み翻訳の `name`・`description`・`historical_connection` を変更した場合の承認失効（`draft`へ戻すこと、`reviewed_at` のクリア、更新経路の保護）は **PR-3 Publication Gateで実装・検証する未完了要件**。PR-1で実装済みとは扱わない。
- 本決定は仕様と監査記録の整合のみ。モデル、Migration、既存API、推薦、Meaning Composer、本番DBを変更しない。

