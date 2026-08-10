> **Status: Stage 1（`users 0006`）・Stage 2（`temples 0090`）はPASS。
> Stage 3初回試行（`temples 0091`）は失敗（`GEOSException`、atomic
> rollback、production変化なし）。remediation（PR #2337、
> `docs/audit/temples-0091-production-remediation.md`、
> `TEMPLES_0091_REMEDIATION_READY`）を経て、Stage 3 Retryで
> `temples 0091`は成功（`TEMPLES_0091_RETRY_PASS`）。**Stage 4で
> `temples 0092`も成功（`TEMPLES_0092_EXECUTION_PASS`）。`temples 0093`
> は未実行のまま停止中。次のアクションはMother Ship判断待ち。**
>
> 本ドキュメントは**正本**である。`docs/audit/
> production-migration-execution-gate.md`・`production-migration-go-no-go-final.md`・
> `local-mac-direct-migration-execution-safety.md`はいずれも背景調査・
> 実測記録として引き続き有効だが、**実際に人間が上から順に実行する
> 手順としては本ドキュメントを使うこと。**
>
> **Execution Recordは本ドキュメント末尾の
> 「Execution Record — Stage 1: `users 0006`」・
> 「Execution Record — Stage 2: `temples 0090`」・
> 「Execution Record — Stage 3: `temples 0091`（失敗・STOP）」・
> 「Execution Record — Stage 3 Retry: `temples 0091`（成功・PASS）」・
> 「Execution Record — Stage 4: `temples 0092`（成功・PASS）」の
> 各節を参照。失敗記録は履歴として削除・改変していない。**
>
> **Production migrationはStage 3 Retryで`temples 0091`、Stage 4で
> `temples 0092`を実行した（write計2件）。`temples 0093`は未実行のまま。**
> それ以外はread-only verification（`showmigrations`・`migrate --plan`・
> `readonly_query.sh`経由のSELECT）のみ。

# Production Migration — Local Direct Execution Final Gate & Runbook

## Phase 1 — develop同期

| 項目 | 結果 |
|---|---|
| develop checkout / 同期 | 完了、既にup to date |
| PR #2332がdevelopへ反映済み | 確認済み（`6c4d9260`） |
| working tree | clean |
| develop HEAD SHA | `6c4d9260...` |

---

## Phase 2 — Execution Environment再確認

| 項目 | 結果 |
|---|---|
| `python --version` | `Python 3.11.13` |
| Django version | `5.2.16`（requirements.txtと一致） |
| psycopg version | `3.3.4`（requirements.txtと一致） |
| `backend/manage.py`存在 | 確認済み |
| settings module | `shrine_project.settings` |
| database backend（`USE_GIS=1`明示時） | `django.contrib.gis.db.backends.postgis`（実測確認済み） |
| USE_GIS方針 | **`USE_GIS=1`を実行コマンドで明示する**（default Trueへの暗黙依存はしない。実測で明示`1`と未設定default Trueが同一の`ENGINE`・`USE_GIS=True`を返すことを確認済み） |
| `manage.py check`（DEBUG=0/USE_GIS=1明示） | `System check identified no issues (0 silenced).` |

---

## Phase 3 — Credential Isolation Contract

| 項目 | 結果 |
|---|---|
| credential file | `~/.config/kami-musubi/production-db.env`（repo外） |
| permission | `600`（確認済み） |
| Git管理対象 | 対象外（`git status`が`fatal: outside repository`を返すことを確認） |
| `DATABASE_URL` set | `VAR_SET=1`（`check_credential_presence.sh`で確認、値は非表示） |
| `.env.local`との優先順位 | **exportされた`DATABASE_URL`が優先されることを実測で確認済み**（ダミーhost `precedence-test-host.invalid`を使い、`settings.DATABASES['default']`がその値を反映することを直接確認。実際のcredential値は一切使用していない） |
| credential値のcommand-line引数化 | 回避済み。`readonly_query.sh`はcredentialを`PG*`環境変数へ変換し、`psql`にconnection stringを渡さない設計（既存実装） |

---

## Phase 4 — Production Baseline Recheck（実測、read-only）

`scripts/migration_safety/sql/pre_migration_snapshot.sql`を
`readonly_query.sh`経由で実行:

| 確認項目 | 結果 |
|---|---|
| `users_0006_applied` | `false` |
| `temples_0093_applied` | `false` |
| aggregate snapshot | `auth_user=1`/`userprofile=1`/`shrine=105`/`favorite=0`/`visit=2`/`goriyaku_relation=280`（既知baselineと完全一致） |
| Knowledge table存在 | 0件（対象5テーブルいずれも不存在） |
| `users_userprofile`新規4カラム存在 | 0件（いずれも不存在） |
| snapshot取得時刻 | `2026-08-09 11:53:59.170123+00`（UTC） |
| 全8 app migration state | `admin=0003`/`auth=0012`/`contenttypes=0002`/`favorites=0002`/`sessions=0001`/`temples=0089`/`token_blacklist=0013`/`users=0005`（既知baselineと完全一致） |

**driftは1件も検出されなかった。`FINAL_GATE = STOP_PRODUCTION_DRIFT`には該当しない。**

---

## Phase 5 — Django Read-Only Execution Recheck（実測、`--plan`のみ、DB書き込みなし）

`USE_GIS=1`/`DEBUG=0`を明示し、credential bridgeパターンで
Productionへ接続して以下を実行した:

- `manage.py showmigrations users` → `0001`-`0005`が`[X]`、`0006`が`[ ]`
- `manage.py showmigrations temples` → `0001`-`0089`が`[X]`、`0090`-`0093`が`[ ]`
- `manage.py migrate users 0006 --plan` → `AddField`×4（`birthday`/`birth_time`/`birth_place`/`worship_style`）
- `manage.py migrate temples 0090 --plan` → `0090`（Raw Python operation）のみ
- `manage.py migrate temples 0091 --plan` → `0090`+`0091`（累積、まだ何も適用されていないため）
- `manage.py migrate temples 0092 --plan` → `0090`+`0091`+`0092`（`AddField`×2: `shrinereflection`/`visit`への`thread`）
- `manage.py migrate temples 0093 --plan` → `0090`+`0091`+`0092`+`0093`（`CreateModel`×3）

**注記**: `--plan`は「現在の実DB状態から指定targetまでの累積計画」を表示する。
今回はいずれの呼び出しも実際にDBを変更していないため、後の呼び出しほど
累積される件数が増えて見える（これはDjangoの標準的な挙動であり、
異常ではない）。**すべての結果は既存監査（`production-migration-execution-gate.md`・
`production-migration-go-no-go-final.md`）の想定と完全に一致した。**

**Production writeは0件。**

---

## Phase 6 — Dependency Revalidation

| migration | TARGET | DEPENDENCIES | OPERATIONS | CROSS_APP_EFFECT |
|---|---|---|---|---|
| `users 0006` | `users`アプリのみ | `users.0005`のみ | `AddField`×4 | なし |
| `temples 0090` | `temples`アプリのみ | `temples.0089`のみ | `RunPython`（self-guarding） | なし |
| `temples 0091` | `temples`アプリのみ | `temples.0090`のみ | `RunPython`（self-guarding） | なし |
| `temples 0092` | `temples`アプリのみ | `temples.0091`のみ | `AddField`×2（FK先=`temples.conciergethread`、同一app内） | なし |
| `temples 0093` | `temples`アプリのみ | `temples.0092`のみ | `CreateModel`×3 + M2M | なし |

**結論**: `users 0006`は`temples`を一切要求しない。`temples 0090`は
`users 0006`を要求しない。`temples`側は`0090→0091→0092→0093`の完全
線形chainであり、分岐・他appへの依存は一切ない。他appの未適用
migrationを暗黙に巻き込むことはない（Phase 4で全8 app中`users`/
`temples`以外に未適用migrationが存在しないことも確認済み）。

---

