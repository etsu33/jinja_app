> **Status: Active**
>
> 本ドキュメントは、`docs/analytics`配下の文書構成、分類および読む順番を管理する正本文書である。

# KAMI MUSUBI Analytics Documents

## 目的

KAMI MUSUBIのイベント、Payload、KPI、Funnelおよび計測責務に関する文書の入口を管理する。

現行のイベント名、Payload、送信条件および集計挙動は、対応するAnalytics契約文書、実装コードおよびテストを最終的な正本とする。

---

## Active

| ドキュメント | 責務 |
| --- | --- |
| `action-suggestion-funnel.md` | Action Suggestion関連Event（PostHog view計測 / Backend `ActionEvent`）の現状を管理する |
| `monetization-funnel.md` | Premium / Monetization FunnelのEvent名を管理する |
| `save-premium-correlation.md` | 保存行動とPremium転換に関するEvent間の相関分析の読み方を管理する |
| `recommendation-score-v2-current-design.md` | Recommendation Score v2の現行スコア式・重みおよびPostHog計測項目の対応関係を管理する |
| `user-state-profile.md` | Recommendation Score v2が用いるUser State Profileの定義を管理する |
| `shrine-meaning-profile.md` | Recommendation Score v2が用いるShrine Meaning Profileの定義を管理する |
| `context-profile.md` | Recommendation Score v2が用いるContext Profileの定義を管理する |
| `behavior-profile.md` | Recommendation Score v2が用いるBehavior Profile（行動シグナル）の定義を管理する |

---

## Reference

| ドキュメント | 責務 |
| --- | --- |
| `analytics-payload-audit.md` | Analytics Payload、Session IDおよび計測設計の背景を補足する |
| `recommendation-score-v3-design.md` | Recommendation Score v3のSignal、Weightおよび評価設計を補足する |
| `reflection-funnel-dashboard.md` | Reflection FunnelのKPI・PostHogダッシュボード設計を補足する |
| `recommendation-score-v2.md` | Recommendation Score v2の4 Profile統合設計の背景を補足する |
| `recommendation-score-v2-foundation.md` | Recommendation Score v2の設計思想・4レイヤー構成の背景を補足する |
| `recommendation-quality-analytics-boundary.md` | `quality` payloadに関するBackend / Web / PostHog / Mobile間の責務境界の設計背景を補足する |
| `history-theme-dashboard.md` | historyTheme別Dashboardの見方に関する設計背景を補足する |
| `history-theme-premium-dashboard.md` | historyTheme × Premium Dashboardの見方に関する設計背景を補足する |
| `reflection-next-recommendation-design.md` | Reflectionから次回推薦への接続に関する設計背景を補足する |
| `consultation-axis-analytics-summary.md` | consultationAxis別の保存・参拝・課金導線の行動差分を確認する集計方針を補足する |

---

## Archive

| ドキュメント | 役割 |
| --- | --- |
| `analytics-card-events.md` | Card単位Analytics Eventの初期設計・監査・移行計画（現行実装は`cardEvents.ts`等へ委譲済み） |
| `card-ctr-aggregation.md` | Card CTR集計の初期設計（現行実装は関連コードへ委譲済み） |
| `premium-analytics-dashboard.md` | Premium Analytics Dashboardの初期設計（現行はAnalytics契約文書へ委譲済み） |
| `shrine-detail-analytics-route.md` | Shrine Detail Analytics Routeの初期設計（現行実装は関連コードへ委譲済み） |
| `consultation-axis-discovery.md` | consultation_axis候補発見のための時点監査 |
| `meaning-context-unused-audit.md` | `meaningContext`の利用実態を確認した時点監査 |
| `recommendation-funnel-analysis.md` | Recommendation Score v2重み調整前の行動ファネル時点監査 |
| `recommendation-output-quality-review.md` | Recommendation Score v2出力品質の時点レビュー |
| `recommendation-output-snapshot.md` | Recommendation Score v2実出力の時点スナップショット |
| `recommendation-score-v2-output-funnel-audit.md` | Recommendation Score v2の実出力と行動ファネルを接続した時点監査 |
| `recommendation-score-v2-quality-audit.md` | Recommendation Score v2の返答品質を確認した時点監査 |
| `score-v2-behavior-correlation-audit.md` | score_v2と行動相関を確認した時点監査 |
| `score-v2-behavior-cvr-sql.md` | score_v2と行動率のSQL方針を記録した時点監査 |
| `score-v2-measurement-source-audit.md` | score_v2と行動相関の実測データ取得元を確認した時点監査 |
| `score-v2-production-snapshot.md` | score_v2の本番データ保存状況を確認した時点スナップショット |

---

## 役割境界

- Active文書は現行のEvent、Payload、KPIおよび計測契約を管理する
- Reference文書は設計背景、監査結果または評価方法を補足する
- Archive文書は履歴保存を目的とし、現行の計測契約判断には使用しない
- 正確な物理挙動は関連するFrontend・Backend実装およびテストを最終的な正本とする
- Audit文書に記載された時点判断やTODOを現行契約として扱わない

---

## 更新ルール

- Event名またはPayloadを変更する場合は、実装と契約文書を同じPRで更新する
- 表示Eventと実行Eventを区別する
- WebとMobileで同じEvent名を使用する場合は意味とPayloadを一致させる
- Reference文書の未実装案を、実装済み仕様として扱わない
- 文書の分類（Active / Reference / Archive）が変更された場合は、対象文書のStatusヘッダと本書を同じPRで更新する
- 新しい文書を追加・移動した場合は本書を更新する
