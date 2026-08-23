> **Status: `BATCH17_PRODUCTION_IMPORT_STOPPED_NO_SAFE_EXECUTION_PATH`。**
>
> 本監査は、PR #2546でdevelopへマージ済みのBatch 17 Production Knowledge
> Seed（`backend/temples/data/knowledge_seeds/batch_17_seed.json`）を対象に、
> Production Importの実行可否を確認した記録である。**Production Importは
> 実行していない。** Phase 3（Render無料枠での実行可能性確認）の時点で、
> このセッション（cloud sandbox）には既存の安全なProduction書き込み経路が
> 存在しないことが確定したため、そこでSTOPした。Production DBへの接続・
> 書き込みは一切行っていない。Seed・Model・Migration・Importer・Evidence
> Gate・Recommendation・Contractのいずれも変更していない。

# Knowledge Batch 17 — Production Import Preflight & Execution

## Scope

- Batch 17 Production Import（北海道神宮・建部大社・波上宮、25 Fact）の
  実行可否確認
- 既存Production Import手順・既存Render無料枠運用・既存Knowledge
  Contractのみを正本とし、新しいImport方式は設計しない
- STOP Gateを1件でも満たさない場合はProduction Importを実行しない

## Preconditions（Phase 0）

| 項目 | 結果 |
|---|---|
| メインworking tree | 変更なし（`docs/shrine-geographic-expansion-rollout-plan`branch、touchしていない） |
| 既存worktree（`shrine-human-review`・`naminoue-human-review`・`batch1-validation`・`takebe-h2-closure`・`batch17-seed`） | 変更なし。いずれもtouchしていない |
| `origin/develop`最新化 | `git fetch origin develop`実行、`origin/develop` SHA=`2070a60082b3802d5b5687bc9518028af2a44a2d`（`fix: Compass Purposeとご利益mappingを修正 (#2545)`）を記録 |
| PR #2546内容のdevelop反映確認 | `git show origin/develop:backend/temples/data/knowledge_seeds/batch_17_seed.json`で存在確認、SHA-256一致確認（後述） |
| `docs/audit/knowledge-batch17-seed-preflight.md`存在確認 | develop上に存在確認済み |
| `ops/shrine-knowledge-batch17-production-import`branch/worktree衝突 | なし（事前確認） |
| worktree作成 | `git worktree add ../jinja_app-batch17-production-import -b ops/shrine-knowledge-batch17-production-import origin/develop` |
| worktree内working tree | clean（作成直後に確認） |
| Compass branch/worktreeへの変更 | 0（一切touchしていない） |

STOP条件（PR #2546未反映、batch_17_seed.json不在、branch/worktree衝突、
origin/develop以外を基点、unrelated変更、Compass側変更が必要）は
いずれも該当しなかった。Phase 0は全項目PASS。

## Seed Path

`backend/temples/data/knowledge_seeds/batch_17_seed.json`

SHA-256（本worktree、develop起点）:
`7b11943e137f8040ff25b21becc726b2df3182cb0b0f699f8e23c5c322fd8013`
（PR #2546時点の値と完全一致、`git diff origin/develop -- <path>`で
差分0行を確認）

## 正本Fresh Read（Phase 1）

以下を本worktree上でfresh readした。

- `backend/temples/data/knowledge_seeds/batch_17_seed.json`
- `backend/temples/tests/test_batch17_knowledge_seed.py`
- `docs/audit/knowledge-batch17-seed-preflight.md`
- `docs/audit/shrine-expansion-batch1-human-review.md`
- `docs/audit/shrine-expansion-batch1-post-review-validation.md`
- `docs/audit/shrine-expansion-batch1-data-quality-closure.md`
- `docs/knowledge/shrine-knowledge-contract.md`
- `backend/temples/management/commands/import_shrine_knowledge.py`（全文）
- `backend/temples/services/evidence_gate.py`（既存確認済み内容の再確認）

既存内容の再設計は行っていない。

## 過去Production Import運用の調査（Phase 2）

`docs/audit/`配下を横断検索し、既存実績を確認した（新しい方式は考案
していない）。