## Phase 7 — Exact Execution Command（作成のみ、未実行）

各migrationは1 migration = 1 commandとして実行する。**実際のcommandには
credential値を直接埋め込まない**——credential fileを同一コマンド内で
`source`し、`readonly_query.sh`と同じ「値を変数展開した状態で
Pythonプロセスへ渡すが、シェル履歴・ログには残さない」設計を踏襲する。

### 実行時の必須環境

```
DEBUG=0
USE_GIS=1
SECRET_KEY=<任意の値でよい。migrateの動作には影響しない>
working directory: backend/
Python: backend/.venv（requirements.txt同期済みであること）
```

### コマンド形（credential部分はplaceholderのまま記載。実行時に
`~/.config/kami-musubi/production-db.env`をsourceして展開する）

```bash
cd backend
( set -a; source ~/.config/kami-musubi/production-db.env; set +a; \
  DEBUG=0 USE_GIS=1 SECRET_KEY="<any-value>" \
  .venv/bin/python3 manage.py migrate users 0006 --noinput )
```

以下、`temples 0090`〜`0093`も同型（`migrate temples 00XX --noinput`）。

**bare `python manage.py migrate`は使用しない。** 各コマンドは必ず
`<app> <migration_target>`を明示する。

---

## Phase 8 — Verification Contract

各migration実行直後、次のmigrationへ進む前に以下を確認する
（`readonly_query.sh` + 該当SQL、またはPhase 5と同型の`showmigrations`）。

### `users 0006`後
- [ ] `django_migrations`で`users`最新 = `0006`
- [ ] `birthday`/`birth_time`/`birth_place`/`worship_style`列すべて存在
- [ ] `auth_user`件数 = `1`維持
- [ ] `users_userprofile`件数 = `1`維持

**PASSしなければtemplesへ進まない。**

### `temples 0090`後
- [ ] `django_migrations`で`temples`最新 = `0090`
- [ ] aggregate counts（`shrine=105`/`goriyaku_relation≥280`/`visit=2`/`favorite=0`）維持

### `temples 0091`後
- [ ] `django_migrations`で`temples`最新 = `0091`
- [ ] aggregate counts維持

### `temples 0092`後
- [ ] `django_migrations`で`temples`最新 = `0092`
- [ ] aggregate counts維持

### `temples 0093`後
- [ ] `django_migrations`で`temples`最新 = `0093`
- [ ] Knowledge 5 table（`temples_shrineknowledgesource`/`temples_shrinedeity`/`temples_shrinehistory`/`temples_shrinedeity_sources`/`temples_shrinehistory_sources`）すべて存在
- [ ] aggregate counts維持

---

## Phase 9 — Runtime Verification（DB Gateとは別軸）

DB側の確認とは独立して、以下のRuntime QAを整理する
（**DB GateとRuntime Gateを混同しない**）:

| 確認項目 | 実施タイミング | 理由 |
|---|---|---|
| `/healthz/` | 全migration完了後 | release SHAとサービス稼働の基本確認 |
| `/api/auth/me` | `users 0006`完了後（temples着手前でも可） | `users/apps.py`の`ensure_profile`signalとschemaの不整合（既知issue）が解消したことの確認 |
| MyPage | `users 0006`完了後 | 同上、UI側の実動作確認 |
| Shrine detail | 全migration完了後 | temples側の変更がSSR/APIへ悪影響を与えていないか |
| recommendation関連endpoint | 全migration完了後 | `goriyaku_tags`関連の変更が既存機能に影響しないか |

これらはいずれも**本セッションでは未実施**（DB専用credential
bridgeの範囲外、認証済みセッションが必要なため）。実行はMother Ship
またはRuntime確認が可能な担当者が行う。

---

## Phase 10 — STOP Conditions

以下のいずれかに該当した場合、即STOPし次のmigrationへ進まない:

- credential check failure（`check_credential_presence.sh`が`VAR_SET=0`または`BLOCKED`を返す）
- Production baseline drift（Phase 4の再実行結果が変化）
- unexpected pending migration（`users`/`temples`以外にpendingが出現）
- `USE_GIS`の不一致（明示`1`のはずが実際は異なる値で動いている）
- package version mismatch（`django.get_version()`が`5.2.16`と異なる、`psycopg.__version__`が`3.3.4`と異なる）
- `manage.py check`失敗
- `migrate --plan`の内容が本Runbook記載の内容と異なる
- dependency graphの変化（migration file自体が変更されている）
- migration commandがnon-zero exit
- verification query不一致
- aggregate count予期しない変化
- 想定外のtable/column出現
- 接続先が本当にProductionか不明（`describe-url-shape`等で`has_host`等の基本形状すら怪しい場合）
- credential露出（stdout/stderr/ログにcredential値や接続hostnameが出た場合。`docs/audit/production-migration-go-no-go-final.md`で発見した`dump_readonly.sh`の既知issueを踏まえ、migrate系コマンドの標準出力・エラー出力を都度確認すること）
- migration target typo（app名・migration名の入力ミス）
- bare `migrate`を誤って使う可能性に気づいた場合

---

## Phase 11 — Recovery Classification

migrationごとに、失敗時は以下の順で状態を観測してから分類する
（自動rollbackはしない。「とりあえずmigrateを再実行」は禁止）:

1. どのmigrationで失敗したか
2. `django_migrations`へ記録されたか
3. schemaが部分適用されたか
4. dataが維持されているか
5. runtimeが動くか

| 状況 | 分類 |
|---|---|
| 原因不明、影響範囲が読めない | `STOP_AND_INVESTIGATE` |
| 安全にreverseできると判断できる（例: `AddField`のみで実データ書き込み前に失敗） | `DJANGO_MIGRATION_ROLLBACK_CANDIDATE`（`migrate <app> <前のmigration>`） |
| schemaとmigration stateの記録が食い違っている | `MANUAL_SCHEMA_RECONCILIATION_REQUIRED` |
| データ破損・aggregate count減少等、Django migration機構では対処できない事故 | `MANUAL_BACKUP_RESTORE_CANDIDATE`（最終手段。`docs/audit/real-production-backup-restore-gate.md`のRunbookに従う） |

---

## Phase 12 — Execution Runbook（人間が上から実行する手順）

| STEP | 内容 | COMMAND | EXPECTED | PASS条件 | STOP条件 |
|---|---|---|---|---|---|
| STEP 0 | Preflight | Phase 3-5の再実行（credential presence・baseline snapshot・`showmigrations`） | Phase 4/5と同じ結果 | 全項目一致 | 1件でも不一致ならSTOP |
| STEP 1 | `users 0006`適用 | `migrate users 0006 --noinput`（Phase 7の形） | exit 0 | エラーなし | non-zero exitでSTOP |
| STEP 2 | `users 0006`検証 | Phase 8「`users 0006`後」の4項目 | 全項目PASS | 全項目一致 | 1件でも不一致ならSTOP、templesへ進まない |
| STEP 3 | `temples 0090`適用 | `migrate temples 0090 --noinput` | exit 0 | エラーなし | non-zero exitでSTOP |
| STEP 4 | `0090`検証 | Phase 8該当項目 | 全項目PASS | 一致 | 不一致ならSTOP |
| STEP 5 | `temples 0091`適用 | `migrate temples 0091 --noinput` | exit 0 | エラーなし | non-zero exitでSTOP |
| STEP 6 | `0091`検証 | Phase 8該当項目 | 全項目PASS | 一致 | 不一致ならSTOP |
| STEP 7 | `temples 0092`適用 | `migrate temples 0092 --noinput` | exit 0 | エラーなし | non-zero exitでSTOP |
| STEP 8 | `0092`検証 | Phase 8該当項目 | 全項目PASS | 一致 | 不一致ならSTOP |
| STEP 9 | `temples 0093`適用 | `migrate temples 0093 --noinput` | exit 0 | エラーなし | non-zero exitでSTOP |
| STEP 10 | Final DB検証 | Phase 8「`temples 0093`後」全項目 + `sql/post_migration_verification.sql`全体 | 全項目PASS | 一致 | 不一致ならSTOP、Phase 11へ |
| STEP 11 | Runtime QA | Phase 9記載の5項目 | 500エラーなし、Knowledge欠落errorなし | 全項目PASS | 異常ならSTOP、Phase 11へ |
| STEP 12 | 完了判定 | STEP 1-11すべてPASSしたことの確認 | — | 全STEP PASS | — |

