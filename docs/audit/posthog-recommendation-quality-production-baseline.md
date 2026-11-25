> **Status: `KNOWLEDGE_CLASSIFICATION_DATA_AVAILABLE`（sample: `INSUFFICIENT_SAMPLE`、N=3・単一thread）。**
>
> [Production Analyticsイベント到達性を監査](posthog-production-event-reachability.md)
> （`PRODUCTION_ANALYTICS_REACHABILITY_CONFIRMED`）で確認したMother Ship
> 自身の既知検証トラフィック（2026-08-12 17:39 JST前後、Concierge結果
> 表示→宇佐神宮推薦→詳細を見る→詳細ページ遷移）を対象に、
> `recommendation_quality`イベントのKnowledge分類property
> （`knowledge_backing_class`/`deity_knowledge_used`/
> `history_knowledge_used`）が実Production payloadに正しく現れている
> ことをaggregate-only queryで確認した。**サンプルはMother Ship自身の
> 検証由来3件・単一threadのみであり、Knowledgeの効果・CTR改善・
> 推薦品質向上はいかなる形でも断定していない。** Recommendation
> behavior・Ranking・Score v3・Analytics event・Knowledge Modelはいずれも
> 変更していない。

---

## 1. Base State（Phase 0）

- **PR #2392** merge確認済み（`cda90a13`、2026-08-12 09:20:14 UTC）
- develop最新化・origin/developと同期・working tree clean
- **HEAD SHA**: `cda90a138f8fd6adb9771381eb7f5b25b1ed71d5`
- `scripts/analytics_safety/`のdrift確認: `git diff e35a6c9d cda90a13 -- scripts/analytics_safety/`は空
  （PR #2390以降、tooling本体への変更なし。PR #2391/#2392はdocs/audit/のみ）

---

## 2. Foundation Gate（Phase 1）

```
$ python3 -m pytest -p no:dotenv scripts/analytics_safety/tests/ -v
============================== 90 passed in 0.10s ==============================
```

`guard.sanitize_query_result()`のoutput allow-list（`results`/`columns`/
`error`のみ）に変更なし。credential contractにも変更なし。

---

## 3. Credential Gate（Phase 2）

```
$ bash scripts/analytics_safety/check_posthog_credential_presence.sh ~/.config/kami-musubi/posthog-readonly.env
POSTHOG_PERSONAL_API_KEY_SET=1 / SHAPE={"length_bucket": "typical", ...}
POSTHOG_PROJECT_ID_SET=1 / SHAPE={"length_bucket": "short", ...}
POSTHOG_HOST_SET=1 / SHAPE={"length_bucket": "typical", ...}
```

ファイルpermission: `600`確認済み。値・project ID・hostnameはいずれも
出力していない。

---

## 4. Observation Window（Phase 3）

- **Baseline開始点**: `2026-08-12T04:12:15Z`（PR #2384 Production rollout時刻、
  `DEFAULT_ROLLOUT_SINCE`）
- **既知観測点**: Mother Shipによる実Production検証操作、2026-08-12
  17:39 JST前後（= `2026-08-12T08:39:00Z`付近）。確認済み操作:
  Concierge結果表示 / 宇佐神宮の推薦表示 /「神社の詳細を見る」/
  神社詳細ページへの遷移
  （[posthog-production-event-reachability.md](posthog-production-event-reachability.md)
  17章で到達確認済み）
- **Query window（本監査）**: `2026-08-12T04:12:15Z` 〜
  `2026-08-12T09:21:46Z`（rollout時刻〜クエリ実行時点）
- raw user/event rowは取得していない（すべてaggregate count / GROUP BY
  count）

---

## 5. Recommendation Quality Aggregate（Phase 4）

既存`posthog_baseline_report.py`（`QUERY_CONTRACT`）+ ad-hoc aggregate
query（既存sanitized wrapper経由、event名+enum property+countのみ）で
取得。

| 指標 | 値 |
|---|---|
| `recommendation_quality`総件数 | **3** |
| `knowledge_backing_class = FULLY_KNOWLEDGE_BACKED` | **2** |
| `knowledge_backing_class = PARTIALLY_KNOWLEDGE_BACKED` | **0** |
| `knowledge_backing_class = LEGACY_BACKED` | **0** |
| `knowledge_backing_class = UNKNOWN` | **1** |
| `deity_knowledge_used = true` | **2** |
| `deity_knowledge_used = false` | **1** |
| `history_knowledge_used = true` | **2** |
| `history_knowledge_used = false` | **1** |

3件の合計とclassification内訳（2+0+0+1=3）が一致することを確認した。

---

## 6. Property Completeness（Phase 5）

`property_completeness`（`QUERY_CONTRACT`既存query、母数=3）:

| property | present | 欠損率 |
|---|---|---|
| `knowledge_backing_class` | 3/3 | **0%** |
| `deity_knowledge_used` | 3/3 | **0%** |
| `history_knowledge_used` | 3/3 | **0%** |

