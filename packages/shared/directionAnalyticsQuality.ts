import {
  DIRECTION_EVENT_NAMES,
  DIRECTION_EVENT_QUALITY_RULES,
  directionEventAllowedKeys,
  type DirectionEventName,
  type DirectionOriginResult,
  type DirectionOriginType,
  type DirectionPlatform,
} from "./directionAnalytics";
import forbiddenKeys from "./directionAnalyticsForbiddenKeys.json";

export const DIRECTION_ANALYTICS_FORBIDDEN_KEYS: readonly string[] = forbiddenKeys;

const FORBIDDEN_KEY_SET = new Set(DIRECTION_ANALYTICS_FORBIDDEN_KEYS.map(normalizeKey));
const EVENT_NAME_SET = new Set<string>(DIRECTION_EVENT_NAMES);
const ORIGIN_COMBINATIONS = new Set<string>([
  "device:success", "device:denied", "device:failed", "station:selected",
  "address:selected", "prefecture:selected", "disabled:selected",
]);
const ORIGIN_TYPES = new Set<DirectionOriginType>(["device", "station", "address", "prefecture", "disabled"]);
const ORIGIN_RESULTS = new Set<DirectionOriginResult>(["success", "denied", "failed", "selected"]);
const PLATFORMS = new Set<DirectionPlatform>(["web", "mobile"]);

function normalizeKey(key: string): string {
  return key.replace(/[^a-zA-Z0-9]/g, "").toLowerCase();
}

export type DirectionAnalyticsQualityEvent = {
  eventName: string;
  payload: Record<string, unknown>;
  sessionKey?: string;
  attemptKey?: string;
  candidateKey?: string;
};

export type DirectionAnalyticsIssueSeverity = "error" | "warning";
export type DirectionAnalyticsIssue = {
  code: string;
  severity: DirectionAnalyticsIssueSeverity;
  message: string;
  eventIndex?: number;
  eventName?: string;
};

export type DirectionAnalyticsQualityReport = {
  valid: boolean;
  issues: DirectionAnalyticsIssue[];
  counts: Record<string, number>;
};

function sequenceKey(event: DirectionAnalyticsQualityEvent): string | null {
  if (!event.sessionKey || !event.attemptKey || !event.candidateKey) return null;
  return `${event.sessionKey}:${event.attemptKey}:${event.candidateKey}`;
}

function attemptKey(event: DirectionAnalyticsQualityEvent): string | null {
  if (!event.sessionKey || !event.attemptKey) return null;
  return `${event.sessionKey}:${event.attemptKey}`;
}

