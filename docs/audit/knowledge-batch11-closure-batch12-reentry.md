> **Status: `BATCH11_CLOSED_BATCH12_REENTRY_READY_WITH_LIMITATIONS`。**
>
> 本ドキュメントは、Human Confirmation後に1回のみ実行されたBatch 11
> Production importの結果をfreshに再検証し、既存フローへのregressionが
> ないことを確認した上で、Batch 12 candidate universeを再構築した記録
> である。**本タスクではProduction writeを一切行っていない。** Batch 12
> Target Selection自体もこのドキュメントでは開始しない。

develop SHA（作業開始時点）: `9edd154d17aa8c2a57f58e7ebbd9e04579abdeee`
（PR #2363反映済み、`origin/develop`と同期済み、working tree clean）。

Batch 11 Production Import Execution Record（Human Confirmation・実行
コマンド・post-import検証・idempotency確認）はrepoに文書として存在
しない（同一セッション内の会話記録にのみ残っている）ため、本ドキュメント
のPhase 1でProduction実測値をfreshに取得し、それを正本として記録する。

---

## Phase 0 — Base State

- [x] `develop`へcheckout
- [x] `origin/develop`と同期（fast-forward不要、既に最新）
- [x] working tree clean確認
- [x] HEAD SHA記録: `9edd154d17aa8c2a57f58e7ebbd9e04579abdeee`
- [x] PR #2363 merge確認（`git log`で確認済み）

---

## Phase 1 — Production Current State（fresh実測）

`scripts/migration_safety/readonly_query.sh`のみ使用。

| 指標 | 実測値 | 期待値 | 判定 |
|---|---:|---:|---|
| Source | 81 | 81 | 一致 |
| Deity | 165 | 165 | 一致 |
| History | 113 | 113 | 一致 |
| Deity–Source relation | 178 | 178 | 一致 |
| History–Source relation | 118 | 118 | 一致 |
| Knowledge Shrine | 61 | 61 | 一致 |

drift 0件。Batch 11 Production importが計画どおり1回のみ適用された
状態と完全に一致する。

---

## Phase 2 — Batch 11 Five-shrine Verification（fresh実測）

| shrine | id | Deity | History | Unique Source | Fact–Source relation | verification_status | confidence |
|---|---:|---:|---:|---:|---:|---|---|
| 小網神社 | 62 | 2 | 1 | 1 | 3 | 全件source_confirmed | 全件high |
| 根津神社 | 48 | 5 | 2 | 1 | 7 | 全件source_confirmed | 全件high |
| 赤坂氷川神社 | 60 | 3 | 2 | 1 | 5 | 全件source_confirmed | 全件high |
| 大宮八幡宮 | 51 | 3 | 1 | 1 | 4 | 全件source_confirmed | 全件high |
| 寳登山神社 | 97 | 3 | 1 | 1 | 4 | 全件source_confirmed | 全件high |

全5社、期待どおりのDeity/History件数と完全一致。全件`place_ref_id IS
NULL`（canonical）・同名重複行1件（重複混入なし）。source-less（対象
5社）: Deity 0・History 0。within-shrine duplicate Fact: 0件。

**福禄寿confirmation**: `display_name='福禄寿'`のShrineDeityはDB全体
（165件）で0件。小網神社のDeityは倉稲魂神・市杵島比賣神の2柱のみ。

---

## Phase 3 — Coverage Recalculation

過去監査（Batch 8–11）と同一のmethodology（`temples_shrine`全105件を
対象、QA fixture等の除外を適用しない生の分類。「complete」=Deity>0か
つHistory>0、「partial」=いずれか一方のみ>0、「none」=両方0）で
fresh算出した。

| 区分 | 実測値 | 期待値 |
|---|---:|---:|
| complete | 59 | 59 |
| partial | 2 | 2 |
| none | 44 | 44 |
| 総Shrine数 | 105 | 105（不変） |

過去監査と完全一致。drift 0件。

---

## Phase 4 — Source Health（Production全体）

| 確認項目 | 結果 |
|---|---:|
| orphan Source（Deity/Historyいずれからも参照されない） | 0件 |
| source-less Deity（DB全体） | 0件 |
| source-less History（DB全体） | 0件 |
| exact-duplicate URL（同一source_type + 完全一致URL） | 0件 |
| normalized-duplicate URL（`normalize_source_url()`実装をそのまま使用） | 0件（URL保有80件全件を突合） |
| ambiguous Source reuse | 0件 |

