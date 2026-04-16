// apps/web/src/hooks/useFavorite.ts
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  createFavoriteByShrineId,
  removeFavoriteByPk,
  removeFavoriteByShrineId,
  type Favorite,
} from "@/lib/api/favorites";

import { favoriteMatchKey } from "@/lib/favorites/normalize";

import {
  peekFavoritesCache,
  getFavoritesCached,
  upsertFavorite,
  removeFavoriteFromCacheByPk,
  removeFavoriteFromCacheByShrineId,
  clearFavoritesInFlight,
} from "@/lib/favoritesCache";

type Args = {
  shrineId?: number;
  initial?: boolean; // SSRなどで明示したい場合だけ使う
  guestMode?: boolean;
};

async function getFavoritesDirect(): Promise<Favorite[]> {
  const r = await fetch("/api/favorites/", { cache: "no-store" });

  if (r.status === 401) {
    const err = new Error("unauthenticated");
    (err as any).status = 401;
    throw err;
  }

  if (!r.ok) {
    throw new Error(`favorites fetch failed: ${r.status}`);
  }

  const data = await r.json();
  return Array.isArray(data) ? data : (data?.results ?? []);
}

export function useFavorite({ shrineId, initial, guestMode = false }: Args) {
  const isGuest = Boolean(guestMode);

  const key = useMemo(() => {
    if (typeof shrineId === "number") return `shrine:${shrineId}`;
    return null;
  }, [shrineId]);

  // ① cache が既にあるなら即反映
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
    if (cached) return cached.fav;
    return false;
  });
  const [favPk, setFavPk] = useState<number | null>(() => {
    if (isGuest) return null;
    return cached ? cached.pk : null;
  });
  const [busy, setBusy] = useState(false);

  const hydratedRef = useRef(false);

  useEffect(() => {
    hydratedRef.current = false;
  }, [isGuest, shrineId, initial]);

  // ② cache が無い/不確実なら一度だけ取得して復元
  useEffect(() => {
    if (!key) return;
    if (hydratedRef.current) return;
    if (isGuest) {
      hydratedRef.current = true;
      setFav(false);
      setFavPk(null);
      return;
    }

    // initial が明示されてる場合は fetch しない
    if (typeof initial === "boolean") {
      hydratedRef.current = true;
      return;
    }

    hydratedRef.current = true;

    (async () => {
      try {
        const list = await getFavoritesCached(getFavoritesDirect);
        const hit = list.find((f) => favoriteMatchKey(f, { shrineId })) ?? null;
        setFav(Boolean(hit));
        setFavPk(hit?.id ?? null);
      } catch {
        // noop
      }
    })();
  }, [key, shrineId, initial, isGuest]);

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
