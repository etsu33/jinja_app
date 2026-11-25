import type { PurchaseIOS, QueryField } from "expo-iap";
import { readFileSync } from "node:fs";
import { describe, expect, it, vi } from "vitest";

import { APPLE_PRODUCTS, createAppleStoreKit, openAppleStoreKit } from "../appleStoreKit";
import { createApplePurchaseFlow } from "../applePurchaseFlow";
import { isPremiumStatus, registerAppleTransaction, type BillingStatus } from "../billing";
import { HttpError, postAuth } from "../http";

vi.mock("../http", async (importOriginal) => {
  const original = await importOriginal<typeof import("../http")>();
  return { ...original, postAuth: vi.fn() };
});
vi.mock("../authTokens", () => ({}));

const [monthly, oneDay, sevenDays, fourteenDays] = APPLE_PRODUCTS;

const backendPremium: BillingStatus = {
  plan: "premium",
  is_active: true,
  provider: "stripe",
  current_period_end: null,
  trial_ends_at: null,
  cancel_at_period_end: false,
};
const backendFree: BillingStatus = { ...backendPremium, plan: "free", is_active: false };

function purchase(productId: string, id = "t1", transactionDate = 1): PurchaseIOS {
  return {
    id,
    transactionId: id,
    productId,
    transactionDate,
    isAutoRenewing: false,
    quantity: 1,
    store: "apple",
    storeId: "apple",
    purchaseState: "purchased",
    purchaseToken: `header-${id}.payload.signature`,
  };
}

function fixture() {
  const native = {
    initConnection: vi.fn().mockResolvedValue(true),
    fetchProducts: vi.fn<QueryField<"fetchProducts">>().mockResolvedValue([
      { id: monthly.id, platform: "ios", type: "subs", typeIOS: "auto-renewable-subscription", displayPrice: "€8,99" },
      { id: oneDay.id, platform: "ios", type: "subs", typeIOS: "non-renewing-subscription", displayPrice: "95円" },
      { id: sevenDays.id, platform: "ios", type: "subs", typeIOS: "non-renewing-subscription", displayPrice: "¥300" },
      {
        id: fourteenDays.id,
        platform: "ios",
        type: "subs",
        typeIOS: "non-renewing-subscription",
        displayPrice: "¥500",
      },
    ] as Awaited<ReturnType<QueryField<"fetchProducts">>>),
    requestPurchase: vi.fn().mockResolvedValue(purchase(monthly.id)),
    finishTransaction: vi.fn().mockResolvedValue(undefined),
    syncIOS: vi.fn().mockResolvedValue(true),
    getAvailablePurchases: vi.fn().mockResolvedValue([]),
    getAllTransactionsIOS: vi.fn().mockResolvedValue([]),
    getPendingTransactionsIOS: vi.fn().mockResolvedValue([]),
  };
  const store = createAppleStoreKit(native);
  const publishStatus = vi.fn();
  const publishPurchaseState = vi.fn();
  const refresh = vi.fn().mockResolvedValue(backendPremium);
  const getSession = vi.fn().mockResolvedValue("session");
  vi.mocked(postAuth).mockResolvedValue(backendPremium);
  const flow = createApplePurchaseFlow({
    store,
    register: registerAppleTransaction,
    refresh,
    getSession,
    publishStatus,
    publishPurchaseState,
  });
  return { native, store, flow, refresh, getSession, publishStatus, publishPurchaseState };
}