export function buildDirectionAnalyticsQualityReport(
  events: readonly DirectionAnalyticsQualityEvent[],
): DirectionAnalyticsQualityReport {
  const issues: DirectionAnalyticsIssue[] = [];
  const counts: Record<string, number> = {};
  const impressions = new Set<string>();
  const deniedAt = new Map<string, number>();
  const manualSelectedAt = new Map<string, number>();

  const addIssue = (issue: DirectionAnalyticsIssue) => {
    issues.push(issue);
    counts[`issue:${issue.code}`] = (counts[`issue:${issue.code}`] ?? 0) + 1;
  };

  events.forEach((event, eventIndex) => {
    counts[event.eventName] = (counts[event.eventName] ?? 0) + 1;
    if (!EVENT_NAME_SET.has(event.eventName)) {
      addIssue({ code: "UNKNOWN_EVENT", severity: "error", message: `Unknown direction event: ${event.eventName}`, eventIndex, eventName: event.eventName });
      return;
    }

    const name = event.eventName as DirectionEventName;
    const rule = DIRECTION_EVENT_QUALITY_RULES[name];
    const allowedKeys = directionEventAllowedKeys(name);
    const payloadKeys = Object.keys(event.payload);

    for (const key of payloadKeys) {
      if (FORBIDDEN_KEY_SET.has(normalizeKey(key))) {
        addIssue({ code: "FORBIDDEN_PAYLOAD_KEY", severity: "error", message: `Forbidden payload key: ${key}`, eventIndex, eventName: name });
      }
      if (!allowedKeys.has(key as never)) {
        addIssue({ code: "UNEXPECTED_PAYLOAD_KEY", severity: "error", message: `Unexpected payload key for ${name}: ${key}`, eventIndex, eventName: name });
      }
    }

    for (const key of rule.requiredKeys) {
      if (!(key in event.payload)) {
        addIssue({ code: "MISSING_REQUIRED_KEY", severity: "error", message: `Missing required key for ${name}: ${key}`, eventIndex, eventName: name });
      }
    }

    const platform = event.payload.platform;
    if (!PLATFORMS.has(platform as DirectionPlatform) || !rule.allowedPlatforms.includes(platform as DirectionPlatform)) {
      addIssue({ code: "INVALID_PLATFORM", severity: "error", message: `Invalid platform for ${name}`, eventIndex, eventName: name });
    }

    if (name === "direction_origin_result") {
      const originType = event.payload.origin_type as DirectionOriginType;
      const result = event.payload.result as DirectionOriginResult;
      if (!ORIGIN_TYPES.has(originType)) addIssue({ code: "INVALID_ORIGIN_TYPE", severity: "error", message: "Invalid origin_type", eventIndex, eventName: name });
      if (!ORIGIN_RESULTS.has(result)) addIssue({ code: "INVALID_ORIGIN_RESULT", severity: "error", message: "Invalid origin result", eventIndex, eventName: name });
      if (ORIGIN_TYPES.has(originType) && ORIGIN_RESULTS.has(result) && !ORIGIN_COMBINATIONS.has(`${originType}:${result}`)) {
        addIssue({ code: "INVALID_ORIGIN_COMBINATION", severity: "error", message: `Invalid origin combination: ${originType} + ${result}`, eventIndex, eventName: name });
      }
      const attempt = attemptKey(event);
      if (attempt && originType === "device" && result === "denied") deniedAt.set(attempt, eventIndex);
      if (attempt && (originType === "station" || originType === "address") && result === "selected") manualSelectedAt.set(attempt, eventIndex);
    }

    if (name === "direction_condition_submitted") {
      if (typeof event.payload.has_visit_date !== "boolean" || typeof event.payload.has_origin !== "boolean") {
        addIssue({ code: "INVALID_SUBMIT_FLAGS", severity: "error", message: "Submit flags must be boolean", eventIndex, eventName: name });
      }
      const attempt = attemptKey(event);
      const denied = attempt ? deniedAt.get(attempt) : undefined;
      const selected = attempt ? manualSelectedAt.get(attempt) : undefined;
      if (denied !== undefined && (selected === undefined || selected < denied)) {
        addIssue({ code: "MANUAL_FALLBACK_MISSING", severity: "warning", message: "Consultation continued after device denial without a later manual origin selection", eventIndex, eventName: name });
      }
    }

    if (name.startsWith("direction_match_")) {
      if (typeof event.payload.matched !== "boolean") {
        addIssue({ code: "INVALID_MATCHED", severity: "error", message: "matched must be boolean", eventIndex, eventName: name });
      }
      const rank = event.payload.recommendation_rank;
      if (rank !== undefined && (typeof rank !== "number" || !Number.isInteger(rank) || rank <= 0)) {
        addIssue({ code: "INVALID_RECOMMENDATION_RANK", severity: "error", message: "recommendation_rank must be a positive integer", eventIndex, eventName: name });
      }
    }

    if ((name === "direction_match_detail_opened" || name === "direction_match_route_clicked") && event.payload.matched === false) {
      addIssue({ code: "UNMATCHED_CANDIDATE_ACTION", severity: "error", message: `${name} is limited to matched candidates`, eventIndex, eventName: name });
    }

    if (name === "direction_match_route_clicked") {
      const position = event.payload.candidate_position;
      if (position !== undefined && position !== "hero" && position !== "other") {
        addIssue({ code: "INVALID_CANDIDATE_POSITION", severity: "error", message: "candidate_position must be hero or other", eventIndex, eventName: name });
      }
      if (platform === "web" && position === undefined) {
        addIssue({ code: "WEB_ROUTE_POSITION_MISSING", severity: "error", message: "Web route events require candidate_position", eventIndex, eventName: name });
      }
    }

    const sequence = sequenceKey(event);
    if (name === "direction_match_impression" && sequence) {
      if (impressions.has(sequence)) {
        addIssue({ code: "DUPLICATE_IMPRESSION", severity: "error", message: "Duplicate impression in the same attempt and candidate", eventIndex, eventName: name });
      } else {
        impressions.add(sequence);
      }
    }
    if ((name === "direction_match_detail_opened" || name === "direction_match_route_clicked") && sequence && !impressions.has(sequence)) {
      addIssue({ code: "MISSING_IMPRESSION", severity: "error", message: `${name} has no preceding impression`, eventIndex, eventName: name });
    }
  });

  return { valid: !issues.some((issue) => issue.severity === "error"), issues, counts };
}

export type DirectionAnalyticsPeriodMetrics = {
  sessions: number;
  impressionDuplicates: number;
  forbiddenPayloads: number;
  unknownEvents: number;
  invalidPlatforms: number;
  locationSuccessRate: number;
  deniedOrFailedRate: number;
  manualFallbackRate: number;
  detailEvents: number;
  routeEvents: number;
  impressionEvents: number;
  invalidCandidatePositions: number;
};

export function detectDirectionAnalyticsAnomalies(
  current: DirectionAnalyticsPeriodMetrics,
  previous?: DirectionAnalyticsPeriodMetrics,
): DirectionAnalyticsIssue[] {
  const issues: DirectionAnalyticsIssue[] = [];
  const warning = (code: string, message: string) => issues.push({ code, severity: "warning", message });
  if (current.impressionDuplicates > 0) warning("DUPLICATE_RATE_NONZERO", "Impression duplicates were detected");
  if (current.forbiddenPayloads > 0) warning("FORBIDDEN_PAYLOAD_NONZERO", "Forbidden payloads were detected");
  if (current.unknownEvents > 0) warning("UNKNOWN_EVENT_NONZERO", "Unknown events were detected");
  if (current.invalidPlatforms > 0) warning("INVALID_PLATFORM_NONZERO", "Invalid platforms were detected");
  if (current.detailEvents > current.impressionEvents || current.routeEvents > current.impressionEvents) warning("ACTION_EXCEEDS_IMPRESSION", "Detail or route events exceed impressions");
  if (current.invalidCandidatePositions > 0) warning("INVALID_POSITION_NONZERO", "Invalid candidate positions were detected");
  if (previous) {
    const reaches = (delta: number, threshold: number) => delta + Number.EPSILON >= threshold;
    if (reaches(previous.locationSuccessRate - current.locationSuccessRate, 0.1)) warning("LOCATION_SUCCESS_DROP", "Location success rate dropped by at least 10 points");
    if (reaches(current.deniedOrFailedRate - previous.deniedOrFailedRate, 0.05)) warning("LOCATION_FAILURE_RISE", "Denied or failed rate increased by at least 5 points");
    if (reaches(previous.manualFallbackRate - current.manualFallbackRate, 0.1)) warning("MANUAL_FALLBACK_DROP", "Manual fallback rate dropped by at least 10 points");
  }
  return issues;
}
