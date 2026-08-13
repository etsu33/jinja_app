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