| 確認項目 | 結果 |
|---|---|
| Productionへ実際に投入済みの最終Batch | **Batch 16**（`docs/audit/knowledge-batch16-production-import-execution.md`、`BATCH16_PRODUCTION_IMPORT_EXECUTED`） |
| 使用command | `import_shrine_knowledge <seed.json>`（flagなし、apply mode）。事前に`--validate-only`・`--dry-run`を通過済み |
| Import前の再現性基盤 | `docs/audit/knowledge-production-import-foundation.md`（`KNOWLEDGE_IMPORT_READY_WITH_LIMITATIONS`）。Batch 1〜7はDjango shell経由のORM直接投入で、再現可能な構造化ファイルが残っていなかった（`LOCAL_DB_ONLY`）ことが判明し、`export_shrine_knowledge`でBatch 1〜7を`batch_1_7_seed.json`へ変換してから以後`FULLY_REPRODUCIBLE`運用へ移行 |
| Import前確認項目 | seed schema valid・shrine identity一意（`AMBIGUOUS`/`NOT_FOUND`0件）・dry-run error 0・duplicate source conflict 0・期待件数一致・idempotency PASS・Production-equivalent test PASS・fresh backup available（Foundation doc Section 11 Acceptance Criteria） |
| Import後確認項目 | Source/Deity/History件数の前後差分、5社（Batch16時点）のper-shrine件数・identity一致、source-less 0件、application aggregate不変、idempotency dry-run（2回目でCREATE 0）、Runtime QA（Production APIでHTTP 200・件数一致） |
| Audit記録方法 | `knowledge-batch<N>-seed-preflight.md`（Import前）→`knowledge-batch<N>-production-import-execution.md`（Import後）の2文書構成 |
| 再実行時の挙動・idempotency | 同一seedの2回目実行は全件`SKIP_EXISTS`/`REUSE_EXISTING`、`CREATE`は0件になることを実測確認済み（Foundation doc Section 8・9、Batch16 execution doc Section 15） |
| CREATE/SKIP_EXISTS/CONFLICT/AMBIGUOUSの扱い | Source: 既存と同一identityなら`REUSE_EXISTING`、metadata不一致は`SOURCE_REUSE_CONFLICT`、複数一致は`SOURCE_REUSE_AMBIGUOUS`（全体停止）。Shrine: `resolve_shrine()`が`NOT_FOUND`/`AMBIGUOUS`なら該当Shrineをエラーとして記録し全体を停止（推測解決なし）。Deity/History: 既存一致なら`SKIP_EXISTS`（**silent overwriteしない**）、新規のみ`CREATE` |
| **実際の書き込み実行経路** | **ローカルMac + `~/.config/kami-musubi/production-db.env`（repo外、mode 600、`.gitignore`対象、Production DATABASE_URLを含む）を人間が事前に用意し、`DATABASE_URL`をそのセッションでexportした状態で`python manage.py import_shrine_knowledge <seed> [--dry-run]`をローカルから直接実行**（`docs/audit/local-mac-direct-migration-execution-safety.md`「候補F」、`scripts/migration_safety/README.md`「Credential Bridge」節） |

Batch 16以前の実績はいずれも既存の`import_shrine_knowledge`・既存
`export_shrine_knowledge`をそのまま使用しており、新しいImport方式・
新しいWorkflow・新しい管理endpointは一切導入されていない。

## Render無料枠での実行可能性確認（Phase 3、STOP判定）

`docs/audit/local-mac-direct-migration-execution-safety.md`・
`scripts/migration_safety/README.md`を確認した結果、本プロジェクトの
確定済み事実として以下がある。

| 候補 | 状態 |
|---|---|
| Render Shell | **Free planでは利用不可と確定済み**（`local-mac-direct-migration-execution-safety.md`、ユーザー確認済み事実として記録） |
| Render One-Off Job | **Free planでは利用不可と確定済み**（同上） |
| Render Pre-Deploy Command等 | 有料plan前提（既存監査で確定、本プロジェクトは無料枠のため対象外） |
| GitHub Actions workflow経由のProduction書き込み | `.github/workflows/`配下を確認した結果、Production DBへ書き込むworkflowは存在しない（`backend-tests.yml`・`runner-smoke.yml`・`mobile-ci.yml`・`backend-integration.yml`・`web-tests.yml`・`dependency-review.yml`・`readme-guard.yml`・`backend-pr.yml`・`codeql.yml`のいずれもCI検証用で、Production接続を行わない） |
| **既存の唯一の実績ある経路（候補F）** | **ローカルMacから、repo外・mode 600の credential file（`~/.config/kami-musubi/production-db.env`）を人間が事前に用意し、そのセッションで`DATABASE_URL`をexportした状態で`manage.py import_shrine_knowledge`を直接実行する** |

