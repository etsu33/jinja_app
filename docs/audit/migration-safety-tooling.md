> **Status: Implementation + local verification complete.
> Production DBは一切変更していない。Production migrate/restore/DB write/
> Environment変更は一切行っていない。Production操作を自動実行するコードは
> 作っていない。**

# Migration Safety Tooling — Implementation & Verification Record

本ドキュメントは、今後のmigration（`users 0006`・`temples 0090-0093`、
および将来のmigration一般）で再利用できる安全な変更・復旧ルートの実装と、
そのローカル検証結果の記録である。

対象コード: `scripts/migration_safety/`（Runbookは
[`scripts/migration_safety/README.md`](../../scripts/migration_safety/README.md)
を参照）。

---

## 実装したもの

| ファイル | 内容 |
|---|---|
| `scripts/migration_safety/guard.py` | 純粋関数のみのPython safety guard。DB接続・ネットワークコードは一切含まない。restore先の許可判定（allow-list方式）、dump出力先のrepo境界チェック、credential redaction |
| `scripts/migration_safety/dump_readonly.sh` | 明示的に渡されたURLのみをdumpするread-only script。デフォルト接続先を持たない |
| `scripts/migration_safety/restore_isolated.sh` | `guard.py`のrestore-target判定を通過した場合のみ動作するrestore script |
| `scripts/migration_safety/sql/migration_state.sql`ほか2件 | SELECT-onlyのmigration state / snapshot / verification クエリ |
| `scripts/migration_safety/tests/test_guard.py` | `guard.py`の単体テスト（DB不要） |
| `scripts/migration_safety/tests/test_backup_restore_e2e.sh` | ローカル隔離DBのみを使ったbackup/restore end-to-endテスト |

いずれもProduction操作を自動実行しない。すべてのscriptは呼び出し側が
明示的に渡した接続先文字列のみを操作対象とし、デフォルト値・環境変数
フォールバックによる暗黙のProduction接続経路は存在しない。

---

## 安全設計の核心: allow-list方式のrestore guard

`guard.py`の`is_safe_restore_target()`は、「Productionっぽいものを
検出してblockする」deny-list方式ではなく、「ローカル隔離DBとして
明確なものだけを許可する」allow-list方式を採用した。理由は、本セッションが
Productionの実際のhostnameを知らないため、deny-listは構造的に不完全
にしかなり得ないためである。許可条件は以下すべてを満たす場合のみ:

- hostが`localhost`/`127.0.0.1`/`::1`のいずれか
- database名が既存local dev DB（`jinja_db`/`jinja_app_dev`/`jinja_test`等）と一致しない
- database名に`audit`/`restore_test`/`migration_safety`のいずれかが含まれる

それ以外（実際のProduction hostnameがどのような値であっても）はすべて
デフォルトでblockされる。

---

## テスト結果

### 単体テスト（`test_guard.py`、DB不要）

```
backend/.venv/bin/python3 -m pytest scripts/migration_safety/tests/test_guard.py -v
```

**結果: 18 passed in 0.04s**（全件pass）。カバー範囲:
- 非localhost（Supabase風hostname・Render風hostname含む）を正しくblock
- 既存local dev DB名（`jinja_db`・`jinja_app_dev`）を正しくblock
- isolation marker（`audit`/`restore_test`/`migration_safety`）を含む
  localhost URLを正しく許可
- query stringにmarkerを紛れ込ませてもdbname本体で判定されるため
  誤って許可しないことを確認
- repo内へのdump path出力を正しくblock、repo外は正しく許可
- credential redactionがuser/passwordを確実にマスクすることを確認

### End-to-endテスト（`test_backup_restore_e2e.sh`、ローカル隔離DBのみ使用）

**結果: PASS（exit code 0）。**

このテストは以下を実施した（すべてローカル、Productionへは一切接続
していない）:

1. `guard.py`の否定テスト4件（非localhost host拒否・既存dev DB拒否・
   隔離target許可・repo内dump path拒否）をすべて確認
