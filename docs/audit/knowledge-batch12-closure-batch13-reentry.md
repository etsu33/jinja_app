> **Status: `BATCH12_CLOSED_BATCH13_REENTRY_READY`。**
>
> 本ドキュメントは、Human Confirmation後に1回のみ実行されたBatch 12
> Production importの結果をfreshに再検証し、既存フローへのregressionが
> ないことを確認した上で、Batch 13 candidate universeを再構築した記録
> である。**本タスクではProduction writeを一切行っていない。** Batch 13
> seed作成・importも本ドキュメントでは実施していない。

develop SHA（作業開始時点）: `1453c2c12f67b52a9008d6f52b955d08d5efe844`
（PR #2366反映済み、`origin/develop`と同期済み、working tree clean）。

Batch 12 Production Import Execution Record（Human Confirmation・実行
コマンド・post-import検証・idempotency確認）はrepoに文書として存在
しない（同一セッション内の会話記録にのみ残っている）ため、本ドキュメント
のPhase 1でProduction実測値をfreshに取得し、それを正本として記録する。

---

## Phase 0 — Base State

- [x] `develop`へcheckout
- [x] `origin/develop`と同期（既に最新）
- [x] HEAD SHA記録: `1453c2c12f67b52a9008d6f52b955d08d5efe844`
- [x] working tree clean確認
- [x] PR #2366 merge確認（`git log`で確認済み）

---

## Phase 1 — Production Current State（fresh実測）

`scripts/migration_safety/readonly_query.sh`のみ使用。

| 指標 | 実測値 | 期待値 | 判定 |
|---|---:|---:|---|
| Source | 86 | 86 | 一致 |
| Deity | 187 | 187 | 一致 |
| History | 123 | 123 | 一致 |
| Deity–Source relation | 200 | 200 | 一致 |
| History–Source relation | 128 | 128 | 一致 |
| Knowledge Shrine | 66 | 66 | 一致 |

drift 0件。Batch 12 Production importが計画どおり1回のみ適用された
状態と完全に一致する。

---

## Phase 2 — Batch 12 Five-shrine DB Verification（fresh実測）

| shrine | id | Deity | History | Unique Source | Fact–Source relation | verification_status | confidence |
|---|---:|---:|---:|---:|---:|---|---|
| 二荒山神社 | 54 | 3 | 1 | 1 | 4 | 全件source_confirmed | 全件high |
| 住吉神社（博多） | 57 | 5 | 2 | 1 | 7 | 全件source_confirmed | 全件high |
| 枚岡神社 | 98 | 4 | 3 | 1 | 7 | 全件source_confirmed | 全件high |
| 安房神社 | 77 | 7 | 2 | 1 | 9 | 全件source_confirmed | 全件high |
| 越中一宮 高瀬神社 | 32 | 3 | 2 | 1 | 5 | 全件source_confirmed | 全件high |

全5社、期待どおりのDeity/History件数と完全一致。全件`place_ref_id IS
NULL`（canonical）・同名重複行1件（重複混入なし）。source-less: Deity 0・
History 0。within-shrine duplicate Fact: 0件。

---

## Phase 3 — Content-model Closure Check（Production actualで再確認）

| 確認項目 | 結果 |
|---|---|
| 「二荒山大神」の重複Fact化 | 0件 |
| 「住吉五所大神」の重複Fact化 | 0件 |
| 「忌部五部神」のcollective Fact化 | 0件 |
| 「元春日」のDeity混入 | 0件（History Factのみに存在、1件） |
| 摂社/末社Fact混入（対象5社スコープ） | 0件（DB全体では同名の別神社由来Factが3件存在するが、いずれも伏見稲荷大社・金刀比羅宮・厳島神社の正当な祭神であり、Batch12対象5社とは無関係） |
| 功霊殿由来Fact混入 | 0件 |
| traditionの史実断定 | なし（全件`note`/`period_text`に伝承である旨を明記） |

**分類: content-model closure PASS。** 新規contaminationなし。

---