`scripts/migration_safety/README.md`の「Credential Bridge」節は、この
credential fileのセットアップを明示的に**「you do this yourself, once,
locally」**（人間が自分のローカル環境で一度だけ行う）と定め、
**「Never paste it into a chat with an AI assistant. Never commit it.」**
と明記している。これは、AIアシスタント（本セッション含む）がこの
credentialを直接扱わないことを前提とした設計である。

### 本セッションでの確認（booleanのみ、値は一切取得・出力していない）

```
$ test -f ~/.config/kami-musubi/production-db.env
→ CREDENTIAL FILE DOES NOT EXIST

$ bash scripts/migration_safety/check_credential_presence.sh \
    ~/.config/kami-musubi/production-db.env DATABASE_URL
VAR_SET=0
[check_credential_presence] no credential file at that path yet
```

このセッション（cloud sandbox、ユーザーのローカルMacとは別環境）には、
Production DBへ接続するためのcredential fileが存在しない。`readonly_query.sh`・
`import_shrine_knowledge`のいずれも、Production DATABASE_URLなしでは
Production DBへ到達できない（`scripts/migration_safety/README.md`
「Every script here requires a `DATABASE_URL`-style argument explicitly —
there is no default, no ambient credential lookup」）。

### 判定

**STOP。** 以下のSTOP条件に該当する。

- 「Render Shellしか既存手段がない」→ 該当しない（Render Shell自体が
  利用不可と確定済みのため、Renderには依存しない経路（候補F）が
  既存の唯一の実績経路である）
- **「Production DB接続方法が不明」→ 該当する。** 接続方法自体は
  文書化されているが（候補F）、それを実行するために必要な
  credential file（人間がローカルMacで用意するもの）がこのセッションには
  存在しない
- 「新規workflow追加が必要」→ 該当しない（既存workflow・既存commandの
  範囲で対応可能。本セッションに実行権限がないだけ）
- 「新規管理endpointが必要」→ 該当しない
- 「Secret追加が必要」→ **該当する可能性がある。** ただしこれは
  「新しいSecretを新設する」という意味ではなく、「既存の運用契約上、
  Production credentialはこのAIセッションへ持ち込まない・パスさせない
  という設計」が守られている結果である。Secretをこのセッションへ
  追加で渡すこと自体が、`scripts/migration_safety/README.md`の
  明示的な禁止事項（「Never paste it into a chat with an AI assistant」）
  に抵触するため、要求しない

**このセッションからProduction Importを実行する既存の安全な経路は
存在しない。** 新しい経路（例: Production credentialをこのチャットへ
貼り付けてもらう、新しいCI workflowを追加する等）を推測で作らず、
ここでSTOPする。

## Phase 4以降の扱い

Phase 3でSTOPしたため、Phase 6（Production Import Preflight、Production
DBに対するvalidate-only/dry-run）・Phase 7（Import前Snapshot）・
Phase 9（Production Import本体）・Phase 10〜13（Import後確認、API
Smoke Check、Coverage再計測）はいずれも実行していない。Production DBへの
接続が本セッションから一切できないため、これらのPhaseは技術的に実行
不可能である。

Production DBへ接続しない範囲のPhase（Phase 4: Seed Integrity Gate、
Phase 5: Importer Safety確認）は、値の再確認・安全性の記録として実施した。

### Phase 4 — Batch 17 Seed Integrity Gate（PASS、DB接続不要）

`parse_seed()`（既存実装、無変更）で本worktree上のSeedを再確認した。

| 指標 | 値 |
|---|---:|
| errors | 0 |
| Source count | 5 |
| Shrine count | 3 |
| Deity count | 12 |
| History count | 13 |
| Total | 25 |

| Shrine | Deity | History |
|---|---:|---:|
| 北海道神宮 | 4 | 3 |
| 建部大社 | 2 | 4 |
| 波上宮 | 6 | 6 |

期待値と完全一致。加えて以下を確認した。

- Source key重複なし（5 key全て一意）
- Fact source relation欠落なし（全25 Factがsource_keysを持つ）
- 建部大社H2-A/H2-B: `history_type=tradition`・`verification_status=disputed`・
  `confidence=high`・`event_date=null`・`period_text`（675年/676年）
  いずれも維持を確認
- Source B（見どころ）URL: `https://takebetaisha.jp/features/`維持を確認
- 波上宮H5-B content: 「境内整備」を含まないことを維持確認
- `git diff origin/develop -- backend/temples/data/knowledge_seeds/batch_17_seed.json`
  の差分行数=0、SHA-256一致——PR #2546からSeedが一切変化していないこと
  を確認

