import { describe, expect, it } from "vitest";
import { directionReferenceMatchCopy, validDirectionReferenceOrNull, type DirectionReference } from "../../../../packages/shared/directionReference";

const reference: DirectionReference = {
  visit_date: "2026-09-15",
  actual_direction: "東",
  reference_directions: ["東", "北西"],
  matched: true,
  calculation_method: "annual_monthly_kyusei_v1",
  note: "年盤と月盤による参考情報です。日盤は使用していません。",
};

describe("directionReferenceMatchCopy", () => {
  it("一致を非断定的な共通文言へ変換する", () => {
    expect(directionReferenceMatchCopy(reference)).toBe("現在地から見た方角が、予定日の参考方位と一致しています。");
  });

  it("不一致を優劣ではなく差異として表す", () => {
    expect(directionReferenceMatchCopy({ ...reference, matched: false })).toBe(
      "現在地から見た方角は、予定日の参考方位とは異なります。",
    );
  });

  it("未知の計算方式と不正な方角を表示契約から除外する", () => {
    expect(validDirectionReferenceOrNull({ ...reference, calculation_method: "unknown" })).toBeNull();
    expect(validDirectionReferenceOrNull({ ...reference, actual_direction: "上" })).toBeNull();
  });
});