**enum外値チェック**: 観測された`knowledge_backing_class`の値は
`FULLY_KNOWLEDGE_BACKED`/`UNKNOWN`の2種のみで、いずれも定義済み4値
（`FULLY_KNOWLEDGE_BACKED`/`PARTIALLY_KNOWLEDGE_BACKED`/
`LEGACY_BACKED`/`UNKNOWN`）の範囲内。enum外の値は観測されなかった。

consultation本文・Fact本文・Source URL等の自由記述fieldは、いかなる
queryでも選択していない（`QUERY_CONTRACT`・ad-hoc queryとも
event名・enum property・countのみを対象とする設計）。

---

## 7. Sample Sufficiency（Phase 6）

- **sample_count = 3**（`unique_recommendation_sessions` = **1**、単一
  threadから発生した3件）
- **分類: `INSUFFICIENT_SAMPLE`**。Mother Ship自身の検証操作由来の3件
  のみであり、独立した複数セッション・複数ユーザーによる分布ではない。
- 有意差判定のためのsample size thresholdは、本監査でも根拠なく新設
  していない。前回までの監査（[Analytics Contract](knowledge-recommendation-analytics-contract.md)
  等）で維持してきた`SAMPLE_SIZE_THRESHOLD_NOT_DEFINED`をそのまま維持
  する。
- この3件のみを根拠に、Knowledge分類間の品質優劣（例:
  「FULLY_KNOWLEDGE_BACKEDの方がUNKNOWNより良い」等）を**断定しない**。

---

## 8. Funnel Reachability（Phase 7）

同じquery window（`2026-08-12T04:12:15Z` 〜 `09:21:46Z`）でのaggregate
count（個人単位JOINは行っていない）:

| event_name | count |
|---|---|
| `concierge_result_impression` | **3** |
| `shrine_detail_transition` | **2** |
| `shrine_decision`（全action） | **0** |
| `route_open` | **0** |
| `visit_done` | **0** |
| `consultation_completed` | **1** |

確認済み操作（Concierge結果表示・宇佐神宮推薦表示・詳細を見る・詳細
ページ遷移）に save/route open/visit操作が含まれないことと、
`shrine_decision`/`route_open`/`visit_done` = 0という結果は整合する。

---

## 9. Baseline Analysis Gate（Phase 8）

- `recommendation_quality` > 0 を再確認: **✅（3件）**
- classification propertyが実Production payloadに存在: **✅**（6章、
  完全性100%）
- property completenessは十分（0%欠損）だが、**sample_count（3、単一
  thread）はrate比較を行うには不十分**と判定した。
- **判定: データ量不足のため、率比較（CTR/save率等）へは進まない**
  （9〜10章はcontract検証・feasibility確認に留める）。

---

## 10. Segmented CTR Contract Validation（Phase 9）

`UNVERIFIED_SEGMENTED_QUERY_CONTRACT`（`posthog_baseline_report.py`の
`ctr_by_classification`）を**実行はせず**、契約の安全性・実行可能性の
みをfresh検証した（8章の判定により、率比較そのものへは進まないため）。

- **query設計**: `imp`(`concierge_result_impression`)/`dt`
  (`shrine_detail_transition`)/`rq`(`recommendation_quality`)を
  `threadId`/`shrineId`/`recommendationRank`でLEFT JOINし、
  `rq.properties.knowledge_backing_class`別に
  `count(DISTINCT imp.uuid)`/`count(DISTINCT dt.uuid)`を集計する設計。
  event名・enum property・count・JOIN keyのみを参照し、raw property
  dump・PIIは選択していない → **aggregate-onlyで安全に算出できる設計
  であることを確認**。
- **FULLY/PARTIALLY/LEGACY/UNKNOWN別impression数の取得可能性**: 理論上
  可能（`rq.properties.knowledge_backing_class`でGROUP BYするのみ）。
  ただし6章の通り現在の分布は`FULLY_KNOWLEDGE_BACKED`=2/`UNKNOWN`=1の
  みで、`PARTIALLY_KNOWLEDGE_BACKED`/`LEGACY_BACKED`は0件のため、
  4分類全てを実データで示すことは今回できない。
- **同分類別detail_transition数の取得可能性**: 同様に理論上可能。
- **join key契約のfresh確認**: `apps/web/src/features/concierge/hooks.ts`
  （`recommendation_quality`）と
  `apps/web/src/features/concierge/components/ConciergeSectionsRenderer.tsx`
  （`concierge_result_impression`/`shrine_detail_transition`）の両方の
  実装コードを直接読み、いずれも`threadId`/`shrineId`/
  `recommendationRank`を実際にpayloadへ含めていることを確認した
  （[Analytics Contract](knowledge-recommendation-analytics-contract.md)
  §7で設計されたjoin keyが実装と一致している）。
- **raw event queryは実行していない**（0回）。
- 実値（unique thread = 1）が少なすぎるため、このJOIN queryを実際に
  実行しても意味のあるCTR差は算出できないと判断し、**実行を見送った**。
  `UNVERIFIED_SEGMENTED_QUERY_CONTRACT`は引き続き**未実行・design-only
  検証済み**のステータスを維持する。

---

## 11. Save / Visit Intent Readiness（Phase 10）

