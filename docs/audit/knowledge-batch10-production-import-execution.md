# Knowledge Batch 10 — Production Import Execution Gate + Execution Record

> **Status: `BATCH10_PRODUCTION_IMPORT_EXECUTED`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch10-seed-preflight.md`
> （`BATCH10_PRODUCTION_IMPORT_READY_WITH_LIMITATIONS`）を受け、Production
> Import実行直前の最終Gate（環境整合性・Credential Gate・Seed Integrity・
> Production pre-state・Coverage・Source conflict最終再確認・Fresh Backup・
> Production `--validate-only`/`--dry-run`・Production-equivalent最終
> テスト・Runtime Payload再計算・Human Execution Boundary）をすべて実施し、
> Mother Shipの明示的承認を得た上で、実際にProduction Knowledge Data
> importを実行した記録である。

develop SHA（作業開始時点）: `06758039...`（PR #2358反映済み、`origin/develop`
と同期済み、working tree clean）。

---

## Execution Gate（Production write前の最終確認、すべてPASS）

| Phase | 項目 | 結果 |
|---|---|---|
| 1 | Environment parity | Python 3.11.13 / Django 5.2.16（requirements一致）/ psycopg 3.3.4（requirements一致）、`manage.py check` 0 issues（DEBUG=0/USE_GIS=1） |
| 2 | Credential Gate | `VAR_SET=1`、valid PostgreSQL shape、値/hostname非表示 |
| 3 | Seed integrity | SHA-256 `e44484431af89274c3ba7258e49dac7cd2b186f8d0bfebb62b60137d0b7255d9` fresh再計算で完全一致。Shrine5/Source6/Deity19/History10/relation19+10/source-less0/duplicate0/invalid enum0/PK hardcode0 |
| 4 | Production pre-state | Source70・Deity130・History96・relation143/101・Knowledge Shrine51、対象5社全件canonical・Knowledge none、drift 0 |
| 5 | Coverage pre-state | complete49・partial2・none54（fresh再計算） |
| 6 | Application baseline | auth_user1・userprofile1・shrine105・favorite3・visit2・goriyakutag39・shrine_goriyaku_rel283 |
| 7 | Source semantic conflict最終再確認 | 全6候補、Production既存70件との一致0件、全件`NO_CONFLICT` |
| 8 | Fresh Backup | PostgreSQL17バージョン一致クライアントでroles.sql(5426B)/schema.sql(93021B)/data.sql(4105505B)取得、接続情報非開示 |
| 9 | Production `--validate-only` | `validate-only: OK, no errors` |
| 10 | Production `--dry-run` | `{'source_CREATE': 6, 'deity_CREATE': 19, 'history_CREATE': 10}`、SKIP/UPDATE/REUSE/error 全て0 |
| 11 | Production-equivalent最終テスト | Phase 8のfresh backupをisolated DBへ復元。baseline一致・5社Knowledge none・validate-only PASS・dry-run exact・import exit0・全delta一致（70→76/130→149/96→106/143→162/101→111/51→56）・coverage一致（49→54/2/54→49）・source-less0・contamination0・無関係aggregate完全不変・2回目dry-run（CREATE0・全REUSE/SKIP・error0） |
| 12 | Runtime expected payload | 大國魂神社(deity7/history2/source1)・寒川神社(2/2/2)・浅草神社(3/2/1)・川越氷川神社(5/2/1)・芝大神宮(2/2/1)、合計Deity19/History10/UniqueSource6/relation29 |
| 13 | Remaining risk check | 靖國神社未着手（対象外）、大國魂神社「御霊大神」「国内諸神」スコープ外（seed note明記済み）、SKIP_EXISTS semantic-diff limitation・Source page instabilityは既知の一般的限界。新規懸念なし |
| 14 | Human Execution Boundary | 全項目PASS → `BATCH10_PRODUCTION_IMPORT_EXECUTION_READY` |
| 15 | Mandatory Human Confirmation | `AskUserQuestion`でMother Shipへ明示確認を要求し、「承認して実行」の回答を得た |

---

## Execution Record

**実行日時**: 2026-08-10 11:35 UTC（Human Execution Boundary通過後、承認直後）

**実行コマンド**（フラグなし = 適用モード、単一`transaction.atomic()`）:

```
python manage.py import_shrine_knowledge \
  backend/temples/data/knowledge_seeds/batch_10_seed.json
```

**結果**:

```
plan summary: {'source_CREATE': 6, 'deity_CREATE': 19, 'history_CREATE': 10}
import complete: sources created=6, deities created=19, histories created=10
```

exit code: `0`。plan通り、全件CREATE（REUSE/SKIP/UPDATE/error 0件）。

### Post-import verification（read-only、実行直後）

| 指標 | 実行前 | 実行後 | 期待値 | 判定 |
|---|---:|---:|---:|---|
| Source | 70 | 76 | 76 | 一致 |
| Deity | 130 | 149 | 149 | 一致 |
| History | 96 | 106 | 106 | 一致 |
| Deity–Source relation | 143 | 162 | 162 | 一致 |
| History–Source relation | 101 | 111 | 111 | 一致 |
| Knowledge Shrine | 51 | 56 | 56 | 一致 |

対象5社のdeity/history内訳（fresh read-only確認）:

| shrine | deity | history |
|---|---:|---:|
| 大國魂神社 | 7 | 2 |
| 寒川神社 | 2 | 2 |
| 浅草神社 | 3 | 2 |
| 川越氷川神社 | 5 | 2 |
| 芝大神宮 | 2 | 2 |

いずれもseed件数と完全一致。`same_name_count`は全件1（重複混入なし）。

**Coverage（fresh read-only確認）**: complete 49→54・partial 2（不変）・none 54→49
— Section「Runtime expected payload」の投影値と完全一致。

**source-less（対象5社）**: Deity 0・History 0。

**Application baseline（無関係集計、fresh read-only確認）**: auth_user1・
userprofile1・shrine105・favorite3・visit2・goriyakutag39・
shrine_goriyaku_rel283 — 実行前と完全に不変。

**Idempotency確認（read-only`--dry-run`、importの再実行ではない）**:

```
plan summary: {'source_REUSE_EXISTING': 6, 'deity_SKIP_EXISTS': 19, 'history_SKIP_EXISTS': 10}
dry-run: OK, no DB writes performed
```

全件REUSE_EXISTING/SKIP_EXISTS、CREATE 0件、error 0件。

---

## Final Classification

**`BATCH10_PRODUCTION_IMPORT_EXECUTED`**

Production Knowledge Data importが実際に実行され、期待どおりの結果を
すべての指標で確認した。second import（実書き込みの再実行）は行って
いない。実行後の`--dry-run`はidempotency確認のための読み取り専用操作
である。

---

## 絶対禁止事項の遵守

本ドキュメント作成セッションでは以下を一切実行していない:

- second import（実書き込みの再実行）
- manual Production SQL
- Batch 11の開始
- partial repair
- Score/Ranking変更
- Source UI
- PER_FACT_RENDERING
- Production restore
- credential表示

Production Batch 10 write = EXECUTED（1回のみ、承認後）
Batch 11 = NOT_STARTED
