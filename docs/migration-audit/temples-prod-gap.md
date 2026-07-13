> **Status: Archive**
>
> 本ドキュメントは、2026年3月時点における本番DatabaseとDjango Migration履歴の差分を調査した監査記録である。
>
> 記載されているTable一覧・Migration適用状況・修復対象・`--fake`判断は監査時点のスナップショットであり、現行のSchema判断や本番復旧手順には使用しない。
>
> 現在のModel・Schema・Migration・修復処理は、以下を正本とする。
>
> - `backend/temples/models.py`
> - `backend/temples/models_usage.py`
> - `backend/temples/migrations/`
> - `backend/temples/management/commands/repair_featureusage_table.py`
> - `backend/start.sh`
> - Production Databaseの`django_migrations`
> - Production Databaseの実Table・Index・Constraint
> - `docs/infra/render-startup.md`
>
> FeatureUsage障害の手動復旧履歴は、`docs/runbooks/render-featureusage-recovery.md`を参照する。

# Temples Migration本番差分監査

## 目的

本番Databaseの実体とDjango Migration履歴が一致していなかった時点において、差分・リスク・修復単位を調査した記録である。

本書は、Database Driftの発生状況と調査過程を保存するArchive文書として扱う。

---

## 監査時点の背景

監査時点では、Django上でMigration適用済みと記録されている一方、本番Databaseに対応Tableが存在しない、または手動作成されたTableが存在する状態が確認された。

```text
django_migrations
↓
適用済みと記録

Production Database
↓
一部Tableが存在しない
または手動補完されている
```

この不一致により、以下のリスクがあった。

- `migrate`実行時の重複作成
- Migration履歴だけが進んだ状態
- Rollback不能
- ModelとDatabase Schemaの乖離
- 未使用機能を呼び出した際のServer Error
- Database Driftの拡大

---

## FeatureUsageで確認された差分

監査時点では、`FeatureUsage`を参照するApplication Codeが本番へ反映されていた一方、対応TableがMigrationから正常に作成されていなかった。

そのため、当時は以下の対応が行われた。

- `temples_featureusage`の手動作成
- 必要なIndex・Constraintの手動補完
- Migration履歴の`--fake`適用
- Concierge Chat APIの復旧確認

この対応は障害復旧時の一時的な措置であり、現行運用では固定SQLによる手動作成を第一選択にしない。

現在のFeatureUsage構造は、Model・Migration・修復コマンドを正本とする。

---

## ローカル空Databaseによる比較

監査では、ローカルDatabaseを空の状態からMigrationで再構築し、生成された`temples_*` Tableを本来の再現結果として利用した。

```text
空Database
↓
python manage.py migrate
↓
生成Table一覧
↓
Production Databaseと比較
```

この比較により、Migration履歴上は存在するはずだが、本番Databaseでは存在しないTable候補を抽出した。

ローカル再構築結果と本番状態はいずれも監査時点の情報であり、現在のTable一覧としては使用しない。

---

## 当時の修復単位

差分Tableは、機能依存と修復リスクに基づいて以下の単位へ分類された。

### 基盤Table

神社・御祭神・ご利益・参拝など、他機能の土台となるTable。

### 神社関連の補助Table

神社と分類・候補情報を接続する中間Table。

### Concierge系Table

相談・会話・推薦・利用回数など、Concierge機能に関係するTable。

### User Interaction系Table

御朱印・Favorite・Like・Rankingなど、ユーザー操作に関係するTable。

### 収集・Cache系Table

外部情報収集・Cache・Seed処理など、運用補助に関係するTable。

この分類はDjango Modelの正式なDomain分類ではなく、当時の本番整合回復を安全に分割するための運用上の分類だった。

---

## 当時の修復判断

監査時点では、以下の原則が採用された。

- 本番主機能に直結する差分を優先する
- 一度に複数のTableを手動修復しない
- `--fake`は実Table・Column・Index・Constraintを確認した場合に限定する
- 手動補完は障害に直結し、Schema定義が明確な場合に限定する
- 全面再構築は最終手段とする
- 補助的なAnalytics Tableは主機能と分離する

これらは当時のDatabase状態に対する判断であり、現在の修復順序を規定するものではない。

---

## Concierge系Tableの調査

監査では、Conciergeに関連するTableについて、以下を個別に確認した。

