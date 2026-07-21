import { describe, expect, it } from "vitest";
import { buildDerivedProfile, normalizeBirthday } from "../profile";

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
});
