import { describe, expect, it } from "vitest";
import {
  buildRecommendationReasonDisplay,
  hasAssertiveRecommendationLanguage,
} from "../../../../../../../packages/shared/recommendationReasonDisplay";

describe("recommendation reason display contract", () => {
  it("主理由、通常理由、方位参考情報を独立した順序で返す", () => {
    const directionReference = {
      visit_date: "2026-09-15", actual_direction: "東", reference_directions: ["東"], matched: true,
      calculation_method: "annual_monthly_kyusei_v1" as const, note: "年盤と月盤による参考情報です。日盤は使用していません。",
    };
    expect(buildRecommendationReasonDisplay({
      matchReason: "仕事の相談と厄除けのご利益が重なります。",
      reason: "静かに気持ちを整えやすい神社です。",
      directionReference,
    })).toEqual({
      matchReason: "仕事の相談と厄除けのご利益が重なります。",
      reason: "静かに気持ちを整えやすい神社です。",
      directionReference,
    });
  });

  it("方位混入、重複、断定表現を主理由と通常理由から除外する", () => {
    expect(buildRecommendationReasonDisplay({
      matchReason: "吉方位なのでこの神社へ行くべきです。",
      reason: "運気が上がるため必ず願いが叶います。",
    })).toEqual({ matchReason: null, reason: null, directionReference: null });
    expect(buildRecommendationReasonDisplay({ matchReason: "相談との一致", reason: "相談との一致" }).reason).toBeNull();
    expect(hasAssertiveRecommendationLanguage("この神社へ行くべきです")).toBe(true);
  });

  it("direction_reference欠落時は方位表示データを作らない", () => {
    expect(buildRecommendationReasonDisplay({ matchReason: "相談との一致", reason: "通常の推薦理由" }).directionReference).toBeNull();
  });
});
