> **Status: Bridge mechanism implemented, tested locally, and ready.
> Classification: `CREDENTIAL_BRIDGE_BLOCKED_LOCAL_SETUP_REQUIRED`**
>
> Production DBへは一切接続していない。credential値は本ドキュメント・
> commit・PR・consoleのいずれにも一切記載していない。Production
> migrate/restore/DB write/Environment変更はいずれも行っていない。

# Production Readonly Credential Bridge — Read-only Access Path Audit

## Phase 0 — Base State

| 項目 | 結果 |
|---|---|
| develop checkout | 完了（既に`develop`ブランチ） |
| `git fetch` + `git merge --ff-only origin/develop` | 完了（実行時点で既にup to date） |
| working tree | clean |
| develop HEAD SHA | `85562497...`（指示値と完全一致、変化なし） |
| `docs/audit/real-production-backup-restore-gate.md`反映確認 | 確認済み |

---

## Phase 1 — Existing Secret Handling Audit（存在確認のみ、値は出力せず）

| 確認対象 | 結果 |
|---|---|
| `DATABASE_URL_SET_IN_SHELL_ENV` | `0` |
| `SUPABASE_DB_URL_SET_IN_SHELL_ENV` | `0` |
| `PRODUCTION_DATABASE_URL_SET_IN_SHELL_ENV` | `0` |
| `.gitignore`の`.env`系カバレッジ | `.env`/`.env.*`/`.envrc`/`backend/.env`/`backend/.env.*`/`.env*.local`をカバー済み（`!.env.example`で明示的にexampleのみ許可） |
| `backend/shrine_project/settings.py`の`DATABASE_URL`利用箇所 | `os.getenv("DATABASE_URL")`で読み取り、`dj_database_url.parse()`へ渡す構造のみ確認（値は見ていない） |
| `scripts/migration_safety/README.md`の既存記述 | Manual Backup Routeが「Export it into your own shell」と書かれていたが、**AI駆動セッションではこの前提が成立しないことが判明**（後述Phase 2） |

---

## Phase 2 — Credential Storage候補比較・実測

### 重要な実測結果: shell state is NOT persisted between Bash calls

Candidate A（shell session env var）を評価する前提として、実際に
検証した:

```bash
# 1回目のBash呼び出し
export TEST_PERSISTENCE_CHECK_VAR="hello"
```
```bash
# 2回目の別Bash呼び出し
echo "TEST_PERSISTENCE_CHECK_VAR is set: $([ -n "${TEST_PERSISTENCE_CHECK_VAR:-}" ] && echo yes || echo no)"
# => "TEST_PERSISTENCE_CHECK_VAR is set: no"
```

**結果: 1回目のBash呼び出しで`export`した変数は、2回目の呼び出しには
一切引き継がれない。** これはAIエージェント（Claude Code/Codex）が
個々のshellコマンドを独立プロセスとして実行するためである。したがって
「ユーザーのshellでexportしてもらう」という素朴なCandidate Aの想定は、
**AI駆動セッションからは機能しない**（ユーザー自身が対話的terminalで
手動操作する場合は別）。

### 候補比較（実測を踏まえた最終評価）

| 候補 | 評価 |
|---|---|
| A. shell session env var | **AI駆動セッションからは機能しないことを実測で確認**。ユーザー本人の対話的terminal操作でのみ有効 |
| B. Git管理外のlocal secret file | **採用**。1回のscript呼び出し内で`source`することで、複数のBash呼び出しをまたぐ必要がなくなる。実測で動作確認済み（後述Phase 6/9） |
| C. OS keychain / secret manager | 不採用（指示通り、新規secret platform導入は目的外） |

---

## Phase 3 — 推奨方式決定

**Candidate B（repo外のlocal secret file）を採用した。**

理由: Candidate Aが実測でAI駆動セッションから機能しないことが判明した
ため、優先順位表の1位ではなく2位を実質的な最終候補として採用した。
指示にある「実環境でCodexから参照不能なら、その方式は採用しない」を
そのまま適用した結果である。

---

## Phase 4 — Secret Fileの安全条件（実装）

採用したpath: `~/.config/kami-musubi/production-db.env`

実施した内容:

- [x] ディレクトリ`~/.config/kami-musubi/`を作成し、`chmod 700`
- [x] **`production-db.env.example`（テンプレートのみ、実値なし）を配置**。
      実際の`production-db.env`はユーザー本人がローカルで作成する