**このRunbookは実行するために作成したが、本PRでは実行していない。**

---

## Phase 13 — Final Classification

**`LOCAL_DIRECT_EXECUTION_GO_READY_WITH_LIMITATIONS`**

### GO_READYと判断する根拠
- Phase 1-6のすべてが実測で確認済み（推測・past auditの盲信ではない）
- Phase 5でDjango自身の実行パス（GDAL/GEOS/postgis backend込み）がProductionへ実際に到達できることを`--plan`で確認
- credential isolation・precedence・非露出の設計が実測で確認済み
- STOP conditions・recovery classification・stepwise runbookまで具体化済み

### `WITH_LIMITATIONS`とする理由（無条件`GO_READY`ではない理由）
1. **実際の書き込み実行（`--noinput`、`--plan`を外した状態）は一度も
   試みていない。** `--plan`はDBに接続して計画を算出するが、実際の
   DDL/DMLは発行しない。最初の実書き込みには依然として初回特有の
   不確実性が残る
2. Phase 9のRuntime QAは未実施のまま（DB専用credential bridgeの範囲外）
3. `docs/audit/production-migration-go-no-go-final.md`で発見した
   `dump_readonly.sh`のhostname非マスク問題は未修正のまま
   （**ただし本Runbookの`migrate`系コマンド自体はこの問題を持つ
   scriptを使用しない**ため、直接の影響はない。念のためPhase 10の
   STOP conditionsに出力監視を含めた）
4. `requirements-dev.txt`の`pytest`/`pytest-dotenv`衝突は未修正（`manage.py migrate`実行には無関係と確認済み）
5. ネットワーク切断時の挙動は依然未検証（`docs/audit/
   local-mac-direct-migration-execution-safety.md`で既に指摘済みの
   既知gap）

**Codexはこれを最終決定としない。Mother Shipが最終判断すること。**

---

## Stop Conditions（本PRでの遵守確認）

- [x] Production migrate禁止（遵守。`--plan`/`showmigrations`のみ実行）
- [x] `RUN_MIGRATIONS_ON_START=1`にしない（遵守）
- [x] schema変更SQL/INSERT/UPDATE/DELETE/ALTER/CREATE/DROP/TRUNCATE禁止（遵守）
- [x] credential値をstdout/stderr/git diff/document/PR/commit/test fixtureへ出さない（遵守。すべての出力を目視確認し、値・hostnameのいずれも含まれないことを確認した）
- [x] Production固有hostname/user/passwordをhardcodeしない（遵守。本ドキュメントにはplaceholderのみ記載）

## Repository Changes

- `docs/audit/production-migration-local-execution-runbook.md`: 本ドキュメント（新規、正本）
- 上記以外の変更なし。Production DBへのwriteは0件

## 次にMother Shipが判断すること（Stage 0時点の記録、以下に更新）

1. ~~`LOCAL_DIRECT_EXECUTION_GO_READY_WITH_LIMITATIONS`を受けて、実際に
   STEP 0から実行を開始するか~~ → **Stage 1（`users 0006`）実行に
   ついてはMother Shipが実行を指示し、完了した**
2. 実行者: このセッション（Codex/Claude、local Mac direct execution）
3. Phase 9のRuntime QAを誰が・いつ実施するか → **Stage 1では未実施
   （`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`、後述）。引き続き未確定**
4. 残存limitations: Stage 1実行により「実際の書き込み実行を一度も
   試みていない」という limitation は解消された。残りは
   Runtime QA未実施・`dump_readonly.sh`のhostname非マスク・
   `pytest`/`pytest-dotenv`衝突・ネットワーク切断時挙動未検証の4点
5. **Stage 3初回試行は`GEOSException`で失敗**（`TEMPLES_0091_EXECUTION_STOP`）
   → remediation（PR #2337、`TEMPLES_0091_REMEDIATION_READY`）を経て、
   **Stage 3 Retryで`temples 0091`はexit 0で成功（`TEMPLES_0091_RETRY_PASS`）**。
   `temples 0092`/`0093`は引き続き未実行のまま、Mother Ship判断待ち
6. 認証済みRuntime QA（`/api/auth/me`・MyPage等）は依然
   `NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`のまま。DB-level verificationは
   Stage 3 Retryで全項目PASS済み

---

## Execution Record — Stage 1: `users 0006`

本Stageは`docs/audit/production-migration-local-execution-runbook.md`
（本ドキュメント）のRunbookに従い、STEP 0〜2相当を実施した記録である。
**`temples 0090`以降は意図的に未実行のまま停止している。**

### 実行環境

| 項目 | 値 |
|---|---|
| develop HEAD SHA（実行時点） | `afed3ac3...`（PR #2333反映済み） |
| Python | `3.11.13` |
| Django | `5.2.16` |
| psycopg | `3.3.4` |
| `DEBUG` | `0`（明示指定） |
| `USE_GIS` | `1`（明示指定） |
| 実行方式 | Local Mac direct execution（`docs/audit/
  local-mac-direct-migration-execution-safety.md`で安全性監査済み） |
| credential | `~/.config/kami-musubi/production-db.env`経由（値は一切表示せず） |

### Credential Gate / Preflight結果

- [x] `check_credential_presence.sh` → `VAR_SET=1`、shape正常
- [x] 実行直前snapshot（`pre_migration_snapshot.sql`）: `users_0006_applied=false`・
  `temples_0093_applied=false`・aggregate（`auth_user=1`/`userprofile=1`/
  `shrine=105`/`favorite=0`/`visit=2`/`goriyaku_relation=280`）が
  既知baselineと完全一致。snapshot時刻`2026-08-09 12:01:35.845917+00`
- [x] 全8 app migration state再確認: baselineと完全一致、drift 0件
- [x] `migrate users 0006 --plan`（実行直前・最終確認）: `AddField`×4
  （`birthday`/`birth_time`/`birth_place`/`worship_style`）、Runbook
  記載内容と完全一致

### 実行

| 項目 | 値 |
|---|---|
| コマンド | `python manage.py migrate users 0006 --noinput`（app-scoped、bare `migrate`は不使用） |
| 実行開始 | `2026-08-09T12:02:09Z` |
| 実行終了 | `2026-08-09T12:02:10Z` |
| 出力 | `Applying users.0006_userprofile_birth_profile_fields... OK` |
| exit status | `0` |

`temples`側のmigrationは一切実行していない。

### 実行後verification

- [x] `django_migrations`: `users`最新 = `0006_userprofile_birth_profile_fields`（applied `2026-08-09 12:02:10.455239+00`）
- [x] `users_userprofile`カラム: `birthday`/`birth_time`/`birth_place`/`worship_style`の4件すべて存在
- [x] Knowledge table: 0件存在（`temples 0090-0093`未実行のため期待通り）
- [x] aggregate counts: `auth_user=1`/`userprofile=1`/`shrine=105`/`favorite=0`/`visit=2`/`goriyaku_relation=280`——**実行前と完全一致、変化なし**
- [x] 全8 app migration state再確認: `users`のみ`0006`へ進み、**`temples`は`0089`のまま不変**であることを確認（`temples 0090`以降が意図せず適用されていないことを明示的に確認済み）
- [ ] Runtime QA（`/healthz/`・`/api/auth/me`・MyPage等）: **`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`**。`/healthz/`への読み取り専用GETを試行したが`503 Service Unavailable`（Render Free tierのsleep、または一時的な問題と推測されるが原因特定はしていない）。認証済みRuntime確認（`/api/auth/me`・MyPage）はDB専用credential bridgeの範囲外であり、本セッションからは実施不可

