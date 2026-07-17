> **Status: Active**
>
> 本ドキュメントは、Billing状態とPaywall表示の判定原則を管理する正本文書である。
>
> 正確なAPI Endpoint、レスポンスField、判定ロジックの実装およびテストケースは、関連するBackend・Frontend実装コードおよびテストを最終的な正本とする。

# Billing / Paywall 判定原則

## 目的

- Billing状態（課金プランの種別と有効性）とPaywall表示の判定原則を一意に定義する
- 「Premiumなのに利用が止まる」「Freeなのに制限されない」といった体験上の事故を防ぐ
- 判定の最終的な責任がサーバー側にあることをProduct / Backend / Frontendで共有する

---

## 真実の所在

利用可否の最終判断はサーバー側で行う。

Frontendは、サーバーから受け取った以下の情報をもとに表示のみを行う。

- 相談を送信するAPIの応答に含まれる利用制限に関する情報
- Billing状態の照会結果によるPremium判定

正確なAPI Endpoint、レスポンスFieldおよび判定処理の実装は、関連するBackend実装とテストを正本とする。

---

## 判定原則

### 1. Premium優先の原則

Billingが有効なPremiumユーザーには、いかなる場合もPaywallを表示しない。

Premiumユーザーの利用を妨げないことを最優先とする。

### 2. Free制限の原則

Freeユーザーは、当日の利用回数が上限に達するまで利用できる。

上限に達した場合は、課金を促す案内とともにPaywallを表示する。

### 3. Billing表示未確定時の原則

Billing状態が未取得またはエラーの場合、FrontendはPremiumユーザーを誤ってPaywall表示で遮断しない。

ただし、相談送信などの実際の利用可否は、常にBackendの判定結果に従う。

Frontend側の未確定状態を理由に、Backendの利用制限を回避できる設計にはしない。

### 4. 判定ロジックの一元化

Premium優先、Free制限および未確定時の判定ロジックは、画面ごとに重複実装しない。

共通の実装に集約し、画面間で判定結果が食い違わない状態を保つ。

正確な実装方式は、関連するFrontend実装とテストを正本とする。

---

## Concierge APIとの関係

利用制限の判定は、相談を送信するAPIの応答を経由して行う。

Billing状態の確認だけで送信可否を判断せず、相談APIを通じた判定を優先する。

正確なAPI契約、Endpointおよびレスポンス構造は、`docs/core/concierge-spec.md`および関連するBackend実装とテストを正本とする。

---

## 非対応

以下は、現時点でBilling / Paywall体験の対象としない。

- 無料残回数の常時表示
- Billing状態のみで送信可否を判断する制御（相談APIを経由しない判定）
- Premium trial・grace periodのUI分岐

これらを実装する場合は、別途本書を更新して対象へ追加する。

---

## 責務境界

### Product

Productでは以下を管理する。

- Billing状態とPaywall表示の判定原則
- Premium優先、Free制限および未確定時の体験方針
- 判定ロジックを画面間で一元化する方針
- Billing / Paywall体験の対象外事項

### Core

以下は`docs/core/`配下の正本文書を参照する。

- 認証、権限およびBilling判定を含むBackendのリクエスト処理構造
- Concierge APIの基本契約

### Backend実装

以下は関連するBackend実装とテストを正本とする。

- API Endpoint
- レスポンスField
- 判定処理の物理実装
- Billing状態の保存・更新処理

### Frontend実装

以下は関連するFrontend実装とテストを正本とする。

- 判定ロジックの共通化実装（Hook / Util）
- 画面ごとのPaywall表示
- Loading / Error状態の扱い

### テスト

正確なテストケースは、関連するBackend・Frontendのテストを正本とする。

---

## 責務外

本書では以下を管理しない。

- API Endpoint
- レスポンスField
- 判定ロジックの実装コード
- テストケース一覧
- 実装進捗
- PR計画
- 作業履歴

---

## 関連ドキュメント

- `docs/product/README.md`
- `docs/product/premium-experience.md`
- `docs/product/pricing.md`
- `docs/product/monetization-flow-design.md`
- `docs/core/concierge-spec.md`
- `docs/core/authentication-flow.md`

---

## 更新ルール

- 本書はBilling状態とPaywall表示の判定原則を管理する。
- Premium優先、Free制限または未確定時の判定方針が変更された場合は、本書を更新する。
- API Endpoint、レスポンスField、判定ロジックの実装コードおよびテストケースは本書で重複管理しない。
- 物理実装のみを変更した場合は、本書の判定原則への影響を確認する。
- 非対応として明示した事項を実装する場合は、本書の対象範囲を更新する。
- TODO、PR計画、実装進捗および作業履歴は本書へ記載しない。
