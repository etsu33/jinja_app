> **Status: `KNOWLEDGE_PRODUCTION_IMPORT_GO_READY_WITH_LIMITATIONS`。**
>
> 本ドキュメントは`docs/audit/knowledge-production-import-foundation.md`
> （`KNOWLEDGE_IMPORT_READY_WITH_LIMITATIONS`）を受けて、Production
> Knowledge Importを実際に実行する直前の最終ゲートとして、canonical
> seedの再検証・Production dry-run再実行・fresh backup・
> production-equivalent最終テスト・実行コマンド固定・post-import
> verification契約・Runtime QA sample設計・STOP条件・recovery
> classificationを確定する。
>
> **本ドキュメント作成のセッションではProduction Knowledge Data write・
> Batch 8のいずれも実行していない。** Productionに対して実行したのは
> `readonly_query.sh`経由のSELECTと、`import_shrine_knowledge
> --validate-only`/`--dry-run`（いずれもDB書き込みなし）のみ。
> **Codexは本ドキュメント作成セッションでProduction importを実行しない。**
> Go/No-Go判断はMother Shipへ返す。

# Production Knowledge Import — Final Execution Gate

## 1. develop SHA

作業開始時点: `d2f74eb6ad4189d239f5efee3128a3877ec1e200`（PR #2341反映済み、
`origin/develop`と同期済み、working tree clean）。

---

## 2. Import Foundation Drift Check（Phase 1）

- [x] `git diff b6a17f90 -- backend/temples/services/knowledge_seed.py
  backend/temples/management/commands/{export,import}_shrine_knowledge.py
  backend/temples/data/knowledge_seeds/batch_1_7_seed.json` が空
  ——develop HEADはPR #2341でverify済みの内容と完全に同一
- [x] `.only(*_SHRINE_IDENTITY_FIELDS)`存在（`location`列非選択）
- [x] `resolve_shrine`内に曖昧な`name_jp`単独selectionなし
  （address narrowing → `place_ref_id IS NULL`優先 → それでも複数なら
  `AMBIGUOUS`で停止、という3段階のみ）
- [x] Production固有numeric PK hardcodeなし
- [x] `SKIP_EXISTS`ロジックによりsilent overwriteなし

drift 0件。

---

## 3. Seed Integrity（Phase 2）

| 項目 | 値 |
|---|---|
| ファイル | `backend/temples/data/knowledge_seeds/batch_1_7_seed.json` |
| SHA-256 | `b3748ecca0469f6b094ce71dc471595ec89e3aeb7e6fa71c806a8e2a9eac844a` |
| `schema_version` | `1.0` |
| Source数 | 59 |
| Deity数 | 103 |
| History数 | 85 |
| Shrine identity数 | 41（全件unique） |
| 期待 deity-source relation数（seedから事前算出） | 116 |
| 期待 history-source relation数（seedから事前算出） | 90 |
| `--validate-only`（local DB対象） | `OK, no errors` |

credential・row-level private dataは記録していない（公開されている
神社の祭神・由緒情報のみ）。

---

## 4. Production Current State（Phase 3）

read-only接続で確認（snapshot時刻`2026-08-10 07:04:04.752005+00`）:

| 項目 | 結果 |
|---|---|
| `users 0006`/`temples 0090`〜`0093` | すべて`applied` |
| `ShrineKnowledgeSource`/`ShrineDeity`/`ShrineHistory` | すべて`0`件 |
| `deity`/`history` source relation | すべて`0`件 |

`STOP_PRODUCTION_KNOWLEDGE_NOT_EMPTY`には該当しない。

---

## 5. Production Existing Application Baseline（Phase 4）

同一snapshotで取得:

| 項目 | 値 |
|---|---|
| `auth_user` | 1 |
| `userprofile` | 1 |
| `shrine` | 105 |
| `favorite` | 0 |
| `visit` | 2 |
| `shrine_goriyaku relation` | 283 |
| Knowledge coverage baseline | 0（`ShrineKnowledgeSource`等が0件のため） |

`temples 0091`のcanonical効果（id=21「長太稲荷神社」・id=22
「給田六所神社」の`history_theme`/`place_ref_id IS NULL`）も同時に
再確認し、無変化であることを確認した。

この値をImport後比較の基準値とする。

---

## 6. Production Dry-run（Phase 5）

Production credentialを使用したが、実行したのは`--validate-only`・
`--dry-run`のみ（write権限のあるコマンドは一切実行していない）。

```
validate-only: OK, no errors
```