## Phase 4 — Coverage Recalculation

過去監査と同一のmethodology（`temples_shrine`全105件を対象、QA fixture
等の除外を適用しない生の分類）でfresh算出した。

| 区分 | 実測値 | 期待値 |
|---|---:|---:|
| complete | 64 | 64 |
| partial | 2 | 2 |
| none | 39 | 39 |
| 総Shrine数 | 105 | 105（不変） |

過去監査と完全一致。drift 0件。

---

## Phase 5 — Source Health（Production全体）

| 確認項目 | 結果 |
|---|---:|
| orphan Source（Deity/Historyいずれからも参照されない） | 0件 |
| source-less Deity（DB全体） | 0件 |
| source-less History（DB全体） | 0件 |
| exact-duplicate URL（同一source_type + 完全一致URL） | 0件 |
| normalized-duplicate URL（`normalize_source_url()`実装をそのまま使用） | 0件（URL保有85件全件を突合） |
| ambiguous Source reuse | 0件 |
| verification_status | 全86件`source_confirmed` |

Source reuse契約は健全。

---

## Phase 6 — Production HTTP Runtime QA

公開Shrine Detail API（`GET https://jinja-app-web.vercel.app/api/shrines/<pk>/data/`、
`ShrineViewSet.retrieve`・`AllowAny`・副作用なし）をBrowser paneから
GETのみで確認した。

| PK | shrine | HTTP | identity一致 | Deity | History | source-less | 判定 |
|---:|---|---:|---|---:|---:|---:|---|
| 54 | 二荒山神社 | 200 | 一致 | 3（期待3） | 1（期待1） | 0 | PASS |
| 57 | 住吉神社（博多） | 200 | 一致 | 5（期待5） | 2（期待2） | 0 | PASS |
| 98 | 枚岡神社 | 200 | 一致 | 4（期待4） | 3（期待3） | 0 | PASS |
| 77 | 安房神社 | 200 | 一致 | 7（期待7） | 2（期待2） | 0 | PASS |
| 32 | 越中一宮 高瀬神社 | 200 | 一致 | 3（期待3） | 2（期待2） | 0 | PASS |

5社すべてHTTP 200・serializer exceptionなし・全件でDeity/History件数
がDB期待値と完全一致。Evidence Source payload（`sources`配列）も
verification_status/confidence込みで正しく返却されている。

GET前後でKnowledge aggregate（Source 86・Deity 187・History 123・
relation 200/128・Knowledge Shrine 66）が完全に不変であることを
read-onlyで確認した。writeを伴うendpointは一切呼び出していない。

---

## Phase 7 — Existing Flow Regression

| endpoint | 確認内容 | 結果 |
|---|---|---|
| `GET /api/shrines/`（Top/list） | `count=105`（Production DB総数と一致）、`goriyaku_tags`/`location`/`kyusei`フィールド健全 | PASS |
| `GET /api/shrines/<pk>/data/`（Detail） | Phase 6参照 | PASS |
| 既存goriyaku/location/kyusei fields | list/detail両方で正しい型・値で返却 | PASS |
| 既存Source payload | Batch 1–11由来のSourceも含め、Detail responseで正しく返却 | PASS |

Recommendation（Concierge chat）endpointはコード確認のみ（`apps/web/src/app/api/concierge/chat/route.ts`は`POST`のみ、DB書き込みを
伴うthread/message作成フロー）。write操作を伴うため本Auditでは実行して
いない。

分類: `RECOMMENDATION_RUNTIME_WRITE_REQUIRED`（記録のみ、blockingに
しない）。

---

## Phase 8 — Application Aggregate Regression

Batch 12 pre-state（Production import前のbaseline）とfresh実測を比較。

| 指標 | Batch12 pre-state | 現在（fresh） | 判定 |
|---|---:|---:|---|
| auth_user | 1 | 1 | 不変 |
| userprofile | 1 | 1 | 不変 |
| shrine | 105 | 105 | 不変 |
| favorite | 0 | 0 | 不変 |
| visit | 2 | 2 | 不変 |
| goriyakutag | 39 | 39 | 不変 |
| shrine_goriyaku_relation | 283 | 283 | 不変 |

