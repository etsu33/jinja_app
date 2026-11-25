# Mobile App

AI参拝ナビの **モバイル版（iOS / Android）** です。  
Expo Router で実装済みで、現在は **iOS リリース準備中**（App Store 審査対応）です。

---

## iOSの外観（2026-11-24承認）

ホームの実画面承認後、既存iOS全画面へ「Indigo & Gold」を展開する。
色定義は `design/theme.ts`、iOSでの選択は `design/platformTheme.ts` が担当する。
Web（Expo Webを含む）・Androidは既存のLight Themeの実体を使用する。
`appColors` / `appSemanticTheme` の元の値とSemanticキー契約は維持する。

- iOSの背景・カードは深藍、文字は明色、主要CTA・選択中タブは淡金。
- 入力枠・選択線はコントラストを確保し、成功・注意・エラーは区別できる色を保つ。
- Root StackのヘッダーとStatusBar、全タブ、認証・条件入力・履歴・神社詳細・Premium・御朱印の既存UIを同じテーマで表示する。
- 読み物の背景は単色とし、四隅の雲文様はホームに保持する。追加画像・ライブラリは導入しない。和紙の写真テクスチャは未適用。
- Splashは既存ロゴと藍のグラデーションに揃え、保持時間・フェード・Reduce Motion処理は維持する。
- 共通ButtonのiOS通常サイズは文字量に応じて伸びる。入力欄にはiOS用キーボード色・選択色だけを補う。

全画面は既存の部品・構造を維持する。API、認証、推薦、DB、課金、保存・計測、ルーティングの業務契約は変更しない。
`vermilion` / `vermilionDeep` は既存の主CTA参照を維持する互換キーとして、iOSでは淡金を割り当てる。

設定アイコンはアプリコードに存在しない。Expo Goの青い歯車は開発ツール側の表示として扱い、設定導線を追加しない。

検証はNode 22.23.4のTypeScript/Vitest、変更TS/TSXの限定Lint、Webトークン契約、iPhone 16e / iOS 26.1の表示比較で行う。
既存モバイルにはLintスクリプトがない。限定Lintは既存24指摘が残るが、変更前後を照合して新規指摘0件を確認する。
2026-11-25にXCTestで主要導線・キーボード操作・AX5のホーム操作と、19ルートの表示状態の自動アクセシビリティ監査を確認した。
実機VoiceOver、全データ状態、実ログイン・購入・登録等のE2Eは未完了。修正内容・適用状態・未確認項目は[検証記録](../../docs/mobile/ios-ui-runtime-qa.md)を参照。

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
