import { trackSearchEvent } from "@/lib/analytics/searchEvents";
import type { SearchAnalyticsPayload } from "@/lib/analytics/searchEvents";
import type { ActionEventActionType, TrackActionEventParams } from "@/lib/api/actionEvents";

export type TrackActionAnalyticsParams = Omit<TrackActionEventParams, "actionType" | "source"> & {
  actionType: ActionEventActionType;
  source?: SearchAnalyticsPayload["source"];
  resultSetId?: string | null;
  recommendationRank?: number | null;
  position?: "hero_primary" | "compact" | "map" | "list" | null;
  actionPosition?: number | null;
};

export function trackActionAnalytics({
  actionType,
  actionSuggestionId,
  source = "concierge_result",
  shrineId = null,
  threadId = null,
  historyTheme = null,
  actionCategory = null,
  resultSetId = null,
  recommendationRank = null,
  position = "hero_primary",
  actionPosition = null,
  metadata = {},
}: TrackActionAnalyticsParams) {
  trackSearchEvent(actionType, {
    source,
    threadId: threadId != null ? String(threadId) : undefined,
    resultSetId,
    shrineId,
    recommendationRank,
    position,
    historyTheme,
    actionSuggestionId,
    actionCategory,
    actionTheme: historyTheme,
    actionPosition,
    ...metadata,
  });
}
