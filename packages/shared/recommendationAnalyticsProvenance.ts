export type RecommendationAnalyticsProvenance = {
  primaryReasonSource: string | null;
  isFallbackRecommendation: boolean | null;
  actionSource: string | null;
  actionSourceKeys: string[];
};

function trimmedString(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed || null;
}

function backendPrimaryFactType(reasonFacts: unknown): string | null {
  if (!Array.isArray(reasonFacts)) return null;

  for (const fact of reasonFacts) {
    if (!fact || typeof fact !== "object" || Array.isArray(fact)) continue;
    const candidate = fact as Record<string, unknown>;
    if (candidate.is_primary !== true) continue;
    return trimmedString(candidate.type);
  }

  return null;
}

export function recommendationAnalyticsProvenance(input: {
  primaryReasonSource?: unknown;
  reasonFacts?: unknown;
  actionSuggestionPreview?: unknown;
}): RecommendationAnalyticsProvenance {
  const primaryReasonSource =
    trimmedString(input.primaryReasonSource) ?? backendPrimaryFactType(input.reasonFacts);

  const preview =
    input.actionSuggestionPreview &&
    typeof input.actionSuggestionPreview === "object" &&
    !Array.isArray(input.actionSuggestionPreview)
      ? (input.actionSuggestionPreview as Record<string, unknown>)
      : null;
  const sourceRaw = preview?.action_source ?? preview?.actionSource;
  const source =
    sourceRaw && typeof sourceRaw === "object" && !Array.isArray(sourceRaw)
      ? trimmedString((sourceRaw as Record<string, unknown>).source)
      : null;
  const sourceKeysRaw = preview?.source_keys ?? preview?.sourceKeys;
  const actionSourceKeys = Array.isArray(sourceKeysRaw)
    ? sourceKeysRaw.flatMap((value) => {
        const key = trimmedString(value);
        return key ? [key] : [];
      })
    : [];

  return {
    primaryReasonSource,
    isFallbackRecommendation:
      primaryReasonSource === null ? null : primaryReasonSource === "fallback",
    actionSource: source,
    actionSourceKeys,
  };
}

export function recommendationAnalyticsProperties(
  provenance: RecommendationAnalyticsProvenance,
): Record<string, string | boolean> {
  return {
    ...(provenance.primaryReasonSource
      ? { primaryReasonSource: provenance.primaryReasonSource }
      : {}),
    ...(provenance.isFallbackRecommendation !== null
      ? { isFallbackRecommendation: provenance.isFallbackRecommendation }
      : {}),
    ...(provenance.actionSource ? { actionSource: provenance.actionSource } : {}),
    ...(provenance.actionSourceKeys.length > 0
      ? { actionSourceKeys: provenance.actionSourceKeys.join(",") }
      : {}),
  };
}

export function buildRecommendationResultSetId(
  threadId: string | number | null | undefined,
  recommendations: Array<{ shrineId: string | number | null | undefined }>,
): string {
  const signature = recommendations
    .map((item, index) => `${index + 1}:${item.shrineId ?? "unknown"}`)
    .join("|");
  return `${threadId ?? "unknown"}:${signature || "empty"}`;
}

// Recommendation Instance Identity Contract
// (docs/audit/recommendation-instance-identity-propagation.md, Option C):
// this only normalizes a value the Backend already produced (`rid`, embedded
// as `recommendation_instance_id` on each recommendation item). Frontend/
// Mobile must never generate, guess, or reconstruct this id -- an absent
// value (e.g. direct detail access with no recommendation origin) stays
// `null`, it is never synthesized.
export function normalizeRecommendationInstanceId(raw: unknown): string | null {
  return trimmedString(raw);
}

// Recommendation Impression Instance Dedup Contract
// (docs/audit/recommendation-strict-funnel-readiness.md §6, §14-1/2):
// the dedup boundary for a rendered Impression must be the Backend-issued
// recommendationInstanceId -- never resultSetId alone. resultSetId is a Frontend-composed
// shrine-order signature that collides across separate generations that happen to return
// the same shrines in the same order/rank; keying dedup on it suppressed the Impression
// for a new generation while its Click still fired (orphan click, no matching Impression).
// recommendationInstanceId is never generated here, only read; resultSetId is used only as
// a per-item fallback for the instance boundary when recommendationInstanceId is absent
// (e.g. malformed Backend payload), preserving prior collision-prone behavior instead of
// dropping the Impression outright. Shared by Web and Mobile so both dedup with the exact
// same algorithm, not just a similar one.
export function buildRecommendationImpressionDedupKey(params: {
  recommendationInstanceId: string | null | undefined;
  resultSetId: string;
  shrineId: string | number | null | undefined;
  rank: number;
  position?: string | null;
}): string {
  const instanceKey = params.recommendationInstanceId ?? params.resultSetId;
  return [
    instanceKey,
    "concierge_result_impression",
    params.shrineId ?? "unknown",
    params.position ?? "",
    params.rank,
  ].join(":");
}