Knowledge importと無関係なaggregateへの影響は0件。

---

## Phase 9 — Batch 13 Candidate Universe（fresh再構築）

Production現在状態（Phase 4の`none`集合39社）から、過去Batchの
candidate listを流用せず再構築した。

| 区分 | 件数 |
|---|---:|
| raw `none`集合 | 39 |
| QA fixture除外 | 1（id=102「テスト確認神社 20260611」） |
| unresolved identity除外 | 1（id=105「広島市」、神社名ではなく地名） |
| duplicate除外（非canonical重複行） | 3（id=104 富岡八幡宮重複／id=101 給田六所神社重複／id=103 長太稲荷神社重複。いずれも対応するcanonical行が候補として別途残存） |
| **canonical candidate（Batch 13対象母集団）** | **34** |

除外5件は`docs/audit/knowledge-batch11-closure-batch12-reentry.md`・
`docs/audit/knowledge-batch12-target-selection.md`に記載された5件と
完全に同一（drift 0）。canonical candidate数は、Batch 12実行前の39から
Batch 12が選定した5社（二荒山神社・住吉神社・枚岡神社・安房神社・
高瀬神社）を差し引いた34と一致する。

**個別のSource availability調査（Batch 8–12のTarget Selection相当の
作業）は本ドキュメントでは実施していない**（Batch 13 Target Selection
自体が本タスクのスコープ外のため）。

---

## Phase 10 — Partial 2 Recheck（fresh再確認）

| shrine | id | Deity | History | Unique Source | missing layer |
|---|---:|---:|---:|---:|---|
| 阿佐ヶ谷神明宮 | 29 | 3 | 0 | 2 | History |
| 香取神宮 | 15 | 1 | 0 | 1 | History |

両社とも変化なし（既存Deity Sourceは健全）。分類:
`PARTIAL_REPAIR_CANDIDATE`。通常のBatch 13 candidate universe（Phase 9）
には含めない。repairは本ドキュメントでは実施しない。

---

## Phase 11 — Contract Reuse Audit

develop HEAD（`1453c2c12f67b52a9008d6f52b955d08d5efe844`）はBatch 12
Production import実行時点から不変であり、以下すべてのcontractを
Batch 12で実際に無変更のまま最後まで通した（同一セッション内で
`--validate-only`→`--dry-run`→Production-equivalent→Production
実行→idempotency確認のフルサイクルを実施済み）。

| contract | 状態 |
|---|---|
| seed schema（`schema_version: "1.0"`） | 無変更・再利用可能 |
| identity resolver（`resolve_shrine`） | 無変更・再利用可能 |
| Source natural key（`source_type + normalized URL`） | 無変更・再利用可能 |
| Source reuse（`resolve_source_identity`） | 無変更・再利用可能 |
| Evidence Gate | 無変更・再利用可能 |
| `--validate-only` | 無変更・再利用可能 |
| `--dry-run` | 無変更・再利用可能 |
| atomic import（単一`transaction.atomic()`） | 無変更・再利用可能 |
| Production-equivalent（`scripts/migration_safety/`一式） | 無変更・再利用可能 |
| idempotency（`SKIP_EXISTS`/`REUSE_EXISTING`） | 無変更・再利用可能 |
| Fresh Backup contract | 無変更・再利用可能 |
| Human Execution Boundary（`AskUserQuestion`） | 無変更・再利用可能 |
| Runtime QA（`GET /api/shrines/<pk>/data/`） | 無変更・再利用可能 |

**分類: `BATCH12_CONTRACT_REUSED`。** Batch 13でコード変更なしに
そのまま再利用可能。

---

## Phase 12 — Local Test Environment Drift

`docs/audit/knowledge-batch11-closure-batch12-reentry.md` Phase 11で
記録済みの`pytest-dotenv`ローカルdriftを継承する。本ドキュメントでも
package変更を一切行っていない。