Batch 11の5件のSourceメタデータをfreshに確認: 全件`source_confirmed`/
`high`。小網神社Source（id=77）の`note`には、公式ページには福禄寿の
記載があるがFact化対象外とした旨が明記されており、orphan化していない
（倉稲魂神・市杵島比賣神・史実Factから引き続き参照）。

Source reuse契約は健全。

---

## Phase 5 — Production HTTP Runtime QA

公開Shrine Detail API（`GET https://jinja-app-web.vercel.app/api/shrines/<pk>/data/`、
`ShrineViewSet.retrieve`・`AllowAny`・副作用なし）をBrowser paneから
GETのみで確認した。

| PK | shrine | HTTP | identity一致 | Deity | History | source-less | 判定 |
|---:|---|---:|---|---:|---:|---:|---|
| 62 | 小網神社 | 200 | 一致 | 2（期待2） | 1（期待1） | 0 | PASS |
| 48 | 根津神社 | 200 | 一致 | 5（期待5） | 2（期待2） | 0 | PASS |
| 60 | 赤坂氷川神社 | 200 | 一致 | 3（期待3） | 2（期待2） | 0 | PASS |
| 51 | 大宮八幡宮 | 200 | 一致 | 3（期待3） | 1（期待1） | 0 | PASS |
| 97 | 寳登山神社 | 200 | 一致 | 3（期待3） | 1（期待1） | 0 | PASS |

5社すべてHTTP 200・serializer exceptionなし・全件でDeity/History件数
がDB期待値と完全一致。Evidence Source payload（`sources`配列）も
verification_status/confidence込みで正しく返却されている。

GET前後でKnowledge aggregate（Source 81・Deity 165・History 113・
relation 178/118・Knowledge Shrine 61）が完全に不変であることを
read-onlyで確認した。writeを伴うendpointは一切呼び出していない。

---

## Phase 6 — Existing Flow Regression

| endpoint | 確認内容 | 結果 |
|---|---|---|
| `GET /api/shrines/`（Top/list） | `count=105`（Production DB総数と一致）、`goriyaku_tags`/`location`/`kyusei`フィールド健全 | PASS |
| `GET /api/shrines/<pk>/data/`（Detail） | Phase 5参照 | PASS |
| 既存goriyaku/location/kyusei fields | list/detail両方で正しい型・値で返却 | PASS |
| 既存Source payload | Batch 1–10由来のSourceも含め、Detail responseで正しく返却（例: 小網神社レスポンスの`sources`） | PASS |

Recommendation（Concierge chat）endpointはコード確認のみ実施（`apps/web/src/app/api/concierge/chat/route.ts`は`POST`のみ、
DB書き込みを伴うthread/message作成フロー）。write操作を伴うため本
Auditでは実行していない。

分類: `RECOMMENDATION_RUNTIME_WRITE_REQUIRED`（記録のみ、blockingに
しない）。

---

## Phase 7 — Application Aggregate Regression

Batch 11 pre-state（Production import前のbaseline）とfresh実測を比較。

| 指標 | Batch11 pre-state | 現在（fresh） | 判定 |
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

## Phase 8 — Batch 12 Candidate Universe（fresh再構築）

Production現在状態（Phase 3の`none`集合44社）から、過去Batchの
candidate listを流用せず再構築した。

| 区分 | 件数 |
|---|---:|
| raw `none`集合 | 44 |
| QA fixture除外 | 1（id=102「テスト確認神社 20260611」） |
| unresolved identity除外 | 1（id=105「広島市」、神社名ではなく地名） |
| duplicate除外（非canonical重複行） | 3（id=104 富岡八幡宮重複／id=101 給田六所神社重複／id=103 長太稲荷神社重複。いずれも対応するcanonical行が候補として別途残存） |
| **canonical candidate（Batch 12対象母集団）** | **39** |

除外5件は`docs/audit/knowledge-batch10-closure-batch11-reentry.md`
Phase「Batch 11 Candidate Universe」に記載された5件と完全に同一（drift
0）。なお、給田六所神社のcanonical行（id=22）はDeity2/History4を
既に保持しており（`none`集合に含まれない）、これは新規のdriftではない
（既存Knowledge保有のため元々候補外）。

**個別のSource availability調査（Batch 8–11のTarget Selection相当の
作業）は本ドキュメントでは実施していない**（Batch 12 Target Selection
自体が本タスクのスコープ外のため）。

---

## Phase 9 — Partial Shrines（fresh再確認）

| shrine | id | Deity | History | Unique Source | missing layer |
|---|---:|---:|---:|---:|---|
| 阿佐ヶ谷神明宮 | 29 | 3 | 0 | 2 | History |
| 香取神宮 | 15 | 1 | 0 | 1 | History |

