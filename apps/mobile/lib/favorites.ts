

import { isUnauthenticatedError, postAuth } from "./http";

export type Favorite = {
  id: number;
  shrine_id?: number | null;
  place_id?: string | null;
  target_type?: "shrine" | "place" | string;
  target_id?: number | string | null;
  created_at?: string | null;
  shrine?: {
    id?: number | null;
    name_jp?: string | null;
    latitude?: number | null;
    longitude?: number | null;
  } | null;
};

function normalizePositiveInt(value: number | string | null | undefined): number | null {
  if (value === null || value === undefined || value === "") return null;

  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

export async function createFavoriteByShrineId(shrineId: number | string): Promise<Favorite | null> {
  const normalizedShrineId = normalizePositiveInt(shrineId);
  if (!normalizedShrineId) return null;

  try {
    const favorite = await postAuth<Favorite>("/favorites/", {
      shrine_id: normalizedShrineId,
    });

    return {
      ...favorite,
      shrine_id: favorite.shrine_id ?? normalizedShrineId,
      target_type: favorite.target_type ?? "shrine",
      target_id: favorite.target_id ?? normalizedShrineId,
      shrine: favorite.shrine ?? { id: normalizedShrineId },
    };
  } catch (error) {
    if (isUnauthenticatedError(error)) throw error;
    if (__DEV__) {
      console.warn("[createFavoriteByShrineId] failed", error);
    }
    return null;
  }
}