- Table実体
- Column
- Index
- Foreign Key
- Constraint
- Migration履歴
- Application Codeからの参照
- API・Serializer・Frontendとの接続
- 保存処理の有無

一部Tableについては、調査の進行に伴って判定が変更された。

特に、ModelやAPI定義の存在と、実際の保存処理・本番主機能での必要性が一致しないケースが確認された。

このため、本書内の当時の途中判定は現行仕様として採用せず、現在のコードとDatabaseを再確認する。

---

## 調査過程で確認された問題

### Migrationはあるが本番Tableがない

Migration履歴上は適用済みでも、実Tableが存在しない状態があった。

### ModelはあるがMigrationがない

Model定義が存在しても、空Databaseから再現できないTable候補があった。

### 定義はあるが実行コードから利用されない

API・Serializer・Modelなどの定義だけが残り、主導線から利用されていない可能性がある機能があった。

### Tableはあるが保存経路が不明

AnalyticsやClick Logなど、Table・Modelが存在しても、実際の保存処理が確認できないケースがあった。

これらは一律に手動修復せず、機能要否・Migration・実行経路を確認してから判断する方針だった。

---

## 恒久対応への移行

監査後、FeatureUsageについてはMigrationおよび専用修復コマンドが追加された。

### Migration

現在のMigration依存関係とSchema定義は、以下を正本とする。

```text
backend/temples/migrations/
```

### 修復コマンド

FeatureUsage Tableの欠損確認と補完には、専用の管理コマンドが用意された。

```text
python manage.py repair_featureusage_table
```

正確な処理内容は以下を正本とする。

```text
backend/temples/management/commands/repair_featureusage_table.py
```

### 起動時制御

起動時の修復処理は、`backend/start.sh`と環境変数によって明示的に制御する。

現行契約は以下を参照する。

- `backend/start.sh`
- `docs/infra/render-startup.md`

---

## 現行の確認順序

Database差分を調査する場合は、固定された過去のTable一覧ではなく、以下を基準に確認する。

```text
現在のModel
↓
現在のMigration
↓
django_migrations
↓
実Table
↓
Column・Index・Constraint
↓
Application Codeの参照
↓
API・Test
```

Production Databaseへの直接変更は、現行Model・Migrationとの一致を確認したうえで、個別の復旧対応として扱う。

---

## 手動SQLとの責務境界

### Migrationが担当するもの

- Schema変更
- Table作成
- Column追加・変更
- Index作成
- Constraint作成
- Migration履歴管理

### 修復コマンドが担当するもの

- 過去のDatabase Drift確認
- 欠損Tableの補完
- 必要構造の存在確認
- 限定的な復旧補助

### 手動SQL

通常運用の第一選択にしない。

手動SQLが必要な場合は、以下を確認する。

- 現行Modelとの一致
- 現行Migrationとの一致
- 既存Table・Columnの存在
- Index・Constraintの重複
- Rollback方法
- Backup
- 適用後のAPI・Test

---

## 本書が保持するもの

- 本番DatabaseとMigration履歴に差分があった事実
- FeatureUsageを手動補完した背景
- 空Database再構築との比較方法
- Tableを修復単位へ分類した考え方
- `--fake`や手動補完を限定した判断
- 調査途中で判定が変化した経緯
- 恒久対応へ移行した背景

---

## 本書が扱わないもの

- 現在のProduction Table一覧
- 現在のMigration適用状況
- 現在の欠損Table
- 現在の修復対象
- 現在の修復順序
- 現在のModel要否
- 現在のAPI利用状況
- 現在のIndex・Constraint
- 本番SQLの実行指示
- `--fake`適用指示
- Migration計画
- TODO
- PR候補
- 作業進捗

---

## 関連実装・文書

### 現行Schema

- `backend/temples/models.py`
- `backend/temples/models_usage.py`
- `backend/temples/migrations/`

### FeatureUsage修復

- `backend/temples/management/commands/repair_featureusage_table.py`
- `backend/start.sh`
- `docs/infra/render-startup.md`

### 障害履歴

- `docs/runbooks/render-featureusage-recovery.md`

---

## 更新ルール

- 本書は2026年3月時点の本番Migration差分監査記録として保持する
- 現行Model・Migration・Production Databaseの変更に合わせて更新しない
- 当時の事象や調査内容に重大な事実誤認が確認された場合のみ修正する
- 現在の修復手順、SQL、TODO、PR候補、Migration計画、作業進捗は記載しない
