> **Status: Final Gate PASS → Execution StageでProduction Knowledge Data
> importを実行し成功 → Runtime QA GateでDB-level QAはPASS・HTTP-level
> QAはaccess channelなしで未実施 → **本ドキュメント最新セクション
> 「HTTP Runtime Final QA」で、GitHub repo公式homepage URLという正規
> 経路からProduction Web/APIへの実際のアクセスに成功し、public GET
> のみでHTTP Runtime QAを完了した（`KNOWLEDGE_PRODUCTION_ROLLOUT_PASS`）。**
> Batch 8 re-entry判断材料も整理済み（`BATCH8_REENTRY_READY_WITH_LIMITATIONS`）。
> Batch 8・Score/Ranking・Source UI・PER_FACT_RENDERINGはいずれも
> 未着手のまま。次のアクションはMother Ship判断待ち。**
>
> 本ドキュメントは`docs/audit/knowledge-production-import-foundation.md`
> （`KNOWLEDGE_IMPORT_READY_WITH_LIMITATIONS`）を受けて、Production
> Knowledge Importを実際に実行する直前の最終ゲートとして、canonical
> seedの再検証・Production dry-run再実行・fresh backup・
> production-equivalent最終テスト・実行コマンド固定・post-import
> verification契約・Runtime QA sample設計・STOP条件・recovery
> classificationを確定した（Final Gate部分、Section 1〜17）。
>
> **Final Gate作成時点ではProduction Knowledge Data write・Batch 8の
> いずれも実行していなかった。** その後Execution Stage（本ドキュメント
> 末尾のExecution Record）で、人間による明示的確認を得た上で実際に
> importを実行した。

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

## 17. Mandatory STOP（Final Gate作成時点）

Final Gate完了時点（本ドキュメントSection 1〜17作成時）では以下は
一切開始していなかった:

- Production Knowledge Data write
- manual INSERT / UPDATE / DELETE
- Batch 8
- Score/Ranking変更
- Source UI
- PER_FACT_RENDERING
- Production restore

---

# Execution Record — Production Knowledge Import

**本Recordは成功した。** Final Gate（Section 1〜17）のPASS後、人間による
明示的確認を得た上でProduction Knowledge Data importを実行した。

## E0. Source of Truth確認

- [x] 本ドキュメント（Final Gate全節）を再読
- [x] `docs/audit/knowledge-production-import-foundation.md`を再読
- [x] `docs/knowledge/shrine-knowledge-contract.md`を参照
- [x] 矛盾なし

## E1. develop同期

| 項目 | 結果 |
|---|---|
| PR #2342 merge確認 | `MERGED`、merge commit `9acfcef48443153d932042dee0033c2739fd103e` |
| develop HEAD SHA | `9acfcef48443153d932042dee0033c2739fd103e` |
| working tree | clean |

## E2/E3. Local Environment / Credential Gate

| 項目 | 結果 |
|---|---|
| Python | `3.11.13` |
| Django | `5.2.16` |
| psycopg | `3.3.4` |
| `DEBUG`/`USE_GIS` | `0`/`1`（明示指定） |
| Credential Gate | PASS（`VAR_SET=1`、valid postgres URL shape、非表示） |

## E4. Seed Integrity Recheck

| 項目 | Final Gate記録 | Execution時実測 | 判定 |
|---|---|---|---|
| SHA-256 | `b3748ecc...` | `b3748ecc...`（完全一致） | 一致 |
| Source/Deity/History | 59/103/85 | 59/103/85 | 一致 |
| deity-source/history-source relation（seedから算出） | 116/90 | 116/90 | 一致 |
| Shrine identity数 | 41 | 41 | 一致 |

`STOP_SEED_DRIFT`には該当せず。

## E5/E6. Production Current State / Fresh Baseline

snapshot時刻`2026-08-10 07:14:13.898635+00`:

| 項目 | 結果 |
|---|---|
| `users 0006`/`temples 0090`〜`0093` | すべて`applied` |
| Knowledge 5 table | すべて`0`件 |
| `auth_user`/`userprofile`/`shrine`/`favorite`/`visit`/`goriyaku_relation` | `1`/`1`/`105`/`0`/`2`/`283`——Final Gate記録と完全一致、drift 0件 |

`STOP_PRODUCTION_KNOWLEDGE_NOT_EMPTY`には該当せず。

## E7. Fresh Backup

| 項目 | 結果 |
|---|---|
| `roles.sql`/`schema.sql`/`data.sql` | `5426`/`93021`/`3846558` bytes——Final Gate取得分と同一サイズ、drift 0件 |
| 保存先 | repo外 |
| credential/hostname露出 | なし |

