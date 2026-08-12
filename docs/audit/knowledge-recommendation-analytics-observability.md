> **Status: `KNOWLEDGE_ANALYTICS_BASELINE_COLLECTION_READY`。**
>
> PR #2384で追加したKnowledge品質property（`knowledge_backing_class`/
> `deity_knowledge_used`/`history_knowledge_used`）が、Production
> Frontend（Vercel）・Backend（Render）の**両方に、実際にmerge commitの
> SHA一致という形でread-onlyに確認済み**。ただし、実際のイベント発火・
> PostHogへの到達・実データでの分類分布は、本監査の範囲では確認できない
> （artificial Production recommendationの実行が絶対禁止であり、PostHog
> への read-only アクセス手段も本セッションには存在しないため）。
> **実装ゼロ・Analytics変更ゼロ・Production writeゼロ・Ranking/Score/
> Recommendation変更ゼロ。**

---

## 1. develop SHA

`98e88b79ddbb503c3351a3d9f204703b7e41c19a`（2026-08-12 13:11:26 +0900、
PR #2384のmerge commit）

PR #2384（[knowledge-recommendation-analytics-properties-implementation.md](knowledge-recommendation-analytics-properties-implementation.md)）
merge確認済み（ユーザー自身によるmerge）。develop同期・working tree
clean。

---

## 2. Production Deployment State（Phase 2）

**`DEPLOYMENT_CONFIRMED`**（推測ではなく、read-only APIで直接確認）。

### Frontend（Vercel）

Vercel Deployments APIで`jinja-app-web`プロジェクトの最新deploymentを
確認した。

| 項目 | 値 |
|---|---|
| Deployment ID | `dpl_AcehvHCZesf5j8xYqwqK4d7k9xwC` |
| target | `production` |
| state | `READY` |
| githubCommitSha | `98e88b79ddbb503c3351a3d9f204703b7e41c19a`（develop SHAと完全一致） |
| githubCommitRef | `develop` |
| githubCommitVerification | `verified` |

### Backend（Render）

Render固有の読み取りAPIツールは本セッションに存在しないが、既存の
`/healthz/`エンドポイント（`shrine_project/urls.py`、GETのみ、read-only、
Recommendation生成を一切伴わない）が`release`フィールドとして
デプロイ済みgit SHAを返すことをfreshに発見し、確認した。

```bash
curl -s https://jinja-backend.onrender.com/healthz/
# => {"ok": true, "release": "98e88b79ddbb503c3351a3d9f204703b7e41c19a"}
```

`release`の値は develop SHAと完全一致する。

**結論**: Production Frontend・Backendの両方が、PR #2384（Knowledge
Analytics property追加）を含む最新コミットで稼働中であることを
read-onlyに確認した。

---

## 3. `recommendation_quality` Runtime State（Phase 3）

コード上は（[knowledge-recommendation-analytics-properties-implementation.md](knowledge-recommendation-analytics-properties-implementation.md)
で確認済みの通り）Backendが`recommendation_reason_quality`へ3
propertyを付与し、Frontendがそれを`recommendation_quality`
イベントへ転送する経路が実装され、2章の通りProductionへデプロイ
済みである。

しかし、**実際にconcierge chatへのリクエストが発生した際にこの経路が
正しく動作し、PostHogへ到達するかどうかは、本監査では確認していない**。
理由:

- 確認するには実際のconcierge chat POST（Recommendation生成）が必要だが、
  「artificial Production recommendation」は絶対禁止事項である。
- 実ユーザートラフィックを人為的に発生させることもしていない
  （「新規Production event生成のためにユーザー行動を人工的に発生させない」
  という制約を遵守）。

**分類: コードの到達性は`DEPLOYMENT_CONFIRMED`。実際のRuntime発火・
PostHog到達の確認は範囲外（未実施、意図的）。**

---

## 4. Analytics Storage / Retrieval Audit（Phase 4）

PostHog（本アプリのAnalytics基盤、[cross-platform-event-contract.md](cross-platform-event-contract.md)参照）
への read-only アクセス手段を調査した。

- 本セッションのツール一覧にPostHog関連のMCPツールは存在しない。
- Vercel Web Analytics（`get_web_analytics`）を試したが、
  `404 Web Analytics not found`（このプロジェクトでは無効。本アプリの
  Analytics送信は`posthog-js`経由であり、Vercel純正のWeb Analyticsとは
  別系統のため、そもそも該当データを持たない）。
- PostHogのAPI Key・ダッシュボードへの認証情報は本セッションに
  存在しない。

**分類: `PRODUCTION_ANALYTICS_READ_ACCESS_NOT_AVAILABLE`**。

---

## 5. Property Completeness（Phase 5）

4章の通りPostHogへのread-onlyアクセスがないため、実データでの
`knowledge_backing_class`/`deity_knowledge_used`/`history_knowledge_used`
存在率・null率・invalid enum率・既存7 propertyの欠損率は算出できない。

