

import { postAuth } from "./http";

export type ActionEventActionType = "action_started" | "action_completed";

export type ActionEventSource =
  | "mobile_concierge_result"
  | "mobile_shrine_detail"
  | "mobile_map"
  | "mobile_shrines"
  | string;

export type TrackActionEventParams = {
  actionType: ActionEventActionType;
  actionSuggestionId: string;
  source?: ActionEventSource | null;
  shrineId?: number | string | null;
  threadId?: number | string | null;
  historyTheme?: string | null;
  actionCategory?: string | null;
  metadata?: Record<string, unknown>;
};

export type ActionEventResponse = {
  id: number;
  action_type: ActionEventActionType;
  action_suggestion_id: string;
  history_theme: string;
  action_category: string;
  source: string;
  shrine_id: number | null;
  thread_id: number | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

function normalizePositiveInt(value: number | string | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;

  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

export async function trackActionEvent({
  actionType,
  actionSuggestionId,
  source = "mobile_concierge_result",
  shrineId = null,
  threadId = null,
  historyTheme = null,
  actionCategory = null,
  metadata = {},
}: TrackActionEventParams): Promise<ActionEventResponse | null> {
  const normalizedActionSuggestionId = actionSuggestionId.trim();
  if (!normalizedActionSuggestionId) return null;

  try {
    return await postAuth<ActionEventResponse>("/action-events/", {
      action_type: actionType,
      action_suggestion_id: normalizedActionSuggestionId,
      source: source ?? "",
      shrine_id: normalizePositiveInt(shrineId),
      thread_id: normalizePositiveInt(threadId),
      history_theme: historyTheme ?? "",
      action_category: actionCategory ?? "",
      metadata,
    });
  } catch (error) {
    if (__DEV__) {
      console.warn("[trackActionEvent] failed", error);
    }
    return null;
  }
}