### Failure Handling

該当なし（migrationはexit 0で正常終了したため、Phase 12のfailure分類は発動していない）。

### Classification

**`USERS_0006_EXECUTION_PASS`**

根拠: migration exit 0、`users 0006` applied確認、期待schema存在確認、
aggregate不変確認、想定外schemaなし確認、`temples 0090-0093`が
引き続き未適用のままであることを確認——Phase 13の全条件を満たす。

### Production Write Summary

- **Production write: `users 0006` = EXECUTED**
- **temples Production writes: `0`**

---

## Execution Record — Stage 2: `temples 0090`

本Stageは正本Runbookに従い、STEP 3〜4相当を実施した記録である。
**`temples 0091`以降は意図的に未実行のまま停止している。**

### 実行環境

| 項目 | 値 |
|---|---|
| develop HEAD SHA（実行時点） | `8f015c7e...`（PR #2334反映済み） |
| Python | `3.11.13` |
| Django | `5.2.16` |
| psycopg | `3.3.4` |
| `DEBUG` | `0`（明示指定） |
| `USE_GIS` | `1`（明示指定） |
| 実行方式 | Local Mac direct execution |
| credential | `~/.config/kami-musubi/production-db.env`経由（値は一切表示せず） |

### Stage 1 State Recheck

- [x] `users`最新 = `0006_userprofile_birth_profile_fields`（不変）
- [x] `birthday`/`birth_time`/`birth_place`/`worship_style`の4列すべて存在（不変）
- [x] `temples`最新 = `0089_actionevent`（Stage 2実行前時点、不変）
- [x] 全8 app migration state: Stage 1完了時点から変化なし

### Fresh Pre-0090 Snapshot

- [x] aggregate: `auth_user=1`/`userprofile=1`/`shrine=105`/`favorite=0`/`visit=2`/`goriyaku_relation=280`（既知baselineと完全一致）。snapshot時刻`2026-08-09 12:11:57.334145+00`

### Fresh Backup（`users 0006`適用後の状態を含む）

**重要**: Stage 0時点のbackupは`users 0006`適用前のschemaであり、
そのままでは今回のrecovery pointとして不十分なため、`temples 0090`
実行直前に**新規fresh dump**を取得した。

| 項目 | 結果 |
|---|---|
| dump取得 | 成功 |
| client version | PostgreSQL 17（`postgresql@17`使用、Production `17.6`と一致） |
| `roles.sql` size | `5426` bytes |
| `schema.sql` size | `81650` bytes（Stage 0時点の`81494`より増加——`users 0006`の4カラム追加を反映） |
| `data.sql` size | `3843016` bytes |
| 保存先 | ユーザーホームディレクトリ配下、repo外（timestampディレクトリ、具体的pathは本ドキュメントに記載しない） |
| credential露出 | **なし**。前回Stage（`docs/audit/production-migration-go-no-go-final.md`で開示済み）で判明した`dump_readonly.sh`のhostname出力行を、今回は`grep -v`で意図的に抑制し、出力に一切含めなかった |

### `temples 0090` Migration File Recheck

- [x] ファイル名: `0090_add_rest_healing_tag_to_silent_shrines.py`（一致）
- [x] dependency: `temples.0089_actionevent`のみ（cross-app dependencyなし）
- [x] operation: `RunPython`のみ（`RunSQL`・`AddField`・`CreateModel`等のschema操作なし）
- [x] destructive operation: なし
- [x] reverse操作: 定義済み（対称的な`remove_rest_healing_tag_from_silent_shrines`）
- [x] 最終commit: `e0e59315`（2026-06-28）——現HEADより大幅に前、変更なし

### 実行前の実データ確認（推測ではなく実測）

`temples 0090`のRunPythonは`GoriyakuTag id=43`を対象4神社
（筑波山神社・榛名神社・森戸大明神・武蔵御嶽神社）の
`goriyaku_tags`へ追加する処理だが、**実行前に確認したところ
`GoriyakuTag id=43`はProductionに存在しなかった**（`tag_43_exists=false`）。
migration file自身が`GoriyakuTag.DoesNotExist`を`try/except`で
self-guardingしているため、**この時点で「実行してもno-opになる」
ことが実測で確定していた**（推測ではない）。

### `migrate --plan`（実行直前・最終確認）

```
Planned operations:
temples.0090_add_rest_healing_tag_to_silent_shrines
    Raw Python operation
```

Runbook記載内容と完全一致。

### 実行

| 項目 | 値 |
|---|---|
| コマンド | `python manage.py migrate temples 0090 --noinput`（app-scoped、bare `migrate`は不使用） |
| 実行開始 | `2026-08-09T12:13:29Z` |
| 実行終了 | `2026-08-09T12:13:30Z` |
| 出力 | `Applying temples.0090_add_rest_healing_tag_to_silent_shrines... OK` |
| exit status | `0` |

`temples 0091`以降は一切実行していない。

### 実行後verification

- [x] `django_migrations`: `temples`最新 = `0090_add_rest_healing_tag_to_silent_shrines`（applied `2026-08-09 12:13:30.066579+00`）
- [x] `temples 0091`/`0092`/`0093`: いずれも`django_migrations`に不存在（未適用のまま）
- [x] aggregate counts: `auth_user=1`/`userprofile=1`/`shrine=105`/`favorite=0`/`visit=2`/`goriyaku_relation=280`——**実行前と完全一致、変化なし**
- [x] `temples 0090`の期待効果確認: 対象4神社のいずれも`GoriyakuTag id=43`との関連付けが**作成されていない**ことを確認（`0`件）——事前予測（no-op）と完全に一致
- [x] `users 0006`回帰確認: `users`最新は`0006`のまま、4カラムすべて存在、`userprofile`件数`1`のまま——`temples 0090`によるuser側への影響は一切なし
- [x] Runtime QA: `/healthz/`が`{"ok": true, "release": "b286a557680c12343282c6e1e57a78f1be4bda43"}`を返し、backendが正常稼働中であることを確認（**前回Stageでは503だったが今回は成功**）。ただし認証済みQA（`/api/auth/me`・MyPage）はDB専用credential bridgeの範囲外であり、依然`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`

### Failure Handling

該当なし（migrationはexit 0で正常終了）。

### Classification

**`TEMPLES_0090_EXECUTION_PASS`**

根拠: migration exit 0、`temples 0090` applied確認、事前実測に基づく
期待効果（no-op）と実際の結果が完全一致、aggregate不変確認、
`users 0006`への回帰なし確認、`temples 0091-0093`が引き続き
未適用のままであることを確認——Phase 17の全条件を満たす。

### Production Write Summary（Stage 2時点の累積）

- **Production write: `temples 0090` = EXECUTED**
- **temples 0091 = NOT_EXECUTED**
- **temples 0092 = NOT_EXECUTED**
- **temples 0093 = NOT_EXECUTED**

---

## Execution Record — Stage 3: `temples 0091`（失敗・STOP）

**本Stageは失敗した。`temples 0091`は適用されていない。
`temples 0092`は実行していない。**

### 実行環境

| 項目 | 値 |
|---|---|
| develop HEAD SHA（実行時点） | `7eebd3c8...`（PR #2335反映済み） |
| Python | `3.11.13` |
| Django | `5.2.16` |
| psycopg | `3.3.4` |
| `DEBUG` | `0`（明示指定） |
| `USE_GIS` | `1`（明示指定） |

### Stage 2 State Recheck / Fresh Pre-0091 Snapshot / Fresh Backup

- [x] `users`最新 = `0006`（不変）、`temples`最新 = `0090`（不変）
- [x] aggregate: `auth_user=1`/`userprofile=1`/`shrine=105`/`favorite=0`/`visit=2`/`goriyaku_relation=280`（baselineと完全一致）。snapshot時刻`2026-08-09 12:23:04.717102+00`
- [x] fresh backup取得成功: `roles.sql=5426`/`schema.sql=81650`/`data.sql=3843102`bytes、repo外保存、hostname出力は抑制済み

