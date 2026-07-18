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
    expect(vm.debug!.reasonKeys.primary).toBe("need_match");
    expect(vm.list.primaryPhrase.length).toBeGreaterThan(0);
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
    expect(vm.debug!.reasonKeys.primary).toBe("element_match");
    expect(vm.list.primaryPhrase.length).toBeGreaterThan(0);
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
    expect(vm.list.primaryPhrase).not.toContain("転機");
    expect(vm.list.summary).not.toContain("願い");
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

    expect(typeof vm.list.secondaryPhrase === "string" || typeof vm.list.secondaryPhrase === "undefined").toBe(true);
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

    expect(vm.list.summary.includes("\n")).toBe(false);
    expect(vm.list.summary).not.toBe(vm.list.primaryPhrase);
    expect(vm.list.summary).not.toBe(vm.list.secondaryPhrase);
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

  it("actionMeaning が今の自分への問いになる", () => {
    const vm = buildRecommendationReasonViewModel({
      rec: { breakdown: { matched_need_tags: ["転機"] }, fallback_mode: "none" },
      index: 0,
      mode: "need",
      needTags: ["転機"],
    });

    expect(vm.detail.actionMeaning).toContain("今の自分は何を続け、何を終わらせ");
    expect(vm.detail.actionMeaning).toContain("でしょうか");
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

    expect(vm.debug!.reasonKeys.primary).toBe("distance");
    expect(vm.list.primaryPhrase).toContain("800m");
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

    expect(vm.debug!.reasonKeys.primary).toBe("popular");
    expect(vm.list.primaryPhrase).toContain("安定感");
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

    expect(vm.debug!.reasonKeys.primary).toBe("element_match");
    expect(vm.list.primaryPhrase).toContain("水");
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

    expect(vm.debug!.reasonKeys.primary).toBe("distance");
    expect(vm.list.primaryPhrase).toContain("動きやすさ");
  });
});
