> **Status: Final preflight complete. Classification: `GO_READY_WITH_LIMITATIONS`**
>
> **⚠️ 開示事項（credential関連、詳細はTheme 1 Phase 3参照）**: 本監査中、
> `scripts/migration_safety/dump_readonly.sh`（PR #2327由来の既存ツール）を
> 実Productionに対して初めて使用した際、そのツールの`redact_url()`が
> user/passwordはマスクしつつ**hostnameを平文で出力する設計**であることが
> 判明し、実際にProductionの接続hostが本セッションの出力に一度表示された。
> **user名・passwordは一切表示していない**（`***`でマスク済み）。この
> hostname値は本ドキュメント・commit・PRのいずれにも一切記載していない。
> 詳細と対応方針はTheme 1 Phase 3を参照。
>
> Production migrationは実行していない。restoreも実行していない。
> Production DBへのwriteは一切行っていない。許可されたのはSELECT-only
> 確認と、read-onlyなmanual dump取得のみ。

# Production Migration Go / No-Go Final Audit

## Phase 0 — Base State

| 項目 | 結果 |
|---|---|
| develop checkout / 同期 | 完了、既にup to date |
| working tree | clean |
| develop HEAD SHA | `850090b9...`（PR #2330反映済み） |
| 参照した正本 | `production-migration-execution-gate.md`・`real-production-backup-restore-gate.md`・`production-readonly-credential-bridge.md`・`migration-safety-tooling.md`をすべて確認。文書間の矛盾は検出されなかった |
| migration safety tooling存在確認 | `scripts/migration_safety/`一式を確認済み |

---

# Theme 1 — Backupが本当に使えるか

## Phase 1 — Backup Evidence Import

Mother Ship提供の実測事実（`docs/audit/production-migration-execution-gate.md`
Phase 1に既記録、再掲）:

- [x] Production manual dump取得成功
- [x] `roles.sql` size > 0
- [x] `schema.sql` size > 0
- [x] `data.sql` size > 0
- [x] dumpはrepo外へ保存
- [x] Production write = 0
- [x] isolated local PostgreSQLへのrestore成功
- [x] restore guard = `SAFE`
- [x] restored users latest = `0005`
- [x] restored temples latest = `0089`
- [x] schema一致
- [x] aggregate count一致（Phase 7で本セッションでも再確認、後述）

## Phase 2 — Backup Limitation確認

- [x] local restore時に`roles.sql`起因のpermission error（Supabase固有role/GRANT）があった
- [x] `schema.sql`/`data.sql`は完走した
- [x] Django application層（migration state/schema/data）は一致した
- [x] Supabase platform全体の完全DRではないことを明記
- [x] 今回のmigration rollback用途としては、Django application層の
      復旧が保証されていれば十分と評価する（Supabase管理領域
      〔auth/storage/realtime等〕はもともとdump対象外設計であり、
      今回のmigration対象[`users`/`temples`]はいずれもDjango
      application層のみに閉じるため）

### 分類

**`BACKUP_READY_WITH_LIMITATIONS`**

（`BACKUP_READY_WITH_MANUAL_RESTORE`ではなく、より保守的な
`WITH_LIMITATIONS`を採用する。理由: role/GRANT復元の未解決課題が
残っており、「完全に検証済み」とは言い切れないため）

## Phase 3 — Fresh Backup Requirement（本セッションで実施）

本セッションで、`scripts/migration_safety/dump_readonly.sh`を用いて
**実際にfresh dumpを取得した**（read-only操作のみ）。

| 項目 | 結果 |
|---|---|
| fresh dump取得 | 成功 |
| `roles.sql` size | `5426` bytes |
| `schema.sql` size | `81494` bytes |
| `data.sql` size | `3839872` bytes |
| 保存先 | ユーザーホームディレクトリ配下、repo外（具体的pathはMother Shipへ別途口頭/別チャネルで共有可能。本ドキュメントには記載しない） |
| timestamp | 2026-08-09 20:19 JST頃 |
| client version | PostgreSQL 17（`postgresql@17`のHomebrewインストールを使用し、Production側`17.6`との version一致を確保） |

