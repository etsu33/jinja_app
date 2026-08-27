import { describe, expect, it } from "vitest";
import { resolveCompassSupplementaryFactText } from "../resolveCompassSupplementaryFactText";
import type { CompassRecommendation } from "../types";

function rec(overrides: Partial<CompassRecommendation>): CompassRecommendation {
  return { name: "テスト神社", ...overrides };
}

describe("resolveCompassSupplementaryFactText", () => {
  // Case 1: Purpose/Need Evidenceあり -- 実際のRanking Evidenceだけ表示。
  // Purpose match is already covered by the existing `reason` text, so this
  // slot stays empty rather than duplicating it.
  it("purposeがmatched_need_tagsに含まれる場合はnull（reasonが既に説明済み）", () => {
    const result = resolveCompassSupplementaryFactText(
      rec({ breakdown: { matched_need_tags: ["career"] } }),
      "career",
    );
    expect(result).toBeNull();
  });

  // Case 2: Direction + Distanceのみ -- Purpose Matchを捏造しない。
  it("purposeが未一致の場合はFilter Contextのみを表示し、Purpose一致を捏造しない", () => {
    const result = resolveCompassSupplementaryFactText(
      rec({ breakdown: { matched_need_tags: [] } }),
      "study",
    );
    expect(result).toBe("今回の方向・距離の条件に合う候補です");
    expect(result).not.toMatch(/study/);
  });

  // Case 3: 一部Evidence欠損 -- 存在するEvidenceのみ表示。
  it("breakdown自体が無い場合でもクラッシュせず、未一致として扱う", () => {
    const result = resolveCompassSupplementaryFactText(rec({}), "money");
    expect(result).toBe("今回の方向・距離の条件に合う候補です");
  });

  // Case 4: Internal tag label不明 -- raw keyを表示しない。
  it("history_themeのlabelが空文字のみのfactは無視し、raw keyを表示しない", () => {
    const result = resolveCompassSupplementaryFactText(
      rec({
        reason_facts: [{ type: "history_theme", label: "   " }],
        breakdown: { matched_need_tags: [] },
      }),
      "money",
    );
    // history_theme label is blank -> falls through to Filter Context, never
    // a blank/placeholder line.
    expect(result).toBe("今回の方向・距離の条件に合う候補です");
  });

  // Case 5: Astrology / 九星気学がRanking非利用の場合 -- Explanationへ一切出さない。
  it("astrology/element系のreason_factはこの関数が一切参照しない", () => {
    const result = resolveCompassSupplementaryFactText(
      rec({
        reason_facts: [{ type: "element", label: "element", is_primary: true }],
        breakdown: { matched_need_tags: ["money"] },
      }),
      "money",
    );
    expect(result).toBeNull();
  });

  // Case 6: Supporting FactはあるがRanking非利用 -- 上位になった理由として表示しない。
  it("history_themeはKAMI MUSUBIの解釈であることが分かる表現で表示する", () => {
    const result = resolveCompassSupplementaryFactText(
      rec({
        reason_facts: [{ type: "history_theme", label: "守り", is_primary: true }],
        breakdown: { matched_need_tags: ["protection"] },
      }),
      "protection",
    );
    expect(result).toBe("守りという文脈（KAMI MUSUBIの解釈）");
  });

  it("history_themeとpurpose不一致が両方ある場合はhistory_themeを優先する", () => {
    const result = resolveCompassSupplementaryFactText(
      rec({
        reason_facts: [{ type: "history_theme", label: "縁" }],
        breakdown: { matched_need_tags: [] },
      }),
      "love",
    );
    expect(result).toBe("縁という文脈（KAMI MUSUBIの解釈）");
  });

  it("purposeが未指定(undefined)の場合はFilter Contextも表示しない（既存呼び出し元の互換性）", () => {
    const result = resolveCompassSupplementaryFactText(rec({ breakdown: { matched_need_tags: [] } }), undefined);
    expect(result).toBeNull();
  });

  it("reason_factsに無関係なtypeしかない場合はnull（fallback factのみ等）", () => {
    const result = resolveCompassSupplementaryFactText(
      rec({
        reason_facts: [{ type: "fallback", label: "fallback" }],
        breakdown: { matched_need_tags: ["career"] },
      }),
      "career",
    );
    expect(result).toBeNull();
  });
});
