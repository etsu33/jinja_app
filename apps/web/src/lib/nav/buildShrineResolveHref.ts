// apps/web/src/lib/nav/buildShrineResolveHref.ts
import {
  pickAllowedShrineDetailQuery,
  pickQueryScalar,
  SHRINE_RESOLVE_ALLOWED_QUERY_KEYS,
} from "@/lib/nav/buildShrineHref";

export type ShrineResolveHrefOpts = {
  ctx?: "map" | "concierge" | null;
  tid?: string | null;
  query?: Record<string, string | number | boolean | null | undefined>;
};

function setIf(q: URLSearchParams, k: string, v: unknown) {
  if (v === null || v === undefined) return;
  const s = typeof v === "string" ? v : String(v);
  if (!s.trim()) return;
  q.set(k, s);
}

export function buildShrineResolveHref(placeId: string, opts: ShrineResolveHrefOpts = {}) {
  const q = new URLSearchParams();

  const ctx = opts.ctx ?? pickQueryScalar(opts.query, "ctx") ?? null;
  const tid = opts.tid ?? pickQueryScalar(opts.query, "tid") ?? null;

  const allowedQuery = pickAllowedShrineDetailQuery(opts.query, SHRINE_RESOLVE_ALLOWED_QUERY_KEYS);
  for (const [k, v] of Object.entries(allowedQuery)) {
    q.set(k, v);
  }

  setIf(q, "place_id", placeId);
  if (ctx) setIf(q, "ctx", ctx);
  if (tid) setIf(q, "tid", tid);

  return `/shrines/resolve?${q.toString()}`;
}
