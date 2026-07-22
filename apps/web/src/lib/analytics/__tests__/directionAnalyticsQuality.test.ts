import { describe, expect, it } from "vitest";
import {
  DIRECTION_EVENT_NAMES,
  DIRECTION_EVENT_QUALITY_RULES,
  sanitizeDirectionEventPayload,
} from "../../../../../../packages/shared/directionAnalytics";
import {
  buildDirectionAnalyticsQualityReport,
  detectDirectionAnalyticsAnomalies,
  DIRECTION_ANALYTICS_FORBIDDEN_KEYS,
  type DirectionAnalyticsQualityEvent,
} from "../../../../../../packages/shared/directionAnalyticsQuality";

const context = { sessionKey: "session-a", attemptKey: "attempt-a", candidateKey: "candidate-a" };
const webFunnel: DirectionAnalyticsQualityEvent[] = [
  { eventName: "direction_visit_date_set", payload: { platform: "web" }, ...context },
  { eventName: "direction_origin_result", payload: { platform: "web", origin_type: "device", result: "success" }, ...context },
  { eventName: "direction_condition_submitted", payload: { platform: "web", has_visit_date: true, has_origin: true }, ...context },
  { eventName: "direction_match_impression", payload: { platform: "web", matched: true, recommendation_rank: 1 }, ...context },
  { eventName: "direction_match_detail_opened", payload: { platform: "web", matched: true, recommendation_rank: 1 }, ...context },
  { eventName: "direction_match_route_clicked", payload: { platform: "web", matched: true, candidate_position: "hero" }, ...context },
];

const issueCodes = (events: readonly DirectionAnalyticsQualityEvent[]) =>
  buildDirectionAnalyticsQualityReport(events).issues.map((issue) => issue.code);