2. 一時DB `jinja_migration_safety_source_<timestamp>` を新規作成し、
   `contenttypes 0002` → `auth 0012` → `admin 0003` → `sessions 0001` →
   `token_blacklist 0013` → `users 0005` → `favorites 0002` →
   `temples 0089`（migration 89件、PostGIS込み）を適用し、Production
   相当のbaseline schemaを再現
3. User/UserProfileの実データを1件ずつ投入
4. `dump_readonly.sh`でこのDBをdump（`roles.sql`/`schema.sql`/
   `data.sql`）
5. 別の一時DB `jinja_migration_safety_restore_test_<timestamp>` を
   新規作成し、`restore_isolated.sh`でguard判定を通過させた上でrestore
6. restore後のaggregate件数（`auth_user`/`users_userprofile`/
   `temples_shrine`）がsource側と完全一致することを確認
7. restore後の`django_migrations`最新状態が`users=0005`/`temples=0089`
   と一致することを確認
8. **restoreされた側（sourceでもProductionでもない）に対してのみ**
   `users 0006`・`temples 0090-0093`を適用し、成功を確認
9. 新規カラム4件・新規Knowledge table 5件の存在、aggregate件数不変を確認
10. `temples 0089`・`users 0005`へのrollbackが成功することを確認
11. 使用した一時DB・dumpファイルをすべて削除（`trap ... EXIT`により
    テスト失敗時も確実に削除される）

### テスト中に発見した実際の不具合（設計段階の文書レビューだけでは
見つからなかったもの）

1. **`pg_dumpall`のバージョン不一致拒否**: ローカルPostgres serverは
   `18.0`だが、`PATH`上のデフォルト`pg_dump`/`pg_dumpall`は`16.10`
   （Homebrewの一般シンボリックリンク）。`pg_dumpall`はバージョン
   不一致時に警告ではなく即エラーで停止する。`PG_DUMP_BIN`/
   `PG_DUMPALL_BIN`/`PSQL_BIN`のオーバーライドをscriptへ追加して解消。
   **実際のProduction dump実行前には、Supabase側のPostgresバージョンを
   確認し、一致するクライアントを使う必要がある。**
2. **`--schema=public`のdumpに含まれる`CREATE SCHEMA public;`が、
   新規作成直後のtarget DBに既に存在する`public`schemaと衝突する**。
   restore前にその1行を除去することで解消（`restore_isolated.sh`内で
   `grep -v`により対処）。
3. **PostGIS/pg_trgm型がrestore先で未定義**: `--schema=public`限定の
   dumpにはextension object自体が含まれない（Supabaseはextensionを
   `public`以外のschemaへインストールする設計のため）。restore前に
   `CREATE EXTENSION IF NOT EXISTS postgis;`/`pg_trgm;`をtargetへ
   実行することで解消。

これら3件はいずれも`restore_isolated.sh`内で既に対処済みだが、実際の
Production dump/restoreを試みる際は、Supabase側のPostgresバージョン・
extension配置がローカル環境と異なる可能性がある点を「既知の未検証事項」
として`README.md`「Known gaps」節に明記した。

---

## Phase別チェックリスト結果

### Phase 0 — Contract確認
- [x] 既存Backup Gate文書（`docs/audit/production-manual-backup-restore-gate.md`）を読んだ
- [x] Migration Safety Audit（`docs/audit/production-migration-0090-0093-safety.md`・`docs/audit/production-all-app-migration-state-audit.md`）を読んだ
- [x] Production Execution Gate（`docs/audit/production-migration-execution-gate.md`）を読んだ
- [x] `users 0006`/`temples 0090-0093`の既知状態を確認した（既存監査の結論を再利用、再実施はしていない）

### Phase 1 — Backup Route
- [x] manual dump手順をRunbook化（`README.md`「Runbook: Manual Backup Route」）
- [x] dump保存先をrepo外に固定（`guard.py`の`is_safe_dump_path`で強制）
- [x] credential・接続先非露出チェックを入れる（URL、username、password、hostname、port、DB名、queryを成功・失敗ログの双方で非表示）
- [x] dump file存在/size確認手順を作る（`dump_readonly.sh`が自動で各ファイルのサイズを表示・0バイト時警告）

