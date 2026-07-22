export type DirectionPlatform = "web" | "mobile";
export type DirectionOriginType = "device" | "station" | "address" | "prefecture" | "disabled";
export type DirectionEventName = "direction_visit_date_set" | "direction_origin_result" | "direction_condition_submitted" | "direction_match_impression" | "direction_match_detail_opened" | "direction_match_route_clicked";
export type DirectionEventPayload = { platform: DirectionPlatform; origin_type?: DirectionOriginType; result?: "success" | "denied" | "failed" | "selected"; has_visit_date?: boolean; has_origin?: boolean; matched?: boolean; recommendation_rank?: number };
export function directionEvent(name: DirectionEventName, payload: DirectionEventPayload) { return { name, payload }; }
