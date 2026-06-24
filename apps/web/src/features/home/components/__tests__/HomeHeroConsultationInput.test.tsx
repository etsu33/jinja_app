import { describe, expect, it } from "vitest";

import { buildConciergeHref } from "../HomeHeroConsultationInput";

describe("buildConciergeHref", () => {
  it("returns concierge URL with encoded theme when theme exists", () => {
    expect(buildConciergeHref("仕事の迷いを整理したい")).toBe(
      "/concierge?theme=%E4%BB%95%E4%BA%8B%E3%81%AE%E8%BF%B7%E3%81%84%E3%82%92%E6%95%B4%E7%90%86%E3%81%97%E3%81%9F%E3%81%84",
    );
  });

  it("returns concierge URL with theme and openFilter when both exist", () => {
    expect(buildConciergeHref("少し休みたい", { openFilter: true })).toBe(
      "/concierge?theme=%E5%B0%91%E3%81%97%E4%BC%91%E3%81%BF%E3%81%9F%E3%81%84&openFilter=1",
    );
  });

  it("returns concierge URL with only openFilter when theme is empty", () => {
    expect(buildConciergeHref("", { openFilter: true })).toBe("/concierge?openFilter=1");
  });

  it("returns concierge URL without query when theme is empty and openFilter is false", () => {
    expect(buildConciergeHref("")).toBe("/concierge");
  });
});
