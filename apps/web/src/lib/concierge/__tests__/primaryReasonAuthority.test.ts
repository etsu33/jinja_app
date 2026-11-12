import { describe, expect, it } from "vitest";
import { MATCH_SECTION_LABEL, resolvePrimaryReasonMatchKind } from "../primaryReasonAuthority";
import { buildRecommendationReasonViewModel, type BuildParams } from "../buildRecommendationReasonViewModel";

// 表示の判断元を primary_reason_source に統一(2026-11-12)。
// backend/temples/services/recommendation_reason_v4.py の _align_interpretation_with_authority() と
// 同じ分け方になっていること。

describe("resolvePrimaryReasonMatchKind", () => {
  it.each(["need_tag", "text_hint", "goriyaku_tag", "history_theme"])("%s → consultation", (source) => {
    expect(resolvePrimaryReasonMatchKind(source)).toBe("consultation");
  });

  it("user_selected_tag → selected_condition(相談との一致とは言わない)", () => {
    expect(resolvePrimaryReasonMatchKind("user_selected_tag")).toBe("selected_condition");
  });

  it.each(["element", "visit_style", "fallback"])("%s → none(本文が「明確な意味的一致が確認できない」になる種類)", (source) => {
    expect(resolvePrimaryReasonMatchKind(source)).toBe("none");
  });

  it.each([null, undefined, "", "  ", "unknown_future_type", 1])("値が無い・知らない値(%s) → none(一致とは言わない側)", (source) => {
    expect(resolvePrimaryReasonMatchKind(source)).toBe("none");
  });

  it("前後の空白は無視する", () => {
    expect(resolvePrimaryReasonMatchKind(" need_tag ")).toBe("consultation");
  });

  it("見出しは種類ごとに1つ", () => {
    expect(MATCH_SECTION_LABEL.consultation).toBe("相談内容・ご利益との一致");
    expect(MATCH_SECTION_LABEL.selected_condition).toBe("選んだ条件との一致");
    expect(MATCH_SECTION_LABEL.none).toBe("この神社が候補に入った理由");
  });
});

describe("topReasonLabel は primary_reason_source が渡されたらそれだけで決まる", () => {
  const base: BuildParams = {
    rec: { breakdown: { matched_need_tags: ["rest"] }, fallback_mode: "none" },
    index: 0,
    mode: "need",
    needTags: ["rest"],
  };

  it("need_tag → 相談との一致が強い", () => {
    const vm = buildRecommendationReasonViewModel({ ...base, primaryReasonSource: "need_tag" });
    expect(vm.hero.topReasonLabel).toBe("相談との一致が強い");
  });

  it.each(["fallback", "visit_style", "element", null])("%s → ラベルを出さない", (source) => {
    const vm = buildRecommendationReasonViewModel({ ...base, primaryReasonSource: source });
    expect(vm.hero.topReasonLabel).toBeUndefined();
  });

  it("user_selected_tag → 選んだ条件に合う", () => {
    const vm = buildRecommendationReasonViewModel({ ...base, primaryReasonSource: "user_selected_tag" });
    expect(vm.hero.topReasonLabel).toBe("選んだ条件に合う");
  });

  it("渡されない(undefined)ときは従来どおり", () => {
    const vm = buildRecommendationReasonViewModel({ ...base });
    expect(vm.hero.topReasonLabel).toBe("相談との一致が強い");
  });
});