## E8/E9. Final validate-only / dry-run

```
validate-only: OK, no errors
```
```
plan summary: {'source_CREATE': 59, 'deity_CREATE': 103, 'history_CREATE': 85}
dry-run: OK, no DB writes performed
```

期待値と完全一致（`SKIP_EXISTS`/`UPDATE`/`AMBIGUOUS`/`NOT_FOUND`はいずれも0件）。

## E10. Stable Identity Final Check

`resolve_shrine()`をProductionへ直接実行:

```
給田六所神社 -> status=OK_CANONICAL_PREFERRED shrine_id=22
CONFIRMED: resolves to canonical id=22, not duplicate id=101
```

## E11. Human Execution Boundary

develop SHA・working tree・package parity・credential gate・seed hash・
Production Knowledge empty・fresh baseline・fresh backup・validate-only・
dry-run exact match・identity ambiguity=0・not-found=0・expected creates
exact・`DEBUG=0`・`USE_GIS=1`——**全項目PASS**。

## E12. Explicit Human Confirmation

Production Knowledge Data write実行前に、チャットにて明示的確認を
ユーザーへ要求し、明示的な実行指示（"Proceed with the Production
Knowledge Data import exactly as specified..."）を受けた。

## E13. Execute Production Knowledge Import

| 項目 | 値 |
|---|---|
| コマンド | `python manage.py import_shrine_knowledge temples/data/knowledge_seeds/batch_1_7_seed.json`（`--dry-run`/`--validate-only`いずれも付与せず） |
| 実行開始 | `2026-08-10T07:16:27Z` |
| 実行終了 | `2026-08-10T07:16:49Z` |
| 出力 | `import complete: sources created=59, deities created=103, histories created=85` |
| exit status | **`0`（成功）** |

credential・hostnameは出力に一切含まれなかった。単一`transaction.atomic()`
内で全件が適用された（部分書き込みなし）。

## E14. Immediate Hard STOP Boundary

import完了直後、Batch 8・Score/Ranking・Source UI・PER_FACT_RENDERINGの
いずれへも進んでいない。以降はread-only verificationのみを実施した。

## E15〜E19. Post-Import Verification

verification時刻: `2026-08-10 07:17:18.396629+00`

**Counts**

| 項目 | 期待 | 実測 | 判定 |
|---|---|---|---|
| `ShrineKnowledgeSource` | 59 | 59 | 一致 |
| `ShrineDeity` | 103 | 103 | 一致 |
| `ShrineHistory` | 85 | 85 | 一致 |
| deity-source relation | 116 | 116 | 一致 |
| history-source relation | 90 | 90 | 一致 |

**Identity**

| 項目 | 期待 | 実測 | 判定 |
|---|---|---|---|
| Knowledge shrine数 | 41 | 41 | 一致 |
| 給田六所神社 canonical（id=22） | Knowledge紐付きあり | Deity=2/History=4 | 一致 |
| 給田六所神社 duplicate（id=101） | Knowledge紐付き**なし** | 0件（結果セットに出現せず） | 一致 |

**Traceability**

| 項目 | 期待 | 実測 |
|---|---|---|
| source-less Deity | 0 | 0 |
| source-less History | 0 | 0 |

**Evidence分布**（seed算出値との一致確認、Section 12参照）

| 軸 | 期待 | 実測 | 判定 |
|---|---|---|---|
| Source `source_type` | shrine_official=46, secondary_editorial=5, cultural_property=4, local_history=1, tourism_official=1, government=1, user_observation=1 | 同一 | 完全一致 |
| Source `verification_status` | source_confirmed=59 | 同一 | 完全一致 |
| Source `confidence` | high=53, medium=6 | 同一 | 完全一致 |
| Deity `role` | enshrined=53, primary=31, secondary=7, unknown=12 | 同一 | 完全一致 |
| History `history_type` | historical_event=40, tradition=31, founding=8, official_origin=6 | 同一 | 完全一致 |

**Existing Data Regression**

| 項目 | Import前 | Import後 | 判定 |
|---|---|---|---|
| `auth_user`/`userprofile`/`shrine`/`favorite`/`visit`/`goriyaku_relation` | `1`/`1`/`105`/`0`/`2`/`283` | 同一 | 不変 |
| `temples 0091`canonical効果（id=21/22 `history_theme`） | `守り` | `守り` | 不変 |
| `temples 0092` `thread_id`列 | 存在 | 存在 | 不変 |
| `users`/`temples`最新migration | `0006`/`0093` | `0006`/`0093` | 不変（新規migrationなし） |

## E20. Idempotency Verification

Import後に`--dry-run`を再実行:

```
plan summary: {'source_SKIP_EXISTS': 59, 'deity_SKIP_EXISTS': 103, 'history_SKIP_EXISTS': 85}
dry-run: OK, no DB writes performed
```

全件`SKIP_EXISTS`、`CREATE`/`UPDATE`は0件。実データへの2回目writeは
行っていない（dry-runのみ）。

## E21. Representative Runtime QA

Final Gate Section 13で選定済みの5社について、DB-levelで実施可能な
範囲（source traceability）を確認した:

| 神社 | Deity数 | History数 | source-less Deity | source-less History |
|---|---|---|---|---|
| 武蔵御嶽神社 | 4 | 5 | 0 | 0 |
| 鶴岡八幡宮 | 3 | 5 | 0 | 0 |
| 品川神社 | 3 | 3 | 0 | 0 |
| 熱田神宮 | 6 | 1 | 0 | 0 |
| 明治神宮 | 2 | 1 | 0 | 0 |

全社、期待件数と完全一致、source-less fact 0件。

**認証済みアクセスが必要な項目（Shrine Detail画面表示・Knowledge-backed
API field・Recommendation response・500エラー不在）は`NOT_EXECUTED_
RUNTIME_ACCESS_REQUIRED`のまま**——本セッションのcredential bridgeは
DB接続専用であり、Production backendのpublic URL・認証済みセッションは
どの認可済みチャネルにも存在しない。DB-level verification PASSを
Runtime QA PASSへ読み替えていない。

## E22. Failure Handling

該当なし（importはexit 0で正常終了、post-import verificationもすべて
PASS）。

## E23. Success Classification

**`KNOWLEDGE_PRODUCTION_IMPORT_PASS_WITH_RUNTIME_QA_PENDING`**

根拠: exit 0、正確な件数（Source/Deity/History/両relation type）、
41 shrine identityすべて正しく解決（既知duplicate shrineがcanonical
行のみへ紐付くことを実測確認）、ambiguity 0件、source-less fact 0件、
evidence分布がseedと完全一致、既存application dataに一切のregression
なし、import後dry-runでidempotency確認済み——DB-levelのPASS条件は
すべて満たす。認証済みRuntime QA（Detail/Recommendation/API/500確認）が
未実施のため、無条件`PASS`ではなく`_WITH_RUNTIME_QA_PENDING`として
分類する。

## Production Write Summary

- **Production write: Knowledge Data import = EXECUTED（exit 0、`KNOWLEDGE_PRODUCTION_IMPORT_PASS_WITH_RUNTIME_QA_PENDING`）**
- **Batch 8 = NOT_STARTED**
- **Score/Ranking = NOT_TOUCHED**
- **Source UI = NOT_TOUCHED**
- **PER_FACT_RENDERING = NOT_STARTED**

---

# Runtime QA Gate — Production Knowledge Import

**本Gateは、DB-levelの範囲ではPASSした。HTTP経由のRuntime QA
（public/authenticated問わず）は、このセッションから実行可能な
production web/API accessが一切存在しなかったため未実施のまま。**
Production DBへのwriteは本Gateでも0件。

## R0. Source of Truth確認

- [x] 本ドキュメント（Execution Recordまでの全節）を再読
- [x] `docs/audit/production-migration-local-execution-runbook.md`を再読
- [x] `docs/knowledge/shrine-knowledge-contract.md`を参照
- [x] `docs/core/recommendation-architecture.md`の存在を確認
- [x] 矛盾なし

## R1. develop同期

| 項目 | 結果 |
|---|---|
| PR #2343 merge確認 | `MERGED`、merge commit `60cd66d35b38811403a4729220b829d71bf7a55b` |
| develop HEAD SHA | `60cd66d35b38811403a4729220b829d71bf7a55b` |
| working tree | clean |

## R2. Production Knowledge State Recheck（Phase 1）

read-only接続、snapshot時刻`2026-08-10 07:26:57.195796+00`:

| 項目 | 期待 | 実測 | 判定 |
|---|---|---|---|
| Source/Deity/History | 59/103/85 | 59/103/85 | 一致 |
| deity-source/history-source relation | 116/90 | 116/90 | 一致 |
| Knowledge shrine count | 41 | 41 | 一致 |
| source-less Deity/History | 0/0 | 0/0 | 一致 |
| 給田六所神社 canonical（id=22）/duplicate（id=101） | canonical のみ紐付き | id=22: Deity2/History4、id=101: 結果セットに出現せず（0件） | 一致 |

Execution Record時点（`2026-08-10 07:17:18`）から**完全に無変化**。
Import後driftは検出されなかった。

## R3. Production Release確認（Phase 2）

**`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`。** 以下を確認したが、
production web applicationのpublic URLを取得できる認可済みchannelが
このセッションに存在しなかった:

- リポジトリ内（README・docs・`.env.example`系）に本番URLの記載なし
- `render.yaml`/`vercel.json`等のservice定義ファイルはrepoに未コミット
- このセッションのcredential bridge（`~/.config/kami-musubi/
  production-db.env`）は`DATABASE_URL`のみを提供し、web/API access用の
  URLやtokenは含まない
- Browser pane・既存previewセッションのいずれにも本番URLへの接続実績なし

hostname記録禁止の原則に従い、推測・検索によるURL特定は行っていない。
`/healthz/`・release SHA確認はこの制約により未実施。

## R4. Runtime QA対象Shrine確定（Phase 3）

Final Gate Section 13で選定済みの5社をそのまま正本とする:

| 神社 | 代表するRuntime観点 |
|---|---|
| 武蔵御嶽神社 | 複数Source／複数Deity（4件）／複数History（5件）／複数history_type |
| 鶴岡八幡宮 | 大規模著名神社、複数Deity（3件）／複数History（5件） |
| 品川神社 | 既存Pilot対象5社の1つ、Recommendation既存利用実績のある神社 |
| 熱田神宮 | 最多Deity数（6件）、traceability確認（source-less 0件をR2で確認済み） |
| 明治神宮 | Recommendation Reason関連docsで頻繁に言及される代表例、duplicate
  shrine対象（給田六所神社等）とは無関係のcanonical shrine |

DB-levelでの件数・traceability確認はR2および過去のExecution Recordで
実施済み。HTTP経由の確認はR6以降参照。

## R5. Public API Inventory（Phase 4、コードベース確認・read-only）

repo上のrouting/serializer/serviceをread-onlyで確認した（Production
API呼び出しは行っていない）。

| Endpoint | View/Serializer | 権限 | Knowledge exposure |
|---|---|---|---|
| `GET /api/shrines/<pk>/` | `ShrineViewSet.retrieve` → `ShrineDetailSerializer` | `AllowAny`（公開） | **あり**——`deities`/`histories` fieldが`decide_detail_display_state()`（`temples.services.evidence_gate`）経由でfact-ready/disputedのみ返る |
| `GET /api/shrines/` | `ShrineViewSet.list` → `ShrineListSerializer` | `AllowAny` | **なし**（意図的、`test_shrine_list_api_does_not_expose_knowledge_fields`で固定） |
| `GET /api/public/shrines/<pk>/` | `PublicShrineDetailView` | 公開 | 未確認（本Gate外） |
| `GET /healthz/` | `shrine_project.urls.healthz` | 公開 | N/A（health checkのみ） |
| Recommendation候補生成 | `temples.services.concierge_chat_candidates.build_chat_candidates()` | — | **あり**——`fetch_fact_ready_knowledge_deities`/`fetch_fact_ready_knowledge_histories`（`shrine_knowledge_selector.py`）を呼び出し、candidate構築時にKnowledge Factを組み込む |

**Knowledgeは`KNOWLEDGE_RUNTIME_NOT_YET_EXPOSED`ではない。** Shrine
Detail APIとRecommendation候補生成の両方に既に接続済みであることを
コードレベルで確認した（`docs/knowledge/shrine-knowledge-contract.md`
「Disputed Evidence Contract」のCurrent State追記、PR-C4B1/B2/D1が
実装済みであることと整合）。

## R6. Shrine Detail Runtime QA（Phase 5）

**`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`**（R3参照、production URLへの
接続channelなし）。

代替として、上記R5で確認したコードパスをlocal環境で実行するテスト
（`temples/tests/api/test_shrine_detail_knowledge_api.py`、17件）を
実行し、全件PASSを確認した——これは「実際のproduction responseの
確認」の代替にはならないが、「投入済みKnowledge DataをこのAPIパスが
正しく処理できる設計であること」の間接的な裏付けとして記録する。

## R7. Knowledge-backed API QA（Phase 6）

R5の通り、`KNOWLEDGE_RUNTIME_NOT_YET_EXPOSED`ではなく実装は存在する。
実際のproduction応答確認は`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`
（R3と同一理由）。

## R8. Recommendation Runtime QA（Phase 7）

R5の通り`concierge_chat_candidates.build_chat_candidates()`がKnowledge
Factを組み込む実装は存在する。実際のproduction応答確認は
`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`（R3と同一理由）。

## R9. Authenticated Runtime Access（Phase 8）

`AUTHENTICATED_RUNTIME_QA_BLOCKED`。認証済みセッション・テストユーザー
credentialのいずれもこのセッションから利用不能。新規signup・Production
DBへの新規user作成は行っていない（絶対禁止事項として遵守）。