両社とも変化なし（既存Deity Sourceは健全）。分類:
`PARTIAL_REPAIR_CANDIDATE`。通常のBatch 12 candidate universe（Phase 8）
には含めない。repairは本ドキュメントでは実施しない。

---

## Phase 10 — Contract Reuse Audit

develop HEAD（`9edd154d17aa8c2a57f58e7ebbd9e04579abdeee`）はBatch 11
Production import実行時点から不変であり、以下すべてのcontractを
Batch 11で実際に無変更のまま最後まで通した（同一セッション内で
`--validate-only`→`--dry-run`→Production-equivalent→Production
実行→idempotency確認のフルサイクルを実施済み）。

| contract | 実装 | 状態 |
|---|---|---|
| seed schema | `schema_version: "1.0"` | 無変更・再利用可能 |
| identity resolution | `temples/services/knowledge_seed.py::resolve_shrine` | 無変更・再利用可能 |
| Source natural key | `source_type + normalized URL` | 無変更・再利用可能 |
| Source reuse | `resolve_source_identity` | 無変更・再利用可能 |
| Evidence Gate | `verification_status`/`confidence`/`verified_at`整合性 | 無変更・再利用可能 |
| `--validate-only` | `import_shrine_knowledge.py` | 無変更・再利用可能 |
| `--dry-run` | 同上 | 無変更・再利用可能 |
| atomic import | 単一`transaction.atomic()` | 無変更・再利用可能 |
| Production-equivalent | `scripts/migration_safety/`一式 | 無変更・再利用可能 |
| idempotency | `SKIP_EXISTS`/`REUSE_EXISTING` | 無変更・再利用可能 |
| Human Execution Boundary | `AskUserQuestion`による明示承認 | 無変更・再利用可能 |
| Runtime QA | `GET /api/shrines/<pk>/data/` | 無変更・再利用可能 |

**分類: `BATCH11_CONTRACT_REUSED`。** Batch 12でコード変更なしに
そのまま再利用可能。

---

## Phase 11 — Local Test Environment Drift

Batch 11 Production Import Execution Gateセッションで判明した、
ローカル環境のみのdriftをfreshに再調査した。

| 確認項目 | 結果 |
|---|---|
| 1. `pytest-dotenv`はrequirementsに宣言されているか | されていない（`backend/requirements.txt`・`backend/requirements-dev.txt`いずれにも記載なし） |
| 2. CIでinstallされるか | されない（`.github/workflows/backend-tests.yml`は`pip install -r requirements.txt -r requirements-dev.txt`のみ実行） |
| 3. local venvだけに存在するか | 存在する（`backend/.venv`に`pytest-dotenv==0.5.2`がinstall済み、由来不明・おそらく過去の手動install） |
| 4. `--envfile` collisionが再現するか | 再現する。`pytest-dotenv`（entry point名`dotenv`）と`pytest-env==1.6.0`（entry point名`env`、v1.6.0で新規追加された`--envfile`オプション）が同一CLIオプション名を登録し、pytestのplugin entry point読み込み時点（`addopts`適用前）で`ValueError: option names {'--envfile'} already added`が発生し、pytest自体が起動不能になる |
| 5. clean CI-declared plugin構成ではtests PASSするか | PASSする。`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`と`-p pytest_django.plugin -p pytest_env.plugin -p pytest_cov.plugin`（CI宣言どおりのplugin一式、`pytest-dotenv`除外）で起動すると、Batch 8–11 Knowledge seed関連38件を含む全テストが正常にPASSする |

**本Auditではpackage変更を一切行っていない**（`pip uninstall`等は
未実施、read-onlyな診断のみ）。

**分類: `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`。**

恒久修正の候補（別PRで検討、本Auditのスコープ外）:
- このマシンの`backend/.venv`から未宣言の`pytest-dotenv`を削除する
- または`pytest-env`を`--envfile`非搭載バージョンへ固定する
- または`pytest.ini`の`addopts`で明示的に`-p no:dotenv`を指定し、
  CI外の環境でも同じplugin構成を強制する

---

## Phase 12 — Batch Size

Batch 8–11実績（各5社）から:

- **Source research負荷**: 1社あたり公式サイト1〜2ページを`WebFetch`で
  直接確認する運用。5社で作業量は管理可能だったが、10社では単純に
  倍増し、1セッション内での確認漏れリスクが増す。
- **Evidence review負荷**: Batch 11は5社でDeity16・History7・Fact-Source
  relation23件。10社ではおよそ倍（Deity30〜40・History15前後）になり、
  Mother Shipのレビュー負荷も比例して増える。