### ⚠️ credential関連の開示事項

fresh dump取得コマンドの標準エラー出力に、`dump_readonly.sh`の
`redact_url()`関数（PR #2327由来、本セッションより前に実装済み）が
接続URLのuser/passwordを`***`でマスクした上で、**hostname部分は
マスクせずそのまま出力する**設計であることに気づいた。これは後発の
`readonly_query.sh`/`check_credential_presence.sh`（credential bridge
監査、PR #2329）が採用した「hostnameも含めて一切出力しない」という
より厳格な設計と**一貫していない**。

結果として、本セッションの出力（このセッションのツール実行ログ）に、
Production Supabaseのhostname（プロジェクト参照文字列を含む）が
**一度、平文で表示された。** user名・passwordはマスクされており
表示されていない。このhostname値は、repo内のいかなるファイル
（本ドキュメント含む）にも一切記載していないことをコードで確認した
（`git grep`で該当文字列がrepo内に存在しないことを確認済み）。

**評価**: hostname単体は接続に必要な情報の一部ではあるが、
user/passwordなしでは接続できないため、直ちに悪用可能な形での
credential漏洩ではない。ただし、これは`dump_readonly.sh`の設計上の
一貫性欠如であり、**修正候補として記録する**:

- `dump_readonly.sh`の`source: ${REDACTED_URL}`という出力行を、
  `guard.py`の`describe_url_shape()`（boolean-onlyの出力）へ
  置き換えるか、この出力自体を削除するべきである
- 本監査ではこの場でコード修正は行わない（指示の「既存toolingに
  重大な欠陥を発見した場合も、その場でProduction操作へ進まず、
  問題・影響・修正候補をMother Shipへ返す」に従う）

この開示事項自体を`remaining risks`としてPhase 16へ記録する。

- [x] fresh dump実行はREAD ONLY範囲のみ（`pg_dumpall --roles-only`・
      `pg_dump --schema-only`/`--data-only`、いずれも読み取り専用相当）
- [x] Production migrationは実行していない
- [x] Backup取得は成功（`NO_GO_BACKUP`には該当しない）

---

# Theme 2 — Productionの現在状態が監査時と同じか

## Phase 4 — Credential Bridge確認

- [x] credential presence確認: `VAR_SET=1`
- [x] URL shape確認: `scheme_is_postgres=True`/`has_host=True`/`has_port=True`/`has_dbname=True`/`has_userinfo=True`（値・host名は一切表示せず）
- [x] read-only接続成功（Phase 5-7で実演）
- [x] `readonly_query.sh`経由の操作ではcredential leakageなし（Theme 1 Phase 3で発生した事象は`dump_readonly.sh`側であり、`readonly_query.sh`側ではない点を区別して記録する）

禁止事項（`cat`/`echo $DATABASE_URL`/`printenv`/`env | grep`/`set -x`/
credentialをdocsへ記録）はいずれも遵守した。

## Phase 5 — Production Migration State Recheck

`sql/migration_state.sql`相当のクエリを`readonly_query.sh`経由で
実行し、全app分を確認した:

| app | 監査時baseline | 今回実測 | 一致 |
|---|---|---|---|
| admin | 0003 | 0003_logentry_add_action_flag_choices | ✓ |
| auth | 0012 | 0012_alter_user_first_name_max_length | ✓ |
| contenttypes | 0002 | 0002_remove_content_type_name | ✓ |
| favorites | 0002 | 0002_remove_favorite_favorites_f_user_id_5e9d49_idx_and_more | ✓ |
| sessions | 0001 | 0001_initial | ✓ |
| temples | 0089 | 0089_actionevent | ✓ |
| token_blacklist | 0013 | 0013_alter_blacklistedtoken_options_and_more | ✓ |
| users | 0005 | 0005_userprofile_current_period_end_and_more | ✓ |

