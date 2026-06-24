

import { postAuth } from "./http";

export type ShrineInteractionActionType = "detail_view" | "route_open" | "shrine_card_click";

export type ShrineInteractionSource =
  | "mobile_shrine_detail"
  | "mobile_concierge_result"
  | "mobile_map"
  | "mobile_shrines"
  | string;

export type TrackShrineInteractionParams = {
  shrineId: number;
  actionType: ShrineInteractionActionType;
  source?: ShrineInteractionSource | null;
  threadId?: number | string | null;
  metadata?: Record<string, unknown>;
};

export type ShrineInteractionResponse = {
  id: number;
  shrine_id: number;
  action_type: ShrineInteractionActionType;
  source: string;
  thread_id: number | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

function normalizeThreadId(threadId: TrackShrineInteractionParams["threadId"]): number | null {
  if (threadId === null || threadId === undefined || threadId === "") return null;

  const value = Number(threadId);
  return Number.isFinite(value) && value > 0 ? value : null;
}

export async function trackShrineInteraction({
  shrineId,
  actionType,
  source = "mobile_shrine_detail",
  threadId = null,
  metadata = {},
}: TrackShrineInteractionParams): Promise<ShrineInteractionResponse | null> {
  if (!Number.isFinite(shrineId) || shrineId <= 0) return null;

  try {
    return await postAuth<ShrineInteractionResponse>("/shrine-interactions/", {
      shrine_id: shrineId,
      action_type: actionType,
      source: source ?? "",
      thread_id: normalizeThreadId(threadId),
      metadata,
    });
  } catch (error) {
    if (__DEV__) {
      console.warn("[trackShrineInteraction] failed", error);
    }
    return null;
  }
}

export async function trackShrineDetailView(params: Omit<TrackShrineInteractionParams, "actionType">) {
  return trackShrineInteraction({
    ...params,
    actionType: "detail_view",
    metadata: {
      event: "shrine_detail_view",
      platform: "mobile",
      ...(params.metadata ?? {}),
    },
  });
}

export async function trackShrineRouteOpen(params: Omit<TrackShrineInteractionParams, "actionType">) {
  return trackShrineInteraction({
    ...params,
    actionType: "route_open",
    metadata: {
      event: "route_open",
      routeTarget: "google_maps",
      platform: "mobile",
      ...(params.metadata ?? {}),
    },
  });
}
