> **Status: Active**
>
> 本ドキュメントは、Premium / Monetization FunnelのEvent名を管理する正本文書である。
>
> 正確なPayload、Web / Mobileの送信差異の検証結果は`docs/audit/cross-platform-event-contract.md`、実装状況は関連するBackend・Frontend実装コードおよびテストを最終的な正本とする。

# Monetization Funnel Events

## 目的

Premiumへの転換Funnelにおいて、どのEventが送信されているかを一意に整理する。

---

## Web

| Event | 意味 |
|---|---|
| `comparison_preview` | 前回比較のプレビューを表示した |
| `upgrade_click` | アップグレード導線を押した |
| `checkout_started` | 決済を開始した |
| `checkout_success` | 決済が成功した |
| `premium_active` | Premiumが有効化された |

---

## Mobile

| Event | 意味 |
|---|---|
| `premium_screen_view` | Premium画面を表示した |
| `premium_status_view` | 現在のBilling状態を表示した |
| `premium_upgrade_click` | アップグレード導線を押した |
| `premium_checkout_started` | 決済を開始した |
| `premium_checkout_failed` | 決済起動に失敗した |
| `premium_checkout_returned` | 外部ブラウザ決済から復帰した |
| `premium_active` | Premiumが有効化された |

---

## Web / Mobileの既知の不整合

以下は`docs/audit/cross-platform-event-contract.md`で確認済みの未解消事項である。

- アップグレード導線: `upgrade_click`（Web）/ `premium_upgrade_click`（Mobile）で名称が異なる
- 決済開始: `checkout_started`（Web）/ `premium_checkout_started`（Mobile）で名称が異なる
- 決済成功・復帰: Webの`checkout_success`は決済成功シグナルだが、Mobileの`premium_checkout_returned`は外部ブラウザからの復帰検知であり、意味が非対称
- `premium_active`はWeb / Mobileでイベント名が一致しているが、Payload形状が異なる

これらの解消方針は本書では決定しない。詳細は`docs/audit/cross-platform-event-contract.md`を参照する。

---

## Funnel / KPI設計の背景

Card可視化からCheckout、Premium化までの詳細なFunnel定義、CTR計算式およびRetention KPIは`docs/analytics/premium-analytics-dashboard.md`（Archive）に設計背景として記録されている。

Archive文書のため、現行実装との整合はイベント名単位でのみ確認済みであり、KPI・Dashboard構成自体の実装状況は未確認である。

---

## 責務外

本書では以下を管理しない。

- Card CTR、Card Visibility Eventの契約
- 正確なPayload、Property
- Dashboard実装
- 実装コード、テストケース

---

## 関連ドキュメント

- `docs/analytics/README.md`
- `docs/analytics/premium-analytics-dashboard.md`
- `docs/audit/cross-platform-event-contract.md`
- `docs/product/monetization-flow-design.md`
- `docs/product/premium-experience.md`
- `docs/product/billing-paywall.md`

---

## 更新ルール

- 本書はPremium / Monetization FunnelのEvent一覧のみを管理する。
- Web / Mobileで新しいEventが追加または名称変更された場合は、本書を更新する。
- 正確なPayload、Property、KPI計算式および実装状況は本書で重複管理しない。
- Web / Mobileの命名統一方針が確定した場合は、本書の記載を実態に合わせて更新する。
- TODO、PR計画、実装進捗および作業履歴は本書へ記載しない。
