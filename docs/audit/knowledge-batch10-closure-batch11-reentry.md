> **Status: `BATCH10_CLOSED_BATCH11_REENTRY_READY_WITH_LIMITATIONS`。**
>
> 本ドキュメントは`docs/audit/knowledge-batch10-production-import-execution.md`
> （`BATCH10_PRODUCTION_IMPORT_EXECUTED`）を受け、Batch 10実行結果をfreshに
> 再検証して正式Closeし、最新none集合からBatch 11 candidate universeを
> 再構築した記録である。
>
> **本ドキュメント作成のセッションでは、Production Knowledge write・
> Batch 11 seed作成・Batch 11 importのいずれも実行していない。** 実行した
> のは、`readonly_query.sh`経由のSELECTと、公開Web（読み取り専用GET）への
> Runtime QAのみ。Production DB writeは0件。

# Knowledge Batch 10 Closure Audit / Batch 11 Re-entry Gate

## develop SHA

作業開始時点: `94e5312a68aa06dc1502806a64f30dd4bf8fba3a`（PR #2359反映済み、
`origin/develop`と同期済み、working tree clean）。

---

## Phase 1 — Execution Record Reconciliation

`docs/audit/knowledge-batch10-production-import-execution.md`の
Execution Recordから実測値を抽出した（計画値ではなくactual値）。

| 項目 | 値 |
|---|---|
| execution timestamp | 2026-08-10 11:35 UTC |
| seed hash | `e44484431af89274c3ba7258e49dac7cd2b186f8d0bfebb62b60137d0b7255d9` |
| exit status | 0 |
| atomic transaction | 単一（`transaction.atomic()`） |
| Source before/after | 70 → 76 |
| Deity before/after | 130 → 149 |
| History before/after | 96 → 106 |
| Deity–Source relation before/after | 143 → 162 |
| History–Source relation before/after | 101 → 111 |
| Knowledge Shrine before/after | 51 → 56 |
| Coverage before/after | complete 49→54・partial 2（不変）・none 54→49 |
| source-less | 0 |
| aggregate regression | なし（無関係データ完全不変） |
| idempotency | PASS（実行後dry-runで全件REUSE/SKIP、CREATE 0） |
| recovery | 該当なし（失敗が一切発生していない） |
| second importなし | 確認済み（apply 1回 + 検証dry-run 1回のみ） |

---

## Phase 2 — Production Current State（fresh再確認）

Production read-only接続でfresh取得（snapshot時刻`2026-08-10 11:42:05+00`）。

| 指標 | Execution Record記載値 | fresh実測値 | 判定 |
|---|---:|---:|---|
| Knowledge Shrine | 56 | 56 | 一致 |
| Source | 76 | 76 | 一致 |
| Deity | 149 | 149 | 一致 |
| History | 106 | 106 | 一致 |
| Deity–Source | 162 | 162 | 一致 |
| History–Source | 111 | 111 | 一致 |

drift 0件。source-less Deity = 0・source-less History = 0（対象5社、fresh
再確認）。ambiguous identity = 0・duplicate contamination = 0（対象5社は
全件`same_name_count=1`、非canonical行の混入なし）。

---

## Phase 3 — Coverage Recalculation

Production 105社（全kind、既存Coverage Contractと同じ母数）でfresh再計算。

| 区分 | 期待値 | fresh実測値 | 判定 |
|---|---:|---:|---|
| complete | 54 | 54 | 一致 |
| partial | 2 | 2 | 一致 |
| none | 49 | 49 | 一致 |

---

## Phase 4 — Batch 10 Five-Shrine DB Verification（content-level）

対象5社について、件数だけでなく個々のFact内容（`display_name`/`role`/
`history_type`/`title`/`verification_status`/`confidence`/Source relation
件数）をseedと突合した。

| shrine | Deity | History | 内容一致 | source-less | Evidence Gate |
|---|---:|---:|---|---:|---|
| 大國魂神社 | 7 | 2 | 完全一致 | 0 | 全件`source_confirmed`/`high`、relation1件ずつ |
| 寒川神社 | 2 | 2 | 完全一致 | 0 | 同上 |
| 浅草神社 | 3 | 2 | 完全一致 | 0 | 同上 |
| 川越氷川神社 | 5 | 2 | 完全一致 | 0 | 同上 |
| 芝大神宮 | 2 | 2 | 完全一致 | 0 | 同上 |

19 Deity・10 Historyの全件について、`display_name`/`role`（primary/
secondary/enshrined/unknown）・`history_type`（tradition/historical_event/
founding）・`title`がseedの値と一字一句一致することを確認した。

---

## Phase 5 — Production HTTP Runtime QA

