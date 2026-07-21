import { describe, expect, it } from "vitest";
import { buildDerivedProfile, buildProfileContext, normalizeBirthday } from "../derivedProfile";

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
  });
});
