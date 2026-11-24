# Mobile App

AI参拝ナビの **モバイル版（iOS / Android）** です。  
Expo Router で実装済みで、現在は **iOS リリース準備中**（App Store 審査対応）です。

---

## iOSホームの外観（2026-11-24承認）

ホーム限定で「Indigo & Gold」を適用する。`design/theme.ts` の `homeIndigo` を
`app/(tabs)/index.tsx` がiOSでのみ使用し、`appColors` / `appSemanticTheme` は維持する。
既存 `assets/icon.png` を使用し、背景の雲文様はホーム内の静的なViewで描く。
追加画像・ライブラリ・アニメーションは導入しない。和紙の写真テクスチャは未適用。
タブバーはiOSホーム選択中だけ深藍・淡金とし、他画面では従来の色へ戻す。
Web（Expo Webを含む）・Androidの外観、相談ペイロード、検索計測、業務ロジックは維持する。
共通Buttonの任意 `textStyle` はホームの検索ボタンで使用し、既定の見た目を変えない。

設定アイコンはアプリコードに存在しない。Expo Go上で表示される青い歯車は
開発ツール側の表示として扱い、アプリに新しい設定導線は追加しない。

検証: TypeScript、モバイル既存テスト、変更TS/TSXの限定Lint、iPhone 16e / iOS 26.1。
ホーム表示のレビュー後に他画面への展開を判断する。現段階では他画面へ展開しない。

## 現在のステータス

- 実装：✅ 実装済み（Expo Router / 既存 Backend API に接続）
- Git 管理：✅ 対象（`apps/mobile`）
- リリース：iOS リリース準備中
- iOS 内課金：✅ 実装済み（StoreKit 2 / expo-iap。後述の「iOS Premium purchases」を参照）

---

## 方針（暫定）

- Web（Next.js）で MVP を完成させることを最優先
- ユーザー反応・機能安定後にモバイル展開を判断
- 初期は **Expo + API 共有（Backend 共通）** を前提とする

---

## 着手時の予定スタック

- Expo
- React Native
- Expo Router
- 既存 Backend API（`/api/*`）

---

## 開発を開始するタイミングでやること

- `src/` を gitignore から外す
- 本 README を **実装前提の内容に更新**
- 環境変数・API 接続方針を明記
- Web との責務分離（UI / UX 差分）を整理

---

## 関連ドキュメント

- プロジェクト全体の概要  
  - リポジトリルートの `README.md`
- アーキテクチャ / 認証 / API 設計  
  - `docs/` 配下を参照

---

> NOTE  
> この README は **「今は触らなくていい」ことを明確にするためのもの**です。  
> 実装が始まったら、迷わず書き換えてください。

### iOS Premium purchases

The Premium screen uses Expo IAP 6.4.4 with StoreKit 2. The module autolinks
on iOS and is excluded from Android autolinking. Use a new native development
build or TestFlight on a physical iPhone. Expo Go cannot run this integration.
Android retains the existing purchase flow.

Configure these products in App Store Connect for `com.morietsu.kamimusubi`:

- `com.morietsu.kamimusubi.premium.monthly` as an auto-renewable monthly subscription.
- `com.morietsu.kamimusubi.pass.1day`, `com.morietsu.kamimusubi.pass.7day`, and
  `com.morietsu.kamimusubi.pass.14day` as Non-Renewing Subscriptions.
  Pass duration is applied by the backend.

For App Review and TestFlight, use a backend with StoreKit verification
configured and Sandbox enabled. On a device, verify the localized product prices,
purchase each product, cancel the purchase sheet, and confirm the Premium status
from the backend. Test Restore Purchases on the same KAMI MUSUBI account, including
a purchase whose backend registration was temporarily unavailable.

The app sends the verified transaction JWS to the existing authenticated
billing API. It finishes the StoreKit transaction only after the API accepts it.
If a purchase is pending, registration fails, or finishing fails, Restore
Purchases can resend unfinished transactions. Restore also resends active monthly
entitlements and the StoreKit transaction history for all three non-renewing
Passes, including previously finished transactions. The backend applies Pass durations
and returns the billing status for the signed-in account. The client finishes only unfinished transactions after server acceptance,
using `isConsumable: false` for both product types.