`backend/temples/api/urls.py`から現行の公開Detail route
（`ShrineViewSet.retrieve`、`AllowAny`、`GET /api/shrines/<pk>/data/`、
Web BFF: `apps/web/src/app/api/shrines/[id]/data/route.ts`、
`forwardAuth: false`）をfresh確認し、Production公開URL
（`gh repo view --json homepageUrl` = `https://jinja-app-web.vercel.app`）
経由で5社へread-only GETを実行した。

| shrine | id | HTTP | name/address一致 | Deity | History | Unique Source | source-lessペイロード |
|---|---:|---:|---|---:|---:|---:|---|
| 大國魂神社 | 25 | 200 | 一致 | 7 | 2 | 1 | なし |
| 寒川神社 | 26 | 200 | 一致 | 2 | 2 | 2 | なし |
| 浅草神社 | 24 | 200 | 一致 | 3 | 2 | 1 | なし |
| 川越氷川神社 | 40 | 200 | 一致 | 5 | 2 | 1 | なし |
| 芝大神宮 | 45 | 200 | 一致 | 2 | 2 | 1 | なし |

HTTP 500は0件。全件`verification_status: source_confirmed`・
`confidence: high`がペイロードにそのまま反映されていることを確認した。

GET後にProduction Knowledge counts（Source76・Deity149・History106・
relation162/111）をfresh再確認し、read-only QAによるwriteが0件で
あることを確認した。

---

## Phase 6 — Existing Flow Regression

- Top page相当（shrine一覧、`GET /api/shrines?name=...`）: HTTP 200、
  read-only、既存動作に変化なし
- Shrine Detail既存field（`goriyaku`/`goriyaku_tags`/`location`/
  `kyusei`等）: Phase 5取得ペイロードに引き続き含まれることを確認、
  Knowledge追加による既存field欠落・破壊なし
- serializer既存contract: `ShrineDetailSerializer`の`deities`/
  `histories`ネスト構造は変更なく機能

Recommendation endpoint（`/api/concierge/chat`）はCookieベースの認証・
セッション状態書き込みを伴う設計であることをコード確認で把握したため、
**本監査では実行していない**（`RECOMMENDATION_RUNTIME_WRITE_REQUIRED`）。
read-only原則を優先し、Mother Ship判断が必要な項目として明示する。

---

## Phase 7 — Batch 11 Candidate Universe

Production `none`集合（49社、Phase 3のfresh実測値）をread-onlyで全件
取得し、既知の除外パターンを適用した。

| id | name_jp | 除外理由 |
|---:|---|---|
| 102 | テスト確認神社 20260611 | QA fixture |
| 105 | 広島市 | unresolved identity（神社名ではなく地名） |
| 104 | 富岡八幡宮（非canonical重複） | duplicate（canonical id=49が候補として残る） |
| 101 | 給田六所神社（非canonical重複） | duplicate |
| 103 | 長太稲荷神社（非canonical重複） | duplicate（canonical id=21が候補として残る） |

**Batch 11 candidate universe = 49 − 5 = 44社。** 全件`place_ref_id IS
NULL`（canonical）、`same_name_count=1`（除外後）、QA fixture・unresolved
identityを含まない。個別のSource availability調査（Batch 10 Phase 2相当）
は本ドキュメントでは実施していない（Batch 11 seed作成そのものが本タスク
の対象外のため）。

---

## Phase 8 — Partial 2 Recheck

| shrine | id | Deity | History | 既存Source状態 |
|---|---:|---:|---:|---|
| 阿佐ヶ谷神明宮 | 29 | 3（天照大神/月読命/須佐之男命、全件`source_confirmed`、relation1件ずつ） | 0 | Deity用Sourceは有効、History用Sourceは未整備 |
| 香取神宮 | 15 | 1（経津主大神、`source_confirmed`、relation1件） | 0 | 同上 |

両社とも**引き続きpartial**。欠落layerはHistoryのみで、既存Deity Sourceは
健全（source-lessではない）。repair feasibilityは高い（Historyの
Source・Fact追加のみで完結する見込み）が、**本監査ではrepairを実行せず、
Batch 11通常候補にも混ぜない**（指示どおり）。

---

## Phase 9 — Batch 11 Contract Reuse

Batch 8〜10で確立した以下の契約は、Batch 10のend-to-end実行（seed構築→
`--validate-only`→`--dry-run`→Production-equivalent test→Human Execution
Boundary→Production import→Runtime QA）を通じて無修正のまま機能した。