```
plan summary: {'source_CREATE': 59, 'deity_CREATE': 103, 'history_CREATE': 85}
dry-run: OK, no DB writes performed
```

| 項目 | 期待 | 実測 | 判定 |
|---|---|---|---|
| Source CREATE | 59 | 59 | 一致 |
| Deity CREATE | 103 | 103 | 一致 |
| History CREATE | 85 | 85 | 一致 |
| ambiguity | 0 | 0 | 一致 |
| not found | 0 | 0 | 一致 |
| validation error | 0 | 0 | 一致 |
| UPDATE | 0 | 0 | 一致（`--allow-update`相当は未実装のためそもそも発生しない） |
| conflicting existing fact | 0 | 0 | 一致 |

想定と完全一致。`STOP`条件には該当しない。

---

## 7. Stable Identity Recheck（Phase 6）

41 shrineすべてが`AMBIGUOUS`/`NOT_FOUND`なく解決された（dry-run出力に
該当文字列0件）。unique性はseed自体でも確認済み（Section 3）。

**特に重点確認**: seedの41神社のうち`給田六所神社`は、
`docs/audit/temples-0091-production-remediation.md`で扱った実在の
duplicate shrine（canonical id=22、duplicate id=101）と同一名称である。
`resolve_shrine()`を実際にProductionへread-only接続して直接実行し、
以下を確認した:

```
給田六所神社 -> status=OK_CANONICAL_PREFERRED shrine_id=22
  detail=2 rows matched name_jp='給田六所神社'; resolved via
  place_ref_id IS NULL preference
長太稲荷神社 -> status=OK_CANONICAL_PREFERRED shrine_id=21
  detail=2 rows matched name_jp='長太稲荷神社'; resolved via
  place_ref_id IS NULL preference
```

**canonical row（id=22）のみが正しく選択され、duplicate row（id=101）へは
向いていない。** `name_jp`単独selectionは一切使用していない
（`resolve_shrine`のaddress narrowing→`place_ref_id IS NULL`優先の
2段階を経由）。

---

## 8. Fresh Backup（Phase 7）

| 項目 | 結果 |
|---|---|
| dump取得 | 成功（PostgreSQL 17クライアント明示指定） |
| `roles.sql` | `5426` bytes |
| `schema.sql` | `93021` bytes（Knowledge 5 table分を含む、Stage 4以降の値と一致） |
| `data.sql` | `3846558` bytes |
| 保存先 | repo外（新規timestampディレクトリ） |
| credential/hostname露出 | なし |

`STOP_BACKUP_FAILED`には該当しない。

---

## 9. Production-Equivalent Final Import Test（Phase 8）

Section 8のfresh dumpを、隔離したlocal PostgreSQL 18 + PostGISへ復元し
（Productionには一切書き込んでいない）、canonical seedを実際に適用した。

| 項目 | 結果 |
|---|---|
| 復元前state | `temples`最新=`0093`、Knowledge 5 table=空——想定通り |
| import（flagなし、隔離DBに対してのみ） | exit `0` |
| Source/Deity/History件数 | `59`/`103`/`85`——完全一致 |
| deity-source / history-source relation件数 | `116`/`90`——事前算出値と完全一致 |
| **duplicate shrine非汚染確認** | `給田六所神社` canonical（id=22）に2件のDeity、duplicate（id=101）に**0件**——canonical行のみが更新されたことを直接確認 |
| orphan fact（source relationを持たないDeity/History） | `0`件（Traceability Contract要件を満たす） |
| 既存aggregate | `auth_user=1`/`shrine=105`/`goriyaku_relation=283`/`visit=2`/`favorite=0`——**完全不変** |
| 2回目`--dry-run`（idempotency再確認） | 全件`SKIP_EXISTS`、`CREATE`0件 |

**このテストがPASSしたため、Production import禁止条件（Phase 8 FAIL時の
規定）には該当しない。** テスト後、この隔離DBは削除した。

---

## 10. Exact Production Command（Phase 9、固定・未実行）

```bash
cd backend
( set -a; source ~/.config/kami-musubi/production-db.env; set +a; \
  DEBUG=0 USE_GIS=1 SECRET_KEY="<any-value>" \
  .venv/bin/python3 manage.py import_shrine_knowledge \
    temples/data/knowledge_seeds/batch_1_7_seed.json )
```

- `import_shrine_knowledge`は対話的確認プロンプトを持たない
  （`--noinput`相当のflagは不要、コマンド自体が非対話式）