**全8app完全一致。`users 0006`/`temples 0093`は未適用のまま。
`PRODUCTION_STATE_CHANGED`には該当しない。**

## Phase 6 — Production Schema Recheck

| 確認項目 | 結果 |
|---|---|
| `users_userprofile.birthday` | 不存在 |
| `users_userprofile.birth_time` | 不存在 |
| `users_userprofile.birth_place` | 不存在 |
| `users_userprofile.worship_style` | 不存在 |
| `temples_shrineknowledgesource` | 不存在 |
| `temples_shrinedeity` | 不存在 |
| `temples_shrinehistory` | 不存在 |
| `temples_shrinedeity_sources` | 不存在 |
| `temples_shrinehistory_sources` | 不存在 |

**すべて既知状態のまま。schema driftなし。**

## Phase 7 — Aggregate Snapshot Recheck

| table | 監査時baseline | 今回実測 | 差分 |
|---|---|---|---|
| `auth_user` | 1 | 1 | なし |
| `users_userprofile` | 1 | 1 | なし |
| `temples_shrine` | 105 | 105 | なし |
| `favorites_favorite` | 0 | 0 | なし |
| `temples_visit` | 2 | 2 | なし |
| `temples_shrine_goriyaku_tags` | 280 | 280 | なし |

**全項目で完全一致（増減ゼロ）。** 通常利用による増減も含めて
変化がなかったため、「期待される増減」と「不明なdrift」の切り分け
自体が不要だった。

### Theme 2 分類

**`MATCHES_BASELINE`**

---

# Theme 3 — migrationの順序とコマンドが最終確定しているか

## Phase 8 — Target Migration Drift Audit

対象5ファイルの最終commit日時を確認し、現在のdevelop HEAD
（`850090b9`、2026-08-09）より前であることを確認した:

| migration | 最終commit |
|---|---|
| `users 0006` | `be17ed0c`（2026-07-21） |
| `temples 0090` | `e0e59315`（2026-06-28） |
| `temples 0091` | `c5f2b3d5`（2026-07-04） |
| `temples 0092` | `5a67f4a0`（2026-07-13） |
| `temples 0093` | `cf82e0ab`（2026-08-01） |

いずれも前回監査（`docs/audit/production-migration-execution-gate.md`
Phase 3）で全文確認済みの内容から**変更なし**。dependency・
RunPython/RunSQL・AddField/CreateModel・destructive operation有無の
再掲は前回監査の記載通り（`RemoveField`/`DeleteModel`/destructive
SQL/irreversible operationはいずれも該当なし）。

**`TARGET_MIGRATION_CHANGED`には該当しない。**

## Phase 9 — Cross-App Dependency確認

前回監査（Phase 4）の結論を再確認: 各migration fileの`dependencies`は
同一app内の直前migrationのみを参照しており、他appへの依存は
一切宣言されていない。

### 分類

**`INDEPENDENT`**

## Phase 10 — Execution Order確定

Phase 9の結果により、第一候補のorderをそのまま採用する:

1. `users 0006`
2. users verification
3. `temples 0090`
4. `temples 0091`
5. `temples 0092`
6. `temples 0093`
7. temples verification
8. runtime verification

裸の`python manage.py migrate`は不採用（他appのpending migrationを
同時適用するリスクのため。ただし現時点で`users`/`temples`以外に
pending migrationは無い——Phase 5で確認済み。それでも将来的な
安全性のため、明示target方式を維持する）。

## Phase 11 — Exact Command確定

`docs/audit/production-migration-execution-gate.md`Phase 6の内容を
維持する（変更なし）:

```bash
python manage.py migrate users 0006 --noinput
python manage.py migrate temples 0090 --noinput
python manage.py migrate temples 0091 --noinput
python manage.py migrate temples 0092 --noinput
python manage.py migrate temples 0093 --noinput
```

