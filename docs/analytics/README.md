# KAMI MUSUBI Analytics Documents

## 目的

KAMI MUSUBIのイベント、Payload、KPI、Funnelおよび計測責務に関する文書の入口を管理する。

現行のイベント名、Payload、送信条件および集計挙動は、対応するAnalytics契約文書、実装コードおよびテストを最終的な正本とする。

---

## Active

| ドキュメント | 責務 |
| --- | --- |
| `monetization-funnel.md` | Premium / Monetization FunnelのEvent名を管理する |

---

## Reference

| ドキュメント | 責務 |
| --- | --- |
| `analytics-payload-audit.md` | Analytics Payload、Session IDおよび計測設計の背景を補足する |
| `recommendation-score-v3-design.md` | Recommendation Score v3のSignal、Weightおよび評価設計を補足する |
| `reflection-funnel-dashboard.md` | Reflection FunnelのKPI・PostHogダッシュボード設計を補足する |

---

## 役割境界

- Active文書は現行のEvent、Payload、KPIおよび計測契約を管理する
- Reference文書は設計背景、監査結果または評価方法を補足する
- 正確な物理挙動は関連するFrontend・Backend実装およびテストを最終的な正本とする
- Audit文書に記載された時点判断やTODOを現行契約として扱わない

---

## 更新ルール

- Event名またはPayloadを変更する場合は、実装と契約文書を同じPRで更新する
- 表示Eventと実行Eventを区別する
- WebとMobileで同じEvent名を使用する場合は意味とPayloadを一致させる
- Reference文書の未実装案を、実装済み仕様として扱わない
- 新しい文書を追加・移動した場合は本書を更新する
