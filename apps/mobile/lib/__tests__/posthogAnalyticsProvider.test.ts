import { afterEach, describe, expect, it, vi } from "vitest";

// __DEV__ は Metro/React Native が注入するグローバルで、vitest実行環境には存在しないため定義する。
(globalThis as unknown as { __DEV__: boolean }).__DEV__ = false;

vi.mock("@react-native-async-storage/async-storage", () => ({
  default: { getItem: vi.fn(), setItem: vi.fn() },
}));

const captureMock = vi.fn();
const postHogConstructorMock = vi.fn();

vi.mock("posthog-react-native", () => ({
  default: class MockPostHog {
    constructor(apiKey: string, options: unknown) {
      postHogConstructorMock(apiKey, options);
    }
    capture(eventName: string, properties: unknown): void {
      captureMock(eventName, properties);
    }
  },
}));

import { setAnalyticsProvider } from "../analytics";
import { PostHogAnalyticsProvider } from "../posthogAnalyticsProvider";

describe("PostHogAnalyticsProvider", () => {
  afterEach(() => {
    captureMock.mockClear();
    postHogConstructorMock.mockClear();
  });

  it("track()はeventNameとpayloadをそのままcapture()へ渡す", () => {
    const provider = new PostHogAnalyticsProvider("phc_test_key", undefined);
    provider.track("premium_screen_view", { source: "mobile_premium", platform: "mobile" });

    expect(captureMock).toHaveBeenCalledWith("premium_screen_view", {
      source: "mobile_premium",
      platform: "mobile",
    });
  });

  it("host未指定時はWeb版と同じdefault hostを使う", () => {
    new PostHogAnalyticsProvider("phc_test_key", undefined);

    expect(postHogConstructorMock).toHaveBeenCalledWith(
      "phc_test_key",
      expect.objectContaining({ host: "https://app.posthog.com" }),
    );
  });

  it("host指定時はそちらを使う", () => {
    new PostHogAnalyticsProvider("phc_test_key", "https://eu.i.posthog.com");

    expect(postHogConstructorMock).toHaveBeenCalledWith(
      "phc_test_key",
      expect.objectContaining({ host: "https://eu.i.posthog.com" }),
    );
  });

  it("customStorageにAsyncStorageを渡し、expo-file-system等を追加要求しない", () => {
    new PostHogAnalyticsProvider("phc_test_key", undefined);

    const options = postHogConstructorMock.mock.calls[0]?.[1] as { customStorage?: unknown };
    expect(options.customStorage).toBeDefined();
  });
});

