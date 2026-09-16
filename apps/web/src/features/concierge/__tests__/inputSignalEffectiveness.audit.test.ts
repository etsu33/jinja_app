/**
 * Audit-only evidence for
 * docs/audit/concierge-input-signal-effectiveness-audit.md.
 *
 * These tests do NOT assert desired behaviour. They pin the CURRENT wiring so
 * the findings in that document are reproducible.
 *
 * Covered findings:
 *   CIS-001  「この条件で探す」(filter_apply) sends `mode: "compat"`, which
 *            flips the backend weight profile and enables astro_bonus.
 *   CIS-002  `crowd` / `duration_max_min` are derived by substring-matching
 *            `extraCondition`, but no preset value contains any trigger
 *            substring, so the derivation can never fire from the live UI.
 *   CIS-004  One 参拝スタイル preset click emits the same intent twice:
 *            as `extra_condition` free text and as `visit_preferences` tags.
 *   CIS-005  `birthdate` / `goriyaku_tag_ids` / `extra_condition` are each
 *            sent BOTH top-level and inside `filters`.
 */
import { describe, expect, it } from "vitest";

import { buildConciergeRequestPayload } from "@/features/concierge/buildConciergeRequestPayload";

/**
 * Every 参拝スタイル preset `value` string, copied verbatim from
 * apps/web/src/features/concierge/components/ConciergeFilterPanel.tsx
 * (QUICK_PRESET_GROUPS). These are the ONLY strings that can reach
 * `extraCondition` from the live UI -- the panel has no free-text field for it.
 */
const PRESET_EXTRA_CONDITION_VALUES = [
  "静かな雰囲気で、気持ちを落ち着けて整理できる場所がいい",
  "気持ちを切り替えて、前向きになれる場所がいい",
  "自然を感じながら、ゆっくり参拝できる場所がいい",
  "歴史や文化を感じながら、意味を受け取れる場所がいい",
  "できるだけ近い場所を優先して",
  "駅から行きやすく、移動の負担が少ない場所がいい",
  "有名で定番感があり、安心して参拝しやすい場所がいい",
  "混雑しにくい、落ち着いた場所がいい",
  "由緒や背景を感じながら参拝できる場所がいい",
  "御朱印も楽しみながら参拝できる場所がいい",
  "神話や祀られている神様の文脈に触れられる場所がいい",
  "境内をゆっくり歩きながら、落ち着いて過ごせる場所がいい",
] as const;

/**
 * The derivation in ConciergeClientFull.tsx (baseFilters memo):
 *   if (extra?.includes("ひとり") || extra?.includes("空いて")) crowd.push("quiet");
 *   if (extra?.includes("駅近")) duration_max_min = 30;
 */
const CROWD_TRIGGERS = ["ひとり", "空いて"] as const;
const DURATION_TRIGGER = "駅近";

const EMPTY_BASE_FILTERS = {
  birthdate: undefined,
  goriyaku_tag_ids: undefined,
  extra_condition: undefined,
  crowd: undefined,
  duration_max_min: undefined,
  free_text: undefined,
};

function buildPayload(overrides: Partial<Parameters<typeof buildConciergeRequestPayload>[0]> = {}) {
  return buildConciergeRequestPayload({
    needText: "仕事の迷いを整理したい",
    temporaryBirthdate: null,
    savedProfile: null,
    baseFilters: EMPTY_BASE_FILTERS,
    visitPreferences: [],
    plannedVisitDate: "",
    userOrigin: null,
    ...overrides,
  });
}