- [x] `guard.py check-dump-path`のロジックを再利用し、このpathがrepo外
      であることをコードで確認（`SAFE: ok`）
- [x] スクリプト側（`check_credential_presence.sh`・`readonly_query.sh`）
      で、対象fileのpermissionが`600`でない場合は即blockする実装
- [x] shell historyへcredentialが残らない手順（file編集はユーザーの
      エディタで行い、コマンドライン引数として値を渡さない）を
      README「Credential Bridge」節に明記
- [x] 本タスク中にsecret値をcommitしていない（`~/.config/kami-musubi/`
      はrepo外であり、`git status`にも一切現れない。実測確認済み、
      Phase 9参照）

---

## Phase 5 — Credential Presence Guard（実装・テスト済み）

`scripts/migration_safety/check_credential_presence.sh`を新規実装した。

許可される確認のみ実施:
- env varがsetか（`VAR_SET=0/1`）
- URL schemeがpostgres/postgresqlか（`scheme_is_postgres: bool`）
- hostnameは一切ログへ出さず、`has_host: bool`のみ

`guard.py`に`describe_url_shape()`を追加し、返す情報を**構造的boolean
のみ**に限定した（`parses`/`scheme_is_postgres`/`has_host`/`has_port`/
`has_dbname`/`has_userinfo`）。**credential長（文字数）を含む数値は
一切返さない・出力しない**（指示のcredential長非表示ルールを反映）。

禁止事項の遵守:
- `echo $PRODUCTION_DATABASE_URL`相当の操作: 一切行っていない
- `env | grep DATABASE`相当: 一切行っていない
- `printenv`でsecret値を出す: 一切行っていない
- `set -x`/`bash -x`: 全scriptで未使用（`set -euo pipefail`のみ）
- exception traceでURLを出す: `describe_url_shape()`は例外時も入力値を
  メッセージに含めない設計（`urlparse`が`ValueError`を出しても
  `{"parses": False}`を返すのみ）

---

## Phase 6 — Read-only Connection Method（実装・実測済み、ローカルのみ）

`scripts/migration_safety/readonly_query.sh`を新規実装した。

**Production URLをcommand lineへ平文で直接書かない設計**: `guard.py`に
`pg_env_exports()`を追加し、URIを`PGHOST`/`PGPORT`/`PGUSER`/
`PGPASSWORD`/`PGDATABASE`/`PGSSLMODE`へ分解し、`eval`経由でsubshell内
だけにexportする。`psql`はconnection stringを一切argvへ渡さずに起動
される（libpqが`PG*`環境変数を自動参照する標準機構を利用）。これにより
`ps`コマンドでの一時的な露出リスクも回避している。

**実測（fake local credentialのみ使用、Productionへは未接続）**:

```
$ scripts/migration_safety/readonly_query.sh <cred-file> TEST_DATABASE_URL select.sql
SAFE: ok
[readonly_query] SQL passed the read-only check. Connecting...
 ok
----
  1
(1 行)
[readonly_query] done.
```

`SELECT 1;`が実際に実行され、結果が返ることを確認した。使用した
credentialはlocalhost上のfake test値であり、Productionではない。

`SHOW transaction_read_only;`相当の追加確認は、指示通り「実行する
SQLをSELECT-onlyに限定することでも安全性を担保する」方針のため、
本bridgeでは必須ステップとせず、Phase 7のSQL allow-list側で担保する
設計とした。

---

## Phase 7 — Read-only SQL Safety Rules（実装・テスト済み）

`guard.py`に`is_readonly_sql()`を追加した。

許可: `SELECT`/`SHOW`/`EXPLAIN`（`ANALYZE`なし）/`WITH`（CTE）
拒否: `INSERT`/`UPDATE`/`DELETE`/`MERGE`/`ALTER`/`CREATE`/`DROP`/
`TRUNCATE`/`GRANT`/`REVOKE`/`VACUUM`/`ANALYZE`/`CALL`/`DO`/`COPY`他

実装方式: SQLをセミコロンで文単位に分割し、各文の先頭keywordが
許可listに含まれるかを判定する。**「実行するSQLをSELECT-onlyに限定する
運用」を、`readonly_query.sh`が接続する前に必ず通過する強制チェックと
して実装した**（Phase 6のコード参照）。

