# NIIGATA-H001 nsrc-000002 青澤神社 G7 Production Import — read-only preflight preparation

## 1. Status

~~~text
candidate_id                 = nsrc-000002
candidate_name               = 青澤神社

UPSTREAM_G4                  = PASS            (PR #3149)
UPSTREAM_G5                  = PASS / ELIGIBLE (PR #3150)
UPSTREAM_G6                  = PASS            (PR #3151)

G7_READ_ONLY_PREFLIGHT       = PASS            (Mother Ship decision, §4)
PRODUCTION_STATE_CLASS       = CLEAN_CREATE
EXPECTED_PRODUCTION_DELTA    =
  Shrine     +1
  Source     +1
  Deity      +0
  History    +1
  SourceFact +0
  goriyaku   +0
PRODUCTION_POSTGRESQL        = 17.6
BACKUP_CLIENT_COMPATIBILITY  = PASS            (client 17.10, §8.1)
PRODUCTION_FRESH_BACKUP      = PASS            (20261010202119, §8.1)
ISOLATED_RESTORE             = PASS
RESTORED_DB_FINGERPRINT      = PASS
ISOLATED_PRE_BASE_GUARD      = PASS
BACKUP_RESTORE_READINESS     = PASS
PRE_BASE_GUARD_READY         = PASS            (committed frozen values tested, §5.1)
POST_BASE_GUARD_READY        = PASS            (local sequential simulation, §5.1)
POST_KNOWLEDGE_VERIFY_READY  = PASS            (local sequential simulation, §5.1)
PRODUCTION_RUNTIME_QA_READY  = PASS

PRODUCTION_WRITE_AUTHORIZED  = NO
PRODUCTION_WRITE             = NONE

FORMAL_G7                    = NOT EXECUTED
~~~

- Recorded at: 2026-10-10
- Base: `develop@3009478a`（PR #3151 merge 後）
- Branch: `audit/nsrc-000002-g7-production-import-preflight`（PR #3152, merged）
- Frozen pre-state update: `audit/nsrc-000002-g7-freeze-production-prestate`（base `develop@08ec7cef`, PR #3153, merged）
- Backup / restore evidence: `audit/nsrc-000002-g7-backup-restore-evidence`（base `develop@9d776d5c`）
- Authority: `docs/knowledge/shrine-expansion-gate-contract.md` §10
- Reference: nsrc-000004 G7（PR #3132 / `docs/audit/niigata-h001-g7-production-import.md`）

本書は G7 の pre-write authorization evidence の準備記録である。G7 PASS を記録しない。

### Blocker（PR #3152 時点。解消済み）

~~~text
G7_BLOCKER (PR #3152) = PRODUCTION_READ_ONLY_ACCESS_UNAVAILABLE_IN_THIS_EXECUTION_ENVIRONMENT
STATUS                = RESOLVED: Production read-only preflight は Mother Ship 側で実行された（§4）
~~~

PR #3152 を作成した実行環境には Production credential が存在しない。

~~~text
scripts/migration_safety/check_credential_presence.sh ~/.config/kami-musubi/production-db.env DATABASE_URL
-> VAR_SET=0
~~~

Production への read-only query（Phase 2）は実行していない。credential は要求も作成もしていない。
そのため Production 実測に依存する項目（Phase 2 / Phase 3 / guard の frozen 値 / Production backup）は
すべて HOLD または NOT_MEASURED とした。推測値は記録していない。
freeze PR を作成した実行環境にも Production credential は無く、本 PR でも Production へは接続していない。
§4 の値は Mother Ship から受け取った Production read-only preflight の実測値である。

---

## 2. Scope

~~~text
G7_SCOPE = { nsrc-000002 }

name_jp   = 青澤神社
address   = 新潟県糸魚川市大字青海2696番地
latitude  = 37.00763484
longitude = 137.79024297

Knowledge Seed = backend/temples/data/knowledge_seeds/nsrc_000002_seed.json
  Source     = 1  (government / https://matsuri.geo-itoigawa.com/calendar/m04/)
  Deity      = 0
  History    = 1  (regional_context / 青沢神社の春季祭礼)
  SourceFact = 0
~~~

Full canonical Base Seed の Production apply は禁止。Production へ入れてよい Base は §6 の1行 subset だけ。

---

## 3. Phase 1 — Read-only preflight SQL

`scripts/migration_safety/sql/nsrc_000002_g7_preflight.sql`（SELECT / WITH のみ。`guard.py check-readonly-sql` = SAFE）

測定項目:

| # | 項目 |
|---|---|
| 1 | database identity / user / server_version の available（boolean のみ） |
| 2 | `server_version` / `server_version_num` |
| 3 | latest `temples` migration |
| 4 | 必要 table の存在（Shrine / Source / Deity / History / History-Source / SourceFact / goriyaku_tags / GoriyakuAssignment） |
| 5 | aggregate count（Shrine / Source / Deity / History / SourceFact） |
| 6 | target exact count、same-name 青澤神社、same-name 青沢神社、same-address count と該当行（id / name_jp / address / latitude / longitude / place_ref_id / goriyaku） |
| 7 | Source: lookalike 行（normalized_url / identity / compatible flag 付き）と Source state counts |
| 8 | target Deity / History / History→Source relation / SourceFact 行、goriyaku tag link / GoriyakuAssignment count |
| 9 | `production_state_class_candidate`（A/B/C/D の SQL 判定。最終分類は Mother Ship が確認） |

credential / hostname / connection URL / database name は出力しない（boolean と version だけ）。

### 3.1 Source identity（PR review で修正）

初版は URL 全体を小文字化した広い一致を accepted Source として数えていた。これは importer の
`normalize_source_url()` と一致しない（path の大小、query、http/https の扱いが違う）ため、次のように分離した。

| 概念 | 定義 | 用途 |
|---|---|---|
| `source_identity_count` | `source_type = 'government'` かつ `url <> ''` かつ importer と同一の正規化 URL = `https://matsuri.geo-itoigawa.com/calendar/m04` | **accepted_source_count に使う唯一の値** |
| `source_metadata_compatible_count` | identity 行のうち `_SOURCE_REUSE_FIELDS`（publisher / verification_status / confidence / bibliography / language）が strip 後に seed と一致 | 再利用可否 |
| `source_url_lookalike_count` | source_type 不問、raw または正規化 URL に host と `calendar…m04` を含む | 診断のみ。再利用根拠にしない |

SQL の `normalized_url` は `normalize_source_url()` を再現する: Python `str.strip()` と同じ空白集合の除去、
`urlsplit()` と同じ C0 制御文字の左除去と TAB/CR/LF の除去、scheme と hostname の小文字化、userinfo 除去、
default port（http 80 / https 443、先頭0付きも含む）除去、fragment 除去、root 以外の末尾 `/` 無視、
path の大小保持、query の byte 保持、http と https の区別。importer が `ValueError` で停止する URL
（不正 port / bracket host）は NULL になり identity に数えない。

同一の block（`-- BEGIN/END nsrc_000002_source_identity`）を preflight と3つの guard に置いた。
`backend/temples/tests/test_nsrc_000002_g7_source_identity_sql.py` が次を検証する:

- 4 file の block が byte 一致
- 表記揺れ・非 identity・一般 URL・importer が停止する URL の corpus（64件）で SQL `normalized_url` = Python `normalize_source_url()`
- identity / lookalike / metadata compatible の分離

`source_identity_state`:

| 条件 | state |
|---|---|
| identity > 1 | `CONFLICT_IDENTITY_AMBIGUOUS` |
| identity = 1 かつ compatible = 0 | `CONFLICT_METADATA_DRIFT` |
| importer が解析できない government URL がある | `CONFLICT_IMPORTER_UNPARSEABLE_URL` |
| identity ではない lookalike がある | `CONFLICT_NON_IDENTITY_LOOKALIKE` |
| identity = 1 かつ compatible = 1 | `REUSABLE` |
| identity = 0 | `ABSENT` |

identity ではない lookalike（例: `http://` 版や別 source_type の同 URL）は再利用しない。
その状態で import すると近似 URL の Source が並存するため、fail closed として CONFLICT に寄せ、Mother Ship 判断にした。
government 行に importer が解析できない URL が1件でもあると importer 自体が停止するので、これも CONFLICT とした。

---

## 4. Phase 2 / Phase 3 — Production 実測と expected delta

Production read-only preflight（`nsrc_000002_g7_preflight.sql`）は Mother Ship 側で実行された。
本実行環境からは実行していない。以下は受け取った実測値である。

~~~text
server_version                     = 17.6
latest_temples_migration           = 0120_shrine_source_fact_foundation

Shrine                             = 121
Source                             = 140
Deity                              = 295
History                            = 228
SourceFact                         = 34

target exact                       = 0
same-name 青澤神社                 = 0
same-name 青沢神社                 = 0
same-address                       = 0

source_identity_count              = 0
source_metadata_compatible_count   = 0
source_url_lookalike_count         = 0
source_url_lookalike_non_identity  = 0
government_url_unparseable_count   = 0
source_identity_state              = ABSENT

target Deity                       = 0
target History                     = 0
target SourceFact                  = 0
target goriyaku tag links          = 0
target goriyaku assignments        = 0

production_state_class_candidate   = CLEAN_CREATE
~~~

Mother Ship decision:

~~~text
G7_READ_ONLY_PREFLIGHT = PASS
PRODUCTION_STATE_CLASS = CLEAN_CREATE
~~~

`source_identity_state = ABSENT` のため、expected delta は Source を新規作成する case に確定した。

~~~text
EXPECTED_PRODUCTION_DELTA:
  Shrine     +1   (121 -> 122)
  Source     +1   (140 -> 141)
  Deity      +0   (295)
  History    +1   (228 -> 229)
  SourceFact +0   (34)
  goriyaku系 +0
~~~

PR #3152 で参考として記した nsrc-000004 G7 完了時点の記録値（121 / 140 / 295 / 228 / 34）と、今回の実測値は一致した。

---

## 5. Phase 4 — Fail-closed SQL

| file | 役割 |
|---|---|
| `sql/nsrc_000002_g7_backup_version_check.sql` | server version / major version |
| `sql/nsrc_000002_g7_pre_base_guard.sql` | Base write 直前の frozen pre-state 一致 |
| `sql/nsrc_000002_g7_post_base_guard.sql` | target Base 1行だけが増えた状態 |
| `sql/nsrc_000002_g7_post_knowledge_verification.sql` | Knowledge import 後の最終状態 |

すべて SELECT / WITH のみ（`guard.py check-readonly-sql` = SAFE）。Production の numeric PK は参照しない。

### Frozen pre-state block

3つの guard は先頭に同じ `frozen` CTE を持つ。

~~~text
shrine_total / source_total / deity_total / history_total / source_fact_total
accepted_source_count   (= 実測 source_identity_count。0 か 1 だけが先へ進める)
~~~

PR #3152 では全値が `NULL::bigint`（どの guard も PASS できない fail closed 状態）だった。
本 freeze で §4 の Production 実測値に置き換えた。3 file の frozen block は byte 一致する。

~~~text
shrine_total          = 121
source_total          = 140
deity_total           = 295
history_total         = 228
source_fact_total     = 34
accepted_source_count = 0
~~~

Source identity block（`nsrc_000002_source_identity`）は変更していない。

### 判定条件

全 guard 共通の Source 条件:

~~~text
accepted_source_count IN (0, 1)
source_identity_count            = accepted（post-Knowledge は 1）
source_metadata_compatible_count = accepted（post-Knowledge は 1）
source_url_lookalike_count       = accepted（post-Knowledge は 1。identity 以外の lookalike = 0）
importer が解析できない government URL = 0
~~~

pre_base_guard:

~~~text
aggregate 5種 = frozen
target exact = 0 / same-name 青澤神社 = 0 / same-name 青沢神社 = 0 / same-address = 0
target Deity / History / SourceFact / goriyaku tag link / GoriyakuAssignment = 0
~~~

post_base_guard:

~~~text
Shrine = frozen + 1、Source / Deity / History / SourceFact = frozen
target exact = 1 / same-name 青澤神社 = 1 / same-name 青沢神社 = 0 / same-address = 1
|latitude - 37.00763484| < 1e-8 かつ |longitude - 137.79024297| < 1e-8、goriyaku = ''
goriyaku tag link = 0 / GoriyakuAssignment = 0、target Deity / History / SourceFact = 0
~~~

post_knowledge_verification（detail SELECT + 最終 pass 判定）:

~~~text
Shrine = frozen + 1 / Source = frozen + (1 - accepted_source_count)
Deity = frozen / History = frozen + 1 / SourceFact = frozen
target exact = 1、canonical coordinate、goriyaku ''
target Deity = 0 / History = 1 / SourceFact = 0
History = regional_context / 青沢神社の春季祭礼 / 毎年4月第3日曜日 / event_date NULL / source_confirmed / high
History-Source relation = 1、その Source は identity かつ metadata compatible
source-less History = 0、goriyaku tag link = 0 / GoriyakuAssignment = 0
~~~

### Disposable local DB simulation（Production ではない）

すべて disposable local PostgreSQL DB（名前に `migration_safety_audit` を含む）で、`readonly_query.sh` 経由で実行した。
共通の模擬 pre-state: canonical Base Seed から青澤神社を除いた121行 + `nsrc_000004_seed.json`
（Shrine 121 / Source 3 / Deity 2 / History 2 / SourceFact 11）。
各 case で preflight を実行し、その実測値を scratch copy の frozen block に入れて guard を実行した（repo の file は NULL のまま）。
repo の file そのまま（frozen NULL）の guard は、どの state でも FAIL（error）になる。

#### Case A — `accepted_source_count = 0`（Source 不在）

~~~text
preflight: source_identity 0 / compatible 0 / lookalike 0 / non-identity lookalike 0 / unparseable 0
           source_identity_state = ABSENT
           production_state_class_candidate = CLEAN_CREATE
frozen   : 121 / 3 / 2 / 2 / 11 / accepted 0
~~~

| step | pre_base | post_base | post_knowledge |
|---|---|---|---|
| pre-state（accepted=0） | **PASS** | FAIL | FAIL |
| pre-state を accepted=1 で凍結した場合 | FAIL | — | — |
| Base subset apply 後 | FAIL | **PASS** | FAIL |
| Knowledge apply 後 | FAIL | FAIL | **PASS** |

~~~text
Base dry-run / apply : done created=1 updated=0 skipped=0 total_seed=1（一致）
Knowledge dry-run    : {'source_CREATE': 1, 'history_CREATE': 1}
Knowledge apply      : sources created=1, deities created=0, histories created=1, source_facts created=0
final                : Shrine 121->122 / Source 3->4 / Deity 2->2 / History 2->3 / SourceFact 11->11 / goriyaku +0
post preflight       : REUSABLE / ALREADY_MATERIALIZED
second import        : Base created=0 skipped=1 / Knowledge {'source_REUSE_EXISTING': 1, 'history_SKIP_EXISTS': 1} / CREATE = 0
runtime QA           : G7_PRODUCTION_RUNTIME_QA=PASS / TRANSACTION_MODE=READ_ONLY
~~~

#### Case B — `accepted_source_count = 1`（metadata compatible な既存 Source を再利用）

target Shrine 不在のまま、seed と reuse 項目が一致する government Source を1件追加した。
URL は `https://matsuri.geo-itoigawa.com/calendar/m04`（末尾 `/` なし。seed と表記は違うが importer identity は同じ）。

~~~text
preflight: source_identity 1 / compatible 1 / lookalike 1 / non-identity lookalike 0 / unparseable 0
           source_identity_state = REUSABLE
           production_state_class_candidate = CLEAN_CREATE
frozen   : 121 / 4 / 2 / 2 / 11 / accepted 1
~~~

| step | pre_base | post_base | post_knowledge |
|---|---|---|---|
| pre-state（accepted=1） | **PASS** | FAIL | FAIL |
| pre-state を accepted=0 で凍結した場合 | FAIL | — | — |
| Base subset apply 後 | FAIL | **PASS** | FAIL |
| Knowledge apply 後 | FAIL | FAIL | **PASS** |

~~~text
Base dry-run / apply : done created=1 updated=0 skipped=0 total_seed=1（Shrine +1 / Source +0）
Knowledge dry-run    : {'source_REUSE_EXISTING': 1, 'history_CREATE': 1}
Knowledge apply      : sources created=0, deities created=0, histories created=1, source_facts created=0
final                : Shrine 121->122 / Source 4->4 / Deity 2->2 / History 2->3 / SourceFact 11->11 / goriyaku +0
post preflight       : REUSABLE / ALREADY_MATERIALIZED
second import        : Base created=0 skipped=1 / Knowledge {'source_REUSE_EXISTING': 1, 'history_SKIP_EXISTS': 1} / CREATE = 0
runtime QA           : G7_PRODUCTION_RUNTIME_QA=PASS / TRANSACTION_MODE=READ_ONLY
~~~

#### Negative cases（import を承認しない）

target Shrine 不在のまま、既存 Source だけを変えた。どれも Base import は実行していない。

| case | 既存 Source | preflight | pre_base（accepted=実測 / 逆値） | importer dry-run |
|---|---|---|---|---|
| metadata drift | identity 1件、publisher = `糸魚川市` | identity 1 / compatible 0 / `CONFLICT_METADATA_DRIFT` / class `CONFLICT` | FAIL / FAIL | `source_CONFLICT` / `SOURCE_REUSE_CONFLICT (meaningful metadata differs: publisher)` |
| identity ambiguous | `…/m04/` と `HTTPS://…:443/calendar/m04#x` の2件 | identity 2 / compatible 2 / `CONFLICT_IDENTITY_AMBIGUOUS` / class `CONFLICT` | FAIL / FAIL | `source_AMBIGUOUS` |
| non-identity lookalike | `http://…/calendar/m04/` の1件 | identity 0 / lookalike 1 / non-identity 1 / `CONFLICT_NON_IDENTITY_LOOKALIKE` / class `CONFLICT` | FAIL / FAIL | `source_CREATE`（importer は別 Source を作る。guard 側で止める） |

metadata drift の場合、frozen accepted を 1 にしても（compatible 0 ≠ 1）、0 にしても（identity 1 ≠ 0）guard は FAIL する。
推測で frozen 値を選んでも通らない。

simulation 用 DB 6個（template + 5 case）は検証後に削除した。

### 5.1 Committed frozen values の sequential simulation（freeze PR）

repo に commit した guard file（frozen 値入り、scratch copy ではない）を、そのまま `readonly_query.sh` 経由で実行した。
disposable local DB（Production ではない）を Production 実測 pre-state と同じ件数に作った:
canonical Base Seed から青澤神社を除いた121行 + `nsrc_000004_seed.json` に、非 target Shrine へ付けた
padding 行（Source は lookalike にならない `https://example.invalid/...` URL）を足して
Shrine 121 / Source 140 / Deity 295 / History 228 / SourceFact 34 にした。

模擬 pre-state の preflight:

~~~text
target exact / same-name / same-address = 0 / 0 / 0 / 0
source_identity 0 / compatible 0 / lookalike 0 / non-identity 0 / unparseable 0 / ABSENT
production_state_class_candidate = CLEAN_CREATE
~~~

| step | pre_base | post_base | post_knowledge |
|---|---|---|---|
| [1] pre-state（121 / 140 / 295 / 228 / 34） | **PASS** | FAIL | FAIL |
| [2] drifted pre-state（別 DB copy に無関係な History を1件追加、History 229） | **FAIL（closed）** | FAIL | FAIL |
| [3] Base subset のみ apply 後 | FAIL | **PASS** | FAIL |
| [4] Knowledge apply 後 | FAIL | FAIL | **PASS** |

~~~text
[3] Base dry-run / apply : done created=1 updated=0 skipped=0 total_seed=1（一致）
[4] Knowledge dry-run    : {'source_CREATE': 1, 'history_CREATE': 1}
    Knowledge apply      : sources created=1, deities created=0, histories created=1, collectives created=0,
                           memberships created=0, source_facts created=0
final state              : Shrine 122 / Source 141 / Deity 295 / History 229 / SourceFact 34
target                   : shrine 1 / deity 0 / history 1 / source_fact 0 / history_source_relations 1 /
                           sourceless_history 0 / goriyaku tag links 0 / assignments 0
post preflight           : production_state_class_candidate = ALREADY_MATERIALIZED
[5] second import        : Base created=0 skipped=1 / Knowledge {'source_REUSE_EXISTING': 1, 'history_SKIP_EXISTS': 1}
runtime QA               : G7_PRODUCTION_RUNTIME_QA=PASS / TRANSACTION_MODE=READ_ONLY
~~~

2つの disposable DB は検証後に削除した。

~~~text
PRE_BASE_GUARD_READY        = PASS
POST_BASE_GUARD_READY       = PASS
POST_KNOWLEDGE_VERIFY_READY = PASS
~~~

guard Ready は「Production pre-state を固定した guard が、同じ件数の模擬 DB で期待通りに通過 / 停止する」ことを意味する。
Production で guard を実行したことは意味しない。

---

## 6. Phase 5 — Target-only Base subset

`scripts/migration_safety/nsrc_000002_g7_extract_base_subset.py <OUTPUT_PATH>`

- canonical Base Seed から `name_jp + address` 完全一致の行を抽出し、1行でなければ停止
- 抽出行が凍結 G7 行（座標・goriyaku `""`・kyusei null・astro_elements []・location）と一致しなければ停止
- 出力先が repo 内なら `guard.is_safe_dump_path()` で拒否
- DB へは接続しない

ローカル実行:

~~~text
SUBSET_ROWS=1
name_jp=青澤神社
address=新潟県糸魚川市大字青海2696番地
SUBSET_SHA256=d5bcc3229b883314d54826f4381877102c4adcda7cb1e1b662ee876260bb7e40
~~~

- 2回実行して byte 一致（deterministic）
- repo 内の出力先は `BLOCKED` / exit 1
- 生成 file は scratch 領域にだけ置き、commit していない

模擬 DB での import（`import_shrines_seed --source <subset> --skip-goriyaku-tags`）:

~~~text
dry-run : CREATE 青澤神社 / goriyaku_tags rows=0 ... / done created=1 updated=0 skipped=0 total_seed=1
apply   : 同上（dry-run と一致）
再 dry-run: SKIP 青澤神社 / done created=0 updated=0 skipped=1 total_seed=1
~~~

Knowledge（模擬 DB）:

~~~text
dry-run : source_CREATE 1 / history_CREATE 1
apply   : sources created=1, deities created=0, histories created=1, collectives created=0, memberships created=0, source_facts created=0
再 dry-run: source_REUSE_EXISTING 1 / history_SKIP_EXISTS 1
~~~

---

## 7. Phase 6 — Production Runtime QA script

`scripts/migration_safety/nsrc_000002_g7_runtime_qa.py`

- 構造は `nsrc_000004_g7_runtime_qa.py`、期待値は `test_nsrc_000002_g6_runtime_qa.py` に合わせた（Deity assertion は流用していない）
- transaction 開始直後に `SET TRANSACTION READ ONLY`、全検証をその中で実行
- 期待: Deity 0 / History 1（regional_context / 青沢神社の春季祭礼、Source 1件）、沼河比賣命・沼河比売命なし、
  candidate 1件・distance 0・goriyaku_tag_ids []、Reason の deity None / shrine_history = H1 / goriyaku None /
  現行 assertive History 文 / 保証表現なし、Compass distance・bearing・direction filter
- Top1 は要求しない
- History の Source は `source_type = government` かつ `normalize_source_url(url)` が seed と一致することを確認する
  （Case B で再利用される既存 Source は URL 表記が seed と違い得るため。raw URL 比較だった初版は Case B で失敗し、修正した）

模擬 materialized DB（Case A / Case B の両方）での実行:

~~~text
DETAIL_RUNTIME=PASS
CONCIERGE_CANDIDATE_PATH=PASS
RECOMMENDATION_REASON=PASS
COMPASS_DISTANCE=PASS
COMPASS_DIRECTION=PASS
G7_PRODUCTION_RUNTIME_QA=PASS
TRANSACTION_MODE=READ_ONLY
exit=0
~~~

同じ設定の DB 接続で `SET TRANSACTION READ ONLY` 後の UPDATE が `InternalError` で拒否されることも確認した。

~~~text
PRODUCTION_RUNTIME_QA_READY = PASS
~~~

（script の準備完了を意味する。Production での Runtime QA は未実行。）

---

## 8. Phase 7 — Backup / restore readiness

~~~text
PRODUCTION_SERVER_VERSION       = 17.6 (Production read-only preflight, §4)
LOCAL_CLIENT (this environment) = pg_dump / psql / pg_restore 16.15
~~~

Production server は 17 系なので、本実行環境の client 16.15 では dump できない（major mismatch）。
nsrc-000004 G7 では client `17.10` で取得した（`docs/audit/niigata-h001-g7-production-import.md` §4.1）。
互換 client での backup / disposable restore / fingerprint 一致は未実施。

~~~text
BACKUP_CLIENT_COMPATIBILITY (this environment, client 16.15) = HOLD
~~~

（Mother Ship 側 client 17.10 での判定は §8.1。）

### Procedure（Production write 前に必須）

credential は repo 外・mode 600 の file に置き、値を出力しない（`scripts/migration_safety/README.md` Credential Bridge）。

1. `sql/nsrc_000002_g7_backup_version_check.sql` を read-only 実行し server major を確認
2. 同じ major 以上の `pg_dump` / `pg_dumpall` を `PG_DUMP_BIN` / `PG_DUMPALL_BIN` で明示
3. `dump_readonly.sh` で roles / schema / data を repo 外へ取得
4. `createdb` で名前に `restore_test` / `audit` / `migration_safety` を含む disposable local DB を作成
5. `restore_isolated.sh` で restore（拡張 PostGIS / pg_trgm を含めて完走すること）
6. restore DB と Production に `nsrc_000002_g7_preflight.sql` を実行し、出力が完全一致すること
7. どれかが失敗したら `G7_WRITE_READY = HOLD`、Production write へ進まない

### Local rehearsal（Production ではない）

模擬 DB を `dump_readonly.sh` で dump し（roles 640 / schema 135,584 / data 79,870 bytes）、
disposable DB へ `restore_isolated.sh` で restore した。両 DB の preflight 出力（73行）は完全一致した。
dump は scratch 領域にだけ置き、commit していない。2つの disposable DB は検証後に削除した。

~~~text
LOCAL_PROCEDURE_REHEARSAL = PASS
~~~

上記 rehearsal 時点では Production backup は未取得だった（`BACKUP_RESTORE_READINESS = HOLD`）。§8.1 で解消。

### 8.1 Production fresh backup / isolated restore（Mother Ship 実行）

Production backup と isolated restore は Mother Ship 側の環境で実行された。本 PR を作成した実行環境は
Production にも backup file にも接続していない。以下は受け取った観測値である。
credential / hostname / database name / connection 詳細は記録しない。

Client compatibility:

~~~text
Production PostgreSQL = 17.6
pg_dump               = 17.10
pg_dumpall            = 17.10
pg_restore            = 17.10
psql                  = 17.10

BACKUP_CLIENT_COMPATIBILITY = PASS   (client major 17 = server major 17)
~~~

Fresh Production backup（`dump_readonly.sh` の roles / schema / data 構成）:

| artifact | bytes |
| --- | ---: |
| `roles.sql` | 5,792 |
| `schema.sql` | 134,714 |
| `data.sql` | 11,761,148 |

~~~text
backup timestamp = 20261010202119
backup location  = repository 外（operator home 配下 ~/kami-musubi-backups/20261010202119）
~~~

backup file は repo に含めていない。

Isolated restore:

~~~text
restore target   = disposable local DB only（Production ではない）
ISOLATED_RESTORE = PASS
~~~

Restored DB fingerprint（restore DB に `nsrc_000002_g7_preflight.sql` を実行）:

~~~text
latest_temples_migration                = 0120_shrine_source_fact_foundation

Shrine                                  = 121
Source                                  = 140
Deity                                   = 295
History                                 = 228
SourceFact                              = 34

target_exact_count                      = 0
same_name_aosawa_kyuji_count            = 0
same_name_aosawa_shinji_count           = 0
same_address_count                      = 0

source_identity_count                   = 0
source_metadata_compatible_count        = 0
source_url_lookalike_count              = 0
source_url_lookalike_non_identity_count = 0
government_url_unparseable_count        = 0
source_identity_state                   = ABSENT

target Deity                            = 0
target History                          = 0
target SourceFact                       = 0
target goriyaku tag links               = 0
target goriyaku assignments             = 0

production_state_class_candidate        = CLEAN_CREATE
~~~

restore DB の fingerprint は §4 の Production read-only preflight 実測値とすべて一致した。

Frozen pre-Base guard（commit 済み `nsrc_000002_g7_pre_base_guard.sql`）を restore DB で実行:

~~~text
g7_pre_base_guard_pass = 1
~~~

Mother Ship decision:

~~~text
PRODUCTION_FRESH_BACKUP  = PASS
ISOLATED_RESTORE         = PASS
RESTORED_DB_FINGERPRINT  = PASS
ISOLATED_PRE_BASE_GUARD  = PASS
BACKUP_RESTORE_READINESS = PASS
~~~

Backup / restore readiness の PASS は Production write の承認を意味しない。

~~~text
PRODUCTION_WRITE_AUTHORIZED = NO
PRODUCTION_WRITE            = NONE
FORMAL_G7                   = NOT EXECUTED
~~~

---

## 9. Observations（変更していない）

1. `readonly_query.sh` / `check_credential_presence.sh` の permission 確認は `stat -f '%OLp' || stat -c '%a'` の順。
   Linux（GNU stat）では `stat -f` が filesystem 情報を返して成功するため、mode 600 の file でも
   `BLOCKED: file permissions are ...` になる。これは fail closed 側の不具合で、write を許す方向ではない。
   macOS では従来通り動く。本 PR では repo の script を変更せず、ローカル検証は順序だけ入れ替えた scratch copy で行った。
   同じ理由で、既存の `tests/test_credential_bridge_e2e.sh` / `tests/test_readonly_query_hostname_redaction.sh` も
   この Linux 環境では失敗する（どちらも本 PR で変更していない script の test）。
2. ローカルの test 設定（`DISABLE_GIS_FOR_TESTS=1`）は `temples.migrations_nogis` を使うため、
   模擬 DB の latest temples migration は `0019_shrine_source_fact_foundation` と出る。
   Production は `temples/migrations` で、実測値は `0120_shrine_source_fact_foundation`（§4）。

---

## 10. Validation

| check | 結果 |
|---|---|
| 新規 SQL 5 file `guard.py check-readonly-sql` | SAFE（5/5） |
| `test_nsrc_000002_g7_source_identity_sql.py`（SQL = importer 正規化、block 一致、概念分離） | 4 passed |
| Case A / Case B / metadata drift / ambiguous / non-identity lookalike simulation | 上記 §5 の通り |
| runtime QA script（Case A / Case B の materialized DB） | PASS / PASS |
| subset extraction（決定性 / repo 内出力拒否） | PASS |
| `scripts/migration_safety/tests/test_guard.py` | 49 passed |
| `scripts/migration_safety/tests/test_backup_logging.sh` | ALL CHECKS PASSED |
| `test_credential_bridge_e2e.sh` / `test_readonly_query_hostname_redaction.sh` | FAIL（既存の Linux `stat` 問題。§9） |
| nsrc-000002 Base / G4 / G5 / G6 test（4 file） | 20 passed |
| knowledge seed / source identity 関連（`-k 'knowledge_seed or source_identity or source_reuse'`） | 318 passed |
| `scripts/tests` | 685 passed |
| backend full suite | 4942 passed, 12 skipped |
| freeze PR: committed frozen guard の sequential simulation（§5.1） | pre PASS / drift FAIL / post-base PASS / post-knowledge PASS |
| freeze PR: nsrc-000002 Base / G4 / G5 / G6 / G7 test（5 file） | 24 passed |
| freeze PR: `test_guard.py` / `test_backup_logging.sh` / `scripts/tests` / backend full suite | 49 passed / PASS / 685 passed / 4942 passed, 12 skipped |
| `makemigrations --check` | No changes detected |
| ruff / black（新規 Python 3 file） | PASS |
| `git diff --check` | clean |
| credential / hostname / connection URL in diff | なし |

---

## 11. Changed files

~~~text
scripts/migration_safety/sql/nsrc_000002_g7_preflight.sql
scripts/migration_safety/sql/nsrc_000002_g7_backup_version_check.sql
scripts/migration_safety/sql/nsrc_000002_g7_pre_base_guard.sql
scripts/migration_safety/sql/nsrc_000002_g7_post_base_guard.sql
scripts/migration_safety/sql/nsrc_000002_g7_post_knowledge_verification.sql
scripts/migration_safety/nsrc_000002_g7_extract_base_subset.py
scripts/migration_safety/nsrc_000002_g7_runtime_qa.py
backend/temples/tests/test_nsrc_000002_g7_source_identity_sql.py
docs/audit/niigata-h001-nsrc-000002-g7-production-import-preflight.md
~~~

Runtime 実装、importer（`knowledge_seed.py`）、Base Seed、Knowledge Seed、Candidate Master、models / migrations、Production 設定は変更していない。

---

## 12. Not executed / next

~~~text
Production backup / restore      = DONE by Mother Ship (§8.1)
Base Shrine apply                = NOT EXECUTED
Knowledge Seed apply             = NOT EXECUTED
INSERT / UPDATE / DELETE         = NONE
Candidate Master transition      = NOT EXECUTED
G8                               = NOT EXECUTED

PRODUCTION_WRITE_AUTHORIZED = NO
PRODUCTION_WRITE            = NONE
FORMAL_G7                   = NOT EXECUTED
~~~

次に必要なこと（Mother Ship 判断）:

1. Production write の明示承認を受ける
2. 承認後: Production で pre-Base guard → target Base subset のみ apply → post-Base guard → Knowledge apply →
   post-Knowledge verification → idempotency → Production Runtime QA
3. 各 step の実測を記録したうえで Formal G7 を判定する
