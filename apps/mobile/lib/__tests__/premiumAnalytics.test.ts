import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// __DEV__ は Metro/React Native が注入するグローバルで、vitest実行環境には存在しないため定義する。
(globalThis as unknown as { __DEV__: boolean }).__DEV__ = false;

import { setAnalyticsProvider, type AnalyticsProvider } from "../analytics";
import type { BillingProvider } from "../billing";
import {
  trackPremiumActive,
  trackPremiumCheckoutFailed,
  trackPremiumCheckoutReturned,
  trackPremiumCheckoutStarted,
  trackPremiumScreenView,
  trackPremiumStatusView,
  trackPremiumUpgradeClick,
  type PremiumCheckoutFailureType,
} from "../premiumAnalytics";

describe("premiumAnalytics", () => {
  const trackSpy = vi.fn();

  beforeEach(() => {
    const customProvider: AnalyticsProvider = { track: trackSpy };
    setAnalyticsProvider(customProvider);
  });

  afterEach(() => {
    trackSpy.mockClear();
    setAnalyticsProvider(null);
  });

  it("trackPremiumScreenViewはsource/platformのみを送る", () => {
    trackPremiumScreenView();

    expect(trackSpy).toHaveBeenCalledWith("premium_screen_view", {
      source: "mobile_premium",
      platform: "mobile",
    });
  });

  it("trackPremiumStatusViewはplan/isActive/provider/sourceを送る(is_activeではなくisActive)", () => {
    trackPremiumStatusView({ plan: "premium", is_active: true, provider: "stripe" });

    expect(trackSpy).toHaveBeenCalledWith("premium_status_view", {
      plan: "premium",
      isActive: true,
      provider: "stripe",
      source: "mobile_premium",
    });
  });

  it("trackPremiumUpgradeClickはplan:freeとsourceを送る", () => {
    trackPremiumUpgradeClick();

    expect(trackSpy).toHaveBeenCalledWith("premium_upgrade_click", {
      plan: "free",
      source: "mobile_premium",
    });
  });

  it("trackPremiumCheckoutStartedはsourceのみを送り、session_id/checkout_urlを含まない", () => {
    trackPremiumCheckoutStarted();

    const [, payload] = trackSpy.mock.calls[0] as [string, Record<string, unknown>];
    expect(payload).toEqual({ source: "mobile_premium" });
    expect(payload).not.toHaveProperty("session_id");
    expect(payload).not.toHaveProperty("sessionId");
    expect(payload).not.toHaveProperty("checkout_url");
  });

  it.each(["unauthenticated", "invalid_response", "open_url_failed", "unknown"] as const)(
    "trackPremiumCheckoutFailedはfailureType=%sとsourceを送る",
    (failureType: PremiumCheckoutFailureType) => {
      trackPremiumCheckoutFailed(failureType);

      expect(trackSpy).toHaveBeenCalledWith("premium_checkout_failed", {
        source: "mobile_premium",
        failureType,
      });
    },
  );

  it("trackPremiumCheckoutReturnedはsourceのみを送る", () => {
    trackPremiumCheckoutReturned();

    expect(trackSpy).toHaveBeenCalledWith("premium_checkout_returned", {
      source: "mobile_premium",
    });
  });

  it("trackPremiumActiveはplan===premium かつ is_active===trueのときのみ送る", () => {
    trackPremiumActive({ plan: "premium", is_active: true, provider: "stripe" });

    expect(trackSpy).toHaveBeenCalledWith("premium_active", {
      plan: "premium",
      isActive: true,
      provider: "stripe",
      source: "mobile_premium",
    });
  });

  it.each([
    { plan: "free", is_active: true, provider: "stripe" },
    { plan: "premium", is_active: false, provider: "stripe" },
    { plan: "free", is_active: false, provider: "unknown" },
  ] as const)(
    "trackPremiumActiveはplan=%s is_active=%sでは送らない",
    (status: { plan: "free" | "premium"; is_active: boolean; provider: BillingProvider }) => {
      trackPremiumActive(status);

      expect(trackSpy).not.toHaveBeenCalled();
    },
  );
});