- `pytest-dotenv`はrequirements未宣言・CI未installのlocal-onlyのdrift
- Batch 13のblocking conditionにはしない
- clean CI-declared plugin構成を正本とする

**分類: `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`（継続）。**

---

## Phase 13 — Batch Size

Batch 8–12実績（各5社）から:

- **Source research負荷**: 5社で管理可能な作業量。10社では確認漏れ
  リスクが増す。
- **Evidence review負荷**: Batch 12は5社でDeity22・History10・
  Fact-Source relation32件。10社ではおよそ倍になり、Mother Shipの
  レビュー負荷も比例して増える。特に枚岡神社・安房神社のように
  由緒・祭神情報が豊富な社が含まれる場合、判断コストがさらに増える。
- **Production blast radius**: 5社なら1回のwriteで最大数十行程度の
  影響に留まるが、10社では単純に倍。
- **Runtime QA負荷**: 5社であれば1社ずつ丁寧にHTTP Runtime QAを実施
  できるが、10社では確認の網羅性が下がるリスクがある。
- **failure isolation**: 単一`transaction.atomic()`のため、件数が
  増えるほど、1つのエラーで無駄になる既検証作業が増える。

**技術的推奨: Batch 13もBatch 8–12同様、5社を基準とする。** 10社への
拡大は、上記のとおりreview負荷・blast radius・Runtime QA網羅性の
トレードオフが明確にあるため、Mother Shipの明示判断なしに本ドキュメント
では決定しない。

---

## Phase 14 — Final Classification

Phase 1–13のすべてでdrift 0・regression 0・新規blocking issueなし。

**`BATCH12_CLOSED_BATCH13_REENTRY_READY`**

Production DB writes（本Audit中） = 0
Batch 13 Data writes = 0
Batch 13 Target Selectionは未着手（本ドキュメントのスコープ外）

---

## 最終報告サマリ

1. develop SHA: `1453c2c12f67b52a9008d6f52b955d08d5efe844`
2. Batch 12 actual result: Source+5/Deity+22/History+10/rel+22/+10、単一
   atomic transaction、1回のみ実行、idempotency確認済み
3. Production current counts: Source86・Deity187・History123・
   rel200/128・Knowledge Shrine66（drift 0）
4. Coverage: complete64・partial2・none39（drift 0）
5. source-less: DB全体で0件
6. duplicate contamination: 0件
7. Batch 12 five-shrine DB verification: 全件PASS
8. content-model closure: PASS（collective name/摂社末社/功霊殿混入0件）
9. Runtime QA: 5/5 HTTP 200、payload完全一致、aggregate不変
10. existing flow regression: PASS（Top/list・Detail・既存フィールド）、
    Recommendationは`RECOMMENDATION_RUNTIME_WRITE_REQUIRED`として記録のみ
11. Source health: orphan0・source-less0・duplicate URL0・ambiguous reuse0
12. application aggregate regression: 完全不変
13. Batch 13 raw none: 39
14. Batch 13 canonical candidates: 34
15. partial status: 2社、`PARTIAL_REPAIR_CANDIDATE`、対象外のまま
16. excluded/unresolved: QA fixture1・unresolved identity1・duplicate3
    （計5件、過去監査と完全一致）
17. reused contracts: `BATCH12_CONTRACT_REUSED`（13契約すべて無変更で
    再利用可能）
18. local pytest drift classification: `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`
19. 5 vs 10 technical recommendation: 5社を維持（Phase 13参照）、10社は
    Mother Ship判断が必要
20. remaining limitations: partial 2社repair未実施・
    `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`未着手・pytest environment
    drift継続
21. audit document: 本ドキュメント
    （`docs/audit/knowledge-batch12-closure-batch13-reentry.md`）
22. PR: 別途作成（本ドキュメントのcommit時に作成）
23. CI: PR作成後に確認
24. final classification: `BATCH12_CLOSED_BATCH13_REENTRY_READY`

Production DB writes = 0
Batch 13 Data writes = 0
