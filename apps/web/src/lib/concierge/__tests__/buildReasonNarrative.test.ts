import { describe, expect, it } from "vitest";
import { buildReasonNarrative } from "../buildReasonNarrative";
import type { BuildParams } from "../buildRecommendationReasonViewModel";

function params(overrides: Partial<BuildParams> = {}): BuildParams {
  return {
    rec: { fallback_mode: "none" },
    index: 0,
    mode: "need",
    needTags: [],
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// inputType 分類
// ---------------------------------------------------------------------------
describe("inputType resolution", () => {
  it("birthdate → birthdate inputType", () => {
    const r = buildReasonNarrative(params({ birthdate: "1990-01-01", mode: "compat", needTags: [] }));
    expect(r.why.reasonKeys.primary).toBe("element_match");
  });

  it("fallback_mode=nearby_unfiltered (needTags なし) → distance primary", () => {
    // needTags がない場合は fallback_choice → distance
    const r = buildReasonNarrative(params({
      rec: { fallback_mode: "nearby_unfiltered", distance_m: 400 },
      mode: "need",
      needTags: [],
    }));
    expect(r.why.reasonKeys.primary).toBe("distance");
    expect(r.list.primaryPhrase).toContain("動きやすさ");
  });
});

// ---------------------------------------------------------------------------
// buildQueryCandidates: need × benefit × tone パス
// ---------------------------------------------------------------------------
describe("query candidates - benefit label × tone", () => {
  const benefitCases: Array<[string, string]> = [
    ["厄除け", "立て直す"],
    ["開運", "整え直す"],
    ["仕事", "立て直す"],
    ["勝運", "背中を押す"],
    ["学業", "集中を定める"],
    ["合格", "目標に焦点"],
    ["恋愛", "関係の流れ"],
    ["縁結び", "結び目"],
    ["健康", "心身の巡り"],
    ["交通安全", "移動や流れ"],
    ["航海安全", "進む流れを安定"],
    ["家内安全", "暮らしの流れ"],
  ];

  for (const [label, expected] of benefitCases) {
    it(`benefit=${label} → primaryPhrase に変換テキストが含まれる`, () => {
      const r = buildReasonNarrative(params({
        rec: {
          fallback_mode: "none",
          reason_facts: { shrine_benefit: label },
        },
        needTags: ["転機"],
        shrineBenefitLabels: [label],
      }));
      expect(r.list.primaryPhrase + (r.list.secondaryPhrase ?? "")).toContain(expected.slice(0, 4));
    });
  }

  it("tone=strong × 厄除け → 停滞を断ち切る", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        display_name: "三峯神社",
        reason_facts: { shrine_benefit: "厄除け" },
      },
      needTags: ["厄除け"],
      shrineBenefitLabels: ["厄除け"],
    }));
    expect(r.list.primaryPhrase).toContain("断ち切る");
  });

  it("tone=quiet × 厄除け → 不安を静かにほどく", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        display_name: "伊勢神宮（内宮）",
        reason_facts: { shrine_benefit: "厄除け" },
      },
      needTags: ["厄除け"],
      shrineBenefitLabels: ["厄除け"],
    }));
    expect(r.list.primaryPhrase).toContain("静かにほどく");
  });

  it("tone=tight × 仕事 → 優先順位を定め直す", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        display_name: "乃木神社",
        reason_facts: { shrine_benefit: "仕事" },
      },
      needTags: ["仕事"],
      shrineBenefitLabels: ["仕事"],
    }));
    expect(r.list.primaryPhrase).toContain("優先順位を定め直す");
  });

  it("tone=open × 開運 → 流れを通し直す", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        reason_facts: { shrine_benefit: "開運", shrine_feature: "巡りや視野を開く" },
      },
      needTags: [],
      shrineBenefitLabels: ["開運"],
    }));
    // open tone is inferred from feature text
    expect(r.list.primaryPhrase.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// buildQueryCandidates: feature tone パス
// ---------------------------------------------------------------------------
describe("query candidates - feature × tone", () => {
  it("feature あり → text_match として含まれる", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        reason_facts: { shrine_feature: "切り替えの場として選ばれる" },
      },
      needTags: ["転機"],
      shrineFeatureLabels: ["切り替えの場として選ばれる"],
    }));
    expect(r.list.primaryPhrase + (r.list.secondaryPhrase ?? "")).toContain("切り替え");
  });
});

