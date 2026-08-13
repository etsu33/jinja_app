// apps/web/src/lib/api/concierge/normalize.ts
import type { ConciergeReasonFact, ConciergeRecommendation } from "./types";

function toTrimmedString(v: unknown): string | null {
  if (v == null) return null;
  const s = typeof v === "string" ? v : String(v);
  const t = s.trim();
  return t ? t : null;
}

function pickReason(r: Record<string, any>): string | null {
  const exp = r.explanation;
  const expReason0 = Array.isArray(exp?.reasons) ? exp.reasons[0] : null;

  return (
    toTrimmedString(r.reason) ??
    toTrimmedString(r.one_liner) ??
    toTrimmedString(expReason0?.text) ??
    toTrimmedString(exp?.summary) ??
    (Array.isArray(r.bullets) ? toTrimmedString(r.bullets[0]) : null) ??
    null
  );
}

export function normalizeReasonFacts(input: unknown): ConciergeReasonFact[] {
  if (!Array.isArray(input)) return [];

  return input.filter((fact): fact is ConciergeReasonFact => {
    if (fact == null || typeof fact !== "object" || Array.isArray(fact)) return false;
    const candidate = fact as Record<string, unknown>;
    if (typeof candidate.type !== "string" || candidate.type.trim().length === 0) return false;
    if (typeof candidate.label !== "string" || candidate.label.trim().length === 0) return false;
    if (!Array.isArray(candidate.evidence) || !candidate.evidence.every((item) => typeof item === "string")) return false;
    if (typeof candidate.score !== "number" || !Number.isFinite(candidate.score)) return false;
    if (candidate.is_primary !== undefined && typeof candidate.is_primary !== "boolean") return false;
    return true;
  });
}

export function normalizeRecommendations(input: unknown): ConciergeRecommendation[] {
  if (!Array.isArray(input)) return [];

  return input
    .filter((x): x is Record<string, any> => x != null && typeof x === "object")
    .map((r) => {
      const nameRaw = (r.display_name ?? r.name ?? "").toString().trim();
      const name = nameRaw || "（名称不明）";

      const loc = typeof r.location === "string" ? r.location.trim() : "";
      const display_address = (r.display_address ?? null) || (loc ? loc : null);

      const reason = pickReason(r);

      return {
        ...r,
        name,
        display_name: (r.display_name ?? "").toString().trim() || name,
        display_address,
        reason,
        reason_facts: normalizeReasonFacts(r.reason_facts),
        is_dummy: r.is_dummy === true || r.__dummy === true,
        __dummy: r.__dummy === true,
      } as ConciergeRecommendation;
    });
}
