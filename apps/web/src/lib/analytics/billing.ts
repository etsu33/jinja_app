// apps/web/src/lib/analytics/billing.ts
import { getAnalyticsProvider } from "@/lib/analytics/providers";

export type BillingAnalyticsEventName =
  | "comparison_preview"
  | "upgrade_click"
  | "checkout_started"
  | "checkout_success"
  | "premium_active";

export type BillingFunnelSource = "state_delta_card" | "concierge_result" | "shrine_detail";

export type BillingFunnelStep = "comparison_preview";

type BillingAnalyticsPrimitive = string | number | boolean | null | undefined;

export type BillingAnalyticsPayload = {
  source?: BillingFunnelSource | null;
  funnelStep?: BillingFunnelStep | null;
  cardId?: string | null;
  checkoutSessionId?: string | null;
  area?: "billing" | null;
  [key: string]: BillingAnalyticsPrimitive;
};

export type SerializedBillingAnalyticsPayload = Record<string, string | number | boolean>;

export function parseBillingFunnelSource(source: string | null): BillingFunnelSource | null {
  if (source === "state_delta_card") return source;
  if (source === "concierge_result") return source;
  if (source === "shrine_detail") return source;

  return null;
}

export function parseBillingFunnelStep(funnelStep: string | null): BillingFunnelStep | null {
  return funnelStep === "comparison_preview" ? funnelStep : null;
}

function isBillingAnalyticsPrimitive(value: unknown): value is BillingAnalyticsPrimitive {
  return (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean" ||
    value === null ||
    value === undefined
  );
}

export function serializeBillingAnalyticsPayload(
  payload: BillingAnalyticsPayload = {},
): SerializedBillingAnalyticsPayload {
  const serialized: SerializedBillingAnalyticsPayload = {};

  for (const [key, value] of Object.entries(payload)) {
    if (key === "session_id" || key === "sessionId") continue;
    if (value === null || value === undefined) continue;
    if (!isBillingAnalyticsPrimitive(value)) continue;

    serialized[key] = value;
  }

  return serialized;
}

export function trackBillingEvent(eventName: BillingAnalyticsEventName, payload: BillingAnalyticsPayload = {}) {
  const serializedPayload = serializeBillingAnalyticsPayload({
    area: "billing",
    ...payload,
  });

  try {
    getAnalyticsProvider().track(eventName, serializedPayload);
  } catch (error) {
    if (process.env.NODE_ENV === "development") {
      console.warn("[billing analytics]", eventName, serializedPayload, error);
    }
  }
}