describe("direction analytics quality contract", () => {
  it("全6イベントを必須・任意属性と両platform付きで登録する", () => {
    expect(Object.keys(DIRECTION_EVENT_QUALITY_RULES)).toEqual(DIRECTION_EVENT_NAMES);
    for (const name of DIRECTION_EVENT_NAMES) {
      expect(DIRECTION_EVENT_QUALITY_RULES[name].requiredKeys).toContain("platform");
      expect(DIRECTION_EVENT_QUALITY_RULES[name].allowedPlatforms).toEqual(["web", "mobile"]);
    }
    expect(DIRECTION_EVENT_QUALITY_RULES.direction_match_route_clicked.optionalKeys).toContain("candidate_position");
  });

  it("Webとモバイルの正常ファネルを受け付ける", () => {
    expect(buildDirectionAnalyticsQualityReport(webFunnel)).toMatchObject({ valid: true, issues: [] });
    const mobile = webFunnel.map((event) => ({
      ...event,
      payload: { ...event.payload, platform: "mobile" },
    })).map((event) => event.eventName === "direction_match_route_clicked"
      ? { ...event, payload: { platform: "mobile", matched: true, recommendation_rank: 1 } }
      : event);
    expect(buildDirectionAnalyticsQualityReport(mobile)).toMatchObject({ valid: true, issues: [] });
  });

  it("未知イベント、必須属性欠落、不正platform、契約外属性を検出する", () => {
    expect(issueCodes([{ eventName: "direction_unknown", payload: { platform: "web" } }])).toContain("UNKNOWN_EVENT");
    expect(issueCodes([{ eventName: "direction_origin_result", payload: { platform: "web" } }])).toContain("MISSING_REQUIRED_KEY");
    expect(issueCodes([{ eventName: "direction_visit_date_set", payload: { platform: "desktop" } }])).toContain("INVALID_PLATFORM");
    expect(issueCodes([{ eventName: "direction_visit_date_set", payload: { platform: "web", matched: true } }])).toContain("UNEXPECTED_PAYLOAD_KEY");
  });

  it.each([
    ["device", "success"], ["device", "denied"], ["device", "failed"],
    ["station", "selected"], ["address", "selected"], ["prefecture", "selected"], ["disabled", "selected"],
  ])("有効なorigin組み合わせ %s + %s を許可する", (origin_type, result) => {
    expect(buildDirectionAnalyticsQualityReport([{ eventName: "direction_origin_result", payload: { platform: "web", origin_type, result } }]).valid).toBe(true);
  });

  it.each([
    ["station", "denied"], ["address", "success"], ["prefecture", "failed"], ["disabled", "success"], ["device", "selected"],
  ])("不正なorigin組み合わせ %s + %s を検出しserializerから除外する", (origin_type, result) => {
    expect(issueCodes([{ eventName: "direction_origin_result", payload: { platform: "web", origin_type, result } }])).toContain("INVALID_ORIGIN_COMBINATION");
    expect(sanitizeDirectionEventPayload("direction_origin_result", { platform: "web", origin_type, result } as never)).toEqual({ platform: "web" });
  });

  it("impressionは不一致を許可し、詳細・経路の不一致を検出する", () => {
    expect(buildDirectionAnalyticsQualityReport([{ eventName: "direction_match_impression", payload: { platform: "web", matched: false } }]).valid).toBe(true);
    expect(issueCodes([{ eventName: "direction_match_detail_opened", payload: { platform: "web", matched: false } }])).toContain("UNMATCHED_CANDIDATE_ACTION");
    expect(issueCodes([{ eventName: "direction_match_route_clicked", payload: { platform: "web", matched: false, candidate_position: "hero" } }])).toContain("UNMATCHED_CANDIDATE_ACTION");
  });

  it("candidate_positionの範囲・イベント・platform差を検証する", () => {
    expect(buildDirectionAnalyticsQualityReport([
      { eventName: "direction_match_impression", payload: { platform: "web", matched: true }, ...context },
      { eventName: "direction_match_route_clicked", payload: { platform: "web", matched: true, candidate_position: "other" }, ...context },
    ]).valid).toBe(true);
    expect(issueCodes([{ eventName: "direction_match_route_clicked", payload: { platform: "web", matched: true, candidate_position: "compact" } }])).toContain("INVALID_CANDIDATE_POSITION");
    expect(issueCodes([{ eventName: "direction_match_route_clicked", payload: { platform: "web", matched: true } }])).toContain("WEB_ROUTE_POSITION_MISSING");
    expect(issueCodes([{ eventName: "direction_match_impression", payload: { platform: "web", matched: true, candidate_position: "hero" } }])).toContain("UNEXPECTED_PAYLOAD_KEY");
    expect(buildDirectionAnalyticsQualityReport([{ eventName: "direction_match_route_clicked", payload: { platform: "mobile", matched: true } }]).issues.map((issue) => issue.code)).not.toContain("WEB_ROUTE_POSITION_MISSING");
  });
});

describe("direction analytics privacy", () => {
  it("禁止属性を一元管理し、表記揺れも検出する", () => {
    expect(DIRECTION_ANALYTICS_FORBIDDEN_KEYS).toContain("latitude");
    const payload = Object.fromEntries([
      ...DIRECTION_ANALYTICS_FORBIDDEN_KEYS.map((key) => [key, "fixed-private-value"]),
      ["googleMapsUrl", "https://www.google.com/maps/dir/"],
      ["shrineName", "固定神社"],
      ["consultationText", "固定相談文"],
    ]);
    const report = buildDirectionAnalyticsQualityReport([{ eventName: "direction_visit_date_set", payload: { platform: "web", ...payload } }]);
    expect(report.counts["issue:FORBIDDEN_PAYLOAD_KEY"]).toBe(DIRECTION_ANALYTICS_FORBIDDEN_KEYS.length + 3);
  });

  it("allowlist serializerは候補全体・位置・URL・本文を送らない", () => {
    const safe = sanitizeDirectionEventPayload("direction_match_route_clicked", {
      platform: "web", matched: true, candidate_position: "hero", latitude: 35.68,
      longitude: 139.76, shrine_name: "固定神社", shrine_address: "固定住所",
      route_url: "https://www.google.com/maps/dir/", consultation: "固定相談文",
      birthdate: "1990-01-01", recommendation_reason: "固定推薦理由",
    } as never);
    expect(safe).toEqual({ platform: "web", matched: true, candidate_position: "hero" });
    expect(JSON.stringify(safe)).not.toMatch(/35\.68|139\.76|固定|google\.com|1990/);
  });
});

