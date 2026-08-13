export type ConciergeReasonFact = {
  type: string;
  label: string;
  evidence: string[];
  score: number;
  is_primary?: boolean;
};

export type ConciergeReasonFacts = ConciergeReasonFact[];

function trimmedString(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

export function normalizeRecommendationReasonFacts(raw: unknown): ConciergeReasonFacts {
  if (!Array.isArray(raw)) return [];

  return raw.flatMap((item): ConciergeReasonFact[] => {
    if (!item || typeof item !== "object" || Array.isArray(item)) return [];

    const value = item as Record<string, unknown>;
    const type = trimmedString(value.type);
    const label = trimmedString(value.label);
    if (!type || !label) return [];

    const evidence = Array.isArray(value.evidence)
      ? value.evidence
          .map(trimmedString)
          .filter((entry): entry is string => entry !== null)
      : [];
    const score =
      typeof value.score === "number" && Number.isFinite(value.score)
        ? value.score
        : 0;

    return [{
      type,
      label,
      evidence,
      score,
      ...(typeof value.is_primary === "boolean"
        ? { is_primary: value.is_primary }
        : {}),
    }];
  });
}

export function findPrimaryReasonFact(
  facts: ConciergeReasonFacts | null | undefined,
): ConciergeReasonFact | null {
  return facts?.find((fact) => fact.is_primary === true) ?? null;
}

const DISPLAY_LABEL_BY_TYPE: Record<string, string> = {
  element: "生年月日との相性",
  need_tag: "相談との一致",
  user_selected_tag: "明示した条件",
  goriyaku_tag: "ご利益・意味",
  history_theme: "神社固有の文脈",
  text_hint: "ご利益・意味",
  visit_style: "参拝との相性",
  fallback: "参考情報",
};

export function buildReasonFactItems(facts: ConciergeReasonFacts | null | undefined) {
  return (facts ?? []).flatMap((fact) => {
    const displayLabel = DISPLAY_LABEL_BY_TYPE[fact.type];
    return displayLabel ? [{ label: displayLabel, value: fact.label }] : [];
  });
}

export function resolveActionEventHistoryTheme(args: {
  facts: ConciergeReasonFacts | null | undefined;
  actionSourceKeys: string[] | null | undefined;
}): string {
  if (!args.actionSourceKeys?.includes("ranked_history_theme")) return "";

  const primary = findPrimaryReasonFact(args.facts);
  return primary?.type === "history_theme" ? primary.label : "";
}