shrine identityが既存Production Shrineと一意に対応可能かどうかは、
Production DBへ接続できないため本監査では確認できていない（**未確認**、
推測PASSにしない）。既存Foundation doc（Section 5）が、この3社を含む
Batch 1〜16以前の対象神社と同型の`resolve_shrine()`ロジック
（`name_jp`+`address`一致、`place_ref_id IS NULL`優先）で解決される設計
であることは確認したが、Production実データに対する実測は未実施である。

### Phase 5 — Importer Safety確認（コードからの再確認のみ、変更なし）

`import_shrine_knowledge.py`を全文読み直し、以下を確認した。

| 確認項目 | 結果 |
|---|---|
| CREATE条件 | Source: 既存と同一identity（`source_type`+URL正規化、またはURLなしなら`source_type`+`title`+`bibliography`）が無ければCREATE。Deity: `shrine`+`display_name`一致が無ければCREATE。History: `shrine`+`history_type`+`title`一致が無ければCREATE |
| UPDATEの有無 | **存在しない。** 既存Fact/Sourceの内容修正を行うコードパスはコマンド内に一切ない |
| SKIP_EXISTS条件 | Deity/Historyで既存一致がある場合。**silent overwriteしない**（既存行の内容は一切書き換えない） |
| CONFLICT条件 | Source識別で既存と複数項目（publisher/verification_status/confidence/bibliography/language等）が不一致の場合、`SOURCE_REUSE_CONFLICT`として`plan.errors`へ追加され、全体を停止する |
| AMBIGUOUS条件 | Source識別で複数の既存候補に一致する場合`SOURCE_REUSE_AMBIGUOUS`。Shrine識別で複数一致し`place_ref_id IS NULL`優先でも絞れない場合`IMPORT_IDENTITY_AMBIGUOUS`。いずれも`plan.errors`へ追加され全体を停止する |
| transaction境界 | `with transaction.atomic():`が`_apply()`全体（全Source→全Shrine→全Deity/History→M2M）を単一transactionで包む（コード264-270行目付近） |
| partial import可能性 | **なし。** `plan.errors`が1件でもあれば`transaction.atomic()`ブロックへ到達する前に`CommandError`で停止する（apply自体を呼ばない）。apply中に`full_clean()`が失敗した場合も、Djangoの`transaction.atomic()`により例外伝播で自動rollbackされ、部分的な行は残らない |
| error時rollback | 上記のとおり自動（Djangoの標準`transaction.atomic()`挙動） |
| `--force`等の破壊的option | **存在しない。** `add_arguments`は`seed_path`（位置引数）・`--validate-only`・`--dry-run`の3つのみ。apply modeはflagなしで実行する既存仕様であり、破壊的optionは実装されていない |
| duplicate import時の挙動 | 同一seedを再実行しても、既存Source/Deity/Historyはすべて`REUSE_EXISTING`/`SKIP_EXISTS`となり、新規作成は発生しない（Foundation doc・Batch16 execution docの両方で実測確認済み。本セッションでもBatch17 test`test_batch17_seed_import_is_idempotent_and_preserves_unrelated_knowledge`で再確認済み、PR #2546） |

**安全性は既存コードから確認できた。** Importerの変更は行っていない。

## Import前Snapshot（Phase 7、未実施）

Production DBへの接続経路がないため、Production側のSnapshotは取得
していない。**未確認。** scratch DB側の状態（このセッション専用の
local PostgreSQL）はPR #2546時点で既に確認済み（3社ともDeity 0/History 0、
`docs/audit/knowledge-batch17-seed-preflight.md`参照）であり、本監査は
それを再取得していない。

## STOP Gate結果（Phase 8）

| チェック項目 | 結果 |
|---|---|
| origin/develop上のBatch 17を使用 | PASS |
| Seed integrity | PASS（Phase 4） |
| validate-only（Production対象） | **未実施**（Production接続不可） |
| dry-run（Production対象） | **未実施**（Production接続不可） |
| Importer safety確認済み | PASS（Phase 5） |
| Production実行経路が既存運用 | PASS（候補Fとして存在するが、本セッションからは実行不可） |
| Render無料枠で実行可能 | **N/A / STOP。** Render Shell/One-Off Jobsは利用不可と確定済み。既存の代替経路（候補F、ローカルMac direct）はこのセッションから実行できない |
| Production credentialsの露出なし | PASS（値を一切取得・出力していない。存在確認はbooleanのみ） |
| Import前Snapshot取得済み | **未実施**（Production接続不可） |
| CONFLICT 0 | **未確認**（Production dry-run未実施のため） |
| AMBIGUOUS 0 | **未確認**（同上） |
| Fact count期待値と一致 | PASS（Seed側、Phase 4） |
| H2-A/H2-B disputed維持 | PASS（Seed側、Phase 4） |
| unrelated変更0 | PASS |

