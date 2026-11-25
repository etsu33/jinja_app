import { describe, expect, it } from "vitest";
import { normalizeRecommendations } from "../normalize";

describe("normalizeRecommendations", () => {
  it("Backend reason_facts wire shapeを順序と値を変えずに保持し、malformed factを除外する", () => {
    const valid = {
      type: "element",
      label: "火",
      evidence: ["astro_bonus"],
      score: 1.25,
      is_primary: true,
    };
    const secondary = {
      type: "need_tag",
      label: "仕事",
      evidence: ["career"],
      score: 9,
    };

    const [rec] = normalizeRecommendations([{
      name: "A",
      reason_facts: [valid, null, { type: "", label: "欠損", evidence: [], score: 1 }, secondary, { ...valid, evidence: "invalid" }],
    }]);

    expect(rec.reason_facts).toEqual([valid, secondary]);
    expect(rec.reason_facts?.[0]).toBe(valid);
    expect(rec.reason_facts?.[1]).toBe(secondary);
  });

  it.each([null, {}, "invalid", 1])("array以外のreason_factsを空配列として安全に扱う: %p", (reasonFacts) => {
    const [rec] = normalizeRecommendations([{ name: "A", reason_facts: reasonFacts }]);
    expect(rec.reason_facts).toEqual([]);
  });

  it("reason_source など未知フィールドを保持する", () => {
    const input = [
      {
        name: "A",
        reason: "転機・仕事に向き合う参拝に",
        reason_source: "reason:matched_need_tags",
        distance_m: 123,
        extra_field: "keep-me",
      },
    ];

    const recs = normalizeRecommendations(input);

    expect(recs).toHaveLength(1);
    expect(recs[0].name).toBe("A");
    expect(recs[0].reason).toBe("転機・仕事に向き合う参拝に");
    expect((recs[0] as any).reason_source).toBe("reason:matched_need_tags");
    expect((recs[0] as any).extra_field).toBe("keep-me");
    expect((recs[0] as any).distance_m).toBe(123);
  });

  it("reason は優先順位どおりに採用する", () => {
    const input = [
      {
        name: "A",
        reason: "  第一候補  ",
        one_liner: "第二候補",
        explanation: {
          reasons: [{ text: "第三候補" }],
          summary: "第四候補",
        },
        bullets: ["第五候補"],
      },
      {
        name: "B",
        reason: "   ",
        one_liner: "  第二候補  ",
        explanation: {
          reasons: [{ text: "第三候補" }],
          summary: "第四候補",
        },
        bullets: ["第五候補"],
      },
      {
        name: "C",
        reason: null,
        one_liner: "",
        explanation: {
          reasons: [{ text: "  第三候補  " }],
          summary: "第四候補",
        },
        bullets: ["第五候補"],
      },
      {
        name: "D",
        reason: null,
        one_liner: null,
        explanation: {
          reasons: [],
          summary: "  第四候補  ",
        },
        bullets: ["第五候補"],
      },
      {
        name: "E",
        reason: null,
        one_liner: null,
        explanation: {
          reasons: [],
          summary: "   ",
        },
        bullets: ["  第五候補  "],
      },
    ];

    const recs = normalizeRecommendations(input);

    expect(recs[0].reason).toBe("第一候補");
    expect(recs[1].reason).toBe("第二候補");
    expect(recs[2].reason).toBe("第三候補");
    expect(recs[3].reason).toBe("第四候補");
    expect(recs[4].reason).toBe("第五候補");
  });

  it("name / display_name / display_address / is_dummy を整形する", () => {
    const input = [
      {
        name: "  神社A  ",
        location: "  東京都千代田区  ",
        __dummy: true,
      },
      {
        display_name: "  神社B  ",
        display_address: "  大阪府大阪市  ",
        is_dummy: true,
      },
      {
        name: "   ",
        location: "",
      },
    ];

    const recs = normalizeRecommendations(input);

    expect(recs[0].name).toBe("神社A");
    expect(recs[0].display_name).toBe("神社A");
    expect(recs[0].display_address).toBe("東京都千代田区");
    expect(recs[0].is_dummy).toBe(true);
    expect((recs[0] as any).__dummy).toBe(true);

    expect(recs[1].name).toBe("神社B");
    expect(recs[1].display_name).toBe("神社B");
    expect(recs[1].display_address).toBe("  大阪府大阪市  ");
    expect(recs[1].is_dummy).toBe(true);

    expect(recs[2].name).toBe("（名称不明）");
    expect(recs[2].display_name).toBe("（名称不明）");
    expect(recs[2].display_address).toBe(null);
  });
});
