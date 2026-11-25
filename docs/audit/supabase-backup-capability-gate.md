> **Status: Active — Phase 0完了、Phase 1/2はSTOP（Supabase Dashboard接続経路なし）、
> Phase 3-6はSupabase公開ドキュメントに基づく設計のみ（実行はしていない）、
> Phase 7分類は`BACKUP_CAPABILITY_UNKNOWN`**
>
> 本ドキュメントはmigration実行前のbackup体制監査の記録である。
> **Production DBへは一切接続していない。INSERT/UPDATE/DELETE/ALTERは
> 一切行っていない。restoreも実行していない。Environment変更も
> 一切していない。**

# Supabase Backup Capability Gate

## Phase 0 — Base State固定

| 項目 | 結果 |
|---|---|
| develop最新化 | 完了（fast-forward `e3584daf..b286a557`） |
| working tree | clean |
| develop HEAD SHA | `b286a557...`（PR #2323のsquash merge commit） |
| Production users latest migration | `0005`（Mother Ship提供値） |
| Production temples latest migration | `0089`（Mother Ship提供値） |
| `users 0006` local safety | **PASS**（`docs/audit/production-all-app-migration-state-audit.md`実測。`AddField`×4のみ、既存データ保持、rollback成功） |
| `temples 0090-0093` local safety | **PASS**（`docs/audit/production-migration-0090-0093-safety.md`実測。`SAFE_SEQUENTIAL_MIGRATION`確定） |
| Production runtime schema mismatch | **確認済み**（`users/apps.py`の`ensure_profile`signalが、schemaが`users 0006`未適用の間、新規User作成時に`UndefinedColumn`を送出することをlocal実測で確認済み。詳細は`docs/audit/production-all-app-migration-state-audit.md`） |
| Production DBへの書き込み | **本監査でも一切行っていない** |

---

## Phase 1 / Phase 2 — Supabase Backup Capability確認（STOP: 接続経路なし）

本セッション環境にはSupabase Dashboardへのアクセス手段（ログインセッション・
API key・MCP tool等）が一切存在しない（過去の全Auditと同じ状態。
`docs/audit/production-db-readonly-audit-access-gate.md`・
`docs/audit/render-reality-gate-phase2-stop.md`と同様）。したがって
チェックリストの以下の項目は**すべてMother Shipが直接Dashboardで確認する
必要がある**：

- [ ] Backups画面（Settings → Database → Backups）を開く
- [ ] 現在のプラン（Free/Pro/Team/Enterprise）を確認
- [ ] 自動backup有無・最新backup日時
- [ ] backup保持期間
- [ ] manual backup/export可否（Dashboard上のボタンとして、または要CLI）
- [ ] restore操作がDashboardから可能か
- [ ] restoreがproject全体に及ぶか
- [ ] PITR可否・現在のplanで利用可能か・有効化済みか
- [ ] migration直前時点へ戻せる粒度か

以下のPhase 3〜6は、上記が未確認のまま**Supabase公式ドキュメント
（公開情報、ログイン不要）に基づく一般仕様の調査・設計**として進めた。
`docs/audit/migration-execution-method-reality-audit.md`でRender公開
ドキュメントを調査したのと同じ方法論である。**現在のproject固有の設定
（実際のplan・実際に自動backupが動いているか等）は依然として未確認**
である点に注意。

---

## Phase 3 — Migration直前Backup方法の候補整理（公開仕様ベース）

