import type { Purchase } from "expo-iap";

export const APPLE_PRODUCTS = [
  { id: "com.morietsu.kamimusubi.premium.monthly", label: "月額Premium", typeIOS: "auto-renewable-subscription" },
  { id: "com.morietsu.kamimusubi.pass.1day", label: "Premium Pass 1日", typeIOS: "non-renewing-subscription" },
  { id: "com.morietsu.kamimusubi.pass.7day", label: "Premium Pass 7日", typeIOS: "non-renewing-subscription" },
  { id: "com.morietsu.kamimusubi.pass.14day", label: "Premium Pass 14日", typeIOS: "non-renewing-subscription" },
] as const;

export type AppleProduct = (typeof APPLE_PRODUCTS)[number];
export type ApplePrices = Partial<Record<AppleProduct["id"], string>>;

type NativeStore = Pick<
  typeof import("expo-iap"),
  | "initConnection"
  | "fetchProducts"
  | "requestPurchase"
  | "finishTransaction"
  | "syncIOS"
  | "getAvailablePurchases"
  | "getAllTransactionsIOS"
  | "getPendingTransactionsIOS"
>;

export type StoreKitTransaction = {
  purchase: Purchase;
  finish: boolean;
};

export type ApplePurchaseFailureCode =
  | "store-unavailable"
  | "product-unavailable"
  | "verification"
  | "backend-unavailable"
  | "ownership"
  | "network"
  | "authentication"
  | "finish"
  | "refresh"
  | "purchase";

export class ApplePurchaseError extends Error {
  constructor(readonly reason: ApplePurchaseFailureCode) {
    super(reason);
    this.name = "ApplePurchaseError";
  }
}

export function storeKitErrorCode(error: unknown): string | undefined {
  if (typeof error !== "object" || error === null || !("code" in error)) return undefined;
  return typeof error.code === "string" ? error.code : undefined;
}

export function isApplePurchaseCancelled(error: unknown): boolean {
  return storeKitErrorCode(error) === "user-cancelled";
}

export function isApplePurchasePending(error: unknown): boolean {
  const code = storeKitErrorCode(error);
  return code === "deferred-payment" || code === "pending";
}

export function appleProductFor(purchase: Purchase): AppleProduct | undefined {
  return purchase.storeId === "apple" ? APPLE_PRODUCTS.find((product) => product.id === purchase.productId) : undefined;
}

function transactionKey(purchase: Purchase): string {
  const environment = "environmentIOS" in purchase ? purchase.environmentIOS : undefined;
  // Older StoreKit runtimes can omit the environment from the native metadata.
  return JSON.stringify([purchase.id, environment ?? purchase.purchaseToken]);
}

export function createAppleStoreKit(native: NativeStore) {
  return {
    async loadPrices(): Promise<ApplePrices> {
      const items = await native.fetchProducts({
        skus: APPLE_PRODUCTS.map((product) => product.id),
        type: "subs",
      });
      const prices: ApplePrices = {};
      for (const product of APPLE_PRODUCTS) {
        const item = items?.find(
          (candidate) =>
            candidate.id === product.id &&
            candidate.platform === "ios" &&
            candidate.type === "subs" &&
            candidate.typeIOS === product.typeIOS,
        );
        if (item?.displayPrice.trim()) prices[product.id] = item.displayPrice;
      }
      return prices;
    },
    async purchase(product: AppleProduct): Promise<StoreKitTransaction | null> {
      // The pinned iOS implementation returns the verified transaction for this request.
      const result = await native.requestPurchase({
        type: "subs",
        request: { apple: { sku: product.id, andDangerouslyFinishTransactionAutomatically: false } },
      });
      const purchase = (Array.isArray(result) ? result : result ? [result] : []).find(
        (candidate) => appleProductFor(candidate)?.id === product.id,
      );
      return purchase ? { purchase, finish: true } : null;
    },
    async restore(): Promise<StoreKitTransaction[]> {
      if (!(await native.syncIOS())) throw new ApplePurchaseError("store-unavailable");
      const [active, history, unfinished] = await Promise.all([
        native.getAvailablePurchases({
          onlyIncludeActiveItemsIOS: true,
          alsoPublishToEventListenerIOS: false,
        }),
        native.getAllTransactionsIOS(),
        native.getPendingTransactionsIOS(),
      ]);
      const transactions = new Map<string, StoreKitTransaction>();
      for (const purchase of active) {
        if (appleProductFor(purchase)?.typeIOS === "auto-renewable-subscription") {
          transactions.set(transactionKey(purchase), { purchase, finish: false });
        }
      }
      // Non-renewing subscriptions can have multiple past transactions for one product.
      // Resend the verified history so the backend can reconcile durations and revocations.
      for (const purchase of history) {
        if (appleProductFor(purchase)?.typeIOS === "non-renewing-subscription") {
          transactions.set(transactionKey(purchase), { purchase, finish: false });
        }
      }
      for (const purchase of unfinished) {
        if (appleProductFor(purchase)) transactions.set(transactionKey(purchase), { purchase, finish: true });
      }
      return [...transactions.values()].sort((a, b) => a.purchase.transactionDate - b.purchase.transactionDate);
    },
    async finish(purchase: Purchase) {
      await native.finishTransaction({ purchase, isConsumable: false });
    },
  };
}

export type AppleStoreKit = ReturnType<typeof createAppleStoreKit>;
let connection: Promise<AppleStoreKit> | undefined;

// Import the native module only on iOS. Keep one StoreKit connection per app runtime.
export async function openAppleStoreKit(
  platform: string,
  load: () => Promise<NativeStore> = () => import("expo-iap"),
): Promise<AppleStoreKit | null> {
  if (platform !== "ios") return null;
  connection ??= load()
    .then(async (native) => {
      if (!(await native.initConnection())) throw new ApplePurchaseError("store-unavailable");
      return createAppleStoreKit(native);
    })
    .catch(() => {
      connection = undefined;
      throw new ApplePurchaseError("store-unavailable");
    });
  return connection;
}