### `temples 0091` Migration File Recheck

- [x] ファイル名: `0091_fill_missing_local_shrine_reason_facts.py`（一致）
- [x] dependency: `temples.0090_add_rest_healing_tag_to_silent_shrines`のみ
- [x] operation: `RunPython`のみ
- [x] 最終commit: `c5f2b3d5`（2026-07-04）——変更なし

### 実行前の実データ確認（推測ではなく実測） — 重要な発見

- [x] 対象2神社（`長太稲荷神社`・`給田六所神社`）の名前が**それぞれ重複して
  2件ずつ存在**することを発見（`長太稲荷神社`: id=21, id=103。
  `給田六所神社`: id=22, id=101）
- [x] `Shrine.Meta.ordering = ["-updated_at"]`のため、migrationの
  `.filter(name_jp=...).first()`は`updated_at`が新しい方
  （`長太稲荷神社`→id=103、`給田六所神社`→id=101）を確定的に対象とする
  ことを特定
- [x] tag `地域安泰`は`temples_goriyakutag`に**存在しない**ことを確認
  （`商売繁盛`/`五穀豊穣`/`家内安全`のみ存在）
- [x] id=101・id=103に既存のtag関連付けは0件であることを確認
- [x] 事前予測: id=103は`history_theme`="守り"+tag2件追加、id=101は
  `history_theme`="守り"+tag1件追加、`goriyaku_relation_count`は
  `280`→`283`になるはず、と推測ではなく実データに基づき確定していた

### `migrate --plan`（実行直前・最終確認）

```
Planned operations:
temples.0091_fill_missing_local_shrine_reason_facts
    Raw Python operation
```

### 実行

| 項目 | 値 |
|---|---|
| コマンド | `python manage.py migrate temples 0091 --noinput`（app-scoped、bare `migrate`は不使用） |
| 実行開始 | `2026-08-09T12:25:42Z` |
| 実行終了 | `2026-08-09T12:25:43Z` |
| exit status | **`1`（失敗）** |

### エラー内容

```
Applying temples.0091_fill_missing_local_shrine_reason_facts...ERROR django.contrib.gis: GEOS_ERROR:
...
File ".../temples/migrations/0091_fill_missing_local_shrine_reason_facts.py", line 24, in fill_missing_local_shrine_reason_facts
    shrine = Shrine.objects.filter(name_jp=item["name"]).first()
...
File ".../django/contrib/gis/db/backends/postgis/operations.py", line 424, in converter
    return None if value is None else GEOSGeometryBase(read(value), geom_class)
...
django.contrib.gis.geos.error.GEOSException: Error encountered checking Geometry returned from GEOS C function "GEOSWKBReader_readHEX_r".
```

credential・hostname・個人情報は含まれない（tracebackはファイルパス・
Djangoの内部コードパスのみ）。

### 根本原因分析

`docs/audit/production-migration-execution-gate.md`Phase 3で発見した
**temples migration lineageの歴史的分岐**が、今回初めて実際の失敗として
顕在化した。

- Django migrationの`RunPython`は`apps.get_model("temples", "Shrine")`
  経由で、**「公式`migrations/`チェーンの操作を`0091`まで積み上げた
  歴史的model state」**を使う。この歴史的state上のShrineは、
  `migrations/0025`〜`0033`（`enable_postgis_and_add_location`等）
  により`location`フィールドが**PostGIS GeometryField**として
  定義されている
- しかしProduction実DBの`temples_shrine.location`列は、実際には
  （`migrations_nogis`由来のため）**`text`型**である（本監査シリーズの
  過去Gateで既に実測確認済み）
- `Shrine.objects.filter(name_jp=...).first()`はShrineの全カラムを
  SELECTするため、ORMが`location`列の値をGEOS geometry objectへ
  変換しようとし、実際の値（text型の生データ）がWKB
  （Well-Known Binary）として解釈できず`GEOSException`が発生した
- **`temples 0090`が成功していた理由**: `0090`のRunPythonは
  `GoriyakuTag.objects.get(id=43)`が`DoesNotExist`で即座に`return`
  していたため、`Shrine.objects.filter(...)`が一度も実行されず、
  この問題を踏んでいなかった（偶然の回避であり、`0090`自体が
  この問題を解消していたわけではない）
- **`0091`はShrineクエリを2件、無条件に実行する**ため、最初の
  `.first()`呼び出しで即座に失敗した

**この問題は実行方式（local Mac / Render Shell / RUN_MIGRATIONS_ON_START
等）に依存しない。** `temples 0091`が現在のコードのまま`Shrine.objects`
経由でクエリを実行する限り、どの実行方式でも同じ`GEOSException`が
発生すると考えられる。

### Failure Handling — 分類

**`A: 0091 recordなし / changeなし`**

read-only再確認により以下を確認した:

- [x] `django_migrations`に`temples 0091`の記録は**存在しない**
  （Djangoの1 migration = 1 transactionによりatomicにrollbackされた）
- [x] `temples`最新は`0090`のまま不変
- [x] aggregate counts: `auth_user=1`/`userprofile=1`/`shrine=105`/
  `favorite=0`/`visit=2`/`goriyaku_relation=280`——**実行前と完全一致、
  変化なし**
- [x] id=21/22/101/103の`history_theme`/`goriyaku`/`updated_at`は
  いずれも実行前の値のまま**一切変化していない**
- [x] `users 0006`・`temples 0090`のstateはいずれも無傷（regression確認済み）
- [x] `temples 0092`/`0093`は未実行のまま

**Production側は実行前と完全に同一の状態を維持している。データ破損・
部分適用はゼロ件。**

### Runtime QA

`/healthz/`が`{"ok": true, "release": "b286a557680c12343282c6e1e57a78f1be4bda43"}`
を返し、backendは正常稼働中であることを確認した（今回の失敗した
ローカル実行はRender側のプロセスに一切影響していない）。認証済みQAは
引き続き`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`。

### 実行していないこと（明示）

- `temples 0091`のreverse migration相当の手動修正: **実行していない**
- 手動SQLによるschema/data修復: **実行していない**
- Production restore: **実行していない**
- `migrate`の再実行: **実行していない**

### Classification

**`TEMPLES_0091_EXECUTION_STOP`**

### Mother Shipへ返す修正候補（決定はしない、選択肢の提示のみ）

`temples 0091`を将来適用可能にするための技術的候補（実装はしていない）:

1. migration側で`Shrine.objects.filter(...).only("id", "name_jp",
   "history_theme", "goriyaku", "updated_at")`のように**`location`列を
   明示的にSELECT対象から除外する**よう書き換える
2. ORMではなく`schema_editor.connection.cursor()`等の生SQLで
   対象shrineを特定・更新する（geometry変換を経由しない）
3. `temples_shrine.location`列の型不整合そのもの（`text` vs
   PostGIS `geometry`）を別Gateとして根本的に解消する
   （影響範囲が大きく、本Gateのscopeを大きく超える）
4. 上記いずれも実施せず、`0091`の目的（2神社への`history_theme`/
   `goriyaku`/tag付与）を**migrationではなく別の一時的な
   read-onlyでない手段**（例: 別途承認を得た上でのdata-only script）
   で実現し、`0091`自体はスキップ扱いにする

**候補1が最も影響範囲が小さく、`0091`のみの修正で完結する可能性が
高いが、修正・再監査・再実行にはMother Shipの承認が必要。**

同様のパターン（`Shrine.objects`への無条件クエリ）が`temples`の
他のmigrationやアプリケーションコードにも存在しないか、**別途
点検を推奨する**（本Gateのscope外）。

### Production Write Summary（Stage 3時点の累積）