| 候補 | 内容 | plan要件 | 出典 |
|---|---|---|---|
| A. Supabase自動Daily Backup | 毎日自動的にfullバックアップを取得、Dashboardから選択してrestore | **Free: なし。Pro: 直近7日、Team: 直近14日、Enterprise: 直近30日** | [Database Backups](https://supabase.com/docs/guides/platform/backups) |
| B. Manual backup/export（CLI） | `supabase db dump`でroles/schema/dataを個別に`.sql`ファイルとしてexport、`psql`でrestore | **全plan共通で利用可能**（Free plan公式推奨手段はこれのみ） | [Backup and Restore using the CLI](https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore) |
| C. PITR（Point-in-Time Recovery） | WALアーカイブによる継続的backup。任意時点への復元 | **Pro/Team/Enterprise限定のadd-on。追加料金（7日毎に月$100）。Small compute add-on以上が前提** | [Manage PITR usage](https://supabase.com/docs/guides/platform/manage-your-usage/point-in-time-recovery) |

### この調査が意味すること

`docs/audit/migration-execution-method-reality-audit.md`でRenderの
Shell/One-Off JobがFree planで使えないことを確認したのと**同型の
問題**が、Supabase側のbackupにも存在する: **もし現在のSupabase plan
がFreeであれば、候補A（自動backup）・候補C（PITR）はいずれも
技術的に利用不可能であり、候補B（Mother Ship自身によるCLI手動export）
が唯一の選択肢になる。**

候補Bは**本セッションから実行できない**。理由:
- `supabase db dump`にはDB接続文字列・パスワードが必要であり、これを
  本セッションが要求することは`docs/audit/
  production-db-readonly-audit-access-gate.md`のStop Conditions
  「Production DB credentialの値を要求する必要がある → 即停止」に
  該当する
- したがって候補Bを取るなら、**Mother Ship自身のローカル環境で
  Supabase CLIを実行する**必要がある

### 確認項目（各候補共通）

**Candidate A**:
- [ ] migration直前に十分新しいbackupが存在するか（Mother Ship確認）
- [ ] backup時刻の記録方法（Dashboard上のタイムスタンプをそのまま記録すれば足りる）
- [ ] restore手順（Phase 4参照）

**Candidate B**:
- [ ] Dashboardからmanual backupボタンがあるか、CLIのみか（Mother Ship確認。
  公式ドキュメント上はCLI手順のみ記載されており、Dashboard上のワンクリック
  exportボタンの有無は未確認）
- [ ] `roles.sql`/`schema.sql`/`data.sql`として取得可能（公式手順で確認済み）
- [ ] restore方法: `psql`で3ファイルを順に適用（公式手順で確認済み、Phase 4参照）
- [ ] backupファイルの保管場所: **リポジトリ（Git）には絶対に入れない**。
  ローカルディスクの一時ディレクトリ、または暗号化済みの外部ストレージを
  推奨（本監査の意見であり、最終決定はMother Ship）
- [ ] 秘密情報をGitへ入れない: `schema.sql`/`data.sql`自体は秘密情報を
  含まないはずだが、接続文字列・パスワードを含むコマンド履歴・シェル
  スクリプトを誤ってcommitしないよう注意喚起する

**Candidate C**:
- [ ] PITRが現在のplanで利用可能か（Pro以上必須、Mother Ship確認）
- [ ] 有効化済みか（有効化には追加料金が発生するため、事前に有効化されて
  いなければmigration当日には使えない）
- [ ] 公式ドキュメント上、正常運用時のRPO（データ欠損許容範囲）は
  「最悪2分間隔」と記載されている（「秒単位」と紹介する二次情報も
  あったが、一次情報である公式ドキュメントの表現を優先して記録する）

---

## Phase 4 — Restore手順設計（未実行・設計のみ）

Supabase公式ドキュメントに基づく一般的な手順を記す。**まだ実行しない。**
なお、公式ドキュメント内に**2種類の異なるrestoreフロー**が存在することを
確認した。この違いはMother Ship側の確認事項として残す:

1. **同一project内restore**（Daily BackupsまたはPITRから、Dashboardの
   Backups画面で「Restore」を選択する想定のフロー）: 二次情報（複数の
   非公式記事）によれば同一project内で完結し、接続文字列は変わらない
   とされる
2. **新規projectへのrestore**（`docs/guides/platform/migrating-within-
   supabase/dashboard-restore`が説明するフロー）: 新しいSupabase
   projectを作成し、そこへ復元する。この場合**接続文字列（`DATABASE_URL`）
   が変わるため、Renderの環境変数更新が別途必要になる**

本セッションが取得できた公式ドキュメントの記述だけでは、Free/Pro等の
条件でどちらのフローが提供されるのか、あるいは両方存在するのかを
確定できなかった。**この点はMother ShipがDashboard上のBackups画面を
実際に開いて確認する必要がある（Phase 1の項目「restore操作がDashboard
から可能か」に含まれる）。**

### 手順案（Candidate A/C、同一project内restoreの場合）

1. Dashboard → Settings → Database → Backups
2. 復元したい時点のbackup（Daily BackupまたはPITRの任意時刻）を選択
3. 確認ダイアログで実行
4. 所要時間: 公式ドキュメントには明記なし。二次情報では「数分〜
   （大規模DBでは）1時間以上」「restore中はproject全体が読み取り専用
   または利用不可になる」と紹介されている。**一次情報での確認が
   取れていないため、正確な時間・影響範囲はMother Ship確認事項とする**
5. restore完了後、データを検証してから本番トラフィックを戻す
   （公式ドキュメントが明記する推奨事項）

### 手順案（Candidate B、CLI手動export/restoreの場合）

1. （事前・migration前）Mother Shipのローカル環境で
   `supabase db dump --db-url <接続文字列> -f roles.sql --role-only`
   `supabase db dump --db-url <接続文字列> -f schema.sql`
   `supabase db dump --db-url <接続文字列> -f data.sql --use-copy --data-only`
   を実行し、3ファイルを安全な場所に保管する
2. （restoreが必要になった場合）`psql --single-transaction
   --variable ON_ERROR_STOP=1 --file roles.sql --file schema.sql
   --command 'SET session_replication_role = replica' --file data.sql
   --dbname <接続先>`で復元する
3. 注意点（公式ドキュメント記載）: Supabase Vaultやcolumn暗号化を
   使っている場合、backupファイル自体には暗号化ルートキーが含まれない。
   本プロジェクトがVault/column暗号化を使用しているかは本監査未確認
   （`docs/audit/supabase-security-advisor-review.md`等の既存監査で
   触れられていないか、別途確認が望ましい）
4. カスタムroleのパスワードはbackupに含まれないため、restore後に
   再設定が必要

### Restore前後の運用設計（未実行・設計のみ）

- **restore前にRenderをどう扱うか**: restore中はDBが読み取り専用または
  利用不可になる可能性が高いため、Renderのweb serviceを事前にmaintenance
  状態にする（またはtraffic遮断・scale down）ことを検討する。**具体的な
  方法（Renderにmaintenance機能があるか）は未確認**であり、`docs/audit/
  migration-execution-method-reality-audit.md`で調査したRender公開
  ドキュメントの範囲では確認できていない。追加調査が必要な場合は
  別途行う
- **restore後のmigration state確認手順**: Phase 5のsnapshotクエリを
  再実行し、restore後の値がsnapshot時点と一致することを確認する
- **restore後のRuntime QA**: Phase 6参照

### Restore開始条件（指示より確定・記録のみ）

- migration途中で失敗
- unexpected destructive schema change
- existing data count減少
- `/api/auth/me`継続500
- Concierge/Knowledge系500悪化
- migration stateとschemaが不一致

---

## Phase 5 — Pre-Migration Snapshot項目（SELECT-only、未実行）

migration実行直前にMother Shipが実行するSQL案。テーブル名・列名は
develop側の`backend/temples/models.py`・`backend/users/models.py`・
`backend/favorites/models.py`から実際に確認した（推測ではない）。

```sql
-- app別最新migration
SELECT app, name, applied
FROM django_migrations
ORDER BY app, applied DESC;
```

```sql
-- users/temples の対象migrationが未適用であることの確認（開始前提の確認）
SELECT EXISTS (
  SELECT 1 FROM django_migrations
  WHERE app = 'users' AND name = '0006_userprofile_birth_profile_fields'
) AS users_0006_applied,
EXISTS (
  SELECT 1 FROM django_migrations
  WHERE app = 'temples' AND name = '0093_shrine_knowledge_model_foundation'
) AS temples_0093_applied;
```

```sql
-- 件数snapshot
SELECT
  (SELECT COUNT(*) FROM auth_user) AS auth_user_count,
  (SELECT COUNT(*) FROM users_userprofile) AS userprofile_count,
  (SELECT COUNT(*) FROM temples_shrine) AS shrine_count,
  (SELECT COUNT(*) FROM favorites_favorite) AS favorite_count,
  (SELECT COUNT(*) FROM temples_visit) AS visit_count,
  (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags) AS shrine_goriyaku_relation_count;
```

```sql
-- Knowledge table不存在確認（migration前提の確認）
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
  'temples_shrineknowledgesource',
  'temples_shrinedeity',
  'temples_shrinehistory',
  'temples_shrinedeity_sources',
  'temples_shrinehistory_sources'
);
-- 期待値: migration前は0件（1件も存在しない）
```

- [ ] snapshot取得時刻を記録する（`SELECT now();`の結果、またはクエリ実行時刻を手動記録）

---

## Phase 6 — Post-Migration Verification項目設計（未実行・設計のみ）

`docs/audit/production-db-readonly-audit-access-gate.md`で用意した
SELECT-only SQLを土台に、今回のPhase 5項目と対応させて拡張する。

```sql
-- migration適用確認
SELECT app, name, applied FROM django_migrations
WHERE (app = 'users' AND name = '0006_userprofile_birth_profile_fields')
   OR (app = 'temples' AND name = '0093_shrine_knowledge_model_foundation');
```

```sql
-- UserProfile 4カラム存在確認
SELECT column_name FROM information_schema.columns
WHERE table_name = 'users_userprofile'
AND column_name IN ('birthday', 'birth_time', 'birth_place', 'worship_style');
```

```sql
-- Knowledge table + M2M relation table存在確認（Phase 5と同一クエリを再実行）
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
  'temples_shrineknowledgesource', 'temples_shrinedeity', 'temples_shrinehistory',
  'temples_shrinedeity_sources', 'temples_shrinehistory_sources'
);
```

```sql
-- 件数不変確認（Phase 5のsnapshot値と比較）
SELECT
  (SELECT COUNT(*) FROM auth_user) AS auth_user_count,
  (SELECT COUNT(*) FROM users_userprofile) AS userprofile_count,
  (SELECT COUNT(*) FROM temples_shrine) AS shrine_count,
  (SELECT COUNT(*) FROM favorites_favorite) AS favorite_count,
  (SELECT COUNT(*) FROM temples_visit) AS visit_count,
  (SELECT COUNT(*) FROM temples_shrine_goriyaku_tags) AS shrine_goriyaku_relation_count;
```

アプリケーションレベルの確認（SQLでは検証できない項目）:

- [ ] `/api/auth/me` 500解消 — 認証済みリクエストが必要なため、Mother Ship
  またはproduction相当の認証済みsessionを持つ担当者が確認する
- [ ] Production MyPage正常表示 — 実際のブラウザ操作による確認が必要
- [ ] Conciergeのmissing-table error解消 — 同上

いずれも本セッションからは認証済みproduction操作ができないため、**確認は
Mother Ship側で実施する想定**とする（これはPhase 6の「設計」であり、
実施はしていない）。

---

## Phase 7 — Backup Gate Classification

**`BACKUP_CAPABILITY_UNKNOWN`**

理由: Phase 1/2（現在のSupabase plan・実際のbackup有無・restore手順の
実機確認）が本セッションからは一切確認できないため。Phase 3で整理した
公開仕様は「一般論として何が可能か」の枠組みに過ぎず、「このprojectで
今何が使えるか」を確定するものではない。

ただし、公開仕様の調査結果から言えること（参考情報）:

- **もし現在のplanがFreeなら**: 候補A（自動backup）も候補C（PITR）も
  技術的に利用不可能であり、**Mother Ship自身による事前のmanual export
  （候補B）を確保しない限り、migration直前へ戻せる手段がない**
  状態になる。この場合、実質的に`BACKUP_NOT_READY`に近い
- **もし現在のplanがPro以上なら**: 候補A（直近7日以上のDaily Backup）は
  追加設定不要で利用できているはずであり、少なくとも
  `BACKUP_READY_WITH_LIMITATIONS`（前日時点までしか戻せない、
  PITRが別途有効化されていなければ秒単位の精度は出ない）の水準は
  満たしている可能性が高い

**この分岐自体がPhase 1の確認結果次第で確定するため、最終classificationは
Mother Shipの確認後に更新する。**

---

## Phase 8 — Mother Ship Gate

Phase 7が`BACKUP_CAPABILITY_UNKNOWN`のため、指示のgate定義に従い：

- [x] Production migrationを継続PAUSE
- [x] backup方法の整備を先行

**Production migration execution planへは進めない。**

---

## Stop Conditions（遵守確認）

- [x] migrateを実行しない
- [x] makemigrationsを実行しない
- [x] SupabaseへINSERT/UPDATE/DELETE/ALTERしない（接続自体していない）
- [x] Environment変更しない
- [x] `RUN_MIGRATIONS_ON_START`変更しない
- [x] Render deploy設定変更しない
- [x] restoreを実際に実行しない
- [x] Batch 8開始しない
- [x] Knowledge Data投入しない

## Mother Shipへ返す確認事項（優先度順）

1. **最優先**: 現在のSupabase plan（Free/Pro/Team/Enterprise）
2. Backups画面で自動backup有無・最新backup日時・保持期間を確認
3. PITRが有効化済みか（有効化済みでなければmigration当日に急遽有効化しても
   間に合わない可能性がある——add-onの反映に時間がかかる可能性を考慮）
4. Dashboard上の「Restore」が同一project内restoreか、新規project作成を
   伴うrestoreか（Phase 4で記載した2フローのどちらが実際に提供されるか）
5. 上記が確定次第、Phase 7のclassificationを`BACKUP_READY` /
   `BACKUP_READY_WITH_LIMITATIONS` / `BACKUP_NOT_READY`のいずれかへ
   確定させる

## Repository Changes

- `docs/audit/supabase-backup-capability-gate.md`: 本ドキュメント（新規）
- 上記以外の変更なし
