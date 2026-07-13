> **Status: Archive**
>
> 本ドキュメントは、本番環境で`temples_featureusage`テーブルが欠損した際に実施した手動復旧の記録である。
>
> 記載されているSQLおよび復旧手順は当時のDatabase構造を前提としたスナップショットであり、現行の復旧手順として使用しない。
>
> 現在のFeatureUsage Model・Migration・修復処理は、以下のコードと現行文書を正本とする。
>
> - `backend/temples/models_usage.py`
> - `backend/temples/migrations/0077_featureusage.py`
> - `backend/temples/migrations/0081_recreate_featureusage_if_missing.py`
> - `backend/temples/migrations/0082_force_recreate_featureusage_table.py`
> - `backend/temples/management/commands/repair_featureusage_table.py`
> - `backend/start.sh`
> - `docs/infra/render-startup.md`
> - `docs/migration-audit/temples-prod-gap.md`

# Render本番FeatureUsage復旧記録

## 目的

本番環境に`FeatureUsage` Modelを利用するコードが反映された一方で、Databaseに対応テーブルが存在しなかった障害について、事象・原因・当時の復旧判断を保存する。

本書はインシデント履歴として保持し、現在の運用Runbookとしては使用しない。

---

## 発生した事象

障害発生時には、以下の状態が確認された。

- `/healthz/`は正常に応答した
- 神社一覧APIは正常に応答した
- Plan関連APIは正常だった
- Concierge Chat APIのみServer Errorとなった

Application全体が停止していたのではなく、`FeatureUsage`を利用する処理に限って障害が発生していた。

---

## 原因

当時の原因は、Application CodeとProduction Databaseの状態不一致だった。

```text
FeatureUsageを参照するCode
↓
本番へDeploy済み

temples_featureusage
↓
本番Databaseに存在しない
```

Migration履歴と実際のDatabase Tableが一致しておらず、Applicationが存在しないTableを参照したことでErrorが発生した。

---

## 当時確認した項目

障害調査では、以下を確認した。

- `django_migrations`に記録されたMigration履歴
- Production Databaseに存在する`temples_*` Table
- `temples_featureusage`の有無
- Concierge Chat APIの応答
- Health Check APIの応答
- Shrine APIの応答

これにより、Application全体の障害ではなく、FeatureUsage Table欠損による局所的な障害と判断した。

---

## 当時の応急対応

当時はProduction Databaseへ直接SQLを適用し、以下を手動で補完した。

- `temples_featureusage` Table
- UserへのForeign Key
- Scope・Feature用Index
- User・Feature用Index
- Anonymous ID・Feature用Index
- User単位のUnique制約
- Anonymous単位のUnique制約
- Scopeと対象の整合を担保するCheck制約

この対応によってApplicationは復旧した。

手動SQLの具体的な内容は当時のDatabase構造へ依存するため、本書では現行の復旧手順として保持しない。

---

## 復旧確認

応急対応後は、以下を確認した。

- `temples_featureusage` Tableが存在する
- 必要なIndexが存在する
- 必要なConstraintが存在する
- Concierge Chat APIが正常応答する
- Recommendation Responseが返る
- FeatureUsageの保存処理が動作する

これらの確認後、Applicationは復旧済みと判断した。

---

## 恒久対応への移行

手動復旧後、FeatureUsage Tableの作成・修復処理はコード側へ移された。

### Migration

FeatureUsageの作成および欠損時の再作成を扱うMigrationが追加された。

現行のMigration依存関係と適用状況は、`backend/temples/migrations/`とProduction Databaseの`django_migrations`を正本とする。

### 修復コマンド

FeatureUsage Tableを修復する管理コマンドが追加された。

```text
python manage.py repair_featureusage_table
```

このコマンドは、Table・Indexなどの必要構造を現在のコードに基づいて確認・補完するためのものである。

現在の正確な処理内容は以下を正本とする。

- `backend/temples/management/commands/repair_featureusage_table.py`

### 起動時制御

Backend起動時のFeatureUsage修復は、環境変数で明示的に制御する。

```text
RUN_FEATUREUSAGE_REPAIR_ON_START
```

通常起動では自動修復を実行せず、必要な環境でのみ明示的に有効化する。

現在の起動契約は以下を参照する。

- `backend/start.sh`
- `docs/infra/render-startup.md`

---

## Render環境での扱い

Render環境では、常設Shellを前提とした運用を行わない。

復旧が必要な場合は、以下の順で確認する。

```text
Migration状態
↓
起動処理
↓
修復コマンド
↓
Database状態
```

手動SQLによるTable作成を第一選択にしない。

直接SQLが必要な場合は、現行Model・Migration・Constraintと一致することを確認し、個別の本番対応として扱う。

---

## Migrationとの責務境界

### Migration

- Schema変更
- Table作成
- Index作成
- Constraint作成
- Migration履歴管理

### 修復コマンド

- 欠損Tableの存在確認
- 必要構造の補完
- 過去のDatabase Driftからの復旧補助

### 本書

- 当時の障害内容
- 当時の原因
- 手動復旧を行った判断
- 恒久対応へ移行した経緯

---

## 現行運用で使用しないもの

以下は、現在の通常運用手順として使用しない。

- 本書に記録された固定SQLによるTable作成
- 当時のIndex名を前提とした直接作成
- 当時のConstraint定義の無条件適用
- Migration履歴を確認しない手動補完
- Application Codeと異なるSchemaの作成

現在のDatabase Schemaは、Model・Migration・修復コマンドを基準とする。

---

## 現行仕様との責務境界

### 本書が保持するもの

- FeatureUsage Table欠損障害の事象
- Migration履歴と実Tableの不整合
- 当時の手動復旧判断
- 復旧確認の観点
- 恒久対応へ移行した背景

### 本書が扱わないもの

- 現在のFeatureUsage Schema
- 現在のIndex定義
- 現在のConstraint定義
- 現在のMigration適用状況
- 現在のRender設定
- 現在の起動手順
- 現在の本番復旧手順
- SQL実行の作業指示
- Migration適用計画
- 開発タスク

---

## 関連実装・文書

### 現行実装

- `backend/temples/models_usage.py`
- `backend/temples/migrations/0077_featureusage.py`
- `backend/temples/migrations/0081_recreate_featureusage_if_missing.py`
- `backend/temples/migrations/0082_force_recreate_featureusage_table.py`
- `backend/temples/management/commands/repair_featureusage_table.py`
- `backend/start.sh`

### 現行運用

- `docs/infra/render-startup.md`

### Migration履歴

- `docs/migration-audit/temples-prod-gap.md`

---

## 更新ルール

- 本書はFeatureUsage障害と手動復旧の履歴として保持する
- 現行Schema・Migration・Render設定の変更に合わせて更新しない
- 当時の事象や原因に重大な事実誤認が確認された場合のみ修正する
- SQL手順、TODO、復旧タスク、Migration計画、作業進捗は記載しない
