import { describe, it, expect } from "vitest";
import { buildHeroConclusionLines, buildHeroNextActionLines } from "../buildHeroConclusion";

// docs/product/recommendation-result-information-architecture.md §6, §13, §15 PR2:
// this module only lays out already-Authority-decided strings into two Hero blocks.
// It must never re-decide which reason wins, never promote Explanation-only Knowledge
// facts, and never invent connective/causal language for fallback recommendations.

describe("buildHeroConclusionLines", () => {
  it("1. structured reason -> Conclusionは1つのlines配列(1 block)として返る", () => {
    const lines = buildHeroConclusionLines({
      hasStructured: true,
      interpretationText: "今の仕事の悩みは、次の一歩を決めきれていない段階にあるようです。",
      factText: "仕事運・決断力向上のご利益があるとされています。",
      primaryReason: null,
      fallbackText: null,
    });

    expect(lines).toEqual([
      "今の仕事の悩みは、次の一歩を決めきれていない段階にあるようです。",
      "仕事運・決断力向上のご利益があるとされています。",
    ]);
  });

  it("3. fact-first独立表示なし: interpretationが常にfactより先に来る", () => {
    const lines = buildHeroConclusionLines({
      hasStructured: true,
      interpretationText: "相談の理解を示す文。",
      factText: "神社の事実を示す文。",
      primaryReason: null,
      fallbackText: null,
    });

    expect(lines[0]).toBe("相談の理解を示す文。");
    expect(lines[1]).toBe("神社の事実を示す文。");
    expect(lines.indexOf("相談の理解を示す文。")).toBeLessThan(lines.indexOf("神社の事実を示す文。"));
  });

  it("4. need_tag Primary: legacy pathのprimaryReason(need_tag由来)がConclusionに含まれる", () => {
    const lines = buildHeroConclusionLines({
      hasStructured: false,
      interpretationText: null,
      factText: null,
      primaryReason: "今回の相談の中心にある「仕事運」のテーマと重なるため、この神社が候補に入っています。",
      fallbackText: null,
    });

    expect(lines).toEqual([
      "今回の相談の中心にある「仕事運」のテーマと重なるため、この神社が候補に入っています。",
    ]);
  });

  it("5. history_theme Primary: legacy pathのprimaryReason(history_theme由来)がConclusionに含まれる", () => {
    const lines = buildHeroConclusionLines({
      hasStructured: false,
      interpretationText: null,
      factText: null,
      primaryReason: "歴史的な文脈が今の相談テーマと重なる神社です。",
      fallbackText: null,
    });

    expect(lines).toEqual(["歴史的な文脈が今の相談テーマと重なる神社です。"]);
  });

  it("6. fallback: Backendが返した文字列をそのまま通し、新しい因果表現を追加しない", () => {
    const lines = buildHeroConclusionLines({
      hasStructured: false,
      interpretationText: null,
      factText: null,
      primaryReason: "近くの神社です。",
      fallbackText: null,
    });

    // 入力文字列以外の新しい接続語("だから"/"意味的に一致"等)が追加されていないことを確認する。
    expect(lines).toEqual(["近くの神社です。"]);
    expect(lines.join("")).not.toContain("だから");
    expect(lines.join("")).not.toContain("意味的に一致");
  });

  it("7. Knowledge Explanation-only: deity由来のfactTextもそのまま(昇格・再ラベルなし)Conclusionへ含まれる", () => {
    const lines = buildHeroConclusionLines({
      hasStructured: true,
      interpretationText: "相談の理解を示す文。",
      factText: "武神が祀られています。", // deity-sourced (Explanation-only, per Signal Authority §8)
      primaryReason: null,
      fallbackText: null,
    });

    // 昇格を示す接頭辞("Primary理由:"等)が付与されず、Backendの文字列そのまま。
    expect(lines).toContain("武神が祀られています。");
    expect(lines[1]).toBe("武神が祀られています。");
  });

  it("9. legacy path non-regression: primaryReason + fallbackTextの両方がある場合はこの順で保持される", () => {
    const lines = buildHeroConclusionLines({
      hasStructured: false,
      interpretationText: null,
      factText: null,
      primaryReason: "相談とご利益の一致です。",
      fallbackText: "静かに過ごせることが通常の推薦理由です。",
    });

    expect(lines).toEqual(["相談とご利益の一致です。", "静かに過ごせることが通常の推薦理由です。"]);
  });

  it("空文字/空白のみの値はConclusionへ含めない", () => {
    const lines = buildHeroConclusionLines({
      hasStructured: true,
      interpretationText: "   ",
      factText: "",
      primaryReason: null,
      fallbackText: null,
    });

    expect(lines).toEqual([]);
  });

  it("すべて欠落していてもクラッシュせず空配列を返す", () => {
    expect(() =>
      buildHeroConclusionLines({
        hasStructured: false,
        interpretationText: null,
        factText: null,
        primaryReason: null,
        fallbackText: null,
      }),
    ).not.toThrow();
  });
});

describe("buildHeroNextActionLines", () => {
  it("2. actionReasonとactionSuggestionが両方ある場合、1つのlines配列(1 block)として返る", () => {
    const lines = buildHeroNextActionLines({
      actionText: "参拝前に、今の仕事で「変えたいこと」を1つだけ書き出しておくと、意図が定まりやすくなります。",
      actionSuggestionSummary: "参拝ルートを確認する",
    });

    expect(lines).toEqual([
      "参拝前に、今の仕事で「変えたいこと」を1つだけ書き出しておくと、意図が定まりやすくなります。",
      "参拝ルートを確認する",
    ]);
  });

  it("8. generic_safe Action: actionSourceがfallbackのAction Suggestion要約でもクラッシュせず表示される", () => {
    // actionSource="fallback"(generic-safe grounding)自体はBackend側で既に決定済みの値であり、
    // この関数はそのgroundingを再判定しない。ここではpickActionSuggestionV4Summary相当の
    // 呼び出し元が既に解決した要約文字列を受け取るだけであることを確認する。
    const lines = buildHeroNextActionLines({
      actionText: null,
      actionSuggestionSummary: "まず詳細を見て、行く理由を確認する",
    });

    expect(lines).toEqual(["まず詳細を見て、行く理由を確認する"]);
  });

  it("actionTextのみの場合はそのまま1件を返す", () => {
    const lines = buildHeroNextActionLines({
      actionText: "参拝前にできることの文。",
      actionSuggestionSummary: null,
    });

    expect(lines).toEqual(["参拝前にできることの文。"]);
  });

  it("完全に同一の文字列は重複させない", () => {
    const lines = buildHeroNextActionLines({
      actionText: "同じ文言です。",
      actionSuggestionSummary: "同じ文言です。",
    });

    expect(lines).toEqual(["同じ文言です。"]);
  });

  it("両方欠落していても空配列を返しクラッシュしない", () => {
    expect(() => buildHeroNextActionLines({ actionText: null, actionSuggestionSummary: null })).not.toThrow();
    expect(buildHeroNextActionLines({ actionText: null, actionSuggestionSummary: null })).toEqual([]);
  });
});
