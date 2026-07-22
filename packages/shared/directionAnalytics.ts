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

const ORIGIN_TYPES = new Set<DirectionOriginType>(["device", "station", "address", "prefecture", "disabled"]);
const ORIGIN_RESULTS = new Set<DirectionOriginResult>(["success", "denied", "failed", "selected"]);

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
    if (ORIGIN_TYPES.has(originType)) safe.origin_type = originType;
    if (ORIGIN_RESULTS.has(result)) safe.result = result;
  }

  if (name === "direction_condition_submitted") {
    if (typeof payload.has_visit_date === "boolean") safe.has_visit_date = payload.has_visit_date;
    if (typeof payload.has_origin === "boolean") safe.has_origin = payload.has_origin;
  }

  if (name === "direction_match_impression" || name === "direction_match_detail_opened" || name === "direction_match_route_clicked") {
    if (typeof payload.matched === "boolean") safe.matched = payload.matched;
    if (typeof payload.recommendation_rank === "number" && Number.isInteger(payload.recommendation_rank) && payload.recommendation_rank > 0) {
      safe.recommendation_rank = payload.recommendation_rank;
    }
  }

  if (name === "direction_match_route_clicked" && (payload.candidate_position === "hero" || payload.candidate_position === "other")) {
    safe.candidate_position = payload.candidate_position;
  }

  return safe;
}

export function directionEvent(name: DirectionEventName, payload: DirectionEventPayload & Record<string, unknown>) {
  return { name, payload: sanitizeDirectionEventPayload(name, payload) };
}
