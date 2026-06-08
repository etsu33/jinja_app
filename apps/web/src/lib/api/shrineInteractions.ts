

import api from "@/lib/api/client";

export type ShrineInteractionActionType =
  | "detail_view"
  | "route_open"
  | "shrine_card_click";

export type ShrineInteractionSource =
  | "concierge_result"
  | "shrine_detail"
  | "map"
  | "shrines"
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
  source = "shrine_detail",
  threadId = null,
  metadata = {},
}: TrackShrineInteractionParams): Promise<ShrineInteractionResponse | null> {
  if (!Number.isFinite(shrineId) || shrineId <= 0) return null;

  try {
    const { data } = await api.post<ShrineInteractionResponse>("shrine-interactions/", {
      shrine_id: shrineId,
      action_type: actionType,
      source: source ?? "",
      thread_id: normalizeThreadId(threadId),
      metadata,
    });

    return data;
  } catch {
    return null;
  }
}
