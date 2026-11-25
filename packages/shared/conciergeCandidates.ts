import { resolveShrineIdentity } from "./shrineIdentity";
export type ConciergeCandidate<T> = { record: T; sourceIndex: number } & (
  | { kind: "registered"; shrineId: number; placeId: string | null; recommendationRank: number }
  | { kind: "place"; shrineId: null; placeId: string; recommendationRank: null }
);
/** Opaque Place IDs: trim only, never infer identity from names, addresses or generic id. */
export function conciergePlaceId(record: unknown): string | null {
  if (!record || typeof record !== "object") return null;
  const value = record as Record<string, unknown>;
  const ids = [value.place_id, value.placeId].filter((v) => v !== undefined && v !== null);
  if (!ids.length || ids.some((v) => typeof v !== "string" || !v.trim())) return null;
  const normalized = new Set(ids.map((v) => (v as string).trim()));
  return normalized.size === 1 ? [...normalized][0] : null;
}
/** Presentation only: no scoring, sorting, merging or fabricated identity.
 * Keep the actual first record and source index, then partition stably.
 */
export function normalizeConciergeCandidates<T>(records: readonly T[]) {
  const ordered: ConciergeCandidate<T>[] = [];
  const seenShrines = new Set<number>();
  const seenPlaces = new Set<string>();
  let rank = 0;
  records.forEach((record, sourceIndex) => {
    const identity = resolveShrineIdentity(record, "registered_compat");
    const placeId = conciergePlaceId(record);
    if (identity.status === "resolved") {
      if (seenShrines.has(identity.shrineId)) return;
      seenShrines.add(identity.shrineId);
      ordered.push({
        record,
        sourceIndex,
        kind: "registered",
        shrineId: identity.shrineId,
        placeId,
        recommendationRank: ++rank,
      });
    } else if (identity.status === "absent" && placeId) {
      if (seenPlaces.has(placeId)) return;
      seenPlaces.add(placeId);
      ordered.push({ record, sourceIndex, kind: "place", shrineId: null, placeId, recommendationRank: null });
    }
    // Invalid/conflicting Shrine claims fail closed, including Place fallback.
  });
  // Preserve existing linked-identity compatibility without reordering or merging:
  // only a retained registered record can suppress its linked external reference.
  const linked = new Set(ordered.filter((c) => c.kind === "registered" && c.placeId).map((c) => c.placeId));
  const retained = ordered.filter((c) => c.kind === "registered" || !linked.has(c.placeId));
  return {
    ordered: retained,
    registered: retained.filter((c): c is ConciergeCandidate<T> & { kind: "registered" } => c.kind === "registered"),
    references: retained.filter((c): c is ConciergeCandidate<T> & { kind: "place" } => c.kind === "place"),
  };
}