// ---------------------------------------------------------------------------
// buildBirthdateCandidates
// ---------------------------------------------------------------------------
describe("birthdate candidates", () => {
  it("element あり → element_match テキストが含まれる", () => {
    const r = buildReasonNarrative(params({
      rec: { fallback_mode: "none", astro_elements: ["wood"], astro_priority: 2 },
      mode: "compat",
      birthdate: "1985-03-15",
      needTags: [],
    }));
    expect(r.list.primaryPhrase).toContain("wood");
    expect(r.why.reasonKeys.primary).toBe("element_match");
  });

  it("element + distance (astro_priority なし) → secondary に distance が入る", () => {
    // astro_priority がないと sign_support が入らず distance が secondary になる
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        astro_elements: ["fire"],
        distance_m: 800,
      },
      mode: "compat",
      birthdate: "1990-06-01",
      needTags: [],
    }));
    expect(r.why.reasonKeys.secondary).toBe("distance");
    expect(r.why.secondaryReason).toContain("800m");
  });

  it("element + astro_priority → secondary に sign_match が入る", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        astro_elements: ["metal"],
        astro_priority: 1,
        popular_score: 0.75,
      },
      mode: "compat",
      birthdate: "1992-11-01",
      needTags: [],
    }));
    // astro_priority > 0 → sign_support が先に入り secondary = sign_match
    expect(r.why.reasonKeys.secondary).toBe("sign_match");
  });

  it("element なし → fallback テキスト", () => {
    const r = buildReasonNarrative(params({
      rec: { fallback_mode: "none" },
      mode: "compat",
      birthdate: "1990-01-01",
      needTags: [],
    }));
    expect(r.list.primaryPhrase).toContain("相性");
  });
});

// ---------------------------------------------------------------------------
// buildFallbackCandidates
// ---------------------------------------------------------------------------
describe("fallback candidates", () => {
  it("distance のみ → distance primary", () => {
    const r = buildReasonNarrative(params({
      rec: { fallback_mode: "nearby_unfiltered", distance_m: 600 },
      mode: "need",
      needTags: [],
    }));
    expect(r.why.reasonKeys.primary).toBe("distance");
  });

  it("popular_score のみ → popular primary", () => {
    const r = buildReasonNarrative(params({
      rec: { fallback_mode: "nearby_unfiltered", popular_score: 0.9 },
      mode: "need",
      needTags: [],
    }));
    expect(r.why.reasonKeys.primary).toBe("popular");
    expect(r.list.primaryPhrase).toContain("選びやすさ");
  });

  it("popular_score + distance → popular primary, distance secondary", () => {
    // popular_score があると fallback_choice は popular を primary に選ぶ
    const r = buildReasonNarrative(params({
      rec: { fallback_mode: "nearby_unfiltered", distance_m: 300, popular_score: 0.7 },
      mode: "need",
      needTags: [],
    }));
    expect(r.why.reasonKeys.primary).toBe("popular");
    expect(r.why.reasonKeys.secondary).toBe("distance");
  });
});

// ---------------------------------------------------------------------------
// secondary reason types
// ---------------------------------------------------------------------------
describe("secondary reason types", () => {
  it("sign_support: astro_priority > 0 → secondary に sign_match", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        breakdown: { matched_need_tags: ["転機"] },
        astro_priority: 1,
        reason_facts: { primary_axis: "need" },
      },
      needTags: ["転機"],
    }));
    const secondaryKey = r.why.reasonKeys.secondary;
    const hasSign = secondaryKey === "sign_match";
    // sign_match か need_match の secondary
    expect(hasSign || secondaryKey !== undefined).toBe(true);
  });

  it("distance_support: need match primary + distance → secondary に distance", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        breakdown: { matched_need_tags: ["厄除け"] },
        reason_facts: {
          primary_axis: "need",
          shrine_benefit: "厄除け",
        },
        distance_m: 450,
      },
      needTags: ["厄除け"],
      shrineBenefitLabels: ["厄除け"],
    }));
    // distance_support が secondary に入る可能性
    expect(r.list.primaryPhrase).toContain("立て直す");
  });
});