- `--dry-run`/`--validate-only`のいずれも付けない状態が実際の適用
- credential実値はこのドキュメントのどこにも記載しない
  （`~/.config/kami-musubi/production-db.env`を都度sourceする既存パターンを踏襲）

**このコマンドは本ドキュメント作成セッションでは実行していない。**

---

## 11. Atomicity / Failure Boundary（Phase 10）

`import_shrine_knowledge.py`の適用パスは単一の`transaction.atomic()`が
`_apply()`全体を包む（Source作成→Shrine identity解決→Deity/History
作成→M2M relation付与のすべて）。途中で1件でも`full_clean()`失敗等が
発生すれば、Django/PostgreSQLのtransaction機構により全体がrollbackされ、
部分的なSource/Deity/History/relationは残らない。これは
`test_import_blocks_entirely_on_ambiguous_shrine_no_partial_write`で
コード上も検証済みであり、Section 9の隔離DBテストでも（今回は全件成功
したため発火しなかったが）同じtransaction境界を通過している。

失敗時は**再実行・手動修復・手動INSERTを行わない**。まずread-onlyで
Production state（`django_migrations`相当の記録はimporterには存在しない
ため、Knowledge table件数そのもの）を確認する（Phase 14参照）。

---

## 12. Post-Import Verification Contract（Phase 11、固定）

### Counts

| 項目 | 期待値 |
|---|---|
| `ShrineKnowledgeSource` | 59 |
| `ShrineDeity` | 103 |
| `ShrineHistory` | 85 |
| deity-source relation | 116 |
| history-source relation | 90 |

### Identity

| 項目 | 期待値 |
|---|---|
| Knowledge Dataを持つshrine数 | 41 |
| ambiguous link | 0 |
| orphan fact（source relationなしのDeity/History） | 0 |

### Traceability

| 項目 | 期待値 |
|---|---|
| source-less Deity | 0 |
| source-less History | 0 |
| invalid source（enum外`source_type`等） | 0 |

### Evidence分布（seedから事前算出、一致確認用）

| 軸 | 分布 |
|---|---|
| Source `source_type` | `shrine_official`=46, `secondary_editorial`=5, `cultural_property`=4, `local_history`=1, `tourism_official`=1, `government`=1, `user_observation`=1 |
| Source `verification_status` | `source_confirmed`=59（全件） |
| Source `confidence` | `high`=53, `medium`=6 |
| Deity `verification_status` | `source_confirmed`=103（全件） |
| Deity `confidence` | `high`=99, `medium`=4 |
| Deity `role` | `enshrined`=53, `primary`=31, `unknown`=12, `secondary`=7 |
| History `verification_status` | `source_confirmed`=85（全件） |
| History `confidence` | `high`=71, `medium`=14 |
| History `history_type` | `historical_event`=40, `tradition`=31, `founding`=8, `official_origin`=6 |

### Existing data（regression確認）

Section 5のbaselineから、`auth_user`/`userprofile`/`shrine`/`favorite`/
`visit`/`shrine_goriyaku relation`が変化していないこと。加えて
`temples 0091`のcanonical効果（id=21/22の`history_theme`）・`temples
0092`の`thread_id`列が無変化であること。

---

## 13. Runtime QA Design（Phase 12）

全41社の手動QAはProduction import前の必須条件にしない。代表サンプルを
以下のとおり選定する（seedの構造的複雑度から機械的に算出、確認済み）:

| 神社 | 選定理由 |
|---|---|
| 武蔵御嶽神社 | 最多の複雑度（Deity4件・History5件・history_type2種・1 Factあたり最大2 Source） |
| 鶴岡八幡宮 | 著名な大規模神社、Deity3件・History5件・history_type2種 |
| 品川神社 | 既存Pilot対象5社の1つ（`docs/audit/shrine-knowledge-pilot-5-result.md`）、Deity/History3件ずつ |
| 熱田神宮 | 最多Deity数（6件、単一Source構成との対比） |
| 明治神宮 | `docs/knowledge/shrine-knowledge-contract.md`で言及される代表例、Deity2件・History1件、`給田六所神社`等のduplicate対象とは無関係のcanonical shrine |

上記5社について、import後に確認する項目:

- Shrine detail（Deity/History表示、`verification_status`に応じた
  `FactDisplayState`——`docs/knowledge/shrine-knowledge-contract.md`
  「Disputed Evidence Contract」参照）
