> **Status: Active — Phase 0/1/2は設計完了、Phase 3以降はSTOP
> （安全に利用可能なProduction接続情報が本セッションに存在しない）**
>
> **Classification: `MANUAL_BACKUP_BLOCKED_CREDENTIAL_ACCESS`**
>
> 本ドキュメントは、Production手動バックアップ・分離環境へのrestore・
> Rollback Gateとしての実用性検証を試みた記録である。
> **Production DBへは一切接続していない。dump取得も実行していない。
> restoreも実行していない。Environment変更も一切していない。**

# Production Manual Backup / Restore Gate Audit

## Phase 0 — Base State

| 項目 | 結果 |
|---|---|
| develop checkout | 完了 |
| `git fetch` + `git merge --ff-only origin/develop` | 完了（既にPR #2324 merge済みでup to date） |
| working tree | clean |
| develop HEAD SHA | `90f1b21f...`（PR #2324のsquash merge commit） |
| `docs/audit/supabase-backup-capability-gate.md`確認 | 読了。Plan=Free/Scheduled Backup unavailable/PITR unavailable/Restore to new project unavailableがMother Ship実測値として既に記録されていることを確認 |
| 重複監査の回避 | `docs/audit/production-migration-0090-0093-safety.md`（temples 0090-0093 apply/rollback実測）、`docs/audit/production-all-app-migration-state-audit.md`（users 0006 apply/rollback実測、schema/code mismatch実測）は既存の結論をそのまま再利用し、再実施しない |
| Production migration state（前提として引き継ぐ値） | users=`0005`、temples=`0089`（Mother Ship提供値。本監査ではProductionへ接続していないため独自には再確認できていない） |

---

## Phase 1 — Backup Tool Reality Audit

Production接続なしで判断できる範囲（tool availability・一般的な互換性）を
調査した。

### ローカル環境のtool availability確認

| tool | 状態 |
|---|---|
| `pg_dump` / `pg_restore` | インストール済み（`/opt/homebrew/bin/pg_dump`、バージョン`16.10 (Homebrew)`） |
| Supabase CLI（`supabase db dump`） | **未インストール**（`supabase: not found`） |

### 候補比較（一般知識・`docs/audit/supabase-backup-capability-gate.md`
Phase 3の内容を土台に、今回は「Djangoのmigration直前snapshotとして
使えるか」の観点で再評価）

| 候補 | PostgreSQL version互換性 | Supabase管理schemaとの相性 | migration/sequence/constraint/index/extension情報 | 採用可否 |
|---|---|---|---|---|
| A. 素の`pg_dump` | ローカル`16.10`。SupabaseのPostgresバージョンは本セッションから未確認（Dashboardアクセスなし）。`pg_dump`はサーバーバージョンより新しいクライアントを使うのが安全という一般原則があり、確認できないままでは互換性リスクが残る | Supabase固有の拡張機能（`pgsodium`/`pg_graphql`/`pg_net`等）や`auth`/`storage`/`realtime`schemaを無条件にdumpしようとすると、権限不足やSupabase管理object特有のエラーが起きる可能性がある（一般的に知られている問題。本セッションでの実測はできていない） | `--schema=public`を明示すればDjango管理領域のみに絞れる（後述Phase 2） | **条件付き可**。ただし後述の通りcredential自体がないため実行不可 |
| B. Supabase CLI `supabase db dump` | SupabaseのPostgresバージョンに合わせて内部的にpg_dumpを選択・調整する設計のため、Aより互換性リスクは低いとされる（`docs/audit/supabase-backup-capability-gate.md`で確認した公式手順もこちらを採用） | Supabase公式ツールのため、Supabase管理schemaとの相性はAより高いと考えられる | 公式手順は`roles.sql`/`schema.sql`/`data.sql`の3分割（Phase 4詳細は前回監査参照） | **推奨候補**（未インストールのため、採用する場合はまず`brew install supabase/tap/supabase`等のインストールが別途必要） |
| C. その他公式手段（Dashboard export等） | 該当なし | 該当なし | 該当なし | **不採用**。Mother Ship実測により`Scheduled Backup = unavailable`が既に確定しているため |