### Phase 2 — Restore Verification Route
- [x] isolated PostgreSQL作成手順を作る
- [x] Production誤接続防止チェックを入れる（`guard.py`のallow-list、`restore_isolated.sh`から強制呼び出し）
- [x] restore手順をRunbook化
- [x] migration state比較SQLを用意（`sql/migration_state.sql`）
- [x] schema比較SQLを用意（`sql/post_migration_verification.sql`内）
- [x] aggregate count比較SQLを用意（`sql/pre_migration_snapshot.sql`・`sql/post_migration_verification.sql`）

### Phase 3 — Pre-Migration Checklist
- [x] Production migration state確認手順を用意（`sql/migration_state.sql`、実行自体はMother Ship側）
- [x] manual backup完了確認手順を用意
- [x] backup timestamp記録手順を用意
- [x] users/temples baseline確認手順を用意
- [x] STOP条件を明文化（`README.md`「Pre-Migration Checklist」）

### Phase 4 — Migration Execution Runbook
- [x] `users 0006`適用候補コマンドを定義（`migrate users 0006 --noinput`）
- [x] users適用後QAを定義（`sql/post_migration_verification.sql`）
- [x] `temples 0090-0093`適用候補を定義（`migrate temples 0093 --noinput`）
- [x] temples適用後QAを定義
- [x] 全app一括migrateを無条件採用しない（`README.md`に明記。`docs/audit/migration-execution-method-reality-audit.md`・`docs/audit/production-all-app-migration-state-audit.md`で確認済みの「app指定なしmigrateは`users 0006`も巻き込む」を踏襲）

### Phase 5 — Recovery Route
- [x] migration失敗時のSTOP条件（`README.md`のPre-Migration Checklist、既存execution gate docのFailure boundariesを参照）
- [x] reverse migration候補整理（`migrate temples 0089`/`migrate users 0005`、E2Eテストで実際に成功を確認）
- [x] backup restore判断条件（既存`docs/audit/production-manual-backup-restore-gate.md`のRestore開始条件を踏襲）
- [x] restore後QAを定義（`sql/post_migration_verification.sql`と同じクエリを再利用可能）
- [ ] service再開条件を定義 — **`UNVERIFIED`**。Renderのmaintenance機能有無が未確認のため（`docs/audit/migration-execution-method-reality-audit.md`で既に指摘済みの既知gap）

### Phase 6 — Safety Guard
- [x] Production hostname検出時の確認処理 → allow-list方式で実装（デザイン上の理由は上述）
- [x] destructive commandを自動実行しない（scriptはいずれも明示的な引数なしでは何もしない。デフォルト接続先なし）
- [x] dry-run/read-onlyをデフォルトにする（`dump_readonly.sh`はread-onlyのみ、書き込み系操作は`restore_isolated.sh`のみで、かつguard必須）
- [x] credential・hostnameをログ出力しない（接続先文字列を表示せず、client stderrもgeneric failureへ置換）
- [x] dumpをGit対象外にする（`is_safe_dump_path`で強制。加えて一時dumpは`/tmp`配下、テスト終了時に削除）

### Phase 7 — Test
- [x] local isolated DBでbackup/restore再現（E2Eテストで実施、PASS）
- [x] `users 0005`状態再現（E2Eテストで実施）
- [x] `temples 0089`状態再現（E2Eテストで実施、GIS込み89件のmigrationを再現）
- [x] restore後データ一致確認（aggregate件数・migration state両方を実測比較）
- [x] migration後QA手順を検証（restoreされたコピーに対して`users 0006`・`temples 0090-0093`を適用し、新規column/table・件数不変・rollbackまで実測）

---

## 完了条件チェック

