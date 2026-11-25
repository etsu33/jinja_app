// 推薦の内部分類名を利用者に見せないことを固定する。
//
// 旧実装は Backend の type に対応する分類名を、そのまま画面に出していた。
//   根拠として見ている情報
//     ご利益・意味 / 神社固有の文脈 / 相談との一致 / 明示した条件 / 参拝との相性
//
// これらは設計上の語であって、利用者の言葉ではない。悩みを整理しに来た人からは
// 「分析されている」ように読める。アプリ内で既に使っている語(願うご縁 /
// 参拝スタイル / 選んだ条件)に揃える。
//
// Backend が生成した文章(推薦理由・行動提案の説明)は対象外。あれの意味を
// Mobile 側で変えることはしない。ここで見るのは Mobile が自分で決めた表示名だけ。
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import {
  buildReasonFactItems,
  normalizeRecommendationReasonFacts,
} from "../recommendationReasonFacts";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function withoutComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");
}

// 設計上の語。画面にそのまま出さない。
const INTERNAL_WORDS = [
  "根拠として見ている情報",
  "ご利益・意味",
  "神社固有の文脈",
  "相談との一致",
  "明示した条件",
  "参拝との相性",
];

// Backend の type と、画面に出す語。
const EXPECTED_LABELS: [string, string][] = [
  ["element", "生年月日との相性"],
  ["need_tag", "相談の言葉"],
  ["user_selected_tag", "選んだ条件"],
  ["goriyaku_tag", "願うご縁"],
  ["history_theme", "この神社の背景"],
  ["text_hint", "願うご縁"],
  ["visit_style", "参拝スタイル"],
  ["fallback", "参考にした情報"],
];

describe("内部語彙を画面に出さない", () => {
  it("表示名は設計上の語を使わない", () => {
    const source = withoutComments(
      readFileSync(resolve(mobileRoot, "lib/recommendationReasonFacts.ts"), "utf8"),
    );

    const offenders = INTERNAL_WORDS.filter((word) => source.includes(word));
    expect(offenders).toEqual([]);
  });

  it("推薦結果の見出しも設計上の語を使わない", () => {
    const concierge = withoutComments(
      readFileSync(resolve(mobileRoot, "app/(tabs)/concierge/index.tsx"), "utf8"),
    );

    const offenders = INTERNAL_WORDS.filter((word) => concierge.includes(word));
    expect(offenders).toEqual([]);
    expect(concierge).toContain("相談と重なったもの");
  });

  it("type ごとの表示名が、アプリ内で使っている語である", () => {
    for (const [type, expected] of EXPECTED_LABELS) {
      const facts = normalizeRecommendationReasonFacts([
        { type, label: `${type}_label`, label_ja: `${type}の値`, evidence: [], score: 1 },
      ]);
      const [item] = buildReasonFactItems(facts);

      expect(item?.label, `${type} の表示名`).toBe(expected);
    }
  });
});
