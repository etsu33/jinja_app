

import { postAuth } from "./http";

export type VisitCreateResponse = {
  id: number;
  created: boolean;
};

function normalizePositiveInt(value: number | string | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;

  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

export async function createVisitByShrineId(shrineId: number | string): Promise<VisitCreateResponse | null> {
  const normalizedShrineId = normalizePositiveInt(shrineId);
  if (!normalizedShrineId) return null;

  try {
    return await postAuth<VisitCreateResponse>(`/shrines/${normalizedShrineId}/visit/`, {
      shrine_id: normalizedShrineId,
      visited_at: new Date().toISOString(),
    });
  } catch (error) {
    if (__DEV__) {
      console.warn("[createVisitByShrineId] failed", error);
    }
    return null;
  }
}
