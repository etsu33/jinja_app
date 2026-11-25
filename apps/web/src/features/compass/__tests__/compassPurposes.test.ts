import {
  COMPASS_PRIMARY_PURPOSE_COUNT,
  COMPASS_PURPOSES,
  COMPASS_PURPOSES_ORDERED,
  COMPASS_PURPOSE_LABELS_JA,
} from "../compassPurposes";

describe("compassPurposes", () => {
  it("COMPASS_PURPOSES_ORDERED is a reordering of COMPASS_PURPOSES, not a different set", () => {
    expect(new Set(COMPASS_PURPOSES_ORDERED)).toEqual(new Set(COMPASS_PURPOSES));
    expect(COMPASS_PURPOSES_ORDERED.length).toBe(COMPASS_PURPOSES.length);
  });

  it("every ordered purpose has a label", () => {
    for (const purpose of COMPASS_PURPOSES_ORDERED) {
      expect(COMPASS_PURPOSE_LABELS_JA[purpose]).toBeTruthy();
    }
  });

  it("primary count is smaller than the full taxonomy", () => {
    expect(COMPASS_PRIMARY_PURPOSE_COUNT).toBeGreaterThan(0);
    expect(COMPASS_PRIMARY_PURPOSE_COUNT).toBeLessThan(COMPASS_PURPOSES_ORDERED.length);
  });
});