`readonly_query.sh`はこのチェックをcredentialに触れる**前**に実行する
ため、SQLが1文でも許可listから外れていれば、credentialは一切
sourceされない。実測で確認済み（Phase 9のE2Eテスト参照）。

`sql/migration_state.sql`・`sql/pre_migration_snapshot.sql`・
`sql/post_migration_verification.sql`（既存3ファイル）はすべてこの
チェックを`SAFE: ok`で通過することを確認した。

---

## Phase 8 — Production Identity Confirmation（未実施: ローカル設定待ち）

`~/.config/kami-musubi/production-db.env`（実credential）は**まだ
存在しない**（テンプレート`.example`のみ配置済み）。

```
$ scripts/migration_safety/check_credential_presence.sh ~/.config/kami-musubi/production-db.env DATABASE_URL
VAR_SET=0
[check_credential_presence] no credential file at that path yet — this is expected before local setup is complete
```

**したがって、Production identity確認（`current_database()`/
`current_user`/`version()`）・Production migration state確認
（`users=0005`/`temples=0089`）のいずれも、本セッションではまだ
実行できない。** これはbridge機構自体の欠陥ではなく、ユーザー側の
一度きりのローカル設定（`production-db.env.example`をコピーして
実値を入れ、`chmod 600`する）が未完了であることによる。

---

## Phase 9 — Credential Leakage Audit

| 確認項目 | 結果 |
|---|---|
| `git status --short` | 新規/変更ファイルのみ表示（後述Repository Changes参照）。credential値・実file自体は一切現れない |
| `git grep -n "postgresql://"`（構造的pattern確認のみ、実credential検索ではない） | 既存の`.env.example`（無関係、pre-existing）のみヒット。新規追加コード内はtest fixture値（`myuser:supersecret@db.example.com`等、明らかなdummy値）のみ |
| `~/.config/kami-musubi/`のgit追跡確認 | `git status`実行時に`fatal: outside repository`となり、そもそもrepoの管理対象になり得ないことを確認 |
| test log / CI config | 新規テスト（`test_credential_bridge_e2e.sh`）はfake local credentialのみ使用し、出力にもcredential値は一切含まれないことを目視確認済み |

**End-to-endでの動作確認（fake local credentialのみ、Production未接続）**:
`scripts/migration_safety/tests/test_credential_bridge_e2e.sh`を新規実装し、
以下すべてがPASSすることを実測した:

1. presence checkがhostを含まずVAR_SET=1を報告
2. 存在しないcredential fileに対しVAR_SET=0を報告（エラー扱いにしない）
3. repo内pathのcredential fileをpresence check・readonly_query.sh
   いずれも拒否
4. `SELECT 1;`が実際に接続・実行され結果を返す
5. `migration_state.sql`相当の複数文read-only queryが成功
6. `DELETE FROM auth_user;`がcredentialに触れる前に拒否される
7. `EXPLAIN ANALYZE SELECT 1;`が拒否される
8. permission`644`のcredential fileが拒否される

---

## Phase 10 — Bridge Classification

**`CREDENTIAL_BRIDGE_BLOCKED_LOCAL_SETUP_REQUIRED`**

（`PRODUCTION_READONLY_CREDENTIAL_BRIDGE_READY`ではない。`CREDENTIAL_BRIDGE_UNSAFE`でもない）

理由: bridge機構自体は実装・ローカルE2Eテストで動作確認済みであり、
「Git/ログへ露出する方法しか使えない」状態（`UNSAFE`）ではない。
一方で、実Production credentialがまだユーザー側で設定されていない
ため、Production接続を伴うPhase 8以降は未実施のままである。これは
`READY`（即座にProduction接続可能）でも`UNSAFE`（安全な手段がない）
でもなく、**ユーザー側の一度きりのローカル設定を待っている**状態
であるため、この分類とした。

---

## Stop Conditions（該当確認）

- [ ] credentialをユーザーへチャットで要求する必要がある → 非該当（要求していない。ユーザーが自発的に設定する前提の仕組みのみ提供した）
- [ ] secretをechoする必要がある → 非該当
- [ ] repo内へsecret fileを置く必要がある → 非該当（`~/.config/kami-musubi/`はrepo外）
- [ ] Productionへwriteが必要 → 非該当
- [ ] Production migrationが必要 → 非該当
- [ ] Production restoreが必要 → 非該当
- [ ] connection methodがsecretをログに出す → 非該当（Phase 5-7で実装・確認済み）
- [ ] Codexから安全にcredentialを参照できない → **一部該当**。Candidate A（shell env var）は不可と実測確定。Candidate B（file）は実装・動作確認済みで可能
- [ ] Production migration stateが変わっている → 未評価（Production未接続のため確認不能）

