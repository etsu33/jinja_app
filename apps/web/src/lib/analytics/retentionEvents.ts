import { getAnalyticsProvider } from "@/lib/analytics/providers";

export type RetentionAnalyticsEventName =
  | "next_session"
  | "next_thread"
  | "thread_resume"
  | "premium_history_click"
  | "premium_history_comparison_view"
  | "premium_history_comparison_click";

type RetentionAnalyticsPrimitive = string | number | boolean | null | undefined;

export type RetentionAnalyticsPayload = {
  analyticsSessionId?: string | null;
  threadId?: string | null;
  resultSetId?: string | null;
  source?: "concierge_result" | "mypage" | "thread_history" | "state_delta_card" | "thread_list" | null;
  previousSessionAt?: string | null;
  [key: string]: RetentionAnalyticsPrimitive;
};

export type SerializedRetentionAnalyticsPayload = Record<string, string | number | boolean>;

function isRetentionAnalyticsPrimitive(value: unknown): value is RetentionAnalyticsPrimitive {
  return (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean" ||
    value === null ||
    value === undefined
  );
}



export function serializeRetentionAnalyticsPayload(
  payload: RetentionAnalyticsPayload = {},
): SerializedRetentionAnalyticsPayload {
  const serialized: SerializedRetentionAnalyticsPayload = {};

  for (const [key, value] of Object.entries(payload)) {
    if (value === null || value === undefined) continue;
    if (!isRetentionAnalyticsPrimitive(value)) continue;

    serialized[key] = value;
  }

  return serialized;
}

export function trackRetentionEvent(eventName: RetentionAnalyticsEventName, payload: RetentionAnalyticsPayload = {}) {
  const serializedPayload = serializeRetentionAnalyticsPayload(payload);

  try {
    getAnalyticsProvider().track(eventName, serializedPayload);
  } catch (error) {
    if (process.env.NODE_ENV === "development") {
      console.warn("[retention analytics]", eventName, serializedPayload, error);
    }
  }
}
