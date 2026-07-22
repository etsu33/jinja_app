import { describe, expect, it } from "vitest";
import { directionEvent } from "../../../../packages/shared/directionAnalytics";
import { directionReferenceMatchCopy } from "../../../../packages/shared/directionReference";
import { prefectureOrigin, toOriginPayload, type UserOrigin } from "../../../../packages/shared/userOrigin";
import { buildRecommendationReasonDisplay } from "../../../../packages/shared/recommendationReasonDisplay";

const privateKeys = new Set(["lat", "lng", "latitude", "longitude", "address", "birthdate", "query", "consultation"]);

function expectPrivacySafe(payload: Record<string, unknown>) {
  expect(Object.keys(payload).filter((key) => privateKeys.has(key))).toEqual([]);
}

describe("mobile direction flow integration", () => {
  it("位置取得成功から送信・一致表示まで共通契約を維持する", () => {
    const origin: UserOrigin = { latitude: 35.681236, longitude: 139.767125, source: "device", displayName: "現在地", accuracy: "precise" };
    const originEvent = directionEvent("direction_origin_result", { platform: "mobile", origin_type: origin.source, result: "success" });
    const submitEvent = directionEvent("direction_condition_submitted", { platform: "mobile", has_visit_date: true, has_origin: true });

    expect(toOriginPayload(origin)).toEqual({ lat: 35.681236, lng: 139.767125 });
    expect(directionReferenceMatchCopy({
      visit_date: "2026-09-15", actual_direction: "東", reference_directions: ["東", "北西"], matched: true,
      calculation_method: "annual_monthly_kyusei_v1", note: "年盤と月盤による参考情報です。日盤は使用していません。",
    })).toBe("現在地から見た方角が、予定日の参考方位と一致しています。");
    expectPrivacySafe(originEvent.payload);
    expectPrivacySafe(submitEvent.payload);

    const display = buildRecommendationReasonDisplay({
      matchReason: "仕事の相談とご利益の一致です。",
      reason: "静かに向き合いやすい神社です。",
      directionReference: {
        visit_date: "2026-09-15", actual_direction: "東", reference_directions: ["東"], matched: true,
        calculation_method: "annual_monthly_kyusei_v1", note: "年盤と月盤による参考情報です。日盤は使用していません。",
      },
    });
    expect(Object.keys(display)).toEqual(["matchReason", "reason", "directionReference"]);
  });

  it("拒否後の手動選択、都道府県の概算、方位無効化を区別する", () => {
    const denied = directionEvent("direction_origin_result", { platform: "mobile", origin_type: "device", result: "denied" });
    const manual: UserOrigin = { latitude: 35.681236, longitude: 139.767125, source: "station", displayName: "東京駅", accuracy: "precise" };
    const approximate = prefectureOrigin("東京都");

    expect(denied.payload).toEqual({ platform: "mobile", origin_type: "device", result: "denied" });
    expect(toOriginPayload(manual)).toEqual({ lat: 35.681236, lng: 139.767125 });
    expect(approximate).toMatchObject({ source: "prefecture", accuracy: "approximate", displayName: "東京都" });
    expect(toOriginPayload(null)).toBeUndefined();
    expectPrivacySafe(denied.payload);
    expect(buildRecommendationReasonDisplay({ matchReason: "相談との一致", reason: "通常理由" }).directionReference).toBeNull();
  });
});
