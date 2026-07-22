import { validDirectionReferenceOrNull, type DirectionReference } from "./directionReference";

const DIRECTION_LANGUAGE = /(?:方位|方角|吉方位|現在地から見た|予定日の参考)/;
const ASSERTIVE_LANGUAGE = /(?:必ず(?:良い結果|叶|成功)|絶対|行くべき|運気が(?:上がる|良くなる)|願いが叶う)/;

export type RecommendationReasonDisplay = {
  matchReason: string | null;
  reason: string | null;
  directionReference: DirectionReference | null;
};

function normalizeReason(value?: string | null): string | null {
  const text = (value ?? "").trim();
  if (!text || DIRECTION_LANGUAGE.test(text) || ASSERTIVE_LANGUAGE.test(text)) return null;
  return text;
}

export function hasAssertiveRecommendationLanguage(value?: string | null): boolean {
  return ASSERTIVE_LANGUAGE.test((value ?? "").trim());
}

export function buildRecommendationReasonDisplay(input: {
  matchReason?: string | null;
  reason?: string | null;
  directionReference?: unknown;
}): RecommendationReasonDisplay {
  const matchReason = normalizeReason(input.matchReason);
  const normalizedReason = normalizeReason(input.reason);

  return {
    matchReason,
    reason: normalizedReason && normalizedReason !== matchReason ? normalizedReason : null,
    directionReference: validDirectionReferenceOrNull(input.directionReference),
  };
}
