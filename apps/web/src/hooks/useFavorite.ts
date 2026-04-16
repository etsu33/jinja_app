// apps/web/src/hooks/useFavorite.ts
"use client";

import { useEffect, useMemo, useState } from "react";
import {
  createFavoriteByShrineId,
  removeFavoriteByPk,
  removeFavoriteByShrineId,
  type Favorite,
} from "@/lib/api/favorites";

import { favoriteMatchKey } from "@/lib/favorites/normalize";

import {
  peekFavoritesCache,
  upsertFavorite,
  removeFavoriteFromCacheByPk,
  removeFavoriteFromCacheByShrineId,
  clearFavoritesInFlight,
} from "@/lib/favoritesCache";

type Args = {
  shrineId?: number;
  initial?: boolean;
  guestMode?: boolean;
};

export function useFavorite({ shrineId, initial, guestMode = false }: Args) {
  const isGuest = Boolean(guestMode);

  const key = useMemo(() => {
    if (typeof shrineId === "number") return `shrine:${shrineId}`;
    return null;
  }, [shrineId]);

  const cached = useMemo(() => {
    if (typeof shrineId !== "number") return null;
    if (isGuest) return null;
    const c = peekFavoritesCache();
    if (!c) return null;
    const hit = c.find((f) => favoriteMatchKey(f, { shrineId })) ?? null;
    return hit ? { fav: true, pk: hit.id } : { fav: false, pk: null };
  }, [shrineId, isGuest]);

  const [fav, setFav] = useState<boolean>(() => {
    if (isGuest) return false;
    if (typeof initial === "boolean") return initial;
    return cached?.fav ?? false;
  });

  const [favPk, setFavPk] = useState<number | null>(() => {
    if (isGuest) return null;
    return cached?.pk ?? null;
  });

  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (isGuest) {
      setFav(false);
      setFavPk(null);
      return;
    }

    if (typeof initial === "boolean") {
      setFav(initial);
      return;
    }

    setFav(cached?.fav ?? false);
    setFavPk(cached?.pk ?? null);
  }, [isGuest, initial, cached?.fav, cached?.pk, key]);

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
        const createdRaw = await createFavoriteByShrineId(shrineId);

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

      if (favPk != null) {
        await removeFavoriteByPk(favPk);
        removeFavoriteFromCacheByPk(favPk);
        setFavPk(null);
        clearFavoritesInFlight();
        return;
      }

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