- `shrine_decision`(save)との集計可能性: 既存`save_count`
  query（`action = 'save'`フィルタ）で確認可能。今回の期間は**0件**
  （8章参照）。
- `route_open`との集計可能性: 既存`route_open_count`
  queryで確認可能。今回の期間は**0件**。
- `visit_done`のrank/resultSetId欠落制約:
  [Analytics Contract](knowledge-recommendation-analytics-contract.md)
  §5/§21、および
  [Analytics Observability監査](knowledge-recommendation-analytics-observability.md)
  §143でfresh再確認した。`visit_done`は`shrineId`/`threadId`は持つが
  `rank`/`resultSetId`を持たず、**`JOIN_READY_WITH_LIMITATIONS`**の
  ままであることを確認した。
- 本監査でもevent schema変更は行っていない（`JOIN_READY_WITH_
  LIMITATIONS`を維持）。

---

## 12. Quality Baseline Classification（Phase 11）

**`KNOWLEDGE_CLASSIFICATION_DATA_AVAILABLE`**

根拠:

- `DATA_NOT_YET_SUFFICIENT`ではない: `recommendation_quality`が実際に
  3件存在し、classification propertyが100%の完全性で観測できている
  （5〜6章）。前回監査時点（`PRODUCTION_TRAFFIC_COLLECTION_PENDING`）
  から明確に進展している。
- `BASELINE_COLLECTION_ACTIVE`だけでは実態を過小評価する:
  単なる「収集が始まった」状態ではなく、既にKnowledge分類（4値enum）
  が実Production payload上で正しく機能していることを実データで確認
  できている。
- `KNOWLEDGE_FUNNEL_BASELINE_READY`ではない: sample_countが3・単一
  threadのみであり（7章）、save/route_open/visit_doneはいずれも0件
  （8章）。Funnel全体を通じた意味のあるbaseline（CTR・save率等）を
  算出できる状態にはまだ達していない。
- 消去法および実態の両面から、**`KNOWLEDGE_CLASSIFICATION_DATA_
  AVAILABLE`が最も正確な分類**と判断した。

---

## 13. No Premature Optimization Boundary（Phase 12）

以下はいずれも本監査で**行っていない**:

- Recommendation reason文言の変更
- Rankingの変更
- Score v3のactive化
- Analytics eventの変更
- Dashboardの実装
- Knowledge Modelの変更
- 3件・単一threadというsmall sampleを根拠にしたプロダクト判断
  （例: 「Knowledgeは効果がある」「CTRが改善した」等の結論は一切
  出していない）

---

## 14. Next Review Cadence（Phase 13）

- **現在のProduction traffic量**: Mother Ship自身の検証セッション
  1件（3イベント）のみ。組織的・多ユーザーによる自然発生トラフィックは
  本監査時点でまだ観測されていない。
- **再計測条件**: 「特定の日付」ではなく、「**独立した複数
  session/threadから`recommendation_quality`が十分蓄積された後**」を
  基本条件とする。
- 具体的な数値thresholdは、根拠なく新設しない（指示通り）。将来、
  統計的に意味のあるsample size算出の根拠（想定効果量・分散等）が
  得られた時点で、別監査として定義する。
- 再計測時に確認すべき点: (1) sample_countが単一threadから複数
  独立threadへ拡大しているか、(2) `PARTIALLY_KNOWLEDGE_BACKED`/
  `LEGACY_BACKED`を含む4分類全てが実データで観測できるか、(3)
  `shrine_decision`/`route_open`/`visit_done`など行動指標側にも
  データが生じているか。

---

## 15. Security（Phase 14）

```
$ gitleaks detect --source docs/audit/posthog-recommendation-quality-production-baseline.md --no-git -v
no leaks found
```

- credential値・Project ID・hostname・raw response混入: 0
  （全query出力は`columns`/`error`/`results`のsanitized allow-list
  経由のみ）
- internal identifier scan: team_id等の内部識別子は本ドキュメントに
  一切記載していない
- PII scan: distinct_id・person情報・consultation本文・Fact本文・
  Source URLはいずれも取得・記載していない
- `git status` / `git diff --check`: doc-only変更を確認

---

## 16. Final Classification

**`KNOWLEDGE_CLASSIFICATION_DATA_AVAILABLE`**
（sample readiness: `INSUFFICIENT_SAMPLE`）

Mother Ship自身の既知検証トラフィック（N=3、単一thread）を通じて、
`recommendation_quality`イベントのKnowledge分類3 property
（`knowledge_backing_class`/`deity_knowledge_used`/
`history_knowledge_used`）が実Production payload上で100%の完全性で
正しく機能していることを確認した。Segmented CTR query contractは
design-onlyで検証済み（join key契約は実装コードと一致）だが、
sample不足のため実行・rate算出はいずれも見送った。Save/Visit
Intent側は引き続き0件・`JOIN_READY_WITH_LIMITATIONS`。Knowledgeの
効果・CTR改善・推薦品質向上はいずれも断定していない。

Production DB writes = 0
PostHog mutations = 0
Raw event exports = 0
Recommendation behavior changes = 0
Ranking changes = 0
Score v3 active化 = 0
Analytics event変更 = 0