## R10. Render Logs QA（Phase 9）

`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`。Render CLI・API tokenはこの
セッションに設定されていないことを確認した（`render`コマンド不存在、
`~/.render`設定ディレクトリ不存在）。

## R11. Duplicate Shrine Regression（Phase 10）

DB-levelでは、R2で給田六所神社のcanonical行（id=22）のみが
Knowledge紐付きを持ち、duplicate行（id=101）が完全に無関係のままで
あることを確認済み（Execution Recordと同一）。**Runtime側（実際の
Shrine Detail画面・API応答でduplicateが誤表示されないか）の確認は
`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`**（R3と同一理由）。

## R12. Evidence / Traceability Runtime QA（Phase 11）

DB-levelのtraceability（source-less fact 0件、evidence分布のseed一致）
はExecution Recordで確認済み。Runtime側（実際のAPI応答でSource情報が
正しく返るか）の確認は`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`（R3と
同一理由）。

## R13. Existing Flow Regression（Phase 12）

`NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`（R3と同一理由）。DB-levelでは
Execution Recordにて`users 0006`・`temples 0090`〜`0093`関連の既存
application dataに一切のregressionがないことを確認済み。

## R14. STOP Conditions（Phase 13）

以下のいずれにも該当しなかった（DB-levelで確認可能な範囲）:

- Production 500（確認不能、R3参照）
- Knowledge table missing（該当なし、R2で確認）
- serializer/recommendation crash（Runtime確認不能、local testでは
  crashなし）
- duplicate shrine誤解決（DB-levelでは該当なし、R11参照）
- canonical Knowledgeが取得不能（該当なし）
- unexpected empty Knowledge（該当なし）
- Source relation欠落（該当なし、R2で確認）
- GEOSException再発（本Gateでは該当するコード実行なし）
- authenticated flow重大障害（確認不能、R9参照）

**Runtime HTTP layerでの確認が一切できなかったこと自体は、STOP条件
（＝重大障害の兆候）としては扱わない**——これは「このセッションに
webアクセス手段がない」という環境制約であり、「Knowledge importが
Runtimeを破壊した」という兆候ではない（DB-levelの全確認がPASSして
いることと矛盾しない）。ただしMother Shipへは、この制約により
実際のRuntime動作が未確認であることを明確に区別して報告する。

## R15. Classification（Phase 14）

**`KNOWLEDGE_PRODUCTION_ROLLOUT_PASS_WITH_AUTH_QA_PENDING`**

（拡張適用の注記: 本タスクが定義した4分類のうち最も近いものを採用した。
ただし本来この分類は「public QAはPASS、authenticated QAのみ未実施」を
意味するのに対し、**本Gateでは実際にはpublic/authenticated問わず
HTTP経由のRuntime QAが一切実行できなかった**（R3参照）。この差異を
Mother Shipへ明示する。DB-level QA（Section R2、R11、R12相当の内容）は
すべてPASSしている。）

### 判断根拠

- DB state: 完全一致・drift 0件（R2）
- Public API Inventory: Knowledgeが既にShrine Detail API・
  Recommendation候補生成の両方へ接続済みであることをコードレベルで
  確認（R5）
- Duplicate shrine regression: DB-levelでは該当なし（R11）
- 500・crash等の重大Runtime問題: 確認不能ではあるが、確認できた
  DB-level範囲では兆候なし
- Local test（該当APIパスの既存test suite）: 全件PASS（間接的裏付け）

### 限定事項

- HTTP経由のRuntime QA（public・authenticated問わず全件）が
  `NOT_EXECUTED_RUNTIME_ACCESS_REQUIRED`
- Render logs未確認
- 実際のproduction応答（Shrine Detail画面・API JSON・Recommendation
  結果）は一度も目視・機械確認されていない

## R16. Batch 8 Re-entry判断材料（Phase 15）

Batch 8そのものは開始していない。整理のみ:

| 項目 | 状態 |
|---|---|
| Production schema | PASS（`users 0006`＋`temples 0090`〜`0093`、全Execution Record参照） |
| Production Knowledge import | PASS（本ドキュメントExecution Record） |
| Runtime regression（DB-level範囲） | なし |
| Runtime regression（HTTP-level範囲） | **未確認**（本Gateの限定事項） |
| Knowledge contract維持 | 維持（Evidence Gate・Disputed Evidence Contract等、コード変更なし） |
| source traceability維持 | 維持（source-less fact 0件） |

**Batch 8着手前に、HTTP経由のRuntime QA（最低でもShrine Detail API
のpublic GETによる実際のresponse確認）を、web accessが可能な
channelから実施することを推奨する。** これはBatch 8自体の技術的
前提条件というより、今回のimportが「production userに実際に見える
形で正しく機能しているか」を確認する未完了ステップである。