- Recommendation経由の挙動（該当神社がcandidateに含まれる場合の
  reason生成、Evidence Gate `decide_fact_usability()`の適用結果）
- Knowledge-backed field（`deity`/`shrine_history`)がAPI responseへ
  正しく反映されているか
- 該当神社関連APIで500エラーが発生しないこと

**認証済みアクセスが必要でこのセッションからは実施不能**: 上記のうち
Detail API・Recommendation経由の確認は、DB専用credential bridgeの
範囲外であり、`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`のまま
（Stage 1〜Final Stageの各Execution Recordと同じ制約）。DB-level
verification（Section 9・Section 12）が本Gateの正式なverificationで
あり、すべてPASSしている。

---

## 14. STOP Conditions（Phase 13）

以下のいずれかに該当する場合、Production importを実行しない
（自動修復しない）:

- Production Knowledge tables non-empty
- seed drift（Section 2のdrift checkが1件でもfail）
- validation error
- ambiguous shrine identity
- not-found shrine
- dry-run count mismatch
- unexpected UPDATE
- fresh backup失敗
- production-equivalent test失敗
- package mismatch（Python/Django/psycopg）
- `USE_GIS`不一致
- credential露出
- import command non-zero exit
- post-import count mismatch
- orphan fact
- source-less fact
- 無関係aggregateの変化

**本Gateの検証範囲内では、上記いずれにも該当しなかった。**

---

## 15. Recovery Classification（Phase 14）

実行時に失敗した場合の分類（実行はまだ行っていないため、これは
将来の実行に備えた分類基準の固定）:

| 分類 | 意味 |
|---|---|
| `IMPORT_ROLLED_BACK_CLEANLY` | `transaction.atomic()`により正常にrollback、Knowledge table件数が実行前と一致 |
| `IMPORT_PARTIAL_STATE_SUSPECTED` | atomic境界の想定外の破れ（DB/接続層の異常等）により部分書き込みが疑われる状態 |
| `IMPORT_VERIFICATION_MISMATCH` | exit 0だが、Section 12のpost-import verification契約と実測が食い違う |
| `IMPORT_CONNECTION_STATE_UNKNOWN` | ネットワーク切断等でcommit/rollbackいずれが起きたか確認できない |

**手動restoreは最終手段。** `IMPORT_ROLLED_BACK_CLEANLY`であれば
再実行は単純（seedはidempotent）。それ以外はMother Ship判断なしに
restore・手動修復を行わない。

---

## 16. Final Classification（Phase 15）

**`KNOWLEDGE_PRODUCTION_IMPORT_GO_READY_WITH_LIMITATIONS`**

### GO_READYと判断する根拠

- Import Foundation（PR #2341）からのdrift 0件
- Seed integrity: 期待件数・relation数が事前算出値と完全一致
- Production dry-run: エラー0件、期待件数と完全一致
- Stable identity: 41神社全件解決、**既知のduplicate shrine
  （給田六所神社）についても直接read-only実行でcanonical行（id=22）へ
  正しく解決することを実証**
- Fresh backup取得成功
- **Production-equivalent最終テスト（隔離DBへのfresh dump復元＋実際の
  import適用）が完全PASS**——期待件数一致、duplicate行非汚染確認、
  orphan fact 0件、既存aggregate不変、idempotency再確認
- Exact command・post-import verification契約・STOP条件・recovery
  classificationをすべて固定済み

### `WITH_LIMITATIONS`とする理由

- 認証済みRuntime QA（Detail API・Recommendation経由の確認、
  Section 13で設計した代表5社分）は、DB専用credential bridgeの範囲外
  であり本Gateでは実施不能（`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`）
- 既存Fact更新（`--allow-update`相当）は引き続き未実装
  （`docs/audit/knowledge-production-import-foundation.md`
  Section 13で既述、変更なし）
- Batch 1〜7の実運用QAプロセス（1社投入ごとのAdmin/Evidence Gate/
  Detail API/Recommendation selector確認）と同水準の確認を、今回の
  一括importでは事前に（Production実行前に）行っていない
  ——事前確認はDBレベルの正しさに限定される

**Production Knowledge Data writeの実行可否はMother Ship判断待ち。**
Codexは本ドキュメント作成セッションでProduction importを実行していない。

---

## 17. Mandatory STOP

本Gate完了をもって以下は一切開始していない:

- Production Knowledge Data write
- manual INSERT / UPDATE / DELETE
- Batch 8
- Score/Ranking変更
- Source UI
- PER_FACT_RENDERING
- Production restore