**分類: `INSUFFICIENT_POST_ROLLOUT_DATA`**。

---

## 6. Classification Distribution（Phase 6）

同様の理由により、Production実データでのFULLY/PARTIALLY/LEGACY/UNKNOWN
分布は算出しない。数値を推測・捏造しない。

**分類: `INSUFFICIENT_POST_ROLLOUT_DATA`**。

参考情報として、[knowledge-recommendation-quality-baseline.md](knowledge-recommendation-quality-baseline.md)
のローカルDB実測（sample 100件、FULLY 85%・UNKNOWN 15%・PARTIALLY/LEGACY
各0%）が存在するが、これはコード上の分類ロジックの動作確認であり、
Production実データでの分布とは異なる可能性がある点を明記する
（当該ドキュメント自身も同じ注意書きを持つ）。

---

## 7. Funnel Join Readiness（Phase 7）

[knowledge-recommendation-analytics-contract.md](knowledge-recommendation-analytics-contract.md)
の内容は本監査時点でも変更されていない（既存イベント自体への変更は
PR #2384に含まれない）ため、fresh再確認の結果、以下は不変である。

| 既存イベント | join key | 状態 |
|---|---|---|
| `concierge_result_impression` | threadId/shrineId/resultSetId/recommendationRank | `recommendation_quality`と同じkey構成 |
| `shrine_detail_transition` | 同上 | 同上 |
| `shrine_decision` | shrineId/tid(threadId)/rank | join可能（key名の対応付けが必要） |
| `route_open` | shrineId/threadId | rank/resultSetIdなし（既知gap） |
| `visit_done` | shrineId/threadId | rank/resultSetIdなし（既知gap、本PRでは修正しない） |

**分類: `JOIN_READY_WITH_LIMITATIONS`**（`concierge_result_impression`/
`shrine_detail_transition`/`shrine_decision`はJOIN_READY、`route_open`/
`visit_done`はrank/resultSetId欠落によりJOIN_READY_WITH_LIMITATIONS）。

---

## 8. CTR Analysis Readiness（Phase 8）

- impressionは`concierge_result_impression`が分母として機能する（保有）
- detail transitionは`shrine_detail_transition`が対応する（保有）
- `knowledge_backing_class`でのsegment化は、4章の理由によりコード上は
  可能だが実データでの検証は未実施
- rank・hero/alternative区別（`position`）は両イベントに保有

**分類: `KNOWLEDGE_CTR_ANALYSIS_READY`（property・join keyの準備は完了。
ただし実データでの実行・検証は未実施、4章のAnalytics Read Access Gapに
依存）**。

---

## 9. Save Analysis Readiness（Phase 9）

- `shrine_decision`(action=save)は保有
- impressionとのjoinはthreadId/shrineIdで可能
- Knowledge classificationとのjoinは`recommendation_quality`イベント
  経由で可能（同じthreadId/shrineId/recommendationRankを保有）

**分類: `KNOWLEDGE_SAVE_ANALYSIS_READY`（8章と同様の限定付き）**。

---

## 10. Visit Intent Analysis Readiness（Phase 10）

`route_open`・`shrine_decision`(action=map_search)・`visit_done`は
いずれも存在するが、7章の通り`visit_done`にrank/resultSetIdが
ないため、「どの推薦順位由来の参拝か」の直接joinができない
（shrineId+threadIdでの間接joinのみ可能）。**本監査ではこのgapを
修正しない**（絶対禁止事項）。

**分類: `KNOWLEDGE_VISIT_INTENT_ANALYSIS_READY_WITH_LIMITATIONS`**。

---

## 11. Retry Analysis（Phase 11）

Retry/相談再入力専用イベントは、fresh再確認の結果も存在しない
（[cross-platform-event-contract.md](cross-platform-event-contract.md)
から変化なし）。

**分類: `RETRY_ANALYSIS_NOT_AVAILABLE`**。実装はしない。

---

## 12. Sample-size Limitation（Phase 12）

現在のevent数・session数・観測期間は、4章の理由により本監査では
取得できない。統計的判断基準（最小サンプルサイズ）も未定義のまま。

**分類: `SAMPLE_SIZE_THRESHOLD_NOT_DEFINED`**。数値を勝手に設定しない。

---

## 13. Baseline Comparison Readiness（Phase 13）

FULLY vs UNKNOWNでのCTR/Detail transition/Save/Visit intent比較は、
コード・join key・propertyの準備という意味では8-10章の通り整った状態
にあるが、4章のAnalytics Read Access GapとPhase 12のサンプルサイズ
未定義により、**現時点では実行不能**。

PARTIALLY/LEGACYは、[knowledge-recommendation-quality-baseline.md](knowledge-recommendation-quality-baseline.md)
のローカル実測で0件だったことから、Production実データでも件数が
少ない可能性が高く、無理に比較対象へ含めない。