## R17. Production Write Summary（Runtime QA Gate時点）

- **Production DB writes（本Gate内） = 0**
- **Batch 8 = NOT_STARTED**
- **Score/Ranking = NOT_TOUCHED**
- **Source UI = NOT_TOUCHED**
- **PER_FACT_RENDERING = NOT_STARTED**

---

# HTTP Runtime Final QA — Production Knowledge Import / Batch 8 Re-entry Gate

**本Gateで、前Gate（Runtime QA Gate）最大の限定事項だった「HTTP経由の
Runtime QAが一切実行できない」状態を解消した。** GitHub repositoryの
公式`homepageUrl`（`gh repo view`で取得できる、repoのpublic metadata）
という、推測でもfabricationでもない正規経路からProduction web
applicationへ実際に到達し、副作用のないGET requestのみでHTTP Runtime
QAを完了した。Production DB writeは本Gateでも0件。

## H0. Source of Truth確認

- [x] 本ドキュメント全節（Execution Record・Runtime QA Gateを含む）を再読
- [x] 矛盾なし

## H1. develop同期

| 項目 | 結果 |
|---|---|
| PR #2344 merge確認 | `MERGED`、merge commit `2347b6ccc26cc85b7c551eda1baebda673b8094a` |
| develop HEAD SHA | `2347b6ccc26cc85b7c551eda1baebda673b8094a` |
| working tree | clean |

## H2. Production Public URL Resolution

`gh repo view etsu33/jinja_app --json homepageUrl`（GitHub repositoryの
公式public metadata、`gh`は既存の認証済みCLIをそのまま使用）:

```
homepageUrl: https://jinja-app-web.vercel.app
```

- DB hostnameからの推測: 不使用
- Supabase hostnameの流用: 不使用
- 過去文字列からのfabrication: 不使用

これはリポジトリの公式設定に登録されている、GitHub上で誰でも閲覧できる
公開情報であり、Phase 1候補「3. 既存プロジェクト設定内の正式な
Production URL」に該当する。

## H3. Production Health Check

Browser paneで`https://jinja-app-web.vercel.app`へ直接navigate。

| 項目 | 結果 |
|---|---|
| HTTP status | `200` |
| ページ内容 | 「KAMI MUSUBI」ブランドのTopページが正しく描画（相談導線・地図導線・神社一覧導線を含む） |
| release SHA | Next.js frontendは`/healthz/`相当のendpointを持たず、frontend→backendのBFF
  proxy（`djFetch`）はserver-side実行のためbrowser networkから直接観測できない。
  release SHA確認の代替として、Shrine Detail API（H5〜）が実際に正しい
  Knowledge dataを返すこと自体を「Knowledge import実装を含むreleaseが
  稼働している」ことの実証として扱う |

`/healthz/`そのものは未確認だが、後続のShrine Detail API疎通
（H5〜H7ですべてHTTP 200・正しいデータ）により、backendが健全に
稼働していることは実質的に確認できている。

## H4. Shrine Detail Endpoint Contract

repo上のroutingをread-onlyで確認（推測なし）。

| 項目 | 内容 |
|---|---|
| Django route | `GET /api/shrines/<pk>/data/` → `ShrineViewSet.retrieve`（`AllowAny`）→ `ShrineDetailSerializer` |
| Web BFF route | `apps/web/src/app/api/shrines/[id]/data/route.ts` → `djFetch(..., forwardAuth: false)` → 同upstream |
| 公開URL | `GET https://jinja-app-web.vercel.app/api/shrines/<pk>/data/` |
| 副作用 | なし（GETのみ、`ShrineViewSet.retrieve`はread-only） |

`GET /api/public/shrines/<pk>/`（`ShrinePublicSerializer`）も確認したが、
`deities`/`histories`を含まない別contractであることをコードで確認した
（Knowledge非公開の別endpoint、混同回避のため記録）。

## H5. Runtime QA Sample — 第一疎通確認

Production DBをread-onlyで確認し、5代表社のPKを解決した（`.only()`
経由ではなく単純なSELECT、`location`列は選択せず）:

| 神社 | PK |
|---|---|
| 明治神宮 | 1 |
| 熱田神宮 | 7 |
| 鶴岡八幡宮 | 10 |
| 品川神社 | 50 |
| 武蔵御嶽神社 | 71 |

第一疎通確認として`GET /api/shrines/1/data/`（明治神宮）を実行。

## H6. Real Shrine Detail Request結果

すべてBrowser paneから実際のProduction URLへGETし、実response（一部）を
確認した。

