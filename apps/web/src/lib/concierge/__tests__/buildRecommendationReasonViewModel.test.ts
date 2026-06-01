import { describe, expect, it } from "vitest";
import { buildRecommendationReasonViewModel } from "../buildRecommendationReasonViewModel";

describe("buildRecommendationReasonViewModel", () => {
  it("query入力で primary_reason が need系になる", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: {
        breakdown: { matched_need_tags: ["転機", "仕事"] },
        fallback_mode: "none",
      },
      index: 0,
      mode: "need",
      needTags: ["転機", "仕事"],
    });

    expect(vm.inputType).toBe("query");
    expect(vm.why.reasonKeys.primary).toBe("need_match");
    expect(vm.why.primaryReason.length).toBeGreaterThan(0);
    expect(vm.hero.topReasonLabel).toBe("相談との一致が強い");
  });

  it("birthdateのみで primary_reason が相性系になる", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: {
        astro_elements: ["water"],
        astro_priority: 2,
        fallback_mode: "none",
      },
      index: 0,
      mode: "compat",
      birthdate: "1992-08-10",
      needTags: [],
    });

    expect(vm.inputType).toBe("birthdate");
    expect(vm.why.reasonKeys.primary).toBe("element_match");
    expect(vm.why.primaryReason.length).toBeGreaterThan(0);
    expect(vm.hero.topReasonLabel).toBe("生年月日との重なりが強い");
  });

  it("fallback時に need文が出ない", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: {
        breakdown: { matched_need_tags: ["転機"] },
        fallback_mode: "nearby_unfiltered",
        distance_m: 550,
      },
      index: 0,
      mode: "need",
      needTags: ["転機"],
    });

    expect(vm.inputType).toBe("fallback");
    expect(vm.why.primaryReason).not.toContain("転機");
    expect(vm.why.summary).not.toContain("願い");
  });

  it("secondary_reason が2件以上出ない", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: {
        breakdown: { matched_need_tags: ["仕事", "転機", "挑戦"] },
        fallback_mode: "none",
        distance_m: 300,
        popular_score: 0.8,
      },
      index: 1,
      mode: "need",
      needTags: ["仕事"],
    });

    expect(typeof vm.why.secondaryReason === "string" || typeof vm.why.secondaryReason === "undefined").toBe(true);
  });

  it("summary が1行で重複しない", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: {
        breakdown: { matched_need_tags: ["厄除け"] },
        fallback_mode: "none",
      },
      index: 1,
      mode: "need",
      needTags: ["厄除け"],
    });

    expect(vm.why.summary.includes("\n")).toBe(false);
    expect(vm.why.summary).not.toBe(vm.why.primaryReason);
    expect(vm.why.summary).not.toBe(vm.why.secondaryReason);
  });

  it("top1 のみ reason_label が表示される", () => {
    const a = buildRecommendationReasonViewModel({
      rec: { breakdown: { matched_need_tags: ["転機"] }, fallback_mode: "none" },
      index: 0,
      mode: "need",
      needTags: ["転機"],
    });

    const b = buildRecommendationReasonViewModel({
      rec: { breakdown: { matched_need_tags: ["転機"] }, fallback_mode: "none" },
      index: 1,
      mode: "need",
      needTags: ["転機"],
    });

    expect(a.hero.topReasonLabel).toBeTruthy();
    expect(b.hero.topReasonLabel).toBeUndefined();
  });

  it("reason文の代表パターンを snapshot で固定する", () => {
    const samples = {
      query: buildRecommendationReasonViewModel({
        rec: { breakdown: { matched_need_tags: ["転機"] }, fallback_mode: "none" },
        index: 0,
        mode: "need",
        needTags: ["転機"],
      }),
      birthdate: buildRecommendationReasonViewModel({
        rec: { astro_elements: ["water"], astro_priority: 2, fallback_mode: "none" },
        index: 0,
        mode: "compat",
        birthdate: "1992-08-10",
        needTags: [],
      }),
      fallback: buildRecommendationReasonViewModel({
        rec: { fallback_mode: "nearby_unfiltered", popular_score: 0.9 },
        index: 0,
        mode: "need",
        needTags: ["転機"],
      }),
    };

    expect(samples).toMatchSnapshot();
  });

  it("③の shrineMeaning が神社側の意味だけに絞られる", () => {
    const cases = [
      {
        label: "厄除け",
        params: {
          rec: { breakdown: { matched_need_tags: ["厄除け"] }, fallback_mode: "none" },
          index: 0,
          mode: "need" as const,
          needTags: ["厄除け"],
        },
      },
      {
        label: "仕事",
        params: {
          rec: { breakdown: { matched_need_tags: ["仕事"] }, fallback_mode: "none" },
          index: 0,
          mode: "need" as const,
          needTags: ["仕事"],
        },
      },
      {
        label: "金運",
        params: {
          rec: { breakdown: { matched_need_tags: ["金運"] }, fallback_mode: "none" },
          index: 0,
          mode: "need" as const,
          needTags: ["金運"],
        },
      },
      {
        label: "転機",
        params: {
          rec: { breakdown: { matched_need_tags: ["転機"] }, fallback_mode: "none" },
          index: 0,
          mode: "need" as const,
          needTags: ["転機"],
        },
      },
      {
        label: "compat",
        params: {
          rec: { astro_elements: ["water"], astro_priority: 2, fallback_mode: "none" },
          index: 0,
          mode: "compat" as const,
          birthdate: "1992-08-10",
          needTags: [],
        },
      },
      {
        label: "distance fallback",
        params: {
          rec: {
            breakdown: { matched_need_tags: ["転機"] },
            reason_facts: { primary_axis: "distance" as const, distance_label: "550m" },
            fallback_mode: "nearby_unfiltered",
            distance_m: 550,
          },
          index: 0,
          mode: "need" as const,
          needTags: ["転機"],
        },
      },
    ];

    for (const sample of cases) {
      const vm = buildRecommendationReasonViewModel(sample.params);
      const sentences = vm.detail.shrineMeaning.match(/[^。]+。/g) ?? [];

      expect(sentences, sample.label).toHaveLength(1);
      expect(vm.detail.shrineMeaning, sample.label).toMatch(/置きやすい場所です/);
      expect(vm.detail.shrineMeaning, sample.label).not.toContain("今は、");
      expect(vm.detail.shrineMeaning, sample.label).not.toContain("ご利益");
      expect(vm.detail.shrineMeaning, sample.label).not.toContain("由緒");
      expect(vm.detail.shrineMeaning, sample.label).not.toBe(vm.detail.heroMeaningCopy);
    }
  });

  it("actionMeaning が次の向き合い方を補完する", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: { breakdown: { matched_need_tags: ["転機"] }, fallback_mode: "none" },
      index: 0,
      mode: "need",
      needTags: ["転機"],
    });

    expect(vm.detail.actionMeaning).toContain("どこを切り替えるかを見直す");
    expect(vm.detail.actionMeaning).not.toBe(vm.detail.shrineMeaning);
  });

  it("reason_facts.primary_axis=distance を優先できる", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: {
        reason_facts: {
          primary_axis: "distance",
          distance_label: "800m",
        },
        fallback_mode: "none",
      },
      index: 0,
      mode: "need",
      needTags: [],
    });

    expect(vm.why.reasonKeys.primary).toBe("distance");
    expect(vm.why.primaryReason).toContain("800m");
  });

  it("reason_facts.primary_axis=popularity を優先できる", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: {
        reason_facts: {
          primary_axis: "popularity",
          popularity_label: "選ばれやすさの安定感があります",
        },
        fallback_mode: "none",
      },
      index: 0,
      mode: "need",
      needTags: [],
    });

    expect(vm.why.reasonKeys.primary).toBe("popular");
    expect(vm.why.primaryReason).toContain("安定感");
  });

  it("reason_facts.primary_axis=element を優先できる", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: {
        reason_facts: {
          primary_axis: "element",
          matched_element: "水",
        },
        fallback_mode: "none",
      },
      index: 0,
      mode: "compat",
      birthdate: "1992-08-10",
      needTags: [],
    });

    expect(vm.why.reasonKeys.primary).toBe("element_match");
    expect(vm.why.primaryReason).toContain("水");
  });

  it("reason_facts.primary_axis=fallback を優先できる", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: {
        reason_facts: {
          primary_axis: "fallback",
          fallback_reason: "まずは動きやすさを優先して見られる候補です",
        },
        fallback_mode: "nearby_unfiltered",
      },
      index: 0,
      mode: "need",
      needTags: [],
    });

    expect(vm.why.reasonKeys.primary).toBe("distance");
    expect(vm.why.primaryReason).toContain("動きやすさ");
  });
});
