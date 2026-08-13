import { describe, expect, it } from "vitest";

import type { ConciergeReasonFact } from "@/lib/api/concierge";
import { adaptReasonFactsForViewModel } from "../adaptReasonFactsForViewModel";
import { buildRecommendationReasonViewModel } from "../buildRecommendationReasonViewModel";

function fact(type: string, label: string, overrides: Partial<ConciergeReasonFact> = {}): ConciergeReasonFact {
  return { type, label, evidence: [`${type}:${label}`], score: 1, is_primary: true, ...overrides };
}

describe("adaptReasonFactsForViewModel", () => {
  it.each([
    ["element", "火", { primary_axis: "element", matched_element: "火" }],
    ["need_tag", "仕事", { primary_axis: "need", matched_need_tags: ["仕事"] }],
    ["user_selected_tag", "厄除け", { primary_axis: "need", matched_need_tags: ["厄除け"] }],
    ["goriyaku_tag", "勝運", { primary_axis: "benefit", shrine_benefit: "勝運" }],
    ["history_theme", "再出発", { primary_axis: "feature", shrine_feature: "再出発" }],
    ["text_hint", "静かな境内", { primary_axis: "feature", shrine_feature: "静かな境内" }],
    ["visit_style", "自然", { primary_axis: "feature", visit_fit: "自然" }],
    ["fallback", "近隣候補から選定", { primary_axis: "fallback", fallback_reason: "近隣候補から選定" }],
  ])("%s Primaryを既存表示slotへ写像する", (type, label, expected) => {
    expect(adaptReasonFactsForViewModel([fact(type, label)])).toEqual(expect.objectContaining(expected));
  });

  it("unknown typeをfallbackへ変換せず無視する", () => {
    expect(adaptReasonFactsForViewModel([fact("unknown", "未知")])).toBeNull();
  });

  it("is_primaryが無ければscoreや配列順からPrimaryを作らない", () => {
    expect(adaptReasonFactsForViewModel([
      fact("element", "火", { is_primary: undefined, score: 999 }),
      fact("need_tag", "仕事", { is_primary: undefined, score: 1 }),
    ])).toBeNull();
  });

  it("複数Primaryでもscoreで再ランキングせず、最初の明示Primaryを採用する", () => {
    const adapted = adaptReasonFactsForViewModel([
      fact("need_tag", "仕事", { score: 1 }),
      fact("element", "火", { score: 999 }),
    ]);
    expect(adapted).toEqual(expect.objectContaining({ primary_fact_type: "need_tag", primary_fact_label: "仕事" }));
  });
});

describe("buildRecommendationReasonViewModel Backend fact consumption", () => {
  const build = (type: string, label: string) => buildRecommendationReasonViewModel({
    rec: { id: 999, name: "契約神社" },
    reasonFacts: [fact(type, label)],
    index: 0,
    mode: "need",
    needTags: [],
  });

  it.each([
    ["element", "火"],
    ["need_tag", "仕事"],
    ["history_theme", "再出発"],
    ["visit_style", "自然"],
    ["fallback", "近隣候補から選定"],
  ])("%s Primaryのlabelがvisible text用ViewModelへ届く", (type, label) => {
    const vm = build(type, label);
    expect([vm.list.primaryPhrase, vm.hero.catchCopy, vm.detail.shrineMeaning].join(" ")).toContain(label);
  });

  it("element PrimaryをHero見出し・catch copyへ反映する", () => {
    const vm = build("element", "火");
    expect(vm.hero.topReasonLabel).toBe("内容との一致が強い");
    expect(vm.hero.catchCopy).toBe("相性から無理なく選びたい時の神社");
    expect(vm.list.primaryPhrase).toContain("火");
  });

  it("history_theme Primaryを詳細meaning文言へ反映する", () => {
    const vm = build("history_theme", "再出発");
    expect(vm.detail.shrineMeaning).toContain("再出発");
  });

  it("is_primaryなしではfact labelをvisible textへ採用しない", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: { id: 999, name: "契約神社" },
      reasonFacts: [fact("element", "Frontendで推測禁止", { is_primary: undefined, score: 999 })],
      index: 0,
      mode: "need",
      needTags: [],
    });
    expect(JSON.stringify(vm)).not.toContain("Frontendで推測禁止");
  });
});
