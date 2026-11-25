// Mobile コンパスの計測。Event名と項目は Web の CompassClient.tsx（compass_entry /
// compass_result）に揃え、platform: "mobile" で区別する。
// 生年月日・座標・相談文は送らない（has_birthdate と origin_mode だけ）。
import { track } from "./analytics";
import type { CompassCalculationMethod, CompassPurpose, CompassResultState } from "./compass";
import type { UserOriginSource } from "../../../packages/shared/userOrigin";

export function trackCompassEntry(referrerSource: "home" | "direct"): void {
  track("compass_entry", { referrer_source: referrerSource, platform: "mobile" });
}

export type CompassResultEvent = {
  resultState: CompassResultState | "backend_error";
  purpose: CompassPurpose;
  originMode: UserOriginSource | null;
  recommendationCount: number | null;
  recommendationInstanceId: string | null;
  calculationMethod: CompassCalculationMethod | null;
  distanceStageKm: 15 | 30 | 60 | null;
  directionCandidateCount: number | null;
  distanceCandidateCount: number | null;
};

export function trackCompassResult(event: CompassResultEvent): void {
  track("compass_result", {
    result_state: event.resultState,
    purpose: event.purpose,
    origin_mode: event.originMode,
    has_birthdate: true,
    recommendation_count: event.recommendationCount,
    recommendationInstanceId: event.recommendationInstanceId,
    calculationMethod: event.calculationMethod,
    distance_stage_km: event.distanceStageKm,
    direction_candidate_count: event.directionCandidateCount,
    distance_candidate_count: event.distanceCandidateCount,
    platform: "mobile",
  });
}