### 採用候補

**候補B（Supabase CLI `supabase db dump`）を採用候補とする。**
理由: Supabase管理schemaとの相性・バージョン互換性の観点でAより安全側に
倒せると判断した（一般的な公式推奨に基づく判断であり、本セッションでの
実機比較検証はしていない）。

**ただし、候補A・候補Bのいずれを採用しても、実行にはProduction DBへの
接続情報（接続文字列またはproject ref + DB password）が必須である。**
この時点で次のPhaseへ進めるかどうかが決まる。

---

## Phase 2 — Dump Scope Design

developの`backend/shrine_project/settings.py`を確認したところ、Postgres
schemaを明示的に指定する設定（`search_path`変更等）は存在せず、Djangoは
デフォルトの**`public`schema**にすべてのtableを作成する。これは
`docs/audit/production-db-readonly-audit-access-gate.md`等、過去の監査で
`information_schema.tables WHERE table_schema = 'public'`のクエリが
一貫して機能してきたことからも裏付けられる。

### 設計方針

**dump対象を`--schema=public`（Supabase CLIの場合は相当オプション）に
限定する。** これにより、指示にある「`auth`/`storage`/`realtime`/
`extensions`などSupabase管理領域を無条件にdump/restore対象へ含めない」
という要件を、個別のtable除外リストを作らずに構造的に満たせる。

`public`schema内に含まれる、今回の目的（migration直前snapshot）に
必要なDjango管理tableの一覧（develop側のmigration履歴・model定義から
確認済み）：

| 分類 | table例 |
|---|---|
| migration履歴 | `django_migrations` |
| Django内蔵 | `django_session`, `django_content_type`, `django_admin_log` |
| auth（Django標準） | `auth_user`, `auth_group`, `auth_permission`, `auth_group_permissions`, `auth_user_groups`, `auth_user_user_permissions` |
| token_blacklist | `token_blacklist_outstandingtoken`, `token_blacklist_blacklistedtoken` |
| users app | `users_userprofile` |
| favorites app | `favorites_favorite` |
| temples app | `temples_shrine`, `temples_visit`, `temples_goriyakutag`, `temples_shrine_goriyaku_tags`ほか多数（`temples/models.py`に多数のmodelが存在。全件листは本監査の主目的ではないため個別列挙はしない） |

sequences・constraints・indexesは、`pg_dump`/`supabase db dump`の
schema dump（`schema.sql`相当）に標準で含まれる（PostgreSQLのschema
dumpの一般的な仕様であり、Djangoのmigration機構が生成したtable定義を
そのまま復元できる設計になっている）。ownership/privilege情報は
Supabaseの管理roleとの兼ね合いで複雑になりやすいため、
`docs/audit/supabase-backup-capability-gate.md`のPhase 4で確認した通り
`roles.sql`を別ファイルとして分離する公式手順に従う設計とする。

---

## Phase 3 — Production Pre-Dump Snapshot（STOP）

**実施不可。** 本Phaseは「ProductionへREAD ONLYで接続できる場合のみ
実施」という前提条件付きだが、その前提が満たされない。

### Credential確認の結果

以下を確認した（値は一切出力せず、キーの有無・値の形状のみを確認する
方法で実施した）:

| 確認対象 | 結果 |
|---|---|
| 本セッションのシェル環境変数（`DATABASE_URL`/`SUPABASE_*`/`DB_*`等） | **存在せず** |
| `backend/.env.prod` | ファイルは存在するが、内容は`OSRM_BASE_URL`/`ROUTE_PROVIDER`/`ROUTE_CACHE_TTL_S`のみ。DB認証情報は一切含まれない |
| `.env` / `.env.dev` / `backend/.env.local` / `backend/.env.test` / `backend/.env.example` / `backend/.env.dev.old` | いずれも`DATABASE_URL`キーは存在するが、値の宛先ホストはすべて`127.0.0.1`または`db`（docker-compose内部ホスト名）——**ローカル開発用であり、Production Supabaseを指していない** |
| `.env.render.example` | `DATABASE_URL`はプレースホルダ（値の長さ16文字、パース不能な形式）であり実際の接続情報ではない |
| Supabase専用のMCP tool・API連携 | 本セッションの利用可能tool一覧に存在せず |

**結論: 本セッションが安全に利用できるProduction接続情報は一切存在
しない。**

指示に明記された通り、この場合は**ユーザーへDB passwordや秘密情報を
チャットへ貼るよう要求せず、ここでSTOPする。**

Phase 4（Manual Dump実行）・Phase 5（Isolated Restore Environment構築）・
Phase 6（Restore Test）・Phase 7（Restore Verification）・Phase 8
（Optional Restore DB Django Check）は、いずれもPhase 3で取得したdump
ファイルを前提とするため、**すべて未着手のまま保留する。**

---

## Phase 9 — Recovery Procedure Draft（`UNVERIFIED`）

実機検証していない設計案として記す。**すべての手順に`UNVERIFIED`ラベルを
付す。実際に機能することを本監査は保証しない。**

1. **`UNVERIFIED`** Production traffic/write停止判断 — Renderに
   maintenance機能があるかは`docs/audit/
   migration-execution-method-reality-audit.md`の調査範囲でも未確認。
   最低限の代替案として、Renderの該当serviceを一時的にsuspend/scale-down
   する運用が考えられるが、その操作方法・影響範囲は未検証
2. **`UNVERIFIED`** restore対象backup確認 — Phase 1で選定した候補B
   （Supabase CLI）で取得した`roles.sql`/`schema.sql`/`data.sql`の
   3ファイルの存在・取得時刻を確認する
3. **`UNVERIFIED`** restore先確認 — 新規に作成する分離環境（Production
   ではない一時DB）のホスト名・DB名を必ず目視確認してから実行する
   （Phase 5で設計した安全確認と同じ考え方）
4. **`UNVERIFIED`** DB restore — `psql --single-transaction
   --variable ON_ERROR_STOP=1 --file roles.sql --file schema.sql
   --command 'SET session_replication_role = replica' --file data.sql
   --dbname <restore先>`（`docs/audit/supabase-backup-capability-gate.md`
   Phase 4で確認した公式手順をそのまま踏襲する設計）
5. **`UNVERIFIED`** migration state確認 — restore後、`django_migrations`
   のapp別最新migrationがdump取得時点のsnapshotと一致することを
   SELECT-onlyで確認する
6. **`UNVERIFIED`** row count確認 — Phase 2で列挙した主要tableの件数を
   snapshot時点と比較する
7. **`UNVERIFIED`** application health確認 — restore先DBに対して
   develop側のDjangoから`manage.py check`や個別クエリで疎通確認する
   （Productionそのものへは接続しない）
8. **`UNVERIFIED`** service再開判断 — 上記すべてが一致した場合のみ
   Mother Shipが再開を判断する

**本Runbookが実際に機能することは、Production相当のdumpをまだ一度も
取得できていないため検証されていない。** 次にこのGateへ戻る際は、
Mother Ship側で安全なProduction接続情報（read-only権限を持つDB
credential等）を用意した上で、Phase 3以降を再開する必要がある。

---

## Phase 10 — Classification

**`MANUAL_BACKUP_BLOCKED_CREDENTIAL_ACCESS`**

理由: 安全に利用可能なProduction接続情報が本セッションに一切存在しない
ため（Phase 3参照）。Production migrationは指示の通りPAUSEDのまま
とする。

---

## Stop Conditions（該当確認）

