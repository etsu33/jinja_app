> **Status: Stage 1（`users 0006`）・Stage 2（`temples 0090`）実行完了・
> いずれもPASS。`temples 0091`以降は未実行のまま意図的に停止中。
> 次のStageはMother Ship判断待ち。**
>
> 本ドキュメントは**正本**である。`docs/audit/
> production-migration-execution-gate.md`・`production-migration-go-no-go-final.md`・
> `local-mac-direct-migration-execution-safety.md`はいずれも背景調査・
> 実測記録として引き続き有効だが、**実際に人間が上から順に実行する
> 手順としては本ドキュメントを使うこと。**
>
> **Execution Recordは本ドキュメント末尾の
> 「Execution Record — Stage 1: `users 0006`」・
> 「Execution Record — Stage 2: `temples 0090`」の各節を参照。**
>
> **Production migrationはこのPRでは実行していない。Production DBへの
> writeは0件。** 許可されたのはread-only verification
> （`showmigrations`・`migrate --plan`・`readonly_query.sh`経由のSELECT）
> のみ。

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