- [x] 本番変更前に戻せる手順が文書化されている（`README.md`、SQL定義済み）
- [x] localで復旧ルートを再現できる（E2Eテストで実測PASS）
- [x] Production操作は自動実行されない（全script、デフォルト接続先なし。CI testpathsにも含まれない）
- [ ] Mother ShipがGo/No-Goを判断できる → 本ドキュメント・README・PRで判断材料を提供。**ただし実際のProductionに対して一度もdump/restoreを試みていない**ため、最終的なGo判定（Backup Gateの`MANUAL_BACKUP_BLOCKED_CREDENTIAL_ACCESS`解消）はMother Ship側でのcredential提供が必要
- [x] PR作成まで

---

## Stop Conditions（遵守確認）

- [x] Production migrate禁止（遵守。すべての`migrate`実行はローカル一時DB上のみ）
- [x] Production restore禁止（遵守。restoreはローカル隔離DB間のみ）
- [x] Production DB write禁止（遵守。Productionへは一切接続していない）
- [x] Environment変更禁止（遵守）
- [x] Production操作を自動実行するコードを作らない（遵守。全scriptはDATABASE_URL等を明示引数として要求し、デフォルト値・環境変数フォールバックによる暗黙のProduction接続経路を持たない。CI wiring もしていない）

---

## Repository Changes

- `scripts/migration_safety/guard.py`: 新規
- `scripts/migration_safety/dump_readonly.sh`: 新規
- `scripts/migration_safety/restore_isolated.sh`: 新規
- `scripts/migration_safety/sql/migration_state.sql`: 新規
- `scripts/migration_safety/sql/pre_migration_snapshot.sql`: 新規
- `scripts/migration_safety/sql/post_migration_verification.sql`: 新規
- `scripts/migration_safety/tests/test_guard.py`: 新規
- `scripts/migration_safety/tests/test_backup_restore_e2e.sh`: 新規
- `scripts/migration_safety/README.md`: 新規（Runbook）
- `docs/audit/migration-safety-tooling.md`: 本ドキュメント（新規）
- 既存コード（`backend/`アプリケーションコード）への変更: **なし**
- Production DB・Environment・deploy設定への変更: **なし**

---

## 追補: Backup connection-target logging remediation

Batch 9 Production Import Gateのfresh backupで、旧
`dump_readonly.sh`がuser/passwordのみをmaskしたURLを表示し、hostname、
port、database name、query parameterをログへ残すことが確認された。
Production固有値を使わず、`.invalid`のdummy URLとfake clientで同じ挙動を
再現し、`BACKUP_LOG_HOSTNAME_EXPOSURE_CONFIRMED`と分類した。

修正後の契約は「接続先を表す文字列そのものを出力しない」である。
`dump_readonly.sh`と`restore_isolated.sh`はgeneric messageのみを表示し、URLを
libpq `PG*`環境変数へ変換してからchild processのargvから除外する。libpqの
失敗診断は接続先要素を含み得るため、tooling境界でgeneric failureへ置換する。
file名、file size、phase、success/failureは安全な運用metadataとして維持する。

`tests/test_backup_logging.sh`はfake clientだけを使用し、成功時・失敗時ともに
dummy username/password/hostname/port/database/queryが出力されないこと、かつ
非0 file sizeと完了状態が残ることを固定する。Production backup、Production
DB接続、Batch 9 importは本remediationでは実行しない。

検証結果:

- logging regression: PASS
- guard unit tests: 47 PASS
- credential bridge E2E: PASS
- local backup/restore/migrate/rollback E2E: PASS
- shellcheck / bash syntax / diff check: PASS
- credential・connection string・private hostname scan: PASS（追加URLはdummy
  `.invalid`、既存local E2E URL、generic provider exampleのみ）

最終分類: `BACKUP_LOGGING_REMEDIATION_READY`

## 次にMother Shipが用意すべきもの

`docs/audit/production-manual-backup-restore-gate.md`と同一の結論のまま
変わらない: 本ツールがそのまま使えるようになるには、Mother Ship側で
read-only Production接続情報を、チャット以外の安全な経路で用意する
必要がある。用意できた時点で、`scripts/migration_safety/README.md`の
Runbookに従い、Phase 1（Manual Backup Route）から実際に実行できる。
