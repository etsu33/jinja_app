

import { getAuth, isUnauthenticatedError, postAuth } from "./http";

export type VisitCreateResponse = {
  id: number;
  created: boolean;
};

export type VisitHistoryItem = {
  id: number;
  user: number;
  shrine: number;
  shrine_name?: string | null;
  shrine_address?: string | null;
  visited_at: string;
  note?: string | null;
  status: "added" | "removed" | string;
};

type PaginatedResponse<T> = {
  results: T[];
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
    if (isUnauthenticatedError(error)) throw error;
    if (__DEV__) {
      console.warn("[createVisitByShrineId] failed", error);
    }
    return null;
  }
}

export async function listVisits(): Promise<VisitHistoryItem[]> {
  try {
    const data = await getAuth<VisitHistoryItem[] | PaginatedResponse<VisitHistoryItem>>("/visits/");
    const items = Array.isArray(data) ? data : (data.results ?? []);
    return items.filter((item) => item.status !== "removed");
  } catch (error) {
    if (__DEV__) {
      console.warn("[listVisits] failed", error);
    }
    return [];
  }
}
