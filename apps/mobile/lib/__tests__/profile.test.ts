import { describe, expect, it } from "vitest";
import { buildDerivedProfile, buildDirectionProfile, normalizeBirthday } from "../profile";

describe("profile calculation input", () => {
  it("normalizes slash-separated dates before calculating", () => {
    expect(normalizeBirthday("1984/05/15")).toBe("1984-05-15");
    expect(buildDerivedProfile({ birthday: "1984/05/15" }).lifePath).toBe("6");
  });

  it("does not produce NaN for incomplete or impossible dates", () => {
    expect(buildDerivedProfile({ birthday: "1984/05/" })).toEqual({
      kyusei: undefined,
      gogyo: undefined,
      lifePath: undefined,
    });
    expect(normalizeBirthday("2025-02-30")).toBeUndefined();
    expect(normalizeBirthday("2999-01-01")).toBeUndefined();
  });

  it("calculates annual lucky directions instead of returning a fixed direction", () => {
    expect(buildDirectionProfile({ birthday: "1984-05-15" }, new Date(2026, 6, 21))).toEqual({
      luckyDirection: "東",
      luckyDirections: ["東", "北西"],
      targetYear: 2026,
      calculationMethod: "annual_kyusei_v1",
      excludedDirections: ["北", "北東", "南", "南西"],
      source: "calculated",
    });
  });
});
