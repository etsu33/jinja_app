export type ScoreV3Metrics = {
  top1_changed_rate_avg: number;
  activation_candidate_rate: number;
  avg_delta: number;
  max_abs_delta_max: number;
};

export type ScoreV3FunnelMetrics = {
  route_open_rate: number;
  save_rate: number;
  visit_done_rate: number;
  reflection_saved_rate: number;
};

export type ScoreV3Decision = {
  active_candidate: boolean;
  rollback_required: boolean;
  reasons: string[];
};

export type ScoreV3DashboardResponse = {
  score_v3: ScoreV3Metrics;
  funnel: ScoreV3FunnelMetrics;
  decision: ScoreV3Decision;
};
