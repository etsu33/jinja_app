// apps/web/src/hooks/useFavorite.ts
"use client";

import { useMemo, useState } from "react";
import {
  createFavoriteByShrineId,
  removeFavoriteByPk,
  removeFavoriteByShrineId,
  type Favorite,
} from "@/lib/api/favorites";


import {
  upsertFavorite,
  removeFavoriteFromCacheByPk,
  removeFavoriteFromCacheByShrineId,
  clearFavoritesInFlight,
} from "@/lib/favoritesCache";

type Args = {
  shrineId?: number;
  initial?: {
    fav: boolean;
    favorite_id: number | null;
  };
  guestMode?: boolean;
};


export function useFavorite({ shrineId, initial, guestMode = false }: Args) {
  const isGuest = Boolean(guestMode);

  const key = useMemo(() => {
    if (typeof shrineId === "number") return `shrine:${shrineId}`;
    return null;
  }, [shrineId]);

  const [fav, setFav] = useState<boolean>(() => {
    if (isGuest) return false;
    return initial?.fav ?? false;
  });
  const [favPk, setFavPk] = useState<number | null>(() => {
    if (isGuest) return null;
    return initial?.favorite_id ?? null;
  });
  const [busy, setBusy] = useState(false);

  async function toggle() {
    if (!key || busy) return;
    if (typeof shrineId !== "number") return;

    if (isGuest) {
      const err = new Error("unauthenticated");
      (err as any).status = 401;
      throw err;
    }

    setBusy(true);
    const prev = fav;
    setFav(!prev);

    try {
      if (!prev) {
        // add
        const createdRaw = await createFavoriteByShrineId(shrineId);

        // backend が id/created_at だけ返しても cache/normalize が成立するよう補完
        const created: Favorite = {
          ...createdRaw,
          shrine_id: shrineId as any,
          target_type: "shrine" as any,
          target_id: shrineId as any,
          shrine: { id: shrineId } as any,
        } as any;

        setFavPk(created.id);
        upsertFavorite(created);
        clearFavoritesInFlight();
        return;
      }

      // remove
      if (favPk != null) {
        await removeFavoriteByPk(favPk);
        removeFavoriteFromCacheByPk(favPk);
        setFavPk(null);
        clearFavoritesInFlight();
        return;
      }

      // pk不明フォールバック
      await removeFavoriteByShrineId(shrineId);
      removeFavoriteFromCacheByShrineId(shrineId);
      clearFavoritesInFlight();
    } catch (e) {
      setFav(prev);
      throw e;
    } finally {
      setBusy(false);
    }
  }

  return {
    fav,
    busy,
    toggle,
    isGuest,
  };
}
