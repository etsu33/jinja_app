import posthog from "posthog-js";

import { track } from "@/lib/analytics/track";

export type AnalyticsPayload = Record<string, string | number | boolean>;

export interface AnalyticsProvider {
  track(eventName: string, payload: AnalyticsPayload): void;
}

export class ConsoleAnalyticsProvider implements AnalyticsProvider {
  track(eventName: string, payload: AnalyticsPayload) {
    track(eventName, payload);
  }
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
      capture_pageview: false,
    });

    this.initialized = true;
    return true;
  }

  track(eventName: string, payload: AnalyticsPayload) {
    const initialized = this.init();


    if (!initialized) return;

    posthog.capture(eventName, payload);
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
