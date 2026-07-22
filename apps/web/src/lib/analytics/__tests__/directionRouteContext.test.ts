import { describe, expect, it } from "vitest";
import { parseDirectionRouteContext, withDirectionRouteContext } from "../directionRouteContext";

const reference = {
  visit_date: "2026-09-15",
  actual_direction: "東",
  reference_directions: ["東", "北西"],
  matched: true,
  calculation_method: "annual_monthly_kyusei_v1" as const,
  note: "年盤と月盤による参考情報です。日盤は使用していません。",
};

describe("direction route context", () => {
  it("有効な方位参考情報の分類値だけを詳細URLへ引き継ぐ", () => {
    expect(withDirectionRouteContext("/shrines/1?ctx=concierge", reference, "hero")).toBe(
      "/shrines/1?ctx=concierge&direction_matched=1&direction_position=hero",
    );
    expect(withDirectionRouteContext("/shrines/2", { ...reference, matched: false }, "other")).toBe(
      "/shrines/2?direction_matched=0&direction_position=other",
    );
  });

  it("方位参考情報がない、または契約上無効ならURLを変更しない", () => {
    expect(withDirectionRouteContext("/shrines/1", null, "hero")).toBe("/shrines/1");
    expect(withDirectionRouteContext("/shrines/1", { ...reference, calculation_method: "daily" } as never, "hero")).toBe(
      "/shrines/1",
    );
  });

  it("許可したbooleanと候補位置だけを読み取る", () => {
    expect(parseDirectionRouteContext({ direction_matched: "0", direction_position: "other" })).toEqual({
      matched: false,
      candidatePosition: "other",
    });
    expect(parseDirectionRouteContext({ direction_matched: "true", direction_position: "hero" })).toBeNull();
    expect(parseDirectionRouteContext({ direction_matched: "1", direction_position: "first" })).toBeNull();
  });
});