describe("initAnalyticsProvider", () => {
  const ORIGINAL_ENV = { ...process.env };

  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
    setAnalyticsProvider(null);
    captureMock.mockClear();
    postHogConstructorMock.mockClear();
    (globalThis as unknown as { __DEV__: boolean }).__DEV__ = false;
  });

  async function freshModules() {
    vi.resetModules();
    const analyticsMod = await import("../analytics");
    const providerMod = await import("../posthogAnalyticsProvider");
    return { ...analyticsMod, ...providerMod };
  }

  it("development時はPostHogを構築せずConsoleAnalyticsProviderのまま", async () => {
    (globalThis as unknown as { __DEV__: boolean }).__DEV__ = true;
    process.env.EXPO_PUBLIC_POSTHOG_KEY = "phc_test_key";

    const { initAnalyticsProvider, getAnalyticsProvider, ConsoleAnalyticsProvider } = await freshModules();
    initAnalyticsProvider();

    expect(postHogConstructorMock).not.toHaveBeenCalled();
    expect(getAnalyticsProvider()).toBeInstanceOf(ConsoleAnalyticsProvider);
  });

  it("productionでもkey未設定ならConsoleAnalyticsProviderのまま", async () => {
    delete process.env.EXPO_PUBLIC_POSTHOG_KEY;

    const { initAnalyticsProvider, getAnalyticsProvider, ConsoleAnalyticsProvider } = await freshModules();
    initAnalyticsProvider();

    expect(postHogConstructorMock).not.toHaveBeenCalled();
    expect(getAnalyticsProvider()).toBeInstanceOf(ConsoleAnalyticsProvider);
  });

  it("productionかつkey設定時のみPostHogAnalyticsProviderへ切り替える", async () => {
    process.env.EXPO_PUBLIC_POSTHOG_KEY = "phc_test_key";

    const { initAnalyticsProvider, getAnalyticsProvider, PostHogAnalyticsProvider: FreshProvider } =
      await freshModules();
    initAnalyticsProvider();

    expect(postHogConstructorMock).toHaveBeenCalledTimes(1);
    expect(getAnalyticsProvider()).toBeInstanceOf(FreshProvider);
  });

  it("2回呼び出してもPostHogクライアントの構築は1回だけ", async () => {
    process.env.EXPO_PUBLIC_POSTHOG_KEY = "phc_test_key";

    const { initAnalyticsProvider } = await freshModules();
    initAnalyticsProvider();
    initAnalyticsProvider();

    expect(postHogConstructorMock).toHaveBeenCalledTimes(1);
  });

  it("PostHogクライアントの構築が例外を投げても呼び出し元に伝播しない", async () => {
    process.env.EXPO_PUBLIC_POSTHOG_KEY = "phc_test_key";
    postHogConstructorMock.mockImplementationOnce(() => {
      throw new Error("boom");
    });

    const { initAnalyticsProvider, getAnalyticsProvider, ConsoleAnalyticsProvider } = await freshModules();

    expect(() => initAnalyticsProvider()).not.toThrow();
    expect(getAnalyticsProvider()).toBeInstanceOf(ConsoleAnalyticsProvider);
  });
});

// vi.resetModules()を使うテストが前にあるため、このブロックでは常に動的importで
// 同一エポックのモジュールインスタンスを取り直してから利用する(取り違え防止)。
describe("end-to-end: premiumAnalytics -> track() -> PostHogAnalyticsProvider", () => {
  afterEach(() => {
    captureMock.mockClear();
    postHogConstructorMock.mockClear();
  });

  it("premium_screen_viewがPostHogのcapture()へ届く", async () => {
    const { setAnalyticsProvider: setProvider } = await import("../analytics");
    const { PostHogAnalyticsProvider: Provider } = await import("../posthogAnalyticsProvider");
    const { trackPremiumScreenView } = await import("../premiumAnalytics");

    setProvider(new Provider("phc_test_key", undefined));
    trackPremiumScreenView();
    setProvider(null);

    expect(captureMock).toHaveBeenCalledWith("premium_screen_view", {
      source: "mobile_premium",
      platform: "mobile",
    });
  });

  it("premium_upgrade_clickがPostHogのcapture()へ届く", async () => {
    const { setAnalyticsProvider: setProvider } = await import("../analytics");
    const { PostHogAnalyticsProvider: Provider } = await import("../posthogAnalyticsProvider");
    const { trackPremiumUpgradeClick } = await import("../premiumAnalytics");

    setProvider(new Provider("phc_test_key", undefined));
    trackPremiumUpgradeClick();
    setProvider(null);

    expect(captureMock).toHaveBeenCalledWith("premium_upgrade_click", {
      plan: "free",
      source: "mobile_premium",
    });
  });

  it("session_id/sessionId/checkout_session_id/checkout_urlを含めてもPostHogへは届かない", async () => {
    const { track, setAnalyticsProvider: setProvider } = await import("../analytics");
    const { PostHogAnalyticsProvider: Provider } = await import("../posthogAnalyticsProvider");

    setProvider(new Provider("phc_test_key", undefined));
    track("premium_checkout_started", {
      source: "mobile_premium",
      session_id: "leak-1",
      sessionId: "leak-2",
      checkout_session_id: "leak-3",
      checkout_url: "https://checkout.example.com/leak",
      token: "leak-4",
    });
    setProvider(null);

    expect(captureMock).toHaveBeenCalledWith("premium_checkout_started", { source: "mobile_premium" });
  });
});
