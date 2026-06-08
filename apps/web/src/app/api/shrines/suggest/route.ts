import { NextRequest, NextResponse } from "next/server";

import { djFetch } from "@/lib/server/backend";

export const dynamic = "force-dynamic";

const NAME_SUGGESTION_MIN_LENGTH = 2;
const NAME_SUGGESTION_LIMIT = 3;

type SuggestCandidate = {
  id: number;
  name: string;
  address: string;
};

function emptyResponse() {
  return NextResponse.json({
    count: 0,
    results: [] as SuggestCandidate[],
  });
}

function normalizeCandidate(value: unknown): SuggestCandidate | null {
  if (!value || typeof value !== "object") return null;

  const row = value as Record<string, unknown>;
  const id = typeof row.id === "number" ? row.id : null;
  const name = typeof row.name === "string"
    ? row.name
    : typeof row.name_jp === "string"
      ? row.name_jp
      : null;
  const address = typeof row.address === "string" ? row.address : "";

  if (!id || !name) return null;

  return {
    id,
    name,
    address,
  };
}

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const name = url.searchParams.get("name")?.trim() ?? "";

  if (name.length < NAME_SUGGESTION_MIN_LENGTH) {
    return emptyResponse();
  }

  const qs = new URLSearchParams();
  qs.set("q", name);
  qs.set("limit", String(NAME_SUGGESTION_LIMIT));

  const upstream = await djFetch(req, `/api/shrines/?${qs.toString()}`, {
    method: "GET",
    forwardAuth: false,
  });

  if (!upstream.ok) {
    const detail = await upstream.text().catch(() => "");
    return NextResponse.json(
      {
        error: "upstream_failed",
        detail: detail.slice(0, 1000) || null,
      },
      { status: upstream.status },
    );
  }

  const data = (await upstream.json()) as { results?: unknown[] };
  const results = (Array.isArray(data.results) ? data.results : [])
    .map(normalizeCandidate)
    .filter((candidate): candidate is SuggestCandidate => candidate !== null)
    .slice(0, NAME_SUGGESTION_LIMIT);

  return NextResponse.json({
    count: results.length,
    results,
  });
}
