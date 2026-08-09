> **Status: Active — Phase 0/1/2完了、Phase 2でSTOP
> （安全に利用可能なProduction接続情報が依然として存在しない）**
>
> **Classification: `MANUAL_BACKUP_BLOCKED_CREDENTIAL_ACCESS`**
>
> 本ドキュメントは、`scripts/migration_safety/`ツール（PR #2327でdevelopへ
> merge済み）を使った実Production dump/restore監査の記録である。
> **Production DBへは一切接続していない。dump取得も実行していない。
> restoreも実行していない。Environment変更も一切していない。
> Production write = 0。**

# Real Production Backup Gate — Production dump / isolated restore 実測

## Phase 0 — Base State

| 項目 | 結果 |
|---|---|
| develop checkout | 完了（既に`develop`ブランチ） |
| `git fetch` + `git merge --ff-only origin/develop` | 完了（実行時点で既にup to date） |
| working tree | clean |
| develop HEAD SHA | `42749353...`（PR #2327、`scripts/migration_safety/`追加のsquash merge commit） |
| `scripts/migration_safety/`のdevelop存在確認 | 確認済み |
| `docs/audit/migration-safety-tooling.md`確認 | 読了 |
| `scripts/migration_safety/README.md`確認 | 読了 |
| migration_safety tooling自体の差分確認 | `git diff origin/develop -- scripts/migration_safety/ docs/audit/migration-safety-tooling.md`で差分なしを確認（前回実装時点から変更なし） |

---

## Phase 1 — Tooling確認（コード変更なし、読むのみ）

### guard（`scripts/migration_safety/guard.py`）

- restore target allow-list条件: host∈{`localhost`,`127.0.0.1`,`::1`} かつ dbname に `audit`/`restore_test`/`migration_safety` のいずれかを含み、かつ`jinja_db`等の既存local dev DB名でないこと。**実装を再読し、条件が変更されていないことを確認した**
- Production host（実際のhostnameは不明だが、少なくとも上記allow-listに含まれないあらゆるhost）をrestore先として拒否できる構造であることをコードレベルで再確認した（allow-listの外は無条件でblock）
- protected local DB（`jinja_db`/`jinja_app_dev`/`jinja_test`/`postgres`/`template0`/`template1`）を拒否できることを再確認した

### dump（`scripts/migration_safety/dump_readonly.sh`）

- Production DBにwriteしない構造: `pg_dumpall --roles-only`・`pg_dump --schema-only`・`pg_dump --data-only`のみを使用し、いずれもread-only相当のコマンドであることを再確認した
- connection URLを明示引数（`$1`）で受け、デフォルト値を持たないことを再確認した
- dump保存先を明示引数（`$2`）で指定し、`guard.py check-dump-path`でrepo外であることを強制することを再確認した
- `PG_DUMP_BIN`/`PG_DUMPALL_BIN`のbinary override機構を再確認した

### restore（`scripts/migration_safety/restore_isolated.sh`）

- `guard.py check-restore-target`を実行し、失敗時は`exit 1`でrestore本体（`psql`呼び出し）に到達しないことをコードで確認した
- local isolated DB以外（allow-list外のhost、または未markedなdbname）を拒否する構造を再確認した
- public schema handling: `grep -v '^CREATE SCHEMA public;$'`でdump内の重複`CREATE SCHEMA`行を除去してから適用する実装を再確認した
- extension handling: `CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS pg_trgm;`をschema適用前に実行する実装を再確認した

### SQL

- `sql/migration_state.sql`・`sql/pre_migration_snapshot.sql`・`sql/post_migration_verification.sql`をすべて再読し、いずれもSELECT-onlyであることを確認した（`INSERT`/`UPDATE`/`DELETE`/`ALTER`/`CREATE`/`DROP`のいずれも含まれない）

### Runbook

- `scripts/migration_safety/README.md`を再読し、Manual Backup Route / Restore Verification Route / Pre-Migration Checklistの内容が今回の監査Phase設計と整合していることを確認した

**本Phaseではコード変更を一切行っていない。**

---

## Phase 2 — Production Connection Safety Gate（STOP）

以下を確認した（値は一切出力せず、キーの有無・値の形状のみを確認する
方法で実施。`docs/audit/production-manual-backup-restore-gate.md`
実施時と同一の方法論）:

| 確認対象 | 結果 |
|---|---|
| 本セッションのシェル環境変数（`DATABASE_URL`/`SUPABASE_*`/`DB_*`/`SERVICE_ROLE`/`ANON_KEY`等） | **存在せず** |
| `.env`/`.env.local`/`.env.dev`/`.env.pytest.local` | `DATABASE_URL`が存在する場合も宛先ホストはすべて`127.0.0.1`または`db`（docker-compose内部ホスト名）。Production Supabaseを指していない |
| `backend/.env.local`/`backend/.env.test`/`backend/.env.example`/`backend/.env.dev.old` | 同上、すべてローカル向け |
| `backend/.env.prod` | `DATABASE_URL`キー自体が存在しない（前回監査から変化なし） |
| `.env.render.example` | プレースホルダ値（パース不能・16文字）であり実際の接続情報ではない |
| `apps/web/.env`・`apps/web/.env.local`・`apps/mobile/.env` | `DATABASE_URL`キー自体が存在しない |
| Supabase専用のMCP tool・API連携 | 本セッションの利用可能tool一覧に存在せず（`ToolSearch`で再確認済み） |
| 新規ファイルの出現有無 | 前回監査（`docs/audit/production-manual-backup-restore-gate.md`実施時）以降、新規`.env*`ファイルは作成されていないことを確認した |

**結論: 前回監査（PR #2325）から状況は一切変わっておらず、本セッションが
安全に利用できるProduction接続情報は依然として存在しない。**

指示に明記された通り、この場合はユーザーへcredentialを要求せず、
既存の安全なローカル手段（環境変数・Git管理外`.env`参照等）だけを使う
という制約の範囲内で確認した結果、該当する手段が見つからなかったため、
**ここでSTOPする。**

Phase 4（Production Migration State Read-only Recheck）以降は、いずれも
Production接続を前提とするため、**すべて未着手のまま保留する。**

---

## Phase 3（部分実施: ローカル情報のみ）

Production接続前提部分（Production PostgreSQLのmajor version確認）は
Phase 2のblockingにより未実施。**ローカル側の情報のみ**、参考として記録する:

| 項目 | 値 |
|---|---|
| local `pg_dump --version` | `16.10 (Homebrew)` |
| local `pg_dumpall --version` | `16.10 (Homebrew)` |
| local `psql --version` | `16.10 (Homebrew)` |
| local Postgres **server**（dev DB、Productionではない）バージョン | `18.0 (Homebrew)` |
| version-matched代替binaryのローカル存在 | `/opt/homebrew/opt/postgresql@{14,15,16,18}/bin/`が利用可能（`PG_DUMP_BIN`等で指定可能） |

**Production PostgreSQLの実際のmajor versionは不明のまま**である。
実際にdump/restoreを試みる際は、この値をMother Ship側で確認し、
一致する`PG_DUMP_BIN`/`PG_DUMPALL_BIN`/`PSQL_BIN`を選定する必要がある
（`scripts/migration_safety/README.md`「Manual Backup Route」手順2を参照）。

---

## Phase 4〜17 — 未着手

Phase 2のblockingにより、以下はいずれも実施していない:

- Phase 4 — Production Migration State Read-only Recheck
- Phase 5 — Production Pre-Dump Snapshot
- Phase 6 — Dump Destination Safety（設計はREADMEに既存、実施は未着手）
- Phase 7 — Production Manual Dump
- Phase 8 — Isolated Restore DB作成
- Phase 9 — Real Production Dump Restore
- Phase 10 — Migration State一致確認
- Phase 11 — Schema一致確認
- Phase 12 — Aggregate Data一致確認
- Phase 13 — Structural Integrity
- Phase 14 — Optional Local Migration Drill
- Phase 15 — Cleanup（対象物が存在しないため該当なし）
- Phase 17 — Execution Gate Re-entry

これらは、Mother Ship側で安全なProduction接続情報が用意された時点で、
本Gateへ再度戻って着手する。

参考: `scripts/migration_safety/`のtoolingそのものは、ローカル隔離DB
のみを使ったend-to-endテスト（`docs/audit/migration-safety-tooling.md`）
で既に動作実績があるため、**Production接続情報さえ用意されれば、
Phase 4以降はこのRunbookに従ってすぐに着手できる状態にある。**

---

## Phase 16 — Backup Gate Final Classification

**`MANUAL_BACKUP_BLOCKED_CREDENTIAL_ACCESS`**

理由: 安全に利用可能なProduction接続情報が本セッションに一切存在しない
ため（Phase 2参照）。`docs/audit/production-manual-backup-restore-gate.md`
（PR #2325）から状況は変化していない。

---

## Phase 18 — Documentation

本ドキュメント自体がPhase 18の成果物である。

---

## Phase 19 — Git / PR