- [x] Production credentialをユーザーへ要求する必要がある → **該当。
  ただし指示に従い実際には要求せず、`MANUAL_BACKUP_BLOCKED_CREDENTIAL_ACCESS`
  として本監査をここで終了した**
- [ ] Productionへwriteが必要 → 非該当（write自体を試みていない）
- [ ] Production migrateが必要 → 非該当
- [ ] Production restoreが必要 → 非該当
- [ ] Production migration stateがusers 0005 / temples 0089から変わっている → **未確認**（Production接続自体をしていないため確認不能。前回Mother Ship提供値をそのまま引き継いでいる）
- [ ] dump destinationの安全性を保証できない → 非該当（dump自体を取得していない）
- [ ] restore destinationがProductionである可能性がある → 非該当（restore自体を実施していない）
- [ ] backupにcredentialが混入している → 非該当（backup自体を取得していない）
- [ ] dumpをGitへ入れる必要がある → 非該当
- [ ] destructive operationがProductionへ向いている → 非該当
- [ ] 判断不能なrestore errorが発生 → 非該当（restore自体を実施していない）

---

## 明示的禁止事項の遵守確認

- [x] Production migrate禁止（遵守）
- [x] Production restore禁止（遵守）
- [x] Production DB write禁止（遵守、接続自体していない）
- [x] Supabase Environment変更禁止（遵守）
- [x] Render Environment変更禁止（遵守）
- [x] 新規signup禁止（遵守）
- [x] Batch 8開始禁止（遵守）
- [x] dump commit禁止（遵守、dump自体を取得していない）
- [x] credential commit禁止（遵守。本ドキュメントおよびcommit履歴に秘密情報は一切含まれない）
- [x] PR merge禁止（本監査ではPR作成のみ行い、mergeはしない）

---

## Mother Shipへの最終報告

1. **Production migration state**: users=`0005`、temples=`0089`（前回Mother Ship提供値を引き継ぎ。本監査では独自に再確認していない）
2. **採用したbackup方式**: 候補B（Supabase CLI `supabase db dump`）を設計上の推奨候補として選定。ローカル未インストールのため、採用する場合は別途インストールが必要
3. **Production dump成功/失敗**: **未実施**（credential access blockedのため着手前でSTOP）
4. **Productionへのwriteが0だったか**: **0（接続自体していないため確実に0）**
5. **isolated restore成功/失敗**: **未実施**
6. **migration state一致/不一致**: **未評価**（dump取得前のためcomparisonできない）
7. **schema一致/不一致**: **未評価**
8. **aggregate data一致/不一致**: **未評価**
9. **Recovery Runbookの検証範囲**: Phase 9に設計案を記載したが、全手順`UNVERIFIED`（未実機検証）
10. **最終Classification**: `MANUAL_BACKUP_BLOCKED_CREDENTIAL_ACCESS`
11. **Production migrationをPAUSEDのままにすべきか**: **はい、PAUSEDのまま維持すべき**
12. **PR番号とCI状態**: 本セクションはPR作成・CI確認後に更新する

## 次にMother Shipが用意すべきもの

本Gateを`MANUAL_BACKUP_RESTORE_PASS`まで前進させるには、以下のいずれかが
必要（本セッションからは用意できない）:

- Mother Ship自身のローカル環境でSupabase CLI（`supabase db dump`）を
  実行し、`roles.sql`/`schema.sql`/`data.sql`を取得した上で、
  それらのファイル（秘密情報を含まないことを確認した上で）を安全な
  方法でこのセッションの作業領域へ持ち込む
- または、read-only権限に限定したProduction DB接続情報を、チャットに
  貼る以外の安全な方法（例: 環境変数として実行環境に設定する等）で
  本セッションが利用できるようにする

## Repository Changes

- `docs/audit/production-manual-backup-restore-gate.md`: 本ドキュメント（新規）
- 上記以外の変更なし。dumpファイル・credentialはリポジトリに一切含まれない