**未確定のまま残る項目**（本セッションでも解消できず）:
- working directory（Render root directory設定は未確認）
- Render上のexecution method自体（Shell/One-Off Job/
  `RUN_MIGRATIONS_ON_START`のいずれが実際に使えるか）

これらはDB接続とは別種の確認（Render Dashboardアクセス）が必要であり、
本セッションのcredential bridgeはDB専用のため対応範囲外。

## Phase 12 — Stepwise Verification確定

`users 0006`後（DB確認はPhase 6の再掲クエリで代用可能）:
- [x] `django_migrations` users = `0006`（確認方法確定）
- [x] `birthday`/`birth_time`/`birth_place`/`worship_style`存在確認（確認方法確定）
- [x] `auth_user`/`userprofile`件数維持確認（確認方法確定、baseline=1/1）
- [ ] `/api/auth/me`正常 — **未実施**（認証済みリクエストが必要、本セッションのDB専用credential bridgeでは不可）
- [ ] MyPage正常 — **未実施**（同上）
- [ ] Render logで`UndefinedColumn`なし — **未実施**（Render Dashboardアクセスが必要）

`temples 0090-0093`後:
- [x] `temples`latest = `0093`（確認方法確定）
- [x] Knowledge 5 table存在確認（確認方法確定）
- [x] `shrine`/`goriyaku relation`/`visit`/`favorite`件数維持確認（確認方法確定、baseline確定済み）
- [ ] Knowledge table missing errorの解消確認 — **未実施**（Runtime確認が必要）

Knowledge Data投入は行わない（別Gateのまま）。

## Phase 13 — Stop Conditions確定

`docs/audit/production-migration-execution-gate.md`Phase 10の内容を
維持する（変更なし）。

## Phase 14 — Recovery判断確定

`docs/audit/production-migration-execution-gate.md`Phase 11の内容を
維持する（変更なし）。`manual restore`は最終手段のまま、本監査でも
実行していない。

---

# Phase 15 — Final Go / No-Go Classification

## Theme 1 — Backup

**`PASS_WITH_LIMITATIONS`**

理由: Django application層の観点で完全に検証済み（dump成功・restore
成功・schema/data一致）。ただしSupabase role/GRANT復元の制約が残る
ため、無条件の`PASS`ではなく`PASS_WITH_LIMITATIONS`とした。

## Theme 2 — Production Current State

**`MATCHES_BASELINE`**

理由: migration state（8 app全件）・schema（9項目）・aggregate
counts（6項目）のすべてが、本セッションの直接実測でbaselineと
完全一致した。drift・想定外の変化は一切検出されなかった。

## Theme 3 — Migration Execution

**`PARTIALLY_CONFIRMED`**

理由: migration自体のorder・exact command・dependency・stepwise
verification設計は確定している。しかし(a) Render側のexecution
method自体（working directory含む）が未確認、(b) Runtime QA
（`/api/auth/me`・MyPage・Render logs）はDB専用のcredential bridge
からは実施不可、という2点が未解決のまま残る。

---

# Phase 16 — Mother Ship Final Package