**1項目以上（Render無料枠での実行可能性、Production側validate-only/
dry-run、Import前Snapshot、CONFLICT/AMBIGUOUS実測）が未達のため、
Final STOP Gateは通過しない。**

## Production Import（Phase 9、未実行）

**実行していない。** STOP Gate不通過のため。

## Import後Verification / disputed Fact確認 / API Smoke Check / Coverage再計測（Phase 10〜13、未実施）

いずれもProduction DBへの接続が本セッションからできないため未実施。
「未確認」として記録する（推測でPASSとしない）。

## Coverage（Phase 13）

未実施（Production DB接続不可のため）。

## Deviations

期待値との差異は発生していない（Production Importを実行していない
ため、Import結果自体が存在しない）。Seed（`batch_17_seed.json`）は
PR #2546時点から一切変更していない。

## STOP / HOLD

**STOP: `RENDER_FREE_TIER_NO_SAFE_PRODUCTION_WRITE_PATH_FROM_THIS_SESSION`**

理由: 本プロジェクトの既存の唯一実績あるProduction書き込み経路（候補F、
`docs/audit/local-mac-direct-migration-execution-safety.md`）は、
人間がローカルMac上で事前に用意するcredential file
（`~/.config/kami-musubi/production-db.env`）を必要とする設計であり、
この設計自体が「Production credentialをAIアシスタントのセッションへ
持ち込まない」ことを意図している（`scripts/migration_safety/README.md`
「Credential Bridge」節）。本セッション（cloud sandbox）にはこの
credential fileが存在しないことをbooleanのみで確認済みであり
（値は一切取得・出力していない）、Production DBへの接続手段が存在しない。

Mother Shipへ必要事項:

- Batch 17 Production Importを実行する場合、**ユーザー自身のローカルMac**
  で、`docs/audit/local-mac-direct-migration-execution-safety.md`・
  `scripts/migration_safety/README.md`が定める手順（credential file
  セットアップ→`import_shrine_knowledge batch_17_seed.json --validate-only`
  →`--dry-run`→flagなしでapply→`readonly_query.sh`等での事後確認）に
  従って人間が直接実行するか、
- 本セッション（AIアシスタント）にProduction credentialを安全に
  渡す新しい仕組みを別途構築するかを、Mother Ship側で判断する必要がある

いずれの場合も、本監査が確認した事実（Seed integrity PASS、Importer
safety確認済み、期待Fact構造・disputed挙動はSeed側で全てPASS）は
そのまま利用できる。Seed自体の再検証は不要。

## Production Result

**`NOT_EXECUTED`（`STOPPED_AT_PHASE_3`）**

「SUCCESS」とは判定しない。Production Importは実行されておらず、
Production DB上のBatch 17データの有無・状態は本監査の対象外（未確認）
のままである。

## 変更ファイル

`docs/audit/knowledge-batch17-production-import.md`（本ドキュメント）
1件のみ。

- Seed（`batch_17_seed.json`）変更 = 0
- Model / Migration変更 = 0
- Importer変更 = 0
- Evidence Gate変更 = 0
- Recommendation変更 = 0
- Source Contract変更 = 0
- Knowledge Contract変更 = 0
- Production DB接続 = 0
- Production DB write = 0
- Production credential値の取得・出力 = 0
- unrelated file変更 = 0
- Compass branch/worktreeへの変更 = 0

## Validation（Phase 15）

```
$ git status --short
?? docs/audit/knowledge-batch17-production-import.md
$ git diff --check
（無出力 = 問題なし）
$ git diff origin/develop -- backend/temples/data/knowledge_seeds/batch_17_seed.json
（無出力 = Seed差分0）
```

変更（新規追加）は本Audit文書1件のみ。Seed・Code・Model・Migration・
Importer・Evidence Gate・Recommendation・unrelated変更はいずれも0件。
main working tree・他worktree（Compass含む）はいずれも未変更。
