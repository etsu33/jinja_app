import { afterEach, describe, expect, it, vi } from "vitest";

// __DEV__ は Metro/React Native が注入するグローバルで、vitest実行環境には存在しないため定義する。
(globalThis as unknown as { __DEV__: boolean }).__DEV__ = false;

import {
  ConsoleAnalyticsProvider,
  getAnalyticsProvider,
  serializeAnalyticsPayload,
  setAnalyticsProvider,
  track,
  type AnalyticsProvider,
} from "../analytics";

describe("serializeAnalyticsPayload", () => {
  it("null / undefined / object / array / session_id / sessionId / NaNを除外し、プリミティブ値のみを残す", () => {
    expect(
      serializeAnalyticsPayload({
        source: "mypage",
        session_id: "session-secret",
        sessionId: "session-secret-legacy",
        nested: { value: 1 },
        list: ["a"],
        invalidNumber: Number.NaN,
      }),
    ).toEqual({
      source: "mypage",
    });
  });

  it("string/number/booleanのプリミティブ値をそのまま残す", () => {
    expect(
      serializeAnalyticsPayload({
        name: "premium_screen_view",
        count: 3,
        active: true,
      }),
    ).toEqual({
      name: "premium_screen_view",
      count: 3,
      active: true,
    });
  });

  it("nullとundefinedのフィールドを除外する", () => {
    expect(serializeAnalyticsPayload({ a: null, b: undefined, c: "ok" })).toEqual({ c: "ok" });
  });

  it("Infinity / -Infinityを除外する", () => {
    expect(serializeAnalyticsPayload({ a: Infinity, b: -Infinity, c: 1 })).toEqual({ c: 1 });
  });

  it("payloadがnull/undefinedでも例外を投げず空オブジェクトを返す", () => {
    expect(serializeAnalyticsPayload(null)).toEqual({});
    expect(serializeAnalyticsPayload(undefined)).toEqual({});
  });

  it("空オブジェクトを渡すと空オブジェクトを返す", () => {
    expect(serializeAnalyticsPayload({})).toEqual({});
  });

  it("空文字列 / 0 / falseはfalsyだが保持する", () => {
    expect(serializeAnalyticsPayload({ a: "", b: 0, c: false })).toEqual({ a: "", b: 0, c: false });
  });
});

describe("track / provider差し替え", () => {
  afterEach(() => {
    setAnalyticsProvider(null);
  });

  it("既定はConsoleAnalyticsProviderを使う", () => {
    expect(getAnalyticsProvider()).toBeInstanceOf(ConsoleAnalyticsProvider);
  });

  it("setAnalyticsProviderで差し替えたproviderのtrackが呼ばれる", () => {
    const trackSpy = vi.fn();
    const customProvider: AnalyticsProvider = { track: trackSpy };
    setAnalyticsProvider(customProvider);

    track("premium_screen_view", { plan: "free" });

    expect(trackSpy).toHaveBeenCalledWith("premium_screen_view", { plan: "free" });
  });

  it("setAnalyticsProvider(null)で既定のConsoleAnalyticsProviderへ戻る", () => {
    setAnalyticsProvider({ track: vi.fn() });
    setAnalyticsProvider(null);

    expect(getAnalyticsProvider()).toBeInstanceOf(ConsoleAnalyticsProvider);
  });

  it("track経由でもsession_id/sessionIdはproviderに渡す前に除外される", () => {
    const trackSpy = vi.fn();
    setAnalyticsProvider({ track: trackSpy });

    track("premium_checkout_started", { session_id: "secret", sessionId: "secret2", plan: "free" });

    expect(trackSpy).toHaveBeenCalledWith("premium_checkout_started", { plan: "free" });
  });

  it("provider.trackが例外を投げても握り潰し、呼び出し元に伝播しない", () => {
    setAnalyticsProvider({
      track: () => {
        throw new Error("boom");
      },
    });

    expect(() => track("premium_checkout_failed", { reason: "unknown" })).not.toThrow();
  });

  it("eventNameが空文字/空白のみの場合は送信しない", () => {
    const trackSpy = vi.fn();
    setAnalyticsProvider({ track: trackSpy });

    track("");
    track("   ");

    expect(trackSpy).not.toHaveBeenCalled();
  });
});
