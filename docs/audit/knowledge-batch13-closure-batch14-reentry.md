> **Status: `BATCH13_CLOSED_BATCH14_REENTRY_READY`。**
>
> 本ドキュメントは、Human Confirmation後に単一atomic transactionで
> 1回のみ実行されたBatch 13 Production importの結果をfreshに再検証し、
> 既存フローへのregressionがないことを確認した上で、Batch 14 candidate
> universeを再構築した記録である。**本タスクではProduction writeを
> 一切行っていない。** Batch 14 Target Selection・seed作成・importも
> 本ドキュメントでは実施していない。

develop SHA（作業開始時点）: `4aadfa49d4354869c92bd4b4abf01d4e4f7c26a6`
（PR #2369反映済み、`origin/develop`と同期済み、working tree clean）。

Batch 13 Production Import Execution Record（Human Confirmation・実行
コマンド・post-import検証・idempotency確認）はrepoに文書として存在
しない（同一セッション内の会話記録にのみ残っている）ため、本ドキュメント
のPhase 1でProduction実測値をfreshに取得し、それを正本として記録する。

---

## Phase 0 — Base State

- [x] `develop`へcheckout
- [x] `origin/develop`と同期（既に最新）
- [x] HEAD SHA記録: `4aadfa49d4354869c92bd4b4abf01d4e4f7c26a6`
- [x] working tree clean確認
- [x] PR #2369 merge確認（`git log`で確認済み）

---

## Phase 1 — Production Current State（fresh実測）

`scripts/migration_safety/readonly_query.sh`のみ使用。

| 指標 | 実測値 | 期待値 | 判定 |
|---|---:|---:|---|
| Source | 91 | 91 | 一致 |
| Deity | 197 | 197 | 一致 |
| History | 133 | 133 | 一致 |
| Deity–Source relation | 210 | 210 | 一致 |
| History–Source relation | 138 | 138 | 一致 |
| Knowledge Shrine | 71 | 71 | 一致 |

drift 0件。Batch 13 Production importが計画どおり1回のみ適用された
状態と完全に一致する。

---

## Phase 2 — Batch 13 Five-shrine DB Verification（seed actualをfresh正本として実測）

| shrine | id | Deity | History | Unique Source | Fact–Source relation | verification_status | confidence |
|---|---:|---:|---:|---:|---:|---|---|
| 富岡八幡宮（canonical） | 49 | 1 | 2 | 1 | 3 | 全件source_confirmed | 全件high |
| 富岡八幡宮（非canonical重複） | 104 | 0 | 0 | 0 | 0 | — | — |
| 忌宮神社 | 95 | 3 | 2 | 1 | 5 | 全件source_confirmed | 全件high |
| 高良大社 | 96 | 3 | 2 | 1 | 5 | 全件source_confirmed | 全件high |
| 笠間稲荷神社 | 82 | 1 | 2 | 1 | 3 | 全件source_confirmed | 全件high |
| 鷲宮神社 | 75 | 2 | 2 | 1 | 4 | 全件source_confirmed | 全件high |

全5社（canonical行）、seedから算出した期待どおりのDeity/History件数と
完全一致。富岡八幡宮の非canonical重複行（id=104）はDeity/History共に
0件を維持。source-less（対象5社canonical行）: Deity 0・History 0。
within-shrine duplicate Fact: 0件。

---

## Phase 3 — Duplicate / Content-model Closure（Production actualで再確認）

| 確認項目 | 結果 |
|---|---|
| 富岡八幡宮canonical行（id=49）へのKnowledge | あり（Deity1・History2、期待どおり） |
| 富岡八幡宮non-canonical重複行（id=104）へのKnowledge | 0件 |
| 「外8柱」「他8柱」のplaceholder Fact | 0件 |
| unnamed deity Fact | 0件 |
| 鷲宮神社への大己貴命誤紐付け | 0件 |
| 摂社/末社 contamination（対象5社スコープ） | 0件 |
| collective spirit contamination | 0件 |
| source-less（対象5社canonical行） | Deity 0・History 0 |
| tradition Historyの非断定表現 | 全4件で維持を確認（「〜と伝えられている」「〜とされる」等） |

**分類: content-model closure PASS。** 新規contaminationなし。

---

## Phase 4 — Coverage Recalculation

過去監査と同一のmethodology（`temples_shrine`全105件を対象、QA fixture
等の除外を適用しない生の分類）でfresh算出した。

