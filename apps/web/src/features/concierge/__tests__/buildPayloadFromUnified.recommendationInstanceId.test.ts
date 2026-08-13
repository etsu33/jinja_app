import { describe, it, expect } from "vitest";
import { buildPayloadFromUnified } from "../buildPayloadFromUnified";

// docs/audit/recommendation-instance-identity-propagation.md:
// Backend rid (embedded as recommendation_instance_id on each item) must reach the
// normalized item unchanged -- this is the single source both the impression/click
// events (via ConciergeSectionsRenderer) and the detail page (via the thread snapshot
// that persists this same normalized-equivalent raw item) read from.

const baseFilterState: any = {
  isOpen: false,
  birthdate: "",
  element4: null,
  goriyakuTags: [],
  suggestedTags: [],
  selectedTagIds: [],
  tagsLoading: false,
  tagsError: null,
  extraCondition: "",
};

describe("buildPayloadFromUnified - recommendationInstanceId", () => {
  it("registered item(shrine_idあり)へBackendのrecommendation_instance_idをそのまま複製する", () => {
    const u: any = {
      data: {
        recommendations: [
          { shrine_id: 10, display_name: "S1", reason: "R1", recommendation_instance_id: "a1b2c3d4" },
        ],
      },
      thread: { id: 1 },
    };

    const p = buildPayloadFromUnified(u, baseFilterState);
    const items = (p?.sections.find((s: any) => s.type === "recommendations") as any)?.items;
    expect(items[0].recommendationInstanceId).toBe("a1b2c3d4");
  });

  it("place item(place_idのみ)へも同じ値を複製する", () => {
    const u: any = {
      data: {
        recommendations: [
          { place_id: "P10", display_name: "S1", reason: "R1", recommendation_instance_id: "a1b2c3d4" },
        ],
      },
      thread: { id: 1 },
    };

    const p = buildPayloadFromUnified(u, baseFilterState);
    const items = (p?.sections.find((s: any) => s.type === "recommendations") as any)?.items;
    expect(items[0].recommendationInstanceId).toBe("a1b2c3d4");
  });

  it("値が無ければnullのまま、Frontendで合成しない", () => {
    const u: any = {
      data: {
        recommendations: [{ shrine_id: 11, display_name: "S2", reason: "R2" }],
      },
      thread: { id: 1 },
    };

    const p = buildPayloadFromUnified(u, baseFilterState);
    const items = (p?.sections.find((s: any) => s.type === "recommendations") as any)?.items;
    expect(items[0].recommendationInstanceId).toBeNull();
  });

  it("同一raw入力を複数回正規化しても同じ値になる(再render相当で不変)", () => {
    const rec = { shrine_id: 12, display_name: "S3", reason: "R3", recommendation_instance_id: "stable-id" };
    const u: any = { data: { recommendations: [rec] }, thread: { id: 1 } };

    const first = buildPayloadFromUnified(u, baseFilterState);
    const second = buildPayloadFromUnified(u, baseFilterState);

    const firstId = (first?.sections.find((s: any) => s.type === "recommendations") as any)?.items[0]
      .recommendationInstanceId;
    const secondId = (second?.sections.find((s: any) => s.type === "recommendations") as any)?.items[0]
      .recommendationInstanceId;

    expect(firstId).toBe("stable-id");
    expect(secondId).toBe("stable-id");
  });
});
