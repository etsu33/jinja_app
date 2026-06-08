import { describe, expect, it } from "vitest";

import { compareState } from "../compareState";
import type { PreviousConsultationSummary } from "../stateComparison";

function makeSummary(
  overrides: Partial<PreviousConsultationSummary> = {},
): PreviousConsultationSummary {
  return {
    threadId: 1,
    createdAt: "2026-05-01T00:00:00.000Z",
    consultationSummary: null,
    matchedNeedTags: [],
    combination: null,
    primaryNeedLabelJa: null,
    primaryReasonLabelJa: null,
    recommendationNames: [],
    actionState: null,
    ...overrides,
  };
}

describe("compareState", () => {
  it("currentだけ combination があると summary が出る", () => {
    const result = compareState(
      makeSummary({ combination: null }),
      makeSummary({
        matchedNeedTags: ["mental", "rest"],
        combination: {
          key: "mental+rest",
          title: "不安と疲れが重なっている状態",
          summary: "考え続ける疲れと、落ち着きたい気持ちが同時に出ています。",
        },
      }),
    );

    expect(result.combinationChange).toEqual({
      previousTitle: null,
      currentTitle: "不安と疲れが重なっている状態",
      changed: true,
      summary: "今回は「不安と疲れが重なっている状態」が状態の重なりとして見えています。",
    });

    expect(result.transitionNarrative.type).toBe("transition");
  });

  it("previous/current が同じ combination なら changed=false", () => {
    const combination = {
      key: "mental+rest",
      title: "不安と疲れが重なっている状態",
      summary: "考え続ける疲れと、落ち着きたい気持ちが同時に出ています。",
    };

    const result = compareState(
      makeSummary({ matchedNeedTags: ["mental", "rest"], combination }),
      makeSummary({ matchedNeedTags: ["mental", "rest"], combination }),
    );

    expect(result.combinationChange).toEqual({
      previousTitle: "不安と疲れが重なっている状態",
      currentTitle: "不安と疲れが重なっている状態",
      changed: false,
      summary: "前回から「不安と疲れが重なっている状態」が継続して見えています。",
    });

    expect(result.transitionNarrative.type).toBe("continuation");
  });

  it("previous/current が違う combination なら changed=true", () => {
    const result = compareState(
      makeSummary({
        matchedNeedTags: ["mental", "rest"],
        combination: {
          key: "mental+rest",
          title: "不安と疲れが重なっている状態",
          summary: "考え続ける疲れと、落ち着きたい気持ちが同時に出ています。",
        },
      }),
      makeSummary({
        matchedNeedTags: ["career", "courage"],
        combination: {
          key: "career+courage",
          title: "仕事や転機に向けて前進したい状態",
          summary: "仕事や役割の流れを変えたい気持ちと、行動に移したい気持ちが重なっています。",
        },
      }),
    );

    expect(result.combinationChange).toEqual({
      previousTitle: "不安と疲れが重なっている状態",
      currentTitle: "仕事や転機に向けて前進したい状態",
      changed: true,
      summary:
        "前回は「不安と疲れが重なっている状態」が見えていましたが、今回は「仕事や転機に向けて前進したい状態」が強く出ています。",
    });

    expect(result.transitionNarrative.type).toBe("progression");
  });

  it("どちらも combination なしなら summary=null", () => {
    const result = compareState(
      makeSummary({ combination: null }),
      makeSummary({ combination: null }),
    );

    expect(result.combinationChange).toEqual({
      previousTitle: null,
      currentTitle: null,
      changed: false,
      summary: null,
    });

    expect(result.transitionNarrative.type).toBe("unknown");
  });

  it("previous の actionState が reflected なら振り返り済みの actionReflection を返す", () => {
    const result = compareState(
      makeSummary({ actionState: "reflected" }),
      makeSummary(),
    );

    expect(result.actionReflection).toEqual({
      type: "reflected",
      title: "前回の提案を振り返りまでつなげています",
      summary:
        "前回の神社について、参拝後の振り返りが保存されています。今回は、その時に見えた変化を踏まえて、次に整えたいテーマを確認する流れです。",
      nextActionLabel: "前回の変化を踏まえて相談する",
    });
  });

  it("previous の actionState が null または none なら hasPreviousAction=false を返す", () => {
    expect(compareState(makeSummary({ actionState: null }), makeSummary()).hasPreviousAction).toBe(false);
    expect(compareState(makeSummary({ actionState: "none" }), makeSummary()).hasPreviousAction).toBe(false);
  });

  it("previous の actionState が saved / visited / reflected なら hasPreviousAction=true を返す", () => {
    expect(compareState(makeSummary({ actionState: "saved" }), makeSummary()).hasPreviousAction).toBe(true);
    expect(compareState(makeSummary({ actionState: "visited" }), makeSummary()).hasPreviousAction).toBe(true);
    expect(compareState(makeSummary({ actionState: "reflected" }), makeSummary()).hasPreviousAction).toBe(true);
  });

  it("前回行動ありなら前回の行動を踏まえた summary を返す", () => {
    const result = compareState(
      makeSummary({ actionState: "visited", matchedNeedTags: ["mental"] }),
      makeSummary({ matchedNeedTags: ["career"] }),
    );

    expect(result.summary).toBe("前回の行動を踏まえると、今回は「仕事や転機を見直したい」を意識する流れが強まっています。");
  });

  it("前回行動なしなら小さく行動へ移す summary を返す", () => {
    const result = compareState(
      makeSummary({ actionState: "none", matchedNeedTags: ["mental"] }),
      makeSummary({ matchedNeedTags: ["career"] }),
    );

    expect(result.summary).toBe("今回は小さく行動へ移すために、「仕事や転機を見直したい」を意識する流れが強まっています。");
  });
});