- [x] 5社batch規模での運用
- [x] canonical identity解決（`resolve_shrine`、`place_ref_id IS NULL`優先）
- [x] official Source優先（`shrine_official`直接確認）
- [x] Source semantic conflict precheck（`url ILIKE`ドメイン突合）
- [x] Source reuse contract（`normalize_source_url` + `resolve_source_identity`）
- [x] Evidence Gate（`source_confirmed`/`high`必須、source-less禁止）
- [x] canonical seed（`schema_version: "1.0"`、PK非依存）
- [x] `--validate-only`
- [x] `--dry-run`
- [x] Production-equivalent test（fresh dump復元isolated DB）
- [x] idempotency（second dry-runでの冪等性確認）
- [x] Fresh Backup（`dump_readonly.sh`、接続情報非開示）
- [x] Human Execution Boundary（`AskUserQuestion`による明示確認）
- [x] Runtime QA（HTTPレベルでのpayload確認）

**`BATCH10_CONTRACT_REUSED`。** 構造変更は不要と判断する。

---

## Phase 10 — Source Reuse Contract Health Check

Production現在状態（Source 76件）をread-only監査した。

| 指標 | 結果 |
|---|---|
| 重複normalized URL（同一`source_type`+URL） | 0件 |
| ambiguous reuse | 0件（Batch10の6候補は全件`NO_CONFLICT`のままCREATEされた） |
| metadata conflict | 0件 |
| orphan Source（どのFactからもrelationされていない） | 0件 |
| Source総数 | 76（URL-backed 75） |

Source reuse contractは健全。Batch 11実行前に追加の修復は不要。

---

## Phase 11 — Batch Size Analysis（5継続 vs 10拡大）

| 観点 | 5社継続 | 10社拡大 |
|---|---|---|
| Source research量 | Batch10実績: `WebFetch`約7回 | 線形に約2倍。個別ページの内容確認は自動化できず、品質を保ったまま倍量処理すると時間コストが線形以上になりやすい |
| Evidence review量 | 29 Fact（Deity19+History10）を個別にrole/history_type判定 | 約2倍（50〜60 Fact）。最も律速する工程 |
| Production blast radius | 単一transactionでSource+6/Deity+19/History+10 | 単一transactionが約2倍。all-or-nothing特性は維持されるが差し止め範囲も倍 |
| failure investigation | 該当なし（Batch10はerror 0件） | 万一エラー時、原因箇所特定の手間が増える |
| recovery判断 | 該当なし | 技術的には5社と同等（atomic transaction） |
| Batch 8〜10実証結果 | 3回連続成功、error 0件、rollback 0件 | 実績なし |

**技術的推奨: 5社継続。** 技術的安全性（atomic transaction・
`--validate-only`・`--dry-run`・Production-equivalent test）はどちらの
規模でも同等に機能するが、実際のボトルネックはSource research/Evidence
reviewという人的判断工程であり、規模に対して線形以上にコストが増える。
Batch 8〜10の3回連続無エラー実績は5社規模で確立されたものであり、10社
への拡大はこの実証範囲を超える。**最終決定はMother Ship判断とする。**

---

## Phase 12 — Final Classification

**`BATCH10_CLOSED_BATCH11_REENTRY_READY_WITH_LIMITATIONS`**

READYと判断する根拠:

- Batch 10 actual counts・Coverageがすべてfresh実測値と完全一致（drift 0）
- source-less = 0・duplicate contamination = 0（対象5社）
- Batch 10 5社のDB内容（content-level）・Runtime QA（HTTP 200・payload
  一致）がともにPASS
- Batch 11 candidate universe（44社）を確定
- Batch 8〜10で確立したcontractが無修正で再利用可能（Source reuse
  contractも健全）

`WITH_LIMITATIONS`とする理由:

- Recommendation endpoint（`/api/concierge/chat`）は認証・Cookie書き込みを
  伴うためexisting flow regressionの対象から除外した
  （`RECOMMENDATION_RUNTIME_WRITE_REQUIRED`）。read-only原則を優先した
  結果であり、Batch 10自体の異常を示すものではない
- partial 2社（阿佐ヶ谷神明宮・香取神宮）はHistory層が引き続き未整備。
  repairはBatch 11の通常候補ではなく別枠の判断が必要
- Batch 11 candidate universe（44社）はnone集合の再構築のみであり、
  個別のOfficial Source availability調査（Batch 10 Phase 2相当）は
  未実施

---

## Mother Ship Decision（判断待ち項目）

1. Batch 11のbatch size（5社継続 or 10社拡大、Phase 11参照）
2. partial 2社（阿佐ヶ谷神明宮・香取神宮）のHistory repairをBatch 11と
   並行するか、別タスクとして扱うか
3. Recommendation endpointのRuntime QAを別途authenticated sessionで
   実施するか

---

## 絶対禁止事項の遵守

本ドキュメント作成セッションでは以下を一切実行していない:

- Production Knowledge write
- Batch 11 seed作成
- Batch 11 import
- partial repair（阿佐ヶ谷神明宮・香取神宮への着手）
- existing Knowledge変更
- manual SQL write
- Score/Ranking変更
- Source UI
- PER_FACT_RENDERING

Production DB writes = 0
Batch 11 Data writes = 0
