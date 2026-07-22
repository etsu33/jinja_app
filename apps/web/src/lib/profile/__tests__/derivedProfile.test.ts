import { describe, expect, it } from "vitest";
import { buildDerivedProfile, buildDirectionProfile, buildProfileContext, normalizeBirthday } from "../derivedProfile";

describe("web profile derivation", () => {
  it("matches the mobile calculation for the same birthday", () => {
    expect(buildDerivedProfile({ birthday: "1984-05-15" })).toEqual({
      kyusei: "七赤金星",
      gogyo: "金",
      lifePath: "6",
    });
  });

  it("normalizes legacy dates and rejects invalid values", () => {
    expect(normalizeBirthday("1984/5/15")).toBe("1984-05-15");
    expect(buildDerivedProfile({ birthday: "1984/05/" }).lifePath).toBeUndefined();
  });

  it("builds the profile context sent to concierge", () => {
    expect(buildProfileContext({ birthday: "1984-05-15", birth_place: "東京都", worship_style: "朝参り" })).toMatchObject({
      user_profile: { birthdate: "1984-05-15", birthPlace: "東京都", worshipStyle: "朝参り" },
      derived_profile: { lifePath: "6" },
    });
    expect(buildProfileContext({ birthday: "1984-05-15" })).not.toHaveProperty("direction_profile");
  });

  it("matches the mobile annual direction result for the same date", () => {
    expect(buildDirectionProfile({ birthday: "1984-05-15" }, new Date(2026, 6, 21))).toEqual({
      luckyDirection: "東", luckyDirections: ["東", "北西"], targetYear: 2026,
      calculationMethod: "annual_kyusei_v1", excludedDirections: ["北", "北東", "南", "南西"], source: "calculated",
    });
  });
});