| 区分 | 実測値 | 期待値 |
|---|---:|---:|
| complete | 69 | 69 |
| partial | 2 | 2 |
| none | 34 | 34 |
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
| normalized-duplicate URL（`normalize_source_url()`実装をそのまま使用） | 0件（URL保有90件全件を突合） |
| ambiguous Source reuse | 0件 |
| verification_status | 全91件`source_confirmed` |

Batch 13の5件のSourceメタデータをfreshに確認: 全件`source_confirmed`/
`high`。Source reuse契約は健全。

---

## Phase 6 — Production HTTP Runtime QA

公開Shrine Detail API（`GET https://jinja-app-web.vercel.app/api/shrines/<pk>/data/`、
`ShrineViewSet.retrieve`・`AllowAny`・副作用なし）をBrowser paneから
GETのみで確認した。

| PK | shrine | HTTP | identity一致 | Deity | History | source-less | 判定 |
|---:|---|---:|---|---:|---:|---:|---|
| 49 | 富岡八幡宮（canonical） | 200 | 一致 | 1（期待1） | 2（期待2） | 0 | PASS |
| 104 | 富岡八幡宮（非canonical重複） | 200 | 一致（別住所表記） | 0（期待0） | 0（期待0） | — | PASS |
| 95 | 忌宮神社 | 200 | 一致 | 3（期待3） | 2（期待2） | 0 | PASS |
| 96 | 高良大社 | 200 | 一致 | 3（期待3） | 2（期待2） | 0 | PASS |
| 82 | 笠間稲荷神社 | 200 | 一致 | 1（期待1） | 2（期待2） | 0 | PASS |
| 75 | 鷲宮神社 | 200 | 一致 | 2（期待2） | 2（期待2） | 0 | PASS |

6件（対象5社canonical行＋富岡八幡宮の非canonical重複行）すべてHTTP
200・serializer exceptionなし・全件でDeity/History件数がDB期待値と
完全一致。Evidence Source payload（`sources`配列）もverification_status/
confidence込みで正しく返却されている。

GET前後でKnowledge aggregate（Source 91・Deity 197・History 133・
relation 210/138・Knowledge Shrine 71）が完全に不変であることを
read-onlyで確認した。writeを伴うendpointは一切呼び出していない。

---

## Phase 7 — Existing Flow Regression

| endpoint | 確認内容 | 結果 |
|---|---|---|
| `GET /api/shrines/`（Top/list） | `count=105`（Production DB総数と一致）、`goriyaku_tags`/`location`/`kyusei`フィールド健全 | PASS |
| `GET /api/shrines/<pk>/data/`（Detail） | Phase 6参照 | PASS |
| 既存goriyaku/location/kyusei fields | list/detail両方で正しい型・値で返却 | PASS |
| 既存Source payload | Batch 1–12由来のSourceも含め、Detail responseで正しく返却 | PASS |

Recommendation（Concierge chat）endpointはコード確認のみ（`apps/web/src/app/api/concierge/chat/route.ts`は`POST`のみ、DB書き込みを
伴うthread/message作成フロー、develop HEAD不変のためコード自体も
未変更）。write操作を伴うため本Auditでは実行していない。

分類: `RECOMMENDATION_RUNTIME_WRITE_REQUIRED`（記録のみ、blockingに
しない）。

---

## Phase 8 — Application Aggregate Regression

Batch 13 pre-state（Production import前のbaseline）とfresh実測を比較。

| 指標 | Batch13 pre-state | 現在（fresh） | 判定 |
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

## Phase 9 — Batch 14 Candidate Universe（fresh再構築）

Production現在状態（Phase 4の`none`集合34社）から、過去Batchの
candidate listを流用せず再構築した。期待値を先に固定せず、fresh actualを
正本として算出した。

| 区分 | 件数 |
|---|---:|
| raw `none`集合 | 34 |
| QA fixture除外 | 1（id=102「テスト確認神社 20260611」） |
| unresolved identity除外 | 1（id=105「広島市」、神社名ではなく地名） |
| duplicate除外（非canonical重複行） | 3（id=104 富岡八幡宮重複／id=101 給田六所神社重複／id=103 長太稲荷神社重複。いずれも対応するcanonical行が候補として別途残存、またはcanonical行が既にKnowledgeを保有） |
| **canonical candidate（Batch 14対象母集団）** | **29** |

