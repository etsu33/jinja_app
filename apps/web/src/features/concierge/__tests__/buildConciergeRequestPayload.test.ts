import { describe, expect, it } from "vitest";
import { buildConciergeRequestPayload, normalizeQueryText } from "../buildConciergeRequestPayload";
import type { ConciergeChatFilters } from "../types/chatRequest";

// Request payload regression (Concierge Entry Frontend IA v2, Task 17).
// UI was reorganized into Initial(L1) / Assist / Personalize(L2/L3), but
// the request payload sent to the backend must be byte-for-byte unchanged
// for the same underlying signal values. Each test below isolates exactly
// one layer's contribution (per docs/product/concierge-input-architecture.md)
// and asserts every other field stays at its untouched baseline -- so a
// future change that leaks one layer's UI state into another layer's
// payload field is caught here.

const emptyBaseFilters: ConciergeChatFilters = {
  birthdate: undefined,
  goriyaku_tag_ids: undefined,
  extra_condition: undefined,
  crowd: undefined,
  duration_max_min: undefined,
  free_text: undefined,
};

const baseParams = {
  needText: "",
  temporaryBirthdate: "",
  savedProfile: null,
  baseFilters: emptyBaseFilters,
  visitPreferences: [] as readonly string[],
  plannedVisitDate: "",
  userOrigin: null,
};