- **Production write: `temples 0090` = EXECUTED（Stage 2、変化なし）**
- **temples 0091 = NOT_EXECUTED（試行1回、失敗、atomic rollback、production変化なし）**
- **temples 0092 = NOT_EXECUTED**
- **temples 0093 = NOT_EXECUTED**

---

## Execution Record — Stage 3 Retry: `temples 0091`（成功・PASS）

**本Stageは成功した。** `temples 0091`はremediation
（PR #2337、`docs/audit/temples-0091-production-remediation.md`、
`TEMPLES_0091_REMEDIATION_READY`）を経てProduction適用に成功した。
`temples 0092`は実行していない。

### Phase 0 — Source of Truth確認

- [x] `docs/audit/production-migration-local-execution-runbook.md`
  （本ドキュメント、Stage 3失敗記録を含む）を再読
- [x] `docs/audit/temples-0091-production-remediation.md`
  （root cause・canonical identity・selected patch・
  Production-equivalent restore result・STOP conditions・recovery
  classification）を再読
- [x] 矛盾なし

### Phase 1 — develop同期

| 項目 | 結果 |
|---|---|
| PR #2337 merge確認 | `MERGED`、merge commit `856b859b75d65a69598a1525c4a6b835313ac0a9` |
| develop checkout / 同期 | 完了、`origin/develop`とfast-forward同期済み |
| develop HEAD SHA | `856b859b75d65a69598a1525c4a6b835313ac0a9` |
| working tree | clean |

### Phase 2 — Local Environment

| 項目 | 結果 |
|---|---|
| `python --version` | `Python 3.11.13` |
| Django version | `5.2.16` |
| psycopg version | `3.3.4` |
| `backend/manage.py`存在 | 確認済み |
| `DEBUG` | `0`（明示指定） |
| `USE_GIS` | `1`（明示指定） |
| Production credential file | 存在確認済み（`~/.config/kami-musubi/production-db.env`、permission `600`） |

### Phase 3 — Credential Gate

- [x] `check_credential_presence.sh` → `VAR_SET=1`、
  `{'parses': True, 'scheme_is_postgres': True, 'has_host': True,
  'has_port': True, 'has_dbname': True, 'has_userinfo': True}`
  （credential値・hostnameは非表示のまま）

### Phase 4 — Production State Recheck（read-only）

`migration_state.sql`を`readonly_query.sh`経由で実行し、全134行の
migration適用状態を確認。関連部分:

| app | 最新migration |
|---|---|
| `temples` | `0090_add_rest_healing_tag_to_silent_shrines` |
| `users` | `0006_userprofile_birth_profile_fields` |

`temples 0091`/`0092`/`0093`はいずれも未適用のまま。previous Stage 3
failure由来の部分適用・schema/state不整合は検出されなかった。他appの
未適用migrationも0件（既知baselineと完全一致）。

### Phase 5 — Fresh Snapshot / Phase 8 — Canonical Identity Recheck / Phase 9 — Expected Effect Recheck

独立したSELECT-only SQL（`pre_0091_retry_snapshot.sql`、repo外の
scratchpadに作成し`readonly_query.sh`経由で実行、credential/hostname
非露出）で以下を一括確認した（snapshot時刻`2026-08-10 01:15:51.064504+00`）:

| 確認項目 | 結果 |
|---|---|
| `temples_0091_applied`/`0092`/`0093` | すべて`false` |
| aggregate | `auth_user=1`/`userprofile=1`/`shrine=105`/`favorite=0`/`visit=2`/`goriyaku_relation=280`（既知baselineと完全一致） |
| canonical identity | id=21（長太稲荷神社、`place_ref_id IS NULL`）・id=22（給田六所神社、同）が引き続きcanonical。id=101・id=103（`place_ref_id`あり）が引き続きduplicateのまま、remediation audit時から変化なし |
| target tag存在確認 | `商売繁盛`・`五穀豊穣`・`家内安全`は存在、`地域安泰`は引き続き不存在（remediation audit時と完全一致） |
| 対象4行の既存goriyaku_tags関連 | 0件（クリーンな状態） |

事前予測（推測ではなく実測に基づくdelta）: id=21へ`history_theme="守り"`
+ `goriyaku`本文 + tag2件（`商売繁盛`・`五穀豊穣`。`地域安泰`は
不存在のため付与されない）、id=22へ`history_theme="守り"` + `goriyaku`
本文 + tag1件（`家内安全`）。`goriyaku_relation`は`280`→`283`
（+3）が期待値。id=101・id=103は無変更のまま。

### Phase 6 — Fresh Backup

| 項目 | 結果 |
|---|---|
| dump取得 | 成功（`dump_readonly.sh`、`PG_DUMP_BIN`/`PG_DUMPALL_BIN`に
  PostgreSQL 17クライアントを明示指定） |
| `roles.sql` size | `5426` bytes |
| `schema.sql` size | `81650` bytes（Stage 3直前backupと同一——schema変更なしのため妥当） |
| `data.sql` size | `3843102` bytes（Stage 3直前backupと同一） |
| 保存先 | ユーザーホームディレクトリ配下、repo外（新規timestampディレクトリ、
  具体的pathは本ドキュメントに記載しない） |
| credential/hostname露出 | **なし**。`dump_readonly.sh`の既知issue
  （`source:`行がhostnameを含む redacted 表示のみでuserinfoしかmaskしない）
  を踏まえ、当該行を`grep -v`で出力から意図的に除外した |

### Phase 7 — Remediation File Recheck

- [x] `git diff c3e09c06 -- backend/temples/migrations/0091_...py` が空
  ——develop HEADのmigrationファイルはPR #2337でverify済みの内容と
  **完全に同一**（バイト単位で差分なし）
- [x] `.only(*SHRINE_LOOKUP_FIELDS)`存在確認（`location`列非選択）
- [x] `order_by(F("place_ref_id").asc(nulls_first=True), "id")`存在確認
  （deterministic canonical selection、`.first()`の暗黙orderingに非依存）
- [x] `RunSQL`/`DROP`/`DELETE`/`TRUNCATE`等のdestructive operationなし
- [x] Production固有ID hardcodeなし

### Phase 10 — Final `--plan`

```
Planned operations:
temples.0091_fill_missing_local_shrine_reason_facts
    Raw Python operation
```

remediation audit時・Stage 3失敗時と完全一致。credential/hostname
非露出。

### Phase 11 — Human Execution Boundary

以下すべてPASS:

- [x] develop SHA correct（`856b859b`）
- [x] working tree clean
- [x] package parity PASS（Python/Django/psycopg一致）
- [x] credential gate PASS
- [x] Production state expected（`temples`最新=`0090`、`users`最新=`0006`）
- [x] `0091`still pending
- [x] `0092`/`0093` pending
- [x] fresh snapshot valid（aggregate baseline一致）
- [x] fresh backup PASS（3ファイルとも0バイトでない）
- [x] remediation file unchanged（PR #2337と完全一致）
- [x] canonical identity unchanged
- [x] expected effect understood（`goriyaku_relation` +3）
- [x] `--plan` match
- [x] `DEBUG=0`
- [x] `USE_GIS=1`

全項目PASS——retry実行可。

### Phase 12 — Execute `temples 0091`

| 項目 | 値 |
|---|---|
| コマンド | `python manage.py migrate temples 0091 --noinput`（app-scoped、
  target-scoped、bare `migrate`は不使用） |
| 実行開始 | `2026-08-10T01:18:33Z` |
| 実行終了 | `2026-08-10T01:18:54Z` |
| 出力 | `Applying temples.0091_fill_missing_local_shrine_reason_facts... OK` |
| exit status | **`0`（成功）** |

credential・hostnameは出力に一切含まれなかった。

### Phase 13 — Immediate Hard STOP

`temples 0091`実行直後、`temples 0092`は**実行していない**。以降は
read-only verificationのみを実施した。

### Phase 14〜17 — Verification（read-only、`post_0091_retry_verification.sql`）

verification時刻: `2026-08-10 01:19:31.066285+00`