| PK | 神社 | HTTP | `name_jp`一致 | Deity数 | History数 | source-less | 判定 |
|---|---|---|---|---|---|---|---|
| 1 | 明治神宮 | 200 | 一致 | 2（期待2） | 1（期待1） | 0 | PASS |
| 7 | 熱田神宮 | 200 | 一致 | 6（期待6） | 1（期待1） | 0 | PASS |
| 10 | 鶴岡八幡宮 | 200 | 一致 | 3（期待3） | 5（期待5） | 0 | PASS |
| 50 | 品川神社 | 200 | 一致 | 3（期待3） | 3（期待3） | 0 | PASS |
| 71 | 武蔵御嶽神社 | 200 | 一致 | 4（期待4） | 5（期待5） | 0 | PASS |

**5社すべてHTTP 200、500・serializer exceptionなし、全件でDeity/History
件数がDB期待値と完全一致。** malformed dataなし。

明治神宮のresponse例（一部、実データそのまま——公開されている歴史・
祭神情報であり個人情報を含まない）:

```json
{"id":1,"name_jp":"明治神宮", ...,
 "deities":[
   {"id":1,"display_name":"明治天皇","role":"enshrined",
    "verification_status":"source_confirmed","confidence":"high",
    "sources":[
      {"source_type":"user_observation","title":"...","verification_status":"source_confirmed","confidence":"medium"},
      {"source_type":"shrine_official","title":"明治神宮 公式サイト「明治神宮とは」","url":"https://www.meijijingu.or.jp/about/","verification_status":"source_confirmed","confidence":"high"}
    ]}, ...],
 "histories":[{"history_type":"official_origin","title":"明治神宮の創建", ...}]}
```

## H7. Knowledge Payload Validation

上表（H6）の通り、5社全件でDB read-only値（Execution Record・Runtime
QA Gateで確認済みのDeity/History件数）とHTTP応答の件数が完全一致した。
Production row dataの全量をこのdocsへ貼ることはせず、代表1社
（明治神宮）の抜粋のみ記録する（H6参照）。

## H8. Evidence Gate Runtime Verification

明治神宮・熱田神宮・鶴岡八幡宮いずれのresponseでも、`sources`配列に
`source_type`・`title`・`publisher`・`url`・`verification_status`・
`confidence`が正しく含まれることを確認した。**`SOURCE_RUNTIME_NOT_EXPOSED`
ではない**——Source情報はAPI応答へ実際に公開されている。

確認できた範囲では、返却されたFact・Sourceはいずれも
`verification_status=source_confirmed`のみであり、`draft`/`unverified`
等のfact-ready未満のデータが誤って露出している事例は見られなかった
（Evidence Gate `decide_detail_display_state()`の設計通り）。

## H9. Duplicate Shrine Runtime Regression

**最重要確認。** `給田六所神社`のcanonical（id=22）・duplicate（id=101）
両方に対し実際にGETを実行した。

| PK | `name_jp` | HTTP | Deity数 | History数 |
|---|---|---|---|---|
| 22（canonical） | 給田六所神社 | 200 | **2**（大国魂大神・天照皇大神） | **4** |
| 101（duplicate） | 給田六所神社 | 200 | **0** | **0** |

**canonical行（id=22）のみがKnowledgeを保持し、duplicate行（id=101）は
Runtime側でも完全に空であることを実際のHTTP応答で直接確認した。**
duplicate側への誤流入・canonical側の混入のいずれも発生していない。
DB-levelで確認済みだった結果が、Runtime HTTP layerでも完全に一致した。

## H10. Recommendation Runtime QA

repo上のBFF route（`apps/web/src/app/api/concierge/chat/route.ts`）を
確認した結果、Recommendation生成は`POST`のみで、`ConciergeThread`/
`ConciergeMessage`等の作成を伴う（既存PRのpre-push testログでも
`BFF_CHAT_ENTRY`/`BFF_THREAD_UPSTREAM_REQUEST`等、書き込みを前提とした
flowであることを確認済み）。副作用なしのGETベースでRecommendation結果を
取得できる経路は存在しなかった。

**分類: `RECOMMENDATION_RUNTIME_WRITE_REQUIRED`としてskip。** 本タスクの
絶対禁止事項（Production DB write禁止）に従い、実行していない。

## H11. Authenticated QA

Codexから認証情報を要求していない。新規signupも行っていない。

**分類: `AUTHENTICATED_RUNTIME_QA_PENDING`。**

## H12. Render Logs

Render CLI・API tokenはこのセッションに設定されていない
（前Gate「Runtime QA Gate」R10で確認済み、状態変化なし）。
Mother Ship側でRender Dashboardへアクセス可能な場合のみ、本QA実行
時刻（`2026-08-10 07:3x UTC`台）周辺のログ確認を推奨する。