- **failure isolation**: 単一`transaction.atomic()`のため、1件でも
  `full_clean()`失敗があれば全体がrollbackされる設計。件数が増えるほど、
  1つのエラーで無駄になる既検証作業（Source確認・Evidence Gate判断）が
  増える。
- **Production blast radius**: 5社なら1回のwriteで最大数十行程度の
  影響に留まるが、10社では単純に倍。ロールバック自体は安全（atomic）
  だが、「何が変わるか」をHuman Confirmationで一目に把握できる範囲を
  超えるリスクがある。
- **human review cost**: Batch 8–11いずれもMother Shipによる個別判断
  （福禄寿の扱い等）が発生している。バッチサイズが大きいほど、
  こうした個別判断ポイントを見落とすリスクが増える。

**技術的推奨: Batch 12もBatch 8–11同様、5社を基準とする。** 10社への
拡大は、上記のとおりreview負荷・blast radius・failure isolationの
トレードオフが明確にあるため、Mother Shipの明示判断なしに本ドキュメント
では決定しない。

---

## Phase 13 — Remaining Limitations

- partial 2社（阿佐ヶ谷神明宮・香取神宮）のHistory repairは未実施のまま
  （Phase 9参照）
- `ASSOCIATED_WORSHIP_TARGET_MODEL_REVIEW`（七福神・神仏習合等、古典的な
  神話系譜を持たない「祀られている対象」のKnowledge Model設計）は
  将来課題のまま未着手
- Recommendation runtime write-required QA（Phase 6参照）は本Auditの
  スコープ外のまま
- Source page instability（公式サイトの将来的な変更リスク）は一般的
  リスクとして継続
- `SKIP_EXISTS`のsemantic-diff limitation（既存Factと同名でも内容差分を
  検知しない）は既知の設計上の制約として継続
- product-value signal availability（Coverage向上がユーザー行動に
  どう影響するかの計測）は未整備のまま
- local pytest environment drift（Phase 11参照）は`LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`
  として記録、恒久修正は別PR候補

---

## Phase 14 — Final Classification

Phase 1–13のすべてでdrift 0・regression 0・新規blocking issueなし。

**`BATCH11_CLOSED_BATCH12_REENTRY_READY_WITH_LIMITATIONS`**

Production DB writes（本Audit中） = 0
Batch 12 Data writes = 0
Batch 12 Target Selectionは未着手（本ドキュメントのスコープ外）

---

## 最終報告サマリ

1. develop SHA: `9edd154d17aa8c2a57f58e7ebbd9e04579abdeee`
2. Batch 11 actual result: Source+5/Deity+16/History+7/rel+16/+7、単一
   atomic transaction、1回のみ実行、idempotency確認済み
3. Production current counts: Source81・Deity165・History113・
   rel178/118・Knowledge Shrine61（drift 0）
4. Coverage: complete59・partial2・none44（drift 0）
5. source-less: DB全体で0件
6. ambiguous identity: 0件
7. duplicate contamination: 0件
8. Batch 11 five-shrine verification: 全件PASS、福禄寿0件
9. Runtime QA: 5/5 HTTP 200、payload完全一致、aggregate不変
10. existing flow regression: PASS（Top/list・Detail・既存フィールド）、
    Recommendationは`RECOMMENDATION_RUNTIME_WRITE_REQUIRED`として記録のみ
11. application aggregate regression: 完全不変
12. Source health: orphan0・source-less0・duplicate URL0・ambiguous reuse0
13. Batch 12 raw candidate count: 44
14. Batch 12 canonical candidate count: 39
15. partial status: 2社、`PARTIAL_REPAIR_CANDIDATE`、対象外のまま
16. excluded/unresolved: QA fixture1・unresolved identity1・duplicate3
    （計5件、過去監査と完全一致）
17. reused contracts: `BATCH11_CONTRACT_REUSED`（12契約すべて無変更で
    再利用可能）
18. local pytest drift classification: `LOCAL_TEST_ENVIRONMENT_DRIFT_NON_BLOCKING`
19. 5 vs 10 technical recommendation: 5社を維持（Phase 12参照）、10社は
    Mother Ship判断が必要
20. remaining limitations: Phase 13参照
21. audit document: 本ドキュメント
    （`docs/audit/knowledge-batch11-closure-batch12-reentry.md`）
22. PR: 別途作成（本ドキュメントのcommit時に作成）
23. CI: PR作成後に確認
24. final classification: `BATCH11_CLOSED_BATCH12_REENTRY_READY_WITH_LIMITATIONS`

Production DB writes = 0
Batch 12 Data writes = 0
