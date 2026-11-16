import {
  ApplePurchaseError,
  appleProductFor,
  isApplePurchaseCancelled,
  isApplePurchasePending,
  storeKitErrorCode,
  type AppleProduct,
  type ApplePurchaseFailureCode,
  type AppleStoreKit,
  type StoreKitTransaction,
} from "./appleStoreKit";
import type { BillingStatus } from "./billing";
import { isHttpError, isUnauthenticatedError } from "./http";

export type ApplePurchaseState =
  | { kind: "idle" | "cancelled" | "pending" | "updated" | "nothing-to-restore" }
  | { kind: "purchasing" | "restoring" }
  | { kind: "error"; reason: ApplePurchaseFailureCode };

type Dependencies = {
  store: AppleStoreKit;
  getSession: () => Promise<string | null>;
  register: (jws: string) => Promise<BillingStatus>;
  refresh: () => Promise<BillingStatus | null>;
  publishStatus: (status: BillingStatus) => void;
  publishPurchaseState: (state: ApplePurchaseState) => void;
};

function purchaseError(error: unknown): ApplePurchaseFailureCode {
  if (error instanceof ApplePurchaseError) return error.reason;
  if (isUnauthenticatedError(error)) return "authentication";
  if (isHttpError(error)) {
    if (error.status === 409) return "ownership";
    if (error.status === 400) return "verification";
    if (error.status >= 500) return "backend-unavailable";
  }
  const code = storeKitErrorCode(error);
  if (error instanceof TypeError || code === "network-error") return "network";
  if (code === "item-unavailable" || code === "sku-not-found") return "product-unavailable";
  if (code === "iap-not-available" || code === "init-connection") return "store-unavailable";
  return "purchase";
}

export function createApplePurchaseFlow(deps: Dependencies) {
  let busy = false;

  async function registerTransaction(
    { purchase, finish }: StoreKitTransaction,
    assertSession: () => Promise<void>,
  ): Promise<ApplePurchaseFailureCode | undefined> {
    const product = appleProductFor(purchase);
    if (!product || purchase.purchaseState !== "purchased" || !purchase.purchaseToken?.trim()) {
      throw new ApplePurchaseError("verification");
    }
    await assertSession();
    const status = await deps.register(purchase.purchaseToken);
    await assertSession();
    deps.publishStatus(status);
    if (finish) {
      try {
        await deps.store.finish(purchase);
      } catch {
        return "finish";
      }
    }
    return undefined;
  }

  async function refresh(assertSession: () => Promise<void>) {
    await assertSession();
    const status = await deps.refresh();
    await assertSession();
    if (!status) throw new ApplePurchaseError("refresh");
    deps.publishStatus(status);
  }

  async function run(
    kind: "purchasing" | "restoring",
    work: (assertSession: () => Promise<void>) => Promise<ApplePurchaseState>,
  ) {
    if (busy) return;
    busy = true;
    deps.publishPurchaseState({ kind });
    try {
      const session = await deps.getSession();
      if (!session) throw new ApplePurchaseError("authentication");
      const assertSession = async () => {
        if ((await deps.getSession()) !== session) throw new ApplePurchaseError("authentication");
      };
      deps.publishPurchaseState(await work(assertSession));
    } catch (error) {
      deps.publishPurchaseState(
        isApplePurchaseCancelled(error)
          ? { kind: "cancelled" }
          : isApplePurchasePending(error)
            ? { kind: "pending" }
            : { kind: "error", reason: purchaseError(error) },
      );
    } finally {
      busy = false;
    }
  }

  return {
    purchase: (product: AppleProduct) =>
      run("purchasing", async (assertSession) => {
        const transaction = await deps.store.purchase(product);
        if (!transaction || transaction.purchase.purchaseState === "pending") return { kind: "pending" };
        const issue = await registerTransaction(transaction, assertSession);
        await refresh(assertSession);
        return issue ? { kind: "error", reason: issue } : { kind: "updated" };
      }),
    restore: () =>
      run("restoring", async (assertSession) => {
        const transactions = await deps.store.restore();
        let issue: ApplePurchaseFailureCode | undefined;
        for (const transaction of transactions) {
          try {
            const warning = await registerTransaction(transaction, assertSession);
            issue ??= warning;
          } catch (error) {
            const reason = purchaseError(error);
            if (reason === "authentication") throw error;
            issue ??= reason;
          }
        }
        await refresh(assertSession);
        if (issue) return { kind: "error", reason: issue };
        return { kind: transactions.length ? "updated" : "nothing-to-restore" };
      }),
  };
}
