import { NextRequest, NextResponse } from "next/server";
import { bffFetchWithAuthFromReq } from "@/lib/server/bffFetch";
import { favoriteMatchKey } from "@/lib/favorites/normalize";

export async function POST(req: NextRequest) {
  let shrineIds: number[];

  try {
    const body = await req.json();
    shrineIds = Array.isArray(body?.shrine_ids)
      ? body.shrine_ids.filter((id: any) => Number.isFinite(id))
      : [];
  } catch {
    shrineIds = [];
  }

  if (shrineIds.length === 0) {
    return NextResponse.json({ by_shrine_id: {} });
  }

  const upstream = await bffFetchWithAuthFromReq(req, "/api/favorites/");

  if (upstream.status === 401) {
    return NextResponse.json({ by_shrine_id: {} });
  }

  if (!upstream.ok) {
    return NextResponse.json({ by_shrine_id: {} }, { status: 200 });
  }

  const data = await upstream.json();
  const list = Array.isArray(data) ? data : data?.results ?? [];

  const map: Record<string, { fav: boolean; favorite_id: number | null }> = {};

  for (const shrineId of shrineIds) {
    const hit = list.find((f: any) => favoriteMatchKey(f, { shrineId }));
    map[String(shrineId)] = {
      fav: Boolean(hit),
      favorite_id: hit?.id ?? null,
    };
  }

  return NextResponse.json({ by_shrine_id: map });
}