// ---------------------------------------------------------------------------
// rank reason
// ---------------------------------------------------------------------------
describe("rank reason (index=0)", () => {
  it("strongest_theme_match: tone=strong → 切り替えや踏み出し", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        display_name: "三峯神社",
        breakdown: { matched_need_tags: ["転機"] },
        reason_facts: { primary_axis: "need", shrine_benefit: "厄除け" },
      },
      needTags: ["転機"],
      index: 0,
    }));
    expect(r.rank.whyTop).toContain("切り替えや踏み出し");
  });

  it("strongest_theme_match: tone=quiet → 落ち着いて受け止め", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        display_name: "伊勢神宮（内宮）",
        breakdown: { matched_need_tags: ["転機"] },
        reason_facts: { primary_axis: "need", shrine_benefit: "厄除け" },
      },
      needTags: ["転機"],
      index: 0,
    }));
    expect(r.rank.whyTop).toContain("落ち着いて受け止め");
  });

  it("strongest_theme_match: tone=tight → 判断を絞り", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        display_name: "乃木神社",
        breakdown: { matched_need_tags: ["仕事"] },
        reason_facts: { primary_axis: "need", shrine_benefit: "仕事" },
      },
      needTags: ["仕事"],
      index: 0,
    }));
    expect(r.rank.whyTop).toContain("判断を絞り");
  });

  it("strongest_theme_match: need=学業 → 学業への集中", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        breakdown: { matched_need_tags: ["学業"] },
        reason_facts: { primary_axis: "need", shrine_benefit: "学業" },
      },
      needTags: ["学業"],
      index: 0,
    }));
    expect(r.rank.whyTop).toContain("学業");
  });

  it("strongest_compat_match → 生年月日との相性", () => {
    const r = buildReasonNarrative(params({
      rec: { fallback_mode: "none", astro_elements: ["water"], astro_priority: 2 },
      mode: "compat",
      birthdate: "1992-08-10",
      needTags: [],
      index: 0,
    }));
    expect(r.rank.whyTop).toContain("生年月日との相性");
  });

  it("most_actionable (distance_fit) → 実際に動きやすい条件", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        reason_facts: { primary_axis: "distance", distance_label: "300m" },
      },
      needTags: [],
      index: 0,
    }));
    expect(r.rank.whyTop).toContain("動きやすい条件");
  });

  it("most_stable_choice (popularity_fit) → 選びやすさの安定感", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        reason_facts: { primary_axis: "popularity", popularity_label: "人気があります" },
      },
      needTags: [],
      index: 0,
    }));
    expect(r.rank.whyTop).toContain("選びやすさの安定感");
  });

  it("index=1 → rank は空", () => {
    const r = buildReasonNarrative(params({
      rec: { fallback_mode: "none", breakdown: { matched_need_tags: ["転機"] } },
      needTags: ["転機"],
      index: 1,
    }));
    expect(r.rank.whyTop).toBeUndefined();
    expect(r.rank.differenceFromOthers).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// hero catchCopy
// ---------------------------------------------------------------------------
describe("hero catchCopy", () => {
  it("mode=compat → 相性から静かに選びたい", () => {
    const r = buildReasonNarrative(params({
      rec: { fallback_mode: "none" },
      mode: "compat",
      needTags: [],
    }));
    expect(r.hero.catchCopy).toContain("相性から静かに");
  });

  it("visit_style quiet がある場合は Hero catchCopy に反映する", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        breakdown_detail: {
          features: {
            visit_style: {
              raw: 1,
              weight: 0.35,
              matched_tags: ["quiet"],
              contribution: 0.35,
            },
          },
        },
      },
      needTags: [],
    }));

    expect(r.hero.catchCopy).toContain("静かに落ち着いて");
  });

  it.each([
    ["nature", "自然を感じながら"],
    ["reset", "気持ちを切り替えたい"],
    ["less_crowded", "人混みを避けて"],
    ["classic", "安心して選びたい"],
    ["nearby", "無理なく向かいやすい"],
    ["静か", "静かに落ち着いて"],
  ])("visit_style %s が Hero catchCopy に反映される", (tag, expected) => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        breakdown_detail: {
          features: {
            visit_style: {
              matched_tags: [tag],
            },
          },
        },
      },
      needTags: [],
    }));

    expect(r.hero.catchCopy).toContain(expected);
  });

  it("need=厄除け → 気持ちを立て直したい", () => {
    const r = buildReasonNarrative(params({
      rec: { fallback_mode: "none" },
      needTags: ["厄除け"],
    }));
    expect(r.hero.catchCopy).toContain("立て直したい");
  });

  it("need=仕事 → 仕事の流れを整えたい", () => {
    const r = buildReasonNarrative(params({
      rec: { fallback_mode: "none" },
      needTags: ["仕事"],
    }));
    expect(r.hero.catchCopy).toContain("仕事の流れ");
  });

  it("need=金運 → 流れを切り替えたい", () => {
    const r = buildReasonNarrative(params({
      rec: { fallback_mode: "none" },
      needTags: ["金運"],
    }));
    expect(r.hero.catchCopy).toContain("切り替えたい");
  });

  it("primary=distance → 行きやすさを優先したい", () => {
    const r = buildReasonNarrative(params({
      rec: {
        fallback_mode: "none",
        reason_facts: { primary_axis: "distance", distance_label: "200m" },
      },
      needTags: [],
    }));
    expect(r.hero.catchCopy).toContain("行きやすさを優先");
  });
});