**Phase 14: Migration State**

| 確認項目 | 結果 |
|---|---|
| `temples 0091` applied | `2026-08-10 01:18:53.573612+00`（新規レコード、previous failure recordではない） |
| `temples 0092` applied | `false` |
| `temples 0093` applied | `false` |

**Phase 15: Canonical Effect Verification**

| id | name_jp | history_theme | goriyaku | place_ref_id NULL | updated_at |
|---|---|---|---|---|---|
| 21 | 長太稲荷神社 | `守り` | 想定文言と完全一致 | true (canonical) | `2026-08-10 01:18:53.489121+00`（更新済み） |
| 22 | 給田六所神社 | `守り` | 想定文言と完全一致 | true (canonical) | `2026-08-10 01:18:53.545498+00`（更新済み） |
| 103 | 長太稲荷神社 | 空 | 空 | false (duplicate) | `2026-06-11 08:00:18.639346+00`（**無変更**） |
| 101 | 給田六所神社 | 空 | 空 | false (duplicate) | `2026-06-11 07:18:01.730693+00`（**無変更**） |

goriyaku_tags: id=21→`五穀豊穣`・`商売繁盛`（2件、`地域安泰`除外）、
id=22→`家内安全`（1件、`地域安泰`除外）。id=101・id=103への関連は
0件。**事前予測と完全一致。unexpected row updateなし。**

**Phase 16: Aggregate Verification**

| 項目 | retry前 | retry後 | 判定 |
|---|---|---|---|
| `auth_user` | 1 | 1 | 不変 |
| `userprofile` | 1 | 1 | 不変 |
| `shrine` | 105 | 105 | 不変 |
| `favorite` | 0 | 0 | 不変 |
| `visit` | 2 | 2 | 不変 |
| `goriyaku_relation` | 280 | 283 | **+3、expected deltaと完全一致** |

expected delta以外の変化なし。

**Phase 17: Previous Stage Regression**

- [x] `users_userprofile`の4カラム（`birthday`/`birth_time`/
  `birth_place`/`worship_style`）すべて存在
- [x] `users 0006` applied timestamp不変（`2026-08-09 12:02:10.455239+00`）
  ——再適用や書き換えは発生していない
- [x] `temples 0090` applied timestamp不変（`2026-08-09 12:13:30.066579+00`）
- [x] 全105 shrine中、`history_theme`が非空なのはid=21・id=22の2件のみ
  ——`temples`アプリ内で他に意図しない行が変更されていないことを確認

### Phase 18 — Runtime Smoke QA

`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`。本セッションで使用したcredential
bridgeはDB接続専用（`DATABASE_URL`のみ）であり、Production backendの
public URLはこのセッションのどの認可済みチャネルにも存在しない。
hostname記録禁止の原則に従い、推測・検索によるURL特定は行わなかった。
DB-level verification（Phase 14〜17）が本Stageの正式なverificationであり、
すべてPASSしている。

### Phase 19 — Failure Handling

該当なし（migrationはexit 0で正常終了）。

### Phase 20 — Success Classification

**`TEMPLES_0091_RETRY_PASS`**

根拠: exit 0、`temples 0091` applied確認、canonical行（id=21/22）のみ
更新、duplicate行（id=101/103）完全無変更、期待fieldと完全一致、
期待tag deltaと完全一致（`地域安泰`欠落時のguard動作も含め）、
aggregate delta期待通り（`goriyaku_relation` +3、他は不変）、
`users 0006`/`temples 0090`にregressionなし、`temples 0092`/`0093`は
引き続き未適用、想定外の変更ゼロ——Phase 20の全条件を満たす。

### Production Write Summary（Stage 3 Retry時点の累積）

- **Production write: `temples 0090` = EXECUTED（Stage 2、変化なし）**
- **temples 0091 = EXECUTED（Stage 3 Retry、exit 0、`TEMPLES_0091_RETRY_PASS`）**
- **temples 0092 = NOT_EXECUTED**
- **temples 0093 = NOT_EXECUTED**

---

## Execution Record — Stage 4: `temples 0092`（成功・PASS）

**本Stageは成功した。** `temples 0092`はProduction適用に成功した。
`temples 0093`は実行していない。

### Phase 0 — Source of Truth確認

- [x] 本ドキュメント（Stage 1〜Stage 3 Retryまでの全Execution Record）を再読
- [x] 矛盾なし

### Phase 1 — develop同期

| 項目 | 結果 |
|---|---|
| PR #2338 merge確認 | `MERGED`、merge commit `a878ade891bb702f0f2512d7af0a7353e55f5009` |
| develop checkout / 同期 | 完了、`origin/develop`とfast-forward同期済み |
| develop HEAD SHA | `a878ade891bb702f0f2512d7af0a7353e55f5009` |
| working tree | clean |

### Phase 2 — Local Environment

| 項目 | 結果 |
|---|---|
| `python --version` | `Python 3.11.13` |
| Django version | `5.2.16` |
| psycopg version | `3.3.4` |
| `DEBUG` | `0`（明示指定） |
| `USE_GIS` | `1`（明示指定） |

### Phase 3 — Credential Gate

- [x] `check_credential_presence.sh` → `VAR_SET=1`、
  `{'parses': True, 'scheme_is_postgres': True, 'has_host': True,
  'has_port': True, 'has_dbname': True, 'has_userinfo': True}`

### Phase 4 — Stage 3 State Recheck / Phase 5 — Fresh Pre-0092 Snapshot

`pre_0092_snapshot.sql`を`readonly_query.sh`経由で実行（snapshot時刻
`2026-08-10 01:36:19.124637+00`）:

| 確認項目 | 結果 |
|---|---|
| `users 0006`/`temples 0090`/`0091` applied、`0092`/`0093` unapplied | 全項目一致 |
| `0091` canonical効果 | id=21・id=22の`history_theme`/`goriyaku`/`updated_at`がStage 3 Retry完了時点から**無変化**、duplicate（id=101/103）も引き続き無変化 |
| goriyaku_tags関連 | 3件（`地域安泰`欠落を反映した内容）、Stage 3 Retry完了時から無変化 |
| aggregate（新baseline） | `auth_user=1`/`userprofile=1`/`shrine=105`/`favorite=0`/`visit=2`/`goriyaku_relation=283`——**旧baseline（280）ではなく`0091`適用後の283を正本として使用** |
| 全8 app migration state | drift 0件、既知構成と完全一致 |

Stage 3 Retry状態の崩れなし。`STOP_STAGE3_STATE_DRIFT`には該当しない。

### Phase 6 — Fresh Backup After 0091

| 項目 | 結果 |
|---|---|
| dump取得 | 成功（PostgreSQL 17クライアント明示指定） |
| `roles.sql` size | `5426` bytes |
| `schema.sql` size | `81650` bytes（`0091`はdata-onlyのため不変、妥当） |
| `data.sql` size | `3843434` bytes（Stage 3 Retry直前backupの`3843102`より+332 bytes——
  `0091`が書き込んだ`history_theme`/`goriyaku`本文・tag関連の増分と整合） |
| 保存先 | repo外（新規timestampディレクトリ） |
| credential/hostname露出 | なし（`source:`行を`grep -v`で除外） |

### Phase 7 — Target Migration 0092 Fresh Audit

過去監査を参照せず、`backend/temples/migrations/0092_add_thread_to_visit_and_reflection.py`
をfreshに読んだ。

| 確認項目 | 結果 |
|---|---|
| ファイル名 | `0092_add_thread_to_visit_and_reflection.py`（一致） |
| dependency | `temples.0091_fill_missing_local_shrine_reason_facts`のみ |
| operation | `AddField`×2のみ（`RunPython`/`RunSQL`なし） |
| 対象1 | `shrinereflection.thread`: `ForeignKey(null=True, blank=True, on_delete=SET_NULL, to="temples.conciergethread", related_name="reflections")` |
| 対象2 | `visit.thread`: 同型（`related_name="visits"`） |
| destructive operation | なし |
| reverse | Django標準の`AddField`逆操作（`RemoveField`相当）、カスタムreverse不要 |
| 最終commit | `5a67f4a0`（PR #1992）——現HEADより大幅に前、変更なし |

