// アプリ内で「購入につながる要素」(購入ボタン・価格・外部決済ページへの遷移・購入を促す文言)を
// 出してよいかを決める。
//
// iOS v1 は App Store 審査ガイドライン 3.1.1 への対応として、iOS 内課金を持たず、
// 外部決済(Stripe Checkout)への導線も出さない。Web で登録済みの Premium の状態表示は残す。
// 米国ストアフロント向けの外部リンク(v1.1)や iOS 内課金(v2)を入れるときは、ここを起点に分岐を広げる。

export function canShowPurchaseUi(platformOS: string): boolean {
  return platformOS !== "ios";
}

export const PREMIUM_COPY = {
  // 全プラットフォーム共通(購入を促さない機能説明)
  screenSubtitle: "前回比較、深い振り返り、保存した相談の整理などをPremiumで利用できます。",
  // Free プランの補足。購入可能な環境では登録を案内し、iOS では状態の説明に留める。
  freeHelperWithPurchase: "前回比較、深い振り返り、保存した相談の整理などのPremium機能を利用できます。",
  freeHelperWithoutPurchase: "このアカウントは現在Freeプランです。",
  // マイページの Premium カード
  mypageDescriptionWithPurchase: "前回比較、深い振り返り、保存した相談の整理を使えるようにします。",
  mypageDescriptionWithoutPurchase: "Premiumの登録状況を確認できます。",
} as const;
