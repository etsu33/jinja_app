export type ShrineSuggestCandidate = {
  id: number;
  name: string;
  address: string;
};

export type ShrineSuggestResponse = {
  count: number;
  results: ShrineSuggestCandidate[];
};

function normalizeCandidate(value: unknown): ShrineSuggestCandidate | null {
  if (!value || typeof value !== "object") return null;

  const row = value as Record<string, unknown>;
  const id = typeof row.id === "number" ? row.id : null;
  const name = typeof row.name === "string" ? row.name : null;
  const address = typeof row.address === "string" ? row.address : "";

  if (!id || !name) return null;

  return {
    id,
    name,
    address,
  };
}

export async function fetchShrineSuggest(name: string): Promise<ShrineSuggestResponse> {
  const qs = new URLSearchParams();
  qs.set("name", name);

  const res = await fetch(`/api/shrines/suggest?${qs.toString()}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`fetchShrineSuggest failed: ${res.status}`);
  }

  const data = (await res.json()) as Partial<ShrineSuggestResponse>;
  const results = (Array.isArray(data.results) ? data.results : [])
    .map(normalizeCandidate)
    .filter((candidate): candidate is ShrineSuggestCandidate => candidate !== null);

  return {
    count: typeof data.count === "number" ? data.count : results.length,
    results,
  };
}
