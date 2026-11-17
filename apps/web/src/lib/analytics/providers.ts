import posthog from "posthog-js";

import { track } from "@/lib/analytics/track";
import { sanitizeCaptureResult } from "@/lib/analytics/urlSanitizer";

export type AnalyticsPayload = Record<string, string | number | boolean>;

export interface AnalyticsProvider {
  track(eventName: string, payload: AnalyticsPayload): void;
  /**
   * ログインユーザーを識別する。渡すのは内部のユーザーID（文字列）だけで、
   * メールアドレス・表示名・ユーザー名などは person properties を含めて渡さない。
   */
  identify(userId: string): void;
  /** 識別を解除し、以後のイベントを新しい匿名 ID で送る。 */
  reset(): void;
}

export class ConsoleAnalyticsProvider implements AnalyticsProvider {
  track(eventName: string, payload: AnalyticsPayload) {
    track(eventName, payload);
  }

  // 開発・テスト環境では識別しない。
  identify(_userId: string) {}

  reset() {}
}

export class PostHogAnalyticsProvider implements AnalyticsProvider {
  private initialized = false;

  private init() {
    if (this.initialized) return true;
    if (process.env.NODE_ENV !== "production") return false;
    if (typeof window === "undefined") return false;

    const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
    if (!key) return false;

    posthog.init(key, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://app.posthog.com",
      // 最初の表示と、App Router の遷移（pushState / replaceState / popstate）ごとに
      // $pageview を送る。パス名が変わったときだけ送る（クエリだけの変化では送らない）。
      capture_pageview: "history_change",
      // URL 系 property から utm_* 以外の query parameter を除く（検索語などを送らない）。
      before_send: sanitizeCaptureResult,
      // apps/web は feature flag を使わないので、/flags への問い合わせをしない。
      // advanced_disable_flags と違い remote config（/array/<token>/config）は読み込むため、
      // autocapture・session recording などプロジェクト設定で決まる機能には影響しない。
      advanced_disable_feature_flags: true,
    });

    this.initialized = true;
    return true;
  }

  track(eventName: string, payload: AnalyticsPayload) {
    const initialized = this.init();


    if (!initialized) return;

    posthog.capture(eventName, payload);
  }

  identify(userId: string) {
    if (!this.init()) return;

    // 第2・第3引数（$set / $set_once）は渡さない。
    posthog.identify(userId);
  }

  reset() {
    if (!this.init()) return;

    posthog.reset();
  }
}

let analyticsProvider: AnalyticsProvider | null = null;
const fallbackAnalyticsProvider = new ConsoleAnalyticsProvider();
const postHogAnalyticsProvider = new PostHogAnalyticsProvider();

export function setAnalyticsProvider(provider: AnalyticsProvider | null) {
  analyticsProvider = provider;
}

function getDefaultAnalyticsProvider(): AnalyticsProvider {
  if (process.env.NODE_ENV === "production" && process.env.NEXT_PUBLIC_POSTHOG_KEY) {
    return postHogAnalyticsProvider;
  }

  return fallbackAnalyticsProvider;
}

export function getAnalyticsProvider(): AnalyticsProvider {
  return analyticsProvider ?? getDefaultAnalyticsProvider();
}