本監査はdocs-onlyである。**tooling自体のバグは発見されなかった**
（Phase 1の再読レベルでは、既存のend-to-end検証結果と矛盾する点は
見つからなかった）ため、tooling修正は行っていない。

---

## Stop Conditions（該当確認）

- [x] credentialをユーザーへ要求する必要がある → **該当。ただし指示に従い実際には要求せず、`MANUAL_BACKUP_BLOCKED_CREDENTIAL_ACCESS`として本監査をここで終了した**
- [ ] Productionへのwriteが必要 → 非該当
- [ ] Production migrationが必要 → 非該当
- [ ] Production restoreが必要 → 非該当
- [ ] Production migration stateが変わっている → **未確認**（Production接続自体をしていないため確認不能。前回Mother Ship提供値`users=0005`/`temples=0089`をそのまま引き継ぐ）
- [ ] compatible pg_dump/psqlがない → 非該当（Production版に接続していないため評価不能。ただしローカルには`postgresql@14/15/16/18`が揃っており、判明次第対応可能）
- [ ] dump destinationがrepo内 → 非該当（dump自体を取得していない）
- [ ] restore destination安全性不明 → 非該当（restore自体を実施していない）
- [ ] guardがFAIL → 非該当（Phase 1で再読のみ、実行はしていない。前回end-to-endテストではPASS実績あり）
- [ ] dumpにcredential露出 → 非該当（dump自体を取得していない）
- [ ] restoreで重大error → 非該当（restore自体を実施していない）
- [ ] aggregate mismatch → 非該当（比較自体を実施していない）
- [ ] schema mismatch → 非該当（比較自体を実施していない）
- [ ] Gitへdumpを入れる必要がある → 非該当

---

## 絶対禁止の遵守確認

- [x] Production migrate禁止（遵守）
- [x] Production restore禁止（遵守）
- [x] Production DB write禁止（遵守、接続自体していない）
- [x] Environment変更禁止（遵守）
- [x] `RUN_MIGRATIONS_ON_START`変更禁止（遵守）
- [x] Production signup禁止（遵守）
- [x] Batch 8開始禁止（遵守）
- [x] dump commit禁止（遵守、dump自体を取得していない）
- [x] credential commit禁止（遵守）
- [x] PR merge禁止（本監査ではPR作成のみ行い、mergeはしない）

---

## Mother Shipへの最終報告

1. **develop SHA**: `42749353...`（PR #2327反映済み、変化なし）
2. **Production migration state**: users=`0005`、temples=`0089`（前回提供値を引き継ぎ、本監査では独自に再確認していない）
3. **backup tool**: `scripts/migration_safety/dump_readonly.sh`（plain `pg_dump`/`pg_dumpall`ベース）を使用予定として確認済み。まだ使用していない
4. **Production dump success/fail**: **未実施**（credential access blockedのため着手前でSTOP）
5. **Production write 0確認**: **0（接続自体していないため確実に0）**
6. **dump file存在/size確認**: **該当なし**（dump未取得）
7. **isolated restore success/fail**: **未実施**
8. **restored migration state**: **該当なし**
9. **schema一致**: **該当なし**
10. **aggregate counts一致**: **該当なし**
11. **structural verification範囲**: **該当なし**（`NOT_FULLY_VERIFIED`にすら至っていない、Phase自体未着手）
12. **Backup Gate classification**: **`MANUAL_BACKUP_BLOCKED_CREDENTIAL_ACCESS`**
13. **Execution Gate再開可否**: **不可**。`docs/audit/production-migration-execution-gate.md`のPhase 1ルール（Backup GateがPASS相当でない場合、即STOP）に従い、本Gateが前進するまでExecution Gateも再開しない
14. **remaining risks**: 最大のriskは変わらず「migration直前に安全に復元できるbackupが実証されていないこと」。tooling自体は準備完了（ローカルでend-to-end動作実績あり）だが、Production接続情報がない限り実証できない
15. **PR番号**: 本セクションはPR作成後に更新する
16. **CI状態**: 本セクションはCI確認後に更新する

## 次にMother Shipが用意すべきもの

変わらず: Mother Ship自身のローカル環境でread-only Production接続情報を
用意し、チャット以外の安全な経路（環境変数として実行環境に設定する等）
で本セッションが利用できるようにする必要がある。用意でき次第、
`scripts/migration_safety/README.md`のRunbookに従いPhase 4以降を
すぐに再開できる。

## Repository Changes

- `docs/audit/real-production-backup-restore-gate.md`: 本ドキュメント（新規）
- 上記以外の変更なし。tooling自体への変更なし（バグが見つからなかったため）
