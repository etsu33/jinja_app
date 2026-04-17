import "server-only";

import { cookies, headers } from "next/headers";
import { resolveServerBaseUrlFromHeaders } from "@/lib/server/resolveServerBaseUrl";

export type ShrineFavoriteInitialState = {
  fav: boolean;
  favorite_id: number | null;
  guestMode: boolean;
};

function hasAuthContext(args: { cookieHeader: string; authorization: string | null }): boolean {
  const { cookieHeader, authorization } = args;
  if (authorization) return true;
  return /(?:^|;\s*)(access_token|refresh_token)=/.test(cookieHeader);
}

function normalizeFavoriteList(data: any): any[] {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

function isShrineFavoriteMatch(favorite: any, shrineId: number): boolean {
  const targetType = favorite?.target_type;
  if (targetType && targetType !== "shrine") return false;

  const candidateShrineId = Number(
    favorite?.shrine_id ?? favorite?.shrine?.id ?? favorite?.target_id ?? NaN,
  );

  return Number.isFinite(candidateShrineId) && candidateShrineId === shrineId;
}

export async function getShrineFavoriteInitialState(
  shrineId: number,
): Promise<ShrineFavoriteInitialState> {
  const headerStore = await headers();
  const cookieStore = await cookies();

  const cookieHeader = cookieStore.toString();
  const authorization = headerStore.get("authorization");

  if (!hasAuthContext({ cookieHeader, authorization })) {
    return {
      fav: false,
      favorite_id: null,
      guestMode: true,
    };
  }

  const baseUrl = resolveServerBaseUrlFromHeaders(headerStore);
  const response = await fetch(`${baseUrl}/api/favorites/`, {
    cache: "no-store",
    headers: {
      ...(cookieHeader ? { cookie: cookieHeader } : {}),
      ...(authorization ? { authorization } : {}),
    },
  });

  if (response.status === 401) {
    return {
      fav: false,
      favorite_id: null,
      guestMode: true,
    };
  }

  if (!response.ok) {
    return {
      fav: false,
      favorite_id: null,
      guestMode: false,
    };
  }

  const data = await response.json();
  const list = normalizeFavoriteList(data);
  const hit = list.find((favorite) => isShrineFavoriteMatch(favorite, shrineId)) ?? null;

  return {
    fav: Boolean(hit),
    favorite_id: typeof hit?.id === "number" ? hit.id : null,
    guestMode: false,
  };
}