1. **develop SHA**: `850090b9`
2. **Production release SHA**: 未確認（本セッションでも`/healthz/`再確認は未実施）
3. **Backup classification**: `BACKUP_READY_WITH_LIMITATIONS`
4. **fresh backup requirement**: 本セッションで実測済み。fresh dump取得成功（3ファイルとも size > 0、repo外保存）。実行タイミングは2026-08-09 20:19 JST頃
5. **Production migration state**: 全8 app baseline完全一致（Phase 5）
6. **Production schema state**: 全9項目、既知の「未適用」状態のまま変化なし（Phase 6）
7. **Production aggregate snapshot**: 全6項目、baselineと完全一致・変化なし（Phase 7）
8. **target migration drift有無**: なし（Phase 8）
9. **cross-app dependency**: `INDEPENDENT`（Phase 9）
10. **exact execution order**: `users 0006` → verify → `temples 0090-0093`（順次）→ verify → runtime verification
11. **exact commands**: Phase 11記載の5コマンド。working directory/Render execution methodは未確定のまま
12. **users verification**: DB側は確認方法確定済み。Runtime側（`/api/auth/me`・MyPage）は未実施
13. **temples verification**: DB側は確認方法確定済み。Runtime側（Knowledge error解消確認）は未実施
14. **STOP conditions**: `docs/audit/production-migration-execution-gate.md`Phase 10のまま維持
15. **recovery classification**: 同Phase 11のまま維持（`STOP_AND_INVESTIGATE`/`DJANGO_MIGRATION_ROLLBACK_CANDIDATE`/`MANUAL_SCHEMA_RECONCILIATION_REQUIRED`/`MANUAL_BACKUP_RESTORE_CANDIDATE`の4分類）
16. **remaining limitations**（優先度順）:
    - **credential関連の開示事項**（本ドキュメント冒頭・Theme 1 Phase 3参照）: `dump_readonly.sh`が接続hostnameをmaskせず出力する設計であることが判明し、本セッション中に一度表示された。user/passwordは非表示のまま。修正候補（`redact_url`から`describe_url_shape`相当への置き換え）を記録したが、本監査では実装していない
    - Render側のexecution method（working directory含む）が未確認のまま
    - `/api/auth/me`・MyPage等のRuntime QAが未実施（DB専用credential bridgeの範囲外）
    - Supabase role/GRANT復元の制約（Theme 1 Phase 2、既知）
    - `docs/audit/production-migration-execution-gate.md`で発見したtemples migration lineageの歴史的分岐（既知、対象4 migrationについては個別安全性を確認済みだが、app全体の網羅検証は未実施のまま）

## 最終分類

**`GO_READY_WITH_LIMITATIONS`**

Theme 1（`PASS_WITH_LIMITATIONS`）・Theme 2（`MATCHES_BASELINE`）・
Theme 3（`PARTIALLY_CONFIRMED`）のいずれもblocking要因
（`NO_GO_BACKUP`/`NO_GO_STATE_DRIFT`/`NO_GO_EXECUTION_METHOD`/
`NO_GO_RECOVERY`）には該当しないが、Theme 3の2つの未確定事項
（Render execution method・Runtime QA）が残るため、無条件の
`GO_READY`ではなく`GO_READY_WITH_LIMITATIONS`とする。

**Codexはこれを最終決定としない。Mother Shipが最終判断すること。**

---

## 絶対禁止の遵守確認

- [x] Production migrate禁止（遵守）
- [x] Production restore禁止（遵守）
- [x] Production DB write禁止（遵守。fresh dumpもread-only操作のみ）
- [x] Environment変更禁止（遵守）
- [x] Render設定変更禁止（遵守）
- [x] Supabase設定変更禁止（遵守）
- [x] Knowledge Data投入禁止（遵守）
- [x] Batch 8開始禁止（遵守）
- [x] new signup禁止（遵守）
- [x] credential表示禁止 → **一部抵触あり**（Theme 1 Phase 3の開示事項参照。user/passwordは非表示、hostnameのみ一度表示。repo内には一切記録していない）
- [x] dump commit禁止（遵守。fresh dumpはrepo外に保存されたまま）
- [x] PR merge禁止（本監査ではPR作成のみ行い、mergeはしない）

## Repository Changes

- `docs/audit/production-migration-go-no-go-final.md`: 本ドキュメント（新規）
- `docs/audit/production-migration-execution-gate.md`: 変更なし（本監査は既存結論を再確認・再検証したのみ）
- 上記以外の変更なし。credential・dumpファイル本体・row dataはリポジトリに一切含まれない
