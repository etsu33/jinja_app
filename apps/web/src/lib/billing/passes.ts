// apps/web/src/lib/billing/passes.ts
//
// 買い切りの旅行パス（自動更新しない）。値段は Stripe の Price と合わせる
// （backend: STRIPE_PASS_PRICE_ID_1D / 7D / 14D）。日数は backend の
// users/services/premium_pass.py の PASS_DEFINITIONS が正本。

export type BillingPassType = "1d" | "7d" | "14d";

export type BillingPass = {
  type: BillingPassType;
  /** 画面に出す名前 */
  label: string;
  /** 画面に出す値段（米ドル） */
  priceLabel: string;
};

export const BILLING_PASSES: readonly BillingPass[] = [
  { type: "1d", label: "1日パス", priceLabel: "$2.99" },
  { type: "7d", label: "7日パス", priceLabel: "$7.99" },
  { type: "14d", label: "14日パス", priceLabel: "$11.99" },
] as const;

const PASS_TYPES: ReadonlySet<string> = new Set(BILLING_PASSES.map((pass) => pass.type));

export function isBillingPassType(value: unknown): value is BillingPassType {
  return typeof value === "string" && PASS_TYPES.has(value);
}

/** Premium の有効期限を、日本時間の「2026年11月10日 15:30」の形にする。読めないときは null。 */
export function formatPassExpiry(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleString("ja-JP", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
