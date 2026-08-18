// Compass MVP UI types.
//
// Mirrors docs/product/compass-mvp-runtime-contract.md Section 5
// (CompassDirectionRuntime) and the response shape of
// backend/temples/api_views_compass.py::CompassRecommendationsView, which
// wraps temples.services.compass_recommendation_orchestrator's 5 fail-safe
// states (see that module's docstring). Kept local to the Compass feature
// rather than packages/shared -- no other app consumes it yet.

export type CompassPurpose =
  | "love"
  | "relationship"
  | "marriage"
  | "communication"
  | "career"
  | "money"
  | "study"
  | "health"
  | "mental"
  | "protection"
  | "courage"
  | "focus"
  | "rest"
  | "family"
  | "travel_safe";

export type CompassDirectionRuntime = {
  targetDate: string;
  targetYear: number;
  solarMonthIndex: number;
  referenceDirections: string[];
  calculationMethod: "annual_monthly_kyusei_v1";
  note: string;
};

// Every state the backend orchestrator can return, plus the frontend-only
// states that never reach the network (birthdate/origin missing before
// submit) and the two states no server response maps to (initial/loading).
// Never collapsed into each other -- see Section 13 of the Phase 5 brief:
// "Do not collapse: direction unavailable and zero candidates into the
// same UX state."
export type CompassUiState =
  | "initial"
  | "birthdate_missing"
  | "origin_missing"
  | "origin_permission_denied"
  | "loading"
  | "invalid_purpose"
  | "direction_filter_unavailable"
  | "direction_zero_candidates"
  | "evidence_zero_candidates"
  | "recommendation_success"
  | "backend_error";

export type CompassRecommendation = {
  shrine_id?: number | string | null;
  id?: number | string | null;
  name?: string | null;
  address?: string | null;
  distance_m?: number | null;
  reason?: string | null;
  place_id?: string | null;
  [key: string]: unknown;
};

export type CompassRecommendationsResponse = {
  state:
    | "invalid_purpose"
    | "direction_filter_unavailable"
    | "direction_zero_candidates"
    | "evidence_zero_candidates"
    | "recommendation_success";
  purpose: string | null;
  direction_context: CompassDirectionRuntime | null;
  recommendations: CompassRecommendation[];
};
