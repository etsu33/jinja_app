> **Status: Decided（技術Policyとして固定）**
>
> 本ドキュメントは`docs/audit/mixed-confidence-policy-audit.md`（技術比較監査）の
> Phase 8「Mother Ship Decision」を確定した記録である。監査自体の正本は
> `docs/audit/mixed-confidence-policy-audit.md`を参照する。

# Mixed Confidence Policy Decision

## Phase 0 — Closure Base

| 項目 | 値 |
|---|---|
| PR #2300（Mixed Confidence Policy Audit） | MERGED（2026-08-08T02:07:27Z、merge commit `6b4a6107`） |
| develop HEAD | `6b4a6107cb2e7244c79f87bd840d4582c11d7f0a` |
| working tree | clean |
| `docs/audit/mixed-confidence-policy-audit.md` | develop反映済み |

本Phaseではコード変更を行っていない。

## Phase 1 — Mother Ship Technical Decision

`docs/audit/mixed-confidence-policy-audit.md` Phase 8の判断材料に基づき、以下を確定する。

- **FULL_SUPPRESSIONを現行Policyとして維持する。** `CONFIDENCE_MIXED`検出時、Deity Fact全体（高confidence Factを含む）をReasonから完全suppressする現行実装（`recommendation_reason_v4._build_fact()`）は変更しない。
- **HIGH_ONLYは採用しない。** 技術的にはSafe（監査Phase 6で確認済み）だが、現時点で採用へ進む理由（実害の規模）が不足していると判断する。
- **PRIMARY_ONLYは採用しない。** 監査Phase 6で指摘した通り、`role`を信頼度の代理として扱うことは「roleを勝手に信頼度として扱わない」という既存原則と構造的に矛盾するため、この案自体を採用対象から外す。
- **PER_FACT_RENDERINGは将来のContract変更候補として記録する。** 直ちに実装しないが、Information Utilizationの観点で最も有望な案として`docs/audit/mixed-confidence-policy-audit.md`のPhase 3/6分析を正本に据え置く。
- **阿佐ヶ谷神明宮の現行fallback挙動を正常系として維持する。** 天照大神(high)を含む全DeityがsuppressされGenericフォールバック文言（「〜に関する情報があります」）になる現在の出力は、Bugではなく設計通りの安全側動作として扱う。

Score/Ranking/Readiness/confidence値/Fact内容のいずれも変更していない。

## Phase 2 — Deferred Follow-up（PER_FACT_RENDERING再検討条件）

PER_FACT_RENDERINGの検討を再開する条件を以下に固定する。**現時点ではこれらの条件は満たされていないため、実装しない。**

| 条件 | 現状 |
|---|---|
| real mixed-confidence shrineがさらに複数件出現 | 現状1件のみ（阿佐ヶ谷神明宮）。Batch 4以降で増える可能性はあるが未確認 |
| 情報損失がRecommendation品質へ実害を出す | 現時点で定量的な実害（ユーザー影響）は未計測。Recommendation Reason Quality Auditの既存指標では検知範囲外 |
| Fact単位payloadへの変更範囲を監査できる | `fact.deity`のpublic契約（`recommendation_reason_v4_detail.fact.deity`）変更範囲の監査は未実施 |
| Web/API contractへの影響を分離できる | Frontend Adapter契約（`docs/product/recommendation-v4-frontend-adapter-contract.md`）への影響分離は未検討 |

4条件すべてが満たされた時点で、別Auditとして再着手を検討する。

## Phase 3 — Fact Integrity Closure（再確認済み）

develop HEAD `6b4a6107`時点で以下を再確認した。

| 項目 | 結果 |
|---|---|
| Evidence Gate real negative case確認済み | ○（`docs/audit/recommendation-fact-integrity-negative-pilot.md`、長太稲荷神社/鹿島神宮/阿佐ヶ谷神明宮の実データで確認済み） |
| Source-less Fact Usage Rate | 0%（Evidence Gate仕様上構造的に不可能。`test_fact_ready_without_source_is_still_unusable_regardless_of_confidence`等で担保） |
| Disputed Fact Usage Rate | 0%（同上。`test_disputed_high_confidence_is_still_unusable`で担保） |
| Tradition Misstatement Rate | 0/13（`docs/audit/tradition-output-contract-fix.md`のfix後、Fact-ready tradition History全件で再確認済み） |
| Mixed Confidenceは安全側に抑止 | ○（本ドキュメントPhase 1でFULL_SUPPRESSION維持を確定） |
| Candidate N+1解消済み | ○（PR #2297。`test_candidates_knowledge_lookup_does_not_scale_query_count_with_shrine_count`が現在もPASS） |
| query count定数構造維持 | ○（上記テストを本Closureで再実行し再確認） |
| Knowledge Coverage 21/100 | ○（`knowledge_coverage_report`で再実測、21.0%） |

バックエンド全1031テストを本Closure時点で再実行し、0 failureを確認した（9 skipはPostGIS/GDAL未導入起因のみ、以前から変化なし）。

## Phase 4 — Final Classification

`FACT_INTEGRITY_READY_WITH_LIMITATIONS`
+ `MIXED_CONFIDENCE_POLICY_CURRENT_SAFE`
+ `PER_FACT_RENDERING_DEFERRED`

Fact Integrityの構造的安全性（Evidence Gate、Tradition hedge floor、Mixed Confidence suppression、N+1解消）はすべて実データ・実測で再確認済みであり、既知の限界（`low`/`disputed`の実データ実例ゼロ、Knowledge Coverage 21/100、Mixed Confidence時の情報損失）を除けば安定している。

`READY_FOR_ROLLOUT`への昇格は、Batch 4以降のCoverage拡大とKnowledge Contractの成熟度次第であり、本Closureでは判断しない。

## 禁止事項の遵守

- コード変更なし
- confidence値変更なし
- 阿佐ヶ谷神明宮Fact書き換えなし
- Score/Ranking変更なし
- Source追加なし
- PER_FACT_RENDERINGの実装なし（Deferredとして記録のみ）

## Repository Changes

- `docs/audit/mixed-confidence-policy-decision.md`: 本ドキュメント（新規）
- 上記以外の変更なし