describe("CIS-002: the crowd / duration derivation cannot fire from the live UI", () => {
  it("no 参拝スタイル preset value contains a crowd trigger substring", () => {
    const matches = PRESET_EXTRA_CONDITION_VALUES.filter((value) =>
      CROWD_TRIGGERS.some((trigger) => value.includes(trigger)),
    );
    expect(matches).toEqual([]);
  });

  it("no 参拝スタイル preset value contains the duration trigger substring", () => {
    const matches = PRESET_EXTRA_CONDITION_VALUES.filter((value) => value.includes(DURATION_TRIGGER));
    expect(matches).toEqual([]);
  });

  it("the 人混みを避けたい preset does NOT produce crowd, even though it is about crowding", () => {
    const crowdPreset = "混雑しにくい、落ち着いた場所がいい";
    // The backend DOES map this text to the `less_crowded` visit-style tag
    // (temples/domain/extra_condition_tags.py), but the frontend `crowd`
    // field stays empty because neither trigger substring is present.
    expect(CROWD_TRIGGERS.some((t) => crowdPreset.includes(t))).toBe(false);
  });

  it("crowd / duration_max_min are absent from the payload when only presets were used", () => {
    const payload = buildPayload({
      baseFilters: { ...EMPTY_BASE_FILTERS, extra_condition: "混雑しにくい、落ち着いた場所がいい", free_text: "混雑しにくい、落ち着いた場所がいい" },
    });

    expect(payload.filters?.crowd).toBeUndefined();
    expect(payload.filters?.duration_max_min).toBeUndefined();
  });
});

describe("CIS-001: filter_apply flips the request mode to compat", () => {
  it("the entry submit path sends mode: need", () => {
    expect(buildPayload().mode).toBe("need");
  });

  it("an explicit mode override (filter_apply) is carried into the payload", () => {
    // ConciergeClientFull's "filter_apply" action spreads
    // `{ ...buildFilterPayload(), mode: "compat" }` -- the builder itself
    // honours input.mode, which is what makes the flip reach the backend.
    expect(buildPayload({ input: { mode: "compat" } }).mode).toBe("compat");
  });
});

describe("CIS-004 / CIS-005: duplicate representations in one request", () => {
  it("a preset click sends the same intent as free text AND as structured tags", () => {
    const presetText = "混雑しにくい、落ち着いた場所がいい";
    const payload = buildPayload({
      baseFilters: { ...EMPTY_BASE_FILTERS, extra_condition: presetText, free_text: presetText },
      visitPreferences: ["less_crowded"],
    });

    // Legacy free-text representation.
    expect(payload.extra_condition).toBe(presetText);
    expect(payload.filters?.extra_condition).toBe(presetText);
    expect(payload.filters?.free_text).toBe(presetText);
    // Structured representation of the same click.
    expect(payload.visit_preferences).toEqual(["less_crowded"]);
  });

  it("birthdate / goriyaku_tag_ids / extra_condition are sent both top-level and in filters", () => {
    const payload = buildPayload({
      temporaryBirthdate: "1990-05-05",
      baseFilters: {
        ...EMPTY_BASE_FILTERS,
        birthdate: "1990-05-05",
        goriyaku_tag_ids: [1, 2],
        extra_condition: "自然を感じながら、ゆっくり参拝できる場所がいい",
      },
    });

    expect(payload.birthdate).toBe("1990-05-05");
    expect(payload.filters?.birthdate).toBe("1990-05-05");

    expect(payload.goriyaku_tag_ids).toEqual([1, 2]);
    expect(payload.filters?.goriyaku_tag_ids).toEqual([1, 2]);

    expect(payload.extra_condition).toBe("自然を感じながら、ゆっくり参拝できる場所がいい");
    expect(payload.filters?.extra_condition).toBe("自然を感じながら、ゆっくり参拝できる場所がいい");
  });

  it("visit_preferences is top-level only (no filters duplication)", () => {
    const payload = buildPayload({ visitPreferences: ["quiet", "nature"] });

    expect(payload.visit_preferences).toEqual(["quiet", "nature"]);
    expect((payload.filters as Record<string, unknown>)?.visit_preferences).toBeUndefined();
  });
});

describe("CIS-003: Level 3-C context fields reach the payload", () => {
  it("visit_date and location are carried when set", () => {
    const payload = buildPayload({
      plannedVisitDate: "2026-10-01",
      userOrigin: { latitude: 35.6762, longitude: 139.6503, source: "prefecture", displayName: "東京都", accuracy: "approximate" } as any,
    });

    expect(payload.visit_date).toBe("2026-10-01");
    expect(payload.location).toEqual({ lat: 35.6762, lng: 139.6503 });
  });
});