---

## 14. Confounders（バイアス・交絡要因）（Phase 14）

Knowledge-backedと行動指標の差を将来比較する際、以下を交絡要因として
明記する。「Knowledgeが原因」と断定しないための整理であり、本監査では
これらの影響を測定・補正しない。

- recommendation rank（上位ほどCTR・Save率が高くなりやすい、Knowledge
  有無と独立の効果）
- hero vs alternative（`position`による表示形式の違い）
- consultation_axis（相談テーマによる基礎的な行動率の違い）
- shrine popularity（`popular_score`、Knowledge有無と相関しうる）
- location/distance（近い神社ほどvisit_doneが増えやすい）
- Knowledge coverage自体の選定バイアス（[post-batch16-knowledge-next-track-comparison.md](post-batch16-knowledge-next-track-comparison.md)
  で指摘した通り、Knowledge投入対象は「有名・良質なSourceが確認できる
  神社」に偏っている可能性がある）
- shrine familiarity（ユーザーが既に知っている神社かどうか）

---

## 15. Analytics Quality Guards（Phase 15）

4章のAnalytics Read Access Gapにより、duplicate event・missing event・
inconsistent threadId/shrineId・invalid rank・classification
missing・event version driftのいずれも実データでは確認できない。

コードレベルでの確認（範囲内）:

- `knowledge_backing_class`は`ShrineReasonProvenance.classification`
  由来のenum文字列のみ（`FULLY_KNOWLEDGE_BACKED`/
  `PARTIALLY_KNOWLEDGE_BACKED`/`LEGACY_BACKED`/`UNKNOWN`の4値以外は
  生成されない、`classify_provenance()`の戻り値型で保証）。
- `recommendation_reason_quality`が存在しない候補は
  `trackRecommendationQualityFromRecommendations()`がイベント送信
  自体をskipする（[knowledge-recommendation-analytics-properties-implementation.md](knowledge-recommendation-analytics-properties-implementation.md)
  テスト確認済み）ため、classification欠損イベントは送信されない設計。

---

## 16. Production Safety確認（Phase 16）

- Production DB write: 0件（read-only API呼び出しのみ）
- artificial Production recommendation POST: 実行していない
- event backfill: 実行していない
- 手動でのAnalytics変更: 実行していない
- Dashboard変更: 実行していない
- event schema変更: 実行していない（PR #2384の範囲を再確認しただけ）
- Ranking変更: 実行していない

---

## 17. Decision Outcome（Phase 17）

**`KNOWLEDGE_ANALYTICS_BASELINE_COLLECTION_READY`**

意味: Productionでpropertyのコード到達性（2章）をread-onlyに確認済み。
今後、自然流入トラフィックによってPostHogへイベントが蓄積されれば、
（4章のAnalytics Read Access Gapが別途解消された時点で）8-10章で
整理した分析が実行可能になる状態にある。現時点では「すでに十分な実
データがあり比較可能」（Option B）ではなく、「実データ未確認のまま
比較を試みる」（Option D、Blocked）でもない。

---

## 18. Next PR Candidates（Phase 18、優先順位はMother Shipへ）

A. **Baseline Report**: PostHogへのread-onlyアクセス手段（API Key
   発行等）を確立した上で、実際の`knowledge_backing_class`分布・
   FULLY vs UNKNOWN比較レポートを作成する。

B. **visit_done Attribution補完**: `visit_done`イベントへrank/
   resultSetIdを追加し、10章のgapを解消する。

C. **Dashboard / Query**: PostHog側でKnowledge分類×行動指標の
   dashboardを設計・実装する（4章のアクセス確立が前提）。

D. **Shadow Ranking Comparison**: [knowledge-recommendation-quality-audit.md](knowledge-recommendation-quality-audit.md)
   のPR候補（未実施のまま）。

E. **Reason Quality Improvement**: [knowledge-recommendation-quality-baseline.md](knowledge-recommendation-quality-baseline.md)
   6章のQuality Guard Metrics（generic wording率等）の実装。

---

## Final Classification

**`KNOWLEDGE_ANALYTICS_BASELINE_COLLECTION_READY`**

Production Frontend・Backendともに、Knowledge Analytics property
（PR #2384）を含む最新コミットで稼働中であることをread-onlyに直接
確認した（2章、healthzのrelease SHA一致）。一方、実際のイベント発火・
PostHogへの到達・実データでの分類分布・行動指標との相関は、artificial
Production recommendationの絶対禁止とPostHog read accessの不在により、
本監査の範囲では確認不能である（`PRODUCTION_ANALYTICS_READ_ACCESS_NOT_AVAILABLE`）。

Production DB writes = 0
Analytics behavior changes = 0
Recommendation behavior changes = 0
Ranking changes = 0