describe("iOS products and platform scope", () => {
  it("loads all backend catalog IDs and shows only localized prices for matching StoreKit products", async () => {
    const { native, store } = fixture();
    const ids = [
      "com.morietsu.kamimusubi.premium.monthly",
      "com.morietsu.kamimusubi.pass.1day",
      "com.morietsu.kamimusubi.pass.7day",
      "com.morietsu.kamimusubi.pass.14day",
    ];
    expect(APPLE_PRODUCTS.map((product) => product.id)).toEqual(ids);
    expect(await store.loadPrices()).toEqual({
      [monthly.id]: "€8,99",
      [oneDay.id]: "95円",
      [sevenDays.id]: "¥300",
      [fourteenDays.id]: "¥500",
    });
    expect(native.fetchProducts).toHaveBeenCalledWith({ skus: ids, type: "subs" });
  });

  it.each([oneDay, sevenDays, fourteenDays])(
    "hides a Pass SKU exposed as the wrong StoreKit type for $id",
    async (product) => {
      const { native, store } = fixture();
      native.fetchProducts.mockResolvedValueOnce([
        { id: product.id, platform: "ios", type: "in-app", typeIOS: "consumable", displayPrice: "¥100" },
        { id: product.id, platform: "ios", type: "subs", typeIOS: "auto-renewable-subscription", displayPrice: "¥200" },
      ] as Awaited<ReturnType<QueryField<"fetchProducts">>>);
      expect(await store.loadPrices()).toEqual({});
    },
  );

  it.each(["android", "web"])("does not load the native module on %s", async (platform) => {
    const load = vi.fn();
    expect(await openAppleStoreKit(platform, load)).toBeNull();
    expect(load).not.toHaveBeenCalled();
  });

  it("routes iOS to StoreKit and guards the external checkout entry point", () => {
    const screen = readFileSync(new URL("../../app/premium/index.tsx", import.meta.url), "utf8");
    expect(screen).toMatch(/const isIOS = Platform\.OS === "ios"/);
    expect(screen).toMatch(/\{isIOS \? <ApplePurchaseSection/);
    expect(screen).toMatch(/if \(isIOS \|\| checkoutInFlightRef\.current\) return;/);
    expect(screen).toContain("await Linking.openURL(session.checkout_url);");
  });
});

describe("iOS purchase lifecycle", () => {
  it.each([monthly, oneDay, sevenDays, fourteenDays])("registers only the signed JWS for $id", async (product) => {
    const { native, flow, refresh, publishStatus, publishPurchaseState } = fixture();
    const transaction = purchase(product.id);
    native.requestPurchase.mockResolvedValue(transaction);
    await flow.purchase(product);

    expect(native.requestPurchase).toHaveBeenCalledWith({
      type: "subs",
      request: { apple: { sku: product.id, andDangerouslyFinishTransactionAutomatically: false } },
    });
    expect(postAuth).toHaveBeenCalledExactlyOnceWith("/billings/apple/transactions/", {
      signed_transaction: transaction.purchaseToken,
    });
    expect(native.finishTransaction).toHaveBeenCalledWith({
      purchase: transaction,
      isConsumable: false,
    });
    expect(postAuth).toHaveBeenCalledBefore(native.finishTransaction);
    expect(native.finishTransaction).toHaveBeenCalledBefore(refresh);
    expect(publishStatus).toHaveBeenLastCalledWith(backendPremium);
    expect(publishPurchaseState).toHaveBeenLastCalledWith({ kind: "updated" });
  });

  it.each([
    [new HttpError(400, "rejected"), "verification"],
    [new HttpError(409, "conflict"), "ownership"],
    [new HttpError(503, "unavailable"), "backend-unavailable"],
    [new TypeError("network"), "network"],
  ])("leaves purchases recoverable when the backend fails with %s", async (failure, reason) => {
    const { native, flow, refresh, publishStatus, publishPurchaseState } = fixture();
    vi.mocked(postAuth).mockRejectedValueOnce(failure);
    await flow.purchase(monthly);

    expect(native.finishTransaction).not.toHaveBeenCalled();
    expect(refresh).not.toHaveBeenCalled();
    expect(publishStatus).not.toHaveBeenCalled();
    expect(publishPurchaseState).toHaveBeenLastCalledWith({ kind: "error", reason });
  });

  it("shows Free when the backend reports no Premium despite StoreKit success", async () => {
    const { flow, refresh, publishStatus } = fixture();
    vi.mocked(postAuth).mockResolvedValueOnce(backendFree);
    refresh.mockResolvedValueOnce(backendFree);
    await flow.purchase(monthly);

    expect(publishStatus).toHaveBeenCalledTimes(2);
    expect(publishStatus.mock.calls.every(([status]) => !isPremiumStatus(status))).toBe(true);
  });

  it("does not finish when the API returns an invalid success response", async () => {
    const { native, flow, publishStatus } = fixture();
    vi.mocked(postAuth).mockResolvedValueOnce({});
    await flow.purchase(monthly);
    expect(native.finishTransaction).not.toHaveBeenCalled();
    expect(publishStatus).not.toHaveBeenCalled();
  });

  it("can retry completion when finishing fails after server acceptance", async () => {
    const { native, flow, refresh, publishPurchaseState } = fixture();
    native.finishTransaction.mockRejectedValueOnce(new Error("store temporarily unavailable"));
    await flow.purchase(monthly);
    expect(refresh).toHaveBeenCalled();
    expect(publishPurchaseState).toHaveBeenLastCalledWith({ kind: "error", reason: "finish" });
  });

  it("does not register delayed purchases under a changed login session", async () => {
    const { native, flow, getSession, publishPurchaseState } = fixture();
    getSession.mockResolvedValueOnce("initial-account").mockResolvedValueOnce("different-account");
    await flow.purchase(monthly);

    expect(postAuth).not.toHaveBeenCalled();
    expect(native.finishTransaction).not.toHaveBeenCalled();
    expect(publishPurchaseState).toHaveBeenLastCalledWith({ kind: "error", reason: "authentication" });
  });

  it.each([
    ["user-cancelled", "cancelled"],
    ["deferred-payment", "pending"],
  ])("handles %s without a destructive error", async (code, kind) => {
    const { native, flow, publishPurchaseState } = fixture();
    native.requestPurchase.mockRejectedValueOnce({ code });
    await flow.purchase(monthly);

    expect(publishPurchaseState).toHaveBeenLastCalledWith({ kind });
    expect(postAuth).not.toHaveBeenCalled();
  });

  it("blocks duplicate purchase or restore taps during an operation", async () => {
    const { native, flow } = fixture();
    let complete!: (result: PurchaseIOS) => void;
    native.requestPurchase.mockReturnValueOnce(
      new Promise((resolve) => {
        complete = resolve;
      }),
    );
    const inFlight = flow.purchase(monthly);
    await flow.purchase(oneDay);
    await flow.restore();
    expect(native.requestPurchase).toHaveBeenCalledTimes(1);
    expect(native.syncIOS).not.toHaveBeenCalled();
    complete(purchase(monthly.id));
    await inFlight;
  });

  it("restores verified active and unfinished transactions once each and refreshes billing", async () => {
    const { native, flow, refresh, publishPurchaseState } = fixture();
    const finished = purchase(monthly.id, "subscription", 2);
    const unfinished = purchase(sevenDays.id, "pass", 1);
    native.getAvailablePurchases.mockResolvedValueOnce([finished, unfinished, purchase("unrelated", "other")]);
    native.getAllTransactionsIOS.mockResolvedValueOnce([finished, unfinished]);
    native.getPendingTransactionsIOS.mockResolvedValueOnce([unfinished]);
    await flow.restore();

    expect(native.syncIOS).toHaveBeenCalledTimes(1);
    expect(native.getAvailablePurchases).toHaveBeenCalledWith({
      onlyIncludeActiveItemsIOS: true,
      alsoPublishToEventListenerIOS: false,
    });
    expect(native.getAllTransactionsIOS).toHaveBeenCalledTimes(1);
    expect(postAuth).toHaveBeenCalledTimes(2);
    expect(postAuth).toHaveBeenNthCalledWith(1, "/billings/apple/transactions/", {
      signed_transaction: unfinished.purchaseToken,
    });
    expect(postAuth).toHaveBeenNthCalledWith(2, "/billings/apple/transactions/", {
      signed_transaction: finished.purchaseToken,
    });
    expect(native.finishTransaction).toHaveBeenCalledExactlyOnceWith({ purchase: unfinished, isConsumable: false });
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(publishPurchaseState).toHaveBeenLastCalledWith({ kind: "updated" });
  });

  it.each([oneDay, sevenDays, fourteenDays])("restores completed Pass history for $id", async (product) => {
    const { native, flow, refresh, publishStatus } = fixture();
    const first = purchase(product.id, "earlier", 1);
    const second = purchase(product.id, "later", 2);
    native.getAvailablePurchases.mockResolvedValueOnce([second]);
    native.getAllTransactionsIOS.mockResolvedValueOnce([
      second,
      purchase(monthly.id, "historical-monthly"),
      first,
      purchase("unrelated", "other"),
    ]);
    refresh.mockResolvedValueOnce(backendFree);
    vi.mocked(postAuth).mockResolvedValue(backendFree);

    await flow.restore();

    expect(postAuth).toHaveBeenCalledTimes(2);
    expect(postAuth).toHaveBeenNthCalledWith(1, "/billings/apple/transactions/", {
      signed_transaction: first.purchaseToken,
    });
    expect(postAuth).toHaveBeenNthCalledWith(2, "/billings/apple/transactions/", {
      signed_transaction: second.purchaseToken,
    });
    expect(native.finishTransaction).not.toHaveBeenCalled();
    expect(publishStatus).toHaveBeenLastCalledWith(backendFree);
  });

  it("preserves both Apple environments when restore returns the same transaction ID", async () => {
    const { native, flow } = fixture();
    const production = { ...purchase(monthly.id), environmentIOS: "Production" };
    const sandbox = { ...production, environmentIOS: "Sandbox", purchaseToken: "sandbox.receipt.jws" };
    native.getAvailablePurchases.mockResolvedValueOnce([production, sandbox]);

    await flow.restore();

    expect(postAuth).toHaveBeenCalledTimes(2);
    expect(native.finishTransaction).not.toHaveBeenCalled();
  });
});
