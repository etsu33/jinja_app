import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const posthogMock = vi.hoisted(() => ({
  init: vi.fn(),
  capture: vi.fn(),
  identify: vi.fn(),
  reset: vi.fn(),
}));

vi.mock("posthog-js", () => ({ default: posthogMock }));

import { ConsoleAnalyticsProvider, PostHogAnalyticsProvider } from "@/lib/analytics/providers";
import { sanitizeCaptureResult } from "@/lib/analytics/urlSanitizer";

describe("PostHogAnalyticsProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  describe("本番以外・キー未設定では何も送らない", () => {
    it.each([
      ["development", "phc_test"],
      ["test", "phc_test"],
      ["production", ""],
    ])("NODE_ENV=%s, key=%j のとき identify / reset / track で posthog を呼ばない", (nodeEnv, key) => {
      vi.stubEnv("NODE_ENV", nodeEnv);
      vi.stubEnv("NEXT_PUBLIC_POSTHOG_KEY", key);

      const provider = new PostHogAnalyticsProvider();
      provider.identify("42");
      provider.reset();
      provider.track("some_event", { a: 1 });

      expect(posthogMock.init).not.toHaveBeenCalled();
      expect(posthogMock.identify).not.toHaveBeenCalled();
      expect(posthogMock.reset).not.toHaveBeenCalled();
      expect(posthogMock.capture).not.toHaveBeenCalled();
    });
  });

  describe("本番かつキー設定済み", () => {
    beforeEach(() => {
      vi.stubEnv("NODE_ENV", "production");
      vi.stubEnv("NEXT_PUBLIC_POSTHOG_KEY", "phc_test");
    });

    it("App Router の遷移ごとに $pageview を送る設定と、URL を絞る before_send で初期化する", () => {
      new PostHogAnalyticsProvider().track("some_event", {});

      expect(posthogMock.init).toHaveBeenCalledTimes(1);
      const [key, config] = posthogMock.init.mock.calls[0];
      expect(key).toBe("phc_test");
      expect(config.capture_pageview).toBe("history_change");
      expect(config.before_send).toBe(sanitizeCaptureResult);
    });

    it("feature flag の問い合わせだけを止め、remote config は止めない", () => {
      new PostHogAnalyticsProvider().track("some_event", {});

      const [, config] = posthogMock.init.mock.calls[0];
      expect(config.advanced_disable_feature_flags).toBe(true);
      // advanced_disable_flags は remote config の読み込みまで止めるため使わない。
      expect(config).not.toHaveProperty("advanced_disable_flags");
    });

    it("identify は内部ユーザーIDの1引数だけで呼ぶ（person properties を渡さない）", () => {
      new PostHogAnalyticsProvider().identify("42");

      expect(posthogMock.init).toHaveBeenCalledTimes(1);
      expect(posthogMock.identify).toHaveBeenCalledTimes(1);
      expect(posthogMock.identify.mock.calls[0]).toEqual(["42"]);
    });

    it("reset は posthog.reset を呼ぶ", () => {
      new PostHogAnalyticsProvider().reset();

      expect(posthogMock.reset).toHaveBeenCalledTimes(1);
    });

    it("初期化は1回だけ行う", () => {
      const provider = new PostHogAnalyticsProvider();
      provider.track("a", {});
      provider.identify("42");
      provider.reset();

      expect(posthogMock.init).toHaveBeenCalledTimes(1);
    });
  });
});

describe("ConsoleAnalyticsProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("identify / reset では posthog を呼ばない", () => {
    const provider = new ConsoleAnalyticsProvider();
    provider.identify("42");
    provider.reset();

    expect(posthogMock.identify).not.toHaveBeenCalled();
    expect(posthogMock.reset).not.toHaveBeenCalled();
  });
});