富岡八幡宮の非canonical重複行（id=104）は、canonical行（id=49）が
Batch 13でKnowledgeを獲得した後もDeity/History共に0件のままraw
`none`集合に残存し、引き続きduplicate除外の対象であることを確認した
（構造上の想定どおり、新規driftではない）。

canonical candidate数29は、Batch 13実行前の34からBatch 13が選定した
5社（富岡八幡宮・忌宮神社・高良大社・笠間稲荷神社・鷲宮神社）を
差し引いた値と一致する。

**個別のSource availability調査（Batch 8–13のTarget Selection相当の
作業）は本ドキュメントでは実施していない**（Batch 14 Target Selection
自体が本タスクのスコープ外のため）。

---

## Phase 10 — Partial 2 Recheck（fresh再確認）

| shrine | id | Deity | History | Unique Source | missing layer |
|---|---:|---:|---:|---:|---|
| 阿佐ヶ谷神明宮 | 29 | 3 | 0 | 2 | History |
| 香取神宮 | 15 | 1 | 0 | 1 | History |

両社とも変化なし（既存Deity Sourceは健全）。分類:
`PARTIAL_REPAIR_CANDIDATE`。通常のBatch 14 candidate universe（Phase 9）
には含めない。repairは本ドキュメントでは実施しない。

---

## Phase 11 — Previously Flagged Model-risk Candidates（fresh再確認、過去判断を上書きしない）

29候補中、過去Batchで保留・除外判断がなされた候補が引き続き残存して
いることをfreshに確認した。

| shrine | 過去の判断 | 本セッションでの扱い |
|---|---|---|
| 靖國神社（id=58） | `docs/audit/knowledge-batch12-target-selection.md`・`knowledge-batch13-target-selection.md`でMajor content-model flag（近代・政治的機微）としてTop10/Recommended5から除外 | 新しい根拠は生じていないため、過去判断を維持 |
| 千葉神社（id=78） | 同上、shinbutsu-shugo疑い（妙見菩薩由来）としてTop10/Recommended5から除外 | 新しい根拠は生じていないため、過去判断を維持 |
| 愛宕神社（id=46） | `docs/audit/knowledge-batch11-seed-preflight.md`で明示的な仏教称号を理由に代替候補から除外、以降のBatchでも継続除外 | 新しい根拠は生じていないため、過去判断を維持 |

**いずれも本ドキュメントでは通常Batchへ復帰させていない。** 3候補とも
29 canonical candidatesには構造的に残存するが、除外状態を継続する。

---

## Phase 12 — Contract Reuse Audit

develop HEAD（`4aadfa49d4354869c92bd4b4abf01d4e4f7c26a6`）はBatch 13
Production import実行時点から不変（`git diff --stat`で確認済み、diff
なし）であり、以下すべてのcontractを Batch 13で実際に無変更のまま
最後まで通した（同一セッション内で`--validate-only`→`--dry-run`→
Production-equivalent→Production実行→idempotency確認のフルサイクルを
実施済み）。

| contract | 状態 |
|---|---|
| seed schema（`schema_version: "1.0"`） | 再利用可能 |
| identity resolver（`resolve_shrine`） | 再利用可能 |
| Source natural key（`source_type + normalized URL`） | 再利用可能 |
| Source reuse（`resolve_source_identity`） | 再利用可能 |
| Evidence Gate | 再利用可能 |
| `--validate-only` | 再利用可能 |
| `--dry-run` | 再利用可能 |
| atomic import | 再利用可能 |
| Production-equivalent test | 再利用可能 |
| Fresh Backup | 再利用可能 |
| idempotency | 再利用可能 |
| Human Execution Boundary | 再利用可能 |
| Runtime QA | 再利用可能 |

**分類: `BATCH13_CONTRACT_REUSED`。** Batch 14でコード変更なしに
そのまま再利用可能。

---

## Phase 13 — Local Test Environment Drift

`pytest-dotenv`のlocal-onlyのdriftをfreshに再確認した。

- requirementsに未宣言（`backend/requirements.txt`・`backend/requirements-dev.txt`いずれにも記載なし）
- CIでinstallされない（`.github/workflows/backend-tests.yml`は`pip install -r requirements.txt -r requirements-dev.txt`のみ実行）
- local-onlyのdrift、本ドキュメントではpackage変更を行っていない

**分類: `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`（継続）。**

---

## Phase 14 — Product Value Availability

Production read-onlyでfreshに確認した。

