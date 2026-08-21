// Compass MVP UI types.
//
// Mirrors docs/product/compass-mvp-runtime-contract.md Section 5
// (CompassDirectionRuntime) and the response shape of
// backend/temples/api_views_compass.py::CompassRecommendationsView, which
// wraps temples.services.compass_recommendation_orchestrator's 6 result
// states (see that module's docstring). Kept local to the Compass feature
// rather than packages/shared -- no other app consumes it yet.
//
// "no_common_direction" is a VALID result (Runtime Contract Section 8
// Group B), never collapsed into "direction_filter_unavailable" (Group A --
// genuinely invalid/unavailable runtime). See compass-product-contract.md
// Section 2.1.

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
  // "monthly_kyusei_v1" = Monthly Fallback (Product Contract Section 2.2 /
  // Runtime Contract Section 5-1, #2508 Option C): referenceDirections come
  // from monthly-only guidance, not annual/monthly agreement. Type-only
  // widening -- no fallback-specific UI/copy is implemented by this change.
  calculationMethod: "annual_monthly_kyusei_v1" | "monthly_kyusei_v1";
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
  | "no_common_direction"
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
  recommendation_instance_id?: string | null;
  [key: string]: unknown;
};

export type CompassRecommendationsResponse = {
  state:
    | "invalid_purpose"
    | "direction_filter_unavailable"
    | "no_common_direction"
    | "direction_zero_candidates"
    | "evidence_zero_candidates"
    | "recommendation_success";
  purpose: string | null;
  direction_context: CompassDirectionRuntime | null;
  recommendation_instance_id: string;
  recommendations: CompassRecommendation[];
};