describe("buildConciergeRequestPayload", () => {
  it("L1 only: query carries the consultation text, every other layer stays empty", () => {
    const payload = buildConciergeRequestPayload({
      ...baseParams,
      needText: "最近少し疲れていて、気持ちを落ち着ける参拝がしたい",
    });

    expect(payload.query).toBe("最近少し疲れていて、気持ちを落ち着ける参拝がしたい");
    expect(payload.birthdate).toBeUndefined();
    expect(payload.goriyaku_tag_ids).toBeUndefined();
    expect(payload.extra_condition).toBeUndefined();
    expect(payload.visit_preferences).toBeUndefined();
    expect(payload.visit_date).toBeUndefined();
    expect(payload.location).toBeUndefined();
    expect(payload.filters).toEqual({
      birthdate: undefined,
      goriyaku_tag_ids: undefined,
      extra_condition: undefined,
      crowd: undefined,
      duration_max_min: undefined,
      free_text: undefined,
    });
  });

  it("L1 + Assist: a chip-picked example produces the same payload shape as manual text (no separate Assist field)", () => {
    const manual = buildConciergeRequestPayload({
      ...baseParams,
      needText: "人との関係やご縁について、落ち着いて見つめ直したいです",
    });
    const viaChip = buildConciergeRequestPayload({
      ...baseParams,
      needText: "人との関係やご縁について、落ち着いて見つめ直したいです",
    });

    expect(viaChip).toEqual(manual);
    expect(viaChip.query).toBe("人との関係やご縁について、落ち着いて見つめ直したいです");
  });

  it("L1 + L2 (visit_preferences): adds visit_preferences only, leaves L3 fields untouched", () => {
    const payload = buildConciergeRequestPayload({
      ...baseParams,
      needText: "静かに過ごしたい",
      visitPreferences: ["quiet", "nature"],
    });

    expect(payload.query).toBe("静かに過ごしたい");
    expect(payload.visit_preferences).toEqual(["quiet", "nature"]);
    expect(payload.birthdate).toBeUndefined();
    expect(payload.goriyaku_tag_ids).toBeUndefined();
    expect(payload.visit_date).toBeUndefined();
    expect(payload.location).toBeUndefined();
  });

  it("L1 + L3-A (birthdate): adds birthdate to top-level, filters, and profile_context only", () => {
    const payload = buildConciergeRequestPayload({
      ...baseParams,
      needText: "相性を見てほしい",
      temporaryBirthdate: "1990-05-20",
    });

    expect(payload.birthdate).toBe("1990-05-20");
    expect(payload.filters?.birthdate).toBe("1990-05-20");
    expect(payload.profile_context?.user_profile).toMatchObject({ birthday: "1990-05-20" });
    expect(payload.goriyaku_tag_ids).toBeUndefined();
    expect(payload.visit_preferences).toBeUndefined();
    expect(payload.visit_date).toBeUndefined();
    expect(payload.location).toBeUndefined();
  });

  it("L1 + L3-B (goriyaku_tag_ids): adds goriyaku_tag_ids to top-level and filters only", () => {
    const payload = buildConciergeRequestPayload({
      ...baseParams,
      needText: "ご利益を絞りたい",
      baseFilters: { ...emptyBaseFilters, goriyaku_tag_ids: [3, 7] },
    });

    expect(payload.goriyaku_tag_ids).toEqual([3, 7]);
    expect(payload.filters?.goriyaku_tag_ids).toEqual([3, 7]);
    expect(payload.birthdate).toBeUndefined();
    expect(payload.visit_preferences).toBeUndefined();
    expect(payload.visit_date).toBeUndefined();
    expect(payload.location).toBeUndefined();
  });

  it("L1 + L3-C (visit_date + location): adds visit_date/location only, no Candidate/Profile fields", () => {
    const payload = buildConciergeRequestPayload({
      ...baseParams,
      needText: "来月お参りに行きたい",
      plannedVisitDate: "2026-09-15",
      userOrigin: { latitude: 35.6762, longitude: 139.6503, source: "device", accuracy: "precise" },
    });

    expect(payload.visit_date).toBe("2026-09-15");
    expect(payload.location).toEqual({ lat: 35.6762, lng: 139.6503 });
    expect(payload.birthdate).toBeUndefined();
    expect(payload.goriyaku_tag_ids).toBeUndefined();
    expect(payload.visit_preferences).toBeUndefined();
  });

  // Shared Birthday Context の解決順序。
  // 既存の Full Integration ケースは temporaryBirthdate と savedProfile.birthday が
  // 同値なので、どちらが勝つかを区別できない。ここで別々の値を与えて固定する。
  it("Shared Birthday: 今回入力したbirthdateを保存済みbirthdayより優先する", () => {
    const payload = buildConciergeRequestPayload({
      ...baseParams,
      needText: "相性を見てほしい",
      temporaryBirthdate: "2000-12-31",
      savedProfile: { birthday: "1990-05-20", birth_time: "08:30", birth_place: "東京都" },
    });

    expect(payload.birthdate).toBe("2000-12-31");
    expect(payload.filters?.birthdate).toBe("2000-12-31");
    expect(payload.profile_context?.user_profile).toMatchObject({ birthday: "2000-12-31" });
    // 保存済みの他項目は temporary birthday に置き換えられない
    expect(payload.profile_context?.user_profile).toMatchObject({
      birthTime: "08:30",
      birthPlace: "東京都",
    });
  });

  it("Shared Birthday: 今回入力がない場合は保存済みbirthdayを再利用する", () => {
    const payload = buildConciergeRequestPayload({
      ...baseParams,
      needText: "相性を見てほしい",
      temporaryBirthdate: "",
      savedProfile: { birthday: "1990-05-20", birth_time: null, birth_place: null },
    });

    expect(payload.birthdate).toBe("1990-05-20");
    expect(payload.filters?.birthdate).toBe("1990-05-20");
    expect(payload.profile_context?.user_profile).toMatchObject({ birthday: "1990-05-20" });
  });

  it("Shared Birthday: 今回入力も保存済みも無い場合はbirthdateを送らない", () => {
    const payload = buildConciergeRequestPayload({
      ...baseParams,
      needText: "相性を見てほしい",
      temporaryBirthdate: "",
      savedProfile: null,
    });

    expect(payload.birthdate).toBeUndefined();
    expect(payload.filters?.birthdate).toBeUndefined();
  });

  it("Full Integration: L1 + L2 + L3-A + L3-B + L3-C all combine without cross-contamination", () => {
    const payload = buildConciergeRequestPayload({
      needText: "仕事の迷いを整理したい",
      temporaryBirthdate: "1990-05-20",
      savedProfile: { birthday: "1990-05-20", birth_time: "08:30", birth_place: "東京都" },
      baseFilters: { ...emptyBaseFilters, goriyaku_tag_ids: [1], extra_condition: "駅近", free_text: "駅近" },
      visitPreferences: ["nearby"],
      plannedVisitDate: "2026-09-15",
      userOrigin: { latitude: 35.6762, longitude: 139.6503, source: "device", accuracy: "precise" },
    });

    expect(payload.query).toBe("仕事の迷いを整理したい");
    expect(payload.birthdate).toBe("1990-05-20");
    expect(payload.goriyaku_tag_ids).toEqual([1]);
    expect(payload.extra_condition).toBe("駅近");
    expect(payload.visit_preferences).toEqual(["nearby"]);
    expect(payload.visit_date).toBe("2026-09-15");
    expect(payload.location).toEqual({ lat: 35.6762, lng: 139.6503 });
    expect(payload.profile_context?.user_profile).toMatchObject({
      birthday: "1990-05-20",
      birthTime: "08:30",
      birthPlace: "東京都",
    });
    expect(payload.profile_context?.user_profile).not.toHaveProperty("worshipStyle");
    expect(payload.filters).toEqual({
      birthdate: "1990-05-20",
      goriyaku_tag_ids: [1],
      extra_condition: "駅近",
      crowd: undefined,
      duration_max_min: undefined,
      free_text: "駅近",
    });
  });

  it("empty query with an active filter falls back to a generic filter-refinement query (unchanged legacy behavior)", () => {
    const payload = buildConciergeRequestPayload({
      ...baseParams,
      needText: "",
      baseFilters: { ...emptyBaseFilters, goriyaku_tag_ids: [2] },
    });

    expect(payload.query).toBe("追加した条件に合う神社を提案してください。");
  });

  it("normalizeQueryText treats a birthdate-only free-text entry as empty (unchanged legacy behavior)", () => {
    expect(normalizeQueryText("1990-05-20")).toBe("");
    expect(normalizeQueryText("  仕事の相談  ")).toBe("仕事の相談");
  });
});
