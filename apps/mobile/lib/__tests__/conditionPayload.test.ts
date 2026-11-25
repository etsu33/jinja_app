import { describe, expect, it } from "vitest";
import { buildConditionFilters, buildConditionProfileContext } from "../conditionPayload";

describe("conditionPayload visit style authority", () => {
  it("keeps the current visit preference as structured visit_style_tags", () => {
    const condition = {
      visitStyleLabel: "静かに整えたい",
    };

    expect(buildConditionFilters(condition).visit_style_tags).toEqual(["quiet"]);

    const context = buildConditionProfileContext({ condition });
    expect(context.user_profile.visit_style_tags).toEqual(["quiet"]);
    expect(context.user_profile).not.toHaveProperty("worshipStyle");
  });

  it("コンシェルジュへ生年月日・出生時刻・出生地と、そこから計算した値を送らない", () => {
    // ドライブ「KAMI MUSUBI コンシェルジュとコンパスの役割の線引き」。backend も PR #3464 で入口で外す。
    const context = buildConditionProfileContext({ condition: { supportText: "静かに" } });
    expect(context).toEqual({ user_profile: { goriyaku_tag_ids: undefined, visit_style_tags: undefined } });
    expect(context).not.toHaveProperty("derived_profile");

    const filters = buildConditionFilters({ plannedVisitDate: "2026-12-01", supportText: "静かに" });
    expect(filters).not.toHaveProperty("birthdate");
    expect(filters.extra_condition).not.toContain("誕生日");
  });
});