---

## 絶対禁止の遵守確認

- [x] Production migrate禁止（遵守）
- [x] Production restore禁止（遵守）
- [x] Production DB write禁止（遵守、接続自体していない）
- [x] Environment変更禁止（遵守）
- [x] Render env変更禁止（遵守）
- [x] Supabase env変更禁止（遵守）
- [x] credential commit禁止（遵守。テンプレートのみ配置、実値は一切扱っていない）
- [x] credential PR掲載禁止（遵守）
- [x] credential docs掲載禁止（遵守。本ドキュメントに実credential値・host名・ユーザー名等は一切記載していない）
- [x] credential console表示禁止（遵守。全script実行ログを確認したが、値の露出はなし）
- [x] Production signup禁止（遵守）
- [x] Batch 8開始禁止（遵守）
- [x] PR merge禁止（本監査ではPR作成のみ行い、mergeはしない）

---

## Mother Shipへの最終報告

1. **develop SHA**: `85562497`（変化なし）
2. **採用credential bridge方式**: Candidate B（repo外local secret file、`~/.config/kami-musubi/production-db.env`）。Candidate A（shell env var）はAI駆動セッションから機能しないことを実測で確認したため不採用
3. **secret保存場所のカテゴリ**: リポジトリ外のユーザーホームディレクトリ配下（`~/.config/`）、permission 600必須
4. **credential値を表示していないこと**: 確認済み（Phase 5・9）
5. **Git管理外確認**: 確認済み（`git status`が`fatal: outside repository`を返す、Phase 9）
6. **Codexから参照成功/失敗**: **成功**（fake local credentialでのend-to-endテストで実証。実Production credentialではまだ未実施）
7. **SELECT-only接続成功/失敗**: **local fake credentialでは成功**。**Production credentialではまだ未実施**（ユーザー側のローカル設定待ち）
8. **Production users latest**: 未取得（Production未接続）
9. **Production temples latest**: 未取得（Production未接続）
10. **leakage audit結果**: 問題なし（Phase 9）
11. **classification**: `CREDENTIAL_BRIDGE_BLOCKED_LOCAL_SETUP_REQUIRED`
12. **Real Production Backup Gate再開可否**: ユーザーが`~/.config/kami-musubi/production-db.env.example`をコピーして実値を設定し`chmod 600`した後、再開可能。設定完了後は`scripts/migration_safety/check_credential_presence.sh`で存在確認してから`docs/audit/real-production-backup-restore-gate.md`のPhase 4以降を再開できる
13. **remaining risks**: (a) bridge機構自体はローカルでのみ検証済みで、実Production環境（実際のSupabase接続文字列の形式・SSL要件等）との相性は未確認。(b) `roles.sql`のbest-effort restore同様、想定外のURL形式（例: Supabase特有のconnection pooling URL）が来た場合の`pg_env_exports()`の挙動は未検証
14. **PR番号**: 本セクションはPR作成後に更新する
15. **CI状態**: 本セクションはCI確認後に更新する

credential値は上記のいずれにも含まれていない。

## Repository Changes

- `scripts/migration_safety/guard.py`: `describe_url_shape()`・`is_readonly_sql()`・`pg_env_exports()`とそのCLIサブコマンドを追加
- `scripts/migration_safety/check_credential_presence.sh`: 新規
- `scripts/migration_safety/readonly_query.sh`: 新規
- `scripts/migration_safety/tests/test_guard.py`: 新規関数のunit test 29件を追加（18件→47件）
- `scripts/migration_safety/tests/test_credential_bridge_e2e.sh`: 新規（fake local credentialのみ使用）
- `scripts/migration_safety/README.md`: 「Credential Bridge」節を新規追加、Manual Backup Route手順を更新
- `docs/audit/production-readonly-credential-bridge.md`: 本ドキュメント（新規）
- リポジトリ外: `~/.config/kami-musubi/production-db.env.example`（テンプレートのみ、実値なし。リポジトリの一部ではないためgit管理外）
- 既存の`dump_readonly.sh`/`restore_isolated.sh`本体のロジックへの変更: なし
