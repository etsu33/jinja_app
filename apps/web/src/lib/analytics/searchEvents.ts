import { getAnalyticsProvider } from "@/lib/analytics/providers";

export type SearchAnalyticsEventName =
  | "shrine_search"
  | "map_search"
  | "route_open"
  | "visit_done"
  | "reflection_prompt_view"
  | "reflection_saved"
  | "shrine_detail_transition"
  | "concierge_result_impression"
  | "empty_state_view"
  | "add_shrine_click"
  | "shrine_card_click"
  | "shrine_detail_view";

type SearchAnalyticsPrimitive = string | number | boolean | null | undefined;

export type SearchAnalyticsPayload = {
  source?: "concierge_result" | "shrine_detail" | "map" | "shrines" | null;
  analyticsSessionId?: string | null;
  threadId?: string | null;
  resultSetId?: string | null;
  shrineId?: number | string | null;
  recommendationRank?: number | null;
  position?: "hero_primary" | "compact" | "map" | "list" | null;
  firstClick?: boolean | null;
  query?: string | null;
  routeTarget?: "google_maps" | "internal_map" | null;
  historyTheme?: string | null;
  actionTheme?: string | null;
  promptType?: string | null;
  answerLength?: number | null;
  moodBefore?: string | null;
  moodAfter?: string | null;
  [key: string]: SearchAnalyticsPrimitive;
};

export type SerializedSearchAnalyticsPayload = Record<string, string | number | boolean>;

function isSearchAnalyticsPrimitive(value: unknown): value is SearchAnalyticsPrimitive {
  return (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean" ||
    value === null ||
    value === undefined
  );
}

export function serializeSearchAnalyticsPayload(
  payload: SearchAnalyticsPayload = {},
): SerializedSearchAnalyticsPayload {
  const serialized: SerializedSearchAnalyticsPayload = {};

  for (const [key, value] of Object.entries(payload)) {
    if (value === null || value === undefined) continue;
    if (!isSearchAnalyticsPrimitive(value)) continue;

    serialized[key] = value;
  }

  return serialized;
}

export function trackSearchEvent(eventName: SearchAnalyticsEventName, payload: SearchAnalyticsPayload = {}) {
  const serializedPayload = serializeSearchAnalyticsPayload(payload);

  try {
    getAnalyticsProvider().track(eventName, serializedPayload);
  } catch (error) {
    if (process.env.NODE_ENV === "development") {
      console.warn("[search analytics]", eventName, serializedPayload, error);
    }
  }
}
