// apps/web/src/lib/analytics/billing.ts
import { track } from "@/lib/analytics/track";

type BillingAnalyticsPayload = Record<string, string | number | boolean | null | undefined>;

export type BillingAnalyticsEvent = "upgrade_click" | "checkout_started" | "checkout_success" | "premium_active";

export function trackBillingEvent(eventName: BillingAnalyticsEvent, payload: BillingAnalyticsPayload = {}) {
  track(eventName, {
    area: "billing",
    ...payload,
  });
}
