// apps/web/src/lib/analytics/billing.ts
import { track, type TrackPayload } from "@/lib/analytics/track";

export type BillingAnalyticsEvent = "upgrade_click" | "checkout_started" | "checkout_success" | "premium_active";

export function trackBillingEvent(eventName: BillingAnalyticsEvent, payload: TrackPayload = {}) {
  track(eventName, {
    area: "billing",
    ...payload,
  });
}
