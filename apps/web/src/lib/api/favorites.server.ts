// apps/web/src/lib/api/favorites.server.ts
import "server-only";
import { headers } from "next/headers";
import type { Favorite } from "./favorites";
import { favoriteMatchKey } from "@/lib/favorites/normalize";
import { resolveServerBaseUrlFromHeaders } from "@/lib/server/resolveServerBaseUrl";

export async function getFavoritesServer(): Promise<Favorite[]> {
  const h = await headers();
  const cookie = h.get("cookie") ?? "";

  const baseUrl = resolveServerBaseUrlFromHeaders(h);

  const r = await fetch(`${baseUrl}/api/favorites/`, {
    headers: cookie ? { cookie } : undefined,
    cache: "no-store",
  });

  if (!r.ok) return [];
  const data = await r.json();
  return Array.isArray(data) ? data : (data?.results ?? []);
}

function hasAuthContext(args: { cookie: string; authorization: string | null }): boolean {
  const { cookie, authorization } = args;
  if (authorization) return true;
  return /(?:^|;\s*)(access_token|refresh_token)=/.test(cookie);
}

export async function getShrineFavoriteStateServer(shrineId: number): Promise<{
  initial: boolean;
  guestMode: boolean;
}> {
  const h = await headers();
  const cookie = h.get("cookie") ?? "";
  const authorization = h.get("authorization");

  if (!hasAuthContext({ cookie, authorization })) {
    return { initial: false, guestMode: true };
  }

  const baseUrl = resolveServerBaseUrlFromHeaders(h);

  const res = await fetch(`${baseUrl}/api/favorites/`, {
    headers: {
      ...(cookie ? { cookie } : {}),
      ...(authorization ? { authorization } : {}),
    },
    cache: "no-store",
  });

  if (res.status === 401) {
    return { initial: false, guestMode: true };
  }

  if (!res.ok) {
    return { initial: false, guestMode: false };
  }

  const data = await res.json();
  const list: Favorite[] = Array.isArray(data) ? data : (data?.results ?? []);

  return {
    initial: list.some((f) => favoriteMatchKey(f, { shrineId })),
    guestMode: false,
  };
}
