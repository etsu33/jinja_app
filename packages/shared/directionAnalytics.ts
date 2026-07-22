export const DIRECTION_EVENT_NAMES = [
  "direction_visit_date_set",
  "direction_origin_result",
  "direction_condition_submitted",
  "direction_match_impression",
  "direction_match_detail_opened",
  "direction_match_route_clicked",
] as const;

export type DirectionPlatform = "web" | "mobile";
export type DirectionOriginType = "device" | "station" | "address" | "prefecture" | "disabled";
export type DirectionOriginResult = "success" | "denied" | "failed" | "selected";
export type DirectionCandidatePosition = "hero" | "other";
export type DirectionEventName = (typeof DIRECTION_EVENT_NAMES)[number];
export type DirectionEventPayload = {
  platform: DirectionPlatform;
  origin_type?: DirectionOriginType;
  result?: DirectionOriginResult;
  has_visit_date?: boolean;
  has_origin?: boolean;
  matched?: boolean;
  recommendation_rank?: number;
  candidate_position?: DirectionCandidatePosition;
};

export type DirectionEventPayloadKey = keyof DirectionEventPayload;
export type DirectionEventQualityRule = {
  requiredKeys: readonly DirectionEventPayloadKey[];
  optionalKeys: readonly DirectionEventPayloadKey[];
  allowedPlatforms: readonly DirectionPlatform[];
};

const BOTH_PLATFORMS = ["web", "mobile"] as const;
export const DIRECTION_EVENT_QUALITY_RULES: Record<DirectionEventName, DirectionEventQualityRule> = {
  direction_visit_date_set: {
    requiredKeys: ["platform"],
    optionalKeys: [],
    allowedPlatforms: BOTH_PLATFORMS,
  },
  direction_origin_result: {
    requiredKeys: ["platform", "origin_type", "result"],
    optionalKeys: [],
    allowedPlatforms: BOTH_PLATFORMS,
  },
  direction_condition_submitted: {
    requiredKeys: ["platform", "has_visit_date", "has_origin"],
    optionalKeys: [],
    allowedPlatforms: BOTH_PLATFORMS,
  },
  direction_match_impression: {
    requiredKeys: ["platform", "matched"],
    optionalKeys: ["recommendation_rank"],
    allowedPlatforms: BOTH_PLATFORMS,
  },
  direction_match_detail_opened: {
    requiredKeys: ["platform", "matched"],
    optionalKeys: ["recommendation_rank"],
    allowedPlatforms: BOTH_PLATFORMS,
  },
  direction_match_route_clicked: {
    requiredKeys: ["platform", "matched"],
    optionalKeys: ["recommendation_rank", "candidate_position"],
    allowedPlatforms: BOTH_PLATFORMS,
  },
};

export function directionEventAllowedKeys(name: DirectionEventName): ReadonlySet<DirectionEventPayloadKey> {
  const rule = DIRECTION_EVENT_QUALITY_RULES[name];
  return new Set([...rule.requiredKeys, ...rule.optionalKeys]);
}

const ORIGIN_TYPES = new Set<DirectionOriginType>(["device", "station", "address", "prefecture", "disabled"]);
const ORIGIN_RESULTS = new Set<DirectionOriginResult>(["success", "denied", "failed", "selected"]);
const ORIGIN_COMBINATIONS = new Set(["device:success", "device:denied", "device:failed", "station:selected", "address:selected", "prefecture:selected", "disabled:selected"]);

/**
 * Direction analytics uses an event-specific allowlist. Unknown keys are dropped
 * even when an untyped caller reaches this boundary, preventing location or form
 * values from leaking into the analytics provider.
 */
export function sanitizeDirectionEventPayload(
  name: DirectionEventName,
  payload: DirectionEventPayload & Record<string, unknown>,
): DirectionEventPayload {
  const safe: DirectionEventPayload = { platform: payload.platform === "mobile" ? "mobile" : "web" };

  if (name === "direction_origin_result") {
    const originType = payload.origin_type as DirectionOriginType;
    const result = payload.result as DirectionOriginResult;
    if (ORIGIN_TYPES.has(originType) && ORIGIN_RESULTS.has(result) && ORIGIN_COMBINATIONS.has(`${originType}:${result}`)) {
      safe.origin_type = originType;
      safe.result = result;
    }
  }

  if (name === "direction_condition_submitted") {
    if (typeof payload.has_visit_date === "boolean") safe.has_visit_date = payload.has_visit_date;
    if (typeof payload.has_origin === "boolean") safe.has_origin = payload.has_origin;
  }

  if (name === "direction_match_impression" || name === "direction_match_detail_opened" || name === "direction_match_route_clicked") {
    const validMatched = name === "direction_match_impression" ? typeof payload.matched === "boolean" : payload.matched === true;
    if (validMatched) safe.matched = payload.matched;
    if (validMatched && typeof payload.recommendation_rank === "number" && Number.isInteger(payload.recommendation_rank) && payload.recommendation_rank > 0) {
      safe.recommendation_rank = payload.recommendation_rank;
    }
  }

  if (name === "direction_match_route_clicked" && payload.matched === true && (payload.candidate_position === "hero" || payload.candidate_position === "other")) {
    safe.candidate_position = payload.candidate_position;
  }

  const allowedKeys = directionEventAllowedKeys(name);
  for (const key of Object.keys(safe) as DirectionEventPayloadKey[]) {
    if (!allowedKeys.has(key)) delete safe[key];
  }

  return safe;
}

export function directionEvent(name: DirectionEventName, payload: DirectionEventPayload & Record<string, unknown>) {
  return { name, payload: sanitizeDirectionEventPayload(name, payload) };
}