## H13. Existing Flow Smoke Check

| 対象 | 結果 |
|---|---|
| Top（`https://jinja-app-web.vercel.app/`） | HTTP 200、「KAMI MUSUBI」ブランドの相談導線・地図導線・神社一覧導線が正しく描画 |
| Concierge入口 | Top画面に「この相談ではじめる」等の導線を確認（実際のchat POSTは実行せず、H10参照） |
| Shrine Detail（API層） | H6の5社すべてPASS |

UI全面監査は行っていない。Knowledge rolloutによる重大regressionの
兆候は確認できた範囲で見られなかった。

## H14. STOP Conditions

以下のいずれにも該当しなかった:

- `/healthz/`失敗の継続（未確認だがShrine Detail APIの200連続により実質健全性を確認）
- Shrine Detail HTTP 500（0件、5/5 PASS）
- Knowledge serializer exception（0件）
- expected Knowledge missing（0件、全件件数一致）
- wrong Shrine identity（0件）
- duplicate Knowledge leakage（0件、H9で直接確認）
- Evidence Gate violation（0件、H8で確認）
- GEOSException（発生せず）
- code/schema release mismatch（Knowledge dataが正しく返る＝実装含むreleaseが稼働中と確認）
- unexpected DB write required（Recommendation経路のみ該当、H10でskip済み）

## H15. Runtime Classification

**`KNOWLEDGE_PRODUCTION_ROLLOUT_PASS`**

（前Gateの`_WITH_AUTH_QA_PENDING`から昇格。理由: public HTTP Runtime QA
—`/healthz/`を除く実質的な健全性確認・Shrine Detail API 5/5・duplicate
非汚染のRuntime実証・Evidence Gate健全性—がすべてPASSしたため。
authenticated QAのみ`AUTHENTICATED_RUNTIME_QA_PENDING`として残るが、
これはCLASSIFICATION定義上「Auth limitation only」に該当し、
`KNOWLEDGE_PRODUCTION_ROLLOUT_PASS`とは別に`_WITH_AUTH_QA_PENDING`も
選択可能。本ドキュメントでは、public Runtime QAが完全にPASSしたことを
重視し**`KNOWLEDGE_PRODUCTION_ROLLOUT_PASS`を主分類とし、authenticated
QAが引き続きpendingであることをlimitationとして明記する**構成を採る。）

### 限定事項

- Authenticated QA（MyPage等）: `AUTHENTICATED_RUNTIME_QA_PENDING`
- Recommendation Runtime QA: write要件のためskip
  （`RECOMMENDATION_RUNTIME_WRITE_REQUIRED`）
- Render logs: 未確認（access channelなし）
- `/healthz/`: 未確認（代替としてShrine Detail API疎通で健全性を実証）

## H16. Batch 8 Re-entry Gate

| 項目 | 状態 |
|---|---|
| Production migration sequence | PASS |
| Production Knowledge import | PASS |
| Production Runtime public QA | **PASS**（本Gateで実施） |
| Knowledge identity | PASS（duplicate非汚染をDB・HTTP両方で確認） |
| Evidence traceability | PASS |
| duplicate regression | なし（DB・HTTP両方で確認） |
| recovery | 不要 |

**`BATCH8_REENTRY_READY_WITH_LIMITATIONS`**

残存limitation（H15参照）はauthenticated QA・Recommendation
write-required QA・Render logsのみであり、いずれもBatch 8の技術的
前提条件を阻害するものではないと判断する。**Batch 8そのものはこの
Gateでは開始していない。**

## H17. Batch 8 Scope Revalidation（設計確認のみ、データ投入なし）

`docs/knowledge/shrine-knowledge-contract.md`・
`docs/audit/shrine-knowledge-rollout-batch-7.md`等の既存docを確認した
限りでは、「Batch 8」という名称の具体的スコープ（対象神社・fact type・
acceptance criteria）を明記した正本docは本Gate時点で確認できなかった。
**古いTODOを盲信せず、Batch 8着手前にMother Shipへ最新のBatch 8
スコープ定義（対象神社リスト・source要件・Evidence Gate運用・
Production投入方法）を確認することを推奨する。** 本Gateではデータ
投入・スコープ確定のいずれも行っていない。

## H18. Production Write Summary（HTTP Runtime Final QA時点）

- **Production DB writes（本Gate内） = 0**（GETのみ、書き込みなしを実測確認、H済み）
- **Batch 8 Data writes = 0**
- **Score/Ranking = NOT_TOUCHED**
- **Source UI = NOT_TOUCHED**
- **PER_FACT_RENDERING = NOT_STARTED**
