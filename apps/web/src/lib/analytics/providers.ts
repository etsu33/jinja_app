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

let analyticsProvider: AnalyticsProvider | null = null;
const fallbackAnalyticsProvider = new ConsoleAnalyticsProvider();

export function setAnalyticsProvider(provider: AnalyticsProvider | null) {
  analyticsProvider = provider;
}

export function getAnalyticsProvider(): AnalyticsProvider {
  return analyticsProvider ?? fallbackAnalyticsProvider;
}