| 指標 | 結果 |
|---|---|
| `views_30d > 0`のShrine数 | 0 |
| `favorites_30d > 0`のShrine数 | 0 |
| `popular_score > 0`のShrine数 | 0 |
| favorite件数（実件数） | 0（`favorites_favorite`テーブル自体がDB全体で0件） |
| visit件数（実件数） | DB全体で2件のみ |
| recommendation exposure | 取得経路なし（write-requiredのため未確認、Phase 7参照） |

**分類: `PRODUCT_VALUE_NOT_AVAILABLE`。** 欠損値を推測で補完していない。

---

## Phase 15 — Batch Size Analysis

Batch 8–13実績（各5社）から:

- **Source research負荷**: 5社で管理可能。10社では確認漏れリスクが増す。
- **Evidence review負荷**: Batch 13は5社でDeity10・History10・
  Fact-Source relation20件（うち富岡八幡宮はDeity Evidence限定という
  個別判断を要した）。10社ではおよそ倍増し、個別判断ポイントの見落とし
  リスクが増す。
- **content-model review負荷**: 靖國神社・千葉神社・愛宕神社等、継続的に
  判断が必要な候補が存在し、10社では見落としリスクが増す。
- **Runtime QA負荷**: Batch 13では富岡八幡宮のcanonical/非canonical
  重複行を含め6件のGET検証を実施した。5社基準でもこの水準の丁寧さが
  必要であり、10社では網羅性が下がるリスクがある。
- **Production blast radius**: 5社なら1回のwriteで最大数十行程度の
  影響に留まるが、10社では単純に倍。
- **failure isolation**: 単一`transaction.atomic()`のため、件数が
  増えるほど1つのエラーで無駄になる既検証作業が増える。

**技術的推奨: Batch 14も5社を維持する。** 10社への拡大はMother Shipの
明示判断が必要であり、本ドキュメントでは決定しない。

---

## Phase 16 — Final Classification

Phase 1–15のすべてでdrift 0・regression 0・新規blocking issueなし。

**`BATCH13_CLOSED_BATCH14_REENTRY_READY`**

Production DB writes（本Audit中） = 0
Batch 14 Data writes = 0
Batch 14 Target Selectionは未着手（本ドキュメントのスコープ外）

---

## 最終報告サマリ

1. develop SHA: `4aadfa49d4354869c92bd4b4abf01d4e4f7c26a6`
2. Batch 13 actual result: Source+5/Deity+10/History+10/rel+10/+10、単一
   atomic transaction、1回のみ実行、idempotency確認済み
3. Production current counts: Source91・Deity197・History133・
   rel210/138・Knowledge Shrine71（drift 0）
4. Coverage: complete69・partial2・none34（drift 0）
5. source-less: DB全体で0件
6. duplicate contamination: 0件（富岡八幡宮の非canonical重複行含め確認）
7. Batch 13 five-shrine DB verification: 全件PASS
8. content-model closure: PASS（「外8柱」placeholder・大己貴命誤紐付け・
   摂社末社・collective spirit混入いずれも0件）
9. Runtime QA: 6/6 HTTP 200（対象5社canonical行＋富岡八幡宮重複行）、
   payload完全一致、aggregate不変
10. existing flow regression: PASS（Top/list・Detail・既存フィールド）、
    Recommendationは`RECOMMENDATION_RUNTIME_WRITE_REQUIRED`として記録のみ
11. Source health: orphan0・source-less0・duplicate URL0・ambiguous reuse0
12. application aggregate regression: 完全不変
13. Batch 14 raw none: 34
14. Batch 14 canonical candidates: 29
15. partial status: 2社、`PARTIAL_REPAIR_CANDIDATE`、対象外のまま
16. excluded/unresolved: QA fixture1・unresolved identity1・duplicate3
    （計5件、過去監査と完全一致）
17. flagged model-risk candidates: 靖國神社・千葉神社・愛宕神社、新規根拠
    なしのため除外継続
18. reused contracts: `BATCH13_CONTRACT_REUSED`（13契約すべて無変更で
    再利用可能）
19. local pytest drift classification: `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`
20. product value: `PRODUCT_VALUE_NOT_AVAILABLE`
21. 5 vs 10 technical recommendation: 5社を維持（Phase 15参照）、10社は
    Mother Ship判断が必要
22. remaining limitations: partial2社repair未実施・
    `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`未着手・靖國神社等
    content-model判断保留・pytest environment drift継続
23. final classification: `BATCH13_CLOSED_BATCH14_REENTRY_READY`

Production DB writes = 0
Batch 14 Data writes = 0
