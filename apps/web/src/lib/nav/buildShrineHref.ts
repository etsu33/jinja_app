// apps/web/src/lib/nav/buildShrineHref.ts
type QueryValue = string | number | boolean | null | undefined;

/** /shrines/:id で query に載せてよいキー（ctx/tid は opts 側で扱う） */
export const SHRINE_HREF_ALLOWED_QUERY_KEYS = ["place_id", "toast"] as const;

/** /shrines/resolve で query に載せてよいキー（place_id/ctx/tid は opts 側で扱う） */
export const SHRINE_RESOLVE_ALLOWED_QUERY_KEYS = ["toast"] as const;

export function pickQueryScalar(query: Record<string, QueryValue> | undefined, key: string): string | undefined {
  const v = query?.[key];
  if (v === null || v === undefined) return undefined;
  const s = String(v).trim();
  return s || undefined;
}

export function pickAllowedShrineDetailQuery(
  query: Record<string, QueryValue> | undefined,
  allowedKeys: readonly string[],
): Record<string, string> {
  if (!query) return {};

  const allowed = new Set(allowedKeys);
  const out: Record<string, string> = {};

  for (const [k, v] of Object.entries(query)) {
    if (!allowed.has(k)) continue;
    if (v === null || v === undefined) continue;

    const s = typeof v === "boolean" ? (v ? "1" : "0") : String(v);
    if (!s.trim()) continue;

    out[k] = s;
  }

  return out;
}

export type ShrineHrefOpts = {
  ctx?: "concierge" | string;
  tid?: number | string | null;
  recommendationInstanceId?: string | null;
  recommendationRank?: number | null;

  /** 追加クエリ（place_id / toast のみ許可） */
  query?: Record<string, string | number | boolean | null | undefined>;

  /** /shrines/:id の後ろに付けるサブパス（例: "goshuins"） */
  subpath?: string | null;

  /** #goshuins など（#は不要） */
  hash?: string | null;
};

export function buildShrineHref(shrineId: number | string, opts: ShrineHrefOpts = {}) {
  const id = encodeURIComponent(String(shrineId));

  const params = new URLSearchParams();

  const ctx = opts.ctx ?? pickQueryScalar(opts.query, "ctx");
  const tid = opts.tid ?? pickQueryScalar(opts.query, "tid");

  if (ctx) params.set("ctx", String(ctx));
  if (tid !== null && tid !== undefined && String(tid).trim() !== "") {
    params.set("tid", String(tid));
  }
  if (opts.recommendationInstanceId?.trim()) {
    params.set("recommendation_instance_id", opts.recommendationInstanceId.trim());
  }
  if (typeof opts.recommendationRank === "number" && Number.isInteger(opts.recommendationRank) && opts.recommendationRank > 0) {
    params.set("recommendation_rank", String(opts.recommendationRank));
  }

  const allowedQuery = pickAllowedShrineDetailQuery(opts.query, SHRINE_HREF_ALLOWED_QUERY_KEYS);
  for (const [k, v] of Object.entries(allowedQuery)) {
    params.set(k, v);
  }

  const sub = (opts.subpath ?? "").toString().trim();
  const base = `/shrines/${id}${sub ? `/${sub.replace(/^\/+/, "")}` : ""}`;

  const qs = params.toString();
  const withQs = qs ? `${base}?${qs}` : base;

  const hash = (opts.hash ?? "").toString().trim().replace(/^#/, "");
  return hash ? `${withQs}#${hash}` : withQs;
}