`0091`のような`RunPython`+ORM無条件クエリという構造ではなく、単純な
schema-only `AddField`だが、Phase 8で実schemaとの互換性を実測確認した
（推測で「単純だから安全」とは判断しない）。

### Phase 8 — Production Actual Schema Compatibility

`schema_compat_0092.sql`を`readonly_query.sh`経由で実行:

| 確認項目 | 結果 |
|---|---|
| 対象table存在 | `temples_shrinereflection`・`temples_visit`・`temples_conciergethread`すべて存在 |
| `thread_id`列の事前不存在 | 0件（両tableとも未存在、conflictなし） |
| FK先`temples_conciergethread`のPK | `id bigint`——標準的なDjango FK互換 |
| 両tableの現行column一覧 | 想定外のcolumn・GIS系型は1件もなし（`0091`のような`location`型drift相当の問題は本tableには存在しない） |
| 既存constraint一覧 | 標準的なPK/FKのみ、命名衝突なし |

`STOP_SCHEMA_COMPATIBILITY_MISMATCH`には該当しない。

### Phase 9 — Production-Equivalent Local Test

Phase 6で取得したfresh backup（`users 0006`/`temples 0090`/`0091`適用
済み状態を実際に反映）を、ローカルの隔離PostgreSQL 18 + PostGIS
インスタンスへ復元し、`temples 0092`のみを適用した。

| 項目 | 結果 |
|---|---|
| 復元前state確認 | `temples`最新=`0091`、`goriyaku_relation=283`、`thread`列不存在——想定通り |
| `migrate temples 0092 --noinput` | exit `0` |
| `thread_id`列 | 両tableに`bigint`・nullable・`temples_conciergethread`参照FK・indexとも正しく作成 |
| aggregate | `auth_user=1`/`userprofile=1`/`shrine=105`/`favorite=0`/`visit=2`/`goriyaku_relation=283`——**完全不変**（schema-only migrationとして期待通り） |
| `temples 0093` | **実行していない** |

Production実行前に、Production相当のschema/dataでPASSすることを確認
済み。テスト後、この隔離DBは削除した。

### Phase 10 — Final Django Plan

```
Planned operations:
temples.0092_add_thread_to_visit_and_reflection
    Add field thread to shrinereflection
    Add field thread to visit
```

Phase 7/9の内容と完全一致。credential/hostname非露出。
`STOP_PLAN_MISMATCH`には該当しない。

### Phase 11 — Human Execution Boundary

以下すべてPASS:

- [x] develop SHA correct（`a878ade8`）
- [x] working tree clean
- [x] package parity PASS
- [x] credential gate PASS
- [x] `users 0006` applied
- [x] `temples 0090` applied
- [x] `temples 0091` applied
- [x] `temples 0092` pending
- [x] `temples 0093` pending
- [x] Stage 3効果intact
- [x] fresh snapshot valid
- [x] fresh backup PASS
- [x] migration file unchanged（PR #1992以来無変更）
- [x] Production schema compatible
- [x] Production-equivalent local test PASS
- [x] `--plan` exact match
- [x] `DEBUG=0`
- [x] `USE_GIS=1`

全項目PASS——実行可。

### Phase 12 — Execute `temples 0092`

| 項目 | 値 |
|---|---|
| コマンド | `python manage.py migrate temples 0092 --noinput`（app-scoped、
  target-scoped、bare `migrate`は不使用） |
| 実行開始 | `2026-08-10T01:38:13Z` |
| 実行終了 | `2026-08-10T01:38:24Z` |
| 出力 | `Applying temples.0092_add_thread_to_visit_and_reflection... OK` |
| exit status | **`0`（成功）** |

credential・hostnameは出力に一切含まれなかった。

### Phase 13 — Immediate Hard STOP

`temples 0092`実行直後、`temples 0093`は**実行していない**。以降は
read-only verificationのみを実施した。

### Phase 14〜17 — Verification（read-only、`post_0092_verification.sql`）

verification時刻: `2026-08-10 01:39:13.072309+00`

**Phase 14: Migration State**

| 確認項目 | 結果 |
|---|---|
| `temples 0092` applied | `2026-08-10 01:38:24.112859+00`（新規レコード） |
| `temples 0093` applied | `false` |
| `temples 0090` applied timestamp | `2026-08-09 12:13:30.066579+00`（**不変**） |
| `temples 0091` applied timestamp | `2026-08-10 01:18:53.573612+00`（**不変**） |
| `users 0006` applied timestamp | `2026-08-09 12:02:10.455239+00`（**不変**） |

**Phase 15: Target Schema Verification**

| table | column | type | nullable |
|---|---|---|---|
| `temples_shrinereflection` | `thread_id` | `bigint` | `YES` |
| `temples_visit` | `thread_id` | `bigint` | `YES` |

FK制約: `temples_visit_thread_id_..._fk_temples_conciergethread_id`・
`temples_shrinereflec_thread_id_..._fk_temples_c`ともに
`temples_conciergethread`を正しく参照。両tableの全column一覧を確認し、
想定外のcolumnは0件。

**Phase 16: Aggregate Verification**

| 項目 | 0092前 | 0092後 | 判定 |
|---|---|---|---|
| `auth_user` | 1 | 1 | 不変 |
| `userprofile` | 1 | 1 | 不変 |
| `shrine` | 105 | 105 | 不変 |
| `favorite` | 0 | 0 | 不変 |
| `visit` | 2 | 2 | 不変 |
| `goriyaku_relation` | 283 | 283 | 不変 |

schema-only migrationとして期待通り、application data aggregatesは
一切変化しなかった。追加で、既存`visit`/`shrinereflection`全行の
`thread_id`が0件を除きすべて`NULL`であることを確認——`AddField`が
意図しないbackfillを行っていないことも実測済み。

**Phase 17: Previous Stage Regression**

- [x] `users_userprofile`の4カラムすべて存在
- [x] `temples 0090`/`0091`のapplied timestamp不変（再適用なし）
- [x] `0091`のcanonical効果（id=21/22の`history_theme`/`goriyaku`/
  `updated_at`）が`0092`実行前後で完全に不変
- [x] duplicate行（id=101/103）も引き続き無変化

`0092`による既存Stageへのregressionは検出されなかった。

### Phase 18 — Runtime Smoke QA

`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`。Stage 3 Retryと同様、本セッション
のcredential bridgeはDB接続専用であり、Production backendのpublic URL
はこのセッションのどの認可済みチャネルにも存在しない。hostname記録
禁止の原則に従い、推測・検索によるURL特定は行わなかった。DB-level
verification（Phase 14〜17）が本Stageの正式なverificationであり、
すべてPASSしている。

### Phase 19 — Failure Handling

該当なし（migrationはexit 0で正常終了）。

### Phase 20 — Success Classification

**`TEMPLES_0092_EXECUTION_PASS`**

根拠: exit 0、`temples 0092` applied確認、target schema（`thread_id`
column×2、FK制約、index）が想定と完全一致、aggregate不変確認
（schema-only migrationとして妥当）、既存行への意図しないbackfillなし、
`users 0006`/`temples 0090`/`temples 0091`にregressionなし、
`temples 0093`は引き続き未適用、想定外の変更ゼロ——Phase 20の全条件を
満たす。

### Production Write Summary（Stage 4時点の累積）

- **Production write: `temples 0090` = EXECUTED（Stage 2、変化なし）**
- **temples 0091 = EXECUTED（Stage 3 Retry、`TEMPLES_0091_RETRY_PASS`）**
- **temples 0092 = EXECUTED（Stage 4、exit 0、`TEMPLES_0092_EXECUTION_PASS`）**
- **temples 0093 = NOT_EXECUTED**