describe("direction analytics sequence quality", () => {
  it("同一試行・同一候補のimpression重複を検出する", () => {
    const impression = { eventName: "direction_match_impression", payload: { platform: "web", matched: true }, ...context };
    expect(issueCodes([impression, impression])).toContain("DUPLICATE_IMPRESSION");
  });

  it("再相談の別試行は同じ候補でも重複扱いしない", () => {
    const event = { eventName: "direction_match_impression", payload: { platform: "web", matched: true }, sessionKey: "s", candidateKey: "c" };
    expect(buildDirectionAnalyticsQualityReport([{ ...event, attemptKey: "a" }, { ...event, attemptKey: "b" }])).toMatchObject({ valid: true, issues: [] });
  });

  it("表示なしの詳細・経路を検出する", () => {
    expect(issueCodes([{ eventName: "direction_match_detail_opened", payload: { platform: "web", matched: true }, ...context }])).toContain("MISSING_IMPRESSION");
    expect(issueCodes([{ eventName: "direction_match_route_clicked", payload: { platform: "web", matched: true, candidate_position: "hero" }, ...context }])).toContain("MISSING_IMPRESSION");
  });

  it("拒否後の手動選択を正常判定し、相談継続時の欠損だけwarningにする", () => {
    const denied = { eventName: "direction_origin_result", payload: { platform: "web", origin_type: "device", result: "denied" }, sessionKey: "s", attemptKey: "a" };
    const selected = { eventName: "direction_origin_result", payload: { platform: "web", origin_type: "station", result: "selected" }, sessionKey: "s", attemptKey: "a" };
    const submitted = { eventName: "direction_condition_submitted", payload: { platform: "web", has_visit_date: true, has_origin: true }, sessionKey: "s", attemptKey: "a" };
    expect(buildDirectionAnalyticsQualityReport([denied, selected, submitted])).toMatchObject({ valid: true, issues: [] });
    expect(issueCodes([denied, submitted])).toContain("MANUAL_FALLBACK_MISSING");
    expect(buildDirectionAnalyticsQualityReport([denied])).toMatchObject({ valid: true, issues: [] });
  });
});

describe("direction analytics anomaly thresholds", () => {
  const baseline = {
    sessions: 200, impressionDuplicates: 0, forbiddenPayloads: 0, unknownEvents: 0,
    invalidPlatforms: 0, locationSuccessRate: 0.8, deniedOrFailedRate: 0.2,
    manualFallbackRate: 0.5, detailEvents: 50, routeEvents: 20, impressionEvents: 100,
    invalidCandidatePositions: 0,
  };

  it("調査開始基準をwarningとして返し、機能の良否を断定しない", () => {
    const current = {
      ...baseline, impressionDuplicates: 1, forbiddenPayloads: 1, unknownEvents: 1,
      invalidPlatforms: 1, locationSuccessRate: 0.69, deniedOrFailedRate: 0.25,
      manualFallbackRate: 0.39, detailEvents: 101, invalidCandidatePositions: 1,
    };
    const issues = detectDirectionAnalyticsAnomalies(current, baseline);
    expect(issues.map((issue) => issue.code)).toEqual(expect.arrayContaining([
      "DUPLICATE_RATE_NONZERO", "FORBIDDEN_PAYLOAD_NONZERO", "UNKNOWN_EVENT_NONZERO",
      "INVALID_PLATFORM_NONZERO", "ACTION_EXCEEDS_IMPRESSION", "INVALID_POSITION_NONZERO",
      "LOCATION_SUCCESS_DROP", "LOCATION_FAILURE_RISE", "MANUAL_FALLBACK_DROP",
    ]));
    expect(issues.every((issue) => issue.severity === "warning")).toBe(true);
  });
});
